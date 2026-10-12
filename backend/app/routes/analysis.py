from flask import Blueprint
from app.core.auth import require_auth
from app.controllers.analysis_controller import AnalysisController

analysis_bp = Blueprint('analysis', __name__)
controller = AnalysisController()


@analysis_bp.route('/analysis', methods=['POST'])
@require_auth
def create_analysis():
    """POST /api/analysis

    Accepts an uploaded endoscopy image via multipart/form-data.
    Validates, uploads to private storage, and creates an analysis record with status 'processing'.
    """
    return controller.create_analysis()


@analysis_bp.route('/analysis/<analysis_id>', methods=['GET'])
@require_auth
def get_analysis(analysis_id: str):
    """GET /api/analysis/<analysis_id>

    Retrieves analysis session details verifying user ownership.
    """
    return controller.get_analysis(analysis_id)


@analysis_bp.route('/history', methods=['GET'])
@require_auth
def list_history():
    """GET /api/history

    Retrieves paginated analysis history for the authenticated user.
    """
    return controller.list_history()


@analysis_bp.route('/history/<analysis_id>', methods=['DELETE'])
@require_auth
def delete_analysis(analysis_id: str):
    """DELETE /api/history/<analysis_id>

    Deletes an analysis session verifying user ownership.
    """
    return controller.delete_analysis(analysis_id)
