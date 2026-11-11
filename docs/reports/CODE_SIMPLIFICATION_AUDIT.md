# CODE SIMPLIFICATION AUDIT — PIXEL-T

**Tanggal:** 11 November 2026  
**Branch:** `fitur/validasi-input` (HEAD `cbb5296`)  
**Sifat:** audit read-only. **Tidak ada refactoring kode yang dilakukan pada tahap ini.**  
**Prinsip:** safety > functionality > correctness > maintainability > simplicity.  
**Larangan yang dipatuhi:** tidak mengubah AI/ML (U-Net, ResNet50, checkpoint, preprocessing, TTA, threshold 0.55, Grad-CAM, dataset/split), API contract, DB schema, auth/RLS, atau alur utama.

---

## 0. Ringkasan Temuan

| ID | Temuan | Lokasi | Level | Kandidat tindakan | Status |
|---|---|---|---|---|---|
| S1 | `analysis_service.py` 1147 baris total (1029 baris non-kosong), 32 method/class, tanggung jawab bercampur | `Backend/src/services/analysis_service.py` | Tinggi | Pecah internal di balik facade stabil | **Belum diubah** |
| S2 | 19 `print()` inline, termasuk 17 log `[CORRELATION]`/`[TIMING]` | `analysis_service.py:254–1083` | Sedang | Ganti dengan logger terstruktur/helper | **Selesai (Langkah 1C)** |
| S3 | Tiga decorator auth menduplikasi parsing Bearer | `Backend/src/core/auth.py:11,87,176` | Rendah | Ekstrak `_extract_bearer_token` | **Selesai (Langkah 1A)** |
| S4 | Envelope error admin berbeda dari handler global | `Backend/src/controllers/admin_controller.py:26,46,63,84,98` | Sedang | Normalisasi envelope; cek FE | **Selesai (Langkah 1B)** |
| S5 | `NewAnalysis` polling tidak memiliki batas maksimum eksplisit | `Frontend/src/pages/analysis/NewAnalysis.tsx:167–209` | Sedang | Tambah `MAX_POLL_ATTEMPTS`, status timeout | **Selesai (Langkah 2)** |
| S6 | Halaman frontend besar | `DoctorProfile.tsx` 974, `NewAnalysis.tsx` 592, `History.tsx` 577, `AdminDashboard.tsx` 505, `Login.tsx` 487 | Sedang | Ekstrak subkomponen/helper internal | **Belum diubah** |
| S7 | Domain gate dijalankan di upload dan lagi di `run_pipeline` | `analysis_service.py:428`, `Backend/ai/inference/pipeline.py:135` | Rendah | **Pertahankan** sebagai defense-in-depth | Tidak diubah |
| S8 | Flag `tta_enabled` tidak dibaca loop aktif | `Backend/ai/inference/segmentation.py:18-21` | Rendah | **Jangan ubah**; sudah didokumentasikan dan dilindungi | Tidak diubah |
| S9 | Fallback LLM timeout sempat 15.0 vs config 30.0 | `analysis_service.py:461-468` | Rendah | Sudah diselaraskan ke 30.0 | **Selesai (cleanup)** |
| S10 | `fetch` frontend sempat tanpa timeout | `Frontend/src/utils/analysis.ts` | Sedang | Sudah ditambahkan `fetchWithTimeout` + `REQUEST_TIMEOUT` | **Selesai (cleanup)** |
| S11 | `getCurrentUser` tidak terpakai | `Frontend/src/utils/auth.ts` (sebelum cleanup) | Rendah | Dihapus setelah grep | **Selesai (cleanup)** |
| S12 | Duplikasi dokumen `.md`/`.txt` | `docs/APIContract`, `StyleGuide`, `DataModelSpecification`, laporan forensik | Rendah | Jangan gabung sebelum konfirmasi skripsi | Ditunda |
| S13 | Root tooling diagram bercampur proyek | 7 file root | Sedang | Archive setelah path `__dirname` diperbaiki | Ditunda |

---

## 1. S1 — `AnalysisService` god service

### 1.1 Bukti

- File: `Backend/src/services/analysis_service.py`, **1147 baris total (1029 baris non-kosong)**.
- Class/def utama: `AnalysisProgressReporter` (baris 65), `AnalysisJobQueue` (151), `AnalysisService` (270), `validate_and_decode_image` (332), `create_analysis` (400), `get_analysis` (609), `list_user_analyses` (762), `delete_analysis` (815), `_run_analysis_job` (888), `_execute_pipeline` (908), `_require_domain_accept` (1097), `run_segmentation` (1120), `run_gradcam` (1135).
- Tanggung jawab:
  1. Validasi file/gambar.
  2. Gate domain heuristik.
  3. Gate LLM Gemini.
  4. Path/storage Supabase.
  5. Insert/update DB.
  6. Antrean job & worker thread.
  7. Progress reporter.
  8. Pipeline AI + upload artefak.
  9. Pembacaan detail/history/delete.

### 1.2 Mengapa berisiko

- Perubahan kecil pada satu method dapat memengaruhi upload, antrean, atau status DB.
- Test suite sudah mencakup 190 tes, tetapi cakupan perilaku async/queue mungkin tidak 100%.
- Nama class/method `AnalysisService`, `AnalysisJobQueue`, `AnalysisProgressReporter` disebut dalam naskah skripsi; **nama publik tidak boleh berubah**.
- `analysis_service.py` adalah titik integrasi AI/DB/storage, sehingga refactor harus mempertahankan signature dan perilaku.

### 1.3 Rekomendasi (belum dieksekusi)

Pecah **internal** menjadi modul dengan facade tetap:

```text
services/analysis/
├── __init__.py          # re-export AnalysisService (nama publik tetap)
├── service.py           # facade/class AnalysisService
├── progress.py          # AnalysisProgressReporter
├── queue.py             # AnalysisJobQueue
├── validation.py        # validate_and_decode_image + domain/LLM gate
├── pipeline_runner.py   # _execute_pipeline, artifact upload
└── queries.py           # get/list/delete read/write
```

**Syarat:** tidak mengubah API, signature publik, status lifecycle, error code, atau urutan gate. Uji regresi penuh sebelum/sesudah.

---

## 2. S2 — Log `print` inline

### 2.1 Bukti

- 19 `print(` di `analysis_service.py`; 17 di antaranya berisi `[CORRELATION]`, `[TIMING]`, `[DOMAIN]`, atau `[LLM_DOMAIN]`.
- Contoh: baris `413`, `432`, `481`, `500`, `518`, `549`, `599`, `602`, `619`, `758`, `943`, `979`, `982`, `1035`, `1039`, `1083`.
- Sebagian logging memakai `logger` (`logger = logging.getLogger(__name__)`), sebagian `print`.

### 2.2 Dampak

- Duplikasi format, sulit dimatikan di production.
- Informasi timing/korelasi bercampur dengan stdout server.
- Tidak mengubah hasil, tetapi menyulitkan observability.

### 2.3 Rekomendasi

- Buat helper `log_stage(stage, **fields)` atau gunakan `logger.info`.
- Pertahankan isi pesan yang berguna untuk audit.
- Jangan mengubah alur; hanya mekanisme logging.
- Jangan menghapus correlation ID pada tahap awal.

---

## 3. S3 — Duplikasi parsing Bearer

### 3.1 Bukti

- `require_auth` di `auth.py:11`.
- `require_admin` di `auth.py:87`.
- `require_approved_doctor` di `auth.py:176`.
- Ketiganya membaca `Authorization`, memisahkan `Bearer`, dan memvalidasi token; pola yang sama berulang.
- Ada 12 kemunculan terkait `Authorization`/`split`/`parts[0].lower() == 'bearer'`.

### 3.2 Rekomendasi

```python
def _extract_bearer_token():
    # raise APIError("UNAUTHORIZED", ...) bila tidak valid
```

Panggil helper dari ketiga decorator. **Jangan mengubah** pesan error, status code, atau urutan validasi karena auth dilindungi dan memiliki tes.

---

## 4. S4 — Envelope error admin tidak konsisten

### 4.1 Bukti

- Handler global `core/errors.py`: `{"success": False, "error": {"code": ..., "message": ...}}`.
- `admin_controller.py` mengembalikan 5 kali:
  `{"success": False, "error": e.message, "code": e.code}`.
- Perbedaan: `error` berupa string + `code` di root, bukan objek `{code, message}`.

### 4.2 Risiko

- Frontend yang membaca `error.message` bisa mendapat `undefined` pada endpoint admin.
- Kontrak API menjadi tidak seragam.

### 4.3 Rekomendasi

- Normalisasi ke envelope global.
- Cek `AdminDashboard.tsx`/`services/*` sebelum mengubah; jangan mengubah kontrak tanpa memastikan client.
- Tambahkan test regresi envelope.

---

## 5. S5 — Polling `NewAnalysis` tanpa batas eksplisit

### 5.1 Bukti

- `PROGRESS_POLL_INTERVAL_MS = 2000` (`NewAnalysis.tsx:21`).
- `pollCount` hanya untuk log (`:167-178`), lalu `setTimeout` berulang (`:194`, `:209`).
- Tidak ada `MAX_POLL_ATTEMPTS` seperti `AnalysisResult.tsx:10` (`MAX_POLL_ATTEMPTS = 12`).

### 5.2 Risiko

- Jika backend macet/status tidak terminal, polling berjalan tanpa henti.
- Beban server dan UX memburuk.

### 5.3 Rekomendasi

- Tambah batas maksimum (misalnya 60 percobaan = 2 menit) dan status “masih diproses, coba buka hasil nanti”.
- Jangan mengubah status API; hanya perilaku klien.
- Uji `NewAnalysis.test.tsx`.

---

## 6. S6 — Halaman frontend besar

| File | Baris | Bagian yang bisa diekstrak |
|---|---:|---|
| `pages/profile/DoctorProfile.tsx` | 974 | form profil, avatar upload, state/modal |
| `pages/analysis/NewAnalysis.tsx` | 592 | dropzone, preview, progress, error/queue handling |
| `pages/history/History.tsx` | 577 | filter, list row, konfirmasi hapus |
| `pages/admin/AdminDashboard.tsx` | 505 | stat cards, table, filter, modal approve/reject |
| `pages/auth/Login.tsx` | 487 | form, role selector, error/loading |

**Rekomendasi:** ekstrak komponen presentasional/helper dengan nama yang jelas, tanpa mengubah DOM, teks, gaya, route, atau kontrak API. Verifikasi dengan snapshot/behavior test yang sudah ada.

---

## 7. Temuan yang **tidak boleh** “disederhanakan”

| Temuan | Alasan |
|---|---|
| Domain gate ganda (upload + pipeline) | Defense-in-depth; `pipeline.py:135` menolak non-`ACCEPT` sebelum inferensi |
| `tta_enabled` tidak dibaca loop aktif | Perilaku model dilindungi; sudah didokumentasikan di `segmentation.py:18-21` |
| Threshold 0.55 | Bagian dari model/config yang dilindungi |
| Checkpoint 135.6 MB dan SHA-256 | Bukti penelitian; jangan diubah/dihapus |
| TTA 5 skala × 5 orientasi | Perilaku inferensi; jangan diubah |
| `GradCAMResult`, `PipelineResult`, `SegmentationResult` | Nama publik skripsi |
| `.md`/`.txt` docs | Artefak skripsi; jangan dihapus tanpa konfirmasi |
| `scripts/*` dan `research/*` | Bukti eksperimen; jangan dihapus |

---

## 8. Kandidat Perbaikan Berdasarkan Risiko

### Rendah — dapat dipertimbangkan lebih dulu setelah approval

1. Ekstrak helper Bearer auth (S3).
2. Normalisasi envelope admin + test (S4).
3. Ganti `print` dengan logger (S2).

### Sedang — perlu test regresi UI

4. Batas polling `NewAnalysis` (S5).
5. Ekstraksi subkomponen halaman besar (S6).

### Tinggi — hanya setelah baseline final dan persetujuan eksplisit

6. Pemecahan `analysis_service.py` (S1).

---

## 9. Kesimpulan

PIXEL-T tidak membutuhkan “penulisan ulang”. Penyederhanaan yang aman adalah **pemecahan internal, konsistensi envelope/logging, dan batas polling**, bukan perubahan model, API, database, atau auth. Tidak ada perubahan kode yang dilakukan pada audit ini; semua rekomendasi menunggu approval pada `REFACTORING_PLAN.md`.
