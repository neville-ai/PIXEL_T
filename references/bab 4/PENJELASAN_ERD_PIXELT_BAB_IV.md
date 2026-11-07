# PENJELASAN PERANCANGAN BASIS DATA (ENTITY RELATIONSHIP DIAGRAM) SISTEM PIXEL-T

Dokumen ini berisi naskah penjelasan akademik untuk **Bab IV Skripsi S1**, disusun dalam bahasa Indonesia formal dan selaras dengan implementasi basis data PostgreSQL pada sistem PIXEL-T.

---

## 4.x Perancangan Basis Data (Entity Relationship Diagram)

Setelah mendefinisikan struktur perangkat lunak melalui *Class Diagram*, tahap perancangan berikutnya adalah memodelkan struktur basis data menggunakan *Entity Relationship Diagram* (ERD). Perancangan basis data bertujuan untuk mendefinisikan struktur penyimpanan data terstruktur, atribut-atribut setiap entitas, tipe data yang digunakan, serta relasi dan batasan integritas referensial antartabel dalam sistem PIXEL-T.

Sistem PIXEL-T memanfaatkan basis data relasional PostgreSQL yang dikelola melalui platform *Supabase Backend-as-a-Service* (BaaS). Arsitektur data dirancang secara terisolasi dan mengikuti prinsip normalisasi untuk mendukung operasi inferensi segmentasi polip kolorektal. Struktur relasi basis data sistem PIXEL-T disajikan pada Gambar IV.x berikut:

```
[Sisipkan Gambar: references/bab 4/ERD_PIXELT_FINAL.png]
Gambar IV.x Entity Relationship Diagram (ERD) Sistem PIXEL-T
```

Berdasarkan Gambar IV.x, struktur basis data sistem PIXEL-T terdiri dari tiga entitas relasional utama, yaitu `users (auth.users)`, `doctor_profiles`, dan `analyses`. Masing-masing entitas memiliki fungsi, spesifikasi atribut, dan aturan integritas data yang diuraikan pada bagian berikut.

---

### 1. Deskripsi Entitas Basis Data

#### a. Entitas `users (auth.users)`

Entitas `users` merupakan entitas autentikasi yang dikelola oleh skema internal Supabase Auth (`auth.users`). Penggunaan skema terisolasi ini memisahkan manajemen kredensial pengguna dari data aplikasi dan memastikan penerbitan token *JSON Web Token* (JWT) yang aman. Entitas ini menyimpan informasi identitas dasar akun tenaga medis dengan atribut sebagai berikut:

1. `id (UUID)`: Kunci Primer (*Primary Key*) unik global yang dibuat secara otomatis saat pengguna melakukan registrasi.
2. `email (TEXT)`: Alamat surat elektronik terdaftar yang digunakan sebagai identitas utama autentikasi.
3. `created_at (TIMESTAMPTZ)`: Stempel waktu pembuatan akun pengguna dalam zona waktu UTC.
4. `user_metadata (JSONB)`: Kolom semi-terstruktur yang menyimpan metadata tambahan pengguna, termasuk nama lengkap, institusi, dan spesialisasi yang dimasukkan saat pendaftaran.

#### b. Entitas `doctor_profiles`

Entitas `doctor_profiles` adalah tabel pada skema publik yang menyimpan informasi profil profesional dokter pengguna sistem PIXEL-T. Pemisahan entitas ini dari data autentikasi dasar menjaga modularitas dan memungkinkan pengelolaan profil klinis secara independen tanpa memodifikasi skema autentikasi inti. Atribut entitas ini adalah sebagai berikut:

1. `id (UUID)`: Kunci Primer (*Primary Key*) yang mengidentifikasi setiap rekaman profil dokter secara unik.
2. `user_id (UUID)`: Kunci Asing (*Foreign Key*) yang merujuk pada `users.id`, dengan kendala unik (*UNIQUE constraint*) untuk memastikan seorang pengguna hanya memiliki satu profil.
3. `full_name (TEXT)`: Nama lengkap dokter.
4. `phone (TEXT)`: Nomor telepon dokter.
5. `birth_date (DATE)`: Tanggal lahir dokter.
6. `city (TEXT)`: Kota domisili atau tempat dokter berpraktik.
7. `primary_specialty (TEXT)`: Bidang spesialisasi medis utama.
8. `hospital (TEXT)`: Nama institusi rumah sakit atau fasilitas kesehatan tempat dokter bertugas.
9. `department (TEXT)`: Unit atau departemen klinis tempat dokter berafiliasi.
10. `str_number (TEXT)`: Nomor Surat Tanda Registrasi resmi sebagai bukti legalitas praktik.
11. `is_verified (BOOLEAN)`: Status verifikasi akun klinis dokter.
12. `bio (TEXT)`: Deskripsi naratif ringkas profil dokter.
13. `education (JSONB)`: Data terstruktur berformat JSON yang menyimpan riwayat pendidikan formal dokter.
14. `experience (JSONB)`: Data terstruktur berformat JSON yang menyimpan riwayat pengalaman kerja klinis dokter.
15. `created_at (TIMESTAMPTZ)`: Stempel waktu pembuatan rekaman profil.
16. `updated_at (TIMESTAMPTZ)`: Stempel waktu pembaruan terakhir profil.

#### c. Entitas `analyses`

Entitas `analyses` adalah entitas transaksional utama yang merekam seluruh siklus hidup pemrosesan citra kolonoskopi: dari pengunggahan berkas hingga penyimpanan hasil inferensi model *deep learning* dan visualisasi *Explainable AI* (Grad-CAM). Atribut yang didefinisikan adalah sebagai berikut:

1. `id (UUID)`: Kunci Primer (*Primary Key*) yang merepresentasikan identitas satu sesi analisis.
2. `user_id (UUID)`: Kunci Asing (*Foreign Key*) yang mereferensikan dokter pemilik analisis pada `users.id`.
3. `status (VARCHAR(20))`: Status siklus hidup analisis dengan nilai terkendala: `processing`, `completed`, atau `failed`.
4. `original_image_path (TEXT)`: Jalur relatif penyimpanan berkas citra kolonoskopi asli pada *Supabase Storage*.
5. `original_filename (TEXT)`: Nama berkas citra asli yang diunggah pengguna.
6. `original_mime_type (VARCHAR(50))`: Tipe format media citra asli (`image/jpeg` atau `image/png`).
7. `original_width (INTEGER)`: Lebar citra asli dalam piksel.
8. `original_height (INTEGER)`: Tinggi citra asli dalam piksel.
9. `binary_mask_path (TEXT)`: Jalur penyimpanan citra masker biner hasil segmentasi.
10. `segmentation_overlay_path (TEXT)`: Jalur penyimpanan citra visualisasi tumpang susun (*overlay*) batas polip pada citra asli.
11. `segmentation_status (VARCHAR(20))`: Status deteksi polip: `detected` atau `not_detected`.
12. `area_pixels (INTEGER)`: Luas area polip yang terdeteksi dalam satuan piksel.
13. `area_ratio (NUMERIC(7,4))`: Rasio persentase luas polip terhadap keseluruhan citra.
14. `gradcam_heatmap_path (TEXT)`: Jalur penyimpanan citra peta panas Grad-CAM.
15. `gradcam_overlay_path (TEXT)`: Jalur penyimpanan citra penggabungan Grad-CAM dan citra asli.
16. `model_architecture (VARCHAR(100))`: Nama arsitektur model yang digunakan pada sesi analisis.
17. `model_version (VARCHAR(50))`: Versi bobot model yang digunakan.
18. `summary_text (TEXT)`: Ringkasan teks naratif hasil segmentasi.
19. `current_step (VARCHAR(64))`: Indikator tahapan komputasi yang sedang berjalan.
20. `progress_percent (SMALLINT)`: Persentase progres komputasi (0–100).
21. `created_at (TIMESTAMPTZ)`: Stempel waktu pembuatan rekaman analisis.
22. `completed_at (TIMESTAMPTZ)`: Stempel waktu saat seluruh tahapan inferensi berhasil dituntaskan.

---

### 2. Relasi dan Kardinalitas Antartabel

Relasi antartabel dalam basis data PIXEL-T dihubungkan menggunakan mekanisme *Foreign Key* dengan notasi kardinalitas *Crow's Foot*:

#### a. Relasi antara `users (auth.users)` dan `doctor_profiles` (Kardinalitas $1 : 0..1$)

Hubungan ini diklasifikasikan sebagai **Satu-ke-Nol/Satu (*One-to-Optional-One*)**: setiap akun dokter pada `users` dapat memiliki paling banyak satu profil klinis pada `doctor_profiles`. Sebelum dokter melengkapi data profil, entri pada `doctor_profiles` dapat bernilai kosong. Sebaliknya, setiap rekaman pada `doctor_profiles` wajib terikat pada tepat satu akun terdaftar.

Relasi ini diikat melalui `doctor_profiles.user_id` yang mereferensikan `users.id` dengan aturan `ON DELETE CASCADE` dan kendala unik:

$$\text{CONSTRAINT } \texttt{doctor\_profiles\_user\_id\_key UNIQUE (user\_id)}$$

Kendala ini mencegah pembuatan profil duplikat untuk pengguna yang sama.

#### b. Relasi antara `users (auth.users)` dan `analyses` (Kardinalitas $1 : N$)

Hubungan ini diklasifikasikan sebagai **Satu-ke-Banyak (*One-to-Many*)**: satu dokter terdaftar dapat melakukan pengunggahan dan pemrosesan analisis sebanyak $N$ kali. Setiap rekaman pada `analyses` dimiliki secara eksklusif oleh tepat satu dokter.

Relasi diwujudkan melalui `analyses.user_id` yang menunjuk pada `users.id` dengan kendala `NOT NULL` dan `ON DELETE CASCADE`. Apabila akun dokter dihapus, seluruh riwayat analisis yang terhubung akan dihapus secara otomatis.

---

### 3. Arsitektur Penyimpanan Berkas dan Keamanan Data

#### a. Pemisahan Basis Data dan Penyimpanan Objek

Berkas citra medis — citra kolonoskopi asli, masker segmentasi biner, dan visualisasi Grad-CAM — disimpan secara fisik pada wadah penyimpanan objek *cloud* (*Supabase Storage*) bernama `analysis-assets`, bukan di dalam tabel relasional. Tabel `analyses` hanya menyimpan jalur relatif berkas (*path storage*), misalnya nilai pada `original_image_path` atau `binary_mask_path`. Saat pengguna mengakses antarmuka hasil segmentasi, *backend* mengonversi jalur relatif tersebut menjadi *Signed URL* bertanda tangan aman dengan masa berlaku terbatas untuk menjaga kerahasiaan data medis.

#### b. Row Level Security (RLS)

Keamanan data ditegakkan pada tingkat mesin basis data menggunakan fitur *PostgreSQL Row Level Security* (RLS). Seluruh operasi pada tabel `analyses` dan `doctor_profiles` dibatasi oleh kebijakan:

$$\texttt{USING (auth.uid() = user\_id)}$$

Kebijakan ini memastikan setiap dokter hanya dapat mengakses data profil dan riwayat analisis miliknya sendiri.

---

### 4. Ringkasan Perancangan Basis Data

Struktur basis data PIXEL-T terdiri dari tiga entitas relasional yang saling terhubung: `auth.users` sebagai entitas autentikasi eksternal, `doctor_profiles` sebagai entitas profil klinis, dan `analyses` sebagai entitas transaksional utama. Pemisahan antara metadata terstruktur pada basis data PostgreSQL dan berkas biner pada *Supabase Storage*, dikombinasikan dengan perlindungan *Row Level Security*, membentuk fondasi penyimpanan data yang terorganisasi dan terisolasi per pengguna.
