from sentence_transformers import SentenceTransformer
from config import settings


class EmbeddingModel:
    _instance: "EmbeddingModel | None" = None
    _model: SentenceTransformer | None = None

    def __new__(cls) -> "EmbeddingModel":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(
                settings.embedding_model,
                cache_folder=str(settings.models_dir),
            )
        return self._model

    def embed_text(self, text: str) -> list[float]:
        model = self._get_model()
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32)
        return embeddings.tolist()
