import hashlib

from shared.config import settings


class EmbeddingModel:
    _instance: "EmbeddingModel | None" = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def _get_model(self):
        if self._model is not None:
            return self._model
        try:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(
                "all-MiniLM-L6-v2",
                cache_folder=str(settings.models_dir),
            )
        except Exception:
            self._model = None
        return self._model

    def embed_text(self, text: str) -> list[float]:
        model = self._get_model()
        if model is not None:
            embedding = model.encode(text, normalize_embeddings=True)
            return embedding.tolist()

        digest = hashlib.sha256(text.encode("utf-8")).digest()
        return [round(byte / 255, 6) for byte in digest] * 12
