from functools import wraps
from flask import request, g
from .errors import APIError
from .supabase import get_supabase_client, is_supabase_configured


def require_auth(f):
    """Decorator to enforce Supabase Bearer token authentication on Flask endpoints.

    Verifies the token via Supabase Auth and establishes authenticated user context in
    `g.current_user` and `request.user`.
    Returns HTTP 401 with standard error envelope if token is missing, malformed, or invalid.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '').strip()
        if not auth_header:
            raise APIError(
                code="UNAUTHORIZED",
                message="Missing Authorization header. Expected 'Bearer <token>'.",
                status_code=401,
            )

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            raise APIError(
                code="UNAUTHORIZED",
                message="Malformed Authorization header. Format must be 'Bearer <token>'.",
                status_code=401,
            )

        token = parts[1].strip()
        if not token:
            raise APIError(
                code="UNAUTHORIZED",
                message="Authentication token is empty.",
                status_code=401,
            )

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

            # Establish authenticated user context (never store password or tokens)
            current_user = {
                "id": str(user.id),
                "email": getattr(user, 'email', None),
                "role": getattr(user, 'role', 'authenticated'),
            }
            g.current_user = current_user
            request.user = current_user

        except APIError:
            raise
        except Exception:
            # Never leak token or raw exception in response
            raise APIError(
                code="UNAUTHORIZED",
                message="Invalid or expired authentication token.",
                status_code=401,
            )

        return f(*args, **kwargs)

    return decorated
