import logging
from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class APIError(Exception):
    """Custom application exception with structured error envelope."""
    def __init__(self, code="BAD_REQUEST", message="Invalid request.", status_code=400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code

    def to_dict(self):
        return {
            "success": False,
            "error": {
                "code": self.code,
                "message": self.message
            }
        }


def register_error_handlers(app):
    """Register standard HTTP error handlers conforming to APIContract."""

    @app.errorhandler(APIError)
    def handle_api_error(error):
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": {
                "code": "BAD_REQUEST",
                "message": getattr(error, "description", "Bad request.")
            }
        }), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({
            "success": False,
            "error": {
                "code": "UNAUTHORIZED",
                "message": getattr(error, "description", "Authentication required.")
            }
        }), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            "success": False,
            "error": {
                "code": "FORBIDDEN",
                "message": getattr(error, "description", "Access denied.")
            }
        }), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": getattr(error, "description", "Resource not found.")
            }
        }), 404

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "success": False,
            "error": {
                "code": "METHOD_NOT_ALLOWED",
                "message": "HTTP method not allowed for this endpoint."
            }
        }), 405

    @app.errorhandler(413)
    def request_too_large(_error):
        return jsonify({
            "success": False,
            "error": {
                "code": "FILE_TOO_LARGE",
                "message": "Uploaded file exceeds the 10 MB limit."
            }
        }), 413

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An internal server error occurred."
            }
        }), 500

    @app.errorhandler(Exception)
    def handle_unexpected_exception(error):
        # Do not expose technical details/traceback to user
        if isinstance(error, HTTPException):
            return jsonify({
                "success": False,
                "error": {
                    "code": f"HTTP_{error.code}",
                    "message": error.description
                }
            }), error.code

        logger.exception("Unhandled exception occurred: %s", error)

        return jsonify({
            "success": False,
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred."
            }
        }), 500
