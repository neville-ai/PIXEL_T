from flask import Flask
from flask_cors import CORS
from src.config.settings import get_config
from src.core.errors import register_error_handlers
from src.routes import register_blueprints


def create_app(config_class=None):
    """
    Application Factory for PIXEL-T Flask Backend.
    Initializes without external service dependencies (database, Supabase, AI model).

    When ``config_class`` resolves to a production environment,
    ``Config.validate_production()`` is invoked before the Flask app object is
    created so that misconfiguration (missing/short SECRET_KEY or DEBUG=True)
    fails the startup with a clear RuntimeError rather than silently serving
    requests with weak security.
    """
    # Load configuration first so validate_production() can inspect it.
    if config_class is None:
        config_class = get_config()

    # Production hardening gate (Phase 10 Stage A/B).
    if hasattr(config_class, 'validate_production'):
        config_class.validate_production()

    app = Flask(__name__)

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
