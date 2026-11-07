# AUDIT FINAL CLASS DIAGRAM PIXEL-T (NEAT)

## 1. Evaluasi Diagram Sebelumnya

Diagram `CLASS_DIAGRAM_PIXELT_FINAL_SIMPLE` memiliki 9 kelas/abstraksi dan 9 relasi. Audit ulang menunjukkan struktur dasarnya dapat dipertahankan, tetapi relasi masih menggunakan label kata (`manages`, `uses`, `raises`, `FK user_id`, `Supabase Auth`). Label tersebut bukan pengganti multiplicity UML dan perlu diganti dengan angka `1` dan `*` atau notasi multiplicity yang benar pada ujung relasi.

Diagram `CLASS_DIAGRAM_PIXELT_FINAL_NEAT` mempertahankan 9 kelas/abstraksi dan 9 relasi, tetapi seluruh relasi kini menggunakan multiplicity, bukan label kata.

## 2. Daftar Kelas Final

1. `AuthContext` — abstraksi konseptual frontend
2. `SupabaseAuth` — layanan eksternal
3. `AdminService` — kelas aktual backend
4. `doctor_profiles` — entitas data
5. `AnalysisService` — kelas aktual backend
6. `analyses` — entitas data
7. `StorageService` — kelas aktual backend
8. `AISegmentationPipeline` — abstraksi konseptual
9. `APIError` — kelas aktual backend

## 3. Kelas yang Dipertahankan

| Kelas | Jenis | Alasan |
|---|---|---|
| `AuthContext` | Abstraksi konseptual | Mewakili autentikasi, session, role, dan status akun. |
| `SupabaseAuth` | Layanan eksternal | Sumber identitas pengguna. |
| `AdminService` | Kelas aktual | Administrasi dan approval dokter. |
| `doctor_profiles` | Entitas data | Profil dokter dan status akun. |
| `AnalysisService` | Kelas aktual | Analisis citra dan orkestrasi hasil. |
| `analyses` | Entitas data | Data hasil dan status analisis. |
| `StorageService` | Kelas aktual | Penyimpanan dan pengambilan berkas. |
| `AISegmentationPipeline` | Abstraksi konseptual | Mewakili pipeline AI tanpa memecah fungsi internal. |
| `APIError` | Kelas aktual | Struktur error aplikasi. |

## 4. Kelas yang Dihapus atau Digabungkan

Kelas yang dihapus dari diagram sebelumnya tetap tidak ditampilkan:
- `AnalysisClient`
- `DoctorProfileService`
- `AdminController`
- `AnalysisController`
- `AnalysisRepository`
- `AnalysisJobQueue`
- `AnalysisProgressReporter`
- `ModelService`
- `ModelConfig`
- `PipelineResult`
- `SegmentationResult`
- `GradCAMResult`
- `AdminDashboard`

Alasan utama: detail internal, adapter HTTP, komponen React, dan tipe hasil inferensi tidak diperlukan untuk Class Diagram skripsi.

## 5. Atribut dan Operasi Final

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

## 6. Relasi dan Multiplicity Final

| Relasi | Jenis | Multiplicity | Makna |
|---|---|---|---|
| `AuthContext` — `SupabaseAuth` | Association | `1` — `1` | Satu context autentikasi merepresentasikan satu pengguna terautentikasi. |
| `AdminService` — `doctor_profiles` | Association | `1` — `*` | Satu service admin dapat mengelola banyak profil dokter. |
| `AnalysisService` — `analyses` | Association | `1` — `*` | Satu service analisis dapat mengelola banyak analisis. |
| `AnalysisService` — `StorageService` | Association | `1` — `1` | Satu service analisis menggunakan satu service storage. |
| `AnalysisService` — `AISegmentationPipeline` | Association | `1` — `1` | Satu service analisis memanggil satu pipeline AI. |
| `AdminService` — `APIError` | Dependency | — | Service admin dapat menaikkan error. |
| `AnalysisService` — `APIError` | Dependency | — | Service analisis dapat menaikkan error. |
| `doctor_profiles` — `SupabaseAuth` | Association | `0..1` — `1` | Satu profil dokter milik tepat satu pengguna; satu pengguna (auth.users) dapat memiliki nol atau satu profil dokter (constraint UNIQUE(user_id)). |
| `analyses` — `SupabaseAuth` | Association | `*` — `1` | Banyak analisis milik satu pengguna; satu analisis milik satu pengguna. |

Multiplicity `*` berarti nol hingga banyak (`0..*`). Jika minimal satu data diwajibkan, notasi yang benar adalah `1..*`.

## 6a. Perubahan Tata Letak (Revisi Struktural)

Penataan ulang posisi kelas dilakukan agar hubungan struktural mudah diikuti dan tidak menyilang:

| Kelas | Posisi Baru | Alasan Penempatan |
|---|---|---|
| `SupabaseAuth` | Atas tengah | Hub utama identitas pengguna; `AuthContext`, `doctor_profiles`, dan `analyses` terhubung kepadanya. |
| `AuthContext` | Kiri atas | Kelas frontend yang merepresentasikan pengguna terautentikasi; berdekatan dengan `SupabaseAuth`. |
| `doctor_profiles` | Kanan atas | Entitas profil dokter; berdekatan dengan `SupabaseAuth` (FK `user_id`) dan `AdminService`. |
| `analyses` | Kanan atas (kanan) | Entitas hasil analisis; berdekatan dengan `SupabaseAuth` (FK `user_id`) dan `AnalysisService`. |
| `AdminService` | Kiri tengah | Mengelola `doctor_profiles` dan dapat menaikkan `APIError`; berdekatan dengan `doctor_profiles`. |
| `AnalysisService` | Tengah bawah | Mengelola `analyses`, menggunakan `StorageService` dan `AISegmentationPipeline`, dapat menaikkan `APIError`. |
| `StorageService` | Tengah bawah (bawah) | Penyimpanan berkas; berdekatan dengan `AnalysisService`. |
| `AISegmentationPipeline` | Kanan bawah | Pipeline AI; berdekatan dengan `AnalysisService`. |
| `APIError` | Kanan tengah | Struktur error; berdekatan dengan `AdminService` dan `AnalysisService`. |

Semua konektor menggunakan jalur orthogonal (siku-siku) dengan jumlah belokan minimal. Tidak ada garis yang menyilang atau menembus kotak kelas lain (diverifikasi secara programatik). Multiplicity label ditempatkan tepat di dekat ujung relasi yang bersangkutan, dengan offset manual untuk menghindari tumpang tindih pada tepi kotak yang sama.

## 6b. Evaluasi Garis dan Persilangan

- Semua 9 relasi diverifikasi tidak menyilang kotak kelas lain.
- Tidak ada konektor yang bertumpuk.
- Multiplicity label tidak bertumpuk dengan kotak kelas maupun label lain.
- Jenis relasi: Association (solid) untuk hubungan struktural; Dependency (dashed, open arrow) untuk `AdminService` — `APIError` dan `AnalysisService` — `APIError`.

## 7. Bukti Source Code

- `AuthContext`: `frontend/src/context/AuthContext.tsx` (baris 16-33, 136-162)
- `AdminService`: `backend/app/services/admin_service.py` (baris 27, 42, 135, 235, 328)
- `doctor_profiles`: `database/migrations/007_add_role_and_account_status.sql` (baris 33), `admin_service.py` (baris 55, 119, 128)
- `AnalysisService`: `backend/app/services/analysis_service.py` (baris 269, 369, 502, 635, 688)
- `analyses`: `backend/app/repositories/analysis_repository.py` (baris 38, 71, 100, 133, 172)
- `StorageService`: `backend/app/services/storage_service.py` (baris 7, 119, 149, 175)
- `AISegmentationPipeline`: `ai/inference/pipeline.py` (baris 101), `segmentation.py`, `gradcam.py`
- `APIError`: `backend/app/core/errors.py` (baris 8-24)

## 8. Status Verifikasi

| No | Elemen | Jenis | Status |
|---|---|---|---|
| 1 | `AuthContext` | Abstraksi konseptual | TERVERIFIKASI |
| 2 | `SupabaseAuth` | Layanan eksternal | TERVERIFIKASI |
| 3 | `AdminService` | Kelas aktual | TERVERIFIKASI |
| 4 | `doctor_profiles` | Entitas data | TERVERIFIKASI |
| 5 | `AnalysisService` | Kelas aktual | TERVERIFIKASI |
| 6 | `analyses` | Entitas data | SEBAGIAN TERVERIFIKASI |
| 7 | `StorageService` | Kelas aktual | TERVERIFIKASI |
| 8 | `AISegmentationPipeline` | Abstraksi konseptual | TERVERIFIKASI |
| 9 | `APIError` | Kelas aktual | TERVERIFIKASI |

## 9. Evaluasi Desain Visual terhadap Referensi

Desain final mengikuti `class_diagram_contoh.png`:
- Monokrom hitam-putih.
- Kotak kelas sederhana dengan kompartemen nama, atribut, dan operasi.
- Stereotype miring.
- Garis pembatas horizontal tipis.
- Tidak ada ikon, badge, bayangan, gradient, atau dekorasi.
- Relasi menggunakan garis asosiasi sederhana.
- Multiplicity ditampilkan sebagai angka `1`, `*`, dan `0..1`, bukan label kata.
- Posisi kelas disusun ulang berdasarkan keterkaitan struktural; tidak ada persilangan garis (diverifikasi secara programatik).
- Konektor orthogonal dengan belokan minimal; tidak ada garis yang menembus kotak kelas lain.
- Kepadatan rendah dan teks terbaca.

## 10. Referensi UML yang Digunakan

1. Object Management Group (OMG). (2017). *Unified Modeling Language (UML), Version 2.5.1*. https://www.omg.org/spec/UML/2.5.1/PDF
2. Object Management Group (OMG). *Unified Modeling Language*. https://www.omg.org/spec/UML
3. OGC Testbed-17 Engineering Report. Konvensi notasi multiplicity dan konsistensi penulisan kardinalitas. https://docs.ogc.org

## 11. Keterbatasan Audit

1. `AuthContext` adalah abstraksi konseptual dari React Context, bukan kelas Python konkret.
2. `AISegmentationPipeline` adalah abstraksi konseptual dari modul dan fungsi pipeline AI.
3. Field `analyses` disederhanakan; tidak semua kolom database ditampilkan.
4. Relasi `approved_by` terhadap `auth.users` tidak digambarkan sebagai association terpisah; kolom tersebut direpresentasikan sebagai atribut `approved_by`.
5. Multiplicity `0..1` — `1` pada `doctor_profiles` — `SupabaseAuth` (kiri-ke-kanan) ditentukan berdasarkan constraint `UNIQUE(user_id)` pada migration 004/008: satu pengguna memiliki nol atau satu profil dokter; satu profil dokter milik tepat satu pengguna. Posisi 1 dan 0..1 telah diperbaiki agar tidak tertukar.

## 12. Kesimpulan Kelayakan Diagram untuk Skripsi

Diagram final NEAT cukup untuk menjelaskan struktur utama PIXEL-T dengan gaya sederhana seperti referensi. Semua kelas yang tersisa memiliki bukti implementasi atau merupakan abstraksi konseptual yang dijelaskan. Relasi menggunakan multiplicity UML, bukan label kata.

## 13. Lokasi Hasil

- `C:\Users\nevil\OneDrive\Dokumen\SKRIPSI\WEB_PIXELT\references\bab 4\CLASS_DIAGRAM_PIXELT_FINAL_NEAT.drawio`
- `C:\Users\nevil\OneDrive\Dokumen\SKRIPSI\WEB_PIXELT\references\bab 4\CLASS_DIAGRAM_PIXELT_FINAL_NEAT.png`
- `C:\Users\nevil\OneDrive\Dokumen\SKRIPSI\WEB_PIXELT\references\bab 4\AUDIT_FINAL_CLASS_DIAGRAM_PIXELT_NEAT.md`

## 14. Status Akhir

STATUS: **SELESAI DENGAN VALIDASI SEBAGIAN**

Diagram selesai dan file dapat dibuka. Semua kelas inti terverifikasi, tetapi terdapat abstraksi konseptual dan penyederhanaan yang didokumentasikan. Tidak ada kode aplikasi yang diubah.