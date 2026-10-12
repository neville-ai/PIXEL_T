from flask import Flask
from flask_cors import CORS
from app.core.config import get_config
from app.core.errors import register_error_handlers
from app.routes import register_blueprints


def create_app(config_class=None):
    """
    Application Factory for PIXEL-T Flask Backend.
    Initializes without external service dependencies (database, Supabase, AI model).
    """
    app = Flask(__name__)

    # Load configuration
    if config_class is None:
        config_class = get_config()
    app.config.from_object(config_class)

    # Centralized CORS configuration
    CORS(
        app,
        resources={r"/api/*": {"origins": app.config.get("CORS_ORIGINS", "*")}},
        supports_credentials=True
    )

    # Register standard error handlers
    register_error_handlers(app)

    # Register API blueprints
    register_blueprints(app)

    return app
