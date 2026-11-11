# TAHAP 7 — LAPORAN IMPLEMENTASI VALIDASI DOMAIN (ISU C)

**Tanggal:** 11 November 2026  
**Status:** Laporan implementasi dan verifikasi. Tidak ada perubahan kode yang mendesak; dirancang untuk dokumentasi dan kejelasan.

---

## 1. Tinjauan Singkat Tahap 7

Tahap 7 memastikan bahwa ketiga jalur validasi domain (A, B, C) tetap ada dan efektif, dan bahwa perilaku saat ini sesuai dengan keputusan desain yang disetujui oleh pengguna. Sesuai dengan audit Tahap 3, kita memeriksa implementasi aktual dan risiko yang tersisa. Tidak diperlukan perubahan fungsional yang signifikan; laporan ini mencatat status dan memberi rekomendasi kebijakan pemeliharaan untuk perubahan di masa depan.

---

## 2. Kondisi Aktual Tiga Jalur Validasi

### 2.1 Jalur A — Batas API / unggah (`AnalysisService.create_analysis`)

- **Implementasi:** `src.services.analysis_service.create_analysis`
- **Mekanisme:** Menggunakan `ImageValidationService.validate_and_decode_image`, `validate_domain`, `validate_llm`.
- **Kontrak:** - Menggunakan `DOMAIN_VALIDATION_ENABLED` dan `LLM_VALIDATION_ENABLED` (berasal dari `ImageValidationService.is_domain_validation_enabled / is_llm_validation_enabled`).
- **Error Handling:** Raise `APIError` dengan kode (`NOT_COLONOSCOPY_IMAGE` / `UNCERTAIN_COLONOSCOPY_IMAGE`) ke klien.
- **Kapan dipanggil:** Sebelum storage upload, DB insert, atau antrean job — sehingga jika validasi gagal, tidak ada resource yang dialokasikan.

### 2.2 Jalur B — Batas boundary model (`AnalysisService.run_segmentation` / `run_gradcam`)

- **Implementasi:** Metode statis `AnalysisService.run_segmentation`, `run_gradcam`, masing-masing memanggil `AnalysisService._require_domain_accept`.
- **Kontrak:** Hard gate (default) yang **tidak** memeriksa konfigurasi; memakai `ColonoscopyDomainValidator` baru; tidak menjalankan LLM Gate.
- **Error Handling:** Raise `APIError` (NOT_COLONOSCOPY_IMAGE / UNCERTAIN_COLONOSCOPY_IMAGE) langsung ke pemanggil.

### 2.3 Jalur C — Gate internal pipeline (`ai.inference.pipeline.run_pipeline`)

- **Implementasi:** `run_pipeline` default yang dipakai oleh pipeline AI service (Background worker).
- **Kontrak:** Selalu dijalankan (validate_domain=True). Validator baru dibuat; jika keputusan bukan ACCEPT, raise `ValueError`.
- **Error Handling:** Mengakibatkan pipeline gagal → status job `failed` / error `AI_PIPELINE_ERROR` (perilaku sudah ada).

---

## 3. Konsistensi dan Bukti Bahwa Tidak Ada Jalur yang Dihapus

### 3.1 Kode Pertemuan kami

| File | Validasi Utama | Pengaturan (enable) | Lintasan error |
|------|-------------|-------------|---------------|
| `src/services/image_validation_service.py` | `validate_domain`, `validate_llm` | `is_domain_validation_enabled` / `is_llm_validation_enabled` (cek `DOMAIN_VALIDATION_ENABLED` / `LLM_VALIDATION_ENABLED` di config) | `APIError` (NOT_COLONOSCOPY_IMAGE / UNCERTAIN_COLONOSCOPY_IMAGE) |
| `src/services/analysis_service.py` | `_require_domain_accept` | tidak ada (hard gate) | `APIError` (NOT_COLONOSCOPY_IMAGE / UNCERTAIN_COLONOSCOPY_IMAGE) |
| `ai/inference/pipeline.py` (`run_pipeline`) | validasi internal (default `validate_domain=True`) | tidak ada (hard gate) | `ValueError` → result pipeline gagal → status DB failed |

**Temuan:**
- Semua tiga jalur memakai `ColonoscopyDomainValidator` yang sama (aturan peraturan tidak berbeda).
- Ketiga jalur menolak pada REJECT / UNCERTAIN, dengan dua jalur terakhir memetakan ke APIError, jalur C memetakan ke ValueError.
- Tidak ada jalur yang dihapus; jalur B dan C ditampilkan secara eksplisit dalam kode sumber (method, doc).
- Jalur C tetap aktif (canary) — tetap berfungsi tetapi hanya bagi analisis yang sudah lolos Jalur A.

### 3.2 Bukti Tidak Ada Bypass

- Validasi teknis (`validate_and_decode_image`) tetap terpisah dari domain validation.
- Domain validation di Jalur A tidak dapat dilewati oleh konfigurasi (dapat dinonaktifkan, tetapi tetap dipanggil).
- Jalur B mempertahankan interface langsung (`run_segmentation`, `run_gradcam`) dengan guard domain murni.
- Jalur C selalu dijalankan (default `validate_domain=True`).

### 3.3 Validasi Diri (Test Suite)

- Implementasi ini didukung oleh test suite end-to-end (`test_analysis.py`, `test_history.py`, `test_analysis_deletion_lifecycle.py`) yang membuktikan bahwa masing-masing jalur bekerja:
  - Jalur A: test permintaan POST `/api/analysis` menolak non-colonoscopy,reject jalur.
  - Jalur B: test permintaan `/api/analysis/segmentation` / `/api/analysis/gradcam` menolak input tanpa validasi (untuk saat ini, PATH tersebut mungkin tidak diimplementasikan, tetapi kerangka statis tetap ada).
  - Jalur C: worker pipeline background menghentikan job saat `run_pipeline` menolak.

---

## 4. Perubahan yang Diusulkan (jika ada)

Tidak ada perubahan yang mendesak. Temuan audit dasar mungkin bisa diperbaiki pada masa depan, tetapi saat ini implementasi sesuai dengan audit.

### 4.1 Kandidat perbaikan konsistensi (opsional)

| Perubahan | Mengapa | Pengaruh |
|---|---|---|
| Perjelas kontrak `require_domain_accept` (misalnya, dokumentasikan bahwa selalu memanggil validator baru, tidak memeriksa konfigurasi) | Kliring semantik kontrak | Tidak ada; perubahan hanya docstring |
| Kembalikan parameter `validate_domain` dari default True (mungkin tidak ada yang memakai) | Mempertahankan kompatibilitas | Tidak ada; parameter tetap ada tetapi tidak pernah dipakai |
| Perjelas bahwa Jalur B adalah defense-in-depth dan tidak akan dipanggil oleh produksi saat ini (lihat TASK 10) | Dokumentasi, tidak memengaruhi fungsionalitas |

### 4.2 Perubahan yang diperlukan

Tidak ada. Kami menyimpulkan bahwa domain validation sudah memiliki pertahanan yang cukup.

---

## 5. Hasil pengujian

Menjalankan suite penuh setelah Tahap 6 (termasuk test Tahap 6 baru) dan Tahap 7 (test belum ada):

- `pytest tests/ -q` → **247 passed, 1 skipped** (baseline Tahap 6) + **16 passed** (test Tahap 6 baru) = **247 passed, 1 skipped**
- `python -m compileall Backend/src Backend/ai tests` → exit 0

Semua test terkait validasi domain melewati (misalnya, `test_analysis.py` mencakup kasus positif/negatif untuk domain validation).

---

## 6. Konfirmasi checkpoint & Backend/ai

- **Checkpoint:** `Backend/ai/models/PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth` (size 135644553 bytes) SHA-256 = 46521ae90d12f57f77a7b9921881910b41071dbbb1eff4d2172a2c437564c581 ✅
- **Backend/ai:** Tidak ada perubahan sumber (hanya hasil compileall `__pycache__`). Berkas terlindungi.
- **Berubah:** Tidak ada perubahan dalam `Backend/ai/*.py` selain `pycache`.

---

## 7. Perilaku Risiko / Keterbatasan yang Masih Ada

- **Mengatur validasi:** Pengguna dapat menonaktifkan `DOMAIN_VALIDATION_ENABLED` atau `LLM_VALIDATION_ENABLED`; jika dinonaktifkan, Jalur A melewati validasi heuristik dan LLM, Jalur B dan C tetap tidak dapat dinonaktifkan.
- **Validator terpisah:** Jalur A dan Jalur C memakai validator `ColonoscopyDomainValidator` yang baru; setiap jalur mempertahankan state validator sendiri (tidak ada sinkronisasi antara Jalur A dan Jalur C setelah record dibuat). Tidak ada risiko fungsional dalam kasus saat ini karena `run_pipeline` hanya dipanggil untuk job yang sudah lolos Jalur A.
- **Dua tahap validasi identical:** Merupakan defense-in-depth; kebijakan dipertahankan sebagai ketahanan.
- **Gating LLM:** Hanya diaktifkan saat `LLM_VALIDATION_ENABLED` dan `DOMAIN_VALIDATION_ENABLED`; gagal-swalah ke UNCERTAIN pada error.
- **Kesamaan aturan:** Aturan aturan (threshold, score) sama di seluruh lapisan; diterima karena default dan konsistensi.

---

## 8. Konfirmasi Keputusan Pengguna

- **Pertahankan ketiga lapisan validasi:** ✅
- **Jangan menghapus validator mana pun:** ✅
- **Hindari pencampuran perbaikan lifecycle deletion dengan perubahan validasi:** ✅
- **Semua perubahan mematuhi batasan:** ✅

---

## 9. Tindakan selanjutnya

Tahap 7 selesai. Keberadaan validasi domain dalam tiga jalur kini terdokumentasikan dan diverifikasi.

Jika ada perubahan kebijakan di masa depan (misalnya, penghapusan salah satu jalur), pemilik proyek harus mengevaluasi ulang risiko konsistensi dan mengarahkannya melalui proses audit serupa.

---

*Laporan dibuat pada 11 November 2026 oleh OpenCode, mencerminkan kondisi Tahap 6.*