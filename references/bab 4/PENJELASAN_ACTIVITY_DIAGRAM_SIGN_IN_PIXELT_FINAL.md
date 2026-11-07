# Penjelasan Activity Diagram Sign In PIXEL-T (Final)

**Gambar 4.y — Activity Diagram Sign In PIXEL-T (Final)**

Dokumen ini menyediakan penjelasan akademik mengenai Activity Diagram Sign In aplikasi web PIXEL-T yang telah diverifikasi terhadap implementasi aktual source code. Diagram tersebut menggambarkan proses masuk ke akun melalui halaman `/login`, mulai dari pembuka halaman hingga pengalihan ke halaman tujuan sesuai peran dan status akun.

---

## 1. Aktor dan Proses Awal

Aktor utama dalam diagram ini adalah **User** (pengguna yang ingin masuk) dan **System** (aplikasi PIXEL-T bersama dengan layanan autentikasi Supabase serta basis data PostgreSQL).

Proses dimulai dari **Initial Node** (lingkaran terisi hitam) yang menunjukkan titik awal alur. Aktivitas pertama adalah *"Membuka halaman /login"*, yang sesuai dengan rute publik `/login` pada `frontend/src/routes/AppRoutes.tsx`. Halaman ini dilindungi oleh `PublicOnlyRoute` sehingga hanya dapat diakses oleh pengguna yang belum terautentikasi; pengguna yang sudah login akan diarahkan ke halaman sesuai perannya (Admin ke `/admin`, Dokter yang disetujui ke `/dashboard`).

Selanjutnya, sistem menampilkan formulir Sign In. Aktivitas *"Mengisi email, kata sandi, dan memilih jenis akun"* mencakup elemen-elemen yang benar-benar tersedia pada `frontend/src/pages/auth/Login.tsx`: dropdown pemilihan jenis akun (default: Dokter), bidang email, dan bidang kata sandi. Pemilihan jenis akun merupakan konteks login yang dipilih pengguna, bukan sumber otorisasi — role aktual ditentukan oleh sistem setelah autentikasi berhasil.

---

## 2. Validasi Input dan Percabangan Pertama

Setelah formulir diisi, sistem melakukan validasi lokal pada aktivitas *"Memvalidasi input"*. Berdasarkan `Login.tsx` (baris 93–101), validasi yang dilakukan meliputi:

- Alamat email wajib diisi.
- Kata sandi wajib diisi.

Semua validasi ini dilakukan di sisi klien sebelum permintaan dikirim ke layanan autentikasi. Apabila validasi gagal, fungsi `handleSubmit` melakukan *early return* dan tidak memanggil `signIn`.

Kemudian terdapat **Decision Node** "Input valid?" dengan dua cabang:

- **[Ya]** — alur lanjut ke aktivitas autentikasi.
- **[Tidak]** — sistem menampilkan pesan kesalahan pada aktivitas "Menampilkan pesan kesalahan (validasi / autentikasi)", lalu kembali ke aktivitas pengisian formulir sehingga pengguna dapat memperbaiki input.

Percabangan ini mencerminkan perilaku aktual di mana `handleSubmit` mengembalikan nilai awal (`return`) saat validasi gagal dan tidak memanggil `signIn`.

---

## 3. Autentikasi dan Pembaruan Sesi

Apabila input valid, sistem memanggil `signIn()` dari `AuthContext` (baris 137) yang pada gilirannya memanggil `loginUser()` di `frontend/src/services/auth.ts` (baris 208). Fungsi ini melakukan **satu panggilan tunggal** ke `supabase.auth.signInWithPassword()` dengan email dan kata sandi yang dimasukkan pengguna.

Setelah panggilan, terdapat **Decision Node** "Kredensial valid?" yang memeriksa apakah panggilan `signInWithPassword` mengembalikan error:

- **[Ya]** — Tidak ada error. Alur lanjut ke pembaruan sesi dan state autentikasi.
- **[Tidak]** — Terdapat error (misalnya kredensial salah, email belum dikonfirmasi, atau masalah jaringan). Sistem menampilkan pesan kesalahan, lalu kembali ke aktivitas pengisian formulir.

Percabangan ini memisahkan keberhasilan pengiriman permintaan autentikasi dari keberhasilan pembaruan state, sehingga tidak digabung menjadi satu aktivitas ambigu.

---

## 4. Pembaruan State Autentikasi dan Pengecekan Role

Apabila kredensial valid, `AuthContext` memperbarui state autentikasi pada aktivitas *"Memperbarui sesi & state autentikasi (user, session, role, account_status)"*. Proses ini meliputi:

1. Menyimpan objek `user` dan `session` dari Supabase Auth.
2. Menentukan role aktual pengguna:
   - Admin: dibaca dari `app_metadata.role` (sumber server-write-only, paling tepercaya).
   - Dokter: dibaca dari tabel `doctor_profiles` melalui `fetchUserProfileStatus`.
3. Menyimpan `account_status` dari `doctor_profiles` (hanya untuk Dokter).
4. Memeriksa *role mismatch*: apakah role yang dipilih pengguna di dropdown cocok dengan role aktual akun.

Kemudian terdapat **Decision Node** "Role cocok dengan akun?" yang memeriksa hasil pengecekan *role mismatch*:

- **[Ya]** — Role cocok. Alur lanjut ke penentuan rute berdasarkan role.
- **[Tidak]** — Role tidak cocok (misalnya pengguna dengan akun Dokter memilih konteks Admin, atau sebaliknya). Sistem menampilkan pesan "jenis akun tidak sesuai" pada aktivitas "Menampilkan pesan jenis akun tidak sesuai", lalu kembali ke aktivitas pengisian formulir.

Percabangan *role mismatch* ini mencegah pengguna mengeksploitasi dropdown pemilihan role untuk mengakses halaman yang tidak sesuai dengan hak akses akun mereka.

---

## 5. Penentuan Route Berdasarkan Role dan Status Akun

Apabila role cocok, sistem memasuki rangkaian pengecekan berurutan untuk menentukan halaman tujuan.

**Decision Node "Role = admin?"** memeriksa apakah `app_metadata.role === 'admin'`:

- **[Ya]** — Pengguna adalah Admin. Sistem mengarahkan ke `/admin`.
- **[Tidak]** — Pengguna adalah Dokter. Lanjut ke pengecekan status akun.

**Decision Node "Akun pending?"** memeriksa apakah `account_status === 'pending'`:

- **[Ya]** — Akun Dokter belum disetujui administrator. Sistem mengarahkan kembali ke `/login` dengan pesan menunggu persetujuan.
- **[Tidak]** — Lanjut ke pengecekan penolakan.

**Decision Node "Akun ditolak?"** memeriksa apakah `account_status === 'rejected'`:

- **[Ya]** — Akun Dokter ditolak oleh administrator. Sistem mengarahkan kembali ke `/login` dengan pesan pendaftaran ditolak.
- **[Tidak]** — Akun Dokter disetujui (`approved`). Sistem mengarahkan ke halaman tujuan, yaitu `/dashboard` (default) atau halaman sebelumnya yang tersimpan di `location.state.from`.

Ketiga cabang akhir (admin, pending, rejected, approved) semuanya menuju **Final Node** (bullseye), sesuai notasi UML standar.

---

## 6. Catatan Tambahan (Non-Aktivitas Utama)

Pada diagram terdapat catatan pendukung yang menyatakan:

- Halaman `/login` dilindungi oleh `PublicOnlyRoute`.
- Role selector (Admin/Dokter) adalah konteks login, bukan sumber otorisasi. Role aktual ditentukan oleh `app_metadata.role` (Admin) atau `doctor_profiles` (Dokter).
- Fitur "Remember my email" hanya menyimpan alamat email di `localStorage` dan tidak memengaruhi masa berlaku sesi autentikasi.
- Halaman Reset Password merupakan use case terpisah dan tidak dimodelkan sebagai aktivitas dalam diagram Sign In.

Catat-catatan ini dimasukkan sebagai informasi pendukung saja dan tidak dimodelkan sebagai aktivitas utama.

---

## 7. Kesimpulan

*Activity Diagram* Sign In PIXEL-T (Gambar 4.y) menggambarkan alur masuk ke aplikasi secara akurat berdasarkan implementasi aktual: validasi lokal dua kondisi, panggilan tunggal `supabase.auth.signInWithPassword()`, pembaruan sesi dan state autentikasi, pengecekan *role mismatch*, penentuan rute berdasarkan role (Admin ke `/admin`) dan status akun Dokter (pending/rejected kembali ke `/login`, approved ke `/dashboard`), serta *final node* yang menandai akhir proses.

Diagram tidak memasukkan proses Reset Password ke dalam alur utama karena merupakan *use case* terpisah yang memiliki halaman dan alur sendiri.

---

*Disclaimer: Penjelasan ini berdasarkan analisis statis source code dan ujian unit yang ada (28/28 lolos untuk Login.test.tsx). Tidak dilakukan pengujian browser (E2E) maupun pengujian dengan akun produksi.*
