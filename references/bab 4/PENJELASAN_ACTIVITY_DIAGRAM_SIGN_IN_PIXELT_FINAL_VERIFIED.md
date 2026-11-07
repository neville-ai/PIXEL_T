# Penjelasan Activity Diagram Sign In PIXEL-T (Final Verified)

**Gambar 4.y — Activity Diagram Sign In PIXEL-T (Final Verified)**

Dokumen ini menyediakan penjelasan akademik mengenai Activity Diagram Sign In aplikasi web PIXEL-T yang telah diverifikasi secara independen terhadap implementasi aktual source code. Diagram tersebut menggambarkan proses masuk ke akun melalui halaman `/login`, mulai dari pembukaan halaman hingga pengalihan ke halaman tujuan sesuai peran dan status akun.

---

## 1. Aktor dan Proses Awal

Aktor utama dalam diagram ini adalah **User** (pengguna yang ingin masuk ke aplikasi) dan **System** (aplikasi PIXEL-T beserta layanan autentikasi Supabase dan basis data PostgreSQL).

Proses dimulai dari **Initial Node** (lingkaran terisi hitam) yang menandai titik awal alur. Aktivitas pertama adalah *"Membuka halaman /login"*, yang sesuai dengan rute publik `/login` pada konfigurasi router `frontend/src/routes/AppRoutes.tsx`. Halaman ini dilindungi oleh komponen `PublicOnlyRoute` sehingga hanya dapat diakses oleh pengguna yang belum memiliki sesi autentikasi aktif; pengguna yang sudah login akan diarahkan secara otomatis ke halaman sesuai perannya.

Setelah halaman dimuat, sistem menampilkan formulir Sign In yang terdiri dari tiga elemen input: dropdown pemilihan jenis akun (default: Dokter), bidang alamat email, dan bidang kata sandi. Dropdown pemilihan jenis akun merupakan **konteks login** yang dipilih pengguna, bukan sumber otorisasi. Pemilihan ini hanya bersifat informatif dan akan dibandingkan dengan role aktual yang tersimpan pada akun setelah autentikasi berhasil.

---

## 2. Validasi Input Lokal

Setelah formulir diisi, sistem melakukan **validasi lokal** pada aktivitas *"Memvalidasi input (email wajib, kata sandi wajib)"*. Berdasarkan implementasi pada `frontend/src/pages/auth/Login.tsx` (baris 93–101), validasi yang dilakukan meliputi:

1. **Alamat email wajib diisi** — jika kolom email kosong setelah trim, sistem menampilkan pesan *"Silakan masukkan alamat email Anda."*
2. **Kata sandi wajib diisi** — jika kolom kata sandi kosong, sistem menampilkan pesan *"Silakan masukkan kata sandi Anda."*

Validasi ini berjalan sepenuhnya di sisi klien (frontend) sebelum permintaan autentikasi dikirim ke layanan Supabase. Apabila validasi gagal, fungsi penangan formulir melakukan *early return* tanpa memanggil fungsi autentikasi.

Kemudian terdapat **Decision Node** *"Input valid?"* dengan dua cabang:

- **[Ya]** — seluruh kondisi validasi terpenuhi. Alur lanjut ke proses autentikasi.
- **[Tidak]** — terdapat satu atau lebih kondisi validasi yang gagal. Sistem menampilkan pesan kesalahan pada aktivitas *"Menampilkan pesan kesalahan (validasi / autentikasi / role mismatch)"*, lalu mengembalikan pengguna ke aktivitas pengisian formulir sehingga pengguna dapat memperbaiki input yang kurang.

Percabangan ini mencerminkan perilaku aktual di mana formulir tidak akan mengirim permintaan autentikasi selama validasi lokal belum berlalu.

---

## 3. Autentikasi Melalui Supabase

Apabila input valid, sistem memanggil fungsi `signIn()` dari `AuthContext` (baris 137) yang pada gilirannya memanggil fungsi `loginUser()` di `frontend/src/services/auth.ts` (baris 208). Fungsi ini melakukan **satu panggilan tunggal** ke `supabase.auth.signInWithPassword()` dengan parameter email dan kata sandi yang dimasukkan pengguna.

Setelah panggilan, terdapat **Decision Node** *"Kredensial valid?"* yang memeriksa apakah panggilan `signInWithPassword` mengembalikan error:

- **[Ya]** — tidak ada error. Sistem melanjutkan ke pembaruan sesi dan state autentikasi.
- **[Tidak]** — terdapat error (misalnya kredensial salah, email belum dikonfirmasi, atau kegagalan jaringan). Sistem menampilkan pesan kesalahan yang telah diformat, lalu mengembalikan pengguna ke aktivitas pengisian formulir.

Percabangan ini memisahkan keberhasilan pengiriman permintaan autentikasi dari keberhasilan pembaruan state, sehingga alur kesalahan dan keberhasilan dapat dikelola secara terpisah.

---

## 4. Pembaruan Sesi dan Resolusi Role

Apabila kredensial valid, `AuthContext` memperbarui state autentikasi pada aktivitas *"Memperbarui sesi & state autentikasi (user, session, role, account_status)"*. Proses ini meliputi empat tahap berurutan:

1. **Menyimpan sesi** — objek `user` dan `session` dari Supabase Auth disimpan ke state React.
2. **Membaca role dari app_metadata** — fungsi `getAdminRoleFromAppMetadata()` membaca nilai `app_metadata.role` dari objek user. Nilai ini bersifat *server-write-only* (hanya dapat diubah melalui Supabase Admin API), sehingga merupakan sumber otoritas tertinggi untuk identifikasi Admin.
3. **Mengambil profil Dokter** — fungsi `fetchUserProfileStatus()` querying tabel `doctor_profiles` untuk mendapatkan kolom `role` dan `account_status`.
4. **Menentukan role aktual** — jika `app_metadata.role === 'admin'`, role ditetapkan sebagai `'admin'`. Selain itu, role diambil dari `doctor_profiles.role`. Status akun diambil dari `doctor_profiles.account_status`.

---

## 5. Pengecekan Role Mismatch

Setelah role aktual ditentukan, sistem memeriksa kecocokan antara role yang dipilih pengguna di dropdown dengan role aktual akun melalui **Decision Node** *"Role cocok dengan akun?"*:

- **[Ya]** — role yang dipilih pengguna sesuai dengan role aktual akun. Alur lanjut ke penentuan rute.
- **[Tidak]** — terdapat ketidakcocokan (misalnya pengguna dengan akun Dokter memilih konteks Admin, atau sebaliknya). Sistem menampilkan pesan *"Jenis akun tidak sesuai dengan hak akses akun Anda"* pada aktivitas *"Menampilkan pesan jenis akun tidak sesuai"*, lalu mengembalikan pengguna ke aktivitas pengisian formulir.

Percabangan *role mismatch* ini mencegah pengguna mengeksploitasi dropdown pemilihan role untuk mengakses halaman yang tidak sesuai dengan hak akses akun mereka. Mekanisme ini merupakan lapisan keamanan tambahan selain route guard.

---

## 6. Penentuan Route Berdasarkan Role dan Status Akun

Apabila role cocok, sistem memasuki rangkaian pengecekan berurutan untuk menentukan halaman tujuan.

**Decision Node *"Role = admin?\""** memeriksa apakah `app_metadata.role === 'admin'`:

- **[Ya]** — pengguna merupakan Admin. Sistem mengarahkan ke `/admin` pada aktivitas *"Mengarahkan ke /admin"*. Admin tidak memerlukan baris pada tabel `doctor_profiles`.
- **[Tidak]** — pengguna bukan Admin. Lanjut ke pengecekan status akun Dokter.

Untuk pengguna non-Admin, sistem memeriksa status akun secara berurutan:

**Decision Node *"Akun pending?\""** memeriksa apakah `account_status === 'pending'`:

- **[Ya]** — akun Dokter belum disetujui administrator. Sistem mengarahkan kembali ke `/login` pada aktivitas *"Kembali ke /login (menunggu persetujuan)"*. Pengguna akan melihat pesan *"Akun Anda sedang menunggu persetujuan administrator"*.
- **[Tidak]** — akun tidak dalam status pending. Lanjut ke pengecekan penolakan.

**Decision Node *"Akun ditolak?\""** memeriksa apakah `account_status === 'rejected'`:

- **[Ya]** — akun Dokter ditolak oleh administrator. Sistem mengarahkan kembali ke `/login` pada aktivitas *"Kembali ke /login (pendaftaran ditolak)"*. Pengguna akan melihat pesan *"Pendaftaran Anda ditolak. Hubungi administrator rumah sakit."*
- **[Tidak]** — akun Dokter telah disetujui (`approved`). Sistem mengarahkan ke halaman tujuan pada aktivitas *"Mengakses halaman tujuan (dashboard atau halaman sebelumnya)"*.

Ketiga cabang akhir (Admin, pending, rejected, approved) semuanya menuju **Final Node** (bullseye: lingkaran luar putih dengan lingkaran dalam hitam), sesuai notasi UML standar.

---

## 7. Catatan Tambahan (Non-Aktivitas Utama)

Pada diagram terdapat catatan pendukung (UML Note) yang menyatakan:

- Halaman `/login` dilindungi oleh `PublicOnlyRoute`, yang mengarahkan pengguna terautentikasi ke halaman sesuai peran mereka.
- Role selector (Admin/Dokter) adalah konteks login, bukan sumber otorisasi. Role aktual ditentukan oleh `app_metadata.role` (Admin, server-write-only) atau `doctor_profiles` (Dokter, dari database).
- Fitur *"Remember my email"* hanya menyimpan alamat email di `localStorage` tanpa memengaruhi masa berlaku sesi autentikasi Supabase.
- Halaman Reset Password merupakan use case terpisah yang memiliki alur dan halaman sendiri, sehingga tidak dimodelkan sebagai aktivitas dalam diagram Sign In.

Catatan-catatan ini dimasukkan sebagai informasi pendukung saja dan tidak dimodelkan sebagai aktivitas utama dalam alur kontrol.

---

## 8. Kesimpulan

*Activity Diagram* Sign In PIXEL-T (Gambar 4.y) menggambarkan alur masuk ke aplikasi secara akurat berdasarkan implementasi aktual: validasi lokal dua kondisi (email dan kata sandi wajib), panggilan tunggal `supabase.auth.signInWithPassword()`, pembaruan sesi dan state autentikasi, pengecekan *role mismatch* sebagai lapisan keamanan, penentuan rute berdasarkan role (Admin ke `/admin`) dan status akun Dokter (pending/rejected kembali ke `/login` dengan pesan sesuai, approved ke `/dashboard` atau halaman sebelumnya), serta *final node* yang menandai akhir proses.

Diagram ini telah diverifikasi secara independen melalui pemeriksaan source code, validasi XML struktur diagram, dan pelaksanaan 39 unit test yang semuanya berhasil.

---

*Penjelasan ini didasarkan pada analisis statis source code aktual web PIXEL-T (November 2026). Tidak dilakukan pengujian browser (E2E) maupun pengujian dengan akun produksi.*