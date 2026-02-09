"""RAG index utilities."""

from __future__ import annotations

import threading
from pathlib import Path

from teleops.config import settings, logger

_INDEX = None
_INDEX_LOCK = threading.Lock()


def _require_llama_index():
    try:
        from llama_index.core import (
            SimpleDirectoryReader,
            StorageContext,
            VectorStoreIndex,
            load_index_from_storage,
        )
        from llama_index.core.vector_stores import SimpleVectorStore
        from llama_index.embeddings.huggingface import HuggingFaceEmbedding
    except ImportError as exc:
        raise RuntimeError("LlamaIndex dependencies not installed") from exc
    return (
        SimpleDirectoryReader,
        StorageContext,
        VectorStoreIndex,
        load_index_from_storage,
        HuggingFaceEmbedding,
        SimpleVectorStore,
    )


def build_or_load_index():
    global _INDEX
    if _INDEX is not None:
        return _INDEX

    with _INDEX_LOCK:
        # Double-check after acquiring lock
        if _INDEX is not None:
            return _INDEX

        (
            SimpleDirectoryReader,
            StorageContext,
            VectorStoreIndex,
            load_index_from_storage,
            HuggingFaceEmbedding,
            SimpleVectorStore,
        ) = _require_llama_index()

        corpus_dir = Path(settings.rag_corpus_dir)
        index_dir = Path(settings.rag_index_dir)
        index_dir.mkdir(parents=True, exist_ok=True)

        embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

        if (index_dir / "docstore.json").exists():
            logger.info("Loading existing RAG index from disk")
            storage_context = StorageContext.from_defaults(persist_dir=str(index_dir))
            _INDEX = load_index_from_storage(storage_context, embed_model=embed_model)
            return _INDEX

        if not corpus_dir.exists():
            logger.warning(f"RAG corpus directory not found: {corpus_dir}")
            corpus_dir.mkdir(parents=True, exist_ok=True)

        documents = SimpleDirectoryReader(str(corpus_dir)).load_data()
        vector_store = SimpleVectorStore()
        storage_context = StorageContext.from_defaults(vector_store=vector_store)
        index = VectorStoreIndex.from_documents(documents, storage_context=storage_context, embed_model=embed_model)
        index.storage_context.persist(persist_dir=str(index_dir))
        logger.info(f"Built RAG index with {len(documents)} documents")
        _INDEX = index
        return _INDEX


def get_rag_context(query: str) -> list[str]:
    index = build_or_load_index()
    retriever = index.as_retriever(similarity_top_k=settings.rag_top_k)
    nodes = retriever.retrieve(query)
    return [node.get_content() for node in nodes]
