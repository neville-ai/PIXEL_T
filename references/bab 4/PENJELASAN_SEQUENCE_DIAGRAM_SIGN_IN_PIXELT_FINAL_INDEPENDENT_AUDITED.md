# PENJELASAN SEQUENCE DIAGRAM SIGN IN PIXEL-T — FINAL INDEPENDENT AUDITED

---

## 1. Tujuan Diagram

Sequence Diagram Sign In PIXEL-T menggambarkan interaksi antara pengguna dan sistem autentikasi pada aplikasi web PIXEL-T. Diagram ini menunjukkan alur lengkap mulai dari pengguna membuka halaman login, memasukkan kredensial, proses autentikasi oleh Supabase Auth, penentuan role pengguna, hingga navigasi ke halaman tujuan yang sesuai.

Diagram ini dibuat berdasarkan audit independen terhadap seluruh source code yang terlibat dalam proses Sign In, sehingga merepresentasikan implementasi aktual aplikasi PIXEL-T.

---

## 2. Aktor dan Lifeline

Diagram Sign In PIXEL-T menggunakan **6 lifeline** yang terdiri dari:

| Lifeline | Peran | Keterangan |
|----------|-------|------------|
| **User** | Aktor eksternal | Pengguna yang melakukan Sign In |
| **Login Page** | Komponen frontend (`Login.tsx`) | Halaman formulir Sign In |
| **AuthContext** | Context React (`AuthContext.tsx`) | Pengelola session dan state autentikasi |
| **AuthService** | Service layer (`auth.ts`) | Layer bisnis autentikasi |
| **Supabase Auth** | Layanan eksternal | Provider autentikasi berbasis JWT |
| **doctor_profiles (DB)** | Database PostgreSQL | Tabel profil dokter di Supabase |

---

## 3. Urutan Interaksi Sign In

Diagram Sign In PIXEL-T terdiri dari **13 interaksi** yang tersusun dalam tiga tahap utama:

### Tahap 1: Inisialisasi dan Input (Interaksi 1–4)

1. **User membuka halaman `/login`** — Pengguna mengakses URL `/login` melalui browser.
2. **Login Page menampilkan formulir** — Halaman Login merender form dengan field email, password, dan role selector.
3. **User submit kredensial** — Pengguna mengisi email, password, dan memilih role (admin/dokter), kemudian menekan tombol Sign In.
4. **Login Page memvalidasi input** — Validasi lokal dilakukan sebelum autentikasi:
   - Email tidak boleh kosong
   - Password tidak boleh kosong
   - Jika validasi gagal, pesan error ditampilkan dan proses berhenti

### Tahap 2: Autentikasi (Interaksi 5–9)

5. **Login Page memanggil `signIn()` di AuthContext** — Form yang tervalidasi diteruskan ke AuthContext bersama role yang dipilih pengguna.
6. **AuthContext memanggil `loginUser()` di AuthService** — AuthContext delegasikan proses autentikasi ke service layer.
7. **AuthService memanggil `signInWithPassword()` di Supabase Auth** — Kredensial dikirim ke Supabase untuk verifikasi.
8. **Supabase Auth mengembalikan `{ user, session }`** — Jika kredensial valid, Supabase Auth mengembalikan objek user dan session (JWT token).
9. **AuthService mengembalikan `{ data, error: null }` ke AuthContext** — Response diproses dan diteruskan ke AuthContext.

### Tahap 3: Role Resolution dan Navigasi (Interaksi 10–13)

10. **AuthContext melakukan resolve role secara internal** — Role ditentukan berdasarkan:
    - Untuk Admin: dibaca dari `app_metadata.role` pada JWT token (sumber tepercaya, server-write-only)
    - Untuk Dokter: dibaca dari tabel `doctor_profiles` di database
11. **AuthContext querying `doctor_profiles`** — Query dilakukan untuk mendapatkan `role` dan `account_status` berdasarkan `user_id`.
12. **Database mengembalikan `{ role, accountStatus }`** — Hasil query diterima oleh AuthContext.
13. **AuthContext mengembalikan `{ error?: string }` ke Login Page** — Response berisi error (jika ada) atau undefined (jika berhasil).

---

## 4. Fragment `alt` dan Percabangan

Diagram Sign In memiliki **3 fragment `alt`** yang merepresentasikan kondisi percabangan:

### Fragment 1: Kredensial Valid / Tidak Valid

- **Kondisi `[alt] kredensial valid`**: Supabase Auth berhasil mengautentikasi kredensial → proses berlanjut ke tahap role resolution.
- **Kondisi `[else] kredensial salah`**: Supabase Auth menolak kredensial → pesan error ditampilkan, pengguna tetap di halaman `/login`.

### Fragment 2: Role Cocok / Role Mismatch

- **Kondisi `[alt] role cocok`**: Role yang dipilih pengguna sesuai dengan role aktual → lanjut ke navigasi.
- **Kondisi `[else] role mismatch`**: Role yang dipilih berbeda dengan role aktual → error ditampilkan, pengguna tetap di `/login`.

> **Catatan penting:** Role mismatch terjadi ketika pengguna memilih konteks yang salah. Misalnya, pengguna dengan role Admin tetapi memilih "dokter" pada role selector, atau sebaliknya.

### Fragment 3: Navigasi Berdasarkan Role dan Status Akun

Fragment ini memiliki **5 kondisi navigasi**:

| Kondisi | Tujuan Navigasi | Keterangan |
|---------|-----------------|------------|
| Admin | `/admin` | Dashboard administrator |
| Dokter approved | `/dashboard` | Dashboard klinis dokter |
| Dokter pending | `/login` (state: `{pending: true}`) | Akun masih menunggu persetujuan |
| Dokter rejected | `/login` (state: `{rejected: true}`) | Akun ditolak, perlu menghubungi admin |
| Default | `from` (halaman sebelumnya) | Mengembalikan ke halaman yang diminta sebelumnya |

---

## 5. Penentuan Role

PIXEL-T menggunakan dua sumber penentuan role yang berbeda:

### Role Admin
- **Sumber:** `app_metadata.role` pada JWT token
- **Sifat:** Server-write-only, tidak dapat dimodifikasi oleh client
- **Keamanan:** Nilai ini ditetapkan oleh administrator melalui Supabase Admin API
- **Fungsi:** `getAdminRoleFromAppMetadata()` di `auth.ts`

### Role Dokter
- **Sumber:** Kolom `role` pada tabel `doctor_profiles`
- **Sifat:** Data relasional yang terhubung dengan `auth.users` melalui `user_id`
- **Query:** `SELECT role, account_status FROM doctor_profiles WHERE user_id = ?`
- **Fungsi:** `fetchUserProfileStatus()` di `auth.ts`

---

## 6. Status Akun Dokter

Tabel `doctor_profiles` memiliki kolom `account_status` yang menentukan akses dokter:

| Status | Akses | Keterangan |
|--------|-------|------------|
| `pending` | Dibatasi | Akun baru, menunggu persetujuan admin |
| `approved` | Penuh | Akun aktif, dapat mengakses fitur klinis |
| `rejected` | Ditolak | Akun ditolak, tidak dapat login |

Status ini diperiksa selama proses Sign In dan menentukan ke mana pengguna diarahkan setelah autentikasi berhasil.

---

## 7. Remember Me

Fitur "Remember my email" pada halaman Login **hanya menyimpan alamat email** di `localStorage`. Fitur ini:

- **TIDAK** menyimpan token sesi
- **TIDAK** menyimpan password
- **TIDAK** otomatis mengautentikasi pengguna
- Hanya mempermudah pengisian form pada kunjungan berikutnya

---

## 8. Reset Password

Reset Password merupakan **use case terpisah** yang tidak termasuk dalam alur Sign In utama. Proses Reset Password menggunakan fungsi `resetPasswordUser()` yang memanggil `supabase.auth.resetPasswordForEmail()`.

---

## 9. Arsitektur Autentikasi

PIXEL-T menggunakan **Supabase Auth** sebagai provider autentikasi utama. Arsitektur autentikasi terdiri dari:

```
User → Login Page → AuthContext → AuthService → Supabase Auth
                                      ↓
                              doctor_profiles (DB)
```

Karakteristik autentikasi PIXEL-T:

1. **Tidak ada middleware Flask** — Autentikasi langsung ke Supabase Auth
2. **JWT-based session** — Session dikelola melalui JWT token
3. **Role separation** — Admin dan Dokter memiliki sumber role berbeda
4. **Role mismatch protection** — Validasi konsistensi role yang dipilih vs role aktual
5. **Account status enforcement** — Status akun diperiksa sebelum akses diberikan

---

## 10. Catatan Penting

- Diagram ini konsisten dengan Sequence Diagram Sign Up PIXEL-T FINAL_AUDITED
- Semua interaksi telah diverifikasi terhadap source code aktual
- 41 unit tests berlulus untuk komponen terkait
- Diagram siap digunakan sebagai referensi Bab IV skripsi
