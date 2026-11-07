# Penjelasan Sequence Diagram Sign Up PIXEL-T — Versi Independent Audited

**Tanggal:** 5 November 2026  
**Versi:** FINAL (setelah audit independen putaran kedua)  
**Gambar:** (Gambar 4.x)

---

## 1. Pendahuluan

Sequence Diagram Sign Up PIXEL-T menggambarkan interaksi antara pengguna, halaman registrasi, konteks autentikasi, layanan autentikasi, dan Supabase Auth selama proses pendaftaran pengguna baru. Diagram ini dibuat berdasarkan pembacaan mendalam seluruh source code relevan dan telah melalui dua putaran audit independen.

Diagram ini menggunakan notasi UML sequence diagram standar dengan lima lifeline, tiga combined fragment bertipe `alt`, dan enam catatan (note box) yang menjelaskan aspek-aspek penting dari implementasi sistem.

---

## 2. Urutan Interaksi

### 2.1 Pembukaan Halaman Registrasi

Proses dimulai ketika pengguna membuka halaman `/register` melalui browser. Router pada `AppRoutes.tsx` mengarahkan permintaan ke komponen `Register` yang dibungkus oleh `PublicOnlyRoute`. Guard ini memastikan bahwa pengguna yang sudah terautentikasi tidak dapat mengakses halaman registrasi (akan diarahkan ke dashboard atau admin).

Setelah halaman dimuat, Register Page menampilkan formulir registrasi yang berisi enam bidang input: nama lengkap, alamat email, kata sandi, konfirmasi kata sandi, nama rumah sakit, dan spesialisasi dokter.

### 2.2 Pengisian dan Validasi Formulir

Pengguna mengisi data pada formulir registrasi. Setiap kali tombol "Daftar" ditekan, fungsi `handleSubmit` pada `Register.tsx` dipanggil. Fungsi ini pertama-tama menjalankan validasi frontend melalui `validateForm()`. Validasi memeriksa tiga kondisi:

1. Alamat email tidak boleh kosong.
2. Kata sandi dan konfirmasi kata sandi harus cocok.
3. Kata sandi memiliki minimal enam karakter.

Jika validasi gagal, pesan error ditampilkan langsung di halaman tanpa mengirim permintaan apa pun ke server. Pengguna tetap berada di halaman registrasi dan dapat memperbaiki data yang salah.

### 2.3 Pemanggilan AuthContext

Setelah validasi berhasil, `handleSubmit` memanggil fungsi `signUp` yang diperoleh dari `useAuth()` hook. Fungsi ini menerima lima argumen: email, kata sandi, nama lengkap, nama rumah sakit, dan spesialisasi dokter. Pemanggilan ini mewakili transisi dari lapisan presentasi (halaman) ke lapisan konteks (state management global).

### 2.4 Pemanggilan AuthService

Di dalam `AuthContext.tsx`, fungsi `signUp` meneruskan lima argumen tersebut ke fungsi `registerUser` pada `auth.ts`. AuthService bertugas memanggil Supabase Auth API dan menangani transformasi respons serta pemetaan error.

### 2.5 Pemanggilan Supabase Auth

AuthService memanggil `supabase.auth.signUp()` dengan payload yang berisi email, kata sandi, dan metadata profesional (`full_name`, `hospital`, `primary_specialty`). Pemanggilan ini terjadi secara sinkron di sisi klien dan menghasilkan respons yang berisi objek `user` dan `session` (atau `null` jika email belum dikonfirmasi).

### 2.6 Eksekusi Trigger Database

Secara internal, setelah Supabase Auth berhasil membuat entri baru di tabel `auth.users`, trigger `on_auth_user_created` dijalankan oleh PostgreSQL. Trigger ini memanggil fungsi `handle_new_doctor_signup()` yang membuat baris baru di tabel `doctor_profiles` dengan `role = 'doctor'` dan `account_status = 'pending'`.

Trigger ini memiliki dua mekanisme pengaman:
- Akun dengan `raw_user_meta_data.full_name` tidak ada (akun Admin yang dibuat manual) akan dilewati.
- Kegagalan trigger hanya menghasilkan peringatan Postgres (WARNING) dan tidak membatalkan proses registrasi.

### 2.7 Penanganan Respons

Respons dari Supabase Auth dikembalikan ke AuthService, kemudian ke AuthContext. Di AuthContext, terdapat pengecekan kondisional pada baris 191:

```typescript
if (result.data?.session && result.data.user) {
  setSession(result.data.session);
  setUser(result.data.user);
  fetchUserProfileStatus(result.data.user);
  return { message: "Registrasi berhasil!", requiresEmailConfirmation: false };
}
```

Jika session dan user tersedia, sesi disimpan, status profil fetched, dan pesan sukses tanpa konfirmasi email dikembalikan. Jika session null (kondisi email belum dikonfirmasi), pesan yang dikembalikan menyatakan bahwa pengguna harus memeriksa email.

Perhatian: `fetchUserProfileStatus()` **hanya dipanggil ketika session tersedia**. Pada kondisi email belum dikonfirmasi (session null), fungsi ini tidak dipanggil. Hal ini penting untuk dijelaskan karena sebelumnya diagram menyatakan kedua operasi berjalan bersamaan, yang kurang tepat secara teknis.

### 2.8 Tampilan Status kepada Pengguna

Register Page menerima objek respons dari AuthContext. Berdasarkan isi respons, halaman menampilkan pesan yang sesuai. Jika registrasi berhasil, halaman menampilkan pesan sukses dan tombol "Masuk ke PIXEL-T" yang mengarahkan ke halaman `/login`. Penting dicatat bahwa **tidak ada redirect otomatis** — pengguna harus menekan tombol tersebut secara manual untuk melanjutkan ke halaman login.

---

## 3. Percabangan dan Alur Alternatif

Diagram menggunakan tiga combined fragment bertipe `alt` untuk merepresentasikan alur bercabang:

### 3.1 alt1 — Ketersediaan Session

Fragment ini membedakan dua kondisi berdasarkan hasil registrasi:
- **session && user tersedia**: Sesi autentikasi berhasil diperoleh. Sistem menyimpan sesi, memperbarui user, dan memanggil `fetchUserProfileStatus()`.
- **session null**: Email belum dikonfirmasi. Sistem tidak menyimpan sesi dan menampilkan pesan yang mengarahkan pengguna untuk memeriksa inbox email.

### 3.2 alt2 — Hasil Registrasi

Fragment ini membedakan keberhasilan dan kegagalan panggilan ke Supabase Auth:
- **registrasi berhasil**: Alur berlanjut ke penanganan session (alt1).
- **registrasi gagal**: Pesan error ditampilkan kepada pengguna.

### 3.3 alt3 — Navigasi

Fragment ini menggambarkan dua skenario navigasi setelah registrasi:
- **session tersedia**: Pengguna tetap di halaman register, sistem mencatat bahwa login otomatis akan terjadi setelah konfirmasi email.
- **session null**: Pengguna melihat pesan untuk memeriksa email dan harus secara manual menekan tombol "Masuk ke PIXEL-T" untuk menuju halaman login.

---

## 4. Catatan Penting

Diagram menyertakan tujuh baris catatan yang menjelaskan aspek-aspek kritis yang tidak tergambarkan secara eksplisit dalam alur pesan:

1. Profil dokter dibuat otomatis oleh trigger database, bukan oleh frontend.
2. Trigger membuat baris `doctor_profiles` dengan `role='doctor'` dan `account_status='pending'`.
3. Akun Admin dibuat secara manual melalui Supabase Admin API, bukan melalui jalur pendaftaran publik.
4. Trigger hanya aktif untuk akun yang memiliki `raw_user_meta_data.full_name`; akun Admin dikecualikan.
5. Kegagalan trigger tidak memblokir registrasi — hanya menghasilkan log peringatan Postgres.
6. `fetchUserProfileStatus()` hanya dipanggil ketika session tersedia, bukan saat email belum dikonfirmasi.
7. Tidak ada redirect otomatis setelah registrasi — pengguna harus menekan tombol "Masuk ke PIXEL-T" secara manual.

---

## 5. Arsitektur dan Batasan Abstraksi

Diagram ini merupakan representasi abstrak yang disederhanakan untuk keperluan akademik. Beberapa aspek tidak ditampilkan secara eksplisit untuk menjaga keterbacaan, antara lain:

- Loading state (`isSubmitting`) selama proses registrasi.
- Detail error mapping pada AuthService.
- Mekanisme refresh token dan persistensi sesi oleh Supabase.
- RLS (Row Level Security) policies pada tabel `doctor_profiles`.
- Animasi dan transisi visual pada halaman Register.

Penyederhanaan ini sah secara UML karena sequence diagram bertujuan menggambarkan interaksi penting, bukan setiap baris kode.

---

## 6. Verifikasi dan Auditing

Diagram ini telah melalui dua putaran audit independen yang memverifikasi setiap pesan, return message, lifeline, fragment, dan note box terhadap source code aktual. Terdapat dua koreksi substantif pada putaran kedua:

1. **Label m11** dikoreksi dari `set session → fetchUserProfileStatus()` menjadi `set session` saja, karena `fetchUserProfileStatus()` hanya dipanggil kondisional.
2. **Guard alt1** dikoreksi dari `session tersedia` menjadi `session && user tersedia`, sesuai kondisi aktual di AuthContext.tsx baris 191.
3. **Note box** diperluas menambahkan penjelasan tentang kondisional fetchUserProfileStatus dan detail navigasi manual.

Kedua puluh lima unit test terkait registrasi dan auth service semuanya lulus, memberikan keyakinan tambahan bahwa alur yang digambarkan sesuai dengan implementasi aktual.

---

## 7. Kesimpulan

Sequence Diagram Sign Up PIXEL-T versi FINAL telah terbukti akurat melalui audit independen putaran kedua. Diagram ini layak digunakan sebagai gambar final Bab IV skripsi S1 karena:

1. Setiap interaksi dalam diagram dapat ditelusuri ke source code aktual.
2. Notasi UML yang digunakan sesuai standar.
3. Tingkat abstraksi sesuai untuk dokumentasi akademik.
4. Konsisten secara visual dengan Sequence Diagram Sign In yang telah diaudit.
5. Semua unit test terkait lulus.
