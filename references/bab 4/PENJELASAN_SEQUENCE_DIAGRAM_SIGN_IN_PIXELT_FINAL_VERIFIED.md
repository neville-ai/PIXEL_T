# PENJELASAN SEQUENCE DIAGRAM SIGN IN PIXEL-T FINAL VERIFIED

**Dokumen Pendukung Bab IV Skripsi S1**

---

## 1. Tujuan Diagram

Sequence Diagram Sign In PIXEL-T memodelkan interaksi antar komponen sistem saat pengguna melakukan masuk ke aplikasi. Diagram ini menggambarkan komunikasi antara aktor (pengguna), halaman login, konteks autentikasi, layanan autentikasi, Supabase Auth, dan database profil dokter.

Diagram dibuat berdasarkan audit independen terhadap implementasi source code aktual, bukan berdasarkan asumsi desain teoretis.

---

## 2. Aktor dan Lifeline

Diagram melibatkan enam lifeline yang masing-masing memiliki tanggung jawab spesifik:

### 2.1 User (Aktor)
Aktor eksternal yang memulai proses sign in dengan membuka halaman `/login` dan mengisi formulir.

### 2.2 Login Page (Login.tsx)
Komponen React yang menyajikan formulir sign in. Bertanggung jawab atas:
- Menampilkan formulir dengan field email, password, dan dropdown pemilihan role
- Melakukan validasi lokal sebelum mengirim data ke AuthContext
- Memanggil fungsi `signIn()` dari AuthContext
- Menangani hasil autentikasi dan melakukan navigasi ke halaman tujuan

### 2.3 AuthContext (AuthContext.tsx)
Context provider yang mengelola state autentikasi aplikasi. Bertanggung jawab atas:
- Menerima kredensial dari Login Page
- Memanggil AuthService untuk otentikasi
- Menyelesaikan role berdasarkan `app_metadata.role` dan `doctor_profiles`
- Memeriksa kecocokan role yang dipilih dengan role aktual
- Memeriksa account status (pending/approved/rejected) untuk akun dokter
- Mengembalikan hasil ke Login Page

### 2.4 AuthService (auth.ts)
Layanan yang membungkus operasi autentikasi Supabase. Bertanggung jawab atas:
- Memanggil `signInWithPassword()` dari Supabase Auth
- Mengambil metadata pengguna (termasuk role dari `app_metadata`)
- Mengambil profil dokter dari tabel `doctor_profiles`
- Memformat pesan kesalahan agar mudah dibaca pengguna

### 2.5 Supabase Auth
Layanan autentikasi berbasis JWT yang dikelola oleh Supabase. Bertanggung jawab atas:
- Memverifikasi kredensial email dan password
- Membuat session autentikasi
- Mengembalikan user object dan session token

### 2.6 doctor_profiles (Database)
Tabel PostgreSQL `public.doctor_profiles` yang menyimpan data profil dokter. Bertanggung jawab atas:
- Menyimpan role aktual dokter
- Menyimpan account_status (pending/approved/rejected)
- Menjadi sumber kebenaran untuk otorisasi akses dokter

---

## 3. Urutan Interaksi

### 3.1 Pembukaan Halaman

Proses dimulai ketika pengguna membuka halaman `/login`. Login Page merespons dengan menampilkan formulir sign in yang berisi field email, password, dan dropdown pemilihan konteks role (Admin atau Dokter).

### 3.2 Submit dan Validasi

Pengguna mengisi kredensial lalu menekan tombol Sign In. Login Page menjalankan validasi lokal:
1. Memastikan email tidak kosong
2. Memastikan password tidak kosong
3. Memastikan format email valid

Jika validasi gagal, pesan error ditampilkan langsung tanpa memanggil AuthContext.

### 3.3 Autentikasi

Setelah validasi lolos, Login Page memanggil `signIn(email, password, selectedRole)` dari AuthContext. Rantai pemanggilan berlanjut:
1. AuthContext memanggil `loginUser(email, password)` dari AuthService
2. AuthService memanggil `signInWithPassword(email, password)` ke Supabase Auth
3. Supabase Auth memverifikasi kredensial dan mengembalikan `{ user, session }`
4. AuthService mengembalikan result ke AuthContext
5. AuthContext memperbarui state session dan user

### 3.4 Penyelesaian Role

Setelah autentikasi berhasil, AuthContext melakukan penyelesaian role:
- Role Admin diambil dari `app_metadata.role` pada user object Supabase
- Role Dokter diambil dari query ke tabel `doctor_profiles`

### 3.5 Pemeriksaan Account Status

Untuk akun dengan selectedRole = dokter, AuthContext memeriksa `account_status` dari `doctor_profiles`:
- **Pending**: akun menunggu persetujuan admin
- **Approved**: akun telah disetujui dan dapat mengakses sistem
- **Rejected**: akun ditolak dan tidak dapat masuk

### 3.6 Pemeriksaan Role Mismatch

AuthContext membandingkan `selectedRole` dengan role aktual. Jika tidak cocok (misalnya pengguna memilih "Admin" padahal akunnya adalah Dokter), sistem mengembalikan error "Jenis akun tidak sesuai" dan pengguna tetap di halaman login.

### 3.7 Navigasi

Berdasarkan role dan status akun, Login Page mengarahkan pengguna:
- **Admin** → `/admin`
- **Dokter approved** → `/dashboard`
- **Dokter pending** → kembali ke `/login` dengan pesan penolakan
- **Dokter rejected** → kembali ke `/login` dengan pesan penolakan

---

## 4. Fragment Kombinasi

### 4.1 Fragment `alt` Pertama: Kredensial Valid / Tidak Valid

Fragment ini memisahkan dua kemungkinan hasil autentikasi:
- **[alt] kredensial valid**: Supabase Auth menerima kredensial, session dibuat
- **[else] kredensial tidak valid**: kredensial salah atau email belum dikonfirmasi

### 4.2 Fragment `alt` Kedua: Navigasi Berdasarkan Role dan Status

Fragment ini memisahkan empat jalur navigasi:
- **Admin** dialihkan ke `/admin`
- **Dokter approved** dialihkan ke `/dashboard`
- **Dokter pending** dikembalikan ke `/login`
- **Dokter rejected** dikembalikan ke `/login`
- **Role mismatch** ditampilkan pesan error

---

## 5. Catatan Penting

1. **Tidak ada integrasi Flask API** — seluruh autentikasi dilakukan langsung melalui Supabase Auth, tidak ada panggilan ke backend Flask.

2. **Role Admin bersifat server-write-only** — nilai `app_metadata.role` ditulis oleh server dan tidak dapat diubah oleh klien. Ini adalah mekanisme keamanan untuk mencegah pengguna memanipulasi role melalui dropdown.

3. **Role Dokter berasal dari database** — tabel `doctor_profiles` adalah sumber kebenaran tunggal untuk role dan status akun dokter.

4. **Remember My Email** — fitur ini hanya menyimpan alamat email di `localStorage`. Fitur ini tidak memengaruhi durasi session Supabase maupun mekanisme autentikasi.

5. **Reset Password** — merupakan use case terpisah yang tidak digambarkan dalam Sequence Diagram Sign In ini.

---

## 6. Konsistensi dengan Diagram Lain

Diagram ini konsisten dengan Activity Diagram Sign In PIXEL-T FINAL VERIFIED yang telah diaudit sebelumnya. Kedua diagram menggambarkan alur yang sama dari perspektif berbeda:
- **Activity Diagram**: fokus pada urutan aktivitas dan keputusan
- **Sequence Diagram**: fokus pada komunikasi antar komponen

Kedua diagram saling melengkapi dan dapat digunakan bersama dalam Bab IV skripsi.
