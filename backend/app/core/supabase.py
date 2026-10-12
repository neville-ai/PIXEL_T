from typing import Optional, Dict
from supabase import create_client, Client
from .config import get_config

_anon_client: Optional[Client] = None
_service_client: Optional[Client] = None


def is_supabase_configured(use_service_role: bool = False) -> bool:
    """Check if the required Supabase environment variables are present.

    Args:
        use_service_role: If True, checks for SERVICE_ROLE_KEY. Otherwise checks ANON_KEY.

    Returns:
        bool: True if URL and required key are configured.
    """
    config = get_config()
    url = getattr(config, 'SUPABASE_URL', '').strip()
    if not url:
        return False

    if use_service_role:
        key = getattr(config, 'SUPABASE_SERVICE_ROLE_KEY', '').strip()
    else:
        key = getattr(config, 'SUPABASE_ANON_KEY', '').strip()

    return bool(key)


def get_supabase_config_status() -> Dict[str, str]:
    """Safe status report for Supabase configuration without exposing secrets.

    Returns:
        Dict[str, str]: Dictionary mapping config names to 'configured' or 'missing'.
    """
    config = get_config()
    return {
        "url": "configured" if getattr(config, 'SUPABASE_URL', '').strip() else "missing",
        "anon_key": "configured" if getattr(config, 'SUPABASE_ANON_KEY', '').strip() else "missing",
        "service_role_key": "configured" if getattr(config, 'SUPABASE_SERVICE_ROLE_KEY', '').strip() else "missing",
    }


def get_supabase_client(use_service_role: bool = False) -> Client:
    """Retrieve or initialize the centralized Supabase client.

    Args:
        use_service_role: If True, returns a client initialized with SUPABASE_SERVICE_ROLE_KEY.
                         This is strictly for server-side trusted operations.
                         If False, returns a client initialized with SUPABASE_ANON_KEY.

    Returns:
        Client: Initialized Supabase client instance.

    Raises:
        ValueError: If Supabase URL or the required key is missing or not configured.
    """
    global _anon_client, _service_client

    if use_service_role and _service_client is not None:
        return _service_client
    if not use_service_role and _anon_client is not None:
        return _anon_client

    config = get_config()
    url = getattr(config, 'SUPABASE_URL', '').strip()

    if not url:
        raise ValueError("Supabase is not configured: SUPABASE_URL is missing.")

    if use_service_role:
        key = getattr(config, 'SUPABASE_SERVICE_ROLE_KEY', '').strip()
        if not key:
            raise ValueError("Supabase is not configured: SUPABASE_SERVICE_ROLE_KEY is missing.")
        _service_client = create_client(url, key)
        return _service_client
    else:
        key = getattr(config, 'SUPABASE_ANON_KEY', '').strip()
        if not key:
            raise ValueError("Supabase is not configured: SUPABASE_ANON_KEY is missing.")
        _anon_client = create_client(url, key)
        return _anon_client
