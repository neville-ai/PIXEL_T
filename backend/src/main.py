import os
import signal
import sys
from pathlib import Path

# Ensure the backend directory is on sys.path so both `src` and `ai` packages resolve.
backend_dir = Path(__file__).resolve().parents[1]
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from src import create_app
from src.config.settings import get_config

app = create_app()

# Module-level reference kept so the atexit/signal handlers can reach it.
_current_app = app


def _shutdown_handler(signum, frame):
    """Graceful-shutdown signal handler.

    When the process receives SIGTERM or SIGINT (the signals sent by most
    container runtimes and process supervisors), we:
      1. Stop accepting new analysis jobs immediately.
      2. Let any in-flight job finish (up to 30 seconds).
      3. Exit with status 0 so the supervisor records a clean termination.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(
        "Shutdown signal %s received; stopping analysis worker …", signum
    )
    # The queue lives inside the AnalysisService singleton held by the
    # controller; we access it via the registered blueprints.
    from src.controllers.analysis_controller import controller
    if hasattr(controller, 'service') and hasattr(controller.service, 'job_queue'):
        controller.service.job_queue.shutdown(join_timeout=30.0)
    sys.exit(0)


# Register POSIX and Windows signal handlers.
try:
    signal.signal(signal.SIGTERM, _shutdown_handler)
except (OSError, ValueError):
    pass  # signal handling unavailable in some test environments
try:
    signal.signal(signal.SIGINT, _shutdown_handler)
except (OSError, ValueError):
    pass

# Fallback: call shutdown on normal interpreter exit.
import atexit


def _atexit_shutdown():
    """Best-effort graceful shutdown of the analysis worker on interpreter exit."""
    try:
        from src.controllers.analysis_controller import controller
        if hasattr(controller, 'service') and hasattr(controller.service, 'job_queue'):
            controller.service.job_queue.shutdown(join_timeout=5.0)
    except Exception:
        pass  # best-effort; don't let atexit failures crash the interpreter


atexit.register(_atexit_shutdown)


if __name__ == '__main__':
    host = app.config.get('BACKEND_HOST', '127.0.0.1')
    port = app.config.get('BACKEND_PORT', 5000)
    debug = app.config.get('DEBUG', False)
    app.run(host=host, port=port, debug=debug)
