# MATRIKS BUKTI AUDIT CLASS DIAGRAM PIXEL-T FINAL_NEAT

**Format:** Matriks Validasi Kelas, Relasi, dan Alur  
**Lokasi:** `references/bab 4/`  
**Status Klasifikasi:**
- **TERVERIFIKASI** — didukung bukti implementasi yang dapat ditelusuri
- **SEBAGIAN TERVERIFIKASI** — hanya sebagian klaim didukung bukti
- **BELUM TERVERIFIKASI** — bukti tidak cukup
- **TIDAK SESUAI** — bertentangan dengan implementasi
- **PERLU KEPUTUSAN PENULIS** — berkaitan dengan pilihan pemodelan konseptual

---

## A. Matriks Validasi Kelas

| No. | Kelas pada Diagram | Lokasi Implementasi | Tanggung Jawab Aktual | Atribut Valid | Operasi Valid | Status | Rekomendasi |
|-----|-------------------|---------------------|----------------------|---------------|---------------|--------|-------------|
| 1 | AuthContext | `frontend/src/context/AuthContext.tsx` (lines 16-243) | State management auth frontend: user, session, role, accountStatus | user, session, role, accountStatus — **BENAR** | signIn, signUp, signOut — **BENAR** | TERVERIFIKASI | Pertahankan |
| 2 | SupabaseAuth | Layanan eksternal Supabase Auth (bukan class internal) | Autentikasi, JWT, app_metadata, user_metadata | Atribut `id: UUID` **tidak tepat** untuk layanan eksternal | Tidak ada operasi (layanan) | SEBAGIAN TERVERIFIKASI | Hapus atribut `id: UUID` atau ganti stereotype jadi `<<external>>` tanpa atribut |
| 3 | AdminService | `backend/app/services/admin_service.py` (lines 27-378) | CRUD registrasi dokter, statistik | client: SupabaseClient — **BENAR** | list_doctors, approve_doctor, reject_doctor, get_statistics — **BENAR** | TERVERIFIKASI | Pertahankan |
| 4 | doctor_profiles | `database/migrations/004_create_doctor_profiles.sql`, `007_add_role_and_account_status.sql` | Tabel profil dokter | id, user_id, full_name, primary_specialty, hospital, account_status, approved_by, approved_at — **BENAR** | N/A (entity) | TERVERIFIKASI | Pertahankan |
| 5 | AnalysisService | `backend/app/services/analysis_service.py` (lines 1-991) | Orkeestrasi analisis end-to-end | repository, storage_service — **BENAR** | create_analysis, get_analysis, list_user_analyses, delete_analysis — **BENAR** | TERVERIFIKASI | Pertahankan |
| 6 | analyses | `database/migrations/001_create_analyses_and_storage.sql`, `002_add_ai_pipeline_metadata.sql` | Tabel rekaman analisis | id, user_id, status, segmentation_status, gradcam_status, summary_text, created_at, completed_at — **BENAR** | N/A (entity) | TERVERIFIKASI | Pertahankan |
| 7 | StorageService | `backend/app/services/storage_service.py` (lines 1-189) | Operasi Supabase Storage | bucket_name — **BENAR** | upload_file, create_signed_url, delete_analysis_files — **BENAR** | TERVERIFIKASI | Pertahankan |
| 8 | AISegmentationPipeline | `ai/inference/pipeline.py` (lines 101-165) | Pipeline inferensi AI | Tidak ada atribut instance (modul fungsi) | run_pipeline, predict, generate_gradcam — **SEBAGIAN BENAR** (predict ada di segmentation.py) | SEBAGIAN TERVERIFIKASI | Atribut kosong OK, operasi run_pipeline benar. Catat: predict & generate_gradcam di file terpisah. |
| 9 | APIError | `backend/app/core/errors.py` (lines 8-23) | Exception envelope | code, message, status_code — **BENAR** | to_dict() — **BENAR** | TERVERIFIKASI | Pertahankan |
| 10 | **AnalysisController** (HILANG) | `backend/app/controllers/analysis_controller.py` (lines 7-96) | HTTP endpoint handler analisis | service: AnalysisService | create_analysis, get_analysis, list_history, delete_analysis | BELUM TERVERIFIKASI (HILANG) | **Tambahkan ke diagram** |
| 11 | **AdminController** (HILANG) | `backend/app/controllers/admin_controller.py` (lines 6-98) | HTTP endpoint handler admin | service: AdminService | list_doctors, get_doctor, approve_doctor, reject_doctor, get_statistics | BELUM TERVERIFIKASI (HILANG) | **Tambahkan ke diagram** |
| 12 | **AnalysisRepository** (HILANG) | `backend/app/repositories/analysis_repository.py` (lines 5-196) | CRUD tabel analyses | client: SupabaseClient | create, get_by_id, list_by_user, update_status, delete, validate_lifecycle_status | BELUM TERVERIFIKASI (HILANG) | **Tambahkan ke diagram** |
| 13 | **DoctorProfileService** (HILANG) | `frontend/src/services/profile.ts` (lines 1-391) | Frontend API profil dokter | supabase client | upsertProfile, getProfile, deleteProfile, calculateStats | BELUM TERVERIFIKASI (HILANG) | **Tambahkan ke diagram** |
| 14 | **AnalysisClient** (HILANG) | `frontend/src/services/analysis.ts` (lines 1-224) | Frontend API analisis | authenticatedRequest helper | createAnalysis, getAnalysis, listHistory, deleteAnalysis | BELUM TERVERIFIKASI (HILANG) | **Tambahkan ke diagram** |
| 15 | **ModelService** (HILANG) | `ai/inference/model_service.py` (lines 19-136) | Model loading U-Net ResNet50 | config: ModelConfig, _model, _device | load, predict_logits, get_gradcam_target_layer, metadata | BELUM TERVERIFIKASI (HILANG) | Opsional: tambahkan untuk kelengkapan AI |
| 16 | **ModelConfig** (HILANG) | `ai/config/model_config.py` (lines 18-69) | Konfigurasi model terverifikasi | architecture, encoder, threshold, checkpoint_path, dll | validate, checkpoint_sha256_matches | BELUM TERVERIFIKASI (HILANG) | Opsional: tambahkan untuk kelengkapan AI |
| 17 | **PipelineResult** (HILANG) | `ai/inference/pipeline.py` (lines 62-70) | Dataclass hasil pipeline | binary_mask_png, segmentation_overlay_png, gradcam_heatmap_png, gradcam_overlay_png, measurements, summary_text, gradcam | N/A (dataclass frozen) | BELUM TERVERIFIKASI (HILANG) | Opsional: tambahkan untuk kelengkapan AI |
| 18 | **SegmentationResult** (HILANG) | `ai/inference/segmentation.py` (lines 24-29) | Dataclass hasil segmentasi | probability_map, binary_mask, threshold | N/A (dataclass frozen) | BELUM TERVERIFIKASI (HILANG) | Opsional: tambahkan untuk kelengkapan AI |
| 19 | **GradCAMResult** (HILANG) | `ai/inference/gradcam.py` (lines 37-44) | Dataclass hasil Grad-CAM | heatmap, overlay, target_layer, target_objective, target_mask_empty | N/A (dataclass frozen) | BELUM TERVERIFIKASI (HILANG) | Opsional: tambahkan untuk kelengkapan AI |

---

## B. Matriks Validasi Relasi

| No. | Kelas Asal | Kelas Tujuan | Relasi pada Diagram | Bukti Implementasi | Kesesuaian | Koreksi Diperlukan |
|-----|-----------|-------------|---------------------|-------------------|------------|-------------------|
| 1 | AuthContext | SupabaseAuth | Association, solid, 1:1 | `AuthContext.tsx` import `supabase` dari `@/lib/supabase` (line 3), panggil `supabase.auth.signInWithPassword`, `signUp`, `signOut` | SESUAI | Tidak |
| 2 | AdminService | doctor_profiles | Association, solid, 1:* | `admin_service.py` query `doctor_profiles` via Supabase client (lines 45-60, 74-95, 107-128, 143-165) | SESUAI | Tidak |
| 3 | AdminService | APIError | Dependency, dashed, open arrow | `admin_service.py` import `APIError` dari `app.core.errors` (line 7), raise `APIError` (lines 61, 97, 130, 168) | SESUAI | Tidak |
| 4 | AnalysisService | analyses | Association, solid, 1:* | `analysis_service.py` gunakan `AnalysisRepository` untuk CRUD `analyses` (lines 17, 85, 110, 135, 200, 270) | SESUAI | Tidak |
| 5 | AnalysisService | StorageService | Association, solid, 1:1 | `analysis_service.py` import `StorageService` (line 18), instansiasi (line 225), panggil `upload_file`, `create_signed_url`, `delete_analysis_files` | SESUAI | Tidak |
| 6 | AnalysisService | AISegmentationPipeline | Association, solid, 1:1 | `analysis_service.py` import `run_pipeline` dari `ai.inference.pipeline` (line 22), panggil di `_run_pipeline_async` (line 340) | SESUAI | Tidak |
| 7 | AnalysisService | APIError | Dependency, dashed, open arrow | `analysis_service.py` import `APIError` (line 16), raise `APIError` (lines 235, 260, 300, 320) | SESUAI | Tidak |
| 8 | doctor_profiles | SupabaseAuth | Association, solid, **0..1 : 1** | Migration `004` line 12: `user_id UUID NOT NULL REFERENCES auth.users(id)`. **Setiap doctor_profiles memiliki tepat 1 user (1). Setiap auth.users memiliki 0..1 doctor_profiles.** | **TIDAK SESUAI** (TERBALIK) | **Perbaiki multiplicity: 1 pada doctor_profiles, 0..1 pada SupabaseAuth** |
| 9 | analyses | SupabaseAuth | Association, solid, **\* : 1** | Migration `001` line 17: `user_id UUID NOT NULL REFERENCES auth.users(id)`. **Setiap analyses memiliki tepat 1 user (1). Setiap auth.users memiliki banyak analyses (*).** | **TIDAK SESUAI** (TERBALIK) | **Perbaiki multiplicity: 1 pada analyses, * pada SupabaseAuth** |

---

## C. Matriks Validasi Alur (7 Skenario)

| No. | Skenario | Komponen yang Terlibat (Implementasi) | Kesesuaian dengan Class Diagram NEAT | Status |
|-----|----------|--------------------------------------|-------------------------------------|--------|
| 1 | **Sign Up** | `Register.tsx` → `auth.ts:registerUser()` → Supabase Auth `signUp` → trigger `handle_new_doctor_signup` (migration 008) → `doctor_profiles` insert (role='doctor', status='pending') | AuthContext → SupabaseAuth ditampilkan. Trigger dan doctor_profiles creation tidak sebagai relasi eksplisit. DoctorProfileService hilang. | SEBAGIAN TERVERIFIKASI |
| 2 | **Sign In** | `Login.tsx` → `auth.ts:loginUser()` → Supabase Auth `signInWithPassword` → `AuthContext` set `user`, `role` (dari `app_metadata`), `accountStatus` (dari `doctor_profiles` query) | AuthContext → SupabaseAuth ditampilkan. | TERVERIFIKASI |
| 3 | **Upload Image** | `NewAnalysis.tsx` → `analysis.ts:createAnalysis()` → `POST /api/analysis` → `AnalysisController.create_analysis()` → `AnalysisService.create_analysis()` → `StorageService.upload_file()` + `AnalysisRepository.create()` → `analyses` insert | AnalysisService → StorageService, analyses ditampilkan. **AnalysisController, AnalysisClient hilang.** | SEBAGIAN TERVERIFIKASI |
| 4 | **Segmentation** | `AnalysisController` → `AnalysisService._run_pipeline_async()` → `ai.inference.pipeline:run_pipeline()` → `predict()` → `generate_gradcam()` → hasil → `StorageService.upload_file()` + `AnalysisRepository.update_status()` | AnalysisService → AISegmentationPipeline, StorageService, analyses ditampilkan. **ModelService, PipelineResult, SegmentationResult, GradCAMResult, AnalysisRepository hilang.** | SEBAGIAN TERVERIFIKASI |
| 5 | **History** | `History.tsx` → `analysis.ts:listHistory()` → `GET /api/history` → `AnalysisController.list_history()` → `AnalysisService.list_user_analyses()` → `AnalysisRepository.list_by_user()` → `analyses` select | AnalysisService → analyses ditampilkan. **AnalysisController, AnalysisClient, AnalysisRepository hilang.** | SEBAGIAN TERVERIFIKASI |
| 6 | **Doctor Profile** | `DoctorProfile.tsx` → `profile.ts:upsertProfile()/getProfile()` → Supabase `doctor_profiles` upsert/select | doctor_profiles ditampilkan. **DoctorProfileService hilang.** | SEBAGIAN TERVERIFIKASI |
| 7 | **Sign Out** | `AuthContext.signOut()` → `auth.ts:logoutUser()` → Supabase Auth `signOut` | AuthContext → SupabaseAuth ditampilkan. | TERVERIFIKASI |

---

## D. Ringkasan Status Keseluruhan

| Kategori | Total | TERVERIFIKASI | SEBAGIAN TERVERIFIKASI | TIDAK SESUAI | HILANG (BELUM TERVERIFIKASI) |
|----------|-------|---------------|------------------------|--------------|-------------------------------|
| Kelas | 19 | 7 | 2 | 0 | 10 |
| Relasi | 9 | 7 | 0 | 2 | 0 |
| Alur | 7 | 2 | 5 | 0 | 0 |

**Kesimpulan Matriks:** Diagram NEAT memiliki fondasi yang baik (7/9 kelas core TERVERIFIKASI), tetapi **2 relasi multiplicity terbalik** dan **10 kelas arsitektur hilang** (5 wajib: AnalysisController, AdminController, AnalysisRepository, DoctorProfileService, AnalysisClient; 5 opsional untuk AI pipeline). Status keseluruhan: **BELUM LULUS — MEMERLUKAN REVISI STRUKTURAL**.