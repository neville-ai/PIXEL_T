# PENJELASAN AKADEMIK CLASS DIAGRAM PIXEL-T FINAL

**Gambar 4.x** — Class Diagram Aplikasi Web PIXEL-T (Versi Final)

---

## 4.x.1 Pendahuluan

Class Diagram merupakan salah satu diagram dalam Unified Modeling Language (UML) yang menggambarkan struktur statis dari sistem perangkat lunak. Diagram ini menampilkan kelas, atribut, operasi, serta hubungan antarkelas yang merepresentasikan arsitektur aplikasi. Dalam konteks skripsi ini, Class Diagram digunakan untuk menjelaskan struktur komponen aplikasi web PIXEL-T yang merupakan sistem pendeteksi segmentasi citra medis berbasis kecerdasan buatan dengan dukungan dua peran pengguna, yaitu Admin dan Dokter.

Class Diagram ini disusun berdasarkan implementasi aktual dari source code aplikasi PIXEL-T, baik sisi frontend (React + TypeScript), backend (Flask + Python), maupun lapisan inferensi AI (PyTorch). Setiap elemen dalam diagram telah diverifikasi terhadap kode sumber aktual sehingga diagram ini akurat dan dapat dipertanggungjawabkan secara akademik.

---

## 4.x.2 Kerangka Pemodelan

Class Diagram PIXEL-T menggunakan enam kategori stereotype untuk mengklasifikasikan setiap kelas berdasarkan tanggung jawabnya:

| Stereotype | Keterangan | Jumlah Kelas |
|------------|------------|--------------|
| `<<module>>` | Modul frontend (React context, service HTTP, fungsi AI) | 3 |
| `<<controller>>` | Controller HTTP Flask | 2 |
| `<<service>>` | Layanan bisnis backend | 5 |
| `<<repository>>` | Abstraksi akses data | 1 |
| `<<dataclass>>` | Struktur data hasil inferensi AI | 3 |
| `<<entity>>` | Tabel basis data PostgreSQL | 3 |
| `<<external>>` | Tabel autentikasi eksternal (Supabase Auth) | 1 |
| `<<exception>>` | Kelas pengecualian aplikasi | 1 |
| **Total** | | **21** |

Hubungan antara kelas ditampilkan dengan empat tipe relasi UML:
- **Association** (garis solid dengan panah): keterkaitan langsung antar komponen internal, mis. controller mendelegasikan ke service.
- **Dependency** (garis putus-putus dengan panah terbuka): ketergantungan antar komponen, mis. service bergantung pada repository.
- **Association FK** (garis solid tanpa panah): kunci asing antar tabel basis data.
- Tidak digunakan **Generalization/Inheritance** karena Admin dan Dokter tidak merupakan subclass, melainkan dibedakan melalui atribut metadata (role).

---

## 4.x.3 Komponen Utama Class Diagram

### 4.x.3.1 Authentication dan Access Control

**AuthContext** (`<<module>>`) merupakan konteks React yang mengelola state autentikasi, session, role, dan status akun pengguna. Kelas ini menyimpan atribut `user`, `session`, `loading`, `role`, dan `accountStatus`, serta menyediakan operasi `signIn()`, `signUp()`, dan `signOut()`.

Mekanisme pemetaan role dalam AuthContext mengacu pada dua sumber terpercaya:
1. **Admin**: role dibaca dari `auth.users.raw_app_meta_data.role` melalui fungsi `getAdminRoleFromAppMetadata()`. Nilai `'admin'` ditetapkan saat akun dibuat melalui Supabase Admin API, bukan melalui pendaftaran publik.
2. **Dokter**: role dan status akun dibaca dari tabel `doctor_profiles` melalui fungsi `fetchUserProfileStatus()`, yang mengembalikan `role = 'doctor'` dan `account_status` bernilai `'pending'`, `'approved'`, atau `'rejected'`.

Tidak terdapat inheritance antara Admin dan Dokter. Kedua peran dibedakan melalui atribut metadata pada akun pengguna, bukan melalui spesialisasi kelas. Keputusan pemodelan ini didasarkan pada implementasi aktual di mana Admin tidak memiliki baris dalam tabel `doctor_profiles` (di-skip oleh database trigger), dan Dokter tidak memiliki entri `app_metadata.role = 'admin'`.

### 4.x.3.2 Backend Layer

Class Diagram mencakup dua controller dan lima service pada lapisan backend:

- **AdminController** (`<<controller>>`): menangani endpoint HTTP untuk manajemen dokter, yaitu daftar dokter, detail dokter, persetujuan, penolakan, dan statistik. Controller mendelegasikan logika bisnis ke `AdminService`.
- **AnalysisController** (`<<controller>>`): menangani endpoint HTTP untuk operasi analisis, yaitu pembuatan analisis, detail analisis, riwayat, dan penghapusan. Controller mendelegasikan ke `AnalysisService`.
- **AdminService** (`<<service>>`): logika bisnis admin untuk persetujuan dan penolakan registrasi dokter menggunakan service-role Supabase client untuk mengatasi RLS.
- **AnalysisService** (`<<service>>`): orkestrasi utama analisis citra, termasuk validasi gambar, upload ke storage, enqueue job, eksekusi pipeline AI, dan pelacakan progres.
- **StorageService** (`<<service>>`): mengelola aset file di Supabase Storage dengan jalur `analysis/{user_id}/{analysis_id}/{category}/{filename}`.
- **AnalysisJobQueue** (`<<service>>`): antrian FIFO untuk job analisis background dengan kapasitas terbatas.
- **AnalysisProgressReporter** (`<<service>>`): melaporkan progres eksekusi pipeline ke basis data melalui AnalysisRepository.
- **AnalysisRepository** (`<<repository>>`): abstraksi CRUD untuk tabel `analyses` dengan enforcing kepemilikan user.

### 4.x.3.3 AI Processing Layer

Lapisan inferensi AI terdiri atas enam kelas:

- **AIInferenceFunctions** (`<<module>>`: kumpulan fungsi pipeline inferensi yang mencakup `run_pipeline()`, `predict()`, `postprocess_mask()`, `measure_mask()`, `generate_gradcam()`, dan `prepare_image()`.
- **ModelService** (`<<service>>`): pemuat model PyTorch (U-Net + ResNet50) secara lazy-loading dan thread-safe dengan verifikasi SHA-256 checkpoint.
- **ModelConfig** (`<<dataclass>>`): konfigurasi beku model yang berisi 19 atribut, termasuk arsitektur, encoder, input size, threshold, dan parameter TTA.
- **PipelineResult** (`<<dataclass>>`): struktur hasil akhir pipeline yang berisi gambar mask, overlay, heatmap Grad-CAM, hasil pengukuran, dan ringkasan teks.
- **SegmentationResult** (`<<dataclass>>`): hasil segmentasi berupa probability map, binary mask, dan threshold.
- **GradCAMResult** (`<<dataclass>>`): hasil Grad-CAM berupa heatmap, overlay, target layer, dan objective.

### 4.x.3.4 Data Access dan Storage

Tiga entitas basis data direpresentasikan dalam diagram:

- **auth_users** (`<<external>>`): tabel autentikasi Supabase Auth yang menyimpan `id` pengguna. Digambarkan sebagai eksternal karena dikelola oleh Supabase, bukan oleh aplikasi PIXEL-T secara langsung.
- **doctor_profiles** (`<<entity>>`): tabel profil dokter yang berisi informasi personal dan profesional, serta kolom `account_status` dengan nilai `pending`, `approved`, atau `rejected`. Memiliki foreign key `user_id` yang merujuk ke `auth_users(id)` dengan constraint `UNIQUE` (satu akun paling banyak satu profil dokter).
- **analyses** (`<<entity>>`): tabel data hasil analisis citra yang menyimpan status, segmentation status, gradcam status, dan timestamp. Memiliki foreign key `user_id` yang merujuk ke `auth_users(id)`.

**APIError** (`<<exception>>`): kelas pengecualian terstruktur dengan atribut `code`, `message`, dan `status_code`, serta metode `to_dict()` untuk merespons error dalam format JSON yang konsisten.

---

## 4.x.4 Hubungan Antarkelas

Class Diagram mencakup 24 relasi yang menggambarkan komunikasi dan ketergantungan antar komponen:

1. **AuthContext → auth_users** (Dependency): AuthContext berinteraksi dengan Supabase Auth untuk autentikasi dan pembacaan role.
2. **AnalysisClient → AnalysisController** (Dependency): Frontend memanggil endpoint HTTP backend melalui REST API.
3. **DoctorProfileService → doctor_profiles** (Dependency): Modul frontend melakukan CRUD profil dokter melalui Supabase RLS.
4. **AdminController → AdminService** (Association): Controller mendelegasikan tugas ke service.
5. **AdminController → APIError** (Dependency): Controller menangkap dan menampilkan error terstruktur.
6. **AnalysisController → AnalysisService** (Association): Controller mendelegasikan tugas ke service.
7. **AnalysisController → APIError** (Dependency): Controller menangkap dan menampilkan error terstruktur.
8. **AdminService → doctor_profiles** (Dependency): Service admin mengelola data profil dokter melalui service-role client.
9. **AnalysisService → AnalysisRepository** (Association): Service menggunakan repository untuk persistensi data analisis.
10. **AnalysisService → StorageService** (Association): Service menggunakan storage untuk aset file analisis.
11. **AnalysisService → AnalysisJobQueue** (Association): Service menggunakan antrian untuk job analisis background.
12. **AnalysisService → AnalysisProgressReporter** (Dependency): Service membuat instance reporter progres.
13. **AnalysisProgressReporter → AnalysisRepository** (Association): Reporter menulis progres eksekusi ke repository.
14. **AnalysisService → AIInferenceFunctions** (Dependency): Service memanggil pipeline AI untuk pemrosesan citra.
15. **AIInferenceFunctions → ModelService** (Dependency): Fungsi inferensi menggunakan layanan model untuk prediksi dan Grad-CAM.
16. **AIInferenceFunctions → PipelineResult** (Dependency): Fungsi inferensi mengembalikan objek hasil pipeline.
17. **AIInferenceFunctions → SegmentationResult** (Dependency): Fungsi inferensi mengembalikan objek hasil segmentasi.
18. **AIInferenceFunctions → GradCAMResult** (Dependency): Fungsi inferensi mengembalikan objek hasil Grad-CAM.
19. **PipelineResult → GradCAMResult** (Association): Hasil pipeline memuat referensi ke objek GradCAMResult.
20. **ModelService → ModelConfig** (Association): Model service menggunakan konfigurasi model saat inisialisasi.
21. **AnalysisRepository → analyses** (Dependency): Repository melakukan CRUD pada tabel analyses.
22. **auth_users → doctor_profiles** (Association FK): Foreign key `user_id` dengan cardinalitas 1 -- 0..1.
23. **auth_users → analyses** (Association FK): Foreign key `user_id` dengan cardinalitas 1 -- *.

---

## 4.x.5 Representasi Role Admin dan Dokter

Dalam Class Diagram ini, Admin dan Dokter **tidak dimodelkan sebagai kelas terpisah dengan inheritance**. Sebaliknya, kedua peran direpresentasikan sebagai:

1. **Satu konsep pengguna** yang diakses melalui `AuthContext` dengan atribut `role` dan `accountStatus`.
2. **Admin** dibedakan melalui `app_metadata.role = 'admin'` pada Supabase Auth (metadata sisi server yang hanya dapat ditulis oleh admin Supabase).
3. **Dokter** dibedakan melalui baris dalam tabel `doctor_profiles` dengan `role = 'doctor'` dan `account_status` yang mengatur tingkat akses.

Keputusan pemodelan ini didasarkan pada implementasi aktual yang menunjukkan:
- Admin tidak memiliki baris di `doctor_profiles` (di-skip oleh trigger `handle_new_doctor_signup`).
- Dokter tidak memiliki entri `app_metadata.role = 'admin'`.
- Route guard memeriksa `role` dari `app_metadata` untuk admin, dan `accountStatus` dari `doctor_profiles` untuk dokter.
- Tidak ada kelas `Admin` atau `Doctor` yang merupakan subclass dari kelas `User` dalam source code.

---

## 4.x.6 Konsistensi dengan Diagram Lain

Class Diagram ini telah disejajarkan dengan diagram UML lain dalam skripsi:

- **Use Case Diagram**: Tanggung jawab Admin (manajemen dokter, statistik) dan Dokter (upload citra, analisis, riwayat, profil) konsisten dengan use case yang telah didefinisikan.
- **ERD**: Entitas `doctor_profiles` dan `analyses` beserta foreign key mereka konsisten dengan skema basis data dalam ERD.
- **Activity Diagram**: Alur Sign Up, Sign In, Upload Image, Segmentation, History, Doctor Profile, dan Sign Out didukung oleh kelas dan operasi dalam Class Diagram.
- **Sequence Diagram**: Interaksi antar komponen dalam sequence diagram sesuai dengan operasi dan tanggung jawab kelas yang ditampilkan.

---

## 4.x.7 Kesimpulan

Class Diagram final PIXEL-T menggambarkan 21 kelas dan 24 relasi yang secara akurat merepresentasikan struktur aplikasi web PIXEL-T berdasarkan implementasi aktual. Diagram ini mencakup mekanisme role Admin dan Dokter yang dibedakan melalui atribut metadata, bukan inheritance, dan konsisten dengan diagram UML lainnya dalam skripsi. Semua elemen telah diverifikasi terhadap source code sehingga diagram ini siap digunakan sebagai ilustrasi pada Bab IV skripsi.