# PENJELASAN PERANCANGAN BASIS DATA (ENTITY RELATIONSHIP DIAGRAM) SISTEM PIXEL-T

Dokumen ini berisi naskah penjelasan akademik resmi untuk **Bab IV Skripsi S1**, yang disusun dengan bahasa Indonesia formal, runtut, dan selaras dengan implementasi basis data PostgreSQL pada sistem PIXEL-T.

---

## 4.x Perancangan Basis Data (Entity Relationship Diagram)

Setelah merancang struktur perangkat lunak melalui *Class Diagram*, tahap berikutnya adalah mendefinisikan struktur basis data menggunakan *Entity Relationship Diagram* (ERD). Perancangan basis data bertujuan untuk memodelkan struktur penyimpanan data terstruktur, atribut-atribut entitas, tipe data yang digunakan, serta relasi dan batasan integritas referensial antar-tabel dalam sistem PIXEL-T.

Sistem PIXEL-T memanfaatkan basis data relasional PostgreSQL yang diorkestrasi melalui platform *Supabase Backend-as-a-Service* (BaaS). Arsitektur data dirancang secara terisolasi, efisien, dan mematuhi prinsip normalisasi data guna mendukung operasi inferensi segmentasi polip kolorektal secara waktu-nyata (*real-time*). Struktur relasi basis data sistem PIXEL-T disajikan pada Gambar IV.x berikut:

```
[Sisipkan Gambar: references/bab 4/ERD_PIXELT_FINAL.png]
Gambar IV.x Entity Relationship Diagram (ERD) Sistem PIXEL-T
```

Berdasarkan perancangan yang ditunjukkan pada Gambar IV.x, struktur basis data sistem PIXEL-T terdiri dari tiga entitas relasional utama, yaitu `users (auth.users)`, `doctor_profiles`, dan `analyses`. Masing-masing entitas memiliki fungsi, spesifikasi atribut, dan aturan integritas data yang diuraikan secara rinci pada bagian berikut.

---

### 1. Deskripsi Entitas Basis Data

#### a. Entitas `users (auth.users)`
Entitas `users` merupakan entitas inti autentikasi yang berada di bawah skema internal Supabase Auth (`auth.users`). Penggunaan skema terisolasi ini bertujuan untuk menjamin keamanan manajemen kredensial pengguna, enkripsi kata sandi berbasis *bcrypt*, serta penerbitan token *JSON Web Token* (JWT) yang aman. Entitas ini menyimpan informasi identitas dasar akun tenaga medis dengan rincian atribut sebagai berikut:
1. `id (UUID)`: Bertindak sebagai Kunci Primer (*Primary Key* - PK) unik global yang digenerasi secara otomatis saat pengguna berhasil melakukan registrasi akun.
2. `email (TEXT)`: Alamat surat elektronik terdaftar milik dokter atau tenaga medis yang digunakan sebagai identitas utama autentikasi login.
3. `created_at (TIMESTAMPTZ)`: Catatan stempel waktu presisi tinggi (*timestamp with time zone*) yang merekam tanggal dan jam pembuatan akun pengguna dalam zona waktu UTC.
4. `user_metadata (JSONB)`: Kolom data semi-terstruktur berformat *Binary JSON* yang menyimpan metadata tambahan bawaan dari penyedia otentikasi.

#### b. Entitas `doctor_profiles`
Entitas `doctor_profiles` merupakan tabel pada skema publik yang menyimpan informasi profil profesional, riwayat klinis, dan kredensial medis dari dokter pengguna sistem PIXEL-T. Pemisahan entitas ini dari data autentikasi dasar bertujuan untuk menjaga modularitas data dan memungkinkan penyesuaian profil klinis secara dinamis tanpa memodifikasi skema otentikasi inti. Atribut yang dikandung oleh entitas ini meliputi:
1. `id (UUID)`: Kunci Primer (*Primary Key* - PK) yang mengidentifikasi setiap rekaman profil dokter secara unik.
2. `user_id (UUID)`: Kunci Asing (*Foreign Key* - FK) yang merujuk pada atribut `id` pada entitas `users (auth.users)`. Kolom ini memiliki kendala unik (*UNIQUE constraint*) untuk memastikan seorang dokter hanya memiliki satu profil klinis.
3. `full_name (TEXT)`: Nama lengkap dokter beserta gelar akademik yang bersangkutan.
4. `phone (TEXT)`: Nomor telepon atau kontak resmi dokter yang dapat dihubungi.
5. `birth_date (DATE)`: Tanggal lahir dokter yang digunakan untuk validasi verifikasi identitas.
6. `city (TEXT)`: Kota domisili atau wilayah tempat dokter berpraktik.
7. `primary_specialty (TEXT)`: Bidang spesialisasi medis utama (misalnya: Gastroenterologi-Hepatologi, Bedah Digestif, atau Penyakit Dalam).
8. `hospital (TEXT)`: Nama institusi rumah sakit atau fasilitas kesehatan tempat dokter bertugas.
9. `department (TEXT)`: Unit kerja atau departemen klinis tempat dokter berafiliasi.
10. `str_number (TEXT)`: Nomor Surat Tanda Registrasi (STR) resmi yang diterbitkan oleh Konsil Kedokteran Indonesia sebagai bukti legalitas praktik kedokteran.
11. `is_verified (BOOLEAN)`: Status verifikasi akun klinis dokter yang menandakan keabsahan kredensial medis.
12. `bio (TEXT)`: Deskripsi naratif singkat mengenai riwayat klinis, minat penelitian, dan fokus keahlian dokter.
13. `education (JSONB)`: Kumpulan data terstruktur dinamis berbentuk larik (*array*) JSON yang menyimpan riwayat pendidikan formal, gelar, institusi, dan tahun kelulusan dokter.
14. `experience (JSONB)`: Kumpulan data terstruktur dinamis berformat JSON yang memuat riwayat pengalaman kerja klinis dan jabatan medis dokter.
15. `created_at (TIMESTAMPTZ)`: Stempel waktu pembuatan rekaman profil dokter.
16. `updated_at (TIMESTAMPTZ)`: Stempel waktu pembaruan terakhir data profil dokter.

#### c. Entitas `analyses`
Entitas `analyses` merupakan entitas transaksional utama yang merekam seluruh siklus hidup pemrosesan citra kolonoskopi, inferensi model pembelajaran mendalam (*deep learning*), hasil segmentasi polip, visualisasi *Explainable AI* (Grad-CAM), serta pemantauan tahapan komputasi. Atribut yang didefinisikan pada entitas ini adalah:
1. `id (UUID)`: Kunci Primer (*Primary Key* - PK) unik yang merepresentasikan identitas satu sesi analisis citra kolonoskopi.
2. `user_id (UUID)`: Kunci Asing (*Foreign Key* - FK) yang mereferensikan dokter pemilik analisis pada entitas `users (auth.users)`.
3. `status (VARCHAR(20))`: Status siklus hidup analisis dengan nilai terkendala (*CHECK constraint*), yaitu `processing` (sedang diproses), `completed` (berhasil selesai), atau `failed` (gagal).
4. `original_image_path (TEXT)`: Alamat jalur relatif penyimpanan berkas citra kolonoskopi asli pada wadah penyimpanan objek (*Supabase Storage*).
5. `original_filename (TEXT)`: Nama berkas citra asli yang diunggah oleh pengguna dari sistem komputer lokal.
6. `original_mime_type (VARCHAR(50))`: Tipe format media citra asli (misalnya: `image/jpeg` atau `image/png`).
7. `original_width (INTEGER)`: Dimensi lebar citra asli dalam satuan piksel.
8. `original_height (INTEGER)`: Dimensi tinggi citra asli dalam satuan piksel.
9. `binary_mask_path (TEXT)`: Alamat jalur penyimpanan citra masker biner hasil segmentasi model AI pada wadah penyimpanan objek.
10. `segmentation_overlay_path (TEXT)`: Alamat jalur penyimpanan berkas citra visualisasi tumpang susun (*overlay*) batas polip pada citra asli.
11. `segmentation_status (VARCHAR(20))`: Label status deteksi polip dengan batasan nilai `detected` (polip ditemukan) atau `not_detected` (polip tidak ditemukan).
12. `area_pixels (INTEGER)`: Luas area lesi polip yang terdeteksi dalam satuan piksel total.
13. `area_ratio (NUMERIC(7,4))`: Rasio persentase perbandingan antara luas area polip terhadap keseluruhan luas bidang citra endoskopi.
14. `gradcam_heatmap_path (TEXT)`: Alamat jalur penyimpanan berkas citra peta panas gradien (*Grad-CAM heatmap*) yang menggambarkan distribusi bobot atensi model AI.
15. `gradcam_overlay_path (TEXT)`: Alamat jalur penyimpanan citra hasil penggabungan visual antara peta panas Grad-CAM dan citra kolonoskopi asli.
16. `model_architecture (VARCHAR(100))`: Nama arsitektur model pembelajaran mendalam yang dieksekusi (misalnya: `Polyp-PVT / Pyramid Vision Transformer`).
17. `model_version (VARCHAR(50))`: Versi model dan parameter penimbang (*weights*) yang digunakan guna menjamin keterulangan (*reproducibility*) penelitian.
18. `summary_text (TEXT)`: Ringkasan teks naratif yang merangkum temuan kuantitatif klinis dari hasil segmentasi.
19. `current_step (VARCHAR(64))`: Indikator langkah atau tahapan komputasi yang sedang berjalan secara aktif pada antrian pemrosesan latar belakang.
20. `progress_percent (SMALLINT)`: Persentase progres komputasi analitik bernilai numerik bulat dari rentang 0 hingga 100.
21. `created_at (TIMESTAMPTZ)`: Stempel waktu ketika berkas citra pertama kali diunggah dan rekaman analisis dibuat.
22. `completed_at (TIMESTAMPTZ)`: Stempel waktu saat seluruh tahapan inferensi segmentasi dan ekstraksi Grad-CAM berhasil dituntaskan oleh sistem.

---

### 2. Relasi dan Kardinalitas Antar-Entitas

Relasi antarentitas dalam sistem basis data PIXEL-T dihubungkan menggunakan mekanisme integritas referensial berbasis *Foreign Key* dengan notasi kardinalitas *Information Engineering* (*Crow's Foot Notation*):

#### a. Relasi antara `users (auth.users)` dan `doctor_profiles` (Kardinalitas $1 : 0..1$)
Hubungan antara entitas `users` dan `doctor_profiles` diklasifikasikan sebagai relasi **Satu-ke-Nol/Satu (*One-to-Optional-One*)**:
- **Tinjauan Kardinalitas:** Setiap satu akun dokter yang terdaftar pada tabel `users (auth.users)` dapat memiliki paling banyak satu profil klinis pada tabel `doctor_profiles`. Pada awal pendaftaran sebelum dokter melengkapi berkas biodata, entri profil dokter dapat bernilai nol (*optional*). Sebaliknya, setiap satu rekaman pada `doctor_profiles` diwajibkan secara mutlak (*mandatory*) terikat tepat pada satu akun dokter terdaftar.
- **Penerapan Teknis:** Relasi ini diikat melalui atribut kunci asing `doctor_profiles.user_id` yang mereferensikan `users.id` dengan aturan kaskade `ON DELETE CASCADE`. Untuk mencegah terjadinya duplikasi profil pada akun yang sama, sistem memberlakukan kendala keunikan eksplisit:
  $$\text{CONSTRAINT } \texttt{doctor\_profiles\_user\_id\_key UNIQUE (user\_id)}$$
  Dengan adanya batasan ini, basis data secara otomatis menolak penyisipan rekaman profil kedua bagi pengguna yang sama.

#### b. Relasi antara `users (auth.users)` dan `analyses` (Kardinalitas $1 : N$)
Hubungan antara entitas `users` dan `analyses` diklasifikasikan sebagai relasi **Satu-ke-Banyak (*One-to-Many*)**:
- **Tinjauan Kardinalitas:** Satu orang dokter terdaftar (`users`) dapat melakukan pengunggahan dan pemrosesan analisis citra kolonoskopi sebanyak berkali-kali ($N$). Di sisi lain, setiap satu entri rekaman pemeriksaan pada entitas `analyses` wajib dimiliki secara eksklusif oleh tepat satu orang dokter yang sah.
- **Penerapan Teknis:** Relasi diwujudkan melalui atribut `analyses.user_id` sebagai kunci asing yang menunjuk pada `users.id` dengan kendala `NOT NULL` dan `ON DELETE CASCADE`. Apabila suatu akun dokter dihapus dari sistem, maka seluruh rekam jejak pemeriksaan yang terhubung dengan dokter tersebut akan dihapus secara otomatis demi mematuhi privasi data klinis.

---

### 3. Arsitektur Penyimpanan Berkas (*Object Storage*) dan Keamanan Data

Salah satu pertimbangan mendasar dalam perancangan basis data sistem PIXEL-T adalah pemisahan antara metadata terstruktur dengan berkas biner berukuran besar (*binary large objects*):

1. **Pemanfaatan Object Storage Supabase (`analysis-assets`):**
   Berkas citra medis kolonoskopi mentah, masker segmentasi biner, dan visualisasi peta panas Grad-CAM disimpan secara fisik pada wadah penyimpanan objek *cloud* terenkripsi bernama `analysis-assets`. Penyimpanan citra beresolusi tinggi di luar tabel relasional mencegah pembengkakan ukuran basis data (*database bloat*), menjaga efisiensi indeksasi memori (*buffer pool*), serta mengoptimalkan kecepatan *query* transaksi relasional.
2. **Representasi Jalur Relatif (*Path Storage*):**
   Entitas `analyses` tidak menyimpan data piksel citra secara langsung, melainkan menyimpan alamat jalur penyimpanan relatif (*virtual path*) berupa teks (misalnya: `original_image_path`, `binary_mask_path`, `segmentation_overlay_path`, dan `gradcam_heatmap_path`). Saat dokter mengakses antarmuka hasil segmentasi, *backend* mengonversi alamat jalur tersebut menjadi URL bertanda tangan aman (*Signed URL*) dengan masa berlaku terbatas (3600 detik) untuk menjaga kerahasiaan data medis.
3. **Isolasi Keamanan melalui Row Level Security (RLS):**
   Keamanan data medis ditegakkan pada tingkat lapisan basis data (*database engine*) menggunakan fitur *PostgreSQL Row Level Security* (RLS). Seluruh operasi pembacaan (`SELECT`), penambahan (`INSERT`), pembaruan (`UPDATE`), maupun penghapusan (`DELETE`) pada tabel `analyses` dan `doctor_profiles` dibatasi oleh kebijakan keamanan terprogram:
   $$\texttt{USING (auth.uid() = user\_id)}$$
   Aturan ini menjamin bahwa setiap dokter hanya memiliki wewenang untuk mengakses data profil dan riwayat analisis miliknya sendiri, serta mengeliminasi risiko kebocoran data antar-pengguna secara menyeluruh.

---

### 4. Ringkasan Perancangan Basis Data

Secara keseluruhan, pemodelan basis data melalui ERD pada sistem PIXEL-T berhasil menyatukan keunggulan performa basis data relasional PostgreSQL dengan fleksibilitas struktur JSONB, efisiensi *Object Storage*, serta kekokohan proteksi *Row Level Security*. Struktur yang ringkas, terarah, dan terbebas dari tabel redundan ini memberikan fondasi komputasi yang andal dalam menopang operasional sistem kecerdasan buatan klinis PIXEL-T.

