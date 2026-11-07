# Laporan Audit Independen ERD PIXEL-T Final

**Versi dokumen:** 1.0  
**Tanggal:** 5 November 2026  
**Ruang lingkup:** `references/bab 4/ERD_PIXELT_FINAL.{drawio,png,svg,puml}` dan revisi `ERD_PIXELT_FINAL_AUDITED.{drawio,png,svg}`  
**Sumber kebenaran utama:** 8 migration SQL (`database/migrations/001–008.sql`) + source code backend (Flask/Python) + source code frontend (React/TypeScript) + uji backend (`tests/backend/`)  
**Metode:** Re-verifikasi independen dari bukti mentah (raw evidence) — bukan mengandalkan laporan audit sebelumnya. File asli `ERD_PIXELT_FINAL.*` tidak diubah; revisi disimpan dengan sufiks `_AUDITED`. Tidak ada kredensial/token dalam dokumen ini.

---

## A. Ringkasan Eksekutif

Audit independen dilakukan terhadap **Entity Relationship Diagram (ERD) PIXEL-T Final** sebagai acuan Bab IV skripsi S1. Hasil: seluruh entitas, atribut, primary key, foreign key, constraint, relasi, dan kardinalitas di diagram final **terverifikasi sesuai skema aktual** (migration 001–008) dan source code.

**Temuan utama:** ERD asli (`ERD_PIXELT_FINAL`) menggambarkan **3 entitas dan 2 relasi garis**; foreign key sekunder `doctor_profiles.approved_by -> auth.users(id)` (migration 007 L33) dimodelkan hanya sebagai atribut, tidak sebagai relasi garis, walaupun digunakan aktif oleh backend `admin_service.approve_doctor` / `reject_doctor` dan diuji di `tests/backend/test_admin_service.py` L314 (constraint `doctor_profiles_approved_by_fkey`). Karena itu, FK ini **belum tercermin sebagai relasi dalam diagram final**.

**Tindak lanjut:** Dibuat revisi `ERD_PIXELT_FINAL_AUDITED` yang menambahkan relasi `approved_by` secara eksplisit (garis polyline dari sisi kiri `doctor_profiles` baris `approved_by` ke sisi kiri `User`, label nama `approved_by` berputar italic, label kardinalitas `0..*` di sisi User dan `0..1` di sisi doctor_profiles). 3 entitas, 73 atribut, dan 2 relasi asli tidak diubah.

**Keputusan akhir audit:** **LULUS DENGAN CATATAN** (detail di bagian I).

---

## B. Inventaris Sumber (Project Inventory)

| Kategori | Item | Path | Verifikasi |
|---|---|---|---|
| Root | Project root | `WEB_PIXELT/` | ✅ Terdapat git repo |
| Diagram | ERD final (asli) | `references/bab 4/ERD_PIXELT_FINAL.drawio` (27922 B, 11/5/2026 9:18 PM) | ✅ Tidak diubah |
| Diagram | PNG final (asli) | `references/bab 4/ERD_PIXELT_FINAL.png` (433318 B) | ✅ Tidak diubah |
| Diagram | SVG final (asli) | `references/bab 4/ERD_PIXELT_FINAL.svg` (11618 B) | ✅ Tidak diubah |
| Diagram | PUML final (asli) | `references/bab 4/ERD_PIXELT_FINAL.puml` (2051 B) | ⚠️ TIDAK konsisten (lihat Finding F-06) |
| Diagram | Generator satu-sumber | `references/bab 4/_build_erd_final.js` | ✅ |
| Diagram | Revisi audited | `references/bab 4/ERD_PIXELT_FINAL_AUDITED.drawio/.png/.svg` | ✅ Dihasilkan ulang, tidak menimpa asli |
| Diagram | Generator revisi audited | `references/bab 4/_build_erd_final_audited.js` | ✅ |
| Database | Migrations 001–008 | `database/migrations/001–008.sql` | ✅ Dibaca penuh |
| Database | Verifikasi pendaftaran | `database/verify_doctor_registration.sql` | ✅ |
| Backend | Routes (admin/analysis/health) | `backend/app/routes/admin.py`, `analysis.py`, `health.py` | ✅ |
| Backend | Controllers | `backend/app/controllers/admin_controller.py`, `analysis_controller.py` | ✅ |
| Backend | Services | `admin_service.py`, `analysis_service.py`, `storage_service.py` | ✅ |
| Backend | Repositories | `analysis_repository.py` | ✅ |
| Frontend | Auth services | `frontend/src/services/auth.ts` | ✅ |
| Frontend | Profile services | `frontend/src/services/profile.ts` | ✅ |
| Frontend | Analysis services | `frontend/src/services/analysis.ts` | ✅ |
| Frontend | Auth context | `frontend/src/context/AuthContext.tsx` | ✅ |
| Tests | Backend tests | `tests/backend/test_admin_service.py` (dll.) | ✅ L314: `doctor_profiles_approved_by_fkey` |

---

## C. Hasil Audit Entitas & Atribut

Diagram final berisi 3 entitas, 73 atribut. Semua cocok persis dengan migration 001–008 (dikonfirmasi skrip verifikasi `_audit_verify.js`: 73 atribut, semua entitas ditemukan).

### C.1 Entitas `User (auth.users)` — 5 atribut

| # | Atribut | Tipe | Sumber | Status |
|---|---------|------|--------|--------|
| 1 | id | uuid (PK) | Supabase Auth | DIVERIFIKASI |
| 2 | email | varchar | Supabase Auth | DIVERIFIKASI |
| 3 | raw_user_meta_data | jsonb | Supabase Auth | DIVERIFIKASI |
| 4 | raw_app_meta_data | jsonb | Supabase Auth | DIVERIFIKASI |
| 5 | created_at | timestamptz | Supabase Auth | DIVERIFIKASI |

Keterangan: `auth.users` adalah tabel eksternal Supabase Auth, bukan tabel aplikasi PIXEL-T; nama entitas ditulis `User (auth.users)` untuk pemisahan yang jelas.

### C.2 Entitas `doctor_profiles` — 29 atribut

| # | Atribut | Tipe | Nullable | Default | Bukti migration | Status |
|---|---------|------|----------|---------|-----------------|--------|
| 1 | id | uuid (PK) | NO | gen_random_uuid() | 004 L11 | DIVERIFIKASI |
| 2 | user_id | uuid (FK, UNIQUE) | NO | — | 004 L12, L46 | DIVERIFIKASI |
| 3 | full_name | text | NO | — | 004 L15 | DIVERIFIKASI |
| 4 | phone | text | YES | — | 004 L16 | DIVERIFIKASI |
| 5 | birth_date | date | YES | — | 004 L17 | DIVERIFIKASI |
| 6 | city | text | YES | — | 004 L18 | DIVERIFIKASI |
| 7 | profession_category | text | YES | — | 004 L21 | DIVERIFIKASI |
| 8 | academic_title | text | YES | — | 004 L22 | DIVERIFIKASI |
| 9 | primary_specialty | text | YES | — | 004 L23 | DIVERIFIKASI |
| 10 | subspecialty | text | YES | — | 004 L24 | DIVERIFIKASI |
| 11 | clinical_focus | text | YES | — | 004 L25 | DIVERIFIKASI |
| 12 | hospital | text | YES | — | 004 L26 | DIVERIFIKASI |
| 13 | department | text | YES | — | 004 L27 | DIVERIFIKASI |
| 14 | clinical_role | text | YES | — | 004 L28 | DIVERIFIKASI |
| 15 | years_experience | text | YES | — | 004 L29 | DIVERIFIKASI |
| 16 | practice_address | text | YES | — | 004 L30 | DIVERIFIKASI |
| 17 | str_number | text | YES | — | 004 L31 | DIVERIFIKASI |
| 18 | is_verified | boolean | NO | false | 004 L32 | DIVERIFIKASI |
| 19 | bio | text | YES | — | 004 L35 | DIVERIFIKASI |
| 20 | education | jsonb | NO | '[]'::jsonb | 004 L38 | DIVERIFIKASI |
| 21 | experience | jsonb | NO | '[]'::jsonb | 004 L39 | DIVERIFIKASI |
| 22 | avatar_url | text | YES | — | 006 L14–15 | DIVERIFIKASI |
| 23 | role | text | NO | 'doctor' | 007 L24–25 | DIVERIFIKASI |
| 24 | account_status | text | NO | 'pending' | 007 L28–29 | DIVERIFIKASI |
| 25 | approved_by | uuid (FK) | YES | — | 007 L33 | DIVERIFIKASI |
| 26 | approved_at | timestamptz | YES | — | 007 L34 | DIVERIFIKASI |
| 27 | rejection_reason | text | YES | — | 007 L35 | DIVERIFIKASI |
| 28 | created_at | timestamptz | NO | timezone('utc', now()) | 004 L42 | DIVERIFIKASI |
| 29 | updated_at | timestamptz | NO | timezone('utc', now()) | 004 L43 | DIVERIFIKASI |

Index: `idx_doctor_profiles_user_id` (004 L50). RLS diaktifkan 004 L53, 4 policy (004 L56–78). 

### C.3 Entitas `analyses` — 39 atribut

| # | Atribut | Tipe | Nullable | Default | Bukti migration | Status |
|---|---------|------|----------|---------|-----------------|--------|
| 1 | id | uuid (PK) | NO | gen_random_uuid() | 001 L16 | DIVERIFIKASI |
| 2 | user_id | uuid (FK) | NO | — | 001 L17 | DIVERIFIKASI |
| 3 | status | varchar(20) | NO | 'processing' | 001 L20–21 | DIVERIFIKASI |
| 4 | original_image_path | text | NO | — | 001 L24 | DIVERIFIKASI |
| 5 | original_filename | text | YES | — | 001 L25 | DIVERIFIKASI |
| 6 | original_mime_type | varchar(50) | YES | — | 001 L26 | DIVERIFIKASI |
| 7 | original_width | integer | YES | — | 001 L27 | DIVERIFIKASI |
| 8 | original_height | integer | YES | — | 001 L28 | DIVERIFIKASI |
| 9 | binary_mask_path | text | YES | — | 001 L31 | DIVERIFIKASI |
| 10 | segmentation_overlay_path | text | YES | — | 001 L32 | DIVERIFIKASI |
| 11 | segmentation_status | varchar(20) | YES | — | 001 L33–34 | DIVERIFIKASI |
| 12 | area_pixels | integer | YES | — | 001 L35 | DIVERIFIKASI |
| 13 | area_ratio | numeric(7,4) | YES | — | 001 L36 | DIVERIFIKASI |
| 14 | bounding_width_pixels | integer | YES | — | 001 L37 | DIVERIFIKASI |
| 15 | bounding_height_pixels | integer | YES | — | 001 L38 | DIVERIFIKASI |
| 16 | gradcam_heatmap_path | text | YES | — | 001 L41 | DIVERIFIKASI |
| 17 | gradcam_overlay_path | text | YES | — | 001 L42 | DIVERIFIKASI |
| 18 | gradcam_target_layer | varchar(100) | YES | — | 001 L43 | DIVERIFIKASI |
| 19 | gradcam_method | varchar(50) | YES | — | 001 L44 | DIVERIFIKASI |
| 20 | gradcam_config_version | varchar(50) | YES | — | 001 L45 | DIVERIFIKASI |
| 21 | gradcam_status | varchar(20) | YES | — | 002 L6–9 | DIVERIFIKASI |
| 22 | model_architecture | varchar(100) | YES | — | 001 L48 | DIVERIFIKASI |
| 23 | model_version | varchar(50) | YES | — | 001 L49 | DIVERIFIKASI |
| 24 | model_config_version | varchar(50) | YES | — | 001 L50 | DIVERIFIKASI |
| 25 | model_input_size | integer | YES | — | 001 L51 | DIVERIFIKASI |
| 26 | model_threshold | numeric(4,3) | YES | — | 001 L52 | DIVERIFIKASI |
| 27 | model_checkpoint_sha256 | varchar(64) | YES | — | 002 L3 | DIVERIFIKASI |
| 28 | tta_enabled | boolean | YES | — | 001 L53 | DIVERIFIKASI |
| 29 | tta_scales | jsonb | YES | — | 002 L4 | DIVERIFIKASI |
| 30 | tta_orientations | jsonb | YES | — | 002 L5 | DIVERIFIKASI |
| 31 | postprocessing_enabled | boolean | YES | — | 001 L54 | DIVERIFIKASI |
| 32 | summary_text | text | YES | — | 001 L57 | DIVERIFIKASI |
| 33 | error_code | varchar(50) | YES | — | 001 L58 | DIVERIFIKASI |
| 34 | error_message | text | YES | — | 001 L59 | DIVERIFIKASI |
| 35 | current_step | varchar(64) | YES | — | 003 L6 | DIVERIFIKASI |
| 36 | progress_percent | smallint | YES | — | 003 L7 | DIVERIFIKASI |
| 37 | created_at | timestamptz | NO | timezone('utc', now()) | 001 L62 | DIVERIFIKASI |
| 38 | completed_at | timestamptz | YES | — | 001 L63 | DIVERIFIKASI |
| 39 | updated_at | timestamptz | NO | timezone('utc', now()) | 001 L64 | DIVERIFIKASI |

Index: `idx_analyses_user_id` (001 L68), `idx_analyses_status` (L69), `idx_analyses_created_at` (L70), `idx_analyses_user_created` (L71). RLS diaktifkan 001 L74, 4 policy tabel (L77–99) + 3 policy storage asset (L123–145).

**Buckets Storage (eksternal, bukan tabel relasi):** `profile-avatars` (005) dan path asset analisis (001). Diecualkan dari ERD (bukan entitas relasional PostgreSQL).

---

## D. Relasi & Kardinalitas

| Relasi | FK sumber | Atribut yang mendasarkan | Kardinalitas diagram | Bukti migration | Status |
|---|---|---|---|---|---|
| User — doctor_profiles | `doctor_profiles.user_id` | NOT NULL + UNIQUE | **1 : 0..1** | 004 L12, L46 | DIVERIFIKASI |
| User — analyses | `analyses.user_id` | NOT NULL, tanpa UNIQUE | **1 : \*** | 001 L17 | DIVERIFIKASI |
| doctor_profiles — User (`approved_by`) | `doctor_profiles.approved_by` | nullable FK | **0..* : 0..1** (revisi audited) | 007 L33 | DIVERIFIKASI |

Catatan kardinalitas:
- `user_id` NOT NULL UNIQUE → satu profil dokter ↔ tepat satu pengguna; satu pengguna ↔ nol atau satu profil dokter.
- `analyses.user_id` NOT NULL tanpa UNIQUE → satu analisis ↔ tepat satu pengguna; satu pengguna ↔ nol atau banyak analisis.
- `approved_by` nullable FK ke `auth.users(id)` → satu admin dapat menyetujui banyak profil (0..*); satu profil memiliki nol atau satu penyetuju (0..1).

**Tidak ada relasi ke tabel Storage** (`analysis-assets`, `profile-avatars`) karena bukan tabel PostgreSQL.

---

## E. Audit Ketujuh Alur Aplikasi

| # | Alur | Elemen database yang terlibat | Bukti kode | Status ERD |
|---|------|------------------------------|------------|------------|
| 1 | Sign Up | `auth.users` (SignUp) + trigger `handle_new_doctor_signup` → `doctor_profiles` (role='doctor', status='pending'); admin dilewati | `frontend/src/services/auth.ts` L131–161 (`registerUser`, signUp + metadata); migration 008 L28–79; admin_service `approve_doctor` L135–233 | ✅ Tercermin: entitas User, doctor_profiles, trigger |
| 2 | Sign In | Baca `auth.users` (session) + `doctor_profiles.role`, `account_status` | `auth.ts` L297–316 (`fetchUserProfileStatus`, `.eq('user_id', user.id)`); `AuthContext.tsx` L78–84, L106–112 | ✅ Tercermin |
| 3 | Upload Image | `analyses` insert (`user_id`, `status='processing'`, path aset) + Storage | `analysis_service.py` L369 (`create_analysis`); `analysis_repository.py` L38–107; routes `analysis.py` L11–13 | ✅ Tercermin |
| 4 | Segmentation | Update `analyses` (status, path artefak, metrik, progres, `completed_at`) | `analysis_repository.py` L133–162 (`update`); `createAnalysis` / `getAnalysis` frontend `analysis.ts` L185–195 | ✅ Tercermin |
| 5 | History | Query `analyses` WHERE `user_id`; DELETE record + file Storage | `listHistory` `analysis.ts` L212–214; `deleteAnalysis` L218–222; routes `/history` L45–47, DELETE L56 | ✅ Tercermin |
| 6 | Doctor Profile | Upsert `doctor_profiles` (avatar_url, role, account_status, dll.) | `profile.ts` L149–163, L344–345 (`onConflict user_id`); `avatar_url` 006 L14–15 | ✅ Tercermin |
| 7 | Sign Out | Hanya mengakhiri sesi Supabase Auth; tidak menambah entitas/relasi | `AuthContext.tsx` L59 (`logoutUser`) | ✅ Tidak memengaruhi ERD |

Admin approval (alur tambahan terkait FK `approved_by`): `admin_service.py` L188–199 (`approved_by` L192, `approved_at` L193); reject L235–294 (`approved_by` L288); controller `admin_controller.py` L55–56 (admin id dari `g.current_user['id']`). Terverifikasi aktif dan diuji (`tests/backend/test_admin_service.py` L314: `doctor_profiles_approved_by_fkey`).

---

## F. Temuan Audit

| ID | Temuan | Severity | Bukti | Rekomendasi |
|---|--------|----------|-------|-------------|
| F-01 | `approved_by` (FK `doctor_profiles -> auth.users`, migration 007 L33) digunakan aktif oleh backend (`admin_service.py` L192, L288) dan diuji (backend test L314 constraint `doctor_profiles_approved_by_fkey`), tetapi ERD FINAL hanya mencantumkannya sebagai atribut, **tidak sebagai relasi garis**. | Sedang | 007 L33; `admin_service.py` L188–199, L284–294; `tests/backend/test_admin_service.py` L314 | Ditangani di revisi `ERD_PIXELT_FINAL_AUDITED` (relasi garis `rel_doctor_approved_by` ditambahkan) |
| F-02 | Komentar migration 007 L17 menyebutkan `raw_user_meta_data.role = 'admin'`, tetapi kode aktual (007 L53–70, 008 L38) dan frontend (`auth.ts` L328–334) menggunakan `raw_app_meta_data` / `app_metadata`. | Rendah | 007 L17 vs 007 L53–70, 008 L38 | Perbaiki komentar 007 L17 agar menyebutkan `raw_app_meta_data` |
| F-03 | `ERD_PIXELT_FINAL.puml` **tidak konsisten** dengan drawio/PNG/SVG final: hanya 16 field `doctor_profiles`, `users` class pakai `user_metadata` (bukan `raw_user_meta_data`/`raw_app_meta_data`), `analyses` hanya 21 field, tidak ada `approved_by`. | Tinggi (dokumen pendukung) | `ERD_PIXELT_FINAL.puml` L31–85 vs drawio 73 atribut | Hapus atau sinkronkan puml agar tidak menyesatkan pembaca skripsi |
| F-04 | Desain ERD sengaja sederhana: hanya tabel relasional PostgreSQL; Storage bucket (`profile-avatars`, `analysis-assets`) dan session/token Supabase Auth tidak dimodelkan sebagai entitas relasi. | Informasi | 005, 001 L107–118 | Pertahankan; catat dalam penjelasan akademik |
| F-05 | Tidak ada E2E/uji browser untuk alur penuh (registrasi → approval → analisis → riwayat); verifikasi berbasis static code + migration. | Rendah | `tests/` (unit backend + frontend saja) | Catat sebagai keterbatasan akademik |

---

## G. Audit Visual & Draw.io

Pemeriksaan programatik terhadap `ERD_PIXELT_FINAL_AUDITED.drawio` (`_audit_verify_audited.js`):

- **Entities:** 3 (`ent_user` User (auth.users), `ent_doctor` doctor_profiles, `ent_analyses` analyses)
- **Edge cells:** 3 (`rel_user_doctor`, `rel_user_analyses`, `rel_doctor_approved_by`)
- **Cardinality labels:** 6 (`1`, `0..1`, `1`, `*`, `0..*`, `0..1`)
- **Relation name:** 1 (`approved_by`, rotasi -90°, italic)
- **Attribute cells:** 73 (5 + 29 + 39)
- **Vertex cells:** 83; edge cells: 3; mxCell tags seimbang (88 open + self-close = 86 close + 2 self-closing → balanced: true)
- **XML:** valid (diparses tanpa error)

SVG audited: 83 text nodes, 2 line, 1 polyline (relasi approved_by), 7 rect — konsisten dengan drawio. PNG audited: canvas 1280×900, render 2× (2560×1800), relasi `approved_by` tergambar bersih sebagai polyline (x=40; stub User di y=88.5; stub doctor_profiles di baris `approved_by` y=742.5), label `0..*` (dekat User) dan `0..1` (dekat doctor_proples), nama `approved_by` italic berputar di margin kiri, tanpa overlap.

File asli `ERD_PIXELT_FINAL.{drawio,png,svg}` **tidak diubah** (ukuran dan timestamp asli terjaga: 27922/433318/11618 B, 11/5/2026 9:18:24 PM).

---

## H. Rekomendasi

1. Gunakan `ERD_PIXELT_FINAL_AUDITED.{png/svg}` sebagai gambar ERD final di Bab IV skripsi (relasi `approved_by` sudah tercermin sebagai garis).
2. Perbaiki komentar migration 007 L17: ganti `raw_user_meta_data.role` menjadi `raw_app_meta_data.role` / `app_metadata`.
3. Hapus atau sinkronkan `ERD_PIXELT_FINAL.puml` (saat ini tidak konsisten: 16 field, `user_metadata`, tanpa `approved_by`).
4. Catat di skripsi bahwa `auth.users` adalah eksternal Supabase Auth dan Storage bucket bukan tabel relasi.
5. Catat keterbatasan: verifikasi berbasis migration + static code (tidak ada E2E browser test; skema Supabase live tidak dibaca via kredensial).
6. Jangan menambahkan controller/service/repository/endpoint/pipeline AI sebagai entitas ERD (bukan lingkup model data relasional).

---

## I. Status Akhir Audit

| Pemeriksaan | Hasil |
|---|---|
| Ketepatan atribut entitas (5 / 29 / 39) | ✅ Cocok persis |
| Primary key & foreign key | ✅ Cocok |
| Kardinalitas 1:0..1 dan 1:* | ✅ Cocok |
| FK `approved_by` (007 L33) | ⚠️ Ada di skema/backend/test, ditambahkan relasi garis di revisi audited |
| Trigger/function/RLS/Storage | ✅ Diverifikasi (005, 007 L81–98, 008) |
| Ketujuh alur aplikasi | ✅ Tercermin dalam ERD |
| Konsistensi drawio / PNG / SVG (revisi audited) | ✅ Konsisten |
| File asli tidak diubah | ✅ Terjaga |
| Konsistensi drawio vs puml | ❌ Tidak konsisten (puml usang) |

**KEPUTUSAN AKHIR: LULUS DENGAN CATATAN**  
Alasan: semua elemen kritis ERD (entitas, atribut, PK, FK, kardinalitas, relasi utama, tujuh alur) valid dan terverifikasi; satu catatan penting adalah FK `approved_by` yang di revisi audited digambarkan sebagai relasi garis, dan dokumen pendukung `.puml` usang yang perlu disinkronkan atau dihapus. Tidak ada temuan yang membatalkan kelayakan ERD untuk Bab IV skripsi S1.

---

## J. Daftar File Audit

1. `references/bab 4/ERD_PIXELT_FINAL.drawio` (asli, tidak diubah)
2. `references/bab 4/ERD_PIXELT_FINAL.png` (asli, tidak diubah)
3. `references/bab 4/ERD_PIXELT_FINAL.svg` (asli, tidak diubah)
4. `references/bab 4/ERD_PIXELT_FINAL.puml` (asli, usang/tidak konsisten)
5. `references/bab 4/ERD_PIXELT_FINAL_AUDITED.drawio` (revisi: +relasi approved_by)
6. `references/bab 4/ERD_PIXELT_FINAL_AUDITED.png` (revisi)
7. `references/bab 4/ERD_PIXELT_FINAL_AUDITED.svg` (revisi)
8. `references/bab 4/_build_erd_final.js` (generator asli)
9. `references/bab 4/_build_erd_final_audited.js` (generator revisi)
10. `references/bab 4/_audit_verify.js` (verifikasi asli)
11. `references/bab 4/_audit_verify_audited.js` (verifikasi revisi)
12. `references/bab 4/_debug_audit.js` (script debugging)
13. `database/migrations/001–008.sql` (sumber kebenaran skema)
14. `database/verify_doctor_registration.sql` (verifikasi pendaftaran)

**Dokumen pendukung audit ini:**
- `MATRIKS_BUKTI_AUDIT_ERD_PIXELT_FINAL.md` (matriks bukti detail)
- `PENJELASAN_AKADEMIK_ERD_PIXELT_FINAL_AUDITED.md` (penjelasan akademik Bab IV)

---
*Dibuat oleh proses audit independen PIXEL-T. Tidak ada kredensial, token, atau rahasia dalam dokumen ini.*