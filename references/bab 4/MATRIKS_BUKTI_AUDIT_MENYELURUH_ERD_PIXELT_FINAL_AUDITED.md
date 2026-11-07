# Matriks Bukti Audit Menyeluruh ERD PIXEL-T Final (Audited)

**Versi:** 2.0  
**Tanggal:** 5 November 2026  
**Objek:** `references/bab 4/ERD_PIXELT_FINAL_AUDITED.{drawio,png,svg}`  
**Sumber kebenaran:** `database/migrations/001–008.sql`, source code backend/frontend, dan uji backend  
**Sifat:** read-only; tidak ada kredensial/token dalam dokumen ini

---

## A. Ringkasan Verifikasi

| Elemen | Target | Hasil | Metode |
|---|---|---|---|
| Entitas | 3 | 3 | Parse Draw.io (`ent_*`) |
| Atribut | 73 | 73 | Regex `ent_*_a*` + pencocokan migration |
| Primary key | 3 | 3 | Inspeksi atribut `(PK)` |
| Foreign key | 3 | 3 | Inspeksi migration + atribut `(FK)` |
| Relasi garis | 3 | 3 | Parse edge `rel_*` |
| Label kardinalitas | 6 | 6 | Parse `rel_*_l*` |
| Nama relasi | 1 | 1 | `approved_by` |
| Vertex cells | 83 | 83 | Parse `vertex="1"` |
| XML well-formed | Ya | Ya | `mxCell` balanced |
| PNG | 2560×1800 | 2560×1800 | Header IHDR |
| SVG | 83 text, 2 line, 1 polyline, 7 rect | Sesuai | Parse SVG |
| Atribut hilang di SVG | 0 | 0 | Perbandingan label |

**Kesimpulan ringkas:** seluruh elemen struktural ERD audited terverifikasi; tidak ada atribut hilang atau berlebih.

---

## B. Matriks Bukti Entitas dan Atribut

### B.1 Entitas `User (auth.users)` — 5 atribut

| No. | Atribut ERD | Skema aktual | Bukti migration | Bukti kode | Status |
|---|---|---|---|---|---|
| 1 | `id : uuid (PK)` | `auth.users.id` uuid PK | Bawaan Supabase Auth | `auth.ts` L306; `auth.py` L223 | TERVERIFIKASI |
| 2 | `email : varchar` | `auth.users.email` | Bawaan Supabase Auth | `auth.py` L257; `admin_service.py` L374–376 | TERVERIFIKASI |
| 3 | `raw_user_meta_data : jsonb` | `auth.users.raw_user_meta_data` jsonb | 008 L37, L54–56 | `auth.ts` L150–161 | TERVERIFIKASI |
| 4 | `raw_app_meta_data : jsonb` | `auth.users.raw_app_meta_data` jsonb | 008 L38; 007 L53–70 | `auth.py` L144–145; `auth.ts` L330–333 | TERVERIFIKASI |
| 5 | `created_at : timestamptz` | `auth.users.created_at` | Bawaan Supabase Auth | Tidak diubah aplikasi | TERVERIFIKASI (atribut Auth) |

**Catatan:** lima kolom ini adalah subset relevan dari `auth.users`; kolom internal Auth lain sengaja tidak ditampilkan. Tidak ada metadata JSON yang dipaksa menjadi kolom tetap.

### B.2 Entitas `doctor_profiles` — 29 atribut

| No. | Atribut ERD | Tipe | Nullable | Default/Constraint | Bukti migration | Bukti kode | Status |
|---|---|---|---|---|---|---|---|
| 1 | `id` | uuid (PK) | NO | `gen_random_uuid()` | 004 L11 | `admin_service.py` L109, L167 | TERVERIFIKASI |
| 2 | `user_id` | uuid (FK, UNIQUE) | NO | FK `auth.users(id)` CASCADE; UNIQUE `doctor_profiles_user_id_key` | 004 L12, L46 | `auth.ts` L306; `profile.ts` L152, L319, L345 | TERVERIFIKASI |
| 3 | `full_name` | text | NO | — | 004 L15 | `profile.ts` L320 | TERVERIFIKASI |
| 4 | `phone` | text | YES | — | 004 L16 | `profile.ts` L321 | TERVERIFIKASI |
| 5 | `birth_date` | date | YES | — | 004 L17 | `profile.ts` L322 | TERVERIFIKASI |
| 6 | `city` | text | YES | — | 004 L18 | `profile.ts` L323 | TERVERIFIKASI |
| 7 | `profession_category` | text | YES | — | 004 L21 | `profile.ts` L324 | TERVERIFIKASI |
| 8 | `academic_title` | text | YES | — | 004 L22 | `profile.ts` L325 | TERVERIFIKASI |
| 9 | `primary_specialty` | text | YES | — | 004 L23 | `profile.ts` L326 | TERVERIFIKASI |
| 10 | `subspecialty` | text | YES | — | 004 L24 | `profile.ts` L327 | TERVERIFIKASI |
| 11 | `clinical_focus` | text | YES | — | 004 L25 | `profile.ts` L328 | TERVERIFIKASI |
| 12 | `hospital` | text | YES | — | 004 L26 | `profile.ts` L329 | TERVERIFIKASI |
| 13 | `department` | text | YES | — | 004 L27 | `profile.ts` L330 | TERVERIFIKASI |
| 14 | `clinical_role` | text | YES | — | 004 L28 | `profile.ts` L331 | TERVERIFIKASI |
| 15 | `years_experience` | text | YES | — | 004 L29 | `profile.ts` L332 | TERVERIFIKASI |
| 16 | `practice_address` | text | YES | — | 004 L30 | `profile.ts` L333 | TERVERIFIKASI |
| 17 | `str_number` | text | YES | — | 004 L31 | `profile.ts` L334 | TERVERIFIKASI |
| 18 | `is_verified` | boolean | NO | `false` | 004 L32 | `profile.ts` L335 | TERVERIFIKASI |
| 19 | `bio` | text | YES | — | 004 L35 | `profile.ts` L336 | TERVERIFIKASI |
| 20 | `education` | jsonb | NO | `'[]'::jsonb` | 004 L38 | `profile.ts` L337 | TERVERIFIKASI |
| 21 | `experience` | jsonb | NO | `'[]'::jsonb` | 004 L39 | `profile.ts` L338 | TERVERIFIKASI |
| 22 | `avatar_url` | text | YES | — | 006 L14–15 | `profile.ts` L340 | TERVERIFIKASI |
| 23 | `role` | text | NO | `'doctor'` | 007 L25 | `auth.ts` L305; `profile.ts` L140 (read-only) | TERVERIFIKASI |
| 24 | `account_status` | text | NO | `'pending'` | 007 L29 | `auth.ts` L305; `profile.ts` L141 (read-only) | TERVERIFIKASI |
| 25 | `approved_by` | uuid (FK) | YES | FK `auth.users(id)` | 007 L33 | `admin_service.py` L192, L288 | TERVERIFIKASI |
| 26 | `approved_at` | timestamptz | YES | — | 007 L34 | `admin_service.py` L193, L289 | TERVERIFIKASI |
| 27 | `rejection_reason` | text | YES | — | 007 L35 | `admin_service.py` L194, L290 | TERVERIFIKASI |
| 28 | `created_at` | timestamptz | NO | `timezone('utc', now())` | 004 L42 | `admin_service.py` L55 | TERVERIFIKASI |
| 29 | `updated_at` | timestamptz | NO | `timezone('utc', now())` | 004 L43 | `admin_service.py` L195, L291; `profile.ts` L339 | TERVERIFIKASI |

**Catatan tata kelola:** `role` dan `account_status` tidak dikirim oleh `saveDoctorProfile` (komentar eksplisit pada `profile.ts` L313–316); keduanya dikelola backend admin. Ini mendukung pemodelan ERD.

### B.3 Entitas `analyses` — 39 atribut

| No. | Atribut ERD | Tipe | Nullable | Default/Constraint | Bukti migration | Bukti kode | Status |
|---|---|---|---|---|---|---|---|
| 1 | `id` | uuid (PK) | NO | `gen_random_uuid()` | 001 L16 | `analysis_repository.py` L65 | TERVERIFIKASI |
| 2 | `user_id` | uuid (FK) | NO | FK `auth.users(id)` CASCADE | 001 L17 | `analysis_repository.py` L53, L92, L125 | TERVERIFIKASI |
| 3 | `status` | varchar(20) | NO | `'processing'`; CHECK 3 nilai | 001 L20–21 | `analysis_repository.py` L12, L56–58 | TERVERIFIKASI |
| 4 | `original_image_path` | text | NO | — | 001 L24 | `analysis_service.py` L396–398, L431 | TERVERIFIKASI |
| 5 | `original_filename` | text | YES | — | 001 L25 | `analysis_service.py` L432 | TERVERIFIKASI |
| 6 | `original_mime_type` | varchar(50) | YES | — | 001 L26 | `analysis_service.py` L433 | TERVERIFIKASI |
| 7 | `original_width` | integer | YES | — | 001 L27 | `analysis_service.py` L434 | TERVERIFIKASI |
| 8 | `original_height` | integer | YES | — | 001 L28 | `analysis_service.py` L435 | TERVERIFIKASI |
| 9 | `binary_mask_path` | text | YES | — | 001 L31 | Hasil pipeline | TERVERIFIKASI |
| 10 | `segmentation_overlay_path` | text | YES | — | 001 L32 | Hasil pipeline | TERVERIFIKASI |
| 11 | `segmentation_status` | varchar(20) | YES | CHECK `detected/not_detected` | 001 L33–34 | `analysis_repository.py` L13, L61–62, L156–157 | TERVERIFIKASI |
| 12 | `area_pixels` | integer | YES | — | 001 L35 | Hasil pipeline | TERVERIFIKASI |
| 13 | `area_ratio` | numeric(7,4) | YES | — | 001 L36 | Hasil pipeline | TERVERIFIKASI |
| 14 | `bounding_width_pixels` | integer | YES | — | 001 L37 | Hasil pipeline | TERVERIFIKASI |
| 15 | `bounding_height_pixels` | integer | YES | — | 001 L38 | Hasil pipeline | TERVERIFIKASI |
| 16 | `gradcam_heatmap_path` | text | YES | — | 001 L41 | Hasil pipeline | TERVERIFIKASI |
| 17 | `gradcam_overlay_path` | text | YES | — | 001 L42 | Hasil pipeline | TERVERIFIKASI |
| 18 | `gradcam_target_layer` | varchar(100) | YES | — | 001 L43 | Hasil pipeline | TERVERIFIKASI |
| 19 | `gradcam_method` | varchar(50) | YES | — | 001 L44 | Hasil pipeline | TERVERIFIKASI |
| 20 | `gradcam_config_version` | varchar(50) | YES | — | 001 L45 | Hasil pipeline | TERVERIFIKASI |
| 21 | `gradcam_status` | varchar(20) | YES | CHECK `completed/failed` atau NULL | 002 L6–9 | Hasil pipeline | TERVERIFIKASI |
| 22 | `model_architecture` | varchar(100) | YES | — | 001 L48 | Metadata pipeline | TERVERIFIKASI |
| 23 | `model_version` | varchar(50) | YES | — | 001 L49 | Metadata pipeline | TERVERIFIKASI |
| 24 | `model_config_version` | varchar(50) | YES | — | 001 L50 | Metadata pipeline | TERVERIFIKASI |
| 25 | `model_input_size` | integer | YES | — | 001 L51 | Metadata pipeline | TERVERIFIKASI |
| 26 | `model_threshold` | numeric(4,3) | YES | — | 001 L52 | Metadata pipeline | TERVERIFIKASI |
| 27 | `model_checkpoint_sha256` | varchar(64) | YES | — | 002 L3 | Metadata pipeline | TERVERIFIKASI |
| 28 | `tta_enabled` | boolean | YES | — | 001 L53 | Metadata pipeline | TERVERIFIKASI |
| 29 | `tta_scales` | jsonb | YES | — | 002 L4 | Metadata pipeline | TERVERIFIKASI |
| 30 | `tta_orientations` | jsonb | YES | — | 002 L5 | Metadata pipeline | TERVERIFIKASI |
| 31 | `postprocessing_enabled` | boolean | YES | — | 001 L54 | Metadata pipeline | TERVERIFIKASI |
| 32 | `summary_text` | text | YES | — | 001 L57 | Hasil pipeline | TERVERIFIKASI |
| 33 | `error_code` | varchar(50) | YES | — | 001 L58 | Penanganan error pipeline | TERVERIFIKASI |
| 34 | `error_message` | text | YES | — | 001 L59 | Penanganan error pipeline | TERVERIFIKASI |
| 35 | `current_step` | varchar(64) | YES | — | 003 L6 | Progres pipeline | TERVERIFIKASI |
| 36 | `progress_percent` | smallint | YES | CHECK 0–100 atau NULL | 003 L7–11 | Progres pipeline | TERVERIFIKASI |
| 37 | `created_at` | timestamptz | NO | `timezone('utc', now())` | 001 L62 | `analysis_repository.py` L126 | TERVERIFIKASI |
| 38 | `completed_at` | timestamptz | YES | — | 001 L63 | Hasil pipeline | TERVERIFIKASI |
| 39 | `updated_at` | timestamptz | NO | `timezone('utc', now())` | 001 L64 | `analysis_repository.py` L160–166 | TERVERIFIKASI |

---

## C. Matriks Bukti Foreign Key dan Kardinalitas

| No. | Tabel Asal | Kolom FK | Tabel Tujuan | Kolom Referensi | Constraint | Nullability | Unique | Kardinalitas Aktual | Kesesuaian ERD | Bukti |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `doctor_profiles` | `user_id` | `auth.users` | `id` | FK CASCADE; UNIQUE `doctor_profiles_user_id_key` | NOT NULL | Ya | 1 pengguna — 0..1 profil | Sesuai (`1`, `0..1`) | 004 L12, L46 |
| 2 | `analyses` | `user_id` | `auth.users` | `id` | FK CASCADE; tanpa UNIQUE | NOT NULL | Tidak | 1 pengguna — 0..* analisis | Sesuai (`1`, `*`) | 001 L17 |
| 3 | `doctor_profiles` | `approved_by` | `auth.users` | `id` | `doctor_profiles_approved_by_fkey`; tanpa UNIQUE | NULL | Tidak | 1 admin — 0..* profil; 1 profil — 0..1 admin | Sesuai (`0..*`, `0..1`) | 007 L33; `test_admin_service.py` L314 |

**Bukti tidak ada FK lain:**

- Migration 001 hanya mendefinisikan FK `analyses.user_id`.
- Migration 004 hanya mendefinisikan FK `doctor_profiles.user_id`.
- Migration 007 hanya menambahkan FK `doctor_profiles.approved_by`.
- Migration 002, 003, 005, 006, 008 tidak menambah FK.

---

## D. Matriks Bukti Trigger dan Function

| No. | Elemen | Definisi | Bukti | Dampak pada ERD | Status |
|---|---|---|---|---|---|
| 1 | Function `handle_new_doctor_signup` | `SECURITY DEFINER`, `search_path=public`, PL/pgSQL | 008 L28–33 | Menjelaskan pembuatan otomatis `doctor_profiles` | TERVERIFIKASI |
| 2 | Trigger `on_auth_user_created_doctor_profile` | AFTER INSERT pada `auth.users`, FOR EACH ROW | 008 L76–79 | Relasi User–doctor_profiles bersifat 0..1 (tidak semua user punya profil) | TERVERIFIKASI |
| 3 | Kondisi dokter | `raw_user_meta_data ? 'full_name'` | 008 L37 | Profil hanya dibuat untuk sign up dokter | TERVERIFIKASI |
| 4 | Pengecualian admin | `raw_app_meta_data->>'role' <> 'admin'` | 008 L38 | Admin tidak punya baris `doctor_profiles` | TERVERIFIKASI |
| 5 | Idempotensi | `NOT EXISTS (... WHERE dp.user_id = NEW.id)` | 008 L41–43 | Tidak ada profil ganda; UNIQUE tetap terjaga | TERVERIFIKASI |
| 6 | Data yang ditulis | `user_id`, `full_name`, `hospital`, `primary_specialty`, `role`, `account_status`, `is_verified` | 008 L44–60 | Semua kolom ada di ERD | TERVERIFIKASI |
| 7 | Penanganan gagal | `EXCEPTION WHEN OTHERS` → `RAISE WARNING` | 008 L63–69 | Sign up tidak gagal; profil bisa absen (0..1) | TERVERIFIKASI |
| 8 | Backfill | Insert untuk user lama tanpa profil | 008 L84–106 | Menjaga konsistensi data lama | TERVERIFIKASI |

**Tidak ada trigger `updated_at` otomatis:** `updated_at` diisi eksplisit oleh aplikasi (`admin_service.py` L195, L291; `profile.ts` L339).

---

## E. Matriks Bukti RLS dan Otorisasi

| No. | Tabel | Policy | Operasi | Role | Kondisi | Bukti | Status |
|---|---|---|---|---|---|---|---|
| 1 | `analyses` | Users can view own analyses | SELECT | authenticated | `auth.uid() = user_id` | 001 L77–81 | TERVERIFIKASI |
| 2 | `analyses` | Users can insert own analyses | INSERT | authenticated | `auth.uid() = user_id` | 001 L84–88 | TERVERIFIKASI |
| 3 | `analyses` | Users can update own analyses | UPDATE | authenticated | `auth.uid() = user_id` | 001 L91–96 | TERVERIFIKASI |
| 4 | `analyses` | Users can delete own analyses | DELETE | authenticated | `auth.uid() = user_id` | 001 L99–103 | TERVERIFIKASI |
| 5 | `doctor_profiles` | Users can view own doctor profile | SELECT | authenticated | `auth.uid() = user_id` | 004 L56–60 | TERVERIFIKASI |
| 6 | `doctor_profiles` | Users can insert own doctor profile | INSERT | authenticated | `auth.uid() = user_id` | 004 L63–67 | TERVERIFIKASI |
| 7 | `doctor_profiles` | Users can update own doctor profile | UPDATE | authenticated | `auth.uid() = user_id` | 004 L70–75 | TERVERIFIKASI |
| 8 | `doctor_profiles` | Users can delete own doctor profile | DELETE | authenticated | `auth.uid() = user_id` | 004 L78–82 | TERVERIFIKASI |
| 9 | `doctor_profiles` | Service role can read all | SELECT | service_role | `true` | 007 L81–86 | TERVERIFIKASI |
| 10 | `doctor_profiles` | Service role can update | UPDATE | service_role | `true` | 007 L98–104 | TERVERIFIKASI |
| 11 | `storage.objects` | Users can upload own analysis assets | INSERT | authenticated | bucket + folder `analysis/{uid}` | 001 L123–131 | TERVERIFIKASI |
| 12 | `storage.objects` | Users can read own analysis assets | SELECT | authenticated | bucket + folder `analysis/{uid}` | 001 L134–142 | TERVERIFIKASI |
| 13 | `storage.objects` | Users can delete own analysis assets | DELETE | authenticated | bucket + folder `analysis/{uid}` | 001 L145–153 | TERVERIFIKASI |
| 14 | `storage.objects` | Avatar policies (select/insert/update/delete) | CRUD | authenticated | folder `{uid}` pada `profile-avatars` | 005 L21–95 | TERVERIFIKASI |

**Otorisasi aplikasi:**

| No. | Guard | Sumber identitas | Bukti | Status |
|---|---|---|---|---|
| 1 | `require_auth` | Bearer token → `auth.get_user` | `auth.py` L11–85, L211–214 | TERVERIFIKASI |
| 2 | `require_admin` | `app_metadata.role == 'admin'` | `auth.py` L87–174, L142–145 | TERVERIFIKASI |
| 3 | `require_approved_doctor` | `doctor_profiles.role` + `account_status='approved'` | `auth.py` L176–275, L224–259, L289–295 | TERVERIFIKASI |
| 4 | Admin tanpa profil | `role is None` → 403 | `auth.py` L229–234 | TERVERIFIKASI |

---

## F. Matriks Bukti Supabase Storage

| No. | Elemen | Nilai | Bukti | Hubungan dengan ERD | Status |
|---|---|---|---|---|---|
| 1 | Bucket analisis | `analysis-assets` | 001 L107–109 | Tidak menjadi entitas; path disimpan di `analyses` | TERVERIFIKASI |
| 2 | Visibilitas | Privat (`public=false`) | 001 L111, L116 | — | TERVERIFIKASI |
| 3 | Batas ukuran | 10 MB | 001 L112 | — | TERVERIFIKASI |
| 4 | MIME | `image/jpeg`, `image/png` | 001 L113 | — | TERVERIFIKASI |
| 5 | Path analisis | `analysis/{user_id}/{analysis_id}/{category}/{filename}` | `storage_service.py` L10–12 | `user_id` cocok dengan `analyses.user_id` | TERVERIFIKASI |
| 6 | Kategori | `original`, `segmentation`, `gradcam` | `storage_service.py` L14 | Masing-masing punya kolom path di `analyses` | TERVERIFIKASI |
| 7 | Bucket avatar | `profile-avatars`, publik | 005 L16–18 | Path disimpan di `doctor_profiles.avatar_url` | TERVERIFIKASI |
| 8 | Path avatar | `{user_id}/profile.{ext}` | 005 L6–8; `profile.ts` L228–229 | `user_id` cocok dengan `doctor_profiles.user_id` | TERVERIFIKASI |
| 9 | Signed URL | Untuk aset privat | `storage_service.py` | Tidak disimpan sebagai kolom | TERVERIFIKASI |
| 10 | Kompensasi gagal insert | Hapus objek yang sudah diunggah | `analysis_service.py` L444–461 | Mencegah orphan saat insert gagal | TERVERIFIKASI |

---

## G. Matriks Bukti Kode Frontend dan Backend

| No. | Fitur | File | Fungsi | Operasi Database | Tabel | Kolom | Relasi | Kesesuaian ERD |
|---|---|---|---|---|---|---|---|---|
| 1 | Sign Up | `frontend/src/services/auth.ts` | `registerUser` L131–188 | `auth.signUp` + metadata L146–163 | `auth.users` | `email`, `raw_user_meta_data` | Trigger → `doctor_profiles` | Sesuai |
| 2 | Sign In | `auth.ts` | `loginUser` L195–225 | `signInWithPassword` L208–211 | `auth.users` | — | — | Sesuai |
| 3 | Status | `auth.ts` | `fetchUserProfileStatus` L297–316 | SELECT L303–307 | `doctor_profiles` | `role`, `account_status`, `user_id` | User–doctor_profiles | Sesuai |
| 4 | Admin role | `auth.ts` | `getAdminRoleFromAppMetadata` L328–334 | Baca JWT `app_metadata` | `auth.users` | `raw_app_meta_data` | — | Sesuai |
| 5 | Profil baca | `frontend/src/services/profile.ts` | `fetchDoctorProfile` L149–153 | SELECT `*` | `doctor_profiles` | semua | User–doctor_profiles | Sesuai |
| 6 | Profil tulis | `profile.ts` | `saveDoctorProfile` L271–389 | UPSERT `onConflict:'user_id'` L343–345 | `doctor_profiles` | 28 kolom payload L318–341 | UNIQUE `user_id` | Sesuai |
| 7 | Avatar | `profile.ts` | `uploadAvatar` L212–254; `deleteAvatar` L256–269 | Storage upload/remove | `profile-avatars` | `avatar_url` | — | Sesuai |
| 8 | Upload | `frontend/src/services/analysis.ts` | `createAnalysis` L185–192 | POST multipart | `analyses` | — | User–analyses | Sesuai |
| 9 | Detail | `analysis.ts` | `getAnalysis` L194–196 | GET | `analyses` | — | User–analyses | Sesuai |
| 10 | Riwayat | `analysis.ts` | `listHistory` L212–216 | GET | `analyses` | — | User–analyses | Sesuai |
| 11 | Hapus | `analysis.ts` | `deleteAnalysis` L218–224 | DELETE | `analyses` | — | User–analyses | Sesuai |
| 12 | Upload backend | `backend/app/services/analysis_service.py` | `create_analysis` L369–500 | INSERT L438–440 | `analyses` | `id`, `user_id`, `status`, path, metadata file L427–435 | User–analyses | Sesuai |
| 13 | Simpan aset | `analysis_service.py` | `create_analysis` L400–423 | Storage upload L403–409 | `analysis-assets` | path | — | Sesuai |
| 14 | Repository insert | `backend/app/repositories/analysis_repository.py` | `create` L38–69 | INSERT L65 | `analyses` | payload | User–analyses | Sesuai |
| 15 | Repository baca | `analysis_repository.py` | `get_by_id` L71–98 | SELECT + filter id/user | `analyses` | `*` | User–analyses | Sesuai |
| 16 | Repository list | `analysis_repository.py` | `list_by_user` L100–131 | SELECT + filter user + order | `analyses` | `*` | User–analyses | Sesuai |
| 17 | Repository update | `analysis_repository.py` | `update` L133–170 | UPDATE + filter id/user | `analyses` | payload | User–analyses | Sesuai |
| 18 | Repository delete | `analysis_repository.py` | `delete` L172–196 | DELETE + filter id/user | `analyses` | — | User–analyses | Sesuai |
| 19 | Admin list | `backend/app/services/admin_service.py` | `list_doctors` L42–101 | SELECT L54–56 | `doctor_profiles` | 9 kolom + email Auth | User–doctor_profiles | Sesuai |
| 20 | Admin detail | `admin_service.py` | `get_doctor` L103–133 | SELECT `*` L106–112 | `doctor_profiles` | semua | User–doctor_profiles | Sesuai |
| 21 | Approve | `admin_service.py` | `approve_doctor` L135–233 | UPDATE L188–200 | `doctor_profiles` | `account_status`, `approved_by`, `approved_at`, `rejection_reason`, `updated_at` | `approved_by` → User | Sesuai |
| 22 | Reject | `admin_service.py` | `reject_doctor` L235–326 | UPDATE L284–296 | `doctor_profiles` | idem | `approved_by` → User | Sesuai |
| 23 | Statistik | `admin_service.py` | `get_statistics` L328–362 | SELECT `account_status` L333 | `doctor_profiles` | `account_status` | — | Sesuai |
| 24 | Guard admin | `backend/app/core/auth.py` | `require_admin` L87–174 | Verifikasi token + `app_metadata` | `auth.users` | `raw_app_meta_data` | — | Sesuai |
| 25 | Guard dokter | `auth.py` | `require_approved_doctor` L176–275 | SELECT role/status L289–295 | `doctor_profiles` | `role`, `account_status` | User–doctor_profiles | Sesuai |

---

## H. Matriks Bukti Alur Fungsional

| Alur | Langkah | Komponen | Operasi DB | Tabel/Kolom | Relasi | Kesesuaian | Bukti |
|---|---|---|---|---|---|---|---|
| Sign Up | Form → signUp → trigger → profil | `Register.tsx`; `auth.ts` L131–188; 008 | INSERT `auth.users`; INSERT `doctor_profiles` | `auth.users.*`; `doctor_profiles.user_id`, `full_name`, `role`, `account_status` | User 1—0..1 doctor_profiles | Sesuai | 008 L44–60 |
| Sign In | Kredensial → session → role/status → route | `auth.ts` L195–225, L297–316; `AuthContext` | SELECT `doctor_profiles` | `role`, `account_status` | User 1—0..1 doctor_profiles | Sesuai | `auth.py` L224–259 |
| Upload | Validasi → Storage → insert → enqueue | `analysis_service.py` L369–500 | INSERT Storage + INSERT `analyses` | `status`, `original_*`, `user_id` | User 1—* analyses | Sesuai | L427–441 |
| Segmentation | Pipeline → update hasil | `analysis_service.py`; `analysis_repository.py` L133–170 | UPDATE `analyses` + INSERT Storage | `segmentation_*`, `gradcam_*`, `model_*`, `progress_*`, `completed_at` | User 1—* analyses | Sesuai | repository L160–166 |
| History | List → detail → delete | `analysis_repository.py` L100–131, L172–196 | SELECT/UPDATE/DELETE `analyses`; DELETE Storage | `user_id`, `created_at` | User 1—* analyses | Sesuai | L122–129, L188–194 |
| Doctor Profile | Baca → form → upsert | `profile.ts` L149–153, L271–389 | SELECT/UPSERT `doctor_profiles`; Storage avatar | 28 kolom; `avatar_url` | User 1—0..1 doctor_profiles | Sesuai | L343–345 |
| Sign Out | Logout → clear session | `auth.ts` L269–279; `AuthContext` | Tidak ada operasi tabel | — | — | Sesuai (tidak memengaruhi ERD) | L271 |
| Admin Approval | List → approve/reject | `AdminDashboard.tsx`; `admin_service.py` | SELECT/UPDATE `doctor_profiles` | `account_status`, `approved_by`, `approved_at`, `rejection_reason` | `approved_by` → User | Sesuai | L188–200, L284–296 |

---

## I. Matriks Kesesuaian ERD dengan Implementasi

| No. | Elemen ERD | Implementasi Database | Implementasi Frontend/Backend | Bukti Migration | Bukti Kode | Status | Rekomendasi |
|---|---|---|---|---|---|---|---|
| 1 | Entitas `User (auth.users)` | `auth.users` | Auth service/context | Bawaan Auth | `auth.ts` L131–188, L297–334 | TERVERIFIKASI | Pertahankan |
| 2 | Entitas `doctor_profiles` | `public.doctor_profiles` | Profil, admin | 004, 006, 007, 008 | `profile.ts`; `admin_service.py` | TERVERIFIKASI | Pertahankan |
| 3 | Entitas `analyses` | `public.analyses` | Upload, history, pipeline | 001, 002, 003 | `analysis_service.py`; `analysis_repository.py` | TERVERIFIKASI | Pertahankan |
| 4 | PK ketiga entitas | `id` uuid | — | 001 L16; 004 L11 | — | TERVERIFIKASI | Pertahankan |
| 5 | FK `doctor_profiles.user_id` | NOT NULL + UNIQUE + CASCADE | Sign in, profil, admin | 004 L12, L46 | `auth.ts` L306; `profile.ts` L345 | TERVERIFIKASI | Pertahankan |
| 6 | FK `analyses.user_id` | NOT NULL + CASCADE | Upload, history | 001 L17 | repository L53, L92, L125 | TERVERIFIKASI | Pertahankan |
| 7 | FK `approved_by` | Nullable FK | Approve/reject | 007 L33 | `admin_service.py` L192, L288 | TERVERIFIKASI | Pertahankan sebagai relasi garis |
| 8 | Kardinalitas `1:0..1` | UNIQUE `user_id` | Satu profil per user | 004 L46 | `profile.ts` L345 (`onConflict user_id`) | TERVERIFIKASI | Pertahankan |
| 9 | Kardinalitas `1:*` | Tanpa UNIQUE | Banyak analisis per user | 001 L17 | `list_by_user` | TERVERIFIKASI | Pertahankan |
| 10 | Kardinalitas `0..*:0..1` | FK nullable | Approver tunggal per profil | 007 L33 | `admin_service.py` L192 | TERVERIFIKASI | Pertahankan |
| 11 | Atribut `role` | text default `doctor` | Dibaca, tidak ditulis user | 007 L25 | `auth.ts` L305; `profile.ts` L313–316 | TERVERIFIKASI | Pertahankan |
| 12 | Atribut `account_status` | text default `pending` | Dibaca, dikelola admin | 007 L29 | `auth.ts` L305; `admin_service.py` L191, L287 | TERVERIFIKASI | Pertahankan |
| 13 | Atribut progres | `current_step`, `progress_percent` | Pipeline | 003 | `analysis_repository.py` L133–170 | TERVERIFIKASI | Pertahankan |
| 14 | Atribut Grad-CAM | path + konfigurasi | Pipeline | 001, 002 | `analysis_repository.py` | TERVERIFIKASI | Pertahankan |
| 15 | Storage `analysis-assets` | Bucket privat | Upload/delete | 001 L107–153 | `storage_service.py` | TERVERIFIKASI (bukan entitas) | Jelaskan sebagai eksternal |
| 16 | Storage `profile-avatars` | Bucket publik | Avatar | 005 | `profile.ts` L204–269 | TERVERIFIKASI (bukan entitas) | Jelaskan sebagai eksternal |
| 17 | Trigger signup | `handle_new_doctor_signup` | Sign up | 008 | `auth.ts` L146–163 | TERVERIFIKASI | Pertahankan |
| 18 | RLS `analyses` | 4 policy | Upload/history | 001 L74–103 | `require_approved_doctor` | TERVERIFIKASI | Uji runtime bila memungkinkan |
| 19 | RLS `doctor_profiles` | 4 + 2 policy | Profil/admin | 004 L53–82; 007 L81–105 | `admin_service.py` (service-role) | TERVERIFIKASI | Uji runtime bila memungkinkan |
| 20 | File `.puml` | — | — | — | — | TIDAK SESUAI (dokumen pendukung) | Sinkronkan/hapus |

---

## J. Rekapitulasi Status

| Status | Jumlah elemen | Keterangan |
|---|---|---|
| TERVERIFIKASI | 73 atribut + 3 entitas + 3 FK + 3 relasi + trigger/RLS/Storage | Seluruh elemen inti |
| SEBAGIAN TERVERIFIKASI | 0 | — |
| BELUM TERVERIFIKASI | 0 (runtime RLS/Storage ditandai terbatas) | Verifikasi statis |
| TIDAK SESUAI | 1 (file `.puml`, bukan ERD) | F-03 |
| TIDAK DIGUNAKAN | 0 | — |
| PERLU KEPUTUSAN DESAIN | 2 (penyajian Storage, subset kolom Auth) | Sudah diputuskan dan dijelaskan |

---

*Dokumen ini melengkapi `AUDIT_INDEPENDEN_MENYELURUH_ERD_PIXELT_FINAL_AUDITED.md`. Tidak memuat kredensial, token, atau data rahasia.*
