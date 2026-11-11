# REFACTORING CHANGELOG — PIXEL-T

**Tanggal:** 11 November 2026  
**Branch:** `fitur/validasi-input`  
**HEAD:** `cbb5296`  
**Status:** baseline + cleanup/regression completed pada tahap ini; **tidak ada commit/push**.  
**Sifat:** changelog perubahan cleanup + eksekusi Tahap 7 Langkah 0–1 (belum commit).

---

## 0. Ringkasan Perubahan

| No | File / Area | Status | Deskripsi | Kelas |
|---|---|---|---|---|
| 0.1 | `Backend/src/core/config.py` | M | `LLM_VALIDATION_TIMEOUT_S` default `15.0 → 30.0` | Cleanup |
| 0.2 | `Backend/src/services/llm_image_validator.py` | M | Gemini: JSON, schema, thinking low, token 1024, retry 1, timeout 30.0 | Cleanup |
| 0.3 | `tests/Backend/test_llm_image_validator.py` | M | Tes timeout/config + tes baru | Cleanup |
| 0.4 | `Backend/requirements.txt` | M | Tambah `google-genai>=3.0.0,<3.1.0` | Cleanup |
| 0.5 | `README.md` | M | Panduan instalasi/arsitektur 2-terminal | Cleanup |
| 0.6 | `Backend/.env.example` | ?? | Template backend baru | Cleanup |
| 0.7 | `Frontend/.env.example` | ?? | Template frontend baru | Cleanup |
| 0.8 | `.gitignore` | — | Verifikasi saja; tidak diubah | Cleanup |
| 1.1 | `Frontend/src/utils/analysis.ts` | M | `fetchWithTimeout`, upload timeout 90 s, `REQUEST_TIMEOUT` | Cleanup |
| 1.2 | `Frontend/src/utils/auth.ts` | M | Hapus `getCurrentUser` | Cleanup |
| 1.3 | `Backend/src/services/analysis_service.py` | M | Fallback timeout konsisten 30.0 | Cleanup |
| 1.4 | Log runtime/cache | — | `backend_foreground*.log`, `.pytest_cache`, `Frontend/dist`, `Frontend/tsconfig.tsbuildinfo` | Cleanup |

**Catatan:** file-file di atas adalah perubahan yang sudah ada pada working tree sebelum tahap laporan/rencana ini. Tahap **refactoring implementasi** belum dimulai; pada 11 Nov 2026 Tahap 7 **DISETUJUI** untuk subset **0 → 1 → 2 → 5** (Langkah 0 sedang dikerjakan, Langkah 3/4/scripts ditunda).

---

## 1. Rencana/Status Langkah R1 dari `docs/audit/refactor_lucit_plan.md`

| Langkah | Rencana | Status |
|---|---|---|
| R0 | Inventarisasi | Selesai |
| R0b | Analisis perbandingan validator LUCIT/PXIELT-T | Selesai |
| R1 | Perencanaan refactor | Selesai; menunggu approval sebelum eksekusi |
| R1 Langkah 1 | Archive diagram root | **DITUNDA** |
| R1 Langkah 2 | `.gitignore` eksplisit | **SELESAI (tanpa ubah)** |
| R1 Langkah 3 | `.env.example` sub-proyek | **SELESAI** |
| R1 Langkah 4 | README 2-terminal | **SELESAI** |
| R1 Langkah 5 | Verifikasi penuh | **SELESAI** |
| R1 Langkah 6 | Rapikan `scripts/` | **DITUNDA** |

---

## 2. Perubahan Cleanup yang Telah Diverifikasi

### 2.1 Dependency

- `Backend/requirements.txt`: `google-genai>=3.0.0,<3.1.0`.
- SDK diimport `llm_image_validator.py`, tes lulus, `pip check` lulus.

### 2.2 Konfigurasi/behavior non-AI

- Timeout LLM: `30.0` detik di config, service, tests, template.
- Frontend: timeout fetch default 30 s, upload 90 s, error `REQUEST_TIMEOUT`.
- `getCurrentUser`: dihapus setelah grep membuktikan tidak ada pemanggil aktif.
- AnalysisService fallback: 30.0.

### 2.3 Dokumentasi/instalasi

- README diperluas prasyarat/instalasi/arsitektur.
- Template env Backend/frontend dibuat.
- `.gitignore` diverifikasi.

### 2.4 File cleanup

- 10 placeholder `.gitkeep` dihapus.
- Log/cache/build dihapus; build baseline membuat ulang artefak regenerable.

### 2.5 Perubahan Langkah 1 (Tahap 7) — konsistensi backend

| Sub | File | Perubahan | Status |
|---|---|---|---|
| 1A | `Backend/src/core/auth.py` | Ekstrak `_extract_bearer_token()` + `_resolve_authenticated_user()`; ketiga decorator memakainya. Pesan error, status code, urutan validasi, `g.current_user`, dan `request.user` **identik**. | Selesai — backend auth/admin 34 tes lulus |
| 1B | `Backend/src/controllers/admin_controller.py` | Error admin memakai `APIError.to_dict()` → envelope standar `{success:false,error:{code,message}}` (5 lokasi + 404). Sukses tidak berubah; frontend hanya membaca status HTTP. | Selesai — backend 34 tes + AdminDashboard 17 tes lulus |
| 1C | `Backend/src/services/analysis_service.py` | 19 `print()` → `logger.info/error` (termasuk `exc_info=True` untuk traceback); inline `import traceback` dihapus. Tidak mencetak token/credential. | Selesai — suite backend 145 passed/1 skipped |

### 2.6 Perubahan Langkah 2 (Tahap 7) — batas polling NewAnalysis

| Sub | File | Perubahan | Status |
|---|---|---|---|
| 2A | `Frontend/src/pages/analysis/NewAnalysis.tsx` | `PROGRESS_POLL_MAX_ATTEMPTS = 300` (~10 menit pada interval 2 s); polling berhenti pada status terminal, unmount, sesi habis, respons server terstruktur, atau batas maksimum. Network/timeout dicoba ulang hingga batas, bukan dianggap kegagalan segmentasi, dan tidak memicu navigasi. | Selesai — NewAnalysis 36 tes lulus |
| 2B | `Frontend/src/utils/analysis.ts` | `REQUEST_TIMEOUT_ERROR_CODE` diekspor agar pemisahan error server vs timeout konsisten. | Selesai |

**Catatan:** perubahan pada 2A–2B adalah refactoring internal frontend; tidak ada perubahan API contract, status analisis backend, tampilan UI, tampilan progres, AI/ML, DB, maupun checkpoint. Belum di-commit.

**Catatan:** perubahan pada 1A–1C adalah refactoring internal; tidak ada perubahan API contract, auth, role/permission, AI/ML, DB, maupun checkpoint. Belum di-commit.

---

## 3. Perubahan yang TIDAK Dilakukan pada Tahap Ini

| No | Area | Alasan |
|---|---|---|
| 1 | `Backend/src/services/analysis_service.py` split | Belum disetujui; risiko tinggi |
| 2 | `Backend/src/core/auth.py` refactor | Menunggu approval; auth dilindungi |
| 3 | `Backend/src/controllers/admin_controller.py` normalize | Menunggu approval; perlu cek FE |
| 4 | `Frontend/src/pages/*` ekstraksi | Menunggu approval; UI berisiko |
| 5 | Archive `scripts/diagram` | Menunggu approval + path fix |
| 6 | Konsolidasi `docs/*.md/*.txt` | Menunggu konfirmasi skripsi |
| 7 | Hapus file tanpa bukti | Diperangi ketat |

---

## 4. Riwayat Hasil Verifikasi Setelah Cleanup

| Verifikasi | Hasil |
|---|---|
| pytest | 190 passed, 1 skipped |
| vitest | 302 passed, 19 file |
| build | sukses |
| pip check | no broken requirements |
| hash checkpoint | cocok |
| Manual E2E | **NOT TESTED** |

---

## 5. Catatan Rollback

- Perubahan source dapat dikembalikan lewat Git.
- `.env.example` baru perlu hapus manual bila rollback template.
- `.gitignore` tidak diubah, sehingga perubahan cleanup tidak menambah ignore baru.
- Tidak ada commit/push.
- Tidak ada force push/reset.

---

## 6. Kesimpulan

Tahap cleanup/regression selesai tanpa perubahan fitur atau AI/ML. Refactoring implementasi **disetujui** pada 11 Nov 2026 untuk subset **0 → 1 → 2 → 5**; Langkah 0 sedang dikerjakan, Langkah 3/4/scripts ditunda; Selanjutnya harus dikerjakan dari `REFACTORING_PLAN.md` dengan urutan yang telah disusun.
