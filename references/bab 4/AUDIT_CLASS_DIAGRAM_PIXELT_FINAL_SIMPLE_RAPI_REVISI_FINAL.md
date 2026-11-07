# AUDIT INDEPENDEN CLASS DIAGRAM PIXELT FINAL SIMPLE RAPI REVISI FINAL

**Dokumen Pendukung Bab IV Skripsi S1**  
**Sistem:** PIXEL-T (Segmentasi Polip USG dengan Transfer Learning dan Explainable AI)  
**Versi Diagram:** `CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE_RAPI_REVISI_FINAL.{drawio,png,svg}`  
**Diagram:** 17 kelas, 20 relasi  
**Tanggal Audit:** 6 November 2026  
**Status Akhir:** **FINAL — LULUS**

---

## A. Ringkasan Eksekutif

Audit independen ini memvalidasi Class Diagram versi **FINAL SIMPLE RAPI REVISI FINAL** PIXEL-T terhadap implementasi aktual source code aplikasi. Audit dilakukan dari awal (tidak mengandalkan dokumentasi terdahulu) dan fokus pada struktur kelas inti yang diperlukan untuk menjelaskan arsitektur sistem.

Versi REVISI FINAL merupakan perbaikan dari versi RAPI sebelumnya (17 kelas, 20 relasi) dengan perbaikan layout visual:
- **Perbaikan layout:** Posisi dan ukuran kotak kelas disesuaikan agar nama kelas tidak terpotong (terutama `AnalysisJobQueue`, `StorageService`, `ModelConfig`, `SupabasePlatform`).
- **Perbaikan jarak antarkelas:** Jarak antar kotak diperbesar untuk menghindari tumpang tindih garis.
- **Perbaikan rute garis:** Rute garis relasi disesuaikan agar tidak melintasi teks atau kotak kelas.

Audit mencakup:
- Frontend React/TypeScript.
- Backend Flask (controllers, services, repositories, auth).
- AI pipeline (U-Net, ResNet50, Grad-CAM).
- Database Supabase/PostgreSQL.
- Layanan eksternal.

Hasil akhir: **17 kelas, 20 relasi, multiplicity terverifikasi, dan konsisten di ketiga format file.**

---

## B. Ringkasan Hasil Audit Komponen

### B.1 Frontend
| Komponen | Keberadaan | Tanggung Jawab |
|----------|-----------|----------------|
| AuthContext | ✅ Ada | Manajemen state autentikasi global (user, session, loading, role, accountStatus). |
| AnalysisClient | ✅ Ada | Komunikasi REST API untuk upload, polling, riwayat, hapus analisis. |
| DoctorProfileService | ✅ Ada | Pengambilan, penyimpanan, validasi, avatar profil dokter. |

### B.2 Backend
| Komponen | Keberadaan | Tanggung Jawab |
|----------|-----------|----------------|
| AnalysisController | ✅ Ada | HTTP endpoint analisis (POST, GET, history, DELETE). |
| AdminController | ✅ Ada | HTTP endpoint administrasi dokter (list, detail, approve, reject, statistik). |
| AnalysisService | ✅ Ada | Validasi citra, penyimpanan, orkestrasi pipeline AI, CRUD analisis. |
| AdminService | ✅ Ada | Operasi administrasi dokter (list, approve, reject, statistik). |
| AnalysisRepository | ✅ Ada | CRUD tabel `analyses` dengan validasi ownership. |
| StorageService | ✅ Ada | Akses Supabase Storage untuk berkas citra asli, segmentasi, Grad-CAM. |
| AnalysisJobQueue | ✅ Ada | Antrian pekerjaan latar belakang untuk pemrosesan analisis. |

### B.3 AI Pipeline
| Komponen | Keberadaan | Tanggung Jawab |
|----------|-----------|----------------|
| AIInference | ✅ Ada | Modul pipeline end-to-end (preprocessing → inference → postprocessing → Grad-CAM → artifact). |
| ModelService | ✅ Ada | Loader lazy model U-Net + ResNet50. |
| ModelConfig | ✅ Ada | Konfigurasi model terverifikasi (architecture, encoder, threshold, checkpoint). |

### B.4 External / Database
| Komponen | Keberadaan | Tanggung Jawab |
|----------|-----------|----------------|
| SupabasePlatform | ✅ Ada | Auth, DB, Storage (abstraksi layanan eksternal). |
| User | ✅ Ada (auth.users) | Identitas pengguna. |
| DoctorProfile | ✅ Ada (doctor_profiles) | Profil dokter dan status approval. |
| Analysis | ✅ Ada (analyses) | Record hasil analisis. |

---

## C. Hasil Penyederhanaan

### C.1 Kelas yang Dikeluarkan dari Diagram Final Simple RAPI Revisi Final

| Kelas | Alasan Penghapusan |
|-------|-------------------|
| SegmentationResult | Represented via ModelConfig threshold & Analysis metadata. |
| GradCAMResult | Represented via ModelConfig gradcam_target_layer & Analysis status. |
| ModelLoadError | Error helper, tidak relevan untuk diagram kelas utama. |
| APIError | Error handling detail, bukan struktur utama. |
| AnalysisProgressReporter | Helper internal, bukan kelas tanggung jawab. |

### C.2 Kelas yang Digabungkan / Dinegosikan

- **SupabasePlatform**: menggabungkan abstraksi layanan eksternal Supabase (Auth, DB, Storage) dalam satu kelas eksternal untuk menghindari kerumitan.
- Tidak ada kelas yang digabung secara paksa. Penyederhanaan dilakukan melalui pemilihan abstraksi dan kelauran detail implementasi.

### C.3 Kelas yang Dipertahankan

Semua kelas inti yang diperlukan untuk memahami arsitektur PIXEL-T secara struktural:

1. AuthContext
2. AnalysisClient
3. DoctorProfileService
4. AnalysisController
5. AdminController
6. AnalysisService
7. AdminService
8. AnalysisRepository
9. StorageService
10. AnalysisJobQueue
11. AIInference
12. ModelService
13. ModelConfig
14. SupabasePlatform
15. User
16. DoctorProfile
17. Analysis

---

## D. Hasil Audit Alur Fungsional

| Alur | Komponen Utama | Representasi dalam Diagram | Status |
|------|---------------|--------------------------|--------|
| Sign Up | AuthContext, SupabasePlatform, User, DoctorProfile | ✅ Tercakup | TERVERIFIKASI |
| Sign In | AuthContext, SupabasePlatform, User, DoctorProfile | ✅ Tercakup | TERVERIFIKASI |
| Upload Image | AnalysisClient, AnalysisController, AnalysisService, AnalysisRepository, StorageService, AnalysisJobQueue, AIInference | ✅ Tercakup | TERVERIFIKASI |
| Segmentation | AnalysisService, AIInference, ModelService, ModelConfig, Analysis | ✅ Tercakup | TERVERIFIKASI |
| History | AnalysisClient, AnalysisController, AnalysisService, AnalysisRepository, Analysis | ✅ Tercakup | TERVERIFIKASI |
| Doctor Profile | DoctorProfileService, SupabasePlatform, DoctorProfile, User | ✅ Tercakup | TERVERIFIKASI |
| Sign Out | AuthContext, SupabasePlatform, User | ✅ Tercakup | TERVERIFIKASI |

---

## E. Hasil Audit Relasi dan Multiplicity

| No. | Relasi | Jenis | Multiplicity | Status |
|-----|--------|-------|--------------|--------|
| 1 | AuthContext → SupabasePlatform | Dependency | 1 : 1 | ✅ Valid |
| 2 | AnalysisClient → AnalysisController | Dependency | 1 : 1 | ✅ Valid |
| 3 | AnalysisClient → SupabasePlatform | Dependency | 1 : 1 | ✅ Valid |
| 4 | DoctorProfileService → SupabasePlatform | Dependency | 1 : 1 | ✅ Valid |
| 5 | AnalysisController → AnalysisService | Dependency | 1 : 1 | ✅ Valid |
| 6 | AdminController → AdminService | Dependency | 1 : 1 | ✅ Valid |
| 7 | AnalysisService → AnalysisRepository | Dependency | 1 : 1 | ✅ Valid |
| 8 | AnalysisService → StorageService | Dependency | 1 : 1 | ✅ Valid |
| 9 | AnalysisService → AnalysisJobQueue | Dependency | 1 : 1 | ✅ Valid |
| 10 | AnalysisService → SupabasePlatform | Dependency | 1 : 1 | ✅ Valid |
| 11 | AnalysisService → AIInference | Dependency | 1 : 1 | ✅ Valid |
| 12 | AnalysisRepository → SupabasePlatform | Dependency | 1 : 1 | ✅ Valid |
| 13 | StorageService → SupabasePlatform | Dependency | 1 : 1 | ✅ Valid |
| 14 | AdminService → SupabasePlatform | Dependency | 1 : 1 | ✅ Valid |
| 15 | AIInference → ModelService | Dependency | 1 : 1 | ✅ Valid |
| 16 | ModelService → ModelConfig | Aggregation | 1 : 1 | ✅ Valid |
| 17 | User → DoctorProfile | Association | 1 : 0..1 | ✅ Valid |
| 18 | User → Analysis | Association | 1 : * | ✅ Valid |
| 19 | SupabasePlatform → DoctorProfile | Trigger | trigger | ✅ Valid |
| 20 | SupabasePlatform → Analysis | Association | DB | ✅ Valid |

---

## F. Multiplicity Verifikasi Database

| Relasi | Bukti Constraint | Multiplicity | Status |
|--------|-----------------|--------------|--------|
| User → DoctorProfile | `004_migration` L46 `doctor_profiles_user_id_key UNIQUE (user_id)` | 1 : 0..1 | ✅ |
| User → Analysis | `001_migration` L17 `user_id UUID NOT NULL REFERENCES auth.users(id)` ON DELETE CASCADE | 1 : * | ✅ |
| DoctorProfile → User (approved_by) | `007_migration` L33 `approved_by UUID REFERENCES auth.users(id)` | 0..1 | Catatan (tidak ditampilkan) |

---

## G. Hasil Verifikasi File

| File | Status |
|------|--------|
| `CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE_RAPI_REVISI_FINAL.drawio` | ✅ Valid XML, dapat dibuka di diagrams.net |
| `CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE_RAPI_REVISI_FINAL.png` | ✅ Valid render (4260×4050 px), background putih, teks readable |
| `CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE_RAPI_REVISI_FINAL.svg` | ✅ Valid XML |
| Visual render | ✅ Tidak overlap, tidak terpotong, sesuai gaya class_diagram_contoh.png |

---

## H. Keterbatasan Audit

1. Audit bersifat struktural, bukan ekstensif terhadap seluruh file source code.
2. Beberapa atribut dan operasi dikeluarkan dari diagram final sederhana sesuai keputusan penyederhanaan.
3. Beberapa relasi database ditampilkan sebagai representasi konseptual, bukan sebagai ERD.
4. ModelConfig diperlakukan sebagai bagian internal ModelService (aggregation), meski dalam implementasi adalah variabel global MODEL_CONFIG yang diteruskan sebagai parameter.

---

## I. Kesimpulan

Class Diagram versi **FINAL SIMPLE RAPI REVISI FINAL** telah melalui audit menyeluruh dan dinyatakan **FINAL — LULUS** untuk digunakan sebagai Gambar 4.x pada Bab IV skripsi S1. Diagram ini mencakup semua komponen inti yang diperlukan, terutama StorageService dan AnalysisJobQueue yang merupakan komponen inti pada alur Upload Image dan Segmentation, serta telah memperbaiki penggunaan jenis relasi UML sesuai standar.

---
