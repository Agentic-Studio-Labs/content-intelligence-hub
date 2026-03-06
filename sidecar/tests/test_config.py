from config import Settings


def test_default_settings():
    settings = Settings()
    assert settings.port == 8420
    assert settings.embedding_model == "all-MiniLM-L6-v2"
    assert settings.embedding_dimensions == 384
    assert settings.llm_model == "claude-sonnet-4-6"
    assert settings.llm_temperature == 0.7
    assert settings.search_limit == 10
    assert settings.hybrid_alpha == 0.5
    assert "ContentIntelligenceHub" in str(settings.data_dir)
    assert settings.db_path.name == "content.db"


def test_settings_from_env(monkeypatch):
    monkeypatch.setenv("CIH_PORT", "9999")
    monkeypatch.setenv("CIH_ANTHROPIC_API_KEY", "sk-test-key")
    settings = Settings()
    assert settings.port == 9999
    assert settings.anthropic_api_key == "sk-test-key"


def test_data_dir_creation(tmp_path, monkeypatch):
    monkeypatch.setenv("CIH_DATA_DIR", str(tmp_path / "test_data"))
    settings = Settings()
    settings.ensure_dirs()
    assert settings.data_dir.exists()
