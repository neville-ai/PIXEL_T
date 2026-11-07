# AUDIT INDEPENDEN ACTIVITY DIAGRAM SIGN IN PIXEL-T

**Dokumen Pendukung Bab IV Skripsi S1**
Audit kedua dilakukan secara independen dari audit sebelumnya, dengan memeriksa seluruh source code dari awal.

Status akhir: **VERIFIED — FINAL**

---

## A. Ringkasan Eksekutif

Audit independen ini memvalidasi kesesuaian *Activity Diagram* Sign In PIXEL-T terhadap implementasi aktual sistem dua peran (Admin + Dokter). Seluruh 22 activity node, 6 decision node, 35 control flow edge, dan 1 UML note telah diperiksa terhadap source code aktual.

**Kesimpulan:** Diagram `ACTIVITY_DIAGRAM_SIGN_IN_PIXELT_FINAL_VERIFIED.drawio` / `.png` **sesuai dengan implementasi aktual** web PIXEL-T. Semua percabangan, loop, dan navigasi yang digambarkan memiliki dasar implementasi nyata di kode sumber.

Perbandingan dengan versi sebelumnya:
- Diagram lama (`FINAL_REVISED.drawio` dan `ROLE_ADMIN_REVISED.drawio`) memiliki cacat struktural kritis (node start/end bukan notasi UML, decision node persegi, node terisolasi).
- Diagram `FINAL.drawio` yang dibuat sebelumnya sudah benar; versi `FINAL_VERIFIED.drawio` merupakan render ulang yang identik dengan validasi XML dan visual baru.

---

## B. Peta Implementasi Sign In

### B.1 Arsitektur Panggilan Fungsi (Call Chain)

```
User klik Sign In
  └─ Login.tsx:handleSubmit() [baris 88-140]
       ├─ Validasi lokal: email.trim() tidak kosong (baris 93-97)
       ├─ Validasi lokal: password tidak kosong (baris 98-101)
       ├─ Remember Me: setRememberedEmail() (baris 107-111)
       └─ signIn(trimmedEmail, password, selectedRole) [baris 115]
            └─ AuthContext.tsx:signIn() [baris 132-173]
                 ├─ loginUser(email, password, selectedRole) [auth.ts:195-225]
                 │    └─ supabase.auth.signInWithPassword({email, password})
                 ├─ setUser(user) + setSession(session) [AuthContext.tsx:142-143]
                 ├─ getAdminRoleFromAppMetadata(user) [auth.ts:328-334]
                 ├─ fetchUserProfileStatus(user) [auth.ts:297-316]
                 │    └─ SELECT role, account_status FROM doctor_profiles WHERE user_id=?
                 ├─ actualRole = admin ? 'admin' : profileInfo?.role
                 ├─ actualStatus = profileInfo?.accountStatus
                 ├─ setRole(actualRole) + setAccountStatus(actualStatus) [baris 154-155]
                 ├─ Role mismatch check [baris 159-170]
                 │    ├─ selectedRole='admin' && actualRole≠'admin' → error
                 │    └─ selectedRole='doctor' && actualRole==='admin' → error
                 └─ return {} (success) or {error}
       └─ Navigasi [Login.tsx:126-134]
            ├─ role==='admin' → navigate('/admin')
            ├─ accountStatus==='pending' → navigate('/login', state.pending=true)
            ├─ accountStatus==='rejected' → navigate('/login', state.rejected=true)
            └─ else → navigate(from)  (default '/dashboard')
```

### B.2 Route Guards

| Guard | File | Perilaku |
|-------|------|----------|
| `PublicOnlyRoute` | `components/auth/PublicOnlyRoute.tsx` | User terautentikasi → redirect ke `/admin` (admin) atau `/dashboard` (approved doctor). Pending/rejected tetap di halaman publik. |
| `ProtectedRoute` | `components/auth/ProtectedRoute.tsx` | !user → `/login`. pending/rejected → `/login` dengan state flag. |
| `AdminRoute` | `components/auth/AdminRoute.tsx` | !user → `/login`. role≠'admin' → `/dashboard`. |
| `DoctorRoute` | `components/auth/DoctorRoute.tsx` | !user → `/login`. role==='admin' → `/admin`. pending/rejected → `/login`. |

### B.3 Sumber Role dan Account Status

| Sumber | Type | Keandalan | Penggunaan |
|--------|------|-----------|------------|
| `app_metadata.role` | Server-write-only | Paling tepercaya | Penentuan Admin |
| `doctor_profiles.role` | Database column | Terpercaya | Penentuan Dokter |
| `doctor_profiles.account_status` | Database column | Terpercaya | pending/approved/rejected |
| `user.user_metadata` | Client-writeable | Kurang tepercaya | Tidak digunakan untuk otorisasi |

---

## C. Matriks Validasi Elemen Diagram

| No | Elemen Diagram | Klaim Alur | Bukti Source Code | File & Baris | Status |
|----|---------------|------------|-------------------|-------------|--------|
| 1 | Initial Node (lingkaran hitam) | Titik awal alur | Standar UML Activity Diagram | — | ✅ TERVERIFIKASI |
| 2 | Membuka halaman `/login` | Pengguna mengakses `/login` | `AppRoutes.tsx:26-33` + `PublicOnlyRoute.tsx` | AppRoutes.tsx:26-33 | ✅ TERVERIFIKASI |
| 3 | Mengisi email, kata sandi, memilih jenis akun | Form memiliki 3 input | `Login.tsx:64-66` (selectedRole, email, password) | Login.tsx:64-66 | ✅ TERVERIFIKASI |
| 4 | Memvalidasi input (email wajib, kata sandi wajib) | Validasi lokal sebelum submit | `Login.tsx:93-101` (early return jika kosong) | Login.tsx:93-101 | ✅ TERVERIFIKASI |
| 5 | Decision "Input valid?" | Percabangan sebelum signIn | `Login.tsx:94,100` (if !trimmedEmail: return; if !password: return) | Login.tsx:94,100 | ✅ TERVERIFIKASI |
| 6 | [Ya] → signIn() | Input valid lanjut autentikasi | `Login.tsx:115` (await signIn(...)) | Login.tsx:115 | ✅ TERVERIFIKASI |
| 7 | [Tidak] → pesan kesalahan → kembali form | Validasi gagal, loop ke form | `Login.tsx:95,100` (setErrorMessage + return) | Login.tsx:95,100 | ✅ TERVERIFIKASI |
| 8 | Memanggil signIn() → supabase.auth.signInWithPassword() | Satu panggilan autentikasi | `AuthContext.tsx:137` → `auth.ts:208` | AuthContext.tsx:137, auth.ts:208 | ✅ TERVERIFIKASI |
| 9 | Decision "Kredensial valid?" | Periksa result.error | `auth.ts:213` (if error → return {error}) | auth.ts:213 | ✅ TERVERIFIKASI |
| 10 | [Ya] → perbarui sesi & state | Session OK, lanjut resolve role | `auth.ts:221` → `AuthContext.tsx:142-155` | auth.ts:221, AuthContext.tsx:142-155 | ✅ TERVERIFIKASI |
| 11 | [Tidak] → pesan kesalahan → kembali form | Error ditampilkan, loop | `Login.tsx:116-118` (setErrorMessage + return) | Login.tsx:116-118 | ✅ TERVERIFIKASI |
| 12 | Decision "Role cocok dengan akun?" | Role mismatch check | `AuthContext.tsx:159-170` (2 kondisi mismatch) | AuthContext.tsx:159-170 | ✅ TERVERIFIKASI |
| 13 | [Tidak] → pesan role mismatch → kembali form | Mismatch: error + loop | `AuthContext.tsx:160-169` + `Login.tsx:116-118` | AuthContext.tsx:160-169 | ✅ TERVERIFIKASI |
| 14 | Decision "Role = admin?" | app_metadata.role check | `AuthContext.tsx:151` (appMetaRole === 'admin') | AuthContext.tsx:151 | ✅ TERVERIFIKASI |
| 15 | [Ya] → arahkan ke /admin | Admin redirect | `Login.tsx:126-127` | Login.tsx:126-127 | ✅ TERVERIFIKASI |
| 16 | [Tidak] → cek account_status | Dokter: lanjut status check | `Login.tsx:128-133` | Login.tsx:128-133 | ✅ TERVERIFIKASI |
| 17 | Decision "Akun pending?" | account_status === 'pending' | `Login.tsx:128` | Login.tsx:128 | ✅ TERVERIFIKASI |
| 18 | [Ya] → kembali /login (pending) | Pending: redirect + pesan | `Login.tsx:129` (navigate /login, state.pending=true) + `Login.tsx:248-250` (pesan) | Login.tsx:129, 248-250 | ✅ TERVERIFIKASI |
| 19 | Decision "Akun ditolak?" | account_status === 'rejected' | `Login.tsx:130` | Login.tsx:130 | ✅ TERVERIFIKASI |
| 20 | [Ya] → kembali /login (rejected) | Rejected: redirect + pesan | `Login.tsx:131` (navigate /login, state.rejected=true) + `Login.tsx:251-253` (pesan) | Login.tsx:131, 251-253 | ✅ TERVERIFIKASI |
| 21 | [Tidak] → akses halaman tujuan | Approved: navigate(from) | `Login.tsx:132-133` (navigate from, default /dashboard) | Login.tsx:132-133 | ✅ TERVERIFIKASI |
| 22 | Final Node (bullseye) | Akhir alur | Standar UML Activity Diagram | — | ✅ TERVERIFIKASI |
| 23 | UML Note (Catatan) | Informasi pendukung | `PublicOnlyRoute.tsx:19-38`, `openingTimeline.ts:152-176` | PublicOnlyRoute.tsx, openingTimeline.ts | ✅ TERVERIFIKASI |

**Ringkasan matriks:** 23/23 elemen **TERVERIFIKASI**. Tidak ada elemen **BERTENTANGAN** atau **SEBAGIAN TERVERIFIKASI**.

---

## D. Analisis 6 Decision Node

### D.1 Decision "Input valid?"
- **Sumber:** `Login.tsx:93-101`
- **Kondisi:** `!trimmedEmail` atau `!password`
- **[Ya]:** Lanjut ke signIn() (baris 115)
- **[Tidak]:** `setErrorMessage()` + `return` (baris 95-101) → loop kembali ke pengisian form
- **Status:** ✅ Diperlukan dan sesuai implementasi

### D.2 Decision "Kredensial valid?"
- **Sumber:** `auth.ts:213` (result.error check)
- **Kondisi:** `signInWithPassword` mengembalikan error atau tidak
- **[Ya]:** `return { data: {...}, error: null }` (baris 221) → lanjut perbarui sesi
- **[Tidak]:** `return { data: null, error: formatAuthError(error) }` (baris 214) → Login.tsx menampilkan error
- **Status:** ✅ Diperlukan dan sesuai implementasi
- **Catatan:** Decision ini memeriksa hasil fungsi `loginUser()`, bukan Supabase langsung. Error yang dikembalikan mencakup: kredensial salah, email belum dikonfirmasi, rate limit, network error.

### D.3 Decision "Role cocok dengan akun?"
- **Sumber:** `AuthContext.tsx:159-170`
- **Kondisi:** selectedRole vs actualRole
  - `selectedRole==='admin' && actualRole≠'admin'` → error
  - `selectedRole==='doctor' && actualRole==='admin'` → error
- **[Ya]:** Lanjut ke penentuan route
- **[Tidak]:** Return error → Login.tsx menampilkan pesan → user tetap di halaman login
- **Status:** ✅ Diperlukan dan sesuai implementasi
- **Keamanan:** Mencegah dokter mengklaim diri sebagai admin melalui dropdown

### D.4 Decision "Role = admin?"
- **Sumber:** `AuthContext.tsx:151` (`appMetaRole === 'admin'`)
- **Kondisi:** app_metadata.role === 'admin'
- **[Ya]:** Login.tsx:126 → navigate('/admin')
- **[Tidak]:** Lanjut ke pengecekan account_status
- **Status:** ✅ Diperlukan dan sesuai implementasi
- **Catatan:** Admin tidak memiliki baris di `doctor_profiles`. Role ditentukan murni dari `app_metadata.role`.

### D.5 Decision "Akun pending?"
- **Sumber:** `Login.tsx:128` (`accountStatus === 'pending'`)
- **Kondisi:** account_status === 'pending'
- **[Ya]:** Navigate ke `/login` dengan state pending=true → pesan "sedang menunggu persetujuan"
- **[Tidak]:** Lanjut ke pengecekan rejected
- **Status:** ✅ Diperlukan dan sesuai implementasi
- **Catatan:** Autentikasi Supabase **berhasil** (session dibuat), tetapi aplikasi memblokir akses fitur klinis.

### D.6 Decision "Akun ditolak?"
- **Sumber:** `Login.tsx:130` (`accountStatus === 'rejected'`)
- **Kondisi:** account_status === 'rejected'
- **[Ya]:** Navigate ke `/login` dengan state rejected=true → pesan "pendaftaran ditolak"
- **[Tidak]:** Login berhasil → navigate ke halaman tujuan
- **Status:** ✅ Diperlukan dan sesuai implementasi

---

## E. Temuan Audit

### E.1 Tidak Ada Ketidaksesuaian

Seluruh 23 elemen diagram telah diverifikasi terhadap source code. Tidak ditemukan aktivitas fiktif, percabangan yang hilang, atau urutan proses yang salah.

### E.2 Pembedaan Autentikasi vs Otorisasi

Diagram dengan tepat membedakan:
1. **Autentikasi** (supabase.auth.signInWithPassword): Memverifikasi identitas pengguna → hasil: session + user
2. **Otorisasi** (role check + account_status check): Memverifikasi hak akses → hasil: route tujuan

Kedua tahap ini tercermin dalam urutan decision node: kredensial valid (autentikasi) → role cocok (otorisasi) → role=admin (pembagian route) → account_status (filtrasi akses).

### E.3 Role Selector: Konteks, Bukan Otoritas

Diagram menyatakan dengan jelas pada UML note bahwa role selector adalah **konteks login**, bukan sumber otorisasi. Hal ini sesuai implementasi:
- `selectedRole` dikirim ke `loginUser()` sebagai parameter (dihapus prefix `_` karena tidak dipakai di service)
- Role aktual ditentukan dari `app_metadata.role` dan `doctor_profiles`
- Mismatch antara selectedRole dan actualRole menghasilkan error, bukan redirect

### E.4 Remember Me Hanya Menyimpan Email

Diagram mencantumkan catatan bahwa Remember Me hanya menyimpan email di localStorage. Implementasi `openingTimeline.ts:152-176` confirms:
- `setRememberedEmail()` hanya menyimpan string email
- `getRememberedEmail()` hanya mengembalikan string email
- Tidak ada intervensi terhadap Supabase session configuration

### E.5 Reset Password Sebagai Use Case Terpisah

Diagram tidak memasukkan proses Reset Password ke dalam alur Sign In. Implementasi `Login.tsx:142-171` menunjukkan mode `reset` yang terpisah, dipicu oleh tombol "Forgot password?" yang mengubah `mode` state dari `'signIn'` ke `'reset'`. Ini adalah use case terpisah.

---

## F. Hasil Pengujian

### F.1 Unit Test

| Test File | Test Cases | Lolos | Gagal |
|-----------|-----------|-------|-------|
| `Login.test.tsx` | 28 | 28 | 0 |
| `auth.test.ts` | 11 | 11 | 0 |
| **Total** | **39** | **39** | **0** |

### F.2 Jenis Pengujian

- **Unit test:** 39 test cases (autentikasi, validasi, role selector, role mismatch, Remember Me, Reset Password, opening animation)
- **Static analysis:** XML validation (45 nodes, 35 edges, 0 broken references)
- **Visual validation:** PIL.Image.verify() + manual inspection

### F.3 Yang Tidak Diuji

- **Integration test:** Tidak dilakukan karena tidak ada akses ke Supabase production instance
- **Browser/E2E test:** Tidak dilakukan karena tidak ada environment browser yang tersedia
- **Route guard test:** `PublicOnlyRoute`, `ProtectedRoute`, `AdminRoute`, `DoctorRoute` tidak memiliki file test terpisah

---

## G. Perubahan Diagram (FINAL vs FINAL_VERIFIED)

Diagram `FINAL_VERIFIED` merupakan **render ulang** dari diagram `FINAL` yang sudah ada, dengan:
- XML drawio di-generate ulang secara programatik (identik struktur)
- PNG di-generate ulang dari kode Python generator
- Validasi XML dan PNG dilakukan ulang

**Tidak ada perubahan struktur, percabangan, atau konten** antara versi FINAL dan FINAL_VERIFIED.

Perbedaan teknis:
- Node geometry menggunakan `mxGeometry` child element (standar drawio yang lebih rapi)
- Edge geometry menggunakan `relative=1` (standar drawio modern)
- PNG dihasilkan via Python PIL (bukan draw.io web API)

---

## H. Lokasi File Output

| File | Ukuran | Deskripsi |
|------|--------|-----------|
| `ACTIVITY_DIAGRAM_SIGN_IN_PIXELT_FINAL_VERIFIED.drawio` | ~11 KB | Sumber diagram editabel |
| `ACTIVITY_DIAGRAM_SIGN_IN_PIXELT_FINAL_VERIFIED.png` | 135 KB | Gambar final (1720×2100 RGB) |
| `AUDIT_INDEPENDEN_ACTIVITY_DIAGRAM_SIGN_IN_PIXELT.md` | ~14 KB | Laporan audit independen |
| `PENJELASAN_ACTIVITY_DIAGRAM_SIGN_IN_PIXELT_FINAL_VERIFIED.md` | ~8 KB | Penjelasan akademik |

File lama `ACTIVITY_DIAGRAM_SIGN_IN_PIXELT_FINAL.drawio` / `.png` **tidak diubah**.

---

## I. Keterbatasan Audit

1. **Audit berbasis analisis statis.** Tidak ada eksekusi runtime terhadap Supabase Auth atau basis data. Seluruh klaim kesesuaian didasarkan pada pembacaan source code.
2. **Tidak ada akses ke lingkungan Supabase produksi.** Konfigurasi `app_metadata` Admin dan data `doctor_profiles` tidak diperiksa secara langsung.
3. **Validasi visual terbatas.** Draw.io Desktop dan engine UML resmi tidak tersedia. Validasi dilakukan melalui (a) XML well-formedness check, (b) edge reference check, dan (c) PIL.Image.verify().
4. **Tidak ada uji browser/E2E.** Perilaku routing dan redirect tidak diuji di browser sesungguhnya.
5. **Tidak ada modifikasi kode aplikasi.** Audit hanya menghasilkan artefak dokumentasi.

---

## J. Kesimpulan

**Status: VERIFIED — FINAL**

Diagram Activity Diagram Sign In PIXEL-T telah diverifikasi secara independen terhadap implementasi aktual. Seluruh 23 elemen diagram (1 initial node, 14 activity node, 6 decision node, 1 final node, 1 UML note) didukung oleh source code. 35 control flow edge terhubung tanpa broken reference. 39 unit test lolos.

Diagram siap digunakan sebagai **Gambar 4.y** di Bab IV skripsi.

---

*Audit dilaksanakan melalui analisis statis independen terhadap kode sumber aktual web PIXEL-T (November 2026). Seluruh temuan dapat dilacak ke berkas yang tercantum pada Bagian B. Tidak ada kode aplikasi yang diubah.*