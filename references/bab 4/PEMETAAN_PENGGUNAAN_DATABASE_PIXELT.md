# Peta Penggunaan Database WEB PIXEL-T

**Versi:** 1.0  
**Tanggal:** 5 November 2026  
**Sumber:** Audit ERD `ERD_PIXELT_FINAL_AUDITED`  
**Metode:** Pemetaan fitur → komponen → endpoint → operasi database → tabel/kolom → Storage

---

## A. Ringkasan

Peta penggunaan database ini menghubungkan setiap fitur aplikasi PIXEL-T dengan operasi database yang benar-benar dilakukan pada migration 001–008, melalui kode backend Flask dan kode frontend React/TypeScript. Tujuannya adalah memastikan ERD Bab IV dapat dikaitkan dengan perilaku aplikasi secara langsung, bukan hanya dengan definisi tabel.

**Peta menyasar:**

- **Fitur autentikasi** → `auth.users` + `doctor_profiles`.
- **Fitur analisis** → `analyses` + Supabase Storage (`analysis-assets`).
- **Fitur profil dokter** → `doctor_profiles` + `profile-avatars`.
- **Fitur admin** → `doctor_profiles` + `auth.users` (kunci `approved_by`).
- **Fitur riwayat** → `analyses`.

---

## B. Peta Umum Aplikasi

```
React Frontend
 ├─ Supabase Auth (sign up/in/out, session)
 ├─ Supabase PostgREST (doctor_profiles: SELECT/UPSERT)
 └─ Flask Backend
     ├─ Supabase Auth (verifikasi token, app_metadata)
     ├─ Supabase PostgREST (analyses, doctor_profiles)
     └─ Supabase Storage (analysis-assets, profile-avatars)

AI Pipeline (backend)
 └─ UPDATE analyses + Storage (segmentation, Grad-CAM, model metadata)
```

---

## C. Peta Fitur → Frontend → Backend → Endpoint → Database → Storage

### C.1 Sign Up

| Fitur | Komponen frontend | Komponen backend | Endpoint | Operasi DB | Tabel/Kolom | Storage | Relasi | Status |
|---|---|---|---|---|---|---|---|---|
| Registrasi dokter | `frontend/src/pages/auth/Register.tsx` → `useAuth().signUp` → `frontend/src/services/auth.ts` (`registerUser`, L131–188) | — (langsung ke Supabase Auth) | — | INSERT ke `auth.users` (via Auth API) | `auth.users.email`, `raw_user_meta_data` | — | User (auth.users) 1—0..1 doctor_profiles | **TERVERIFIKASI** |

**Catatan:** penerus `doctor_profiles` dilakukan oleh trigger database (migration 008), bukan oleh operasi aplikasi biasa. Metadata pendaftaran dibawa melalui `raw_user_meta_data`.

### C.2 Sign In / Sign Out

| Fitur | Komponen frontend | Komponen backend | Endpoint | Operasi DB | Tabel/Kolom | Storage | Relasi | Status |
|---|---|---|---|---|---|---|---|---|
| Sign In | `frontend/src/services/auth.ts` (`loginUser`, L195–225) → `frontend/src/context/AuthContext.tsx` | — | — | SELECT session via Auth API; SELECT `doctor_profiles.role`, `account_status` | `auth.users` (session); `doctor_profiles.role`, `account_status`, `user_id` | — | User 1—0..1 doctor_profiles | **TERVERIFIKASI** |
| Sign Out | `frontend/src/services/auth.ts` (`logoutUser`, L269–279) → `AuthContext` | — | — | Tidak ada operasi tabel aplikasi | — | — | — | **TERVERIFIKASI** (tidak memengaruhi ERD) |

---

### C.3 Upload Image dan Segmentation

| Fitur | Komponen frontend | Komponen backend | Endpoint | Operasi DB | Tabel/Kolom | Storage | Relasi | Status |
|---|---|---|---|---|---|---|---|---|
| Upload | `frontend/src/services/analysis.ts` (`createAnalysis`, L185–192) | `backend/app/routes/analysis.py` (`POST /api/analysis`, L11–26) → `backend/app/controllers/analysis_controller.py` → `backend/app/services/analysis_service.py` (`create_analysis`, L369–500) → `backend/app/repositories/analysis_repository.py` (`create`, L38–69) | `POST /api/analysis` | INSERT `analyses` | `analyses.id`, `user_id`, `status='processing'`, `original_image_path`, `original_filename`, `original_mime_type`, `original_width`, `original_height` | INSERT `analysis-assets` path `analysis/{uid}/{aid}/original/...` | User 1—* analyses | **TERVERIFIKASI** |
| Segmenasi & Grad-CAM | `frontend/src/services/analysis.ts` (`getAnalysis` polling, L194–196) | `backend/app/services/analysis_service.py` (pipeline → update hasil) → `backend/app/repositories/analysis_repository.py` (`update`, L133–170) | `GET /api/analysis/<id>` (route L29–42) | UPDATE `analyses` | `status`, `binary_mask_path`, `segmentation_overlay_path`, `segmentation_status`, area/bounding metrics, `gradcam_*`, `gradcam_status`, `model_*`, `tta_*`, `postprocessing_enabled`, `summary_text`, error fields, `current_step`, `progress_percent`, `completed_at`, `updated_at` | INSERT `analysis-assets` (segmentation/gradcam) | User 1—* analyses | **TERVERIFIKASI** |

**Catatan:** HTTP 202 (`create_analysis` di `analysis_service.py` L497–500; `analysis.ts` L175–192) berarti tugas diterima; penyelesaian dicatat melalui polling dan update status.

### C.4 History dan Delete

| Fitur | Komponen frontend | Komponen backend | Endpoint | Operasi DB | Tabel/Kolom | Storage | Relasi | Status |
|---|---|---|---|---|---|---|---|---|
| Riwayat | `frontend/src/services/analysis.ts` (`listHistory`, L212–216) | `backend/app/routes/analysis.py` (`GET /api/history`, L45–53) → controller → service → repository | `GET /api/history` | SELECT | `analyses.user_id`, `analyses.created_at`, `status`, `original_filename`, `segmentation_status`, `completed_at` | — | User 1—* analyses | **TERVERIFIKASI** |
| Detail riwayat | `frontend/src/services/analysis.ts` (`getAnalysis`, L194–196) | `GET /api/analysis/<id>` | `GET /api/analysis/<id>` | SELECT + filter `user_id` | `analyses.*` | SELECT signed URL | User 1—* analyses | **TERVERIFIKASI** |
| Hapus | `frontend/src/services/analysis.ts` (`deleteAnalysis`, L218–224) | `DELETE /api/history/<id>` (route L56–64) → controller/service/repository | `DELETE /api/history/<id>` | DELETE record + DELETE Storage | `analyses.user_id`, `id` | DELETE `analysis-assets` | User 1—* analyses | **TERVERIFIKASI** |

---

### C.5 Doctor Profile

| Fitur | Komponen frontend | Komponen backend | Operasi DB | Tabel/Kolom | Storage | Relasi | Status |
|---|---|---|---|---|---|---|---|
| Baca profil | `frontend/src/services/profile.ts` (`fetchDoctorProfile`, L110–163) | — | SELECT | `doctor_profiles.*` | — | User 1—0..1 doctor_profiles | **TERVERIFIKASI** |
| Simpan profil | `frontend/src/services/profile.ts` (`saveDoctorProfile`, L271–389) | — | UPSERT `onConflict: 'user_id'` | 28 kolom payload (user_id, full_name, …, avatar_url, updated_at) | — | User 1—0..1 doctor_profiles | **TERVERIFIKASI** |
| Avatar baca/tulis | `profile.ts` (`uploadAvatar`, L212–254; `deleteAvatar`, L256–269) | — | Storage upload/remove; `doctor_profiles.avatar_url` | `doctor_profiles.avatar_url` | `profile-avatars` `{uid}/profile.{ext}` | User 1—0..1 doctor_profiles | **TERVERIFIKASI** |

---

### C.6 Admin: Approval dan Rejection

| Fitur | Komponen frontend | Komponen backend | Endpoint | Operasi DB | Tabel/Kolom | Kunci | Status |
|---|---|---|---|---|---|---|---|
| Daftar dokter | `frontend/src/pages/admin/AdminDashboard.tsx` (`fetchAdminDoctors`, L46) | `backend/app/routes/admin.py` (`GET /api/admin/doctors`, L9–12) → controller → `backend/app/services/admin_service.py` (`list_doctors`, L42–101) | `GET /api/admin/doctors` | SELECT | `doctor_profiles.id`, `user_id`, `full_name`, `hospital`, `primary_specialty`, `account_status`, `created_at`, `approved_at`, `rejection_reason`; email dari `auth.users` | Admin doctor_profiles | **TERVERIFIKASI** |
| Detail | `AdminDashboard` (`fetchAdminDoctorDetail`, L63) | `GET /api/admin/doctors/<id>` (route L23–27) → service `get_doctor` L103–133 | — | SELECT `*` | `doctor_profiles.*` | — | **TERVERIFIKASI** |
| Approve | `AdminDashboard` (`approveDoctor`, L71) → `POST /api/admin/doctors/<id>/approve` (route L30–33) → controller → `admin_service.approve_doctor` L135–233 | `POST /api/admin/doctors/<id>/approve` | UPDATE | `doctor_profiles.account_status='approved'`, `approved_by=admin.id`, `approved_at`, `rejection_reason=NULL`, `updated_at` | FK `approved_by` → `auth.users.id` | Admin doctor_profiles | **TERVERIFIKASI** |
| Reject | `AdminDashboard` (`rejectDoctor`, L80) → `POST /api/admin/doctors/<id>/reject` (route L34–41) → controller → `admin_service.reject_doctor` L235–326 | `POST /api/admin/doctors/<id>/reject` | UPDATE | `doctor_profiles.account_status='rejected'`, `approved_by`, `approved_at=NULL`, `rejection_reason`, `updated_at` | FK `approved_by` → `auth.users.id` | Admin doctor_profiles | **TERVERIFIKASI** |
| Statistik | `AdminDashboard` (`fetchAdminStats`, L55) | `GET /api/admin/doctors/stats` (route L13–15) → service `get_statistics` L328–362 | SELECT | `doctor_profiles.account_status` + agregasi | — | — | **TERVERIFIKASI** |

---

## D. Ringkasan Penggunaan per Tabel

### D.1 `auth.users`

| Fitur | Operasi | Kolom | Keterangan |
|---|---|---|---|
| Sign Up | INSERT | `email`, `raw_user_meta_data`, `raw_app_meta_data` | Metadata dokter: `full_name`, `hospital`, `primary_specialty` |
| Sign In | SELECT | `id`, `email` | Session dan lookup role |
| Admin approval | UPDATE via Admin API | `raw_app_meta_data` | Menetapkan `role='admin'` (server-write-only) |
| Admin lookup | SELECT | `id`, `email` | Mengisi `approved_by` |

### D.2 `doctor_profiles`

| Fitur | Operasi | Kolom | Keterangan |
|---|---|---|---|
| Sign Up (trigger) | INSERT | `user_id`, `full_name`, `hospital`, `primary_specialty`, `role`, `account_status`, `is_verified` | 008 L44–60 |
| Sign In | SELECT | `user_id`, `role`, `account_status` | `fetchUserProfileStatus` |
| Dokter | SELECT/UPSERT | seluruh kolom + `avatar_url` | Profil sendiri |
| Admin | SELECT/UPDATE | `id`, `user_id`, `full_name`, …, `account_status`, `approved_by`, `approved_at`, `rejection_reason`, `updated_at` | Approve/reject |

### D.3 `analyses`

| Fitur | Operasi | Kolom | Keterangan |
|---|---|---|---|
| Upload | INSERT | `id`, `user_id`, `status='processing'`, `original_image_path`, `original_filename`, `original_mime_type`, `original_width`, `original_height` | 001 L16–28 |
| Segmenasi | UPDATE | `status`, `binary_mask_path`, `segmentation_overlay_path`, `segmentation_status`, metrics, `gradcam_*`, `model_*`, `tta_*`, `postprocessing_enabled`, `summary_text`, `error_*`, `current_step`, `progress_percent`, `completed_at`, `updated_at` | 001–003 |
| Riwayat | SELECT | `user_id`, `created_at`, `status`, `original_filename`, `segmentation_status` | `list_by_user` |
| Hapus | DELETE | `user_id`, `id` | `delete` |

---

## E. Ringkasan Penggunaan per Tabel (operasi dan jumlah)

| Tabel | Operasi yang relevan | Fitur | Jumlah operasi (dalam satu siklus lengkap) |
|---|---|---|---|
| `auth.users` | INSERT (signup), SELECT (sign in/lookup), UPDATE (admin) | Sign Up, Sign In, Admin | 3 |
| `doctor_profiles` | INSERT (trigger), SELECT, UPSERT, UPDATE, DELETE | Sign Up, Sign In, Profile, Admin | 5 |
| `analyses` | INSERT, UPDATE, SELECT, DELETE | Upload, Segmentation, History, Delete | 4 |
| `storage.buckets` / `storage.objects` | INSERT/SELECT/DELETE objek | Upload, Segmentation, Avatar, Hapus | 5 |

---

## F. Keterbatasan Peta Penggunaan

1. Peta ini bersifat **alam konsep/arsitektural** hasil audit statis, bukan rekam transaksi runtime.
2. Tidak ada transaksi gabungan yang diuji (mis. upload Storage → insert DB → enqueue) pada lingkungan runtime.
3. Riwayat penghapusan: urutan hapus record dan hapus objek Storage ditetapkan di kode tetapi tidak diuji bersamaan pada runtime.
4. RLS dan policy Storage ditetapkan di SQL, bukan diuji langsung pada database live.

---

*Referensi ketat: migration 001–008, `backend/app/**`, `frontend/src/services/**`, `frontend/src/context/**`, `frontend/src/pages/**`, `tests/backend/test_admin_service.py`.*
