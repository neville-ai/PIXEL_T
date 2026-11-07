# AUDIT USE CASE DIAGRAM — SISTEM PIXEL-T

**Dokumen Pendukung Bab IV Skripsi S1**
Disusun berdasarkan analisis implementasi aktual kode sumber web PIXEL-T.
Berkas audit ini melengkapi hasil revisi `USE_CASE_DIAGRAM_PIXELT_AUDIT_REVISED.drawio` / `.png` dan dokumen penjelasan `PENJELASAN_USE_CASE_DIAGRAM_PIXELT_AUDIT_REVISED.md`.

Status akhir: **TERVALIDASI DENGAN REVISI** (lihat Bagian K).

---

## A. Ringkasan Eksekutif

Audit ini memvalidasi kesesuaian *Use Case Diagram* PIXEL-T terhadap implementasi aktual sistem, dengan penekanan pada pemisahan hak akses peran **Admin** dan **Dokter** yang diperkenalkan melalui migrasi database 007 dan 008.

Temuan utama:

1. **Model peran terkonfirmasi pada implementasi.** Admin direpresentasikan secara eksklusif melalui `auth.users.raw_app_meta_data.role = 'admin'` yang hanya dapat ditulis melalui Supabase Admin API (service-role), tanpa tabel `admins` dan tanpa baris pada `doctor_profiles`. Dokter direpresentasikan melalui baris `public.doctor_profiles` dengan kolom `role` dan `account_status` (`pending` / `approved` / `rejected`).
2. **Diagram revisi sebelumnya (`USE_CASE_DIAGRAM_PIXELT_ROLE_ADMIN_REVISED.drawio`) tidak lengkap.** Terdapat asosiasi yang hilang: Admin → *Dashboard Admin* / *Daftar Dokter* / *Setujui Akun Dokter* / *Tolak Akun Dokter*, dan Dokter → *Upload Image* / *Segmentation* / *View History* / *View Doctor Profile*. Akibatnya, empat *use case* admin pada diagram lama tidak terhubung ke aktor mana pun sehingga tidak sah secara notasi UML.
3. **Diagram revisi audit memperbaiki seluruh asosiasi tersebut.** Diagram baru memuat 3 aktor, 14 *use case*, 14 relasi asosiasi, 1 relasi `<<include>>`, dan 3 relasi `<<extend>>`, seluruhnya terlacak ke kode sumber.
4. **Pemisahan hak akses terverifikasi pada tiga lapisan:** *frontend* (`AdminRoute`, `ProtectedRoute`, `DoctorRoute`, `PublicOnlyRoute`), *backend* (`require_admin`, `require_approved_doctor`), dan *basis data* (RLS + trigger 008 yang mengecualikan akun admin).
5. **Tidak ada *use case* fiktif** pada diagram revisi: seluruh 14 *use case* memiliki penerapan nyata pada kode. Sebaliknya, tiga artefak internal AI (*Validate Image*, *Generate Overlay*, *Generate Grad-CAM*) sengaja **tidak** dipetakan sebagai *use case* aktor karena merupakan langkah internal pipeline yang tidak dapat diinisiasi pengguna secara independen.

---

## B. Inventarisasi Sumber

### B.1 Frontend (React 18 + TypeScript + Vite)

| Berkas | Peran terhadap audit |
|--------|----------------------|
| `frontend/src/routes/AppRoutes.tsx` | Daftar rute resmi dan pemetaan penjaga rute |
| `frontend/src/components/auth/AdminRoute.tsx` | Penjaga rute admin (`role === 'admin'`) |
| `frontend/src/components/auth/ProtectedRoute.tsx` | Penjaga rute klinis (autentikasi + `account_status === 'approved'`) |
| `frontend/src/components/auth/DoctorRoute.tsx` | Penjaga rute profil dokter (dokter saja; admin dialihkan) |
| `frontend/src/components/auth/PublicOnlyRoute.tsx` | Penjaga rute publik (`/login`, `/register`) |
| `frontend/src/context/AuthContext.tsx` | Resolusi peran, `signIn`, `signUp`, `signOut` |
| `frontend/src/services/auth.ts` | `registerUser`, `loginUser`, `logoutUser`, `resetPasswordUser` |
| `frontend/src/pages/auth/Login.tsx` | Sign In + mode *inline* Reset Password |
| `frontend/src/pages/auth/Register.tsx` | Sign Up (khusus calon dokter) |
| `frontend/src/pages/auth/ResetPassword.tsx` | Penyelesaian reset kata sandi |
| `frontend/src/pages/dashboard/Dashboard.tsx` | Dasbor dokter |
| `frontend/src/pages/analysis/NewAnalysis.tsx` | Unggah citra + pemicu segmentasi |
| `frontend/src/pages/analysis/AnalysisResult.tsx` | Hasil segmentasi (polling) |
| `frontend/src/pages/history/History.tsx` | Riwayat + pencarian/filter klien + hapus |
| `frontend/src/pages/profile/DoctorProfile.tsx` | Lihat/edit profil + avatar |
| `frontend/src/pages/admin/AdminDashboard.tsx` | Dasbor admin, daftar, setujui/tolak |
| `frontend/src/services/analysis.ts` | `createAnalysis`, `getAnalysis`, `listHistory`, `deleteAnalysis` |
| `frontend/src/services/profile.ts` | `fetchDoctorProfile`, `saveDoctorProfile`, `uploadAvatar`, `deleteAvatar` |
| `frontend/src/components/layout/AppShell.tsx` | Navigasi sesuai peran |

### B.2 Backend (Python + Flask)

| Berkas | Peran terhadap audit |
|--------|----------------------|
| `backend/app/core/auth.py` | `require_auth`, `require_admin`, `require_approved_doctor`, `_get_user_role_and_status` |
| `backend/app/routes/admin.py` | Endpoint admin (dilindungi `require_admin`) |
| `backend/app/routes/analysis.py` | Endpoint analisis (dilindungi `require_approved_doctor`) |
| `backend/app/controllers/admin_controller.py` | Logika HTTP manajemen dokter |
| `backend/app/services/admin_service.py` | Transisi status (hanya dari `pending`) |

### B.3 Basis Data & AI

| Berkas | Peran terhadap audit |
|--------|----------------------|
| `database/migrations/001_create_analyses_and_storage.sql` | Tabel `analyses` + RLS + bucket penyimpanan |
| `database/migrations/002_add_ai_pipeline_metadata.sql` | Metadata pipeline (checkpoint, TTA, gradcam) |
| `database/migrations/004_create_doctor_profiles.sql` | Tabel `doctor_profiles` + RLS |
| `database/migrations/007_add_role_and_account_status.sql` | Kolom `role` dan `account_status`; dokumen bahwa admin disimpan pada `raw_app_meta_data.role` |
| `database/migrations/008_create_doctor_profile_trigger.sql` | Trigger pembuatan profil; mengecualikan akun admin |
| `ai/inference/pipeline.py` | Fase pipeline (preprocessing, inference, postprocessing, gradcam, artifact_composition) |

### B.4 Dokumen Referensi yang Dibandingkan

| Berkas | Catatan |
|--------|---------|
| `references/bab 4/use_case_diagram_revisi.png` | Objek audit utama (raster, tidak dimodifikasi) |
| `references/bab 4/SPESIFIKASI_REVISI_USE_CASE_DIAGRAM_PIXELT.md` | Kode sumber PlantUML baseline: 2 aktor, 13 *use case*, 4 `<<include>>`, 3 `<<extend>>` |
| `references/bab 4/USE_CASE_DIAGRAM_PIXELT_ROLE_ADMIN_REVISED.drawio` | Revisi peran sebelumnya, memiliki asosiasi hilang |
| `references/bab 4/LAPORAN_AUDIT_USE_CASE_PIXELT.md` | Audit lama (2 aktor, tanpa pemisahan peran) |
| `references/bab 4/AUDIT_DAMPAK_ROLE_ADMIN_DOKTER_PIXELT.md` | Audit dampak peran (perlu direkonsiliasi, lihat Bagian G) |

---

## C. Peta Implementasi

### C.1 Peta Rute ke *Use Case*

| Rute | Komponen | Penjaga | *Use case* |
|------|----------|---------|-----------|
| `/register` | `Register` | `PublicOnlyRoute` | Sign Up |
| `/login` | `Login` | `PublicOnlyRoute` | Sign In, Reset Password (tahap permintaan) |
| `/reset-password` | `ResetPassword` | — (rute publik berdiri sendiri) | Reset Password (tahap pembaruan) |
| `/dashboard` | `Dashboard` | `ProtectedRoute` | (beranda dokter; ringkasan riwayat) |
| `/analysis/new` | `NewAnalysis` | `ProtectedRoute` | Upload Image, Segmentation |
| `/analysis/:id` | `AnalysisResult` | `ProtectedRoute` | (tampilan hasil segmentasi) |
| `/history` | `History` | `ProtectedRoute` | View History, Search / Filter History |
| `/history/:id` | `HistoryDetail` | `ProtectedRoute` | (detail riwayat) |
| `/profile` | `DoctorProfile` | `DoctorRoute` | View Doctor Profile, Edit Doctor Profile |
| `/admin` | `AdminDashboard` | `AdminRoute` | View Admin Dashboard, View Doctor Registrations, Approve/Reject |

### C.2 Alur Otorisasi Backend

| Endpoint | Dekorator | Sumber otorisasi |
|----------|-----------|------------------|
| `GET /api/admin/doctors` | `require_admin` | `app_metadata.role == 'admin'` |
| `GET /api/admin/doctors/stats` | `require_admin` | idem |
| `GET /api/admin/doctors/<id>` | `require_admin` | idem |
| `POST /api/admin/doctors/<id>/approve` | `require_admin` | idem |
| `POST /api/admin/doctors/<id>/reject` | `require_admin` | idem |
| `POST /api/analysis` | `require_approved_doctor` | `doctor_profiles.role` + `account_status == 'approved'` |
| `GET /api/analysis/<id>` | `require_approved_doctor` | idem |
| `GET /api/history` | `require_approved_doctor` | idem |
| `DELETE /api/history/<id>` | `require_approved_doctor` | idem |

### C.3 Model Peran pada Basis Data

| Aspek | Admin | Dokter |
|-------|-------|--------|
| Tabel tersendiri | Tidak ada tabel `admins` | `public.doctor_profiles` |
| Baris di `doctor_profiles` | Tidak ada (trigger 008 mengecualikan) | Ada, `user_id` UNIQUE merujuk `auth.users.id` |
| Sumber kebenaran peran | `auth.users.raw_app_meta_data.role = 'admin'` (hanya dapat ditulis server via Supabase Admin API) | `doctor_profiles.role = 'doctor'` |
| Status akun | Tidak berlaku | `account_status`: `pending` / `approved` / `rejected` |
| Jalur pembuatan akun | Eksternal (service-role key) | Sign Up publik `/register` (memicu trigger 008 → `pending`) |

---

## D. Matriks Hak Akses

Legenda: **Y** = diizinkan; **N** = ditolak; **—** = tidak berlaku.

| *Use case* | Calon Pengguna (belum login) | Dokter `pending` | Dokter `rejected` | Dokter `approved` | Admin |
|---|---|---|---|---|---|
| Sign Up | Y | N (sudah terdaftar) | N | N | N (dibuat eksternal) |
| Sign In | Y | Y | Y | Y | Y |
| Sign Out | — | Y | Y | Y | Y |
| Reset Password | Y | Y | Y | Y | Y |
| Upload Image | N | N (`ProtectedRoute`) | N | Y | N (`DoctorRoute`/`AdminRoute`) |
| Segmentation | N | N | N | Y | N |
| View History | N | N | N | Y | N |
| Search / Filter History | N | N | N | Y | N |
| View Doctor Profile | N | N | N | Y | N (dialihkan ke `/admin`) |
| Edit Doctor Profile | N | N | N | Y | N |
| View Admin Dashboard | N | N | N | N (`AdminRoute`) | Y |
| View Doctor Registrations | N | N | N | N | Y |
| Approve Doctor Account | N | N | N | N | Y |
| Reject Doctor Account | N | N | N | N | Y |

**Bukti penolakan:**

- **Frontend:** `AdminRoute.tsx` mengizinkan hanya `role === 'admin'`; `ProtectedRoute.tsx` menolak `pending` dan `rejected`; `DoctorRoute.tsx` mengalihkan admin ke `/dashboard`/`/admin` dan menolak `pending`/`rejected`.
- **Backend:** `require_admin` menaikkan `403 FORBIDDEN` bila `app_metadata.role != 'admin'` (`core/auth.py`); `require_approved_doctor` menaikkan `403 ACCOUNT_PENDING` / `403 ACCOUNT_REJECTED` / `403 FORBIDDEN` (`core/auth.py`).
- **Basis data:** RLS pada `analyses` dan `doctor_profiles` membatasi akses baris per `user_id`; operasi admin memakai *service-role client* yang melewati RLS namun tetap dijaga dekorator backend.

---

## E. Matriks Audit *Use Case*

Seluruh 14 *use case* pada diagram revisi diperiksa terhadap kode sumber.

| # | *Use case* | Aktor | Status | Bukti implementasi |
|---|-----------|-------|--------|--------------------|
| 1 | **Sign Up** | Calon Pengguna | ✅ TERIMPLEMENTASI | `Register.tsx` (formulir + validasi) → `AuthContext.signUp` → `services/auth.ts:131` `registerUser()` → `supabase.auth.signUp()` dengan metadata `full_name`, `hospital`, `primary_specialty`. Trigger 008 membuat baris `doctor_profiles` berstatus `pending`. Sign Up bersifat khusus dokter; tidak ada jalur pendaftaran publik untuk admin. |
| 2 | **Sign In** | Calon Pengguna, Dokter, Admin | ✅ TERIMPLEMENTASI | `Login.tsx` → `AuthContext.signIn` → `loginUser()` → `supabase.auth.signInWithPassword()`. `AuthContext.tsx` menentukan prioritas peran: `app_metadata.role` (admin) lebih dahulu, lalu `doctor_profiles.role` + `account_status`. |
| 3 | **Sign Out** | Dokter, Admin | ✅ TERIMPLEMENTASI | `AuthContext.tsx:206` `signOut()` → `logoutUser()` → `supabase.auth.signOut()`; dipanggil dari `AppShell.tsx` dengan modal konfirmasi. |
| 4 | **Reset Password** | (melalui Sign In) | ✅ TERIMPLEMENTASI | Dua tahap: `Login.tsx` mode `reset` → `resetPasswordUser()` → `supabase.auth.resetPasswordForEmail()`; dan `/reset-password` (`ResetPassword.tsx`) → `supabase.auth.updateUser({ password })` setelah sesi *recovery*. |
| 5 | **Upload Image** | Dokter | ✅ TERIMPLEMENTASI | `NewAnalysis.tsx` (validasi klien: ekstensi, MIME, ukuran ≤ 10 MB) → `services/analysis.ts` `createAnalysis()` → `POST /api/analysis` (dilindungi `require_approved_doctor`) → `analysis_controller.create_analysis()` memvalidasi berkas dan mengembalikan HTTP 202. |
| 6 | **Segmentation** | Dokter | ✅ TERIMPLEMENTASI | `analysis_service.py` + `ai/inference/pipeline.py`: preprocessing → inferensi U-Net → postprocessing → Grad-CAM → komposisi artefak; `AnalysisResult.tsx` melakukan polling `GET /api/analysis/<id>`. |
| 7 | **View History** | Dokter | ✅ TERIMPLEMENTASI | `History.tsx` → `listHistory()` → `GET /api/history` (dilindungi `require_approved_doctor`), menampilkan tabel riwayat milik `user_id`. |
| 8 | **Search / Filter History** | Dokter | ✅ TERIMPLEMENTASI | `History.tsx:118` `useMemo` dengan tiga filter berbasis klien: `query` (nama berkas), `statusFilter`, `dateFilter`. Terkait `View History` melalui `<<extend>>`. |
| 9 | **View Doctor Profile** | Dokter | ✅ TERIMPLEMENTASI | `DoctorProfile.tsx` → `fetchDoctorProfile()` dari tabel `doctor_profiles` + statistik dari `listHistory()`. Dilindungi `DoctorRoute`. |
| 10 | **Edit Doctor Profile** | Dokter | ✅ TERIMPLEMENTASI | `DoctorProfile.tsx:445` → `saveDoctorProfile()` (upsert `doctor_profiles`); avatar melalui `uploadAvatar()` / `deleteAvatar()` (baris 338–390). Terkait `View Doctor Profile` melalui `<<extend>>`. |
| 11 | **View Admin Dashboard** | Admin | ✅ TERIMPLEMENTASI | `AdminDashboard.tsx` → `GET /api/admin/doctors/stats` (baris 56) dengan agregat total/pending/approved/rejected. Dilindungi `AdminRoute` + `require_admin`. |
| 12 | **View Doctor Registrations** | Admin | ✅ TERIMPLEMENTASI | `AdminDashboard.tsx:46` `fetchAdminDoctors()` → `GET /api/admin/doctors` (opsional `?status=`); `admin_service.list_doctors()` mengembalikan `full_name`, `email`, `hospital`, `account_status`, `created_at`, `rejection_reason`. |
| 13 | **Approve Doctor Account** | Admin | ✅ TERIMPLEMENTASI | `AdminDashboard.tsx:71` `approveDoctor()` → `POST /api/admin/doctors/<id>/approve`; `admin_service.approve_doctor()` (baris 135) hanya mengubah status **dari `pending`** menjadi `approved` (syarat `.eq('account_status','pending')`). |
| 14 | **Reject Doctor Account** | Admin | ✅ TERIMPLEMENTASI | `AdminDashboard.tsx:80` `rejectDoctor()` → `POST /api/admin/doctors/<id>/reject`; `admin_service.reject_doctor()` (baris 235) hanya dari `pending` menjadi `rejected`, menyimpan `rejection_reason`. Modal alasan tolak pada `AdminDashboard.tsx:189`. |

**Artefak internal (bukan *use case* aktor):**

| Artefak | Bukti | Pembenaran pemodelan |
|---------|-------|----------------------|
| Validate Image | `analysis_service.py` (validasi MIME/integritas Pillow) | Langkah internal pipeline, tidak dapat diinisiasi pengguna |
| Generate Overlay | `pipeline.py` fase `artifact_composition` | Selalu dijalankan sebagai bagian pipeline segmentasi |
| Generate Grad-CAM | `pipeline.py` fase `gradcam` + `analysis_service.py` | Selalu dijalankan sebagai bagian pipeline segmentasi |

---

## F. Audit Relasi UML

### F.1 Relasi `<<include>>`

| Relasi | Arah | Status | Analisis |
|--------|------|--------|----------|
| Segmentation `<<include>>` Upload Image | Segmentation → Upload Image | ✅ VALID | Segmentasi tidak dapat berjalan tanpa citra yang tersimpan. `POST /api/analysis` menolak permintaan tanpa berkas (`MISSING_FILE`) dan pipeline selalu memerlukan artefak asli. Relasi wajib, sehingga `<<include>>` tepat. |

### F.2 Relasi `<<extend>>`

| Relasi | Arah | Status | Analisis |
|--------|------|--------|----------|
| Reset Password `<<extend>>` Sign In | Reset Password → Sign In | ✅ VALID | Reset kata sandi bersifat opsional dan hanya dijalankan bila pengguna memilih mode `reset` pada `Login.tsx`. Arah *extending* → *base* sesuai UML 2.x. |
| Search / Filter History `<<extend>>` View History | Search / Filter History → View History | ✅ VALID | Riwayat dapat dilihat tanpa filter; pencarian/filter hanya aktif bila `query`, `statusFilter`, atau `dateFilter` diisi (`History.tsx:118–136`). |
| Edit Doctor Profile `<<extend>>` View Doctor Profile | Edit Doctor Profile → View Doctor Profile | ✅ VALID | Profil dapat dilihat tanpa mengedit; modal edit dan unggah avatar hanya aktif atas aksi pengguna (`DoctorProfile.tsx`). |

### F.3 Asosiasi Aktor–*Use Case*

| Aktor | *Use case* terhubung | Status |
|-------|----------------------|--------|
| Calon Pengguna | Sign Up, Sign In | ✅ LENGKAP |
| Dokter | Sign In, Sign Out, Upload Image, Segmentation, View History, View Doctor Profile | ✅ LENGKAP |
| Admin | Sign In, Sign Out, View Admin Dashboard, View Doctor Registrations, Approve Doctor Account, Reject Doctor Account | ✅ LENGKAP |

> Catatan: `Search / Filter History` dan `Edit Doctor Profile` tidak memiliki asosiasi langsung ke aktor karena keduanya merupakan *extending use case*; aktor mengaksesnya melalui *base use case* masing-masing. `Reset Password` juga tidak memiliki asosiasi langsung karena merupakan *extending use case* dari Sign In.

### F.4 Generalisasi

Tidak ada relasi generalisasi pada diagram revisi. Tidak ditemukan hierarki aktor (misalnya `Admin` mewarisi `Dokter`) pada implementasi: admin dan dokter adalah dua jalur otorisasi yang saling eksklusif (`AdminRoute` vs `DoctorRoute`). Penambahan generalisasi justru akan **menyesatkan** karena admin tidak mewarisi fitur klinis.

### F.5 Batas Sistem

Batas sistem berlabel **"Sistem PIXEL-T"** mencakup seluruh *use case* yang dijalankan oleh frontend React, backend Flask, dan pipeline AI. Ketiga komponen beroperasi sebagai satu kesatuan; tidak ada *use case* yang berada di luar batas sistem.

---

## G. Temuan Ketidaksesuaian

Temuan diurutkan berdasarkan prioritas. Tidak ada temuan yang mengubah kode aplikasi; seluruhnya bersifat dokumentasi/diagram.

### G.1 Kritis

**K-1 — Asosiasi admin hilang pada diagram revisi sebelumnya.**
`USE_CASE_DIAGRAM_PIXELT_ROLE_ADMIN_REVISED.drawio` memuat empat *use case* admin (`Dashboard Admin`, `Daftar Dokter`, `Setujui Akun Dokter`, `Tolak Akun Dokter`) **tanpa asosiasi** ke aktor Admin. Secara UML, *use case* tanpa aktor tidak memiliki pemicu dan tidak sah. **Dampak:** diagram lama tidak dapat dipertanggungjawabkan secara akademik. **Perbaikan:** seluruh asosiasi ditambahkan pada diagram revisi audit (`e12`–`e15`).

**K-2 — Asosiasi dokter hilang pada diagram revisi sebelumnya.**
`Upload Image`, `Segmentation`, `View History`, dan `View Doctor Profile` tidak terhubung ke aktor Dokter. **Dampak:** alur klinis utama tampak tidak memiliki pelaku. **Perbaikan:** asosiasi `e6`–`e9` ditambahkan.

### G.2 Tinggi

**T-1 — Klaim "tidak ada RBAC" pada audit lama tidak lagi benar.**
`LAPORAN_AUDIT_USE_CASE_PIXELT.md` menyatakan sistem tidak membedakan hak akses peran. Setelah migrasi 007/008 dan penjaga rute, klaim tersebut **kedaluwarsa**. **Perbaikan:** audit ini menggantinya dengan matriks hak akses (Bagian D).

**T-2 — Inkonsistensi basis URL API pada frontend.**
`AdminDashboard.tsx:44` memakai `import.meta.env.VITE_API_URL`, sedangkan `services/analysis.ts` memakai `VITE_API_BASE_URL`. Bila hanya salah satu variabel dikonfigurasi, salah satu kelompok endpoint dapat gagal. **Status:** dicatat sebagai temuan; **tidak diperbaiki** karena di luar lingkup audit diagram dan menyentuh kode aplikasi.

**T-3 — Catatan `reset-password` pada audit dampak peran keliru.**
`AUDIT_DAMPAK_ROLE_ADMIN_DOKTER_PIXELT.md` menyiratkan `/reset-password` dibungkus `PublicOnlyRoute`. Pada `AppRoutes.tsx:42–45`, rute tersebut **berdiri sendiri** (tanpa penjaga). **Dampak:** dokumentasi keamanan rute tidak akurat. **Perbaikan:** audit ini mencatat keadaan sebenarnya; rekomendasi pembungkusan `PublicOnlyRoute` diserahkan ke pengembang.

### G.3 Sedang

**S-1 — Navigasi seluler admin menampilkan tautan klinis.**
`AppShell.tsx` menyembunyikan `/profile` dan navigasi klinis untuk admin pada tampilan desktop, tetapi menu seluler masih merender tautan Dashboard/New Analysis/History. Penjaga rute tetap memblokir akses, sehingga ini adalah cacat kosmetik, bukan pelanggaran otorisasi.

**S-2 — Validasi status approve/reject hanya dari `pending`.**
`admin_service.py` menolak approve/reject bila status bukan `pending`. Diagram tidak menampilkan prasyarat ini. **Perbaikan:** prasyarat dicatat pada Bagian E (baris 13–14) dan dokumen penjelasan; diagram tetap minimal sesuai kaidah UML.

**S-3 — Sign Up mengembalikan sesi hanya bila konfirmasi email nonaktif.**
`Register.tsx` menangani dua jalur: langsung masuk (sesi aktif) atau `requiresEmailConfirmation`. Diagram tidak membedakan keduanya; hal ini wajar karena keduanya berada dalam satu *use case* Sign Up.

### G.4 Rendah

**R-1 — Penamaan campur bahasa pada diagram lama.**
Label seperti `Dashboard Admin`, `Daftar Dokter`, `Setujui Akun Dokter` bercampur dengan label Inggris. Diagram revisi audit menyeragamkan label menjadi bahasa Inggris akademik (`View Admin Dashboard`, `View Doctor Registrations`, `Approve Doctor Account`, `Reject Doctor Account`) agar konsisten dengan *use case* lain.

**R-2 — Artefak AI berpotensi disalahartikan sebagai *use case* aktor.**
Audit lama memodelkan `Validate Image`, `Generate Overlay`, dan `Generate Grad-CAM` sebagai *use case* terpisah. Diagram revisi audit mengeluarkannya dari level aktor dan mendokumentasikannya sebagai langkah internal pipeline (Bagian E).

---

## H. Rekomendasi Diagram

1. **Gunakan `USE_CASE_DIAGRAM_PIXELT_AUDIT_REVISED.drawio` / `.png` sebagai diagram final Bab IV.** Diagram ini memuat 3 aktor, 14 *use case*, 14 asosiasi, 1 `<<include>>`, dan 3 `<<extend>>`, seluruhnya terlacak ke kode.
2. **Pertahankan tiga aktor:** Calon Pengguna, Dokter, Admin. Jangan menambahkan generalisasi Admin → Dokter karena bertentangan dengan implementasi (dua jalur otorisasi eksklusif).
3. **Pertahankan Sign In dan Sign Out sebagai *use case* bersama** yang terhubung ke ketiga aktor (Calon Pengguna hanya ke Sign In). Hal ini mencerminkan satu halaman login yang melayani semua peran.
4. **Jangan memodelkan artefak pipeline AI sebagai *use case* aktor.** Cukup jelaskan sebagai langkah internal pada narasi `Segmentation`.
5. **Jika pembimbing mensyaratkan bahasa Indonesia penuh,** gunakan padanan: *View Admin Dashboard* → *Melihat Dasbor Admin*, *View Doctor Registrations* → *Melihat Pendaftaran Dokter*, *Approve Doctor Account* → *Menyetujui Akun Dokter*, *Reject Doctor Account* → *Menolak Akun Dokter*. Struktur dan relasi tidak berubah.
6. **Sertakan prasyarat status pada narasi, bukan pada diagram.** Diagram dijaga minimal; prasyarat `pending` untuk approve/reject dijelaskan pada tabel spesifikasi *use case*.
7. **Rekonsiliasi dokumen lama:** tandai `LAPORAN_AUDIT_USE_CASE_PIXELT.md` dan catatan `/reset-password` pada `AUDIT_DAMPAK_ROLE_ADMIN_DOKTER_PIXELT.md` sebagai **digantikan** oleh audit ini.

---

## I. Penjelasan Akademik

*Use Case Diagram* PIXEL-T memodelkan interaksi antara tiga aktor dan empat belas *use case* di dalam batas sistem. Aktor **Calon Pengguna** merepresentasikan individu yang belum memiliki sesi autentikasi dan hanya dapat melakukan **Sign Up** serta **Sign In**. Aktor **Dokter** merepresentasikan tenaga medis dengan akun berstatus `approved` yang dapat menjalankan alur klinis: **Upload Image**, **Segmentation**, **View History**, **Search / Filter History**, **View Doctor Profile**, dan **Edit Doctor Profile**, serta **Sign In** dan **Sign Out**. Aktor **Admin** merepresentasikan pengelola sistem yang tidak memiliki fitur klinis dan hanya dapat menjalankan **View Admin Dashboard**, **View Doctor Registrations**, **Approve Doctor Account**, dan **Reject Doctor Account**, selain **Sign In** dan **Sign Out**.

Pemisahan aktor Dokter dan Admin bukan sekadar konvensi diagram, melainkan tercermin pada tiga lapisan implementasi. Pada lapisan *frontend*, `AdminRoute` hanya mengizinkan `role === 'admin'`, sedangkan `ProtectedRoute` dan `DoctorRoute` mensyaratkan akun dokter yang telah disetujui. Pada lapisan *backend*, dekorator `require_admin` membaca `app_metadata.role`, sementara `require_approved_doctor` membaca `doctor_profiles.role` dan `account_status`. Pada lapisan basis data, akun admin tidak memiliki baris pada `doctor_profiles` karena trigger migrasi 008 secara eksplisit mengecualikan `raw_app_meta_data.role = 'admin'`. Dengan demikian, diagram merepresentasikan pembedaan hak akses yang benar-benar ditegakkan, bukan sekadar pembedaan visual.

Relasi `<<include>>` digunakan tepat satu kali, yaitu **Segmentation** `<<include>>` **Upload Image**, karena segmentasi tidak mungkin dijalankan tanpa citra yang tersimpan. Sebaliknya, relasi `<<extend>>` digunakan tiga kali untuk perilaku opsional: **Reset Password** memperluas **Sign In**, **Search / Filter History** memperluas **View History**, dan **Edit Doctor Profile** memperluas **View Doctor Profile**. Arah panah seluruh relasi `<<extend>>` mengikuti kaidah UML 2.x, yakni dari *extending use case* menuju *base use case*.

Artefak internal pipeline AI — validasi citra, pembuatan *overlay* segmentasi, dan pembangkitan Grad-CAM — tidak dimodelkan sebagai *use case* aktor karena ketiganya tidak dapat diinisiasi secara independen oleh pengguna. Ketiganya merupakan tahapan wajib di dalam **Segmentation** dan didokumentasikan pada narasi spesifikasi *use case*, sehingga diagram tetap ringkas tanpa kehilangan ketertelusuran teknis.

---

## J. Keterbatasan Audit

1. **Audit berbasis pembacaan kode sumber, bukan pengujian runtime.** Tidak ada pengujian otomatis, pengujian beban, atau pengujian penetrasi yang dijalankan dalam audit ini. Seluruh klaim kesesuaian didasarkan pada pembacaan statis berkas yang tercantum pada Bagian B.
2. **Validasi visual diagram terbatas.** Draw.io Desktop, PlantUML, dan Java tidak tersedia pada lingkungan audit. Validasi diagram dilakukan melalui (a) pemeriksaan *well-formedness* XML dengan `xml.etree.ElementTree`, (b) verifikasi bahwa setiap `source`/`target` sisi merujuk ID yang ada, dan (c) pemeriksaan berkas PNG dengan `PIL.Image.verify()`. Tidak ada pemeriksaan tata letak oleh *engine* UML resmi.
3. **`use_case_diagram_revisi.png` adalah raster.** Tidak tersedia sumber vektor asli, sehingga perbandingan elemen dilakukan secara konseptual terhadap spesifikasi PlantUML dan diagram revisi, bukan melalui ekstraksi vektor.
4. **Tidak ada akses ke lingkungan Supabase produksi.** Konfigurasi `app_metadata` admin dan data `doctor_profiles` tidak diperiksa secara langsung; kesimpulan diambil dari migrasi SQL dan kode otorisasi.
5. **Kredensial tidak diungkap.** Audit tidak membaca, menyalin, atau menampilkan *service-role key*, kata sandi, atau token apa pun.
6. **Inkonsistensi `VITE_API_URL` vs `VITE_API_BASE_URL` (T-2) tidak diverifikasi pada runtime.** Dampak aktual bergantung pada berkas `.env` yang tidak diperiksa.
7. **Perubahan kode tidak dilakukan.** Audit ini hanya menghasilkan artefak dokumentasi/diagram baru; tidak ada berkas aplikasi, migrasi, atau konfigurasi yang diubah.

---

## K. Status Akhir

**Status: TERVALIDASI DENGAN REVISI.**

| Kriteria | Hasil |
|----------|-------|
| Seluruh aktor pada diagram memiliki dasar implementasi | ✅ 3/3 aktor terverifikasi |
| Seluruh *use case* pada diagram memiliki dasar implementasi | ✅ 14/14 *use case* terverifikasi |
| Seluruh asosiasi aktor–*use case* lengkap | ✅ 14/14 asosiasi lengkap |
| Relasi `<<include>>` valid | ✅ 1/1 valid |
| Relasi `<<extend>>` valid dan arah benar | ✅ 3/3 valid |
| Pemisahan hak akses Admin/Dokter terverifikasi | ✅ Tiga lapisan (frontend, backend, DB) |
| *Use case* fiktif | ✅ Tidak ditemukan |
| Generalisasi yang menyesatkan | ✅ Tidak ada |
| Validasi visual oleh *engine* UML | ⚠️ Terbatas (lihat J-2) |
| Pengujian runtime | ⚠️ Tidak dilakukan (lihat J-1) |

**Keputusan:** `USE_CASE_DIAGRAM_PIXELT_AUDIT_REVISED.drawio` / `.png` **layak** digunakan sebagai *Use Case Diagram* Bab IV, dengan catatan keterbatasan validasi visual dan ketiadaan pengujian runtime sebagaimana diuraikan pada Bagian J. Dokumen audit lama yang bertentangan (`LAPORAN_AUDIT_USE_CASE_PIXELT.md` dan catatan `/reset-password` pada `AUDIT_DAMPAK_ROLE_ADMIN_DOKTER_PIXELT.md`) dinyatakan **digantikan** oleh dokumen ini.

---

*Audit dilaksanakan melalui analisis statis terhadap kode sumber aktual web PIXEL-T. Seluruh temuan dapat dilacak ke berkas yang tercantum pada Bagian B. Tidak ada kode aplikasi yang diubah.*
