from flask import request, g, jsonify
from app.core.errors import APIError
from app.services.admin_service import AdminService


class AdminController:
    """Controller handling HTTP endpoints for admin doctor management."""

    def __init__(self, service: AdminService = None):
        self.service = service or AdminService()

    def list_doctors(self):
        """GET /api/admin/doctors

        Returns a list of all doctor profiles with their status.
        Query param `status` can filter by: pending, approved, rejected.
        """
        status = request.args.get('status')
        try:
            doctors = self.service.list_doctors(status=status)
            return jsonify({
                "success": True,
                "data": doctors,
            }), 200
        except APIError as e:
            return jsonify({"success": False, "error": e.message, "code": e.code}), e.status_code

    def get_doctor(self, doctor_id: str):
        """GET /api/admin/doctors/:id

        Returns full details for a single doctor profile.
        """
        try:
            doctor = self.service.get_doctor(doctor_id)
            if not doctor:
                return jsonify({
                    "success": False,
                    "error": "Doctor profile not found.",
                    "code": "NOT_FOUND",
                }), 404
            return jsonify({
                "success": True,
                "data": doctor,
            }), 200
        except APIError as e:
            return jsonify({"success": False, "error": e.message, "code": e.code}), e.status_code

    def approve_doctor(self, doctor_id: str):
        """POST /api/admin/doctors/:id/approve

        Changes the doctor's account_status from 'pending' to 'approved'.
        Records the admin who performed the approval.
        """
        try:
            admin_user_id = g.current_user['id']
            doctor = self.service.approve_doctor(doctor_id, admin_user_id)
            return jsonify({
                "success": True,
                "data": doctor,
                "message": "Doctor account has been approved.",
            }), 200
        except APIError as e:
            return jsonify({"success": False, "error": e.message, "code": e.code}), e.status_code

    def reject_doctor(self, doctor_id: str):
        """POST /api/admin/doctors/:id/reject

        Changes the doctor's account_status from 'pending' to 'rejected'.
        Optionally accepts a rejection_reason in the request body.
        """
        reason = ''
        if request.is_json and request.get_json(silent=True):
            reason = request.get_json().get('reason', '') or ''

        try:
            admin_user_id = g.current_user['id']
            doctor = self.service.reject_doctor(doctor_id, admin_user_id, reason)
            return jsonify({
                "success": True,
                "data": doctor,
                "message": "Doctor account has been rejected.",
            }), 200
        except APIError as e:
            return jsonify({"success": False, "error": e.message, "code": e.code}), e.status_code

    def get_statistics(self):
        """GET /api/admin/doctors/stats

        Returns aggregate counts: total, pending, approved, rejected.
        """
        try:
            stats = self.service.get_statistics()
            return jsonify({
                "success": True,
                "data": stats,
            }), 200
        except APIError as e:
            return jsonify({"success": False, "error": e.message, "code": e.code}), e.status_code
