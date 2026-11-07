# MATRIKS BUKTI AUDIT INDEPENDEN CLASS DIAGRAM PIXEL-T

**Versi Diagram:** `CLASS_DIAGRAM_PIXELT_FINAL_INDEPENDENT_AUDIT`  
**Tanggal Audit:** 5 November 2026  
**Lokasi:** `references/bab 4/`  
**Status:** FINAL — Siap Publikasi Tesis Bab IV

---

## A. Matriks Kelas: Implementasi Aktual → Elemen Diagram

| # | Kelas Diagram | Stereotipe | File Sumber | Baris Kunci | Bukti Atribut | Bukti Operasi | Status | Tindakan |
|---|---------------|------------|-------------|-------------|---------------|---------------|--------|----------|
| 1 | AuthContext | `<<module>>` | `frontend/src/context/AuthContext.tsx` | L46-50 | `user: User\|null` L46, `session: Session\|null` L47, `role: string\|null` L49, `accountStatus: string\|null` L50, `loading: boolean` L48 | `signIn()` L132, `signUp()` L175, `signOut()` L206 | ✓ Diperbaiki | Tambah `loading: Boolean` |
| 2 | AnalysisClient | `<<module>>` | `frontend/src/services/analysis.ts` | L34-224 | `-` (tidak ada atribut) | `createAnalysis()` L185, `getAnalysis()` L194, `listHistory()` L212, `deleteAnalysis()` L218 | ✓ Diperbaiki | Hapus `authenticatedRequest: Function` (bukan atribut) |
| 3 | DoctorProfileService | `<<module>>` | `frontend/src/services/profile.ts` | L108-391 | `supabase` (import) | `fetchDoctorProfile(user)` L108, `saveDoctorProfile(user,data)` L271, `uploadAvatar(user,file)` L212, `deleteAvatar(user)` L256, `validateProfileData(data)` L168 | ✓ **Ditulis Ulang** | Ganti 4 operasi salah: `upsertProfile`→`saveDoctorProfile`, `getProfile`→`fetchDoctorProfile`, `deleteProfile`→`deleteAvatar`, hapus `calculateStats()` (tidak ada) |
| 4 | AnalysisController | `<<controller>>` | `backend/app/controllers/analysis_controller.py` | L7-96 | `service: AnalysisService` L10-11 | `create_analysis()` L13, `get_analysis(id)` L41, `list_history()` L61, `delete_analysis(id)` L79 | ✓ Benar | - |
| 5 | AdminController | `<<controller>>` | `backend/app/controllers/admin_controller.py` | L6-98 | `service: AdminService` L9-10 | `list_doctors()` L12, `get_doctor(id)` L28, `approve_doctor(id)` L48, `reject_doctor(id)` L65, `get_statistics()` L86 | ✓ Benar | - |
| 6 | AnalysisService | `<<service>>` | `backend/app/services/analysis_service.py` | L269-302 | `repository: AnalysisRepository` L291, `storage_service: StorageService` L292 | `create_analysis(file_storage,user_id)` L369, `get_analysis(id,user_id)` L502, `list_user_analyses(user_id)` L635, `delete_analysis(id,user_id)` L688 | ✓ Benar | - |
| 7 | AdminService | `<<service>>` | `backend/app/services/admin_service.py` | L27-41 | `client: SupabaseClient` (via `get_supabase_client`) | `list_doctors(status)` L42, `approve_doctor(doctor_id, by)` L135, `reject_doctor(doctor_id, by, reason)` L235, `get_statistics()` L328 | ✓ Benar | - |
| 8 | StorageService | `<<service>>` | `backend/app/services/storage_service.py` | L7-26 | `bucket_name: String` L20 | `upload_file(path, file_bytes, content_type)` L119, `create_signed_url(path, expires_in)` L149, `delete_analysis_files(paths)` L175 | ✓ Benar | - |
| 9 | APIError | `<<exception>>` | `backend/app/core/errors.py` | L8-23 | `code: String` L10, `message: String` L13, `status_code: Integer` L14 | `to_dict()` L16 | ✓ Benar | - |
| 10 | AnalysisRepository | `<<repository>>` | `backend/app/repositories/analysis_repository.py` | L5-196 | `client: SupabaseClient` L15-22 | `create(user_id, data)` L38, `get_by_id(id, user_id)` L71, `list_by_user(user_id)` L100, `update(id, user_id, data)` L133, `delete(id, user_id)` L172 | ✓ Diperbaiki | `update_status(id,status)` → `update(id,user_id,data)` (tidak ada method terpisah) |
| 11 | AISegmentationPipeline | `<<module>>` | `ai/inference/pipeline.py` | L101-168 | `-` (modul) | `run_pipeline(original_bytes, config, on_phase, on_pass)` L101, `predict(image, ...)` (segmentation.py L98), `generate_gradcam(tensor, ...)` (gradcam.py L99) | ✓ Benar | Abstraksi modul pipeline AI |
| 12 | SupabaseAuth | `<<external>>` | Supabase Auth (`auth.users`) | - | `id: UUID` (PK) | `-` | ✓ Benar | Representasi layanan eksternal |
| 13 | doctor_profiles | `<<entity>>` | `database/migrations/004_create_doctor_profiles.sql` L10-46 | L10-46 | `id: UUID` L11, `user_id: UUID` L12, `full_name: String` L15, `primary_specialty: String` L23, `hospital: String` L26, `account_status: String` (mig 007 L28), `role: String` (mig 007 L24), `approved_by: UUID` L33, `approved_at: Timestamp` L34 | `-` | ✓ Diperbaiki | Tambah `role: String` (Migration 007) |
| 14 | analyses | `<<entity>>` | `database/migrations/001_create_analyses_and_storage.sql` L14-65 | L14-65 | `id: UUID` L16, `user_id: UUID` L17, `status: String` L20, `segmentation_status: String` L33, `gradcam_status: String` (mig 002), `summary_text: String` L57, `created_at: Timestamp` L62, `completed_at: Timestamp` L63 | `-` | ✓ Benar | - |

---

## B. Matriks Atribut: Sumber Kode → Diagram

| # | Kelas | Atribut | Tipe | Visibility | File Sumber | Baris | Status |
|---|-------|---------|------|------------|-------------|-------|--------|
| 1 | AuthContext | user | User\|null | - | AuthContext.tsx | L46 | ✓ |
| 2 | AuthContext | session | Session\|null | - | AuthContext.tsx | L47 | ✓ |
| 3 | AuthContext | role | String | - | AuthContext.tsx | L49 | ✓ |
| 4 | AuthContext | accountStatus | String | - | AuthContext.tsx | L50 | ✓ |
| 5 | AuthContext | loading | Boolean | - | AuthContext.tsx | L48 | ✓ Ditambah |
| 6 | AnalysisClient | - | - | - | analysis.ts | - | - (modul, tidak ada atribut) |
| 7 | DoctorProfileService | supabase | SupabaseClient | - | profile.ts | L1 | - (import, bukan atribut) |
| 8 | AnalysisController | service | AnalysisService | - | analysis_controller.py | L10 | ✓ |
| 9 | AdminController | service | AdminService | - | admin_controller.py | L9 | ✓ |
| 10 | AnalysisService | repository | AnalysisRepository | - | analysis_service.py | L291 | ✓ |
| 11 | AnalysisService | storage_service | StorageService | - | analysis_service.py | L292 | ✓ |
| 12 | AdminService | client | SupabaseClient | - | admin_service.py | L34-40 | ✓ |
| 13 | StorageService | bucket_name | String | - | storage_service.py | L20 | ✓ |
| 14 | APIError | code | String | + | errors.py | L10 | ✓ |
| 15 | APIError | message | String | + | errors.py | L13 | ✓ |
| 16 | APIError | status_code | Integer | + | errors.py | L14 | ✓ |
| 17 | AnalysisRepository | client | SupabaseClient | - | analysis_repository.py | L15 | ✓ |
| 18 | SupabaseAuth | id | UUID | + | Supabase Auth | - | ✓ |
| 19 | doctor_profiles | id | UUID | + | Migration 004 | L11 | ✓ |
| 20 | doctor_profiles | user_id | UUID | + | Migration 004 | L12 | ✓ |
| 21 | doctor_profiles | full_name | String | + | Migration 004 | L15 | ✓ |
| 22 | doctor_profiles | primary_specialty | String | + | Migration 004 | L23 | ✓ |
| 23 | doctor_profiles | hospital | String | + | Migration 004 | L26 | ✓ |
| 24 | doctor_profiles | account_status | String | + | Migration 007 | L28-29 | ✓ |
| 25 | doctor_profiles | role | String | + | Migration 007 | L24-25 | ✓ Ditambah |
| 26 | doctor_profiles | approved_by | UUID | + | Migration 007 | L33 | ✓ |
| 27 | doctor_profiles | approved_at | Timestamp | + | Migration 007 | L34 | ✓ |
| 28 | analyses | id | UUID | + | Migration 001 | L16 | ✓ |
| 29 | analyses | user_id | UUID | + | Migration 001 | L17 | ✓ |
| 30 | analyses | status | String | + | Migration 001 | L20 | ✓ |
| 31 | analyses | segmentation_status | String | + | Migration 001 | L33 | ✓ |
| 32 | analyses | gradcam_status | String | + | Migration 002 | L6 | ✓ |
| 33 | analyses | summary_text | String | + | Migration 001 | L57 | ✓ |
| 34 | analyses | created_at | Timestamp | + | Migration 001 | L62 | ✓ |
| 35 | analyses | completed_at | Timestamp | + | Migration 001 | L63 | ✓ |

---

## C. Matriks Operasi: Sumber Kode → Diagram

| # | Kelas | Operasi | Parameter | Return Type | Visibility | File Sumber | Baris | Status |
|---|-------|---------|-----------|-------------|------------|-------------|-------|--------|
| 1 | AuthContext | signIn | email, password, selectedRole? | Promise | + | AuthContext.tsx | L132 | ✓ |
| 2 | AuthContext | signUp | email, password, fullName?, hospitalName?, doctorSpecialty? | Promise | + | AuthContext.tsx | L175 | ✓ |
| 3 | AuthContext | signOut | - | Promise | + | AuthContext.tsx | L206 | ✓ |
| 4 | AnalysisClient | createAnalysis | file: File | Promise\<CreatedAnalysis\> | + | analysis.ts | L185 | ✓ |
| 5 | AnalysisClient | getAnalysis | id: string | Promise\<AnalysisDetail\> | + | analysis.ts | L194 | ✓ |
| 6 | AnalysisClient | listHistory | - | Promise\<HistoryList\> | + | analysis.ts | L212 | ✓ |
| 7 | AnalysisClient | deleteAnalysis | id: string | Promise\<void\> | + | analysis.ts | L218 | ✓ |
| 8 | DoctorProfileService | fetchDoctorProfile | user: User | Promise\<DoctorProfileData\> | + | profile.ts | L108 | ✓ (diganti `getProfile`) |
| 9 | DoctorProfileService | saveDoctorProfile | user: User, data: DoctorProfileData | Promise\<{data?, error?}\> | + | profile.ts | L271 | ✓ (diganti `upsertProfile`) |
| 10 | DoctorProfileService | uploadAvatar | user: User, file: File | Promise\<{url?, error?}\> | + | profile.ts | L212 | ✓ (baru) |
| 11 | DoctorProfileService | deleteAvatar | user: User | Promise\<{success?, error?}\> | + | profile.ts | L256 | ✓ (diganti `deleteProfile`) |
| 12 | DoctorProfileService | validateProfileData | data: DoctorProfileData | {isValid, errors} | + | profile.ts | L168 | ✓ (baru) |
| 13 | AnalysisController | create_analysis | - | JSON response | + | analysis_controller.py | L13 | ✓ |
| 14 | AnalysisController | get_analysis | analysis_id: str | JSON response | + | analysis_controller.py | L41 | ✓ |
| 15 | AnalysisController | list_history | - | JSON response | + | analysis_controller.py | L61 | ✓ |
| 16 | AnalysisController | delete_analysis | analysis_id: str | JSON response | + | analysis_controller.py | L79 | ✓ |
| 17 | AdminController | list_doctors | status? | JSON response | + | admin_controller.py | L12 | ✓ |
| 18 | AdminController | get_doctor | doctor_id: str | JSON response | + | admin_controller.py | L28 | ✓ |
| 19 | AdminController | approve_doctor | doctor_id: str | JSON response | + | admin_controller.py | L48 | ✓ |
| 20 | AdminController | reject_doctor | doctor_id: str | JSON response | + | admin_controller.py | L65 | ✓ |
| 21 | AdminController | get_statistics | - | JSON response | + | admin_controller.py | L86 | ✓ |
| 22 | AnalysisService | create_analysis | file_storage, user_id | Dict | + | analysis_service.py | L369 | ✓ |
| 23 | AnalysisService | get_analysis | analysis_id, user_id | Dict | + | analysis_service.py | L502 | ✓ |
| 24 | AnalysisService | list_user_analyses | user_id | List | + | analysis_service.py | L635 | ✓ |
| 25 | AnalysisService | delete_analysis | analysis_id, user_id | Boolean | + | analysis_service.py | L688 | ✓ |
| 26 | AdminService | list_doctors | status | List | + | admin_service.py | L42 | ✓ |
| 27 | AdminService | approve_doctor | id, by | Dict | + | admin_service.py | L135 | ✓ |
| 28 | AdminService | reject_doctor | id, by, reason | Dict | + | admin_service.py | L235 | ✓ |
| 29 | AdminService | get_statistics | - | Dict | + | admin_service.py | L328 | ✓ |
| 30 | StorageService | upload_file | path, bytes, type | String | + | storage_service.py | L119 | ✓ |
| 31 | StorageService | create_signed_url | path, exp | String | + | storage_service.py | L149 | ✓ |
| 32 | StorageService | delete_analysis_files | paths | Boolean | + | storage_service.py | L175 | ✓ |
| 33 | APIError | to_dict | - | Dict | + | errors.py | L16 | ✓ |
| 34 | AnalysisRepository | create | user_id, data | Dict | + | analysis_repository.py | L38 | ✓ |
| 35 | AnalysisRepository | get_by_id | id, user_id | Dict\|None | + | analysis_repository.py | L71 | ✓ |
| 36 | AnalysisRepository | list_by_user | user_id | List | + | analysis_repository.py | L100 | ✓ |
| 37 | AnalysisRepository | update | id, user_id, data | Dict\|None | + | analysis_repository.py | L133 | ✓ (diganti `update_status`) |
| 38 | AnalysisRepository | delete | id, user_id | Boolean | + | analysis_repository.py | L172 | ✓ |
| 39 | AISegmentationPipeline | run_pipeline | original, config, on_phase, on_pass | PipelineResult | + | pipeline.py | L101 | ✓ |
| 40 | AISegmentationPipeline | predict | image, model_service, config | SegmentationResult | + | segmentation.py | L98 | ✓ |
| 41 | AISegmentationPipeline | generate_gradcam | tensor, model_service | GradCAMResult | + | gradcam.py | L99 | ✓ |

---

## D. Matriks Relasi & Multiplicity: Bukti Kode dan Database

| No | Class A | Class B | Jenis Relasi | Mult A | Mult B | Basis Hubungan | File/Baris Bukti | Status |
|----|---------|---------|--------------|--------|--------|----------------|------------------|--------|
| 1 | AuthContext | SupabaseAuth | Association | 1 | 1 | AuthContext pakai Supabase client untuk auth | `AuthContext.tsx` L1-11, `lib/supabase.ts` | ✓ |
| 2 | AnalysisClient | AnalysisController | Association | 1 | 1 | HTTP request frontend→backend | `analysis.ts` L185 (`/analysis`), `analysis_controller.py` L13 | ✓ |
| 3 | DoctorProfileService | doctor_profiles | Association | 1 | 1 | Query/upsert tabel doctor_profiles | `profile.ts` L108, L271; Migration 004 L10 | ✓ |
| 4 | AnalysisController | AnalysisService | Association | 1 | 1 | Controller instantiate service | `analysis_controller.py` L10-11 | ✓ |
| 5 | AdminController | AdminService | Association | 1 | 1 | Controller instantiate service | `admin_controller.py` L9-10 | ✓ |
| 6 | AnalysisService | AnalysisRepository | Association | 1 | 1 | Service instantiate repository | `analysis_service.py` L291 | ✓ |
| 7 | AnalysisService | StorageService | Association | 1 | 1 | Service instantiate storage service | `analysis_service.py` L292 | ✓ |
| 8 | AnalysisService | AISegmentationPipeline | Association | 1 | 1 | Service call `run_pipeline()` | `analysis_service.py` L808 | ✓ |
| 9 | AnalysisService | analyses | Association | 1 | * | Service CRUD analyses table | `analysis_repository.py` L38, L71, L100, L133, L172 | ✓ |
| 10 | AnalysisService | APIError | Dependency | - | - | Service raise APIError exception | `analysis_service.py` L16, L379 | ✓ |
| 11 | AdminService | doctor_profiles | Association | 1 | * | Service CRUD doctor_profiles table | `admin_service.py` L54, L107, L165 | ✓ |
| 12 | AdminService | APIError | Dependency | - | - | Service raise APIError exception | `admin_service.py` L152, L250 | ✓ |
| 13 | doctor_profiles | SupabaseAuth | Association | 1 | 0..1 | FK user_id + UNIQUE constraint (max 1 profile/user) | Migration 004 L12, L46 | ✓ |
| 14 | analyses | SupabaseAuth | Association | 1 | * | FK user_id NOT NULL (tiap analysis milik 1 user) | Migration 001 L17 | ✓ |

---

## E. Matriks Tujuh Alur Aplikasi

| Fitur | Komponen Frontend | Context/Service | Backend | Repository/Database | External Service | Representasi Diagram | Status |
|-------|-------------------|-----------------|---------|---------------------|------------------|---------------------|--------|
| Sign Up | Register page | AuthContext.signUp → auth.ts registerUser | - | Trigger → doctor_profiles (mig 008) | Supabase Auth signUp | AuthContext → SupabaseAuth | ✓ |
| Sign In | Login page | AuthContext.signIn → auth.ts loginUser | - | doctor_profiles role/status | Supabase Auth signIn | AuthContext → SupabaseAuth | ✓ |
| Upload Image | Analysis page | AnalysisClient.createAnalysis | AnalysisController.create_analysis | AnalysisService.create_analysis → analyses INSERT | Supabase Storage upload | AnalysisClient→AnalysisController→AnalysisService→StorageService→analyses | ✓ |
| Segmentation | Polling getAnalysis | AnalysisClient.getAnalysis | AnalysisController.get_analysis | AnalysisService._execute_pipeline→run_pipeline→analyses UPDATE | AI Pipeline (PyTorch) | AnalysisService→AISegmentationPipeline→analyses | ✓ |
| History | History page | AnalysisClient.listHistory | AnalysisController.list_history | AnalysisService.list_user_analyses → analyses SELECT | Supabase Storage signed URL | AnalysisService→analyses→StorageService | ✓ |
| Doctor Profile | Profile page | DoctorProfileService.fetchDoctorProfile/saveDoctorProfile | - | doctor_profiles SELECT/UPSERT | Supabase Auth metadata sync | DoctorProfileService→doctor_profiles | ✓ |
| Sign Out | AppShell | AuthContext.signOut → auth.ts logoutUser | - | - | Supabase Auth signOut | AuthContext → SupabaseAuth | ✓ |

---

## F. Matriks Konsistensi Antardiagram

| Diagram Referensi | Konsistensi | Detail |
|-------------------|-------------|--------|
| ERD | ✓ | `analyses`, `doctor_profiles`, FK `user_id`, UNIQUE constraint sama |
| Use Case Diagram | ✓ | 7 use case terwakili oleh class di Class Diagram |
| Activity Diagram (7) | ✓ | Alur aktivitas sesuai sequence controller→service→repository |
| Sequence Diagram (7) | ✓ | Pesan antarobjek sesuai relasi Class Diagram |
| Class Diagram vs ERD | ✓ | Tabel `doctor_profiles.user_id` UNIQUE → multiplicity 0..1 terpenuhi |
| Class Diagram vs ERD | ✓ | Tabel `analyses.user_id` FK NOT NULL → multiplicity * terpenuhi |

---

## G. Catatan Perbaikan dari Versi Sebelumnya (FINAL_REVISED → INDEPENDENT_AUDIT)

| Elemen | Versi Sebelumnya | Versi INDEPENDENT_AUDIT | Alasan |
|--------|-----------------|------------------------|--------|
| `DoctorProfileService` operasi | `upsertProfile`, `getProfile`, `deleteProfile`, `calculateStats()` | `saveDoctorProfile`, `fetchDoctorProfile`, `uploadAvatar`, `deleteAvatar`, `validateProfileData` | Operasi sebelumnya tidak ada di source code `profile.ts` |
| `doctor_profiles` atribut | Tanpa `role` | Tambah `role: String` | Migration 007 menambahkan kolom `role` (krusial untuk model Admin/Dokter) |
| `AnalysisClient` atribut | `- authenticatedRequest: Function` | (dihapus) | `authenticatedRequest` adalah fungsi private module, bukan atribut objek |
| `AnalysisRepository` operasi | `update_status(id, status)` | `update(id, user_id, data)` | Tidak ada method `update_status` terpisah; `update()` digunakan untuk semua pembaruan termasuk status |

---

## H. Versi File yang Dijaga (Tidak Tertimpa)

| Versi | File | Status |
|-------|------|--------|
| Original | `CLASS_DIAGRAM_PIXELT_FINAL.drawio/.png` | Terjaga |
| Audited | `CLASS_DIAGRAM_PIXELT_FINAL_AUDITED.drawio/.png` | Terjaga |
| Neat | `CLASS_DIAGRAM_PIXELT_FINAL_NEAT.drawio/.png` | Terjaga |
| Revised | `CLASS_DIAGRAM_PIXELT_FINAL_REVISED.drawio/.png` | Terjaga |
| Independent Audit (baru) | `CLASS_DIAGRAM_PIXELT_FINAL_INDEPENDENT_AUDIT.drawio/.png` | **Baru** |

---

**Semua nomor baris dalam matriks ini adalah nomor baris aktual dari file source code yang telah dibaca langsung, bukan estimasi.**
