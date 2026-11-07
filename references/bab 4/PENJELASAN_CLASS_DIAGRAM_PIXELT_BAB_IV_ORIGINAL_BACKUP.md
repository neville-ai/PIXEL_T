# PENJELASAN PERANCANGAN STRUKTUR KELAS (CLASS DIAGRAM) SISTEM PIXEL-T

Dokumen ini berisi naskah penjelasan akademik resmi untuk **Bab IV Skripsi S1**, yang disusun dengan bahasa Indonesia formal, ilmiah, runtut, dan mengadaptasi secara konsisten gaya penulisan pada naskah penjelasan basis data (*Entity Relationship Diagram*). Seluruh isi dokumen telah disinkronkan secara mendalam terhadap kode sumber implementasi aktual sistem PIXEL-T.

---

## 4.x Perancangan Struktur Perangkat Lunak (Class Diagram)

Setelah memodelkan aspek fungsionalitas sistem melalui *Use Case Diagram*, tahap perancangan berikutnya adalah mendefinisikan struktur statis perangkat lunak menggunakan *Class Diagram*. *Class Diagram* berfungsi untuk memetakan arsitektur komponen perangkat lunak, mendefinisikan kelas-kelas objek, modul fungsi, atribut internal, operasi atau metode, serta relasi ketergantungan dan kepemilikan struktural antar-komponen dalam sistem PIXEL-T.

Pada sistem PIXEL-T, antarmuka pengguna di sisi klien (*frontend*) dibangun menggunakan pustaka React 18 dengan TypeScript yang menerapkan paradigma fungsional murni berbasis komponen (*Functional Components*) dan kait khusus (*React Custom Hooks* seperti `useAuth` dan `useTheme`). Dalam kaidah rekayasa perangkat lunak modern, memaksakan halaman atau komponen fungsional React menjadi kelas berorientasi objek merupakan bentuk kesalahan pemodelan (*modeling anti-pattern*). Oleh karena itu, perancangan *Class Diagram* sistem PIXEL-T difokuskan secara mendalam dan terarah pada arsitektur berorientasi objek (*Object-Oriented Programming* - OOP) di sisi peladen (*backend application layer*), mesin inferensi kecerdasan buatan (*AI inference engine*), serta pemodelan entitas persistensi basis data relasional.

Struktur rancangan kelas sistem PIXEL-T disajikan pada Gambar IV.x berikut:

```
[Sisipkan Gambar: references/bab 4/class_diagram.png]
Gambar IV.x Class Diagram Sistem PIXEL-T
```

Berdasarkan arsitektur yang diilustrasikan pada Gambar IV.x, struktur perangkat lunak sistem PIXEL-T terbagi secara modular ke dalam empat lapisan tanggung jawab utama (*layered architecture*), yaitu:
1. **Lapisan Pengendali Web (*Web & Controller Layer*)**
2. **Lapisan Layanan Bisnis dan Infrastruktur (*Service & Infrastructure Layer*)**
3. **Lapisan Mesin Kecerdasan Buatan dan Pipeline (*AI Engine & Pipeline Layer*)**
4. **Lapisan Persistensi Basis Data (*Persistence Layer*)**

Rincian struktur kelas, fungsi atribut, spesifikasi metode, serta hubungan antar-kelas diuraikan secara komprehensif pada bagian berikut.

---

### 1. Deskripsi Detail Kelas Berdasarkan Lapisan Arsitektur

#### A. Lapisan Pengendali Web (Web & Controller Layer)

Lapisan ini bertindak sebagai gerbang terdepan di sisi peladen yang berinteraksi langsung dengan antarmuka web klien melalui protokol HTTP REST API.

##### 1. Kelas `AnalysisController` (`«controller»`)
Kelas `AnalysisController` diimplementasikan pada berkas `backend/app/controllers/analysis_controller.py`. Kelas ini bertanggung jawab menerima permintaan (*request*) HTTP dari dokter, memvalidasi parameter permintaan, mengoordinasikan eksekusi proses melalui lapisan *service*, serta memformat data kembalian (*response payload*) ke dalam format JSON.
- **Atribut:** Kelas ini tidak menyimpan data keadaan (*stateless*), melainkan menginjeksi instans `AnalysisService` sebagai dependensi pemrosesan.
- **Operasi dan Metode:**
  1. `+create_analysis() : Dict`: Menangani *endpoint* `POST /api/analysis`. Metode ini membaca berkas citra kolonoskopi yang diunggah (`request.files['image']`), mengekstrak identitas dokter terautentikasi (`user_id`), memicu inisiasi analisis, dan mengembalikan respons awal berstatus HTTP 202 (*Accepted*) yang memuat ID analisis.
  2. `+get_analysis(analysis_id : str) : Dict`: Menangani *endpoint* `GET /api/analysis/<analysis_id>`. Berfungsi mengambil rincian hasil segmentasi, status inferensi, ringkasan klinis, serta tautan berkas citra berkeamanan tinggi (*signed URL*) berdasarkan identitas analisis dan hak kepemilikan dokter.
  3. `+list_history() : List`: Menangani *endpoint* `GET /api/history`. Bertanggung jawab mengambil daftar seluruh rekam jejak pemeriksaan polip yang pernah dilakukan oleh dokter yang sedang aktif.
  4. `+delete_analysis(analysis_id : str) : bool`: Menangani *endpoint* `DELETE /api/history/<analysis_id>`. Menghapus rekaman analisis dari basis data serta membersihkan seluruh artefak citra fisik terkait dari media penyimpanan *cloud*.

---

#### B. Lapisan Layanan Bisnis dan Infrastruktur (Service & Infrastructure Layer)

Lapisan ini menerapkan pola *Separation of Concerns* (SoC) untuk memisahkan logika bisnis analisis medis dari mekanisme transportasi HTTP dan teknologi persistensi fisik.

##### 1. Kelas `AnalysisService` (`«service»`)
Kelas `AnalysisService` diimplementasikan pada berkas `backend/app/services/analysis_service.py`. Kelas ini merupakan inti orkestrator yang mengendalikan seluruh siklus hidup analisis citra polip, mulai dari validasi citra digital, manipulasi basis data, hingga penjadwalan komputasi AI di latar belakang.
- **Atribut Internal:**
  1. `+repository : AnalysisRepository`: Instans lapisan repositori untuk operasi transaksi data relasional.
  2. `+storage_service : StorageService`: Instans layanan penyimpanan objek untuk mengelola berkas citra fisik.
  3. `+pipeline_runner : Callable`: Penunjuk fungsi eksekusi *pipeline* kecerdasan buatan (mengacu pada `run_pipeline`).
  4. `+job_queue : AnalysisJobQueue`: Instans antrean pemrosesan asinkron multi-thread.
- **Operasi dan Metode:**
  1. `+validate_and_decode_image(file_storage) : tuple`: Melakukan sanitasi nama berkas untuk mencegah serangan *path traversal*, memvalidasi ukuran berkas (maksimum 10 MB), memeriksa tipe MIME (`image/jpeg` atau `image/png`), serta memverifikasi integritas dimensi piksel citra menggunakan pustaka Pillow sebelum dialirkan ke model AI.
  2. `+create_analysis(file_storage, user_id : str) : Dict`: Mengunggah citra asli ke *Supabase Storage*, mencatat rekaman awal pada tabel basis data dengan status `processing`, dan memasukkan tugas komputasi ke dalam antrean *job queue*.
  3. `+get_analysis(analysis_id : str, user_id : str) : Dict`: Mengambil rekaman analisis dari repositori, memastikan integritas status proses, serta mengonversi jalur berkas relatif menjadi *Signed URL* aktif dengan masa kedaluwarsa 3600 detik.
  4. `+list_user_analyses(user_id : str) : List`: Mengambil kumpulan riwayat analisis dokter dan menyematkan tautan *thumbnail* citra asli untuk kebutuhan pratinjau antarmuka.
  5. `+delete_analysis(analysis_id : str, user_id : str) : bool`: Mengoordinasikan penghapusan rekaman data pada basis data dan pembersihan multi-berkas citra fisik (gambar asli, masker, overlay, dan heatmap) secara atomik.

##### 2. Kelas `StorageService` (`«service»`)
Kelas `StorageService` diimplementasikan pada berkas `backend/app/services/storage_service.py`. Bertugas mengabstraksi komunikasi dengan wadah penyimpanan objek *Supabase Storage*.
- **Atribut Internal:**
  1. `+bucket_name : str`: Nama wadah penyimpanan privat terisolasi, yaitu `analysis-assets`.
- **Operasi dan Metode:**
  1. `+upload_file(path : str, file_bytes : bytes, content_type : str, user_id : str) : str`: Mengunggah aliran biner citra digital ke lokasi penyimpanan terproteksi berbasis struktur hierarki `analysis/{user_id}/{analysis_id}/{kategori}/{nama_berkas}`.
  2. `+create_signed_url(path : str, expires_in : int) : str`: Menerbitkan token URL bertanda tangan aman berekspirasi sementara agar berkas medis privat dapat diakses dan ditampilkan pada peramban web dokter.
  3. `+delete_analysis_files(paths : List[str], user_id : str) : bool`: Menghapus sekumpulan berkas aset fisik secara sekaligus saat riwayat analisis dihapus oleh pengguna.

##### 3. Kelas `AnalysisJobQueue` (`«service»`)
Kelas `AnalysisJobQueue` didefinisikan pada berkas `backend/app/services/analysis_service.py`. Kelas ini merupakan implementasi antrean kerja *thread-safe* memori berbasis mekanisme sinkronisasi primitif `threading.Lock` dan `threading.Condition`.
- **Atribut Internal:**
  1. `+capacity : int`: Kapasitas batas penerimaan beban tugas komputasi dalam antrean memori.
- **Operasi dan Metode:**
  1. `+try_enqueue(job : Dict) : bool`: Memasukkan paket data pekerjaan analisis baru ke dalam antrean FIFO. Mengembalikan nilai `False` jika antrean telah mencapai kapasitas penuh (*overload protection*).
  2. `+contains(analysis_id : str) : bool`: Memeriksa apakah suatu identitas analisis sedang aktif dieksekusi atau masih berada dalam status menunggu antrean.
  3. `+pending_count() : int`: Mengembalikan jumlah total pekerjaan yang sedang mengantre.
  4. `+drain_one() : bool`: Menjalankan tepat satu tugas inferensi secara berurutan dan mengelola siklus hidup *worker thread*.

##### 4. Kelas `AnalysisRepository` (`«repository»`)
Kelas `AnalysisRepository` diimplementasikan pada berkas `backend/app/repositories/analysis_repository.py`. Kelas ini menerapkan *Repository Pattern* untuk mengisolasi logika akses data relasional SQL dari logika bisnis aplikasi.
- **Operasi dan Metode:**
  1. `+create(user_id : str, data : Dict) : Dict`: Menyisipkan baris rekaman baru ke dalam tabel basis data `analyses`.
  2. `+get_by_id(analysis_id : str, user_id : str) : Optional[Dict]`: Menjalankan kueri seleksi data berdasarkan kunci primer `id` dengan klausul keamanan kepemilikan akun dokter (`user_id`).
  3. `+list_by_user(user_id : str) : List`: Mengambil seluruh koleksi riwayat analisis milik pengguna tertentu yang diurutkan secara menurun (*descending*) berdasarkan stempel waktu pembuatan.
  4. `+update(analysis_id : str, user_id : str, data : Dict) : Optional[Dict]`: Memperbarui data hasil inferensi, status penyelesaian, progres tahapan komputasi, dan metrik kuantitatif polip.
  5. `+delete(analysis_id : str, user_id : str) : bool`: Menghapus baris rekaman analisis secara permanen dari tabel basis data.

---

#### C. Lapisan Mesin Kecerdasan Buatan dan Pipeline (AI Engine & Pipeline Layer)

Lapisan ini memuat algoritma pembelajaran mendalam (*deep learning*), model segmentasi citra kolonoskopi, serta modul transparansi keputusan model (*Explainable AI*).

##### 1. Modul `AIInferenceFunctions` (`«module»`)
Modul `AIInferenceFunctions` merepresentasikan kumpulan fungsi komputasi tingkat tinggi yang didefinisikan secara modular pada berkas `ai/inference/pipeline.py`, `ai/inference/segmentation.py`, `ai/inference/postprocessing.py`, dan `ai/inference/gradcam.py`. Penggunaan stereotipe UML `«module»` secara tepat mencerminkan struktur fungsi prosedural PyTorch pada Python tanpa mendistorsinya menjadi kelas semu.
- **Operasi dan Fungsi:**
  1. `+run_pipeline(original_bytes : bytes, config : ModelConfig) : PipelineResult`: Fungsi orkestrasi pemrosesan menyeluruh yang menerima aliran biner citra asli, menjalankan inferensi model, melakukan pascapemrosesan morfologi, mengekstrak peta panas Grad-CAM, mengukur dimensi lesi, dan membungkus seluruh artefak ke dalam objek `PipelineResult`.
  2. `+predict(image : Image.Image, model_service : ModelService, config : ModelConfig) : SegmentationResult`: Mengeksekusi inferensi segmentasi berbasis teknik *Test-Time Augmentation* (TTA) multi-skala dan rotasi untuk menghasilkan probabilitas prediksi piksel yang stabil.
  3. `+postprocess_mask(mask : np.ndarray, config : ModelConfig) : np.ndarray`: Menerapkan operasi morfologi citra medis (penghapusan pulau biner palsu di bawah batas area minimum `postprocessing_min_area`) guna menyempurnakan kontur tepi polip.
  4. `+measure_mask(mask : np.ndarray) : dict`: Menghitung estimasi luas area polip dalam piksel (`area_pixels`) serta rasio persentase luasan lesi terhadap bidang pandang endoskopi (`area_ratio`).
  5. `+generate_gradcam(image_tensor : torch.Tensor, model_service : ModelService) : GradCAMResult`: Menghitung gradien bobot aktivasi pada lapisan konvolusi target untuk merekonstruksi visualisasi peta atensi visual (*Explainable AI*).

##### 2. Kelas `ModelService` (`«service»`)
Kelas `ModelService` diimplementasikan pada berkas `ai/inference/model_service.py`. Bertindak sebagai pengelola siklus hidup model PyTorch tunggal (*Singleton Service*) agar berkas bobot model berukuran besar tidak dimuat ulang pada setiap permintaan inferensi.
- **Atribut Internal:**
  1. `+config : ModelConfig`: Objek konfigurasi model yang menjadi acuan parameter komputasi.
  2. `+device : torch.device`: Perangkat keras komputasi yang dialokasikan (GPU CUDA atau CPU).
  3. `+load_count : int`: Pencatat frekuensi inisialisasi pemuatan model ke dalam memori.
- **Operasi dan Metode:**
  1. `+load() : torch.nn.Module`: Memuat arsitektur model UNet dengan tulang punggung ResNet50 ke dalam memori kerja perangkat komputasi secara *thread-safe*.
  2. `+metadata() : dict`: Mengembalikan informasi rincian versi model, ukuran input, nama lapisan target, dan penanda verifikasi integritas bobot.
  3. `+predict_logits(tensor : torch.Tensor) : torch.Tensor`: Menjalankan komputasi umpan-maju (*forward pass*) untuk memproduksi nilai *logits* prediksi mentah.
  4. `+get_gradcam_target_layer() : torch.nn.Module`: Mengambil referensi lapisan konvolusional terakhir pada arsitektur jaringan saraf tiruan untuk kalkulasi gradien Grad-CAM.

##### 3. Kelas `ModelConfig` (`«dataclass»`)
Didefinisikan pada berkas `ai/config/model_config.py` sebagai kelas konfigurasi tak-berubah (*immutable frozen dataclass*).
- **Atribut Konfigurasi:**
  1. `+architecture : str`: Nama varian arsitektur jaringan saraf tiruan (UNet).
  2. `+encoder : str`: Arsitektur ekstraktor fitur atau *backbone* (ResNet50).
  3. `+input_size : int`: Resolusi dimensi citra masukan model (misalnya 512 piksel).
  4. `+threshold : float`: Nilai ambang batas binerisasi probabilitas (misalnya 0.50).
  5. `+tta_enabled : bool`: Penanda aktivasi augmentasi waktu pengujian (*Test-Time Augmentation*).
  6. `+gradcam_target_layer : str`: Nama lapisan konvolusi target ekstraksi Grad-CAM.
  7. `+checkpoint_sha256 : str`: Nilai *hash* kriptografis SHA-256 untuk memverifikasi keaslian berkas bobot model.
  8. `+postprocessing_enabled : bool`: Status pengaktifan pembersihan morfologi pascasegmentasi.
  9. `+postprocessing_min_area : int`: Luas area piksel minimum penapisan derau biner.
- **Operasi dan Metode:**
  1. `+checkpoint_path : Path`: Properti jalur absolut berkas model berbobot (`.pth`).
  2. `+validate() : None`: Memvalidasi kelayakan parameter konfigurasi saat inisialisasi aplikasi.
  3. `+checkpoint_sha256_matches(path : Path) : bool`: Memverifikasi kecocokan *checksum* berkas bobot guna menjamin keterulangan (*reproducibility*) penelitian.

##### 4. Kelas Struktur Data Hasil Inferensi (`«dataclass»`)
1. **`SegmentationResult` (`«dataclass»`):** Didefinisikan pada `ai/inference/segmentation.py`. Membungkus luaran inferensi segmentasi mentah yang terdiri atas tensor peta probabilitas (`probability_map : torch.Tensor`), tensor masker biner (`binary_mask : torch.Tensor`), dan nilai ambang batas (`threshold : float`).
2. **`GradCAMResult` (`«dataclass»`):** Didefinisikan pada `ai/inference/gradcam.py`. Menyimpan struktur data peta panas atensi model, meliputi larik numerik matriks panas (`heatmap : np.ndarray`), citra tumpang susun Grad-CAM (`overlay : np.ndarray`), nama lapisan target (`target_layer : str`), fungsi objektif target (`target_objective : str`), dan status kekosongan masker (`target_mask_empty : bool`).
3. **`PipelineResult` (`«dataclass»`):** Didefinisikan pada berkas `ai/inference/pipeline.py`. Merupakan agregator data akhir yang merangkum seluruh hasil pemrosesan ke dalam format yang siap disimpan dan ditransmisikan: aliran biner masker (`binary_mask_png : bytes`), aliran biner citra tumpang susun segmentasi (`segmentation_overlay_png : bytes`), biner heatmap (`gradcam_heatmap_png : bytes`), biner overlay heatmap (`gradcam_overlay_png : bytes`), kamus pengukuran klinis (`measurements : dict`), ringkasan teks temuan medis (`summary_text : str`), serta objek hasil interpretabilitas (`gradcam : GradCAMResult`).

---

#### D. Lapisan Persistensi Basis Data (Persistence Layer)

Lapisan ini memodelkan struktur entitas data relasional pada basis data PostgreSQL yang diakses dan dikelola oleh sistem PIXEL-T.

##### 1. Entitas `auth_users` (`«external»`)
Merepresentasikan tabel data otentikasi eksternal yang dikelola oleh skema terproteksi Supabase Auth (`auth.users`). Memiliki atribut kunci primer global `id : UUID` yang menjadi entitas induk bagi relasi kepemilikan seluruh akun dokter dan transaksi pemeriksaan.

##### 2. Entitas `doctor_profiles` (`«entity»`)
Merepresentasikan tabel relasional `public.doctor_profiles` pada skema basis data PostgreSQL yang menyimpan informasi biodata klinis dokter:
- `id : UUID`: Kunci Primer (*Primary Key*).
- `user_id : UUID`: Kunci Asing (*Foreign Key*) dengan batasan unik (*UNIQUE*) yang merujuk pada `auth_users.id`.
- `full_name : TEXT`: Nama lengkap dokter beserta gelar akademik.
- `primary_specialty : TEXT`: Spesialisasi medis utama (misalnya Gastroenterologi).
- `hospital : TEXT`: Rumah sakit atau institusi tempat dokter berpraktik.
- `education : JSONB`: Riwayat pendidikan formal dokter dalam format JSON semi-terstruktur.
- `experience : JSONB`: Riwayat pengalaman klinis dokter dalam format JSON semi-terstruktur.
- `bio : TEXT`: Deskripsi naratif ringkas profil klinis dokter.

##### 3. Entitas `analyses` (`«entity»`)
Merepresentasikan tabel utama `public.analyses` yang menyimpan seluruh siklus hidup inferensi dan rekam medis digital polip kolorektal:
- `id : UUID`: Kunci Primer (*Primary Key*) identitas analisis.
- `user_id : UUID`: Kunci Asing (*Foreign Key*) perujuk dokter pemilik data pada `auth_users.id`.
- `original_image_path : TEXT`: Alamat relatif berkas citra asli pada *Supabase Storage*.
- `binary_mask_path : TEXT`: Alamat relatif berkas masker biner hasil segmentasi.
- `segmentation_overlay_path : TEXT`: Alamat berkas citra visualisasi tumpang susun kontur polip.
- `area_pixels : INTEGER`: Estimasi luasan lesi polip dalam satuan piksel.
- `area_ratio : NUMERIC`: Rasio luasan lesi polip terhadap total bidang pandang citra.
- `gradcam_heatmap_path : TEXT`: Alamat berkas citra peta panas Grad-CAM.
- `gradcam_overlay_path : TEXT`: Alamat berkas citra penggabungan Grad-CAM dan citra asli.
- `model_input_size : INTEGER`: Resolusi input inferensi yang digunakan.
- `model_threshold : NUMERIC`: Nilai ambang batas binerisasi inferensi.
- `summary_text : TEXT`: Ringkasan naratif hasil pembacaan kuantitatif citra polip.
- `created_at : TIMESTAMPTZ`: Stempel waktu pembuatan analisis.
- `updated_at : TIMESTAMPTZ`: Stempel waktu pembaruan rekaman data.
- `status : VARCHAR(20)`: Status siklus hidup proses (`processing`, `completed`, atau `failed`).
- `segmentation_status : VARCHAR(20)`: Status deteksi polip (`detected` atau `not_detected`).
- `gradcam_target_layer : VARCHAR(100)`: Nama lapisan jaringan syaraf target Grad-CAM.
- `model_architecture : VARCHAR(100)`: Varian arsitektur model AI yang mengeksekusi analisis.
- `model_version : VARCHAR(50)`: Versi parameter penimbang (*checkpoint weights*) model.

---

### 2. Relasi Antar-Kelas dan Semantik Notasi UML

Relasi antar-kelas pada Gambar IV.x mematuhi standar baku spesifikasi OMG UML 2.5 dengan makna semantik yang didukung secara penuh oleh kode sumber sistem PIXEL-T:

#### A. Relasi Komposisi (Composition — Simbol Wajik Hitam Pejal)
Komposisi menyatakan hubungan kepemilikan siklus hidup yang kuat (*strong ownership/whole-part relationship*), di mana keberadaan bagian (*part*) terikat secara permanen pada keberadaan entitas pemiliknya (*whole*):
1. **`AnalysisService` $\blacklozenge\hspace{-0.5em}\longrightarrow$ `AnalysisRepository`, `StorageService`, `AnalysisJobQueue`:**  
   Pada berkas `analysis_service.py` baris 288–293, konstruktor kelas `AnalysisService` menginisialisasi dan memiliki secara langsung instans dari `AnalysisRepository`, `StorageService`, dan `AnalysisJobQueue`. Komponen-komponen pendukung ini diciptakan bersamaan dengan diciptakannya *service* dan hidup di dalam lingkup instans tersebut.
2. **`PipelineResult` $\blacklozenge\hspace{-0.5em}\longrightarrow$ `GradCAMResult`:**  
   Pada berkas `ai/inference/pipeline.py` baris 65, kelas `@dataclass class PipelineResult` memiliki atribut internal `gradcam: GradCAMResult`. Objek `GradCAMResult` menjadi bagian tak terpisahkan dari struktur hasil akhir pipa inferensi yang dibentuk pada satu siklus eksekusi.

#### B. Relasi Dependensi (Dependency — Simbol Garis Putus-putus dengan Panah Terbuka)
Dependensi menunjukkan ketergantungan pemakaian (*usage dependency*), di mana perubahan pada suatu elemen penyedia (*supplier*) dapat memengaruhi elemen klien (*client*), namun klien tidak mengikat siklus hidup objek tersebut:
1. **`AnalysisController` $\dashrightarrow$ `AnalysisService` (Label `calls`):**  
   Pengendali HTTP memanggil operasi bisnis pada `AnalysisService` untuk melayani rute permintaan web tanpa mengikat siklus hidupnya secara kaku.
2. **`AnalysisService` $\dashrightarrow$ `AIInferenceFunctions` (Label `background pipeline`):**  
   Metode pekerja latar belakang `_execute_pipeline` pada `AnalysisService` memanggil fungsi tingkat modul `run_pipeline` secara asinkron di dalam *worker thread*.
3. **`AIInferenceFunctions` $\dashrightarrow$ `SegmentationResult` (Label `predict output`):**  
   Fungsi `predict()` memanfaatkan kelas dataclass `SegmentationResult` sebagai tipe data kembalian hasil segmentasi probabilitas dan biner.
4. **`AIInferenceFunctions` $\dashrightarrow$ `ModelService` (Label `inference / Grad-CAM`):**  
   Fungsi `predict()` dan `generate_gradcam()` menerima instans `ModelService` sebagai parameter operasi guna mengeksekusi inferensi umpan-maju (*forward pass*) dan perambatan mundur gradien (*backward pass*).

#### C. Relasi Asosiasi Terarah (Directed Association — Simbol Garis Solid)
1. **`AnalysisRepository` $\longrightarrow$ `analyses` (Label `CRUD`):**  
   Lapisan repositori memiliki relasi asosiasi terarah dengan entitas basis data `analyses` untuk menjalankan manipulasi data (*Create, Read, Update, Delete*).
2. **`ModelService` $\longrightarrow$ `ModelConfig` (Label `uses`):**  
   Pada `model_service.py` baris 34, kelas `ModelService` memegang referensi asosiasi navigasi langsung ke objek `ModelConfig` melalui atribut `self.config = config` untuk membaca konfigurasi arsitektur jaringan.

#### D. Relasi Asosiasi Entitas Relasional Basis Data
1. **`auth_users` $\longleftrightarrow$ `doctor_profiles` (Kardinalitas $1 : 0..1$):**  
   Relasi Satu-ke-Nol/Satu (*One-to-Optional-One*). Satu pengguna terdaftar pada `auth_users` dapat memiliki paling banyak satu profil dokter yang terikat melalui kunci asing `user_id` dengan batasan `UNIQUE` (`doctor_profiles_user_id_key`).
2. **`auth_users` $\longleftrightarrow$ `analyses` (Kardinalitas $1 : 0..*$):**  
   Relasi Satu-ke-Banyak (*One-to-Many*). Satu akun dokter terdaftar dapat memiliki banyak ($0..*$) rekaman riwayat analisis polip kolorektal yang terikat melalui kunci asing `analyses.user_id` dengan aturan kaskade `ON DELETE CASCADE`.

---

### 3. Validasi Alur Eksekusi Sistem Berdasarkan Struktur Kelas

Keterpaduan antar-kelas pada Gambar IV.x terbukti mampu menopang seluruh alur skenario fungsional pada aplikasi web PIXEL-T:

1. **Alur Analisis Baru (*New Analysis Workflow*):**  
   Dokter memilih citra kolonoskopi pada halaman antarmuka web $\rightarrow$ permintaan dialirkan ke `AnalysisController.create_analysis()` $\rightarrow$ divalidasi format dan dimensinya oleh `AnalysisService.validate_and_decode_image()` $\rightarrow$ berkas citra asli diunggah ke *storage* via `StorageService.upload_file()` $\rightarrow$ rekaman awal berstatus `processing` dibuat oleh `AnalysisRepository.create()` $\rightarrow$ pekerjaan dimasukkan ke dalam antrean `AnalysisJobQueue.try_enqueue()` $\rightarrow$ fungsi asinkron `AIInferenceFunctions.run_pipeline()` memanggil model pada `ModelService` untuk menghasilkan masker dan peta Grad-CAM $\rightarrow$ seluruh artefak disimpan kembali oleh `StorageService` $\rightarrow$ rekaman diperbarui menjadi `completed` beserta metrik klinis polip oleh `AnalysisRepository.update()`.
2. **Alur Pemantauan dan Peninjauan Hasil (*Polling & Result Display Workflow*):**  
   Antarmuka web secara berkala memanggil `AnalysisController.get_analysis()` $\rightarrow$ `AnalysisService` membaca data dari `AnalysisRepository.get_by_id()` $\rightarrow$ `StorageService.create_signed_url()` menerbitkan tautan aman berdurasi terbatas untuk citra masker, overlay, dan heatmap $\rightarrow$ data hasil diagnosis disajikan secara interaktif kepada dokter.
3. **Alur Riwayat dan Pengelolaan Profil (*History & Doctor Profile Workflow*):**  
   Permintaan peninjauan riwayat ditangani melalui `AnalysisController.list_history()` yang didelegasikan ke `AnalysisRepository.list_by_user()`. Sementara itu, pengelolaan biodata klinis dokter terhubung langsung dengan entitas `doctor_profiles`.

---

### 4. Ringkasan Perancangan Struktur Perangkat Lunak

Melalui perancangan *Class Diagram* yang disajikan, sistem PIXEL-T berhasil menerapkan prinsip arsitektur perangkat lunak yang bersih (*Clean Architecture*), terstruktur, dan modular. Pemisahan peran yang tegas antara lapisan pengendali, lapisan layanan bisnis, lapisan antrean asinkron, repositori data, mesin kecerdasan buatan, serta entitas persistensi memastikan sistem memiliki tingkat skalabilitas (*scalability*) yang tinggi, kemudahan pemeliharaan (*maintainability*), serta ketahanan konkurensi komputasi yang kokoh dalam menunjang operasional medis klinis deteksi polip kolorektal.

