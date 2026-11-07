# DOKUMEN PENJELASAN AKADEMIK TUJUH ACTIVITY DIAGRAM PIXEL-T
## Naskah Siap Salin untuk Bab IV Skripsi S1

> **Petunjuk bagi Penulis Skripsi:**  
> Penomoran subbab `4.x` dan nomor gambar `Gambar 4.x` pada naskah ini merupakan placeholder penomoran standar skripsi. Sesuaikan digit `x` dengan urutan nomor subbab dan urutan gambar yang berlaku pada draf naskah Bab IV Anda (misalnya `4.3.1`, `Gambar 4.12`, dst.).

---

### 4.x Activity Diagram Sistem PIXEL-T

*Activity Diagram* digunakan untuk memodelkan aspek dinamis dari sistem web PIXEL-T dengan menggambarkan aliran kerja (*workflow*), urutan aktivitas operasional, titik pengambilan keputusan (*decision nodes*), cabang alternatif, siklus pengulangan, serta penggabungan alur (*merge nodes*) yang terjadi dalam sistem. Pemodelan ini menggambarkan interaksi fungsional antara pengguna (*User*) sebagai pihak yang mengoperasikan antarmuka dan sistem (*System*) yang mencakup antarmuka peramban berbasis React, server web API berbasis Flask, mesin komputasi kecerdasan buatan (*AI Pipeline* U-Net + ResNet50 dan Grad-CAM), serta layanan *backend-as-a-service* Supabase (Autentikasi, Basis Data PostgreSQL, dan Penyimpanan Objek Berkas).

Pada perancangan web PIXEL-T, *Activity Diagram* dipetakan ke dalam tujuh fungsionalitas utama yang mencakup seluruh siklus hidup penggunaan aplikasi, yaitu:
1. Pendaftaran akun baru (*Sign Up*)
2. Masuk ke dalam sistem (*Sign In*)
3. Pengunggahan citra medis kolonoskopi (*Upload Image*)
4. Segmentasi citra dan visualisasi *Explainable AI* (*Segmentation*)
5. Penelusuran dan pengelolaan riwayat pemeriksaan (*History*)
6. Pengelolaan data profil klinis dokter (*Doctor Profile*)
7. Keluar dari sistem secara aman (*Sign Out*)

---

#### 4.x.1 Activity Diagram Sign Up

Gambar 4.x menunjukkan *Activity Diagram Sign Up* yang merepresentasikan alur proses pendaftaran akun baru bagi dokter atau tenaga medis ke dalam sistem web PIXEL-T.

```
[Sisipkan Gambar: Activity Diagram - Sign Up.drawio.png]
Gambar 4.x Activity Diagram Sign Up
```

Alur aktivitas pendaftaran diawali pada *initial node* ketika calon pengguna membuka antarmuka pendaftaran (*Sign Up*) pada peramban web. Pengguna kemudian melengkapi kolom isian pada formulir yang mencakup nama lengkap, alamat surat elektronik (*email*), kata sandi (*password*), serta konfirmasi kata sandi. Setelah pengguna mengirimkan formulir, sistem pada lapisan klien melakukan validasi masukan (*input validation*) untuk memastikan seluruh kolom terisi, format email memenuhi standar, kata sandi memiliki panjang minimal 8 karakter, dan nilai konfirmasi kata sandi cocok dengan kata sandi yang dimasukkan.

Tahap berikutnya adalah evaluasi integritas data dan ketersediaan akun melalui simpul keputusan (*Decision Node: Apakah data valid & email belum terdaftar?*). Sistem memeriksa keabsahan masukan dan memverifikasi status registrasi email ke layanan Supabase Auth:
- **Cabang Tidak Valid / Email Terdaftar (`[Tidak]`):** Apabila data isian tidak memenuhi kualifikasi atau alamat email tersebut ternyata telah terdaftar sebelumnya pada basis data sistem, sistem mengirimkan pesan kesalahan (*"Email sudah terdaftar / Data tidak valid"*). Pengguna menerima pemberitahuan galat tersebut pada layar dan alur aktivitas berputar kembali (*loop back*) ke langkah pengisian formulir pendaftaran agar pengguna dapat memperbaiki data atau mengganti alamat email yang belum pernah didaftarkan.
- **Cabang Valid & Email Baru (`[Ya]`):** Apabila data valid dan alamat email belum terdaftar, sistem Supabase Auth mengeksekusi pembuatan entitas akun baru pada skema `auth.users` serta mengaitkan metadata identitas dokter yang bersangkutan. Sistem kemudian mengirimkan pesan konfirmasi bahwa registrasi telah berhasil, menampilkan notifikasi sukses pada antarmuka pengguna, dan secara otomatis mengalihkan navigasi pengguna ke halaman masuk (*Sign In*). Alur aktivitas pendaftaran akun baru ini diselesaikan pada satu *Activity Final Node*.

---

#### 4.x.2 Activity Diagram Sign In

Gambar 4.x menunjukkan *Activity Diagram Sign In* yang memodelkan alur verifikasi identitas dan pembentukan sesi autentikasi pengguna pada sistem web PIXEL-T.

```
[Sisipkan Gambar: Activity Diagram - Sign In.drawio.png]
Gambar 4.x Activity Diagram Sign In
```

Proses masuk sistem dimulai dari *initial node* pada saat pengguna mengakses antarmuka *Sign In*. Pengguna memasukkan kredensial akun yang terdiri atas alamat email dan kata sandi terdaftar, kemudian mengirimkan formulir masuk. Sistem pada lapisan antarmuka melakukan validasi awal untuk memastikan kolom kredensial tidak dalam kondisi kosong, lalu meneruskan permintaan autentikasi tersebut ke server Supabase Auth melalui fungsi `signInWithPassword`.

Pada simpul keputusan (*Decision Node: Email dan password Sesuai?*), sistem memverifikasi kesesuaian pasangan email dan kata sandi terhadap catatan pangkalan data terenkripsi:
- **Cabang Kredensial Tidak Sesuai (`[Tidak]`):** Apabila kredensial yang dimasukkan keliru atau akun tidak ditemukan, sistem mengirimkan pesan kesalahan autentikasi (*"Email or password is incorrect"*). Pengguna menerima pesan galat tersebut pada layar dan alur aktivitas berputar kembali (*loop back*) ke langkah pengisian formulir agar pengguna dapat memeriksa serta memasukkan ulang kombinasi kredensial yang tepat.
- **Cabang Kredensial Sesuai (`[Ya]`):** Apabila kredensial yang dimasukkan terbukti sah dan cocok, sistem Supabase Auth menerbitkan token otentikasi *JSON Web Token* (JWT) dan membentuk sesi aktif pengguna (*active user session*). Status sesi ini disimpan secara aman pada lapisan status global aplikasi (*AuthContext*) serta penyimpanan lokal peramban (*localStorage*). Selanjutnya, sistem mengarahkan antarmuka pengguna menuju halaman utama (*Dashboard*). Rangkaian aktivitas autentikasi masuk sistem ini diselesaikan pada satu *Activity Final Node*.

---

#### 4.x.3 Activity Diagram Upload Image

Gambar 4.x menunjukkan *Activity Diagram Upload Image* yang memodelkan alur penerimaan, validasi berkas, serta pengiriman citra medis kolonoskopi ke server komputasi PIXEL-T.

```
[Sisipkan Gambar: Activity Diagram - Upload Image.drawio.png]
Gambar 4.x Activity Diagram Upload Image
```

Aktivitas pengunggahan dimulai dari *initial node* saat dokter mengakses fitur analisis baru (*Upload Image*) pada sistem web PIXEL-T. Pengguna memilih berkas citra medis kolonoskopi dari media penyimpanan lokal komputer, baik melalui dialog pemilihan berkas maupun mekanisme seret-dan-lepas (*drag-and-drop*). Sistem segera menjalankan validasi integritas berkas citra pada sisi klien melalui simpul keputusan (*Decision Node: Berkas gambar sudah valid?*):
- **Cabang Berkas Tidak Valid (`[Tidak]`):** Apabila berkas yang dipilih tidak memenuhi kualifikasi teknis yang dipersyaratkan—seperti ekstensi di luar format resmi (`.jpg`, `.jpeg`, `.png`), tipe MIME tidak cocok, atau ukuran berkas melampaui batas maksimal 10 MB—sistem mengirimkan dan menampilkan pesan kesalahan (*"Invalid Image File"*). Alur aktivitas kemudian kembali mengarahkan pengguna ke langkah pemilihan berkas citra.
- **Cabang Berkas Valid (`[Ya]`):** Apabila berkas citra dinyatakan valid, sistem menampilkan pratinjau instan (*image preview*) dari citra kolonoskopi tersebut pada layar antarmuka pengguna agar dokter dapat memverifikasi visual citra sebelum proses komputasi dimulai.

Setelah memeriksa pratinjau citra, pengguna menekan tombol *"Start Analysis"*. Sistem merespons dengan menyusun berkas citra ke dalam objek `FormData` dan mengunggahnya melalui permintaan HTTP POST multipart ke server backend API PIXEL-T. Server backend menerima berkas, menerbitkan kode status HTTP 202 Accepted, menyimpan citra asli ke wadah penyimpanan privat (*Supabase Storage*), mendaftarkan sesi analisis ke tabel basis data `analyses` dengan status awal `processing`, serta memasukkan pekerjaan tersebut ke dalam antrean komputasi inferensi kecerdasan buatan (*AnalysisJobQueue*). Terakhir, sistem mengarahkan navigasi antarmuka pengguna menuju halaman pemantauan hasil analisis (`/analysis/:id`), dan alur aktivitas berakhir pada *Activity Final Node*.

---

#### 4.x.4 Activity Diagram Segmentation

Gambar 4.x menunjukkan *Activity Diagram Segmentation* yang menggambarkan tahapan pemrosesan komputasi inferensi kecerdasan buatan berbasis *deep learning* dan visualisasi interpretasi model (*Explainable AI*) pada citra kolonoskopi.

```
[Sisipkan Gambar: Activity Diagram - Segmentation.drawio.png]
Gambar 4.x Activity Diagram Segmentation
```

Alur aktivitas segmentasi diawali ketika proses analisis dimulai (*Start Segmentation*) oleh pengguna atau saat *worker* komputasi latar belakang (*background job queue*) mengeksekusi antrean inferensi citra kolonoskopi. Sistem backend terlebih dahulu melakukan validasi citra masukan dengan memeriksa integritas matriks piksel dan melakukan pra-pemrosesan tensor (penyesuaian ukuran citra ke dimensi standar $512 \times 512$ piksel serta normalisasi nilai kanal warna berbasis ImageNet).

Sistem mengevaluasi keberhasilan persiapan dan pemrosesan komputasi melalui simpul keputusan (*Decision Node: Apakah proses inferensi AI berhasil?*):
- **Cabang Inferensi Gagal (`[Tidak]`):** Apabila terjadi kegagalan komputasi tensor atau berkas mengalami kerusakan data biner, sistem menyimpan catatan log kegagalan (*failure log*), memperbarui status sesi analisis menjadi gagal (*failed*), dan mengalirkan status tersebut ke antarmuka pengguna sehingga pengguna dapat memulai ulang proses segmentasi jika diperlukan.
- **Cabang Inferensi Berhasil (`[Ya]`):** Apabila persiapan komputasi berhasil, sistem mengalirkan tensor citra ke model pembelajaran mendalam U-Net dengan *encoder* ResNet50 untuk mengeksekusi proses segmentasi biner (*binary segmentation*). Proses ini menghasilkan masker biner probabilitas keberadaan lesi polip kolorektal melalui fungsi aktivasi sigmoid dengan nilai ambang batas (*threshold*) terkalibrasi.

Secara simultan, sistem menjalankan algoritma *Gradient-weighted Class Activation Mapping* (Grad-CAM) dengan mengekstrak gradien fitur visual pada lapisan konvolusi terakhir *backbone* ResNet50 (`layer4`). Sistem menghasilkan representasi penjelasan visual Grad-CAM berupa *heatmap* atensi spasial model dan citra tumpang-tindih (*overlay*). Seluruh artefak luaran—yang meliputi berkas citra masker biner, citra tumpang-tindih segmentasi, peta panas Grad-CAM, dan citra tumpang-tindih Grad-CAM—disimpan secara terstruktur ke ember penyimpanan objek *Supabase Storage*, sementara status sesi pada tabel basis data `analyses` diperbarui menjadi selesai (*completed*) lengkap dengan ringkasan metrik kuantitatif luas lesi polip. Terakhir, sistem mentransmisikan hasil inferensi beserta status berhasil ke peramban pengguna, antarmuka menyajikan visualisasi masker segmentasi polip dan atribusi visual Grad-CAM secara komparatif kepada dokter, dan alur aktivitas selesai pada *Activity Final Node*.

---

#### 4.x.5 Activity Diagram History

Gambar 4.x menunjukkan *Activity Diagram History* yang memodelkan alur interaksi pengguna dalam meninjau daftar riwayat pemeriksaan kolonoskopi, menyaring data, melihat rincian hasil segmentasi, dan melakukan penghapusan rekaman riwayat secara aman.

```
[Sisipkan Gambar: Activity Diagram - History.drawio.png]
Gambar 4.x Activity Diagram History
```

Aktivitas penelusuran riwayat dimulai dari *initial node* saat dokter membuka halaman *History* pada aplikasi web PIXEL-T. Sistem segera merespons dengan memicu kueri pengambilan data riwayat analisis (`listHistory`) dari basis data PostgreSQL Supabase yang terisolasi berdasarkan pengenal pengguna (*user_id*) yang sedang aktif. Sistem kemudian mengevaluasi ketersediaan rekaman riwayat melalui simpul keputusan (*Decision Node: Apakah riwayat tersedia?*):
1. **Jalur Riwayat Kosong (`[Tidak]`):** Apabila dokter belum pernah melakukan analisis atau seluruh data telah dihapus, sistem menyajikan antarmuka kondisi kosong (*Empty State*) bertuliskan pesan bahwa riwayat belum tersedia (*"Riwayat Kosong"*). Alur dari kondisi ini langsung dialirkan ke simpul penggabungan (*Merge Node*) penutup aktivitas.
2. **Jalur Riwayat Tersedia (`[Ya]`):** Apabila ditemukan data analisis sebelumnya, sistem mengirimkan dan merender daftar riwayat dalam format tabel interaktif yang dilengkapi kartu statistik dan kontrol penyaringan (*filter/search bar*).

Pada tampilan data riwayat yang aktif, dokter dapat menentukan aksi lanjutan pada simpul keputusan (*Decision Node: Tindakan pada riwayat?*):
- **Opsi Lihat Detail:** Jika dokter ingin meninjau kembali laporan pemeriksaan polip terdahulu, dokter memilih opsi *Lihat Detail*. Sistem merespons dengan mengarahkan navigasi peramban ke halaman laporan rincian hasil analisis (`/analysis/:id`) yang menyajikan visualisasi segmentasi polip, masker biner, dan peta Grad-CAM secara lengkap. Alur ini selanjutnya bermuara pada simpul penggabungan (*Merge Node*) penutup.
- **Opsi Hapus Riwayat:** Jika dokter bermaksud menghapus rekaman pemeriksaan tertentu, dokter menekan tombol hapus pada baris data terkait. Sistem menampilkan kotak dialog modal konfirmasi penghapusan (*Delete Confirmation Modal*) guna memastikan keamanan data dari tindakan yang tidak disengaja.

Pada dialog konfirmasi (*Decision Node: Konfirmasi hapus?*), dokter memiliki dua pilihan keputusan:
- **Cabang Batal (`[Tidak]`):** Dokter membatalkan penghapusan dengan menekan tombol batal, sistem menutup jendela modal tanpa melakukan perubahan data apa pun, dan alur dialirkan ke simpul penggabungan (*Merge Node*).
- **Cabang Konfirmasi Hapus (`[Ya]`):** Dokter menyetujui penghapusan dengan menekan tombol konfirmasi. Sistem backend mengeksekusi penghapusan rekaman pada tabel basis data `analyses` sekaligus menghapus seluruh berkas citra terkait (citra asli, masker biner, dan visualisasi Grad-CAM) pada penyimpanan *Supabase Storage*. Sistem selanjutnya memuat ulang daftar data riwayat terbaru ke layar pengguna dan mengalirkan proses ke simpul penggabungan (*Merge Node*).

Seluruh empat jalur alternatif pada fitur riwayat (kondisi riwayat kosong, peninjauan rincian hasil, pembatalan penghapusan, dan penyelesaian penghapusan) menyatu secara harmonis pada satu *Merge Node*, lalu use case diakhiri secara formal pada tepat SATU *Activity Final Node*.

---

#### 4.x.6 Activity Diagram Doctor Profile

Gambar 4.x menunjukkan *Activity Diagram Doctor Profile* yang memodelkan alur peninjauan informasi profil klinis dokter, pemeriksaan ringkasan metrik statistik aktivitas, serta pembaruan data profil profesional melalui formulir modal dengan mekanisme validasi terintegrasi.

```
[Sisipkan Gambar: Activity Diagram - Doctor Profile.drawio.png]
Gambar 4.x Activity Diagram Doctor Profile
```

Proses diawali dari *initial node* ketika dokter mengakses halaman profil klinisi (*Doctor Profile*) melalui menu navigasi aplikasi. Sistem secara otomatis menjalankan pemanggilan data paralel, yaitu mengambil rincian data profil dokter dari tabel basis data `doctor_profiles` serta mengambil riwayat sesi pemeriksaan guna mengkalkulasi ringkasan statistik klinis (seperti jumlah total pemeriksaan kolonoskopi yang telah dilakukan, jumlah temuan polip, dan rata-rata estimasi area lesi). Sistem kemudian mengirimkan data tersebut dan menampilkan profil lengkap klinisi (nama, gelar, nomor STR, spesialisasi, afiliasi fasilitas kesehatan, kontak, serta riwayat pendidikan dan pengalaman) bersanding dengan kartu metrik statistik pada antarmuka pengguna.

Pengguna dihadapkan pada simpul keputusan awal (*Decision Node: Apakah ingin mengubah profil?*):
- **Opsi Hanya Meninjau (`[Tidak]`):** Apabila dokter hanya berniat meninjau informasi profil dan metrik statistik tanpa melakukan perubahan data, alur aktivitas langsung dialirkan ke simpul penggabungan (*Merge Node*) akhir.
- **Opsi Mengubah Profil (`[Ya]`):** Apabila dokter ingin memperbarui informasi kredensial atau identitas klinisnya, dokter menekan tombol *"Edit Profile"*. Sistem merespons dengan memunculkan jendela dialog formulir modal yang berisi kolom-kolom data profil yang dapat disunting.

Dokter melakukan pengisian atau penyuntingan pada kolom informasi yang diinginkan. Setelah selesai, dokter menentukan tindakan formulir pada simpul keputusan (*Decision Node: Aksi formulir?*):
- **Opsi Batal:** Jika dokter memutuskan untuk tidak menyimpan perubahan data, dokter menekan tombol *"Batal"*. Sistem menutup jendela formulir modal tanpa menyimpan perubahan sementara, dan alur langsung menuju ke *Merge Node* akhir.
- **Opsi Simpan:** Jika dokter menekan tombol *"Simpan Profil"*, sistem segera menjalankan prosedur validasi integritas data masukan (*validateProfileData*) untuk memverifikasi kelengkapan nama, keabsahan nomor STR, batas panjang narasi bio, dan format nomor kontak.

Hasil validasi dievaluasi pada simpul keputusan (*Decision Node: Apakah data valid?*):
- **Data Tidak Valid (`[Tidak]`):** Apabila ditemukan masukan yang melanggar aturan integritas data, sistem menampilkan pesan kesalahan validasi spesifik pada jendela formulir modal. Alur aktivitas kemudian **berputar kembali (*loop back*)** ke langkah pengisian data profil agar dokter dapat langsung mengoreksi isian tanpa kehilangan data yang telah diketikkan sebelumnya.
- **Data Valid (`[Ya]`):** Apabila seluruh data dinyatakan valid, sistem mengeksekusi penyimpanan permanen (*upsert*) ke tabel basis data `doctor_profiles` sekaligus menyinkronkan data nama pengguna pada skema autentikasi Supabase Auth. Sistem kemudian mengirimkan notifikasi keberhasilan, menampilkan pemberitahuan sukses penyimpanan pada layar antarmuka, menyajikan data profil terbaru, menutup dialog modal, dan mengalirkan proses ke simpul penggabungan (*Merge Node*).

Seluruh percabangan alur use case profil dokter (peninjauan tanpa ubah, pembatalan formulir, dan keberhasilan penyimpanan data) menyatu pada satu *Merge Node* utama sebelum use case berakhir secara tuntas pada tepat SATU *Activity Final Node*.

---

#### 4.x.7 Activity Diagram Sign Out

Gambar 4.x menunjukkan *Activity Diagram Sign Out* yang memodelkan alur pelepasan hak akses dan penghentian sesi autentikasi pengguna secara aman dari sistem web PIXEL-T.

```
[Sisipkan Gambar: Activity Diagram - Sign Out.drawio.png]
Gambar 4.x Activity Diagram Sign Out
```

Alur keluar sistem diawali pada *initial node* ketika pengguna yang sedang masuk dalam sistem membuka menu navigasi aplikasi (baik melalui bilah navigasi atas maupun bilah samping) dan menekan tombol *"Sign Out"*. Sistem segera merespons tindakan tersebut dengan menutup menu navigasi peramban dan menampilkan jendela dialog modal konfirmasi keluar sistem (*Sign Out Confirmation Modal*) untuk memastikan bahwa proses logout dilakukan atas kehendak sadar pengguna.

Pada simpul keputusan (*Decision Node: Konfirmasi Sign Out?*), pengguna menentukan kelanjutan aksi keluar sistem:
- **Cabang Batal (`[Tidak]`):** Apabila pengguna memutuskan untuk membatalkan proses keluar, pengguna menekan tombol batal. Sistem menutup jendela dialog modal konfirmasi tanpa memodifikasi status sesi, status autentikasi pengguna tetap dipertahankan, dan pengguna tetap berada pada halaman aktif aplikasi saat ini. Alur aktivitas kemudian kembali ke kondisi sebelum tombol keluar ditekan.
- **Cabang Konfirmasi Keluar (`[Ya]`):** Apabila pengguna mengonfirmasi untuk keluar dari sistem, sistem mengeksekusi pemanggilan fungsi `signOut` ke server Supabase Auth untuk mencabut dan membatalkan validitas token akses JWT yang aktif di server.

Sistem pada lapisan klien selanjutnya membersihkan seluruh data pengguna dan token sesi yang tersimpan dalam *AuthContext* serta menghapus jejak sesi pada penyimpanan lokal peramban (*localStorage*). Selanjutnya, sistem mengarahkan antarmuka pengguna ke halaman masuk (*Sign In*) dan membatasi kembali hak akses halaman privat. Pengguna dialihkan ke halaman *Sign In*, dan rangkaian aktivitas penghentian sesi masuk ini diselesaikan pada satu *Activity Final Node*.

---
