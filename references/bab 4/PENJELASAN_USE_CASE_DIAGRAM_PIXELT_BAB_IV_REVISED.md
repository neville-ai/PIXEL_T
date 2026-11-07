# PENJELASAN USE CASE DIAGRAM SISTEM PIXEL-T (BAB IV)

Dokumen ini berisi naskah penjelasan akademik untuk **Bab IV Skripsi S1**, disusun dalam bahasa Indonesia formal dan selaras dengan implementasi kode sumber serta diagram Use Case sistem PIXEL-T.

> **Petunjuk bagi Penulis:** Nomor subbab `4.x` dan nomor gambar `Gambar 4.x` merupakan *placeholder* yang disesuaikan dengan penomoran akhir skripsi.

---

## 4.1 Use Case Diagram

*Use Case Diagram* digunakan untuk menggambarkan fungsi-fungsi yang tersedia pada sistem PIXEL-T serta interaksi antara aktor dengan sistem. Diagram ini memperlihatkan ruang lingkup fungsional aplikasi, termasuk proses pendaftaran akun, autentikasi pengguna, pengunggahan citra, segmentasi, pengelolaan riwayat, pengelolaan profil dokter, dan pengakhiran sesi. Diagramm disusun berdasarkan implementasi aktual aplikasi web PIXEL-T.

Rancangan *Use Case Diagram* sistem PIXEL-T disajikan pada Gambar 4.x berikut:

```
[Sisipkan Gambar: references/bab 4/Use Case Diagram PIXELT.png]
Gambar 4.x Use Case Diagram Sistem PIXEL-T
```

Diagram ini memuat tiga aktor dan tujuh *use case* utama di dalam satu batas sistem berlabel **Sistem PIXEL-T**.

---

## 4.1.1 Aktor

Aktor merepresentasikan entitas eksternal yang berinteraksi dengan sistem. PIXEL-T memiliki tiga aktor yang dibedakan berdasarkan status autentikasi dan hak aksesnya.

### Calon Pengguna

**Calon Pengguna** adalah individu yang belum memiliki sesi autentikasi aktif. Aktor ini merepresentasikan dokter yang bermaksud mendaftar ke sistem. Calon Pengguna hanya dapat menjalankan **Sign Up** dan **Sign In**. Pendaftaran melalui halaman `/register` bersifat khusus dokter; tidak terdapat jalur pendaftaran publik untuk peran admin.

### Dokter / Tenaga Medis

**Dokter / Tenaga Medis** adalah tenaga medis yang telah memiliki akun dan berstatus klinis. Dokter dapat menjalankan **Sign In**, **Sign Out**, **Upload Image**, **Segmentation**, **History**, dan **Doctor Profile**.

### Admin

**Admin** adalah pengelola sistem yang dapat menjalankan **Sign In** dan **Sign Out**. Admin tidak memiliki fitur klinis seperti pengunggahan citra atau segmentasi.

---

## 4.1.2 Tujuh Use Case Utama

Berikut diuraikan tujuh *use case* utama beserta aktor yang terlibat dan deskripsi perilakunya.

### Sign Up

**Aktor:** Calon Pengguna.

**Deskripsi:** Calon pengguna mengakses halaman pendaftaran, mengisi formulir pendaftaran, dan mengirimkannya. Sistem memvalidasi data yang dimasukkan, kemudian memproses permintaan pendaftaran melalui layanan autentikasi. Apabila pendaftaran berhasil, akun dibuat dan sistem menampilkan konfirmasi. Pengguna kemudian dapat melakukan Sign In untuk masuk ke sistem.

**Tabel 4.x — Deskripsi Use Case Sign Up**

| Bagian | Keterangan |
|--------|------------|
| Actor | Calon Pengguna |
| Trigger & Type | Pengguna mengakses halaman pendaftaran dan mengirimkan formulir pendaftaran. Tipe: *User-initiated*, *Synchronous*. |
| Pre-Conditions | Pengguna belum memiliki akun PIXEL-T dan belum berada dalam sesi autentikasi yang aktif. |
| Normal Course | 1. Pengguna membuka halaman pendaftaran.<br>2. Sistem menampilkan formulir pendaftaran.<br>3. Pengguna mengisi data diri dan kredensial akun.<br>4. Pengguna menekan tombol pendaftaran untuk mengirimkan permintaan.<br>5. Sistem melakukan validasi data yang dimasukkan.<br>6. Sistem memproses permintaan pendaftaran melalui layanan autentikasi.<br>7. Sistem menampilkan konfirmasi bahwa akun telah berhasil didaftarkan.<br>8. Pengguna diarahkan ke halaman Sign In. |
| Post Condition | Akun pengguna berhasil didaftarkan dan tersimpan dalam sistem. Pengguna berada di halaman Sign In dan dapat segera masuk menggunakan akun yang baru dibuat. |

Tabel 4.x menjelaskan tahapan proses yang dilakukan calon pengguna dalam mendaftarkan akun baru pada sistem PIXEL-T.

---

### Sign In

**Aktor:** Calon Pengguna, Dokter / Tenaga Medis, Admin.

**Deskripsi:** Pengguna mengakses halaman masuk, memasukkan kredensial (email dan kata sandi), dan mengirimkannya untuk diverifikasi. Sistem memeriksa kredensial yang diberikan, dan apabila valid, membentuk sesi autentikasi aktif. Pengguna kemudian diarahkan ke halaman utama sesuai peran atau status akunnya.

**Tabel 4.x — Deskripsi Use Case Sign In**

| Bagian | Keterangan |
|--------|------------|
| Actor | Calon Pengguna, Dokter / Tenaga Medis, Admin |
| Trigger & Type | Pengguna mengakses halaman masuk dan memasukkan kredensial. Tipe: *User-initiated*, *Synchronous*. |
| Pre-Conditions | Pengguna telah memiliki akun terdaftar dan belum berada dalam sesi autentikasi yang aktif. |
| Normal Course | 1. Pengguna membuka halaman masuk.<br>2. Sistem menampilkan formulir masuk.<br>3. Pengguna mengisi email dan kata sandi.<br>4. Pengguna menekan tombol masuk untuk mengirimkan kredensial.<br>5. Sistem melakukan validasi input awal.<br>6. Sistem memverifikasi kredensial melalui layanan autentikasi.<br>7. Sistem membentuk sesi autentikasi aktif apabila kredensial valid.<br>8. Pengguna diarahkan ke halaman utama sesuai peran atau status akunnya. |
| Post Condition | Sesi autentikasi aktif terbentuk dan pengguna dapat mengakses fitur sistem sesuai hak akses yang dimilikinya. |

Tabel 4.x menjelaskan tahapan proses yang dilakukan pengguna dalam masuk ke sistem PIXEL-T.

---

### Upload Image

**Aktor:** Dokter / Tenaga Medis.

**Deskripsi:** Dokter mengakses halaman pengunggahan citra, memilih berkas citra endoskopi dari perangkat lokal, dan mengirimkannya ke sistem. Sistem melakukan validasi berkas, lalu mengirim citra ke backend untuk diproses. Citra disimpan dan rekaman analisis dibuat. Sistem mengembalikan konfirmasi bahwa permintaan analisis telah diterima untuk diproses lebih lanjut.

**Tabel 4.x — Deskripsi Use Case Upload Image**

| Bagian | Keterangan |
|--------|------------|
| Actor | Dokter / Tenaga Medis |
| Trigger & Type | Pengguna mengakses halaman pengunggahan citra dan memilih berkas citra untuk diunggah. Tipe: *User-initiated*, *Asynchronous*. |
| Pre-Conditions | Pengguna telah masuk ke sistem dan memiliki sesi autentikasi yang aktif. |
| Normal Course | 1. Pengguna membuka halaman pengunggahan citra.<br>2. Sistem menampilkan antarmuka pemilihan berkas.<br>3. Pengguna memilih berkas citra endoskopi dari perangkat lokal.<br>4. Sistem melakukan validasi format, tipe, dan ukuran berkas.<br>5. Pengguna mengonfirmasi pengunggahan citra.<br>6. Sistem mengirim berkas citra ke backend untuk diproses.<br>7. Backend menerima berkas citra dan menyimpannya.<br>8. Sistem membuat rekaman analisis baru.<br>9. Sistem mengembalikan konfirmasi bahwa permintaan analisis telah diterima dan sedang diproses. |
| Post Condition | Berkas citra endoskopi berhasil diunggah dan tersimpan. Rekaman analisis baru dibuat dengan status yang menunjukkan proses sedang berlangsung. |

Tabel 4.x menjelaskan tahapan proses yang dilakukan dokter dalam mengunggah citra endoskopi untuk dianalisis pada sistem PIXEL-T.

---

### Segmentation

**Aktor:** Dokter / Tenaga Medis.

**Deskripsi:** Setelah citra berhasil diunggah, sistem menjalankan proses segmentasi polip melalui pipeline AI. Citra diproses untuk menghasilkan hasil segmentasi, dan frontend memantau status proses melalui polling. Apabila berhasil, hasil segmentasi disimpan dan ditampilkan kepada pengguna. Apabila gagal, sistem mencatat kegagalan dan memberitahukan kepada pengguna.

**Tabel 4.x — Deskripsi Use Case Segmentation**

| Bagian | Keterangan |
|--------|------------|
| Actor | Dokter / Tenaga Medis |
| Trigger & Type | Citra berhasil diunggah dan rekaman analisis dibuat. Tipe: *System-initiated*, *Asynchronous*. |
| Pre-Conditions | Citra endoskopi telah berhasil diunggah dan rekaman analisis tersedia dalam status pemrosesan. |
| Normal Course | 1. Sistem memulai proses segmentasi melalui pipeline AI.<br>2. Citra endoskopi diproses untuk menghasilkan hasil segmentasi.<br>3. Sistem menyimpan hasil segmentasi ke dalam penyimpanan data.<br>4. Frontend memantau status proses melalui polling.<br>5. Apabila proses berhasil, status diperbarui dan hasil ditampilkan kepada pengguna.<br>6. Sistem menyajikan hasil segmentasi kepada dokter. |
| Alternative Course | Apabila proses segmentasi mengalami kegagalan, sistem mencatat kegagalan dan memperbarui status analisis sebagai gagal. Pengguna diberitahukan bahwa analisis tidak dapat diselesaikan. |
| Post Condition | Hasil segmentasi tersimpan dan ditampilkan kepada pengguna, atau status kegagalan dicatat apabila proses tidak berhasil. |

Tabel 4.x menjelaskan tahapan proses yang dilakukan sistem dalam segmentasi polip pada citra endoskopi menggunakan pipeline AI.

---

### History

**Aktor:** Dokter / Tenaga Medis.

**Deskripsi:** Dokter mengakses halaman riwayat untuk melihat daftar analisis yang telah dilakukan sebelumnya. Sistem mengambil data riwayat yang terkait dengan pengguna yang sedang login dan menampilkannya dalam bentuk daftar. Pengguna dapat melihat detail hasil analisis dari masing-masing entri riwayat.

**Tabel 4.x — Deskripsi Use Case History**

| Bagian | Keterangan |
|--------|------------|
| Actor | Dokter / Tenaga Medis |
| Trigger & Type | Pengguna mengakses halaman riwayat analisis. Tipe: *User-initiated*, *Synchronous*. |
| Pre-Conditions | Pengguna telah masuk ke sistem dan memiliki sesi autentikasi yang aktif. |
| Normal Course | 1. Pengguna membuka halaman riwayat analisis.<br>2. Sistem meminta data riwayat analisis yang terkait dengan pengguna yang sedang login.<br>3. Sistem mengambil data dari basis data sesuai identitas pengguna.<br>4. Sistem menampilkan daftar riwayat analisis kepada pengguna.<br>5. Pengguna dapat melihat detail hasil analisis dari masing-masing entri riwayat. |
| Post Condition | Daftar riwayat analisis berhasil ditampilkan kepada pengguna sesuai identitas yang login. |

Tabel 4.x menjelaskan tahapan proses yang dilakukan pengguna dalam melihat riwayat analisis yang telah dilakukan pada sistem PIXEL-T.

---

### Doctor Profile

**Aktor:** Dokter / Tenaga Medis.

**Deskripsi:** Dokter mengakses halaman profil untuk melihat data profilnya. Sistem mengambil informasi profil dari data yang tersedia dan menampilkannya kepada pengguna. Pengguna dapat memperbarui data profil apabila diperlukan.

**Tabel 4.x — Deskripsi Use Case Doctor Profile**

| Bagian | Keterangan |
|--------|------------|
| Actor | Dokter / Tenaga Medis |
| Trigger & Type | Pengguna mengakses halaman profil dokter. Tipe: *User-initiated*, *Synchronous*. |
| Pre-Conditions | Pengguna telah masuk ke sistem dan memiliki data profil yang tersedia. |
| Normal Course | 1. Pengguna membuka halaman profil dokter.<br>2. Sistem mengambil data profil pengguna dari basis data.<br>3. Sistem menampilkan data profil kepada pengguna.<br>4. Pengguna dapat memperbarui data profil apabila diperlukan.<br>5. Sistem menyimpan perubahan data profil. |
| Post Condition | Data profil berhasil ditampilkan. Apabila dilakukan perubahan, data profil berhasil diperbarui dan disimpan. |

Tabel 4.x menjelaskan tahapan proses yang dilakukan pengguna dalam mengelola profil dokter pada sistem PIXEL-T.

---

### Sign Out

**Aktor:** Dokter / Tenaga Medis, Admin.

**Deskripsi:** Pengguna yang sedang login memilih opsi keluar dari sistem. Sistem menampilkan konfirmasi keluar, lalu mengeksekusi proses logout. Sesi autentikasi diakhiri dan pengguna diarahkan kembali ke halaman masuk.

**Tabel 4.x — Deskripsi Use Case Sign Out**

| Bagian | Keterangan |
|--------|------------|
| Actor | Dokter / Tenaga Medis, Admin |
| Trigger & Type | Pengguna memilih opsi keluar dari sistem melalui menu navigasi. Tipe: *User-initiated*, *Synchronous*. |
| Pre-Conditions | Pengguna sedang berada dalam sesi autentikasi yang aktif. |
| Normal Course | 1. Pengguna memilih opsi Sign Out pada menu navigasi.<br>2. Sistem menampilkan konfirmasi keluar.<br>3. Pengguna mengonfirmasi keluar dari sistem.<br>4. Sistem mengeksekusi proses logout.<br>5. Sesi autentikasi pengguna diakhiri.<br>6. Pengguna diarahkan kembali ke halaman masuk. |
| Post Condition | Sesi autentikasi pengguna diakhiri sepenuhnya dan pengguna berada di halaman masuk. |

Tabel 4.x menjelaskan tahapan proses yang dilakukan pengguna dalam mengakhiri sesi autentikasi pada sistem PIXEL-T.

---

## 4.1.3 Hubungan Antar Aktor dan Use Case

Hubungan antara aktor dan use case pada Gambar 4.x menunjukkan siapa saja yang berhak menggunakan fitur sistem:

- **Calon Pengguna** terhubung dengan **Sign Up** dan **Sign In**, mencerminkan bahwa calon pengguna hanya dapat mendaftar dan masuk ke sistem sebelum memiliki akun aktif.
- **Dokter / Tenaga Medis** terhubung dengan **Sign In**, **Sign Out**, **Upload Image**, **Segmentation**, **History**, dan **Doctor Profile**, mencerminkan akses penuh ke fitur klinis dan manajemen akun pribadi.
- **Admin** terhubung dengan **Sign In** dan **Sign Out**, mencerminkan bahwa admin mengelola sistem tanpa melibatkan fitur klinis langsung.

Tidak terdapat relasi `<<include>>` atau `<<extend>>` pada tujuh use case utama yang ditampilkan dalam diagram. Tidak pula terdapat generalisasi antara aktor.

---

## 4.1.4 Batas Sistem

Batas sistem pada Gambar 4.x berlabel **Sistem PIXEL-T** dan mencakup seluruh tujuh *use case* utama yang disediakan oleh aplikasi. Batas ini memisahkan tanggung jawab internal sistem dari aktor eksternal. Seluruh aktor berada di luar batas sistem, sedangkan seluruh *use case* berada di dalamnya. Batas sistem mencakup antarmuka pengguna, layanan backend, serta pipeline AI yang beroperasi sebagai satu kesatuan. Aktor tidak berinteraksi langsung dengan basis data maupun model AI; seluruh interaksi dimediasi oleh *use case* di dalam batas sistem.

---

## 4.1.5 Kesimpulan

*Use Case Diagram* PIXEL-T yang disajikan pada Gambar 4.x merepresentasikan tiga aktor dan tujuh *use case* utama yang konsisten dengan implementasi aktual sistem. Setiap *use case* menggambarkan fungsi inti yang mendukung tujuan penelitian PIXEL-T, yaitu sistem informasi web untuk segmentasi polip menggunakan citra endoskopi dengan pendekatan kecerdasan buatan. Diagram ini layak digunakan sebagai bagian dari Bab IV skripsi dan konsisten dengan perangkat lunak yang dibangun.

---

*Dokumen ini disusun berdasarkan analisis terhadap Use Case Diagram PIXEL-T dan dokumen pendukung di folder `references\bab 4`. Tidak ada kode aplikasi yang diubah dalam penyusunan dokumen ini.*
