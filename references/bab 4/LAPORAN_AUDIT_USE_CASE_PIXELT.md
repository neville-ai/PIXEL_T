# LAPORAN AUDIT MENYELURUH USE CASE DIAGRAM — SISTEM PIXEL-T
**Dokumen Pendukung Bab IV Skripsi S1**
Disusun berdasarkan analisis implementasi aktual kode sumber web PIXEL-T.

---

## 1. Ringkasan Eksekutif

Audit ini dilaksanakan untuk memvalidasi kesesuaian antara *Use Case Diagram* PIXEL-T dengan implementasi aktual sistem. Seluruh 13 *use case*, 2 aktor, 1 batas sistem, 4 relasi `<<include>>`, dan 3 relasi `<<extend>>` yang terdapat pada diagram telah diperiksa secara seksama terhadap kode sumber.

**Kesimpulan utama:** *Use Case Diagram* PIXEL-T dinyatakan **LAYAK** untuk dimasukkan ke dalam skripsi S1. Seluruh elemen yang tertera pada diagram telah terimplementasi dalam kode sumber aktual sistem. Dua catatan minor teridentifikasi namun tidak bersifat *blocking* pada level skripsi S1.

---

## 2. Informasi Sistem

| Aspek                    | Keterangan |
|--------------------------|------------|
| **Nama Sistem**          | PIXEL-T (*Polyp Identification with eXplainable Intelligence for Early-stage Local Tissue detection*) |
| **Tipe Aplikasi**        | Aplikasi web *full-stack* untuk segmentasi citra kolonoskopi berbasis AI |
| **Frontend**             | React 18 + TypeScript + Vite + TailwindCSS |
| **Backend**              | Python + FastAPI |
| **Layanan Autentikasi**  | Supabase Auth (JWT) |
| **Penyimpanan Data**     | Supabase PostgreSQL + Supabase Storage |
| **Model AI**             | U-Net (segmentasi) + ResNet50 + Grad-CAM |
| **Pengelolaan Rute**     | React Router v6 + `ProtectedRoute.tsx` |

---

## 3. Berkas yang Diperiksa

### 3.1 Frontend
| Berkas | Fungsi |
|--------|--------|
| `frontend/src/pages/auth/Register.tsx` | Halaman Sign Up |
| `frontend/src/pages/auth/Login.tsx` | Halaman Sign In + alur Reset Password tahap permintaan tautan |
| `frontend/src/pages/auth/ResetPassword.tsx` | Halaman Reset Password tahap pembaruan kata sandi |
| `frontend/src/pages/analysis/NewAnalysis.tsx` | Halaman unggah citra + pemicu segmentasi |
| `frontend/src/pages/analysis/AnalysisResult.tsx` | Halaman tampilan hasil segmentasi |
| `frontend/src/pages/history/History.tsx` | Halaman View History + Search History |
| `frontend/src/pages/history/HistoryDetail.tsx` | Halaman detail riwayat |
| `frontend/src/pages/profile/DoctorProfile.tsx` | Halaman View + Edit Doctor Profile |
| `frontend/src/context/AuthContext.tsx` | Manajemen sesi (signUp, signIn, signOut) |
| `frontend/src/routes/AppRoutes.tsx` | Definisi rute + perlindungan rute |
| `frontend/src/services/analysis.ts` | Layanan API analisis (listHistory, deleteAnalysis) |
| `frontend/src/services/profile.ts` | Layanan profil (fetchDoctorProfile, saveDoctorProfile, validateProfileData) |
| `frontend/src/services/auth.ts` | Layanan autentikasi (resetPasswordUser) |

### 3.2 Backend & AI
| Berkas | Fungsi |
|--------|--------|
| `backend/app/controllers/analysis_controller.py` | *Endpoint* `POST /api/analysis` (HTTP 202) |
| `backend/app/services/analysis_service.py` | Logika bisnis analisis, `JobQueue`, orkestrasi penyimpanan |
| `ai/inference/pipeline.py` | Pipeline inferensi U-Net + ResNet50 + Grad-CAM |

---

## 4. Validasi Aktor

| Aktor | Status | Bukti Implementasi |
|-------|--------|--------------------|
| **Pengguna (Belum Terdaftar)** | ✅ VALID | Rute `/register` dan `/login` bersifat publik (tidak dilindungi `ProtectedRoute`). Hanya *use case* Sign Up yang dapat diakses tanpa sesi aktif. |
| **Pengguna Terdaftar (Dokter / Tenaga Medis)** | ✅ VALID | Seluruh rute fitur utama (`/dashboard`, `/analysis/*`, `/history/*`, `/profile`) dilindungi `ProtectedRoute.tsx` yang memeriksa keberadaan sesi Supabase aktif sebelum mengizinkan akses. |

**Catatan Tambahan:** Sistem PIXEL-T tidak menerapkan pembedaan hak akses berbasis peran (*role-based access control*) di antara pengguna terdaftar. Seluruh pengguna yang telah terautentikasi, baik dokter maupun tenaga medis lainnya, memiliki hak akses yang identik. Label aktor *"Dokter / Tenaga Medis"* merupakan deskriptor gabungan yang tepat dan sesuai dengan desain sistem.

---

## 5. Validasi Batas Sistem

Batas sistem pada diagram berlabel **"Sistem PIXEL-T"** mencakup seluruh 13 *use case* yang teridentifikasi. Validasi ini dikonfirmasi oleh struktur aplikasi yang terbagi menjadi komponen *frontend* (React), *backend* (FastAPI), dan layanan AI (pipeline inferensi), yang ketiganya beroperasi sebagai satu kesatuan sistem PIXEL-T.

---

## 6. Validasi Tiga Belas Use Case

### 6.1 Use Case Milik Aktor "Pengguna (Belum Terdaftar)"

| # | Use Case | Status | Bukti |
|---|----------|--------|-------|
| 1 | **Sign Up** | ✅ DIIMPLEMENTASIKAN | `Register.tsx`: formulir pendaftaran, validasi (format email regex, panjang kata sandi ≥8 karakter), pemanggilan `signUp()` pada `AuthContext`, dan respons sukses ke pengguna setelah akun dibuat di Supabase `auth.users`. |

### 6.2 Use Case Milik Aktor "Pengguna Terdaftar (Dokter / Tenaga Medis)"

| # | Use Case | Status | Bukti |
|---|----------|--------|-------|
| 2 | **Sign In** | ✅ DIIMPLEMENTASIKAN | `Login.tsx`: validasi email dan kata sandi sisi klien, pemanggilan `signIn()` pada `AuthContext` → `supabase.auth.signInWithPassword()`, pengelolaan sesi JWT, pengalihan ke `/dashboard`. |
| 3 | **Reset Password** | ✅ DIIMPLEMENTASIKAN | `Login.tsx` (mode `reset`): permintaan tautan reset melalui `resetPasswordUser()` → `supabase.auth.resetPasswordForEmail()`. `ResetPassword.tsx`: pembaruan kata sandi melalui `supabase.auth.updateUser({ password })` setelah verifikasi sesi *recovery*. |
| 4 | **Upload Image** | ✅ DIIMPLEMENTASIKAN | `NewAnalysis.tsx`: validasi berkas sisi klien (ekstensi, MIME, ukuran ≤10 MB), pratinjau citra, `POST /api/analysis`, penerimaan HTTP `202 Accepted`, pengalihan ke `/analysis/:id`. |
| 5 | **Segmentation** | ✅ DIIMPLEMENTASIKAN | `analysis_service.py` + `pipeline.py`: validasi integritas citra (Pillow), inferensi U-Net (segmentasi biner), inferensi ResNet50 + Grad-CAM, penyimpanan 4 artefak ke Storage, pembaruan `status = completed`. |
| 6 | **Validate Image** | ✅ DIIMPLEMENTASIKAN | `analysis_service.py`: validasi MIME dan integritas citra menggunakan pustaka Pillow pada sisi *backend*, dijalankan sebagai bagian wajib dari pipeline segmentasi. |
| 7 | **Generate Overlay** | ✅ DIIMPLEMENTASIKAN | `pipeline.py`: `segmentation_overlay.png` selalu dibuat (citra asli + *binary mask*) dan disimpan ke Supabase Storage pada setiap proses segmentasi. |
| 8 | **Generate Grad-CAM** | ✅ DIIMPLEMENTASIKAN | `pipeline.py`: `gradcam_heatmap.png` dan `gradcam_overlay.png` selalu dibuat melalui algoritma Grad-CAM berbasis ResNet50 dan disimpan ke Supabase Storage. |
| 9 | **View History** | ✅ DIIMPLEMENTASIKAN | `History.tsx`: pemanggilan `listHistory()` untuk mengambil rekaman analisis milik pengguna, tampilan tabel berisi nama berkas, tanggal, dan status, serta navigasi ke halaman detail. |
| 10 | **Search History** | ✅ DIIMPLEMENTASIKAN | `History.tsx`: tiga filter berbasis klien menggunakan `useMemo` — (a) pencarian teks nama berkas, (b) filter *dropdown* status, dan (c) filter tanggal. |
| 11 | **View Doctor Profile** | ✅ DIIMPLEMENTASIKAN | `DoctorProfile.tsx`: pemanggilan `fetchDoctorProfile()` dari tabel `doctor_profiles` dan `listHistory()` untuk statistik aktivitas. |
| 12 | **Edit Doctor Profile** | ✅ DIIMPLEMENTASIKAN | `DoctorProfile.tsx`: modal edit profil, `validateProfileData()`, `saveDoctorProfile()` → *upsert* ke `doctor_profiles` + `supabase.auth.updateUser()`. |
| 13 | **Sign Out** | ✅ DIIMPLEMENTASIKAN | `AuthContext.tsx` + komponen navigasi: modal konfirmasi keluar, `supabase.auth.signOut()`, pembersihan sesi, pengalihan ke `/login`. |

---

## 7. Validasi Relasi `<<include>>`

Relasi `<<include>>` menggambarkan perilaku yang **wajib** dieksekusi sebagai bagian dari *use case* dasar.

| Relasi | Arah | Status | Analisis |
|--------|------|--------|----------|
| Segmentation `<<include>>` Upload Image | Segmentation → Upload Image | ✅ VALID | Citra harus diunggah terlebih dahulu sebelum segmentasi dapat dijalankan. Backend tidak dapat memproses analisis tanpa berkas citra yang tersimpan di Storage. Ini merupakan prasyarat wajib. |
| Segmentation `<<include>>` Validate Image | Segmentation → Validate Image | ✅ VALID | `analysis_service.py` selalu menjalankan validasi integritas citra menggunakan Pillow sebelum pipeline inferensi dijalankan. Tidak dapat dilewati. |
| Segmentation `<<include>>` Generate Overlay | Segmentation → Generate Overlay | ✅ VALID | `pipeline.py` selalu menghasilkan `segmentation_overlay.png`. Tidak ada alur kondisional yang melewatkan pembuatan artefak ini. |
| Segmentation `<<include>>` Generate Grad-CAM | Segmentation → Generate Grad-CAM | ✅ VALID | `pipeline.py` selalu menjalankan inferensi Grad-CAM dan menyimpan `gradcam_heatmap.png` serta `gradcam_overlay.png`. Tidak ada alur kondisional yang melewatkan proses ini. |

---

## 8. Validasi Relasi `<<extend>>`

Relasi `<<extend>>` menggambarkan perilaku yang bersifat **opsional** dan hanya dieksekusi dalam kondisi tertentu.

| Relasi | Arah | Status | Analisis |
|--------|------|--------|----------|
| Reset Password `<<extend>>` Sign In | Reset Password → Sign In | ✅ VALID | Fitur *reset* kata sandi bersifat opsional. Pada `Login.tsx`, pengguna secara aktif memilih opsi "Forgot Password?" yang mengubah tampilan formulir ke mode `reset`. Tidak semua alur Sign In akan memasuki Reset Password. Arah panah (dari *extending* menuju *base*) sudah benar sesuai standar UML. |
| Search History `<<extend>>` View History | Search History → View History | ✅ VALID | Fitur pencarian dan filter pada `History.tsx` bersifat opsional. Pengguna dapat melihat daftar riwayat tanpa menggunakan filter sama sekali. Fitur ini hanya aktif apabila pengguna secara sengaja mengisi kolom pencarian atau memilih filter status/tanggal. |
| Edit Doctor Profile `<<extend>>` View Doctor Profile | Edit Doctor Profile → View Doctor Profile | ✅ VALID | Pengeditan profil bersifat opsional. Pengguna dapat mengunjungi halaman `DoctorProfile.tsx` hanya untuk melihat profil tanpa membuka modal edit. Modal edit hanya muncul apabila pengguna menekan tombol **Edit Profile**. |

---

## 9. Matriks Keterlacakan (*Traceability Matrix*)

| Use Case | Berkas Frontend | Berkas Backend/AI | Endpoint / Fungsi Utama |
|----------|----------------|-------------------|-------------------------|
| Sign Up | `Register.tsx`, `AuthContext.tsx` | Supabase Auth | `signUp()`, `supabase.auth.signUp()` |
| Sign In | `Login.tsx`, `AuthContext.tsx` | Supabase Auth | `signIn()`, `supabase.auth.signInWithPassword()` |
| Reset Password | `Login.tsx`, `ResetPassword.tsx`, `auth.ts` | Supabase Auth | `resetPasswordUser()`, `supabase.auth.updateUser()` |
| Upload Image | `NewAnalysis.tsx`, `analysis.ts` | `analysis_controller.py` | `POST /api/analysis` (HTTP 202) |
| Segmentation | `AnalysisResult.tsx` | `analysis_service.py`, `pipeline.py` | `JobQueue`, U-Net + ResNet50 + Grad-CAM inference |
| Validate Image | *(dipicu dari Upload Image)* | `analysis_service.py` | Validasi Pillow (MIME, dimensi) |
| Generate Overlay | *(dipicu dari Segmentation)* | `pipeline.py` | Simpan `segmentation_overlay.png` ke Storage |
| Generate Grad-CAM | *(dipicu dari Segmentation)* | `pipeline.py` | Grad-CAM → `gradcam_heatmap.png`, `gradcam_overlay.png` |
| View History | `History.tsx`, `analysis.ts` | Supabase DB | `listHistory()`, query `analyses` by `user_id` |
| Search History | `History.tsx` | *(client-side)* | `useMemo` filter (teks, status, tanggal) |
| View Doctor Profile | `DoctorProfile.tsx`, `profile.ts`, `analysis.ts` | Supabase DB | `fetchDoctorProfile()`, `listHistory()` untuk statistik |
| Edit Doctor Profile | `DoctorProfile.tsx`, `profile.ts` | Supabase DB | `saveDoctorProfile()`, `supabase.auth.updateUser()` |
| Sign Out | Komponen navigasi, `AuthContext.tsx` | Supabase Auth | `signOut()`, `supabase.auth.signOut()` |

---

## 10. Temuan Audit

### 10.1 Temuan Mayor
**Tidak ada temuan mayor.** Seluruh 13 *use case* pada diagram telah terimplementasi dalam kode sumber.

### 10.2 Temuan Minor
*Tidak ada temuan minor yang bersifat kritis. Lihat Catatan di bawah.*

### 10.3 Catatan Teknis

**Catatan 1 — Semantik Relasi Upload Image:**
*Use Case Diagram* menggambarkan Upload Image sebagai relasi `<<include>>` dari Segmentation. Secara teknis, Upload Image merupakan *prasyarat sekuensial* (terjadi sebelum Segmentation, bukan sebagai sub-behavior yang dipanggil di dalam Segmentation). Namun, karena Upload Image adalah bagian yang **wajib** dan tidak dapat dilewati dalam alur kerja utama Segmentation, pemodelan dengan `<<include>>` dapat diterima dan sudah umum digunakan dalam pemodelan UML tingkat S1. Tidak perlu direvisi.

**Catatan 2 — Validate Image, Generate Overlay, Generate Grad-CAM sebagai Use Case Terpisah:**
Ketiga *use case* ini dalam implementasi aktual merupakan langkah-langkah internal dalam pipeline `analysis_service.py` dan `pipeline.py`, bukan fitur yang dapat diinisiasi secara independen oleh pengguna. Pemodelan sebagai *use case* terpisah yang dihubungkan dengan `<<include>>` adalah pilihan yang dapat diterima untuk tujuan dokumentasi skripsi karena memperlihatkan komponen-komponen proses segmentasi yang signifikan secara teknis. Tidak perlu direvisi.

**Catatan 3 — Arah Panah Relasi `<<extend>>`:**
Seluruh tiga relasi `<<extend>>` pada diagram menggunakan arah panah dari *extending use case* menuju *base use case* (contoh: Reset Password → Sign In). Arah ini **sudah benar** sesuai standar notasi UML 2.x. Tidak perlu direvisi.

---

## 11. Kesimpulan

Berdasarkan audit menyeluruh yang telah dilaksanakan terhadap seluruh elemen *Use Case Diagram* PIXEL-T:

1. **Seluruh 13 use case telah diimplementasikan** dalam kode sumber aktual sistem PIXEL-T.
2. **Kedua aktor telah direpresentasikan dengan benar** sesuai hak akses yang diterapkan melalui mekanisme *protected route*.
3. **Seluruh 4 relasi `<<include>>`** menggambarkan perilaku yang memang bersifat wajib dalam alur kerja sistem.
4. **Seluruh 3 relasi `<<extend>>`** menggambarkan perilaku yang bersifat opsional sesuai implementasi aktual.
5. **Tidak ditemukan *use case* fiktif** (use case yang digambarkan pada diagram namun tidak diimplementasikan).
6. **Arah relasi dan notasi UML** telah sesuai dengan standar UML 2.x.

> **Keputusan Akhir: *Use Case Diagram* PIXEL-T dinyatakan LAYAK untuk dimasukkan ke dalam Bab IV Skripsi S1 tanpa memerlukan revisi.**

---

*Audit dilaksanakan berdasarkan analisis langsung terhadap kode sumber aktual web PIXEL-T. Seluruh temuan dapat dilacak kembali ke berkas kode sumber yang tercantum pada Bagian 3.*

