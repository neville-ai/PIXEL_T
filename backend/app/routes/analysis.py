from flask import Blueprint, request
from app.core.auth import require_approved_doctor
from app.controllers.analysis_controller import AnalysisController
import time
import uuid

analysis_bp = Blueprint('analysis', __name__)
controller = AnalysisController()


@analysis_bp.route('/analysis', methods=['POST'])
@require_approved_doctor
def create_analysis():
    """POST /api/analysis

    Accepts an uploaded endoscopy image via multipart/form-data.
    Validates, uploads to private storage, and creates an analysis record with status 'processing'.
    Requires authenticated doctor with approved account status.
    """
    request_id = str(uuid.uuid4())[:8]
    start_time = time.perf_counter()
    print(f"[CORRELATION] request_id={request_id} stage=POST /api/analysis start")
    result = controller.create_analysis()
    duration_ms = (time.perf_counter() - start_time) * 1000
    print(f"[CORRELATION] request_id={request_id} stage=POST /api/analysis end duration_ms={duration_ms:.1f}")
    return result


@analysis_bp.route('/analysis/<analysis_id>', methods=['GET'])
@require_approved_doctor
def get_analysis(analysis_id: str):
    """GET /api/analysis/<analysis_id>

    Retrieves analysis session details verifying user ownership.
    Requires authenticated doctor with approved account status.
    """
    start_time = time.perf_counter()
    print(f"[CORRELATION] analysis_id={analysis_id} stage=GET /api/analysis/:id start")
    result = controller.get_analysis(analysis_id)
    duration_ms = (time.perf_counter() - start_time) * 1000
    print(f"[CORRELATION] analysis_id={analysis_id} stage=GET /api/analysis/:id end duration_ms={duration_ms:.1f}")
    return result


@analysis_bp.route('/history', methods=['GET'])
@require_approved_doctor
def list_history():
    """GET /api/history

    Retrieves paginated analysis history for the authenticated doctor.
    Requires authenticated doctor with approved account status.
    """
    return controller.list_history()


@analysis_bp.route('/history/<analysis_id>', methods=['DELETE'])
@require_approved_doctor
def delete_analysis(analysis_id: str):
    """DELETE /api/history/<analysis_id>

    Deletes an analysis session verifying user ownership.
    Requires authenticated doctor with approved account status.
    """
    return controller.delete_analysis(analysis_id)
