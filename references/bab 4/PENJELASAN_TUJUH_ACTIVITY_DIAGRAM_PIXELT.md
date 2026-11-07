# DOKUMEN PENJELASAN AKADEMIK TUJUH ACTIVITY DIAGRAM PIXEL-T
## Naskah Siap Salin untuk Bab IV Skripsi S1

> **Petunjuk bagi Penulis Skripsi:**  
> Penomoran subbab `4.x` dan nomor gambar `Gambar 4.x` merupakan *placeholder*. Sesuaikan dengan urutan nomor yang berlaku pada draf Bab IV skripsi Anda.

---

### 4.x Activity Diagram Sistem PIXEL-T

*Activity Diagram* digunakan untuk memodelkan aspek dinamis sistem PIXEL-T dengan menggambarkan aliran kerja, urutan aktivitas, titik keputusan (*decision nodes*), cabang alternatif, dan penggabungan alur (*merge nodes*). Pemodelan ini menggambarkan interaksi fungsional antara pengguna (*User*) yang mengoperasikan antarmuka dan sistem (*System*) yang mencakup antarmuka React berbasis peramban, server API berbasis Flask, mesin inferensi AI (pipeline U-Net + ResNet50 dan Grad-CAM), serta layanan Supabase (autentikasi, basis data PostgreSQL, dan penyimpanan objek berkas).

Pada sistem PIXEL-T, *Activity Diagram* dipetakan ke dalam tujuh fungsionalitas utama:
1. Pendaftaran akun baru (*Sign Up*)
2. Masuk ke sistem (*Sign In*)
3. Pengunggahan citra kolonoskopi (*Upload Image*)
4. Segmentasi citra dan visualisasi *Explainable AI* (*Segmentation*)
5. Penelusuran riwayat pemeriksaan (*History*)
6. Pengelolaan profil dokter (*Doctor Profile*)
7. Keluar dari sistem (*Sign Out*)

---

#### 4.x.1 Activity Diagram Sign Up

Gambar 4.x menunjukkan *Activity Diagram Sign Up* yang menggambarkan alur pendaftaran akun baru bagi dokter atau tenaga medis ke dalam sistem PIXEL-T.

```
[Sisipkan Gambar: Activity Diagram - Sign Up.drawio.png]
Gambar 4.x Activity Diagram Sign Up
```

Alur pendaftaran dimulai pada *initial node* ketika calon pengguna membuka antarmuka pendaftaran (*Sign Up*). Pengguna melengkapi enam kolom isian: nama lengkap, alamat email, nama rumah sakit, bidang keahlian, kata sandi, dan konfirmasi kata sandi. Setelah pengguna mengirimkan formulir, sistem melakukan validasi masukan sisi klien (*Decision Node: Apakah data valid?*): memastikan seluruh kolom terisi, format email memenuhi pola yang ditentukan, kata sandi minimal 6 karakter, dan konfirmasi kata sandi cocok dengan kata sandi.

- **Cabang Tidak Valid (`[Tidak]`):** Apabila salah satu syarat validasi tidak terpenuhi, sistem menampilkan pesan kesalahan yang spesifik sesuai kolom yang bermasalah. Alur kembali ke langkah pengisian formulir agar pengguna dapat memperbaiki masukan.
- **Cabang Valid (`[Ya]`):** Apabila seluruh validasi lolos, sistem memanggil layanan Supabase Auth untuk membuat akun baru. Supabase membuat rekaman akun pada skema `auth.users` dan memproses permintaan pendaftaran. Sistem menampilkan notifikasi keberhasilan kepada pengguna, kemudian mengarahkan navigasi ke halaman masuk (*Sign In*). Alur berakhir pada *Activity Final Node*.

---

#### 4.x.2 Activity Diagram Sign In

Gambar 4.x menunjukkan *Activity Diagram Sign In* yang memodelkan alur verifikasi identitas dan pembentukan sesi autentikasi pengguna pada sistem PIXEL-T.

```
[Sisipkan Gambar: Activity Diagram - Sign In.drawio.png]
Gambar 4.x Activity Diagram Sign In
```

Proses masuk sistem dimulai pada *initial node* saat pengguna mengakses antarmuka *Sign In*. Pengguna memasukkan alamat email dan kata sandi terdaftar, kemudian mengirimkan formulir. Sistem melakukan validasi awal untuk memastikan kolom tidak kosong, lalu meneruskan permintaan autentikasi ke Supabase Auth melalui fungsi `signInWithPassword`.

Pada simpul keputusan (*Decision Node: Kredensial sesuai?*), sistem memverifikasi pasangan email dan kata sandi:

- **Cabang Tidak Sesuai (`[Tidak]`):** Apabila kredensial keliru atau akun tidak ditemukan, sistem menampilkan pesan kesalahan autentikasi. Alur kembali ke langkah pengisian formulir.
- **Cabang Sesuai (`[Ya]`):** Apabila kredensial sah, Supabase Auth menerbitkan token JWT dan membentuk sesi aktif. Status sesi disimpan pada lapisan manajemen status global aplikasi (*AuthContext*). Sistem mengarahkan pengguna ke halaman utama (*Dashboard*). Alur berakhir pada *Activity Final Node*.

---

#### 4.x.3 Activity Diagram Upload Image

Gambar 4.x menunjukkan *Activity Diagram Upload Image* yang memodelkan alur penerimaan, validasi berkas, dan pengiriman citra kolonoskopi ke server PIXEL-T.

```
[Sisipkan Gambar: Activity Diagram - Upload Image.drawio.png]
Gambar 4.x Activity Diagram Upload Image
```

Aktivitas pengunggahan dimulai pada *initial node* saat dokter mengakses halaman analisis baru (*New Analysis*). Pengguna memilih berkas citra dari media penyimpanan lokal melalui dialog pemilihan berkas atau mekanisme seret-dan-lepas. Sistem segera menjalankan validasi berkas sisi klien (*Decision Node: Berkas valid?*):

- **Cabang Tidak Valid (`[Tidak]`):** Apabila ekstensi berkas di luar format yang diizinkan (`.jpg`, `.jpeg`, `.png`), tipe MIME tidak sesuai, atau ukuran berkas melebihi 10 MB, sistem menampilkan pesan kesalahan. Alur kembali ke langkah pemilihan berkas.
- **Cabang Valid (`[Ya]`):** Apabila berkas memenuhi syarat, sistem menampilkan pratinjau citra (*image preview*) agar dokter dapat memeriksa citra sebelum memulai analisis.

Pengguna menekan tombol *"Start Analysis"*. Sistem menyusun berkas ke dalam `FormData` dan mengirimkannya melalui permintaan HTTP POST ke *endpoint* `/api/analysis` pada server *backend*. Server menerima berkas, menyimpan citra asli ke *Supabase Storage*, mendaftarkan rekaman analisis pada tabel `analyses` berstatus `processing`, dan mengantrekan tugas inferensi. Server mengembalikan respons HTTP 202 *Accepted* beserta `analysis_id`. Sistem mengarahkan pengguna ke halaman pemantauan hasil (`/analysis/:id`), dan alur berakhir pada *Activity Final Node*.

---

#### 4.x.4 Activity Diagram Segmentation

Gambar 4.x menunjukkan *Activity Diagram Segmentation* yang menggambarkan tahapan pemrosesan inferensi AI dan visualisasi *Explainable AI* pada citra kolonoskopi.

```
[Sisipkan Gambar: Activity Diagram - Segmentation.drawio.png]
Gambar 4.x Activity Diagram Segmentation
```

Alur segmentasi diawali ketika *background worker* mengeksekusi tugas dari antrean inferensi. Sistem *backend* terlebih dahulu memuat citra dari *Supabase Storage* dan melakukan validasi integritas citra serta pra-pemrosesan (normalisasi dan penyesuaian ukuran ke dimensi standar $512 \times 512$ piksel).

Sistem mengevaluasi keberhasilan proses melalui simpul keputusan (*Decision Node: Proses inferensi berhasil?*):

- **Cabang Gagal (`[Tidak]`):** Apabila terjadi kegagalan komputasi, sistem mencatat log kegagalan dan memperbarui status rekaman analisis menjadi `failed`. Antarmuka pengguna yang sedang memantau hasil menampilkan notifikasi bahwa analisis tidak dapat diselesaikan. Alur berakhir pada *Activity Final Node*.
- **Cabang Berhasil (`[Ya]`):** Sistem mengeksekusi tahapan inferensi secara sekuensial:
  1. Segmentasi biner menggunakan model U-Net dengan *encoder* ResNet50, menghasilkan masker biner area polip.
  2. Pasca-pemrosesan morfologi untuk menyempurnakan kontur masker.
  3. Perhitungan metrik luas area polip dalam piksel dan rasio terhadap keseluruhan citra.
  4. Pembangkitan visualisasi *Gradient-weighted Class Activation Mapping* (Grad-CAM) pada lapisan konvolusi target, menghasilkan peta panas atensi model.
  5. Penyusunan empat artefak: masker biner, citra *overlay* segmentasi, peta panas Grad-CAM, dan citra *overlay* Grad-CAM.

Seluruh artefak diunggah ke *Supabase Storage*. Status rekaman pada tabel `analyses` diperbarui menjadi `completed` beserta metrik klinis. *Frontend* yang melakukan *polling* mendeteksi perubahan status dan memuat halaman hasil secara otomatis, menyajikan keempat artefak visualisasi kepada dokter. Alur berakhir pada *Activity Final Node*.

---

#### 4.x.5 Activity Diagram History

Gambar 4.x menunjukkan *Activity Diagram History* yang memodelkan alur penelusuran riwayat pemeriksaan, penyaringan data, peninjauan detail, dan penghapusan rekaman pada sistem PIXEL-T.

```
[Sisipkan Gambar: Activity Diagram - History.drawio.png]
Gambar 4.x Activity Diagram History
```

Aktivitas penelusuran dimulai pada *initial node* saat dokter membuka halaman *History*. Sistem memanggil fungsi `listHistory` untuk mengambil seluruh rekaman analisis milik pengguna dari basis data, difilter berdasarkan `user_id`. Sistem mengevaluasi ketersediaan data (*Decision Node: Riwayat tersedia?*):

- **Jalur Kosong (`[Tidak]`):** Apabila belum ada rekaman analisis, sistem menampilkan antarmuka kondisi kosong (*empty state*). Alur menuju *Merge Node* akhir.
- **Jalur Tersedia (`[Ya]`):** Sistem menyajikan daftar riwayat dalam format tabel interaktif yang memuat nama berkas, tanggal analisis, dan status (`COMPLETED`, `PROCESSING`, atau `FAILED`). Tabel menampilkan 4 rekaman per halaman dengan kontrol paginasi.

Pengguna dapat mempersempit daftar menggunakan filter pencarian teks nama berkas, filter *dropdown* status, atau filter tanggal — seluruhnya berjalan di sisi klien tanpa permintaan baru ke server. Pengguna selanjutnya memilih tindakan (*Decision Node: Tindakan pada riwayat?*):

- **Opsi Lihat Detail:** Sistem mengarahkan navigasi ke halaman detail analisis (`/analysis/:id`) yang menampilkan seluruh artefak visualisasi. Alur menuju *Merge Node*.
- **Opsi Hapus:** Sistem menampilkan modal konfirmasi penghapusan (*Decision Node: Konfirmasi hapus?*):
  - **Batal (`[Tidak]`):** Modal ditutup tanpa perubahan data. Alur menuju *Merge Node*.
  - **Konfirmasi (`[Ya]`):** Sistem menghapus rekaman pada tabel `analyses` dan seluruh berkas artefak terkait di *Supabase Storage*. Daftar diperbarui dan alur menuju *Merge Node*.

Seluruh jalur menyatu pada satu *Merge Node*, dan alur berakhir pada *Activity Final Node*.

---

#### 4.x.6 Activity Diagram Doctor Profile

Gambar 4.x menunjukkan *Activity Diagram Doctor Profile* yang memodelkan alur peninjauan profil klinis dokter dan pembaruan data profil melalui formulir modal.

```
[Sisipkan Gambar: Activity Diagram - Doctor Profile.drawio.png]
Gambar 4.x Activity Diagram Doctor Profile
```

Proses diawali pada *initial node* ketika dokter mengakses halaman profil (*Doctor Profile*). Sistem mengambil data profil dari tabel `doctor_profiles` dan menghitung ringkasan statistik aktivitas dari riwayat analisis (total analisis yang dilakukan dan jumlah analisis berstatus `completed`). Sistem menampilkan halaman profil yang memuat informasi personal, data profesional, dan kartu ringkasan statistik.

Pengguna menentukan tindakan (*Decision Node: Ingin mengubah profil?*):

- **Hanya Meninjau (`[Tidak]`):** Alur langsung menuju *Merge Node* akhir.
- **Mengubah Profil (`[Ya]`):** Pengguna menekan tombol *"Edit Profile"*. Sistem membuka modal formulir berisi kolom-kolom profil yang dapat disunting.

Pengguna mengisi atau menyunting data, kemudian menentukan tindakan formulir (*Decision Node: Aksi formulir?*):

- **Batal:** Modal ditutup tanpa perubahan. Alur menuju *Merge Node*.
- **Simpan:** Sistem menjalankan `validateProfileData()` untuk memverifikasi nama tidak kosong, format nomor telepon (jika diisi), dan integritas data lainnya.

Hasil validasi dievaluasi (*Decision Node: Data valid?*):

- **Tidak Valid (`[Tidak]`):** Sistem menampilkan pesan kesalahan spesifik pada modal. Alur kembali ke langkah pengisian agar pengguna dapat mengoreksi data.
- **Valid (`[Ya]`):** Sistem menjalankan operasi *upsert* ke tabel `doctor_profiles` dan menyinkronkan nama pada metadata Supabase Auth. Sistem menampilkan notifikasi keberhasilan, menutup modal, dan memperbarui tampilan profil. Alur menuju *Merge Node*.

Seluruh jalur menyatu pada satu *Merge Node*, dan alur berakhir pada *Activity Final Node*.

---

#### 4.x.7 Activity Diagram Sign Out

Gambar 4.x menunjukkan *Activity Diagram Sign Out* yang memodelkan alur pengakhiran sesi autentikasi pengguna secara aman dari sistem PIXEL-T.

```
[Sisipkan Gambar: Activity Diagram - Sign Out.drawio.png]
Gambar 4.x Activity Diagram Sign Out
```

Alur dimulai pada *initial node* saat pengguna menekan tombol *"Sign Out"* pada menu navigasi. Sistem menutup menu dan menampilkan modal konfirmasi keluar untuk mencegah tindakan yang tidak disengaja.

Pada simpul keputusan (*Decision Node: Konfirmasi Sign Out?*):

- **Batal (`[Tidak]`):** Pengguna menekan batal. Modal ditutup tanpa mengubah status sesi. Pengguna tetap berada di halaman aktif. Alur kembali ke kondisi sebelum tombol ditekan.
- **Konfirmasi (`[Ya]`):** Sistem memanggil `signOut()` ke Supabase Auth untuk mengakhiri token akses JWT. *AuthContext* membersihkan data sesi dan status autentikasi. Sistem mengarahkan pengguna ke halaman *Sign In* (`/login`), dan seluruh rute privat kembali terlindungi. Alur berakhir pada *Activity Final Node*.

---
