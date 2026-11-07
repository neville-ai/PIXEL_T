# Penjelasan Akademik ERD PIXEL-T Final (Audited)

**Versi:** 3.0 (revisi audited — relasi `approved_by` disertakan)  
**Tanggal:** 5 November 2026  
**Untuk:** Bab IV Skripsi S1  
**Gambar acuan:** `ERD_PIXELT_FINAL_AUDITED.png` (2560×1800 px, skala 2×)  
**Direktori:** `references/bab 4/`

---

## A. Pendahuluan

Entity Relationship Diagram (ERD) ini menggambarkan struktur data logis dan fisik sistem web **PIXEL-T** (*Pixel-based Tumor Analysis Tool*), aplikasi analisis citra tumor otak berbasis web yang dibangun dengan React (frontend), Flask/Python (backend), dan Supabase (PostgreSQL + Auth + Storage) sebagai platform backend-as-a-service.

ERD disusun dari **bukti mentah** dan bukan dari asumsi desain:

- 8 file migration SQL (`database/migrations/001–008.sql`) sebagai sumber kebenaran struktur database;
- source code backend (Flask/Python) yang membaca dan menulis tabel;
- source code frontend (React/TypeScript) yang memicu operasi data;
- uji backend (`tests/backend/`) yang mengunci perilaku operasi basis data;
- ketujuh alur aplikasi utama: Sign Up, Sign In, Upload Image, Segmentation, History, Doctor Profile, dan Sign Out.

Setiap entitas, atribut, primary key, foreign key, constraint, relasi, dan kardinalitas dapat dilacak ke migration atau source code tertentu. ERD tidak memuat atribut yang dirancang tanpa dasar implementasi.

---

## B. Tujuan ERD

1. Menjelaskan struktur penyimpanan data PIXEL-T secara ringkas dan akurat.
2. Menjadi dasar visual yang konsisten dengan notasi ERD sederhana (`ERD_contoh.png`): kotak tabel polos, header, dan baris `nama : tipe (PK/FK)`.
3. Menjadi acuan akademik Bab IV untuk menjelaskan model data fisik sistem.
4. Menjadi bukti bahwa model data mendukung seluruh alur fungsional aplikasi dua peran (admin dan dokter).

---

## C. Entitas dan Atribut

ERD final memuat **3 entitas** dan **73 atribut** (5 + 29 + 39). Jumlah ini identik dengan hasil verifikasi programatik berkas drawio.

### C.1 Entitas `User (auth.users)`

Entitas ini mewakili akun pengguna yang dibangun oleh **Supabase Auth**, bukan tabel aplikasi yang dibuat PIXEL-T. Penulisan `User (auth.users)` menegaskan pemisahan antara skema `auth` (eksternal) dan skema `public` (aplikasi).

| Atribut | Tipe | Keterangan |
|---------|------|-----------|
| `id` | uuid (PK) | Identitas pengguna; menjadi target FK kedua tabel aplikasi |
| `email` | varchar | Alamat email akun |
| `raw_user_meta_data` | jsonb | Metadata pendaftaran (mis. `full_name`, `hospital`, `primary_specialty`) yang dibaca trigger |
| `raw_app_meta_data` | jsonb | Metadata tepercaya; berisi `role = 'admin'` untuk akun administrator |
| `created_at` | timestamptz | Waktu pembuatan akun |

### C.2 Entitas `doctor_profiles`

Tabel aplikasi penyimpan profil klinisi. Setiap baris memiliki relasi satu-ke-satu ke akun pengguna melalui `user_id` yang **NOT NULL** dan **UNIQUE**. Tabel ini menyimpan data pribadi, data profesional, pendidikan, pengalaman, avatar, serta atribut tata kelola akun (`role`, `account_status`, `approved_by`, `approved_at`, `rejection_reason`).

Rincian 29 atribut tercantum pada `MATRIKS_BUKTI_AUDIT_ERD_PIXELT_FINAL.md` bagian B.2, masing-masing dengan nomor baris migration sebagai bukti.

### C.3 Entitas `analyses`

Tabel aplikasi penyimpan hasil analisis citra. Setiap baris dimiliki langsung oleh satu pengguna melalui `user_id` yang **NOT NULL** tanpa batas jumlah. Tabel ini menampung metadata citra asli, artefak segmentasi, metrik area dan *bounding box*, artefak serta konfigurasi Grad-CAM, metadata model dan TTA, ringkasan hasil, status/error, dan progres pemrosesan.

Rincian 39 atribut tercantum pada matriks bagian B.3.

---

## D. Primary Key dan Foreign Key

### D.1 Primary Key

| Tabel | Primary Key | Bukti |
|---|---|---|
| `doctor_profiles` | `id` (uuid, `gen_random_uuid()`) | 004 L11 |
| `analyses` | `id` (uuid, `gen_random_uuid()`) | 001 L16 |

`User (auth.users)` menggunakan primary key bawaan Supabase Auth (`id`).

### D.2 Foreign Key

Terdapat **tiga foreign key fisik**, seluruhnya merujuk ke `auth.users(id)`:

1. `doctor_profiles.user_id` — **NOT NULL**, `ON DELETE CASCADE` (004 L12), dengan constraint `UNIQUE` (004 L46).
2. `analyses.user_id` — **NOT NULL**, `ON DELETE CASCADE` (001 L17), tanpa `UNIQUE`.
3. `doctor_profiles.approved_by` — **nullable**, `REFERENCES auth.users(id)` (007 L33). Kolom ini menyimpan identitas admin yang menyetujui atau menolak akun dokter.

FK ketiga bukan atribut pasif: `admin_service.approve_doctor()` menulis `approved_by` (dan `approved_at`) pada proses persetujuan (L188–199), `reject_doctor()` menulis `approved_by` pada proses penolakan (L284–294), dan constraint tersebut dikunci oleh uji backend (`tests/backend/test_admin_service.py` L314, `doctor_profiles_approved_by_fkey`). Karena itu, revisi audited menggambarkannya sebagai **relasi garis eksplisit**, bukan sekadar atribut.

---

## E. Relasi dan Kardinalitas

### E.1 `User` — `doctor_profiles` : **1 : 0..1**

- Satu profil dokter terhubung ke **tepat satu** pengguna (`user_id` NOT NULL).
- Satu pengguna memiliki **nol atau satu** profil dokter (`user_id` UNIQUE).
- Bukti: 004 L12 dan L46.

Kardinalitas ini juga menjelaskan mengapa akun admin tidak memiliki baris `doctor_profiles`: trigger 008 melewati akun dengan `raw_app_meta_data.role = 'admin'` (008 L38).

### E.2 `User` — `analyses` : **1 : \***

- Satu analisis terhubung ke **tepat satu** pengguna (`user_id` NOT NULL).
- Satu pengguna memiliki **nol atau banyak** analisis (tanpa UNIQUE).
- Bukti: 001 L17.

### E.3 `doctor_profiles` — `User` melalui `approved_by` : **0..\* : 0..1**

- Satu admin dapat menyetujui/menolak **nol atau banyak** profil dokter.
- Satu profil dokter memiliki **nol atau satu** admin penyetuju (kolom nullable).
- Bukti: 007 L33; penggunaan di `admin_service.py` L192 dan L288.

Relasi ini digambarkan sebagai polyline dari sisi kiri baris `approved_by` pada `doctor_profiles` menuju sisi kiri `User`, dengan label nama `approved_by` (italic, berputar) serta label kardinalitas `0..*` di dekat `User` dan `0..1` di dekat `doctor_profiles`. Arah pembacaan mengikuti konvensi: sisi `User` adalah "satu admin", sisi `doctor_profiles` adalah "banyak profil".

---

## F. Hubungan Data dengan Fitur PIXEL-T

| Fitur | Operasi data | Entitas/atribut yang terlibat |
|---|---|---|
| **Sign Up** | `auth.users` dibuat; trigger `handle_new_doctor_signup` menyisipkan `doctor_profiles` (`role='doctor'`, `account_status='pending'`) | User, doctor_profiles, trigger 008 |
| **Sign In** | Membaca sesi dan `doctor_profiles.role`/`account_status` | User, doctor_profiles |
| **Upload Image** | Menyisipkan baris `analyses` (`user_id`, `status='processing'`, path aset) | analyses, Storage |
| **Segmentation** | Memperbarui status, path artefak, metrik, progres, `completed_at` | analyses |
| **History** | Membaca dan menghapus baris `analyses` milik pengguna beserta file Storage | analyses, Storage |
| **Doctor Profile** | Upsert profil berdasarkan `user_id`; menyimpan `avatar_url` | doctor_profiles, Storage `profile-avatars` |
| **Sign Out** | Mengakhiri sesi Supabase Auth; tidak mengubah data | — |
| **Admin Approval** (pendukung) | Menulis `account_status`, `approved_by`, `approved_at`, `rejection_reason` | doctor_profiles, User (`approved_by`) |

---

## G. Keputusan Desain

1. **Tiga entitas saja.** Hanya tabel relasional PostgreSQL yang menjadi entitas. Controller, service, repository, endpoint, dan pipeline AI adalah komponen perangkat lunak, bukan entitas data.
2. **Storage bukan entitas.** Bucket `analysis-assets` dan `profile-avatars` menyimpan objek berkas, bukan baris relasional; keberadaannya dijelaskan sebagai atribut path/URL pada tabel (`original_image_path`, `binary_mask_path`, `avatar_url`, dan seterusnya).
3. **Supabase Auth diwakili seperlunya.** Hanya lima kolom `auth.users` yang relevan bagi model aplikasi yang ditampilkan; kolom internal Auth lainnya tidak ditampilkan agar diagram tetap terbaca.
4. **FK sekunder tetap digambar.** `approved_by` adalah FK fisik yang aktif dipakai; menghilangkannya dari garis relasi akan membuat diagram tidak lengkap. Revisi audited menambahkannya secara eksplisit tanpa mengubah entitas/atribut lain.
5. **Satu sumber generator.** Berkas `.drawio`, `.png`, dan `.svg` dihasilkan dari satu model (`_build_erd_final_audited.js`) sehingga ketiganya konsisten.

---

## H. Keterbatasan

1. Verifikasi dilakukan terhadap migration dan source code (analisis statis), bukan terhadap skema Supabase *live* melalui kredensial. Hal ini disengaja agar audit tidak mengubah atau membocorkan data.
2. Tidak tersedia uji E2E berbasis browser untuk alur penuh; pengujian yang ada bersifat unit (backend Python dan frontend Vitest).
3. Berkas `ERD_PIXELT_FINAL.puml` merupakan artefak lama dan **tidak** konsisten dengan versi drawio/PNG/SVG (jumlah atribut lebih sedikit, `user_metadata`, tanpa `approved_by`); berkas ini sebaiknya disinkronkan atau dihapus agar tidak menimbulkan ambiguitas.
4. Komentar migration 007 L17 menyebut `raw_user_meta_data.role = 'admin'`, sedangkan implementasi memakai `raw_app_meta_data.role`; ini adalah ketidaktepatan dokumentasi kode, bukan kesalahan desain ERD.

---

## I. Kesimpulan Akademik

ERD PIXEL-T versi audited memenuhi syarat sebagai model data fisik Bab IV:

- **Lengkap:** tiga tabel aplikasi/eksternal yang relevan, 73 atribut, tiga foreign key, dan seluruh constraint utama.
- **Akurat:** setiap elemen dapat dilacak ke migration 001–008 dan source code.
- **Konsisten:** drawio, PNG, dan SVG dihasilkan dari satu sumber; kardinalitas sesuai constraint (`0..1` untuk UNIQUE, `*` untuk non-UNIQUE).
- **Siap pakai:** relasi `approved_by` sudah tampil sebagai garis, sehingga proses persetujuan admin yang nyata tidak lagi hanya tersirat sebagai atribut.

Dengan demikian, ERD layak digunakan pada Bab IV skripsi dengan status **LULUS DENGAN CATATAN** (catatan dokumen `.puml` dan komentar migration 007 L17), sebagaimana dirinci pada `AUDIT_INDEPENDEN_ERD_PIXELT_FINAL.md`.

---

## J. Catatan Publikasi

Gambar yang disarankan untuk dimasukkan ke naskah adalah **`ERD_PIXELT_FINAL_AUDITED.png`** (2560×1800 px, skala 2×, latar putih, garis hitam) agar tampil tajam pada media cetak maupun digital, dengan keterangan gambar sesuai penomoran Bab IV (misalnya **Gambar 4.1**). Versi `.svg` disediakan untuk kebutuhan vektor, dan `.drawio` untuk penyuntingan lebih lanjut.

---
*Dokumen ini merupakan bagian dari audit independen ERD PIXEL-T. Tidak memuat kredensial, token, atau data rahasia.*