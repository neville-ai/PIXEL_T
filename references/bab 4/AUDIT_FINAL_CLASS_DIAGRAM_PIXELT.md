# AUDIT FINAL CLASS DIAGRAM PIXEL-T (VERSI SEDERHANA)

## 1. Ringkasan Audit Diagram Sebelumnya

Diagram sebelumnya (`CLASS_DIAGRAM_PIXELT_FINAL.drawio`) memiliki 21 kotak kelas dan 24 relasi. Audit terhadap kode sumber menunjukkan bahwa diagram tersebut terlalu detail untuk penyajian Class Diagram skripsi. Banyak komponen internal (repository, queue, progress reporter, controller HTTP, modul AI rinci, dan tipe hasil inferensi) tidak perlu ditampilkan sebagai kelas terpisah.

Diagram final sederhana (`CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE.drawio`) memiliki 9 kelas/abstraksi dan 9 relasi. Penyederhanaan dilakukan tanpa mengubah kode aplikasi.

## 2. Daftar Kelas yang Dipertahankan

| Kelas | Jenis | Alasan |
|---|---|---|
| `AuthContext` | Abstraksi konseptual | Mewakili autentikasi, session, role, dan status akun pada frontend. |
| `SupabaseAuth` | Layanan eksternal | Sumber identitas pengguna dan autentikasi. |
| `AdminService` | Kelas aktual backend | Tanggung jawab administrasi dan approval dokter. |
| `doctor_profiles` | Entitas data | Profil dokter dan status akun. |
| `AnalysisService` | Kelas aktual backend | Tanggung jawab utama analisis citra. |
| `analyses` | Entitas data | Data hasil dan status analisis. |
| `StorageService` | Kelas aktual backend | Penyimpanan dan pengambilan berkas analisis. |
| `AISegmentationPipeline` | Abstraksi konseptual | Mewakili pipeline AI tanpa memecah fungsi internal. |
| `APIError` | Kelas aktual backend | Struktur error aplikasi. |

## 3. Daftar Kelas yang Dihapus

| Kelas Sebelumnya | Keputusan | Alasan |
|---|---|---|
| `AnalysisClient` | Dihapus | Thin HTTP client frontend; detail komunikasi API tidak diperlukan pada struktur utama. |
| `DoctorProfileService` | Dihapus | Fungsi profil dokter direpresentasikan melalui `doctor_profiles` dan `AdminService`. |
| `AdminController` | Dihapus | Controller HTTP adalah adapter; tanggung jawab inti admin berada pada `AdminService`. |
| `AnalysisController` | Dihapus | Controller HTTP adalah adapter; tanggung jawab inti analisis berada pada `AnalysisService`. |
| `AnalysisRepository` | Digabung ke `AnalysisService` | Repository adalah detail akses data, bukan struktur sistem utama. |
| `AnalysisJobQueue` | Dihapus | Detail internal antrean job. |
| `AnalysisProgressReporter` | Dihapus | Progres lebih tepat menjadi atribut/status pada `analyses`. |
| `ModelService` | Digabung ke `AISegmentationPipeline` | Detail internal model. |
| `ModelConfig` | Digabung ke `AISegmentationPipeline` | Detail konfigurasi model. |
| `PipelineResult` | Digabung ke `AISegmentationPipeline` | Tipe hasil internal pipeline. |
| `SegmentationResult` | Digabung ke `AISegmentationPipeline` | Tipe hasil internal segmentasi. |
| `GradCAMResult` | Digabung ke `AISegmentationPipeline` | Tipe hasil internal Grad-CAM. |
| `AdminDashboard` | Tidak dimodelkan | React functional component, bukan kelas UML aktual. |

## 4. Atribut dan Operasi Final

### `AuthContext`
- Atribut: `user`, `session`, `role`, `accountStatus`
- Operasi: `signIn`, `signUp`, `signOut`

### `SupabaseAuth`
- Atribut: `id`

### `AdminService`
- Atribut: `client`
- Operasi: `list_doctors`, `approve_doctor`, `reject_doctor`, `get_statistics`

### `doctor_profiles`
- Atribut: `id`, `user_id`, `full_name`, `primary_specialty`, `hospital`, `account_status`, `approved_by`, `approved_at`

### `AnalysisService`
- Atribut: `repository`, `storage_service`
- Operasi: `create_analysis`, `get_analysis`, `list_user_analyses`, `delete_analysis`

### `analyses`
- Atribut: `id`, `user_id`, `status`, `segmentation_status`, `gradcam_status`, `summary_text`, `created_at`, `completed_at`

### `StorageService`
- Atribut: `bucket_name`
- Operasi: `upload_file`, `create_signed_url`, `delete_analysis_files`

### `AISegmentationPipeline`
- Operasi: `run_pipeline`, `predict`, `generate_gradcam`

### `APIError`
- Atribut: `code`, `message`, `status_code`
- Operasi: `to_dict`

## 5. Relasi Final

| Relasi | Jenis | Alasan |
|---|---|---|
| `AuthContext` -> `SupabaseAuth` | Dependency | Autentikasi menggunakan Supabase Auth. |
| `AdminService` -> `doctor_profiles` | Dependency | Administrasi mengelola profil dokter. |
| `AnalysisService` -> `analyses` | Dependency | Analisis mengelola data analisis. |
| `AnalysisService` -> `StorageService` | Dependency | Analisis menggunakan storage. |
| `AnalysisService` -> `AISegmentationPipeline` | Dependency | Analisis memanggil pipeline AI. |
| `AdminService` -> `APIError` | Dependency | Error handling admin. |
| `AnalysisService` -> `APIError` | Dependency | Error handling analisis. |
| `doctor_profiles` -> `SupabaseAuth` | Association | `user_id` mereferensikan pengguna Supabase Auth. |
| `analyses` -> `SupabaseAuth` | Association | `user_id` mereferensikan pengguna Supabase Auth. |

Multiplicity tidak dicantumkan secara eksplisit agar diagram tetap sederhana. Relasi `approved_by` terhadap `auth.users` tidak digambarkan sebagai relasi terpisah; kolom tersebut direpresentasikan sebagai atribut `approved_by`.

## 6. Matriks Validasi terhadap Kode

| No | Elemen | Jenis | Bukti Implementasi | File | Status |
|---|---|---|---|---|---|
| 1 | `AuthContext` | Abstraksi konseptual | `createContext`, `signIn`, `signUp`, `signOut`, `role`, `accountStatus` | `frontend/src/context/AuthContext.tsx` | TERVERIFIKASI |
| 2 | `SupabaseAuth` | Layanan eksternal | Supabase Auth | Supabase | TERVERIFIKASI |
| 3 | `AdminService` | Kelas aktual | `list_doctors`, `approve_doctor`, `reject_doctor`, `get_statistics` | `backend/app/services/admin_service.py` | TERVERIFIKASI |
| 4 | `doctor_profiles` | Entitas data | `id`, `user_id`, `account_status`, `approved_by`, `approved_at` | migration 007, `admin_service.py` | TERVERIFIKASI |
| 5 | `AnalysisService` | Kelas aktual | `create_analysis`, `get_analysis`, `list_user_analyses`, `delete_analysis` | `backend/app/services/analysis_service.py` | TERVERIFIKASI |
| 6 | `analyses` | Entitas data | Field inti analisis | `analysis_repository.py`, migration | SEBAGIAN TERVERIFIKASI |
| 7 | `StorageService` | Kelas aktual | `upload_file`, `create_signed_url`, `delete_analysis_files` | `backend/app/services/storage_service.py` | TERVERIFIKASI |
| 8 | `AISegmentationPipeline` | Abstraksi konseptual | `run_pipeline`, `predict`, `generate_gradcam` | `ai/inference/*.py` | TERVERIFIKASI |
| 9 | `APIError` | Kelas aktual | `code`, `message`, `status_code`, `to_dict` | `backend/app/core/errors.py` | TERVERIFIKASI |

## 7. Elemen yang Masih Belum Terverifikasi

1. `ProfileCompleteness` tidak dimodelkan sebagai kelas; tipe hasilnya tidak diverifikasi secara eksplisit.
2. `approved_by` memiliki foreign key ke `auth.users(id)` pada migration 007, tetapi relasi tersebut tidak digambarkan sebagai association terpisah agar diagram tetap sederhana.
3. Field `analyses` disederhanakan; tidak semua kolom database ditampilkan.
4. `AuthContext` adalah abstraksi konseptual dari React context, bukan kelas Python aktual.

## 8. Evaluasi Kesesuaian Desain dengan Referensi

Desain final mengikuti `class_diagram_contoh.png`:
- Monokrom hitam-putih.
- Kotak kelas sederhana.
- Nama kelas tebal dan di tengah.
- Stereotype miring.
- Atribut/operasi dipisah garis tipis.
- Tidak ada ikon, badge, bayangan, gradient, atau dekorasi.
- Kepadatan rendah dan teks terbaca.

## 9. Kesimpulan Kelayakan Diagram untuk Skripsi

Diagram final sederhana cukup untuk menjelaskan struktur utama PIXEL-T tanpa menampilkan detail internal yang tidak diperlukan. Semua kelas yang tersisa memiliki bukti implementasi atau merupakan abstraksi konseptual yang dijelaskan.

## 10. Lokasi Hasil

- `C:\Users\nevil\OneDrive\Dokumen\SKRIPSI\WEB_PIXELT\references\bab 4\CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE.drawio`
- `C:\Users\nevil\OneDrive\Dokumen\SKRIPSI\WEB_PIXELT\references\bab 4\CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE.png`
- `C:\Users\nevil\OneDrive\Dokumen\SKRIPSI\WEB_PIXELT\references\bab 4\AUDIT_FINAL_CLASS_DIAGRAM_PIXELT.md`

## 11. Status Akhir

STATUS: **SELESAI DENGAN VALIDASI SEBAGIAN**

Diagram selesai dan file dapat dibuka. Semua kelas inti terverifikasi, tetapi terdapat abstraksi konseptual dan penyederhanaan yang didokumentasikan.