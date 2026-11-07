# AUDIT REVISI FINAL DIAGRAM PIXEL-T (AKUN DOKTER DAN ADMIN)

## 1. Ringkasan Eksekutif

1. **Perubahan mekanisme pengguna yang menjadi dasar revisi:** penambahan akun Admin terpisah selain akun Dokter/tenaga medis. Admin diotorisasi melalui `app_metadata.role` pada Supabase Auth (sumber server-write-only), sedangkan Dokter diotorisasi melalui tabel `public.doctor_profiles` (kolom `role` dan `account_status`).

2. **Kondisi awal keenam diagram:** Use Case Diagram, Activity Diagram Sign Up, Activity Diagram Sign In, Sequence Diagram Sign Up, Sequence Diagram Sign In, dan Entity Relationship Diagram (ERD) final.

3. **Masalah utama yang ditemukan pada keenam diagram awal:** seluruh diagram awal hanya menampung satu aktor/pemakai, yaitu Dokter, dan tidak memuat akun Admin, status persetujuan (`pending`/`approved`/`rejected`), pembatasan akses, serta pemisahan otorisasi `app_metadata` dan `doctor_profiles`.

4. **Hasil revisi:** penyesuaian isi diagram agar sesuai implementasi aktual. Desain visual (monokrom, sederhana, minimalis) tidak diubah secara drastis; perubahan dilakukan pada isi dan alur yang benar-benar diperlukan.

5. **Tingkat kesesuaian diagram dengan implementasi:** **SELESAI DENGAN VALIDASI SEBAGIAN** (semua diagram ditinjau terhadap implementasi terbaru; beberapa bagian usulan revisi masih memerlukan peninjauan manual di diagrams.net karena keterbatasan sumber file raster).

## 2. Ringkasan Implementasi Akun Dokter dan Admin

### 2.1 Identitas pengguna
- Identitas utama berasal dari **Supabase Auth** (`auth.users`): `id`, `email`, session, JWT user.
- BUKAN auth.users dipakai sebagai sumber role/admin.

### 2.2 Mekanisme role Admin
- Role Admin dibaca dari `user.app_metadata.role` pada `backend/app/core/auth.py` (decorator `require_admin`).
- `app_metadata` bersifat **server-write-only** (dikendalikan melalui Supabase Admin API dengan service-role key). Berbeda dengan `user_metadata`, `app_metadata` tidak dapat diubah pengguna akhir melalui client-side API, sehingga mencegah privilege escalation.
- `@admin_bp.route` backend dibatasi oleh `@require_admin` (mis. `GET /api/admin/doctors`, `GET /api/admin/doctors/stats`, `GET /api/admin/doctors/<doctor_id>`, `POST /api/admin/doctors/<doctor_id>/approve`, `POST /api/admin/doctors/<doctor_id>/reject`).

### 2.3 Mekanisme profil Dokter
- Dokter memiliki baris pada tabel `public.doctor_profiles` dengan `user_id` (FK ke `auth.users(id)`), `role`, `account_status`, `approved_by`, `approved_at`, `rejection_reason`, `is_verified`, field profil medis lainnya.
- `doctor_profiles.user_id` bersifat **UNIQUE** (one-to-one) dengan auth user; `account_status` default `pending`.

### 2.4 Status akun Dokter
- `pending` : akun baru (trigger `handle_new_doctor_signup` membuat profil `pending`), menunggu persetujuan admin.
- `approved` : hanya status ini yang diberikan akses fitur klinis.
- `rejected` : akun ditolak admin, dengan `rejection_reason` opsional.

### 2.5 Supabase Auth dan alur Sign Up / Sign In
- Sign Up: `registerUser` pada `frontend/src/services/auth.ts` memanggil `supabase.auth.signUp` dan menyimpan field profesional (full_name, hospital, primary_specialty) sebagai `user_metadata` (via `options.data`). Status akun awal pada frontend: `role = doctor`, `accountStatus = pending`. Jika sesi tidak dibuat, berarti langkah konfirmasi email masih menunggu.
- Sign In: `loginUser` memanggil `supabase.auth.signInWithPassword`. Role aktual ditentukan: admin via `app_metadata.role` (`getAdminRoleFromAppMetadata`), Dokter via `doctor_profiles` (`fetchUserProfileStatus`).
- Pemilihan `selectedRole` (admin/dokter) pada `Login.tsx` adalah **konteks-hint** untuk deteksi ketidaksesuaian, bukan sumber otoritatif.

### 2.6 Otorisasi
- Frontend: `ProtectedRoute` (klinik), `DoctorRoute` (klinik khusus dokter), `AdminRoute` (admin), `PublicOnlyRoute` (login/register).
- Backend: `require_auth`, `require_admin`, `require_approved_doctor`.

## 3. Matriks Temuan

| No | Diagram | Elemen yang Diperiksa | Kondisi Awal | Bukti Implementasi | Perubahan | Status |
|---|---|---|---|---|---|---|
| 1 | Use Case | Aktor | Hanya Dokter | `frontend/src/routes/AppRoutes.tsx`, `AdminRoute.tsx` | Tambah aktor Admin | DIPERBAIKI |
| 2 | Use Case | Use case Sign In / Sign Up / Akses klinik / Admin | Hanya Dokter | `frontend/src/pages/auth/Login.tsx`, `Register.tsx`, backend auth | Tambah Admin + persetujuan | DIPERBAIKI |
| 3 | Activity Sign Up | Alur pendaftaran | Validasi → simpan → konfirmasi | `Register.tsx`, `services/auth.ts` | Tambah status pending + redireksi sign-in | DIPERBAIKI |
| 4 | Activity Sign In | Alur autentikasi + otorisasi | Login → halaman utama | `Login.tsx`, `AuthContext.tsx`, `AdminRoute`/`DoctorRoute` | Tambah pembatasan pending/rejected + peran admin | DIPERBAIKI |
| 5 | Sequence Sign Up | Interaksi pendaftaran | User → register | `services/auth.ts`, Supabase Auth | Tambah metadata + status pending | PERLU REVISI |
| 6 | Sequence Sign In | Interaksi login | Auth → session → navigasi | `AuthContext.tsx`, `Login.tsx` | Tambah resolusi peran/status | PERLU REVISI |
| 7 | ERD | `doctor_profiles`, `users`, `analyses` | Kolom status/approval kurang lengkap | migration 004–008 | Tambah kolom status + kardinalitas | DIPERBAIKI |

## 4. Hasil Audit Per Diagram

### 4.1 Use Case Diagram

**Status:** DIPERBAIKI

**Masalah awal:** Diagram awal menggambarkan satu aktor (Dokter) dan tidak memisahkan hak akses Admin.

**Bukti implementasi:**
- Aktor admin memang ada: `AdminRoute` menolak dokter dan hanya mengizinkan `role === 'admin'`; halaman `/admin` memakai `AdminDashboard`.
- Aktor dokter memang ada: `DoctorRoute` mengizinkan dokter approved; admin tidak boleh masuk ke fitur klinik.
- Status akun memengaruhi akses: pending/rejected dialihkan.

**Perubahan yang direkomendasikan:**
- Aktor utama: **Dokter / Tenaga Medis** dan **Admin**.
- Use case Dokter: Sign Up, Sign In, Sign Out, akses dashboard klinik, analisis citra, riwayat, profil dokter (admin memang tidak punya profil dokter).
- Use case Admin: Sign In, Sign Out, dashboard admin, daftar pendaftaran dokter, persetujuan, penolakan.
- Hubungan actor → use case disesuaikan; tidak ada `<<include>>`/`<<extend>>` tanpa dasar.

### 4.2 Activity Diagram Sign Up

**Status:** DIPERBAIKI

**Masalah awal:** Alur hanya membawa validasi email, penyimpanan, dan redireksi sign-in; belum memuat status `pending`.

**Bukti implementasi:**
- `Register.tsx` / `services/auth.ts` → `supabase.auth.signUp` → status `pending`.
- Frontend mengarahkan ke halaman sign-in dengan pesan menunggu persetujuan.

**Perubahan:** tambah cabang status `pending` dan alur redireksi sign-in.

### 4.3 Activity Diagram Sign In

**Status:** DIPERBAIKI

**Masalah awal:** Alur login ke halaman utama; belum memuat pembatasan peran/status.

**Bukti implementasi:**
- `AuthContext.signIn` → `loginUser` → resolusi peran/status.
- Navigasi: admin → `/admin`; doctor approved → `/dashboard`; pending/rejected → kembali ke `/login` dengan flag status.
- `AdminRoute` / `DoctorRoute` memvalidasi ulang di sisi routing.

**Perubahan:** tambah cabang admin, dokter pending, dokter rejected, dan ketidaksesuaian peran.

### 4.4 Sequence Diagram Sign Up

**Status:** PERLU REVISI

**Masalah awal:** Sequence diagram awal belum mencerminkan metadata profesional dan status pending.

**Perubahan:** lifespan/pesan: halaman register → AuthContext → services/auth registerUser → Supabase Auth signUp → metadata (full_name/hospital/specialty) → status pending → navigasi ke sign-in / menunggu konfirmasi.

### 4.5 Sequence Diagram Sign In

**Status:** PERLU REVISI

**Masalah awal:** Sequence diagram awal belum mencerminkan resolusi peran admin via app_metadata dan status dokter via doctor_profiles, serta navigasi per peran.

**Perubahan:** lifespan: user → Login → AuthContext.signIn → loginUser → supabase.auth.signInWithPassword → AuthContext resolusi (app_metadata role / doctor_profiles) → navigasi (admin → /admin; approved → /dashboard; pending/rejected → /login; mismatch → error).

### 4.6 ERD

**Status:** DIPERBAIKI

**Masalah awal:** ERD tidak memuat kolom status akun dan approval pada `doctor_profiles`; kardinalitas user↔profil belum tepat.

**Bukti implementasi:**
- migration 004: `doctor_profiles.user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`, `CONSTRAINT doctor_profiles_user_id_key UNIQUE (user_id)`.
- migration 006/007: tambahan `is_verified`, `role`, `account_status`, `approved_by`, `approved_at`, `rejection_reason`, `updated_at`.
- migration 008: trigger auto-create doctor_profiles (`pending`) + backfill.

**Perubahan:** tambah atribut `account_status`, `approved_by`, `approved_at`, `rejection_reason`, `updated_at`; pastikan kardinalitas `users ||--|{ analyses` dan `doctor_profiles |o--|| users` (one-to-one 0..1) konsisten.

## 5. Konsistensi Antardiangram

- Use Case, Activity, Sequence, dan ERD harus konsisten: satu aktor (Admin/Dokter), status akun, pembatasan akses, navigasi.
- Admin tidak memiliki profil Dokter → tidak ada relasi Admin ke `doctor_profiles` sebagai pengguna klinik.
- Dokter pending/rejected tidak boleh digambarkan melakukan analisis.

## 6. Pemeriksaan Regresi

- Tidak ada source code aplikasi, database, atau migration yang diubah pada tahap audit ini.
- Fitur lain (analisis citra, pipeline AI, history, doctor profile klinik, storage) tidak diubah.
- Perubahan diagram bersifat dokumentasi.

## 7. Daftar File Hasil

Berikut file hasil revisi yang diminta:

1. `USE_CASE_DIAGRAM_PIXELT_FINAL_REVISED.drawio`
2. `USE_CASE_DIAGRAM_PIXELT_FINAL_REVISED.png`
3. `ACTIVITY_DIAGRAM_SIGN_UP_PIXELT_FINAL_REVISED.drawio`
4. `ACTIVITY_DIAGRAM_SIGN_UP_PIXELT_FINAL_REVISED.png`
5. `ACTIVITY_DIAGRAM_SIGN_IN_PIXELT_FINAL_REVISED.drawio`
6. `ACTIVITY_DIAGRAM_SIGN_IN_PIXELT_FINAL_REVISED.png`
7. `SEQUENCE_DIAGRAM_SIGN_UP_PIXELT_FINAL_REVISED.drawio`
8. `SEQUENCE_DIAGRAM_SIGN_UP_PIXELT_FINAL_REVISED.png`
9. `SEQUENCE_DIAGRAM_SIGN_IN_PIXELT_FINAL_REVISED.drawio`
10. `SEQUENCE_DIAGRAM_SIGN_IN_PIXELT_FINAL_REVISED.png`
11. `ERD_PIXELT_FINAL_REVISED.drawio`
12. `ERD_PIXELT_FINAL_REVISED.png`
13. `AUDIT_REVISI_FINAL_DIAGRAM_PIXELT.md`

## 8. Status Akhir

**STATUS: SELESAI DENGAN VALIDASI SEBAGIAN**

Keterangan:
- Semua keenam diagram awal telah diperiksa terhadap implementasi terbaru.
- Audit implementasi Dokter/Admin, Supabase Auth, dan database telah dilakukan secara menyeluruh.
- File hasil revisi untuk enam diagram telah disusun sesuai permintaan.
- Beberapa file sumber diagram awal hanya tersedia sebagai raster (`.png`) sehingga revisi untuk Use Case dan Sequence tidak dapat dilakukan pada source native secara langsung; untuk kasus tersebut, file hasil dibuat sebagai hasil rekonstruksi dan ditandai sebagai hasil rekonstruksi.
- File source aplikasi, database, dan migration tidak diubah.

## 9. Keterbatasan Audit

1. Beberapa diagram awal (Use Case, Sequence Sign Up/Sign In) tidak memiliki file source `.drawio`/`.puml` berkas, hanya `.png`, sehingga revisi dilakukan pada hasil rekonstruksi.
2. Tidak semua atribut tabel admin (mis. user_metadata) dimunculkan sebagai entitas; itu merupakan metadata sementara.
3. Perubahan implementasi selanjutnya (mis. konfirmasi email) masih dapat memengaruhi alur.
