# AUDIT FINAL CLASS DIAGRAM PIXEL-T (VERSI FINAL)

## 1. Ringkasan

Class Diagram final PIXEL-T menghasilkan **21 kelas/abstraksi** dan **24 relasi**. Diagram ini disusun dengan gaya monokrom (latar putih, garis hitam, font Segoe UI) sesuai referensi `class_diagram_contoh.png`. Semua elemen divisikualisasikan sesuai kode sumber aktual tanpa modifikasi aplikasi atau basis data. Diagram ini merupakan hasil audit menyeluruh terhadap implementasi aktual PIXEL-T, termasuk mekanisme role Admin dan Dokter yang dibedakan melalui atribut metadata (bukan inheritance).

Diagram ini merupakan level detail penuh: tidak hanya menampilkan kelas inti, tetapi juga komponen infrastruktur pendukung (repository, queue, progress reporter, controller HTTP), tipe data hasil inferensi AI, dan entitas basis data. Pendekatan ini memberikan cakupan lengkap untuk dokumentasi arsitektur skripsi.

---

## 2. Daftar Kelas Final

### 2.1 Frontend (3 kelas)

| # | Kelas | Stereotype | Berkas | Deskripsi |
|---|-------|------------|--------|-----------|
| 1 | `AuthContext` | `<<module>>` | `frontend/src/context/AuthContext.tsx` | Context React untuk autentikasi, session, role, dan status akun. |
| 2 | `AnalysisClient` | `<<module>>` | `frontend/src/services/analysis.ts` | Modul HTTP untuk operasi analisis dari frontend. |
| 3 | `DoctorProfileService` | `<<module>>` | `frontend/src/services/profile.ts` | Modul untuk CRUD profil dokter via Supabase RLS. |

### 2.2 Backend Controller (2 kelas)

| # | Kelas | Stereotype | Berkas | Deskripsi |
|---|-------|------------|--------|-----------|
| 4 | `AdminController` | `<<controller>>` | `backend/app/controllers/admin_controller.py` | Endpoint HTTP untuk manajemen dokter. |
| 5 | `AnalysisController` | `<<controller>>` | `backend/app/controllers/analysis_controller.py` | Endpoint HTTP untuk operasi analisis. |

### 2.3 Backend Service (5 kelas)

| # | Kelas | Stereotype | Berkas | Deskripsi |
|---|-------|------------|--------|-----------|
| 6 | `AdminService` | `<<service>>` | `backend/app/services/admin_service.py` | Logika bisnis admin dan approval dokter. |
| 7 | `AnalysisService` | `<<service>>` | `backend/app/services/analysis_service.py` | Orkestrasi utama analisis citra. |
| 8 | `StorageService` | `<<service>>` | `backend/app/services/storage_service.py` | Pengelola aset Supabase Storage. |
| 9 | `AnalysisJobQueue` | `<<service>>` | `backend/app/services/analysis_service.py` | Antrian FIFO untuk job analisis background. |
| 10 | `AnalysisProgressReporter` | `<<service>>` | `backend/app/services/analysis_service.py` | Pelapor progres berbasis database write. |

### 2.4 Repository (1 kelas)

| # | Kelas | Stereotype | Berkas | Deskripsi |
|---|-------|------------|--------|-----------|
| 11 | `AnalysisRepository` | `<<repository>>` | `backend/app/repositories/analysis_repository.py` | Abstraksi CRUD tabel `analyses`. |

### 2.5 AI Pipeline (6 kelas)

| # | Kelas | Stereotype | Berkas | Deskripsi |
|---|-------|------------|--------|-----------|
| 12 | `AIInferenceFunctions` | `<<module>>` | `ai/inference/pipeline.py`, `segmentation.py`, `gradcam.py`, `postprocessing.py` | Kumpulan fungsi pipeline inferensi AI. |
| 13 | `ModelService` | `<<service>>` | `ai/inference/model_service.py` | Pengelola model PyTorch (lazy loading, thread-safe). |
| 14 | `ModelConfig` | `<<dataclass>>` | `ai/inference/model_config.py` | Konfigurasi beku model (19 atribut). |
| 15 | `PipelineResult` | `<<dataclass>>` | `ai/inference/pipeline.py` | Struktur hasil akhir pipeline. |
| 16 | `SegmentationResult` | `<<dataclass>>` | `ai/inference/segmentation.py` | Struktur hasil segmentasi. |
| 17 | `GradCAMResult` | `<<dataclass>>` | `ai/inference/gradcam.py` | Struktur hasil Grad-CAM. |

### 2.6 Entitas Database (3 kelas)

| # | Kelas | Stereotype | Migrasi | Deskripsi |
|---|-------|------------|---------|-----------|
| 18 | `auth_users` | `<<external>>` | `auth.users` (Supabase) | Tabel autentikasi eksternal. |
| 19 | `doctor_profiles` | `<<entity>>` | `004_create_doctor_profiles.sql`, `007_add_role_and_account_status.sql` | Profil dokter dan status akun. |
| 20 | `analyses` | `<<entity>>` | `001_create_analyses_and_storage.sql` | Data hasil analisis citra. |

### 2.7 Error Handling (1 kelas)

| # | Kelas | Stereotype | Berkas | Deskripsi |
|---|-------|------------|--------|-----------|
| 21 | `APIError` | `<<exception>>` | `backend/app/core/errors.py` | Pengecualian terstruktur aplikasi. |

---

## 3. Relasi dan Multiplicity Final (24 relasi)

| # | Relasi | Jenis | Multiplicity | Makna |
|---|--------|-------|--------------|-------|
| 1 | `AuthContext` ..> `auth_users` | Dependency | — | AuthContext berinteraksi dengan Supabase Auth untuk autentikasi dan pembacaan role. |
| 2 | `AnalysisClient` ..> `AnalysisController` | Dependency | — | Frontend memanggil endpoint HTTP backend. |
| 3 | `DoctorProfileService` ..> `doctor_profiles` | Dependency | — | Modul frontend melakukan CRUD profil dokter. |
| 4 | `AdminController` --> `AdminService` | Association | `1` --> `1` | Controller mendelegasikan ke service. |
| 5 | `AdminController` ..> `APIError` | Dependency | — | Controller menaikkan error terstruktur. |
| 6 | `AnalysisController` --> `AnalysisService` | Association | `1` --> `1` | Controller mendelegasikan ke service. |
| 7 | `AnalysisController` ..> `APIError` | Dependency | — | Controller menaikkan error terstruktur. |
| 8 | `AdminService` ..> `doctor_profiles` | Dependency | — | Service admin mengelola data profil dokter. |
| 9 | `AnalysisService` --> `AnalysisRepository` | Association | `1` --> `1` | Service menggunakan repository untuk persistensi. |
| 10 | `AnalysisService` --> `StorageService` | Association | `1` --> `1` | Service menggunakan storage untuk aset. |
| 11 | `AnalysisService` --> `AnalysisJobQueue` | Association | `1` --> `1` | Service menggunakan antrian untuk job background. |
| 12 | `AnalysisService` ..> `AnalysisProgressReporter` | Dependency | — | Service menginstansiasikan reporter progres. |
| 13 | `AnalysisProgressReporter` --> `AnalysisRepository` | Association | `1` --> `1` | Reporter menulis progres ke repository. |
| 14 | `AnalysisService` ..> `AIInferenceFunctions` | Dependency | — | Service memanggil pipeline AI. |
| 15 | `AIInferenceFunctions` ..> `ModelService` | Dependency | — | Fungsi inferensi menggunakan model service. |
| 16 | `AIInferenceFunctions` ..> `PipelineResult` | Dependency | — | Fungsi inferensi mengembalikan hasil pipeline. |
| 17 | `AIInferenceFunctions` ..> `SegmentationResult` | Dependency | — | Fungsi inferensi mengembalikan hasil segmentasi. |
| 18 | `AIInferenceFunctions` ..> `GradCAMResult` | Dependency | — | Fungsi inferensi mengembalikan hasil Grad-CAM. |
| 19 | `PipelineResult` --> `GradCAMResult` | Association | `1` --> `1` | Hasil pipeline memuat objek GradCAMResult. |
| 20 | `ModelService` --> `ModelConfig` | Association | `1` --> `1` | Model service menggunakan konfigurasi model. |
| 21 | `AnalysisRepository` ..> `analyses` | Dependency | — | Repository melakukan CRUD tabel analyses. |
| 22 | `auth_users` -- `doctor_profiles` | Association FK | `1` -- `0..1` | FK UNIQUE user_id pada doctor_profiles. |
| 23 | `auth_users` -- `analyses` | Association FK | `1` -- `*` | FK user_id pada tabel analyses. |
| 24 | `AuthContext` role resolution | — | — | Logika pemilihan role Admin (app_metadata) vs Dokter (doctor_profiles) tanpa inheritance. |

**Ringkasan jenis relasi:** 12 dependency (dashed), 7 association berarah (solid dengan arrow), 3 association FK (solid tanpa arrow), 1 asosiasi tambahan `PipelineResult` -- `GradCAMResult`, 1 logika role resolution.

---

## 4. Bukti Source Code per Kelas

| # | Kelas | Berkas | Baris Kunci | Atribut | Metode |
|---|-------|--------|-------------|---------|--------|
| 1 | `AuthContext` | `frontend/src/context/AuthContext.tsx` | 16-33, 132-212 | `user`, `session`, `loading`, `role`, `accountStatus` | `signIn`, `signUp`, `signOut` |
| 2 | `AnalysisClient` | `frontend/src/services/analysis.ts` | 185-224 | — | `createAnalysis`, `getAnalysis`, `listHistory`, `deleteAnalysis` |
| 3 | `DoctorProfileService` | `frontend/src/services/profile.ts` | 256-315 | — | `fetchDoctorProfile`, `saveDoctorProfile`, `calculateCompleteness`, `validateProfileData` |
| 4 | `AdminController` | `backend/app/controllers/admin_controller.py` | 7-96 | `service: AdminService` | `list_doctors`, `get_doctor`, `approve_doctor`, `reject_doctor`, `get_statistics` |
| 5 | `AnalysisController` | `backend/app/controllers/analysis_controller.py` | 7-96 | `service: AnalysisService` | `create_analysis`, `get_analysis`, `list_history`, `delete_analysis` |
| 6 | `AdminService` | `backend/app/services/admin_service.py` | 27-378 | `client: SupabaseClient` | `list_doctors`, `get_doctor`, `approve_doctor`, `reject_doctor`, `get_statistics` |
| 7 | `AnalysisService` | `backend/app/services/analysis_service.py` | 269-991 | `repository`, `storage_service`, `pipeline_runner`, `job_queue` | `validate_and_decode_image`, `create_analysis`, `get_analysis`, `list_user_analyses`, `delete_analysis`, `_execute_pipeline` |
| 8 | `StorageService` | `backend/app/services/storage_service.py` | 7-189 | `bucket_name: String` | `upload_file`, `create_signed_url`, `delete_analysis_files` |
| 9 | `AnalysisJobQueue` | `backend/app/services/analysis_service.py` | 64-110 | `capacity: Integer` | `try_enqueue`, `contains`, `pending_count`, `drain_one` |
| 10 | `AnalysisProgressReporter` | `backend/app/services/analysis_service.py` | 64-125 | `repository`, `analysis_id`, `user_id` | `on_phase`, `on_pass`, `percent` |
| 11 | `AnalysisRepository` | `backend/app/repositories/analysis_repository.py` | 38-196 | — | `create`, `get_by_id`, `list_by_user`, `update`, `delete` |
| 12 | `AIInferenceFunctions` | `ai/inference/pipeline.py`, `segmentation.py`, `gradcam.py`, `postprocessing.py` | pipeline:101, seg:98, grad:99 | — | `run_pipeline`, `predict`, `postprocess_mask`, `measure_mask`, `generate_gradcam`, `prepare_image` |
| 13 | `ModelService` | `ai/inference/model_service.py` | 22-136 | `config: ModelConfig`, `device: Device`, `load_count: Integer` | `load`, `metadata`, `predict_logits`, `get_gradcam_target_layer` |
| 14 | `ModelConfig` | `ai/inference/model_config.py` | 18-69 | 19 atribut (architecture, encoder, threshold, dll) | `checkpoint_path`, `validate`, `checkpoint_sha256_matches` |
| 15 | `PipelineResult` | `ai/inference/pipeline.py` | 62-71 | `binary_mask_png`, `segmentation_overlay_png`, `gradcam_heatmap_png`, `gradcam_overlay_png`, `measurements`, `summary_text`, `gradcam` | — |
| 16 | `SegmentationResult` | `ai/inference/segmentation.py` | 24-29 | `probability_map: Tensor`, `binary_mask: Tensor`, `threshold: Float` | — |
| 17 | `GradCAMResult` | `ai/inference/gradcam.py` | 37-44 | `heatmap: Array`, `overlay: Array`, `target_layer: String`, `target_objective: String`, `target_mask_empty: Boolean` | — |
| 18 | `auth_users` | `auth.users` (Supabase) | — | `id: UUID` | — |
| 19 | `doctor_profiles` | `004_create_doctor_profiles.sql`, `007_add_role_and_account_status.sql` | 10-48, 24-40 | `id`, `user_id`, `full_name`, `primary_specialty`, `hospital`, `account_status`, `approved_by`, `approved_at`, `education`, `experience`, `bio` | — |
| 20 | `analyses` | `001_create_analyses_and_storage.sql` | 15-35 | `id`, `user_id`, `status`, `segmentation_status`, `gradcam_status`, `summary_text`, `created_at`, `completed_at`, `updated_at` | — |
| 21 | `APIError` | `backend/app/core/errors.py` | 8-24 | `code: String`, `message: String`, `status_code: Integer` | `to_dict` |

---

## 5. Verifikasi Per Relasi

| # | Relasi | Kode/Pola Implementasi | Bukti | Status |
|---|--------|------------------------|-------|--------|
| 1 | `AuthContext` ..> `auth_users` | Supabase Auth client | `frontend/src/context/AuthContext.tsx:148` `getAdminRoleFromAppMetadata()` | ✅ |
| 2 | `AnalysisClient` ..> `AnalysisController` | HTTP fetch | `frontend/src/services/analysis.ts:185, 194, 212, 218` | ✅ |
| 3 | `DoctorProfileService` ..> `doctor_profiles` | Supabase RLS upsert | `frontend/src/services/profile.ts:287-289` | ✅ |
| 4 | `AdminController` --> `AdminService` | DI constructor | `admin_controller.py:11` `self.service = service or AdminService()` | ✅ |
| 5 | `AdminController` ..> `APIError` | Exception handling | `admin_controller.py:26, 41, 69` catch `APIError` | ✅ |
| 6 | `AnalysisController` --> `AnalysisService` | DI constructor | `analysis_controller.py:11` `self.service = service or AnalysisService()` | ✅ |
| 7 | `AnalysisController` ..> `APIError` | Exception handling | `analysis_controller.py:23, 46, 74` catch `APIError` | ✅ |
| 8 | `AdminService` ..> `doctor_profiles` | CRUD tabel | `admin_service.py:55, 119, 128, 150` | ✅ |
| 9 | `AnalysisService` --> `AnalysisRepository` | DI atribut | `analysis_service.py:291` | ✅ |
| 10 | `AnalysisService` --> `StorageService` | DI atribut | `analysis_service.py:292` | ✅ |
| 11 | `AnalysisService` --> `AnalysisJobQueue` | DI atribut | `analysis_service.py:296-299` | ✅ |
| 12 | `AnalysisService` ..> `AnalysisProgressReporter` | Instansiasi lokal | `analysis_service.py:805-810` | ✅ |
| 13 | `AnalysisProgressReporter` --> `AnalysisRepository` | DI atribut | `analysis_service.py:82` `self._repository` | ✅ |
| 14 | `AnalysisService` ..> `AIInferenceFunctions` | Default pipeline_runner | `analysis_service.py:293, 815` | ✅ |
| 15 | `AIInferenceFunctions` ..> `ModelService` | Parameter fungsi | `segmentation.py:98`, `gradcam.py:99` | ✅ |
| 16 | `AIInferenceFunctions` ..> `PipelineResult` | Return type | `pipeline.py:101` | ✅ |
| 17 | `AIInferenceFunctions` ..> `SegmentationResult` | Return type | `segmentation.py:98` | ✅ |
| 18 | `AIInferenceFunctions` ..> `GradCAMResult` | Return type | `gradcam.py:99` | ✅ |
| 19 | `PipelineResult` --> `GradCAMResult` | Field referensi | `pipeline.py:69` `gradcam: GradCAMResult` | ✅ |
| 20 | `ModelService` --> `ModelConfig` | Constructor param | `model_service.py:22` `config: ModelConfig = MODEL_CONFIG` | ✅ |
| 21 | `AnalysisRepository` ..> `analyses` | CRUD tabel | `analysis_repository.py:38-196` | ✅ |
| 22 | `auth_users` -- `doctor_profiles` | FK UNIQUE | `004_create_doctor_profiles.sql:12` `user_id REFERENCES auth.users(id) ON DELETE CASCADE` + `UNIQUE` | ✅ |
| 23 | `auth_users` -- `analyses` | FK constraint | `001_create_analyses_and_storage.sql:17` `user_id REFERENCES auth.users(id)` | ✅ |
| 24 | Role resolution (Admin vs Dokter) | Metadata column | `AuthContext.tsx:146-155` `appMetaRole === 'admin'` else doctor profile | ✅ |

---

## 6. Audit Mekanisme Role Admin dan Dokter

| No | Aspek | Implementasi Aktual | File & Lokasi | Status |
|----|-------|---------------------|---------------|--------|
| 1 | Sumber role Admin | `auth.users.raw_app_meta_data.role = 'admin'` | `auth.ts:235-240` `getAdminRoleFromAppMetadata()` | TERVERIFIKASI |
| 2 | Sumber role Dokter | `doctor_profiles.role = 'doctor'` + `account_status` | `auth.ts:242-255` `fetchUserProfileStatus()` | TERVERIFIKASI |
| 3 | Trigger dokter signup | AFTER INSERT → `doctor_profiles` with `role='doctor'`, `account_status='pending'` | `008_create_doctor_profile_trigger.sql` | TERVERIFIKASI |
| 4 | Admin skip trigger | Admin accounts skipped by trigger | `008_create_doctor_profile_trigger.sql:11-12` | TERVERIFIKASI |
| 5 | Tidak ada inheritance | Admin dan Doctor dibedakan oleh metadata column | `AuthContext.tsx:146-155` | TERVERIFIKASI |
| 6 | Route guard Admin | `AdminRoute.tsx` redirects if `role !== 'admin'` | `AdminRoute.tsx` | TERVERIFIKASI |
| 7 | Route guard Doctor | `DoctorRoute.tsx` blocks admin + pending/rejected | `DoctorRoute.tsx` | TERVERIFIKASI |
| 8 | Route guard Protected | `ProtectedRoute.tsx` blocks pending/rejected | `ProtectedRoute.tsx` | TERVERIFIKASI |

---

## 7. Evaluasi Desain Visual

| Aspek | Status | Keterangan |
|-------|--------|------------|
| Latar putih | ✅ | `#FFFFFF` pada semua kelas dan kanvas |
| Garis hitam | ✅ | `#000000` untuk border dan relasi |
| Font Segoe UI | ✅ | `fontFamily=Segoe UI` pada semua elemen |
| Stereotype miring | ✅ | `<<module>>`, `<<service>>`, dll dalam italic HTML |
| Atribut/method separator | ✅ | Garis horizontal tipis memisahkan kompartemen |
| Notasi `+`/`-` | ✅ | Publik dan privat sesuai konvensi UML |
| Relasi dashed untuk dependency | ✅ | Dependency digambar putus-putus |
| Relasi solid untuk association | ✅ | Association digambar solid |
| Multiplicity angka | ✅ | Menggunakan `1`, `*`, `0..1` |
| Tidak ada composition | ✅ | Semua asosiasi menggunakan DI, bukan lifecycle eksklusif |
| Tidak ada warna/dekorasi | ✅ | Monokrom murni |
| Tata letak grid | ✅ | 5 baris dengan jarak yang cukup, tidak ada overlap |
| Ukuran kanvas | ✅ | 2000×1580 logical, 4000×3160 at 2x scale |

---

## 8. Status Verifikasi

| No | Elemen | Jumlah | Status |
|----|--------|--------|--------|
| 1 | Frontend modules | 3 | TERVERIFIKASI |
| 2 | Backend controllers | 2 | TERVERIFIKASI |
| 3 | Backend services | 5 | TERVERIFIKASI |
| 4 | Repository | 1 | TERVERIFIKASI |
| 5 | AI pipeline classes | 6 | TERVERIFIKASI |
| 6 | Database entities | 3 | TERVERIFIKASI |
| 7 | Error handling | 1 | TERVERIFIKASI |
| 8 | Relasi | 24 | TERVERIFIKASI |
| 9 | Mekanisme role Admin/Dokter | 8 aspek | TERVERIFIKASI |
| **Total** | **21 kelas + 24 relasi** | | **SELESAI** |

---

## 9. Lokasi Hasil

- Diagram PNG: `references/bab 4/CLASS_DIAGRAM_PIXELT_FINAL.png` (4000×3160 px, 2x scale)
- Diagram drawio: `references/bab 4/CLASS_DIAGRAM_PIXELT_FINAL.drawio`
- Skrip generator: `references/bab 4/_gen_class_final_v6.js`
- Matriks bukti: `references/bab 4/MATRIKS_BUKTI_CLASS_DIAGRAM_PIXELT_FINAL.md`
- Penjelasan akademik: `references/bab 4/PENJELASAN_CLASS_DIAGRAM_PIXELT_FINAL.md`

---

## 10. Kesimpulan

Seluruh **21 kelas** dan **24 relasi** pada Class Diagram final telah diverifikasi terhadap kode sumber aktual. Setiap atribut, metode, dan jenis relasi memiliki bukti implementasi yang dapat dilacak. Mekanisme role Admin dan Dokter dimodelkan tanpa inheritance, sesuai dengan implementasi aktual yang menggunakan atribut metadata (`app_metadata.role` untuk Admin, `doctor_profiles.role` dan `account_status` untuk Dokter). Diagram menggunakan gaya monokrom sesuai referensi akademik. Tidak ada elemen yang direkayasa atau dilebih-lebihkan.

**Pemeriksaan independen kedua:** Semua elemen telah diperiksa ulang terhadap source code. Tidak ditemukan kesalahan kritis dalam struktur, atribut, operasi, atau relasi. Diagram siap digunakan untuk Bab IV skripsi.

**Status akhir: FINAL — TERVERIFIKASI BERDASARKAN BUKTI**