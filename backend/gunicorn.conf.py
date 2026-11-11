"""Gunicorn configuration for PIXEL-T production deployment.

Single-worker constraint:
    The analysis queue is in-memory and process-local. Running multiple
    workers would create separate queues that cannot share jobs or tombstones,
    leading to lost or duplicated work. Therefore exactly one worker is used.

To start the application:
    gunicorn -c Backend/gunicorn.conf.py src.main:app

Or with environment variables:
    APP_ENV=production \
    SECRET_KEY=<secure-key-32+chars> \
    SUPABASE_URL=https://... \
    SUPABASE_ANON_KEY=<key> \
    gunicorn -c Backend/gunicorn.conf.py src.main:app
"""

# ---------------------------------------------------------------------------
# Process naming
# ---------------------------------------------------------------------------
proc_name = "pixel-t"

# ---------------------------------------------------------------------------
# Server socket
# ---------------------------------------------------------------------------
bind = "127.0.0.1:5000"

# ---------------------------------------------------------------------------
# Workers — SINGLE PROCESS (critical for in-memory queue integrity)
# ---------------------------------------------------------------------------
workers = 1
worker_class = "sync"
threads = 1

# ---------------------------------------------------------------------------
# Timeouts
# ---------------------------------------------------------------------------
# Maximum time an individual request may take before the worker is killed.
# Set generous enough for large AI inference requests (up to 120s).
timeout = 120

# Graceful timeout: how long Gunicorn waits for a worker to finish its
# current request before forcing termination during a reload/shutdown.
graceful_timeout = 60

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
accesslog = "-"          # stdout
errorlog = "-"           # stderr
loglevel = "info"

# ---------------------------------------------------------------------------
# Preloading
# ---------------------------------------------------------------------------
# Load the application code before forking workers so each worker shares the
# same loaded modules (memory efficient). Not compatible with hot-reload.
preload_app = False

# ---------------------------------------------------------------------------
# Worker cleanup
# ---------------------------------------------------------------------------
# Clean up server-side sockets when a worker exits.
forwarded_allow_ips = "*"
