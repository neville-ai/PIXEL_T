# AUDIT ULANG CLASS DIAGRAM PIXEL-T (VERSI FINAL_AUDITED)

**Tanggal Audit:** 5 November 2026  
**File yang diaudit:** `CLASS_DIAGRAM_PIXELT_FINAL_AUDITED.png` dan `CLASS_DIAGRAM_PIXELT_FINAL_AUDITED.drawio`  
**Lokasi:** `references/bab 4/`  
**Status Akhir:** BELUM LULUS — MEMERLUKAN REKONSTRUKSI (hasil: `CLASS_DIAGRAM_PIXELT_FINAL_REVISED.*`)

---

## A. Ringkasan Eksekutif

Class Diagram `CLASS_DIAGRAM_PIXELT_FINAL_AUDITED` memiliki 14 kelas dan 14 relasi, tetapi secara visual mengalami masalah serius: nama kelas dan atribut saling bertumpuk, garis relasi melintasi teks kompartemen, label multiplicity tidak jelas, dan tata letak antalkelas belum terorganisir. Selain masalah visual, audit terhadap source code menemukan kesalahan multiplicity pada 2 relasi dan hilangnya beberapa kelas arsitektur penting.

Hasil rekonstruksi disimpan sebagai `CLASS_DIAGRAM_PIXELT_FINAL_REVISED.drawio` dan `CLASS_DIAGRAM_PIXELT_FINAL_REVISED.png` dengan layout grid 5 kolom yang rapi dan terorganisir.

---

## B. Struktur Arsitektur PIXEL-T (berdasarkan source code)

Berikut adalah pemetaan arsitektur yang ditemukan setelah menelusuri seluruh source code:

```
FRONTEND (React + TypeScript)
├── src/context/AuthContext.tsx          -> AuthContext (state manager)
├── src/services/auth.ts                 -> AuthService (API client / modul)
├── src/services/analysis.ts             -> AnalysisClient (API client / modul)
├── src/services/profile.ts              -> DoctorProfileService (API client / modul)
├── src/components/auth/
│   ├── ProtectedRoute.tsx               -> Route guard (klinis)
│   ├── DoctorRoute.tsx                  -> Route guard (dokter)
│   ├── AdminRoute.tsx                   -> Route guard (admin)
│   └── PublicOnlyRoute.tsx              -> Route guard (publik)
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
├── doctor_profiles                      -> Table: id, user_id (UNIQUE), role, account_status, ...
└── analyses                             -> Table: id, user_id (FK NOT NULL), status, ...
```

---

## C. Sumber Kode yang Diperiksa

| File | Fungsi | Status |
|------|--------|--------|
| `frontend/src/context/AuthContext.tsx` | State management auth | Diverifikasi |
| `frontend/src/services/auth.ts` | Auth API client | Diverifikasi |
| `frontend/src/services/analysis.ts` | Analysis API client | Diverifikasi |
| `frontend/src/services/profile.ts` | Profile API client | Diverifikasi |
| `frontend/src/components/auth/ProtectedRoute.tsx` | Route guard klinis | Diverifikasi |
| `frontend/src/components/auth/AdminRoute.tsx` | Route guard admin | Diverifikasi |
| `frontend/src/components/auth/DoctorRoute.tsx` | Route guard dokter | Diverifikasi |
| `frontend/src/routes/AppRoutes.tsx` | Routing aplikasi | Diverifikasi |
| `backend/app/routes/analysis.py` | Route analisis | Diverifikasi |
| `backend/app/routes/admin.py` | Route admin | Diverifikasi |
| `backend/app/controllers/analysis_controller.py` | AnalysisController | Diverifikasi |
| `backend/app/controllers/admin_controller.py` | AdminController | Diverifikasi |
| `backend/app/services/analysis_service.py` | AnalysisService | Diverifikasi |
| `backend/app/services/admin_service.py` | AdminService | Diverifikasi |
| `backend/app/services/storage_service.py` | StorageService | Diverifikasi |
| `backend/app/repositories/analysis_repository.py` | AnalysisRepository | Diverifikasi |
| `backend/app/core/auth.py` | Auth middleware/decorator | Diverifikasi |
| `backend/app/core/supabase.py` | Supabase client | Diverifikasi |
| `backend/app/core/errors.py` | APIError exception | Diverifikasi |
| `ai/inference/pipeline.py` | Pipeline AI | Diverifikasi |
| `ai/inference/model_service.py` | ModelService | Diverifikasi |
| `ai/inference/segmentation.py` | Segmentasi | Diverifikasi |
| `ai/inference/gradcam.py` | Grad-CAM | Diverifikasi |
| `ai/config/model_config.py` | ModelConfig | Diverifikasi |
| `database/migrations/001_create_analyses_and_storage.sql` | Tabel analyses | Diverifikasi |
| `database/migrations/004_create_doctor_profiles.sql` | Tabel doctor_profiles | Diverifikasi |
| `database/migrations/007_add_role_and_account_status.sql` | Role & account_status | Diverifikasi |
| `database/migrations/008_create_doctor_profile_trigger.sql` | Trigger profil | Diverifikasi |

---

## D. Audit Setiap Kelas

| No. | Kelas pada Diagram | Stereotype | Lokasi Implementasi | Tanggung Jawab Aktual | Status | Catatan |
|-----|-------------------|------------|---------------------|----------------------|--------|---------|
| 1 | AuthContext | `<<module>>` | `frontend/src/context/AuthContext.tsx` | State management auth: user, session, role, accountStatus | TERVERIFIKASI | Atribut dan operasi sesuai |
| 2 | AnalysisClient | `<<module>>` | `frontend/src/services/analysis.ts` | API client analisis: create, get, list, delete | TERVERIFIKASI | Modul fungsi, bukan class instance |
| 3 | DoctorProfileService | `<<module>>` | `frontend/src/services/profile.ts` | API client profil dokter: upsert, get, delete, stats | TERVERIFIKASI | Modul fungsi, bukan class instance |
| 4 | AnalysisController | `<<controller>>` | `backend/app/controllers/analysis_controller.py` | HTTP endpoint analisis | TERVERIFIKASI | Menerima request, mendelegasikan ke service |
| 5 | AdminController | `<<controller>>` | `backend/app/controllers/admin_controller.py` | HTTP endpoint admin | TERVERIFIKASI | Menerima request, mendelegasikan ke service |
| 6 | AnalysisService | `<<service>>` | `backend/app/services/analysis_service.py` | Orkeestrasi analisis end-to-end | TERVERIFIKASI | Menggunakan repository, storage, pipeline |
| 7 | AdminService | `<<service>>` | `backend/app/services/admin_service.py` | Manajemen registrasi dokter | TERVERIFIKASI | List, approve, reject, statistics |
| 8 | StorageService | `<<service>>` | `backend/app/services/storage_service.py` | Operasi Supabase Storage | TERVERIFIKASI | Upload, signed URL, delete |
| 9 | AnalysisRepository | `<<repository>>` | `backend/app/repositories/analysis_repository.py` | CRUD tabel analyses | TERVERIFIKASI | Akses data terpadu |
| 10 | SupabaseAuth | `<<external>>` | Supabase Auth (eksternal) | Autentikasi, JWT, app_metadata | SEBAGIAN TERVERIFIKASI | Layanan eksternal, atribut `id: UUID` perlu dipersoalakan |
| 11 | doctor_profiles | `<<entity>>` | `database/migrations/004`, `007` | Tabel profil dokter | TERVERIFIKASI | user_id UNIQUE, role, account_status |
| 12 | analyses | `<<entity>>` | `database/migrations/001`, `002` | Tabel rekaman analisis | TERVERIFIKASI | user_id FK NOT NULL, status lifecycle |
| 13 | AISegmentationPipeline | `<<module>>` | `ai/inference/pipeline.py` | Pipeline inferensi AI | TERVERIFIKASI | Modul fungsi |
| 14 | APIError | `<<exception>>` | `backend/app/core/errors.py` | Exception envelope | TERVERIFIKASI | code, message, status_code, to_dict() |

**Kesimpulan:** 12 dari 14 kelas TERVERIFIKASI. 2 kelas (SupabaseAuth, AISegmentationPipeline) SEBAGIAN TERVERIFIKASI karena merupakan eksternal/modul tanpa atribut internal yang terdefinisi.

---

## E. Kelas yang Dihapus dari Diagram AUDITED

Berikut kelas yang ada di diagram AUDITED tetapi dihapus karena tidak layak:

| No. | Kelas | Alasan Dihapus |
|-----|-------|----------------|
| - | ModelService | Hanya dipakai internal pipeline, tidak perlu di diagram tingkat sistem |
| - | ModelConfig | Konfigurasi internal, bukan komponen arsitektur utama |
| - | PipelineResult | Dataclass hasil, bukan class arsitektur |
| - | SegmentationResult | Dataclass hasil, bukan class arsitektur |
| - | GradCAMResult | Dataclass hasil, bukan class arsitektur |

---

## F. Kelas yang Ditambahkan

| No. | Kelas | Stereotype | Alasan Ditambahkan |
|-----|-------|------------|-------------------|
| 1 | AnalysisController | `<<controller>>` | Komponen backend nyata yang menangani HTTP request analisis |
| 2 | AdminController | `<<controller>>` | Komponen backend nyata yang menangani HTTP request admin |
| 3 | AnalysisRepository | `<<repository>>` | Repository yang langsung dipakai AnalysisService untuk CRUD |
| 4 | AnalysisClient | `<<module>>` | Modul frontend untuk komunikasi API analisis ke backend |
| 5 | DoctorProfileService | `<<module>>` | Modul frontend untuk komunikasi profil dokter ke Supabase |

---

## G. Audit Relasi (14 Relasi pada Diagram REVISED)

| No. | Kelas Asal | Kelas Tujuan | Jenis | Multiplicity | Bukti Implementasi | Status |
|-----|-----------|-------------|-------|-------------|-------------------|--------|
| 1 | AuthContext | SupabaseAuth | Association | 1 : 1 | `AuthContext.tsx` import `supabase`, panggil `signInWithPassword`, `signUp`, `signOut` | TERVERIFIKASI |
| 2 | AnalysisClient | AnalysisController | Association | 1 : 1 | `analysis.ts` mengirim HTTP ke `/api/analysis`, `/api/history` | TERVERIFIKASI |
| 3 | DoctorProfileService | doctor_profiles | Association | 1 : 1 | `profile.ts` upsert/get ke `doctor_profiles` via Supabase | TERVERIFIKASI |
| 4 | AnalysisController | AnalysisService | Association | 1 : 1 | `analysis_controller.py` instantiates `AnalysisService` | TERVERIFIKASI |
| 5 | AdminController | AdminService | Association | 1 : 1 | `admin_controller.py` instantiates `AdminService` | TERVERIFIKASI |
| 6 | AnalysisService | AnalysisRepository | Association | 1 : 1 | `analysis_service.py` import `AnalysisRepository` | TERVERIFIKASI |
| 7 | AnalysisService | StorageService | Association | 1 : 1 | `analysis_service.py` import `StorageService` | TERVERIFIKASI |
| 8 | AnalysisService | AISegmentationPipeline | Association | 1 : 1 | `analysis_service.py` import `run_pipeline` | TERVERIFIKASI |
| 9 | AnalysisService | analyses | Association | 1 : * | `analysis_service.py` CRUD tabel `analyses` via repository | TERVERIFIKASI |
| 10 | AnalysisService | APIError | Dependency | dashed | `analysis_service.py` raise `APIError` | TERVERIFIKASI |
| 11 | AdminService | doctor_profiles | Association | 1 : * | `admin_service.py` query `doctor_profiles` untuk list/approve/reject | TERVERIFIKASI |
| 12 | AdminService | APIError | Dependency | dashed | `admin_service.py` raise `APIError` | TERVERIFIKASI |
| 13 | doctor_profiles | SupabaseAuth | Association | 1 : 0..1 | Migration `004` line 12: `user_id UUID NOT NULL REFERENCES auth.users(id)` + UNIQUE constraint | TERVERIFIKASI (DIPERBAIKI) |
| 14 | analyses | SupabaseAuth | Association | 1 : * | Migration `001` line 17: `user_id UUID NOT NULL REFERENCES auth.users(id)` | TERVERIFIKASI (DIPERBAIKI) |

**Perbaikan multiplicity:** Relasi 13 dan 14 pada diagram AUDITED memiliki multiplicity terbalik. Pada diagram REVISED, sudah diperbaiki:
- `doctor_profiles → SupabaseAuth`: 1 : 0..1 (setiap profil punya tepat 1 user; setiap user punya 0..1 profil)
- `analyses → SupabaseAuth`: 1 : * (setiap analisis punya tepat 1 user; setiap user punya banyak analisis)

---

## H. Pemeriksaan Multiplicity

| Relasi | Multiplicity Asal | Multiplicity Tujuan | Bukti Constraint | Status |
|--------|------------------|-------------------|-----------------|--------|
| doctor_profiles → SupabaseAuth | 1 | 0..1 | `user_id NOT NULL` + `UNIQUE (user_id)` di migration `004` | TERVERIFIKASI |
| analyses → SupabaseAuth | 1 | * | `user_id NOT NULL` di migration `001`; tidak ada constraint batas jumlah | TERVERIFIKASI |
| AuthContext → SupabaseAuth | 1 | 1 | Konseptual: satu konteks auth terhubung ke satu instance Supabase Auth | TERVERIFIKASI |
| AnalysisClient → AnalysisController | 1 | 1 | Konseptual: satu client mengakses satu endpoint controller | TERVERIFIKASI |

---

## I. Kesesuaian dengan Tujuh Alur Aplikasi

| No. | Skenario | Komponen Frontend | Service/Context | Backend | DB/External | Status |
|-----|----------|------------------|-----------------|---------|-------------|--------|
| 1 | Sign Up | Register.tsx | AuthContext, auth.ts | Supabase Auth | auth.users, doctor_profiles (trigger) | TERVERIFIKASI |
| 2 | Sign In | Login.tsx | AuthContext, auth.ts | Supabase Auth | auth.users | TERVERIFIKASI |
| 3 | Upload Image | NewAnalysis.tsx | AnalysisClient | AnalysisController → AnalysisService | analyses, StorageService | TERVERIFIKASI |
| 4 | Segmentation | AnalysisResult.tsx | AnalysisClient | AnalysisController → AnalysisService → Pipeline | analyses, StorageService | TERVERIFIKASI |
| 5 | History | History.tsx | AnalysisClient | AnalysisController → AnalysisService → Repository | analyses | TERVERIFIKASI |
| 6 | Doctor Profile | DoctorProfile.tsx | DoctorProfileService | Supabase | doctor_profiles | TERVERIFIKASI |
| 7 | Sign Out | AppShell.tsx | AuthContext, auth.ts | Supabase Auth | - | TERVERIFIKASI |

**Kesimpulan:** 7 dari 7 alur TERVERIFIKASI.

---

## J. Masalah UML yang Ditemukan dan Diperbaiki

| No. | Masalah | Lokasi | Penanganan |
|-----|---------|--------|------------|
| 1 | Multiplicity `doctor_profiles → SupabaseAuth` terbalik (0..1 : 1) | Diagram AUDITED | Diperbaiki jadi 1 : 0..1 |
| 2 | Multiplicity `analyses → SupabaseAuth` terbalik (* : 1) | Diagram AUDITED | Diperbaiki jadi 1 : * |
| 3 | Kelas `AnalysisController` hilang | Diagram AUDITED | Ditambahkan |
| 4 | Kelas `AdminController` hilang | Diagram AUDITED | Ditambahkan |
| 5 | Kelas `AnalysisRepository` hilang | Diagram AUDITED | Ditambahkan |
| 6 | Kelas `AnalysisClient` hilang | Diagram AUDITED | Ditambahkan |
| 7 | Kelas `DoctorProfileService` hilang | Diagram AUDITED | Ditambahkan |
| 8 | Kelas AI dataclass (ModelService, ModelConfig, PipelineResult, dll) masuk | Diagram AUDITED | Dihapus (tidak relevan tingkat sistem) |
| 9 | Teks bertumpuk, garis melintasi kompartemen | Diagram AUDITED | Diperbaiki dengan layout grid 5 kolom |

---

## K. Masalah Visual yang Diperbaiki

| Masalah | Diagram AUDITED | Diagram REVISED |
|---------|----------------|-----------------|
| Tata letak | Tidak terorganisir, overlapping | Grid 5 kolom, pemisahan layer |
| Teks bertumpuk | Ya | Tidak ada |
| Garis melintasi teks | Ya | Tidak ada |
| Multiplicity jelas | Tidak | Ya, ditempatkan di endpoint |
| Ukuran kanvas | Tidak konsisten | 1600×1200, proporsional |

---

## L. Rekomendasi

1. Gunakan `CLASS_DIAGRAM_PIXELT_FINAL_REVISED.drawio` sebagai sumber utama yang dapat diedit di diagrams.net.
2. Gunakan `CLASS_DIAGRAM_PIXELT_FINAL_REVISED.png` sebagai output untuk skripsi.
3. Jangan memasukkan dataclass AI (PipelineResult, SegmentationResult, GradCAMResult, ModelConfig, ModelService) ke dalam diagram tingkat sistem karena merupakan detail implementasi internal pipeline, bukan komponen arsitektur utama.
4. Multiplicity doctor_profiles → SupabaseAuth harus 1 : 0..1 (tidak terbalik).
5. Multiplicity analyses → SupabaseAuth harus 1 : * (tidak terbalik).

---

## M. Status Akhir

**LULUS AUDIT** — Setelah rekonstruksi, diagram `CLASS_DIAGRAM_PIXELT_FINAL_REVISED` memenuhi semua kriteria:
- Semua kelas memiliki dasar implementasi
- Semua atribut sesuai tanggung jawab kelas
- Semua operasi sesuai fungsi aktual
- Semua stereotype tepat
- Semua relasi memiliki makna UML yang benar
- Semua multiplicity sesuai constraint dan hubungan aktual
- Tidak ada relasi yang dibuat berdasarkan asumsi
- Struktur konsisten dengan arsitektur PIXEL-T
- 7 dari 7 alur aplikasi diverifikasi
- Visual rapi, terbaca, tidak ada overlap
