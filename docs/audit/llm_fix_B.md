# Laporan Perbaikan B: Perbaikan Kecil Validasi Masukan LLM (Gemini Gate)

**Proyek:** PIXEL-T | **Tanggal:** 10 November 2026 | **Bahasa:** Indonesia  
**Status:** B1–B6 Selesai Diimplementasikan dan Diverifikasi Suite

---

## 1. Ringkasan Perubahan per Butir (B1–B6)

| Butir | Masalah / Temuan Audit A | Tindakan yang Diambil | Status Verifikasi |
|---|---|---|---|
| **B1** | Satuan timeout SDK `google-genai` adalah milidetik (`HttpOptions.timeout: Optional[int] in milliseconds`). Kode lama sudah menggunakan `int(timeout_s * 1000)` (15 detik → 15.000 ms), namun tanpa dokumentasi eksplisit dan belum ada tes spy pada opsi klien. | Ditambahkan komentar penjelasan satuan ms di `Backend/src/services/llm_image_validator.py:158-163`. Ditambahkan 2 tes unit spy konstruktor di `test_llm_image_validator.py` (`test_b1_timeout_milliseconds_passed_to_client` dan `test_b1_timeout_custom_value_conversion`). | **LULUS** (15.000 ms dan nilai kustom 30.000 ms terverifikasi diteruskan ke klien) |
| **B2** | Perlu pembuktian bahwa pipeline segmentasi (mask, peta probabilitas, Grad-CAM) identik antara gerbang LLM aktif vs nonaktif pada citra positif nyata. | Ditambahkan tes `test_b2_regression_mask_pipeline_not_terverifikasi` di `test_llm_image_validator.py`. Karena file checkpoint model (`MODEL_CHECKPOINT_PATH` / `.pth`) tidak tersedia di repositori kerja lokal, tes menandai dirinya dengan `pytest.skip("TIDAK TERVERIFIKASI — model checkpoint tidak tersedia di environment ini")`. | **TIDAK TERVERIFIKASI** (Checkpoint model tidak ada di lokal. Membutuhkan file `.pth` untuk uji Dice=1.0) |
| **B3** | Risiko keluaran LLM mengandung teks injeksi, non-JSON dengan kata "true", tipe boolean tidak ketat (integer 1), atau nilai confidence tidak valid (NaN/inf). | Ditambahkan 4 tes parsing injeksi di `test_llm_image_validator.py` (`test_b3_text_before_false_json_is_rejected`, `test_b3_non_json_containing_true_is_rejected`, `test_b3_is_colonoscopy_integer_one_is_rejected`, `test_b3_nan_confidence_is_rejected`). Semua skenario terbukti ditolak (fail-closed). | **LULUS** (Catatan: Menguji ketahanan parser, bukan ketahanan model LLM terhadap adversarial prompt) |
| **B4** | Fallback frontend `UNCERTAIN_COLONOSCOPY_IMAGE` di `NewAnalysis.tsx:271` menggunakan pesan usang (`"Sistem tidak dapat memastikan..."`) yang tidak sinkron dengan pesan baku server. | Diperbarui fallback di `NewAnalysis.tsx:267-272` menjadi `'Validasi citra belum dapat diselesaikan. Silakan coba lagi beberapa saat.'`. Ditambahkan 4 tes Vitest di `NewAnalysis.test.tsx` untuk memverifikasi prioritas pesan server dan konsistensi fallback untuk kedua kode error (`NOT_COLONOSCOPY_IMAGE` dan `UNCERTAIN_COLONOSCOPY_IMAGE`). | **LULUS** (Vitest 298 passed, tsc 0 error) |
| **B5** | Pesan error layanan perlu dapat diganti di satu tempat terpusat tanpa duplikasi string antar-berkas. | Dibuat konstanta `MSG_LLM_SERVICE_ERROR` di awal file `Backend/src/services/llm_image_validator.py:17-19` dan diimpor serta digunakan di `Backend/src/services/analysis_service.py:456, 494`. Ditambahkan tes konsistensi konstanta `test_b5_msg_llm_service_error_constant_matches_analysis_service`. | **LULUS** (Konstanta tunggal terpusat) |
| **B6** | Respons kosong (`response.text is None`), respons diblokir filter keamanan (`finish_reason=SAFETY`, `PROHIBITED_CONTENT`), atau terpotong (`MAX_TOKENS`) harus berakhir fail-closed (`ERROR`) dan mencatat kategori tanpa mengekspos isi citra/respons. | Ditambahkan penanganan dan kategorisasi `finish_reason` pada `_call_gemini` di `Backend/src/services/llm_image_validator.py:101-122`. Jika `finish_reason` masuk dalam `_SAFETY_REASONS`, dicatat log `category=safety`. Ditambahkan 4 tes di `test_llm_image_validator.py` (`test_b6_empty_response_text_none_fail_closed`, `test_b6_safety_blocked_response_fail_closed`, `test_b6_max_tokens_truncated_fail_closed`, `test_b6_prohibited_content_blocked_fail_closed`). | **LULUS** (Semua berakhir LlmDecision.ERROR / fail-closed) |

---

## 2. Diff Ringkas per Berkas (file:baris)

### 2.1 `Backend/src/services/llm_image_validator.py`
- **Baris 14–19:** Penambahan konstanta terpusat `MSG_LLM_SERVICE_ERROR = ("Validasi citra belum dapat diselesaikan. Silakan coba lagi beberapa saat.")` dengan catatan konsekuensi desain.
- **Baris 101–122:** Penambahan set `_SAFETY_REASONS` (`SAFETY`, `PROHIBITED_CONTENT`, `BLOCKLIST`, `SPII`, `IMAGE_SAFETY`, `IMAGE_PROHIBITED_CONTENT`) dan pencatatan log terstruktur `category=safety finish_reason=%s` vs `llm_validation_non_stop finish_reason=%s`.
- **Baris 158–163:** Penambahan dokumentasi kode eksplisit mengenai satuan timeout milidetik SDK `google-genai` pada `HttpOptions(timeout=int(timeout_s * 1000))`.

### 2.2 `Backend/src/services/analysis_service.py`
- **Baris 456:** Impor konstanta `MSG_LLM_SERVICE_ERROR` dari `app.services.llm_image_validator`.
- **Baris 494:** Penggantian string literal pesan error UNCERTAIN dengan referensi `MSG_LLM_SERVICE_ERROR`.

### 2.3 `Frontend/src/pages/analysis/NewAnalysis.tsx`
- **Baris 267–272:** Pembaruan string fallback saat `code === 'UNCERTAIN_COLONOSCOPY_IMAGE'` dari string lama (`'Sistem tidak dapat memastikan apakah berkas adalah citra kolonoskopi valid...'`) menjadi `'Validasi citra belum dapat diselesaikan. Silakan coba lagi beberapa saat.'`, selaras dengan pesan server.

### 2.4 `tests/Backend/test_llm_image_validator.py`
- **Baris 608–885 (+12 tes baru):**
  - `test_b1_timeout_milliseconds_passed_to_client`: Memverifikasi konstruktor `Client` menerima `http_options.timeout == 15000` (ms).
  - `test_b1_timeout_custom_value_conversion`: Memverifikasi nilai kustom mis. 30 detik dikonversi menjadi `30000` ms.
  - `test_b2_regression_mask_pipeline_not_terverifikasi`: Menggunakan `pytest.skip` untuk mendokumentasikan ketiadaan model checkpoint.
  - `test_b3_text_before_false_json_is_rejected`: Memverifikasi teks instruksi di luar JSON tetap ditolak.
  - `test_b3_non_json_containing_true_is_rejected`: Memverifikasi keluaran non-JSON yang memuat "true" ditolak.
  - `test_b3_is_colonoscopy_integer_one_is_rejected`: Memverifikasi nilai integer `1` (bukan boolean murni `True`) ditolak.
  - `test_b3_nan_confidence_is_rejected`: Memverifikasi nilai `NaN` pada field confidence ditolak.
  - `test_b6_empty_response_text_none_fail_closed`: Memverifikasi `response.text = None` menghasilkan `ERROR`.
  - `test_b6_safety_blocked_response_fail_closed`: Memverifikasi respons terblokir filter keamanan dengan `finish_reason="SAFETY"` menghasilkan `ERROR` dan mencatat log keamanan.
  - `test_b6_max_tokens_truncated_fail_closed`: Memverifikasi respons terpotong `MAX_TOKENS` menghasilkan `ERROR`.
  - `test_b6_prohibited_content_blocked_fail_closed`: Memverifikasi respons `PROHIBITED_CONTENT` menghasilkan `ERROR`.
  - `test_b5_msg_llm_service_error_constant_matches_analysis_service`: Memverifikasi konstanta pesan layanan sama persis dengan yang diharapkan API.

### 2.5 `Frontend/src/pages/analysis/NewAnalysis.test.tsx`
- **Baris 361–427 (+4 tes baru B4):**
  - `B4: penolakan NOT_COLONOSCOPY_IMAGE memprioritaskan pesan dari server`
  - `B4: penolakan NOT_COLONOSCOPY_IMAGE dengan error non-Error menggunakan fallback baku`
  - `B4: penolakan UNCERTAIN_COLONOSCOPY_IMAGE memprioritaskan pesan dari server`
  - `B4: penolakan UNCERTAIN_COLONOSCOPY_IMAGE dengan error non-Error menggunakan fallback baku konsisten`

---

## 3. Hasil Test Suite Sebelum vs Sesudah

| Test Suite | Sebelum Perbaikan B | Sesudah Perbaikan B | Status |
|---|---|---|---|
| **pytest** (Backend & AI) | **177 passed** | **188 passed, 1 skipped** (0 failed) | ✅ Bertambah +11 tes lulus, 1 skip (B2) |
| **vitest** (Frontend) | **294 passed** | **298 passed** (0 failed) | ✅ Bertambah +4 tes lulus |
| **TypeScript Typecheck** (`tsc -b --noEmit`) | **0 errors** | **0 errors** | ✅ Lulus bersih tanpa komplain tipe |

---

## 4. Hash SHA-256 Sebelum vs Sesudah Perbaikan B

| Berkas | SHA-256 Sebelum (dari `hash_sebelum_llm_fix.txt`) | SHA-256 Sesudah | Status Perubahan |
|---|---|---|---|
| `Backend/src/services/llm_image_validator.py` | `52ecb6368b6ff4de718bde50e6b62ef09879ae302e838ceeca6b5c80b7aaea12` | `804b22ebe0dd672e0a514ef49e57028d3fdfa1ce2204bc579ec6d9a47c184b27` | Diubah (B1, B5, B6) |
| `Backend/src/core/config.py` | `897fd1e524b45e7c5ad2b869828fa779c5d37785bbeeb63a023c5b3a82dd6761` | `897fd1e524b45e7c5ad2b869828fa779c5d37785bbeeb63a023c5b3a82dd6761` | **Sama** (tidak diubah) |
| `Backend/src/services/analysis_service.py` | `6b20024d4959c98f7d21fee3230f621a444eec9627d742883b7b20b8631a8bdc` | `86b5b9700f9b3f896649ec0afe73b86bde0851e34ed521329e529a0236aa8191` | Diubah (B5) |
| `tests/Backend/test_llm_image_validator.py` | `26517e7f73fd4ad7ab835ed7182d3bfab14582059f66ec50ca66e7ba4897c874` | `971b7ca865485858f562b25f66e388883ad45637ab5db5c190dc44a8122c1c65` | Diubah (B1, B2, B3, B5, B6) |
| `Frontend/src/pages/analysis/NewAnalysis.tsx` | `289c50ae0d3a06ded2ed7b95de7f8806004908618ef58f304423e623b34ee8ce` | `cfba59cc7e59e67e2b737c9215c70a9f5da8aee1ad7feecca8567727f3fc2e81` | Diubah (B4) |
| `Frontend/src/pages/analysis/NewAnalysis.test.tsx` | *(tidak dicatat di hash awal)* | `29b5cf6295394aadac96c855f12bd7dd5e3b50e2cbbb30bd8e84ac21bb216206` | Diubah (B4 tes) |

---

## 5. Status Git dan Output Diff Stat

### `git status --short` (pada berkas terkait)
```
 M Backend/src/services/analysis_service.py
 M Frontend/src/pages/analysis/NewAnalysis.test.tsx
 M Frontend/src/pages/analysis/NewAnalysis.tsx
?? Backend/src/services/llm_image_validator.py
?? tests/Backend/test_llm_image_validator.py
```

### `git diff --stat`
```
 Backend/src/services/analysis_service.py         | 158 ++++++++++++++++++++++-
 Frontend/src/pages/analysis/NewAnalysis.test.tsx |  67 ++++++++++
 Frontend/src/pages/analysis/NewAnalysis.tsx      |  24 +++-
 3 files changed, 242 insertions(+), 7 deletions(-)
```

---

## 6. Pembuktian Isolasi Dampak (Halaman Lain Tidak Terpengaruh)

Fungsi yang diubah dalam backend hanya:
- `validate_with_llm` di `llm_image_validator.py`
- `AnalysisService.create_analysis()` di `analysis_service.py`

**Pemanggil `create_analysis` di seluruh repositori:**
Satu-satunya pemanggil adalah `AnalysisController.create_analysis()` (`Backend/src/controllers/analysis_controller.py:32`), yang dipetakan secara eksklusif ke route `POST /api/analysis` (`Backend/src/routes/analysis.py:22`).
Tidak ada endpoint lain, controller autentikasi, controller profil dokter, controller riwayat, atau endpoint admin yang memanggil fungsi ini. Halaman Login, Sign Up, History, Doctor Profile, Admin, dan Sign Out terisolasi sepenuhnya.

---

## 7. Pernyataan Batasan & Keamanan

1. **Tidak Ada Git Commit:** Tidak ada `git commit`, `git reset`, `git clean`, `git stash`, atau `git checkout` yang dijalankan.
2. **Tidak Ada API Key Tercetak:** Seluruh pengujian B1–B6 berjalan menggunakan mock/spy. Tidak ada pemanggilan API Gemini nyata yang dilakukan pada Bagian A dan B. Tidak ada API key, token, atau variabel rahasia yang dicetak ke konsol maupun disimpan ke dalam berkas log/laporan.
3. **B2 TIDAK TERVERIFIKASI:** Model checkpoint `.pth` tidak tersedia di repositori kerja lokal. Untuk memverifikasi nilai Dice=1.0 secara riil, diperlukan penyalinan file bobot model ke direktori `models/` yang dikonfigurasi pada environment produksi.

