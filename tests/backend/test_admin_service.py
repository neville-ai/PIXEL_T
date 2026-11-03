"""Tests for backend/app/services/admin_service.py.

Covers the doctor registration flows used by the Admin Dashboard:
- list_doctors, get_statistics, approve_doctor, reject_doctor, _get_user_email.

All tests mock the Supabase client so no real network/database call is made.
"""
from types import SimpleNamespace

import pytest

from postgrest.exceptions import APIError as PostgrestAPIError

from app.services.admin_service import AdminService
from app.core.errors import APIError


LIST_DOCTORS_SELECT = (
    'id, user_id, full_name, hospital, primary_specialty, account_status, '
    'created_at, approved_at, rejection_reason'
)


class FakeQuery:
    """Minimal Supabase query builder stub used by AdminService."""

    def __init__(self, client):
        self._client = client
        self._select = None
        self._update_data = None

    def select(self, columns):
        self._select = columns
        self._client.select_calls.append(columns)
        return self

    def eq(self, _column, _value):
        return self

    def maybe_single(self):
        # The real postgrest-py 2.x SDK only exposes snake_case `maybe_single`.
        # Intentionally NOT named `maybeSingle` so that a regression to the
        # non-existent camelCase method fails these tests instead of crashing
        # in production with an AttributeError (HTTP 500).
        return self

    def update(self, data):
        self._update_data = data
        self._client.update_calls.append(data)
        return self

    def execute(self):
        if self._client.fail_query:
            raise RuntimeError("database connection failed")
        if self._update_data is not None:
            # Mirrors the real postgrest-py behaviour:
            # - failure raises PostgrestAPIError
            # - success returns an APIResponse that has ONLY `data`/`count`,
            #   i.e. NO `.error` attribute.
            if self._client.fail_update:
                raise PostgrestAPIError(
                    self._client.update_error
                    or {"message": "db write failed", "code": "XX000"}
                )
            if self._client.fail_no_rows:
                # UPDATE matched zero rows (e.g. concurrent status change).
                return SimpleNamespace(data=[])
            return SimpleNamespace(data=[dict(self._update_data)])
        response = self._client.responses.get(self._select)
        if response is None:
            return SimpleNamespace(data=[], error=None)
        return SimpleNamespace(data=response.get("data", []), error=response.get("error"))


class FakeClient:
    """Supabase service-role client stub."""

    def __init__(self, responses=None, fail_query=False, fail_update=False, fail_no_rows=False, auth_email_by_id=None):
        self.responses = responses or {}
        self.fail_query = fail_query
        self.fail_update = fail_update
        self.fail_no_rows = fail_no_rows
        self.update_error = None  # optional custom PostgREST error payload
        self.select_calls = []
        self.update_calls = []
        self.auth = SimpleNamespace(
            admin=SimpleNamespace(get_user_by_id=self._get_user_by_id)
        )
        self._auth_email_by_id = auth_email_by_id or {}

    def _get_user_by_id(self, user_id):
        if user_id not in self._auth_email_by_id:
            raise RuntimeError("user not found")
        return SimpleNamespace(user=SimpleNamespace(email=self._auth_email_by_id[user_id], id=user_id))

    def table(self, _name):
        return FakeQuery(self)


@pytest.fixture
def client():
    return FakeClient(
        responses={
            LIST_DOCTORS_SELECT: {
                'data': [
                    {
                        'id': 'doc-1',
                        'user_id': 'user-1',
                        'full_name': 'dr. Alice',
                        'hospital': 'RS A',
                        'primary_specialty': 'Patologi',
                        'account_status': 'pending',
                        'created_at': '2026-01-01T00:00:00Z',
                    },
                    {
                        'id': 'doc-2',
                        'user_id': 'user-2',
                        'full_name': 'dr. Budi',
                        'hospital': 'RS B',
                        'primary_specialty': 'Jantung',
                        'account_status': 'approved',
                        'created_at': '2026-01-02T00:00:00Z',
                    },
                    {
                        'id': 'doc-3',
                        'user_id': 'user-3',
                        'full_name': 'dr. Cici',
                        'hospital': 'RS C',
                        'primary_specialty': 'Kulit',
                        'account_status': 'rejected',
                        'created_at': '2026-01-03T00:00:00Z',
                    },
                ]
            },
            'account_status': {
                'data': [
                    {'account_status': 'pending'},
                    {'account_status': 'pending'},
                    {'account_status': 'approved'},
                    {'account_status': 'rejected'},
                ]
            },
            'id, account_status, user_id': {
                'data': {'id': 'doc-1', 'account_status': 'pending', 'user_id': 'user-1'}
            },
            'id, account_status': {
                'data': {'id': 'doc-1', 'account_status': 'pending'}
            },
            '*': {
                'data': {
                    'id': 'doc-1',
                    'user_id': 'user-1',
                    'full_name': 'dr. Alice',
                    'hospital': 'RS A',
                    'account_status': 'pending',
                }
            },
        },
        auth_email_by_id={'user-1': 'alice@rs-a.com'},
    )


def make_service(client):
    return AdminService(client=client)


# ---------------------------------------------------------------------------
# list_doctors
# ---------------------------------------------------------------------------


def test_list_doctors_does_not_select_nonexistent_email_column(client):
    """Regression test: selecting a missing `email` column causes HTTP 500."""
    service = make_service(client)
    service.list_doctors()

    assert client.select_calls, "list_doctors should issue a select query"
    assert 'email' not in client.select_calls[0]


def test_list_doctors_returns_enriched_rows_with_email(client):
    service = make_service(client)
    rows = service.list_doctors()

    assert len(rows) == 3
    pending = [r for r in rows if r['account_status'] == 'pending'][0]
    assert pending['user_id'] == 'user-1'
    assert pending['email'] == 'alice@rs-a.com'
    assert pending['full_name'] == 'dr. Alice'


def test_list_doctors_filters_by_status(client):
    service = make_service(client)
    pending = service.list_doctors(status='pending')

    assert len(pending) == 1
    assert pending[0]['account_status'] == 'pending'


# ---------------------------------------------------------------------------
# get_statistics
# ---------------------------------------------------------------------------


def test_get_statistics_counts_all_statuses(client):
    service = make_service(client)
    stats = service.get_statistics()

    assert stats == {
        'total': 4,
        'pending': 2,
        'approved': 1,
        'rejected': 1,
    }


# ---------------------------------------------------------------------------
# approve_doctor
# ---------------------------------------------------------------------------


def test_approve_doctor_requires_pending_status(client):
    client.responses['id, account_status, user_id'] = {
        'data': {'id': 'doc-2', 'account_status': 'approved', 'user_id': 'user-2'}
    }
    service = make_service(client)

    with pytest.raises(APIError) as excinfo:
        service.approve_doctor('doc-2', approved_by_user_id='admin-1')

    assert excinfo.value.code == 'INVALID_STATUS'
    assert excinfo.value.status_code == 400


def test_approve_doctor_unknown_id_returns_404(client):
    client.responses['id, account_status, user_id'] = {'data': None}
    service = make_service(client)

    with pytest.raises(APIError) as excinfo:
        service.approve_doctor('does-not-exist', approved_by_user_id='admin-1')

    assert excinfo.value.code == 'NOT_FOUND'
    assert excinfo.value.status_code == 404


def test_approve_doctor_updates_fields(client):
    client.responses['id, account_status, user_id'] = {
        'data': {'id': 'doc-1', 'account_status': 'pending', 'user_id': 'user-1'}
    }
    client.responses['*'] = {
        'data': {
            'id': 'doc-1',
            'user_id': 'user-1',
            'full_name': 'dr. Alice',
            'hospital': 'RS A',
            'account_status': 'approved',
        }
    }
    service = make_service(client)

    doctor = service.approve_doctor('doc-1', approved_by_user_id='admin-1')

    assert doctor['account_status'] == 'approved'
    assert doctor['email'] == 'alice@rs-a.com'
    assert client.update_calls[0]['account_status'] == 'approved'
    assert client.update_calls[0]['approved_by'] == 'admin-1'


def test_approve_doctor_update_zero_rows_returns_conflict(client):
    """Update must not return HTTP 200 when no row actually changed."""
    client.responses['id, account_status, user_id'] = {
        'data': {'id': 'doc-1', 'account_status': 'pending', 'user_id': 'user-1'}
    }
    client.fail_no_rows = True
    service = make_service(client)

    with pytest.raises(APIError) as excinfo:
        service.approve_doctor('doc-1', approved_by_user_id='admin-1')

    assert excinfo.value.code == 'UPDATE_CONFLICT'
    assert excinfo.value.status_code == 409


def test_reject_doctor_update_zero_rows_returns_conflict(client):
    client.responses['id, account_status'] = {
        'data': {'id': 'doc-1', 'account_status': 'pending'}
    }
    client.fail_no_rows = True
    service = make_service(client)

    with pytest.raises(APIError) as excinfo:
        service.reject_doctor('doc-1', approved_by_user_id='admin-1')

    assert excinfo.value.code == 'UPDATE_CONFLICT'
    assert excinfo.value.status_code == 409


def test_approve_doctor_foreign_key_error_returns_update_failed(client):
    """A Postgres FK violation (approved_by -> auth.users) must surface as
    APIError UPDATE_FAILED, never as an unhandled HTTP 500."""
    client.responses['id, account_status, user_id'] = {
        'data': {'id': 'doc-1', 'account_status': 'pending', 'user_id': 'user-1'}
    }
    client.fail_update = True
    client.update_error = {
        'message': (
            'insert or update on table "doctor_profiles" violates foreign key '
            'constraint "doctor_profiles_approved_by_fkey"'
        ),
        'code': '23503',
    }
    service = make_service(client)

    with pytest.raises(APIError) as excinfo:
        service.approve_doctor('doc-1', approved_by_user_id='not-a-real-admin-id')

    assert excinfo.value.code == 'UPDATE_FAILED'
    assert excinfo.value.status_code == 500


# ---------------------------------------------------------------------------
# reject_doctor
# ---------------------------------------------------------------------------


def test_reject_doctor_sets_rejected(client):
    client.responses['id, account_status'] = {
        'data': {'id': 'doc-1', 'account_status': 'pending'}
    }
    client.responses['*'] = {
        'data': {
            'id': 'doc-1',
            'user_id': 'user-1',
            'account_status': 'rejected',
        }
    }
    service = make_service(client)

    doctor = service.reject_doctor('doc-1', approved_by_user_id='admin-1', reason='tidak layak')

    assert doctor['account_status'] == 'rejected'
    assert client.update_calls[0]['account_status'] == 'rejected'
    assert client.update_calls[0]['rejection_reason'] == 'tidak layak'


def test_reject_doctor_requires_pending_status(client):
    client.responses['id, account_status'] = {
        'data': {'id': 'doc-2', 'account_status': 'approved'}
    }
    service = make_service(client)

    with pytest.raises(APIError) as excinfo:
        service.reject_doctor('doc-2', approved_by_user_id='admin-1')

    assert excinfo.value.code == 'INVALID_STATUS'
    assert excinfo.value.status_code == 400


# ---------------------------------------------------------------------------
# _get_user_email
# ---------------------------------------------------------------------------


def test_get_user_email_returns_email(client):
    service = make_service(client)
    assert service._get_user_email('user-1') == 'alice@rs-a.com'


def test_get_user_email_handles_missing_user(client):
    service = make_service(client)
    assert service._get_user_email('unknown-user') == ''


def test_get_user_email_handles_empty_id(client):
    service = make_service(client)
    assert service._get_user_email('') == ''

# ---------------------------------------------------------------------------
# Regression tests for the HTTP 500 on Approve/Reject
# ---------------------------------------------------------------------------


def test_approve_doctor_update_success_returns_without_error_attribute(client):
    """Regression: `execute()` on update returns an APIResponse that has NO
    `.error` attribute. Accessing `.error` used to raise AttributeError -> 500."""
    client.responses['id, account_status, user_id'] = {
        'data': {'id': 'doc-1', 'account_status': 'pending', 'user_id': 'user-1'}
    }
    client.responses['*'] = {
        'data': {
            'id': 'doc-1',
            'user_id': 'user-1',
            'full_name': 'dr. Kharis',
            'hospital': 'RS A',
            'account_status': 'approved',
        }
    }
    service = make_service(client)

    doctor = service.approve_doctor('doc-1', approved_by_user_id='admin-1')

    assert doctor['account_status'] == 'approved'


def test_approve_doctor_persists_approval_metadata(client):
    captured = {}
    original_execute = FakeQuery.execute

    def patched_execute(self):
        result = original_execute(self)
        if self._update_data is not None:
            captured.update(self._update_data)
        return result

    FakeQuery.execute = patched_execute
    try:
        client.responses['id, account_status, user_id'] = {
            'data': {'id': 'doc-1', 'account_status': 'pending', 'user_id': 'user-1'}
        }
        client.responses['*'] = {
            'data': {'id': 'doc-1', 'user_id': 'user-1', 'account_status': 'approved'}
        }
        service = make_service(client)
        service.approve_doctor('doc-1', approved_by_user_id='admin-1')

        assert captured.get('account_status') == 'approved'
        assert captured.get('approved_by') == 'admin-1'
        assert captured.get('approved_at') is not None
    finally:
        FakeQuery.execute = original_execute


def test_approve_doctor_database_error_returns_update_failed(client):
    """Database failure during update must surface as APIError UPDATE_FAILED,
    not an unhandled 500."""
    client.fail_update = True
    client.responses['id, account_status, user_id'] = {
        'data': {'id': 'doc-1', 'account_status': 'pending', 'user_id': 'user-1'}
    }
    service = make_service(client)

    with pytest.raises(APIError) as excinfo:
        service.approve_doctor('doc-1', approved_by_user_id='admin-1')

    assert excinfo.value.code == 'UPDATE_FAILED'
    assert excinfo.value.status_code == 500


def test_reject_doctor_database_error_returns_update_failed(client):
    client.fail_update = True
    client.responses['id, account_status'] = {
        'data': {'id': 'doc-1', 'account_status': 'pending'}
    }
    service = make_service(client)

    with pytest.raises(APIError) as excinfo:
        service.reject_doctor('doc-1', approved_by_user_id='admin-1')

    assert excinfo.value.code == 'UPDATE_FAILED'
    assert excinfo.value.status_code == 500
