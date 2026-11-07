# Penjelasan Activity Diagram Sign Up PIXEL-T (Final)

**Gambar 4.x — Activity Diagram Sign Up PIXEL-T (Final)**

Dokumen ini menyediakan penjelasan akademik mengenai Activity Diagram Sign Up aplikasi web PIXEL-T yang telah diverifikasi terhadap implementasi aktual source code. Diagram tersebut menggambarkan proses pendaftaran akun Dokter melalui halaman `/register`, mulai dari pembuka halaman hingga pengalihan ke halaman Sign In, beserta percabangan yang benar-benar terdapat pada kode aplikasi.

## 1. Aktor dan Proses Awal

Aktor utama dalam diagram ini adalah **User** (calon pengguna Dokter) dan **System** (aplikasi PIXEL-T bersama dengan layanan autentikasi Supabase serta basis data PostgreSQL).

Proses dimulai dari **Initial Node** (node awal) yang menunjukkan titik awal alur. Aktivitas pertama adalah "Membuka halaman /register", yang sesuai dengan rute publik `/register` pada `frontend/src/routes/AppRoutes.tsx`. Halaman ini dilindungi oleh `PublicOnlyRoute` sehingga hanya dapat diakses oleh pengguna yang belum terautentikasi; pengguna yang sudah login akan diarahkan ke halaman sesuai perannya (admin ke `/admin`, dokter yang disetujui ke `/dashboard`). Aktivitas ini dimodelkan sebagai tanggung jawab User.

Selanjutnya, sistem menampilkan formulir pendaftaran. Aktivitas "Mengisi formulir pendaftaran" mencakup enam bidang yang benar-benar tersedia pada `frontend/src/pages/auth/Register.tsx`: nama lengkap, email, kata sandi, konfirmasi kata sandi, nama rumah sakit, dan spesialisasi dokter. Tidak ada bidang tambahan yang dimodelkan karena tidak ditemukan pada implementasi.

## 2. Validasi Input dan Percabangan Pertama

Setelah formulir diisi, sistem melakukan validasi lokal pada aktivitas "Memvalidasi input". Berdasarkan `Register.tsx`, validasi yang dilakukan meliputi:

- Nama lengkap wajib diisi.
- Email wajib diisi dan memenuhi format email.
- Nama rumah sakit wajib diisi.
- Spesialisasi dokter wajib diisi.
- Kata sandi wajib diisi dan minimal 6 karakter.
- Konfirmasi kata sandi harus cocok dengan kata sandi.

Semua validasi ini dilakukan di sisi klien sebelum permintaan dikirim ke layanan autentikasi. Apabila validasi gagal, proses berhenti dan tidak melanjutkan ke `signUp`.

Kemudian terdapat **Decision Node** "Input valid?" dengan dua cabang:

- **[Ya]** — alur lanjut ke aktivitas pembuatan akun.
- **[Tidak]** — sistem menampilkan pesan kesalahan pada aktivitas "Menampilkan pesan kesalahan", lalu kembali ke aktivitas pengisian formulir sehingga pengguna dapat memperbaiki input.

Percabangan ini mencerminkan perilaku aktual di mana `handleSubmit` mengembalikan nilai awal (`return`) saat validasi gagal dan tidak memanggil `signUp`.

## 3. Pembuatan Akun dan Profil Dokter

Apabila input valid, sistem memanggil `signUp()` yang pada gilirannya memanggil `supabase.auth.signUp()` melalui `frontend/src/services/auth.ts`.

Kemudian terdapat **Decision Node** "Permintaan signUp berhasil?" yang memeriksa apakah panggilan `supabase.auth.signUp` mengembalikan error (dicek pada `registerUser` dalam `services/auth.ts`):

- **[Ya]** — Tidak ada error. Alur lanjut ke pembuatan akun Supabase.
- **[Tidak]** — Terdapat error (misalnya email sudah terdaftar, kata sandi lemah, atau rate limit). Sistem menampilkan pesan kesalahan, lalu kembali ke aktivitas pengisian formulir.

Percabangan ini memisahkan keberhasilan pengiriman permintaan pendaftaran dari keberhasilan penerbitan sesi, sehingga tidak digabung menjadi satu aktivitas ambigu. Supabase Auth membuat baris baru pada tabel `auth.users` beserta `user_metadata` yang berisi informasi profesional (nama lengkap, rumah sakit, spesialisasi, dll.).

Setelah akun dibuat, sistem menjalankan **trigger database** `handle_new_doctor_signup` (migration `008_create_doctor_profile_trigger.sql`). Trigger ini adalah `AFTER INSERT` pada `auth.users` dan secara otomatis memasukkan baris baru ke tabel `doctor_profiles` dengan:

- `role = 'doctor'`
- `account_status = 'pending'`

Data diambil dari `raw_user_meta_data`. Trigger secara eksplisit melewati akun admin (`app_metadata.role = 'admin'`) sehingga admin tidak memiliki baris pada `doctor_profiles`. Kegagalan pembuatan profil dicatat sebagai peringatan (WARNING) dan tidak membatalkan proses pendaftaran.

## 4. Percabangan Sesi dan Konfirmasi Email

Setelah profil Dokter dibuat, terdapat **Decision Node** kedua: "Sesi dikembalikan?". Percabangan ini memisahkan dua kondisi yang benar-benar ada dalam `AuthContext.signUp`:

- **[Ya]** — Sesi autentikasi dikembalikan. Sistem menyimpan sesi dengan `role = 'doctor'` dan `account_status = 'pending'`, lalu menampilkan pesan pendaftaran berhasil.
- **[Tidak]** — Sesi tidak dikembalikan (karena konfirmasi email diperlukan atau alasan kebijakan Supabase Auth). Sistem menampilkan instruksi konfirmasi email pada aktivitas "Menampilkan instruksi konfirmasi email".

Kedua cabang kemudian bergabung (**merge**) pada aktivitas "Menampilkan pesan pendaftaran berhasil (menunggu persetujuan admin)".

Percabangan ini sengaja memisahkan keberhasilan pembuatan akun dari keberhasilan penerbitan sesi, karena keduanya adalah proses yang berbeda dan tidak boleh disatukan menjadi satu aktivitas ambigu.

## 5. Akhir Proses

Terakhir, sistem menampilkan pesan pendaftaran berhasil yang menyatakan akun telah dibuat dan menunggu persetujuan administrator rumah sakit. Pengguna kemudian mengakses halaman `/login` untuk masuk ke aplikasi. Aktivitas akhir mencapai **Final Node** (node akhir) yang ditandai dengan lingkaran bundar dengan titik hitam di tengahnya, sesuai notasi UML standar.

## 6. Catatan Tambahan (Non-Aktivitas Utama)

Pada diagram terdapat catatan pendukung yang menyatakan:

- Pendaftaran publik hanya untuk Dokter.
- Admin dibuat melalui Supabase Admin API dengan pengaturan `app_metadata.role = 'admin'` dan tidak memiliki baris pada `doctor_profiles`.

Catatan ini dimasukkan sebagai informasi pendukung saja dan tidak dimodelkan sebagai aktivitas utama, karena pembuatan akun admin berada di luar alur pendaftaran publik.

## 7. Kesimpulan

Activity Diagram Gambar 4.x menggambarkan alur Sign Up PIXEL-T secara akurat berdasarkan implementasi aktual: validasi lokal, panggilan tunggal `supabase.auth.signUp`, trigger pembuatan profil Dokter dengan status awal `pending`, percabangan sesi dan konfirmasi email, serta pengalihan ke halaman login. Diagram tidak memasukkan proses persetujuan admin karena merupakan use case terpisah yang terjadi setelah pendaftaran.

---

*Disclaimer: Penjelasan ini berdasarkan analisis statis source code dan ujian unit yang ada. Tidak dilakukan pengujian browser (E2E) maupun pengujian dengan akun produksi.*