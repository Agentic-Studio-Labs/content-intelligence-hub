import numpy as np
from embeddings import EmbeddingModel


def test_embed_text_returns_correct_dimensions():
    model = EmbeddingModel()
    result = model.embed_text("hello world")
    assert isinstance(result, list)
    assert len(result) == 384


def test_embed_text_deterministic():
    model = EmbeddingModel()
    a = model.embed_text("cloud migration strategy")
    b = model.embed_text("cloud migration strategy")
    assert a == b


def test_embed_batch():
    model = EmbeddingModel()
    texts = ["hello world", "cloud migration", "devops practices"]
    results = model.embed_batch(texts)
    assert len(results) == 3
    assert all(len(r) == 384 for r in results)


def test_similar_texts_closer_than_dissimilar():
    model = EmbeddingModel()
    a = model.embed_text("cloud computing and migration strategies")
    b = model.embed_text("cloud infrastructure and migration planning")
    c = model.embed_text("chocolate cake recipe with frosting")
    sim_ab = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    sim_ac = np.dot(a, c) / (np.linalg.norm(a) * np.linalg.norm(c))
    assert sim_ab > sim_ac
