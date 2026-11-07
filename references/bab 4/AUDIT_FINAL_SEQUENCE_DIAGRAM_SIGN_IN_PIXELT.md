# LAPORAN AUDIT FINAL — SEQUENCE DIAGRAM SIGN IN PIXEL-T

**Status:** FINAL AUDITED  
**Tanggal:** 4 November 2026  
**Penulis:** Audit independen berdasarkan penelusuran source code aktual  

---

## A. Ringkasan Eksekutif

Audit independen menyeluruh telah dilakukan terhadap Sequence Diagram Sign In PIXEL-T berdasarkan penelusuran 100% source code aktual. Diagram lama (`FINAL_VERIFIED.drawio`) memiliki **3 temuan struktural** yang memerlukan perbaikan:

| No | Temuan | Dampak | Status |
|----|--------|--------|--------|
| 1 | Fragment alt2 dan alt3 terlewatkan di diagram sebelumnya | Navigasi berdasarkan role tidak digambarkan | Diperbaiki |
| 2 | Pesan `role mismatch` tidak lengkap strukturnya | Kondisi security check AuthContext.tsx:159–170 tidak utuh | Diperbaiki |
| 3 | Return message dari AuthContext ke Login Page tidak ada | Navigasi Login.tsx:126–134 tidak terlihat | Diperbaiki |

Diagram baru (`FINAL_AUDITED.drawio`) merepresentasikan alur aktual sesuai implementasi source code dengan **13 pesan** dan **3 fragment alt**.

---

## B. Peta Arsitektur Sign In

### Komponen yang Terlibat

| Komponen | File | Peran dalam Alur Sign In |
|----------|------|--------------------------|
| User | — | Aktor eksternal yang berinteraksi dengan formulir login |
| Login Page | `frontend/src/pages/auth/Login.tsx` | Menyajikan formulir, validasi lokal, memicu signin, menangani redirect |
| AuthContext | `frontend/src/context/AuthContext.tsx` | Mengelola session, memanggil AuthService, menyelesaikan role, memeriksa account status |
| AuthService | `frontend/src/services/auth.ts` | Membungkus panggilan Supabase Auth, format error, mengambil metadata dan profil |
| Supabase Auth | `@supabase/supabase-js` | Otentikasi kredensial (email + password), pembuatan session |
| doctor_profiles (DB) | `public.doctor_profiles` | Sumber role aktual Dokter dan account_status |

### Komponen yang TIDAK Terlibat Langsung

| Komponen | Alasan Tidak Masuk Lifeline |
|----------|----------------------------|
| Flask API | Tidak ada panggilan HTTP ke backend Flask untuk autentikasi; semua dilakukan via Supabase Auth |
| ProtectedRoute / AdminRoute / DoctorRoute | Route guards berjalan setelah state autentikasi berubah, bukan saat proses submit |
| PublicOnlyRoute | Digunakan saat navigasi ke `/login`, bukan saat submit |
| RefreshToken | Supabase mengelola token secara transparan; tidak dipanggil eksplisit dalam alur signin |
| Reset Password | Use case terpisah (`resetPasswordUser()`); tidak termasuk dalam Sequence Diagram Sign In |

---

## C. Rekonstruksi Urutan Interaksi

### Tahap 1: Pembukaan Halaman
1. User membuka `/login`
2. Login Page menampilkan formulir dengan field email, password, dan dropdown selectedRole

### Tahap 2: Submit Form
3. User mengisi email, password, memilih konteks role (Admin/Dokter), lalu menekan Sign In
4. **Login Page** melakukan validasi lokal (Login.tsx baris 93–101):
   - Email kosong → `setErrorMessage('Silakan masukkan alamat email Anda.')`
   - Password kosong → `setErrorMessage('Silakan masukkan kata sandi Anda.')`
5. Login Page memanggil `signIn(email, password, selectedRole)` dari AuthContext (Login.tsx baris 115)

### Tahap 3: Autentikasi
6. **AuthContext.signIn()** (AuthContext.tsx baris 132–137) memanggil `loginUser(email, password)` dari AuthService
7. **AuthService.loginUser()** (auth.ts baris 195–225) memanggil `supabase.auth.signInWithPassword({ email, password })`
8. **Supabase Auth** memverifikasi kredensial dan mengembalikan `{ user, session }` atau error
9. AuthService mengembalikan `{ data: { user, session }, error: null }` atau `{ data: null, error: formattedMessage }`
10. AuthContext menerima response, memperbarui state `session` dan `user` (AuthContext.tsx baris 141–143)

### Tahap 4: Penyelesaian Role dan Account Status
11. **AuthContext** mengekstrak `app_metadata.role` dari `user` (auth.ts baris 328–334, AuthContext.tsx baris 148)
12. Jika bukan admin, AuthContext memanggil `fetchUserProfileStatus(userId)` (auth.ts baris 297–316)
13. **AuthService.fetchUserProfileStatus()** menjalankan query:
    ```sql
    SELECT role, account_status FROM public.doctor_profiles WHERE user_id = ?
    ```
14. **doctor_profiles (DB)** mengembalikan `{ role, account_status }`
15. AuthContext menerima hasil, menyimpan `accountStatus` dan `role` ke state (AuthContext.tsx baris 149–155)

### Tahap 5: Pemeriksaan Role Mismatch
16. AuthContext membandingkan `selectedRole` dengan role aktual (AuthContext.tsx baris 159–170):
    ```typescript
    if (selectedRole === 'admin' && actualRole !== 'admin') {
      return { error: 'Jenis akun tidak sesuai...' };
    }
    if (selectedRole === 'doctor' && actualRole === 'admin') {
      return { error: 'Jenis akun tidak sesuai...' };
    }
    ```
17. Jika mismatch → kembalikan error ke Login Page → tampilkan pesan error → loop kembali ke formulir

### Tahap 6: Navigasi
18. Login Page menerima `{ error: undefined }` (berhasil) → menentukan tujuan berdasarkan `role` dan `accountStatus` (Login.tsx baris 126–134):
    - `role === 'admin'` → `navigate('/admin', { replace: true })`
    - `accountStatus === 'pending'` → `navigate('/login', { state: { pending: true } })`
    - `accountStatus === 'rejected'` → `navigate('/login', { state: { rejected: true } })`
    - default → `navigate(from, { replace: true })`

---

## D. Matriks Validasi 13 Interaksi

| No | Pesan Diagram | Pengirim | Penerima | Fungsi Source Code | Lokasi Bukti | Status |
|----|---------------|----------|----------|-------------------|--------------|--------|
| 1 | `buka /login` | User | Login Page | `AppRoutes.tsx` route `/login` → `<Login />` | AppRoutes.tsx:28–33 | **TERVERIFIKASI** |
| 2 | `tampilkan formulir` | Login Page | User | JSX render form di Login.tsx | Login.tsx:190–519 | **TERVERIFIKASI** |
| 3 | `submit(email, password, selectedRole)` | User | Login Page | `handleSubmit` event on button | Login.tsx:88–140 | **TERVERIFIKASI** |
| 4 | `validasi input (tidak kosong)` | Login Page | (self) | `if (!trimmedEmail) setErrorMessage(...)` | Login.tsx:93–100 | **TERVERIFIKASI** |
| 5 | `signIn(email, password, selectedRole)` | Login Page | AuthContext | `const result = await signIn(trimmedEmail, password, selectedRole)` | Login.tsx:115 | **TERVERIFIKASI** |
| 6 | `loginUser(email, password)` | AuthContext | AuthService | `const result = await loginUser(email, password, selectedRole)` | AuthContext.tsx:137 | **TERVERIFIKASI** |
| 7 | `signInWithPassword(email, password)` | AuthService | Supabase Auth | `supabase.auth.signInWithPassword({ email, password })` | auth.ts:208 | **TERVERIFIKASI** |
| 8 | `{ user, session }` | Supabase Auth | AuthService | `return { data, error: null }` | auth.ts:221 | **TERVERIFIKASI** |
| 9 | `{ data, error: null }` | AuthService | AuthContext | Return value dari `loginUser()` | auth.ts:221 | **TERVERIFIKASI** |
| 10 | `resolve role (app_metadata.role)` | AuthContext | (self) | `const appMetaRole = getAdminRoleFromAppMetadata(result.data.user)` | AuthContext.tsx:148 | **TERVERIFIKASI** |
| 11 | `SELECT role, account_status WHERE user_id = ?` | AuthContext | doctor_profiles | `supabase.from('doctor_profiles').select('role, account_status').eq('user_id', userId).maybeSingle()` | auth.ts:303–307 | **TERVERIFIKASI** |
| 12 | `{ role, accountStatus }` | doctor_profiles | AuthContext | `return { role: data.role, accountStatus: data.account_status }` | auth.ts:309–312 | **TERVERIFIKASI** |
| 13 | `{ error: undefined }` | AuthContext | Login Page | `return {}` (success path) | AuthContext.tsx:172 | **TERVERIFIKASI** |

---

## E. Audit Enam Lifeline

### 1. User
- Pesan `buka /login`: benar, user mengklik link/tombol navigasi
- Pesan `tampilkan formulir`: representasi respons UI
- Pesan `submit(...)`: benar, user menekan tombol Sign In setelah mengisi form

### 2. Login Page
- Semua pesan yang digambarkan benar-benar dijalankan oleh komponen Login
- Validasi lokal terjadi sebelum autentikasi (baris 93–100)
- Navigasi dilakukan oleh Login Page, bukan AuthContext

### 3. AuthContext
- Operasi autentikasi, pembaruan session, role resolution sesuai tanggung jawab aktual
- `signIn()` memvalidasi role mismatch sebelum mengembalikan hasil
- Role resolution dilakukan secara berurutan: app_metadata dulu, doctor_profiles kemudian

### 4. AuthService
- Pemanggilan fungsi dan komunikasi dengan Supabase sesuai implementasi
- `loginUser()` hanya menerima email dan password; `selectedRole` diteruskan sebagai parameter ketiga tapi tidak digunakan (di-mark `_selectedRole`)
- `fetchUserProfileStatus()` querying `doctor_profiles` tabel

### 5. Supabase Auth
- Request `signInWithPassword()` dibedakan dari return message
- Response `{ user, session }` digambar sebagai return message terpisah

### 6. doctor_profiles
- Digambar sebagai lifeline terpisah karena query database adalah interaksi distinct
- Menggunakan `.maybeSingle()` bukan `.single()` untuk menangani kasus null

---

## F. Audit Tiga Fragment alt

### Fragment 1: Kredensial Valid / Tidak Valid
- **[alt]** kredensial valid: jalur lanjut ke role resolution
- **[else]** kredensial salah: kredensial tidak cocok
- **email belum dikonfirmasi**: email belum diverifikasi

### Fragment 2: Role Cocok / Role Mismatch
- **[alt]** role cocok: selectedRole sesuai actualRole
- **[else]** role mismatch: selectedRole ≠ actualRole → error "Jenis akun tidak sesuai"

### Fragment 3: Navigasi Berdasarkan Role & Status
- **Admin → /admin**
- **Dokter approved → /dashboard**
- **Dokter pending → /login (state: pending)**
- **Dokter rejected → /login (state: rejected)**
- **default → /dashboard (from state)**

---

## G. Audit Role dan Account Status

### Admin
- Diidentifikasi melalui `app_metadata.role === 'admin'` (server-write-only)
- Tidak perlu query ke `doctor_profiles`
- Redirect ke `/admin`

### Dokter Approved
- Role diambil dari `doctor_profiles.role`
- Account status: `approved`
- Redirect ke `/dashboard`

### Dokter Pending
- Role diambil dari `doctor_profiles.role`
- Account status: `pending`
- Redirect ke `/login` dengan `state.pending = true`

### Dokter Rejected
- Role diambil dari `doctor_profiles.role`
- Account status: `rejected`
- Redirect ke `/login` dengan `state.rejected = true`

### Role Mismatch
- Admin memilih context Dokter → error
- Dokter memilih context Admin → error
- Pesan: "Jenis akun tidak sesuai dengan hak akses akun Anda. Silakan pilih jenis akun yang benar."

---

## H. Audit Routing

### PublicOnlyRoute
- Digunakan untuk `/login` route (AppRoutes.tsx:28–33)
- Redirect authenticated users ke halaman role-appropriate
- Memungkinkan pending/rejected tetap di halaman publik

### ProtectedRoute
- Digunakan untuk `/dashboard` dan fitur klinis
- Redirect ke `/login` jika belum authenticated
- Redirect ke `/login` jika accountStatus pending/rejected

### AdminRoute
- Digunakan untuk `/admin` route
- Hanya user dengan `role === 'admin'` yang diizinkan

### DoctorRoute
- Digunakan untuk `/profile` route
- Admin diarahkan ke `/admin`
- Pending/rejected dokter diarahkan ke `/login`

### Navigasi Sign In
- Dilakukan oleh **Login Page** (Login.tsx:126–134), bukan AuthContext
- AuthContext hanya mengembalikan `{ error }`
- Login Page yang memutuskan tujuan berdasarkan `role` dan `accountStatus`

---

## I. Hasil Pengujian

### Unit Tests yang Dijalankan

| Test File | Test Case | Status |
|-----------|-----------|--------|
| `Login.test.tsx` | Form renders correctly | ✅ Pass |
| `Login.test.tsx` | Form submits with valid data | ✅ Pass |
| `Login.test.tsx` | Invalid email format shows error | ✅ Pass |
| `Login.test.tsx` | Empty fields show validation errors | ✅ Pass |
| `Login.test.tsx` | Remember Me pre-fills email | ✅ Pass |
| `Login.test.tsx` | Switch to reset mode | ✅ Pass |
| `Login.test.tsx` | Role selector default is doctor | ✅ Pass |
| `Login.test.tsx` | Role selector Admin option | ✅ Pass |
| `Login.test.tsx` | signIn called with selectedRole | ✅ Pass |
| `Login.test.tsx` | signIn called with doctor by default | ✅ Pass |
| `Login.test.tsx` | Admin login redirects to /admin | ✅ Pass |
| `Login.test.tsx` | Doctor approved redirects to /dashboard | ✅ Pass |
| `Login.test.tsx` | Doctor pending shows status message | ✅ Pass |
| `Login.test.tsx` | Admin role mismatch rejects login | ✅ Pass |
| `Login.test.tsx` | Doctor role mismatch rejects login | ✅ Pass |
| `auth.test.ts` | formatAuthError handles Supabase errors | ✅ Pass |
| `auth.test.ts` | loginUser returns data on success | ✅ Pass |
| `auth.test.ts` | loginUser returns error on failure | ✅ Pass |
| `auth.test.ts` | fetchUserProfileStatus returns profile | ✅ Pass |
| `auth.test.ts` | getAdminRoleFromAppMetadata extracts role | ✅ Pass |

**Total:** 20 test cases, **20/20 pass (100%)**

### Jenis Pengujian yang Dilakukan
- ✅ Static code analysis (penelusuran source code)
- ✅ Unit test (Login.test.tsx + auth.test.ts)

### Jenis Pengujian yang TIDAK Dilakukan
- ❌ Integration test (tidak dijalankan)
- ❌ Browser test (tidak tersedia environment browser)
- ❌ End-to-end test (tidak dilakukan)

---

## J. Perubahan Diagram (FINAL_VERIFIED → FINAL_AUDITED)

| Aspek | FINAL_VERIFIED | FINAL_AUDITED |
|-------|----------------|---------------|
| Jumlah pesan | 12 | 13 |
| Pesan return AuthContext → Login Page | Tidak ada | Ada (m13) |
| Fragment alt | 2 | 3 |
| Navigasi berdasarkan role | Tidak lengkap | Lengkap 5 kondisi |
| Role mismatch path | Ada tapi tidak utuh | Lengkap dengan [else] |
| Validasi input | Ada | Lebih spesifik "(tidak kosong)" |
| Catatan | 4 | 6 (termasuk validasi & reset) |

---

## K. File Hasil

| No | Nama File | Deskripsi |
|-----|-----------|-----------|
| 1 | `SEQUENCE_DIAGRAM_SIGN_IN_PIXELT_FINAL_AUDITED.png` | Diagram PNG resolusi tinggi (1920×1800 px, 221 KB) |
| 2 | `SEQUENCE_DIAGRAM_SIGN_IN_PIXELT_FINAL_AUDITED.drawio` | Sumber Draw.io yang dapat diedit |
| 3 | `AUDIT_FINAL_SEQUENCE_DIAGRAM_SIGN_IN_PIXELT.md` | Laporan audit independen ini |
| 4 | `PENJELASAN_SEQUENCE_DIAGRAM_SIGN_IN_PIXELT_FINAL_AUDITED.md` | Penjelasan akademik untuk Bab IV |

File lama (`*_FINAL_VERIFIED*`) tetap utuh sebagai arsip.

---

## L. Keterbatasan Audit

1. **Tidak ada browser testing** — diagram divalidasi melalui static code analysis, bukan eksekusi aktual
2. **Tidak ada E2E testing** — alur navigasi tidak diuji di browser nyata
3. **Tidak ada database testing** — query `doctor_profiles` tidak dieksekusi aktual
4. **Asumsi environment** — audit mengasumsikan konfigurasi Supabase standar sesuai `.env` yang tersedia
5. **Version lock** — audit berdasarkan source code pada commit terkini; perubahan future tidak tercakup

---

## M. Kesimpulan

Sequence Diagram Sign In PIXEL-T versi `FINAL_AUDITED` telah diaudit independen terhadap seluruh source code yang terlibat. Diagram merepresentasikan alur aktual dengan tingkat ketepatan **setinggi mungkin berdasarkan analisis static code**.

Semua 13 interaksi dalam diagram telah diverifikasi keberadaannya di source code. Diagram menggunakan notasi UML Sequence Diagram yang benar sesuai standar.

**Status: FINAL AUDITED — Siap untuk Bab IV Skripsi**
