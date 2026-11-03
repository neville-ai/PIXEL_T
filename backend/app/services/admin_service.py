import logging
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from postgrest.exceptions import APIError as PostgrestAPIError
from app.core.supabase import get_supabase_client
from app.core.errors import APIError


logger = logging.getLogger(__name__)


class AdminService:
    """Service layer for admin operations on doctor registrations.

    All methods use the service-role Supabase client to bypass RLS,
    since admin operations are enforced via backend auth decorators.
    """

    def __init__(self, client=None):
        self._client = client

    def _get_client(self):
        if self._client is not None:
            return self._client
        return get_supabase_client(use_service_role=True)

    def list_doctors(self, status: Optional[str] = None) -> list[Dict[str, Any]]:
        """Return a list of doctor profiles, optionally filtered by account_status.

        Excludes the `education`, `experience`, and `bio` columns from the
        response to keep the listing lightweight.
        """
        client = self._get_client()
        try:
            # NOTE: `email` is NOT a column on doctor_profiles. It lives in
            # auth.users and is resolved separately via `_get_user_email`.
            # Selecting a non-existent column makes PostgREST return an error
            # (HTTP 500), so it must never appear in this select list.
            query = client.table('doctor_profiles').select(
                'id, user_id, full_name, hospital, primary_specialty, account_status, created_at, approved_at, rejection_reason'
            )

            result = query.execute()
            profiles = result.data or []
        except Exception as e:
            # Provide a clear error when migration 007 has not been applied.
            # The query fails because account_status/approved_at/rejection_reason
            # columns do not exist yet.
            err_msg = str(e).lower()
            if 'account_status' in err_msg or 'approved_at' in err_msg or 'rejection_reason' in err_msg:
                raise APIError(
                    code="SCHEMA_NOT_APPLIED",
                    message=(
                        "Tabel doctor_profiles belum memiliki kolom status akun. "
                        "Hubungi administrator sistem untuk menjalankan Migration 007 pada database."
                    ),
                    status_code=500,
                )
            raise APIError(
                code="DATABASE_ERROR",
                message="Gagal mengambil data pendaftaran dokter.",
                status_code=500,
            )

        # Enrich with email from auth.users
        enriched = []
        for row in profiles:
            user_id = row.get('user_id')
            email = self._get_user_email(user_id)
            enriched.append({
                'id': row.get('id'),
                'user_id': user_id,
                'full_name': row.get('full_name', ''),
                'email': email,
                'hospital': row.get('hospital'),
                'primary_specialty': row.get('primary_specialty'),
                'account_status': row.get('account_status', 'pending'),
                'created_at': row.get('created_at'),
                'approved_at': row.get('approved_at'),
                'rejection_reason': row.get('rejection_reason'),
            })

        if status:
            enriched = [p for p in enriched if p['account_status'] == status]

        return enriched

    def get_doctor(self, doctor_id: str) -> Optional[Dict[str, Any]]:
        """Return a single doctor profile with full details."""
        client = self._get_client()
        result = (
            client.table('doctor_profiles')
            .select('*')
            .eq('id', doctor_id)
            .maybeSingle()
            .execute()
        )
        if not result.data:
            return None

        row = result.data
        return {
            'id': row.get('id'),
            'user_id': row.get('user_id'),
            'full_name': row.get('full_name', ''),
            'email': self._get_user_email(row.get('user_id')),
            'hospital': row.get('hospital'),
            'primary_specialty': row.get('primary_specialty'),
            'department': row.get('department'),
            'clinical_role': row.get('clinical_role'),
            'years_experience': row.get('years_experience'),
            'phone': row.get('phone'),
            'account_status': row.get('account_status', 'pending'),
            'created_at': row.get('created_at'),
            'approved_at': row.get('approved_at'),
            'rejection_reason': row.get('rejection_reason'),
            'is_verified': row.get('is_verified', False),
        }

    def approve_doctor(self, doctor_id: str, approved_by_user_id: str) -> Dict[str, Any]:
        """Change a doctor's account_status to 'approved'.

        Args:
            doctor_id: The doctor_profiles.id to approve.
            approved_by_user_id: The auth.users.id of the admin performing the action.

        Returns:
            The updated profile dict.

        Raises:
            APIError: If the doctor does not exist, is not pending, or the update fails.
        """
        client = self._get_client()

        # Fetch current profile
        fetch_result = (
            client.table('doctor_profiles')
            .select('id, account_status, user_id')
            .eq('id', doctor_id)
            .maybeSingle()
            .execute()
        )
        if not fetch_result.data:
            raise APIError(
                code="NOT_FOUND",
                message="Doctor profile not found.",
                status_code=404,
            )

        current_status = fetch_result.data.get('account_status')
        if current_status != 'pending':
            raise APIError(
                code="INVALID_STATUS",
                message=f"Cannot approve a doctor with status '{current_status}'. Only pending accounts can be approved.",
                status_code=400,
            )

        # Update.
        # NOTE: postgrest-py's execute() returns an APIResponse (fields: data,
        # count) on success and RAISES PostgrestAPIError on failure. It has no
        # `.error` attribute, so the old `update_result.error` check raised
        # AttributeError and produced an HTTP 500 even when the update worked.
        now = datetime.now(timezone.utc).isoformat()
        try:
            (
                client.table('doctor_profiles')
                .update({
                    'account_status': 'approved',
                    'approved_by': approved_by_user_id,
                    'approved_at': now,
                    'rejection_reason': None,
                    'updated_at': now,
                })
                .eq('id', doctor_id)
                .execute()
            )
        except PostgrestAPIError:
            logger.exception("Failed to approve doctor %s", doctor_id)
            raise APIError(
                code="UPDATE_FAILED",
                message="Gagal menyetujui dokter. Perubahan database tidak dapat disimpan.",
                status_code=500,
            )

        return self.get_doctor(doctor_id)

    def reject_doctor(self, doctor_id: str, approved_by_user_id: str, reason: str = '') -> Dict[str, Any]:
        """Change a doctor's account_status to 'rejected'.

        Args:
            doctor_id: The doctor_profiles.id to reject.
            approved_by_user_id: The auth.users.id of the admin performing the action.
            reason: Optional rejection reason.

        Returns:
            The updated profile dict.

        Raises:
            APIError: If the doctor does not exist, is not pending, or the update fails.
        """
        client = self._get_client()

        # Fetch current profile
        fetch_result = (
            client.table('doctor_profiles')
            .select('id, account_status')
            .eq('id', doctor_id)
            .maybeSingle()
            .execute()
        )
        if not fetch_result.data:
            raise APIError(
                code="NOT_FOUND",
                message="Doctor profile not found.",
                status_code=404,
            )

        current_status = fetch_result.data.get('account_status')
        if current_status != 'pending':
            raise APIError(
                code="INVALID_STATUS",
                message=f"Cannot reject a doctor with status '{current_status}'. Only pending accounts can be rejected.",
                status_code=400,
            )

        # Update (see note in approve_doctor: execute() raises on failure and
        # returns a response object without an `.error` attribute on success).
        now = datetime.now(timezone.utc).isoformat()
        try:
            (
                client.table('doctor_profiles')
                .update({
                    'account_status': 'rejected',
                    'approved_by': approved_by_user_id,
                    'approved_at': None,
                    'rejection_reason': reason.strip() if reason else None,
                    'updated_at': now,
                })
                .eq('id', doctor_id)
                .execute()
            )
        except PostgrestAPIError:
            logger.exception("Failed to reject doctor %s", doctor_id)
            raise APIError(
                code="UPDATE_FAILED",
                message="Gagal menolak dokter. Perubahan database tidak dapat disimpan.",
                status_code=500,
            )

        return self.get_doctor(doctor_id)

    def get_statistics(self) -> Dict[str, Any]:
        """Return aggregate statistics for the admin dashboard."""
        client = self._get_client()
        try:
            # Count by status
            all_result = client.table('doctor_profiles').select('account_status').execute()
            profiles = all_result.data or []
        except Exception as e:
            err_msg = str(e).lower()
            if 'account_status' in err_msg:
                raise APIError(
                    code="SCHEMA_NOT_APPLIED",
                    message=(
                        "Tabel doctor_profiles belum memiliki kolom status akun. "
                        "Hubungi administrator sistem untuk menjalankan Migration 007 pada database."
                    ),
                    status_code=500,
                )
            raise APIError(
                code="DATABASE_ERROR",
                message="Gagal menghitung statistik pendaftaran dokter.",
                status_code=500,
            )

        stats = {'total': len(profiles), 'pending': 0, 'approved': 0, 'rejected': 0}
        for p in profiles:
            status = p.get('account_status', 'pending')
            if status == 'pending':
                stats['pending'] += 1
            elif status == 'approved':
                stats['approved'] += 1
            elif status == 'rejected':
                stats['rejected'] += 1

        return stats

    def _get_user_email(self, user_id: Optional[str]) -> str:
        """Fetch email for a user_id from auth.users (service role).

        `auth.admin.get_user_by_id` returns a UserResponse object, with the
        actual user under `.user` — not a bare object with `.email`.
        """
        if not user_id:
            return ''
        try:
            client = self._get_client()
            response = client.auth.admin.get_user_by_id(user_id)
            user = getattr(response, 'user', None) or response
            return getattr(user, 'email', '') or ''
        except Exception:
            return ''
