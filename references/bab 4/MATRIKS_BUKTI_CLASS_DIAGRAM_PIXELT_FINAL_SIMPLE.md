# MATRIKS BUKTI AUDIT CLASS DIAGRAM PIXELT FINAL SIMPLE

**Sistem:** PIXEL-T (Segmentasi Polip USG dengan Transfer Learning dan Explainable AI)  
**Versi Diagram:** `CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE.{drawio,png,svg}`  
**Jumlah Kelas:** 15  
**Jumlah Relasi:** 17  
**Tanggal Audit:** 6 November 2026

---

## A. Matriks Kelas: Sumber Kode → Diagram (15 Kelas)

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
| 9 | AIInference | <<module>> | AI Pipeline | `ai/inference/pipeline.py` | L101 | ✅ |
| 10 | ModelService | <<service>> | AI Pipeline | `ai/inference/model_service.py` | L19 | ✅ |
| 11 | ModelConfig | <<dataclass>> | AI Pipeline | `ai/config/model_config.py` | L19 | ✅ |
| 12 | SupabasePlatform | <<external>> | External | — (abstraksi layanan) | — | ✅ |
| 13 | User | <<entity>> | Database | `database/migrations/001_create_analyses_and_storage.sql` | L14 | ✅ |
| 14 | DoctorProfile | <<entity>> | Database | `database/migrations/004_create_doctor_profiles.sql` | L10 | ✅ |
| 15 | Analysis | <<entity>> | Database | `database/migrations/001_create_analyses_and_storage.sql` | L14 | ✅ |

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
| 10 | AnalysisService | pipeline_runner | Callable | - | analysis_service.py | L293 | ✅ |
| 11 | AdminService | client | SupabaseClient | - | admin_service.py | L34 | ✅ |
| 12 | AnalysisRepository | client | SupabaseClient | - | analysis_repository.py | L17 | ✅ |
| 13 | ModelService | config | ModelConfig | + | model_service.py | L22 | ✅ |
| 14 | ModelConfig | architecture | String | + | model_config.py | L20 | ✅ |
| 15 | ModelConfig | encoder | String | + | model_config.py | L21 | ✅ |
| 16 | ModelConfig | input_size | Integer | + | model_config.py | L27 | ✅ |
| 17 | ModelConfig | threshold | Float | + | model_config.py | L29 | ✅ |
| 18 | ModelConfig | checkpoint_sha256 | String | + | model_config.py | L38 | ✅ |
| 19 | User | id | UUID | + | 001_migration | L16 | ✅ |
| 20 | User | email | String | + | auth.users | — | ✅ |
| 21 | User | app_metadata.role | String | + | auth.users | — | ✅ |
| 22 | DoctorProfile | id | UUID | + | 004_migration | L11 | ✅ |
| 23 | DoctorProfile | user_id | UUID | + | 004_migration | L12 | ✅ |
| 24 | DoctorProfile | full_name | String | + | 004_migration | L15 | ✅ |
| 25 | DoctorProfile | hospital | String | + | 004_migration | L25 | ✅ |
| 26 | DoctorProfile | primary_specialty | String | + | 004_migration | L23 | ✅ |
| 27 | DoctorProfile | account_status | String | + | 007_migration | L29 | ✅ |
| 28 | DoctorProfile | role | String | + | 007_migration | L25 | ✅ |
| 29 | Analysis | id | UUID | + | 001_migration | L16 | ✅ |
| 30 | Analysis | user_id | UUID | + | 001_migration | L17 | ✅ |
| 31 | Analysis | status | String | + | 001_migration | L20 | ✅ |
| 32 | Analysis | created_at | Timestamp | + | 001_migration | L62 | ✅ |
| 33 | Analysis | segmentation_status | String | + | 001_migration | L33 | ✅ |
| 34 | Analysis | gradcam_status | String | + | 001_migration | L45 | ✅ |

**Total Atribut: 34**

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
| 33 | AIInference | run_pipeline | bytes, config | PipelineResult | pipeline.py | L101 | ✅ |
| 34 | AIInference | predict | image, config | SegmentationResult | pipeline.py / segmentation.py | L98 | ✅ |
| 35 | AIInference | generate_gradcam | tensor, ... | GradCAMResult | pipeline.py / gradcam.py | L99 | ✅ |
| 36 | ModelService | load | — | Module | model_service.py | L61 | ✅ |
| 37 | ModelService | predict_logits | tensor | Tensor | model_service.py | L112 | ✅ |
| 38 | ModelService | metadata | — | Dict | model_service.py | L95 | ✅ |

**Total Operasi: 38**

---

## D. Matriks Relasi: Sumber Kode → Diagram (17 Relasi)

| No | Relasi | Jenis | Multiplicity | Dasar Implementasi / Bukti |
|----|--------|-------|--------------|---------------------------|
| 1 | AuthContext → SupabasePlatform | Dependency | 1 : 1 | `AuthContext.tsx` L1-11 pakai `supabase` client |
| 2 | AnalysisClient → AnalysisController | Dependency | 1 : 1 | `analysis.ts` L185 `POST /api/analysis` |
| 3 | AnalysisClient → SupabasePlatform | Dependency | 1 : 1 | `analysis.ts` L101 Bearer token |
| 4 | DoctorProfileService → SupabasePlatform | Dependency | 1 : 1 | `profile.ts` query/upsert `doctor_profiles` |
| 5 | AnalysisController → AnalysisService | Aggregation | 1 : 1 | `analysis_controller.py` L10-11 |
| 6 | AdminController → AdminService | Aggregation | 1 : 1 | `admin_controller.py` L9-10 |
| 7 | AnalysisService → AnalysisRepository | Aggregation | 1 : 1 | `analysis_service.py` L291 |
| 8 | AnalysisService → SupabasePlatform | Dependency | 1 : 1 | `storage_service` via service-role |
| 9 | AnalysisService → AIInference | Dependency | 1 : 1 | `analysis_service.py` L293 `run_pipeline` |
| 10 | AnalysisRepository → SupabasePlatform | Dependency | 1 : 1 | `analysis_repository.py` L2 `get_supabase_client()` |
| 11 | AdminService → SupabasePlatform | Dependency | 1 : 1 | `admin_service.py` L6 `get_supabase_client(use_service_role=True)` |
| 12 | AIInference → ModelService | Dependency | 1 : 1 | `segmentation.py` L13 `ModelService` |
| 13 | ModelService → ModelConfig | Aggregation | 1 : 1 | `model_service.py` L22 `__init__(config)` |
| 14 | User → DoctorProfile | Association | 1 : 0..1 | `004_migration` L12 `user_id` UNIQUE NOT NULL FK |
| 15 | User → Analysis | Association | 1 : * | `001_migration` L17 `user_id` NOT NULL FK ON DELETE CASCADE |
| 16 | SupabasePlatform → DoctorProfile | Trigger | trigger | `008_migration` `handle_new_doctor_signup()` |
| 17 | SupabasePlatform → Analysis | Association | DB | `001_migration` tabel `analyses` |

---

## E. Multiplicity Verifikasi Database

| Relasi | Bukti Constraint | Multiplicity | Status |
|--------|-----------------|--------------|--------|
| User → DoctorProfile | `004_migration` L46 `doctor_profiles_user_id_key UNIQUE (user_id)` | 1 : 0..1 | ✅ |
| User → Analysis | `001_migration` L17 `user_id UUID NOT NULL REFERENCES auth.users(id)` | 1 : * | ✅ |
| DoctorProfile → User (approved_by) | `007_migration` L33 `approved_by UUID REFERENCES auth.users(id)` | 0..1 | Catatan |

---

## F. Total Statistik

| Komponen | Jumlah |
|----------|--------|
| Kelas | 15 |
| Atribut | 34 |
| Operasi | 38 |
| Relasi | 17 |
| Multiplicity labels | 15 |

---
