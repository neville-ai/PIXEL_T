from flask import Blueprint
from src.core.auth import require_admin
from src.controllers.admin_controller import AdminController

admin_bp = Blueprint('admin', __name__)
controller = AdminController()


@admin_bp.route('/admin/doctors', methods=['GET'])
@require_admin
def list_doctors():
    """GET /api/admin/doctors — List all doctor registrations (with optional status filter)."""
    return controller.list_doctors()


@admin_bp.route('/admin/doctors/stats', methods=['GET'])
@require_admin
def get_doctor_statistics():
    """GET /api/admin/doctors/stats — Return aggregate registration statistics."""
    return controller.get_statistics()


@admin_bp.route('/admin/doctors/<doctor_id>', methods=['GET'])
@require_admin
def get_doctor(doctor_id: str):
    """GET /api/admin/doctors/:id — Get full details for a single doctor profile."""
    return controller.get_doctor(doctor_id)


@admin_bp.route('/admin/doctors/<doctor_id>/approve', methods=['POST'])
@require_admin
def approve_doctor(doctor_id: str):
    """POST /api/admin/doctors/:id/approve — Approve a pending doctor registration."""
    return controller.approve_doctor(doctor_id)


@admin_bp.route('/admin/doctors/<doctor_id>/reject', methods=['POST'])
@require_admin
def reject_doctor(doctor_id: str):
    """POST /api/admin/doctors/:id/reject — Reject a pending doctor registration.

    Request body (JSON, optional):
      { "reason": "string" }
    """
    return controller.reject_doctor(doctor_id)
