# AUDIT DAN VALIDASI CLASS DIAGRAM FINAL PIXEL-T

## A. Ringkasan Arsitektur PIXEL-T

PIXEL-T adalah aplikasi web berbasis React (frontend) dan Flask (backend) dengan integrasi Supabase Auth/PostgreSQL/Storage serta pipeline AI berbasis PyTorch untuk segmentasi citra medis. Struktur inti yang dimodelkan pada Class Diagram final adalah:

- **Autentikasi dan otorisasi**: `AuthContext`, `auth_users` (Supabase Auth), `doctor_profiles`.
- **Manajemen dokter/admin**: `AdminController`, `AdminService`, `doctor_profiles`.
- **Analisis citra**: `AnalysisClient`, `AnalysisController`, `AnalysisService`, `AnalysisRepository`, `StorageService`, `AnalysisJobQueue`, `AnalysisProgressReporter`.
- **Pipeline AI**: `AIInferenceFunctions`, `ModelService`, `ModelConfig`, `PipelineResult`, `SegmentationResult`, `GradCAMResult`.
- **Data dan error handling**: `analyses`, `APIError`.

Class Diagram yang dihasilkan bersifat konseptual pada komponen frontend yang fungsional (React functional component/context/module), sedangkan komponen backend yang memang berupa class Python dimodelkan sebagai class UML.

## B. Analisis Desain Visual ERD_contoh.png

Karakteristik visual referensi yang diterapkan:

- Format persegi sederhana (`451 x 451` piksel), monokrom hitam-putih.
- Tidak ada warna, gradient, ikon, bayangan, atau dekorasi.
- Kotak kelas sederhana dengan border hitam tipis.
- Nama kelas tebal dan ditengah.
- Stereotype ditulis miring di atas nama kelas.
- Atribut dan operasi dipisah dengan garis horizontal tipis.
- Visibilitas menggunakan `+` dan `-`.
- Format atribut/operasi `nama: tipe`.
- Relasi sederhana dengan garis hitam dan label teks.
- Whitespace tinggi, kepadatan rendah, keterbacaan diprioritaskan.

Prinsip yang digunakan: **same visual style, different diagram semantics and content**. Gaya visual ERD_contoh.png ditiru, tetapi isi, struktur kelas, atribut, operasi, dan relasi berasal dari implementasi PIXEL-T.

## C. Ruang Lingkup dan Daftar Kelas Final

Total 21 kelas/abstraksi konseptual:

1. `AuthContext` — modul frontend autentikasi/session/role.
2. `AnalysisClient` — modul frontend komunikasi API analisis.
3. `DoctorProfileService` — modul frontend profil dokter.
4. `AdminController` — controller backend admin.
5. `AnalysisController` — controller backend analisis.
6. `AdminService` — service backend admin.
7. `AnalysisService` — service backend analisis.
8. `AnalysisRepository` — repository akses data analisis.
9. `StorageService` — service storage Supabase.
10. `AnalysisJobQueue` — antrean job analisis.
11. `AnalysisProgressReporter` — pelapor progres analisis.
12. `AIInferenceFunctions` — modul fungsi pipeline AI.
13. `ModelService` — layanan model PyTorch.
14. `ModelConfig` — konfigurasi model.
15. `PipelineResult` — hasil pipeline.
16. `SegmentationResult` — hasil segmentasi.
17. `GradCAMResult` — hasil Grad-CAM.
18. `auth_users` — entitas eksternal Supabase Auth.
19. `doctor_profiles` — entitas domain dokter.
20. `analyses` — entitas domain analisis.
21. `APIError` — exception aplikasi.

Komponen React lain (mis. `AdminDashboard`, `Dashboard`, `NewAnalysis`) tidak dimasukkan sebagai kelas terpisah karena merupakan functional component. Tanggung jawab inti admin tetap direpresentasikan melalui `AdminController` dan `AdminService`.

## D. Atribut dan Operasi

### Autentikasi
- `AuthContext`: `user`, `session`, `loading`, `role`, `accountStatus`; operasi `signIn`, `signUp`, `signOut`.
- `auth_users`: `id`.

### Profil Dokter dan Admin
- `DoctorProfileService`: `fetchDoctorProfile`, `saveDoctorProfile`, `calculateCompleteness`, `validateProfileData`.
- `AdminController`: `list_doctors`, `get_doctor`, `approve_doctor`, `reject_doctor`, `get_statistics`.
- `AdminService`: `list_doctors`, `get_doctor`, `approve_doctor`, `reject_doctor`, `get_statistics`.
- `doctor_profiles`: `id`, `user_id`, `full_name`, `primary_specialty`, `hospital`, `account_status`, `approved_by`, `approved_at`, `education`, `experience`, `bio`.

Catatan: `approved_by` dan `approved_at` direpresentasikan sesuai implementasi approval dokter. Nilai `approved_by` diambil dari token terverifikasi backend, bukan input frontend.

### Analisis
- `AnalysisClient`: `createAnalysis`, `getAnalysis`, `listHistory`, `deleteAnalysis`.
- `AnalysisController`: `create_analysis`, `get_analysis`, `list_history`, `delete_analysis`.
- `AnalysisService`: `validate_and_decode_image`, `create_analysis`, `get_analysis`, `list_user_analyses`, `delete_analysis`.
- `AnalysisRepository`: `create`, `get_by_id`, `list_by_user`, `update`, `delete`.
- `StorageService`: `upload_file`, `create_signed_url`, `delete_analysis_files`.
- `AnalysisJobQueue`: `try_enqueue`, `contains`, `pending_count`, `drain_one`.
- `AnalysisProgressReporter`: `on_phase`, `on_pass`, `percent`.
- `analyses`: `id`, `user_id`, `status`, `segmentation_status`, `gradcam_status`, `summary_text`, `created_at`, `completed_at`, `updated_at`.

### AI
- `AIInferenceFunctions`: `run_pipeline`, `predict`, `postprocess_mask`, `measure_mask`, `generate_gradcam`, `prepare_image`.
- `ModelService`: `load`, `metadata`, `predict_logits`, `get_gradcam_target_layer`.
- `ModelConfig`: atribut konfigurasi model dan checkpoint.
- `PipelineResult`, `SegmentationResult`, `GradCAMResult`: data hasil inferensi.

### Error
- `APIError`: `code`, `message`, `status_code`, `to_dict`.

## E. Penjelasan Relasi

- `AuthContext` menggunakan `auth_users` (Supabase Auth) untuk identitas pengguna.
- `AnalysisClient` berkomunikasi dengan `AnalysisController` melalui HTTP/REST.
- `DoctorProfileService` mengakses `doctor_profiles`.
- `AdminController` memanggil `AdminService` dan dapat menaikkan `APIError`.
- `AnalysisController` memanggil `AnalysisService` dan dapat menaikkan `APIError`.
- `AdminService` mengakses `doctor_profiles`.
- `AnalysisService` memiliki komposisi dengan `AnalysisRepository`, `StorageService`, dan `AnalysisJobQueue`.
- `AnalysisService` menggunakan `AnalysisProgressReporter` dan `AIInferenceFunctions`.
- `AnalysisProgressReporter` menggunakan `AnalysisRepository`.
- `AnalysisRepository` mengakses `analyses`.
- `AIInferenceFunctions` menggunakan `ModelService` dan menghasilkan `PipelineResult`, `SegmentationResult`, `GradCAMResult`.
- `PipelineResult` memiliki komposisi dengan `GradCAMResult`.
- `ModelService` menggunakan `ModelConfig`.
- `auth_users` berelasi dengan `analyses` (satu pengguna memiliki banyak analisis).
- `auth_users` berelasi dengan `doctor_profiles` (satu pengguna memiliki maksimal satu profil dokter).

## F. Matriks Validasi Kode

| No | Elemen Diagram | Bukti Kode | Lokasi File | Status |
|---|---|---|---|---|
| 1 | `AuthContext` | `createContext`, `signIn`, `signUp`, `signOut`, `role`, `accountStatus` | `frontend/src/context/AuthContext.tsx` | TERVERIFIKASI |
| 2 | `AnalysisClient` | `createAnalysis`, `getAnalysis`, `listHistory`, `deleteAnalysis` | `frontend/src/services/analysis.ts` | TERVERIFIKASI |
| 3 | `DoctorProfileService` | `fetchDoctorProfile`, `saveDoctorProfile`, `calculateCompleteness`, `validateProfileData` | `frontend/src/services/profile.ts` | TERVERIFIKASI |
| 4 | `AdminController` | `list_doctors`, `get_doctor`, `approve_doctor`, `reject_doctor`, `get_statistics` | `backend/app/controllers/admin_controller.py` | TERVERIFIKASI |
| 5 | `AnalysisController` | `create_analysis`, `get_analysis`, `list_history`, `delete_analysis` | `backend/app/controllers/analysis_controller.py` | TERVERIFIKASI |
| 6 | `AdminService` | `list_doctors`, `get_doctor`, `approve_doctor`, `reject_doctor`, `get_statistics` | `backend/app/services/admin_service.py` | TERVERIFIKASI |
| 7 | `AnalysisService` | `validate_and_decode_image`, `create_analysis`, `get_analysis`, `list_user_analyses`, `delete_analysis` | `backend/app/services/analysis_service.py` | TERVERIFIKASI |
| 8 | `AnalysisRepository` | `create`, `get_by_id`, `list_by_user`, `update`, `delete` | `backend/app/repositories/analysis_repository.py` | TERVERIFIKASI |
| 9 | `StorageService` | `upload_file`, `create_signed_url`, `delete_analysis_files` | `backend/app/services/storage_service.py` | TERVERIFIKASI |
| 10 | `AnalysisJobQueue` | `try_enqueue`, `contains`, `pending_count`, `drain_one` | `backend/app/services/analysis_service.py` | TERVERIFIKASI |
| 11 | `AnalysisProgressReporter` | `on_phase`, `on_pass`, `percent` | `backend/app/services/analysis_service.py` | TERVERIFIKASI |
| 12 | `AIInferenceFunctions` | `run_pipeline`, `predict`, `postprocess_mask`, `measure_mask`, `generate_gradcam`, `prepare_image` | `ai/inference/pipeline.py`, `segmentation.py`, `postprocessing.py`, `gradcam.py`, `preprocessing.py` | TERVERIFIKASI |
| 13 | `ModelService` | `load`, `metadata`, `predict_logits`, `get_gradcam_target_layer` | `ai/inference/model_service.py` | TERVERIFIKASI |
| 14 | `ModelConfig` | atribut konfigurasi model dan checkpoint | `ai/config/model_config.py` | TERVERIFIKASI |
| 15 | `PipelineResult`, `SegmentationResult`, `GradCAMResult` | dataclass hasil inferensi | `ai/inference/pipeline.py`, `segmentation.py`, `gradcam.py` | TERVERIFIKASI |
| 16 | `auth_users` | identitas pengguna Supabase Auth | Supabase Auth | TERVERIFIKASI |
| 17 | `doctor_profiles` | `id`, `user_id`, `account_status`, `approved_by`, `approved_at` | migration 007 dan `admin_service.py` | TERVERIFIKASI |
| 18 | `analyses` | field inti analisis | `analysis_repository.py` dan migration | SEBAGIAN TERVERIFIKASI |
| 19 | `APIError` | `code`, `message`, `status_code`, `to_dict` | `backend/app/core/errors.py` | TERVERIFIKASI |

## G. Elemen yang Belum Terverifikasi / Keputusan Pemodelan

1. `ProfileCompleteness` pada `DoctorProfileService.calculateCompleteness` merupakan tipe konseptual; bukti tipe eksplisit tidak diverifikasi pada sesi ini.
2. `AdminDashboard` tidak dimodelkan sebagai kelas terpisah karena merupakan React functional component. Tanggung jawab inti admin direpresentasikan melalui `AdminController` dan `AdminService`.
3. Multiplicity pada relasi tidak disalin otomatis dari ERD; hanya relasi utama yang diperlukan untuk struktur sistem yang ditampilkan.
4. Field `analyses` disederhanakan menjadi field inti; tidak semua kolom database ditampilkan agar diagram tetap ringkas.
5. Relasi `approved_by` ke `auth_users` tidak digambarkan sebagai relasi terpisah untuk menjaga kesederhanaan, meskipun kolom tersebut ada pada `doctor_profiles`.

## H. Pemeriksaan UML

- Setiap kelas memiliki nama yang jelas.
- Atribut dan operasi mengikuti format UML `nama: tipe`.
- Visibilitas menggunakan `+` dan `-`.
- Relasi menggunakan association dan dependency yang sesuai dengan tanggung jawab kelas.
- Composition digunakan untuk kepemilikan objek yang jelas (`AnalysisService` terhadap repository/storage/queue, `PipelineResult` terhadap `GradCAMResult`).
- Inheritance tidak digunakan karena tidak ditemukan bukti inheritance pada kelas inti.
- Aggregation/composition hanya digunakan pada hubungan kepemilikan yang jelas.
- Tidak ada campuran notasi ERD dan Class Diagram.

## I. Hasil Desain Visual

- Gaya visual mengikuti ERD_contoh.png: monokrom, kotak sederhana, garis tipis, tanpa dekorasi.
- Desain tidak terlalu padat: atribut dan operasi disederhanakan ke inti.
- Kotak dan teks proporsional.
- Relasi dapat diikuti dan tidak ada teks terpotong pada PNG yang dihasilkan.
- File Draw.io dapat dibuka dan PNG merupakan hasil ekspor dari diagram yang sama.

## J. File Hasil

1. `C:\Users\nevil\OneDrive\Dokumen\SKRIPSI\WEB_PIXELT\references\bab 4\CLASS_DIAGRAM_PIXELT_FINAL.drawio`
2. `C:\Users\nevil\OneDrive\Dokumen\SKRIPSI\WEB_PIXELT\references\bab 4\CLASS_DIAGRAM_PIXELT_FINAL.png`
3. `C:\Users\nevil\OneDrive\Dokumen\SKRIPSI\WEB_PIXELT\references\bab 4\AUDIT_DAN_VALIDASI_CLASS_DIAGRAM_PIXELT.md`

## K. Status Akhir

STATUS: DIAGRAM SELESAI, VALIDASI SEBAGIAN

Diagram selesai dan file dapat dibuka. Seluruh kelas inti telah divalidasi terhadap kode, tetapi terdapat elemen konseptual (`ProfileCompleteness`) dan penyederhanaan field/relasi yang didokumentasikan pada bagian G.