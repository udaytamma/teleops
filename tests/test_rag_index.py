from teleops.config import settings
from teleops.rag import index


class DummyNode:
    def __init__(self, content: str) -> None:
        self._content = content

    def get_content(self) -> str:
        return self._content


class DummyRetriever:
    def __init__(self, nodes):
        self._nodes = nodes

    def retrieve(self, query: str):
        return self._nodes


class DummyStorageContext:
    def __init__(self):
        self.persisted = False

    def persist(self, persist_dir: str):
        self.persisted = True

    @classmethod
    def from_defaults(cls, **kwargs):
        return cls()


class DummyIndex:
    def __init__(self, storage_context: DummyStorageContext):
        self.storage_context = storage_context

    def as_retriever(self, similarity_top_k: int):
        return DummyRetriever([DummyNode("test context")])

    @classmethod
    def from_documents(cls, documents, storage_context, embed_model):
        return cls(storage_context=storage_context)


class DummyReader:
    def __init__(self, path: str):
        self.path = path

    def load_data(self):
        return ["doc"]


class DummyEmbed:
    """Stand-in for a LlamaIndex BaseEmbedding subclass."""

    model_name = "dummy-model"


def _fake_require_llama_index():
    # Returns: (SimpleDirectoryReader, StorageContext, VectorStoreIndex,
    #          load_index_from_storage, BaseEmbedding, SimpleVectorStore)
    return (
        DummyReader,
        DummyStorageContext,
        DummyIndex,
        lambda storage_context, embed_model=None: DummyIndex(storage_context=storage_context),
        DummyEmbed,
        object,
    )


def _fake_make_gemini_embedding(_base_embedding_cls):
    return DummyEmbed()


def test_build_or_load_index_creates_and_retrieves(tmp_path, monkeypatch):
    corpus_dir = tmp_path / "corpus"
    index_dir = tmp_path / "index"
    corpus_dir.mkdir()
    (corpus_dir / "doc.txt").write_text("test", encoding="utf-8")

    monkeypatch.setattr(settings, "rag_corpus_dir", str(corpus_dir))
    monkeypatch.setattr(settings, "rag_index_dir", str(index_dir))
    monkeypatch.setattr(index, "_require_llama_index", _fake_require_llama_index)
    monkeypatch.setattr(index, "_make_gemini_embedding", _fake_make_gemini_embedding)
    # Reset the module-level cache so each test gets a fresh build path
    monkeypatch.setattr(index, "_INDEX", None)

    built = index.build_or_load_index()
    assert isinstance(built, DummyIndex)

    context = index.get_rag_context("query")
    assert context == ["test context"]


def test_build_or_load_index_uses_existing(tmp_path, monkeypatch):
    corpus_dir = tmp_path / "corpus"
    index_dir = tmp_path / "index"
    corpus_dir.mkdir()
    index_dir.mkdir()
    (index_dir / "docstore.json").write_text("{}", encoding="utf-8")

    monkeypatch.setattr(settings, "rag_corpus_dir", str(corpus_dir))
    monkeypatch.setattr(settings, "rag_index_dir", str(index_dir))
    monkeypatch.setattr(index, "_require_llama_index", _fake_require_llama_index)
    monkeypatch.setattr(index, "_make_gemini_embedding", _fake_make_gemini_embedding)
    # Reset the module-level cache so each test gets a fresh build path
    monkeypatch.setattr(index, "_INDEX", None)

    built = index.build_or_load_index()
    assert isinstance(built, DummyIndex)
