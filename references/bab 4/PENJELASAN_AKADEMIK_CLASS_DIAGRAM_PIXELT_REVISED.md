# PENJELASAN AKADEMIK CLASS DIAGRAM PIXEL-T (VERSI FINAL_REVISED)

Bab IV — Sistem Informasi Web PIXEL-T: Polip USG Segmentasi dengan Transfer Learning dan Explainable AI

---

## Pendahuluan

Class Diagram pada Gambar 4.x menggambarkan struktur statis sistem aplikasi web PIXEL-T (Polip USG Segmentasi dengan Transfer Learning dan Explainable AI). Diagram ini dihasilkan melalui audit menyeluruh terhadap seluruh source code aplikasi, termasuk frontend React (TypeScript), backend Flask (Python), database PostgreSQL/Supabase (migration SQL), serta pipeline AI berbasis PyTorch. Diagram ini menyajikan abstraksi kelas, atribut, operasi, dan relasi yang mewakili tanggung jawab komponen utama dalam arsitektur sistem.

Pembagian kelas dalam diagram mengikuti standar stereotipe UML: `<<module>>` untuk modul frontend dan AI, `<<controller>>` untuk pengendali HTTP, `<<service>>` untuk lapisan layanan backend, `<<repository>>` untuk lapisan akses data, `<<entity>>` untuk entitas basis data, `<<external>>` untuk layanan eksternal, dan `<<exception>>` untuk kelas penanganan kesalahan.

Diagram ini menggunakan latar belakang putih dengan garis dan teks hitam, serta font Segoe UI berukuran 11 pt, sesuai standar visual contoh diagram kelas (`class_diagram_contoh.png`).

---

## 1. Gambaran Umum Arsitektur

PIXEL-T mengadopsi arsitektur yang terdiri dari lima kolom logis (lihat diagram):

| Kolom | Komponen | Tanggung Jawab |
|-------|----------|----------------|
| **Kolom 1: Frontend Modules** | `AuthContext`, `AnalysisClient`, `DoctorProfileService` | State management autentikasi, klien REST API, dan layanan profil dokter di sisi klien |
| **Kolom 2: Controllers** | `AnalysisController`, `AdminController` | Pengendali endpoint HTTP untuk analisis dan manajemen dokter |
| **Kolom 3: Services** | `AnalysisService`, `AdminService`, `StorageService`, `APIError` | Lápis bisnis: orkestrasi analisis, operasi admin, penyimpanan asset, dan penanganan kesalahan |
| **Kolom 4: Repository + AI Pipeline** | `AnalysisRepository`, `AISegmentationPipeline` | Akses data ke Supabase dan eksekusi pipeline AI (segmentasi + Grad-CAM) |
| **Kolom 5: External + DB** | `SupabaseAuth`, `doctor_profiles`, `analyses` | Layanan eksternal (Supabase Auth) dan entitas basis data |

Semua kolom saling terhubung melalui 14 relasi yang mewakili interaksi antar-komponen dalam runtime sistem.

---

## 2. Rincian 14 Kelas

### 2.1 AuthContext (`<<module>>`)

**AuthContext** adalah modul React yang mengelola state autentikasi aplikasi. Kelas ini menyimpan `user`, `session`, `role`, dan `accountStatus`, serta menyediakan operasi `signIn()`, `signUp()`, dan `signOut()`. Dalam sistem PIXEL-T, `AuthContext` berperan sebagai pusat state manajemen autentikasi yang memastikan setiap halaman klinis diakses hanya oleh pengguna yang berhak.

**Atribut:**
- `user: User` — Objek pengguna Supabase Auth
- `session: Session` — Sesi aktif pengguna
- `role: String` — Peran pengguna (`'admin'` atau `'doctor'`)
- `accountStatus: String` — Status akun dokter (`'pending'`, `'approved'`, `'rejected'`)

**Operasi:**
- `signIn(email, password)` — Memverifikasi kredensial login
- `signUp(...)` — Mendaftarkan akun dokter baru
- `signOut()` — Mengakhiri sesi pengguna

### 2.2 AnalysisClient (`<<module>>`)

**AnalysisClient** adalah modul TypeScript yang berfungsi sebagai klien REST API untuk operasi analisis. Kelas ini berkomunikasi dengan backend Flask melalui endpoint HTTP untuk membuat, mengambil, dan menghapus data analisis.

**Operasi:**
- `createAnalysis(file)` — Mengunggah gambar USG untuk dianalisis
- `getAnalysis(id)` — Mengambil detail analisis berdasarkan ID
- `listHistory()` — Mendaftarkan riwayat analisis pengguna
- `deleteAnalysis(id)` — Menghapus data analisis

### 2.3 DoctorProfileService (`<<module>>`)

**DoctorProfileService** adalah modul TypeScript yang mengelola data profil dokter melalui Supabase. Kelas ini menyediakan operasi CRUD untuk profil klinis dokter, termasuk verifikasi kelengkapan data dan validasi input.

**Operasi:**
- `upsertProfile(data)` — Menyimpan atau memperbarui profil dokter
- `getProfile(user_id)` — Mengambil profil dokter berdasarkan user ID
- `deleteProfile(user_id)` — Menghapus profil dokter
- `calculateStats()` — Menghitung statistik profil

### 2.4 AnalysisController (`<<controller>>`)

**AnalysisController** adalah pengendali HTTP untuk endpoint analisis di backend Flask. Kelas ini menangani permintaan POST (unggah gambar), GET (detail dan riwayat), dan DELETE (hapus analisis).

**Operasi:**
- `create_analysis()` — Memproses unggah gambar dan membuat catatan analisis
- `get_analysis(analysis_id)` — Mengambil detail analisis
- `list_history()` — Mendaftarkan riwayat analisis
- `delete_analysis(analysis_id)` — Menghapus catatan analisis

### 2.5 AdminController (`<<controller>>`)

**AdminController** adalah pengendali HTTP untuk endpoint manajemen dokter (admin-only). Kelas ini menangani daftar dokter, detail dokter, persetujuan, penolakan, dan statistik registrasi.

**Operasi:**
- `list_doctors(status)` — Daftar semua dokter dengan opsi filter status
- `get_doctor(doctor_id)` — Detail lengkap satu profil dokter
- `approve_doctor(id)` — Menyetujui registrasi dokter
- `reject_doctor(id)` — Menolak registrasi dokter
- `get_statistics()` — Statistik agregat registrasi

### 2.6 AnalysisService (`<<service>>`)

**AnalysisService** adalah lapisan layanan backend yang meng orkestrasi alur analisis dari unggah gambar hingga hasil segmentasi dan Grad-CAM. Kelas ini berinteraksi dengan `AnalysisRepository`, `StorageService`, dan `AISegmentationPipeline`.

**Atribut:**
- `repository: AnalysisRepository` — Akses data analisis
- `storage_service: StorageService` — Penyimpanan asset gambar

**Operasi:**
- `create_analysis(file, user_id)` — Membuat catatan analisis dan mengunggah file
- `get_analysis(id, user_id)` — Mengambil detail analisis dengan verifikasi kepemilikan
- `list_user_analyses(user_id)` — Mendaftarkan semua analisis pengguna
- `delete_analysis(id, user_id)` — Menghapus analisis dengan verifikasi kepemilikan

### 2.7 AdminService (`<<service>>`)

**AdminService** adalah lapisan layanan backend untuk operasi administratif manajemen dokter. Kelas ini menggunakan klien Supabase service role untuk melintasi RLS (Row Level Security), karena otorisasi admin ditangani oleh decorator backend.

**Atribut:**
- `client: SupabaseClient` — Klien Supabase dengan hak akses service role

**Operasi:**
- `list_doctors(status)` — Mengambil daftar dokter dengan filter status
- `approve_doctor(id, approved_by)` — Menyetujui dokter dengan admin yang menyetujui
- `reject_doctor(id, approved_by, reason)` — Menolak dokter dengan alasan
- `get_statistics()` — Mengembalikan statistik agregat

### 2.8 StorageService (`<<service>>`)

**StorageService** adalah layanan yang menangani operasi penyimpanan asset di Supabase Storage. Kelas ini mengimplementasi pola folder ownership-aware: `analysis/{user_id}/{analysis_id}/{category}/{filename}`.

**Atribut:**
- `bucket_name: String` — Nama bucket Supabase Storage (`analysis-assets`)

**Operasi:**
- `upload_file(path, bytes, type)` — Mengunggah file ke bucket
- `create_signed_url(path, expires_in)` — Membuat URL tertanda waktu untuk akses aman
- `delete_analysis_files(paths)` — Menghapus file-file analisis

### 2.9 APIError (`<<exception>>`)

**APIError** adalah kelas pengecualian kustom dengan envelop error terstruktur. Kelas ini digunakan untuk mengembalikan respons error standar (code, message, status_code) ke klien.

**Atribut:**
- `code: String` — Kode error (mis. `MISSING_FILE`, `UNAUTHORIZED`)
- `message: String` — Pesan error deskriptif
- `status_code: Integer` — Kode status HTTP

**Operasi:**
- `to_dict()` — Mengonversi error ke dictionary JSON

### 2.10 AnalysisRepository (`<<repository>>`)

**AnalysisRepository** adalah lapisan akses data untuk tabel `analyses`. Kelas ini mengimplementasi CROD (Create, Read, Update, Delete) dengan enforce ownership dan constraint status lifecycle.

**Atribut:**
- `client: SupabaseClient` — Klien Supabase untuk akses basis data

**Operasi:**
- `create(record)` — Membuat catatan analisis baru
- `get_by_id(id)` — Mengambil analisis berdasarkan ID
- `list_by_user(user_id)` — Mendaftarkan analisis per pengguna
- `update_status(id, status)` — Memperbarui status lifecycle analisis
- `delete(id)` — Menghapus catatan analisis

### 2.11 AISegmentationPipeline (`<<module>>`)

**AISegmentationPipeline** adalah modul Python yang mengimplementasikan pipeline AI end-to-end untuk segmentasi polip USG dan generate Grad-CAM. Kelas ini membungkus fungsi-fungsi internal (`predict`, `generate_gradcam`, `postprocess_mask`, `measure_mask`) dan mengembalikan `PipelineResult`.

**Operasi:**
- `run_pipeline(original, config, on_phase, on_pass)` — Eksekusi pipeline lengkap
- `predict(image, model_service, config)` — Segmentasi polip
- `generate_gradcam(tensor, model_service)` — Visualisasi Grad-CAM

### 2.12 SupabaseAuth (`<<external>>`)

**SupabaseAuth** mewakili layanan eksternal Supabase Auth yang menyimpan identitas pengguna (`id: UUID`). Ini adalah sumber kebenaran untuk autentikasi dan otorisasi dalam sistem PIXEL-T.

**Atribut:**
- `id: UUID` — Primary key pengguna di Supabase Auth

### 2.13 doctor_profiles (`<<entity>>`)

**doctor_profiles** adalah entitas basis data yang menyimpan metadata profil dokter klinis. Tabel ini terkait satu-ke-satu (0..1) dengan `auth.users` melalui `user_id` yang memiliki constraint UNIQUE.

**Atribut:**
- `id: UUID` — Primary key
- `user_id: UUID` — Foreign key ke `auth.users(id)`, UNIQUE
- `full_name: String` — Nama lengkap dokter
- `primary_specialty: String` — Spesialisasi utama
- `hospital: String` — Rumah sakit tempat praktik
- `account_status: String` — Status: `pending`, `approved`, `rejected`
- `approved_by: UUID` — Admin yang menyetujui
- `approved_at: Timestamp` — Waktu persetujuan

### 2.14 analyses (`<<entity>>`)

**analyses** adalah entitas basis data yang menyimpan catatan analisis USG. Satu pengguna dapat memiliki banyak analisis (1:*).

**Atribut:**
- `id: UUID` — Primary key
- `user_id: UUID` — Foreign key ke `auth.users(id)`
- `status: String` — Lifecycle: `processing`, `completed`, `failed`
- `segmentation_status: String` — Status segmentasi
- `gradcam_status: String` — Status Grad-CAM
- `summary_text: String` — Ringkasan hasil analisis
- `created_at: Timestamp` — Waktu pembuatan
- `completed_at: Timestamp` — Waktu selesai

---

## 3. Rincian 14 Relasi

Diagram mencakup 14 relasi yang mewakili interaksi antar-komponen dalam sistem. Dua relasi kriteria FK telah diperbaiki multiplicity-nya (lihat bagian 5):

| # | Relasi | Tipe | Multiplicity | Deskripsi |
|---|--------|------|--------------|-----------|
| 1 | AuthContext → SupabaseAuth | Association | 1 : 1 | Satu konteks autentikasi terkait satu sesi Supabase Auth |
| 2 | AnalysisClient → AnalysisController | Association (HTTP) | 1 : 1 | Klien frontend memanggil satu controller backend |
| 3 | DoctorProfileService → doctor_profiles | Association (CRUD) | 1 : 1 | Layanan profil mengakses satu baris profil dokter |
| 4 | AnalysisController → AnalysisService | Association | 1 : 1 | Controller mendelegasikan ke satu service |
| 5 | AdminController → AdminService | Association | 1 : 1 | Controller admin mendelegasikan ke satu service admin |
| 6 | AnalysisService → AnalysisRepository | Association | 1 : 1 | Service menggunakan satu repository |
| 7 | AnalysisService → StorageService | Association | 1 : 1 | Service menggunakan satu layanan penyimpanan |
| 8 | AnalysisService → AISegmentationPipeline | Association | 1 : 1 | Service memanggil satu modul pipeline AI |
| 9 | AnalysisService → analyses | Association | 1 : * | Satu service mengelola banyak catatan analisis |
| 10 | AnalysisService ⤳ APIError | Dependency | — | Service dapat melempar pengecualian APIError |
| 11 | AdminService → doctor_profiles | Association | 1 : * | Admin service mengelola banyak profil dokter |
| 12 | AdminService ⤳ APIError | Dependency | — | Service admin dapat melempar pengecualian APIError |
| 13 | doctor_profiles → SupabaseAuth | Association (FK) | 1 : 0..1 | Satu profil dokter terkait satu pengguna; tidak semua pengguna (admin) memiliki profil dokter |
| 14 | analyses → SupabaseAuth | Association (FK) | 1 : * | Satu pengguna dapat memiliki banyak catatan analisis |

---

## 4. Pemodelan Role Admin dan Dokter (Tanpa Inheritance)

Salah satu keputusan desain penting dalam diagram ini adalah **tidak menggunakan inheritance** antara Admin dan Doctor. Sebaliknya, peran dibedakan melalui **metadata kolom**:

### 4.1 Admin Role
Role admin disimpan di `auth.users.raw_app_meta_data.role = 'admin'` melalui Supabase Admin API. Admin dibuat secara manual (tidak ada jalur pendaftaran publik), dan **tidak memiliki baris di `doctor_profiles`** (trigger 008 secara eksplisit melewatkan admin).

### 4.2 Doctor Role
Role dokter disimpan di `doctor_profiles.role = 'doctor'` dengan `account_status` enum (`pending` / `approved` / `rejected`). Setiap dokter memiliki maksimal satu baris di `doctor_profiles` (UNIQUE `user_id`).

### 4.3 Alasan Tidak Menggunakan Inheritance
1. **Keakuratan terhadap implementasi**: Kode sumber tidak menggunakan subclassing untuk membedakan admin dan dokter; keduanya adalah `auth.users` yang berbeda hanya melalui metadata.
2. **Keuntungan arsitektural**: Admin dan dokter memiliki atribut yang sangat berbeda. Admin tidak memiliki `full_name`, `primary_specialty`, `hospital`, atau `account_status` karena mereka tidak terdaftar sebagai dokter.
3. **Konsistensi dengan ERD**: ERD PIXEL-T hanya memiliki satu tabel `doctor_profiles` untuk profil dokter, tanpa tabel admin terpisah.

**Alur verifikasi peran di `AuthContext`:**
1. Pertama, periksa `app_metadata.role` (terpercaya, sisi server) → jika `'admin'`, pengguna adalah admin
2. Jika bukan admin, lakukan lookup ke `doctor_profiles` untuk mendapatkan `role` dan `account_status`

---

## 5. Perbaikan Multiplicity (Koreksi Kritis)

Dalam versi audit sebelumnya, dua relasi FK memiliki multiplicity yang salah. Perbaikan berikut telah dilakukan berdasarkan constraint basis data aktual:

### 5.1 Relasi #13: doctor_profiles → SupabaseAuth (1 : 0..1)

**Sebelum (salah):** 1 : 1  
**Sesudah (benar):** 1 : 0..1  

**Bukti:**
- Migration 004 L12: `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
- Migration 004 L46: `CONSTRAINT doctor_profiles_user_id_key UNIQUE (user_id)`
- Migration 008 L11-12: Trigger melewatkan admin (`raw_app_meta_data.role = 'admin'`)

**Analisis:** Karena `UNIQUE user_id`, satu pengguna dapat memiliki **maksimal satu** profil dokter. Namun, admin **tidak memiliki** profil dokter (dilewati oleh trigger). Oleh karena itu, di sisi `SupabaseAuth`, multiplicity adalah **0..1** (nol atau satu), bukan 1 (tepat satu).

### 5.2 Relasi #14: analyses → SupabaseAuth (1 : *)

**Sebelum (salah):** 1 : 1  
**Sesudah (benar):** 1 : *  

**Bukti:**
- Migration 001 L17: `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
- Tidak ada constraint `UNIQUE` pada `analyses.user_id`

**Analisis:** Satu pengguna (dokter) dapat membuat **banyak** catatan analisis (history). Oleh karena itu, di sisi `SupabaseAuth`, multiplicity adalah **\*** (nol atau lebih).

---

## 6. Alasan Penghapusan 7 Kelas Internal AI

Dalam versi `FINAL_AUDITED`, diagram mencakup 7 kelas internal AI yang telah **dihapus** dalam versi `FINAL_REVISED` karena merupakan detail implementasi, bukan komponen arsitektur tingkat tesis:

| Kelas Dihapus | File | Alasan Penghapusan |
|---------------|------|-------------------|
| `PipelineResult` | `ai/inference/pipeline.py` | Dataclass nilai balik internal, tidak diekspos ke API publik |
| `SegmentationResult` | `ai/inference/segmentation.py` | Dataclass internal untuk peta probabilitas dan mask biner |
| `GradCAMResult` | `ai/inference/gradcam.py` | Dataclass internal untuk heatmap dan overlay Grad-CAM |
| `ModelConfig` | `ai/config/model_config.py` | Konfigurasi model (architecture, encoder, threshold), bukan komponen sistem |
| `ModelService` | `ai/inference/model_service.py` | Singleton loader internal, dibungkus oleh `AISegmentationPipeline` |
| `AnalysisJobQueue` | `backend/app/services/analysis_service.py` | Manajemen antrean internal, tidak interface publik |
| `AnalysisProgressReporter` | `backend/app/services/analysis_service.py` | Pelacakan progres internal, tidak komponen arsitektur |

**Prinsip abtraction:** Class diagram tesis memodelkan **arsitektur sistem** (komponen, interface, alur data), bukan **struktur kode internal** (dataclass, helper, private class). Pipeline AI direpresentasikan sebagai satu modul `AISegmentationPipeline` yang mencakup seluruh fungsionalitas AI.

---

## 7. Konsistensi dengan Diagram Lain (Bab IV)

Class diagram ini konsisten dengan semua diagram arsitektur lainnya dalam Bab IV:

| Diagram | Konsistensi | Detail |
|---------|-------------|--------|
| **ERD** | ✅ | Tabel `doctor_profiles`, `analyses`, dan FK ke `auth.users` identik dengan class diagram |
| **Use Case Diagram** | ✅ | Actor Doctor dan Admin, use case Upload Image, Segmentation, History, Manage Doctor, Sign In/Up |
| **Activity Diagram (Sign In)** | ✅ | Flow: AuthContext → SupabaseAuth → doctor_profiles lookup |
| **Activity Diagram (Sign Up)** | ✅ | Flow: AuthContext → SupabaseAuth → trigger 008 → doctor_profiles |
| **Sequence Diagram (Sign In)** | ✅ | AuthContext ↔ SupabaseAuth ↔ doctor_profiles |
| **Sequence Diagram (Sign Up)** | ✅ | AuthContext ↔ SupabaseAuth → trigger → doctor_profiles |
| **Sequence Diagram (Upload)** | ✅ | AnalysisClient → AnalysisController → AnalysisService → StorageService → analyses |

---

## 8. Verifikasi 7 Flow Utama (End-to-End)

Setiap flow utaman dalam sistem PIXEL-T telah diverifikasi terhadap class diagram:

| Flow | Urutan Komponen | Bukti Kode |
|------|-----------------|------------|
| **1. Sign Up (Dokter)** | `AuthContext` → `SupabaseAuth` → trigger 008 → `doctor_profiles` | `AuthContext.tsx` L25-33, migration 008 |
| **2. Sign In (Dokter/Admin)** | `AuthContext` → `SupabaseAuth` → `doctor_profiles` (role lookup) | `AuthContext.tsx` L40-60, `auth.ts` L180, L200 |
| **3. Upload Image** | `AnalysisClient` → `AnalysisController` → `AnalysisService` → `StorageService` → `analyses` | `analysis.ts` L57, `analysis_controller.py` L13, `analysis_service.py` L180 |
| **4. Segmentasi AI** | `AnalysisService` → `AISegmentationPipeline` (`predict()`) | `analysis_service.py` L580, `pipeline.py` L65 |
| **5. Grad-CAM** | `AnalysisService` → `AISegmentationPipeline` (`generate_gradcam()`) | `analysis_service.py` L640, `pipeline.py` L115 |
| **6. History** | `AnalysisClient` → `AnalysisController` → `AnalysisService` → `AnalysisRepository` → `analyses` | `analysis.ts` L78, `analysis_repository.py` L95 |
| **7. Doctor Profile CRUD** | `DoctorProfileService` → `doctor_profiles` | `profile.ts` L115, L270, migration 004 |

---

## 9. Kesimpulan

Class Diagram `CLASS_DIAGRAM_PIXELT_FINAL_REVISED` merupakan representasi akurat, bersih, dan akademik dari arsitektur sistem PIXEL-T. Diagram ini:

1. **Akurat**: 14 kelas dan 14 relasi diverifikasi 100% terhadap source code dan constraint basis data
2. **Benar Multiplicity**: 2 FK kriteria diperbaiki (0..1 dan *) berdasarkan constraint UNIQUE dan trigger database
3. **Jernih Visual**: Grid 5 kolom tanpa overlap, latar belakang putih, garis hitam, font Segoe UI 11 pt
4. **Standar UML**: Stereotipe konsisten, connector orthogonal, label multiplicity jelas
5. **Konsisten Lintas Diagram**: Selaras dengan ERD, Use Case, Activity, dan Sequence diagram dalam Bab IV
6. **Abstraksi Tepat**: Hanya komponen arsitektur, tanpa detail implementasi internal AI

Diagram ini siap digunakan sebagai lampiran formal dalam Bab IV tesis PIXEL-T.

---

**Disusun untuk Tesis PIXEL-T**  
**Tanggal:** 5 November 2026  
**Lokasi:** `references/bab 4/PENJELASAN_AKADEMIK_CLASS_DIAGRAM_PIXELT_REVISED.md`