# PENJELASAN SEQUENCE DIAGRAM SIGN IN PIXEL-T FINAL AUDITED

**Dokumen Pendukung Bab IV Skripsi S1**

---

## 1. Tujuan Diagram

Sequence Diagram Sign In PIXEL-T memodelkan interaksi antar komponen sistem saat pengguna melakukan masuk ke aplikasi. Diagram ini menggambarkan komunikasi antara aktor (pengguna), halaman login, konteks autentikasi, layanan autentikasi, Supabase Auth, dan database profil dokter.

Diagram dibuat berdasarkan audit independen terhadap implementasi source code aktual, bukan berdasarkan asumsi desain teoretis. Seluruh interaksi dalam diagram telah diverifikasi terhadap source code yang tersedia di repository PIXEL-T.

---

## 2. Aktor dan Lifeline

Diagram melibatkan enam lifeline yang masing-masing memiliki tanggung jawab spesifik:

### 2.1 User (Aktor)
Aktor eksternal yang memulai proses sign in dengan membuka halaman `/login` dan mengisi formulir. User berinteraksi dengan sistem melalui tiga peristiwa utama: membuka halaman, menampilkan formulir, dan submitting kredensial.

### 2.2 Login Page (Login.tsx)
Komponen React yang menyajikan formulir sign in. Bertanggung jawab atas:
- Menampilkan formulir dengan field email, password, dan dropdown pemilihan role
- Melakukan validasi lokal sebelum mengirim data ke AuthContext
- Memanggil fungsi `signIn()` dari AuthContext
- Menangani hasil autentikasi dan melakukan navigasi ke halaman tujuan

Validasi lokal dilakukan sebelum autentikasi diproses. Jika email atau password kosong, pesan error ditampilkan langsung tanpa memanggil AuthContext.

### 2.3 AuthContext (AuthContext.tsx)
Context provider yang mengelola state autentikasi aplikasi. Bertanggung jawab atas:
- Menerima kredensial dari Login Page
- Memanggil AuthService untuk otentikasi
- Menyelesaikan role berdasarkan `app_metadata.role` dan `doctor_profiles`
- Memeriksa kecocokan role yang dipilih dengan role aktual
- Memeriksa account status (pending/approved/rejected) untuk akun dokter
- Mengembalikan hasil ke Login Page

AuthContext merupakan komponen sentral yang menghubungkan Login Page dengan AuthService dan database profil dokter.

### 2.4 AuthService (auth.ts)
Layanan yang membungkus operasi autentikasi Supabase. Bertanggung jawab atas:
- Memanggil `signInWithPassword()` dari Supabase Auth
- Mengambil metadata pengguna (termasuk role dari `app_metadata`)
- Mengambil profil dokter dari tabel `doctor_profiles`
- Memformat pesan kesalahan agar mudah dibaca pengguna

AuthService bertindak sebagai abstraction layer antara AuthContext dan Supabase Auth SDK.

### 2.5 Supabase Auth
Layanan autentikasi berbasis JWT yang dikelola oleh Supabase. Bertanggung jawab atas:
- Memverifikasi kredensial email dan password
- Membuat session autentikasi
- Mengembalikan user object dan session token

Supabase Auth adalah satu-satunya sumber otentikasi dalam alur Sign In PIXEL-T. Tidak ada panggilan ke backend Flask API.

### 2.6 doctor_profiles (Database)
Tabel PostgreSQL `public.doctor_profiles` yang menyimpan data profil dokter. Bertanggung jawab atas:
- Menyimpan role aktual dokter
- Menyimpan account_status (pending/approved/rejected)
- Menjadi sumber kebenaran untuk otorisasi akses dokter

Query ke tabel ini dilakukan menggunakan `.maybeSingle()` yang mengembalikan null jika baris tidak ditemukan, berbeda dengan `.single()` yang akan melempar error.

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

Setelah autentikasi berhasil, AuthContext melakukan penyelesaian role secara berurutan:
1. Mengecek `app_metadata.role` dari user object Supabase (sumber terpercaya untuk Admin)
2. Jika bukan Admin, melakukan query ke `doctor_profiles` untuk mendapatkan role dan account_status

Pendekatan ini memastikan Admin diidentifikasi dengan benar meskipun mereka tidak memiliki baris di tabel `doctor_profiles`.

### 3.5 Pemeriksaan Account Status

Untuk akun dengan selectedRole = dokter, AuthContext memeriksa `account_status` dari `doctor_profiles`:
- **Pending**: akun menunggu persetujuan admin
- **Approved**: akun telah disetujui dan dapat mengakses sistem
- **Rejected**: akun ditolak dan tidak dapat masuk

### 3.6 Pemeriksaan Role Mismatch

AuthContext membandingkan `selectedRole` dengan role aktual. Jika tidak cocok (misalnya pengguna memilih "Admin" padahal akunnya adalah Dokter), sistem mengembalikan error "Jenis akun tidak sesuai dengan hak akses akun Anda. Silakan pilih jenis akun yang benar."

Pemeriksaan ini merupakan mekanisme keamanan untuk mencegah pengguna berpura-pura menjadi role yang bukan miliknya.

### 3.7 Navigasi

Berdasarkan role dan status akun, Login Page mengarahkan pengguna:
- **Admin** → `/admin`
- **Dokter approved** → `/dashboard`
- **Dokter pending** → kembali ke `/login` dengan flag `pending: true`
- **Dokter rejected** → kembali ke `/login` dengan flag `rejected: true`
- **Default** → `/dashboard` (berdasarkan `location.state.from`)

---

## 4. Fragment Kombinasi

### 4.1 Fragment `alt` Pertama: Kredensial Valid / Tidak Valid

Fragment ini memisahkan dua kemungkinan hasil autentikasi:
- **[alt] kredensial valid**: Supabase Auth menerima kredensial, session dibuat
- **[else] kredensial tidak valid**: kredensial salah atau email belum dikonfirmasi

### 4.2 Fragment `alt` Kedua: Role Cocok / Role Mismatch

Fragment ini memisahkan dua kondisi pemeriksaan role:
- **[alt] role cocok**: selectedRole sesuai dengan actualRole
- **[else] role mismatch**: selectedRole tidak sesuai dengan actualRole → tampilkan error

### 4.3 Fragment `alt` Ketiga: Navigasi Berdasarkan Role dan Status

Fragment ini memisahkan lima jalur navigasi:
- **Admin** dialihkan ke `/admin`
- **Dokter approved** dialihkan ke `/dashboard`
- **Dokter pending** dikembalikan ke `/login` dengan state pending
- **Dokter rejected** dikembalikan ke `/login` dengan state rejected
- **Default** dialihkan ke halaman tujuan dari state

---

## 5. Catatan Penting

1. **Tidak ada integrasi Flask API** — seluruh autentikasi dilakukan langsung melalui Supabase Auth, tidak ada panggilan ke backend Flask.

2. **Role Admin bersifat server-write-only** — nilai `app_metadata.role` ditulis oleh server dan tidak dapat diubah oleh klien. Ini adalah mekanisme keamanan untuk mencegah pengguna memanipulasi role melalui dropdown.

3. **Role Dokter berasal dari database** — tabel `doctor_profiles` adalah sumber kebenaran tunggal untuk role dan status akun dokter.

4. **Remember My Email** — fitur ini hanya menyimpan alamat email di `localStorage`. Fitur ini tidak memengaruhi durasi session Supabase maupun mekanisme autentikasi.

5. **Validasi input sebelum autentikasi** — validasi lokal (email kosong, password kosong) terjadi sebelum panggilan ke AuthContext. Ini mengurangi beban server dan memberikan feedback instan kepada pengguna.

6. **Reset Password** — merupakan use case terpisah yang tidak digambarkan dalam Sequence Diagram Sign In ini. Fungsi `resetPasswordUser()` dipanggil secara independen melalui route `/reset-password`.

---

## 6. Konsistensi dengan Diagram Lain

Diagram ini konsisten dengan Activity Diagram Sign In PIXEL-T FINAL AUDITED yang telah diaudit sebelumnya. Kedua diagram menggambarkan alur yang sama dari perspektif berbeda:
- **Activity Diagram**: fokus pada urutan aktivitas dan keputusan
- **Sequence Diagram**: fokus pada komunikasi antar komponen

Kedua diagram saling melengkapi dan dapat digunakan bersama dalam Bab IV skripsi.

---

## 7. Rekomendasi Penulisan Bab IV

Dalam Bab IV skripsi, Sequence Diagram ini dapat digunakan sebagai Gambar 4.x untuk mendeskripsikan proses autentikasi pengguna. Penjelasan harus mencakup:
1. Peran masing-masing lifeline
2. Urutan autentikasi dan role resolution
3. Mekanisme keamanan role mismatch
4. Perbedaan penanganan navigasi berdasarkan role dan status akun

Gunakan bahasa formal, objektif, dan konsisten dengan gaya penulisan Bab IV LUCIT.
