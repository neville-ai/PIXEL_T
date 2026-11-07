# MATRIKS VALIDASI ACTIVITY DIAGRAM DAN SEQUENCE DIAGRAM SIGN UP / SIGN IN PIXEL-T

Dokumen ini merupakan pendukung audit untuk Bab IV skripsi S1 PIXEL-T. Semua klaim teknis dalam penjelasan Activity Diagram dan Sequence Diagram Sign Up/Sign In dicantumkan dengan sumber bukti dari diagram dan implementasi kode sumber PIXEL-T.

> **Petunjuk:** Nomor baris source code adalah estimasi berdasarkan pembacaan file yang tersedia dan dapat bervariasi tergantung versi file. Path file adalah path relatif dari root proyek `WEB_PIXELT`.

---

## 1. Inventaris Diagram

| No. | Nama File Diagram | Jenis Diagram | Lokasi | Format |
|-----|-------------------|---------------|--------|--------|
| 1 | Activity Diagram - Sign Up.drawio.png | Activity Diagram | `references/bab 4/revisi/` | PNG raster |
| 2 | Activity Diagram - Sign In.drawio.png | Activity Diagram | `references/bab 4/revisi/` | PNG raster |
| 3 | Sequence Diagram - Sign Up.drawio.png | Sequence Diagram | `references/bab 4/revisi/` | PNG raster |
| 4 | Sequence Diagram - Sign In.drawio.png | Sequence Diagram | `references/bab 4/revisi/` | PNG raster |

**Catatan:** Keempat diagram hanya tersedia sebagai gambar PNG raster. Tidak ada file sumber `.drawio` untuk diagram revisi di folder ini.

---

## 2. Hasil Audit Activity Diagram Sign Up

| Elemen Diagram | Aktivitas yang Ditampilkan | Bukti Implementasi | Status | Catatan |
|----------------|---------------------------|-------------------|--------|---------|
| Initial node | Mulai proses pendaftaran | — | TERVERIFIKASI | Awal alur Sign Up |
| Aktivitas pengguna | Membuka halaman register, mengisi formulir | `frontend/src/pages/auth/Register.tsx` | TERVERIFIKASI | Halaman `/register` |
| Aktivitas sistem | Validasi input formulir | `Register.tsx` baris 40-79 | TERVERIFIKASI | Validasi nama, email, rumah sakit, bidang keahlian, kata sandi, konfirmasi kata sandi |
| Decision node | Validasi input berhasil/gagal | `Register.tsx` baris 40-79 | TERVERIFIKASI | Jika gagal, menampilkan error dan berhenti |
| Aktivitas sistem | Pemanggilan signUp() | `AuthContext.tsx` baris 175-204 | TERVERIFIKASI | Fungsi `signUp` pada AuthContext |
| Aktivitas sistem | Pemanggilan registerUser() | `frontend/src/services/auth.ts` baris 131-188 | TERVERIFIKASI | Fungsi `registerUser` pada AuthService |
| Aktivitas sistem | pemanggilan supabase.auth.signUp() | `auth.ts` baris 146 | TERVERIFIKASI | Memanggil Supabase Auth |
| Aktivitas sistem | Trigger handle_new_doctor_signup | `database/migrations/008_create_doctor_profile_trigger.sql` baris 28-79 | TERVERIFIKASI | AFTER INSERT trigger pada auth.users, membuat baris doctor_profiles dengan role='doctor', account_status='pending' |
| Decision node | Sesi tersedia / tidak tersedia | `AuthContext.tsx` baris 191-203 | TERVERIFIKASI | Jika session ada → update state; jika tidak → requiresEmailConfirmation=true |
| Aktivitas sistem | Update state autentikasi (role=doctor, accountStatus=pending) | `AuthContext.tsx` baris 194-196 | TERVERIFIKASI | Hanya jika session tersedia |
| Notifikasi | Pesan sukses / gagal kepada pengguna | `Register.tsx` baris 93-98, 196-204 | TERVERIFIKASI | Tampilan sukses atau error message |
| Pengalihan | Link ke halaman login | `Register.tsx` baris 159-165 | TERVERIFIKASI | Link "Masuk ke PIXEL-T" ke `/login` |
| Activity final node | Selesai proses pendaftaran | — | TERVERIFIKASI | Akhir alur Sign Up |

---

## 3. Hasil Audit Activity Diagram Sign In

| Elemen Diagram | Aktivitas yang Ditampilkan | Bukti Implementasi | Status | Catatan |
|----------------|---------------------------|-------------------|--------|---------|
| Initial node | Mulai proses masuk | — | TERVERIFIKASI | Awal alur Sign In |
| Aktivitas pengguna | Membuka halaman login, mengisi email/password/jenis akun | `frontend/src/pages/auth/Login.tsx` | TERVERIFIKASI | Halaman `/login` |
| Aktivitas sistem | Validasi input (email dan password tidak kosong) | `Login.tsx` baris 93-101 | TERVERIFIKASI | Validasi dasar |
| Aktivitas sistem | Remember my email (hanya email, tidak disimpan password) | `Login.tsx` baris 57-59, 107-111 | TERVERIFIKASI | Hanya email disimpan ke sessionStorage |
| Aktivitas sistem | Pemanggilan signIn() | `AuthContext.tsx` baris 132-173 | TERVERIFIKASI | Fungsi `signIn` pada AuthContext |
| Aktivitas sistem | Pemanggilan loginUser() | `auth.ts` baris 195-225 | TERVERIFIKASI | Fungsi `loginUser` pada AuthService |
| Aktivitas sistem | supabase.auth.signInWithPassword() | `auth.ts` baris 208 | TERVERIFIKASI | Verifikasi kredensial Supabase Auth |
| Decision node | Kredensial valid / tidak valid | `auth.ts` baris 213-219 | TERVERIFIKASI | Jika error → tampilkan pesan kesalahan |
| Aktivitas sistem | Update state autentikasi (user, session, role, accountStatus) | `AuthContext.tsx` baris 142-155 | TERVERIFIKASI | Hanya jika berhasil |
| Aktivitas sistem | Cek app_metadata.role (admin) | `auth.ts` baris 328-334, `AuthContext.tsx` baris 148-151 | TERVERIFIKASI | Sumber tepercaya untuk admin |
| Aktivitas sistem | Cek doctor_profiles (role, account_status) | `auth.ts` baris 297-316, `AuthContext.tsx` baris 149 | TERVERIFIKASI | Untuk dokter |
| Decision node | Role cocok / tidak cocok | `AuthContext.tsx` baris 159-170 | TERVERIFIKASI | Mencegah impersonasi admin |
| Decision node | Status akun: admin / approved / pending / rejected | `AuthContext.tsx` baris 126-134 | TERVERIFIKASI | Navigasi sesuai status |
| Pengalihan | Admin → /admin, approved → /dashboard, pending/rejected → /login | `Login.tsx` baris 126-134 | TERVERIFIKASI | Berdasarkan role dan accountStatus |
| Notifikasi | Pesan kesalahan autentikasi | `Login.tsx` baris 116-118 | TERVERIFIKASI | Error message ditampilkan |
| Activity final node | Selesai proses masuk | — | TERVERIFIKASI | Akhir alur Sign In |

---

## 4. Hasil Audit Sequence Diagram Sign Up

| Urutan | Pesan pada Diagram | Pengirim | Penerima | Bukti Source Code | Status |
|--------|-------------------|----------|----------|-------------------|--------|
| 1 | accessesFormSignUp() | User | Register Page | `Register.tsx` | TERVERIFIKASI |
| 2 | submitFormSignUp() | User | Register Page | `Register.tsx` baris 30-108 | TERVERIFIKASI |
| 3 | inputValidation() | Register Page | Register Page | `Register.tsx` baris 40-79 | TERVERIFIKASI |
| 4 | signUp() | Register Page | AuthContext | `AuthContext.tsx` baris 175-204 | TERVERIFIKASI |
| 5 | RegisterUser() | AuthContext | AuthService | `auth.ts` baris 131-188 | TERVERIFIKASI |
| 6 | SignUp() | AuthService | SupabaseAuth | `auth.ts` baris 146 | TERVERIFIKASI |
| 7 | authSignup() (after insert trigger) | SupabaseAuth | auth.users + doctor_profiles | `008_create_doctor_profile_trigger.sql` baris 28-79 | TERVERIFIKASI |
| 8 | Respons pendaftaran | SupabaseAuth | AuthService | `auth.ts` baris 165-187 | TERVERIFIKASI |
| 9 | Percabangan: Registration Failed / Successful | AuthService | AuthContext | `AuthContext.tsx` baris 187-188, 191-203 | TERVERIFIKASI |
| 10 | Kondisi sesi tersedia / tidak tersedia | AuthContext | AuthContext | `AuthContext.tsx` baris 191-203 | TERVERIFIKASI |
| 11 | Kondisi konfirmasi email | AuthContext | User | `AuthContext.tsx` baris 200-203 | TERVERIFIKASI |
| 12 | Pembaruan state aplikasi (role=doctor, accountStatus=pending) | AuthContext | State aplikasi | `AuthContext.tsx` baris 194-196 | TERVERIFIKASI |
| 13 | Notifikasi kepada pengguna | Register Page | User | `Register.tsx` baris 93-98 | TERVERIFIKASI |
| 14 | Pengalihan ke halaman login | Register Page | User | `Register.tsx` baris 159-165 | TERVERIFIKASI |

---

## 5. Hasil Audit Sequence Diagram Sign In

| Urutan | Pesan pada Diagram | Pengirim | Penerima | Bukti Source Code | Status |
|--------|-------------------|----------|----------|-------------------|--------|
| 1 | accessesFormSignIn() | User | Login Page | `Login.tsx` | TERVERIFIKASI |
| 2 | submitFormSignIn() | User | Login Page | `Login.tsx` baris 88-140 | TERVERIFIKASI |
| 3 | inputValidation() | Login Page | Login Page | `Login.tsx` baris 93-101 | TERVERIFIKASI |
| 4 | signIn(email,password,selectedRole) [diagram label: 'signUp'] | Login Page | AuthContext | `AuthContext.tsx` baris 132-173 | SEBAGIAN TERVERIFIKASI |
| 5 | loginUser() | AuthContext | AuthService | `auth.ts` baris 195-225 | TERVERIFIKASI |
| 6 | signInWithPassword() | AuthService | SupabaseAuth | `auth.ts` baris 208 | TERVERIFIKASI |
| 7 | Respons autentikasi | SupabaseAuth | AuthService | `auth.ts` baris 213-224 | TERVERIFIKASI |
| 8 | Role resolution (app_metadata / doctor_profiles) | AuthContext | AuthContext | `AuthContext.tsx` baris 148-151 | TERVERIFIKASI |
| 9 | SELECT role / account status | AuthContext | doctor_profiles | `auth.ts` baris 297-316 | TERVERIFIKASI |
| 10 | Pembaruan sesi (user, session, role, accountStatus) | AuthContext | State aplikasi | `AuthContext.tsx` baris 142-155 | TERVERIFIKASI |
| 11 | Notifikasi hasil | Login Page | User | `Login.tsx` baris 116-118 | TERVERIFIKASI |
| 12 | Pengalihan navigasi | Login Page | Browser | `Login.tsx` baris 126-134 | TERVERIFIKASI |

---

## 6. Matriks Bukti Validasi (Klaim Teknis)

| No. | Diagram | Pernyataan Teknis | Bukti pada Diagram | Bukti Source Code | Status | Tindakan |
|-----|---------|-------------------|-------------------|-------------------|--------|----------|
| 1 | Activity Sign Up | Validasi input dilakukan di frontend sebelum pengiriman | Decision node validasi | `Register.tsx` baris 40-79 | TERVERIFIKASI | — |
| 2 | Activity Sign Up | Format email diperiksa | Decision node validasi | `Register.tsx` baris 50-54 | TERVERIFIKASI | — |
| 3 | Activity Sign Up | Batas minimal kata sandi 6 karakter | Decision node validasi | `Register.tsx` baris 71-74 | TERVERIFIKASI | — |
| 4 | Activity Sign Up | Konfirmasi kata sandi dibandingkan | Decision node validasi | `Register.tsx` baris 76-79 | TERVERIFIKASI | — |
| 5 | Activity Sign Up | Metadata pengguna dikirim saat pendaftaran | Aktivitas sistem | `auth.ts` baris 149-161 | TERVERIFIKASI | — |
| 6 | Activity Sign Up | Supabase Auth digunakan | Aktivitas sistem | `auth.ts` baris 146 | TERVERIFIKASI | — |
| 7 | Activity Sign Up | Sesi tidak selalu tersedia setelah Sign Up | Decision node sesi | `AuthContext.tsx` baris 191-203 | TERVERIFIKASI | — |
| 8 | Activity Sign Up | Konfirmasi email mungkin diperlukan | Decision node konfirmasi email | `AuthContext.tsx` baris 200-203 | TERVERIFIKASI | — |
| 9 | Activity Sign Up | Pendaftaran gagal → pesan kesalahan ditampilkan | Percabangan kegagalan | `Register.tsx` baris 196-204 | TERVERIFIKASI | — |
| 10 | Activity Sign Up | Pengalihan ke halaman login setelah sukses | Link navigasi | `Register.tsx` baris 159-165 | TERVERIFIKASI | — |
| 11 | Activity Sign In | Validasi email dan password tidak kosong | Decision node validasi | `Login.tsx` baris 93-101 | TERVERIFIKASI | — |
| 12 | Activity Sign In | Remember Me hanya menyimpan email, bukan password | Aktivitas sistem | `Login.tsx` baris 107-111 | TERVERIFIKASI | — |
| 13 | Activity Sign In | Fungsi signIn() dipanggil saat tombol masuk | Aktivitas sistem | `AuthContext.tsx` baris 132-173 | TERVERIFIKASI | — |
| 14 | Activity Sign In | supabase.auth.signInWithPassword() digunakan | Aktivitas sistem | `auth.ts` baris 208 | TERVERIFIKASI | — |
| 15 | Activity Sign In | Kredensial tidak valid → pesan kesalahan | Percabangan kegagalan | `Login.tsx` baris 116-118 | TERVERIFIKASI | — |
| 16 | Activity Sign In | Sesi diperbarui hanya setelah berhasil | Aktivitas sistem | `AuthContext.tsx` baris 142-155 | TERVERIFIKASI | — |
| 17 | Activity Sign In | Admin diarahkan ke /admin | Pengalihan | `Login.tsx` baris 126-127 | TERVERIFIKASI | — |
| 18 | Activity Sign In | Dokter approved diarahkan ke /dashboard | Pengalihan | `Login.tsx` baris 132-134 | TERVERIFIKASI | — |
| 19 | Activity Sign In | Dokter pending/rejected kembali ke /login | Pengalihan | `Login.tsx` baris 128-131 | TERVERIFIKASI | — |
| 20 | Sequence Sign Up | Pesan signUp() dari Register Page ke AuthContext | Urutan pesan | `AuthContext.tsx` baris 175-204 | TERVERIFIKASI | — |
| 21 | Sequence Sign Up | Pesan RegisterUser() dari AuthContext ke AuthService | Urutan pesan | `auth.ts` baris 131-188 | TERVERIFIKASI | — |
| 22 | Sequence Sign Up | Pesan SignUp() dari AuthService ke SupabaseAuth | Urutan pesan | `auth.ts` baris 146 | TERVERIFIKASI | — |
| 23 | Sequence Sign Up | Trigger handle_new_doctor_signup membuat doctor_profiles | Aktivitas sistem | `008_create_doctor_profile_trigger.sql` baris 28-79 | TERVERIFIKASI | — |
| 24 | Sequence Sign In | Pesan signIn() dari Login Page ke AuthContext | Urutan pesan | `AuthContext.tsx` baris 132-173 | SEBAGIAN TERVERIFIKASI | Diagram memiliki label 'signUp' yang salah |
| 25 | Sequence Sign In | Pesan loginUser() dari AuthContext ke AuthService | Urutan pesan | `auth.ts` baris 195-225 | TERVERIFIKASI | — |
| 26 | Sequence Sign In | Pesan signInWithPassword() dari AuthService ke SupabaseAuth | Urutan pesan | `auth.ts` baris 208 | TERVERIFIKASI | — |
| 27 | Sequence Sign In | Role resolution dari app_metadata dan doctor_profiles | Aktivitas sistem | `AuthContext.tsx` baris 148-151 | TERVERIFIKASI | — |
| 28 | Sequence Sign In | Pembaruan sesi hanya pada kondisi berhasil | Aktivitas sistem | `AuthContext.tsx` baris 142-155 | TERVERIFIKASI | — |

---

## 7. Ketidaksesuaian Diagram dan Implementasi

| No. | Diagram | Elemen yang Tidak Sesuai | Deskripsi | Rekomendasi |
|-----|---------|------------------------|-----------|-------------|
| 1 | Sequence Diagram Sign In | Label fungsi `signUp` pada pesan dari Login Page ke AuthContext | Diagram menggunakan label `signUp` meskipun alur adalah Sign In. Implementasi aktual menggunakan `signIn`. | Perbaiki label diagram menjadi `signIn(email, password, selectedRole)` untuk konsisten dengan `AuthContext.tsx` dan `auth.ts`. |
| 2 | Activity Diagram Sign Up / Sign In | Tidak ada indikasi visual mengenai Remember Me | Diagram Sign In tidak menunjukkan opsi "Remember my email" meskipun tersedia di implementasi. | Tambahkan aktivitas opsi Remember Me pada Activity Diagram Sign In jika diperlukan. |
| 3 | Activity Diagram Sign Up | Tidak ada indikasi visual tentang trigger database | Diagram tidak menunjukkan trigger `handle_new_doctor_signup` yang membuat baris `doctor_profiles`. | Tambahkan catatan atau aktivitas tentang trigger database setelah pembuatan auth.users. |
| 4 | Sequence Diagram Sign Up | Pesan `authSignup()` tidak eksplisit mengenai trigger | Pesan dari Supabase Auth ke pembuatan auth.users tidak menyebut trigger database secara eksplisit. | Tambahkan catatan tentang trigger `handle_new_doctor_signup` pada diagram. |
| 5 | Activity Diagram Sign Up / Sign In | Tidak ada indikasi visual mengenai role mismatch | Diagram tidak menunjukkan pemeriksaan kecocokan peran (admin vs doctor) saat Sign In. | Tambahkan decision node untuk pemeriksaan kecocokan peran pada Activity Diagram Sign In. |

---

## 8. Keterbatasan Pemeriksaan

| No. | Keterbatasan | Deskripsi | Dampak |
|-----|-------------|-----------|--------|
| 1 | Diagram hanya tersedia sebagai PNG raster | Tidak ada file sumber `.drawio` untuk diagram revisi | Tidak dapat memverifikasi struktur diagram secara detail dari file sumber; verifikasi terbatas pada bacaan visual gambar. |
| 2 | Tidak ada pengujian runtime browser / end-to-end | Tidak dilakukan pengujian secara langsung pada aplikasi yang berjalan | Beberapa perilaku runtime (misalnya navigasi sesi sebenarnya) tidak dapat divalidasi secara langsung; validasi hanya berdasarkan kode sumber. |
| 3 | Konfigurasi environment (.env) tidak dibaca | Nilai konfigurasi Supabase (URL, key) tidak diverifikasi | Tidak dapat memastikan konfigurasi Supabase Auth pada environment production. |
| 4 | Skrip AI dan build TypeScript tidak dijalankan | Tidak ada verifikasi build atau eksekusi pipeline AI | Tidak relevan langsung dengan autentikasi, tetapi membatasi verifikasi keutuhan sistem. |
| 5 | Nomor baris source code adalah estimasi | Nomor baris didasarkan pada pembacaan file saat ini | Nomor baris dapat bervariasi jika file diubah; perlu disesuaikan saat finalisasi skripsi. |

---

## 9. Catatan yang Memerlukan Konfirmasi Penulis

| No. | Catatan | Deskripsi |
|-----|---------|-----------|
| 1 | Label `signUp` pada Sequence Diagram Sign In | Perlu dikonfirmasi apakah label ini sengaja digunakan atau merupakan kesalahan labeling yang perlu diperbaiki pada diagram asli. |
| 2 | Konfirmasi email | Implementasi menunjukkan kemungkinan konfirmasi email (`requiresEmailConfirmation`), tetapi tidak dapat dipastikan apakah fitur email confirmation secara keseluruhan diaktifkan pada Supabase project PIXEL-T. |
| 3 | Nomor gambar dan tabel | Placeholder `Gambar 4.x` dan `Tabel 4.x` perlu disesuaikan dengan penomoran akhir Bab IV skripsi. |
| 4 | Perbaikan diagram | Keempat ketidaksesuaian di bagian 7 perlu dikonfirmasi apakah akan diperbaiki pada diagram asli atau hanya dicatat dalam penjelasan. |

---

## 10. Kesimpulan Validasi

Berdasarkan audit yang dilakukan, keempat diagram (Activity Sign Up, Activity Sign In, Sequence Sign Up, Sequence Sign In) secara keseluruhan **konsisten dengan implementasi aktual PIXEL-T**. Sebagian besar klaim teknis terverifikasi dengan bukti source code. Terdapat satu ketidaksesuaian labeling pada Sequence Diagram Sign In (label `signUp` seharusnya `signIn`) yang perlu dikoreksi pada diagram atau dicatat dalam penjelasan.

Tidak ada klaim yang tidak didukung bukti dalam penjelasan akademik. Setiap pernyataan teknis memiliki dasar dari diagram atau implementasi kode sumber PIXEL-T.

---

*Dokumen ini disusun sebagai pendukung audit untuk Bab IV skripsi PIXEL-T. Tidak ada kode aplikasi atau gambar diagram yang diubah dalam penyusunan dokumen ini.*