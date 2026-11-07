# Penjelasan Akademik ERD PIXEL-T Final

**Versi:** 2.0 (Desain Sederhana mengikuti ERD_contoh.png)
**Tanggal:** 5 November 2026
**Untuk:** Bab IV Skripsi S1
**Direktori:** `references/bab 4/`

---

## 1. Pendahuluan

Entity Relationship Diagram (ERD) ini menggambarkan struktur data logis dan fisik sistem web **PIXEL-T** (*Pixel-based Tumor Analysis Tool*), sebuah aplikasi analisis citra tumor otak berbasis web yang dikembangkan menggunakan React (frontend), Flask/Python (backend), dan Supabase (PostgreSQL + Auth + Storage) sebagai platform backend-as-a-service.

ERD ini merupakan **versi final** yang telah diaudit independen terhadap:
- **8 file migration SQL** (`database/migrations/001–008.sql`) sebagai sumber kebenaran utama struktur database,
- **Source code** frontend (React/TypeScript) dan backend (Flask/Python),
- **Ketujuh alur aplikasi utama** (Sign Up, Sign In, Upload Image, Segmentation, History, Doctor Profile, Sign Out).

Semua entitas, atribut, primary key, foreign key, constraint, relasi, dan kardinalitas diturunkan langsung dari database aktual dan tidak ada satu pun atribut yang dirancang tanpa dasar migrasi atau source code.

---

## 2. Tujuan ERD

ERD pada tahap ini disusun dengan tujuan:
1. Menjelaskan struktur penyimpanan data database aplikasi PIXEL-T secara sederhana.
2. Menjadi dasar visual yang konsisten dengan notasi ERD sederhana pada `ERD_contoh.png`.
3. Menjadi acuan akademik bagi Bab IV skripsi mengenai model data fisik sistem.

---

## 3. Entitas dan Atribut

### 3.1 Entitas `User (auth.users)`

Entitas ini mewakili akun pengguna yang dibangun oleh **Supabase Auth**, bukan tabel aplikasi yang dibuat oleh PIXEL-T. Oleh karena itu namanya ditulis `User (auth.users)` agar pemisahannya jelas.

| Atribut | Keterangan |
|---------|-----------|
| id | Primary key (UUID) pengguna |
| email | Alamat email pengguna |
| raw_user_meta_data | Metadata pengguna yang diisi pada sign up |
| raw_app_meta_data | App metadata berisi `role = 'admin'` untuk akun admin |
| created_at | Waktu pembuatan akun |

### 3.2 Entitas `doctor_profiles`

Tabel aplikasi yang menyimpan profil klinisi. Setiap baris memiliki relasi satu-ke-satu ke akun pengguna melalui `user_id` yang bersifat **NOT NULL** sekaligus **UNIQUE**, sehingga interpretasi kardinalitasnya adalah **satu profil dokter berhubungan dengan tepat satu pengguna**, dan satu pengguna dapat memiliki nol atau satu profil dokter.

### 3.3 Entitas `analyses`

Tabel aplikasi yang menyimpan hasil analisis citra dari satu pengguna. Setiap baris analisis berownership-nya langsung pada akun pengguna melalui `user_id` yang **NOT NULL** tanpa batasan jumlah, sehingga kardinalitasnya adalah **satu analisis berhubungan dengan tepat satu pengguna**, dan satu pengguna dapat memiliki nol atau banyak analisis.

---

## 4. Primary Key dan Foreign Key

- **Primary Key** wajib pada kolom identitas `id` (UUID) untuk `doctor_profiles` dan `analyses`.
- **Foreign Key** utama pada `doctor_profiles.user_id` (NOT NULL, UNIQUE) dan `analyses.user_id` (NOT NULL) yang merujuk ke `auth.users.id`.
- Selain itu terdapat foreign key pengantar persetujuan (`doctor_profiles.approved_by`) yang merujuk ke `auth.users.id` untuk proses verifikasi doktor oleh admin.

---

## 5. Relasi dan Kardinalitas

1. **User (auth.users) — doctor_profiles : Kardinalitas 1 : 0..1**
   - Satu profil dokter → tepat satu pengguna.
   - Satu pengguna → nol atau satu profil dokter.
   - Didasarkan pada `doctor_profiles.user_id` berstatus NOT NULL dan UNIQUE.

2. **User (auth.users) — analyses : Kardinalitas 1 : \***
   - Satu analisis → tepat satu pengguna.
   - Satu pengguna → nol atau banyak analisis.
   - Didasarkan pada `analyses.user_id` berstatus NOT NULL tanpa UNIQUE.

---

## 6. Hubungan Data dengan Fitur PIXEL-T

- **Sign Up:** memicu pembuatan akun di Supabase Auth dan otomatis pembuatan profil dokter melalui trigger `handle_new_doctor_signup` (admin dilewati).
- **Sign In:** mengenali identitas pengguna serta status akun melalui `doctor_profiles`.
- **Upload Image:** pembuatan awal baris `analyses` (`status = 'processing'`) pada akun pengguna.
- **Segmentation:** pembaruan status, path artefak, metrik, dan progres pada baris `analyses`.
- **History:** penghapusan baris `analyses` dan file terkait pada penyimpanan.
- **Doctor Profile:** penyimpanan dan verifikasi profil doktor pada `doctor_profiles`.

---

## 7. Hasil Audit Desain

- Desain ERD akhir bersifat **sederhana**: tiga entitas dan dua relasi.
- Setiap entitas ditampilkan sebagai kotak tabel polos dengan header dan atribut.
- Tidak memuat controller, service, repository, endpoint, atau pipeline AI sebagai entitas.
- Tidak memasukkan Supabase Storage sebagai tabel relasional.
- Tidak menggambarkan session, token, atau signed URL sebagai atribut permanen tanpa bukti.

---

## 8. Catatan

Gambar ERD ini dipublikasikan sebagai `ERD_PIXELT_FINAL.png` dengan resolusi 2560×1800 piksel (skala 2×) sehingga dapat langsung ditampilkan pada halaman skripsi dengan keterangan gambar sesuai penyusunan Bab IV (misalnya **Gambar 4.1**).
