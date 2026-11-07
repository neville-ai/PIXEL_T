# LAPORAN DEEP AUDIT WEB PIXEL-T DAN VALIDASI USE CASE DIAGRAM

**Dokumen Laporan Audit — Skripsi S1 Sistem Informasi / Teknik Informatika**
Sistem: PIXEL-T (*Polyp Identification with eXplainable Intelligence for Early-stage Local Tissue detection*)
Lingkup: audit menyeluruh implementasi web PIXEL-T (frontend, backend, basis data, autentikasi, pipeline AI) dan validasi *Use Case Diagram*.

Jenis pemeriksaan: **analisis kode sumber (static code analysis)** dan **pengujian unit otomatis lokal** (pytest backend, Vitest frontend). Tidak ada pengujian browser / end-to-end manual yang dijalankan. Seluruh klaim pada laporan ini dapat ditelusuri ke berkas kode sumber yang tercantum pada Bagian B.

Status akhir: **TERVALIDASI DENGAN REVISI** (Bagian O).

Diagram final hasil audit: `USE_CASE_DIAGRAM_PIXELT_FINAL_AUDITED.drawio` / `.png`.
Naskah akademik: `PENJELASAN_USE_CASE_DIAGRAM_PIXELT_FINAL_AUDITED.md`.

---

## A. Ringkasan Eksekutif

1. **Implementasi sistem telah memuat pemisahan peran dua tingkat** (Admin dan Dokter) yang ditegakkan pada tiga lapisan: penjaga rute frontend (`AdminRoute`, `ProtectedRoute`, `DoctorRoute`, `PublicOnlyRoute`), dekorator otorisasi backend (`require_admin`, `require_approved_doctor`), dan kebijakan basis data (RLS + trigger migrasi 008).
2. **Identitas peran berbeda sumber kebenaran.** Admin bersumber dari `auth.users.app_metadata.role = 'admin'` yang hanya dapat ditulis di sisi server melalui Supabase Admin API (service-role key), tanpa tabel `admins` dan tanpa baris pada `doctor_profiles`. Dokter bersumber dari `public.doctor_profiles` dengan kolom `role` dan `account_status` (`pending` / `approved` / `rejected`).
3. **Seluruh 14 *use case* pada diagram revisi terimplementasi** dan dapat ditelusuri ke halaman, layanan, endpoint, dan tabel yang nyata. Tidak ditemukan *use case* fiktif.
4. **Diagram referensi sebelumnya memiliki cacat asosiasi** (empat *use case* admin dan empat *use case* dokter tidak terhubung ke aktor mana pun), yang telah diperbaiki pada revisi audit.
5. **Relasi UML dievaluasi ulang berdasarkan perilaku aktual:** satu `<<include>>` (Segmentation → Upload Image) dan tiga `<<extend>>` (Reset Password → Sign In; Search / Filter History → View History; Edit Doctor Profile → View Doctor Profile) seluruhnya valid. Generalisasi aktor tidak diterapkan karena bertentangan dengan implementasi (dua jalur otorisasi eksklusif).
6. **Pengujian otomatis tersedia dan lulus:** 110 test backend (pytest) dan 285 test frontend (Vitest, 18 berkas). Tidak ada pengujian browser, pengujian beban, maupun pengujian penetrasi.
7. **Tidak ditemukan bug pada alur Use Case** yang menuntut perubahan kode. Satu temuan kualitas kode bersifat dokumentatif (inkonsistensi variabel basis URL API frontend) dicatat sebagai rekomendasi, tanpa mengubah kode pada audit ini.

---

## B. Inventarisasi Proyek

Root proyek: `C:\Users\nevil\OneDrive\Dokumen\SKRIPSI\WEB_PIXELT` (bukan folder `references\bab 4`).

### B.1 Struktur Utama

| Bagian | Direktori / File Utama | Fungsi | Komponen Terkait |
|---|---|---|---|
| Frontend | `frontend/src/` (React 18 + TypeScript + Vite) | Antarmuka pengguna | `routes/AppRoutes.tsx`, `components/auth/*`, `pages/*`, `services/*`, `context/AuthContext.tsx` |
| Backend | `backend/app/` (Flask) | REST API dan otorisasi | `routes/`, `controllers/`, `services/`, `repositories/`, `core/auth.py` |
| Basis Data | `database/migrations/` (8 berkas SQL) | Skema, RLS, trigger | `analyses`, `doctor_profiles`, trigger 008, bucket storage |
| AI | `ai/inference/` | Pipeline segmentasi | `pipeline.py`, `segmentation.py`, `gradcam.py`, `preprocessing.py`, `postprocessing.py` |
| Pengujian | `tests/backend/`, `tests/frontend/`, `tests/ai/` | Unit test | pytest (backend), Vitest (frontend) |
| Referensi | `references/bab 4/` | Artefak diagram & audit | diagram, spesifikasi, laporan audit |

### B.2 Frontend

- **Rute resmi** (`AppRoutes.tsx`): `/login`, `/register` (dibungkus `PublicOnlyRoute`); `/reset-password` (berdiri sendiri, tanpa penjaga); `/dashboard`, `/analysis/new`, `/analysis/:id`, `/history`, `/history/:id` (`ProtectedRoute`); `/profile` (`DoctorRoute`); `/admin` (`AdminRoute`); fallback 404.
- **Penjaga rute:** `ProtectedRoute` memblokir `pending` dan `rejected`; `AdminRoute` hanya mengizinkan `role === 'admin'`; `DoctorRoute` menolak admin serta `pending`/`rejected`; `PublicOnlyRoute` mengalihkan pengguna terautentikasi sesuai peran.
- **Layanan:** `services/auth.ts` (`registerUser` baris 131, `loginUser` baris 195, `resetPasswordUser` baris 239), `services/analysis.ts` (`createAnalysis` 185, `getAnalysis` 194, `listHistory` 212, `deleteAnalysis` 218), `services/profile.ts`.
- **State autentikasi:** `AuthContext.tsx` menyelesaikan peran dengan prioritas `app_metadata.role` lebih dahulu (baris 74–87, 106–115, 148–152), lalu `doctor_profiles.role` + `account_status`.

### B.3 Backend

- **Endpoint:** `routes/admin.py` (5 endpoint, seluruhnya `@require_admin`), `routes/analysis.py` (4 endpoint, seluruhnya `@require_approved_doctor`), `routes/health.py`.
- **Otorisasi** (`core/auth.py`): `require_auth` (baris 11), `require_admin` (baris 87; membaca `app_metadata.role`, menolak dengan `403 FORBIDDEN`), `require_approved_doctor` (baris 176; membaca `doctor_profiles`, menolak `403 ACCOUNT_PENDING` / `403 ACCOUNT_REJECTED` / `403 FORBIDDEN`), `_get_user_role_and_status` (baris 278).
- **Lapisan:** controller → service → repository → Supabase client (service-role untuk operasi admin, yang melewati RLS namun tetap dijaga dekorator).

### B.4 Basis Data

- `analyses` (migrasi 001): `status` terbatas `processing`/`completed`/`failed` (CHECK constraint), kepemilikan `user_id` → `auth.users`.
- `doctor_profiles` (migrasi 004): `user_id` UNIQUE → `auth.users`, RLS baca/tulis per baris sendiri.
- Migrasi 007: menambah `role` dan `account_status`; mendokumentasikan bahwa admin disimpan pada `raw_app_meta_data.role` (jalur eksternal, tanpa registrasi publik).
- Migrasi 008: trigger AFTER INSERT pada `auth.users` membuat baris `doctor_profiles` `role='doctor'`, `account_status='pending'`, dan **mengecualikan akun admin**.

### B.5 Autentikasi dan Pipeline AI

- Supabase Auth dipakai frontend (Supabase JS) dan backend (verifikasi Bearer token). Sesi disimpan di sisi klien; backend selalu memverifikasi ulang token.
- Pipeline AI (`ai/inference/pipeline.py`) dijalankan sebagai job latar belakang setelah `POST /api/analysis` menerima berkas (HTTP 202, status `processing`); fase: praproses → inferensi U-Net → pascaproses → Grad-CAM → komposisi artefak. Status akhir `completed` atau `failed`, dipantau frontend melalui polling `GET /api/analysis/<id>`.

---

## C. Peta Arsitektur Aktual

```
Browser (React + Supabase JS)
  │  1. Autentikasi : /login, /register, /reset-password  →  Supabase Auth
  │  2. Role guard  : PublicOnlyRoute | ProtectedRoute | DoctorRoute | AdminRoute
  │  3. API call    : Authorization: Bearer <access_token>
  ▼
Flask API (backend/app)
  ├─ require_admin  ────────────► GET/POST /api/admin/*   (app_metadata.role == 'admin')
  ├─ require_approved_doctor ───► /api/analysis, /api/history (doctor_profiles.role + approved)
  ├─ AdminService / AnalysisService → Supabase (service-role)
  └─ Job latar belakang → ai/inference/pipeline.py (U-Net + Grad-CAM)
  ▼
Supabase (PostgreSQL + Auth + Storage)
  ├─ auth.users            : session, app_metadata.role (admin)
  ├─ public.doctor_profiles: role, account_status, trigger 008
  ├─ public.analyses       : status lifecycle, artefak AI
  └─ RLS + bucket storage (private)
```

**Alur end-to-end Sign Up (misal):** `Register.tsx` → validasi klien → `AuthContext.signUp` → `services/auth.ts: registerUser` → `supabase.auth.signUp(metadata)` → trigger 008 menulis `doctor_profiles` (`pending`) → navigasi/penanganan konfirmasi email. Tidak ada jalur pendaftaran publik untuk Admin.

**Alur end-to-end analisis:** `NewAnalysis.tsx` (validasi ekstensi, MIME, ukuran ≤ 10 MB) → `createAnalysis()` → `POST /api/analysis` (202, `processing`) → job latar belakang menjalankan pipeline → frontend polling `getAnalysis()` → `AnalysisResult.tsx` menampilkan hasil saat `completed`, atau pesan kegagalan saat `failed`.

---

## D. Pemetaan Fitur

| Fitur | Halaman Frontend | Service | Endpoint / DB | Role |
|---|---|---|---|---|
| Sign Up | `pages/auth/Register.tsx` | `services/auth.ts: registerUser` | `supabase.auth.signUp` + trigger 008 → `doctor_profiles` | Calon Pengguna |
| Sign In | `pages/auth/Login.tsx` | `AuthContext.signIn` → `loginUser` | `supabase.auth.signInWithPassword` + pembacaan peran | Calon Pengguna / Dokter / Admin |
| Sign Out | `components/layout/AppShell.tsx` (modal konfirmasi, baris 123) | `AuthContext.signOut` (baris 206) → `logoutUser` | `supabase.auth.signOut` | Dokter / Admin |
| Reset Password | `Login.tsx` (mode `reset`) + `pages/auth/ResetPassword.tsx` | `resetPasswordUser`, `supabase.auth.updateUser` | `/reset-password` rute publik mandiri | Pengguna berakun |
| Upload Image | `pages/analysis/NewAnalysis.tsx` | `services/analysis.ts: createAnalysis` | `POST /api/analysis` (`require_approved_doctor`) | Dokter approved |
| Segmentation | `pages/analysis/AnalysisResult.tsx` (polling) | `analysis_service.py` + `ai/inference/pipeline.py` | `analyses.status` + artefak Storage | Dokter approved |
| View History | `pages/history/History.tsx` | `services/analysis.ts: listHistory` | `GET /api/history` | Dokter approved |
| Search / Filter History | `History.tsx` (baris 118–136, `useMemo`) | filter klien | — | Dokter approved |
| View Doctor Profile | `pages/profile/DoctorProfile.tsx` | `services/profile.ts: fetchDoctorProfile` | `public.doctor_profiles` | Dokter approved |
| Edit Doctor Profile | `DoctorProfile.tsx` (modal edit, baris 445) | `saveDoctorProfile`, `uploadAvatar`, `deleteAvatar` | upsert `doctor_profiles` | Dokter approved |
| View Admin Dashboard | `pages/admin/AdminDashboard.tsx` (baris 55, 226) | fetch klien `VITE_API_URL` | `GET /api/admin/doctors/stats` | Admin |
| View Doctor Registrations | `AdminDashboard.tsx` (baris 46, 208) | fetch klien | `GET /api/admin/doctors?status=` | Admin |
| Approve Doctor Account | `AdminDashboard.tsx` (baris 71, 249) | `admin_service.approve_doctor` (hanya dari `pending`) | `POST /api/admin/doctors/<id>/approve` | Admin |
| Reject Doctor Account | `AdminDashboard.tsx` (baris 80, 269) | `admin_service.reject_doctor` (hanya dari `pending`, menyimpan `rejection_reason`) | `POST /api/admin/doctors/<id>/reject` | Admin |

---

## E. Audit Autentikasi dan Role

### E.1 Calon Pengguna (belum terautentikasi)

- Dapat mengakses `/login`, `/register`, dan `/reset-password`.
- Dapat melakukan Sign Up (khusus calon dokter) dan Sign In.
- Rute klinis dan admin seluruhnya diblokir (`ProtectedRoute` / `AdminRoute` → redirect `/login`).
- Rute `/reset-password` **berdiri sendiri** tanpa penjaga rute (`AppRoutes.tsx` baris 42–45); namun halaman tersebut hanya menyetel kata sandi bila sesi *recovery* valid, jika tidak dikembalikan ke `/login` (`ResetPassword.tsx` baris 33–36).

### E.2 Dokter

- Sumber kebenaran: baris `public.doctor_profiles` (`role`, `account_status`) — dibaca frontend melalui `fetchUserProfileStatus` dan backend melalui `_get_user_role_and_status`.
- `pending`: dapat Sign In tetapi seluruh rute klinis diarahkan kembali ke `/login`; backend menolak `403 ACCOUNT_PENDING`.
- `rejected`: sama, dengan `403 ACCOUNT_REJECTED`.
- `approved`: akses penuh ke rute klinis dan endpoint analisis; tetap ditolak dari seluruh endpoint admin (`require_admin` tidak mengenali peran dokter).
- Sign Up memicu trigger migrasi 008 sehingga status awal selalu `pending`; tidak ada jalur pembuatan dokter berstatus `approved` langsung dari publik.

### E.3 Admin

- Sumber kebenaran: `auth.users.app_metadata.role = 'admin'` — hanya dapat ditulis server-side via Supabase Admin API; `user_metadata` sengaja tidak dipakai karena dapat diubah klien (`core/auth.py` baris 142–147).
- Tidak memiliki baris `doctor_profiles` (trigger 008 mengecualikannya); sehingga `require_approved_doctor` menolak admin dengan `403 FORBIDDEN` (baris 228–234).
- Tidak memiliki fitur klinis; `DoctorRoute` mengalihkan admin dari `/profile`, dan `AdminRoute` menolak semua non-admin.
- Keamanan endpoint admin tidak bergantung pada frontend semata: seluruh 5 endpoint admin dibungkus `require_admin` pada route.

### E.4 Matriks Hak Akses

Legenda: **Y** = diizinkan; **N** = ditolak; **—** = tidak relevan.

| Fungsi | Calon Pengguna | Dokter Pending | Dokter Rejected | Dokter Approved | Admin |
|---|---|---|---|---|---|
| Sign Up | Y | N (sudah punya akun) | N | N | N (dibuat eksternal) |
| Sign In | Y | Y | Y | Y | Y |
| Sign Out | — | Y | Y | Y | Y |
| Reset Password | Y | Y | Y | Y | Y |
| Upload Image | N | N | N | Y | N |
| Segmentation | N | N | N | Y | N |
| View History | N | N | N | Y | N |
| Search / Filter History | N | N | N | Y | N |
| View Doctor Profile | N | N | N | Y | N |
| Edit Doctor Profile | N | N | N | Y | N |
| View Admin Dashboard | N | N | N | N | Y |
| View Doctor Registrations | N | N | N | N | Y |
| Approve Doctor Account | N | N | N | N | Y |
| Reject Doctor Account | N | N | N | N | Y |

**Bukti frontend:** `AdminRoute.tsx` (baris 32), `ProtectedRoute.tsx` (baris 31), `DoctorRoute.tsx` (penolakan admin/`pending`/`rejected`), `PublicOnlyRoute.tsx`.
**Bukti backend:** `require_admin` → `403 FORBIDDEN`; `require_approved_doctor` → `403 ACCOUNT_PENDING` / `403 ACCOUNT_REJECTED` / `403 FORBIDDEN`.
**Bukti basis data:** RLS pada `analyses` dan `doctor_profiles` per `user_id`; operasi admin memakai service-role tetap berada di balik dekorator backend; approve/reject hanya dari `pending` (`.eq('account_status','pending')`).

---

## F. Matriks Hak Akses (Ringkas per Lapisan)

| Fitur | Penjaga Rute Frontend | Otorisasi Backend | Sumber Data |
|---|---|---|---|
| Fitur klinis | `ProtectedRoute` (`approved`) | `require_approved_doctor` | `analyses`, Storage |
| Profil dokter | `DoctorRoute` (dokter `approved`) | service memakai `user_id` pengguna | `doctor_profiles` |
| Fitur admin | `AdminRoute` (`role === 'admin'`) | `require_admin` (`app_metadata.role`) | `doctor_profiles` (service-role) |
| Halaman publik | `PublicOnlyRoute` | — | Supabase Auth |

Catatan: penjaga frontend mencegah ketidaknyamanan UI; **otorisasi sesungguhnya ada di backend dan RLS**, sehingga menyembunyikan menu tidak menjadi satu-satunya pertahanan.

---

## G. Matriks Audit *Use Case*

| No. | Use Case | Status | Bukti Implementasi | Catatan Audit |
|---|---|---|---|---|
| 1 | Sign Up | ✅ Terimplementasi | `Register.tsx` → `registerUser` (baris 131) → `supabase.auth.signUp` + trigger 008 → `pending` | Khusus calon dokter; tidak ada jalur sign-up publik Admin |
| 2 | Sign In | ✅ Terimplementasi | `Login.tsx` → `AuthContext.signIn` (baris 132) → `loginUser` (baris 195) | Satu halaman login untuk semua peran; peran: `app_metadata` dulu |
| 3 | Sign Out | ✅ Terimplementasi | `AppShell.tsx` baris 123 + modal baris 384 → `signOut` (baris 206) | Dilakukan keduanya setelah terautentikasi |
| 4 | Reset Password | ✅ Terimplementasi | `Login.tsx` mode `reset` (baris 174, `resetPasswordUser` baris 156) + `/reset-password` (`updateUser` baris 76) | Opsional; relasi `<<extend>>` Sign In |
| 5 | Upload Image | ✅ Terimplementasi | `NewAnalysis.tsx` (`MAX_FILE_SIZE` 10 MB, MIME JPG/PNG) → `createAnalysis` (baris 185) → `POST /api/analysis` | Dapat berjalan sebagai unggahan yang memicu analisis; tidak mandiri dari kebutuhan citra |
| 6 | Segmentation | ✅ Terimplementasi | `analysis_controller.create_analysis` (baris 13; `202`, status `processing`) → pipeline → polling `getAnalysis` | Wajib membutuhkan citra tersimpan ⇒ `<<include>>` Upload Image valid |
| 7 | View History | ✅ Terimplementasi | `History.tsx` → `listHistory` (baris 212) → `GET /api/history` (per `user_id`) | Basis untuk pencarian/filter |
| 8 | Search / Filter History | ✅ Terimplementasi | `History.tsx` baris 118–136 (`useMemo`, query/status/date) | Opsional ⇒ `<<extend>>` View History |
| 9 | View Doctor Profile | ✅ Terimplementasi | `DoctorProfile.tsx` → `fetchDoctorProfile` + statistik dari riwayat | Dilindungi `DoctorRoute` |
| 10 | Edit Doctor Profile | ✅ Terimplementasi | `DoctorProfile.tsx` baris 445 (`saveDoctorProfile`), avatar 350–390 | Opsional ⇒ `<<extend>>` View Doctor Profile |
| 11 | View Admin Dashboard | ✅ Terimplementasi | `AdminDashboard.tsx` baris 55/226 → `GET /api/admin/doctors/stats` (total/pending/approved/rejected) | `AdminRoute` + `require_admin` |
| 12 | View Doctor Registrations | ✅ Terimplementasi | `AdminDashboard.tsx` baris 46/208 → `GET /api/admin/doctors` (+`?status=`) | Menampilkan identitas, status, `rejection_reason` |
| 13 | Approve Doctor Account | ✅ Terimplementasi | `AdminDashboard.tsx` baris 71/249 → `admin_service.approve_doctor` (baris 135; hanya dari `pending`) | Prasyarat status tidak digambar di diagram, dijelaskan narasi |
| 14 | Reject Doctor Account | ✅ Terimplementasi | `AdminDashboard.tsx` baris 80/269 → `admin_service.reject_doctor` (baris 235; hanya dari `pending`, menyimpan alasan) | idem |

**Bukan *use case* aktor (langkah internal):** *Validate Image* (validasi MIME/integritas Pillow pada `analysis_service.py`), *Generate Overlay* dan *Generate Grad-CAM* (fase pipeline `artifact_composition` dan `gradcam`) — ketiganya tidak dapat diinisiasi pengguna secara independen, sehingga tidak dipetakan sebagai *use case*.

---

## H. Audit Relasi UML

### H.1 Association

| Aktor | Use Case Terhubung | Status |
|---|---|---|
| Calon Pengguna | Sign Up, Sign In | ✅ Sesuai (hanya layanan publik) |
| Dokter | Sign In, Sign Out, Upload Image, Segmentation, View History, View Doctor Profile | ✅ Sesuai hak akses dokter approved |
| Admin | Sign In, Sign Out, View Admin Dashboard, View Doctor Registrations, Approve Doctor Account, Reject Doctor Account | ✅ Sesuai `require_admin` |

- *Extending use case* (Reset Password, Search / Filter History, Edit Doctor Profile) tidak memiliki asosiasi langsung ke aktor; aktor mencapainya melalui *base use case* — sesuai kaidah UML.
- Tidak ada asosiasi yang memberi kesan akses tidak tersedia (misal tidak ada Dokter → Admin Dashboard, tidak ada Admin → Upload Image).

### H.2 `<<include>>`

| Relasi | Analisis | Keputusan |
|---|---|---|
| Segmentation → Upload Image | `POST /api/analysis` menolak permintaan tanpa berkas (`MISSING_FILE`, baris 23); pipeline selalu membutuhkan citra asli tersimpan. Riwayat lama tidak menggantikan kebutuhan unggahan pada analisis baru. | ✅ Pertahankan `<<include>>` (wajib) |

### H.3 `<<extend>>`

| Relasi | Opsional? | Arah Panah | Keputusan |
|---|---|---|---|
| Reset Password → Sign In | Ya — hanya bila pengguna memilih mode lupa sandi | extending → base | ✅ Valid |
| Search / Filter History → View History | Ya — hanya bila kriteria diisi | extending → base | ✅ Valid |
| Edit Doctor Profile → View Doctor Profile | Ya — hanya bila modal edit dibuka | extending → base | ✅ Valid |

### H.4 Generalisasi

Tidak ada generalisasi aktor. Admin dan Dokter memiliki kesamaan *Sign In / Sign Out*, namun hierarki `Admin → Dokter` akan menyiratkan pewarisan fitur klinis yang **tidak ada** pada implementasi (AdminRoute dan DoctorRoute saling eksklusif). Alternatif aktor induk "Pengguna Terautentikasi" dinilai tidak menambah kejelasan pada diagram dengan 14 *use case*, sehingga tidak diterapkan.

### H.5 System Boundary

Satu boundary berlabel **Sistem PIXEL-T** mencakup seluruh *use case*; seluruh aktor berada di luar. Komponen internal (AuthContext, controller, model AI, tabel) tidak digambarkan sebagai aktor.

---

## I. Audit Kualitas Kode

### I.1 Frontend

- Penjaga rute jelas dan terpusat (`components/auth/*`); tidak ditemukan rute klinis/admin tanpa penjaga.
- Validasi unggahan terdapat satu lokasi (`NewAnalysis.tsx: validateFile`) tanpa duplikasi berarti.
- Service layer bertanggung jawab jelas: `auth.ts`, `analysis.ts`, `profile.ts`.
- Kondisi peran terkonsolidasi dalam `AuthContext` sehingga halaman tidak menghitung peran sendiri.

### I.2 Backend

- Pemisahan route → controller → service → repository konsisten dan mudah diikuti.
- Validasi request dilakukan (konten berkas, `MISSING_FILE`, UUID path param divalidasi `_is_valid_uuid`).
- Otorisasi selalu di backend, bukan hanya frontend.
- Transisi status ketat (`pending` saja) dan diverifikasi ulang setelah UPDATE (baris 225–229, 318–322).
- Penangkapan error memakai `APIError` dengan kode kontrak (`FORBIDDEN`, `ACCOUNT_PENDING`, `MISSING_FILE`, `QUEUE_FULL`).

### I.3 Basis Data

- Query memfilter `user_id`; repository `analyses` membatasi `ALLOWED_STATUSES` dan `ALLOWED_SEGMENTATION_STATUSES`.
- Trigger 008 idempoten (hanya membuat profil bila belum ada) dan mengecualikan akun admin.
- RLS konsisten dengan hak akses; operasi admin memakai service-role namun tetap dibatasi dekorator.

### I.4 Pipeline AI

- Status lifecycle `processing → completed | failed` konsisten antara repository dan frontend (`AnalysisStatus`).
- Frontend menunggu dengan polling dan menangani `failed` (tidak menyatakan selesai hanya karena request diterima).
- Job berjalan latar belakang sehingga endpoint `POST /api/analysis` cepat membalas 202.

### I.5 Temuan Kualitas Kode

| No. | File/Komponen | Masalah | Bukti | Dampak | Rekomendasi | Prioritas |
|---|---|---|---|---|---|---|
| 1 | `AdminDashboard.tsx` vs `services/analysis.ts` | Dua nama variabel basis URL berbeda: `VITE_API_URL` (baris 44) vs `VITE_API_BASE_URL` (baris 3) | grep terhadap kedua berkas | Bila hanya satu variabel diatur `.env`, satu kelompok endpoint gagal | Seragamkan nama variabel **di lingkup perubahan terpisah** (dampak deployment), cukup satu nama env var | Medium |
| 2 | `AppRoutes.tsx` rute `/reset-password` | Rute publik tanpa `PublicOnlyRoute` (berbeda dari narasi `AUDIT_DAMPAK_ROLE_ADMIN_DOKTER_PIXELT.md`) | baris 42–45 vs catatan dokumen audit lama | Dokumentasi keamanan rute tidak akurat; halaman tetap aman karena sesi recovery wajib | Rekonsiliasi dokumentasi; opsional bungkus `PublicOnlyRoute` bila dianggap perlu | Medium (dokumentasi) |
| 3 | `AppShell.tsx` navigasi seluler | Menu seluler masih merender tautan klinis untuk admin (desktop disembunyikan) | pemeriksaan navigasi | Cacat kosmetik; penjaga rute tetap memblokir | Perbaikan tampilan opsional | Low |

**Tidak ada perubahan kode yang dilakukan** pada audit ini: tidak ditemukan bug alur Use Case yang dapat diperbaiki dengan perubahan kecil tanpa risiko regresi, dan ketiga temuan di atas bersifat konsolidasi/dokumentasi yang menyentuh konfigurasi deployment atau UI di luar lingkup validasi diagram.

---

## J. Hasil Pengujian

| Jenis Pengujian | Perangkat | Lingkup | Hasil |
|---|---|---|---|
| Static code analysis | Pembacaan berkas | Seluruh modul terkait Bagian C–I | ✅ Selesai (dasar seluruh klaim audit) |
| Unit test backend | `pytest` (Python 3.11 venv) | `tests/backend` (auth, admin, analysis, history, repository, storage, konfigurasi) | ✅ **110 passed** (2.28 s) |
| Unit test frontend | `Vitest` | `frontend/src` — 18 berkas test | ✅ **285 passed** (≈26 s) |
| Unit test AI | tersedia (`tests/ai`) | tidak dijalankan pada sesi ini | ⚠️ Tidak dijalankan |
| TypeScript build | `tsc -b` via `npm run build` | — | ⚠️ Tidak dijalankan |
| Integration test | — | Tidak tersedia terpisah dari unit test | ⚠️ Tidak dilakukan |
| Browser / end-to-end test | — | Lingkungan Supabase/kredensial tidak disediakan | ❌ Tidak dilakukan |
| Pengujian beban / penetrasi | — | — | ❌ Tidak dilakukan |

Pernyataan kejujuran: pengujian yang dilakukan hanyalah **unit test otomatis lokal** dan **analisis kode statis**. Tidak ada klaim pengujian alur Sign Up/Sign In/Approve melalui browser, tidak ada penggunaan akun produksi, dan tidak ada data produksi yang diubah atau dihapus.

---

## K. Temuan dan Perbaikan

| No. | Temuan | Bukti | Dampak | Tindakan pada Audit Ini | Prioritas |
|---|---|---|---|---|---|
| K-1 | `USE_CASE_DIAGRAM_PIXELT_ROLE_ADMIN_REVISED.drawio`: 4 *use case* admin tanpa asosiasi aktor | perbandingan edge & vertex drawio | Diagram tidak sah UML; alur admin kehilangan pelaku | Diperbaiki: asosiasi `e12`–`e15` pada diagram final audited | Critical (dokumen) |
| K-2 | *use case* dokter (Upload, Segmentation, View History, View Profile) juga tanpa asosiasi pada diagram lama | idem | Alur klinis utama kehilangan pelaku | Diperbaiki: asosiasi `e6`–`e9` | Critical (dokumen) |
| K-3 | `LAPORAN_AUDIT_USE_CASE_PIXELT.md` menyatakan "tanpa RBAC" — kedaluwarsa setelah migrasi 007/008 | dokumen lama vs kode aktif | Klaim audit lama menyesatkan | Dokumen ini menggantikan; matriks hak akses Bagian E | High |
| K-4 | Narasi `/reset-password` pada `AUDIT_DAMPAK_ROLE_ADMIN_DOKTER_PIXELT.md` tidak akurat (rute tanpa penjaga) | `AppRoutes.tsx` 42–45 | Dokumentasi keamanan keliru | Direkonsiliasi Bagian I.5-2 | Medium |
| K-5 | Dua variabel basis URL API berbeda | `VITE_API_URL` vs `VITE_API_BASE_URL` | Risiko salah satu endpoint tidak terjangkau bila konfigurasi parsial | Direkomendasikan penyeragaman; tidak diubah agar tidak menyentuh deployment | Medium |
| K-6 | Penamaan label campur bahasa pada diagram lama | label Inggris/Indonesia | Estetika akademik | Diagram final audited menyeragamkan label Inggris | Low |
| K-7 | Artefak AI berpotensi disalahartikan sebagai *use case* | diagram audit lama | Diagram terlalu ramai, prinsip *use case* aktor dilanggar | Dikeluarkan dari level aktor, didokumentasikan sebagai langkah internal | Low |

**Perubahan berkas:** hanya penambahan file baru di `references/bab 4/` (`USE_CASE_DIAGRAM_PIXELT_FINAL_AUDITED.drawio`, `USE_CASE_DIAGRAM_PIXELT_FINAL_AUDITED.png`, `PENJELASAN_USE_CASE_DIAGRAM_PIXELT_FINAL_AUDITED.md`, laporan ini). **Tidak ada kode aplikasi, migrasi, konfigurasi, maupun file diagram lama yang diubah.**

---

## L. Rekomendasi Diagram

1. Gunakan **`USE_CASE_DIAGRAM_PIXELT_FINAL_AUDITED.drawio` / `.png`** sebagai *Use Case Diagram* Bab IV: 3 aktor, 14 *use case*, 14 asosiasi, 1 `<<include>>`, 3 `<<extend>>`.
2. Pertahankan tiga aktor (Calon Pengguna, Dokter, Admin); **jangan** menambahkan generalisasi Admin → Dokter.
3. Pertahankan Sign In dan Sign Out sebagai *use case* bersama; Sign In juga terhubung ke Calon Pengguna.
4. Jangan memodelkan artefak pipeline AI sebagai *use case* aktor.
5. Sertakan prasyarat status (approve/reject hanya dari `pending`) pada narasi/tabel spesifikasi, bukan pada diagram.
6. Jika pembimbing mensyaratkan bahasa Indonesia penuh, gunakan padanan terjemah label tanpa mengubah struktur.
7. Dokumen lama yang bertentangan (`LAPORAN_AUDIT_USE_CASE_PIXELT.md`, catatan `/reset-password` pada `AUDIT_DAMPAK_ROLE_ADMIN_DOKTER_PIXELT.md`) ditandai **digantikan** oleh laporan ini.

---

## M. Penjelasan Akademik

Naskah narasi *Use Case Diagram* untuk Bab IV tersedia lengkap dalam berkas `PENJELASAN_USE_CASE_DIAGRAM_PIXELT_FINAL_AUDITED.md` (bahasa Indonesia formal, penomoran sementara `Gambar 4.x` dan `Tabel 4.x`). Ringkasan isi:

- **Aktор:** Calon Pengguna (Sign Up, Sign In), Dokter (fitur klinis + profil + Sign In/Out), Admin (dashboard, daftar pendaftaran, approve/reject + Sign In/Out).
- **Use case:** 14 *use case*, seluruhnya terlacak ke berkas sumber (Bagian G).
- **Relasi:** satu `<<include>>` untuk perilaku wajib, tiga `<<extend>>` untuk perilaku opsional, tanpa generalisasi aktor.
- **Batas sistem:** satu boundary "Sistem PIXEL-T" yang mencakup frontend React, backend Flask, dan pipeline AI sebagai satu kesatuan.

---

## N. Keterbatasan Audit

1. **Objek audit bernama pada instruksi tidak tersedia.** Berkas `references\bab 4\use_case_diagram_revisi_audit.png` **tidak ditemukan** di proyek. Audit dilakukan terhadap artefak yang benar-benar ada: `use_case_diagram_revisi.png` (baseline raster), `SPESIFIKASI_REVISI_USE_CASE_DIAGRAM_PIXELT.md` (baseline PlantUML), dan `USE_CASE_DIAGRAM_PIXELT_ROLE_ADMIN_REVISED.drawio/.png` (revisi sebelumnya yang memiliki cacat asosiasi).
2. **Audit berbasis pembacaan kode dan unit test, bukan pengujian runtime aplikasi penuh.** Tidak ada pengujian browser, tidak ada pengujian terhadap instance Supabase nyata.
3. **Validasi visual diagram terbatas:** XML diperiksa *well-formed* dengan `xml.etree.ElementTree` (18 vertex, 18 edge, seluruh `source`/`target` valid), PNG diverifikasi dengan `PIL.Image.verify()` (2400×1960). Tidak ada render melalui mesin UML resmi (draw.io Desktop/PlantUML tidak tersedia di lingkungan audit).
4. **Tidak ada akses ke Supabase produksi.** Keadaan `app_metadata` admin dan data `doctor_profiles` disimpulkan dari migrasi dan kode, bukan dari data runtime.
5. **Konfigurasi `.env` tidak dibaca.** Dampak temuan `VITE_API_URL` vs `VITE_API_BASE_URL` tidak diverifikasi pada runtime.
6. **Kredensial tidak diungkap** dalam bentuk apa pun.
7. **Test AI (`tests/ai`) dan build TypeScript tidak dijalankan** pada sesi ini.
8. **Keamanan menyeluruh tidak dapat diklaim.** Audit ini mencakup scope otorisasi dan diagram, bukan pengujian keamanan menyeluruh.

---

## O. Status Akhir

**Status: TERVALIDASI DENGAN REVISI.**

| Kriteria | Hasil |
|---|---|
| Seluruh aktor memiliki dasar implementasi | ✅ 3/3 |
| Seluruh use case memiliki dasar implementasi | ✅ 14/14 |
| Seluruh asosiasi aktor–use case lengkap dan sesuai hak akses | ✅ 14/14 |
| `<<include>>` valid | ✅ 1/1 |
| `<<extend>>` valid dengan arah benar | ✅ 3/3 |
| Pemisahan hak akses Admin/Dokter pada tiga lapisan | ✅ Terverifikasi |
| Use case fiktif | ✅ Tidak ada |
| Generalisasi menyesatkan | ✅ Tidak ada |
| Unit test backend | ✅ 110 lulus |
| Unit test frontend | ✅ 285 lulus |
| Validasi visual mesin UML resmi | ⚠️ Terbatas (Bagian N-3) |
| Pengujian browser/end-to-end | ⚠️ Tidak dilakukan (Bagian J) |
| File diagram & kode asli tidak diubah | ✅ Terverifikasi |

**Keputusan:** `USE_CASE_DIAGRAM_PIXELT_FINAL_AUDITED.drawio` / `.png` **layak digunakan** sebagai *Use Case Diagram* Bab IV, disertai naskah `PENJELASAN_USE_CASE_DIAGRAM_PIXELT_FINAL_AUDITED.md`. Status tidak dinaikkan menjadi `TERVALIDASI` penuh karena pengujian runtime terhadap instance aplikasi dan validasi visual mesin UML belum dilakukan sebagaimana dinyatakan pada Bagian N.

---

*Laporan disusun melalui analisis statis terhadap kode sumber aktual web PIXEL-T dan pengujian unit lokal (pytest, Vitest). Seluruh temuan dapat dilacak ke berkas pada Bagian B. Tidak ada kode aplikasi, migrasi, konfigurasi, kredensial, atau file referensi asli yang diubah.*
