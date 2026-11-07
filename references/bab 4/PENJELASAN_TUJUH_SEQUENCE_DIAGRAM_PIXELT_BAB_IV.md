# DOKUMEN PENJELASAN AKADEMIK TUJUH SEQUENCE DIAGRAM PIXEL-T
## Naskah Siap Salin untuk Bab IV Skripsi S1

> **Catatan Penomoran bagi Penulis Skripsi:**  
> Penomoran subbab `4.x` dan nomor gambar `Gambar 4.x` merupakan *placeholder*. Sesuaikan dengan urutan yang berlaku pada draf Bab IV skripsi Anda.

---

### 4.x Sequence Diagram

*Sequence Diagram* digunakan untuk memodelkan aspek dinamis sistem PIXEL-T dengan menggambarkan urutan interaksi dan komunikasi antarkomponen secara kronologis berdasarkan garis waktu (*lifeline*). Pada sistem PIXEL-T, *Sequence Diagram* memetakan kolaborasi antara pengguna (*User*), antarmuka berbasis React (*Frontend*), lapisan manajemen status autentikasi (*AuthContext*), lapisan layanan (*Service Layer*), server API berbasis Flask (*Backend*), mesin inferensi kecerdasan buatan (*Pipeline AI*), serta layanan Supabase yang mengelola autentikasi, basis data PostgreSQL, dan penyimpanan objek.

Pembahasan *Sequence Diagram* sistem PIXEL-T terbagi menjadi tujuh skenario: pendaftaran akun (*Sign Up*), masuk sistem (*Sign In*), pengunggahan citra (*Upload Image*), segmentasi citra (*Segmentation*), penelusuran riwayat (*History*), pengelolaan profil dokter (*Doctor Profile*), dan keluar sistem (*Sign Out*).

---

#### 4.x.1 Sequence Diagram Sign Up

Gambar 4.x menunjukkan *Sequence Diagram Sign Up* yang memodelkan rangkaian interaksi dalam proses registrasi akun baru pada sistem PIXEL-T.

```
[Sisipkan Gambar: Sequence Diagram - Sign Up.drawio.png]
Gambar 4.x Sequence Diagram Sign Up
```

Proses pendaftaran dimulai saat pengguna membuka halaman registrasi dan sistem menampilkan formulir pendaftaran. Pengguna mengisi enam kolom — nama lengkap, alamat email, nama rumah sakit, bidang keahlian, kata sandi, dan konfirmasi kata sandi — lalu menekan tombol pendaftaran. Komponen `Register.tsx` menjalankan validasi formulir sisi klien: memastikan seluruh kolom terisi, format email memenuhi pola yang ditentukan, kata sandi minimal 6 karakter, dan konfirmasi kata sandi cocok.

Apabila validasi gagal, antarmuka menampilkan pesan kesalahan spesifik tanpa melanjutkan permintaan ke server. Apabila validasi lolos, antarmuka memanggil fungsi `signUp` pada *AuthContext*, yang meneruskan ke layanan autentikasi (`auth.ts`) untuk mengeksekusi `supabase.auth.signUp` beserta metadata pengguna (nama, institusi, spesialisasi).

Supabase Auth memproses permintaan dan mengembalikan hasil. Apabila terjadi kegagalan — seperti email telah terdaftar, kata sandi terlalu lemah, atau kesalahan jaringan — layanan mengonversi kode kesalahan teknis menjadi pesan berbahasa Indonesia yang informatif melalui `formatAuthError()` dan menampilkannya kepada pengguna.

Apabila pendaftaran berhasil, Supabase Auth mengembalikan data pengguna. Sistem mengevaluasi keberadaan sesi (`alt`): apabila sesi langsung aktif, *AuthContext* memperbarui status pengguna dan antarmuka menampilkan konfirmasi bahwa akun telah dibuat dan sesi sudah aktif; apabila sesi belum aktif karena konfirmasi email diperlukan, antarmuka menampilkan notifikasi agar pengguna memeriksa kotak masuk email.

---

#### 4.x.2 Sequence Diagram Sign In

Gambar 4.x menunjukkan *Sequence Diagram Sign In* yang memodelkan alur autentikasi pengguna saat masuk ke sistem PIXEL-T.

```
[Sisipkan Gambar: Sequence Diagram - Sign In.drawio.png]
Gambar 4.x Sequence Diagram Sign In
```

Alur masuk sistem dimulai ketika pengguna membuka halaman *Sign In* dan sistem menampilkan formulir. Pengguna memasukkan email dan kata sandi, kemudian menekan tombol masuk. Komponen `Login.tsx` melakukan validasi masukan lokal untuk memastikan kedua kolom tidak kosong.

Setelah masukan tervalidasi, antarmuka memanggil `signIn` pada *AuthContext*, yang meneruskan ke layanan autentikasi (`auth.ts`) untuk mengeksekusi `supabase.auth.signInWithPassword`. Supabase Auth memverifikasi kredensial dan mengembalikan hasil autentikasi.

Apabila autentikasi ditolak — karena email tidak ditemukan, kata sandi keliru, atau akun belum dikonfirmasi — layanan menyaring kesalahan melalui `formatAuthError()` dan antarmuka menampilkan notifikasi galat. Apabila kredensial sah, Supabase Auth menerbitkan token akses JWT dan objek sesi. *AuthContext* memperbarui status pengguna secara global dan antarmuka mengarahkan pengguna ke halaman utama (*Dashboard*) atau halaman tujuan yang tersimpan sebelumnya.

---

#### 4.x.3 Sequence Diagram Upload Image

Gambar 4.x menunjukkan *Sequence Diagram Upload Image* yang menggambarkan proses pengunggahan berkas citra kolonoskopi ke server sistem PIXEL-T.

```
[Sisipkan Gambar: Sequence Diagram - Upload Image.drawio.png]
Gambar 4.x Sequence Diagram Upload Image
```

Proses pengunggahan dimulai saat pengguna memilih berkas citra dari perangkat lokal pada halaman *New Analysis*. *Frontend* segera melakukan validasi berkas sisi klien yang mencakup pemeriksaan ekstensi (`.jpg`, `.jpeg`, `.png`), tipe MIME, dan batas ukuran maksimal 10 MB.

Apabila berkas tidak memenuhi syarat, antarmuka menampilkan pesan kesalahan dan menolak pemrosesan. Apabila berkas valid, antarmuka menampilkan pratinjau citra dan mengonfirmasi bahwa berkas siap dianalisis. Pengguna menekan tombol untuk memulai analisis.

Antarmuka mengambil sesi autentikasi aktif, menyusun berkas citra ke dalam `FormData`, dan mengirimkannya bersama token JWT ke *backend* melalui *endpoint* `POST /api/analysis`. *Backend* memverifikasi keabsahan token, melakukan validasi integritas citra di sisi server, menyimpan berkas ke *Supabase Storage*, membuat rekaman analisis pada tabel `analyses` berstatus `processing`, dan mengantrekan pekerjaan inferensi.

Apabila antrean penuh, *backend* menghapus rekaman yang baru dibuat dan mengembalikan HTTP 429 dengan pesan yang sesuai. Apabila berhasil, *backend* mengembalikan HTTP 202 *Accepted* beserta `analysis_id` dan status awal. Antarmuka menerima konfirmasi dan mulai melakukan *polling* untuk memantau perkembangan analisis.

---

#### 4.x.4 Sequence Diagram Segmentation

Gambar 4.x menunjukkan *Sequence Diagram Segmentation* yang memodelkan siklus lengkap proses inferensi segmentasi AI dan visualisasi Grad-CAM yang berjalan secara asinkron pada sistem PIXEL-T.

```
[Sisipkan Gambar: Sequence Diagram - Segmentation.drawio.png]
Gambar 4.x Sequence Diagram Segmentation
```

Alur segmentasi berkesinambungan dengan proses pengunggahan. Setelah *backend* menerima permintaan dan membuat rekaman `analyses` berstatus `processing`, *backend* menyimpan citra ke Supabase Storage dan mengantrekan tugas. Segera setelahnya, *backend* mengembalikan HTTP 202 ke *frontend* sehingga antarmuka tidak mengalami pemblokiran (*non-blocking UI*).

Secara bersamaan di latar belakang (*background worker*), *backend* memulai pipeline inferensi pada komponen *Pipeline AI*. Pipeline menjalankan serangkaian tahapan secara sekuensial:

1. **Pra-pemrosesan:** Dekode citra, konversi ke RGB, dan normalisasi ke dimensi 512×512 piksel.
2. **Inferensi segmentasi:** Eksekusi model U-Net + ResNet50 untuk menghasilkan masker biner probabilitas keberadaan polip kolorektal.
3. **Pasca-pemrosesan:** Operasi morfologi untuk menyempurnakan kontur masker.
4. **Grad-CAM:** Kalkulasi gradien pada lapisan konvolusi target untuk menghasilkan peta panas atensi visual model.
5. **Penyusunan artefak:** Pembuatan empat berkas keluaran dalam format PNG.

Pipeline mengembalikan `PipelineResult` ke *backend*. Apabila berhasil, *backend* mengunggah keempat artefak ke *Supabase Storage* dan memperbarui rekaman basis data dengan `status = completed` beserta metadata metrik. Apabila gagal, *backend* memperbarui status menjadi `failed` dan menyimpan kode galat.

Sementara itu, *frontend* melakukan *polling* berkala dengan mengirim `GET /api/analysis/{id}`. *Backend* membaca status terkini dari basis data dan mengembalikannya beserta *Signed URL* berkas artefak. Apabila status `failed`, antarmuka menampilkan pesan bahwa analisis tidak dapat diselesaikan. Apabila status `completed`, antarmuka menampilkan masker segmentasi polip, citra *overlay*, peta Grad-CAM, dan metrik pengukuran kepada dokter.

---

#### 4.x.5 Sequence Diagram History

Gambar 4.x menunjukkan *Sequence Diagram History* yang menggambarkan alur penelusuran riwayat analisis, peninjauan detail, dan pengelolaan penghapusan sesi pada sistem PIXEL-T.

```
[Sisipkan Gambar: Sequence Diagram - History.drawio.png]
Gambar 4.x Sequence Diagram History
```

Penelusuran riwayat dimulai saat pengguna membuka halaman riwayat. Komponen `History.tsx` mengirimkan permintaan ke *Backend* (Flask API) melalui *endpoint* `GET /api/history`. *Backend* mengambil data riwayat milik pengguna aktif dari basis data Supabase, membuat *Signed URL* untuk gambar pratinjau, dan mengembalikan daftar riwayat beserta URL tersebut ke *frontend*.

*Frontend* mengevaluasi data yang diterima: apabila koneksi gagal, antarmuka menampilkan *error state*; apabila daftar kosong, antarmuka menampilkan pesan bahwa belum ada riwayat analisis; apabila data tersedia, antarmuka menampilkan tabel daftar riwayat.

Terdapat dua blok interaksi opsional. Pertama (`opt`), pengguna dapat melakukan pencarian dan filter lokal — berdasarkan nama berkas, status, atau tanggal — serta paginasi, yang seluruhnya berjalan di sisi klien tanpa permintaan baru ke server. Pengguna kemudian memilih satu rekaman dan *frontend* mengirimkan `GET /api/analysis/{id}` ke *backend*. *Backend* mengambil detail rekaman dan menghasilkan *Signed URL* untuk seluruh artefak, lalu mengembalikannya ke *frontend* untuk ditampilkan.

Kedua (`opt`), pengguna dapat menghapus rekaman. *Frontend* menampilkan dialog konfirmasi. Apabila pengguna membatalkan, dialog ditutup tanpa perubahan. Apabila pengguna mengonfirmasi, *frontend* mengirimkan `DELETE /api/history/{id}` ke *backend*. *Backend* memverifikasi kepemilikan, menghapus rekaman dari basis data, dan menghapus berkas artefak dari *Supabase Storage*. *Frontend* memperbarui daftar sesuai respons yang diterima.

---

#### 4.x.6 Sequence Diagram Doctor Profile

Gambar 4.x menunjukkan *Sequence Diagram Doctor Profile* yang memodelkan alur pemuatan profil dokter, penyajian statistik aktivitas, serta pengeditan dan penyimpanan data profil pada sistem PIXEL-T.

```
[Sisipkan Gambar: Sequence Diagram - Doctor Profile.drawio.png]
Gambar 4.x Sequence Diagram Doctor Profile
```

Alur dimulai saat pengguna mengakses halaman profil. Komponen `DoctorProfile.tsx` memanggil `fetchDoctorProfile()` dari *Profile Service* (`profile.ts`), yang mengeksekusi kueri ke tabel `doctor_profiles` pada Supabase berdasarkan `user_id` pengguna aktif. Apabila profil belum tersedia pada tabel, layanan menggunakan data cadangan (*fallback*) dari metadata akun Supabase Auth sebagai data awal.

Secara bersamaan, *frontend* memanggil *Backend* melalui `GET /api/history` untuk mengambil riwayat analisis pengguna. Data riwayat dikembalikan ke *frontend*, di mana sistem menghitung metrik agregat dan ringkasan statistik aktivitas. Pengguna kemudian disajikan halaman profil yang memadukan informasi identitas personal, data profesional, serta kartu statistik.

Terdapat blok interaksi opsional (`opt`) untuk pengeditan profil. Apabila pengguna menekan tombol *"Edit Profile"*, *frontend* menampilkan modal formulir. Pengguna dapat membatalkan tindakan dengan menutup modal tanpa menyimpan perubahan. Apabila pengguna menyimpan perubahan, *frontend* meneruskan data ke *Profile Service* yang menjalankan `validateProfileData()` untuk memverifikasi kelengkapan dan format data.

Apabila validasi gagal, layanan mengembalikan pesan galat dan antarmuka menampilkannya pada formulir modal. Apabila validasi berhasil, layanan mengeksekusi operasi *upsert* ke tabel `doctor_profiles` dan memperbarui metadata nama pada Supabase Auth melalui `supabase.auth.updateUser()`. Apabila penyimpanan berhasil, modal ditutup dan antarmuka menampilkan notifikasi keberhasilan serta data profil yang diperbarui. Apabila penyimpanan gagal, antarmuka menampilkan notifikasi gagal pada modal.

---

#### 4.x.7 Sequence Diagram Sign Out

Gambar 4.x menunjukkan *Sequence Diagram Sign Out* yang memodelkan alur pemutusan sesi dan pembersihan status autentikasi dari sistem PIXEL-T.

```
[Sisipkan Gambar: Sequence Diagram - Sign Out.drawio.png]
Gambar 4.x Sequence Diagram Sign Out
```

Proses keluar dimulai ketika pengguna menekan tombol *"Sign Out"* pada antarmuka navigasi (*AppShell*). Untuk mencegah tindakan yang tidak disengaja, komponen menampilkan modal konfirmasi. Pengguna mengonfirmasi dengan menekan tombol *"Yes"*.

*AppShell* memanggil `signOut()` pada *AuthContext*, yang meneruskan ke `logoutUser()` pada *Auth Service*. Layanan mengeksekusi `supabase.auth.signOut()` ke server Supabase Auth untuk mengakhiri sesi aktif. Supabase Auth mengembalikan status terminasi sesi.

*AuthContext* menerima respons dan membersihkan variabel status pengguna dan sesi menjadi `null`, terlepas dari hasil respons Supabase. *AppShell* kemudian mengarahkan navigasi ke halaman masuk (`/login`) secara eksplisit. Selain itu, *listener* `onAuthStateChange` pada *AuthContext* menerima notifikasi dari Supabase bahwa sesi telah berakhir dan menyinkronkan status secara otomatis sebagai lapisan sinkronisasi kedua. Seluruh rute privat kembali terlindungi dari akses tanpa autentikasi.

---
