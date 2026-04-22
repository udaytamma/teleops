"""RAG index utilities.

Uses Gemini's `text-embedding-004` (768 dim) via a minimal custom LlamaIndex
embedding wrapper. This replaces the previous `sentence-transformers`
(MiniLM, 384 dim) setup to eliminate the PyTorch runtime dependency and
drop ~800MB of resident memory on Railway.

NOTE: Dimensions differ between old (384) and new (768) models. The
persisted index at `settings.rag_index_dir` must be rebuilt -- loading an
index created with MiniLM will fail at retrieval time. Delete the
directory or call `rebuild_index()` once after deploying this change.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

from teleops.config import logger, settings

_INDEX = None
_INDEX_LOCK = threading.Lock()

_GEMINI_EMBED_MODEL = "models/gemini-embedding-001"
_GEMINI_EMBED_DIM = 768  # gemini-embedding-001 supports 768/1536/3072; 768 is cheapest + fastest


def _require_llama_index():
    try:
        from llama_index.core import (
            SimpleDirectoryReader,
            StorageContext,
            VectorStoreIndex,
            load_index_from_storage,
        )
        from llama_index.core.embeddings import BaseEmbedding
        from llama_index.core.vector_stores import SimpleVectorStore
    except ImportError as exc:
        raise RuntimeError("LlamaIndex dependencies not installed") from exc
    return (
        SimpleDirectoryReader,
        StorageContext,
        VectorStoreIndex,
        load_index_from_storage,
        BaseEmbedding,
        SimpleVectorStore,
    )


def _require_gemini():
    try:
        import google.generativeai as genai
    except ImportError as exc:
        raise RuntimeError("google-generativeai not installed") from exc
    api_key = getattr(settings, "gemini_api_key", None) or _env_gemini_key()
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is required for Gemini embeddings. "
            "Set the env var before building the RAG index."
        )
    genai.configure(api_key=api_key)
    return genai


def _env_gemini_key() -> str | None:
    import os

    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def _make_gemini_embedding(BaseEmbedding: Any) -> Any:  # noqa: N803
    """Build a minimal Gemini-backed LlamaIndex embedding class.

    We define the class inside a factory so that importing this module
    does not require `llama_index` at import time (keeps `_require_*`
    lazy-loading pattern consistent with the old implementation).
    """
    genai = _require_gemini()

    class GeminiEmbedding(BaseEmbedding):
        """LlamaIndex embedding wrapper around Gemini text-embedding-004."""

        model_name: str = _GEMINI_EMBED_MODEL

        def _embed(self, text: str, task_type: str) -> list[float]:
            result = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type=task_type,
                output_dimensionality=_GEMINI_EMBED_DIM,
            )
            # SDK returns {"embedding": [...]} for single input
            embedding = result["embedding"] if isinstance(result, dict) else result.embedding
            return list(embedding)

        # LlamaIndex hooks -- sync
        def _get_query_embedding(self, query: str) -> list[float]:
            return self._embed(query, task_type="RETRIEVAL_QUERY")

        def _get_text_embedding(self, text: str) -> list[float]:
            return self._embed(text, task_type="RETRIEVAL_DOCUMENT")

        # LlamaIndex hooks -- async (delegate to sync; Gemini SDK is sync)
        async def _aget_query_embedding(self, query: str) -> list[float]:
            return self._get_query_embedding(query)

        async def _aget_text_embedding(self, text: str) -> list[float]:
            return self._get_text_embedding(text)

    return GeminiEmbedding()


def build_or_load_index():
    global _INDEX
    if _INDEX is not None:
        return _INDEX

    with _INDEX_LOCK:
        # Double-check after acquiring lock
        if _INDEX is not None:
            return _INDEX

        (
            SimpleDirectoryReader,  # noqa: N806
            StorageContext,  # noqa: N806
            VectorStoreIndex,  # noqa: N806
            load_index_from_storage,
            BaseEmbedding,  # noqa: N806
            SimpleVectorStore,  # noqa: N806
        ) = _require_llama_index()

        corpus_dir = Path(settings.rag_corpus_dir)
        index_dir = Path(settings.rag_index_dir)
        index_dir.mkdir(parents=True, exist_ok=True)

        embed_model = _make_gemini_embedding(BaseEmbedding)

        if (index_dir / "docstore.json").exists():
            logger.info("Loading existing RAG index from disk")
            try:
                storage_context = StorageContext.from_defaults(persist_dir=str(index_dir))
                _INDEX = load_index_from_storage(storage_context, embed_model=embed_model)
                return _INDEX
            except Exception as exc:  # dim mismatch or stale index
                logger.warning(
                    f"Failed to load existing RAG index ({exc}); rebuilding from corpus"
                )

        if not corpus_dir.exists():
            logger.warning(f"RAG corpus directory not found: {corpus_dir}")
            corpus_dir.mkdir(parents=True, exist_ok=True)

        documents = SimpleDirectoryReader(str(corpus_dir)).load_data()
        vector_store = SimpleVectorStore()
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex.from_documents(
            documents, storage_context=storage_context, embed_model=embed_model
        )
        index.storage_context.persist(persist_dir=str(index_dir))
        logger.info(
            f"Built RAG index with {len(documents)} documents using {_GEMINI_EMBED_MODEL}"
        )
        _INDEX = index
        return _INDEX


def rebuild_index() -> None:
    """Force a rebuild of the RAG index (clears cache + disk)."""
    global _INDEX
    import shutil

    with _INDEX_LOCK:
        _INDEX = None
        index_dir = Path(settings.rag_index_dir)
        if index_dir.exists():
            shutil.rmtree(index_dir)
            logger.info(f"Cleared RAG index at {index_dir}")
    build_or_load_index()


def get_rag_context(query: str) -> list[str]:
    index = build_or_load_index()
    retriever = index.as_retriever(similarity_top_k=settings.rag_top_k)
    nodes = retriever.retrieve(query)
    return [node.get_content() for node in nodes]
