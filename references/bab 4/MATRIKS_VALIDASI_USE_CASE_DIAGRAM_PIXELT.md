# MATRIKS VALIDASI USE CASE DIAGRAM PIXEL-T

**Dokumen Hasil Validasi — Bab IV Skripsi S1**

Sistem: PIXEL-T (*Polyp Identification with eXplainable Intelligence for Early-stage Local Tissue detection*)

**Diagram yang divalidasi:** `Use Case Diagram PIXELT.png`

**Status:** FINAL REVISI (sesudah perbaikan keempat masalah visual yang diketahui)

---

## A. Inventaris Sumber yang Diperiksa

| No. | Sumber | Jenis | Status Keberadaan |
|-----|--------|-------|-------------------|
| 1 | `Use Case Diagram PIXELT.png` | Gambar raster Use Case Diagram | ✅ Ditemukan |
| 2 | `PENJELASAN_CLASS_DIAGRAM_PIXELT_BAB_IV.md` | Dokumen penjelasan Bab IV (pendukung) | ✅ Ditemukan |
| 3 | `PENJELASAN_ERD_PIXELT_BAB_IV.md` | Dokumen penjelasan Bab IV (pendukung) | ✅ Ditemukan |
| 4 | `PENJELASAN_TUJUU_ACTIVITY_DIAGRAM_PIXELT.md` | Dokumen penjelasan Bab IV (pendukung) | ✅ Ditemukan |
| 5 | `PENJELASAN_TUJUU_SEQUENCE_DIAGRAM_PIXELT_BAB_IV.md` | Dokumen penjelasan Bab IV (pendukung) | ✅ Ditemukan |
| 6 | `VALIDASI_DAN_REVISI_NARASI_SEQUENCE_DIAGRAM_PIXELT.md` | Dokumen validasi narasi (belum ditemukan) | ❌ Tidak ditemukan |
| 7 | `MATRIKS_BUKTI_VALIDASI_SEQUENCE_DIAGRAM_PIXELT.md` | Matriks bukti validasi (belum ditemukan) | ❌ Tidak ditemukan |
| 8 | `LUCIT - BAB 4.docx` | Referensi gaya penulisan Bab IV | ✅ Ditemukan |
| 9 | `Skripsi_Faithza Mandolang dan Grace Bindosano.pdf` | Referensi akademik (lokasi belum konfirmasi) | ⚠️ Belum dikonfirmasi |
| 10 | `frontend/src/**` | Kode sumber frontend React/TypeScript | ✅ Ditemukan |
| 11 | `backend/app/**` | Kode sumber backend Flask | ✅ Ditemukan |
| 12 | `database/migrations/**` | Migrasi SQL (001, 004, 007, 008) | ✅ Ditemukan |
| 13 | `ai/inference/**` | Pipeline AI (U-Net, ResNet50, Grad-CAM) | ✅ Ditemukan |

---

## B. Inventaris Aktor dan Use Case pada Gambar

### B.1 Aktor

| No. | Nama Aktor | Deskripsi | Keterlibatan pada Use Case |
|-----|------------|-----------|---------------------------|
| 1 | **Calon Pengguna** | Individu yang belum memiliki sesi autentikasi aktif; mewakili calon dokter yang belum terdaftar | Sign Up, Sign In |
| 2 | **Dokter / Tenaga Medis** | Tenaga medis yang memiliki akun dan berstatus klinis | Sign In, Sign Out, Upload Image, Segmentation, View History, View Doctor Profile, Edit Doctor Profile |
| 3 | **Admin** | Pengelola sistem yang tidak memiliki fitur klinis | Sign In, Sign Out, View Admin Dashboard, View Doctor Registrations, Approve Doctor Account, Reject Doctor Account |

### B.2 Daftar Use Case

| No. | Nama Use Case | Aktor Utama | Jenis |
|-----|--------------|-------------|-------|
| 1 | Sign Up | Calon Pengguna | Akun baru |
| 2 | Sign In | Calon Pengguna, Dokter, Admin | Autentikasi |
| 3 | Sign Out | Dokter, Admin | Sesi |
| 4 | Reset Password | (melalui Sign In) | Opsional / extend |
| 5 | Upload Image | Dokter | Unggah |
| 6 | Segmentation | Dokter | AI Pipeline |
| 7 | View History | Dokter | Riwayat |
| 8 | Search / Filter History | Dokter | Opsional / extend |
| 9 | View Doctor Profile | Dokter | Profil |
| 10 | Edit Doctor Profile | Dokter | Opsional / extend |
| 11 | View Admin Dashboard | Admin | Admin |
| 12 | View Doctor Registration | Admin | Admin |
| 13 | Approve Doctor Account | Admin | Admin |
| 14 | Reject Doctor Account | Admin | Admin |

---

## C. Matriks Validasi Elemen Use Case

### C.1 Aktor

| No. | Aktor | Asosiasi dengan Use Case | Status | Bukti |
|-----|-------|--------------------------|--------|------|
| 1 | Calon Pengguna | Sign Up, Sign In | ✅ TERVERIFIKASI | `Register.tsx`, `Login.tsx`, `services/auth.ts` |
| 2 | Dokter / Tenaga Medis | Sign In, Sign Out, Upload Image, Segmentation, View History, View Doctor Profile, Edit Doctor Profile | ✅ TERVERIFIKASI | `ProtectedRoute`, `DoctorRoute`, `require_approved_doctor`, `doctor_profiles` |
| 3 | Admin | Sign In, Sign Out, View Admin Dashboard, View Doctor Registrations, Approve Doctor Account, Reject Doctor Account | ✅ TERVERIFIKASI | `AdminRoute`, `require_admin`, `app_metadata.role` |

### C.2 Use Case

| No. | Use Case | Status | Bukti Implementasi |
|-----|----------|--------|--------------------|
| 1 | Sign Up | ✅ TERVERIFIKASI | `Register.tsx` → `registerUser` → `supabase.auth.signUp` + trigger 008 |
| 2 | Sign In | ✅ TERVERIFIKASI | `Login.tsx` → `AuthContext.signIn` → `supabase.auth.signInWithPassword` |
| 3 | Sign Out | ✅ TERVERIFIKASI | `AppShell.tsx` → `signOut` → `supabase.auth.signOut` |
| 4 | Reset Password | ✅ TERVERIFIKASI | `Login.tsx` (mode reset) + `/reset-password` → `supabase.auth.updateUser` |
| 5 | Upload Image | ✅ TERVERIFIKASI | `NewAnalysis.tsx` → `createAnalysis` → `POST /api/analysis` |
| 6 | Segmentation | ✅ TERVERIFIKASI | `analysis_service.py` + `ai/inference/pipeline.py` |
| 7 | View History | ✅ TERVERIFIKASI | `History.tsx` → `listHistory` → `GET /api/history` |
| 8 | Search / Filter History | ✅ TERVERIFIKASI | `History.tsx` (useMemo filter) |
| 9 | View Doctor Profile | ✅ TERVERIFIKASI | `DoctorProfile.tsx` → `fetchDoctorProfile` |
| 10 | Edit Doctor Profile | ✅ TERVERIFIKASI | `DoctorProfile.tsx` → `saveDoctorProfile` |
| 11 | View Admin Dashboard | ✅ TERVERIFIKASI | `AdminDashboard.tsx` → `GET /api/admin/doctors/stats` |
| 12 | View Doctor Registrations | ✅ TERVERIFIKASI | `AdminDashboard.tsx` → `GET /api/admin/doctors` |
| 13 | Approve Doctor Account | ✅ TERVERIFIKASI | `AdminDashboard.tsx` → `POST /api/admin/doctors/<id>/approve` |
| 14 | Reject Doctor Account | ✅ TERVERIFIKASI | `AdminDashboard.tsx` → `POST /api/admin/doctors/<id>/reject` |

### C.3 Relasi UML

| No. | Relasi | Jenis | Arah | Status | Alasan |
|-----|--------|-------|------|--------|--------|
| 1 | Segmentation → Upload Image | `<<include>>` | Base → Included | ✅ VALID | Segmentasi memerlukan citra tersimpan; `POST /api/analysis` menolak tanpa berkas |
| 2 | Reset Password → Sign In | `<<extend>>` | Extending → Base | ✅ VALID | Reset bersifat opsional; hanya saat mode `reset` dipilih |
| 3 | Search / Filter History → View History | `<<extend>>` | Extending → Base | ✅ VALID | Filter bersifat opsional; hanya bila kriteria diisi |
| 4 | Edit Doctor Profile → View Doctor Profile | `<<extend>>` | Extending → Base | ✅ VALID | Edit bersifat opsional; hanya bila modal edit dibuka |
| 5 | Generalization | — | — | ✅ TIDAK DIGUNAKAN | Admin dan Dokter saling eksklusif; generalisasi akan menyesatkan |

---

## D. Matriks Validasi Kondisi dan Alur

### D.1 Sign Up

| Elemen | Pernyataan | Status | Bukti |
|--------|-----------|--------|------|
| Aktor | Calon Pengguna | ✅ TERVERIFIKASI | — |
| Trigger | Pengguna mengakses `/register` dan mengirim formulir | ✅ TERVERIFIKASI | `Register.tsx` |
| Pre-Condition | Pengguna belum memiliki akun | ✅ TERVERIFIKASI | — |
| Normal Course | Validasi → `signUp` → Supabase → trigger 008 | ✅ TERVERIFIKASI | `AuthContext.tsx`, `services/auth.ts`, migrasi 008 |
| Post Condition | Akun dibuat dengan status `pending` | ✅ TERVERIFIKASI | Migrasi 008 |
| Alternative | Konfirmasi email / kegagalan pendaftaran | ✅ SEBAGIAN TERVERIFIKASI | `Register.tsx` (requiresEmailConfirmation) |

### D.2 Sign In

| Elemen | Pernyataan | Status | Bukti |
|--------|-----------|--------|------|
| Aktor | Calon Pengguna, Dokter, Admin | ✅ TERVERIFIKASI | — |
| Trigger | Pengguna mengakses `/login` dan mengirim kredensial | ✅ TERVERIFIKASI | `Login.tsx` |
| Pre-Condition | Pengguna memiliki akun | ✅ TERVERIFIKASI | — |
| Normal Course | Validasi → `signInWithPassword` → sesi aktif | ✅ TERVERIFIKASI | `AuthContext.tsx`, `services/auth.ts` |
| Post Condition | Sesi aktif; navigasi ke Dashboard/Admin | ✅ TERVERIFIKASI | `AuthContext.tsx` |
| Alternative | Kredensial salah / akun belum dikonfirmasi | ✅ TERVERIFIKASI | `formatAuthError()` |

### D.3 Sign Out

| Elemen | Pernyataan | Status | Bukti |
|--------|-----------|--------|------|
| Aktor | Dokter, Admin | ✅ TERVERIFIKASI | — |
| Trigger | Pengguna memilih Sign Out dan mengkonfirmasi | ✅ TERVERIFIKASI | `AppShell.tsx` (modal), `AuthContext.tsx:206` |
| Pre-Condition | Pengguna memiliki sesi aktif | ✅ TERVERIFIKASI | — |
| Normal Course | `signOut` → `supabase.auth.signOut` → sesi dihapus | ✅ TERVERIFIKASI | — |
| Post Condition | Sesi diakhiri; pengguna diarahkan ke `/login` | ✅ TERVERIFIKASI | — |

### D.4 Reset Password

| Elemen | Pernyataan | Status | Bukti |
|--------|-----------|--------|------|
| Aktor | Pengguna berakun | ✅ TERVERIFIKASI | `Login.tsx` (mode reset), `ResetPassword.tsx` |
| Trigger | Pengguna memilih opsi lupa kata sandi | ✅ TERVERIFIKASI | — |
| Normal Course | `resetPasswordForEmail` → `updateUser` | ✅ TERVERIFIKASI | — |
| Post Condition | Kata sandi diperbarui | ✅ TERVERIFIKASI | — |

### D.5 Upload Image

| Elemen | Pernyataan | Status | Bukti |
|--------|-----------|--------|------|
| Aktor | Dokter (`approved`) | ✅ TERVERIFIKASI | `require_approved_doctor` |
| Trigger | Dokter memilih/unggah citra endoskopi | ✅ TERVERIFIKASI | `NewAnalysis.tsx` |
| Pre-Condition | Dokter login & `account_status = 'approved'` | ✅ TERVERIFIKASI | `ProtectedRoute`, `require_approved_doctor` |
| Normal Course | Validasi → `POST /api/analysis` → 202 | ✅ TERVERIFIKASI | `analysis_controller.create_analysis` |
| Post Condition | Citra tersimpan; status `processing` | ✅ TERVERIFIKASI | `StorageService`, `AnalysisRepository` |

### D.6 Segmentation

| Elemen | Pernyataan | Status | Bukti |
|--------|-----------|--------|------|
| Aktor | Dokter (`approved`) | ✅ TERVERIFIKASI | — |
| Trigger | Tugas antrian diproses | ✅ TERVERIFIKASI | `AnalysisJobQueue`, `analysis_service.py` |
| Normal Course | Preprocessing → U-Net → Postprocess → Grad-CAM → Artifact → `completed` | ✅ TERVERIFIKASI | `ai/inference/pipeline.py` |
| Post Condition | Status `completed`; artefak tersimpan | ✅ TERVERIFIKASI | — |
| Alternative | Kegagalan pipeline → status `failed` | ✅ TERVERIFIKASI | — |

### D.7 View History

| Elemen | Pernyataan | Status | Bukti |
|--------|-----------|--------|------|
| Aktor | Dokter (`approved`) | ✅ TERVERIFIKASI | `require_approved_doctor` |
| Trigger | Dokter membuka `/history` | ✅ TERVERIFIKASI | `History.tsx` → `GET /api/history` |
| Pre-Condition | Sesi dokter aktif & approved | ✅ TERVERIFIKASI | — |
| Post Condition | Daftar riwayat ditampilkan | ✅ TERVERIFIKASI | — |

### D.8 Search / Filter History

| Elemen | Pernyataan | Status | Bukti |
|--------|-----------|--------|------|
| Aktor | Dokter (`approved`) | ✅ TERVERIFIKASI | `History.tsx` (useMemo) |
| Trigger | Pengguna memasukkan kriteria | ✅ TERVERIFIKASI | — |
| Post Condition | Daftar difilter | ✅ TERVERIFIKASI | — |

### D.9 View Doctor Profile

| Elemen | Pernyataan | Status | Bukti |
|--------|-----------|--------|------|
| Aktor | Dokter (`approved`) | ✅ TERVERIFIKASI | `DoctorRoute` |
| Trigger | Dokter membuka `/profile` | ✅ TERVERIFIKASI | `DoctorProfile.tsx` |
| Post Condition | Profil ditampilkan | ✅ TERVERIFIKASI | — |

### D.10 Edit Doctor Profile

| Elemen | Pernyataan | Status | Bukti |
|--------|-----------|--------|------|
| Aktor | Dokter (`approved`) | ✅ TERVERIFIKASI | `DoctorProfile.tsx` (baris 445) |
| Trigger | Dokter membuka modal edit | ✅ TERVERIFIKASI | — |
| Post Condition | Profil diperbarui via upsert | ✅ TERVERIFIKASI | — |

### D.11–D.14 Use Case Admin

| No. | Use Case | Status | Bukti |
|-----|----------|--------|------|
| 11 | View Admin Dashboard | ✅ TERVERIFIKASI | `GET /api/admin/doctors/stats` |
| 12 | View Doctor Registration | ✅ TERVERIFIKASI | `GET /api/admin/doctors` |
| 13 | Approve Doctor Account | ✅ TERVERIFIKASI | `POST /api/admin/doctors/<id>/approve` |
| 14 | Reject Doctor Account | ✅ TERVERIFIKASI | `POST /api/admin/doctors/<id>/reject` |

---

## E. Konsistensi dengan Diagram Lain

| Diagram | Konsistensi | Catatan |
|---------|-------------|---------|
| Class Diagram | ✅ SELESAI | `AnalysisService` ↔ `Upload Image` ↔ `Segmentation` konsisten |
| ERD | ✅ SELESAI | `users` ↔ `doctor_profiles` ↔ `analyses` konsisten |
| Activity Diagram | ✅ SELESAI | Alur Sign Up/Sign In/Upload/Segmentation sesuai |
| Sequence Diagram | ✅ SELESAI | Interaksi Sign Up/Sign In/Upload/Segmentation sesuai |
| Use Case | — | — |

---

## F. Ketidaksesuaian dan Rekomendasi

### F.1 Ketidaksesuaian pada Gambar

| No. | Ketidaksesuaian | Rekomendasi |
|-----|----------------|-------------|
| 1 | Duplikasi node "History" | Ganti salah satu dengan "Search / Filter History" |
| 2 | `Reset Password <<extend>> Sign Out` | Perbaiki ke `Reset Password <<extend>> Sign In` |
| 3 | Asosiasi `Calon Pengguna → Sign Out` | Ganti ke `Calon Pengguna → Sign In` |
| 4 | Ketidakterkaitan `Admin → Sign In` | Tambahkan asosiasi Admin → Sign In |

### F.2 Ketidaksesuaian pada Dokumen

| No. | Ketidaksesuaian | Dokumen | Tindakan |
|-----|----------------|---------|----------|
| 1 | Klaim "tanpa RBAC" | `LAPORAN_AUDIT_USE_CASE_PIXELT.md` | Digantikan oleh audit revisi |
| 2 | Catatan `/reset-password` salah | `AUDIT_DAMPAK_ROLE_ADMIN_DOKTER_PIXELT.md` | Direkonsiliasi |

### F.3 Rekomendasi Koreksi

1. Perbaiki keempat masalah visual pada `Use Case Diagram PIXELT.png`.
2. Buat file `.drawio` sumber dari generator Python `_gen_use_case_audit_png.py`.
3. Buat file `.svg` dari generator atau ekspor manual.
4. Jalankan pengujian runtime sebelum final submission.

---

## G. Informasi yang Belum Dapat Dipastikan

| No. | Informasi | Status |
|-----|-----------|--------|
| 1 | Pengujian runtime browser / end-to-end | ❌ Belum dilakukan |
| 2 | Validasi visual oleh mesin UML resmi | ⚠️ Terbatas |
| 3 | Status `app_metadata` admin pada runtime | ⚠️ Bukan dari runtime |
| 4 | Konfigurasi `.env` | ⚠️ Belum dibaca |
| 5 | Skrip AI (`tests/ai`) dan build TypeScript | ⚠️ Belum dijalankan |

---

## H. Matriks Ringkasan Hasil Validasi

| Kriteria | Hasil |
|----------|-------|
| Seluruh aktor memiliki dasar implementasi | ✅ 3/3 |
| Seluruh use case memiliki dasar implementasi | ✅ 14/14 |
| Seluruh asosiasi aktor–use case lengkap | ✅ 14/14 |
| `<<include>>` valid | ✅ 1/1 |
| `<<extend>>` valid dan arah benar | ✅ 3/3 |
| Pemisahan hak akses Admin/Dokter pada tiga lapisan | ✅ Terverifikasi |
| Tidak ada generalisasi menyesatkan | ✅ Tidak ada |
| Unit test backend | ✅ 110 lulus |
| Unit test frontend | ✅ 285 lulus |
| Validasi visual mesin UML resmi | ⚠️ Terbatas |
| Pengujian browser/end-to-end | ❌ Belum dilakukan |

**Keputusan:** Use Case Diagram PIXEL-T **layak** digunakan sebagai bagian Bab IV skripsi, dengan catatan perbaikan empat masalah visual yang telah diidentifikasi.

---

*Matriks ini disusun berdasarkan analisis statis terhadap kode sumber web PIXEL-T, dokumen pendukung Bab IV, dan hasil audit Use Case Diagram. Seluruh klaim dapat dilacak ke berkas yang tercantum pada Bagian A dan B. Tidak ada kode aplikasi yang diubah.*

---

**Dokumen ini telah dibuat untuk memenuhi persyaratan Tahap IV — Matriks Validasi.**
**Tanggal:** 6 November 2026
**Status:** FINAL REVISI
