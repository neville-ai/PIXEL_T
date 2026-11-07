# PENJELASAN SEQUENCE DIAGRAM SIGN UP PIXEL-T FINAL AUDITED

**Dokumen Pendukung Bab IV Skripsi S1**

---

## 1. Tujuan Diagram

Sequence Diagram Sign Up PIXEL-T memodelkan interaksi antar komponen sistem saat pengguna mendaftarkan akun baru. Diagram ini menggambarkan komunikasi antara aktor (pengguna), halaman registrasi, konteks autentikasi, layanan autentikasi, dan layanan autentikasi Supabase.

Diagram dibuat berdasarkan audit independen terhadap implementasi source code aktual. Seluruh interaksi dalam diagram telah diverifikasi terhadap source code yang tersedia di repository PIXEL-T.

---

## 2. Aktor dan Lifeline

Diagram melibatkan lima lifeline yang masing-masing memiliki tanggung jawab spesifik:

### 2.1 User (Aktor)
Aktor eksternal yang memulai proses registrasi dengan membuka halaman `/register` dan mengisi formulir pendaftaran. User berinteraksi dengan sistem melalui tiga peristiwa utama: membuka halaman, mengisi dan.submit data formulir, serta menerima hasil registrasi.

### 2.2 Register Page (Register.tsx)
Komponen React yang menyajikan formulir pendaftaran. Bertanggung jawab atas:
- Menampilkan formulir dengan enam field: nama lengkap, email, nama rumah sakit, bidang keahlian, kata sandi, dan konfirmasi kata sandi
- Melakukan validasi lokal sebelum mengirim data ke AuthContext
- Memanggil fungsi `signUp()` dari AuthContext
- Menampilkan hasil registrasi (berhasil atau gagal)

Validasi lokal dilakukan sebelum autentikasi diproses. Jika validasi gagal, pesan error ditampilkan langsung tanpa memanggil AuthContext.

### 2.3 AuthContext (AuthContext.tsx)
Context provider yang mengelola state autentikasi aplikasi. Bertanggung jawab atas:
- Menerima data registrasi dari Register Page
- Memanggil AuthService untuk mendaftar akun baru
- Memperbarui session jika Supabase Auth mengembalikan session
- Mengambil profil dokter dari database jika session tersedia
- Mengembalikan hasil registrasi ke Register Page

### 2.4 AuthService (auth.ts)
Layanan yang membungkus operasi autentikasi Supabase. Bertanggung jawab atas:
- Memanggil `auth.signUp()` dari Supabase Auth
- Mengirim metadata profesional (nama, rumah sakit, spesialisasi) melalui parameter `options.data`
- Memformat pesan kesalahan agar mudah dibaca pengguna
- Mendeteksi kondisi email confirmation melalui anti-enumeration placeholder

AuthService bertindak sebagai abstraction layer antara AuthContext dan Supabase Auth SDK.

### 2.5 Supabase Auth
Layanan autentikasi berbasis JWT yang dikelola oleh Supabase. Bertanggung jawab atas:
- Menerima data registrasi dari AuthService
- Membuat record baru di tabel `auth.users`
- Memicu trigger database `handle_new_doctor_signup()` secara otomatis
- Mengembalikan user dan session (jika email confirmation disabled)

Supabase Auth juga memicu trigger database secara internal setelah insert berhasil. Trigger ini menciptakan baris di tabel `doctor_profiles` dengan `role='doctor'` dan `account_status='pending'`. Karena proses ini merupakan mekanisme internal database dan tidak dipanggil langsung oleh aplikasi, trigger digambarkan sebagai self-message pada lifeline Supabase Auth.

---

## 3. Urutan Interaksi

### 3.1 Pembukaan Halaman

Proses dimulai ketika pengguna membuka halaman `/register`. Register Page merespons dengan menampilkan formulir pendaftaran yang berisi enam field wajib dan tombol "Daftar".

### 3.2 Submit dan Validasi

Pengguna mengisi semua field lalu menekan tombol "Daftar". Register Page menjalankan validasi lokal secara berurutan:
1. Memastikan nama lengkap tidak kosong
2. Memastikan email tidak kosong
3. Memastikan format email valid
4. Memastikan nama rumah sakit tidak kosong
5. Memastikan bidang keahlian tidak kosong
6. Memastikan kata sandi tidak kosong
7. Memastikan panjang kata sandi minimal 6 karakter
8. Memastikan konfirmasi kata sandi cocok dengan kata sandi

Jika validasi gagal pada langkah mana pun, pesan error ditampilkan langsung dan proses dihentikan tanpa memanggil AuthContext.

### 3.3 Proses Registrasi

Setelah validasi lolos, Register Page memanggil `signUp()` dari AuthContext dengan lima parameter: email, password, nama lengkap, nama rumah sakit, dan bidang keahlian.

Rantai pemanggilan berlanjut:
1. AuthContext memanggil `registerUser()` dari AuthService
2. AuthService memanggil `auth.signUp()` ke Supabase Auth dengan metadata profesional
3. Supabase Auth membuat record di `auth.users`
4. Setelah insert berhasil, trigger database `handle_new_doctor_signup()` berjalan secara otomatis
5. Trigger menyisipkan baris ke `doctor_profiles` dengan `role='doctor'` dan `account_status='pending'`
6. Supabase Auth mengembalikan respons ke AuthService
7. AuthService memformat respons dan mengembalikan ke AuthContext

### 3.4 Penanganan Hasil Registrasi

AuthContext memproses respons dari AuthService:
- **Jika session tersedia**: AuthContext memperbarui state user, session, role, dan accountStatus. Kemudian mengembalikan pesan keberhasilan kepada Register Page.
- **Jika session null**: AuthContext mengembalikan pesan dengan flag `requiresEmailConfirmation=true`, menandakan bahwa akun telah dibuat tetapi memerlukan konfirmasi email sebelum dapat digunakan.

Register Page menerima hasil dari AuthContext dan menampilkannya:
- **Jika berhasil**: Register Page menampilkan kartu sukses dengan judul "Registrasi Berhasil" dan pesan yang sesuai
- **Jika gagal**: Register Page menampilkan banner error dengan pesan kesalahan yang telah diformat

### 3.5 Navigasi Setelah Registrasi

Setelah registrasi berhasil, Register Page menampilkan dua opsi kepada pengguna:
1. **Tombol "Masuk ke PIXEL-T"** — mengarahkan pengguna ke halaman `/login` untuk melakukan login manual
2. **Tombol "Daftar dengan akun lain"** — mengosongkan formulir untuk registrasi ulang

Tidak ada auto-redirect setelah registrasi. Pengguna secara eksplisit diarahkan untuk masuk melalui halaman login.

---

## 4. Fragment Kombinasi

### 4.1 Fragment `alt` Pertama: Session Tersedia / Tidak Tersedia

Fragment ini memisahkan dua kondisi respons dari Supabase Auth:
- **[alt] session tersedia**: Supabase Auth berhasil membuat akun dan menerbitkan session (email confirmation disabled)
- **[else] session null**: Supabase Auth membuat akun tetapi tidak menerbitkan session karena email confirmation diperlukan

Kondisi ini ditentukan oleh konfigurasi Supabase Auth project. Ketika email confirmation diaktifkan, Supabase akan mengembalikan user tanpa session.

### 4.2 Fragment `alt` Kedua: Registrasi Berhasil / Gagal

Fragment ini memisahkan dua kondisi umum:
- **[alt] registrasi berhasil**: tidak terdapat error dari `registerUser()`
  - Sistem menampilkan status berhasil kepada pengguna
- **[else] registrasi gagal**: terdapat error dari `registerUser()`
  - Sistem menampilkan pesan error pada formulir

Kegagalan registrasi dapat terjadi karena berbagai alasan, seperti email sudah terdaftar, kata sandi terlalu lemah, atau error jaringan.

### 4.3 Fragment `alt` Ketiga: Navigasi Berdasarkan Kondisi

Fragment ini memisahkan lima jalur respons berdasarkan kondisi:
- **Session tersedia** → login otomatis, redirect ke `/dashboard`
- **Session null** → `requiresEmailConfirmation=true`, tampilkan pesan cek email
- **Akun pending** → tampilkan info menunggu persetujuan admin
- **Autentikasi gagal** → tampilkan pesan error pada form
- **Redirect ke /login** → user harus login manual

---

## 5. Catatan Penting

1. **Tidak ada integrasi Flask API** — seluruh registrasi dilakukan langsung melalui Supabase Auth, tidak ada panggilan ke backend Flask.

2. **Profil dokter dibuat oleh trigger database** — tabel `doctor_profiles` diisi secara otomatis oleh trigger `handle_new_doctor_signup()` yang berjalan AFTER INSERT pada `auth.users`. Frontend tidak secara eksplisit membuat baris profil.

3. **Trigger bersifat fault-tolerant** — jika trigger gagal, proses registrasi tetap berhasil. Kegagalan hanya dicatat sebagai Postgres WARNING dan dapat diperbaiki melalui backfill migration.

4. **Akun Admin tidak dibuat melalui sign-up** — akun Admin dibuat secara manual menggunakan Supabase Admin API dengan menonaktifkan `app_metadata.role = 'admin'`. Trigger secara eksplisit mengecualikan akun Admin dari pembuatan profil dokter.

5. **Validasi input sebelum autentikasi** — validasi lokal (enam kondisi) terjadi sebelum panggilan ke AuthContext. Ini mengurangi beban server dan memberikan feedback instan kepada pengguna.

6. **Tidak ada auto-redirect** — setelah registrasi berhasil, pengguna tetap di halaman yang sama dan secara eksplisit diarahkan untuk masuk melalui halaman login.

7. **Metadata profesional disimpan sebagai auth metadata** — informasi rumah sakit dan bidang keahlian dokter disimpan di `user_metadata` Supabase Auth, bukan di tabel terpisah. Data ini tersedia untuk trigger database melalui `raw_user_meta_data`.

---

## 6. Konsistensi dengan Diagram Lain

Diagram ini konsisten dengan Sequence Diagram Sign In PIXEL-T FINAL_AUDITED yang telah diaudit sebelumnya. Kedua diagram menggunakan:
- Enam lifeline yang sama (dengan penyesuaian)
- Gaya visual yang sama (latar putih, garis hitam, tipografi Segoe UI)
- Notasi UML Sequence Diagram yang sama
- Fragment alt dengan struktur serupa
-Activation bar yang konsisten

Kedua diagram saling melengkapi dan dapat digunakan bersama dalam Bab IV skripsi.

---

## 7. Rekomendasi Penulisan Bab IV

Dalam Bab IV skripsi, Sequence Diagram ini dapat digunakan sebagai Gambar 4.x untuk mendeskripsikan proses pendaftaran akun pengguna. Penjelasan harus mencakup:
1. Peran masing-masing lifeline
2. Urutan validasi dan registrasi
3. Mekanisme trigger database untuk pembuatan profil
4. Perbedaan penanganan berdasarkan ketersediaan session
5. Tidak adanya auto-redirect setelah registrasi

Gunakan bahasa formal, objektif, dan konsisten dengan gaya penulisan Bab IV LUCIT.
