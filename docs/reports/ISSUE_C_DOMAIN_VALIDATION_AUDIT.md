# AUDIT ISU C — VALIDASI DOMAIN PIXEL-T: DUA/JALUR BERBAGAI

**Tanggal:** 11 November 2026  
**Status:** Audit & dokumentasi **hanya**. **Tidak ada** perubahan kode, prompt, threshold, provider, fallback, urutan, atau keputusan validasi yang dilakukan pada tahap ini.  
**Scope:** Menjawab dua-duanya: (1) di mana masing-masing jalur validasi domain dipanggil, (2) apakah kedua jalur sama atau berbeda, (3) dampak keputusan, (4) kemungkinan saling melewati.

> Catatan pengembangan: laporan ini dibuat di akhir Tahap 3 refactoring (ekstraksi `ImageValidationService`). Audit dilakukan pada kode yang sudah berupa tahap ekstraksi tersebut. Semua temuan berdasarkan kode aktual `Backend/src/services/*` dan `Backend/ai/inference/*`.

---

## 1. Konteks Singkat

Validasi domain kolonoskopi di PixéLT memiliki dua jalur utama yang terbentuk sebelum ekstraksi service, yaitu:

1. **Jalur A (Primary) — Batas saat unggah / API (`AnalysisService.create_analysis`)**
2. **Jalur B (Defensif) — Batas model / inference langsung (`AnalysisService.run_segmentation` / `run_gradcam`)**

Ditambah **temuan lapangan**: internal pipeline AI (`Backend/ai/inference/pipeline.py::run_pipeline`) juga memuat gerbang domain sendiri (Jalur C), sehingga alur riil produksi dapat melibatkan tiga titik pemeriksaan domain pada satu job analisis yang berjalan.

Tahap ini **tidak mengubah** perilaku ketiga jalur tersebut. Audit Isu C hanya memetakan perilaku yang sudah ada.

---

## 2. Pemetaan Jalur Validasi Domain

### Jalur A — Batas ungguh / API (Primary Gate, upload path)

**Lokasi implementasi (pasca-Tahap-3):**
- `Backend/src/services/image_validation_service.py`
  - `ImageValidationService.validate_and_decode_image(...)` — validasi teknis (MIME, ukuran ≤ 10 MB, decode wajib, dimensi, kecocokan MIME vs konten).
  - `ImageValidationService.validate_domain(...)` — gerbang heuristik kolonokopia.
  - `ImageValidationService.validate_llm(...)` — gerbang sekunder LLM (Gemini Gate).

**Lokasi pemanggil:** `AnalysisService.create_analysis` → delegasi tipis ke `ImageValidationService`.

**Kapan dipanggil:**
1. Setelah validasi teknis lolos (sebelum storage upload, DB insert, queue enqueue).
2. Hanya jika `ImageValidationService.is_domain_validation_enabled` **true** (dari `enforce_domain_validation` atau konfigurasi `DOMAIN_VALIDATION_ENABLED`).
3. Setelah heuristik menghasilkan keputusan (langkah ini: heuristik → jika keputusan bukan ACCEPT, LLM **tidak** dijalankan; fail-closed / short-circuit).

**Keputusan & error:**
- Heuristic **REJECT** → `APIError("NOT_COLONOSCOPY_IMAGE", ...)` → 400 → **tidak** ada storage/DB/enqueue.
- Heuristic **UNCERTAIN** → `APIError("UNCERTAIN_COLONOSCOPY_IMAGE", ...)` → 400 → **tidak** ada storage/DB/enqueue.
- Heuristic **ACCEPT** → lanjut ke LLM.
- LLM **REJECT** (atau confidence < `LLM_VALIDATION_MIN_CONF` = 0.80) → `APIError("NOT_COLONOSCOPIC..." → "NOT_COLONOSCOPY_IMAGE", ...)` → 400.
- LLM **ERROR / gagal** (timeout, quota, key kosong, respons tidak valid) → `APIError("UNCERTAIN_COLONOSCOPY_IMAGE", MSG_LLM_SERVICE_ERROR)` → 400.
- LLM **PASS** → lanjut storage → DB → enqueue → pipeline.

### Jalur B — Batas model / inference langsung

**Lokasi implementasi:** `Backend/src/services/analysis_service.py` (`AnalysisService._require_domain_accept`) → delegate ke `ImageValidationService.require_domain_accept` (static method).

**Pemanggil riil saat ini:** `AnalysisService.run_segmentation` dan `AnalysisService.run_gradcam` (hook defansif; belum ada pemanggil HTTP produksi yang memakainya — TASK 10).

**Kapan dipanggil:**
- Setiap kali pemanggil memasuki boundary model langsung, tanpa melalui `create_analysis`.

**Karakteristik:**
- Membuat `ColonoscopyDomainValidator` **baru** (default parameter) per panggilan.
- **Tidak memeriksa** `DOMAIN_VALIDATION_ENABLED`.
- **Tidak menjalankan** LLM Gate.
- Hanya hasil heuristik: REJECT / UNCERTAIN → raise; ACCEPT → lolos ke inferensi.

### Jalur C — Internal pipeline AI (defense-in-depth / redundansi)

**Lokasi implementasi:** `Backend/ai/inference/pipeline.py::run_pipeline` (tidak disentuh Tahap 1–3).

**Lokasi pemanggil:** `Backend/src/services/analysis_pipeline_service.py::AnalysisPipelineService.execute` → `pipeline_runner(...)` dengan runner default `ai.inference.pipeline.run_pipeline`.

**Kapan dipanggil:** Setiap kali pipeline analisis benar-benar dijalankan (dari background worker untuk analisis yang sudah lolos Jalur A).

**Karakteristik:** Membuat `ColonoscopyDomainValidator` **baru** (default parameter) dan memvalidasi citra yang sudah ter-decode → jika decision ≠ ACCEPT → `raise ValueError("Domain validation failed (...)")`.

---

## 3. Apakah Kedua/Jalur Berbeda?

### 3.1 Perbedaan Mekanis

| Dimensi | Jalur A (create_analysis) | Jalur B (run_segmentation/run_gradcam) | Jalur C (run_pipeline) |
|---|---|---|---|
| Titik pemeriksaan | Batas ungguh/API | Batas model/inference | Dalam pipeline (sebelum preprocessing/inference) |
| Validasi teknis | Ya (ukuran/MIME/decode/dimensi) | Tidak (butuh bytes valid sudah lolos sebelumnya) | Ya (decode dulu) |
| Validator domain | `ImageValidationService` → validator **yang di-inject** atau default baru | `ImageValidationService.require_domain_accept` → validator default **baru** | `ColonoscopyDomainValidator()` **baru** (default) |
| Konfigurasi gating | `DOMAIN_VALIDATION_ENABLED` / `enforce_domain_validation`; LLM `LLM_VALIDATION_ENABLED` + model/min-conf/timeout | Tidak ada gating (hard gate) | Tidak ada gating konfigurasi pada level pipeline (parameter `validate_domain` ada tetapi inert) |
| LLM Gate | Ya (sekunder, hanya setelah heuristik ACCEPT) | Tidak | Tidak |
| Jenis error pada REJECT/UNCERTAIN | `APIError("NOT_COLONOSCOPY_IMAGE"/"UNCERTAIN_COLONOSCOPY_IMAGE", status 400)` | Exception domain (APIError identik pada level API) sebelum masuk blok inferensi | `ValueError` → ditangkap oleh pemanggang pipeline → status DB `failed` / error `AI_PIPELINE_ERROR` |

### 3.2 Kesamaan

- Semua jalur memakai algoritma domain yang sama: `ColonoscopyDomainValidator` (fitur: dimensi/min-aspek, rasio aktif, mukosa/kromatisitas CIE L*a*b*/HSV, cool-hue penalty, line-density Hough, glint, composite confidence → threshold accept 0.55, dsb.).
- Semua jalur memakai aturan keputusan yang sama: `ACCEPT` / `REJECT` / `UNCERTAIN`.
- Semua jalur menolak sebelum preprocessing/inference (kecuali Jalur B/C memakai entry yang sudah terdecode).

### 3.3 Perbedaan Desain yang Disengaja / Perbedaan Konteks

- **Jalur A** adalah gerbang *produksi*: menggabungkan validasi teknis, heuristik, dan LLM dengan fail-closed, dan menentukan apakah analisis *dikirim* ke queue.
- **Jalur B** adalah gerbang *defensif di dalam*: untuk pemanggil yang menyentuh boundary model secara langsung (hook TASK 10). Tanpa konfigurasi/LLM — kontraknya: "input harus ACCEPT".
- **Jalur C** adalah gerbang *internal dalam pipeline*: redundansi/keamanan bahwa tidak ada pipeline yang berjalan tanpa validator.

---

## 4. Perbedaan Model / Prompt / Threshold / Aturan

| Komponen | Jalur A | Jalur B | Jalur C |
|---|---|---|---|
| Model heuristik | `ColonoscopyDomainValidator` (backend CV) | `ColonoscopyDomainValidator` (default) | `ColonoscopyDomainValidator` (default) |
| Threshold accept heuristik | 0.55 (mucosal_accept_threshold) | 0.55 (default) | 0.55 (default) |
| Threshold reject heuristik | 0.32 / 0.30 / 1.0 / 12.0 (default) | 0.32 / 0.30 / 1.0 / 12.0 (default) | 0.32 / 0.30 / 1.0 / 12.0 (default) |
| LLM / prompt | `src.services.llm_image_validator.PROMPT` + `validate_with_llm` | Tidak dipakai | Tidak dipakai |
| LLM min confidence | `LLM_VALIDATION_MIN_CONF` = 0.80 (default) | Tidak dipakai | Tidak dipakai |
| LLM model | `LLM_VALIDATION_MODEL` = `gemini-3.8-flash` (default) | Tidak dipakai | Tidak dipakai |
| LLM timeout | `LLM_VALIDATION_TIMEOUT_S` = 30.0 (default) | Tidak dipakai | Tidak dipakai |
| Fail-closed | Ya (ERROR → UNCERTAIN) | Ya (dengan keputusan heuristik saja) | Ya (ValueError → gagal job) |

Perbedaan threshold/keputusan tidak bersifat bug: threshold heuristik (0.55 accept) dan threshold LLM (0.80) adalah dua lapisan evaluasi yang berbeda oleh desain, dan hanya Jalur A yang menggabungkan keduanya.

---

## 5. Dampak Keputusan (Accept / Reject / Uncertain)

- **Jalur A:** satu gambar → himpunan keputusan eksplisit (ACCEPT → LLM → ACCEPT → proceed; REJECT → 400 NOT_COLONOSCOPY_IMAGE; UNCERTAIN → 400 UNCERTAIN_COLONOSCOPY_IMAGE; LLM REJECT/ERROR → 400 yang sama/dua kode yang sama). Menentukan apakah analisis *dikirim*.
- **Jalur B:** satu gambar → keputusan heuristik murni → raise pada REJECT/UNCERTAIN; ACCEPT → masuk inference. Menentukan apakah *work* dimulai.
- **Jalur C:** satu gambar (sudah ter-decode) → keputusan heuristik → ValueError pada ≠ ACCEPT → job berakhir `failed` (AI_PIPELINE_ERROR).

Pada alur normal produksi, sebuah gambar yang lolos Jalur A lalu masuk queue harus juga lolos Jalur C (karena `create_analysis` hanya enqueue setelah LLM PASS). Redundansi ini dipertahankan (defense-in-depth) dan **tidak** mengubah keputusan masuk.

---

## 6. Kemungkinan Saling Melewati (Bypass / Skip) & Risiko Konsistensi

1. **Gating konfigurasi berbeda per jalur.** Jika `DOMAIN_VALIDATION_ENABLED=false` (misalnya `TestingConfig`) atau `enforce_domain_validation=False` dipakai, Jalur A melewati heuristik dan LLM. Jalur B dan Jalur C tetap memakai gate yang tidak konfigurasi. Artinya: pada konfigurasi uji, keamanan bergantung pada pemilihan jalur yang benar — bukan seragam.
2. **Gating LLM.** Dengan `LLM_VALIDATION_ENABLED=false`, hanya heuristik yang berlaku (Jalur A). Jalur B/C tidak pernah memakai LLM, konsisten dengan desain "LLM hanya menahan".
3. **Injeksi validator.** Pada test, validator domain dapat di-inject dengan aturan/threshold berbeda; perilaku produksi memakai default. Risiko: dua jalur dengan validator berbeda tetapi dengan logika "ACCEPT" yang mungkin tidak setara.
4. **Parameter pipeline yang inert.** `run_pipeline(..., validate_domain: bool = True)` menyimpan parameter untuk kompatibilitas signature, namun docstring menyatakan gerbang kini *tidak lagi* memungkiri penonaktifan (`no longer disables the gate`). Jadi penonaktifan hanya bisa dilakukan dengan mengganti runner — bukan lewat parameter.
5. **Error taxonomy berbeda.** Jalur A memetakan ke `NOT_COLONOSCOPY_IMAGE` / `UNCERTAIN_COLONOSCOPY_IMAGE` (HTTP 400). Jalur C memetakan ke `ValueError` → konsekuensi menjadi `AI_PIPELINE_ERROR` / status `failed`. Pada dasarnya tidak mungkin terjadi REJECT di Jalur C untuk analisis yang lolos Jalur A, tetapi secara pemodelan perilaku error berbeda antarjalur.
6. **Tahap B (Isu B) terkait.** Penghapusan analisis saat pipeline masih berjalan tidak disentuh; hal ini dapat memengaruhi apakah Jalur C (gate di dalam pipeline) pernah berjalan untuk analisis yang dibuang — tetapi itu luar lingkup Isu C.

---

## 7. Kesimpulan Audit Isu C

1. Terdapat **lebih dari dua jalur** pemeriksaan domain setelah penambahan internal pipeline gate: **A (API/upload), B (model boundary), dan C (internal pipeline)**.
2. Semua jalur memakai aturan heuristik yang sama, namun konteks/kontrak berbeda: A = keputusan masuk ke sistem, B = proteksi boundary, C = proteksi runtime pipeline.
3. Tidak ada perubahan perilaku pada tahap audit ini. Keputusan desain berikutnya (mis. memadukan jalur, menghapus redundansi, atau menyesuaikan kontrak `validate_domain`) tetap memerlukan keputusan pemilik proyek.
4. Temuan ini harus diberitahukan sebagai dasar keputusan Isu C; **belum ada keputusan final** dan **belum ada perubahan implementasi**.

---

## Lampiran: Peta Panggilan Domain (pasca-Tahap-3)

```text
create_analysis (AnalysisService)
  └─ ImageValidationService.validate_and_decode_image   (teknis)
  └─ ImageValidationService.validate_domain             (heuristic, gated by DOMAIN_VALIDATION_ENABLED)
        └─ ImageValidationService.validate_llm          (Gemini Gate, gated by LLM_VALIDATION_ENABLED)
              └─ ImageValidationService.validate_domain ... (Accept → proceed)

run_segmentation / run_gradcam (AnalysisService)
  └─ AnalysisService._require_domain_accept
        └─ ImageValidationService.require_domain_accept (static, hard gate, no LLM/config)

AnalysisPipelineService.execute (background)
  └─ pipeline_runner = ai.inference.pipeline.run_pipeline
        └─ ColonoscopyDomainValidator().validate_image  (internal gate, always on)
```
