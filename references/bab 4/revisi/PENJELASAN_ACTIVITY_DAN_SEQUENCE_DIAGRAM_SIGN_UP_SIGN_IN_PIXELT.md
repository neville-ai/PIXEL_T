# PENJELASAN ACTIVITY DIAGRAM DAN SEQUENCE DIAGRAM SIGN UP DAN SIGN IN PIXEL-T

Dokumen ini berisi penjelasan akademik untuk Bab IV skripsi S1 dengan judul penelitian:

**“TRANSFER LEARNING DAN EXPLAINABLE AI UNTUK SEGMENTASI POLIP USUS MENGGUNAKAN CITRA ENDOSKOPI BERBASIS WEB.”**

Penjelasan di bawah ini membahas empat diagram:

1. Activity Diagram Sign Up.
2. Activity Diagram Sign In.
3. Sequence Diagram Sign Up.
4. Sequence Diagram Sign In.

Empat diagram tersebut berada di folder `references\bab 4\revisi` dalam format gambar PNG.

> **Petunjuk bagi Penulis:** Nomor subbab `4.x` dan nomor gambar `Gambar 4.x` merupakan *placeholder* yang disesuaikan dengan penomoran akhir skripsi. Semua uraian disusun berdasarkan diagram yang tersedia dan implementasi kode sumber aktual PIXEL-T.

---

## 4.x Pendahuluan: Mekanisme Autentikasi PIXEL-T

PIXEL-T merupakan aplikasi web berbasis kecerdasan buatan yang dirancang untuk mendukung segmentasi polip usus pada citra endoskopi melalui pendekatan Transfer Learning dan Explainable AI. Sebelum pengguna dapat mengakses fitur klinis aplikasi, pengguna harus terlebih dahulu melalui proses pendaftaran akun dan masuk ke sistem. Mekanisme ini merupakan bagian dari perancangan sistem yang bertanggung jawab atas pengelolaan akses pengguna dan pengawasan sesi autentikasi.

Pada sistem PIXEL-T, proses autentikasi dikembangkan dengan memanfaatkan layanan Supabase Auth sebagai penyedia manajemen identitas dan akses. Frontend aplikasi dibangun dengan React dan TypeScript, sedangkan backend menggunakan Flask. Proses Sign Up dan Sign In digambarkan melalui Activity Diagram dan Sequence Diagram untuk memperlihatkan alur interaksi antara pengguna, komponen frontend, dan layanan autentikasi.

Dokumen ini menyajikan penjelasan akademik untuk keempat diagram tersebut dengan tetap mempertahankan konsistensi antara Activity Diagram dan Sequence Diagram, serta memastikan setiap uraian sesuai dengan implementasi aktual yang terdapat dalam kode sumber PIXEL-T.

---

## 4.x Activity Diagram Sign Up

### 4.x.1 Pengantar

Activity Diagram Sign Up menggambarkan alur proses pendaftaran akun baru oleh calon pengguna sistem PIXEL-T. Diagram ini memperlihatkan aktivitas yang dilakukan pengguna dari membuka halaman pendaftaran hingga hasil pendaftaran dikonfirmasikan. Setiap aktivitas dan decision node pada diagram merepresentasikan langkah konkret yang dijalankan oleh komponen frontend dan layanan autentikasi sistem.

### 4.x.2 Tujuan Diagram

Tujuan Activity Diagram Sign Up adalah untuk menggambarkan alur kerja pendaftaran akun pada sistem PIXEL-T secara berurutan, termasuk validasi input, pemanggilan layanan autentikasi, penanganan hasil pendaftaran, dan kondisi percabangan yang menentukan apakah pengguna mendapatkan sesi autentikasi atau perlu melalui konfirmasi email.

### 4.x.3 Aktor

Aktor dalam diagram ini adalah **Calon Pengguna**, yang merepresentasikan individu yang belum memiliki akun PIXEL-T dan bermaksud mendaftar sebagai tenaga medis atau dokter.

### 4.x.4 Alur Proses

Proses pendaftaran diawali ketika calon pengguna membuka halaman pendaftaran (`/register`). Sistem menampilkan formulir pendaftaran yang meminta data berikut:

1. Nama lengkap.
2. Alamat email pengguna.
3. Nama rumah sakit.
4. Bidang keahlian dokter.
5. Kata sandi.
6. Konfirmasi kata sandi.

Setelah calon pengguna mengisi semua kolom formulir, sistem melakukan validasi input dengan kriteria berikut:

- Nama lengkap tidak boleh kosong.
- Alamat email tidak boleh kosong dan harus sesuai format email yang valid.
- Nama rumah sakit tidak boleh kosong.
- Bidang keahlian dokter tidak boleh kosong.
- Kata sandi tidak boleh kosong dan harus memiliki minimal 6 karakter.
- Konfirmasi kata sandi harus sama dengan kata sandi yang dimasukkan.

Jika validasi gagal, sistem menampilkan pesan kesalahan dan proses pendaftaran tidak dilanjutkan. Pengguna diminta memperbaiki input yang salah sebelum mencoba kembali.

Jika validasi berhasil, sistem mengirimkan permintaan pendaftaran ke layanan autentikasi Supabase Auth melalui fungsi `signUp()` pada `AuthContext`, yang kemudian memanggil `registerUser()` pada `AuthService`. Layanan autentikasi memproses permintaan dengan memanggil `supabase.auth.signUp()` dan menyertakan metadata pengguna (nama lengkap, nama rumah sakit, dan bidang keahlian) sebagai `auth metadata`.

Percabangan berikutnya bergantung pada respons layanan autentikasi:

**Jika pendaftaran berhasil ditanggapi (user berhasil dibuat):**

- Jika layanan autentikasi mengembalikan sesi autentikasi, sistem memperbarui state autentikasi aplikasi dengan peran `doctor` dan status akun `pending`. Pengguna diberi pesan bahwa akun berhasil dibuat dan akan dapat diakses setelah disetujui oleh administrator rumah sakit.
- Jika layanan autentikasi tidak mengembalikan sesi (karena akun memerlukan konfirmasi email), sistem memberikan informasi bahwa pendaftaran telah diproses dan menunggu konfirmasi email.

**Jika pendaftaran gagal (terdapat error dari layanan autentikasi):**

- Sistem menampilkan pesan kesalahan sesuai jenis kegagalan (misalnya email sudah terdaftar, kata sandi terlalu lemah, format email tidak valid, atau layanan autentikasi tidak tersedia).
- Pengguna tetap berada di halaman pendaftaran dan dapat mencoba kembali setelah memperbaiki data.

Setiap hasil pendaftaran, baik berhasil maupun gagal, ditampilkan kepada pengguna melalui notifikasi pada antarmuka. Setelah pendaftaran berhasil, pengguna dapat memilih untuk melanjutkan ke halaman masuk (`/login`) atau mendaftar akun lain.

### 4.x.5 Node Akhir

Activity Diagram Sign Up berakhir dengan activity final node yang menunjukkan proses pendaftaran telah selesai, baik dengan hasil pendaftaran yang berhasil maupun gagal.

---

## 4.x Activity Diagram Sign In

### 4.x.1 Pengantar

Activity Diagram Sign In menggambarkan alur proses pengguna masuk ke sistem PIXEL-T. Diagram ini memperlihatkan aktivitas dari membuka halaman masuk hingga pengalihan halaman sesuai peran dan status akun pengguna setelah autentikasi berhasil.

### 4.x.2 Tujuan Diagram

Tujuan Activity Diagram Sign In adalah untuk menggambarkan alur kerja autentikasi masuk ke sistem, termasuk validasi formulir, pemeriksaan kredensial melalui layanan autentikasi, pembaruan status sesi, penanganan kegagalan autentikasi, dan pengalihan ke halaman yang sesuai.

### 4.x.3 Aktor

Aktor dalam diagram ini meliputi:

- **Calon Pengguna**: individu yang belum memiliki sesi aktif dan ingin masuk ke sistem.
- **Dokter / Tenaga Medis**: pengguna yang telah memiliki akun dokter.
- **Admin**: pengguna yang mengelola sistem.

### 4.x.4 Alur Proses

Proses masuk diawali ketika pengguna membuka halaman masuk (`/login`). Sistem menampilkan formulir masuk yang meminta:

1. Alamat email.
2. Kata sandi.
3. Pilihan jenis akun (admin atau dokter).
4. Opsi "Remember my email".

Sebelum mengirimkan kredensial, sistem melakukan validasi input dasar:

- Alamat email tidak boleh kosong.
- Kata sandi tidak boleh kosong.

Jika opsi "Remember my email" diaktifkan, sistem menyimpan alamat email pengguna ke penyimpanan lokal browser. Kata sandi **tidak** disimpan dalam penyimpanan lokal. Opsi ini hanya mengingat alamat email untuk kemudahan pengisian ulang pada kunjungan berikutnya.

Setelah validasi berhasil, pengguna menekan tombol masuk dan sistem memanggil fungsi `signIn()` pada `AuthContext`, yang kemudian memanggil `loginUser()` pada `AuthService`. Fungsi ini meneruskan alamat email dan kata sandi ke `supabase.auth.signInWithPassword()` untuk memverifikasi kredensial melalui layanan Supabase Auth.

Percabangan berikutnya bergantung pada hasil verifikasi kredensial:

**Jika kredensial valid:**

- Layanan autentikasi mengembalikan pengguna dan sesi autentikasi.
- Sistem memperbarui state autentikasi aplikasi dengan menyimpan informasi pengguna dan sesi.
- Sistem menentukan peran dan status akun pengguna:
  - Jika `app_metadata.role` adalah `admin`, peran ditetapkan sebagai `admin`.
  - Bukan admin, sistem memeriksa tabel `doctor_profiles` untuk menentukan peran dan status akun (`pending`, `approved`, atau `rejected`).
- Sistem melakukan pemeriksaan kecocokan peran antara pilihan jenis akun pengguna dan peran aktual. Jika tidak cocok, sistem menampilkan pesan kesalahan dan proses masuk tidak dilanjutkan.
- Jika peran cocok, sistem memeriksa status akun:
  - Admin diarahkan ke halaman `/admin`.
  - Dokter dengan status `approved` diarahkan ke halaman `/dashboard`.
  - Dokter dengan status `pending` dikembalikan ke halaman masuk dengan indikasi akun menunggu persetujuan.
  - Dokter dengan status `rejected` dikembalikan ke halaman masuk dengan indikasi pendaftaran ditolak.

**Jika kredensial tidak valid:**

- Sistem menampilkan pesan kesalahan autentikasi (misalnya email atau kata sandi salah, email belum dikonfirmasi, atau layanan autentikasi tidak tersedia).
- Pengguna tetap berada di halaman masuk dan dapat mencoba kembali.

Setiap hasil masuk, baik berhasil maupun gagal, ditampilkan kepada pengguna melalui notifikasi pada antarmuka.

### 4.x.5 Node Akhir

Activity Diagram Sign In berakhir dengan activity final node yang menunjukkan proses masuk telah selesai, baik dengan hasil masuk yang berhasil (pengguna diarahkan ke halaman yang sesuai) maupun gagal (pengguna tetap di halaman masuk).

---

## 4.x Sequence Diagram Sign Up

### 4.x.1 Pengantar

Sequence Diagram Sign Up menggambarkan urutan interaksi antara komponen-komponen sistem selama proses pendaftaran akun. Diagram ini memperlihatkan alur pesan dari pengguna hingga layanan autentikasi eksternal dan balasan yang diterima oleh frontend.

### 4.x.2 Aktor dan Lifeline

Aktor dan lifeline yang terlibat dalam diagram ini adalah:

- **User**: calon pengguna yang memulai proses pendaftaran.
- **Register Page**: halaman pendaftaran yang menerima input dari pengguna.
- **AuthContext**: komponen pengelolaan state autentikasi aplikasi.
- **AuthService**: lapisan layanan autentikasi frontend.
- **SupabaseAuth**: layanan autentikasi eksternal (Supabase Auth).

### 4.x.3 Urutan Pesan

Urutan interaksi dalam proses pendaftaran adalah sebagai berikut:

1. **User mengakses formulir pendaftaran** (`accessesFormSignUp()`): Pengguna membuka halaman pendaftaran dan sistem menampilkan formulir untuk diisi.

2. **User mengirimkan formulir pendaftaran** (`submitFormSignUp()`): Setelah mengisi formulir, pengguna menekan tombol pendaftaran untuk mengirimkan data.

3. **Register Page melakukan validasi input** (`inputValidation()`): Halaman pendaftaran memvalidasi semua kolom formulir (nama, email, rumah sakit, bidang keahlian, kata sandi, dan konfirmasi kata sandi) sebelum melanjutkan.

4. **Register Page memanggil AuthContext** (`signUp()`): Jika validasi berhasil, halaman pendaftaran memanggil fungsi `signUp()` pada `AuthContext` dengan menyertakan data formulir.

5. **AuthContext memanggil AuthService** (`RegisterUser()`): `AuthContext` meneruskan permintaan pendaftaran ke `AuthService` melalui fungsi `registerUser()`.

6. **AuthService memanggil Supabase Auth** (`SignUp()`): `AuthService` memanggil `supabase.auth.signUp()` untuk membuat akun baru di layanan autentikasi, beserta metadata pengguna.

7. **Supabase Auth membuat auth users** (`authSignup()`): Layanan Supabase Auth memproses pembuatan akun pengguna baru. Setelah berhasil, trigger database `handle_new_doctor_signup` secara otomatis membuat baris dalam tabel `doctor_profiles` dengan peran `doctor` dan status akun `pending`.

8. **Supabase Auth mengembalikan respons**: Layanan autentikasi mengembalikan respons yang berisi objek pengguna dan sesi (jika tersedia) atau pesan kesalahan.

Percabangan berikutnya bergantung pada kondisi respons:

- **Registration Failed**: Jika terdapat error dari layanan autentikasi, pesan kesalahan dikembalikan ke frontend dan ditampilkan kepada pengguna.
- **Registration Successful**: Jika pendaftaran berhasil diproses, alur melanjutkan ke pemeriksaan sesi.
- **Session Available**: Jika layanan autentikasi mengembalikan sesi, sistem memperbarui state autentikasi aplikasi dengan peran `doctor` dan status akun `pending`, lalu memberikan pesan sukses kepada pengguna.
- **Account Available**: Sistem mengonfirmasi bahwa akun telah tersedia dalam sistem.
- **Requires Email Confirmation**: Jika layanan autentikasi tidak mengembalikan sesi (karena memerlukan konfirmasi email), sistem memberikan informasi bahwa pendaftaran telah diproses dan menunggu konfirmasi email.

### 4.x.4 Pembaruan State dan Sesi

Jika sesi autentikasi tersedia setelah pendaftaran, `AuthContext` memperbarui state `user`, `session`, `role`, dan `accountStatus`. Jika sesi tidak tersedia, state autentikasi tidak diperbarui dan pengguna diberi informasi tentang konfirmasi email.

### 4.x.5 Notifikasi dan Pengalihan

Setiap hasil pendaftaran ditampilkan kepada pengguna melalui notifikasi pada antarmuka. Setelah pendaftaran berhasil, pengguna dapat melanjutkan ke halaman masuk.

---

## 4.x Sequence Diagram Sign In

### 4.x.1 Pengantar

Sequence Diagram Sign In menggambarkan urutan interaksi antara komponen-komponen sistem selama proses masuk ke aplikasi. Diagram ini memperlihatkan alur pesan dari pengguna hingga layanan autentikasi eksternal dan balasan yang diterima oleh frontend.

### 4.x.2 Aktor dan Lifeline

Aktor dan lifeline yang terlibat dalam diagram ini adalah:

- **User**: pengguna yang memulai proses masuk.
- **Login Page**: halaman masuk yang menerima kredensial dari pengguna.
- **AuthContext**: komponen pengelolaan state autentikasi aplikasi.
- **AuthService**: lapisan layanan autentikasi frontend.
- **SupabaseAuth**: layanan autentikasi eksternal (Supabase Auth).

### 4.x.3 Urutan Pesan

Urutan interaksi dalam proses masuk adalah sebagai berikut:

1. **User mengakses formulir masuk** (`accessesFormSignIn()`): Pengguna membuka halaman masuk dan sistem menampilkan formulir untuk diisi.

2. **User mengirimkan formulir masuk** (`submitFormSignIn()`): Setelah mengisi email dan kata sandi, pengguna menekan tombol masuk untuk mengirimkan kredensial.

3. **Login Page melakukan validasi input** (`inputValidation()`): Halaman masuk memvalidasi bahwa email dan kata sandi tidak kosong sebelum melanjutkan.

4. **Login Page memanggil AuthContext** (`signIn(email, password, selectedRole)`): Jika validasi berhasil, halaman masuk memanggil fungsi `signIn()` pada `AuthContext` dengan menyertakan email, kata sandi, dan pilihan jenis akun.

   > **Catatan:** Pada diagram, fungsi ini diberi label `signUp` meskipun alur yang dijelaskan adalah Sign In. Ini merupakan ketidaksesuaian labeling yang perlu dikoreksi pada diagram agar sesuai dengan implementasi aktual yang menggunakan `signIn`.

5. **AuthContext memanggil AuthService** (`loginUser()`): `AuthContext` meneruskan permintaan masuk ke `AuthService` melalui fungsi `loginUser()`.

6. **AuthService memanggil Supabase Auth** (`signInWithPassword()`): `AuthService` memanggil `supabase.auth.signInWithPassword()` untuk memverifikasi kredensial pengguna melalui layanan Supabase Auth.

7. **Supabase Auth mengembalikan respons**: Layanan autentikasi mengembalikan respons yang berisi objek pengguna dan sesi jika kredensial valid, atau pesan kesalahan jika kredensial tidak valid.

Percabangan berikutnya bergantung pada hasil verifikasi:

- **Admin**: Jika `app_metadata.role` adalah `admin`, peran ditetapkan sebagai `admin` dan pengguna diarahkan ke halaman admin.
- **Doctor Approved**: Jika peran adalah `doctor` dan status akun adalah `approved`, pengguna diarahkan ke halaman dashboard.
- **Doctor Pending**: Jika peran adalah `doctor` dan status akun adalah `pending`, pengguna dikembalikan ke halaman masuk dengan indikasi akun menunggu persetujuan.
- **Doctor Rejected**: Jika peran adalah `doctor` dan status akun adalah `rejected`, pengguna dikembalikan ke halaman masuk dengan indikasi pendaftaran ditolak.
- **Default / Unsuitable Role**: Jika peran tidak dikenali atau tidak cocok dengan pilihan jenis akun, sistem menampilkan pesan kesalahan mengenai ketidakcocokan jenis akun.

### 4.x.4 Pembaruan Sesi

Jika autentikasi berhasil, `AuthContext` memperbarui state `user`, `session`, `role`, dan `accountStatus`. Pembaruan sesi hanya dilakukan setelah kredensial terverifikasi dan peran/status akun berhasil ditentukan. Jika autentikasi gagal, sesi tidak diperbarui dan pesan kesalahan ditampilkan kepada pengguna.

### 4.x.5 Navigasi

Setiap hasil masuk menentukan arah navigasi berikutnya:

- Admin → halaman admin (`/admin`).
- Dokter approved → halaman dashboard (`/dashboard`).
- Dokter pending / rejected → kembali ke halaman masuk dengan indikasi status.
- Kesalahan autentikasi → tetap di halaman masuk dengan pesan kesalahan.

---

## 4.x Konsistensi Antar Diagram

Activity Diagram dan Sequence Diagram untuk Sign Up dan Sign In saling konsisten dalam hal:

- **Urutan proses**: Aktivitas dalam Activity Diagram sesuai dengan urutan pesan dalam Sequence Diagram.
- **Percabangan validasi**: Kondisi validasi input dan hasil autentikasi memiliki percabangan yang sama pada kedua jenis diagram.
- **Kondisi sesi**: Ketersediaan sesi autentikasi dan konfirmasi email dijelaskan secara terpisah dan tidak disamakan.
- **Tanggung jawab**: Aktivitas pengguna dan proses sistem memiliki pembagian tanggung jawab yang jelas.

Terdapat satu ketidaksesuaian labeling pada Sequence Diagram Sign In, yaitu fungsi `signUp` digunakan meskipun alur yang dijelaskan adalah Sign In. Implementasi aktual menggunakan `signIn` untuk proses masuk. Ini perlu dikoreksi pada diagram agar konsisten dengan kode sumber.

---

*Dokumen ini disusun berdasarkan analisis terhadap keempat diagram di folder `references\bab 4\revisi` dan implementasi kode sumber PIXEL-T. Tidak ada kode aplikasi yang diubah dalam penyusunan dokumen ini.*