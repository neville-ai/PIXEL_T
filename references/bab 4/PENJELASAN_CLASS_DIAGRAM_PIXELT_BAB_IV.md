# PENJELASAN PERANCANGAN STRUKTUR KELAS (CLASS DIAGRAM) SISTEM PIXEL-T

Dokumen ini berisi naskah penjelasan akademik untuk **Bab IV Skripsi S1**, disusun dalam bahasa Indonesia formal dan selaras dengan implementasi kode sumber serta diagram kelas (*Class Diagram*) sistem PIXEL-T.

> **Petunjuk bagi Penulis:** Nomor subbab `4.x` dan nomor gambar `Gambar IV.x` merupakan *placeholder* yang disesuaikan dengan penomoran akhir skripsi.

---

## 4.x Perancangan Struktur Perangkat Lunak (Class Diagram)

Setelah memodelkan aspek fungsionalitas melalui *Use Case Diagram*, tahap perancangan berikutnya adalah mendefinisikan struktur statis perangkat lunak menggunakan *Class Diagram*. *Class Diagram* berfungsi untuk memetakan komponen-komponen perangkat lunak, mendefinisikan atribut dan operasi setiap kelas atau modul, serta menggambarkan relasi ketergantungan dan asosiasi antarkomponen dalam sistem PIXEL-T.

Antarmuka pengguna (*frontend*) dibangun menggunakan React 18 dengan TypeScript yang menerapkan paradigma komponen fungsional. Dalam rekayasa perangkat lunak modern, memaksakan komponen fungsional React ke dalam kelas berorientasi objek merupakan kesalahan pemodelan. Oleh karena itu, *Class Diagram* sistem PIXEL-T difokuskan pada arsitektur berorientasi objek di sisi peladen (*backend*), mesin inferensi kecerdasan buatan, dan entitas persistensi basis data relasional.

Rancangan kelas sistem PIXEL-T disajikan pada Gambar IV.x berikut:

```
[Sisipkan Gambar: references/bab 4/class_diagram.png]
Gambar IV.x Class Diagram Sistem PIXEL-T
```

Berdasarkan Gambar IV.x, komponen perangkat lunak sistem PIXEL-T terbagi ke dalam tiga lapisan tanggung jawab utama:

1. **Lapisan Layanan Bisnis dan Infrastruktur (*Service & Infrastructure Layer*)**
2. **Lapisan Mesin Kecerdasan Buatan (*AI Engine & Pipeline Layer*)**
3. **Lapisan Persistensi Basis Data (*Persistence Layer*)**

---

### 1. Deskripsi Komponen Berdasarkan Lapisan Arsitektur

#### A. Lapisan Layanan Bisnis dan Infrastruktur

Lapisan ini memuat komponen yang mengimplementasikan logika bisnis analisis, orkestrasi penyimpanan, dan komunikasi dengan layanan eksternal.

##### 1. Kelas `AnalysisService` (`«service»`)

Kelas `AnalysisService` diimplementasikan pada berkas `backend/app/services/analysis_service.py`. Kelas ini merupakan orkestrator utama yang mengendalikan seluruh siklus hidup analisis citra polip, mulai dari validasi masukan, pengunggahan berkas, penjadwalan inferensi latar belakang (*background inference*), hingga pembersihan data.

- **Atribut:**
  1. `+repository : AnalysisRepository` — Instans lapisan repositori untuk operasi basis data.
  2. `+storage_service : StorageService` — Instans layanan penyimpanan objek.
  3. `+pipeline_runner : Callable` — Fungsi yang mengacu pada `run_pipeline` untuk eksekusi inferensi AI.

- **Operasi:**
  1. `+validate_and_decode_image(file_storage) : tuple` — Memvalidasi ukuran berkas (maks. 10 MB), tipe MIME (`image/jpeg` atau `image/png`), dan integritas dimensi piksel menggunakan pustaka Pillow.
  2. `+create_analysis(file_storage, user_id : str) : Dict` — Mengunggah citra asli ke *Supabase Storage*, membuat rekaman awal pada tabel `analyses` berstatus `processing`, dan mengantrekan tugas inferensi.
  3. `+get_analysis(analysis_id : str, user_id : str) : Dict` — Mengambil rekaman analisis dan mengonversi jalur berkas menjadi *Signed URL* aktif.
  4. `+list_user_analyses(user_id : str) : list` — Mengambil daftar riwayat analisis milik pengguna yang bersangkutan.
  5. `+delete_analysis(analysis_id : str, user_id : str) : bool` — Menghapus rekaman pada basis data dan membersihkan seluruh berkas terkait di *Supabase Storage*.

##### 2. Kelas `StorageService` (`«service»`)

Kelas `StorageService` diimplementasikan pada berkas `backend/app/services/storage_service.py`. Kelas ini mengabstraksi komunikasi dengan wadah penyimpanan objek *Supabase Storage* bernama `analysis-assets`.

- **Atribut:**
  1. `+bucket_name : str` — Nama wadah penyimpanan, yaitu `analysis-assets`.

- **Operasi:**
  1. `+upload_file(path : str, file_bytes : bytes, content_type : str) : str` — Mengunggah berkas citra ke lokasi terproteksi pada *Supabase Storage*.
  2. `+create_signed_url(path : str, expires_in : int) : str` — Menerbitkan *Signed URL* berkedaluarsa yang memungkinkan berkas privat ditampilkan di antarmuka pengguna.
  3. `+delete_analysis_files(paths : List[str]) : bool` — Menghapus sekumpulan berkas secara sekaligus saat rekaman analisis dihapus.

##### 3. Kelas `AnalysisRepository` (`«repository»`)

Kelas `AnalysisRepository` diimplementasikan pada berkas `backend/app/repositories/analysis_repository.py`. Kelas ini menerapkan *Repository Pattern* untuk mengisolasi logika akses data dari logika bisnis.

- **Operasi:**
  1. `+create(user_id : str, data : Dict) : Dict` — Menyisipkan rekaman baru ke tabel `analyses`.
  2. `+get_by_id(analysis_id : str, user_id : str) : Optional[Dict]` — Mengambil rekaman berdasarkan kunci primer dengan verifikasi kepemilikan.
  3. `+list_by_user(user_id : str) : List` — Mengambil seluruh riwayat analisis pengguna, diurutkan berdasarkan waktu pembuatan terbaru.
  4. `+update(analysis_id : str, user_id : str, data : Dict) : Optional[Dict]` — Memperbarui hasil inferensi, status, dan metrik analisis.
  5. `+delete(analysis_id : str, user_id : str) : bool` — Menghapus rekaman analisis secara permanen.

---

#### B. Lapisan Mesin Kecerdasan Buatan (*AI Engine & Pipeline Layer*)

Lapisan ini memuat algoritma *deep learning*, model segmentasi citra kolonoskopi, dan modul transparansi keputusan model (*Explainable AI*).

##### 1. Modul `AI inference functions` (`«module»`)

Modul ini merepresentasikan kumpulan fungsi komputasi yang didefinisikan pada berkas `ai/inference/pipeline.py`, `ai/inference/segmentation.py`, `ai/inference/postprocessing.py`, dan `ai/inference/gradcam.py`. Stereotipe `«module»` mencerminkan struktur fungsi prosedural Python tanpa mendistorsinya menjadi kelas.

- **Fungsi-fungsi utama:**
  1. `+run_pipeline(original_bytes : bytes, config : ModelConfig) : PipelineResult` — Fungsi orkestrasi menyeluruh yang menjalankan seluruh tahapan inferensi secara sekuensial: pra-pemrosesan, segmentasi, pasca-pemrosesan, Grad-CAM, dan penyusunan artefak.
  2. `+predict(image : Image.Image, model_service : ModelService) : SegmentationResult` — Mengeksekusi inferensi segmentasi menggunakan model U-Net + ResNet50 untuk menghasilkan masker biner probabilitas polip.
  3. `+postprocess_mask(mask : np.ndarray, config : ModelConfig) : np.ndarray` — Menerapkan operasi morfologi untuk menyempurnakan kontur masker hasil segmentasi.
  4. `+measure_mask(mask : np.ndarray) : dict` — Menghitung estimasi luas area polip dalam piksel dan rasio terhadap keseluruhan citra.
  5. `+generate_gradcam(image_tensor : torch.Tensor, model_service : ModelService) : GradCAMResult` — Menghitung visualisasi peta atensi Grad-CAM pada lapisan konvolusi target.

##### 2. Kelas `ModelService` (`«service»`)

Kelas `ModelService` diimplementasikan pada berkas `ai/inference/model_service.py`. Kelas ini bertindak sebagai pengelola siklus hidup model PyTorch tunggal (*Singleton*) agar bobot model yang berukuran besar tidak dimuat ulang pada setiap permintaan inferensi.

- **Atribut:**
  1. `+config : ModelConfig` — Objek konfigurasi yang menyimpan parameter model (arsitektur UNet, *encoder* ResNet50, ukuran input, ambang batas binerisasi).
  2. `+device : torch.device` — Perangkat keras komputasi yang dialokasikan (GPU atau CPU).
  3. `+load_count : int` — Pencatat frekuensi pemuatan model ke dalam memori.

- **Operasi:**
  1. `+load() : torch.nn.Module` — Memuat arsitektur model dan bobot ke dalam memori secara *thread-safe*.
  2. `+metadata() : dict` — Mengembalikan informasi versi model dan parameter konfigurasi.
  3. `+predict_logits(tensor : torch.Tensor) : torch.Tensor` — Menjalankan komputasi *forward pass* untuk menghasilkan nilai *logits*.
  4. `+get_gradcam_target_layer() : torch.nn.Module` — Mengambil referensi lapisan konvolusi terakhir untuk kalkulasi gradien Grad-CAM.

---

#### C. Lapisan Persistensi Basis Data (*Persistence Layer*)

Lapisan ini memodelkan entitas data relasional yang digunakan oleh sistem PIXEL-T.

##### 1. Entitas `auth.users` (`«external»`)

Merepresentasikan tabel autentikasi eksternal yang dikelola oleh Supabase Auth. Atribut utamanya adalah `id : UUID` yang menjadi kunci induk bagi seluruh data pengguna dalam sistem.

##### 2. Entitas `doctor_profiles` (`«entity»`)

Merepresentasikan tabel `public.doctor_profiles` yang menyimpan informasi profil klinis dokter, meliputi: `id`, `user_id` (FK), `full_name`, `primary_specialty`, `hospital`, `education` (JSONB), `experience` (JSONB), dan `bio`.

##### 3. Entitas `analyses` (`«entity»`)

Merepresentasikan tabel utama `public.analyses` yang menyimpan seluruh siklus hidup analisis citra, meliputi: `id`, `user_id` (FK), `status`, jalur-jalur berkas artefak (`original_image_path`, `binary_mask_path`, `segmentation_overlay_path`, `gradcam_heatmap_path`, `gradcam_overlay_path`), metrik klinis (`area_pixels`, `area_ratio`, `segmentation_status`), metadata model, dan stempel waktu.

---

### 2. Relasi Antarkomponen dan Semantik Notasi UML

Seluruh relasi pada Gambar IV.x mengikuti standar UML 2.5 dengan semantik yang konsisten terhadap implementasi:

#### A. Relasi Asosiasi Basis Data (Garis Solid)

1. **`auth.users` — `doctor_profiles`** (Kardinalitas $1 : 0..1$): Satu akun pengguna dapat memiliki paling banyak satu profil dokter. Diikat melalui `doctor_profiles.user_id` dengan kendala UNIQUE.
2. **`auth.users` — `analyses`** (Kardinalitas $1 : 0..*$): Satu akun pengguna dapat memiliki banyak rekaman analisis. Diikat melalui `analyses.user_id` dengan aturan `ON DELETE CASCADE`.

#### B. Relasi Dependensi (Garis Putus-putus dengan Panah Terbuka `..>`)

Relasi dependensi menunjukkan ketergantungan penggunaan (*usage dependency*) — suatu komponen memanggil atau menggunakan komponen lain tanpa mengikat siklus hidupnya:

1. **`AnalysisService` → `AnalysisRepository`** (label `persistence`): `AnalysisService` mendelegasikan seluruh operasi baca/tulis basis data ke `AnalysisRepository`.
2. **`AnalysisService` → `StorageService`** (label `upload / assets`): `AnalysisService` menggunakan `StorageService` untuk mengunggah dan menghapus berkas citra.
3. **`AnalysisService` → `AI inference functions`** (label `background pipeline`): Metode pemrosesan latar belakang `AnalysisService` memanggil fungsi `run_pipeline` pada modul inferensi secara asinkron melalui *worker thread*.
4. **`AnalysisRepository` → `analyses`** (label `CRUD`): Repositori mengeksekusi operasi baca/tulis langsung ke tabel `analyses`.
5. **`AI inference functions` → `ModelService`** (label `inference / Grad-CAM`): Fungsi `predict()` dan `generate_gradcam()` menerima instans `ModelService` sebagai parameter untuk menjalankan inferensi dan kalkulasi gradien.

---

### 3. Alur Eksekusi Berdasarkan Struktur Kelas

Keterpaduan antarkomponen pada Gambar IV.x menopang tiga alur utama sistem:

1. **Alur Analisis Baru:** Permintaan HTTP diterima → `AnalysisService.validate_and_decode_image()` memvalidasi citra → `StorageService.upload_file()` menyimpan citra asli → `AnalysisRepository.create()` membuat rekaman berstatus `processing` → tugas inferensi diantrekan → `AI inference functions.run_pipeline()` memanggil `ModelService` untuk segmentasi dan Grad-CAM secara sekuensial → artefak disimpan kembali via `StorageService` → `AnalysisRepository.update()` mengubah status ke `completed`.

2. **Alur Pemantauan Hasil:** *Frontend* melakukan *polling* → permintaan GET ditangani → `AnalysisService.get_analysis()` membaca dari `AnalysisRepository.get_by_id()` → `StorageService.create_signed_url()` menerbitkan tautan aman berdurasi terbatas → data hasil disajikan ke antarmuka dokter.

3. **Alur Riwayat dan Profil:** Daftar riwayat diambil melalui `AnalysisRepository.list_by_user()`. Pengelolaan profil dokter berinteraksi langsung dengan entitas `doctor_profiles` melalui Supabase client di lapisan layanan profil (*frontend service layer*).

---

### 4. Ringkasan Perancangan Struktur Perangkat Lunak

*Class Diagram* sistem PIXEL-T menggambarkan arsitektur berlapis yang memisahkan tanggung jawab secara tegas: `AnalysisService` sebagai orkestrator bisnis, `StorageService` dan `AnalysisRepository` sebagai lapisan infrastruktur, modul `AI inference functions` sebagai mesin komputasi, dan entitas basis data sebagai lapisan persistensi. Pemisahan ini mendukung kemandirian setiap komponen dan memungkinkan pengujian serta pemeliharaan sistem secara terpisah.
