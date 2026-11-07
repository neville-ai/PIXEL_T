# MATRIKS BUKTI AUDIT CLASS DIAGRAM PIXELT FINAL SIMPLE RAPI REVISI FINAL

**Sistem:** PIXEL-T (Segmentasi Polip USG dengan Transfer Learning dan Explainable AI)  
**Versi Diagram:** `CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE_RAPI_REVISI_FINAL.{drawio,png,svg}`  
**Jumlah Kelas:** 17  
**Jumlah Relasi:** 20  
**Tanggal Audit:** 6 November 2026

---

## A. Matriks Kelas: Sumber Kode → Diagram (17 Kelas)

| # | Kelas | Stereotype | Jenis | File Sumber | Baris | Status |
|---|-------|------------|-------|-------------|-------|--------|
| 1 | AuthContext | <<module>> | Frontend | `frontend/src/context/AuthContext.tsx` | L43 | ✅ |
| 2 | AnalysisClient | <<module>> | Frontend | `frontend/src/services/analysis.ts` | L185 | ✅ |
| 3 | DoctorProfileService | <<module>> | Frontend | `frontend/src/services/profile.ts` | L108 | ✅ |
| 4 | AnalysisController | <<controller>> | Backend | `backend/app/controllers/analysis_controller.py` | L7 | ✅ |
| 5 | AdminController | <<controller>> | Backend | `backend/app/controllers/admin_controller.py` | L6 | ✅ |
| 6 | AnalysisService | <<service>> | Backend | `backend/app/services/analysis_service.py` | L269 | ✅ |
| 7 | AdminService | <<service>> | Backend | `backend/app/services/admin_service.py` | L27 | ✅ |
| 8 | AnalysisRepository | <<repository>> | Backend | `backend/app/repositories/analysis_repository.py` | L5 | ✅ |
| 9 | StorageService | <<service>> | Backend | `backend/app/services/storage_service.py` | L7 | ✅ |
| 10 | AnalysisJobQueue | <<module>> | Backend | `backend/app/services/analysis_service.py` | L240 | ✅ |
| 11 | AIInference | <<module>> | AI Pipeline | `ai/inference/pipeline.py` | L101 | ✅ |
| 12 | ModelService | <<service>> | AI Pipeline | `ai/inference/model_service.py` | L19 | ✅ |
| 13 | ModelConfig | <<dataclass>> | AI Pipeline | `ai/config/model_config.py` | L19 | ✅ |
| 14 | SupabasePlatform | <<external>> | External | — (abstraksi layanan) | — | ✅ |
| 15 | User | <<entity>> | Database | `database/migrations/001_create_analyses_and_storage.sql` | L14 | ✅ |
| 16 | DoctorProfile | <<entity>> | Database | `database/migrations/004_create_doctor_profiles.sql` | L10 | ✅ |
| 17 | Analysis | <<entity>> | Database | `database/migrations/001_create_analyses_and_storage.sql` | L14 | ✅ |

---

## B. Matriks Atribut: Sumber Kode → Diagram

| # | Kelas | Atribut | Tipe | Visibility | File Sumber | Baris | Status |
|---|-------|---------|------|------------|-------------|-------|--------|
| 1 | AuthContext | user | User | - | AuthContext.tsx | L17 | ✅ |
| 2 | AuthContext | session | Session | - | AuthContext.tsx | L18 | ✅ |
| 3 | AuthContext | loading | Boolean | - | AuthContext.tsx | L19 | ✅ |
| 4 | AuthContext | role | String | - | AuthContext.tsx | L21 | ✅ |
| 5 | AuthContext | accountStatus | String | - | AuthContext.tsx | L23 | ✅ |
| 6 | AnalysisController | service | AnalysisService | - | analysis_controller.py | L10 | ✅ |
| 7 | AdminController | service | AdminService | - | admin_controller.py | L9 | ✅ |
| 8 | AnalysisService | repository | AnalysisRepository | - | analysis_service.py | L291 | ✅ |
| 9 | AnalysisService | storage | StorageService | - | analysis_service.py | L292 | ✅ |
| 10 | AnalysisService | job_queue | AnalysisJobQueue | - | analysis_service.py | L240 | ✅ |
| 11 | AnalysisService | pipeline_runner | Callable | - | analysis_service.py | L293 | ✅ |
| 12 | AdminService | client | SupabaseClient | - | admin_service.py | L34 | ✅ |
| 13 | AnalysisRepository | client | SupabaseClient | - | analysis_repository.py | L17 | ✅ |
| 14 | StorageService | client | SupabaseClient | - | storage_service.py | L16 | ✅ |
| 15 | StorageService | bucket_name | String | - | storage_service.py | L20 | ✅ |
| 16 | AnalysisJobQueue | max_waiting | Integer | - | analysis_service.py | L240 | ✅ |
| 17 | AnalysisJobQueue | jobs | Queue<Job> | - | analysis_service.py | L243 | ✅ |
| 18 | AnalysisJobQueue | worker | Thread | - | analysis_service.py | L249 | ✅ |
| 19 | ModelService | config | ModelConfig | + | model_service.py | L22 | ✅ |
| 20 | ModelConfig | architecture | String | + | model_config.py | L20 | ✅ |
| 21 | ModelConfig | encoder | String | + | model_config.py | L21 | ✅ |
| 22 | ModelConfig | input_size | Integer | + | model_config.py | L27 | ✅ |
| 23 | ModelConfig | threshold | Float | + | model_config.py | L29 | ✅ |
| 24 | ModelConfig | checkpoint_sha256 | String | + | model_config.py | L38 | ✅ |
| 25 | User | id | UUID | + | 001_migration | L16 | ✅ |
| 26 | User | email | String | + | auth.users | — | ✅ |
| 27 | User | app_metadata.role | String | + | auth.users | — | ✅ |
| 28 | DoctorProfile | id | UUID | + | 004_migration | L11 | ✅ |
| 29 | DoctorProfile | user_id | UUID | + | 004_migration | L12 | ✅ |
| 30 | DoctorProfile | full_name | String | + | 004_migration | L15 | ✅ |
| 31 | DoctorProfile | hospital | String | + | 004_migration | L25 | ✅ |
| 32 | DoctorProfile | primary_specialty | String | + | 004_migration | L23 | ✅ |
| 33 | DoctorProfile | account_status | String | + | 007_migration | L29 | ✅ |
| 34 | DoctorProfile | role | String | + | 007_migration | L25 | ✅ |
| 35 | Analysis | id | UUID | + | 001_migration | L16 | ✅ |
| 36 | Analysis | user_id | UUID | + | 001_migration | L17 | ✅ |
| 37 | Analysis | status | String | + | 001_migration | L20 | ✅ |
| 38 | Analysis | created_at | Timestamp | + | 001_migration | L62 | ✅ |
| 39 | Analysis | segmentation_status | String | + | 001_migration | L33 | ✅ |
| 40 | Analysis | gradcam_status | String | + | 001_migration | L45 | ✅ |

**Total Atribut: 40**

---

## C. Matriks Operasi: Sumber Kode → Diagram

| # | Kelas | Operasi | Parameter | Return | File Sumber | Baris | Status |
|---|-------|---------|-----------|--------|-------------|-------|--------|
| 1 | AuthContext | signIn | email, password, role | Promise | AuthContext.tsx | L132 | ✅ |
| 2 | AuthContext | signUp | email, password, ... | Promise | AuthContext.tsx | L175 | ✅ |
| 3 | AuthContext | signOut | — | Promise | AuthContext.tsx | L206 | ✅ |
| 4 | AnalysisClient | createAnalysis | file: File | Promise | analysis.ts | L185 | ✅ |
| 5 | AnalysisClient | getAnalysis | id: String | Promise | analysis.ts | L194 | ✅ |
| 6 | AnalysisClient | listHistory | — | Promise | analysis.ts | L212 | ✅ |
| 7 | AnalysisClient | deleteAnalysis | id: String | Promise | analysis.ts | L218 | ✅ |
| 8 | DoctorProfileService | fetchDoctorProfile | user | Promise | profile.ts | L108 | ✅ |
| 9 | DoctorProfileService | saveDoctorProfile | user, data | Promise | profile.ts | L271 | ✅ |
| 10 | DoctorProfileService | uploadAvatar | user, file | Promise | profile.ts | L212 | ✅ |
| 11 | AnalysisController | create_analysis | — | Response | analysis_controller.py | L13 | ✅ |
| 12 | AnalysisController | get_analysis | analysis_id: String | Response | analysis_controller.py | L42 | ✅ |
| 13 | AnalysisController | list_history | — | Response | analysis_controller.py | L62 | ✅ |
| 14 | AnalysisController | delete_analysis | analysis_id: String | Response | analysis_controller.py | L80 | ✅ |
| 15 | AdminController | list_doctors | status? | Response | admin_controller.py | L12 | ✅ |
| 16 | AdminController | approve_doctor | id: String | Response | admin_controller.py | L49 | ✅ |
| 17 | AdminController | reject_doctor | id: String | Response | admin_controller.py | L66 | ✅ |
| 18 | AdminController | get_statistics | — | Response | admin_controller.py | L87 | ✅ |
| 19 | AnalysisService | validate_and_decode_image | file | Tuple | analysis_service.py | L301 | ✅ |
| 20 | AnalysisService | create_analysis | file, user_id | Dict | analysis_service.py | L369 | ✅ |
| 21 | AnalysisService | get_analysis | id, user_id | Dict | analysis_service.py | L502 | ✅ |
| 22 | AnalysisService | list_user_analyses | user_id | List | analysis_service.py | L635 | ✅ |
| 23 | AnalysisService | delete_analysis | id, user_id | Boolean | analysis_service.py | L688 | ✅ |
| 24 | AdminService | list_doctors | status? | List | admin_service.py | L42 | ✅ |
| 25 | AdminService | approve_doctor | id, approved_by | Dict | admin_service.py | L135 | ✅ |
| 26 | AdminService | reject_doctor | id, approved_by, reason | Dict | admin_service.py | L235 | ✅ |
| 27 | AdminService | get_statistics | — | Dict | admin_service.py | L328 | ✅ |
| 28 | AnalysisRepository | create | user_id, data | Dict | analysis_repository.py | L38 | ✅ |
| 29 | AnalysisRepository | get_by_id | id, user_id | Optional | analysis_repository.py | L71 | ✅ |
| 30 | AnalysisRepository | list_by_user | user_id | List | analysis_repository.py | L101 | ✅ |
| 31 | AnalysisRepository | update | id, user_id, data | Optional | analysis_repository.py | L133 | ✅ |
| 32 | AnalysisRepository | delete | id, user_id | Boolean | analysis_repository.py | L172 | ✅ |
| 33 | StorageService | upload_file | path, bytes, type | String | storage_service.py | L50 | ✅ |
| 34 | StorageService | download_file | path | Bytes | storage_service.py | L78 | ✅ |
| 35 | StorageService | create_signed_url | path, expires | String | storage_service.py | L102 | ✅ |
| 36 | StorageService | delete_file | path | Boolean | storage_service.py | L130 | ✅ |
| 37 | StorageService | generate_asset_path | user, analysis, cat, file | String | storage_service.py | L160 | ✅ |
| 38 | AnalysisJobQueue | try_enqueue | job | Boolean | analysis_service.py | L254 | ✅ |
| 39 | AnalysisJobQueue | drain_one | — | Boolean | analysis_service.py | L245 | ✅ |
| 40 | AnalysisJobQueue | pending_count | — | Integer | analysis_service.py | L258 | ✅ |
| 41 | AIInference | run_pipeline | bytes, config | PipelineResult | pipeline.py | L101 | ✅ |
| 42 | AIInference | predict | image, config | SegmentationResult | pipeline.py / segmentation.py | L98 | ✅ |
| 43 | AIInference | generate_gradcam | tensor, ... | GradCAMResult | pipeline.py / gradcam.py | L99 | ✅ |
| 44 | ModelService | load | — | Module | model_service.py | L61 | ✅ |
| 45 | ModelService | predict_logits | tensor | Tensor | model_service.py | L112 | ✅ |
| 46 | ModelService | metadata | — | Dict | model_service.py | L95 | ✅ |
| 47 | ModelService | get_gradcam_target_layer | — | Module | model_service.py | L140 | ✅ |
| 48 | User | get_profile | — | DoctorProfile | auth.users | — | ✅ |
| 49 | User | get_analyses | — | List<Analysis> | analyses table | — | ✅ |
| 50 | DoctorProfile | get_user | — | User | doctor_profiles | — | ✅ |
| 51 | Analysis | get_user | — | User | analyses | — | ✅ |

**Total Operasi: 51**

---

## D. Matriks Relasi: Sumber Kode → Diagram (20 Relasi)

| No | Relasi | Jenis | Multiplicity | Dasar Implementasi / Bukti |
|----|--------|-------|--------------|---------------------------|
| 1 | AuthContext → SupabasePlatform | Dependency | 1 : 1 | `AuthContext.tsx` L1-11 pakai `supabase` client |
| 2 | AnalysisClient → AnalysisController | Dependency | 1 : 1 | `analysis.ts` L185 `POST /api/analysis` |
| 3 | AnalysisClient → SupabasePlatform | Dependency | 1 : 1 | `analysis.ts` L101 Bearer token |
| 4 | DoctorProfileService → SupabasePlatform | Dependency | 1 : 1 | `profile.ts` query/upsert `doctor_profiles` |
| 5 | AnalysisController → AnalysisService | Dependency | 1 : 1 | `analysis_controller.py` L10-11 |
| 6 | AdminController → AdminService | Dependency | 1 : 1 | `admin_controller.py` L9-10 |
| 7 | AnalysisService → AnalysisRepository | Dependency | 1 : 1 | `analysis_service.py` L291 |
| 8 | AnalysisService → StorageService | Dependency | 1 : 1 | `analysis_service.py` L292 |
| 9 | AnalysisService → AnalysisJobQueue | Dependency | 1 : 1 | `analysis_service.py` L240 |
| 10 | AnalysisService → SupabasePlatform | Dependency | 1 : 1 | `storage_service` via service-role |
| 11 | AnalysisService → AIInference | Dependency | 1 : 1 | `analysis_service.py` L293 `run_pipeline` |
| 12 | AnalysisRepository → SupabasePlatform | Dependency | 1 : 1 | `analysis_repository.py` L2 `get_supabase_client()` |
| 13 | StorageService → SupabasePlatform | Dependency | 1 : 1 | `storage_service.py` L4-5 `get_supabase_client()` |
| 14 | AdminService → SupabasePlatform | Dependency | 1 : 1 | `admin_service.py` L6 `get_supabase_client(use_service_role=True)` |
| 15 | AIInference → ModelService | Dependency | 1 : 1 | `segmentation.py` L13 `ModelService` |
| 16 | ModelService → ModelConfig | Aggregation | 1 : 1 | `model_service.py` L22 `__init__(config)` |
| 17 | User → DoctorProfile | Association | 1 : 0..1 | `004_migration` L12 `user_id` UNIQUE NOT NULL FK |
| 18 | User → Analysis | Association | 1 : * | `001_migration` L17 `user_id` NOT NULL FK ON DELETE CASCADE |
| 19 | SupabasePlatform → DoctorProfile | Trigger | trigger | `008_migration` `handle_new_doctor_signup()` |
| 20 | SupabasePlatform → Analysis | Association | DB | `001_migration` tabel `analyses` |

---

## E. Multiplicity Verifikasi Database

| Relasi | Bukti Constraint | Multiplicity | Status |
|--------|-----------------|--------------|--------|
| User → DoctorProfile | `004_migration` L46 `doctor_profiles_user_id_key UNIQUE (user_id)` | 1 : 0..1 | ✅ |
| User → Analysis | `001_migration` L17 `user_id UUID NOT NULL REFERENCES auth.users(id)` ON DELETE CASCADE | 1 : * | ✅ |
| DoctorProfile → User (approved_by) | `007_migration` L33 `approved_by UUID REFERENCES auth.users(id)` | 0..1 | Catatan (tidak ditampilkan) |

---

## F. Total Statistik

| Komponen | Jumlah |
|----------|--------|
| Kelas | 17 |
| Atribut | 40 |
| Operasi | 51 |
| Relasi | 20 |
| Multiplicity labels | 17 |

---
