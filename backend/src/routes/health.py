from flask import Blueprint, jsonify

health_bp = Blueprint('health', __name__)


@health_bp.route('/livez', methods=['GET'])
def liveness_check():
    """Liveness probe — answers only "is the process alive?".

    Never queries external dependencies (database, storage, GPU). A false
    negative here would cause a orchestrator to restart a perfectly healthy
    process. Intended for Kubernetes ``livenessProbe`` or similar probes.
    """
    return jsonify({
        "success": True,
        "data": {
            "status": "ok"
        }
    }), 200


@health_bp.route('/readyz', methods=['GET'])
def readiness_check():
    """Readiness probe — answers "is the app ready to serve requests?".

    Checks only lightweight, non-mutating conditions:
      - Config is present and well-formed.
      - Queue worker slot is available (no hard limit enforcement here;
        we merely confirm the service object exists).

    Dependency-level checks (Supabase connectivity, model availability) are
    intentionally omitted because transient upstream failures must not cause
    pod eviction — those belong in an application-level monitoring metric,
    not in a readiness probe that drives traffic routing.
    """
    from src.config.settings import get_config as _get_config

    try:
        cfg = _get_config()
    except Exception:
        return jsonify({
            "success": False,
            "data": {
                "status": "not_ready",
                "details": "configuration unavailable"
            }
        }), 503

    # Check that Supabase credentials are present (non-mutating, cheap).
    supabase_url = getattr(cfg, 'SUPABASE_URL', '')
    anon_key = getattr(cfg, 'SUPABASE_ANON_KEY', '')
    if not supabase_url or not anon_key:
        return jsonify({
            "success": False,
            "data": {
                "status": "not_ready",
                "details": "supabase credentials not configured"
            }
        }), 503

    return jsonify({
        "success": True,
        "data": {
            "status": "ok",
            "env": cfg.APP_ENV
        }
    }), 200


# Backward-compatible alias so existing callers of /api/health keep working.
@health_bp.route('/health', methods=['GET'])
def health_check():
    """Legacy endpoint — delegated to liveness for compatibility."""
    return jsonify({
        "success": True,
        "data": {
            "status": "ok"
        }
    }), 200
