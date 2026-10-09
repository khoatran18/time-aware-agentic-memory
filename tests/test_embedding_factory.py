import pytest

from tam.config.loader import Config
from tam.embeddings import registry
from tam.embeddings.base import DenseEmbedder, SparseEmbedder, SparseVec
from tam.embeddings.factory import HybridEmbedder, get_embedder


class StubDense(DenseEmbedder):
    dim = 3

    @classmethod
    def from_profile(cls, profile):
        return cls()

    def embed(self, texts):
        return [[1.0, 0.0, 0.0] for _ in texts]

    def embed_query(self, text):
        return [0.0, 1.0, 0.0]


class StubSparse(SparseEmbedder):
    @classmethod
    def from_profile(cls, profile):
        return cls()

    def embed(self, texts):
        return [SparseVec([1], [1.0]) for _ in texts]

    def embed_query(self, text):
        return SparseVec([2], [1.0])


@pytest.fixture
def stub_providers(monkeypatch):
    monkeypatch.setitem(registry.DENSE_PROVIDERS, "stub", StubDense)
    monkeypatch.setitem(registry.SPARSE_PROVIDERS, "stub", StubSparse)


def cfg(dense="stub", sparse="stub"):
    """Config giả: profiles.dense.d -> provider `dense`, profiles.sparse.s -> provider `sparse`."""
    return Config({"embedding": {
        "profiles": {"dense": {"d": {"provider": dense, "model_id": "m"}}, "sparse": {"s": {"provider": sparse, "model_id": "m"}}},
        "dense": "d",
        "sparse": "s",
    }})


def test_factory_composes_dense_and_sparse(stub_providers):
    e = get_embedder(cfg())
    assert isinstance(e, HybridEmbedder) and e.dense_dim == 3
    assert e.embed_dense(["a", "b"]) == [[1.0, 0.0, 0.0]] * 2
    assert e.embed_sparse_query("q").indices == [2]


def test_dense_and_sparse_can_use_different_providers(stub_providers, monkeypatch):
    monkeypatch.setitem(registry.SPARSE_PROVIDERS, "other", StubSparse)
    assert get_embedder(cfg(dense="stub", sparse="other")).dense_dim == 3


def test_unknown_profile_name_lists_available():
    c = Config({"embedding": {
        "profiles": {"dense": {"d": {"provider": "fastembed", "model_id": "m"}}, "sparse": {}},
        "dense": "nope",
        "sparse": "x",
    }})
    with pytest.raises(ValueError, match="'nope'.*profiles.dense.*\\['d'\\]"):
        get_embedder(c)


def test_real_configs_point_to_existing_profiles():
    from tam.config.loader import load_config

    for env in ("dev", "prod"):
        c = load_config(env)
        assert c.embedding.dense in c.embedding.profiles.dense
        assert c.embedding.sparse in c.embedding.profiles.sparse


def test_unknown_provider_lists_available():
    with pytest.raises(ValueError, match="'openai'.*fastembed"):
        get_embedder(cfg(dense="openai"))


def test_provider_missing_method_fails_at_creation():
    class Broken(DenseEmbedder):  # thiếu embed_query
        dim = 1

        @classmethod
        def from_profile(cls, profile):
            return cls()

        def embed(self, texts):
            return []

    with pytest.raises(TypeError, match="embed_query"):
        Broken.from_profile({})


def test_fastembed_listed_by_default():
    assert "fastembed" in registry.DENSE_PROVIDERS and "fastembed" in registry.SPARSE_PROVIDERS
