# Matriks Bukti Validasi ERD PIXEL-T

**Versi:** 2.0 (Desain Sederhana mengikuti ERD_contoh.png)
**Tanggal:** 5 November 2026
**Sumber kebenaran utama:** File migration SQL (`database/migrations/001–008.sql`) + Source Code
**Direktori:** `references/bab 4/`

---

## A. Matriks Tabel

| No. | Tabel/Entitas | Schema | Jenis | Bukti Migration/Schema | Status | Tindakan |
|-----|---------------|--------|-------|------------------------|--------|----------|
| 1 | `auth.users` | `auth` | Entitas eksternal (Supabase Auth) | Layanan bawaan Supabase; direferensikan FK dari tabel publik | DIVERIFIKASI | Ditampilkan di ERD sebagai entitas eksternal (kolom relevan saja) |
| 2 | `doctor_profiles` | `public` | Tabel aplikasi | `004_create_doctor_profiles.sql` L11–47; `006_add_avatar_url_to_doctor_profiles.sql`; `007_add_role_and_account_status.sql` | DIVERIFIKASI | 29 atribut dimasukkan ke ERD |
| 3 | `analyses` | `public` | Tabel aplikasi | `001_create_analyses_and_storage.sql` L14–64; `002_add_ai_pipeline_metadata.sql`; `003_add_analysis_progress.sql` | DIVERIFIKASI | 39 atribut dimasukkan ke ERD |
| 4 | `analysis-assets` | `storage` | Bucket (eksternal) | `001_create_analyses_and_storage.sql` L107–118 | Diverifikasi, diecualkan | Tidak menjadi entitas relasi (file object, bukan tabel PostgreSQL) |
| 5 | `profile-avatars` | `storage` | Bucket (eksternal) | `005_create_profile_avatars_bucket.sql` | Diverifikasi, diecualkan | Tidak menjadi entitas relasi |

---

## B. Matriks Atribut (berdasarkan migration)

### `auth.users` (eksternal, kolom relevan)
| Atribut | Tipe | Nullable | Default | Bukti |
|---------|------|----------|---------|-------|
| id | uuid | NO | gen_random_uuid | auth.users (Supabase) |
| email | varchar | YES | — | auth.users (Supabase) |
| raw_user_meta_data | jsonb | YES | — | auth.users (Supabase) |
| raw_app_meta_data | jsonb | YES | — | auth.users (Supabase) |
| created_at | timestamptz | NO | now() | auth.users (Supabase) |

### `doctor_profiles`
| No | Atribut | Tipe | Nullable | Default | Bukti |
|----|---------|------|----------|---------|-------|
| 1 | id | uuid | NO | gen_random_uuid() | 004 L11 |
| 2 | user_id | uuid | NO | — | 004 L12 |
| 3 | full_name | text | NO | — | 004 L15 |
| 4 | phone | text | YES | — | 004 L16 |
| 5 | birth_date | date | YES | — | 004 L17 |
| 6 | city | text | YES | — | 004 L18 |
| 7 | profession_category | text | YES | — | 004 L21 |
| 8 | academic_title | text | YES | — | 004 L22 |
| 9 | primary_specialty | text | YES | — | 004 L23 |
| 10 | subspecialty | text | YES | — | 004 L24 |
| 11 | clinical_focus | text | YES | — | 004 L25 |
| 12 | hospital | text | YES | — | 004 L26 |
| 13 | department | text | YES | — | 004 L27 |
| 14 | clinical_role | text | YES | — | 004 L28 |
| 15 | years_experience | text | YES | — | 004 L29 |
| 16 | practice_address | text | YES | — | 004 L30 |
| 17 | str_number | text | YES | — | 004 L31 |
| 18 | is_verified | boolean | NO | false | 004 L32 |
| 19 | bio | text | YES | — | 004 L35 |
| 20 | education | jsonb | NO | '[]'::jsonb | 004 L38 |
| 21 | experience | jsonb | NO | '[]'::jsonb | 004 L39 |
| 22 | avatar_url | text | YES | — | 006 L14–15 |
| 23 | role | text | NO | 'doctor' | 007 L24–25 |
| 24 | account_status | text | NO | 'pending' | 007 L28–29 |
| 25 | approved_by | uuid | YES | — | 007 L33 |
| 26 | approved_at | timestamptz | YES | — | 007 L34 |
| 27 | rejection_reason | text | YES | — | 007 L35 |
| 28 | created_at | timestamptz | NO | timezone('utc', now()) | 004 L42 |
| 29 | updated_at | timestamptz | NO | timezone('utc', now()) | 004 L43 |

### `analyses`
| No | Atribut | Tipe | Nullable | Default | Bukti |
|----|---------|------|----------|---------|-------|
| 1 | id | uuid | NO | gen_random_uuid() | 001 L16 |
| 2 | user_id | uuid | NO | — | 001 L17 |
| 3 | status | varchar(20) | NO | 'processing' | 001 L20–21 |
| 4 | original_image_path | text | NO | — | 001 L24 |
| 5 | original_filename | text | YES | — | 001 L25 |
| 6 | original_mime_type | varchar(50) | YES | — | 001 L26 |
| 7 | original_width | integer | YES | — | 001 L27 |
| 8 | original_height | integer | YES | — | 001 L28 |
| 9 | binary_mask_path | text | YES | — | 001 L31 |
| 10 | segmentation_overlay_path | text | YES | — | 001 L32 |
| 11 | segmentation_status | varchar(20) | YES | — | 001 L33–34 |
| 12 | area_pixels | integer | YES | — | 001 L35 |
| 13 | area_ratio | numeric(7,4) | YES | — | 001 L36 |
| 14 | bounding_width_pixels | integer | YES | — | 001 L37 |
| 15 | bounding_height_pixels | integer | YES | — | 001 L38 |
| 16 | gradcam_heatmap_path | text | YES | — | 001 L41 |
| 17 | gradcam_overlay_path | text | YES | — | 001 L42 |
| 18 | gradcam_target_layer | varchar(100) | YES | — | 001 L43 |
| 19 | gradcam_method | varchar(50) | YES | — | 001 L44 |
| 20 | gradcam_config_version | varchar(50) | YES | — | 001 L45 |
| 21 | gradcam_status | varchar(20) | YES | — | 002 L6–9 |
| 22 | model_architecture | varchar(100) | YES | — | 001 L48 |
| 23 | model_version | varchar(50) | YES | — | 001 L49 |
| 24 | model_config_version | varchar(50) | YES | — | 001 L50 |
| 25 | model_input_size | integer | YES | — | 001 L51 |
| 26 | model_threshold | numeric(4,3) | YES | — | 001 L52 |
| 27 | model_checkpoint_sha256 | varchar(64) | YES | — | 002 L3 |
| 28 | tta_enabled | boolean | YES | — | 001 L53 |
| 29 | tta_scales | jsonb | YES | — | 002 L4 |
| 30 | tta_orientations | jsonb | YES | — | 002 L5 |
| 31 | postprocessing_enabled | boolean | YES | — | 001 L54 |
| 32 | summary_text | text | YES | — | 001 L57 |
| 33 | error_code | varchar(50) | YES | — | 001 L58 |
| 34 | error_message | text | YES | — | 001 L59 |
| 35 | current_step | varchar(64) | YES | — | 003 L6 |
| 36 | progress_percent | smallint | YES | — | 003 L7 |
| 37 | created_at | timestamptz | NO | timezone('utc', now()) | 001 L62 |
| 38 | completed_at | timestamptz | YES | — | 001 L63 |
| 39 | updated_at | timestamptz | NO | timezone('utc', now()) | 001 L64 |

---

## C. Matriks Primary Key

| Tabel | PK | Bukti | Status |
|-------|----|-------|--------|
| `doctor_profiles` | id | 004 L11 | DIVERIFIKASI |
| `analyses` | id | 001 L16 | DIVERIFIKASI |

---

## D. Matriks Foreign Key

| Tabel | FK | Referensi | On Delete | Bukti | Status |
|-------|----|-----------|-----------|-------|--------|
| `doctor_profiles` | user_id | auth.users(id) | CASCADE | 004 L12 | DIVERIFIKASI |
| `doctor_profiles` | approved_by | auth.users(id) | — | 007 L33 | DIVERIFIKASI |
| `analyses` | user_id | auth.users(id) | CASCADE | 001 L17 | DIVERIFIKASI |

---

## E. Matriks Constraint

| Tabel | Constraint | Tipe | Bukti | Status |
|-------|------------|------|-------|--------|
| `doctor_profiles` | doctor_profiles_user_id_key | UNIQUE (user_id) | 004 L46 | DIVERIFIKASI |
| `doctor_profiles` | id PRIMARY KEY | PK | 004 L11 | DIVERIFIKASI |
| `analyses` | analyses_pkey | PK | 001 L16 | DIVERIFIKASI |
| `analyses` | status check | CHECK | 001 L20–21 | DIVERIFIKASI |
| `analyses` | segmentation_status check | CHECK | 001 L33–34 | DIVERIFIKASI |
| `analyses` | gradcam_status check | CHECK | 002 L6–9 | DIVERIFIKASI |
| `analyses` | progress_percent check | CHECK | 003 L9–10 | DIVERIFIKASI |

---

## F. Matriks Trigger & Function

| Nama | Tabel Pemicu | Event | Fungsi | Dampak | Bukti |
|------|--------------|-------|--------|--------|-------|
| `on_auth_user_created_doctor_profile` | `auth.users` | AFTER INSERT | `public.handle_new_doctor_signup()` | Membuat baris `doctor_profiles` (role='doctor', account_status='pending') untuk pendaftaran dokter; dilewati untuk akun admin | 008 L28–71 |
| `handle_new_doctor_signup()` | auth.users | — | PL/pgSQL trigger function (SECURITY DEFINER) | Idempotensi (lewati jika profil sudah ada); tidak membatalkan signup saat gagal | 008 L28–71 |

---

## G. Matriks Relasi dan Kardinalitas

| No | Entitas A | Entitas B | FK | Constraint | Kardinalitas | Bukti | Status |
|----|-----------|-----------|----|------------|--------------|-------|--------|
| 1 | User (auth.users) | doctor_profiles | doctor_profiles.user_id | FK NOT NULL + UNIQUE | 1 : 0..1 | 004 L12, L46 | DIVERIFIKASI |
| 2 | User (auth.users) | analyses | analyses.user_id | FK NOT NULL | 1 : * | 001 L17 | DIVERIFIKASI |
| 3 | User (auth.users) | doctor_profiles | doctor_profiles.approved_by | FK nullable | 1 : 0..* (untuk admin) | 007 L33 | DIVERIFIKASI (dicatat sebagai atribut FK, tidak digambar garis terpisah guna kesederhanaan diagram) |

---

## H. Matriks Kesesuaian Tujuh Alur Aplikasi

| Fitur | Data yang Digunakan | Entitas/Tabel | Operasi DB | Relasi | Kesesuaian ERD | Status |
|-------|---------------------|---------------|------------|--------|----------------|--------|
| Sign Up | auth.users, doctor_profiles (full_name, hospital, primary_specialty) | Supabase Auth, doctor_profiles | INSERT auth.users; trigger INSERT doctor_profiles | user_id (1:0..1) | TERPENUHI | DIVERIFIKASI |
| Sign In | auth.users (identity/role), doctor_profiles (account_status) | Supabase Auth, doctor_profiles | SELECT | user_id | TERPENUHI | DIVERIFIKASI |
| Upload Image | analyses (user_id, status, path) + Storage file | analyses | INSERT analyses | user_id (1:*) | TERPENUHI | DIVERIFIKASI |
| Segmentation | analyses (status, artefak, metrik, progres) | analyses | UPDATE analyses | user_id (1:*) | TERPENUHI | DIVERIFIKASI |
| History | analyses WHERE user_id; file Storage | analyses | SELECT, DELETE | user_id | TERPENUHI | DIVERIFIKASI |
| Doctor Profile | doctor_profiles (upsert profil, statistik dihitung saat tampil) | doctor_profiles | SELECT/INSERT/UPSERT | user_id | TERPENUHI | DIVERIFIKASI |
| Sign Out | Sesi Supabase Auth | — | (tidak ada operasi DB aplikasi) | — | TERPENUHI — tidak menambah entitas | DIVERIFIKASI |

---

## I. Catatan Validasi

- Seluruh atribut pada ERD tercatat di atas dengan lokasi baris migration asli. Tidak ada atribut yang dirancang tanpa bukti migration.
- Admin role berada di `auth.users.raw_app_meta_data.role = 'admin'`; **bukan** di `doctor_profiles` — telah diverifikasi dari 007 dan 008.
- Supabase Storage tidak dirancang sebagai tabel relasional pada ERD.
