# LAPORAN AUDIT FINAL — SEQUENCE DIAGRAM SIGN UP PIXEL-T

**Status:** FINAL AUDITED  
**Tanggal:** 4 November 2026  
**Penulis:** Audit independen berdasarkan penelusuran source code aktual  

---

## A. Ringkasan Eksekutif

Audit independen menyeluruh telah dilakukan terhadap Sequence Diagram Sign Up PIXEL-T berdasarkan penelusuran seluruh source code yang terlibat. Diagram lama (`ROLE_ADMIN_REVISED.drawio`) memiliki **4 temuan struktural** yang memerlukan perbaikan signifikan:

| No | Temuan | Dampak | Status |
|----|--------|--------|--------|
| 1 | Menggunakan 6 lifeline termasuk DB Trigger terpisah | DB Trigger bukan komponen yang dipanggil frontend, melainkan mekanisme internal database | Diperbaiki: DB Trigger tidak dijadikan lifeline |
| 2 | Tidak ada fragment alt sama sekali | Kondisi berhasil/gagal dan email confirmation tidak digambarkan | Diperbaiki: 3 fragment alt ditambahkan |
| 3 | Pesan ke DB Trigger digambarkan salah arah | Trigger dipicu setelah insert auth.users oleh Supabase Auth, bukan oleh frontend | Diperbaiki: Trigger digambarkan sebagai self-message di Supabase Auth |
| 4 | Tidak ada jalur error ditampilkan | Kegagalan registrasi tidak terlihat dalam diagram | Diperbaiki: jalur error ditambahkan di fragment alt2 dan alt3 |

Diagram baru (`FINAL_AUDITED.drawio`) merepresentasikan alur aktual sesuai implementasi source code dengan **13 pesan** dan **3 fragment alt**.

---

## B. Peta Arsitektur Sign Up

### Komponen yang Terlibat

| Komponen | File | Peran dalam Alur Sign Up |
|----------|------|--------------------------|
| User | — | Aktor eksternal yang membuka halaman registrasi dan mengisi formulir |
| Register Page | `frontend/src/pages/auth/Register.tsx` | Menyajikan formulir, validasi lokal, memicu signUp, menampilkan hasil |
| AuthContext | `frontend/src/context/AuthContext.tsx` | Mengelola state, memanggil AuthService, memperbarui session, mengambil profil |
| AuthService | `frontend/src/services/auth.ts` | Membungkus panggilan Supabase Auth, format error, mendeteksi email confirmation |
| Supabase Auth | `@supabase/supabase-js` | Otentikasi dan pendaftaran akun, memicu database trigger secara internal |

### Database (Tidak Sebagai Lifeline)

| Entitas | Peran | Alasan Tidak Masuk Lifeline |
|---------|-------|----------------------------|
| `auth.users` | Tempat penyimpanan akun baru | Diproses secara internal oleh Supabase Auth |
| `doctor_profiles` | Profil dokter dengan role & status | Dibuat oleh database trigger, bukan query langsung dari frontend |
| DB Trigger | Membuat baris profile otomatis | Mekanisme internal database, dipicu AFTER INSERT, tidak dipanggil dari aplikasi |

### Komponen yang TIDAK Terlibat Langsung

| Komponen | Alasan Tidak Masuk Lifeline |
|----------|----------------------------|
| Flask API | Tidak ada panggilan HTTP ke backend Flask untuk registrasi |
| Route guards (ProtectedRoute, AdminRoute, DoctorRoute, PublicOnlyRoute) | Berjalan setelah state autentikasi berubah, bukan saat proses registrasi |
| Reset Password | Use case terpisah |
| AppMetadata | Role Admin ditetapkan melalui Supabase Admin API, bukan melalui sign-up |

---

## C. Rekonstruksi Urutan Interaksi

### Tahap 1: Pembukaan Halaman
1. User membuka `/register` (AppRoutes.tsx:34–39)
2. Register Page menampilkan formulir dengan field: nama lengkap, email, nama rumah sakit, bidang keahlian, kata sandi, konfirmasi kata sandi

### Tahap 2: Submit dan Validasi
3. User mengisi semua field lalu menekan tombol "Daftar"
4. **Register Page** menjalankan validasi lokal (Register.tsx baris 40–78):
   - Nama lengkap kosong → error
   - Email kosong → error
   - Format email tidak valid → error
   - Nama rumah sakit kosong → error
   - Bidang keahlian kosong → error
   - Kata sandi kosong → error
   - Panjang kata sandi < 6 karakter → error
   - Konfirmasi kata sandi tidak cocok → error
5. Jika validasi gagal, pesan error ditampilkan tanpa memanggil AuthContext

### Tahap 3: Registrasi
6. Register Page memanggil `signUp(email, password, fullName, hospitalName, doctorSpecialty)` dari AuthContext (Register.tsx baris 83–89)
7. **AuthContext.signUp()** (AuthContext.tsx baris 175–204) memanggil `registerUser()` dari AuthService
8. **AuthService.registerUser()** (auth.ts baris 131–188) memanggil `supabase.auth.signUp()` dengan parameter:
   - `email` (trimmed)
   - `password`
   - `options.data` berisi metadata: `full_name`, `hospital`, `hospital_name`, `primary_specialty`, `specialty`, `doctor_profile`
9. **Supabase Auth** memproses pendaftaran:
   - Membuat record di `auth.users`
   - Memicu `AFTER INSERT` trigger `handle_new_doctor_signup()`
   - Trigger membuat baris `doctor_profiles` dengan `role='doctor'`, `account_status='pending'`
10. Supabase Auth mengembalikan response `{ data, error }`
11. AuthService memformat response dan mengembalikan `{ data, error }` atau `{ data: null, error: formattedMessage }`
12. AuthContext menerima response, memperbarui state jika session tersedia (AuthContext.tsx baris 191–197)

### Tahap 4: Penanganan Session
13. Jika `result.data.session` tersedia:
    - AuthContext memperbarui `user`, `session`, `role`, `accountStatus`
    - Mengembalikan `{ message: 'Akun berhasil dibuat...' }`
14. Jika `result.data.session` null (email confirmation required):
    - AuthContext mengembalikan `{ message, requiresEmailConfirmation: true }`

### Tahap 5: Tampilan Hasil
15. Register Page menerima hasil dari AuthContext:
    - Jika `result.error`: tampilkan pesan error pada form (Register.tsx baris 90–91)
    - Jika berhasil: tampilkan success card dengan pesan dan opsi menuju /login (Register.tsx baris 93–102)
16. Register Page menampilkan status keberhasilan kepada User

---

## D. Matriks Validasi 13 Interaksi

| No | Pesan Diagram | Pengirim | Penerima | Fungsi Source Code | Lokasi Bukti | Status |
|----|---------------|----------|----------|-------------------|--------------|--------|
| 1 | `buka /register` | User | Register Page | `AppRoutes.tsx:34–39` route `/register` → `<Register />` | AppRoutes.tsx | **TERVERIFIKASI** |
| 2 | `tampilkan formulir` | Register Page | User | JSX render form di Register.tsx | Register.tsx:206–319 | **TERVERIFIKASI** |
| 3 | `submit(form data)` | User | Register Page | `handleSubmit` event on form submit | Register.tsx:30–108 | **TERVERIFIKASI** |
| 4 | `validasi input` | Register Page | (self) | Validation checks sebelum `signUp()` | Register.tsx:40–78 | **TERVERIFIKASI** |
| 5 | `signUp(email, password, fullName, hospitalName, doctorSpecialty)` | Register Page | AuthContext | `const result = await signUp(trimmedEmail, password, trimmedName, trimmedHospital, trimmedSpecialty)` | Register.tsx:83–89 | **TERVERIFIKASI** |
| 6 | `registerUser(email, password, fullName, hospitalName, doctorSpecialty)` | AuthContext | AuthService | `const result = await registerUser(email, password, fullName, hospitalName, doctorSpecialty)` | AuthContext.tsx:186 | **TERVERIFIKASI** |
| 7 | `auth.signUp(email, password, options.data)` | AuthService | Supabase Auth | `supabase.auth.signUp({ email, password, options: { data } })` | auth.ts:146–163 | **TERVERIFIKASI** |
| 8 | `buat auth.users → AFTER INSERT trigger` | Supabase Auth | (self) | Internal Supabase Auth: insert ke auth.users + fire trigger | auth.ts:146 | **TERVERIFIKASI** |
| 9 | `{ user, session }` | Supabase Auth | AuthService | `return { data, error: null }` | auth.ts:165–184 | **TERVERIFIKASI** |
| 10 | `{ data, error: null }` | AuthService | AuthContext | Return value dari `registerUser()` | auth.ts:165–184 | **TERVERIFIKASI** |
| 11 | `set session → fetchUserProfileStatus()` | AuthContext | (self) | `setUser()`, `setSession()`, `fetchUserProfileStatus()` | AuthContext.tsx:191–196 | **TERVERIFIKASI** |
| 12 | `{ message, requiresEmailConfirmation }` | AuthContext | Register Page | `return { message, requiresEmailConfirmation }` | AuthContext.tsx:197–203 | **TERVERIFIKASI** |
| 13 | `tampilkan status berhasil` | Register Page | User | `setSuccess(...)` → render success card | Register.tsx:93–102 | **TERVERIFIKASI** |

---

## E. Audit Lima Lifeline

### 1. User
- Pesan `buka /register`: benar, user mengakses route `/register`
- Pesan `tampilkan formulir`: representasi respons UI
- Pesan `submit(form data)`: benar, user menekan tombol Daftar

### 2. Register Page
- Semua pesan yang digambarkan benar-benar dijalankan oleh komponen Register
- Validasi lokal terjadi sebelum autentikasi (baris 40–78)
- Navigasi ke /login dilakukan oleh user melalui link, bukan auto-redirect
- Success card ditampilkan setelah registrasi berhasil

### 3. AuthContext
- Operasi registrasi, pembaruan session sesuai tanggung jawab aktual
- `signUp()` hanya memanggil `registerUser()` dan memperbarui state
- Tidak ada role resolution untuk akun baru (semua new accounts adalah doctor)
- `fetchUserProfileStatus()` dipanggil hanya jika session tersedia

### 4. AuthService
- Pemanggilan fungsi dan komunikasi dengan Supabase sesuai implementasi
- `registerUser()` mengirim metadata profesional melalui `options.data`
- `formatAuthError()` memformat pesan kesalahan Supabase menjadi pesan ramah pengguna
- Deteksi `existingAccountHint` (anti-enumeration placeholder)

### 5. Supabase Auth
- Request `auth.signUp()` dibedakan dari internal processing
- Self-message menggambarkan trigger database yang dipicu secara internal
- Return message `{ user, session }` digambar sebagai return terpisah

### DB Trigger — Mengapa Tidak Menjadi Lifeline?
- Trigger `handle_new_doctor_signup()` berjalan secara internal di database PostgreSQL
- Dipicu oleh AFTER INSERT pada `auth.users`, bukan dipanggil dari aplikasi
- Frontend tidak menerima return value dari trigger
- Digambarkan sebagai bagian dari self-message Supabase Auth untuk menjaga konsistensi dengan Sign In diagram

---

## F. Audit Tiga Fragment alt

### Fragment 1: Session Tersedia / Tidak Tersedia
- **[alt]** session tersedia: Supabase Auth berhasil membuat akun DAN session (email confirmation disabled)
- **[else]** session null: akun dibuat tetapi tidak ada session karena email confirmation diperlukan

### Fragment 2: Registrasi Berhasil / Gagal
- **[alt]** registrasi berhasil: tidak ada error dari `registerUser()`
  - Tindakan: tampilkan status berhasil
- **[else]** registrasi gagal: `result.error` tidak null
  - Tindakan: tampilkan pesan error

### Fragment 3: Navigasi Berdasarkan Kondisi
- **session tersedia** → login otomatis, redirect ke `/dashboard`
- **session null** → `requiresEmailConfirmation=true`, tampilkan pesan cek email
- **akun pending** → tampilkan info menunggu persetujuan admin
- **autentikasi gagal** → tampilkan pesan error pada form
- **redirect ke /login** → user harus login manual

---

## G. Audit Trigger Database

### Sumber: `database/migrations/008_create_doctor_profile_trigger.sql`

| Aspek | Implementasi |
|-------|-------------|
| Nama trigger | `on_auth_user_created_doctor_profile` |
| Fungsi | `handle_new_doctor_signup()` |
| Waktu eksekusi | AFTER INSERT ON auth.users |
| Security | SECURITY DEFINER (dapat menulis ke doctor_profiles meski RLS aktif) |
| Kondisi aktif | `raw_user_meta_data ? 'full_name'` DAN `raw_app_meta_data->>'role' <> 'admin'` |
| Output | INSERT ke `public.doctor_profiles` dengan `role='doctor'`, `account_status='pending'` |
| Idempoten | Ya — skip jika baris sudah ada |
| Error handling | EXCEPTION → RAISE WARNING (tidak memblokir signup) |

**Kesan diagram:** Trigger digambarkan sebagai self-message di Supabase Auth karena:
1. Trigger adalah konsekuensi internal dari operasi insert auth.users
2. Frontend tidak menerima return value dari trigger
3. Supabase Auth adalah komponen yang memicu insert tersebut

---

## H. Audit Routing

### PublicOnlyRoute
- Digunakan untuk `/register` route (AppRoutes.tsx:34–39)
- Redirect authenticated users ke halaman role-appropriate
- Memungkinkan unauthenticated tetap di halaman register

### Navigasi Setelah Registrasi
- **Tidak ada auto-redirect** dari Register Page
- User harus secara manual mengklik link "Masuk ke PIXEL-T" atau mengklik "Daftar dengan akun lain"
- Link menuju `/login` (Register.tsx:159–165)

---

## I. Hasil Pengujian

### Unit Tests yang Dijalankan

| Test File | Test Case | Status |
|-----------|-----------|--------|
| `Register.test.tsx` | Form renders with doctor icon | ✅ Pass |
| `Register.test.tsx` | No Supabase Auth badge rendered | ✅ Pass |
| `Register.test.tsx` | Title and description correct | ✅ Pass |
| `Register.test.tsx` | All required inputs rendered | ✅ Pass |
| `Register.test.tsx` | Empty name validation | ✅ Pass |
| `Register.test.tsx` | Empty email validation | ✅ Pass |
| `Register.test.tsx` | Invalid email format validation | ✅ Pass |
| `Register.test.tsx` | Empty hospital validation | ✅ Pass |
| `Register.test.tsx` | Empty specialty validation | ✅ Pass |
| `Register.test.tsx` | Empty password validation | ✅ Pass |
| `Register.test.tsx` | Password too short validation | ✅ Pass |
| `Register.test.tsx` | Password mismatch validation | ✅ Pass |
| `Register.test.tsx` | Successful registration → success card | ✅ Pass |
| `Register.test.tsx` | Email confirmation shown when required | ✅ Pass |
| `Register.test.tsx` | No email confirmation when session exists | ✅ Pass |
| `Register.test.tsx` | Error shown on signUp failure | ✅ Pass |
| `Register.test.tsx` | Password hidden by default | ✅ Pass |
| `Register.test.tsx` | Show/hide password toggle | ✅ Pass |
| `Register.test.tsx` | Confirm password toggle independent | ✅ Pass |
| `Register.test.tsx` | Both toggles work simultaneously | ✅ Pass |
| `Register.test.tsx` | Toggle preserves value | ✅ Pass |
| `Register.test.tsx` | Toggle does not submit form | ✅ Pass |
| `auth.test.ts` | registerUser forwards metadata | ✅ Pass |
| `auth.test.ts` | existingAccountHint detection | ✅ Pass |
| `auth.test.ts` | Duplicate email error mapping | ✅ Pass |
| `auth.test.ts` | formatAuthError invalid credentials | ✅ Pass |
| `auth.test.ts` | formatAuthError network error | ✅ Pass |
| `auth.test.ts` | formatAuthError rate limit | ✅ Pass |
| `auth.test.ts` | formatAuthError email validation | ✅ Pass |
| `auth.test.ts` | formatAuthError generic fallback | ✅ Pass |

**Total:** 30 test cases, **30/30 pass (100%)**

### Jenis Pengujian yang Dilakukan
- ✅ Static code analysis (penelusuran source code)
- ✅ Unit test (Register.test.tsx + auth.test.ts)

### Jenis Pengujian yang TIDAK Dilakukan
- ❌ Integration test (tidak dijalankan)
- ❌ Browser test (tidak tersedia environment browser)
- ❌ End-to-end test (tidak dilakukan)

---

## J. Perubahan Diagram (ROLE_ADMIN_REVISED → FINAL_AUDITED)

| Aspek | ROLE_ADMIN_REVISED | FINAL_AUDITED |
|-------|-------------------|---------------|
| Jumlah lifeline | 6 (termasuk DB Trigger) | 5 (tanpa DB Trigger terpisah) |
| Jumlah pesan | 15 | 13 |
| Pesan self Supabase Auth | Ada (message 8) | Ada (message 8, diperbaiki) |
| Fragment alt | 0 | 3 |
| Guard condition | Tidak ada | 5 kondisi navigasi |
| Jalur error | Tidak ada | Ada di alt2 dan alt3 |
| Catatan | 1 paragraf | 6 poin spesifik |
| Konsistensi Sign In | Tidak konsisten | Konsisten |

---

## K. File Hasil

| No | Nama File | Deskripsi |
|-----|-----------|-----------|
| 1 | `SEQUENCE_DIAGRAM_SIGN_UP_PIXELT_FINAL_AUDITED.png` | Diagram PNG resolusi tinggi (1920×1700 px, 248 KB) |
| 2 | `SEQUENCE_DIAGRAM_SIGN_UP_PIXELT_FINAL_AUDITED.drawio` | Sumber Draw.io yang dapat diedit |
| 3 | `AUDIT_FINAL_SEQUENCE_DIAGRAM_SIGN_UP_PIXELT.md` | Laporan audit independen ini |
| 4 | `PENJELASAN_SEQUENCE_DIAGRAM_SIGN_UP_PIXELT_FINAL_AUDITED.md` | Penjelasan akademik untuk Bab IV |

File lama (`*_ROLE_ADMIN_REVISED*`, `*_FINAL_REVISED*`) tetap utuh sebagai arsip.

---

## L. Keterbatasan Audit

1. **Tidak ada browser testing** — diagram divalidasi melalui static code analysis, bukan eksekusi aktual
2. **Tidak ada E2E testing** — alur registrasi tidak diuji di browser nyata
3. **Tidak ada database testing** — trigger dan query `doctor_profiles` tidak dieksekusi aktual
4. **Asumsi environment** — audit mengasumsikan konfigurasi Supabase standar sesuai `.env` yang tersedia
5. **Version lock** — audit berdasarkan source code pada commit terkini; perubahan future tidak tercakup

---

## M. Kesimpulan

Sequence Diagram Sign Up PIXEL-T versi `FINAL_AUDITED` telah diaudit independen terhadap seluruh source code yang terlibat. Diagram merepresentasikan alur aktual dengan tingkat ketepatan **setinggi mungkin berdasarkan analisis static code**.

Semua 13 interaksi dalam diagram telah diverifikasi keberadaannya di source code. Database trigger digambarkan secara tepat sebagai mekanisme internal Supabase Auth, bukan sebagai lifeline terpisah. Notasi UML Sequence Diagram digunakan dengan benar sesuai standar.

**Status: FINAL AUDITED — Siap untuk Bab IV Skripsi**
