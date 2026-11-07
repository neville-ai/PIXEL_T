# SPESIFIKASI TUJUH USE CASE — SISTEM PIXEL-T
**Dokumen untuk Bab IV Skripsi S1**
Disusun berdasarkan analisis implementasi aktual kode sumber web PIXEL-T.

---

## Tabel 4.x — Spesifikasi Use Case Sign Up

| Bagian             | Keterangan |
|--------------------|------------|
| **Aktor**          | Pengguna (Belum Terdaftar) |
| **Trigger & Tipe** | Pengguna mengakses halaman `/register` dan mengisi formulir pendaftaran. Tipe: *User-initiated*, *Synchronous*. |
| **Pre-Conditions** | 1. Pengguna belum memiliki akun PIXEL-T.<br>2. Pengguna belum berada dalam sesi autentikasi yang aktif. |
| **Normal Course**  | 1. Pengguna membuka halaman Sign Up (`/register`) melalui tautan yang tersedia di halaman Sign In.<br>2. Sistem menampilkan formulir pendaftaran yang memuat tiga kolom: *Full Name*, *Email Address*, dan *Password*.<br>3. Pengguna mengisi seluruh kolom dan menekan tombol **Create Account**.<br>4. Sistem melakukan validasi sisi klien: (a) memastikan kolom nama tidak kosong, (b) memverifikasi format email dengan pola regex, (c) memastikan panjang kata sandi minimal 8 karakter, dan (d) memastikan kolom kata sandi tidak kosong.<br>5. Apabila validasi lolos, sistem memanggil fungsi `signUp(fullName, email, password)` pada `AuthContext.tsx` yang meneruskan permintaan ke `supabase.auth.signUp()`.<br>6. Supabase Auth membuat rekaman akun baru pada tabel `auth.users` dan mengirimkan email verifikasi ke alamat yang didaftarkan.<br>7. Sistem menampilkan pesan sukses kepada pengguna yang menginformasikan bahwa akun berhasil dibuat dan email konfirmasi telah dikirim.<br>8. Pengguna diarahkan kembali ke halaman Sign In (`/login`) untuk masuk menggunakan akun yang baru dibuat. |
| **Post Condition** | Rekaman akun baru berhasil dibuat pada `auth.users` Supabase. Pengguna berada di halaman Sign In dan dapat segera masuk ke sistem. |

---

## Tabel 4.x — Spesifikasi Use Case Sign In

| Bagian             | Keterangan |
|--------------------|------------|
| **Aktor**          | Pengguna Terdaftar (Dokter / Tenaga Medis) |
| **Trigger & Tipe** | Pengguna mengakses halaman `/login` dan memasukkan kredensial. Tipe: *User-initiated*, *Synchronous*. |
| **Pre-Conditions** | 1. Pengguna telah memiliki akun PIXEL-T yang terdaftar.<br>2. Pengguna belum berada dalam sesi autentikasi yang aktif. |
| **Normal Course**  | 1. Pengguna membuka halaman Sign In (`/login`). Sistem menampilkan formulir yang memuat kolom *Email Address* dan *Password*, serta opsi *Remember Me*.<br>2. Pengguna mengisi alamat email dan kata sandi, kemudian menekan tombol **Sign In**.<br>3. Sistem melakukan validasi sisi klien: (a) memastikan kolom email tidak kosong dan (b) memastikan kolom kata sandi tidak kosong.<br>4. Jika opsi *Remember Me* diaktifkan, sistem menyimpan alamat email ke `localStorage` melalui fungsi `setRememberedEmail()` agar formulir dapat terisi otomatis pada kunjungan berikutnya.<br>5. Sistem memanggil fungsi `signIn(email, password)` pada `AuthContext.tsx` yang meneruskan permintaan ke `supabase.auth.signInWithPassword()`.<br>6. Supabase Auth memverifikasi kredensial dan mengembalikan token JWT serta objek sesi yang aktif.<br>7. `AuthContext` menyimpan data sesi dan memperbarui status autentikasi pada seluruh aplikasi.<br>8. Sistem mengarahkan pengguna ke halaman tujuan sebelum diminta masuk, atau ke `/dashboard` apabila tidak ada halaman tujuan yang tersimpan. |
| **Post Condition** | Sesi autentikasi aktif tersimpan. Pengguna berada di halaman Dashboard dan dapat mengakses seluruh fitur yang dilindungi (*protected routes*). |

---

## Tabel 4.x — Spesifikasi Use Case Upload Image

| Bagian             | Keterangan |
|--------------------|------------|
| **Aktor**          | Pengguna Terdaftar (Dokter / Tenaga Medis) |
| **Trigger & Tipe** | Pengguna mengakses halaman New Analysis dan mengunggah citra kolonoskopi. Tipe: *User-initiated*, *Asynchronous*. |
| **Pre-Conditions** | 1. Pengguna telah masuk ke sistem (sesi autentikasi aktif).<br>2. Pengguna berada pada halaman New Analysis (`/analysis/new`).<br>3. Pengguna memiliki berkas citra kolonoskopi yang akan diunggah. |
| **Normal Course**  | 1. Pengguna membuka halaman New Analysis melalui menu navigasi atau tombol **New Analysis** di halaman History.<br>2. Sistem menampilkan antarmuka unggah berkas yang mendukung mekanisme seret-dan-lepas (*drag-and-drop*) maupun pemilihan berkas melalui dialog.<br>3. Pengguna memilih atau menyeret berkas citra ke area unggah.<br>4. Sistem melakukan validasi berkas sisi klien: (a) memeriksa ekstensi berkas (hanya `.jpg`, `.jpeg`, `.png`, `.bmp` yang diizinkan), (b) memeriksa tipe MIME berkas, dan (c) memastikan ukuran berkas tidak melebihi 10 MB.<br>5. Apabila validasi lolos, sistem menampilkan pratinjau (*preview*) citra yang dipilih beserta informasi nama dan ukuran berkas.<br>6. Pengguna menekan tombol **Start Analysis** untuk memulai proses.<br>7. Sistem mengirimkan permintaan HTTP `POST` ke *endpoint* `/api/analysis` dengan data berkas citra menggunakan `FormData`.<br>8. Backend menerima permintaan, menyimpan berkas citra ke Supabase Storage, dan membuat rekaman analisis baru pada tabel `analyses` dengan status awal `processing`. Backend mengembalikan respons HTTP `202 Accepted` beserta `analysis_id`.<br>9. Sistem mengarahkan pengguna ke halaman detail analisis (`/analysis/:id`) untuk menunggu hasil segmentasi. |
| **Post Condition** | Berkas citra tersimpan di Supabase Storage. Rekaman analisis baru dibuat pada tabel `analyses` dengan `status = processing` dan antrean tugas segmentasi telah diajukan. |

---

## Tabel 4.x — Spesifikasi Use Case Segmentation

| Bagian             | Keterangan |
|--------------------|------------|
| **Aktor**          | Pengguna Terdaftar (Dokter / Tenaga Medis) |
| **Trigger & Tipe** | Proses segmentasi dipicu secara otomatis setelah citra berhasil diunggah dan rekaman analisis dibuat. Tipe: *System-initiated*, *Asynchronous*. |
| **Pre-Conditions** | 1. Pengguna telah berhasil mengunggah citra kolonoskopi (use case Upload Image telah selesai).<br>2. Rekaman analisis dengan `status = processing` tersedia pada tabel `analyses`.<br>3. Berkas citra tersimpan di Supabase Storage dan dapat diakses oleh layanan AI. |
| **Normal Course**  | 1. *Background worker* (`analysis_service.py`) mengambil tugas dari `JobQueue` dan memuat berkas citra dari Supabase Storage.<br>2. Sistem memvalidasi integritas citra menggunakan pustaka Pillow: memeriksa format berkas, tipe MIME aktual, dan dimensi citra.<br>3. Sistem menjalankan model U-Net untuk menghasilkan segmentasi biner (*binary mask*) yang membedakan area polip dari jaringan sekitarnya.<br>4. Sistem menjalankan model ResNet50 secara bersamaan untuk mengklasifikasikan citra dan menghasilkan peta Grad-CAM (*Gradient-weighted Class Activation Mapping*) yang menunjukkan area perhatian model.<br>5. Sistem menghasilkan empat artefak hasil: (a) `binary_mask.png` — hasil segmentasi biner, (b) `segmentation_overlay.png` — citra asli yang ditumpangkan dengan segmentasi, (c) `gradcam_heatmap.png` — peta panas Grad-CAM murni, dan (d) `gradcam_overlay.png` — citra asli yang ditumpangkan dengan Grad-CAM.<br>6. Keempat artefak disimpan ke Supabase Storage dan URL aksesnya diperbarui pada rekaman analisis di tabel `analyses`.<br>7. Sistem memperbarui `status` rekaman analisis dari `processing` menjadi `completed` pada tabel `analyses`.<br>8. *Frontend* pada halaman detail analisis (`/analysis/:id`) mendeteksi perubahan status melalui mekanisme *polling* dan secara otomatis memuat ulang hasil.<br>9. Sistem menampilkan keempat artefak hasil beserta statistik analisis kepada pengguna. |
| **Post Condition** | Keempat artefak hasil segmentasi dan Grad-CAM tersimpan di Supabase Storage. Rekaman analisis diperbarui dengan `status = completed`. Hasil analisis ditampilkan secara penuh kepada pengguna di halaman detail analisis. |

---

## Tabel 4.x — Spesifikasi Use Case View History

| Bagian             | Keterangan |
|--------------------|------------|
| **Aktor**          | Pengguna Terdaftar (Dokter / Tenaga Medis) |
| **Trigger & Tipe** | Pengguna mengakses halaman Analysis History. Tipe: *User-initiated*, *Synchronous*. |
| **Pre-Conditions** | 1. Pengguna telah masuk ke sistem (sesi autentikasi aktif).<br>2. Sistem dapat terhubung ke layanan backend untuk mengambil data riwayat. |
| **Normal Course**  | 1. Pengguna mengakses halaman Analysis History (`/history`) melalui menu navigasi atau tautan di Dashboard.<br>2. Sistem memanggil fungsi `listHistory()` dari `analysis.ts` untuk mengambil seluruh rekaman analisis milik pengguna yang sedang aktif, difilter berdasarkan `user_id`.<br>3. Sistem menampilkan indikator *loading* selama proses pengambilan data berlangsung.<br>4. Apabila tidak ada rekaman yang ditemukan, sistem menampilkan tampilan *empty state* yang menginformasikan bahwa belum ada riwayat analisis.<br>5. Apabila rekaman tersedia, sistem menampilkan daftar riwayat dalam format tabel berisi: nama berkas asli (*original filename*), tanggal analisis, dan lencana status (`COMPLETED`, `PROCESSING`, atau `FAILED`).<br>6. Sistem menampilkan 4 rekaman per halaman (paginasi). Informasi jumlah total rekaman dan rentang halaman aktif ditampilkan di atas tabel.<br>7. Pengguna dapat mempersempit daftar menggunakan fitur pencarian dan filter: (a) kolom pencarian teks untuk mencocokkan nama berkas, (b) filter *dropdown* berdasarkan status analisis, dan (c) filter tanggal menggunakan *date picker*. Seluruh filter berjalan pada sisi klien menggunakan `useMemo`.<br>8. Pengguna dapat menekan tombol ikon mata (👁) atau tautan **View** untuk mengakses halaman detail hasil analisis tertentu (`/analysis/:id`).<br>9. Pengguna dapat menghapus rekaman riwayat dengan menekan ikon hapus, mengonfirmasi melalui modal konfirmasi, dan sistem memanggil `deleteAnalysis()` untuk menghapus rekaman beserta artefaknya. |
| **Post Condition** | Daftar riwayat analisis berhasil ditampilkan. Pengguna dapat menelusuri, memfilter, melihat detail, atau menghapus rekaman riwayat sesuai kebutuhan. |

---

## Tabel 4.x — Spesifikasi Use Case View Doctor Profile

| Bagian             | Keterangan |
|--------------------|------------|
| **Aktor**          | Pengguna Terdaftar (Dokter / Tenaga Medis) |
| **Trigger & Tipe** | Pengguna mengakses halaman Doctor Profile. Tipe: *User-initiated*, *Synchronous*. |
| **Pre-Conditions** | 1. Pengguna telah masuk ke sistem (sesi autentikasi aktif).<br>2. Sistem dapat terhubung ke layanan backend untuk mengambil data profil. |
| **Normal Course**  | 1. Pengguna mengakses halaman Doctor Profile (`/profile`) melalui menu navigasi atau avatar profil.<br>2. Sistem memanggil fungsi `fetchDoctorProfile()` dari `profile.ts` untuk mengambil data profil dari tabel `doctor_profiles` berdasarkan `user_id` pengguna aktif.<br>3. Secara bersamaan, sistem memanggil `listHistory()` untuk menghitung statistik aktivitas: total analisis yang telah dilakukan dan jumlah analisis dengan status `completed`.<br>4. Sistem menampilkan indikator *loading* selama proses pengambilan data berlangsung.<br>5. Sistem menampilkan halaman profil yang memuat: (a) bagian **Profil Pribadi** berisi nama lengkap, spesialisasi, nomor lisensi, dan nomor telepon; (b) bagian **Ringkasan Aktivitas** berisi total analisis dan jumlah analisis berhasil; serta (c) informasi akun yaitu alamat email yang digunakan.<br>6. Pengguna dapat secara opsional menekan tombol **Edit Profile** untuk membuka modal *Edit Doctor Profile*.<br>7. Pada modal *Edit Doctor Profile*, sistem menampilkan formulir yang telah terisi dengan data profil aktif. Pengguna dapat mengubah: nama lengkap, spesialisasi, nomor lisensi medis, dan nomor telepon.<br>8. Pengguna menyimpan perubahan dengan menekan tombol **Save Changes**.<br>9. Sistem menjalankan `validateProfileData()` untuk memvalidasi data yang dimasukkan (nama tidak boleh kosong, nomor telepon jika diisi harus berformat valid).<br>10. Apabila validasi lolos, sistem memanggil `saveDoctorProfile()` yang melakukan operasi *upsert* pada tabel `doctor_profiles` dan memperbarui nama tampilan pada `supabase.auth.updateUser()`.<br>11. Sistem menutup modal dan menampilkan notifikasi keberhasilan. Data profil pada halaman diperbarui secara langsung. |
| **Post Condition** | Data profil berhasil ditampilkan. Apabila pengguna melakukan pengeditan dan menyimpan, rekaman pada tabel `doctor_profiles` diperbarui dan nama tampilan pada akun Supabase Auth ikut diperbarui. |

---

## Tabel 4.x — Spesifikasi Use Case Sign Out

| Bagian             | Keterangan |
|--------------------|------------|
| **Aktor**          | Pengguna Terdaftar (Dokter / Tenaga Medis) |
| **Trigger & Tipe** | Pengguna memilih opsi keluar melalui menu navigasi. Tipe: *User-initiated*, *Synchronous*. |
| **Pre-Conditions** | 1. Pengguna sedang berada dalam sesi autentikasi yang aktif.<br>2. Menu navigasi tersedia dan dapat diakses oleh pengguna. |
| **Normal Course**  | 1. Pengguna membuka menu navigasi dan menekan opsi **Sign Out**.<br>2. Sistem menutup menu navigasi (*dropdown* ditutup) dan menampilkan modal konfirmasi keluar yang berisi pertanyaan kepada pengguna apakah benar-benar ingin mengakhiri sesi.<br>3. Pengguna menekan tombol **Confirm** atau **Yes, Sign Out** pada modal konfirmasi.<br>4. Sistem memanggil fungsi `signOut()` dari `AuthContext.tsx` yang meneruskan permintaan ke `supabase.auth.signOut()`.<br>5. Supabase Auth mengakhiri sesi aktif dan menghapus token JWT dari penyimpanan lokal (*localStorage* dan *sessionStorage*).<br>6. `AuthContext` memperbarui status autentikasi menjadi tidak aktif, sehingga seluruh *protected route* tidak lagi dapat diakses.<br>7. Sistem mengarahkan pengguna ke halaman Sign In (`/login`) secara otomatis. |
| **Post Condition** | Sesi autentikasi pengguna diakhiri sepenuhnya. Token JWT dihapus. Pengguna berada di halaman Sign In. Seluruh *protected route* tidak dapat diakses tanpa proses Sign In ulang. |

---

*Catatan: Nomor tabel (`Tabel 4.x`) merupakan placeholder yang perlu disesuaikan dengan penomoran akhir pada skripsi. Seluruh alur yang tertulis di atas didasarkan pada analisis langsung terhadap kode sumber aktual web PIXEL-T.*

