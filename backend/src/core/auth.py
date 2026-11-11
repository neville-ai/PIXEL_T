from functools import wraps
from flask import request, g
from .errors import APIError
from src.config.supabase import get_supabase_client, is_supabase_configured
import logging


logger = logging.getLogger(__name__)


def _extract_bearer_token(
    missing_message="Missing Authorization header.",
    malformed_message="Malformed Authorization header.",
):
    """Ekstrak & validasi format header 'Authorization: Bearer <token>'.

    Pesan error dapat di-override per decorator tanpa mengubah kode/status yang
    dikembalikan ke klien. Tidak mencetak token.
    """
    auth_header = request.headers.get('Authorization', '').strip()
    if not auth_header:
        raise APIError(
            code="UNAUTHORIZED",
            message=missing_message,
            status_code=401,
        )

    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        raise APIError(
            code="UNAUTHORIZED",
            message=malformed_message,
            status_code=401,
        )

    token = parts[1].strip()
    if not token:
        raise APIError(
            code="UNAUTHORIZED",
            message="Authentication token is empty.",
            status_code=401,
        )
    return token


def _resolve_authenticated_user(token: str):
    """Verifikasi token Bearer ke Supabase dan kembalikan objek user.

    Memeriksa ketersediaan Supabase, memanggil `auth.get_user`, dan memvalidasi
    keberadaan user. Semua kegagalan diubah ke `APIError` standar tanpa bocorkan
    token atau detail exception ke response klien.
    """
    if not is_supabase_configured():
        raise APIError(
            code="UNAUTHORIZED",
            message="Authentication service is temporarily unavailable.",
            status_code=401,
        )

    try:
        client = get_supabase_client(use_service_role=False)
        response = client.auth.get_user(token)
        user = getattr(response, 'user', None)

        if not user or not getattr(user, 'id', None):
            raise APIError(
                code="UNAUTHORIZED",
                message="Invalid or expired authentication token.",
                status_code=401,
            )

        return user
    except APIError:
        raise
    except Exception:
        # Never leak token or raw exception in response
        raise APIError(
            code="UNAUTHORIZED",
            message="Invalid or expired authentication token.",
            status_code=401,
        )


def require_auth(f):
    """Decorator to enforce Supabase Bearer token authentication on Flask endpoints.

    Verifies the token via Supabase Auth and establishes authenticated user context in
    `g.current_user` and `request.user`.
    Returns HTTP 401 with standard error envelope if token is missing, malformed, or invalid.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_bearer_token(
            missing_message="Missing Authorization header. Expected 'Bearer <token>'.",
            malformed_message="Malformed Authorization header. Format must be 'Bearer <token>'.",
        )
        user = _resolve_authenticated_user(token)

        # Establish authenticated user context (never store password or tokens)
        current_user = {
            "id": str(user.id),
            "email": getattr(user, 'email', None),
            "role": getattr(user, 'role', 'authenticated'),
        }
        g.current_user = current_user
        request.user = current_user

        return f(*args, **kwargs)

    return decorated


def require_admin(f):
    """Decorator that enforces: authenticated + admin role.

    Admin identity is determined from Supabase app_metadata.role, which is
    server-write-only (set via the Admin API using the service-role key).
    Unlike user_metadata, app_metadata cannot be modified by the end user
    through any client-side API, preventing privilege escalation.

    Returns HTTP 403 if the user is authenticated but not an admin.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_bearer_token()
        try:
            user = _resolve_authenticated_user(token)

            # Read admin role from app_metadata (server-write-only), NOT
            # user_metadata (user-writable via updateUser).
            app_metadata = getattr(user, 'app_metadata', {}) or {}
            admin_role = app_metadata.get('role', '')

            if admin_role != 'admin':
                raise APIError(
                    code="FORBIDDEN",
                    message="Access denied. Admin privileges required.",
                    status_code=403,
                )

            current_user = {
                "id": str(user.id),
                "email": getattr(user, 'email', None),
                "role": "admin",
            }
            g.current_user = current_user
            request.user = current_user

        except APIError:
            raise
        except Exception:
            raise APIError(
                code="UNAUTHORIZED",
                message="Invalid or expired authentication token.",
                status_code=401,
            )

        return f(*args, **kwargs)

    return decorated


def require_approved_doctor(f):
    """Decorator: authenticated + doctor role + approved account status."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = _extract_bearer_token()
        try:
            user = _resolve_authenticated_user(token)

            user_id = str(user.id)
            profile_info = _get_user_role_and_status(user_id)
            role = profile_info.get('role')
            status = profile_info.get('account_status')

            # Admin users do not have a doctor_profile row; deny clinical access
            if role is None:
                raise APIError(
                    code="FORBIDDEN",
                    message="Access denied. This feature requires a doctor account.",
                    status_code=403,
                )

            if status != 'approved':
                if status == 'pending':
                    raise APIError(
                        code="ACCOUNT_PENDING",
                        message="Your account is awaiting administrator approval.",
                        status_code=403,
                    )
                if status == 'rejected':
                    raise APIError(
                        code="ACCOUNT_REJECTED",
                        message="Your registration has been rejected. Please contact your hospital administrator.",
                        status_code=403,
                    )
                raise APIError(
                    code="FORBIDDEN",
                    message="Your account does not have the required approval status.",
                    status_code=403,
                )

            current_user = {
                "id": user_id,
                "email": getattr(user, 'email', None),
                "role": "doctor",
                "account_status": "approved",
            }
            g.current_user = current_user
            request.user = current_user

        except APIError:
            raise
        except Exception:
            raise APIError(
                code="UNAUTHORIZED",
                message="Invalid or expired authentication token.",
                status_code=401,
            )

        return f(*args, **kwargs)

    return decorated


def _get_user_role_and_status(user_id: str):
    """Look up a user's role and account_status from doctor_profiles.

    Returns a dict with keys:
      - role: 'doctor' or None (admin has no doctor_profile row)
      - account_status: 'pending', 'approved', 'rejected', or None

    Used by login flow and protected route checks.
    """
    try:
        client = get_supabase_client(use_service_role=True)
        result = (
            client.table('doctor_profiles')
            .select('role, account_status')
            .eq('user_id', user_id)
            .maybe_single()
            .execute()
        )
        if result.data:
            return {
                'role': result.data.get('role', 'doctor'),
                'account_status': result.data.get('account_status', 'pending'),
            }
    except Exception:
        # Never leak details, but keep a server-side trace for debugging.
        logger.exception("Failed to resolve doctor role/status for user %s", user_id)
    return {'role': None, 'account_status': None}
