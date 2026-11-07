# Laporan Audit Independen Menyeluruh ERD PIXEL-T Final (Audited)

**Versi dokumen:** 2.0 (audit menyeluruh — Tahap I–XVI)  
**Tanggal:** 5 November 2026  
**Objek audit utama:** `references/bab 4/ERD_PIXELT_FINAL_AUDITED.png`  
**Objek pendukung:** `ERD_PIXELT_FINAL_AUDITED.drawio`, `ERD_PIXELT_FINAL_AUDITED.svg`, serta pembanding `ERD_PIXELT_FINAL.{drawio,png,svg,puml}`  
**Sumber kebenaran:** 8 migration SQL (`database/migrations/001–008.sql`), source code backend (Flask/Python), source code frontend (React/TypeScript), dan uji backend (`tests/backend/`)  
**Metode:** re-verifikasi independen dari bukti mentah (raw evidence), bukan mengandalkan laporan audit sebelumnya  
**Sifat:** read-only terhadap aplikasi dan database; tidak ada kode, migration, database, RLS, trigger, bucket, atau file ERD asli yang diubah  
**Kerahasiaan:** dokumen ini tidak memuat API key, password, access token, service-role key, atau kredensial lain

---

## A. Ringkasan Eksekutif

Audit dilakukan ulang dari awal terhadap **ERD PIXEL-T Final versi audited** yang menjadi acuan Bab IV skripsi S1. Seluruh entitas, atribut, primary key, foreign key, constraint, relasi, kardinalitas, trigger, kebijakan RLS, objek Storage, dan tujuh alur fungsional ditelusuri kembali ke migration dan source code aktual.

**Hasil pokok:**

1. ERD memuat **3 entitas** — `User (auth.users)`, `doctor_profiles`, dan `analyses` — dan **73 atribut** (5 + 29 + 39). Jumlah ini **identik** dengan hasil rekonstruksi skema final dari migration 001–008 dan dikonfirmasi secara programatik dari berkas Draw.io.
2. Terdapat **3 foreign key fisik**, seluruhnya merujuk ke `auth.users(id)`:
   - `doctor_profiles.user_id` — NOT NULL, UNIQUE, `ON DELETE CASCADE`;
   - `analyses.user_id` — NOT NULL, tanpa UNIQUE, `ON DELETE CASCADE`;
   - `doctor_profiles.approved_by` — nullable, tanpa UNIQUE.
3. ERD audited menggambarkan **3 relasi garis** dengan **6 label kardinalitas**: `1 : 0..1` (User–doctor_profiles), `1 : *` (User–analyses), dan `0..* : 0..1` (User–doctor_profiles melalui `approved_by`).
4. Tidak ditemukan entitas, atribut, relasi, atau kardinalitas yang bertentangan dengan migration. Tidak ada atribut JSON hasil API yang keliru diangkat menjadi kolom fisik. Storage tetap dimodelkan sebagai komponen eksternal melalui kolom path/URL, bukan sebagai tabel relasional.
5. Seluruh tujuh alur utama (Sign Up, Sign In, Upload Image, Segmentation, History, Doctor Profile, Sign Out) dan alur administrasi (approval/rejection) memiliki jalur data yang konsisten dengan ERD.

**Temuan yang tersisa (tidak membatalkan struktur ERD):**

- **F-01 (telah diperbaiki pada versi audited):** ERD final sebelumnya hanya mencantumkan `approved_by` sebagai atribut, padahal FK tersebut aktif dipakai backend dan diuji. Versi audited sudah menambahkannya sebagai relasi garis.
- **F-02 (rendah):** Komentar migration 007 baris 17 menyebut `raw_user_meta_data.role`, sedangkan implementasi memakai `raw_app_meta_data.role`. Ini kesalahan dokumentasi kode, bukan kesalahan ERD.
- **F-03 (tinggi untuk dokumen pendukung):** `ERD_PIXELT_FINAL.puml` adalah artefak lama dan tidak konsisten dengan Draw.io/PNG/SVG final (jumlah atribut lebih sedikit, memakai `user_metadata`, tanpa `approved_by`). File ini harus disinkronkan atau dihapus.
- **F-04 (informasi):** Storage bucket dan sesi/token Supabase Auth sengaja tidak dimodelkan sebagai entitas relasional; keputusan ini tepat untuk ERD fisik aplikasi.
- **F-05 (rendah):** Verifikasi bersifat statis (migration + source code); tidak ada uji E2E browser dan tidak ada pembacaan skema Supabase live.

**Keputusan akhir:** **LULUS DENGAN CATATAN**. Struktur inti ERD benar dan dapat dipertanggungjawabkan secara teknis maupun akademik; catatan yang tersisa bersifat dokumentasi pendukung dan keterbatasan verifikasi, bukan kesalahan struktural.

---

## B. Inventaris File yang Diperiksa

### B.1 File ERD

| No. | File | Ukuran | Timestamp | Status |
|---|---|---|---|---|
| 1 | `references/bab 4/ERD_PIXELT_FINAL.drawio` | 27.922 B | 11/5/2026 21:18:24 | Asli — tidak diubah |
| 2 | `references/bab 4/ERD_PIXELT_FINAL.png` | 433.318 B | 11/5/2026 21:18:24 | Asli — tidak diubah |
| 3 | `references/bab 4/ERD_PIXELT_FINAL.svg` | 11.618 B | 11/5/2026 21:18:24 | Asli — tidak diubah |
| 4 | `references/bab 4/ERD_PIXELT_FINAL.puml` | 2.051 B | 11/1/2026 15:10:27 | Artefak lama — tidak konsisten (F-03) |
| 5 | `references/bab 4/ERD_PIXELT_FINAL_AUDITED.drawio` | 29.439 B | 11/5/2026 21:47:56 | Revisi — objek audit |
| 6 | `references/bab 4/ERD_PIXELT_FINAL_AUDITED.png` | 439.233 B | 11/5/2026 21:47:58 | Revisi — objek audit utama |
| 7 | `references/bab 4/ERD_PIXELT_FINAL_AUDITED.svg` | 12.143 B | 11/5/2026 21:47:58 | Revisi — objek audit |
| 8 | `references/bab 4/_build_erd_final_audited.js` | 15.203 B | 11/5/2026 21:47:51 | Generator satu sumber revisi |
| 9 | `references/bab 4/_audit_verify_audited.js` | 1.490 B | 11/5/2026 21:48:13 | Verifikator struktur Draw.io |
| 10 | `references/bab 4/_audit_verify_files.js` | — | — | Verifikator silang Draw.io/SVG/PNG (dibuat untuk audit ini) |

### B.2 Migration dan database

| No. | File | Fungsi |
|---|---|---|
| 1 | `database/migrations/001_create_analyses_and_storage.sql` | Tabel `analyses`, index, RLS, bucket `analysis-assets`, policy Storage |
| 2 | `database/migrations/002_add_ai_pipeline_metadata.sql` | Kolom `model_checkpoint_sha256`, `tta_scales`, `tta_orientations`, `gradcam_status` |
| 3 | `database/migrations/003_add_analysis_progress.sql` | Kolom `current_step`, `progress_percent` + CHECK |
| 4 | `database/migrations/004_create_doctor_profiles.sql` | Tabel `doctor_profiles`, UNIQUE `user_id`, RLS |
| 5 | `database/migrations/005_create_profile_avatars_bucket.sql` | Bucket `profile-avatars` + policy |
| 6 | `database/migrations/006_add_avatar_url_to_doctor_profiles.sql` | Kolom `avatar_url` |
| 7 | `database/migrations/007_add_role_and_account_status.sql` | Kolom `role`, `account_status`, `approved_by`, `approved_at`, `rejection_reason`; policy service-role |
| 8 | `database/migrations/008_create_doctor_profile_trigger.sql` | Function dan trigger `handle_new_doctor_signup`, backfill |

### B.3 Source code backend

| No. | File | Bagian yang diperiksa |
|---|---|---|
| 1 | `backend/app/routes/analysis.py` | Endpoint `/analysis`, `/history` |
| 2 | `backend/app/routes/admin.py` | Endpoint `/admin/doctors*` |
| 3 | `backend/app/controllers/analysis_controller.py` | Handler upload, detail, history, delete |
| 4 | `backend/app/controllers/admin_controller.py` | Handler list, detail, approve, reject, stats |
| 5 | `backend/app/services/analysis_service.py` | Validasi citra, upload Storage, insert record, enqueue pipeline, update hasil |
| 6 | `backend/app/services/admin_service.py` | List, detail, approve, reject, statistik |
| 7 | `backend/app/services/storage_service.py` | Path aset, upload, signed URL, delete |
| 8 | `backend/app/repositories/analysis_repository.py` | CRUD `analyses` dengan filter `user_id` |
| 9 | `backend/app/core/auth.py` | `require_auth`, `require_admin`, `require_approved_doctor`, lookup role/status |
| 10 | `backend/app/core/supabase.py` | Klien anon dan service-role |

### B.4 Source code frontend

| No. | File | Bagian yang diperiksa |
|---|---|---|
| 1 | `frontend/src/services/auth.ts` | `registerUser`, `loginUser`, `logoutUser`, `fetchUserProfileStatus`, `getAdminRoleFromAppMetadata` |
| 2 | `frontend/src/services/profile.ts` | `fetchDoctorProfile`, `saveDoctorProfile`, `uploadAvatar`, `deleteAvatar` |
| 3 | `frontend/src/services/analysis.ts` | `createAnalysis`, `getAnalysis`, `listHistory`, `deleteAnalysis` |
| 4 | `frontend/src/context/AuthContext.tsx` | Restorasi sesi, role/status, sign in/up/out |
| 5 | `frontend/src/pages/admin/AdminDashboard.tsx` | Daftar dokter, statistik, approve, reject |
| 6 | `frontend/src/pages/auth/Register.tsx` | Formulir pendaftaran |
| 7 | `frontend/src/pages/profile/DoctorProfile.tsx` | Profil dokter, avatar, statistik |
| 8 | `frontend/src/pages/dashboard/Dashboard.tsx` | Ringkasan dan riwayat terbaru |

### B.5 Pengujian

| No. | File | Bagian yang diperiksa |
|---|---|---|
| 1 | `tests/backend/test_admin_service.py` | L304–324: constraint `doctor_profiles_approved_by_fkey` |
| 2 | `tests/backend/test_admin_service.py` | L290–301: konflik update nol baris |
| 3 | `tests/backend/test_admin_service.py` | L332–…: reject menulis status dan alasan |

---

## C. Ringkasan Arsitektur Web PIXEL-T

PIXEL-T adalah aplikasi web analisis citra endoskopi/kolonoskopi dengan tiga lapisan utama:

1. **Frontend React + TypeScript + Vite + Tailwind CSS.**
   - Routing di `frontend/src/routes/AppRoutes.tsx`: `/login`, `/register`, `/reset-password`, `/dashboard`, `/analysis/new`, `/analysis/:id`, `/history`, `/history/:id`, `/profile`, `/admin`, dan halaman 404.
   - AuthContext mengelola sesi Supabase, role, dan `accountStatus`.
   - Service layer memanggil Supabase untuk data profil dan backend Flask untuk analisis.

2. **Backend Flask (Python).**
   - Route analysis: `POST /api/analysis`, `GET /api/analysis/<id>`, `GET /api/history`, `DELETE /api/history/<id>`.
   - Route admin: `GET /api/admin/doctors`, `GET /api/admin/doctors/stats`, `GET /api/admin/doctors/<id>`, `POST /api/admin/doctors/<id>/approve`, `POST /api/admin/doctors/<id>/reject`.
   - Autentikasi Bearer token diverifikasi ke Supabase Auth (`require_auth`, `require_admin`, `require_approved_doctor`).
   - Operasi administratif dan operasi pipeline memakai klien **service-role** untuk melewati RLS secara terkendali di server.

3. **Supabase (PostgreSQL + Auth + Storage).**
   - `auth.users` menyimpan akun; `public.doctor_profiles` menyimpan profil dan status akun; `public.analyses` menyimpan metadata dan hasil analisis.
   - Bucket `analysis-assets` (privat) menyimpan citra asli, mask, overlay, dan Grad-CAM.
   - Bucket `profile-avatars` (publik) menyimpan avatar profil.
   - Trigger `on_auth_user_created_doctor_profile` membuat baris `doctor_profiles` untuk pendaftaran dokter.

**Jalur komunikasi aktual:**

- Frontend → Supabase Auth: sign up, sign in, sign out, session.
- Frontend → Supabase PostgREST: baca/tulis `doctor_profiles` (profil sendiri), baca status role.
- Frontend → Backend Flask: upload analisis, polling status, history, delete, admin approval.
- Backend → Supabase PostgREST: `analyses`, `doctor_profiles`.
- Backend → Supabase Storage: unggah/hapus aset analisis, signed URL.
- Backend → Supabase Auth Admin API: verifikasi token, lookup email pengguna, role admin dari `app_metadata`.
- AI pipeline (U-Net + ResNet50 + Grad-CAM) berjalan di proses backend, bukan di frontend.

---

## D. Rekonstruksi Skema Database Final

Rekonstruksi dilakukan dengan membaca seluruh migration sesuai urutan penerapan (001 → 008), termasuk penambahan kolom dan constraint pada migration lanjutan.

### D.1 Tabel `public.analyses` — 39 atribut

| # | Kolom | Tipe | Nullable | Default / Constraint | Bukti |
|---|---|---|---|---|---|
| 1 | `id` | uuid | NO | PK, `gen_random_uuid()` | 001 L16 |
| 2 | `user_id` | uuid | NO | FK → `auth.users(id)` ON DELETE CASCADE | 001 L17 |
| 3 | `status` | varchar(20) | NO | default `'processing'`; CHECK `processing/completed/failed` | 001 L20–21 |
| 4 | `original_image_path` | text | NO | — | 001 L24 |
| 5 | `original_filename` | text | YES | — | 001 L25 |
| 6 | `original_mime_type` | varchar(50) | YES | — | 001 L26 |
| 7 | `original_width` | integer | YES | — | 001 L27 |
| 8 | `original_height` | integer | YES | — | 001 L28 |
| 9 | `binary_mask_path` | text | YES | — | 001 L31 |
| 10 | `segmentation_overlay_path` | text | YES | — | 001 L32 |
| 11 | `segmentation_status` | varchar(20) | YES | CHECK `detected/not_detected` | 001 L33–34 |
| 12 | `area_pixels` | integer | YES | — | 001 L35 |
| 13 | `area_ratio` | numeric(7,4) | YES | — | 001 L36 |
| 14 | `bounding_width_pixels` | integer | YES | — | 001 L37 |
| 15 | `bounding_height_pixels` | integer | YES | — | 001 L38 |
| 16 | `gradcam_heatmap_path` | text | YES | — | 001 L41 |
| 17 | `gradcam_overlay_path` | text | YES | — | 001 L42 |
| 18 | `gradcam_target_layer` | varchar(100) | YES | — | 001 L43 |
| 19 | `gradcam_method` | varchar(50) | YES | — | 001 L44 |
| 20 | `gradcam_config_version` | varchar(50) | YES | — | 001 L45 |
| 21 | `gradcam_status` | varchar(20) | YES | CHECK `completed/failed` atau NULL | 002 L6–9 |
| 22 | `model_architecture` | varchar(100) | YES | — | 001 L48 |
| 23 | `model_version` | varchar(50) | YES | — | 001 L49 |
| 24 | `model_config_version` | varchar(50) | YES | — | 001 L50 |
| 25 | `model_input_size` | integer | YES | — | 001 L51 |
| 26 | `model_threshold` | numeric(4,3) | YES | — | 001 L52 |
| 27 | `model_checkpoint_sha256` | varchar(64) | YES | — | 002 L3 |
| 28 | `tta_enabled` | boolean | YES | — | 001 L53 |
| 29 | `tta_scales` | jsonb | YES | — | 002 L4 |
| 30 | `tta_orientations` | jsonb | YES | — | 002 L5 |
| 31 | `postprocessing_enabled` | boolean | YES | — | 001 L54 |
| 32 | `summary_text` | text | YES | — | 001 L57 |
| 33 | `error_code` | varchar(50) | YES | — | 001 L58 |
| 34 | `error_message` | text | YES | — | 001 L59 |
| 35 | `current_step` | varchar(64) | YES | — | 003 L6 |
| 36 | `progress_percent` | smallint | YES | CHECK 0–100 atau NULL | 003 L7–11 |
| 37 | `created_at` | timestamptz | NO | `timezone('utc', now())` | 001 L62 |
| 38 | `completed_at` | timestamptz | YES | — | 001 L63 |
| 39 | `updated_at` | timestamptz | NO | `timezone('utc', now())` | 001 L64 |

Index: `idx_analyses_user_id`, `idx_analyses_status`, `idx_analyses_created_at`, `idx_analyses_user_created` (001 L68–71). RLS aktif (001 L74) dengan 4 policy tabel (L77–103) dan 3 policy Storage (L123–153).

### D.2 Tabel `public.doctor_profiles` — 29 atribut

| # | Kolom | Tipe | Nullable | Default / Constraint | Bukti |
|---|---|---|---|---|---|
| 1 | `id` | uuid | NO | PK, `gen_random_uuid()` | 004 L11 |
| 2 | `user_id` | uuid | NO | FK → `auth.users(id)` ON DELETE CASCADE; UNIQUE | 004 L12, L46 |
| 3 | `full_name` | text | NO | — | 004 L15 |
| 4 | `phone` | text | YES | — | 004 L16 |
| 5 | `birth_date` | date | YES | — | 004 L17 |
| 6 | `city` | text | YES | — | 004 L18 |
| 7 | `profession_category` | text | YES | — | 004 L21 |
| 8 | `academic_title` | text | YES | — | 004 L22 |
| 9 | `primary_specialty` | text | YES | — | 004 L23 |
| 10 | `subspecialty` | text | YES | — | 004 L24 |
| 11 | `clinical_focus` | text | YES | — | 004 L25 |
| 12 | `hospital` | text | YES | — | 004 L26 |
| 13 | `department` | text | YES | — | 004 L27 |
| 14 | `clinical_role` | text | YES | — | 004 L28 |
| 15 | `years_experience` | text | YES | — | 004 L29 |
| 16 | `practice_address` | text | YES | — | 004 L30 |
| 17 | `str_number` | text | YES | — | 004 L31 |
| 18 | `is_verified` | boolean | NO | default `false` | 004 L32 |
| 19 | `bio` | text | YES | — | 004 L35 |
| 20 | `education` | jsonb | NO | default `'[]'::jsonb` | 004 L38 |
| 21 | `experience` | jsonb | NO | default `'[]'::jsonb` | 004 L39 |
| 22 | `avatar_url` | text | YES | — | 006 L14–15 |
| 23 | `role` | text | NO | default `'doctor'` | 007 L25 |
| 24 | `account_status` | text | NO | default `'pending'` | 007 L29 |
| 25 | `approved_by` | uuid | YES | FK → `auth.users(id)` | 007 L33 |
| 26 | `approved_at` | timestamptz | YES | — | 007 L34 |
| 27 | `rejection_reason` | text | YES | — | 007 L35 |
| 28 | `created_at` | timestamptz | NO | `timezone('utc', now())` | 004 L42 |
| 29 | `updated_at` | timestamptz | NO | `timezone('utc', now())` | 004 L43 |

Index: `idx_doctor_profiles_user_id` (004 L50), `idx_doctor_profiles_account_status` (007 L47–48). RLS aktif (004 L53), 4 policy pengguna (004 L56–82), 2 policy service-role (007 L81–105).

### D.3 Tabel eksternal `auth.users` — 5 atribut yang relevan

| # | Kolom | Tipe | Keterangan |
|---|---|---|---|
| 1 | `id` | uuid (PK) | Identitas pengguna Supabase Auth |
| 2 | `email` | varchar | Alamat email akun |
| 3 | `raw_user_meta_data` | jsonb | Metadata pendaftaran (dibaca trigger 008) |
| 4 | `raw_app_meta_data` | jsonb | Metadata tepercaya, memuat `role = 'admin'` |
| 5 | `created_at` | timestamptz | Waktu pembuatan akun |

`auth.users` bukan tabel aplikasi PIXEL-T; kolom internal Auth lainnya tidak ditampilkan karena tidak relevan bagi model data aplikasi.

### D.4 Objek non-relasional

- Bucket `analysis-assets` (privat, batas 10 MB, MIME `image/jpeg` dan `image/png`) — 001 L107–118.
- Bucket `profile-avatars` (publik, path `{user_id}/profile.{ext}`) — 005 L16–18.
- Sesi dan token Supabase Auth — bukan tabel relasional.

---

## E. Audit Setiap Entitas

### E.1 `User (auth.users)`

| Aspek | Hasil | Bukti |
|---|---|---|
| Apakah tabel Auth yang digunakan? | Ya; seluruh autentikasi memakai `supabase.auth` | `frontend/src/services/auth.ts` L146–163, L208–211; `backend/app/core/auth.py` L211–214 |
| Atribut relevan | `id`, `email`, `raw_user_meta_data`, `raw_app_meta_data`, `created_at` | Digunakan trigger 008 L37–56; role admin dari `app_metadata` (`auth.ts` L328–334; `auth.py` L144–145) |
| Pemisahan kolom fisik vs metadata | ERD menampilkan `raw_user_meta_data` dan `raw_app_meta_data` sebagai **kolom jsonb**, bukan tabel terpisah | Migration 008 L37–38; `auth.ts` L150–161 |
| Peran `id` | PK dan target ketiga FK aplikasi | 001 L17; 004 L12; 007 L33 |
| Penyimpanan role admin | `raw_app_meta_data.role = 'admin'` (server-write-only), bukan `user_metadata` | 007 L53–70; 008 L38; `auth.py` L142–145; `auth.ts` L318–334 |
| Profil dokter | Disimpan di `doctor_profiles`, bukan di metadata Auth; metadata Auth hanya menyimpan data pendaftaran awal | 008 L44–60; `profile.ts` L313–345 |

**Kesimpulan:** entitas dan atribut `User (auth.users)` sesuai implementasi. Tidak ada metadata JSON yang diperlakukan sebagai kolom tetap di luar `jsonb`.

### E.2 `doctor_profiles`

| Aspek | Hasil | Bukti |
|---|---|---|
| `user_id` FK ke `auth.users(id)`? | Ya | 004 L12 |
| `user_id` UNIQUE? | Ya, `doctor_profiles_user_id_key` | 004 L46 |
| Setiap profil wajib punya pengguna? | Ya, `user_id` NOT NULL | 004 L12 |
| Satu pengguna boleh lebih dari satu profil? | Tidak; UNIQUE mencegahnya | 004 L46 |
| Profil dibuat otomatis? | Ya, trigger `handle_new_doctor_signup` | 008 L28–79 |
| Admin dikecualikan? | Ya, `raw_app_meta_data->>'role' <> 'admin'` | 008 L37–38 |
| Role disimpan di tabel ini? | Ya, kolom `role` default `doctor` | 007 L25 |
| `account_status`? | Ya, `pending`/`approved`/`rejected` (nilai dikendalikan backend) | 007 L29; `admin_service.py` L191, L287 |
| `approved_by`? | Ya, nullable FK ke `auth.users(id)` | 007 L33 |
| Relasi lain yang belum tampil? | Tidak ada FK lain selain `user_id` dan `approved_by` | 004, 007 |

**Kesimpulan:** seluruh 29 atribut dan constraint sesuai. Tidak ada kolom role terpisah di `auth.users` yang perlu dimodelkan; role admin berada di `app_metadata` (JSON), role dokter di `doctor_profiles.role`.

### E.3 `analyses`

| Aspek | Hasil | Bukti |
|---|---|---|
| Identitas | `id` uuid PK | 001 L16 |
| Kepemilikan | `user_id` NOT NULL FK ke `auth.users(id)` | 001 L17 |
| Referensi citra input | `original_image_path` (wajib) + metadata file | 001 L24–28 |
| Lokasi objek Storage | kolom path (original, mask, overlay, Grad-CAM) | 001 L24, L31–32, L41–42 |
| Status analisis | `status` CHECK tiga nilai + `gradcam_status` | 001 L20–21; 002 L6–9 |
| Waktu | `created_at`, `completed_at`, `updated_at` | 001 L62–64 |
| Parameter pengukuran | `area_pixels`, `area_ratio`, `bounding_*` | 001 L35–38 |
| Metrik segmentasi | `segmentation_status` | 001 L33–34 |
| Referensi hasil segmentasi | `binary_mask_path`, `segmentation_overlay_path` | 001 L31–32 |
| Referensi Grad-CAM | `gradcam_heatmap_path`, `gradcam_overlay_path`, konfigurasi | 001 L41–45 |
| Error | `error_code`, `error_message` | 001 L58–59 |
| Progress | `current_step`, `progress_percent` | 003 L6–7 |
| Metadata model | arsitektur, versi, config, input size, threshold, SHA-256, TTA | 001 L48–54; 002 L3–5 |

**Kesimpulan:** 39 atribut sesuai; tidak ada kolom yang hanya milik objek JSON respons API yang dipaksakan menjadi kolom fisik. Hasil segmentasi/Grad-CAM disimpan sebagai **path file** di Storage, bukan blob di database.

---

## F. Audit Setiap Atribut

### F.1 Kesesuaian jumlah

| Entitas | Jumlah atribut ERD | Jumlah skema final | Selisih |
|---|---|---|---|
| `User (auth.users)` | 5 | 5 (atribut relevan yang dipilih) | 0 |
| `doctor_profiles` | 29 | 29 | 0 |
| `analyses` | 39 | 39 | 0 |
| **Total** | **73** | **73** | **0** |

Verifikasi programatik `_audit_verify_audited.js` mengonfirmasi **73 attribute cells**, dan `_audit_verify_files.js` mengonfirmasi seluruh 73 label atribut hadir di SVG (0 missing).

### F.2 Pemeriksaan tipe data

Seluruh tipe pada ERD cocok dengan migration:

- `uuid`, `text`, `varchar(n)`, `integer`, `smallint`, `numeric(p,s)`, `boolean`, `date`, `timestamptz`, `jsonb`;
- tidak ada tipe yang dibulatkan atau disederhanakan secara menyesatkan;
- kolom `jsonb` (`raw_user_meta_data`, `raw_app_meta_data`, `education`, `experience`, `tta_scales`, `tta_orientations`) tetap ditampilkan sebagai `jsonb`, bukan diuraikan menjadi kolom fiktif.

### F.3 Pemeriksaan penanda PK/FK/UNIQUE

| Penanda | Jumlah | Lokasi |
|---|---|---|
| `(PK)` | 3 | `auth.users.id`, `doctor_profiles.id`, `analyses.id` |
| `(FK)` | 2 | `doctor_profiles.user_id`, `analyses.user_id` |
| `(FK, UNIQUE)` | 1 | `doctor_profiles.user_id` |
| `(FK)` untuk `approved_by` | 1 | `doctor_profiles.approved_by` |

**Catatan notasi:** ERD memakai notasi sederhana `nama : tipe (PK/FK)` mengikuti `ERD_contoh.png`; nullability dan default dijelaskan pada tabel laporan, bukan pada gambar. Ini keputusan tingkat abstraksi yang konsisten, bukan ketidaksesuaian.

### F.4 Atribut yang sengaja tidak dimasukkan

- Kolom internal `auth.users` (mis. `encrypted_password`, `last_sign_in_at`, token) — tidak relevan untuk model data aplikasi dan bersifat sensitif.
- Kolom metadata Storage internal (`storage.objects`, `storage.buckets`) — bukan tabel relasional aplikasi; hubungan dijelaskan melalui kolom path/URL.
- Properti turunan frontend (mis. `thumbnail_url`, `email` pada `DoctorItem`) — dihitung/di-resolve dari data lain, bukan kolom `doctor_profiles`; `admin_service.py` L50–53 secara eksplisit mencatat bahwa `email` bukan kolom tabel.

---

## G. Audit Seluruh Foreign Key dan Kardinalitas

### G.1 Matriks relasi

| No. | Tabel Asal | Kolom FK | Tabel Tujuan | Kolom Referensi | Constraint | Nullability | Unique | Kardinalitas Aktual | Kesesuaian ERD |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `doctor_profiles` | `user_id` | `auth.users` | `id` | `doctor_profiles_user_id_fkey` (implisit), `ON DELETE CASCADE`; UNIQUE `doctor_profiles_user_id_key` | NOT NULL | Ya | 1 pengguna : 0..1 profil; 1 profil : 1 pengguna | Sesuai (label `1` dan `0..1`) |
| 2 | `analyses` | `user_id` | `auth.users` | `id` | `analyses_user_id_fkey` (implisit), `ON DELETE CASCADE` | NOT NULL | Tidak | 1 pengguna : 0..* analisis; 1 analisis : 1 pengguna | Sesuai (label `1` dan `*`) |
| 3 | `doctor_profiles` | `approved_by` | `auth.users` | `id` | `doctor_profiles_approved_by_fkey` (dikonfirmasi uji L314) | NULL | Tidak | 1 admin : 0..* profil; 1 profil : 0..1 admin penyetuju | Sesuai (label `0..*` dan `0..1`) |

### G.2 Pembacaan kardinalitas

- **`user_id` NOT NULL + UNIQUE** pada `doctor_profiles` menghasilkan relasi **one-to-zero-or-one**. NOT NULL saja tidak cukup untuk menyimpulkan `0..1`; dasar utamanya adalah UNIQUE (004 L46).
- **`user_id` NOT NULL tanpa UNIQUE** pada `analyses` menghasilkan **one-to-zero-or-many**. Tidak ada bukti yang mewajibkan setiap pengguna memiliki minimal satu analisis, sehingga sisi pengguna ditulis `0..*` (bukan `1..*`).
- **`approved_by` nullable tanpa UNIQUE** menghasilkan **zero-or-many-to-zero-or-one**: satu admin dapat menyetujui banyak profil; satu profil memiliki nol atau satu penyetuju. Tidak ada constraint yang membatasi approver hanya pada role admin; pembatasan admin dilakukan di lapisan otorisasi backend (`require_admin`, `auth.py` L87–145), bukan di FK.

### G.3 Foreign key lain

Tidak ditemukan foreign key lain pada migration 001–008. Tidak ada relasi many-to-many dan tidak ada junction table. Tidak ada FK yang digambarkan dengan arah terbalik.

---

## H. Audit Trigger dan Function

### H.1 `public.handle_new_doctor_signup()`

| Aspek | Hasil | Bukti |
|---|---|---|
| Nama function | `public.handle_new_doctor_signup()` | 008 L28 |
| Bahasa / keamanan | PL/pgSQL, `SECURITY DEFINER`, `search_path = public` | 008 L30–33 |
| Trigger | `on_auth_user_created_doctor_profile` | 008 L76 |
| Tabel pemicu | `auth.users` | 008 L77 |
| Event / timing | `AFTER INSERT`, `FOR EACH ROW` | 008 L77–78 |
| Kondisi dokter | `raw_user_meta_data ? 'full_name'` | 008 L37 |
| Pengecualian admin | `COALESCE(raw_app_meta_data->>'role','') <> 'admin'` | 008 L38 |
| Idempoten | Cek `NOT EXISTS` berdasarkan `user_id` sebelum insert | 008 L41–43 |
| Data yang ditulis | `user_id`, `full_name`, `hospital`, `primary_specialty`, `role='doctor'`, `account_status='pending'`, `is_verified=false` | 008 L44–60 |
| Penanganan kegagalan | `EXCEPTION WHEN OTHERS` → `RAISE WARNING`, tidak membatalkan sign up | 008 L63–69 |
| Transaksi | Berjalan dalam transaksi INSERT `auth.users` yang sama | Sifat trigger AFTER INSERT |

### H.2 Backfill

Migration 008 L84–106 melakukan backfill untuk `auth.users` yang memiliki `full_name` dan belum memiliki profil, dengan pengecualian admin. Proses ini idempoten karena memakai `NOT EXISTS` dan tidak mengubah profil yang sudah ada.

### H.3 Trigger lain

Tidak ditemukan trigger lain pada migration 001–008 (tidak ada trigger `updated_at` otomatis; `updated_at` diisi eksplisit oleh backend, mis. `admin_service.py` L195 dan `profile.ts` L339).

### H.4 Ketidaksesuaian dokumentasi (F-02)

Komentar 007 L17 menyatakan admin disimpan di `raw_user_meta_data.role`, sedangkan kode aktual memakai `raw_app_meta_data` (007 L53–70; 008 L38; `auth.py` L144–145; `auth.ts` L328–334). Ini adalah **komentar yang salah**, bukan perilaku sistem yang salah. Tidak memengaruhi ERD.

---

## I. Audit RLS dan Otorisasi

### I.1 Tabel `analyses`

| Policy | Operasi | Role | USING / WITH CHECK | Bukti |
|---|---|---|---|---|
| `Users can view own analyses` | SELECT | authenticated | `auth.uid() = user_id` | 001 L77–81 |
| `Users can insert own analyses` | INSERT | authenticated | `auth.uid() = user_id` | 001 L84–88 |
| `Users can update own analyses` | UPDATE | authenticated | `auth.uid() = user_id` (USING dan WITH CHECK) | 001 L91–96 |
| `Users can delete own analyses` | DELETE | authenticated | `auth.uid() = user_id` | 001 L99–103 |

RLS diaktifkan pada 001 L74. Backend pipeline dan operasi tertentu memakai service-role (`analysis_service.py` L408, L439), sehingga melewati RLS secara terkendali; route tetap dilindungi `require_approved_doctor` (`routes/analysis.py` L12, L30, L46, L57).

### I.2 Tabel `doctor_profiles`

| Policy | Operasi | Role | Kondisi | Bukti |
|---|---|---|---|---|
| `Users can view own doctor profile` | SELECT | authenticated | `auth.uid() = user_id` | 004 L56–60 |
| `Users can insert own doctor profile` | INSERT | authenticated | `auth.uid() = user_id` | 004 L63–67 |
| `Users can update own doctor profile` | UPDATE | authenticated | `auth.uid() = user_id` | 004 L70–75 |
| `Users can delete own doctor profile` | DELETE | authenticated | `auth.uid() = user_id` | 004 L78–82 |
| `Service role can read all doctor profiles` | SELECT | service_role | `true` | 007 L81–86 |
| `Service role can update doctor profiles` | UPDATE | service_role | `true` | 007 L98–104 |

### I.3 Otorisasi backend

- `require_auth` (`core/auth.py` L11–85) memverifikasi Bearer token via `client.auth.get_user(token)` (L211–214).
- `require_admin` (L87–174) membaca `app_metadata.role` (L142–145) dan menolak non-admin.
- `require_approved_doctor` (L176–275) membaca role/status dari `doctor_profiles` melalui `_get_user_role_and_status` (L278–303), lalu mewajibkan `account_status = 'approved'` (L236–259).
- Admin tidak memiliki baris `doctor_profiles`, sehingga `role is None` ditolak untuk akses klinis (L229–234) — konsisten dengan keputusan trigger 008 yang melewati admin.

**Kesimpulan RLS:** policy benar-benar membatasi data berdasarkan `auth.uid()` dan bukan hanya berdasarkan nama policy. Keterbatasan: policy tidak diuji secara runtime pada database live; verifikasi dilakukan terhadap definisi SQL.

---

## J. Audit Supabase Storage

### J.1 Bucket `analysis-assets`

| Aspek | Hasil | Bukti |
|---|---|---|
| Nama | `analysis-assets` | 001 L107–109 |
| Visibilitas | Privat (`public = false`) | 001 L111, L116 |
| Batas ukuran | 10 MB | 001 L112 |
| MIME diizinkan | `image/jpeg`, `image/png` | 001 L113 |
| Struktur path | `analysis/{user_id}/{analysis_id}/{category}/{filename}` | `storage_service.py` L10–12; dokumen 001 L121 |
| Kategori | `original`, `segmentation`, `gradcam` | `storage_service.py` L14 |
| Pola akses | Insert/select/delete oleh pemilik folder `analysis/{user_id}/...` | 001 L123–153 |
| Signed URL | Digunakan untuk membaca aset privat | `storage_service.py` (metode signed URL) |
| Penghapusan | Backend menghapus objek saat delete analisis | `analysis_service.py`/`storage_service.py` |

### J.2 Bucket `profile-avatars`

| Aspek | Hasil | Bukti |
|---|---|---|
| Nama | `profile-avatars` | 005 L16–18 |
| Visibilitas | Publik (`public = true`) | 005 L17 |
| Path | `{user_id}/profile.{ext}` | 005 L6–8; `profile.ts` L228–229 |
| MIME avatar | JPEG, PNG, WebP | `profile.ts` L205–206 |
| Batas ukuran | 5 MB (validasi frontend) | `profile.ts` L205, L222–224 |
| URL | `getPublicUrl` | `profile.ts` L248–249 |
| Policy | Select/insert/update/delete berbasis folder pemilik | 005 L21–95 |

### J.3 Hubungan Storage dengan ERD

- Nama bucket **bukan** entitas relasional dan **tidak** digambarkan sebagai tabel. Hubungannya diwakili oleh kolom:
  - `analyses.original_image_path`, `binary_mask_path`, `segmentation_overlay_path`, `gradcam_heatmap_path`, `gradcam_overlay_path`;
  - `doctor_profiles.avatar_url`.
- Tidak ada foreign key dari tabel ke `storage.objects`; ini hubungan **konseptual**, bukan relasional. ERD sudah tepat tidak menggambar garis FK ke Storage.
- Risiko orphaned object: bila insert database gagal setelah upload, backend melakukan kompensasi hapus objek (`analysis_service.py` L444–461); bila penghapusan Storage gagal, record dapat terhapus lebih dulu. Ini risiko operasional, bukan kesalahan ERD.

---

## K. Audit Kode Frontend dan Backend

### K.1 Frontend

| No. | Fitur | File | Fungsi | Operasi DB | Tabel/Kolom | Kesesuaian ERD |
|---|---|---|---|---|---|---|
| 1 | Sign Up | `frontend/src/services/auth.ts` | `registerUser` (L131–188) | `supabase.auth.signUp` dengan metadata `full_name`, `hospital`, `hospital_name`, `primary_specialty`, `specialty`, `doctor_profile` (L146–163) | `auth.users` (metadata) | Sesuai |
| 2 | Sign In | `auth.ts` | `loginUser` (L195–225) | `signInWithPassword` (L208–211) | `auth.users` (session) | Sesuai |
| 3 | Status/role | `auth.ts` | `fetchUserProfileStatus` (L297–316) | `from('doctor_profiles').select('role, account_status').eq('user_id', user.id).maybeSingle()` (L303–307) | `doctor_profiles.role`, `account_status`, `user_id` | Sesuai |
| 4 | Role admin | `auth.ts` | `getAdminRoleFromAppMetadata` (L328–334) | Baca `app_metadata.role` dari objek user (L330–333) | `auth.users.raw_app_meta_data` | Sesuai |
| 5 | Profil dokter | `frontend/src/services/profile.ts` | `fetchDoctorProfile` (L149–153) | `from('doctor_profiles').select('*').eq('user_id', user.id).maybeSingle()` | `doctor_profiles` | Sesuai |
| 6 | Simpan profil | `profile.ts` | `saveDoctorProfile` (L271–389) | `from('doctor_profiles').upsert(payload, { onConflict: 'user_id' })` (L343–345) | `doctor_profiles` (28 kolom payload) | Sesuai |
| 7 | Avatar | `profile.ts` | `uploadAvatar` (L212–254), `deleteAvatar` (L256–269) | `storage.from('profile-avatars').upload/remove` | Storage `profile-avatars`; `doctor_profiles.avatar_url` | Sesuai |
| 8 | Upload analisis | `frontend/src/services/analysis.ts` | `createAnalysis` (L185–192) | `POST /api/analysis` multipart | `analyses`, Storage | Sesuai |
| 9 | Detail analisis | `analysis.ts` | `getAnalysis` (L194–196) | `GET /api/analysis/{id}` | `analyses` | Sesuai |
| 10 | Riwayat | `analysis.ts` | `listHistory` (L212–216) | `GET /api/history` | `analyses` | Sesuai |
| 11 | Hapus | `analysis.ts` | `deleteAnalysis` (L218–224) | `DELETE /api/history/{id}` | `analyses`, Storage | Sesuai |
| 12 | Auth context | `frontend/src/context/AuthContext.tsx` | Restorasi sesi (L68), status/role (L49–50, L147) | Session + lookup `doctor_profiles` | `auth.users`, `doctor_profiles` | Sesuai |
| 13 | Admin | `frontend/src/pages/admin/AdminDashboard.tsx` | `fetchAdminDoctors` (L46), `fetchAdminStats` (L55), `approveDoctor` (L71), `rejectDoctor` (L80) | API admin | `doctor_profiles` | Sesuai |

**Catatan penting:** `saveDoctorProfile` secara eksplisit **tidak** mengirim `role` dan `account_status` (komentar L313–316), sehingga pengguna tidak dapat menaikkan hak aksesnya sendiri. Ini konsisten dengan ERD yang menempatkan kedua kolom tersebut sebagai data tata kelola yang dikelola backend.

### K.2 Backend

| No. | Fitur | File | Fungsi | Operasi DB | Tabel/Kolom | Kesesuaian ERD |
|---|---|---|---|---|---|---|
| 1 | Upload | `backend/app/routes/analysis.py` | `create_analysis` (L11–26) | `POST /api/analysis` | `analyses` | Sesuai |
| 2 | Validasi/upload | `backend/app/services/analysis_service.py` | `create_analysis` (L369–500) | Validasi (L386–388), upload Storage (L403–409), insert record (L427–441), enqueue (L465–492) | `analyses.*`; Storage | Sesuai |
| 3 | Insert | `backend/app/repositories/analysis_repository.py` | `create` (L38–69) | `table('analyses').insert(record)` (L65) | `analyses` | Sesuai |
| 4 | Detail | `analysis_repository.py` | `get_by_id` (L71–98) | `select('*').eq('id').eq('user_id')` (L88–94) | `analyses` | Sesuai |
| 5 | Riwayat | `analysis_repository.py` | `list_by_user` (L100–131) | `select('*').eq('user_id').order('created_at', desc).range(...)` (L122–129) | `analyses` | Sesuai |
| 6 | Update hasil | `analysis_repository.py` | `update` (L133–170) | `update(updates).eq('id').eq('user_id')` (L160–166) | `analyses` | Sesuai |
| 7 | Hapus | `analysis_repository.py` | `delete` (L172–196) | `delete().eq('id').eq('user_id')` (L188–194) | `analyses` | Sesuai |
| 8 | Admin list | `backend/app/services/admin_service.py` | `list_doctors` (L42–101) | `select('id, user_id, full_name, hospital, primary_specialty, account_status, created_at, approved_at, rejection_reason')` (L54–56) | `doctor_profiles`; email dari `auth.users` (L80–96) | Sesuai |
| 9 | Admin detail | `admin_service.py` | `get_doctor` (L103–133) | `select('*').eq('id')` (L106–112) | `doctor_profiles` | Sesuai |
| 10 | Approve | `admin_service.py` | `approve_doctor` (L135–233) | `update({account_status:'approved', approved_by, approved_at, ...}).eq('id').eq('account_status','pending')` (L188–200) | `doctor_profiles.account_status`, `approved_by`, `approved_at`, `rejection_reason`, `updated_at` | Sesuai |
| 11 | Reject | `admin_service.py` | `reject_doctor` (L235–326) | `update({account_status:'rejected', approved_by, approved_at:None, rejection_reason, ...})` (L284–296) | `doctor_profiles` | Sesuai |
| 12 | Statistik | `admin_service.py` | `get_statistics` (L328–362) | `select('account_status')` lalu hitung (L333–361) | `doctor_profiles.account_status` | Sesuai |
| 13 | Guard | `backend/app/core/auth.py` | `require_admin` (L87–174), `require_approved_doctor` (L176–275) | Verifikasi token + `select('role, account_status').eq('user_id')` (L289–295) | `auth.users`, `doctor_profiles` | Sesuai |

**Kesimpulan:** seluruh nama tabel dan kolom yang dipakai kode **persis** sama dengan nama pada ERD. Tidak ditemukan kolom yang dipanggil kode tetapi tidak ada di skema, atau sebaliknya.

---

## L. Audit Tujuh Alur Utama

| # | Alur | Urutan proses aktual | Operasi database | Bukti | Kesesuaian ERD |
|---|---|---|---|---|---|
| 1 | **Sign Up** | Form → `registerUser` → `supabase.auth.signUp` dengan metadata → trigger `handle_new_doctor_signup` → insert `doctor_profiles` (`role='doctor'`, `account_status='pending'`) → sesi/konfirmasi email | INSERT `auth.users`; INSERT `doctor_profiles` | `Register.tsx`; `auth.ts` L131–188; 008 L28–79 | Sesuai; entitas dan trigger tercermin |
| 2 | **Sign In** | Form → `signInWithPassword` → session → AuthContext membaca `doctor_profiles.role`/`account_status` → routing berdasarkan role/status | SELECT `auth.users` (Auth); SELECT `doctor_profiles` | `auth.ts` L195–225, L297–316; `AuthContext.tsx` L49–50, L147; `auth.py` L224–226 | Sesuai |
| 3 | **Upload Image** | Pilih file → validasi klien → `POST /api/analysis` → `require_approved_doctor` → validasi server → generate path → upload ke `analysis-assets` → insert `analyses` (`status='processing'`) → enqueue → respons 202 | INSERT Storage; INSERT `analyses` | `analysis_service.py` L369–500; `analysis_repository.py` L38–69; `routes/analysis.py` L11–26 | Sesuai |
| 4 | **Segmentation** | Worker mengambil job → pipeline U-Net + ResNet50 → hasil segmentasi + Grad-CAM → update `analyses` (status, path, metrik, progres, `completed_at`) | UPDATE `analyses`; INSERT objek Storage | `analysis_service.py` (pipeline/update); `analysis_repository.py` L133–170 | Sesuai; hasil disimpan sebagai path + metrik, bukan tabel terpisah |
| 5 | **History** | `GET /api/history` → `list_by_user` filter `user_id`, urut `created_at` desc → tampilkan; detail; `DELETE /api/history/{id}` → hapus record + aset Storage | SELECT/UPDATE/DELETE `analyses`; DELETE Storage | `analysis_repository.py` L100–131, L172–196; `analysis.ts` L212–224 | Sesuai |
| 6 | **Doctor Profile** | `fetchDoctorProfile` → fallback metadata → form → validasi → `upsert` `doctor_profiles` `onConflict: 'user_id'` → sinkron metadata Auth | SELECT/UPSERT `doctor_profiles`; Storage avatar | `profile.ts` L149–153, L271–389 | Sesuai; `UNIQUE(user_id)` mendukung `onConflict` |
| 7 | **Sign Out** | Tombol keluar → `supabase.auth.signOut()` → AuthContext membersihkan sesi → ProtectedRoute mengalihkan | Tidak ada operasi tabel aplikasi | `auth.ts` L269–279; `AuthContext.tsx` | Tidak memengaruhi ERD |

**Catatan status:** respons `202 Accepted` pada Upload adalah **penerimaan tugas**, bukan penyelesaian. Status terminal (`completed`/`failed`) baru diketahui melalui polling `GET /api/analysis/{id}`. ERD tidak menggambarkan state machine, sehingga tidak ada konflik; status hanya kolom `analyses.status`.

---

## M. Audit Alur Administrasi

| Langkah | Komponen | Operasi database | Bukti |
|---|---|---|---|
| Daftar dokter | `AdminDashboard.fetchAdminDoctors` → `GET /api/admin/doctors` → `AdminService.list_doctors` | SELECT `doctor_profiles` + lookup email `auth.users` | `AdminDashboard.tsx` L46–54; `admin_service.py` L42–101 |
| Statistik | `fetchAdminStats` → `GET /api/admin/doctors/stats` | SELECT `doctor_profiles.account_status`, agregasi di aplikasi | L55–62; `admin_service.py` L328–362 |
| Detail | `fetchAdminDoctorDetail` → `GET /api/admin/doctors/{id}` | SELECT `doctor_profiles` WHERE `id` | L63–70; `admin_service.py` L103–133 |
| Approve | `approveDoctor` → `POST /api/admin/doctors/{id}/approve` | UPDATE `account_status`, `approved_by`, `approved_at`, `rejection_reason`, `updated_at` | L71–79; `admin_service.py` L135–233 |
| Reject | `rejectDoctor` → `POST /api/admin/doctors/{id}/reject` | UPDATE `account_status`, `approved_by`, `approved_at=NULL`, `rejection_reason`, `updated_at` | L80–95; `admin_service.py` L235–326 |

**Bukti FK `approved_by`:** `admin_service.py` L192 (approve) dan L288 (reject) menulis `approved_by`; uji `tests/backend/test_admin_service.py` L304–324 secara eksplisit menangani pelanggaran constraint `doctor_profiles_approved_by_fkey` (kode PostgreSQL `23503`). Karena itu, relasi `approved_by` pada ERD audited **wajib dipertahankan**.

**Catatan otorisasi:** nilai `approved_by` berasal dari `g.current_user['id']` (`admin_controller.py` L55, L76) yang telah diverifikasi `require_admin` dari `app_metadata.role`. Tidak ada bukti bahwa approver dibatasi oleh constraint database; pembatasan berada di lapisan aplikasi.

---

## N. Audit Visual ERD

### N.1 Entitas dan penamaan

- Tiga entitas: `User (auth.users)`, `doctor_profiles`, `analyses`.
- Nama tabel aplikasi sama persis dengan nama tabel PostgreSQL (`public.doctor_profiles`, `public.analyses`).
- `User (auth.users)` diberi konteks eksplisit sebagai tabel eksternal Supabase Auth — tepat, karena bukan tabel buatan PIXEL-T.

### N.2 Atribut

- 73 atribut, tanpa duplikasi.
- PK ditandai `(PK)` pada ketiga entitas.
- FK ditandai `(FK)`; `user_id` pada `doctor_profiles` ditandai `(FK, UNIQUE)`.
- Urutan atribut mengikuti kelompok logis (identitas → data pribadi → profesional → tata kelola → timestamp).
- Keterbacaan: font 11 px pada kanvas 1280×900, dirender 2× menjadi 2560×1800; tajam untuk cetak.

### N.3 Relasi dan kardinalitas

| Relasi | Label di sisi kiri/atas | Label di sisi kanan/bawah | Status visual |
|---|---|---|---|
| `rel_user_doctor` | `1` (User) | `0..1` (doctor_profiles) | Garis ortogonal vertikal, tanpa panah |
| `rel_user_analyses` | `1` (User) | `*` (analyses) | Garis ortogonal horizontal, tanpa panah |
| `rel_doctor_approved_by` | `0..*` (User) | `0..1` (doctor_profiles) | Polyline kiri, label nama `approved_by` italic berputar, tanpa overlap |

### N.4 Kualitas gambar

- Tidak ada tumpang tindih teks atau garis.
- Label `approved_by` ditempatkan di margin kiri (x≈26–116) dengan rotasi −90°, sehingga tidak menutupi atribut.
- Warna konsisten: header abu-abu, isi putih, garis hitam.
- Gambar terbaca pada ukuran halaman skripsi; versi SVG tersedia untuk kebutuhan vektor.

---

## O. Perbandingan PNG, Draw.io, dan SVG

| Elemen | Draw.io | SVG | PNG | Status |
|---|---|---|---|---|
| Jumlah entitas | 3 | 3 header teks | 3 terlihat | Konsisten |
| Jumlah atribut | 73 | 73 label (0 missing) | 73 terlihat | Konsisten |
| Jumlah relasi | 3 edge | 2 line + 1 polyline | 3 garis | Konsisten |
| Label kardinalitas | 6 | 6 (`1`, `0..1`, `1`, `*`, `0..*`, `0..1`) | 6 terlihat | Konsisten |
| Nama relasi | 1 (`approved_by`) | 1 | 1 | Konsisten |
| Vertex cells | 83 | 83 text node | — | Konsisten |
| Ukuran kanvas | 1280×900 | 1280×900 | 2560×1800 (2×) | Konsisten |

**Verifikasi programatik yang dijalankan:**

- `_audit_verify_audited.js` → 3 entitas, 3 edge, 6 label kardinalitas, 1 nama relasi, 73 atribut, 83 vertex, XML `mxCell` seimbang (`balanced: true`).
- `_audit_verify_files.js` → PNG signature valid, dimensi 2560×1800; 73 label Draw.io semuanya ada di SVG; SVG berisi 83 text, 2 line, 1 polyline, 7 rect.

**Kesimpulan:** tidak ada file yang merupakan versi lama di antara ketiga format audited. Draw.io dapat dibuka dan diedit (XML valid, `mxfile`/`mxGraphModel` standar).

---

## P. Daftar Ketidaksesuaian

| ID | Severity | Temuan | Bukti | Dampak | Rekomendasi | Status |
|---|---|---|---|---|---|---|
| F-01 | Tinggi (telah diperbaiki) | ERD final sebelum revisi hanya menampilkan `approved_by` sebagai atribut, bukan relasi, padahal FK aktif dipakai dan diuji | 007 L33; `admin_service.py` L192, L288; `test_admin_service.py` L314 | Proses approval admin tidak terbaca sebagai relasi data | Diperbaiki pada `ERD_PIXELT_FINAL_AUDITED` (edge `rel_doctor_approved_by`) | **Selesai** |
| F-02 | Rendah | Komentar 007 L17 menyebut `raw_user_meta_data.role`, aktual `raw_app_meta_data` | 007 L17 vs L53–70; 008 L38; `auth.py` L144–145 | Membingungkan pembaca kode | Perbaiki komentar menjadi `raw_app_meta_data` | Terbuka (dokumentasi) |
| F-03 | Tinggi (dokumen pendukung) | `ERD_PIXELT_FINAL.puml` tidak konsisten: 16 field `doctor_profiles`, 21 field `analyses`, `user_metadata`, tanpa `approved_by` | `ERD_PIXELT_FINAL.puml` vs Draw.io 73 atribut | Pembaca dapat memakai versi usang | Sinkronkan atau hapus file `.puml` | Terbuka (dokumen) |
| F-04 | Informasi | Storage bucket dan sesi Auth tidak dimodelkan sebagai entitas | 001 L107–118; 005 L16–18 | Tidak ada — keputusan desain tepat | Pertahankan; jelaskan di narasi akademik | Diterima |
| F-05 | Rendah | Tidak ada uji E2E browser untuk alur penuh; verifikasi statis | `tests/` berisi unit test backend/frontend | Klaim runtime terbatas | Catat sebagai keterbatasan | Diterima |
| F-06 | Rendah | Skema Supabase live tidak dibaca (tanpa kredensial) | Kebijakan audit read-only | Tidak dapat memastikan drift produksi | Catat sebagai keterbatasan; bandingkan saat akses tersedia | Diterima |

**Tidak ditemukan** temuan CRITICAL: tidak ada entitas hilang, tidak ada FK salah, tidak ada kardinalitas yang bertentangan dengan constraint, dan tidak ada atribut penting yang salah tipe.

---

## Q. Rekomendasi Koreksi

1. **Gunakan `ERD_PIXELT_FINAL_AUDITED.png`** (2560×1800) sebagai gambar ERD pada Bab IV; sertakan `.svg` untuk kebutuhan vektor dan `.drawio` untuk penyuntingan.
2. **Perbaiki komentar migration 007 L17** agar menyebut `raw_app_meta_data.role` (bukan `raw_user_meta_data.role`). Ini perbaikan dokumentasi; tidak mengubah skema.
3. **Sinkronkan atau hapus `ERD_PIXELT_FINAL.puml`.** Jika dipertahankan, samakan jumlah atribut (73), nama metadata (`raw_user_meta_data`/`raw_app_meta_data`), dan tambahkan `approved_by`.
4. **Pertahankan tiga entitas dan 73 atribut.** Jangan menambahkan controller/service/repository/endpoint/pipeline AI sebagai entitas ERD.
5. **Pertahankan `approved_by` sebagai relasi garis.** FK ini nyata, aktif, dan diuji; menghapusnya akan menurunkan keakuratan ERD.
6. **Jelaskan di narasi skripsi** bahwa `auth.users` adalah tabel eksternal Supabase Auth dan bucket Storage bukan tabel relasional; hubungan file diwakili kolom path/URL.
7. **Catat keterbatasan verifikasi** (statis, tanpa database live, tanpa E2E) secara jujur di Bab IV atau lampiran.

---

## R. Keterbatasan Pemeriksaan

1. **Verifikasi statis.** Audit membandingkan migration dan source code; tidak membaca katalog `information_schema` pada database Supabase live. Drift antara migration dan database produksi tidak dapat dikesampingkan tanpa akses terkontrol.
2. **Tanpa kredensial.** Sesuai batasan read-only, tidak ada service-role key atau koneksi database yang digunakan; ini mencegah perubahan dan kebocoran data, tetapi membatasi uji runtime.
3. **Tanpa E2E browser.** Tidak ada pengujian end-to-end (registrasi → approval → upload → segmentasi → riwayat → logout) pada lingkungan browser; bukti alur berasal dari kode dan unit test.
4. **Uji RLS tidak dijalankan.** Policy dibaca dari definisi SQL; perilaku aktual bergantung pada konfigurasi Supabase dan peran JWT.
5. **Perilaku Storage tidak diuji langsung.** Signed URL, masa berlaku, dan kegagalan parsial dijelaskan dari kode, bukan dari observasi runtime.
6. **Cakupan kode.** Pencarian difokuskan pada file yang menyentuh database/Auth/Storage; komponen presentasional murni tidak diaudit baris per baris.

---

## S. Kesimpulan Akhir

| Pemeriksaan | Hasil |
|---|---|
| Entitas sesuai skema final | 3/3 sesuai |
| Atribut sesuai skema final | 73/73 sesuai |
| Primary key | 3/3 sesuai |
| Foreign key | 3/3 sesuai (termasuk `approved_by`) |
| UNIQUE dan NOT NULL | Sesuai (004 L12, L46; 001 L17; 007 L33) |
| Kardinalitas | Sesuai constraint (`1:0..1`, `1:*`, `0..*:0..1`) |
| Trigger dan function | `handle_new_doctor_signup` terverifikasi (008) |
| RLS dan otorisasi | Policy terverifikasi dari definisi SQL; otorisasi backend sesuai |
| Supabase Auth | Terverifikasi (role admin dari `app_metadata`) |
| Supabase Storage | Terverifikasi sebagai komponen eksternal + kolom path/URL |
| Kode frontend/backend | Nama tabel/kolom konsisten dengan ERD |
| Tujuh alur utama | Seluruhnya konsisten |
| Alur administrasi | Konsisten |
| Visual PNG | Bersih, terbaca, tanpa overlap |
| Konsistensi Draw.io/SVG/PNG | Konsisten (3 entitas, 73 atribut, 3 relasi, 6 label) |
| File asli tidak berubah | Terverifikasi (ukuran dan timestamp tetap) |

**KEPUTUSAN AKHIR: LULUS DENGAN CATATAN**

**Alasan:** seluruh elemen struktural ERD — entitas, atribut, PK, FK, constraint, relasi, dan kardinalitas — terverifikasi sesuai migration 001–008 dan penggunaan aktual pada frontend/backend. Temuan F-01 sudah diselesaikan pada versi audited. Catatan yang tersisa (F-02 komentar migration, F-03 file `.puml` usang, F-05/F-06 keterbatasan verifikasi) bersifat dokumentasi dan metodologis; tidak ada yang membatalkan kelayakan ERD sebagai model data Bab IV skripsi S1.

---

## T. Daftar File Audit

**Dokumen audit yang dihasilkan:**

1. `references/bab 4/AUDIT_INDEPENDEN_MENYELURUH_ERD_PIXELT_FINAL_AUDITED.md` (dokumen ini)
2. `references/bab 4/MATRIKS_BUKTI_AUDIT_MENYELURUH_ERD_PIXELT_FINAL_AUDITED.md`
3. `references/bab 4/PEMETAAN_PENGGUNAAN_DATABASE_PIXELT.md`
4. `references/bab 4/PENJELASAN_AKADEMIK_ERD_PIXELT_FINAL_REAUDITED.md`

**Artefak yang diperiksa (tidak diubah):**

- `ERD_PIXELT_FINAL_AUDITED.drawio/.png/.svg`
- `ERD_PIXELT_FINAL.drawio/.png/.svg/.puml`
- `_build_erd_final_audited.js`, `_audit_verify_audited.js`, `_audit_verify_files.js`
- `database/migrations/001–008.sql`
- Source code backend dan frontend sebagaimana dirinci pada Bagian B.

---

*Dokumen ini dihasilkan oleh proses audit independen PIXEL-T. Tidak memuat kredensial, token, atau data rahasia. File ERD asli dan revisi audited tidak diubah oleh audit ini.*
