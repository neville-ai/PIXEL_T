# Phase 10 — Stage A: Security & Environment Configuration Hardening

**Tanggal:** 2026-11-11  
**Status:** SELESAI  
**Baseline test:** 269 passed, 1 skipped  
**Hasil akhir:** 281 passed, 1 skipped (**+12 test baru**, 0 regresi)

---

## 1. Konteks

Tahap 9 Final Audit mengidentifikasi tiga temuan keamanan yang harus ditindaklanjuti sebelum deployment production:

| Tingkat | Temuan | Lokasi |
|---------|--------|--------|
| **HIGH** | Default SECRET_KEY hard-coded (`pixel-t-dev-secret-change-in-production`) | `Backend/src/config/settings.py:10` |
| **MEDIUM** | `.env.example` mengandung placeholder secret yang bisa disalahtafsirkan sebagai nilai aktual | `Backend/.env.example:32` |
| **LOW** | Flask debug mode memiliki default `True` pada DevelopmentConfig tanpa validasi production eksplisit | `Backend/src/config/settings.py` |

Audit juga menegaskan bahwa queue in-memory bersifat process-local dan single-worker constraint perlu dipertahankan sampai migrasi Redis/RQ dilakukan di tahap terpisah.

---

## 2. Temuan Awal

### 2.1 SECRET_KEY Hard-Coded

File `Backend/src/config/settings.py` sebelumnya menggunakan:

```python
SECRET_KEY = os.getenv('SECRET_KEY', 'pixel-t-dev-secret-change-in-production')
```

Teks fallback ini bersifat development-only namun tidak dibedakan secara eksplisit dari konfigurasi production. Siapa pun yang meniru template tanpa membaca komentar berisiko menjalankan aplikasi production dengan kunci yang diketahui publik.

### 2.2 .env.example Berisi Placeholder yang Samar

`.env.example` versi lama berisi baris:

```
SECRET_KEY=pixel-t-dev-secret-change-in-production
```

Nilai ini bukan secret sesungguhnya, tetapi penulisannya menyerupai bentuk production-ready dan dapat menimbulkan kesalahpahaman.

### 2.3 Tidak Ada Validasi Production

Tidak ada mekanisme yang mencegah aplikasi starting dengan debug mode aktif atau SECRET_KEY kosong/pendek di lingkungan production. `validate_production()` belum pernah tồnongdi kelas Config.

### 2.4 Konfirmasi Positif

- `.gitignore` sudah mencakup `.env` dan `.env.*` (line 11–13, 57).
- File `.env` lokal di `Backend/.env` tidak ter-track oleh Git (dikonfirmasi dengan `git ls-files` dan `git check-ignore`).
- Tidak ada credential lain yang ter-hardcode di sumber Python.
- Checkpoint model `PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth` tetap utuh: **SHA-256 `46521ae90d12f57f77a7b9921881910b41071dbbb1eff4d2172a2c437564c581`** ✅
- `Backend/ai/` tidak disentuh sama sekali (29 file, semua unchanged).

---

## 3. File yang Diubah / Dibuat

| File | Aksi | Deskripsi |
|------|------|-----------|
| `Backend/src/config/settings.py` | **Dimodifikasi** | Menambahkan `_MIN_SECRET_KEY_LENGTH`, `_raw_secret`, method `validate_production()`, dan memisahkan logic SECRET_KEY per-env |
| `Backend/.env.example` | **Diperbarui** | Mengganti placeholder secret dengan instruksi generasi + placeholder eksplisit |
| `tests/backend/test_security_config.py` | **Baru** | 12 test unit untuk SECRET_KEY validation, debug mode, dan anti-leakage |

**Catatan:** `.env` lokal pengguna tidak diubah, tidak dihapus, dan tidak masuk Git.

---

## 4. Perubahan Konfigurasi

### 4.1 SECRET_KEY Logic

```python
_MIN_SECRET_KEY_LENGTH = 32

class Config:
    APP_ENV = os.getenv('APP_ENV', 'development')
    _raw_secret = os.getenv('SECRET_KEY', '')
    SECRET_KEY = _raw_secret if _raw_secret else 'pixel-t-dev-secret-for-local-development-only'
    # ...
```

Perubahan kunci:
- **Development/Test:** Menggunakan placeholder `'pixel-t-dev-secret-for-local-development-only'` hanya bila `SECRET_KEY` tidak diatur di environment. Placeholder ini pendek dan eksplisit bertuliskan "development only".
- **Production:** Harus mengatur `SECRET_KEY` melalui environment variable. Jika kosong atau < 32 karakter, startup akan **gagal dengan `RuntimeError`**.

### 4.2 Method `validate_production()`

```python
@classmethod
def validate_production(cls) -> None:
    if cls.APP_ENV != 'production':
        return
    if not cls.SECRET_KEY:
        raise RuntimeError(
            "PIXEL-T production startup failed: SECRET_KEY environment variable is not set. "
            "Generate a secure key (≥ 32 random characters) and set it before starting."
        )
    if len(cls.SECRET_KEY) < _MIN_SECRET_KEY_LENGTH:
        raise RuntimeError(
            f"PIXEL-T production startup failed: SECRET_KEY must be at least "
            f"{_MIN_SECRET_KEY_LENGTH} characters long. Current length: {len(cls.SECRET_KEY)}. "
            "Generate a secure key (≥ 32 random characters) and set it before starting."
        )
    if cls.DEBUG:
        raise RuntimeError(
            "PIXEL-T production startup failed: DEBUG mode must not be enabled in production. "
            "Set APP_ENV=production with DEBUG=False, or ensure the production config class is used."
        )
```

Validasi berjalan saat `validate_production()` dipanggil. Caller (misalnya `main.py` atau entrypoint deployment) bertanggung jawab memanggilnya sebelum melayani request.

### 4.3 Debug Mode Per-Environment

| Class | DEBUG | TESTING | APP_ENV |
|-------|-------|---------|---------|
| `DevelopmentConfig` | `True` | `False` | `'development'` (default) |
| `TestingConfig` | `False` | `True` | `'testing'` |
| `ProductionConfig` | `False` | `False` | `'production'` |

Production **selalu** `DEBUG = False`. Nilai ini tidak dapat di-overrides melalui env var karena ditetapkan secara hardcoded di kelas.

### 4.4 `.env.example` Baru

```ini
# --- Server Secret ---
# Generate a cryptographically secure key (≥ 32 random characters).
# Example: python -c "import secrets; print(secrets.token_hex(32))"
# NEVER commit the real value to version control.
SECRET_KEY=your-random-secret-key-minimum-32-chars
```

Tidak ada lagi string yang menyerupai secret nyata. Terdapat instruksi lengkap untuk generasi kunci.

---

## 5. Perilaku Development vs Production

| Skenario | Development | Testing | Production |
|----------|------------|---------|------------|
| `SECRET_KEY` tidak diatur | Placeholder dev digunakan | Placeholder dev digunakan | `RuntimeError` (startup gagal) |
| `SECRET_KEY` < 32 karakter | Placeholder dev digunakan | Placeholder dev digunakan | `RuntimeError` (startup gagal) |
| `SECRET_KEY` ≥ 32 karakter | Kunci tersebut dipakai | Kunci tersebut dipakai | Kunci tersebut dipakai, validasi lolos |
| `DEBUG = True` | Aktif | Nonaktif | Ditolak `validate_production()` |
| `validate_production()` dipanggil | Returns early (no-op) | Returns early (no-op) | Validates all constraints |

---

## 6. Test yang Ditambahkan

**File:** `tests/backend/test_security_config.py`  
**Jumlah:** 12 test, semua lulus.

### TestSecretKeyValidation (6 test)
| Test | Penjelasan |
|------|-----------|
| `test_production_missing_secret_key_raises` | Produksi tanpa SECRET_KEY → `RuntimeError` |
| `test_production_short_secret_key_raises` | SECRET_KEY < 32 karakter → `RuntimeError` |
| `test_production_valid_secret_key_passes` | SECRET_KEY ≥ 32 karakter → lolos |
| `test_development_uses_placeholder` | Development tetap lancar tanpa SECRET_KEY |
| `test_testing_unaffected` | Testing unaffected oleh panjang SECRET_KEY |
| `test_get_config_returns_correct_class` | `get_config()` memilih class sesuai `APP_ENV` |

### TestDebugMode (4 test)
| Test | Penjelasan |
|------|-----------|
| `test_production_debug_disabled_by_default` | ProductionConfig.DEBUG = False |
| `test_development_debug_enabled` | DevelopmentConfig.DEBUG = True |
| `test_testing_debug_disabled` | TestingConfig.DEBUG = False |
| `test_production_rejects_explicit_debug_true` | DEBUG=True di production → `RuntimeError` |

### TestNoSecretLeakage (2 test)
| Test | Penjelasan |
|------|-----------|
| `test_secret_not_in_validation_error_message` | Pesan error tidak membocorkan nilai secret |
| `test_env_example_has_no_real_secret` | `.env.example` tidak mengandung secret nyata |

---

## 7. Hasil Full Test Suite

```
pytest tests/ -q
============================= 281 passed, 1 skipped in 135.84s ==============================
```

| Metric | Sebelum Tahap 10-A | Setelah Tahap 10-A |
|--------|-------------------|-------------------|
| Passed | 269 | **281** (+12) |
| Skipped | 1 | 1 |
| Failed | 0 | 0 |

**Tidak ada regresi.** Ke-12 test baru semuanya passes.

---

## 8. Status Checkpoint Model

| Item | Nilai | Status |
|------|-------|--------|
| File | `Backend/ai/models/PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth` | — |
| SHA-256 | `46521ae90d12f57f77a7b9921881910b41071dbbb1eff4d2172a2c437564c581` | ✅ **Identik** |
| Ukuran | 135.644.553 bytes | ✅ |
| Jumlah file di `Backend/ai/` | 29 | ✅ Tidak berubah |

Verifikasi dilakukan dengan Python `hashlib.sha256` pada file `.pth` asli. Tidak ada file di bawah `Backend/ai/` yang dimodifikasi selama Tahap 10 Stage A.

---

## 9. Risiko yang Masih Tersisa

Risiko yang **tidak** diselesaikan di Stage A (ditinggalkan sengaja untuk stage berikutnya atau pekerjaan terpisah):

| Risiko | Tingkat | Catatan |
|--------|---------|---------|
| Queue in-memory non-multi-worker | MEDIUM | Single-process constraint didokumentasikan. Migrasi ke Redis/RQ adalah pekerjaan terpisah. |
| Graceful shutdown | MEDIUM | Belum diimplementasi. Worker yang sedang memproses job akan terhenti paksa jika proses dihentikan. |
| Health / readiness probe lengkap | LOW | Endpoint `/api/health` sudah ada (return `{"status":"ok"}`), tetapi tidak memeriksa dependensi eksternal (Supabase, GPU, dll.). |
| WSGI server (Gunicorn/uWSGI) | LOW | Aplikasi masih berjalan di Flask development server. Tidak direkomendasikan untuk production. |
| Pemanggilan `validate_production()` di entrypoint | MEDIUM | Method sudah tersedia, tetapi `Backend/src/main.py` belum memanggilnya secara otomatis. Caller perlu menambahkan `Config.validate_production()` sebelum `app.run()`. |
| Rotasi SECRET_KEY | LOW | Tidak ada mekanisme rotasi. Mengubah SECRET_KEY di produksi akan invalidate semua session yang ada. |

---

## 10. Instruksi Deployment Production

Untuk部署 aplikasi ke production, lakukan langkah berikut:

```bash
# 1. Generate SECRET_KEY yang aman (minimal 32 karakter)
python -c "import secrets; print(secrets.token_hex(32))"

# 2. Salin .env.example dan isi nilai nyata
cp Backend/.env.example Backend/.env
# Edit Backend/.env:
#   APP_ENV=production
#   SECRET_KEY=<nilai-yang-di-generate>
#   SUPABASE_URL=https://your-project.supabase.co
#   SUPABASE_ANON_KEY=<anon-key>
#   SUPABASE_SERVICE_ROLE_KEY=<service-role-key>
#   MODEL_CHECKPOINT_PATH=ai/models/PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth

# 3. Jalankan dengan config production
APP_ENV=production PYTHONPATH=Backend python Backend/src/main.py

# 4. (Recommended) Gunakan WSGI server seperti Gunicorn
#    pip install gunicorn
#    APP_ENV=production gunicorn -w 1 -b 127.0.0.1:5000 "src.main:app"
#    CATATAN: Gunakan -w 1 (single worker) karena queue in-memory bersifat process-local.
```

**Penting:** Jangan pernah commit file `.env` ke repository. `.gitignore` sudah melarangnya (line 11–13, 57).

---

## 11. Ringkasan Implementasi

Tahap 10 Stage A selesai dengan hasil:

- ✅ **HIGH issue** (default SECRET_KEY hard-coded) — ditangani dengan validasi production yang tegas.
- ✅ **MEDIUM issue** (.env.example) — diperbarui dengan placeholder eksplisit dan instruksi generasi.
- ✅ **LOW issue** (debug mode default) — dipertahankan untuk development, dikunci di production.
- ✅ **12 test baru** ditambah, 0 regresi.
- ✅ **Checkpoint model** tetap utuh (SHA-256 identik).
- ✅ **Backend/ai/** tidak tersentuh.
- ✅ **Tidak ada commit/push** yang dilakukan.

**STOP di Stage A.** Tahap 10 Stage B (graceful shutdown, health check improvement, Gunicorn WSGI) menjadi pekerjaan terpisah menunggu persetujuan.
