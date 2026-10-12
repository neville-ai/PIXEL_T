from app.routes.health import health_bp
from app.routes.analysis import analysis_bp


def register_blueprints(app):
    """Register all API route blueprints under /api prefix."""
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(analysis_bp, url_prefix='/api')
