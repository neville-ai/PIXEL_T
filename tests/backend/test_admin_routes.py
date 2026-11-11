"""Endpoint tests for the admin approve/reject routes.

These exercise the real Flask route + `require_admin` decorator + controller,
while the AdminService is replaced with a fake so no database is touched.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

import src.core.auth as auth_module
import src.routes.admin as admin_routes
from src.core.errors import APIError


def _make_user(token):
    if token == 'admin-token':
        return SimpleNamespace(
            user=SimpleNamespace(
                id='admin-1',
                email='admin@test.com',
                app_metadata={'role': 'admin'},
            )
        )
    if token == 'doctor-token':
        return SimpleNamespace(
            user=SimpleNamespace(
                id='doc-user-1',
                email='doctor@test.com',
                app_metadata={'role': 'authenticated'},
            )
        )
    raise Exception('invalid token')


@pytest.fixture
def admin_api_client(client, monkeypatch):
    monkeypatch.setattr(auth_module, 'is_supabase_configured', lambda: True)
    auth_client = MagicMock()
    auth_client.auth.get_user.side_effect = _make_user
    monkeypatch.setattr(auth_module, 'get_supabase_client', lambda **kwargs: auth_client)
    return client


class FakeAdminService:
    def __init__(self, fail_approve=False):
        self.fail_approve = fail_approve
        self.approved = []
        self.rejected = []

    def approve_doctor(self, doctor_id, approved_by_user_id):
        if self.fail_approve:
            raise APIError(
                code='UPDATE_FAILED',
                message='Gagal menyetujui dokter. Perubahan database tidak dapat disimpan.',
                status_code=500,
            )
        self.approved.append((doctor_id, approved_by_user_id))
        return {'id': doctor_id, 'account_status': 'approved'}

    def reject_doctor(self, doctor_id, approved_by_user_id, reason=''):
        self.rejected.append((doctor_id, approved_by_user_id, reason))
        return {'id': doctor_id, 'account_status': 'rejected', 'rejection_reason': reason or None}


@pytest.fixture
def fake_service(monkeypatch):
    service = FakeAdminService()
    monkeypatch.setattr(admin_routes.controller, 'service', service)
    return service


def _headers(token):
    return {'Authorization': f'Bearer {token}'}


# ---------------------------------------------------------------------------
# Authorization
# ---------------------------------------------------------------------------


def test_approve_requires_authentication(admin_api_client):
    response = admin_api_client.post('/api/admin/doctors/doc-1/approve')

    assert response.status_code == 401
    assert response.get_json()['error']['code'] == 'UNAUTHORIZED'


def test_approve_rejects_invalid_token(admin_api_client):
    response = admin_api_client.post(
        '/api/admin/doctors/doc-1/approve',
        headers=_headers('bogus-token'),
    )

    assert response.status_code == 401
    assert response.get_json()['error']['code'] == 'UNAUTHORIZED'


def test_approve_forbidden_for_doctor(admin_api_client):
    response = admin_api_client.post(
        '/api/admin/doctors/doc-1/approve',
        headers=_headers('doctor-token'),
    )

    assert response.status_code == 403
    assert response.get_json()['error']['code'] == 'FORBIDDEN'


def test_reject_forbidden_for_doctor(admin_api_client):
    response = admin_api_client.post(
        '/api/admin/doctors/doc-1/reject',
        headers=_headers('doctor-token'),
    )

    assert response.status_code == 403
    assert response.get_json()['error']['code'] == 'FORBIDDEN'


# ---------------------------------------------------------------------------
# Admin actions
# ---------------------------------------------------------------------------


def test_approve_admin_uses_authenticated_admin_id(admin_api_client, fake_service):
    response = admin_api_client.post(
        '/api/admin/doctors/doc-1/approve',
        headers=_headers('admin-token'),
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload['success'] is True
    assert payload['data']['account_status'] == 'approved'
    # approved_by must come from the verified token, never from the client body.
    assert fake_service.approved == [('doc-1', 'admin-1')]


def test_approve_service_failure_returns_500_update_failed(admin_api_client, monkeypatch):
    failing = FakeAdminService(fail_approve=True)
    monkeypatch.setattr(admin_routes.controller, 'service', failing)

    response = admin_api_client.post(
        '/api/admin/doctors/doc-1/approve',
        headers=_headers('admin-token'),
    )

    assert response.status_code == 500
    payload = response.get_json()
    assert payload['success'] is False
    assert payload['error']['code'] == 'UPDATE_FAILED'


def test_reject_admin_still_works(admin_api_client, fake_service):
    response = admin_api_client.post(
        '/api/admin/doctors/doc-1/reject',
        headers=_headers('admin-token'),
        json={'reason': 'Dokumen tidak lengkap'},
    )

    assert response.status_code == 200
    payload = response.get_json()
    assert payload['success'] is True
    assert payload['data']['account_status'] == 'rejected'
    assert fake_service.rejected == [('doc-1', 'admin-1', 'Dokumen tidak lengkap')]
