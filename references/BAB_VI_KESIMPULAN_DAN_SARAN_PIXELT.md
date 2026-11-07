# BAB VI

# KESIMPULAN DAN SARAN

## 6.1 Kesimpulan

Penelitian ini bertujuan mengembangkan sistem segmentasi polip usus pada citra endoskopi berbasis web dengan pendekatan Transfer Learning dan Explainable AI, menggunakan arsitektur U-Net dengan enkoder ResNet-50 dan visualisasi Grad-CAM. Berdasarkan seluruh hasil eksperimen, implementasi aplikasi web, dan pengujian yang dilakukan, berikut disajikan kesimpulan penelitian.

**1. Metode segmentasi yang dikembangkan**

Sistem segmentasi dikembangkan dengan arsitektur U-Net yang dikombinasikan dengan enkoder ResNet-50 (dilatih sebelumnya pada ImageNet melalui Transfer Learning) dan lapisan pengantar dekoder bertipe SCSE. Model menerima citra berukuran 512 × 512 piksel yang telah dinormalisasi, menghasilkan mask biner polip dengan ambang threshold 0,55, dan dilengkapi Test-Time Augmentation (TTA) lima skala berkelipatan lima orientasi (25 forward pass per citra) serta pasca-pemrosesan mask (operasi morfologi close dan open, filter komponen terkecil 25 piksel, pengisian lubang, dan pelurus kontur). Proses pelatihan dilakukan selama 130 epoch dengan ukuran batch 16, learning rate 1 × 10⁻⁴, pembekuan enkoder hingga epoch ke-5, eksponensial moving average (EMA) dengan peluruhan 0,999, dan fungsi loss gabungan BCE–Dice–Tversky–Lovasz dengan bobot masing-masing 0,10, 0,40, 0,35, dan 0,15. Pelatihan dihentikan pada epoch ke-83 berdasarkan mekanisme early stopping dengan kesalahan pengukuran paling rendah pada data validasi.

**2. Hasil evaluasi model**

Berdasarkan hasil evaluasi akhir pada data uji (TTA dan pasca-pemrosesan aktif), model memperoleh nilai Dice Coefficient 0,9510, Intersection over Union 0,9136, akurasi piksel 0,9918, presisi 0,9568, dan recall (sensitivitas) 0,9685, dengan jarak Hausdorff 95 persenil (HD95) sebesar 12,9049 piksel. Nilai Dice validasi terbaik (EMA) yang dicatat selama pelatihan adalah 0,9507. Hasil ini menunjukkan bahwa model mampu menghasilkan mask segmen yang secara 시각is berdekatan dengan anotasi mask ground truth pada data uji yang diuji. Nilai reaksi yang lebih tinggi dari presisi konsisten dengan pemilihan fungsi Tversky yang memberikan bobot lebih besar pada salah deteksi negatif (false negative), mengingat dalam konteks medis kegagalan mendeteksi polip dianggap lebih serius daripada alarm palsu.

**3. Keterbatasan data uji**

Seluruh citra dalam data uji berasal dari enam sumber publik dan berisi polip (data polip-positif); tidak terdapat citra endoskopi tanpa polip (citra normal) dalam data uji. Karena itulah, kinerja model pada citra yang tidak mengandung polip, termasuk risiko deteksi palsu pada citra normal, belum dapat ditentukan dari hasil evaluasi yang tersedia. Kesimpulan mengenai kinerja model bersifat bersyarat pada distribusi data uji yang telah diuji dan tidak dapat diperluas secara mutlak ke seluruh citra endoskopi dalam praktek klinis.

**4. Peran Explainable AI (Grad-CAM)**

Explainable AI diterapkan melalui Grad-CAM yang dihasilkan dari lapisan target `decoder.blocks.4.conv2.0` pada model segmentasi. Grad-CAM menghasilkan peta panas yang menunjukkan wilayah fitur yang berkontribusi pada prediksi segmen, ditampilkan sebagai heatmap dan overlay pada halaman hasil analisis. Visualisasi Grad-CAM dijalankan secara terpisah dari inferensi segmen (satu forward pass kanonik tanpa TTA) dan gagalnya Grad-CAM menyebabkan seluruh pekerjaan analisis ditandai gagal. Grad-CAM berfungsi sebagai bantuan visual interpretasi arah perhatian model, bukan sebagai bukti alasan klinis, tidak menjamin interpretabilitas penuh proses pengambilan keputusan model, dan tidak meningkatkan akurasi segmentasi secara langsung.

**5. Implementasi aplikasi web PIXEL-T**

Aplikasi web PIXEL-T berhasil dikembangkan sebagai aplikasi satu halaman (single-page application) dengan frontend React dan TypeScript, backend Flask, dan layanan autentikasi Supabase Auth. Tujuh fitur utama tersedia, yaitu Sign Up, Sign In, Upload Image, Segmentation, History, Doctor Profile, dan Sign Out. Alur kerja klinis mencakup unggah citra endoskopi, validasi citra (ekstensi, tipe MIME, ukuran maksimal 10 MB, dekodeabilitas), inferensi model melalui worker proses backend, penyimpanan empat artefak hasil (mask biner, overlay segmentasi, heatmap Grad-CAM, overlay Grad-CAM), pengukuran model yang dihasilkan (luas area segmen, rasio luas, dan kotak pembatas), penyimpanan riwayat analisis, dan pengelolaan profil dokter. Proteksi rute diterapkan melalui Protected Route pada klien dan verifikasi token Bearer pada setiap endpoint backend, sehingga user_id selalu diambil dari token autentikasi dan tidak pernah dari input klien.

**6. Pengujian fungsionalitas aplikasi**

Pengujian fungsionalitas frontend telah dilakukan dengan hasil 245 tes lulus dari 17 berkas tes, mencakup alur autentikasi, unggah citra, polling status analisis, riwayat, dan profil dokter. Pengujian backend dan lapisan AI tidak dapat dieksekusi pada mesin audit karena kebijakan kontrol aplikasi sistem operasi memblokir berkas pustaka PyTorch (`torch/lib/c10_cuda.dll`), sehingga pengujian tersebut tetap bersifat belum terverifikasi secara runtime pada lingkungan audit. Temuan implementasi yang relevan, antara lain: reset sesi saat membuka tab baru mengakhiri sesi di semua tab (startup reset pada AuthContext), riwayat analisis dibatasi maksimal 20 rekaman, polling halaman hasil berhenti setelah 12 percobaan (±60 detik), dan kebijakan tingkat baris (RLS) yang mengizinkan pengguna menulis dan mengubah baris analisis miliknya sendiri tanpa melalui backend. Temuan-temuan ini merupakan keterbatasan implementasi yang perlu dipertimbangkan dalam interpretasi kesesuaian aplikasi dengan tujuan penelitian.

**7. Jawaban terhadap rumusan masalah dan tujuan penelitian**

Berdasarkan uraian di atas, penelitian menjawab bahwa:
a) Metode Transfer Learning dengan U-Net dan enkoder ResNet-50 dapat mengembangkan model segmentasi polip usus pada citra endoskopi dengan kinerja tinggi pada data uji yang diuji (Dice 0,9510, IoU 0,9136, presisi 0,9568, reaksi 0,9685, HD95 12,9049 piksel);
b) Explainable AI melalui Grad-CAM dapat memberikan visualisasi fokus model sebagai pelengkap hasil segmentasi dalam aplikasi web;
c) Aplikasi web PIXEL-T telah mengimplementasikan alur kerja segmentasi polip dari unggah citra hingga penyajian hasil, riwayat, dan manajemen profil, dengan batasan yang tercantum pada poin 3 dan 6 di atas.

Kesimpulan ini terbatas pada bukti hasil eksperimen dan implementasi yang tersedia, dan tidak melayani klaim mengenai kebermanfaatan klinis, peningkatan diagnosis medis, atau kesiapan penggunaan dalam lingkungan klinis produksi.

---

## 6.2 Saran

Berdasarkan temuan dan keterbatalan penelitian di atas, berikut disajikan saran pengembangan sistem dan penelitian selanjutnya.

**1. Pengembangan dataset**

Data uji saat ini terdiri sepenuhnya dari citra berisi polip tanpa citra normal. Disarankan menambahkan variasi citra endoskopi, termasuk citra tanpa polip, dari lebih banyak sumber dan karakteristik polip yang bervariasi, serta mempertahankan konsistensi kualitas anotasi mask. Hal ini diperlukan untuk mengukur performa model pada kasus negatif dan mengurangi risiko deteksi palsu sebelum sistem diuji lebih luas.

**2. Pengembangan model segmentasi**

Hasil perbandingan skenario model yang tersedia secara verifikasi hanya mencakup skenario utama (U-Net dengan enkoder ResNet-50, Scenario 1 Ver.22). Disarankan melengkapi dan membandingkan kembali hasil skenario lain (misalnya U-Net murni dan ResNet-50 dengan kepala segmentasi tanpa koneksi lompat/skip connection) dengan rancangan eksperimen yang memungkinkan atribusi kinerja pada komponen arsitektur tertentu. Pengembangan lanjutan juga dapat mengevaluasi kembali penggunaan boundary loss (yang pada penelitian ini dinonaktifkan karena terbukti tidak membantu dan menjadi bottleneck waktu pelatihan), strategi Transfer Learning yang berbeda, konfigurasi pelatihan, serta penanganan ketidakseimbangan kelas.

**3. Pengembangan Explainable AI**

Grad-CAM pada penelitian ini memberikan visualisasi fokus model tetapi belum dievaluasi secara terstruktur terhadap interpretabilitas klinis. Disarankan melakukan evaluasi lebih lanjut terhadap visualisasi Grad-CAM, misalnya dengan uji kesesuaian area perhatian model terhadap anotasi mask ground truth, serta membandingkan dengan metode Explainable AI lain apabila diperlukan untuk penelitian selanjutnya.

**4. Pengembangan aplikasi web PIXEL-T**

Berdasarkan temuan implementasi, disarankan perbaikan dan pengembangan berikut:

- Mengatasi perilaku startup reset yang mengakhiri sesi di semua tab saat tab baru dibuka, sehingga ketersediaan sesi pengguna lebih stabil.
- Menyelaraskan batas riwayat analisis (maksimal 20 rekaman) dengan kebutuhan pengguna atau menambahkan navigasi halaman riwayat agar analisis lebih dari 20 rekaman dapat diakses.
- Memperpanjang atau memberi batas berbasis waktu pada polling halaman hasil agar halaman tidak terjebak pada status pemrosesan selama inferensi yang lambat.
- Membatasi operasi tulis dan ubah langsung pada tabel analisis melalui tingkat baris (RLS) sehingga integritas data analisis terjaga, dengan backend sebagai satu-satunya penulis data ilmiah.
- Memastikan kode kesalahan pipeline disampaikan secara utuh kepada pengguna dan mengatasi manajemen pekerjaan analisis yang macet setelah restart proses backend (pengaturan ulang status `processing` menjadi gagal pada startup).
- Menyelaraskan variabel konfigurasi lingkungan dengan parameter model yang sebenarnya digunakan pada waktu inferensi.

**5. Pengujian lanjutan**

Disarankan menjalankan pengujian backend dan lapisan AI pada lingkungan yang mengizinkan eksekusi pustaka PyTorch (misalnya WSL atau Linux) agar klaim pengujian lengkap dapat diperoleh. Selain itu, pengujian generalisasi model pada data eksternal, pengujian performa dan keamanan aplikasi, pengujian usability, serta evaluasi oleh tenaga medis atau ahli yang relevan merupakan peluang penelitian lanjutan yang relevan untuk memastikan kesiapan sistem sebelum digunakan dalam konteks yang lebih luas.

Kesimpulan dan saran pada bab ini terbatas pada hasil dan bukti yang tersedia dalam penelitian PIXEL-T, dan tidak melayani klaim yang melebihi cakupan eksperimen dan implementasi yang telah dilakukan.

---

*BAB VI disusun berdasarkan sumber internal penelitian PIXEL-T: dokumen prasyarat produk (PRD), spesifikasi integrasi model, spesifikasi fungsional, analisis codebase, arsip eksperimen (notebook, konfigurasi, dan hasil evaluasi), serta implementasi kode sumber aplikasi web. Tidak ada informasi yang diambil dari sumber web atau referensi eksternal.*
