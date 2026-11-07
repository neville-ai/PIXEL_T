# Laporan Audit Final ERD PIXEL-T

**Versi:** 2.0 (Desain Sederhana mengikuti ERD_contoh.png)
**Tanggal:** 5 November 2026
**Status:** FINAL — LULUS AUDIT
**Direktori:** `references/bab 4/`

---

## 1. Ringkasan Eksekutif

Audit menyeluruh telah dilakukan terhadap Entity Relationship Diagram (ERD) sistem web PIXEL-T untuk memastikan kesesuaian struktur diagram dengan implementasi database aktual (migration SQL 001–008), source code frontend/backend, dan ketujuh alur aplikasi utama.

**Hasil:** ERD final dibangun ulang dari sumber kebenaran utama (database migrations), divalidasi terhadap source code, lalu dirender dalam desain **sederhana** yang konsisten dengan `ERD_contoh.png` (kotak putih, header abu-abu tipis, garis orthogonal, label kardinalitas polos).

**File Hasil:**
- `ERD_PIXELT_FINAL.drawio` — Sumber diagram (dapat diedit di diagrams.net)
- `ERD_PIXELT_FINAL.png` — PNG resolusi tinggi 2560×1800 (2× scale) siap skripsi
- `ERD_PIXELT_FINAL.svg` — Format vektor

**Struktur diagram:** 3 entitas — `User (auth.users)`, `doctor_profiles`, `analyses` — dan 2 relasi (1:0..1 dan 1:*). Seluruhnya diturunkan dari migration 001–008.

---

## 2. Struktur Database Aktual

Database PIXEL-T menggunakan PostgreSQL (Supabase) dengan **dua tabel aplikasi** dan **satu entitas eksternal** (Supabase Auth):

| Tabel | Schema | Sumber |
|---|---|---|
| `auth.users` | `auth` | Supabase Auth (eksternal, bukan tabel aplikasi) |
| `public.analyses` | `public` | Migration 001, 002, 003 |
| `public.doctor_profiles` | `public` | Migration 004, 006, 007 |

Supabase Storage (`analysis-assets`, `profile-avatars`) berupa **file object**, bukan tabel relasional, sehingga tidak dijadikan entitas relasi pada ERD.

---

## 3. Tabel dan Atribut yang Diverifikasi

### 3.1 `User (auth.users)` — entitas eksternal Supabase Auth
Ditampilkan hanya kolom yang relevan dengan kebutuhan sistem:
`id (PK)`, `email`, `raw_user_meta_data`, `raw_app_meta_data`, `created_at`.

Peran admin disimpan di `raw_app_meta_data.role = 'admin'` (dibuat manual via Admin API), **bukan** di `doctor_profiles`.

### 3.2 `doctor_profiles` (29 atribut)
Diverifikasi dari migration 004 (kolom dasar), 006 (`avatar_url`), 007 (`role`, `account_status`, `approved_by`, `approved_at`, `rejection_reason`):
`id (PK)`, `user_id (FK, UNIQUE)`, `full_name`, `phone`, `birth_date`, `city`, `profession_category`, `academic_title`, `primary_specialty`, `subspecialty`, `clinical_focus`, `hospital`, `department`, `clinical_role`, `years_experience`, `practice_address`, `str_number`, `is_verified`, `bio`, `education`, `experience`, `avatar_url`, `role`, `account_status`, `approved_by (FK)`, `approved_at`, `rejection_reason`, `created_at`, `updated_at`.

### 3.3 `analyses` (39 atribut)
Diverifikasi dari migration 001 (kolom dasar), 002 (`model_checkpoint_sha256`, `tta_scales`, `tta_orientations`, `gradcam_status`), 003 (`current_step`, `progress_percent`):
`id (PK)`, `user_id (FK)`, `status`, seluruh kolom metadata citra, hasil segmentasi, Grad-CAM, metadata model/TTA, ringkasan, error, progres, dan timestamp — sebanyak 39 kolom.

---

## 4. Primary Key & Foreign Key

| Tabel | PK | FK | Ke |
|---|---|---|---|
| `doctor_profiles` | `id` | `user_id` (NOT NULL, UNIQUE) | `auth.users(id)` |
| `doctor_profiles` | — | `approved_by` (nullable) | `auth.users(id)` |
| `analyses` | `id` | `user_id` (NOT NULL) | `auth.users(id)` |

---

## 5. Constraint, Trigger, dan Function

- **CHECK:** `analyses.status IN ('processing','completed','failed')`; `analyses.segmentation_status IN ('detected','not_detected')`; `analyses.gradcam_status IN ('completed','failed')`; `analyses.progress_percent` 0–100.
- **UNIQUE:** `doctor_profiles_user_id_key UNIQUE (user_id)` — jaminan tepat satu profil per pengguna.
- **DEFAULT:** `analyses.status = 'processing'`; `analyses.progress_percent` nullable; `doctor_profiles.role = 'doctor'`; `doctor_profiles.account_status = 'pending'`; `is_verified = false`.
- **Trigger `on_auth_user_created_doctor_profile`** (migration 008): AFTER INSERT pada `auth.users` — membuat baris `doctor_profiles` (role='doctor', account_status='pending') untuk pendaftaran dokter, **dilewati untuk akun admin** (`raw_app_meta_data.role = 'admin'`). Ini bukan entitas, melainkan mekanisme pembentukan relasi yang dijelaskan dalam laporan.

---

## 6. Relasi dan Kardinalitas

| Relasi | Bukti | Kardinalitas |
|---|---|---|
| `User (auth.users)` — `doctor_profiles` | `doctor_profiles.user_id` FK NOT NULL + UNIQUE (004 L12, L46) | 1 : 0..1 |
| `User (auth.users)` — `analyses` | `analyses.user_id` FK NOT NULL, tanpa UNIQUE (001 L17) | 1 : * |

`approved_by` adalah FK sekunder dalam relasi `User` — `doctor_profiles`; untuk menjaga kesederhanaan diagram, garis khusus tidak digambar dan hanya dicatat sebagai atribut FK. Seluruh bukti terdokumentasi di `MATRIKS_BUKTI_VALIDASI_ERD_PIXELT.md`.

---

## 7. Audit Tujuh Alur

1. **Sign Up** → Supabase Auth membuat `auth.users`; trigger 008 membuat `doctor_profiles` (admin dilewati).
2. **Sign In** → membaca identitas dari Supabase Auth + `doctor_profiles` (role/account_status).
3. **Upload Image** → file ke Storage, metadata ke `analyses` (user_id, status='processing').
4. **Segmentation** → update `analyses` (status, path artefak, metrik, progres, completed_at).
5. **History** → query `analyses` WHERE user_id; hapus record + file Storage.
6. **Doctor Profile** → upsert `doctor_profiles`; statistik dihitung saat tampilan, bukan kolom.
7. **Sign Out** → hanya mengakhiri sesi Supabase Auth; tidak menambah entitas/relasi database.

Ketujuh alur tervalidasi; rinciannya di `MATRIKS_BUKTI_VALIDASI_ERD_PIXELT.md` bagian H.

---

## 8. Kesesuaian dengan Diagram Bab IV Lain

- **Class Diagram** menggambarkan kelas/perangkat lunak (Service, Controller, Repository) — sengaja tidak disamakan dengan tabel; tidak menjadi entitas ERD.
- **Use Case / Activity / Sequence** menggambarkan perilaku dan urutan, bukan struktur data.
- Peran admin/dokter dan status akun konsisten: admin pada `auth.users.raw_app_meta_data.role`, dokter pada `doctor_profiles.role` + `account_status`.

---

## 9. Kesalahan ERD Lama dan Perbaikan

- ERD lama terlalu kompleks (mirip Class Diagram, kolom berlebih, dekorasi) → dirender ulang dengan gaya sederhana `ERD_contoh.png`.
- Struktur ulang dari migration 001–008; kardinalitas diperbaiki menjadi 1:0..1 (UNIQUE) dan 1:* (NOT NULL tanpa UNIQUE).
- Enam file versi sebelumnya dipertahankan sebagai `*_PREVIOUS.*`.

---

## 10. Keterbatasan Audit

- Skema Supabase live tidak diubah/dibaca lewat kredensial; verifikasi berbasis migration + source code.
- Kolom internal Supabase Auth selain yang direferensikan tidak ditampilkan (sengaja, untuk kesederhanaan).

---

## 11. Status Akhir

**FINAL — LULUS AUDIT.** Seluruh pemeriksaan kritis (ketepatan database, ketepatan relasi, kesesuaian aplikasi, kualitas desain, kualitas file) memenuhi syarat kelulusan. Tidak ada atribut, relasi, atau kardinalitas yang dirancang tanpa bukti migration/source code.
