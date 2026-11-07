# AUDIT DAMPAK PERAN ADMIN DOKTER — SISTEM PIXEL-T

**Dokumen Pendukung Bab IV Skripsi S1**
Disusun berdasarkan analisis implementasi aktual kode sumber web PIXEL-T.
Status akhir: **SELESAI DENGAN VALIDASI SEBAGIAN** (diagram dan laporan selesai; validasi melalui rendering Draw.io/PNG tanpa engine UML bawaan).

---

## 1. Ringkasan Eksekutif

Audit ini dilakukan untuk memvalidasi kesesuaian antara dokumentasi diagram PIXEL-T (ERD, Use Case, Activity, Sequence) dengan implementasi aktual sistem terkait dukungan peran **Admin** dan **Dokter**, serta untuk menghasilkan berkas revisi diagram beruffix `_ROLE_ADMIN_REVISED` dan laporan dampak lengkap.

### Kesimpulan utama

1. **Admin** tidak memiliki tabel tersendiri dan tidak memiliki baris di `doctor_profiles`. Admin direpresentasikan secara eksklusif melalui `auth.users.raw_app_meta_data.role = 'admin'`, yang hanya dapat ditulis melalui Supabase Admin API dengan service-role key (`set_admin_role.py`).
2. **Dokter** direpresentasikan via baris di `public.doctor_profiles` (`user_id` UNIQUE merujuk ke `auth.users.id`) dengan kolom `role` (default `'doctor'`) dan `account_status` (default `'pending'`, nilai `pending|approved|rejected`).
3. Frontend menggunakan empat *route guard* berbeda: `PublicOnlyRoute` (`/login`, `/register`), `AdminRoute` (`/admin`, role `== 'admin'`), `ProtectedRoute` (`/dashboard`, `/analysis/*`, `/history/*`, status `approved`), dan `DoctorRoute` (`/profile`, dokter yang disetujui).
4. Enforcement backend melalui dekorator `@require_admin` (baca `app_metadata.role`) dan `@require_approved_doctor` (baca `doctor_profiles.role` + `account_status` via `_get_user_role_and_status`).
5. Enam diagram terdampak direvisi dan disimpan sebagai berkas `_ROLE_ADMIN_REVISED` (PNG + Draw.io): ERD, Use Case, Activity Sign Up, Activity Sign In, Sequence Sign Up, Sequence Sign In.
6. Semua enam berkas Draw.io divisikan sebagai XML well-formed tanpa referensi edge yang rusak; semua enam PNG diverifikasi dapat dibuka PIL.

### Perbedaan dengan revisi sebelumnya (`*_FINAL_REVISED`)

Berkas `*_FINAL_REVISED` sebelumnya tertimpa konten placeholder oleh skrip pengujian dan tidak memenuhi standar UML (multiplicity numerik tidak lengkap, peran Admin tidak terwakili dengan benar). Berkas `_ROLE_ADMIN_REVISED` saat ini menggantikan mereka dan menjadi artefak revisi yang sah.

---

## 2. Informasi Sistem

| Aspek | Keterangan |
|-------|------------|
| **Nama Sistem** | PIXEL-T (*Polyp Identification with eXplainable Intelligence for Early-stage Local Tissue detection*) |
| **Tipe Aplikasi** | Aplikasi web *full-stack* untuk segmentasi citra medis berbasis AI |
| **Frontend** | React 18 + TypeScript + Vite + TailwindCSS |
| **Backend** | Python + Flask |
| **Autentikasi** | Supabase Auth (JWT) |
| **Basis Data** | Supabase PostgreSQL (tabel `auth.users` bawaan Supabase + tabel publik `doctor_profiles`, `analyses`) |
| **Penyimpanan Berkas** | Supabase Storage |
| **Model AI** | U-Net (segmentasi) + ResNet50 + Grad-CAM |
| **Pengelolaan Rute** | React Router v6 + `ProtectedRoute.tsx`, `AdminRoute.tsx`, `DoctorRoute.tsx`, `PublicOnlyRoute.tsx` |
| **Diagram yang Divalidasi** | ERD, Use Case, Activity Sign Up, Activity Sign In, Sequence Sign Up, Sequence Sign In |

---

## 3. Arsitektur & Model Peran (Admin vs Dokter)

### 3.1 Model peran

| Aspek | Admin | Dokter |
|-------|-------|--------|
| **Sumber identitas** | `auth.users.raw_app_meta_data.role = 'admin'` | `public.doctor_profiles.user_id` → `auth.users.id` |
| **Cara pembuatan** | Eksternal: Supabase Admin API (`set_admin_role.py`), service-role key | Publik: `Register.tsx` → `supabase.auth.signUp()` |
| **Tabel khusus** | Tidak ada tabel `admins` | `public.doctor_profiles` (unik per `user_id`) |
| **Baris profil** | Tidak memiliki baris `doctor_profiles` | Setiap dokter memiliki baris (0..1 ke `auth.users`) |
| **Status akun** | Tidak berlaku (`account_status = NULL`) | `pending` \| `approved` \| `rejected` |
| **Tulis *role*** | Server-write-only (service role), tidak dapat diubah klien | Server-write-only via trigger, default `'doctor'` |
| **Guard backend** | `@require_admin` (`auth.py` L87) | `@require_approved_doctor` (`auth.py` L176) |
| **Guard frontend** | `AdminRoute` (`/admin`) | `ProtectedRoute` / `DoctorRoute` |

### 3.2 Bukti implementasi kunci

**Pembuatan Admin (eksternal, bukan Sign Up publik):**
- `backend/set_admin_role.py` L40–L66: memanggil `supabase.auth.admin.get_user_by_id()` lalu `supabase.auth.admin.update_user_by_id()` dengan `app_metadata.role = 'admin'`; mempertahankan `app_metadata` yang ada.
- `backend/set_admin_role.py` L77–L96: memverifikasi `actual_role == 'admin'` setelah pembaruan.
- `frontend/src/pages/auth/Register.tsx` dan `Login.tsx`: tidak ada pemilihan peran admin pada pendaftaran publik; pendaftaran publik hanya untuk dokter.

**Enforcement Admin di backend:**
- `backend/app/core/auth.py` L87–L173: `require_admin` membaca `user.app_metadata.get('role')` dan menolak dengan HTTP 403 jika bukan `'admin'`. Komentar eksplisit: *app_metadata server-write-only, tidak dapat dimodifikasi klien melalui `updateUser`*.
- `backend/app/routes/admin.py` L9–L39: semua endpoint admin (`GET /api/admin/doctors`, `/api/admin/doctors/stats`, `/api/admin/doctors/<id>`, `POST .../approve`, `POST .../reject`) dilindungi `@require_admin`.

**Enforcement Dokter di backend:**
- `backend/app/core/auth.py` L176–L275: `require_approved_doctor` memanggil `_get_user_role_and_status(user_id)`; menolak admin (tidak memiliki baris profil) dan menolak status `pending` / `rejected`.
- `backend/app/core/auth.py` L278–L299: `_get_user_role_and_status` membaca `doctor_profiles.role` + `account_status` via service-role client.

**Provisi profil dokter saat Sign Up:**
- `database/migrations/007_add_role_and_account_status.sql`: menambahkan `role` (default `'doctor'`) dan `account_status` (default `'pending'`) pada `doctor_profiles`; admin disimpan di `auth.users.raw_app_meta_data.role = 'admin'`, dibuat secara manual, tidak ada jalur pendaftaran publik.
- `database/migrations/008_create_doctor_profile_trigger.sql` L28–L54: trigger `handle_new_doctor_signup()` pada `auth.users`; hanya beraksi jika `raw_user_meta_data ? 'full_name'` **dan** `raw_app_meta_data->>'role' <> 'admin'`; menyisipkan `doctor_profiles` dengan `role = 'doctor'`, `account_status = 'pending'`; idempotent, `SECURITY DEFINER`.
- `database/migrations/008_create_doctor_profile_trigger.sql` L83–L103: backfill untuk akun dokter lama yang belum punya baris profil; admin tetap dikecualikan.

**Resolusi peran di frontend:**
- `frontend/src/context/AuthContext.tsx` L73–L152: saat pemulihan sesi dan perubahan status auth, peran diselesaikan dengan prioritas `app_metadata.role` terlebih dahulu (admin), kemudian `doctor_profiles` (dokter); `role` dan `accountStatus` diekspos melalui konteks.
- `frontend/src/services/auth.ts` L127–L146 (`registerUser`) dan L195–L239 (`loginUser`): hanya memanggil Supabase Auth; tidak ada pemanggilan endpoint Flask pada alur Sign Up / Sign In.
- `frontend/src/services/auth.ts` L297–L338: `fetchUserProfileStatus` dan `getAdminRoleFromAppMetadata`.

---

## 4. Matriks Akses

### 4.1 Rute Frontend

| Rute | Guard | Kondisi Akses | Redirect jika gagal |
|------|-------|---------------|---------------------|
| `/` | — | — | `/login` |
| `/login` | `PublicOnlyRoute` | Publik; jika terautentikasi → arahkan sesuai role | — |
| `/register` | `PublicOnlyRoute` | Publik (hanya pendaftaran dokter) | — |
| `/reset-password` | `PublicOnlyRoute` | Publik | — |
| `/dashboard` | `ProtectedRoute` | Autentikasi + `account_status == 'approved'` | `/login` (pending/rejected) |
| `/analysis/new` | `ProtectedRoute` | Sama di atas | `/login` |
| `/analysis/:id` | `ProtectedRoute` | Sama di atas | `/login` |
| `/history` | `ProtectedRoute` | Sama di atas | `/login` |
| `/history/:id` | `ProtectedRoute` | Sama di atas | `/login` |
| `/profile` | `DoctorRoute` | Autentikasi + dokter + `approved` | Admin → `/dashboard`; pending/rejected → `/login` |
| `/admin` | `AdminRoute` | `role == 'admin'` | Dokter → `/login` |

### 4.2 Endpoint Backend

| Endpoint | Metode | Dekorator | Sumber otorisasi |
|----------|--------|-----------|------------------|
| `GET /api/admin/doctors` | GET | `@require_admin` | `app_metadata.role == 'admin'` |
| `GET /api/admin/doctors/stats` | GET | `@require_admin` | `app_metadata.role == 'admin'` |
| `GET /api/admin/doctors/<id>` | GET | `@require_admin` | `app_metadata.role == 'admin'` |
| `POST /api/admin/doctors/<id>/approve` | POST | `@require_admin` | `app_metadata.role == 'admin'` |
| `POST /api/admin/doctors/<id>/reject` | POST | `@require_admin` | `app_metadata.role == 'admin'` |
| `POST /api/analysis` | POST | `@require_approved_doctor` | `doctor_profiles.role + account_status == 'approved'` |
| `GET /api/analysis/...` | GET | `@require_approved_doctor` | Sama di atas |
| `DELETE /api/analysis/...` | DELETE | `@require_approved_doctor` | Sama di atas |

### 4.3 Tabel Basis Data

| Tabel | Pemilik | Catatan terkait peran |
|-------|---------|-----------------------|
| `auth.users` (bawaan Supabase) | Supabase Auth | `raw_app_meta_data.role` = `'admin'` untuk admin; tidak ada baris untuk dokter di sini terkait profesi |
| `public.doctor_profiles` | Publik (RLS) | `user_id` UNIQUE → `auth.users.id`; `role = 'doctor'`; `account_status` default `'pending'` |
| `public.analyses` | Publik (RLS) | `user_id` → `auth.users.id`; hanya dokter yang dapat membuat analisis |

---

## 5. Matriks Dampak terhadap Diagram

Enam diagram terdampak oleh tambahan peran Admin. Setiap diagram direvisi tanpa merancang ulang (minimalis, monokrom, standar UML), dan disimpan dengan suffik `_ROLE_ADMIN_REVISED`.

| Diagram | Dampak | Revisi yang Dilakukan | Status |
|---------|--------|-----------------------|--------|
| **ERD** | Admin tidak ada tabel sendiri; relasi `doctor_profiles` (0..1) → `auth.users` (1); `analyses` (*) → `auth.users` (1) | Tambah catatan: admin tanpa tabel `admins` dan tanpa baris `doctor_profiles`; `admin = raw_app_meta_data.role = 'admin'` (server-write-only); multiplicity numerik `1`, `*`, `0..1` | Revisi selesai (`_ROLE_ADMIN_REVISED`) |
| **Use Case** | Tambah aktor Admin dengan 4 use case eksklusif | Tambah aktor "Admin"; use case `Dashboard Admin`, `Daftar Dokter`, `Setujui Akun Dokter`, `Tolak Akun Dokter`; relasi asosiasi Admin ke use case publik (Sign In / Sign Out) | Revisi selesai (`_ROLE_ADMIN_REVISED`) |
| **Activity Sign Up** | Pendaftaran publik hanya untuk dokter; admin tidak mendaftar | Catatan: pendaftaran publik hanya Dokter; admin dibuat via Supabase Admin API (`app_metadata.role='admin'`) dan tidak punya baris `doctor_profiles`; trigger `handle_new_doctor_signup` menambahkan baris `doctor_profiles` (role=`doctor`, status=`pending`) | Revisi selesai (`_ROLE_ADMIN_REVISED`) |
| **Activity Sign In** | Resolusi peran: admin via `app_metadata`, dokter via `doctor_profiles` | Cabang `role = 'admin'?` → `/admin`; cabang dokter → baca `doctor_profiles` → cek `account_status` (approved → `/dashboard`; pending/rejected → `/login`) | Revisi selesai (`_ROLE_ADMIN_REVISED`) |
| **Sequence Sign Up** | Admin tidak terlibat alur publik | Catatan: tidak ada pemanggilan Flask API pada Sign Up; akun admin tidak dibuat di alur ini; trigger DB membuat `doctor_profiles` | Revisi selesai (`_ROLE_ADMIN_REVISED`) |
| **Sequence Sign In** | Resolusi peran setelah autentikasi | Fragment `[alt] app_metadata.role = 'admin'` → set role admin; `[else]` → `fetchUserProfileStatus` dari `doctor_profiles`; validasi kecocokan `selectedRole`; navigasi via Route Guard ke `/admin`, `/dashboard`, atau `/login` | Revisi selesai (`_ROLE_ADMIN_REVISED`) |

---

## 6. Audit Kode Sumber

Berkas yang diperiksa sebagai bukti implementasi:

| Berkas | Fungsi dalam audit |
|--------|-------------------|
| `backend/app/core/auth.py` | `require_admin` (L87), `require_approved_doctor` (L176), `_get_user_role_and_status` (L278) |
| `backend/app/routes/admin.py` | 5 endpoint admin, semuanya `@require_admin` (L9–L39) |
| `backend/app/controllers/admin_controller.py` | `list_doctors`, `get_doctor` (L12–L98) |
| `backend/app/services/admin_service.py` | `list_doctors` (L42), `approve_doctor` (L135), `reject_doctor` (L235), `get_statistics` (L328) |
| `backend/set_admin_role.py` | Pembuatan admin via Supabase Admin API `app_metadata.role='admin'` (L40–L96) |
| `database/migrations/007_add_role_and_account_status.sql` | Kolom `role` + `account_status` di `doctor_profiles`; admin di `raw_app_meta_data` |
| `database/migrations/008_create_doctor_profile_trigger.sql` | Trigger signup; admin dikecualikan; `role='doctor'`, `account_status='pending'` |
| `database/verify_doctor_registration.sql` | Query verifikasi (baca-saja) trigger dan profil dokter |
| `frontend/src/context/AuthContext.tsx` | Resolusi `role`/`accountStatus` (L73–L152), `signUp`/`signIn` |
| `frontend/src/services/auth.ts` | `registerUser` (L131), `loginUser` (L195), `fetchUserProfileStatus` (L297), `getAdminRoleFromAppMetadata` (L328) |
| `frontend/src/routes/AppRoutes.tsx` | Definisi rute + guard (L19–L113) |
| `frontend/src/components/auth/AdminRoute.tsx` | Guard `/admin`, `role !== 'admin'` → tolak (L18–L39) |
| `frontend/src/components/auth/ProtectedRoute.tsx` | Guard klinis, cek `account_status` pending/rejected (L18–L41) |
| `frontend/src/components/auth/DoctorRoute.tsx` | Guard `/profile`, blokir admin (L21–L49) |
| `frontend/src/components/auth/PublicOnlyRoute.tsx` | Guard `/login`, `/register`, arahkan sesuai role (L19–L41) |
| `frontend/src/pages/auth/Login.tsx` | Halaman Sign In; tidak ada peran admin pada formulir |
| `frontend/src/pages/auth/Register.tsx` | Halaman Sign Up publik (hanya dokter) |

**Tidak ada perubahan pada kode sumber aplikasi, basis data, migrasi, konfigurasi, atau berkas referensi gambar sebagai bagian dari tugas ini.** Hanya dokumentasi diagram dan laporan audit yang ditulis/diperbarui.

---

## 7. Audit per Diagram

### 7.1 ERD

| Elemen Diagram | Status | Bukti Implementasi |
|----------------|--------|-------------------|
| `auth.users (auth.users)` | ✅ Valid | Tabel auth bawaan Supabase; `raw_app_meta_data.role` untuk admin |
| `doctor_profiles` | ✅ Valid | `migrations/004_create_doctor_profiles.sql`, `007_add_role_and_account_status.sql` |
| `analyses` | ✅ Valid | `migrations/001_create_analyses_and_storage.sql` |
| Relasi `doctor_profiles` (0..1) → `auth.users` (1) | ✅ Valid | `user_id` UNIQUE FK ke `auth.users(id)` |
| Relasi `analyses` (*) → `auth.users` (1) | ✅ Valid | `user_id` NOT NULL FK ke `auth.users(id)` |
| Admin tanpa tabel `admins` | ✅ Valid | Tidak ada tabel `admins` di kode basis data |
| Admin tanpa baris `doctor_profiles` | ✅ Valid | Admin dilewati oleh trigger (`008` L37–L38) |

**Catatan:** Multiplicity numerik (`1`, `*`, `0..1`) dipasang di ujung asosiasi yang tepat; tidak ada label kata.

### 7.2 Use Case

| Use Case / Relasi | Status | Bukti |
|-------------------|--------|-------|
| Aktor Dokter | ✅ Valid | `ProtectedRoute` + `DoctorRoute` |
| Aktor Calon Pengguna | ✅ Valid | `/register`, `/login` publik |
| Aktor Admin | ✅ Valid | `AdminRoute` (`/admin`) |
| Sign Up | ✅ Valid | `Register.tsx` → `supabase.auth.signUp` (hanya dokter) |
| Sign In | ✅ Valid | `Login.tsx` → `supabase.auth.signInWithPassword` |
| Sign Out | ✅ Valid | `supabase.auth.signOut` |
| Reset Password | ✅ Valid | `Login.tsx` mode reset / `ResetPassword.tsx` |
| Upload Image | ✅ Valid | `POST /api/analysis` (`@require_approved_doctor`) |
| Segmentation | ✅ Valid | `analysis_service.py` + `pipeline.py` |
| View History / Search History | ✅ Valid | `History.tsx` |
| View / Edit Doctor Profile | ✅ Valid | `DoctorProfile.tsx` |
| Dashboard Admin / Daftar Dokter / Setujui / Tolak | ✅ Valid | `backend/app/routes/admin.py` + `@require_admin` |
| `<<include>>` Segmentation → Upload Image | ✅ Valid | Citra harus diunggah sebelum diproses |
| `<<extend>>` Search → View History; Edit → View Profile | ✅ Valid | Opsional di klien |

### 7.3 Activity Sign Up & Sign In

Activity Sign Up mencerminkan `Register.tsx` → `services/auth.ts` (`registerUser` → `supabase.auth.signUp`) → trigger DB. Activity Sign In mencerminkan `Login.tsx` → `services/auth.ts` (`loginUser` → `supabase.auth.signInWithPassword`) → `AuthContext` resolusi peran → cabang admin/dokter. Kedua diagram diverifikasi sesuai alur aktual dan tidak terdapat pemanggilan endpoint Flask pada alur autentikasi.

### 7.4 Sequence Sign Up & Sign In

Sequence Sign Up: Pengguna → Register Page → AuthContext → AuthService → Supabase Auth → (trigger) DB Trigger `doctor_profiles`. Tidak ada aktor Admin; tidak ada pemanggilan Flask API.
Sequence Sign In: Pengguna → Login Page → AuthContext → AuthService → Supabase Auth → cabang alternatif `app_metadata.role = 'admin'` atau `doctor_profiles` → Route Guard → navigasi ke `/admin`, `/dashboard`, atau `/login`. Cocok dengan `AuthContext.tsx` L148–L152.

---

## 8. Alur Ujung-ke-Ujung (End-to-End)

### 8.1 Pendaftaran Dokter (Sign Up)

1. Pengguna membuka `/register` (`PublicOnlyRoute`).
2. Mengisi formulir (`Register.tsx`): nama lengkap, email, kata sandi, rumah sakit, spesialisasi.
3. Validasi input klien (format email, panjang kata sandi).
4. `AuthContext.signUp()` → `services/auth.ts` `registerUser()` → `supabase.auth.signUp({ email, password, options.data })`.
5. Supabase membuat baris di `auth.users`; `raw_user_meta_data` berisi `full_name`, dll.
6. Trigger `handle_new_doctor_signup()` (migrasi 008) memeriksa `raw_user_meta_data ? 'full_name'` dan `raw_app_meta_data.role <> 'admin'`, lalu menyisipkan `doctor_profiles` dengan `role = 'doctor'`, `account_status = 'pending'`.
7. Jika sesi dikembalikan → disimpan; role `doctor`, status `pending`; tampilkan instruksi konfirmasi email.
8. Pengguna diarahkan ke `/login`; menunggu persetujuan admin.

**Admin tidak terlibat di alur ini.** Admin tidak dapat didaftarkan melalui halaman publik.

### 8.2 Masuk (Sign In)

1. Pengguna membuka `/login` (`PublicOnlyRoute`).
2. Mengisi email, kata sandi, dan memilih jenis akun.
3. `AuthContext.signIn()` → `loginUser()` → `supabase.auth.signInWithPassword`.
4. Supabase mengembalikan `{ user, session }`.
5. `AuthContext` memanggil `getAdminRoleFromAppMetadata(user)`:
   - Jika `app_metadata.role == 'admin'` → `role = 'admin'`, `account_status = null`.
   - Jika tidak → `fetchUserProfileStatus(user)` membaca `doctor_profiles.role` + `account_status`.
6. Validasi kecocokan `selectedRole` dengan role aktual.
7. `Route Guard` menavigasi:
   - Admin → `/admin` (`AdminRoute`).
   - Dokter approved → `/dashboard` (`ProtectedRoute`).
   - Dokter pending/rejected → `/login` (`ProtectedRoute`).

---

## 9. Ketidaksesuaian (Discrepancy) dan Rekomendasi

| # | Ketidaksesuaian | Dampak | Rekomendasi |
|---|----------------|--------|-------------|
| 1 | Beberapa diagram sumber asli hanya tersedia sebagai raster (PNG) tanpa sumber Draw.io/PlantUML asli. | Tidak dapat diverifikasi struktural penuh sebelum rekonstruksi. | Rekonstruksi ditandai sebagai `_ROLE_ADMIN_REVISED`; batas ini dicatat dalam laporan. |
| 2 | Aktor "Admin" sebelumnya tidak terwakili di diagram awal. | Diagram tidak mencerminkan dukungan peran ganda. | Ditambahkan aktor Admin dan 4 use case admin pada revisi. |
| 3 | Multiplicity pada ERD awal menggunakan label kata. | Tidak standar UML. | Diganti dengan angka (`1`, `*`, `0..1`) di ujung asosiasi. |
| 4 | Tidak ada engine UML/PlantUML/Java di lingkungan; validasi Draw.io dilakukan secara parsial (XML well-formed + referensi edge). | Tidak dapat memastikan render visual sempurna di Draw.io desktop. | Semua PNG diverifikasi dapat dibuka; file Draw.io valid XML tanpa edge rusak. |

---

## 10. Regresi & Status

- Tidak ada perubahan pada kode sumber aplikasi, basis data, migrasi, atau konfigurasi.
- Berkas `*_FINAL_REVISED` yang lama diganti oleh `_ROLE_ADMIN_REVISED` (berkas lama tertimpa placeholder oleh skrip sebelumnya; artefak saat ini adalah yang sah).
- Git working tree memiliki 43+ berkas yang dimodifikasi/ditambahkan yang **tidak terkait** dengan tugas diagram ini (inferensi AI, backend routes/controllers, dokumentasi lain) — perubahan tersebut ada sebelum tugas ini dan tidak disentuh.
- Berkas diagram revisi:
  - `ERD_PIXELT_ROLE_ADMIN_REVISED.drawio` + `.png`
  - `USE_CASE_DIAGRAM_PIXELT_ROLE_ADMIN_REVISED.drawio` + `.png`
  - `ACTIVITY_DIAGRAM_SIGN_UP_PIXELT_ROLE_ADMIN_REVISED.drawio` + `.png`
  - `ACTIVITY_DIAGRAM_SIGN_IN_PIXELT_ROLE_ADMIN_REVISED.drawio` + `.png`
  - `SEQUENCE_DIAGRAM_SIGN_UP_PIXELT_ROLE_ADMIN_REVISED.drawio` + `.png`
  - `SEQUENCE_DIAGRAM_SIGN_IN_PIXELT_ROLE_ADMIN_REVISED.drawio` + `.png`

---

## 11. Status Akhir

**SELESAI DENGAN VALIDASI SEBAGIAN**

- ✅ Enam diagram `_ROLE_ADMIN_REVISED` tersedia (PNG + Draw.io).
- ✅ Semua Draw.io valid XML well-formed tanpa referensi edge yang rusak.
- ✅ Semua PNG diverifikasi dapat dibuka (PIL).
- ✅ Laporan audit dampak (`AUDIT_DAMPAK_ROLE_ADMIN_DOKTER_PIXELT.md`) selesai ditulis.
- ⚠️ Validasi visual render Draw.io di aplikasi desktop tidak dilakukan (tidak ada engine UML/PlantUML/Java; validasi terbatas pada struktur XML dan render raster).
- ❌ Tidak ada perubahan pada kode sumber aplikasi (sebagai kebijakan tugas).

Lokasi berkas: `references/bab 4/AUDIT_DAMPAK_ROLE_ADMIN_DOKTER_PIXELT.md`
