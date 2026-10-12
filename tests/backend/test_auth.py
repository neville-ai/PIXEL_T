import pytest
from unittest.mock import patch, MagicMock
from flask import Blueprint, jsonify, g
from app.core.auth import require_auth

# Create a test blueprint using require_auth to test the decorator in isolation
test_auth_bp = Blueprint('test_auth', __name__)


@test_auth_bp.route('/api/test-protected', methods=['GET'])
@require_auth
def protected_endpoint():
    return jsonify({
        "success": True,
        "data": {
            "user_id": g.current_user["id"],
            "email": g.current_user["email"],
        }
    }), 200


@pytest.fixture
def auth_client(app):
    """Register test_auth_bp on the test app and return test client."""
    if 'test_auth' not in app.blueprints:
        app.register_blueprint(test_auth_bp)
    return app.test_client()


def test_missing_authorization_header(auth_client):
    """Requests without Authorization header must return 401 UNAUTHORIZED."""
    response = auth_client.get('/api/test-protected')
    assert response.status_code == 401
    data = response.get_json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"
    assert "Missing Authorization header" in data["error"]["message"]


def test_malformed_authorization_header(auth_client):
    """Malformed headers (e.g. Basic, missing Bearer, extra parts) must return 401."""
    # Case 1: Basic auth
    res1 = auth_client.get(
        '/api/test-protected',
        headers={"Authorization": "Basic dXNlcjpwYXNz"}
    )
    assert res1.status_code == 401
    assert res1.get_json()["error"]["code"] == "UNAUTHORIZED"

    # Case 2: Only Bearer without token
    res2 = auth_client.get(
        '/api/test-protected',
        headers={"Authorization": "Bearer"}
    )
    assert res2.status_code == 401
    assert res2.get_json()["error"]["code"] == "UNAUTHORIZED"


def test_invalid_token(auth_client):
    """Invalid or expired Supabase tokens must return 401 UNAUTHORIZED without leaking the token."""
    dummy_token = "invalid-or-expired-token-xyz"

    with patch('app.core.auth.is_supabase_configured', return_value=True), \
         patch('app.core.auth.get_supabase_client') as mock_get_client:

        mock_supabase = MagicMock()
        mock_supabase.auth.get_user.side_effect = Exception("JWT expired or invalid")
        mock_get_client.return_value = mock_supabase

        response = auth_client.get(
            '/api/test-protected',
            headers={"Authorization": f"Bearer {dummy_token}"}
        )
        assert response.status_code == 401
        data = response.get_json()
        assert data["success"] is False
        assert data["error"]["code"] == "UNAUTHORIZED"
        # Ensure the token itself is never reflected in the error response
        assert dummy_token not in str(data)


def test_valid_token_sets_user_context(auth_client):
    """Valid token establishes g.current_user and returns HTTP 200."""
    valid_token = "valid-mocked-token-abc"

    mock_user = MagicMock()
    mock_user.id = "user-uuid-12345"
    mock_user.email = "dokter@rumah-sakit.id"
    mock_user.role = "authenticated"

    mock_response = MagicMock()
    mock_response.user = mock_user

    with patch('app.core.auth.is_supabase_configured', return_value=True), \
         patch('app.core.auth.get_supabase_client') as mock_get_client:

        mock_supabase = MagicMock()
        mock_supabase.auth.get_user.return_value = mock_response
        mock_get_client.return_value = mock_supabase

        response = auth_client.get(
            '/api/test-protected',
            headers={"Authorization": f"Bearer {valid_token}"}
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["user_id"] == "user-uuid-12345"
        assert data["data"]["email"] == "dokter@rumah-sakit.id"


def test_health_endpoint_remains_public(auth_client):
    """The health endpoint must remain public without requiring Authorization."""
    response = auth_client.get('/api/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["status"] == "ok"
