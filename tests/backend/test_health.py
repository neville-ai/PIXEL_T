def test_health_check_success(client):
    """Test that GET /api/health returns 200 and success envelope."""
    response = client.get('/api/health')
    assert response.status_code == 200

    data = response.get_json()
    assert data == {
        "success": True,
        "data": {
            "status": "ok"
        }
    }


def test_health_check_no_auth_required(client):
    """Test that GET /api/health is publicly accessible without Authorization header."""
    response = client.get('/api/health', headers={})
    assert response.status_code == 200
    assert response.get_json()["success"] is True


def test_error_handler_404(client):
    """Test that unknown endpoints return standard error envelope with 404."""
    response = client.get('/api/unregistered_endpoint')
    assert response.status_code == 404

    data = response.get_json()
    assert data["success"] is False
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
    assert "message" in data["error"]


def test_error_handler_405_method_not_allowed(client):
    """Test that calling health endpoint with POST returns standard error envelope with 405."""
    response = client.post('/api/health')
    assert response.status_code == 405

    data = response.get_json()
    assert data["success"] is False
    assert "error" in data
    assert data["error"]["code"] == "METHOD_NOT_ALLOWED"
