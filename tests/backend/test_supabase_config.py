import pytest
from unittest.mock import patch
from app.core.supabase import (
    is_supabase_configured,
    get_supabase_config_status,
    get_supabase_client,
)
import app.core.supabase as supabase_module


@pytest.fixture(autouse=True)
def reset_supabase_singletons():
    """Reset singletons before and after each test."""
    supabase_module._anon_client = None
    supabase_module._service_client = None
    yield
    supabase_module._anon_client = None
    supabase_module._service_client = None


def test_supabase_unconfigured():
    """Verify safe behavior when Supabase environment variables are absent."""
    with patch('app.core.supabase.get_config') as mock_get_config:
        class EmptyConfig:
            SUPABASE_URL = ''
            SUPABASE_ANON_KEY = ''
            SUPABASE_SERVICE_ROLE_KEY = ''

        mock_get_config.return_value = EmptyConfig

        assert is_supabase_configured(use_service_role=False) is False
        assert is_supabase_configured(use_service_role=True) is False

        status = get_supabase_config_status()
        assert status == {
            "url": "missing",
            "anon_key": "missing",
            "service_role_key": "missing",
        }

        with pytest.raises(ValueError, match="SUPABASE_URL is missing"):
            get_supabase_client(use_service_role=False)

        with pytest.raises(ValueError, match="SUPABASE_URL is missing"):
            get_supabase_client(use_service_role=True)


def test_supabase_configured_status():
    """Verify safe status reporting when Supabase variables are configured."""
    with patch('app.core.supabase.get_config') as mock_get_config:
        class DummyConfig:
            SUPABASE_URL = 'https://dummy-project.supabase.co'
            SUPABASE_ANON_KEY = 'dummy-anon-key'
            SUPABASE_SERVICE_ROLE_KEY = 'dummy-service-role-key'

        mock_get_config.return_value = DummyConfig

        assert is_supabase_configured(use_service_role=False) is True
        assert is_supabase_configured(use_service_role=True) is True

        status = get_supabase_config_status()
        assert status == {
            "url": "configured",
            "anon_key": "configured",
            "service_role_key": "configured",
        }
        # Ensure secrets are never exposed in status
        assert "dummy-anon-key" not in str(status)
        assert "dummy-service-role-key" not in str(status)


def test_supabase_client_initialization_and_singleton():
    """Verify that clients are initialized and cached as singletons."""
    with patch('app.core.supabase.get_config') as mock_get_config, \
         patch('app.core.supabase.create_client') as mock_create_client:
        
        class MockConfig:
            SUPABASE_URL = 'https://dummy-project.supabase.co'
            SUPABASE_ANON_KEY = 'dummy-anon-key'
            SUPABASE_SERVICE_ROLE_KEY = 'dummy-service-role-key'

        mock_get_config.return_value = MockConfig
        mock_create_client.side_effect = lambda url, key: f"Client({url}, {key})"

        # First call creates client
        anon_1 = get_supabase_client(use_service_role=False)
        assert anon_1 == "Client(https://dummy-project.supabase.co, dummy-anon-key)"
        assert mock_create_client.call_count == 1

        # Second call returns cached singleton
        anon_2 = get_supabase_client(use_service_role=False)
        assert anon_2 is anon_1
        assert mock_create_client.call_count == 1

        # Service role client initialization
        svc_1 = get_supabase_client(use_service_role=True)
        assert svc_1 == "Client(https://dummy-project.supabase.co, dummy-service-role-key)"
        assert mock_create_client.call_count == 2

        # Second call returns cached service role singleton
        svc_2 = get_supabase_client(use_service_role=True)
        assert svc_2 is svc_1
        assert mock_create_client.call_count == 2
