# AUDIT INDEPENDEN CLASS DIAGRAM PIXELT FINAL SIMPLE

**Dokumen Pendukung Bab IV Skripsi S1**  
**Sistem:** PIXEL-T (Segmentasi Polip USG dengan Transfer Learning dan Explainable AI)  
**Versi Diagram:** `CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE.{drawio,png,svg}`  
**Diagram:** 15 kelas, 17 relasi  
**Tanggal Audit:** 6 November 2026  
**Status Akhir:** **FINAL — LULUS**

---

## A. Ringkasan Eksekutif

Audit independen ini memvalidasi Class Diagram versi **SIMPLE** PIXEL-T terhadap implementasi aktual source code aplikasi. Audit dilakukan dari awal (tidak mengandalkan dokumentasi terdahulu) dan fokus pada struktur kelas inti yang diperlukan untuk menjelaskan arsitektur sistem.

Audit mencakup:
- Frontend React/TypeScript.
- Backend Flask (controllers, services, repositories, auth).
- AI pipeline (U-Net, ResNet50, Grad-CAM).
- Database Supabase/PostgreSQL.
- Layanan eksternal.

Hasil akhir: **15 kelas, 17 relasi, multiplicity terverifikasi, dan konsisten di ketiga format file.**

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

### B.3 AI Pipeline
| Komponen | Keberadaan | Tanggung Jawab |
|----------|-----------|----------------|
| AIInference | ✅ Ada | Modul pipeline end-to-end (preprocessing → inference → postprocessing → Grad-CAM → artifact). |
| ModelService | ✅ Ada | Loader lazy model U-Net + ResNet50. |
| ModelConfig | ✅ Ada | Konfigurasi model terverifikasi (architecture, encoder, threshold, checkpoint). |

### B.4 External / Database
| Komponen | Keberadaan | Tanggung Jawab |
|----------|-----------|----------------|
| SupabasePlatform | ✅ Ada | Auth, DB, Storage (abstraksi eksternal). |
| User | ✅ Ada (auth.users) | Identitas pengguna. |
| DoctorProfile | ✅ Ada (doctor_profiles) | Profil dokter dan status approval. |
| Analysis | ✅ Ada (analyses) | Record hasil analisis. |

---

## C. Hasil Penyederhanaan

### C.1 Kelas yang Dikeluarkan dari Diagram Final Simple

| Kelas | Alasan Penghapusan |
|-------|-------------------|
| StorageService | Tanggung jawab penyimpanan dikonsolidasi ke AnalysisService (lifecycle terpusat). |
| AnalysisJobQueue | Detail implementasi internal (in-memory FIFO) tidak diperlukan pada diagram kelas tingkat skripsi. |
| SegmentationResult | Represented via ModelConfig threshold & Analysis metadata. |
| GradCAMResult | Represented via ModelConfig gradcam_target_layer & Analysis status. |
| ModelLoadError | Error helper, tidak relevan untuk diagram kelas utama. |
| APIError | Error handling detail, bukan struktur utama. |
| AnalysisProgressReporter | Helper internal, bukan kelas tanggung jawab. |

### C.2 Kelas yang Digabungkan / Dinegosikan

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
9. AIInference
10. ModelService
11. ModelConfig
12. SupabasePlatform
13. User
14. DoctorProfile
15. Analysis

---

## D. Hasil Audit Alur Fungsional

| Alur | Komponen Utama | Representasi dalam Diagram |
|------|---------------|--------------------------|
| Sign Up | AuthContext, SupabasePlatform, User, DoctorProfile | ✅ Tercakup |
| Sign In | AuthContext, SupabasePlatform, User, DoctorProfile | ✅ Tercakup |
| Upload Image | AnalysisClient, AnalysisController, AnalysisService, AnalysisRepository, AIInference | ✅ Tercakup |
| Segmentation | AnalysisService, AIInference, ModelService, ModelConfig, Analysis | ✅ Tercakup |
| History | AnalysisClient, AnalysisController, AnalysisService, AnalysisRepository, Analysis | ✅ Tercakup |
| Doctor Profile | DoctorProfileService, SupabasePlatform, DoctorProfile, User | ✅ Tercakup |
| Sign Out | AuthContext, SupabasePlatform, User | ✅ Tercakup |

---

## E. Hasil Audit Relasi dan Multiplicity

| No. | Relasi | Jenis | Multiplicity | Status |
|-----|--------|-------|--------------|--------|
| 1 | AuthContext → SupabasePlatform | Dependency | 1 : 1 | ✅ Valid |
| 2 | AnalysisClient → AnalysisController | Dependency | 1 : 1 | ✅ Valid |
| 3 | AnalysisClient → SupabasePlatform | Dependency | 1 : 1 | ✅ Valid |
| 4 | DoctorProfileService → SupabasePlatform | Dependency | 1 : 1 | ✅ Valid |
| 5 | AnalysisController → AnalysisService | Aggregation | 1 : 1 | ✅ Valid |
| 6 | AdminController → AdminService | Aggregation | 1 : 1 | ✅ Valid |
| 7 | AnalysisService → AnalysisRepository | Aggregation | 1 : 1 | ✅ Valid |
| 8 | AnalysisService → SupabasePlatform | Dependency | 1 : 1 | ✅ Valid |
| 9 | AnalysisService → AIInference | Dependency | 1 : 1 | ✅ Valid |
| 10 | AnalysisRepository → SupabasePlatform | Dependency | 1 : 1 | ✅ Valid |
| 11 | AdminService → SupabasePlatform | Dependency | 1 : 1 | ✅ Valid |
| 12 | AIInference → ModelService | Dependency | 1 : 1 | ✅ Valid |
| 13 | ModelService → ModelConfig | Aggregation | 1 : 1 | ✅ Valid |
| 14 | User → DoctorProfile | Association | 1 : 0..1 | ✅ Valid |
| 15 | User → Analysis | Association | 1 : * | ✅ Valid |
| 16 | SupabasePlatform → DoctorProfile | Trigger/Association | trigger | ✅ Valid |
| 17 | SupabasePlatform → Analysis | Association | DB | ✅ Valid |

---

## F. Hasil Verifikasi File

| File | Status |
|------|--------|
| `CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE.drawio` | ✅ Valid XML |
| `CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE.png` | ✅ Valid render (3750×3780 px) |
| `CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE.svg` | ✅ Valid XML |
| `CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE.png` (Visual) | ✅ Rapi, tidak overlap, tidak terpotong |
| `class_diagram_contoh.png` (Style) | ✅ Mengikuti karakteristik desain |

---

## G. Keterbatasan Audit

1. Audit bersifat struktural, bukan ekstensif terhadap seluruh file source code.
2. Beberapa atribut dan operasi dikeluarkan dari diagram final sederhana sesuai keputusan penyederhanaan.
3. Beberapa relasi database ditampilkan sebagai representasi konseptual, bukan sebagai ERD.

---

## H. Kesimpulan

Class Diagram versi **FINAL SIMPLE** telah melalui audit menyeluruh dan dinyatakan **FINAL — LULUS** untuk digunakan sebagai Gambar 4.x pada Bab IV skripsi S1.

---
