# PENJELASAN AKADEMIK CLASS DIAGRAM PIXEL-T FINAL SIMPLE

## DOKUMEN PENUNJANG BAB IV SKRIPSI S1

**Judul Skripsi:** PIXEL-T: Sistem Informasi Web Segmentasi Polip USG dengan Transfer Learning dan Explainable AI

**File Diagram:** `CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE.{drawio,png,svg}`  
**Jumlah Kelas:** 15 kelas  
**Jumlah Relasi:** 17 relasi  
**Gambar Placeholder:** Gambar 4.x (nomor gambar akan disesuaikan pada penulisan akhir skripsi)  
**Status:** FINAL — LULUS  
**Tanggal:** 6 November 2026

---

## KATA PENGANTAR

Dokumen ini menyajikan penjelasan akademik mengenai Class Diagram sistem informasi web PIXEL-T yang digunakan sebagai referensi arsitektur dalam Bab IV skripsi S1. Penjelasan ini dibuat berdasarkan versi final yang disederhanakan (Final Simple) dari Class Diagram, yang telah divalidasi terhadap implementasi aktual source code aplikasi PIXEL-T, termasuk frontend, backend, pipeline AI, database, serta layanan eksternal.

Tujuan penjelasan ini adalah membantu pembaca memahami struktur kelas utama, tanggung jawab masing-masing komponen, serta hubungan antarkelas yang mendukung operasional sistem PIXEL-T secara garis besar. Penjelasan ini tidak menguraikan setiap detail implementasi source code, tidak menggambarkan urutan interaksi antarobjek (sebagai tugas Sequence Diagram), dan tidak mencampurkan seluruh atribut tabel database ke dalam penjelasan kelas aplikasi.

---

## BAB IV — STRUKTUR SISTEM

### 4.x Class Diagram PIXEL-T

Class Diagram dalam Gambar 4.x menggambarkan struktur statis sistem informasi web PIXEL-T. Diagram ini menyajikan hubungan antara komponen frontend, backend, pipeline AI, layanan eksternal, serta entitas data yang tersimpan dalam database. Struktur kelas disusun dengan mempertahankan komponen inti yang mewakili arsitektur sistem, sambil menyederhanakan detail implementasi yang tidak relevan untuk pemodelan kelas tingkat skripsi.

Dari hasil audit terhadap implementasi aktual, Class Diagram versi Final Simple menyusun 15 kelas yang dikelompokkan ke dalam lima kelompok arsitektur:

1. **Komponen Frontend** — menangani antarmuka dan komunikasi klien.
2. **Komponen Backend API** — menangani permintaan HTTP dari frontend.
3. **Layanan Backend dan Repositori** — mengelola logika bisnis dan akses data.
4. **Pipeline AI** — menangani pemrosesan citra medis, inferensi model, dan pembuatan artefak.
5. **Layanan Eksternal dan Entitas Database** — menyediakan infrastruktur autentikasi, penyimpanan, dan basis data.

Setiap kelas direpresentasikan dalam notasi UML class standar dengan nama kelas, stereotype, atribut, dan operasi. Hubungan antara kelas ditampilkan melalui asosiasi, agregasi, dan dependensi dengan arah serta multiplicity yang sesuai dengan implementasi aktual.

---

### 4.x.1 Komponen Frontend

Komponen frontend bertanggung jawab atas antarmuka pengguna, pengelolaan sesi autentikasi, dan komunikasi dengan backend melalui REST API. Tiga kelas dalam kelompok ini adalah:

**1. AuthContext**  
AuthContext adalah modul manajemen state autentikasi global dalam aplikasi React. Kelas ini menyimpan informasi pengguna yang sedang login, sesi, status pemuatan, peran pengguna, dan status akun. Operasi utamanya mencakup signIn, signUp, dan signOut, yang terhubung ke layanan eksternal Supabase untuk autentikasi.

**2. AnalysisClient**  
AnalysisClient adalah klien REST API yang bertanggung jawab atas komunikasi frontend dengan backend untuk fitur analisis citra. Operasi utamanya mencakup pengunggahan citra (createAnalysis), pengambilan detail analisis (getAnalysis), pengambilan riwayat analisis (listHistory), dan penghapusan analisis (deleteAnalysis).

**3. DoctorProfileService**  
DoctorProfileService adalah layanan frontend yang mengelola profil dokter, mencakup pengambilan data profil, penyimpanan atau pembaruan data profil, serta unggah foto profil avatar melalui layanan eksternal Supabase.

---

### 4.x.2 Komponen Backend API

Komponen backend API bertanggung jawab atas penerimaan permintaan HTTP dari frontend, validasi input, dan delegasi tugas ke layanan backend yang relevan. Dua kelas dalam kelompok ini adalah:

**4. AnalysisController**  
AnalysisController adalah controller backend yang menangani endpoint terkait analisis citra, yaitu pengunggahan citra baru, pengambilan detail analisis, pengambilan riwayat, dan penghapusan analisis. Controller ini bergantung pada AnalysisService untuk menjalankan logika bisnis analisis.

**5. AdminController**  
AdminController adalah controller backend yang menangani endpoint administrasi terkait manajemen dokter, yaitu daftar dokter, detail dokter, persetujuan dokter, penolakan dokter, dan statistik pendaftaran. Controller ini bergantung pada AdminService untuk menjalankan operasi administrasi.

---

### 4.x.3 Layanan Backend dan Repositori

Kelompok ini mengelola logika bisnis aplikasi serta akses data langsung ke database. Tiga kelas dalam kelompok ini adalah:

**6. AnalysisService**  
AnalysisService adalah layanan inti backend yang mengatur seluruh siklus proses analisis citra, mulai dari validasi dan dekodiran citra yang diunggah, pembuatan record analisis, orkestrasi pemanggilan pipeline AI, hingga pengambilan dan penghapusan data analisis. Layanan ini bergantung pada AnalysisRepository untuk akses data dan AIInference untuk pemrosesan AI.

**7. AdminService**  
AdminService adalah layanan backend yang mengelola operasi administrasi dokter, yaitu daftar dokter dengan filter status, persetujuan dokter, penolakan dokter dengan alasan, dan statistik pendaftaran. Layanan ini menggunakan klien Supabase dengan peran service-role untuk mengakses database.

**8. AnalysisRepository**  
AnalysisRepository adalah repositori yang bertanggung jawab atas operasi CRUD dan akses data untuk tabel `analyses` dalam database. Repositori ini memberlakukan validasi kepemilikan data (user ownership) dan pembatasan status siklus hidup analisis.

---

### 4.x.4 Pipeline AI

Kelompok ini menangani pemrosesan citra medis menggunakan model pembelajaran mesin, mulai dari praproses hingga pembuatan artefak hasil segmentasi dan Grad-CAM. Tiga kelas dalam kelompok ini adalah:

**9. AIInference**  
AIInference adalah modul pipeline akhir (end-to-end pipeline) yang mengatur urutan pemrosesan citra, yaitu praproses citra, inferensi model, pasca-proses mask, pembuatan Grad-CAM, dan komposisi artefak hasil. Pipeline ini bergantung pada ModelService untuk menjalankan inferensi model.

**10. ModelService**  
ModelService adalah layanan yang bertanggung jawab atas pemuatan model U-Net + ResNet50 secara lazy (pemuatan sekali dan digunakan ulang), menjalankan inferensi logits pada tensor citra, dan menyediakan metadata model. Layanan ini bergantung pada ModelConfig untuk konfigurasi model.

**11. ModelConfig**  
ModelConfig adalah struktur konfigurasi model yang menyimpan parameter utama model terverifikasi, yaitu arsitektur, encoder, ukuran masukan, ambang batas segmentasi, serta checksum checkpoint model.

---

### 4.x.5 Layanan Eksternal dan Entitas Database

Kelompok ini mencakup abstraksi layanan eksternal yang digunakan oleh sistem serta entitas data yang disimpan dalam database. Empat kelas dalam kelompok ini adalah:

**12. SupabasePlatform**  
SupabasePlatform adalah representasi layanan eksternal Supabase yang menyediakan autentikasi (Auth), basis data (DB), dan penyimpanan berkas (Storage). Platform ini digunakan oleh komponen frontend dan backend untuk mengelola sesi pengguna, data profil, data analisis, serta berkas citra dan artefak.

**13. User**  
User adalah entitas data yang mewakili identitas pengguna dalam sistem, mencakup identifikasi unik, alamat email, dan metadata peran pengguna. User memiliki hubungan satu-ke-nol-atau-satu dengan DoctorProfile, serta satu-ke-banyak dengan Analysis.

**14. DoctorProfile**  
DoctorProfile adalah entitas data yang menyimpan profil lengkap dokter, mencakup identifikasi unik, referensi ke pengguna, nama lengkap, rumah sakit, spesialisasi utama, peran, dan status akun. Setiap profil dokter dimiliki oleh tepat satu pengguna.

**15. Analysis**  
Analysis adalah entitas data yang mencatat hasil analisis citra medis, mencakup identifikasi unik, referensi ke pengguna, status siklus hidup, waktu pembuatan, status segmentasi, dan status Grad-CAM. Setiap analisis dimiliki oleh tepat satu pengguna, sedangkan satu pengguna dapat memiliki banyak analisis.

---

### 4.x.6 Atribut dan Operasi Penting

Tabel berikut meringkas atribut dan operasi utama dari setiap kelas dalam Class Diagram:

| Kelas | Atribut Utama | Operasi Utama |
|-------|--------------|---------------|
| AuthContext | user, session, loading, role, accountStatus | signIn, signUp, signOut |
| AnalysisClient | — | createAnalysis, getAnalysis, listHistory, deleteAnalysis |
| DoctorProfileService | — | fetchDoctorProfile, saveDoctorProfile, uploadAvatar |
| AnalysisController | service | create_analysis, get_analysis, list_history, delete_analysis |
| AdminController | service | list_doctors, approve_doctor, reject_doctor, get_statistics |
| AnalysisService | repository, storage, pipeline_runner | validate_and_decode_image, create_analysis, get_analysis, list_user_analyses, delete_analysis |
| AdminService | client | list_doctors, approve_doctor, reject_doctor, get_statistics |
| AnalysisRepository | client | create, get_by_id, list_by_user, update, delete |
| AIInference | — | run_pipeline, predict, generate_gradcam |
| ModelService | config | load, predict_logits, metadata |
| ModelConfig | architecture, encoder, input_size, threshold, checkpoint_sha256 | — |
| SupabasePlatform | — | Auth: signUp, signIn, signOut; DB: doctor_profiles, analyses; Storage: analysis-assets, profile-avatars |
| User | id, email, app_metadata.role | get_profile, get_analyses |
| DoctorProfile | id, user_id, full_name, hospital, primary_specialty, account_status, role | get_user |
| Analysis | id, user_id, status, created_at, segmentation_status, gradcam_status | get_user |

Catatan: Tabel di atas hanya menyajikan atribut dan operasi yang relevan untuk pemahaman struktural, bukan seluruh atribut dan metode yang terdapat dalam source code.

---

### 4.x.7 Hubungan Antar Kelas

Hubungan antara kelas dalam Class Diagram dibagi menjadi tiga jenis notasi UML, yaitu asosiasi, agregasi, dan dependensi. Multiplicity pada setiap hubungan dicantumkan untuk menggambarkan kardinalitas hubungan.

**Asosasi (Association)** digunakan untuk hubungan struktural antara entitas data:
- **User → DoctorProfile** (1 : 0..1): Setiap pengguna memiliki nol atau satu profil dokter. Setiap profil dokter dimiliki oleh tepat satu pengguna.
- **User → Analysis** (1 : *): Setiap pengguna dapat memiliki nol atau banyak analisis. Setiap analisis dimiliki oleh tepat satu pengguna.

**Agregasi (Aggregation)** digunakan untuk hubungan keseluruhan–bagian di antar komponen aplikasi:
- **AnalysisController → AnalysisService** (1 : 1)
- **AdminController → AdminService** (1 : 1)
- **AnalysisService → AnalysisRepository** (1 : 1)
- **ModelService → ModelConfig** (1 : 1)

**Dependensi (Dependency)** digunakan untuk hubungan penggunaan atau pemanggilan antara komponen:
- **AuthContext → SupabasePlatform** — penggunaan autentikasi Supabase.
- **AnalysisClient → AnalysisController** — pemanggilan REST API.
- **AnalysisClient → SupabasePlatform** — penggunaan access token.
- **DoctorProfileService → SupabasePlatform** — akses basis data dan penyimpanan.
- **AnalysisService → SupabasePlatform** — akses penyimpanan berkas.
- **AnalysisService → AIInference** — pemanggilan pipeline AI.
- **AnalysisRepository → SupabasePlatform** — akses basis data.
- **AdminService → SupabasePlatform** — akses basis data dengan peran service-role.
- **AIInference → ModelService** — penggunaan layanan model.
- **SupabasePlatform → DoctorProfile** — trigger pembuatan profil otomatis.
- **SupabasePlatform → Analysis** — penyimpanan data analisis dalam basis data.

Seluruh hubungan telah diverifikasi terhadap implementasi aktual dan tidak menggunakan agregasi atau komposisi tanpa dasar kepemilikan objek yang jelas.

---

### 4.x.8 Pembagian Tanggung Jawab Komponen

Tanggung jawab komponen dalam sistem PIXEL-T terbagi secara jelas berdasarkan lapisan arsitektur:

- **Frontend** bertanggung jawab atas antarmuka pengguna, manajemen sesi autentikasi, dan komunikasi dengan backend.
- **Backend API** bertanggung jawab atas penerimaan permintaan HTTP, validasi input, dan delegasi tugas ke layanan backend.
- **Layanan Backend dan Repositori** bertanggung jawab atas logika bisnis, orkestrasi proses analisis, dan akses data ke database.
- **Pipeline AI** bertanggung jawab atas pemrosesan citra medis, inferensi model U-Net + ResNet50, dan pembuatan artefak segmentasi serta Grad-CAM.
- **Layanan Eksternal dan Entitas Database** menyediakan infrastruktur autentikasi, basis data, dan penyimpanan berkas yang digunakan oleh seluruh komponen sistem.

Pembagian tanggung jawab ini memastikan pemisahan keterkaitan (separation of concerns) antar lapisan, sehingga masing-masing komponen memiliki tanggung jawab yang jelas dan tidak tumpang tindih secara signifikan.

---

### 4.x.9 Hubungan Struktur dengan Arsitektur Web PIXEL-T

Struktur Class Diagram ini mencerminkan arsitektur web PIXEL-T yang terdiri dari tiga lapisan utama, yaitu lapisan presentasi (frontend), lapisan aplikasi (backend), dan lapisan data (database), dengan penambahan lapisan inferensi AI dan layanan eksternal.

- **Lapisan presentasi** direpresentasikan oleh AuthContext, AnalysisClient, dan DoctorProfileService yang berkomunikasi dengan pengguna serta backend melalui REST API.
- **Lapisan aplikasi** direpresentasikan oleh AnalysisController, AdminController, AnalysisService, AdminService, dan AnalysisRepository yang mengelola logika bisnis dan akses data.
- **Lapisan inferensi AI** direpresentasikan oleh AIInference, ModelService, dan ModelConfig yang menangani pemrosesan citra medis.
- **Lapisan data dan eksternal** direpresentasikan oleh SupabasePlatform, User, DoctorProfile, dan Analysis yang menyimpan dan mengelola data sistem.

Hubungan antar komponen dalam diagram konsisten dengan alur aktual dalam aplikasi, yaitu autentikasi pengguna melalui Supabase Auth, pengunggahan citra melalui REST API, pemrosesan segmentasi melalui pipeline AI, penyimpanan hasil analisis dalam database, dan manajemen profil dokter melalui layanan eksternal.

---

### 4.x.10 Penyederhanaan dan Keputusan Desain

Dalam penyusunan Class Diagram versi Final Simple, dilakukan penyederhanaan terhadap versi sebelumnya dengan klasifikasi berikut:

- **Dipertahankan:** Komponen inti yang diperlukan untuk memahami arsitektur PIXEL-T secara struktural, yaitu semua 15 kelas yang tercantum di atas.
- **Disederhanakan:** Beberapa komponen eksternal digabung dalam representasi abstraksi tunggal (SupabasePlatform) untuk menghindari kerumitan yang tidak perlu.
- **Dikeluarkan:** Detail implementasi internal yang tidak relevan untuk diagram kelas tingkat skripsi, yaitu StorageService, AnalysisJobQueue, SegmentationResult, GradCAMResult, ModelLoadError, APIError, dan AnalysisProgressReporter.

Penyederhanaan dilakukan melalui pemilihan abstraksi dan pengelompokan tanggung jawab yang tepat, bukan dengan menghapus informasi secara sembarangan. Komponen penting yang mendukung seluruh alur fungsional utama sistem tetap dipertahankan dalam diagram.

---

### 4.x.11 Kesimpulan

Class Diagram PIXEL-T versi Final Simple menyajikan struktur kelas sistem informasi web PIXEL-T secara jelas, tepat secara UML, dan sesuai dengan implementasi aktual. Diagram ini mencakup komponen frontend, backend, pipeline AI, layanan eksternal, serta entitas database yang saling terhubung melalui hubungan asosiasi, agregasi, dan dependensi dengan multiplicity yang terverifikasi.

Dengan 15 kelas dan 17 relasi, diagram ini cukup sederhana untuk dimasukkan ke dalam halaman skripsi, namun tetap informatif untuk menjelaskan struktur arsitektur PIXEL-T. Semua elemen dalam diagram telah diverifikasi terhadap source code aktual, sehingga diagram ini layak digunakan sebagai Gambar 4.x pada Bab IV skripsi S1.

---

## LAMPIRAN

| File | Keterangan |
|------|------------|
| `CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE.drawio` | Sumber diagram yang dapat diedit (Draw.io XML) |
| `CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE.png` | Hasil render PNG (3750 × 3780 px) |
| `CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE.svg` | Hasil eksport SVG |
| `AUDIT_CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE.md` | Laporan audit |
| `MATRIKS_BUKTI_CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE.md` | Matriks bukti audit |

---

**Dokumen ini merupakan bagian dari dokumentasi pendukung Bab IV skripsi S1 PIXEL-T. Status akhir: FINAL — LULUS.**
