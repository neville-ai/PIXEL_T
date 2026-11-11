# Phase 10 — Stage B: Startup, Worker Lifecycle & Deployment Hardening

**Tanggal:** 2026-11-11  
**Status:** SELESAI  
**Baseline sebelum Stage B:** 281 passed, 1 skipped  
**Hasil akhir:** 304 passed, 1 skipped (**+23 test baru**, 0 regresi)

---

## 1. Ringkasan Perubahan

Tahap 10 Stage B melanjutkan hardening yang dimulai di Stage A dengan empat task utama:

| Task | Pekerjaan | Status |
|------|-----------|--------|
| **A** | Integrasi `validate_production()` ke startup aplikasi | ✅ Selesai |
| **B** | Graceful shutdown untuk worker queue | ✅ Selesai |
| **C** | Konfigurasi WSGI/Gunicorn single-worker | ✅ Selesai |
| **D** | Pemisahan liveness & readiness health check | ✅ Selesai |

---

## 2. Task A — Production Startup Validation

### Perubahan

`Backend/src/__init__.py` dimodifikasi untuk memanggil `config_class.validate_production()` **sebelum** objek Flask dibuat:

```python
def create_app(config_class=None):
    if config_class is None:
        config_class = get_config()

    # Production hardening gate (Phase 10 Stage A/B).
    if hasattr(config_class, 'validate_production'):
        config_class.validate_production()

    app = Flask(__name__)
    ...
```

### Mekanisme

1. Config dimuat terlebih dahulu via `get_config()` atau parameter eksplisit.
2. Jika config memiliki method `validate_production()` (semua class di `settings.py` memilikinya), metode dipanggil.
3. Method hanya aktif saat `APP_ENV == 'production'` — development dan testing aman.
4. Flask app object hanya dibuat setelah validasi berhasil.

### Test (6 test baru)

| Test | Penjelasan |
|------|-----------|
| `test_create_app_validates_production_config` | Valid production config → app dibuat sukses |
| `test_create_app_rejects_missing_secret_in_production` | SECRET_KEY kosong → `RuntimeError` |
| `test_create_app_rejects_short_secret_in_production` | SECRET_KEY < 32 karakter → `RuntimeError` |
| `test_create_app_rejects_debug_true_in_production` | DEBUG=True → `RuntimeError` |
| `test_create_app_development_does_not_validate` | Development skip validasi → app dibuat sukses |
| `test_create_app_testing_does_not_validate` | Testing skip validasi → app dibuat sukses |

---

## 3. Task B — Graceful Shutdown

### Desain

`AnalysisJobQueue` diberi mekanisme shutdown thread-safe berbasis `threading.Event`:

```python
class AnalysisJobQueue:
    def __init__(...):
        self._shutdown_event = threading.Event()
        self._worker_thread: Optional[threading.Thread] = None

    def shutdown(self, join_timeout: float = 30.0) -> None:
        self._shutdown_event.set()
        with self._not_empty:
            self._not_empty.notify_all()
        if self._worker_thread is not None and self._worker_thread.is_alive():
            self._worker_thread.join(timeout=join_timeout)
            if self._worker_thread.is_alive():
                logger.warning("[SHUTDOWN] Worker thread did not finish within %.1fs...", ...)
```

**Perubahan pada `_work_loop`:**
- Loop berhenti ketika `_shutdown_event` diset DAN tidak ada job aktif.
- `wait(timeout=0.5)` ditambahkan agar worker memeriksa shutdown event secara berkala.

### Sifat-sifat

| Properti | Keterangan |
|----------|-----------|
| **Thread-safe** | Semua operasi menggunakan lock yang sama |
| **Idempotent** | `shutdown()` bisa dipanggil berulang tanpa error |
| **Non-blocking enqueue** | Setelah shutdown, `try_enqueue()` langsung return `False` |
| **Graceful join** | Job aktif diberi kesempatan selesai sebelum timeout |
| **Logging** | Warning dicatat jika worker tidak selesai dalam timeout |

### Test (9 test baru)

| Test | Penjelasan |
|------|-----------|
| `test_shutdown_prevents_new_jobs` | After shutdown, enqueue returns False |
| `test_shutdown_empty_queue_returns_quickly` | Empty queue + shutdown = instant return |
| `test_shutdown_allows_active_job_to_finish` | In-flight job selesai sebelum shutdown complete |
| `test_shutdown_is_idempotent` | Double-shutdown safe |
| `test_shutdown_worker_stops_fetching_new_jobs` | Worker berhenti ambil job baru |
| `test_fifo_capacity_unchanged_after_shutdown` | Kapasitas queue tetap 4 |
| `test_drain_one_works_before_shutdown` | drain_one normal sebelum shutdown |
| `test_worker_survives_exception_and_continues` | Worker tahan exception runner |
| `test_shutdown_timeout_logs_warning` | Timeout logging warning message |

---

## 4. Task C — WSGI / Gunicorn Configuration

### File Baru: `Backend/gunicorn.conf.py`

Konfigurasi Gunicorn dengan **single-worker constraint**:

```python
workers = 1
worker_class = "sync"
threads = 1
timeout = 120          # cukup untuk AI inference besar
graceful_timeout = 60  # waktu tunggu job aktif selesai
preload_app = False    # kompatibel dengan signal handler
```

### Alasan Single-Worker

Queue bersifat **in-memory dan process-local**. Setiap worker Gunicorn punya queue sendiri yang tidak tersinkronisasi. Multi-worker akan menyebabkan:
- Job hilang jika worker tertentu restart
- Tombstone/deletion state terfragmentasi
- Cooperative cancellation tidak bekerja lintas proses

**Kesimpulan:** Satu worker adalah satu-satunya konfigurasi yang aman sampai migrasi Redis/RQ dilakukan.

### File Baru: `Backend/pyproject.toml`

Memisahkan dependency dengan optional group `production` (gunicorn) dan `dev`.

### Cara Menjalankan Produksi (Lokal)

```bash
# Install dependency production
pip install "gunicorn>=21.2.0,<23.0.0"

# Jalankan dengan Gunicorn
APP_ENV=production \
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") \
SUPABASE_URL=https://your-project.supabase.co \
SUPABASE_ANON_KEY=<key> \
gunicorn -c Backend/gunicorn.conf.py src.main:app
```

---

## 5. Task D — Liveness & Readiness Endpoints

### Perubahan: `Backend/src/routes/health.py`

Endpoint dipisah menjadi tiga route:

| Route | Tujuan | Respons |
|-------|--------|---------|
| `GET /api/livez` | Liveness probe | Selalu 200 selama proses hidup |
| `GET /api/readyz` | Readiness probe | 200 jika config + Supabase kredensial ada; 503 jika tidak |
| `GET /api/health` | Legacy compat | Delegasi ke liveness (backward compatible) |

### Liveness (`/api/livez`)
- Hanya menjawab "apakah proses masih berjalan?"
- Tidak mengecek database, storage, atau GPU
- Avoids false-positive pod restart

### Readiness (`/api/readyz`)
- Memeriksa apakah Supabase credentials tersedia
- Mengembalikan status environment (`APP_ENV`)
- Tidak menjalankan inference model
- Tidak melakukan query database berat
- Bisa diperluas nanti untuk cek koneksi Supabase aktual

### Test (8 test baru)

| Test | Penjelasan |
|------|-----------|
| `test_liveness_returns_200` | `/api/livez` mengembalikan 200 |
| `test_liveness_no_auth_required` | Livez tidak butuh auth |
| `test_readiness_with_supabase_configured` | Readyz 200 dengan kredensial |
| `test_readiness_without_supabase_credentials` | Readyz 503 tanpa kredensial |
| `test_readiness_no_auth_required` | Readyz bisa diakses publik |
| `test_health_legacy_endpoint` | `/api/health` legacy tetap berfungsi |
| `test_health_legacy_no_auth` | Legacy endpoint accessible without auth |
| `test_enqueue_blocked_during_shutdown` | Concurrent safety: enqueue ditolak saat shutdown |

---

## 6. Signal Handling di `main.py`

`Backend/src/main.py` menambahkan:

1. **SIGTERM & SIGINT handler** — memanggil `job_queue.shutdown(join_timeout=30.0)` sebelum `sys.exit(0)`.
2. **atexit fallback** — shutdown dipanggil juga saat interpreter exiting normal.
3. Handler aman terhadap environment tanpa signal support (testing).

```python
def _shutdown_handler(signum, frame):
    logger.info("Shutdown signal %s received; stopping analysis worker …", signum)
    from src.controllers.analysis_controller import controller
    if hasattr(controller, 'service') and hasattr(controller.service, 'job_queue'):
        controller.service.job_queue.shutdown(join_timeout=30.0)
    sys.exit(0)

signal.signal(signal.SIGTERM, _shutdown_handler)
signal.signal(signal.SIGINT, _shutdown_handler)
```

---

## 7. Daftar File yang Berubah / Dibuat

| File | Aksi | Deskripsi |
|------|------|-----------|
| `Backend/src/__init__.py` | **Dimodifikasi** | Tambah `validate_production()` call di `create_app()` |
| `Backend/src/services/analysis_queue_service.py` | **Dimodifikasi** | Tambah graceful shutdown mechanism (`shutdown()`, `_shutdown_event`, `_worker_thread`) |
| `Backend/src/main.py` | **Diperbarui** | Signal handler SIGTERM/SIGINT + atexit fallback |
| `Backend/src/routes/health.py` | **Diperbarui** | Split ke `/api/livez`, `/api/readyz`, legacy `/api/health` |
| `Backend/gunicorn.conf.py` | **Baru** | Konfigurasi Gunicorn single-worker |
| `Backend/pyproject.toml` | **Baru** | Dependency management dengan optional groups |
| `tests/backend/test_stage_b.py` | **Baru** | 23 test untuk Stage B |

**Total file diubah/dibuat:** 7 file  
**Test baru:** 23 (6 Task A + 9 Task B + 8 Task D)

---

## 8. Hasil Full Test Suite

```
pytest tests/ -q
======================== 304 passed, 1 skipped in 138.24s ========================
```

| Metric | Sebelum Stage B | Setelah Stage B |
|--------|----------------|-----------------|
| Passed | 281 | **304** (+23) |
| Skipped | 1 | 1 |
| Failed | 0 | 0 |

**Regresi:** 0  
**Test health legacy:** 5 passed  
**Test integration lifecycle:** 22 passed  
**Test queue service:** 9 passed  

---

## 9. Checkpoint Integrity

| Item | Nilai | Status |
|------|-------|--------|
| File | `Backend/ai/models/PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth` | — |
| SHA-256 | `46521ae90d12f57f77a7b9921881910b41071dbbb1eff4d2172a2c437564c581` | ✅ **Identik** |
| Ukuran | 135.644.553 bytes | ✅ |
| `Backend/ai/` | 29 files, tidak ada yang berubah | ✅ |

---

## 10. Target Kondisi Backend — Tercapai

| Aspek | Target | Status |
|-------|--------|--------|
| **Startup** | Production config divalidasi otomatis | ✅ `create_app()` memanggil `validate_production()` |
| **Worker** | Dapat dihentikan secara terkontrol | ✅ `shutdown()` dengan graceful timeout |
| **Server** | Konfigurasi WSGI terdokumentasi | ✅ `gunicorn.conf.py` single-worker |
| **Health** | Liveness + readiness tersedia | ✅ `/api/livez`, `/api/readyz`, `/api/health` |
| **Queue** | Tetap single-process, belum durable | ✅ Catatan dokumentasi dipertahankan |

---

## 11. Risiko yang Masih Tersisa

| Risiko | Tingkat | Catatan |
|--------|---------|---------|
| Queue in-memory non-durable | MEDIUM | Job hilang saat proses restart. Perlu migrasi Redis/RQ untuk durability. |
| Multi-worker constraint | MEDIUM | Gunicorn wajib dikonfigurasi dengan `workers = 1`. Default Gunicorn (4 worker) akan merusak queue integrity. |
| Readiness hanya cek credential presence | LOW | Belumcek koneksi aktual ke Supabase. Bisa diperluas di tahap berikutnya. |
| Signal handler Windows compatibility | LOW | Handler terdaftar tetapi Windows tidak mendukung SIGTERM secara native. Gunakan `KeyboardInterrupt` (Ctrl+C) untuk stop. |
| atexit callback pada error startup | LOW | Jika `create_app()` raise exception, atexit tidak terregistrasi dengan benar. Acceptable karena app tidak berjalan. |
| Gunicorn dependency optional | LOW | Harus diinstall manual: `pip install "gunicorn>=21.2.0,<23.0.0"` |

---

## 12. Instruksi Menjalankan Aplikasi Production Secara Lokal

```bash
# 1. Setup environment
cd Backend
cp .env.example .env
# Edit .env:
#   APP_ENV=production
#   SECRET_KEY=<generate dengan python -c "import secrets; print(secrets.token_hex(32))">
#   SUPABASE_URL=https://xxx.supabase.co
#   SUPABASE_ANON_KEY=<anon-key>
#   SUPABASE_SERVICE_ROLE_KEY=<service-role-key>

# 2. Install production dependencies
pip install -e ".[production]"
# Atau manual:
pip install gunicorn>=21.2.0,<23.0.0

# 3. Jalankan dengan Gunicorn (single-worker)
gunicorn -c gunicorn.conf.py src.main:app

# 4. Verifikasi health endpoints
curl http://127.0.0.1:5000/api/livez     # {"success":true,"data":{"status":"ok"}}
curl http://127.0.0.1:5000/api/readyz    # {"success":true,"data":{"status":"ok","env":"production"}}
curl http://127.0.0.1:5000/api/health    # legacy, same as livez

# 5. Stop gracefully
# Kirim SIGTERM: kill <pid> (Unix) atau Ctrl+C (Windows/local)
# Worker akan menyelesaikan job aktif (max 30s) sebelum exit
```

---

**STOP di Stage B.** Tahap 10 Stage C (jika ada) menunggu persetujuan. Tidak ada deployment, migrasi queue, atau commit/push yang dilakukan.
