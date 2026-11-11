"""Security and environment configuration tests — Phase 10 Stage A.

Verifies:
- Production rejects missing or short SECRET_KEY.
- Production accepts a valid SECRET_KEY.
- Development uses a placeholder without raising.
- Testing environment is unaffected.
- DEBUG is disabled in production by default.
- Debug mode cannot be accidentally enabled in production.
- No secret value leaks into error messages or logs.
"""
import os
import pytest
from unittest.mock import patch


class TestSecretKeyValidation:
    """Tests for SECRET_KEY validation logic."""

    def test_production_missing_secret_key_raises(self, monkeypatch):
        """Production without SECRET_KEY must fail fast with a clear message."""
        from src.config.settings import ProductionConfig

        monkeypatch.setattr(ProductionConfig, 'APP_ENV', 'production')
        monkeypatch.setattr(ProductionConfig, 'SECRET_KEY', '')
        with pytest.raises(RuntimeError) as exc_info:
            ProductionConfig.validate_production()
        msg = str(exc_info.value)
        assert "SECRET_KEY" in msg
        assert "not set" in msg.lower() or "environment variable" in msg.lower()

    def test_production_short_secret_key_raises(self, monkeypatch):
        """Production with a SECRET_KEY shorter than 32 chars must fail."""
        from src.config.settings import ProductionConfig

        monkeypatch.setattr(ProductionConfig, 'APP_ENV', 'production')
        monkeypatch.setattr(ProductionConfig, 'SECRET_KEY', 'short-key')
        with pytest.raises(RuntimeError) as exc_info:
            ProductionConfig.validate_production()
        msg = str(exc_info.value)
        assert "SECRET_KEY" in msg
        assert "32" in msg

    def test_production_valid_secret_key_passes(self, monkeypatch):
        """Production with a ≥ 32-char SECRET_KEY must pass validation."""
        from src.config.settings import ProductionConfig

        valid_key = 'x' * 32  # exactly 32 characters
        monkeypatch.setattr(ProductionConfig, 'APP_ENV', 'production')
        monkeypatch.setattr(ProductionConfig, 'SECRET_KEY', valid_key)
        # Should not raise
        ProductionConfig.validate_production()

    def test_development_uses_placeholder(self, monkeypatch):
        """Development must not raise even with no SECRET_KEY set."""
        from src.config.settings import DevelopmentConfig

        monkeypatch.setattr(DevelopmentConfig, 'APP_ENV', 'development')
        monkeypatch.setattr(DevelopmentConfig, 'SECRET_KEY', '')
        # validate_production returns early for non-production → no raise
        DevelopmentConfig.validate_production()
        assert DevelopmentConfig.DEBUG is True

    def test_testing_unaffected(self, monkeypatch):
        """Testing config must work regardless of SECRET_KEY length."""
        from src.config.settings import TestingConfig

        monkeypatch.setattr(TestingConfig, 'APP_ENV', 'testing')
        monkeypatch.setattr(TestingConfig, 'SECRET_KEY', '')
        TestingConfig.validate_production()  # returns early
        assert TestingConfig.TESTING is True
        assert TestingConfig.DEBUG is False

    def test_get_config_returns_correct_class(self):
        """get_config() returns the right class for each APP_ENV."""
        from src.config.settings import get_config

        with patch.dict(os.environ, {'APP_ENV': 'production'}):
            cfg = get_config()
            assert cfg.__name__ == 'ProductionConfig'

        with patch.dict(os.environ, {'APP_ENV': 'development'}):
            cfg = get_config()
            assert cfg.__name__ == 'DevelopmentConfig'

        with patch.dict(os.environ, {'APP_ENV': 'testing'}):
            cfg = get_config()
            assert cfg.__name__ == 'TestingConfig'

        # Unknown env falls back to Development
        with patch.dict(os.environ, {'APP_ENV': 'staging'}):
            cfg = get_config()
            assert cfg.__name__ == 'DevelopmentConfig'


class TestDebugMode:
    """Tests for DEBUG mode configuration."""

    def test_production_debug_disabled_by_default(self):
        """Production must have DEBUG=False regardless of env vars."""
        from src.config.settings import ProductionConfig
        assert ProductionConfig.DEBUG is False

    def test_development_debug_enabled(self):
        """Development must have DEBUG=True."""
        from src.config.settings import DevelopmentConfig
        assert DevelopmentConfig.DEBUG is True

    def test_testing_debug_disabled(self):
        """Testing must have DEBUG=False."""
        from src.config.settings import TestingConfig
        assert TestingConfig.DEBUG is False

    def test_production_rejects_explicit_debug_true(self, monkeypatch):
        """Production must raise if DEBUG is somehow set to True."""
        from src.config.settings import ProductionConfig

        monkeypatch.setattr(ProductionConfig, 'APP_ENV', 'production')
        monkeypatch.setattr(ProductionConfig, 'SECRET_KEY', 'a' * 32)
        monkeypatch.setattr(ProductionConfig, 'DEBUG', True)
        with pytest.raises(RuntimeError) as exc_info:
            ProductionConfig.validate_production()
        msg = str(exc_info.value)
        assert "DEBUG" in msg
        assert "production" in msg.lower()


class TestNoSecretLeakage:
    """Verify that secrets never appear in error messages or logs."""

    def test_secret_not_in_validation_error_message(self, monkeypatch):
        """Error message for short/missing key must not contain the actual value."""
        from src.config.settings import ProductionConfig

        secret = 'short'  # below 32-char minimum → will trigger error
        monkeypatch.setattr(ProductionConfig, 'APP_ENV', 'production')
        monkeypatch.setattr(ProductionConfig, 'SECRET_KEY', secret)
        with pytest.raises(RuntimeError) as exc_info:
            ProductionConfig.validate_production()
        msg = str(exc_info.value)
        assert secret not in msg

    def test_env_example_has_no_real_secret(self):
        """The .env.example file must not contain a real secret value."""
        import pathlib
        example = (
            pathlib.Path(__file__).resolve().parents[2] / 'Backend' / '.env.example'
        )
        content = example.read_text(encoding='utf-8')
        # Should contain a placeholder, not the old dev secret
        assert 'pixel-t-dev-secret-change-in-production' not in content
        # Should have an instruction about generating a key
        assert '32' in content or 'generate' in content.lower() or 'random' in content.lower()
