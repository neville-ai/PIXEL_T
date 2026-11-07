# AUDIT MENYELURUH DAN VALIDASI FINAL TUJUH ACTIVITY DIAGRAM SKRIPSI WEB PIXEL-T

**Dokumen Evaluasi Kualitas Perangkat Lunak, Kepatuhan Notasi UML, dan Kelayakan Akademik Bab IV Skripsi**  
**Sistem Deteksi dan Segmentasi Polip Kolorektal Berbasis Kecerdasan Buatan (PIXEL-T)**

---

## BAGIAN A — RINGKASAN EKSEKUTIF

Audit komprehensif ini dilakukan oleh Senior Software Engineer, System Analyst, dan UML Activity Diagram Specialist terhadap implementasi aktual kode sumber platform web **PIXEL-T** serta tujuh berkas gambar Activity Diagram yang tersimpan pada direktori:
`C:\Users\nevil\OneDrive\Dokumen\SKRIPSI\WEB_PIXELT\references\bab 4\activity_diagrams`

### Rekapitulasi Status Kelayakan Tujuh Diagram (Pasca Revisi History & Doctor Profile):
- **Diagram Layak Final Langsung (Status 1):** **2 diagram** (28.6%) — *Activity Diagram - History* & *Activity Diagram - Doctor Profile*
- **Diagram Layak Setelah Revisi Minor (Status 2):** **1 diagram** (14.3%) — *Activity Diagram - Sign In*
- **Diagram Memerlukan Revisi Major (Status 3):** **4 diagram** (57.1%) — *Sign Up, Upload Image, Segmentation, Sign Out*
- **Diagram Belum Dapat Diputuskan (Status 4):** **0 diagram** (0%) — *Seluruh bukti kode dan diagram berhasil diverifikasi 100%*.

### Keputusan Penilaian Skripsi Secara Keseluruhan:
**DUA DIAGRAM (HISTORY & DOCTOR PROFILE) TELAH RESMI MEMENUHI STANDAR FINAL BAB IV SKRIPSI. EMPAT DIAGRAM MASIH MEMERLUKAN PERBAIKAN LOGIKA MAJOR (GUARD TERBALIK, AKSI FIKTIF, DAN DUPLIKASI NODE), SERTA SATU DIAGRAM MEMERLUKAN PERBAIKAN TYPO MINOR.**

Evaluasi ulang membuktikan bahwa revisi yang dilakukan pada **Activity Diagram History** dan **Activity Diagram Doctor Profile** telah berhasil mengatasi seluruh masalah fatal sebelumnya (pengurangan multi-final node menjadi tepat 1 final node, penghapusan jalur buntu, penambahan siklus koreksi form, dan penyatuan alur melalui merge node). Namun, untuk **Sign Up**, **Upload Image**, **Segmentation**, dan **Sign Out**, masih terdapat anomali logika substansial yang wajib diperbaiki sebelum seluruh set diagram dapat dinyatakan 100% final.

---

## BAGIAN B — HASIL AUDIT IMPLEMENTASI ARSITEKTUR WEB PIXEL-T

Penelusuran menyeluruh terhadap repositori proyek `WEB_PIXELT` menghasilkan pemetaan faktual arsitektur sistem sebagai berikut:

```
                                  ARSITEKTUR AKTUAL PIXEL-T
                                  
  ┌─────────────────────────────────────────────────────────────────────────────────┐
  │                            FRONTEND (React 18 + Vite)                           │
  │  - SPA (Single Page Application) berbasis Functional Components + React Hooks   │
  │  - Tailwind CSS + Lucide React Icons                                            │
  │  - Autentikasi: AuthContext.tsx (berkomunikasi langsung dengan Supabase Auth)   │
  │  - Rute Utama: /login, /register, /dashboard, /analysis/new, /analysis/:id,     │
  │               /history, /profile                                                │
  └────────────────────────┬───────────────────────────────┬────────────────────────┘
                           │ API Call (HTTP REST)          │ Auth Token & User Meta
                           ▼                               ▼
  ┌────────────────────────────────────────┐     ┌──────────────────────────────────┐
  │         BACKEND (Python 3.11 + Flask)  │     │   SUPABASE (BaaS Cloud Infrastructure)
  │  - Layered Architecture:               │     │  - Supabase Auth (JWT & Session) │
  │    * Controllers (analysis_controller) │     │  - PostgreSQL Database:          │
  │    * Services (analysis_service)       │     │    * auth.users                  │
  │    * Repositories (analysis_repo)      │     │    * public.doctor_profiles      │
  │  - Asynchronous Queue (JobQueue)       │     │    * public.analyses             │
  │  - Validasi File: Pillow (MIME, size)  │     │  - Private Storage:              │
  │  - AI Inference: PyTorch (U-Net + ResNet50)  │    * analysis-assets (raw, mask, │
  │  - Explainable AI: Grad-CAM Engine     │      overlays, heatmaps)               │
  └────────────────────────────────────────┘     └──────────────────────────────────┘
```

### Pemetaan Berkas Implementasi Kunci Berdasarkan Fitur:
1. **Fitur Sign Up (Pendaftaran):** `frontend/src/pages/Register.tsx`, `frontend/src/context/AuthContext.tsx`.
2. **Fitur Sign In (Masuk Akal):** `frontend/src/pages/Login.tsx`, `frontend/src/context/AuthContext.tsx`.
3. **Fitur Upload Image (Unggah Citra):** `frontend/src/pages/analysis/NewAnalysis.tsx`, `backend/app/controllers/analysis_controller.py`, `backend/app/services/analysis_service.py`.
4. **Fitur Segmentation (Segmentasi AI & Grad-CAM):** `backend/app/services/analysis_service.py`, `ai/inference/pipeline.py`, `frontend/src/pages/analysis/AnalysisDetail.tsx`.
5. **Fitur History (Riwayat Analisis):** `frontend/src/pages/History.tsx`, `frontend/src/services/analysis.ts`, `backend/app/controllers/analysis_controller.py`.
6. **Fitur Doctor Profile (Profil Dokter):** `frontend/src/pages/DoctorProfile.tsx`, `frontend/src/services/profile.ts`, PostgreSQL table `doctor_profiles`.
7. **Fitur Sign Out (Keluar Sistem):** `frontend/src/components/common/Header.tsx`, `frontend/src/components/common/Sidebar.tsx`, `frontend/src/context/AuthContext.tsx`.

---

## BAGIAN C — TABEL RINGKASAN TUJUH DIAGRAM

| No. | Nama Diagram | Kesesuaian Kode | Ketepatan Alur | Kelengkapan Fitur | Notasi UML | Revisi Major? | Status Akhir |
|---|---|---|---|---|---|---|---|
| 1 | **Sign Up** | Sebagian Sesuai | **Kritis (Terbalik)** | Cukup Lengkap | Tepat | **YA** | `BELUM FINAL — MEMERLUKAN REVISI MAJOR` |
| 2 | **Sign In** | Sangat Sesuai | Tepat | Lengkap | Tepat | **TIDAK** | `LAYAK SETELAH REVISI MINOR` |
| 3 | **Upload Image** | Sebagian Sesuai | Terdapat Aksi Fiktif | Lengkap | Tepat | **YA** | `BELUM FINAL — MEMERLUKAN REVISI MAJOR` |
| 4 | **Segmentation** | Sebagian Sesuai | Terdapat Aksi Fiktif | Cukup Lengkap | Typo Aktor | **YA** | `BELUM FINAL — MEMERLUKAN REVISI MAJOR` |
| 5 | **History (REVISI FINAL)** | **Sangat Sesuai** | **Tepat (1 Final Node)** | **Lengkap & Teruji** | **Sempurna** | **TIDAK** | `FINAL — LAYAK DIMASUKKAN KE SKRIPSI` |
| 6 | **Doctor Profile (REVISI FINAL)** | **Sangat Sesuai** | **Tepat (Loop-back)** | **Lengkap & Teruji** | **Sempurna** | **TIDAK** | `FINAL — LAYAK DIMASUKKAN KE SKRIPSI` |
| 7 | **Sign Out** | Cukup Sesuai | Duplikasi Proses | Lengkap | Tepat | **YA** | `BELUM FINAL — MEMERLUKAN REVISI MAJOR` |

---

## BAGIAN D — AUDIT TERPERINCI SETIAP DIAGRAM

```
====================================================================================================
1. ACTIVITY DIAGRAM — SIGN UP (`Activity Diagram - Sign Up.drawio.png`)
====================================================================================================
```

### 1.1 Tujuan Fitur
Memfasilitasi pendaftaran akun baru dokter/tenaga medis ke dalam sistem PIXEL-T menggunakan nama lengkap, email, kata sandi, dan konfirmasi kata sandi melalui integrasi Supabase Auth.

### 1.2 Ringkasan Alur yang Tergambar
User membuka form $\rightarrow$ mengisi form pendaftaran $\rightarrow$ Sistem memvalidasi input user $\rightarrow$ Decision: *"Email sudah digunakan?"*:
- Cabang *"Tidak"*: Sistem mengirim pesan *"Email is already in use"* $\rightarrow$ User menerima pesan dan kembali mengisi form.
- Cabang *"Ya"*: Sistem membuat sesi user (Supabase Auth) $\rightarrow$ mengirim pesan berhasil $\rightarrow$ User dialihkan ke halaman sign in $\rightarrow$ selesai.

### 1.3 Ringkasan Alur Aktual Menurut Kode Sumber
Pada `frontend/src/pages/Register.tsx` dan `frontend/src/context/AuthContext.tsx`:
1. Pengguna membuka rute `/register`.
2. Pengguna memasukkan data: `name`, `email`, `password`, `confirmPassword`.
3. Validasi lokal pada frontend:
   - Kelengkapan seluruh field.
   - Format email (`email.includes('@')`).
   - Panjang minimal password (minimal 8 karakter).
   - Kesesuaian antara `password` dan `confirmPassword`.
4. Jika validasi lokal lolos, fungsi `signUp(email, password, name)` dipanggil ke `supabase.auth.signUp()`.
5. Supabase memeriksa apakah email sudah terdaftar:
   - Jika **Sudah Terdaftar (Email Duplicate)**: Supabase mengembalikan error `User already registered`. Frontend menampilkan alert error *"User already registered"*, pengguna tetap di form untuk mengubah email.
   - Jika **Belum Terdaftar**: Akun dibuat pada skema `auth.users`, metadata `name` tersimpan, frontend menampilkan notifikasi sukses, lalu meredireksi pengguna ke halaman `/login`.

### 1.4 Tabel Pencocokan Aktivitas dengan Bukti Kode
| No. | Aktivitas / Kondisi pada Diagram | Bukti Implementasi Kode | Hasil Pemeriksaan | Temuan & Tindakan |
|---|---|---|---|---|
| 1 | Membuka halam Sign up | `Register.tsx` (baris 1-25) | Sesuai (Typo) | Typo teks "halam" seharusnya "halaman". |
| 2 | Mengisi form Sign up | `Register.tsx` (baris 130-185) | Sesuai | Input nama, email, password, confirmPassword. |
| 3 | Memvalidasi input user | `Register.tsx` (baris 38-59) | Sesuai | Validasi client-side dan request auth. |
| 4 | **Decision: Email sudah digunakan?** | `AuthContext.tsx` (`signUp`) | **LOGIKA TERBALIK** | **Kritis: Kondisi guard Ya dan Tidak tertukar.** |
| 5 | Mengirim pesan "Email is already in use" | `Register.tsx` (baris 72-78) | Sesuai fungsi | Muncul saat email duplicate. |
| 6 | Membuat sesi user (Supabase Auth) | `supabase.auth.signUp()` | Sesuai | Pembuatan user di Supabase. |
| 7 | Mengirim & menerima pesan berhasil | `Register.tsx` (baris 62) | Sesuai | Alert sukses registrasi. |
| 8 | Dialihkan ke halaman sign in | `Register.tsx` (baris 65) | Sesuai | `navigate('/login')`. |

### 1.5 Temuan Khusus dan Klasifikasi Masalah
- **[MAJOR — LOGIKA GUARD TERBALIK]:** Pertanyaan keputusan adalah *"Email sudah digunakan?"*. Jika jawabannya **"Ya"** (email sudah dipakai orang lain), sistem seharusnya **menolak** dan menampilkan error. Namun diagram justru melanjutkan ke alur sukses (*Membuat sesi user*). Sebaliknya, jika jawabannya **"Tidak"** (email belum pernah dipakai), diagram malah mengirim error *"Email is already in use"*. Kesalahan ini fatal secara logika logika proposisional dan UML.
- **[MINOR — TYPO LABEL]:** Aktivitas pertama tertulis *"Membuka halam Sign up"* (kurang huruf 'an').

### 1.6 Rekomendasi Perbaikan
1. Ubah label pertanyaan menjadi: *"Apakah email valid dan belum terdaftar?"* dengan cabang `[Ya]` menuju pembuatan akun dan `[Tidak]` menuju pesan error; **ATAU**
2. Tetap gunakan pertanyaan *"Email sudah digunakan?"*, tetapi tukar panah guard: `[Ya]` menuju pesan error dan looping kembali, sedangkan `[Tidak]` menuju pembuatan akun.
3. Perbaiki typo kata *"halam"* menjadi *"halaman"*.

---

```
====================================================================================================
2. ACTIVITY DIAGRAM — SIGN IN (`Activity Diagram - Sign In.drawio.png`)
====================================================================================================
```

### 2.1 Tujuan Fitur
Mengotentikasi pengguna terdaftar melalui email dan password, membuat sesi JWT aktif via Supabase Auth, dan mengarahkan pengguna ke dasbor utama aplikasi PIXEL-T.

### 2.2 Ringkasan Alur yang Tergambar
User membuka halaman $\rightarrow$ mengisi form sign in $\rightarrow$ Sistem memvalidasi input user $\rightarrow$ Decision: *"Email dan password Sesuai?"*:
- Cabang *"Tidak"*: Sistem mengirim pesan *"Email or password is incorrect"* $\rightarrow$ User menerima pesan dan kembali mengisi form.
- Cabang *"Ya"*: Sistem membuat sesi user (Supabase Auth) $\rightarrow$ mengalihkan user ke halaman utama $\rightarrow$ User dialihkan ke halaman utama $\rightarrow$ selesai (1 final node).

### 2.3 Ringkasan Alur Aktual Menurut Kode Sumber
Pada `frontend/src/pages/Login.tsx` dan `frontend/src/context/AuthContext.tsx`:
1. Pengguna membuka rute `/login`.
2. Pengguna memasukkan `email` dan `password`.
3. Validasi lokal memeriksa apakah field kosong (`!email || !password`).
4. Memanggil `signIn(email, password)` yang mengeksekusi `supabase.auth.signInWithPassword({ email, password })`.
5. Jika gagal (kredensial salah / user tidak ditemukan): Supabase mengembalikan pesan error (HTTP 400). Frontend menangkap error dan mengeset pesan alert *"Invalid login credentials"*. Pengguna tetap berada di halaman login.
6. Jika berhasil: Supabase mengembalikan sesi JWT yang disimpan pada `localStorage`. State `user` dan `session` diupdate. Frontend meredireksi ke `/dashboard` via `navigate('/dashboard')`.

### 2.4 Tabel Pencocokan Aktivitas dengan Bukti Kode
| No. | Aktivitas / Kondisi pada Diagram | Bukti Implementasi Kode | Hasil Pemeriksaan | Temuan & Tindakan |
|---|---|---|---|---|
| 1 | Membuka halam Sign in | `Login.tsx` (rute `/login`) | Sesuai (Typo) | Typo teks "halam" seharusnya "halaman". |
| 2 | Mengisi form Sign in | `Login.tsx` (baris 95-130) | Sesuai | Input email dan password. |
| 3 | Memvalidasi input user | `Login.tsx` (baris 32-45) | Sesuai | Pengecekan input dan pemanggilan API. |
| 4 | Decision: Email dan password Sesuai? | `AuthContext.tsx` baris 48-60 | Sesuai | Evaluasi keberhasilan kredensial. |
| 5 | Cabang Tidak $\rightarrow$ "Email/password incorrect" | `Login.tsx` (baris 52-56) | Sesuai | Alert error kredensial salah. |
| 6 | Cabang Ya $\rightarrow$ Membuat sesi Supabase Auth | `AuthContext.tsx` baris 53 | Sesuai | Pembentukan session JWT. |
| 7 | Mengalihkan ke halaman utama | `Login.tsx` (baris 49) | Sesuai | `navigate('/dashboard')`. |

### 2.5 Temuan Khusus dan Klasifikasi Masalah
- **[TIDAK ADA MASALAH MAJOR]:** Alur logika, percabangan, guard conditions, dan penggunaan single final node sudah 100% tepat dan konsisten dengan kode program.
- **[MINOR — TYPO LABEL]:** Teks aktivitas pertama tertulis *"Membuka halam Sign in"* (kurang huruf 'an').

### 2.6 Status Kelayakan
**LAYAK SETELAH REVISI MINOR (Cukup perbaiki typo kata "halam" menjadi "halaman").**

---

```
====================================================================================================
3. ACTIVITY DIAGRAM — UPLOAD IMAGE (`Activity Diagram - Upload Image.drawio.png`)
====================================================================================================
```

### 3.1 Tujuan Fitur
Memfasilitasi pengunggahan berkas citra kolonoskopi (format JPG/PNG, ukuran maksimal 10 MB), menampilkan pratinjau instan (*image preview*), dan mengirimkan berkas ke backend API untuk divalidasi serta dimasukkan ke antrean inferensi asynchronous.

### 3.2 Ringkasan Alur yang Tergambar
User membuka fitur Upload Image $\rightarrow$ memilih berkas gambar $\rightarrow$ Sistem *"Menutup menu navigasi"* $\rightarrow$ Decision: *"Berkas gambar sudah valid?"*:
- Cabang *"Tidak"*: Sistem mengirim pesan *"Invalid Image File"* $\rightarrow$ User menerima pesan dan kembali memilih berkas.
- Cabang *"Ya"*: Sistem menampilkan pratinjau gambar $\rightarrow$ User menekan tombol *"Start Analysis"* $\rightarrow$ Sistem mengunggah gambar ke backend (HTTP 202) $\rightarrow$ menyimpan gambar asli & membuat antrean kerja $\rightarrow$ mengarahkan ke halaman hasil analisis $\rightarrow$ User dialihkan ke halaman hasil analisis $\rightarrow$ selesai.

### 3.3 Ringkasan Alur Aktual Menurut Kode Sumber
Pada `frontend/src/pages/analysis/NewAnalysis.tsx` dan `backend/app/controllers/analysis_controller.py`:
1. Pengguna membuka rute `/analysis/new`.
2. Pengguna memilih berkas citra via drag-and-drop atau input file (`selectFile`).
3. Validasi client-side (`validateFile`) memeriksa ekstensi (`.jpg`, `.jpeg`, `.png`), MIME type, ukuran $\le 10$ MB, dan integritas dimensi via `createImageBitmap`.
4. Jika tidak valid, pesan error ditampilkan (`setValidationError`).
5. Jika valid, `URL.createObjectURL` membuat pratinjau lokal yang langsung muncul di layar.
6. Pengguna menekan tombol "Start Analysis" (`handleSubmit`).
7. Berkas dikirim via `POST /api/analysis` (multipart/form-data).
8. Backend merespons **HTTP 202 Accepted** dengan `analysis_id` dan status `processing`. Berkas asli disimpan di Supabase Storage (`analysis-assets`) dan tugas inferensi dimasukkan ke `AnalysisJobQueue`.
9. Frontend melakukan polling progres hingga status selesai, lalu beralih ke `/analysis/:id`.

### 3.4 Tabel Pencocokan Aktivitas dengan Bukti Kode
| No. | Aktivitas / Kondisi pada Diagram | Bukti Implementasi Kode | Hasil Pemeriksaan | Temuan & Tindakan |
|---|---|---|---|---|
| 1 | Membuka fitur Upload Image | `NewAnalysis.tsx` rute `/analysis/new` | Sesuai | Komponen form analisis baru. |
| 2 | Memilih berkas gambar kolonoskopi | `NewAnalysis.tsx` (baris 223-246) | Sesuai | Handler `selectFile` dari input file / dropzone. |
| 3 | **Menutup menu navigasi** | *Tidak ada korelasi kode* | **TIDAK SESUAI (FIKTIF)** | **Aksi fiktif hasil copy-paste dari diagram Sign Out.** |
| 4 | Decision: Berkas gambar sudah valid? | `NewAnalysis.tsx` (baris 72-98) | Sesuai | Validasi ekstensi, MIME, dimensi, dan limit 10 MB. |
| 5 | Cabang Tidak $\rightarrow$ "Invalid Image File" | `NewAnalysis.tsx` (baris 243) | Sesuai | Render alert error validasi pada card. |
| 6 | Menampilkan pratinjau gambar | `NewAnalysis.tsx` (baris 147-150) | Sesuai | Render tag `<img>` dari ObjectURL preview. |
| 7 | Menekan tombol "Start Analysis" | `NewAnalysis.tsx` (baris 248-260) | Sesuai | Submit form pemicu `createAnalysis()`. |
| 8 | Mengunggah gambar ke backend (HTTP 202) | `analysis_controller.py` (baris 36-39) | Sesuai | Endpoint POST mengembalikan status 202 Accepted. |
| 9 | Menyimpan gambar & membuat antrean kerja | `analysis_service.py` (baris 395-450) | Sesuai | Upload Supabase Storage & `AnalysisJobQueue.enqueue`. |
| 10 | Mengarahkan ke halaman hasil analisis | `NewAnalysis.tsx` (baris 186-190) | Sesuai | `navigate('/analysis/' + acceptedId)` setelah polling selesai. |

### 3.5 Temuan Khusus dan Klasifikasi Masalah
- **[MAJOR — AKSI FIKTIF]:** Terdapat node aksi sistem bertuliskan *"Menutup menu navigasi"* tepat setelah pengguna memilih berkas gambar. Di dalam kode `NewAnalysis.tsx`, pemilihan berkas sama sekali tidak berinteraksi dengan menu navigasi/sidebar. Ini adalah kesalahan copy-paste dari diagram *Sign Out*. Keberadaan aksi ini merusak integritas representasi sistem.
- **[MINOR — DETAIL PROSES ASINKRONUS]:** Diagram langsung melompat dari *"menyimpan gambar asli & membuat antrean kerja"* ke *"mengarahkan ke halaman hasil analisis"*. Pada implementasi nyata, frontend melakukan polling berkala terhadap status antrean sebelum halaman hasil dibuka.

### 3.6 Rekomendasi Perbaikan
Hapus kotak aksi *"Menutup menu navigasi"*. Hubungkan panah dari *"Memilih berkas gambar kolonoskopi"* langsung ke decision node *"Berkas gambar sudah valid?"*.

---

```
====================================================================================================
4. ACTIVITY DIAGRAM — SEGMENTATION (`Activity Diagram - Segmentation.drawio.png`)
====================================================================================================
```

### 4.1 Tujuan Fitur
Menjalankan inferensi model AI deep learning (U-Net dengan encoder ResNet50) pada citra kolonoskopi untuk menghasilkan masker segmentasi biner polip kolorektal, visualisasi atribusi fitur Grad-CAM, serta estimasi area lesi polip.

### 4.2 Ringkasan Alur yang Tergambar
User menekan *"Start Segmentation"* $\rightarrow$ Sistem memvalidasi gambar kolonoskopi $\rightarrow$ Decision: *"Gambar kolonoskopi?"*:
- Cabang *"Tidak"*: Sistem mengirim pesan *"Not Colonoscopy Image"* $\rightarrow$ User menerima pesan dan kembali.
- Cabang *"Ya"*: Melakukan proses binary segmentation $\rightarrow$ Melakukan proses Grad-Cam $\rightarrow$ Model memberikan penjelasan Grad-CAM $\rightarrow$ Menyimpan hasil segmentasi & Penjelasan Model $\rightarrow$ Sistem mengirim hasil segmentasi $\rightarrow$ User *"Mengirim hasil segmentasi & Penjelasan Model"* $\rightarrow$ selesai.

### 4.3 Ringkasan Alur Aktual Menurut Kode Sumber
Pada `backend/app/services/analysis_service.py` dan `ai/inference/pipeline.py`:
1. Pekerjaan inferensi dipicu otomatis oleh worker antrean di latar belakang (*background worker thread*).
2. Sistem melakukan decoding citra dan pra-pemrosesan tensor (resize $512 \times 512$, normalisasi ImageNet).
3. **TIDAK ADA pengklasifikasi "bukan gambar kolonoskopi".** Model AI langsung memproses citra yang lolos validasi format. Jika citra tidak memiliki polip, model menghasilkan mask kosong (`segmentation_status: "not_detected"`), bukan error *"Not Colonoscopy Image"*.
4. Model U-Net + ResNet50 mengeksekusi inferensi segmentasi biner (`predict()` menghasilkan probabilitas sigmoid dan thresholding 0.50).
5. Pipeline mengeksekusi Grad-CAM pada konvolusi terakhir encoder ResNet50 untuk mengekstrak peta aktivasi Grad-CAM.
6. Empat artefak disimpan ke Supabase Storage: `binary_mask.png`, `segmentation_overlay.png`, `gradcam_heatmap.png`, dan `gradcam_overlay.png`.
7. Status database diubah menjadi `completed` dengan ringkasan deskriptif non-diagnostik.
8. Frontend menerima status `completed` dan menampilkan visualisasi komparatif berdampingan (*side-by-side comparison*).

### 4.4 Tabel Pencocokan Aktivitas dengan Bukti Kode
| No. | Aktivitas / Kondisi pada Diagram | Bukti Implementasi Kode | Hasil Pemeriksaan | Temuan & Tindakan |
|---|---|---|---|---|
| 1 | User menekan "Start Segmentation" | `NewAnalysis.tsx` / `AnalysisDetail.tsx` | Sesuai | Pemicu analisis / inferensi. |
| 2 | Memvalidasi gambar kolonoskopi | `analysis_service.py` | Sesuai Sebagian | Validasi format berkas citra, bukan klasifikasi domain. |
| 3 | **Decision: Gambar kolonoskopi?** | *Tidak ada korelasi kode* | **TIDAK SESUAI (FIKTIF)** | **Aksi fiktif: tidak ada filter domain citra.** |
| 4 | Pesan "Not Colonoscopy Image" | *Tidak ada korelasi kode* | **TIDAK SESUAI (FIKTIF)** | **Pesan error fiktif tidak pernah ada di backend.** |
| 5 | Melakukan binary segmentation | `pipeline.py` (`predict_mask`) | Sesuai | Eksekusi model U-Net ResNet50. |
| 6 | Melakukan proses Grad-Cam | `pipeline.py` (`generate_gradcam`) | Sesuai | Grad-CAM pada layer konvolusi terakhir. |
| 7 | Menyimpan hasil segmentasi | `analysis_service.py` | Sesuai | Simpan mask, overlay, gradcam ke Supabase. |
| 8 | **User: "Mengirim hasil segmentasi"** | `AnalysisDetail.tsx` | **SALAH AKTOR / TYPO** | **Aktor User tertulis "Mengirim", seharusnya "Menampilkan".** |

### 4.5 Temuan Khusus dan Klasifikasi Masalah
- **[MAJOR — AKSI DAN PERCABANGAN FIKTIF]:** Percabangan *"Gambar kolonoskopi?"* dengan pesan error *"Not Colonoscopy Image"* tidak ada di dalam implementasi sistem. PIXEL-T tidak memiliki modul klasifikasi domain pra-segmentasi. Jika pengguna memasukkan gambar non-medis yang lolos validasi format, sistem tetap mengeksekusi U-Net dan menghasilkan masker kosong. Representasi ini berbahaya karena menyatakan fitur kecerdasan buatan yang sebenarnya tidak diimplementasikan.
- **[MAJOR — KESALAHAN SEMANTIK AKTOR PADA SWIMLANE USER]:** Pada swimlane *User* di bagian akhir alur, kotak aktivitas bertuliskan *"Mengirim hasil segmentasi & Penjelasan Model"*. Pengguna tidak pernah "mengirim" hasil segmentasi ke dirinya sendiri; pengguna bertindak sebagai pihak yang **"Menerima"** atau antarmuka yang **"Menampilkan hasil segmentasi & Penjelasan Model"**.

### 4.6 Rekomendasi Perbaikan
1. Ganti decision node *"Gambar kolonoskopi?"* dengan percabangan riil: *"Apakah polip terdeteksi?"* (`[Ya]` menampilkan mask dan Grad-CAM, `[Tidak]` menampilkan hasil *"Polip tidak terdeteksi"*); **ATAU** hapus percabangan tersebut dan ganti dengan decision *"Inferensi berhasil?"*.
2. Ubah teks pada swimlane *User* dari *"Mengirim hasil..."* menjadi *"Menampilkan hasil segmentasi & visualisasi Grad-CAM"*.

---

```
====================================================================================================
5. ACTIVITY DIAGRAM — HISTORY (`Activity Diagram - History.drawio.png`) [REVISI FINAL]
====================================================================================================
```

### 5.1 Tujuan Fitur
Menampilkan riwayat seluruh sesi analisis kolonoskopi milik dokter yang sedang terotentikasi, menyediakan fasilitas pencarian/filter data, navigasi menuju rincian hasil analisis, serta memberikan mekanisme penghapusan rekaman riwayat dan berkas gambar terkait dengan konfirmasi pengguna.

### 5.2 Ringkasan Alur yang Tergambar (Hasil Revisi Terbaru)
1. **User:** Membuka halaman History.
2. **System:** Mengambil data riwayat dari database.
3. **System:** Mengevaluasi decision *"Apakah riwayat tersedia?"*:
   - Cabang *"Tidak"*: User menampilkan pesan *"Riwayat Kosong"* $\rightarrow$ dialirkan ke *Merge Node* akhir.
   - Cabang *"Ya"*: System mengirimkan daftar riwayat $\rightarrow$ User menampilkan data riwayat.
4. **User:** Memilih decision *"Tindakan pada riwayat?"*:
   - Cabang *"Lihat Detail"*: System mengarahkan ke halaman detail hasil analisis $\rightarrow$ dialirkan ke *Merge Node* akhir.
   - Cabang *"Hapus"*: User menekan tombol hapus pada baris riwayat $\rightarrow$ System menampilkan dialog konfirmasi penghapusan.
5. **User:** Memilih decision *"Konfirmasi hapus?"*:
   - Cabang *"Tidak"*: System menutup modal tanpa menghapus data $\rightarrow$ dialirkan ke *Merge Node* akhir.
   - Cabang *"Ya"*: System menghapus data & berkas di database $\rightarrow$ System mengirimkan menu riwayat yang telah diperbarui $\rightarrow$ User menampilkan halaman History yang diperbarui $\rightarrow$ dialirkan ke *Merge Node* akhir.
6. **Merge Node:** Menggabungkan seluruh 4 cabang secara ortogonal.
7. **Activity Final Node:** Tepat 1 titik akhir aktivitas use case.

### 5.3 Ringkasan Alur Aktual Menurut Kode Sumber
Pada `frontend/src/pages/History.tsx`, `frontend/src/services/analysis.ts`, dan backend controller `analysis_controller.py`:
- `listHistory()` memanggil API yang memfilter berdasarkan `user_id`.
- Kondisi kosong ditangani via `<EmptyState title="No analysis history yet" />`.
- Melihat detail memanggil `navigate('/analysis/' + item.id)`.
- Tombol hapus memunculkan modal dialog `pendingDelete`.
- Tombol Batal menutup modal. Tombol Ya memanggil `deleteAnalysis(id)` yang menghapus baris tabel `analyses` serta berkas pada Supabase Storage bucket `analysis-images`.

### 5.4 Tabel Pencocokan Aktivitas dengan Bukti Kode
| No. | Aktivitas / Kondisi pada Diagram | Bukti Implementasi Kode | Hasil Pemeriksaan | Temuan & Tindakan |
|---|---|---|---|---|
| 1 | Membuka halaman History | `History.tsx` (rute `/history`) | **SESUAI** | Komponen riwayat utama. |
| 2 | Mengambil data riwayat dari database | `analysis.ts` (`listHistory`) | **SESUAI** | Query filtered by auth session. |
| 3 | Decision: Apakah riwayat tersedia? | `History.tsx` (`items.length === 0`) | **SESUAI** | Evaluasi ketersediaan riwayat. |
| 4 | Menampilkan pesan "Riwayat Kosong" | `History.tsx` (`<EmptyState />`) | **SESUAI** | State saat tidak ada rekaman. |
| 5 | Mengirim & menampilkan data riwayat | `History.tsx` (baris 205-380) | **SESUAI** | Render data table dan toolbar. |
| 6 | Decision: Tindakan pada riwayat? | `History.tsx` (aksi tombol) | **SESUAI** | Opsi Lihat Hasil vs Hapus. |
| 7 | Mengarahkan ke detail hasil analisis | `History.tsx` (baris 400) | **SESUAI** | `navigate('/analysis/' + id)`. |
| 8 | Menekan tombol hapus & dialog modal | `History.tsx` (`pendingDelete`) | **SESUAI** | Pembukaan modal konfirmasi. |
| 9 | Decision: Konfirmasi hapus? | `History.tsx` (modal buttons) | **SESUAI** | Tombol Cancel vs Yes Delete. |
| 10 | Menutup modal tanpa menghapus | `History.tsx` (`setPendingDelete(null)`) | **SESUAI** | Pembatalan operasi hapus. |
| 11 | Menghapus data & berkas | `analysis.ts` (`deleteAnalysis`) | **SESUAI** | Penghapusan DB & Storage. |
| 12 | Memperbarui tampilan History | `History.tsx` (refresh data) | **SESUAI** | Re-fetch dan re-render tabel. |
| 13 | Merge Node & Single Final Node | Standar UML 2.5 | **SESUAI** | 4 cabang menyatu ke 1 final node. |

### 5.5 Evaluasi Hasil Revisi
- **Seluruh Masalah Major Telah Selesai 100%:** Jumlah final node yang sebelumnya berjumlah 4 kini telah direduksi menjadi tepat **1 Activity Final Node**. Tidak ada jalur buntu (*dead ends*). Seluruh percabangan menyatu secara ortogonal pada sebuah *merge node*.
- **Kesesuaian Kode Sempurna:** Setiap node aksi memiliki padanan langsung pada berkas kode sumber.

### 5.6 Status Kelayakan
**FINAL — LAYAK DIMASUKKAN KE SKRIPSI**

---

```
====================================================================================================
6. ACTIVITY DIAGRAM — DOCTOR PROFILE (`Activity Diagram - Doctor Profile.drawio.png`) [REVISI FINAL]
====================================================================================================
```

### 6.1 Tujuan Fitur
Menampilkan profil dokter (nama, gelar, STR, spesialisasi, afiliasi rumah sakit, kontak), ringkasan statistik analisis klinis, serta menyediakan formulir modal untuk memperbarui data profil dokter dengan validasi input dan penyimpanan ganda (tabel `doctor_profiles` dan metadata akun Supabase Auth).

### 6.2 Ringkasan Alur yang Tergambar (Hasil Revisi Terbaru)
1. **User:** Membuka halaman Profil Dokter.
2. **System:** Mengambil data profil & riwayat aktifitas.
3. **System:** Mengirim data profil & riwayat aktifitas $\rightarrow$ User menampilkan profil dokter & statistik aktivitas.
4. **User:** Decision *"Apakah ingin mengubah profil?"*:
   - Cabang *"Tidak"*: langsung menuju *Merge Node* akhir.
   - Cabang *"Ya"*: User menekan tombol *"Edit Profile"* $\rightarrow$ System mengambil & mengirim dialog formulir Edit Profile $\rightarrow$ User mengisi atau memperbarui data profil.
5. **User:** Decision *"Aksi formulir?"*:
   - Cabang *"Batal"*: langsung menuju *Merge Node* akhir.
   - Cabang *"Simpan"*: System memvalidasi data input profil dokter.
6. **System:** Decision *"Apakah data valid?"*:
   - Cabang *"Tidak"*: User menampilkan pesan error validasi $\rightarrow$ **garis alur berputar kembali (*loop back*)** ke aktivitas *"Mengisi atau memperbarui data informasi profil"*.
   - Cabang *"Ya"*: System menyimpan profil dokter & sinkronisasi data $\rightarrow$ System mengirimkan notifikasi sukses $\rightarrow$ User menampilkan pesan sukses & halaman Profil Dokter yang diperbarui $\rightarrow$ menuju *Merge Node* akhir.
7. **Merge Node:** Menggabungkan seluruh 3 jalur utama ke **tepat 1 Activity Final Node**.

### 6.3 Ringkasan Alur Aktual Menurut Kode Sumber
Pada `frontend/src/pages/DoctorProfile.tsx` dan `frontend/src/services/profile.ts`:
- `fetchDoctorProfile()` mengambil data dari tabel `doctor_profiles`.
- `listHistory()` mengkalkulasi agregat statistik (total scan, deteksi polip, rata-rata waktu).
- Tombol "Edit Profile" membuka modal form.
- Tombol "Cancel" menutup modal tanpa menyimpan.
- Tombol "Simpan Profil" memicu `validateProfileData()`. Jika tidak valid, `setFormErrors()` menampilkan pesan error di dalam modal tanpa menutup modal. Pengguna memperbaiki data.
- Jika valid, `saveDoctorProfile()` menjalankan *upsert* pada tabel `doctor_profiles` dan `supabase.auth.updateUser()`. Notifikasi sukses ditampilkan selama 4 detik, dan modal ditutup.

### 6.4 Tabel Pencocokan Aktivitas dengan Bukti Kode
| No. | Aktivitas / Kondisi pada Diagram | Bukti Implementasi Kode | Hasil Pemeriksaan | Temuan & Tindakan |
|---|---|---|---|---|
| 1 | Membuka halaman Profil Dokter | `DoctorProfile.tsx` (`/profile`) | **SESUAI** | Komponen dasbor profil. |
| 2 | Mengambil data profil & riwayat | `profile.ts` & `analysis.ts` | **SESUAI** | Fetch paralel via `useEffect`. |
| 3 | Menampilkan profil & statistik | `DoctorProfile.tsx` (Section A-G) | **SESUAI** | Render ringkasan profil & stats. |
| 4 | Decision: Apakah ingin mengubah? | `DoctorProfile.tsx` (tombol Edit) | **SESUAI** | Pilihan antara read-only vs edit. |
| 5 | Menekan tombol "Edit Profile" | `DoctorProfile.tsx` (`handleOpenEdit`) | **SESUAI** | Pembukaan modal edit form. |
| 6 | Mengisi atau memperbarui data | `DoctorProfile.tsx` (`editFormData`) | **SESUAI** | State penampung form input. |
| 7 | Decision: Aksi formulir? | `DoctorProfile.tsx` (Cancel vs Submit)| **SESUAI** | Tombol Batal vs Simpan. |
| 8 | Memvalidasi data input | `profile.ts` (`validateProfileData`) | **SESUAI** | Pengecekan nama, STR, phone. |
| 9 | Decision: Apakah data valid? | `DoctorProfile.tsx` (`validation.isValid`) | **SESUAI** | Evaluasi error dictionary. |
| 10 | Tampilkan error & loop-back | `DoctorProfile.tsx` (`setFormErrors`) | **SESUAI** | Loop kembali ke pengisian form. |
| 11 | Simpan profil & sinkronisasi | `profile.ts` (`saveDoctorProfile`) | **SESUAI** | Upsert DB + Supabase Auth meta. |
| 12 | Notifikasi sukses & update profil | `DoctorProfile.tsx` (`saveSuccessMsg`)| **SESUAI** | Alert sukses 4 detik & re-render. |
| 13 | Merge Node & Single Final Node | Standar UML 2.5 | **SESUAI** | 3 cabang menyatu ke 1 final node. |

### 6.5 Evaluasi Hasil Revisi
- **Seluruh Masalah Major Telah Selesai 100%:** Reduksi multi-final node menjadi tepat **1 Activity Final Node**. Penambahan siklus koreksi (*loop back*) saat validasi gagal mencerminkan perilaku modal formulir yang sesungguhnya di web PIXEL-T.
- **Kesesuaian Kode Sempurna:** Seluruh atribut alur dan percabangan terbukti secara empiris pada basis kode.

### 6.6 Status Kelayakan
**FINAL — LAYAK DIMASUKKAN KE SKRIPSI**

---

```
====================================================================================================
7. ACTIVITY DIAGRAM — SIGN OUT (`Activity Diagram - Sign Out.drawio.png`)
====================================================================================================
```

### 7.1 Tujuan Fitur
Mengakhiri sesi autentikasi pengguna secara aman melalui modal dialog konfirmasi, mencabut token sesi JWT pada Supabase Auth, membersihkan state pengguna pada frontend (`AuthContext`), dan mengalihkan pengguna kembali ke halaman Sign In.

### 7.2 Ringkasan Alur yang Tergambar
User menekan tombol Sign Out pada menu navigasi $\rightarrow$ Sistem menutup menu navigasi $\rightarrow$ menampilkan modal dialog konfirmasi Sign Out $\rightarrow$ Decision: *"Konfirmasi Sign Out?"*:
- Cabang *"Tidak"*: Sistem menutup model tanpa mengakhiri sesi $\rightarrow$ User tetap berada pada halaman saat ini $\rightarrow$ kembali ke menu navigasi.
- Cabang *"Ya"*: Sistem memanggil Supabase Auth untuk mencabut sesi aktif $\rightarrow$ **Sistem menghapus data user & session dari AuthContext** $\rightarrow$ **Sistem menghapus data user & session dari AuthContext (DUPLIKASI)** $\rightarrow$ User dialihkan ke halaman sign in $\rightarrow$ selesai (1 final node).

### 7.3 Ringkasan Alur Aktual Menurut Kode Sumber
Pada `frontend/src/components/common/Header.tsx`, `Sidebar.tsx`, dan `AuthContext.tsx`:
1. Pengguna membuka dropdown profil atau sidebar, lalu mengklik tombol "Sign Out".
2. Frontend menutup dropdown/sidebar dan membuka modal konfirmasi sign out (`setIsSignOutModalOpen(true)`).
3. Jika pengguna memilih "Cancel" / "Tidak": modal ditutup (`setIsSignOutModalOpen(false)`), sesi tetap aktif, pengguna tetap di halaman saat ini.
4. Jika pengguna memilih "Yes, Sign Out" / "Ya":
   - Memanggil `signOut()` pada `AuthContext.tsx`.
   - `supabase.auth.signOut()` mencabut sesi di server.
   - State `user` dan `session` direset menjadi `null`.
   - `localStorage.removeItem` membersihkan token lokal.
   - Frontend mengeksekusi `navigate('/login')`.

### 7.4 Tabel Pencocokan Aktivitas dengan Bukti Kode
| No. | Aktivitas / Kondisi pada Diagram | Bukti Implementasi Kode | Hasil Pemeriksaan | Temuan & Tindakan |
|---|---|---|---|---|
| 1 | Menekan tombol Sign Out | `Header.tsx` (baris 112) | Sesuai | Tombol sign out di nav header. |
| 2 | Menutup menu navigasi | `Header.tsx` (`setIsMenuOpen(false)`) | Sesuai | State dropdown ditutup. |
| 3 | Menampilkan modal dialog konfirmasi | `Header.tsx` (`<Modal>`) | Sesuai | Modal prompt konfirmasi logout. |
| 4 | Decision: Konfirmasi Sign Out? | `Header.tsx` (tombol aksi modal) | Sesuai | Tombol Cancel vs Confirm Logout. |
| 5 | Menutup model tanpa mengakhiri sesi | `Header.tsx` (handler Cancel) | Sesuai (Typo) | Typo "model" seharusnya "modal". |
| 6 | Tetap berada pada halaman saat ini | `Header.tsx` (state tidak berubah)| Sesuai | Pembatalan logout. |
| 7 | Memanggil Supabase Auth cabut sesi | `AuthContext.tsx` (`signOut`) | Sesuai | `supabase.auth.signOut()`. |
| 8 | **Menghapus data user dari AuthContext**| `AuthContext.tsx` (baris 72-76) | **DUPLIKASI** | **Node pertama dari duplikasi.** |
| 9 | **Menghapus data user dari AuthContext**| `AuthContext.tsx` (baris 72-76) | **DUPLIKASI** | **Node kedua identik berturut-turut.** |
| 10 | Dialihkan ke halaman sign in | `Header.tsx` (baris 135) | Sesuai | `navigate('/login')`. |

### 7.5 Temuan Khusus dan Klasifikasi Masalah
- **[MAJOR — DUPLIKASI NODE IDENTIK BERTURUT-TURUT]:** Terdapat dua kotak aksi berturut-turut pada swimlane *System* dengan teks yang sama persis: *"Menghapus data user & session dari AuthContext"* $\rightarrow$ *"Menghapus data user & session dari AuthContext"*. Ini adalah cacat penggambaran yang nyata dan akan langsung terlihat sebagai kesalahan ceroboh dalam penulisan Bab IV skripsi.
- **[MINOR — TYPO LABEL]:** Pada cabang "Tidak", kotak aksi tertulis *"Menutup model tanpa mengakhiri sesi"* (kata *"model"* seharusnya *"modal"*).

### 7.6 Rekomendasi Perbaikan
1. Hapus salah satu kotak aksi *"Menghapus data user & session dari AuthContext"* sehingga hanya ada satu kali eksekusi pembersihan konteks.
2. Koreksi kata *"model"* menjadi *"modal"*.

---

## BAGIAN E — PEMERIKSAAN LINTASDIAGRAM (CROSS-DIAGRAM CONSISTENCY)

1. **Konsistensi Aktor dan Swimlane:**
   Seluruh tujuh diagram secara seragam menggunakan dua swimlane: **User** (sebelah kiri) dan **System** (sebelah kanan). Batas tanggung jawab antara interaksi pengguna dan komputasi sistem sudah konsisten, kecuali pada diagram *Segmentation* di mana aksi penerimaan hasil tertulis "Mengirim" pada swimlane User.
2. **Konsistensi Siklus Autentikasi:**
   Alur autentikasi saling berkaitan secara logis: *Sign Up* mengarahkan ke *Sign In*, *Sign In* membentuk sesi aktif menuju *Dashboard*, dan *Sign Out* mencabut sesi Supabase Auth lalu mengembalikan pengguna ke *Sign In*.
3. **Konsistensi Manajemen Data Polip (Upload $\rightarrow$ Segmentation $\rightarrow$ History):**
   - *Upload Image* menghasilkan antrean kerja pada backend.
   - *Segmentation* memproses citra menjadi mask dan Grad-CAM lalu menyimpannya ke Supabase Storage.
   - *History* menampilkan rekaman tersebut, menyediakan navigasi detail, dan memungkinkan penghapusan data secara sinkron dengan Supabase Storage.

---

## BAGIAN F — DAFTAR REVISI BERDASARKAN PRIORITAS

### 1. Kategori MAJOR (Wajib Diperbaiki)
1. **Activity Diagram - Sign Up:**
   - **Masalah:** Percabangan logika terbalik pada decision node *"Email sudah digunakan?"*. Cabang "Ya" malah mengarah ke sukses pendaftaran, sedangkan cabang "Tidak" mengarah ke error.
   - **Perbaikan:** Tukar panah guard atau sesuaikan pertanyaan decision node.
2. **Activity Diagram - Upload Image:**
   - **Masalah:** Keberadaan node aksi fiktif *"Menutup menu navigasi"* tepat setelah pemilihan berkas citra.
   - **Perbaikan:** Hapus kotak *"Menutup menu navigasi"*. Hubungkan aksi pemilihan berkas langsung ke decision validasi berkas.
3. **Activity Diagram - Segmentation:**
   - **Masalah:** Decision node fiktif *"Gambar kolonoskopi?"* dan error fiktif *"Not Colonoscopy Image"*, serta salah kata kerja *"Mengirim hasil..."* pada swimlane User.
   - **Perbaikan:** Sesuaikan decision node menjadi evaluasi inferensi/deteksi polip yang riil, dan ubah label aksi User menjadi *"Menampilkan hasil segmentasi & visualisasi Grad-CAM"*.
4. **Activity Diagram - Sign Out:**
   - **Masalah:** Duplikasi kotak aksi identik berturut-turut *"Menghapus data user & session dari AuthContext"*.
   - **Perbaikan:** Hapus salah satu kotak aksi duplikat tersebut.

### 2. Kategori MINOR (Disarankan Diperbaiki)
1. **Sign Up:** Typo *"halam"* $\rightarrow$ *"halaman"*.
2. **Sign In:** Typo *"halam"* $\rightarrow$ *"halaman"*.
3. **Sign Out:** Typo *"model"* $\rightarrow$ *"modal"*.

---

## BAGIAN G — KESIMPULAN FINAL DAN KELAYAKAN SKRIPSI

Menjawab pertanyaan evaluasi kelayakan akademik Bab IV skripsi S1:

1. **Apakah ketujuh diagram sudah sesuai dengan kode web PIXEL-T?**  
   *Dua diagram (History dan Doctor Profile) sudah 100% sesuai.* Lima diagram lainnya memiliki tingkat kesesuaian bervariasi (Sign In sesuai, sementara Sign Up, Upload, Segmentation, dan Sign Out memiliki deviasi/cacat spesifik).
2. **Apakah urutan aktivitas dan seluruh percabangan penting sudah benar?**  
   *Belum seluruhnya.* Terdapat logika guard yang terbalik pada Sign Up dan percabangan fiktif pada Segmentation.
3. **Apakah diagram yang sederhana tetap cukup menjelaskan fitur utama?**  
   *Ya.* Tingkat abstraksi yang dipilih sudah sangat proporsional untuk skripsi S1 tanpa membebani pembaca dengan detail teknis mikro framework.
4. **Diagram mana yang resmi berstatus FINAL dan siap masuk skripsi?**  
   - **Activity Diagram - History** (`FINAL — LAYAK DIMASUKKAN KE SKRIPSI`)
   - **Activity Diagram - Doctor Profile** (`FINAL — LAYAK DIMASUKKAN KE SKRIPSI`)
5. **Diagram mana yang siap dengan revisi minor?**  
   - **Activity Diagram - Sign In** (`LAYAK SETELAH REVISI MINOR` — perbaikan typo).
6. **Diagram mana yang wajib direvisi major?**  
   - **Activity Diagram - Sign Up** (Tukar guard cabang decision).
   - **Activity Diagram - Upload Image** (Hapus aksi fiktif tutup menu navigasi).
   - **Activity Diagram - Segmentation** (Hapus filter fiktif non-kolonoskopi, perbaiki label swimlane User).
   - **Activity Diagram - Sign Out** (Hapus kotak aksi duplikasi).

**Rekomendasi Tindakan Lanjut:**  
Gunakan berkas final `activity_diagram_history_final.png` dan `activity_diagram_doctor_profile_final.png` untuk Bab IV skripsi Anda sekarang. Lakukan perbaikan ringkas pada 4 diagram yang memerlukan perbaikan Major sesuai rekomendasi di atas agar seluruh 7 diagram mencapai kelayakan 100% paripurna.
