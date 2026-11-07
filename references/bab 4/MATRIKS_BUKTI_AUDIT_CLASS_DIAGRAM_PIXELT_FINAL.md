# MATRIKS BUKTI AUDIT CLASS DIAGRAM PIXEL-T FINAL

**Versi Diagram:** `CLASS_DIAGRAM_PIXELT_FINAL.{drawio,png,svg}`  
**Tanggal Audit:** 5 November 2026  
**Lokasi:** `references/bab 4/`  
**Status:** FINAL — LULUS

---

## A. Matriks Kelas: Implementasi Aktual → Elemen Diagram

| # | Kelas Diagram | Stereotipe | File Sumber | Baris Kunci | Bukti Atribut | Bukti Operasi | Status |
|---|---------------|------------|-------------|-------------|---------------|---------------|--------|
| 1 | AuthContext | `<<module>>` | `frontend/src/context/AuthContext.tsx` | L17-24, L132-206 | `user: User\|null` L17, `session: Session\|null` L18, `loading: boolean` L19, `role: string\|null` L21, `accountStatus: string\|null` L23 | `signIn()` L132, `signUp()` L175, `signOut()` L206 | ✅ |
| 2 | DoctorProfileService | `<<module>>` | `frontend/src/services/profile.ts` | L108-391 | — (modul, tanpa atribut) | `fetchDoctorProfile()` L108, `saveDoctorProfile()` L271, `uploadAvatar()` L212, `validateProfileData()` L168 | ✅ |
| 3 | AnalysisClient | `<<module>>` | `frontend/src/services/analysis.ts` | L185-224 | — (modul, tanpa atribut) | `createAnalysis()` L185, `getAnalysis()` L194, `listHistory()` L212, `deleteAnalysis()` L218 | ✅ |
| 4 | AnalysisController | `<<controller>>` | `backend/app/controllers/analysis_controller.py` | L7-96 | `service: AnalysisService` L10 | `create_analysis()` L13, `get_analysis()` L41, `list_history()` L61, `delete_analysis()` L79 | ✅ |
| 5 | AdminController | `<<controller>>` | `backend/app/controllers/admin_controller.py` | L6-98 | `service: AdminService` L9 | `list_doctors()` L12, `get_doctor()` L28, `approve_doctor()` L48, `reject_doctor()` L65, `get_statistics()` L86 | ✅ |
| 6 | APIError | `<<exception>>` | `backend/app/core/errors.py` | L8-23 | `code` L10, `message` L13, `status_code` L14 | `to_dict()` L16 | ✅ |
| 7 | AnalysisService | `<<service>>` | `backend/app/services/analysis_service.py` | L269-302 | `repository` L291, `storage_service` L292, `pipeline_runner` L293, `job_queue` L296 | `validate_and_decode_image()` L301, `create_analysis()` L369, `get_analysis()` L502, `list_user_analyses()` L635, `delete_analysis()` L688 | ✅ |
| 8 | StorageService | `<<service>>` | `backend/app/services/storage_service.py` | L7-26 | `bucket_name: String` L20 | `upload_file()` L119, `create_signed_url()` L149, `delete_analysis_files()` L175 | ✅ |
| 9 | AdminService | `<<service>>` | `backend/app/services/admin_service.py` | L27-40 | `client: SupabaseClient` L35 | `list_doctors()` L42, `get_doctor()` L103, `approve_doctor()` L135, `reject_doctor()` L235, `get_statistics()` L328 | ✅ |
| 10 | AnalysisRepository | `<<repository>>` | `backend/app/repositories/analysis_repository.py` | L5-196 | `client` L15 | `create()` L38, `get_by_id()` L71, `list_by_user()` L100, `update()` L133, `delete()` L172 | ✅ |
| 11 | AnalysisJobQueue | `<<service>>` | `backend/app/services/analysis_service.py` | L150-218 | `MAX_WAITING` L166, `capacity` L184 | `try_enqueue()` L188, `contains()` L202, `pending_count()` L209, `drain_one()` L213 | ✅ |
| 12 | AIInference | `<<module>>` | `ai/inference/pipeline.py` | L101-165 | — (modul, tanpa atribut) | `run_pipeline()` L101, `predict()` (`segmentation.py` L98), `generate_gradcam()` (`gradcam.py` L99) | ✅ |
| 13 | ModelService | `<<service>>` | `ai/inference/model_service.py` | L19-136 | `config` L23, `device` L35, `load_count` L27 | `load()` L61, `metadata()` L95, `predict_logits()` L112, `get_gradcam_target_layer()` L129 | ✅ |
| 14 | ModelConfig | `<<dataclass>>` | `ai/config/model_config.py` | L19-66 | `architecture` L20, `encoder` L21, `model_version` L26, `input_size` L27, `threshold` L29, `tta_enabled` L30, `checkpoint_sha256` L38 | — (dataclass konfigurasi) | ✅ |
| 15 | PipelineResult | `<<dataclass>>` | `ai/inference/pipeline.py` | L62-70 | `binary_mask_png` L64, `segmentation_overlay_png` L65, `gradcam_heatmap_png` L66, `gradcam_overlay_png` L67, `measurements` L68, `summary_text` L69, `gradcam` L70 | — (dataclass output) | ✅ |
| 16 | SegmentationResult | `<<dataclass>>` | `ai/inference/segmentation.py` | L24-28 | `probability_map` L26, `binary_mask` L27, `threshold` L28 | — (dataclass output) | ✅ |
| 17 | GradCAMResult | `<<dataclass>>` | `ai/inference/gradcam.py` | L37-43 | `heatmap` L39, `overlay` L40, `target_layer` L41, `target_objective` L42, `target_mask_empty` L43 | — (dataclass output) | ✅ |
| 18 | SupabasePlatform | `<<external>>` | Supabase Auth + DB + Storage | — | — | `Auth`, `DB`, `Storage` (layanan eksternal) | ✅ |

---

## B. Matriks Atribut: Sumber Kode → Diagram (44 Atribut)

| # | Kelas | Atribut | Tipe Diagram | Visibility | File Sumber | Baris | Status |
|---|-------|---------|--------------|------------|-------------|-------|--------|
| 1 | AuthContext | user | User | - | AuthContext.tsx | L17 | ✅ |
| 2 | AuthContext | session | Session | - | AuthContext.tsx | L18 | ✅ |
| 3 | AuthContext | loading | Boolean | - | AuthContext.tsx | L19 | ✅ |
| 4 | AuthContext | role | String | - | AuthContext.tsx | L21 | ✅ |
| 5 | AuthContext | accountStatus | String | - | AuthContext.tsx | L23 | ✅ |
| 6 | AnalysisController | service | AnalysisService | - | analysis_controller.py | L10-11 | ✅ |
| 7 | AdminController | service | AdminService | - | admin_controller.py | L9-10 | ✅ |
| 8 | APIError | code | String | + | errors.py | L10 | ✅ |
| 9 | APIError | message | String | + | errors.py | L13 | ✅ |
| 10 | APIError | status_code | Integer | + | errors.py | L14 | ✅ |
| 11 | AnalysisService | repository | AnalysisRepository | - | analysis_service.py | L291 | ✅ |
| 12 | AnalysisService | storage_service | StorageService | - | analysis_service.py | L292 | ✅ |
| 13 | AnalysisService | pipeline_runner | Callable | - | analysis_service.py | L293 | ✅ |
| 14 | AnalysisService | job_queue | AnalysisJobQueue | - | analysis_service.py | L296 | ✅ |
| 15 | StorageService | bucket_name | String | - | storage_service.py | L20 | ✅ |
| 16 | AdminService | client | SupabaseClient | - | admin_service.py | L34-35 | ✅ |
| 17 | AnalysisRepository | client | SupabaseClient | - | analysis_repository.py | L15-17 | ✅ |
| 18 | AnalysisJobQueue | MAX_WAITING | Integer | + | analysis_service.py | L166 | ✅ |
| 19 | AnalysisJobQueue | capacity | Integer | + | analysis_service.py | L184 | ✅ |
| 20 | ModelService | config | ModelConfig | + | model_service.py | L23 | ✅ |
| 21 | ModelService | device | Device | + | model_service.py | L35 | ✅ |
| 22 | ModelService | load_count | Integer | + | model_service.py | L27-32 | ✅ |
| 23 | ModelConfig | architecture | String | + | model_config.py | L20 | ✅ |
| 24 | ModelConfig | encoder | String | + | model_config.py | L21 | ✅ |
| 25 | ModelConfig | model_version | String | + | model_config.py | L26 | ✅ |
| 26 | ModelConfig | input_size | Integer | + | model_config.py | L27 | ✅ |
| 27 | ModelConfig | threshold | Float | + | model_config.py | L29 | ✅ |
| 28 | ModelConfig | tta_enabled | Boolean | + | model_config.py | L30 | ✅ |
| 29 | ModelConfig | checkpoint_sha256 | String | + | model_config.py | L38 | ✅ |
| 30 | PipelineResult | binary_mask_png | Bytes | + | pipeline.py | L64 | ✅ |
| 31 | PipelineResult | segmentation_overlay_png | Bytes | + | pipeline.py | L65 | ✅ |
| 32 | PipelineResult | gradcam_heatmap_png | Bytes | + | pipeline.py | L66 | ✅ |
| 33 | PipelineResult | gradcam_overlay_png | Bytes | + | pipeline.py | L67 | ✅ |
| 34 | PipelineResult | measurements | Dict | + | pipeline.py | L68 | ✅ |
| 35 | PipelineResult | summary_text | String | + | pipeline.py | L69 | ✅ |
| 36 | PipelineResult | gradcam | GradCAMResult | + | pipeline.py | L70 | ✅ |
| 37 | SegmentationResult | probability_map | Tensor | + | segmentation.py | L26 | ✅ |
| 38 | SegmentationResult | binary_mask | Tensor | + | segmentation.py | L27 | ✅ |
| 39 | SegmentationResult | threshold | Float | + | segmentation.py | L28 | ✅ |
| 40 | GradCAMResult | heatmap | Array | + | gradcam.py | L39 | ✅ |
| 41 | GradCAMResult | overlay | Array | + | gradcam.py | L40 | ✅ |
| 42 | GradCAMResult | target_layer | String | + | gradcam.py | L41 | ✅ |
| 43 | GradCAMResult | target_objective | String | + | gradcam.py | L42 | ✅ |
| 44 | GradCAMResult | target_mask_empty | Boolean | + | gradcam.py | L43 | ✅ |

> Catatan: seluruh 44 baris atribut di atas terverifikasi di `.drawio` (termasuk `target_mask_empty` pada `GradCAMResult` dan `client` pada `AnalysisRepository`).

---

## C. Matriks Operasi: Sumber Kode → Diagram (53 Operasi)

| # | Kelas | Operasi | Parameter | Return Type | Visibility | File Sumber | Baris | Status |
|---|-------|---------|-----------|-------------|------------|-------------|-------|--------|
| 1 | AuthContext | signIn | email, password, selectedRole? | Promise | + | AuthContext.tsx | L132 | ✅ |
| 2 | AuthContext | signUp | email, password, fullName?, hospitalName?, doctorSpecialty? | Promise | + | AuthContext.tsx | L175 | ✅ |
| 3 | AuthContext | signOut | — | Promise | + | AuthContext.tsx | L206 | ✅ |
| 4 | DoctorProfileService | fetchDoctorProfile | user: User | Promise | + | profile.ts | L108 | ✅ |
| 5 | DoctorProfileService | saveDoctorProfile | user: User, data: DoctorProfileData | Promise | + | profile.ts | L271 | ✅ |
| 6 | DoctorProfileService | uploadAvatar | user: User, file: File | Promise | + | profile.ts | L212 | ✅ |
| 7 | DoctorProfileService | validateProfileData | data: DoctorProfileData | Object | + | profile.ts | L168 | ✅ |
| 8 | AnalysisClient | createAnalysis | file: File | Promise | + | analysis.ts | L185 | ✅ |
| 9 | AnalysisClient | getAnalysis | id: String | Promise | + | analysis.ts | L194 | ✅ |
| 10 | AnalysisClient | listHistory | — | Promise | + | analysis.ts | L212 | ✅ |
| 11 | AnalysisClient | deleteAnalysis | id: String | Promise | + | analysis.ts | L218 | ✅ |
| 12 | AnalysisController | create_analysis | — | Response | + | analysis_controller.py | L13 | ✅ |
| 13 | AnalysisController | get_analysis | analysis_id: String | Response | + | analysis_controller.py | L41 | ✅ |
| 14 | AnalysisController | list_history | — | Response | + | analysis_controller.py | L61 | ✅ |
| 15 | AnalysisController | delete_analysis | analysis_id: String | Response | + | analysis_controller.py | L79 | ✅ |
| 16 | AdminController | list_doctors | status: String | Response | + | admin_controller.py | L12 | ✅ |
| 17 | AdminController | get_doctor | doctor_id: String | Response | + | admin_controller.py | L28 | ✅ |
| 18 | AdminController | approve_doctor | doctor_id: String | Response | + | admin_controller.py | L48 | ✅ |
| 19 | AdminController | reject_doctor | doctor_id: String | Response | + | admin_controller.py | L65 | ✅ |
| 20 | AdminController | get_statistics | — | Response | + | admin_controller.py | L86 | ✅ |
| 21 | APIError | to_dict | — | Dict | + | errors.py | L16 | ✅ |
| 22 | AnalysisService | validate_and_decode_image | file | Tuple | + | analysis_service.py | L301 | ✅ |
| 23 | AnalysisService | create_analysis | file, user_id | Dict | + | analysis_service.py | L369 | ✅ |
| 24 | AnalysisService | get_analysis | analysis_id, user_id | Dict | + | analysis_service.py | L502 | ✅ |
| 25 | AnalysisService | list_user_analyses | user_id | List | + | analysis_service.py | L635 | ✅ |
| 26 | AnalysisService | delete_analysis | analysis_id, user_id | Boolean | + | analysis_service.py | L688 | ✅ |
| 27 | StorageService | upload_file | path, file_bytes, content_type | String | + | storage_service.py | L119 | ✅ |
| 28 | StorageService | create_signed_url | path, expires_in | String | + | storage_service.py | L149 | ✅ |
| 29 | StorageService | delete_analysis_files | paths | Boolean | + | storage_service.py | L175 | ✅ |
| 30 | AdminService | list_doctors | status? | List | + | admin_service.py | L42 | ✅ |
| 31 | AdminService | get_doctor | doctor_id: String | Optional | + | admin_service.py | L103 | ✅ |
| 32 | AdminService | approve_doctor | doctor_id, approved_by | Dict | + | admin_service.py | L135 | ✅ |
| 33 | AdminService | reject_doctor | doctor_id, approved_by, reason | Dict | + | admin_service.py | L235 | ✅ |
| 34 | AdminService | get_statistics | — | Dict | + | admin_service.py | L328 | ✅ |
| 35 | AnalysisRepository | create | user_id, data | Dict | + | analysis_repository.py | L38 | ✅ |
| 36 | AnalysisRepository | get_by_id | analysis_id, user_id | Optional | + | analysis_repository.py | L71 | ✅ |
| 37 | AnalysisRepository | list_by_user | user_id | List | + | analysis_repository.py | L100 | ✅ |
| 38 | AnalysisRepository | update | analysis_id, user_id, data | Optional | + | analysis_repository.py | L133 | ✅ |
| 39 | AnalysisRepository | delete | analysis_id, user_id | Boolean | + | analysis_repository.py | L172 | ✅ |
| 40 | AnalysisJobQueue | try_enqueue | job | Boolean | + | analysis_service.py | L188 | ✅ |
| 41 | AnalysisJobQueue | contains | analysis_id | Boolean | + | analysis_service.py | L202 | ✅ |
| 42 | AnalysisJobQueue | pending_count | — | Integer | + | analysis_service.py | L209 | ✅ |
| 43 | AnalysisJobQueue | drain_one | — | Boolean | + | analysis_service.py | L213 | ✅ |
| 44 | AIInference | run_pipeline | original_bytes, config, on_phase, on_pass, analysis_id | PipelineResult | + | pipeline.py | L101 | ✅ |
| 45 | AIInference | predict | image, config, on_pass | SegmentationResult | + | segmentation.py | L98 | ✅ |
| 46 | AIInference | generate_gradcam | image_tensor, ... | GradCAMResult | + | gradcam.py | L99 | ✅ |
| 47 | ModelService | load | — | Module | + | model_service.py | L61 | ✅ |
| 48 | ModelService | metadata | — | Dict | + | model_service.py | L95 | ✅ |
| 49 | ModelService | predict_logits | tensor | Tensor | + | model_service.py | L112 | ✅ |
| 50 | ModelService | get_gradcam_target_layer | — | Module | + | model_service.py | L129 | ✅ |
| 51 | SupabasePlatform | Auth | — | Service | + | Supabase | — | ✅ |
| 52 | SupabasePlatform | DB | — | Service | + | Supabase | — | ✅ |
| 53 | SupabasePlatform | Storage | — | Service | + | Supabase | — | ✅ |

---

## D. Matriks Relasi & Multiplicity: Bukti Kode dan Database (21 Relasi)

| No | Class A | Class B | Jenis | Mult A | Mult B | Basis Hubungan | File/Baris Bukti | Status |
|----|---------|---------|-------|--------|--------|----------------|------------------|--------|
| 1 | AuthContext | SupabasePlatform | Asosiasi | 1 | 1 | Client Supabase untuk autentikasi | `AuthContext.tsx` L1-11 | ✅ |
| 2 | DoctorProfileService | SupabasePlatform | Asosiasi | 1 | 1 | Query/upsert profil + Storage avatar | `profile.ts` L1, L108, L271 | ✅ |
| 3 | AnalysisClient | AnalysisController | Asosiasi | 1 | 1 | HTTP frontend → backend | `analysis.ts` L185; `analysis_controller.py` L13 | ✅ |
| 4 | AnalysisClient | SupabasePlatform | Asosiasi | 1 | 1 | Bearer access token Supabase | `analysis.ts` L101 | ✅ |
| 5 | AnalysisController | AnalysisService | Agregasi | 1 | 1 | Controller memegang service | `analysis_controller.py` L10-11 | ✅ |
| 6 | AnalysisController | APIError | Dependensi | — | — | Import + raise APIError | `analysis_controller.py` L3 | ✅ |
| 7 | AdminController | AdminService | Agregasi | 1 | 1 | Controller memegang service | `admin_controller.py` L9-10 | ✅ |
| 8 | AdminController | APIError | Dependensi | — | — | Import + raise APIError | `admin_controller.py` L2 | ✅ |
| 9 | AnalysisService | AnalysisRepository | Agregasi | 1 | 1 | Service memegang repository | `analysis_service.py` L291 | ✅ |
| 10 | AnalysisService | StorageService | Agregasi | 1 | 1 | Service memegang storage | `analysis_service.py` L292 | ✅ |
| 11 | AnalysisService | AnalysisJobQueue | Agregasi | 1 | 1 | Service memegang antrean | `analysis_service.py` L296 | ✅ |
| 12 | AnalysisService | AIInference | Dependensi | — | — | Import + panggil `run_pipeline` | `analysis_service.py` L22-23 | ✅ |
| 13 | AnalysisRepository | SupabasePlatform | Asosiasi | 1 | 1 | Supabase client ke tabel `analyses` | `analysis_repository.py` L2 | ✅ |
| 14 | StorageService | SupabasePlatform | Asosiasi | 1 | 1 | Supabase Storage bucket | `storage_service.py` L4 | ✅ |
| 15 | AdminService | SupabasePlatform | Asosiasi | 1 | 1 | Service-role client ke DB | `admin_service.py` L6, L40 | ✅ |
| 16 | AIInference | ModelService | Dependensi | — | — | Import + pakai ModelService | `segmentation.py` L13 | ✅ |
| 17 | AIInference | PipelineResult | Dependensi | — | — | `run_pipeline` mengembalikan | `pipeline.py` L101-108 | ✅ |
| 18 | AIInference | SegmentationResult | Dependensi | — | — | `predict` mengembalikan | `segmentation.py` L98-100 | ✅ |
| 19 | AIInference | GradCAMResult | Dependensi | — | — | `generate_gradcam` mengembalikan | `gradcam.py` L99-106 | ✅ |
| 20 | PipelineResult | GradCAMResult | Agregasi | 1 | 1 | Field `gradcam` | `pipeline.py` L70 | ✅ |
| 21 | ModelService | ModelConfig | Agregasi | 1 | 1 | Field `config` | `model_service.py` L22-23 | ✅ |

### D.1 Multiplicity Basis Data (Catatan ERD, Bukan Kelas Diagram)

| Relasi Tabel | Multiplicity | Constraint | Bukti |
|--------------|--------------|------------|-------|
| `auth.users` → `doctor_profiles` | 1 : 0..1 | `user_id UUID NOT NULL REFERENCES auth.users(id)` + `UNIQUE(user_id)` | Migrasi 004 L12, L46 |
| `auth.users` → `analyses` | 1 : 1..* | `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE` | Migrasi 001 |
| `doctor_profiles.approved_by` → `auth.users` | 0..* : 0..1 | `approved_by UUID REFERENCES auth.users(id)` | Migrasi 007 L33 |

---

## E. Matriks Kelengkapan Format

| Aspek | DrawIO | PNG | SVG | Status |
|-------|--------|-----|-----|--------|
| Root/struktur valid | `<mxfile>` ✅ | 3750×3780 ✅ | `<svg>` 3750×3780 ✅ | ✅ |
| Kelas (18) | 18 vertex rectangle | 18 kotak | 18 body rect | ✅ |
| Atribut (44) | 44 baris | tergambar | tergambar | ✅ |
| Operasi (53) | 53 baris | tergambar | tergambar | ✅ |
| Relasi (21) | 21 edge | 21 jalur | 21 jalur | ✅ |
| Label multiplicity (14) | 14 text cell | tergambar | 14 text bold | ✅ |
| Latar putih, teks hitam | ✅ | ✅ | ✅ | ✅ |
| Tidak overlap/terpotong | — | ✅ (inspeksi visual) | ✅ | ✅ |

---

## F. Ringkasan

- **18/18 kelas** terbukti di source code.
- **44/44 atribut** terbukti di source code.
- **53/53 operasi** terbukti di source code.
- **21/21 relasi** terbukti di source code / migrasi database.
- **14/14 label multiplicity** konsisten di drawio dan SVG.
- **0 elemen** diarang atau tanpa dasar.

**Status: FINAL — LULUS**
