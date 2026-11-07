# Penjelasan Akademik ERD PIXEL-T Final (Reaudited)

**Versi:** 4.0 (revisi berdasarkan audit menyeluruh)  
**Tanggal:** 5 November 2026  
**Untuk:** Bab IV Skripsi S1  
**Gambar acuan:** `ERD_PIXELT_FINAL_AUDITED.png` (2560 × 1800 px)  
**Direktori:** `references/bab 4/`

---

## A. Pendahuluan

Entity Relationship Diagram (ERD) ini menggambarkan struktur data logis dan fisik sistem web **PIXEL-T** (*Pixel-based Tumor Analysis Tool*), aplikasi analisis citra endoskopi/kolonoskopi berbasis kecerdasan buatan yang dibangun dengan React (frontend), Flask/Python (backend), dan Supabase (PostgreSQL, Authentication, dan Storage).

ERD disusun berdasarkan delapan berkas migration SQL (`database/migrations/001–008.sql`) sebagai sumber kebenaran struktur database, dilengkapi dengan verifikasi terhadap source code backend dan frontend yang benar-benar membaca dan menulis tabel. Dengan demikian, setiap entitas, atribut, primary key, foreign key, relasi, dan kardinalitas pada diagram dapat ditelusuri ke bukti implementasi tertentu.

Pada gambar terdapat tiga entitas utama: **`User (auth.users)`**, **`doctor_profiles`**, dan **`analyses`**, yang saling terhubung melalui relasi bertanda kardinalitas.

---

## B. Tujuan ERD

1. Menjelaskan struktur penyimpanan data sistem PIXEL-T secara ringkas dan akurat.
2. Menjadi acuan visual model data fisik pada Bab IV skripsi.
3. Menunjukkan bagaimana tiga entitas mendukung seluruh alur fungsional aplikasi, yaitu pendaftaran, masuk, unggah gambar, segmentasi, riwayat, profil dokter, dan keluar.
4. Menjadi dasar penjelasan penggunaan Supabase Auth dan Supabase Storage dalam sistem.

---

## C. Entitas dan Atribut

ERD memuat **3 entitas** dan **73 atribut**, dibagi sebagai berikut.

### C.1 Entitas `User (auth.users)` — 5 atribut

Entitas ini mewakili akun pengguna yang dikelola oleh **Supabase Auth**. `auth.users` adalah tabel eksternal milik platform Supabase, bukan tabel yang dibuat oleh aplikasi PIXEL-T; penulisan `User (auth.users)` pada nama entitas dimaksudkan untuk menegaskan pemisahan antara skema `auth` (milik platform) dan skema `public` (milik aplikasi).

| Atribut | Tipe | Keterangan |
|---|---|---|
| `id` | uuid (PK) | Identitas pengguna; menjadi sasaran seluruh foreign key aplikasi |
| `email` | varchar | Alamat email akun |
| `raw_user_meta_data` | jsonb | Metadata pendaftaran yang diisi pengguna saat mendaftar, misalnya `full_name`, `hospital`, dan `primary_specialty` |
| `raw_app_meta_data` | jsonb | Metadata tepercaya yang hanya dapat ditulis server; memuat `role = 'admin'` untuk akun administrator |
| `created_at` | timestamptz | Waktu pembuatan akun |

**Catatan:** kelima atribut tersebut adalah kolom `auth.users` yang relevan bagi model aplikasi. Kolom internal Supabase Auth lainnya bersifat operasional dan tidak ditampilkan agar diagram tetap terbaca. Metadata pada `raw_user_meta_data` dan `raw_app_meta_data` disajikan sebagai kolom bertipe `jsonb`, bukan sebagai kolom terpisah, karena struktur isinya dinamis dan tidak dibatasi oleh constraint tetap.

### C.2 Entitas `doctor_profiles` — 29 atribut

Tabel ini menyimpan profil klinisi dan status tata kelola akun. Setiap baris dimiliki oleh tepat satu akun pengguna melalui `user_id`. Secara kelompok, atributnya adalah:

1. **Identitas:** `id` (PK), `user_id` (FK, UNIQUE).
2. **Data pribadi:** `full_name`, `phone`, `birth_date`, `city`, `avatar_url`.
3. **Data profesional:** `profession_category`, `academic_title`, `primary_specialty`, `subspecialty`, `clinical_focus`, `hospital`, `department`, `clinical_role`, `years_experience`, `practice_address`, `str_number`, `is_verified`.
4. **Biografi dan daftar terstruktur:** `bio`, `education` (jsonb), `experience` (jsonb).
5. **Tata kelola akun:** `role`, `account_status`, `approved_by`, `approved_at`, `rejection_reason`.
6. **Waktu:** `created_at`, `updated_at`.

Tabel `analyses` juga menyimpan `created_at` dan `updated_at` sebagai penanda waktu konsisten dengan tabel di atas.

### C.3 Entitas `analyses` — 39 atribut

Tabel ini menyimpan metadata hasil analisis citra milik pengguna. Kelompok atributnya meliputi:

1. **Identitas dan kepemilikan:** `id` (PK), `user_id` (FK).
2. **Lifecyle analisis:** `status` dengan nilai `processing`, `completed`, `failed`, serta `current_step`, `progress_percent`, `created_at`, `completed_at`, `updated_at`.
3. **Metadata citra asli:** `original_image_path`, `original_filename`, `original_mime_type`, `original_width`, `original_height`.
4. **Hasil segmentasi:** `binary_mask_path`, `segmentation_overlay_path`, `segmentation_status`, `area_pixels`, `area_ratio`, `bounding_width_pixels`, `bounding_height_pixels`.
5. **Grad-CAM (penjelasan model):** `gradcam_heatmap_path`, `gradcam_overlay_path`, `gradcam_target_layer`, `gradcam_method`, `gradcam_config_version`, `gradcam_status`.
6. **Metadata model dan reproduksibilitas:** `model_architecture`, `model_version`, `model_config_version`, `model_input_size`, `model_threshold`, `model_checkpoint_sha256`, `tta_enabled`, `tta_scales`, `tta_orientations`, `postprocessing_enabled`.
7. **Ringkasan dan error:** `summary_text`, `error_code`, `error_message`.

Hasil segmentasi dan Grad-CAM disimpan sebagai **path berkas pada Supabase Storage**, bukan sebagai blob dalam tabel, sehingga tabel tetap berisi metadata yang ringan.

---

## D. Primary Key dan Foreign Key

### D.1 Primary Key

| Tabel | Primary Key |
|---|---|
| `User (auth.users)` | `id` (uuid) — primary key bawaan Supabase Auth |
| `doctor_profiles` | `id` (uuid) — `gen_random_uuid()` |
| `analyses` | `id` (uuid) — `gen_random_uuid()` |

### D.2 Foreign Key

Terdapat **tiga foreign key fisik**, seluruhnya merujuk ke `auth.users(id)`:

1. **`doctor_profiles.user_id`** — NOT NULL, `ON DELETE CASCADE`, dengan constraint UNIQUE. Memastikan satu akun pengguna memiliki paling banyak satu profil dokter, dan setiap profil selalu memiliki pemilik.
2. **`analyses.user_id`** — NOT NULL, `ON DELETE CASCADE`, tanpa UNIQUE. Setiap analisis selalu dimiliki tepat satu pengguna, sedangkan satu pengguna dapat memiliki nol atau banyak analisis.
3. **`doctor_profiles.approved_by`** — nullable (dapat NULL), `REFERENCES auth.users(id)`. Menyimpan identitas akun administrator yang menyetujui atau menolak pendaftaran dokter. Ketika sebuah pendaftaran belum diproses atau tidak melalui persetujuan manual, nilai ini NULL.

Foreign key ketiga bukan atribut pasif: setiap kali admin menyetujui atau menolak pendaftaran, sistem menulis `approved_by` bersama `account_status` dan `approved_at`/`rejection_reason`. Karena itu, relasi ini digambar sebagai garis relasi eksplisit antara `doctor_profiles` dan `User (auth.users)`.

---

## E. Relasi dan Kardinalitas

### E.1 `User` — `doctor_profiles` : 1 : 0..1

- Setiap profil dokter terhubung ke **tepat satu** pengguna (`user_id` NOT NULL), ditandai label **1** pada sisi `User`.
- Satu pengguna memiliki **nol atau satu** profil dokter (`user_id` UNIQUE), ditandai label **0..1** pada sisi `doctor_profiles`.
- Kondisi `0..1` pada sisi pengguna juga mencerminkan akun administrator: sistem hanya membuat baris `doctor_profiles` untuk pendaftaran dokter, sedangkan akun administrator tidak memiliki baris profil dokter.

### E.2 `User` — `analyses` : 1 : *

- Setiap analisis dimiliki **tepat satu** pengguna (`user_id` NOT NULL), ditandai label **1** pada sisi `User`.
- Satu pengguna dapat memiliki **nol atau banyak** analisis (tidak ada UNIQUE), ditandai label **\*** pada sisi `analyses`.
- Label `*` dipilih karena tidak ada constraint yang mewajibkan setiap pengguna memiliki minimal satu analisis.

### E.3 `doctor_profiles` — `User` melalui `approved_by` : 0..* : 0..1

- Satu administrator dapat menyetujui **nol atau banyak** profil dokter, ditandai label **0..\*** pada sisi `User`.
- Satu profil dokter memiliki **nol atau satu** administrator penyetuju (kolom nullable), ditandai label **0..1** pada sisi `doctor_profiles`.
- Relasi ini digambar sebagai garis pada sisi kiri diagram, lengkap dengan label nama `approved_by`.

Ketiga relasi menggunakan notasi kardinalitas yang sama: angka `1` berarti tepat satu, `0..1` berarti nol atau satu, dan `*` berarti nol atau banyak.

---

## F. Hubungan dengan Supabase Auth dan Supabase Storage

### F.1 Supabase Auth

Supabase Auth mengelola akun pengguna pada tabel `auth.users`. Dalam aplikasi, platform ini berperan dalam:

1. **Pendaftaran (Sign Up):** aplikasi membuat akun melalui Supabase Auth sekaligus mengirimkan metadata pendaftaran. Sistem database kemudian otomatis membuat baris `doctor_profiles` dengan status `pending`.
2. **Masuk (Sign In):** aplikasi memperoleh sesi autentikasi, lalu membaca `role` dan `account_status` dari `doctor_profiles` untuk menentukan hak akses.
3. **Administrator:** peran admin ditetapkan melalui metadata internal `raw_app_meta_data`, sehingga hanya dapat diubah oleh administrator sistem, tidak oleh pengguna biasa.
4. **Keluar (Sign Out):** sesi diakhiri tanpa operasi apa pun pada tabel aplikasi.

ERD menampilkan `auth.users` sebagai entitas karena tabel tersebut menjadi sasaran seluruh foreign key sistem, meskipun pengelolaannya berada di luar aplikasi.

### F.2 Supabase Storage

Supabase Storage digunakan untuk menyimpan berkas, bukan baris data. Penggunaannya:

1. **Bucket `analysis-assets`** (bersifat privat) menyimpan citra asli, mask segmentasi, overlay segmentasi, dan visualisasi Grad-CAM.
2. **Bucket `profile-avatars`** (bersifat publik) menyimpan foto profil dokter.
3. Setiap objek diakses melalui path yang mencantumkan pemiliknya, misalnya `analysis/{user_id}/{analysis_id}/...` untuk aset analisis dan `{user_id}/profile.{ext}` untuk avatar.

Karena bucket bukan tabel relasional, ERD tidak menampilkannya sebagai entitas. Hubungan antara record dan berkas diwakili oleh kolom path/URL: `original_image_path`, `binary_mask_path`, `segmentation_overlay_path`, `gradcam_heatmap_path`, dan `gradcam_overlay_path` pada `analyses`, serta `avatar_url` pada `doctor_profiles`.

---

## G. Hubungan Data dengan Fitur Aplikasi

| Fitur | Operasi data | Entitas/atribut yang terlibat |
|---|---|---|
| **Sign Up** | Akun dibuat di `auth.users`; sistem otomatis membuat `doctor_profiles` dengan `role = 'doctor'` dan `account_status = 'pending'` | User, `doctor_profiles.user_id`, `role`, `account_status` |
| **Sign In** | Sesi dibuat; `role` dan `account_status` dibaca dari `doctor_profiles` | User, `doctor_profiles` |
| **Upload Image** | Baris `analyses` dibuat dengan `status = 'processing'`; citra disimpan ke Storage | `analyses.user_id`, `original_image_path`, `status` |
| **Segmentation** | Status diperbarui menjadi `completed`/`failed`; path hasil, metrik, dan progres diisi | `analyses` (kolom segmentasi, Grad-CAM, model, progres) |
| **History** | Riwayat diambil berdasarkan pengguna dan waktu; detail dibuka; record dan berkas dihapus | `analyses.user_id`, `created_at`, path Storage |
| **Doctor Profile** | Profil dibaca dan disimpan (`upsert` berdasarkan `user_id`); avatar diunggah | `doctor_profiles`, `avatar_url` |
| **Sign Out** | Sesi diakhiri; tidak ada perubahan data | — |
| **Persetujuan Admin** (pendukung) | `account_status` diubah menjadi `approved`/`rejected` disertai `approved_by`, `approved_at`, `rejection_reason` | `doctor_profiles`, relasi `approved_by` |

---

## H. Keputusan Desain Pemodelan

1. **Tabel aplikasi sebagai entitas.** Hanya tabel relasional yang dijadikan entitas. Komponen perangkat lunak seperti controller, service, repository, endpoint, dan pipeline AI tidak dimodelkan sebagai entitas karena bukan entitas data.
2. **Storage bukan entitas.** Bucket berkas diwakili melalui atribut path/URL pada tabel agar diagram tetap menjadi ERD yang sah.
3. **Supabase Auth ditampilkan seperlunya.** Hanya kolom `auth.users` yang relevan bagi model aplikasi yang ditampilkan.
4. **Relasi foreign key digambar lengkap.** Ketiga foreign key sistem digambar sebagai relasi garis, termasuk `approved_by` yang aktif digunakan pada proses persetujuan admin.
5. **Kardinalitas diturunkan dari constraint.** `0..1` ditetapkan karena adanya UNIQUE, `*` ditetapkan karena tidak ada UNIQUE, dan `0..*` ditetapkan karena kolom relasi bersifat nullable tanpa batas jumlah.

---

## I. Keterbatasan

1. Verifikasi struktur dilakukan terhadap migration SQL dan source code (analisis statis), bukan terhadap database produksi secara langsung.
2. Penjelasan ini memuat informasi struktural yang didukung bukti; detail audit teknis disimpan dalam dokumen terpisah, yaitu `AUDIT_INDEPENDEN_MENYELURUH_ERD_PIXELT_FINAL_AUDITED.md`.

---

## J. Kesimpulan

ERD PIXEL-T versi reaudited memenuhi syarat sebagai model data fisik pada Bab IV skripsi:

- **Lengkap:** tiga entitas relevan, 73 atribut, tiga foreign key, serta seluruh constraint utama.
- **Akurat:** setiap elemen dapat ditelusuri ke migration 001–008 dan source code.
- **Konsisten:** kardinalitas seluruh relasi diturunkan langsung dari constraint (UNIQUE, NOT NULL, nullable).
- **Relevan:** seluruh alur fungsional aplikasi, termasuk persetujuan admin, tercermin dalam diagram.

Dengan demikian, **`ERD_PIXELT_FINAL_AUDITED.png` layak digunakan sebagai gambar ERD pada Bab IV skripsi**, dengan penomoran gambar sesuai naskah (misalnya **Gambar 4.x**). Versi `.svg` tersedia untuk kebutuhan vektor dan `.drawio` untuk penyuntingan lebih lanjut.

---

*Penjelasan ini merupakan bagian dari hasil audit independen ERD PIXEL-T dan tidak memuat kredensial, token, atau data rahasia.*
