# Penjelasan Activity Diagram Sign Up PIXEL-T (Final Verifikasi Independen)

**Gambar 4.x — Activity Diagram Sign Up PIXEL-T (Final)**

Dokumen ini merupakan penjelasan akademik pendamping *Activity Diagram* Sign Up aplikasi web PIXEL-T. Diagram telah melalui dua putaran audit independen terhadap implementasi aktual *source code*, migrasi database, *trigger* PostgreSQL, dan ujian unit. Hasil audit terakhir (4 November 2026) menyimpulkan bahwa diagram **sudah akurat** dan **tidak memerlukan revisi**.

---

## 1. Aktor dan Proses Awal

Aktor utama dalam diagram ini adalah **User** (calon pengguna Dokter) dan **System** (aplikasi PIXEL-T bersama layanan autentikasi Supabase serta basis data PostgreSQL).

Proses dimulai dari **Initial Node** (lingkaran terisi hitam) yang menunjukkan titik awal alur. Aktivitas pertama adalah *"Membuka halaman /register"*, yang sesuai dengan rute publik `/register` pada `frontend/src/routes/AppRoutes.tsx` (baris 35–41). Halaman ini dilindungi oleh komponen `PublicOnlyRoute` (`frontend/src/components/auth/PublicOnlyRoute.tsx`) sehingga hanya dapat diakses oleh pengguna yang belum terautentikasi. Pengguna yang sudah login akan diarahkan ke halaman sesuai perannya: Admin ke `/admin`, Dokter yang disetujui ke `/dashboard`, sedangkan Dokter *pending* atau *rejected* tetap diperbolehkan berada di halaman pendaftaran.

Aktivitas ini dimodelkan di swimlane User karena merupakan inisiatif langsung dari calon pengguna.

---

## 2. Formulir Pendaftaran

Setelah halaman dibuka, sistem menampilkan formulir pendaftaran. Aktivitas *"Mengisi formulir pendaftaran"* mencakup enam bidang yang benar-benar tersedia pada `frontend/src/pages/auth/Register.tsx` (baris 18–23):

1. `fullName` — Nama lengkap
2. `email` — Alamat email
3. `password` — Kata sandi
4. `confirmPassword` — Konfirmasi kata sandi
5. `hospitalName` — Nama rumah sakit
6. `doctorSpecialty` — Spesialisasi dokter

Tidak ada bidang tambahan yang dimodelkan karena tidak ditemukan pada implementasi. Form ini juga dilengkapi dengan tombol *show/hide* untuk kedua bidang kata sandi (baris 251–305), namun fitur tersebut bersifat utilitas dan tidak memengaruhi alur logika pendaftaran, sehingga tidak dimodelkan secara terpisah.

---

## 3. Validasi Input dan Percabangan Pertama

Setelah formulir diisi, sistem melakukan validasi lokal pada aktivitas *"Memvalidasi input"*. Berdasarkan `Register.tsx` (baris 35–79), validasi yang dilakukan meliputi urutan berikut:

1. Nama lengkap wajib diisi.
2. Email wajib diisi.
3. Format email harus valid (regex `/^[^\s@]+@[^\s@]+\.[^\s@]+$/`).
4. Nama rumah sakit wajib diisi.
5. Spesialisasi dokter wajib diisi.
6. Kata sandi wajib diisi.
7. Kata sandi minimal 6 karakter.
8. Konfirmasi kata sandi harus cocok dengan kata sandi.

Semua validasi ini dilakukan di sisi klien **sebelum** permintaan dikirim ke layanan autentikasi. Apabila salah satu validasi gagal, fungsi `handleSubmit` melakukan *early return* (baris 40–78) dan tidak memanggil `signUp`.

Kemudian terdapat **Decision Node** *"Input valid?"* (d1) dengan dua cabang:

- **[Ya]** — Alur lanjut ke aktivitas pembuatan akun (`a4`: *"Memanggil signUp() → supabase.auth.signUp()"*).
- **[Tidak]** — Sistem menampilkan pesan kesalahan (`aerr`: *"Menampilkan pesan kesalahan (validasi / Supabase Auth)"`), lalu kembali ke aktivitas pengisian formulir (`a2`) sehingga pengguna dapat memperbaiki input.

Percabangan ini mencerminkan perilaku aktual di mana setiap kondisi validasi yang gagal menghasilkan `setErrorMessage(...)` dilanjutkan `return` tanpa memanggil `signUp`.

---

## 4. Pemanggilan Autentikasi dan Penanganan Error

Apabila input valid, sistem memanggil `signUp()` dari `AuthContext` (baris 186) yang pada gilirannya memanggil `registerUser()` di `frontend/src/services/auth.ts` (baris 146). Fungsi ini melakukan **satu panggilan tunggal** ke `supabase.auth.signUp()` dengan Metadata profesional (`full_name`, `hospital`, `hospital_name`, `primary_specialty`, `specialty`, dan `doctor_profile`) dikirim sebagai `user_metadata`.

Setelah panggilan, terdapat **Decision Node** *"Permintaan signUp berhasil?"* (d3) yang memeriksa apakah terdapat error dari Supabase Auth:

- **[Ya]** — Tidak ada error. Alur lanjut ke pembuatan akun di Supabase (`a5`).
- **[Tidak]** — Terdapat error (misalnya email sudah terdaftar, kata sandi lemah, atau *rate limit*). Sistem menampilkan pesan kesalahan pada `aerr`, lalu kembali ke aktivitas pengisian formulir (`a2`).

Percabangan ini memisahkan keberhasilan pengiriman permintaan pendaftaran dari keberhasilan penerbitan sesi, sehingga tidak digabung menjadi satu aktivitas ambigu. Fungsi `formatAuthError` di `services/auth.ts` (baris 45–108) menerjemahkan berbagai kode error Supabase menjadi pesan dalam Bahasa Indonesia yang ramah pengguna, termasuk penanganan anti-enumerasi untuk alamat email yang sudah terdaftar.

---

## 5. Pembuatan Akun dan Profil Dokter

Apabila permintaan berhasil, Supabase Auth membuat baris baru pada tabel `auth.users` beserta `user_metadata` yang berisi informasi profesional (`a5`: *"Supabase membuat auth.users (dengan user_metadata)"*).

Setelah akun dibuat, *trigger database* `handle_new_doctor_signup` (migrasi `008_create_doctor_profile_trigger.sql`, baris 28–71) secara otomatis menjalankan aktivitas `a6`: *"Trigger handle_new_doctor_signup INSERT doctor_profiles (role='doctor', account_status='pending')"*.

Detail trigger:
- Merupakan *AFTER INSERT* trigger pada `auth.users`.
- Hanya berjalan untuk baris di mana `raw_user_meta_data` mengandung `full_name` **dan** `raw_app_meta_data.role ≠ 'admin'`.
- Memasukkan baris baru ke `doctor_profiles` dengan `role = 'doctor'` dan `account_status = 'pending'`.
- Bersifat idempoten: melewati jika profil untuk `user_id` yang sama sudah ada.
- Menggunakan `SECURITY DEFINER` agar dapat menulis ke `doctor_profiles` meskipun RLS aktif.
- **Kegagalan tidak membatalkan pendaftaran**: blok `EXCEPTION WHEN OTHERS THEN RAISE WARNING` mencatat kegagalan di log PostgreSQL tanpa menggagalkan transaksi.

Catatan ini juga tercantum dalam UML Note pada diagram:
> *Pendaftaran publik hanya untuk Dokter. Admin dibuat via Supabase Admin API (app_metadata.role='admin') dan tidak memiliki baris doctor_profiles. Kegagalan trigger dicatat sebagai WARNING dan tidak membatalkan pendaftaran.*

---

## 6. Percabangan Sesi dan Konfirmasi Email

Setelah profil Dokter dibuat, terdapat **Decision Node** kedua: *"Sesi dikembalikan?"* (d2). Percabangan ini memisahkan dua kondisi yang benar-benar ada dalam `AuthContext.signUp()` (baris 191–203):

- **[Ya]** — Sesi autentikasi dikembalikan oleh Supabase. Sistem menyimpan sesi, pengguna, serta memperbarui *state* autentikasi: `role = 'doctor'` dan `account_status = 'pending'` (diambil dari `doctor_profiles` via `fetchUserProfileStatus`, ataufallback ke nilai default). Sistem kemudian menampilkan pesan pendaftaran berhasil.
- **[Tidak]** — Sesi tidak dikembalikan (karena konfirmasi email diperlukan atau kebijakan Supabase Auth). Sistem menampilkan instruksi konfirmasi email pada aktivitas *"Menampilkan instruksi konfirmasi email"* (a8), dengan `requiresEmailConfirmation = true`.

Kedua cabang kemudian bergabung (**merge node**) pada aktivitas *"Menampilkan pesan pendaftaran berhasil (menunggu persetujuan admin)"* (a9). Meskipun pesannya sedikit berbeda antara kedua cabang, keduanya menyatakan bahwa akun telah dibuat dan menunggu persetujuan administrator, sehingga digabungkan menjadi satu aktivitas penyampaian pesan.

Percabangan ini sengaja memisahkan keberhasilan pembuatan akun dari keberhasilan penerbitan sesi, karena keduanya adalah proses yang berbeda dan tidak boleh disatukan menjadi satu aktivitas ambigu.

---

## 7. Akhir Proses

Terakhir, pengguna mengakses halaman `/login` melalui tautan *"Masuk ke PIXEL-T"* yang terdapat pada layar sukses (`Register.tsx`, baris 159–165). Tautan ini merupakan **tindakan manual** pengguna — sistem tidak melakukan *redirect* otomatis. Pengguna dapat juga memilih *"Daftar dengan akun lain"* untuk mengosongkan formulir dan memulai ulang.

Aktivitas mencapai **Final Node** (bullseye: lingkaran luar putih dengan lingkaran dalam hitam), sesuai notasi UML standar untuk menandai akhir alur.

---

## 8. Catatan Penting

- **Pendaftaran publik hanya untuk Dokter.** Akun Admin dibuat secara eksternal melalui Supabase Admin API dengan `app_metadata.role = 'admin'` dan tidak pernah melewati jalur pendaftaran publik. Admin juga tidak memiliki baris pada `doctor_profiles`.
- **Persetujuan Admin (approve/reject) di luar alur Sign Up.** Merupakan *use case* terpisah yang terjadi setelah pendaftaran, sehingga tidak dimodelkan dalam diagram ini.
- **Status `pending` memblokir akses klinis.** Rute klinis (`/dashboard`, `/analysis/*`) dilindungi `ProtectedRoute` dan `DoctorRoute` yang memeriksa `account_status === 'pending'` dan mengarahkan kembali ke `/login`.

---

## 9. Kesimpulan

*Activity Diagram* Sign Up PIXEL-T (Gambar 4.x) menggambarkan alur pendaftaran akun Dokter melalui halaman `/register` secara akurat berdasarkan implementasi aktual:

1. Formulir enam bidang dengan validasi lokal delapan kondisi.
2. Panggilan tunggal `supabase.auth.signUp()` dengan metadata profesional.
3. *Trigger* `handle_new_doctor_signup` yang secara otomatis membuat profil Dokter berstatus `pending`, mengecualikan Admin, dan gagal secara non-fatal.
4. Dua *decision node* (validasi input dan keberadaan sesi) dengan percabangan yang benar.
5. Merge kedua cabang sukses ke pesan keberhasilan yang sama.
6. Pengalihan manual ke `/login` sebagai akhir proses.

Diagram tidak memasukkan proses persetujuan Admin karena merupakan *use case* terpisah yang terjadi setelah pendaftaran.

---

*Disclaimer: Penjelasan ini berdasarkan analisis statis source code dan ujian unit yang ada (25/25 lolos). Tidak dilakukan pengujian browser (E2E) maupun pengujian dengan akun produksi.*
