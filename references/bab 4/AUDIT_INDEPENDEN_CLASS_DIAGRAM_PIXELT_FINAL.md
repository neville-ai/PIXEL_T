# AUDIT INDEPENDEN CLASS DIAGRAM PIXEL-T FINAL

**Dokumen Pendukung Bab IV Skripsi S1**  
**Sistem:** PIXEL-T (Segmentasi Polip USG dengan Transfer Learning dan Explainable AI)  
**Versi Diagram:** `CLASS_DIAGRAM_PIXELT_FINAL.{drawio,png,svg}`  
**Diagram:** 18 kelas, 21 relasi, 14 label multiplicity  
**Tanggal Audit:** 5 November 2026  
**Status Akhir:** **FINAL — LULUS**

---

## A. Ringkasan Eksekutif

Audit independen ini memvalidasi keseluruhan *Class Diagram* PIXEL-T terhadap implementasi aktual source code. Audit dilakukan dari awal (tidak mengandalkan dokumentasi terdahulu), memeriksa:

- **Backend Flask:** controller, service, repository, core (errors), dependency injection
- **Frontend React:** service modules, AuthContext (auth state management)
- **Pipeline AI (PyTorch):** inference pipeline, model service, model config, dataclasses (PipelineResult, SegmentationResult, GradCAMResult)
- **Database:** migrasi Supabase/PostgreSQL (tabel `analyses`, `doctor_profiles`, RLS, trigger)

Hasil: semua 18 kelas, 44 atribut, 53 operasi, dan 21 relasi dalam diagram memiliki dasar implementasi nyata di source code. Tidak ada elemen yang diarang atau tidak terbukti.

**Kesimpulan:** `CLASS_DIAGRAM_PIXELT_FINAL.drawio` / `.png` / `.svg` **sesuai dengan implementasi aktual** web PIXEL-T dan layak untuk publikasi dalam Bab IV skripsi S1.

---

## B. Kerangka Acuan (Stereotipe UML)

Diagram menggunakan stereotipe UML standar untuk memisahkan tanggung jawab:

| Stereotipe | Arti | Warna Kotak |
|------------|------|-------------|
| `<<module>>` | Modul frontend TypeScript / modul AI pipeline Python | putih `#FFFFFF` |
| `<<controller>>` | Pengendali HTTP (Flask controller) | putih `#FFFFFF` |
| `<<service>>` | Lapisan layanan bisnis | putih `#FFFFFF` |
| `<<repository>>` | Lapisan akses data | putih `#FFFFFF` |
| `<<dataclass>>` | Struktur data output / konfigurasi (hanya atribut) | putih `#FFFFFF` |
| `<<exception>>` | Kelas penanganan kesalahan | putih `#FFFFFF` |
| `<<external>>` | Layanan eksternal (Supabase) | abu-abu terang `#F5F5F5` |

Relasi digambarkan dengan tanda tangan hijau (diamond) untuk agregasi (hollow diamond, start arrow) dan panah terbuka untuk dependensi/asosiasi.

---

## C. Daftar Kelas dan Dasar Implementasi (18 Kelas)

| # | Kelas | Stereotipe | File Sumber | Atribut | Operasi |
|---|-------|------------|-------------|---------|---------|
| 1 | AuthContext | `<<module>>` | `frontend/src/context/AuthContext.tsx` L17-24 | `user`, `session`, `loading`, `role`, `accountStatus` | `signIn` L132, `signUp` L175, `signOut` L206 |
| 2 | DoctorProfileService | `<<module>>` | `frontend/src/services/profile.ts` | — | `fetchDoctorProfile` L108, `saveDoctorProfile` L271, `uploadAvatar` L212, `validateProfileData` L168 |
| 3 | AnalysisClient | `<<module>>` | `frontend/src/services/analysis.ts` | — | `createAnalysis` L185, `getAnalysis` L194, `listHistory` L212, `deleteAnalysis` L218 |
| 4 | AnalysisController | `<<controller>>` | `backend/app/controllers/analysis_controller.py` L7 | `service: AnalysisService` L10 | `create_analysis` L13, `get_analysis` L41, `list_history` L61, `delete_analysis` L79 |
| 5 | AdminController | `<<controller>>` | `backend/app/controllers/admin_controller.py` L6 | `service: AdminService` L9 | `list_doctors` L12, `get_doctor` L28, `approve_doctor` L48, `reject_doctor` L65, `get_statistics` L86 |
| 6 | APIError | `<<exception>>` | `backend/app/core/errors.py` L8 | `code` L10, `message` L13, `status_code` L14 | `to_dict` L16 |
| 7 | AnalysisService | `<<service>>` | `backend/app/services/analysis_service.py` L269 | `repository` L291, `storage_service` L292, `pipeline_runner` L293, `job_queue` L296 | `validate_and_decode_image` L301, `create_analysis` L369, `get_analysis` L502, `list_user_analyses` L635, `delete_analysis` L688 |
| 8 | StorageService | `<<service>>` | `backend/app/services/storage_service.py` L7 | `bucket_name` L20 | `upload_file` L119, `create_signed_url` L149, `delete_analysis_files` L175 |
| 9 | AdminService | `<<service>>` | `backend/app/services/admin_service.py` L27 | `client: SupabaseClient` L35 | `list_doctors` L42, `get_doctor` L103, `approve_doctor` L135, `reject_doctor` L235, `get_statistics` L328 |
| 10 | AnalysisRepository | `<<repository>>` | `backend/app/repositories/analysis_repository.py` L5 | `client` L15 | `create` L38, `get_by_id` L71, `list_by_user` L100, `update` L133, `delete` L172 |
| 11 | AnalysisJobQueue | `<<service>>` | `backend/app/services/analysis_service.py` L150 | `MAX_WAITING` L166, `capacity` L184 | `try_enqueue` L188, `contains` L202, `pending_count` L209, `drain_one` L213 |
| 12 | AIInference | `<<module>>` | `ai/inference/pipeline.py` | — | `run_pipeline` L101, `predict` (seg. L98), `generate_gradcam` (gradcam L99) |
| 13 | ModelService | `<<service>>` | `ai/inference/model_service.py` L19 | `config` L23, `device` L35, `load_count` L27 | `load` L61, `metadata` L95, `predict_logits` L112, `get_gradcam_target_layer` L129 |
| 14 | ModelConfig | `<<dataclass>>` | `ai/config/model_config.py` L19 | `architecture`, `encoder`, `model_version`, `input_size`, `threshold`, `tta_enabled`, `checkpoint_sha256` | — |
| 15 | PipelineResult | `<<dataclass>>` | `ai/inference/pipeline.py` L63 | `binary_mask_png`, `segmentation_overlay_png`, `gradcam_heatmap_png`, `gradcam_overlay_png`, `measurements`, `summary_text`, `gradcam` | — |
| 16 | SegmentationResult | `<<dataclass>>` | `ai/inference/segmentation.py` L25 | `probability_map`, `binary_mask`, `threshold` | — |
| 17 | GradCAMResult | `<<dataclass>>` | `ai/inference/gradcam.py` L38 | `heatmap`, `overlay`, `target_layer`, `target_objective`, `target_mask_empty` | — |
| 18 | SupabasePlatform | `<<external>>` | Supabase Auth + DB + Storage | — | `Auth`, `DB`, `Storage` |

**Catatan:** `AnalysisProgressReporter` (L64) adalah kelas helper internal `AnalysisService` untuk progres throttled, tidak dipisahkan sebagai kelas sendiri dalam diagram agar tetap konsisten dengan derajat abstraksi kelas lain.

---

## D. Matriks Relasi dan Multiplicity (21 Relasi)

| No | Relasi | Jenis | Multiplicity | Dasar Implementasi |
|----|--------|-------|--------------|-------------------|
| 1 | AuthContext → SupabasePlatform | Asosiasi | 1 : 1 | `AuthContext.tsx` L1-11 pakai `supabase` client |
| 2 | DoctorProfileService → SupabasePlatform | Asosiasi | 1 : 1 | `profile.ts` query/upsert `doctor_profiles` + Storage avatar |
| 3 | AnalysisClient → AnalysisController | Asosiasi | 1 : 1 | `analysis.ts` L185 `POST /api/analysis` → controller L13 |
| 4 | AnalysisClient → SupabasePlatform | Asosiasi | 1 : 1 | `analysis.ts` L101 Bearer token Supabase |
| 5 | AnalysisController → AnalysisService | Agregasi | 1 : 1 | `analysis_controller.py` L10-11 `self.service = ...AnalysisService()` |
| 6 | AnalysisController → APIError | Dependensi | — | `analysis_controller.py` L3 `from app.core.errors import APIError` |
| 7 | AdminController → AdminService | Agregasi | 1 : 1 | `admin_controller.py` L9-10 `self.service = ...AdminService()` |
| 8 | AdminController → APIError | Dependensi | — | `admin_controller.py` L2 `from app.core.errors import APIError` |
| 9 | AnalysisService → AnalysisRepository | Agregasi | 1 : 1 | `analysis_service.py` L291 `self.repository = ...AnalysisRepository()` |
| 10 | AnalysisService → StorageService | Agregasi | 1 : 1 | `analysis_service.py` L292 `self.storage_service = ...StorageService()` |
| 11 | AnalysisService → AnalysisJobQueue | Agregasi | 1 : 1 | `analysis_service.py` L296 `self.job_queue = ...AnalysisJobQueue()` |
| 12 | AnalysisService → AIInference | Dependensi | — | `analysis_service.py` L22-23 import `run_pipeline` |
| 13 | AnalysisRepository → SupabasePlatform | Asosiasi | 1 : 1 | `analysis_repository.py` L2 `get_supabase_client()` |
| 14 | StorageService → SupabasePlatform | Asosiasi | 1 : 1 | `storage_service.py` L4 `get_supabase_client()` |
| 15 | AdminService → SupabasePlatform | Asosiasi | 1 : 1 | `admin_service.py` L6 `get_supabase_client(use_service_role=True)` |
| 16 | AIInference → ModelService | Dependensi | — | `segmentation.py` L13 `from ai.inference.model_service import ModelService` |
| 17 | AIInference → PipelineResult | Dependensi (mengembalikan) | — | `pipeline.py` L101-108 `run_pipeline(...) -> PipelineResult` |
| 18 | AIInference → SegmentationResult | Dependensi (mengembalikan) | — | `segmentation.py` L98-100 `predict(...) -> SegmentationResult` |
| 19 | AIInference → GradCAMResult | Dependensi (mengembalikan) | — | `gradcam.py` L99-106 `generate_gradcam(...) -> GradCAMResult` |
| 20 | PipelineResult → GradCAMResult | Agregasi | 1 : 1 | `pipeline.py` L70 `gradcam: GradCAMResult` |
| 21 | ModelService → ModelConfig | Agregasi | 1 : 1 | `model_service.py` L22-23 `__init__(self, config: ModelConfig)` |

Multiplicity tambahan dari spesifikasi basis data (bukan relasi antar kelas diagram, tercantum sebagai catatan pendukung):
- `auth.users 1 : doctor_profiles 0..1` — `user_id` UNIQUE NOT NULL FK (Migration 004 L12, L46)
- `auth.users 1 : analyses 1:*` — `user_id` NOT NULL FK (Migration 001)
- `doctor_profiles.approved_by → auth.users 0..* : 0..1` — Migration 007 L33

---

## E. Verifikasi Format dan Konsistensi

| Format | File | Status | Detail |
|--------|------|--------|--------|
| DrawIO XML | `CLASS_DIAGRAM_PIXELT_FINAL.drawio` | ✅ Valid | Root `<mxfile>`, 18 vertex kelas, 21 edge, 14 text multiplicity |
| PNG | `CLASS_DIAGRAM_PIXELT_FINAL.png` | ✅ Render valid | 3750 × 3780 px (scale 3×), latar putih, tidak terpotong/overlap |
| SVG | `CLASS_DIAGRAM_PIXELT_FINAL.svg` | ✅ Valid XML | Root `<svg>`, 18 class body rects, 14 multiplicity text |

Konsistensi drawio ↔ SVG ↔ PNG telah diverifikasi secara terprogram (skrip `_verify_class_final_v3.js`): jumlah kelas, label multiplicity, dan dimensi PNG cocok antara ketiga format.

---

## F. Catatan Pemeriksaan (Findings)

1. Empat kelas `<<dataclass>>` (`ModelConfig`, `PipelineResult`, `SegmentationResult`, `GradCAMResult`) hanya memiliki atribut, tanpa operasi — dikompartemenkan sesuai standar UML (operations compartment kosong).
2. `AuthContext` menyimpan `role` dan `accountStatus` yang di-resolve dari `app_metadata.role` (admin, server-write-only) dan `doctor_profiles` (dokter); admin tidak memiliki baris di `doctor_profiles`.
3. `AnalysisService` tidak melakukan inferensi AI sendiri — itu di-delegasikan ke `AIInference.run_pipeline()` (boundary TASK 08 di kode).
4. Semua relasi aggregate menggunakan hollow diamond (start arrow) dengan multiplicity `1 : 1`; dependensi menggunakan panah terbuka (open arrow).

---

## G. Kesimpulan dan Status

Audit independen menyeluruh terhadap source code aktual menunjukkan bahwa `CLASS_DIAGRAM_PIXELT_FINAL` akurat, konsisten di ketiga format, dan bebas dari elemen yang diarang.

**Status Akhir: FINAL — LULUS**  
Diagram siap digunakan dalam Bab IV skripsi S1.

---

**Berkas pendukung:** `MATRIKS_BUKTI_AUDIT_CLASS_DIAGRAM_PIXELT_FINAL.md`, `PENJELASAN_AKADEMIK_CLASS_DIAGRAM_PIXELT_FINAL.md`
