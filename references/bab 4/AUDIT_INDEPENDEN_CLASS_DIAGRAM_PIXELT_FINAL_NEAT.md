# AUDIT INDEPENDEN CLASS DIAGRAM PIXEL-T (FINAL_NEAT)

**Tanggal Audit:** 5 November 2026  
**File yang diaudit:** `CLASS_DIAGRAM_PIXELT_FINAL_NEAT.drawio` dan `CLASS_DIAGRAM_PIXELT_FINAL_NEAT.png`  
**Lokasi:** `references/bab 4/`  
**Status Akhir:** BELUM LULUS — MEMERLUKAN REVISI STRUKTURAL

---

## 1. Ringkasan Eksekutif

Class Diagram `CLASS_DIAGRAM_PIXELT_FINAL_NEAT` terdiri dari 9 kelas dan 9 relasi. Setelah audit menyeluruh terhadap source code frontend, backend, database migration, dan pipeline AI, ditemukan beberapa kesalahan struktural yang memerlukan revisi:

- **Multiplicity terbalik** pada 2 relasi (doctor_profiles ↔ SupabaseAuth dan analyses ↔ SupabaseAuth).
- **Kelas penting yang dihilangkan**: AnalysisController, AdminController, AnalysisRepository, DoctorProfileService, AnalysisClient.
- **Kelas AI pipeline yang dihilangkan**: ModelService, ModelConfig, PipelineResult, SegmentationResult, GradCAMResult.

Diagram saat ini tidak layak sebagai Class Diagram final untuk Bab IV skripsi tanpa revisi.

---

## 2. Peta Arsitektur PIXEL-T (berdasarkan source code)

```
FRONTEND (React + TypeScript)
├── src/context/AuthContext.tsx          -> AuthContext (state manager)
├── src/services/auth.ts                 -> AuthService (API client)
├── src/services/analysis.ts             -> AnalysisClient (API client)
├── src/services/profile.ts              -> DoctorProfileService (API client)
├── src/components/auth/
│   ├── ProtectedRoute.tsx               -> Route guard (clinical)
│   ├── DoctorRoute.tsx                  -> Route guard (doctor)
│   ├── AdminRoute.tsx                   -> Route guard (admin)
│   └── PublicOnlyRoute.tsx              -> Route guard (public)
├── src/pages/
│   ├── auth/Login.tsx, Register.tsx
│   ├── dashboard/Dashboard.tsx
│   ├── analysis/NewAnalysis.tsx, AnalysisResult.tsx
│   ├── history/History.tsx, HistoryDetail.tsx
│   ├── profile/DoctorProfile.tsx
│   └── admin/AdminDashboard.tsx
└── src/routes/AppRoutes.tsx

BACKEND (Flask + Python)
├── app/routes/analysis.py               -> Route: /api/analysis, /api/history
├── app/routes/admin.py                  -> Route: /api/admin/doctors
├── app/controllers/analysis_controller.py -> AnalysisController
├── app/controllers/admin_controller.py   -> AdminController
├── app/services/analysis_service.py     -> AnalysisService
├── app/services/admin_service.py        -> AdminService
├── app/services/storage_service.py      -> StorageService
├── app/repositories/analysis_repository.py -> AnalysisRepository
├── app/core/auth.py                     -> require_auth, require_admin, require_approved_doctor
├── app/core/supabase.py                 -> Supabase client
├── app/core/errors.py                   -> APIError
└── app/core/config.py

AI PIPELINE (Python)
├── ai/inference/pipeline.py             -> run_pipeline(), PipelineResult
├── ai/inference/segmentation.py         -> predict(), SegmentationResult
├── ai/inference/gradcam.py              -> generate_gradcam(), GradCAMResult
├── ai/inference/model_service.py        -> ModelService
├── ai/inference/preprocessing.py        -> prepare_image()
├── ai/inference/postprocessing.py       -> postprocess_mask(), measure_mask()
└── ai/config/model_config.py            -> ModelConfig, MODEL_CONFIG

DATABASE (Supabase / PostgreSQL)
├── auth.users                           -> External auth table (Supabase Auth)
├── doctor_profiles                      -> Table: id, user_id, role, account_status, ...
└── analyses                             -> Table: id, user_id, status, ...
```

---

## 3. Audit Setiap Kelas pada Diagram NEAT

Tabel berikut memeriksa 9 kelas yang muncul pada diagram NEAT:

| No. | Kelas pada Diagram | Stereotype | Lokasi Implementasi | Tanggung Jawab Aktual | Status | Catatan |
|-----|-------------------|------------|---------------------|----------------------|--------|---------|
| 1 | AuthContext | `<<module>>` | `frontend/src/context/AuthContext.tsx` | Pengelolaan sesi auth, role, accountStatus di frontend | TERVERIFIKASI | Atribut `user`, `session`, `role`, `accountStatus` sesuai. Operasi `signIn`, `signUp`, `signOut` sesuai. |
| 2 | SupabaseAuth | `<<external>>` | Supabase Auth (layanan eksternal) | Autentikasi pengguna, penyimpanan app_metadata | SEBAGIAN TERVERIFIKASI | Atribut `id: UUID` tidak terdefinisi sebagai atribut kelas eksternal; lebih tepat modeling sebagai layanan eksternal tanpa atribut internal. |
| 3 | AdminService | `<<service>>` | `backend/app/services/admin_service.py` | Manajemen registrasi dokter (list, approve, reject, statistik) | TERVERIFIKASI | Atribut `client`, operasi `list_doctors`, `approve_doctor`, `reject_doctor`, `get_statistics` sesuai. |
| 4 | doctor_profiles | `<<entity>>` | `database/migrations/004_create_doctor_profiles.sql`, `007_add_role_and_account_status.sql` | Tabel profil dokter dengan user_id FK ke auth.users | TERVERIFIKASI | Atribut `id`, `user_id`, `full_name`, `primary_specialty`, `hospital`, `account_status`, `approved_by`, `approved_at` sesuai migration. |
| 5 | AnalysisService | `<<service>>` | `backend/app/services/analysis_service.py` | Orkeestrasi analisis: create, get, list, delete, pemanggilan pipeline AI | TERVERIFIKASI | Atribut `repository`, `storage_service`. Operasi `create_analysis`, `get_analysis`, `list_user_analyses`, `delete_analysis` sesuai. |
| 6 | analyses | `<<entity>>` | `database/migrations/001_create_analyses_and_storage.sql` | Tabel rekaman analisis citra dengan FK ke auth.users | TERVERIFIKASI | Atribut `id`, `user_id`, `status`, `segmentation_status`, `gradcam_status`, `summary_text`, `created_at`, `completed_at` sesuai. |
| 7 | StorageService | `<<service>>` | `backend/app/services/storage_service.py` | Operasi Supabase Storage: upload, signed URL, delete | TERVERIFIKASI | Atribut `bucket_name`. Operasi `upload_file`, `create_signed_url`, `delete_analysis_files` sesuai. |
| 8 | AISegmentationPipeline | `<<module>>` | `ai/inference/pipeline.py` | Pipeline inferensi AI: run_pipeline menghasilkan PipelineResult | TERVERIFIKASI | Operasi `run_pipeline` sesuai. Namun model hasilnya (PipelineResult, SegmentationResult, GradCAMResult) tidak ditampilkan. |
| 9 | APIError | `<<exception>>` | `backend/app/core/errors.py` | Kelas exception dengan kode, pesan, status_code | TERVERIFIKASI | Atribut `code`, `message`, `status_code`. Operasi `to_dict()` sesuai. |

**Kesimpulan audit kelas:** 7 dari 9 kelas TERVERIFIKASI. 2 kelas (SupabaseAuth, AISegmentationPipeline) SEBAGIAN TERVERIFIKASI karena atribut dan representasi kelas eksternal/abstraksi perlu penyesuaian.

---

## 4. Kelas yang Hilang dari Diagram NEAT

Berikut kelas yang ada dalam source code tetapi TIDAK dimasukkan ke diagram NEAT:

| No. | Kelas yang Hilang | Stereotype | Lokasi Implementasi | Alasan Penting untuk Ditampilkan |
|-----|-------------------|------------|---------------------|----------------------------------|
| 10 | AnalysisController | `<<controller>>` | `backend/app/controllers/analysis_controller.py` | Controller HTTP untuk endpoint analisis (create, get, list, delete). Komponen arsitektur backend yang nyata. |
| 11 | AdminController | `<<controller>>` | `backend/app/controllers/admin_controller.py` | Controller HTTP untuk endpoint admin (list doctors, approve, reject, statistics). |
| 12 | AnalysisRepository | `<<repository>>` | `backend/app/repositories/analysis_repository.py` | Repository yang langsung dipakai AnalysisService untuk CRUD tabel `analyses`. |
| 13 | DoctorProfileService | `<<module>>` | `frontend/src/services/profile.ts` | Service frontend untuk CRUD profil dokter (upsert, get, delete). |
| 14 | AnalysisClient | `<<module>>` | `frontend/src/services/analysis.ts` | Service frontend untuk pemanggilan API analisis ke backend. |
| 15 | ModelService | `<<service>>` | `ai/inference/model_service.py` | Pemuat model U-Net ResNet-50, digunakan oleh pipeline AI. |
| 16 | ModelConfig | `<<module>>` | `ai/config/model_config.py` | Konfigurasi model (architecture, encoder, threshold, checkpoint). |
| 17 | PipelineResult | `<<dataclass>>` | `ai/inference/pipeline.py` | Hasil akhir pipeline AI (mask, overlay, gradcam, measurements). |
| 18 | SegmentationResult | `<<dataclass>>` | `ai/inference/segmentation.py` | Hasil segmentasi (probability map, binary mask, threshold). |
| 19 | GradCAMResult | `<<dataclass>>` | `ai/inference/gradcam.py` | Hasil Grad-CAM (heatmap, overlay, target layer). |

**Kesimpulan:** Diagram NEAT menghilangkan 10 kelas yang merupakan komponen arsitektur nyata. Untuk skripsi, minimal controllers, repository, dan 2 service frontend harus ditampilkan.

---

## 5. Audit Relasi Antarclass (9 relasi pada diagram NEAT)

| No. | Kelas Asal | Kelas Tujuan | Jenis Relasi | Arah | Multiplicity (Diagram) | Multiplicity (Benar) | Bukti Implementasi | Status |
|-----|-----------|-------------|-------------|------|----------------------|---------------------|-------------------|--------|
| 1 | AuthContext | SupabaseAuth | Association | AuthContext → SupabaseAuth | 1 : 1 | 1 : 1 (konseptual) | `AuthContext.tsx` import `supabase` dari `@/lib/supabase`, panggil `supabase.auth.signInWithPassword` dll. | TERVERIFIKASI |
| 2 | AdminService | doctor_profiles | Association | AdminService → doctor_profiles | 1 : * | 1 : * (konseptual) | `admin_service.py` query `doctor_profiles` untuk list, approve, reject. | TERVERIFIKASI |
| 3 | AdminService | APIError | Dependency | AdminService → APIError | (dashed) | (dashed) | `admin_service.py` raise `APIError` dari `app.core.errors`. | TERVERIFIKASI |
| 4 | AnalysisService | analyses | Association | AnalysisService → analyses | 1 : * | 1 : * (konseptual) | `analysis_service.py` gunakan `AnalysisRepository` untuk CRUD `analyses`. | TERVERIFIKASI |
| 5 | AnalysisService | StorageService | Association | AnalysisService → StorageService | 1 : 1 | 1 : 1 | `analysis_service.py` import `StorageService`, panggil `upload_file`, `create_signed_url`. | TERVERIFIKASI |
| 6 | AnalysisService | AISegmentationPipeline | Association | AnalysisService → AISegmentationPipeline | 1 : 1 | 1 : 1 | `analysis_service.py` panggil `run_pipeline` dari `ai.inference.pipeline`. | TERVERIFIKASI |
| 7 | AnalysisService | APIError | Dependency | AnalysisService → APIError | (dashed) | (dashed) | `analysis_service.py` raise `APIError`. | TERVERIFIKASI |
| 8 | doctor_profiles | SupabaseAuth | Association | doctor_profiles → SupabaseAuth | 0..1 : 1 | **1 : 0..1** (TERBALIK) | Migration `004`: `doctor_profiles.user_id UUID NOT NULL REFERENCES auth.users(id)`. Setiap profil memiliki tepat 1 user; setiap user memiliki 0..1 profil. | TIDAK SESUAI |
| 9 | analyses | SupabaseAuth | Association | analyses → SupabaseAuth | * : 1 | **1 : * (TERBALIK)** | Migration `001`: `analyses.user_id UUID NOT NULL REFERENCES auth.users(id)`. Setiap analisis memiliki tepat 1 user; setiap user memiliki banyak analisis. | TIDAK SESUAI |

**Kesimpulan audit relasi:** 7 dari 9 relasi TERVERIFIKASI. 2 relasi (no. 8 dan 9) TIDAK SESUAI karena multiplicity terbalik.

---

## 6. Audit Role Admin dan Dokter

### Implementasi Aktual

**Admin:**
- Role disimpan di `auth.users.raw_app_meta_data.role = 'admin'` (server-write-only via Supabase Admin API)
- Tidak ada baris di `doctor_profiles` untuk admin (trigger `handle_new_doctor_signup` skip admin)
- Diverifikasi oleh backend `require_admin` decorator (`app/core/auth.py` line 144-152): membaca `app_metadata.role`
- Frontend `AuthContext` cek `app_metadata.role` terlebih dahulu, lalu fallback ke `doctor_profiles` lookup

**Dokter:**
- Role disimpan di `doctor_profiles.role = 'doctor'`
- `account_status`: `pending` / `approved` / `rejected`
- Dibuat otomatis oleh trigger `handle_new_doctor_signup` setelah signup melalui `auth.users`
- Diverifikasi oleh backend `require_approved_decor` (`app/core/auth.py` line 278-304): query `doctor_profiles` untuk role dan account_status
- Frontend `DoctorRoute` blokir jika `role === 'admin'` atau `accountStatus` pending/rejected

### Pemodelan pada Diagram NEAT

Diagram NEAT memodelkan role melalui:
- `AuthContext` memiliki atribut `role: String` dan `accountStatus: String` — **BENAR**, mencerminkan state frontend
- `doctor_profiles` memiliki atribut `role` (tidak ditampilkan dalam atribut yang terlihat, tapi ada di migration) dan `account_status: String` — **BENAR**
- Tidak ada inheritance antara Admin dan Dokter — **BENAR**, sesuai implementasi (tidak ada subclassing)

**Kesimpulan:** Pemodelan role Admin dan Dokter pada diagram NEAT sudah tepat (tidak ada inheritance, dibedakan melalui metadata/kolom). Namun, tidak ada kelas yang mewakili Admin secara eksplisit di luar `AuthContext` dan `AdminService`.

---

## 7. Audit Kesesuaian dengan Tujuh Alur Sistem

| No. | Skenario | Komponen yang Terlibat | Implementasi Aktual | Kesesuaian dengan Diagram NEAT | Status |
|-----|----------|----------------------|-------------------|-------------------------------|--------|
| 1 | Sign Up | Register.tsx, AuthContext, auth.ts, Supabase Auth, trigger `handle_new_doctor_signup` | Frontend panggil `registerUser` → Supabase Auth signup → trigger buat `doctor_profiles` row dengan status `pending` | AuthContext → SupabaseAuth ditampilkan. Trigger dan doctor_profiles creation tidak ditampilkan sebagai relasi eksplisit. | SEBAGIAN TERVERIFIKASI |
| 2 | Sign In | Login.tsx, AuthContext, auth.ts, Supabase Auth | Frontend panggil `loginUser` → Supabase Auth signIn → AuthContext set user, role, accountStatus | AuthContext → SupabaseAuth ditampilkan. | TERVERIFIKASI |
| 3 | Upload Image | NewAnalysis.tsx, analysis.ts, AnalysisController, AnalysisService, StorageService, analyses table | Frontend upload → POST /api/analysis → controller → service → storage upload + create analysis record | AnalysisService → StorageService dan analyses ditampilkan. AnalysisController dan AnalysisClient hilang. | SEBAGIAN TERVERIFIKASI |
| 4 | Segmentation | AnalysisController, AnalysisService, AISegmentationPipeline, ModelService, ai pipeline | Controller → service → `run_pipeline` → model inference → hasil disimpan ke analyses | AnalysisService → AISegmentationPipeline ditampilkan. ModelService, pipeline dataclasses hilang. | SEBAGIAN TERVERIFIKASI |
| 5 | History | History.tsx, analysis.ts, AnalysisController, AnalysisService, analyses table | Frontend GET /api/history → controller → service → list_user_analyses | AnalysisService → analyses ditampilkan. Controller dan client hilang. | SEBAGIAN TERVERIFIKASI |
| 6 | Doctor Profile | DoctorProfile.tsx, profile.ts, doctor_profiles table | Frontend upsert/get profil → Supabase doctor_profiles | doctor_profiles ditampilkan. DoctorProfileService hilang. | SEBAGIAN TERVERIFIKASI |
| 7 | Sign Out | AuthContext, auth.ts, Supabase Auth | `signOut()` → Supabase auth signOut | AuthContext → SupabaseAuth ditampilkan. | TERVERIFIKASI |

**Kesimpulan audit alur:** 2 dari 7 alur TERVERIFIKASI sepenuhnya. 5 alur SEBAGIAN TERVERIFIKASI karena kelas controller, repository, dan frontend service hilang dari diagram.

---

## 8. Audit Konsistensi dengan Diagram Lain

| Aspek | Konsistensi | Catatan |
|-------|------------|---------|
| ERD (`doctor_profiles` ↔ `auth.users`, `analyses` ↔ `auth.users`) | TIDAK KONSISTEN | Multiplicity terbalik pada 2 relasi yang menghubungkan ke SupabaseAuth/auth.users. |
| Use Case Diagram | TERVERIFIKASI | Kelas yang ditampilkan mendukung use case yang ada. |
| Activity Diagram | SEBAGIAN TERVERIFIKASI | Kelas layanan sesuai, tapi controller dan repository yang muncul dalam sequence tidak ada di class diagram. |
| Sequence Diagram | SEBAGIAN TERVERIFIKASI | AnalysisController dan AnalysisRepository muncul dalam sequence tapi tidak ada di class diagram. |

---

## 9. Temuan Utama

1. **Multiplicity terbalik** pada relasi `doctor_profiles → SupabaseAuth` (harus 1 : 0..1, diagram menunjukkan 0..1 : 1).
2. **Multiplicity terbalik** pada relasi `analyses → SupabaseAuth` (harus 1 : *, diagram menunjukkan * : 1).
3. **Kelas controller hilang**: `AnalysisController` dan `AdminController` adalah komponen backend nyata yang menangani HTTP request.
4. **Kelas repository hilang**: `AnalysisRepository` langsung dipakai oleh `AnalysisService` untuk operasi database.
5. **Kelas service frontend hilang**: `DoctorProfileService` dan `AnalysisClient` adalah modul frontend yang berkomunikasi dengan backend.
6. **Kelas AI pipeline hilang**: `ModelService`, `ModelConfig`, `PipelineResult`, `SegmentationResult`, `GradCAMResult` adalah bagian dari struktur sistem AI.
7. **Pemodelan role Admin/Dokter sudah BENAR** — tidak ada inheritance, dibedakan melalui `app_metadata.role` (admin) dan `doctor_profiles.role` + `account_status` (dokter).

---

## 10. Rekomendasi

**Status: BELUM LULUS — MEMERLUKAN REVISI STRUKTURAL**

Direvisi dengan menambahkan:
1. `AnalysisController` (`<<controller>>`)
2. `AdminController` (`<<controller>>`)
3. `AnalysisRepository` (`<<repository>>`)
4. `DoctorProfileService` (`<<module>>`)
5. `AnalysisClient` (`<<module>>`)
6. Perbaikan multiplicity pada 2 relasi yang terbalik

Opsional (untuk kelengkapan pipeline AI): `ModelService`, `ModelConfig`, `PipelineResult`, `SegmentationResult`, `GradCAMResult`.

File hasil revisi disarankan: `CLASS_DIAGRAM_PIXELT_FINAL_AUDITED.drawio` dan `CLASS_DIAGRAM_PIXELT_FINAL_AUDITED.png`.

---

## 11. Keterbatasan Pemeriksaan

- File PNG dibuka secara visual untuk memeriksa keterbacaan, tetapi detail mikro (ukuran font, ketebalan garis) tidak dapat diverifikasi secara terstruktur dari file gambar.
- File `.bak` (backup) tidak diperiksa secara individu; asumsi bahwa konten sama dengan file asli.
- Beberapa nomor baris dalam source code tidak dapat ditentukan dengan tepat karena pembacaan file yang terpotong.

---

## 12. Kesimpulan Akhir

Class Diagram `CLASS_DIAGRAM_PIXELT_FINAL_NEAT` **BELUM LULUS** audit independen. Struktur dasar 9 kelas sudah mencakup komponen inti, tetapi terdapat kesalahan multiplicity pada 2 relasi dan hilangnya kelas arsitektur penting (controllers, repository, frontend services). Revisi diperlukan sebelum diagram dapat digunakan sebagai Class Diagram final dalam Bab IV skripsi.
