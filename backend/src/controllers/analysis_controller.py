from flask import request, jsonify, g
from src.core.errors import APIError
from src.services.analysis_service import AnalysisService
import time


class AnalysisController:
    """Controller handling HTTP endpoints for analysis upload and retrieval."""

    def __init__(self, service: AnalysisService = None):
        self.service = service or AnalysisService()

    def create_analysis(self):
        """Handle POST /api/analysis.

        Accepts multipart/form-data with 'image' field, validates it, persists
        the original, and enqueues the AI pipeline as a background job. Returns
        202 Accepted with the stable analysis_id and status 'processing'; the
        caller polls GET /api/analysis/<id> for completion (Batch P-02).
        """
        start_time = time.perf_counter()
        if "image" not in request.files:
            raise APIError("MISSING_FILE", "No image file provided in request. Expected form field 'image'.", 400)

        image_file = request.files["image"]
        user_id = getattr(g, "current_user", {}).get("id") or getattr(getattr(request, "user", None), "get", lambda k: None)("id")

        if not user_id:
            raise APIError("UNAUTHORIZED", "Authenticated user identity could not be verified.", 401)

        print(f"[CORRELATION] user_id={user_id} stage=create_analysis start")
        result = self.service.create_analysis(file_storage=image_file, user_id=user_id)
        analysis_id = result.get("analysis_id", "unknown")
        duration_ms = (time.perf_counter() - start_time) * 1000
        print(f"[CORRELATION] analysis_id={analysis_id} user_id={user_id} stage=create_analysis end duration_ms={duration_ms:.1f}")
        return jsonify({
            "success": True,
            "data": result,
        }), 202

    def get_analysis(self, analysis_id: str):
        """Handle GET /api/analysis/<analysis_id>.

        Retrieves analysis metadata and signed original image URL verifying ownership.
        """
        start_time = time.perf_counter()
        user_id = getattr(g, "current_user", {}).get("id") or getattr(getattr(request, "user", None), "get", lambda k: None)("id")

        if not user_id:
            raise APIError("UNAUTHORIZED", "Authenticated user identity could not be verified.", 401)

        print(f"[CORRELATION] analysis_id={analysis_id} user_id={user_id} stage=get_analysis start")
        result = self.service.get_analysis(analysis_id=analysis_id, user_id=user_id)
        duration_ms = (time.perf_counter() - start_time) * 1000
        print(f"[CORRELATION] analysis_id={analysis_id} user_id={user_id} stage=get_analysis end duration_ms={duration_ms:.1f}")
        return jsonify({
            "success": True,
            "data": result,
        }), 200

    def list_history(self):
        """Handle GET /api/history.

        Retrieves paginated analysis history for the authenticated user.
        """
        user_id = getattr(g, "current_user", {}).get("id") or getattr(getattr(request, "user", None), "get", lambda k: None)("id")

        if not user_id:
            raise APIError("UNAUTHORIZED", "Authenticated user identity could not be verified.", 401)

        records = self.service.list_user_analyses(user_id=user_id)
        return jsonify({
            "success": True,
            "data": {
                "items": records,
            },
        }), 200

    def delete_analysis(self, analysis_id: str):
        """Handle DELETE /api/history/<analysis_id>.

        Deletes an analysis session verifying user ownership.

        The service raises APIError on every failure path, so a successful
        return always means the record was deleted (APIContract §21).
        """
        user_id = getattr(g, "current_user", {}).get("id") or getattr(getattr(request, "user", None), "get", lambda k: None)("id")

        if not user_id:
            raise APIError("UNAUTHORIZED", "Authenticated user identity could not be verified.", 401)

        self.service.delete_analysis(analysis_id=analysis_id, user_id=user_id)
        return jsonify({
            "success": True,
            "message": "Analysis deleted successfully",
        }), 200


# Shared singleton used by routes and shutdown handlers.
controller = AnalysisController()