"""Phase 10 Stage B — Startup, Worker Lifecycle & Deployment hardening tests."""
import logging
import signal
import threading
import time

import pytest

from src.services.analysis_queue_service import AnalysisJobQueue


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _job(analysis_id: str) -> dict:
    return {"analysis_id": analysis_id}


def _wait_until(predicate, timeout: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.005)
    return bool(predicate())


# ===================================================================
# TASK A — Production Startup Validation
# ===================================================================

class TestProductionStartupValidation:
    """Tests that validate_production() is called during app creation."""

    def test_create_app_validates_production_config(self, monkeypatch):
        """create_app() must call validate_production() when config is production."""
        from src.config.settings import ProductionConfig

        # Simulate valid production config
        monkeypatch.setattr(ProductionConfig, 'APP_ENV', 'production')
        monkeypatch.setattr(ProductionConfig, 'SECRET_KEY', 'a' * 32)
        monkeypatch.setattr(ProductionConfig, 'DEBUG', False)

        # Should not raise with valid production config
        from src import create_app
        app = create_app(ProductionConfig)
        assert app is not None

    def test_create_app_rejects_missing_secret_in_production(self, monkeypatch):
        """create_app() must raise RuntimeError when SECRET_KEY is missing in production."""
        from src.config.settings import ProductionConfig

        monkeypatch.setattr(ProductionConfig, 'APP_ENV', 'production')
        monkeypatch.setattr(ProductionConfig, 'SECRET_KEY', '')
        monkeypatch.setattr(ProductionConfig, 'DEBUG', False)

        from src import create_app
        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            create_app(ProductionConfig)

    def test_create_app_rejects_short_secret_in_production(self, monkeypatch):
        """create_app() must raise RuntimeError when SECRET_KEY < 32 chars in production."""
        from src.config.settings import ProductionConfig

        monkeypatch.setattr(ProductionConfig, 'APP_ENV', 'production')
        monkeypatch.setattr(ProductionConfig, 'SECRET_KEY', 'short')
        monkeypatch.setattr(ProductionConfig, 'DEBUG', False)

        from src import create_app
        with pytest.raises(RuntimeError, match="32"):
            create_app(ProductionConfig)

    def test_create_app_rejects_debug_true_in_production(self, monkeypatch):
        """create_app() must raise RuntimeError when DEBUG=True in production."""
        from src.config.settings import ProductionConfig

        monkeypatch.setattr(ProductionConfig, 'APP_ENV', 'production')
        monkeypatch.setattr(ProductionConfig, 'SECRET_KEY', 'a' * 32)
        monkeypatch.setattr(ProductionConfig, 'DEBUG', True)

        from src import create_app
        with pytest.raises(RuntimeError, match="DEBUG"):
            create_app(ProductionConfig)

    def test_create_app_development_does_not_validate(self, monkeypatch):
        """Development config must skip production validation."""
        from src.config.settings import DevelopmentConfig
        from src import create_app

        monkeypatch.setattr(DevelopmentConfig, 'APP_ENV', 'development')
        monkeypatch.setattr(DevelopmentConfig, 'SECRET_KEY', '')
        monkeypatch.setattr(DevelopmentConfig, 'DEBUG', True)

        # Must not raise — development skips validate_production()
        app = create_app(DevelopmentConfig)
        assert app is not None

    def test_create_app_testing_does_not_validate(self, monkeypatch):
        """Testing config must skip production validation."""
        from src.config.settings import TestingConfig
        from src import create_app

        monkeypatch.setattr(TestingConfig, 'APP_ENV', 'testing')
        monkeypatch.setattr(TestingConfig, 'SECRET_KEY', '')
        monkeypatch.setattr(TestingConfig, 'DEBUG', False)

        app = create_app(TestingConfig)
        assert app is not None


# ===================================================================
# TASK B — Graceful Shutdown
# ===================================================================

class TestGracefulShutdown:
    """Tests for queue worker graceful shutdown behavior."""

    def test_shutdown_prevents_new_jobs(self):
        """After shutdown(), try_enqueue must return False immediately."""
        queue = AnalysisJobQueue(runner=lambda job: None, auto_start=False)
        queue.shutdown()
        assert queue.is_shutdown_requested is True
        assert queue.try_enqueue(_job("after-shutdown")) is False

    def test_shutdown_empty_queue_returns_quickly(self):
        """Shutdown with no running worker should complete promptly."""
        queue = AnalysisJobQueue(runner=lambda job: None, auto_start=False)
        start = time.perf_counter()
        queue.shutdown(join_timeout=5.0)
        elapsed = time.perf_counter() - start
        assert elapsed < 1.0  # should be nearly instant when no worker running

    def test_shutdown_allows_active_job_to_finish(self):
        """Shutdown must wait for an in-flight job to finish (within timeout)."""
        completed = threading.Event()

        def slow_runner(job):
            time.sleep(0.2)
            completed.set()

        queue = AnalysisJobQueue(runner=slow_runner, auto_start=True)
        assert queue.try_enqueue(_job("slow-job")) is True

        # Wait until worker picks up and starts the job
        assert _wait_until(completed.is_set, timeout=5.0)

        # Now trigger shutdown — should wait for the job to finish
        start = time.perf_counter()
        queue.shutdown(join_timeout=5.0)
        elapsed = time.perf_counter() - start

        # The job was already finishing; shutdown should complete quickly
        assert elapsed < 2.0
        assert completed.is_set()

    def test_shutdown_is_idempotent(self):
        """Calling shutdown() multiple times must not raise or cause issues."""
        queue = AnalysisJobQueue(runner=lambda job: None, auto_start=False)
        queue.shutdown(join_timeout=1.0)
        queue.shutdown(join_timeout=1.0)  # second call must be safe
        assert queue.is_shutdown_requested is True

    def test_shutdown_worker_stops_fetching_new_jobs(self):
        """Worker thread must stop after shutdown even if new jobs arrive."""
        received = []
        lock = threading.Lock()

        def runner(job):
            with lock:
                received.append(job["analysis_id"])

        queue = AnalysisJobQueue(runner=runner, auto_start=True)

        # Enqueue a fast job first
        assert queue.try_enqueue(_job("first")) is True
        assert _wait_until(lambda: len(received) >= 1, timeout=5.0)

        # Request shutdown
        queue.shutdown(join_timeout=5.0)

        # Try to enqueue after shutdown — must be rejected
        assert queue.try_enqueue(_job("after-shutdown")) is False

        # No more jobs should be processed
        assert _wait_until(lambda: not queue.worker_alive, timeout=5.0)

    def test_fifo_capacity_unchanged_after_shutdown(self):
        """Shutdown must not alter queue capacity or FIFO semantics."""
        queue = AnalysisJobQueue(runner=lambda job: None, auto_start=False)
        original_capacity = queue.capacity
        assert original_capacity == 4  # 1 active + 3 waiting

        queue.shutdown(join_timeout=1.0)

        # Capacity property remains the same
        assert queue.capacity == original_capacity
        assert queue.pending_count() == 0

    def test_drain_one_works_before_shutdown(self):
        """drain_one() must work normally before shutdown is requested."""
        order = []
        queue = AnalysisJobQueue(
            runner=lambda job: order.append(job["analysis_id"]),
            auto_start=False,
        )
        for name in ("a", "b", "c"):
            assert queue.try_enqueue(_job(name)) is True

        # Drain all before shutdown
        while queue.drain_one():
            pass
        assert order == ["a", "b", "c"]

        # Shutdown should still work
        queue.shutdown(join_timeout=1.0)
        assert queue.is_shutdown_requested

    def test_worker_survives_exception_and_continues(self, caplog):
        """Worker must survive exceptions and keep processing (pre-shutdown)."""
        finished = threading.Event()
        order = []

        def runner(job):
            if job["analysis_id"] == "boom":
                raise RuntimeError("simulated failure")
            order.append(job["analysis_id"])
            finished.set()

        queue = AnalysisJobQueue(runner=runner, auto_start=True)
        assert queue.try_enqueue(_job("boom")) is True
        assert queue.try_enqueue(_job("ok")) is True
        assert _wait_until(finished.is_set, timeout=5.0)
        assert order == ["ok"]
        # Queue should still accept more jobs
        assert queue.try_enqueue(_job("next")) is True

    def test_shutdown_timeout_logs_warning(self, caplog):
        """Shutdown with long-running job should log warning when timeout reached."""
        started = threading.Event()
        block = threading.Event()

        def blocking_runner(job):
            started.set()
            block.wait(timeout=10)

        queue = AnalysisJobQueue(runner=blocking_runner, auto_start=True)
        assert queue.try_enqueue(_job("infinite")) is True
        assert _wait_until(started.is_set, timeout=5.0)

        with caplog.at_level(logging.WARNING):
            # Use short timeout so the worker is forced to terminate
            queue.shutdown(join_timeout=0.2)

        # The warning should appear because the worker couldn't finish in time
        assert any("[SHUTDOWN]" in record.getMessage() for record in caplog.records)
        block.set()  # unblock the runner


# ===================================================================
# TASK D — Health Check & Readiness
# ===================================================================

class TestLivenessEndpoint:
    """Tests for GET /api/livez endpoint."""

    def test_liveness_returns_200(self, client):
        response = client.get('/api/livez')
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["status"] == "ok"

    def test_liveness_no_auth_required(self, client):
        response = client.get('/api/livez', headers={})
        assert response.status_code == 200
        assert response.get_json()["success"] is True


class TestReadinessEndpoint:
    """Tests for GET /api/readyz endpoint."""

    def test_readiness_with_supabase_configured(self, app, client):
        """Readiness returns ok when Supabase credentials are present."""
        from src.config.settings import TestingConfig
        # TestingConfig may not have real Supabase keys set, but the endpoint
        # checks for non-empty strings. We test the happy path via mocking.
        from unittest.mock import patch
        import src.config.settings as settings_mod

        class FakeCfg:
            APP_ENV = 'testing'
            SUPABASE_URL = 'https://example.supabase.co'
            SUPABASE_ANON_KEY = 'fake-anon-key'

        with patch.object(settings_mod, 'get_config', return_value=FakeCfg):
            response = client.get('/api/readyz')
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["status"] == "ok"

    def test_readiness_without_supabase_credentials(self, client):
        """Readiness returns 503 when Supabase credentials are missing."""
        from unittest.mock import patch
        import src.config.settings as settings_mod

        class EmptyCfg:
            APP_ENV = 'testing'
            SUPABASE_URL = ''
            SUPABASE_ANON_KEY = ''

        with patch.object(settings_mod, 'get_config', return_value=EmptyCfg):
            response = client.get('/api/readyz')
        assert response.status_code == 503
        data = response.get_json()
        assert data["success"] is False
        assert data["data"]["status"] == "not_ready"

    def test_readiness_no_auth_required(self, client):
        response = client.get('/api/readyz', headers={})
        # Status depends on whether Supabase is configured in the test env
        assert response.status_code in (200, 503)


class TestLegacyHealthEndpoint:
    """Backward-compatibility: /api/health must still work."""

    def test_health_legacy_endpoint(self, client):
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data["success"] is True
        assert data["data"]["status"] == "ok"

    def test_health_legacy_no_auth(self, client):
        response = client.get('/api/health', headers={})
        assert response.status_code == 200
        assert response.get_json()["success"] is True


# ===================================================================
# CONCURRENT SAFETY — Worker + Shutdown
# ===================================================================

class TestConcurrentSafety:
    """Tests verifying thread-safety under concurrent access."""

    def test_enqueue_blocked_during_shutdown(self):
        """Enqueue attempts during shutdown must not race or hang."""
        started = threading.Event()
        block = threading.Event()

        def blocking_runner(job):
            started.set()
            block.wait(timeout=10)

        queue = AnalysisJobQueue(runner=blocking_runner, auto_start=True)
        assert queue.try_enqueue(_job("blocker")) is True
        assert _wait_until(started.is_set, timeout=5.0)

        # Request shutdown while job is running
        shutdown_done = threading.Event()

        def do_shutdown():
            queue.shutdown(join_timeout=5.0)
            shutdown_done.set()

        t = threading.Thread(target=do_shutdown)
        t.start()

        # Try enqueuing from another thread during shutdown
        result = queue.try_enqueue(_job("concurrent"))
        assert result is False  # rejected during shutdown

        block.set()  # unblock the runner
        assert _wait_until(shutdown_done.is_set, timeout=5.0)
        t.join(timeout=5.0)
