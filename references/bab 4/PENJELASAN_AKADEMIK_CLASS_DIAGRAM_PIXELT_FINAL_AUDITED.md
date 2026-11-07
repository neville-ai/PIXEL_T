# PENJELASAN AKADEMIK CLASS DIAGRAM PIXEL-T (VERSI AUDITED)

Bab IV — Sistem Informasi Web PIXEL-T

---

## Pendahuluan

Class Diagram pada Gambar 4.x menggambarkan struktur statis sistem aplikasi web PIXEL-T (Polip USG Segmentasi dengan Transfer Learning dan Explainable AI). Diagram ini dihasilkan melalui audit menyeluruh terhadap source code aplikasi, termasuk frontend React, backend Flask, database PostgreSQL/Supabase, serta pipeline AI berbasis PyTorch. Diagram ini menyajikan abstraksi kelas, atribut, operasi, dan relasi yang mewakili tanggung jawab komponen utama dalam arsitektur sistem.

Pembagian kelas dalam diagram mengikuti standar stereotipe UML: `<<module>>` untuk modul frontend dan AI, `<<service>>` untuk lapisan layanan backend, `<<controller>>` untuk pengendali HTTP, `<<repository>>` untuk lapisan akses data, `<<entity>>` untuk entitas basis data, `<<external>>` untuk layanan eksternal, dan `<<exception>>` untuk kelas penanganan kesalahan.

Diagram ini menggunakan latar belakang putih dengan garis dan teks hitam, serta font formal (Segoe UI) untuk memenuhi standar visual skripsi yang sederhana, bersih, dan mudah dibaca.

---

## Struktur Kelas

Class Diagram Gambar 4.x terdiri dari 19 kelas yang dikelompokkan menjadi lima lapisan:

### 1. Lapisan Presentasi (Frontend)

**AuthContext** (`<<module>>`) adalah pengelola estado autentikasi di sisi klien. Kelas ini menyimpan informasi pengguna yang sedang login, meliputi objek `user`, `session`, `role` (admin atau doctor), dan `accountStatus` (pending, approved, atau rejected). Operasi utama meliputi `signIn`, `signUp`, dan `signOut`. AuthContext berkomunikasi dengan Supabase Auth melalui klien autentikasi.

**DoctorProfileService** (`<<module>>`) adalah modul layanan frontend untuk pengelolaan profil dokter. Meliputi operasi upsert profil, pengambilan data profil, dan perhitungan statistik dokter.

**AnalysisClient** (`<<module>>`) adalah modul layanan frontend untuk berkomunikasi dengan backend melalui REST API. Meliputi operasi pembuatan analisis, pengambilan detail analisis, daftar riwayat, dan penghapusan analisis.

### 2. Lapisan Kontroler (Backend)

**AnalysisController** (`<<controller>>`) adalah pengendali HTTP untuk endpoint analisis, meliputi `POST /api/analysis` (upload gambar), `GET /api/analysis/:id` (detail analisis), `GET /api/history` (daftar riwayat), dan `DELETE /api/history/:id` (penghapusan analisis).

**AdminController** (`<<controller>>`) adalah pengendali HTTP untuk endpoint administrasi, meliputi `GET /api/admin/doctors` (daftar dokter), `GET /api/admin/doctors/stats` (statistik), `GET /api/admin/doctors/:id` (detail dokter), `POST /api/admin/doctors/:id/approve` (setuju registrasi), dan `POST /api/admin/doctors/:id/reject` (tolak registrasi).

### 3. Lapisan Layanan (Backend Services)

**AnalysisService** (`<<service>>`) adalah layanan inti backend yang mengorkestrasi alur analisis citra. Bertanggung jawab untuk membuat rekaman analisis, mengunggah berkas asli ke Storage, memanggil pipeline AI, dan memperbarui status analisis.

**AdminService** (`<<service>>`) adalah layanan backend untuk manajemen registrasi dokter. Bertanggung jawab untuk menampilkan daftar dokter, menyetujui, menolak, serta menghasilkan statistik registrasi.

**StorageService** (`<<service>>`) adalah layanan backend untuk operasi Supabase Storage, meliputi unggah berkas, pembuatan URL tertanda waktu (signed URL), dan penghapusan berkas analisis.

### 4. Lapisan Akses Data (Repository)

**AnalysisRepository** (`<<repository>>`) adalah lapisan akses data untuk tabel `analises`. Meliputi operasi CRUD, filter berdasarkan pengguna, pembaruan status, dan validasi siklus hidup status analisis.

### 5. Entitas Basis Data

**doctor_profiles** (`<<entity>>`) adalah tabel yang menyimpan profil dokter, termasuk informasi pribadi dan profesional, serta kolom `role` dan `account_status` untuk manajemen akses.

**analyses** (`<<entity>>`) adalah tabel yang menyimpan rekaman analisis citra endoskopi, termasuk status proses, hasil segmentasi, data Grad-CAM, dan metadata model AI.

### 6. Layanan Eksternal

**SupabaseAuth** (`<<external>>`) adalah layanan autentikasi eksternal dari Supabase yang menyediakan manajemen pengguna, sesi, dan app_metadata untuk identifikasi role admin.

### 7. Pipeline AI

**AISegmentationPipeline** (`<<module>>`) adalah modul pipeline inferensi AI yang menghasilkan mask segmentasi, overlay, dan visualisasi Grad-CAM dari citra endoskopi input.

**ModelService** (`<<service>>`) adalah layanan pemuat model U-Net dengan encoder ResNet-50 yang digunakan oleh pipeline AI untuk inferensi.

**ModelConfig** (`<<module>>`) adalah konfigurasi terverifikasi model AI, termasuk arsitektur, encoder, threshold, dan parameter TTA.

**PipelineResult**, **SegmentationResult**, dan **GradCAMResult** (`<<dataclass>>`) adalah struktur data hasil pipeline AI yang berisi citra hasil, heatmap, overlay, dan pengukuran area segmentasi.

### 8. Penanganan Kesalahan

**APIError** (`<<exception>>`) adalah kelas exception dengan struktur kode kesalahan, pesan, dan status code HTTP untuk respons standar backend.

---

## Relasi Antarclass

Relasi dalam diagram menggambarkan ketergantungan dan hubungan antarkomponen:

1. **AuthContext — SupabaseAuth** (Association, 1 : 1): AuthContext menggunakan layanan Supabase Auth untuk autentikasi dan pengambilan informasi role pengguna.

2. **AdminService — doctor_profiles** (Association, 1 : *): AdminService mengelola banyak entitas profil dokter melalui operasi CRUD.

3. **AdminService — APIError** (Dependency, dashed): AdminService melempar pengecualian APIError pada kegagalan operasi.

4. **AnalysisService — AnalysisController** (Association, 1 : 1): AnalysisController mendelegasikan permintaan HTTP ke AnalysisService.

5. **AnalysisService — AnalysisRepository** (Association, 1 : 1): AnalysisService menggunakan repository untuk operasi persisten data analisis.

6. **AnalysisService — StorageService** (Association, 1 : 1): AnalysisService menggunakan StorageService untuk unggah dan pengambilan berkas aset.

7. **AnalysisService — AISegmentationPipeline** (Association, 1 : 1): AnalysisService memanggil pipeline AI untuk pemrosesan segmentasi citra.

8. **AnalysisService — APIError** (Dependency, dashed): AnalysisService melempar pengecarian APIError pada kegagalan operasi.

9. **DoctorProfileService — doctor_profiles** (Association, 1 : 1): DoctorProfileService mengelola data profil dokter melalui Supabase.

10. **AnalysisClient — AnalysisController** (Association, 1 : 1): AnalysisClient mengirim permintaan HTTP ke controller analisis melalui API.

11. **AISegmentationPipeline — ModelService** (Association, 1 : 1): Pipeline AI menggunakan ModelService untuk pemuatan dan inferensi model.

12. **AISegmentationPipeline — ModelConfig** (Association, 1 : 1): Pipeline AI menggunakan konfigurasi model untuk parameter inferensi.

13. **doctor_profiles — SupabaseAuth** (Association, 1 : 0..1): Setiap profil dokter terhubung dengan tepat satu pengguna Supabase Auth melalui `user_id` (foreign key). Sebaliknya, satu pengguna mungkin memiliki nol atau satu profil dokter (admin tidak memiliki profil dokter).

14. **analyses — SupabaseAuth** (Association, 1 : *): Setiap rekaman analisis terhubung dengan tepat satu pengguna melalui `user_id`. Sebaliknya, satu pengguna dapat memiliki banyak rekaman analisis.

15. **AISegmentationPipeline — PipelineResult** (Association, 1 : 1): Pipeline menghasilkan satu objek hasil akhir.

16. **PipelineResult — SegmentationResult** (Association, 1 : 1): Hasil pipeline mencakup satu hasil segmentasi.

17. **PipelineResult — GradCAMResult** (Association, 1 : 1): Hasil pipeline mencakup satu hasil Grad-CAM.

---

## Pemodelan Role Admin dan Dokter

Berdasarkan implementasi aktual, Admin dan Dokter **tidak dimodelkan sebagai subclass** dari satu kelas induk. Kedua peran dibedakan melalui mekanisme berikut:

- **Admin**: role disimpan di `auth.users.raw_app_meta_data.role = 'admin'` (server-write-only melalui Supabase Admin API). Admin tidak memiliki baris di tabel `doctor_profiles`. Frontend AuthContext membaca `app_metadata.role` sebagai sumber kebenaran utama.
- **Dokter**: role disimpan di `doctor_profiles.role = 'doctor'` dengan `account_status` bernilai `pending`, `approved`, atau `rejected`. Dokter memiliki baris di tabel `doctor_profiles` yang dibuat otomatis oleh trigger database setelah signup.

Pendekatan ini menghindari pewarisan kelas yang tidak didukung oleh implementasi dan mencerminkan bahwa peran adalah atribut metadata, bukan hierarki kelas.

---

## Kesimpulan

Class Diagram Gambar 4.x merupakan representasi yang akurat terhadap struktur perangkat lunak PIXEL-T berdasarkan implementasi source code. Setiap kelas, atribut, operasi, dan relasi memiliki dasar bukti yang dapat ditelusuri ke file implementasi. Diagram ini konsisten dengan ERD, Use Case Diagram, Activity Diagram, dan Sequence Diagram yang ada, serta menggambarkan pembagian tanggung jawab antara frontend, backend, layanan eksternal, dan pipeline AI dengan tepat.
