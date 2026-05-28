from apps.api.app.core.config import Settings, settings


def test_settings_default_allowed_origins_is_list():
    cfg = Settings()
    assert isinstance(cfg.allowed_origins, list)
    assert "http://localhost:3000" in cfg.allowed_origins


def test_global_settings_has_required_fields():
    assert isinstance(settings.ollama_base_url, str)
    assert isinstance(settings.ollama_model, str)
    assert isinstance(settings.allowed_origins, list)
