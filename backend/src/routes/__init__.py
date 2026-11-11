from src.routes.health import health_bp
from src.routes.analysis import analysis_bp
from src.routes.admin import admin_bp


def register_blueprints(app):
    """Register all API route blueprints under /api prefix."""
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(analysis_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/api')
