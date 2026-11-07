# PENJELASAN USE CASE DIAGRAM SISTEM PIXEL-T (BAB IV)

Dokumen ini berisi naskah penjelasan akademik untuk **Bab IV Skripsi S1**, disusun dalam bahasa Indonesia formal dan selaras dengan implementasi kode sumber serta diagram Use Case sistem PIXEL-T.

> **Petunjuk bagi Penulis:** Nomor subbab `4.x` dan nomor gambar `Gambar 4.x` merupakan *placeholder* yang disesuaikan dengan penomoran akhir skripsi.

---

## 4.x Use Case Diagram

*Use Case Diagram* merupakan salah satu diagram *Unified Modeling Language* (UML) yang digunakan untuk memodelkan interaksi antara aktor dengan sistem pada tingkat perilaku fungsional. Diagram ini tidak menjelaskan urutan eksekusi maupun rincian teknis, melainkan menegaskan **siapa** yang berinteraksi dengan sistem dan **apa** layanan yang disediakan sistem bagi aktor tersebut.

Pada penelitian ini, *Use Case Diagram* disusun berdasarkan implementasi aktual aplikasi web PIXEL-T, bukan berdasarkan asumsi perancangan. Setiap aktor, *use case*, asosiasi, dan relasi *stereotype* ditelusuri langsung ke berkas kode sumber, sehingga diagram yang dihasilkan dapat dipertanggungjawabkan secara akademik dan konsisten dengan perangkat lunak yang dibangun.

Rancangan *Use Case Diagram* sistem PIXEL-T disajikan pada Gambar 4.x berikut:

```
[Sisipkan Gambar: references/bab 4/Use Case Diagram PIXELT.png]
Gambar 4.x Use Case Diagram Sistem PIXEL-T
```

Berdasarkan Gambar 4.x, sistem PIXEL-T memuat tiga aktor dan empat belas *use case* di dalam satu batas sistem berlabel **Sistem PIXEL-T**.

---

## 4.x.1 Aktor

Aktor merepresentasikan entitas eksternal yang berinteraksi dengan sistem. PIXEL-T memiliki tiga aktor yang dibedakan berdasarkan status autentikasi dan hak aksesnya.

### Calon Pengguna

**Calon Pengguna** adalah individu yang belum memiliki sesi autentikasi aktif. Aktor ini merepresentasikan dokter yang bermaksud mendaftar ke sistem. Calon Pengguna hanya dapat menjalankan **Sign Up** dan **Sign In**. Pendaftaran melalui halaman `/register` bersifat khusus dokter; tidak terdapat jalur pendaftaran publik untuk peran admin.

### Dokter / Tenaga Medis

**Dokter / Tenaga Medis** adalah tenaga medis yang telah memiliki akun pada tabel `public.doctor_profiles` dengan `role = 'doctor'`. Dokter hanya memperoleh akses penuh setelah `account_status` berubah dari `pending` menjadi `approved` oleh admin. Dokter yang masih berstatus `pending` atau `rejected` dapat melakukan **Sign In** dan **Sign Out**, tetapi tidak dapat menjalankan fitur klinis. Dokter yang telah disetujui dapat menjalankan **Upload Image**, **Segmentation**, **View History**, **Search / Filter History**, **View Doctor Profile**, dan **Edit Doctor Profile**, serta **Sign In** dan **Sign Out**.

### Admin

**Admin** adalah pengelola sistem yang tidak memiliki fitur klinis. Peran admin direpresentasikan secara eksklusif melalui `auth.users.app_metadata.role = 'admin'`, yang hanya dapat ditulis melalui Supabase Admin API menggunakan *service-role key*. Admin tidak memiliki tabel tersendiri dan tidak memiliki baris pada `doctor_profiles`; trigger basis data secara eksplisit mengecualikan akun admin dari pembuatan profil dokter. Admin menjalankan **View Admin Dashboard**, **View Doctor Registrations**, **Approve Doctor Account**, dan **Reject Doctor Account**, serta **Sign In** dan **Sign Out**.

Tabel berikut meringkasan aktor dan hak akses utamanya:

**Tabel 4.x — Ringkasan Aktor**

| Aktor | Representasi pada Sistem | Hak Akses Utama |
|-------|--------------------------|-----------------|
| Calon Pengguna | Tanpa sesi autentikasi | Sign Up, Sign In |
| Dokter / Tenaga Medis | `doctor_profiles.role = 'doctor'`, `account_status = 'approved'` | Fitur klinis + profil |
| Admin | `auth.users.app_metadata.role = 'admin'` | Manajemen pendaftaran dokter |

---

## 4.x.2 Use Case dan Deskripsi

Berikut diuraikan empat belas *use case* beserta aktor utama dan ringkasan perilakunya.

### 4.x.2.1 Sign Up

**Aktor:** Calon Pengguna.

**Deskripsi:** Calon pengguna membuka halaman `/register`, mengisi formulir pendaftaran, dan mengirimkannya. Sistem memvalidasi format surel dan panjang kata sandi pada sisi klien, kemudian memanggil layanan autentikasi Supabase. Apabila pendaftaran berhasil, trigger basis data membuat baris `doctor_profiles` dengan `role = 'doctor'` dan `account_status = 'pending'`. Akun belum dapat mengakses fitur klinis sampai disetujui admin.

**Tabel 4.x — Deskripsi Use Case Sign Up**

| Bagian | Keterangan |
|--------|------------|
| Actor | Calon Pengguna |
| Trigger & Type | Pengguna mengakses halaman `/register` dan mengirimkan formulir pendaftaran. Tipe: *User-initiated*, *Synchronous*. |
| Pre-Conditions | 1. Pengguna belum memiliki akun PIXEL-T.<br>2. Pengguna belum berada dalam sesi autentikasi yang aktif. |
| Normal Course | 1. Pengguna membuka halaman pendaftaran (`/register`).<br>2. Sistem menampilkan formulir pendaftaran yang memuat nama lengkap, alamat surel, kata sandi, nama rumah sakit, dan spesialisasi.<br>3. Pengguna mengisi seluruh kolom dan menekan tombol pendaftaran.<br>4. Sistem melakukan validasi sisi klien untuk memastikan seluruh kolom terisi, format surel sesuai pola yang ditentukan, dan kata sandi memenuhi syarat panjang minimal.<br>5. Apabila validasi lolos, sistem memanggil fungsi `signUp` pada *AuthContext* yang meneruskan permintaan ke `supabase.auth.signUp()` dengan metadata pengguna.<br>6. Supabase Auth membuat rekaman akun baru pada skema `auth.users` dan mengirimkan email verifikasi ke alamat yang didaftarkan.<br>7. Sistem menampilkan notifikasi keberhasilan pendaftaran.<br>8. Pengguna diarahkan ke halaman Sign In (`/login`) untuk masuk menggunakan akun yang baru dibuat. |
| Post Condition | Rekaman akun baru berhasil dibuat pada `auth.users` Supabase. Baris `doctor_profiles` dibuat dengan `account_status = 'pending'`. Pengguna berada di halaman Sign In dan dapat segera masuk ke sistem. |

Tabel 4.x menjelaskan tahapan proses yang dilakukan oleh pengguna dalam pendaftaran akun baru pada sistem PIXEL-T. Setelah pendaftaran berhasil, akun harus menunggu persetujuan admin sebelum dapat mengakses fitur klinis.

---

### 4.x.2.2 Sign In

**Aktor:** Calon Pengguna, Dokter, Admin.

**Deskripsi:** Pengguna memasukkan surel dan kata sandi pada halaman `/login`. Sistem memverifikasi kredensial melalui Supabase Auth, kemudian menentukan peran pengguna. Penentuan peran mendahulukan `app_metadata.role` untuk admin, lalu membaca `doctor_profiles.role` dan `account_status` untuk dokter. Setelah peran diketahui, sistem mengalihkan pengguna ke beranda yang sesuai: `/admin` untuk admin dan `/dashboard` untuk dokter yang telah disetujui.

**Tabel 4.x — Deskripsi Use Case Sign In**

| Bagian | Keterangan |
|--------|------------|
| Actor | Calon Pengguna, Dokter, Admin |
| Trigger & Type | Pengguna mengakses halaman `/login` dan memasukkan kredensial. Tipe: *User-initiated*, *Synchronous*. |
| Pre-Conditions | 1. Pengguna telah memiliki akun PIXEL-T yang terdaftar.<br>2. Pengguna belum berada dalam sesi autentikasi yang aktif. |
| Normal Course | 1. Pengguna membuka halaman Sign In (`/login`). Sistem menampilkan formulir yang memuat kolom *Email Address* dan *Password*.<br>2. Pengguna mengisi alamat email dan kata sandi, kemudian menekan tombol Sign In.<br>3. Sistem melakukan validasi sisi klien untuk memastikan kolom tidak kosong.<br>4. Sistem memanggil fungsi `signIn` pada *AuthContext* yang meneruskan permintaan ke `supabase.auth.signInWithPassword()`.<br>5. Supabase Auth memverifikasi kredensial dan mengembalikan token JWT serta objek sesi yang aktif.<br>6. *AuthContext* menyimpan data sesi dan memperbarui status autentikasi pada seluruh aplikasi.<br>7. Sistem mengarahkan pengguna ke halaman tujuan sebelum diminta masuk, atau ke `/dashboard` apabila tidak ada halaman tujuan yang tersimpan. |
| Post Condition | Sesi autentikasi aktif tersimpan. Pengguna berada di halaman Dashboard (dokter) atau halaman Admin (admin) dan dapat mengakses seluruh fitur yang dilindungi (*protected routes*). |

Tabel 4.x menjelaskan tahapan proses yang dilakukan pengguna dalam masuk ke sistem PIXEL-T. Penentuan peran mengikuti prioritas peran admin terlebih dahulu, lalu diikuti oleh status dokter pada basis data.

---

### 4.x.2.3 Sign Out

**Aktor:** Dokter, Admin.

**Deskripsi:** Pengguna terautentikasi memilih tombol keluar pada bilah navigasi. Sistem menampilkan modal konfirmasi, menghapus sesi melalui Supabase Auth, dan mengalihkan pengguna ke halaman `/login`.

**Tabel 4.x — Deskripsi Use Case Sign Out**

| Bagian | Keterangan |
|--------|------------|
| Actor | Dokter, Admin |
| Trigger & Type | Pengguna memilih opsi keluar melalui menu navigasi. Tipe: *User-initiated*, *Synchronous*. |
| Pre-Conditions | 1. Pengguna sedang berada dalam sesi autentikasi yang aktif.<br>2. Menu navigasi tersedia dan dapat diakses oleh pengguna. |
| Normal Course | 1. Pengguna membuka menu navigasi dan menekan opsi Sign Out.<br>2. Sistem menutup menu navigasi dan menampilkan modal konfirmasi keluar yang berisi pertanyaan kepada pengguna apakah benar-benar ingin mengakhiri sesi.<br>3. Pengguna menekan tombol konfirmasi pada modal.<br>4. Sistem memanggil fungsi `signOut` dari *AuthContext* yang meneruskan permintaan ke `supabase.auth.signOut()`.<br>5. Supabase Auth mengakhiri sesi aktif dan menghapus token JWT dari penyimpanan klien.<br>6. *AuthContext* memperbarui status autentikasi menjadi tidak aktif, sehingga seluruh *protected route* tidak lagi dapat diakses.<br>7. Sistem mengarahkan pengguna ke halaman Sign In (`/login`) secara otomatis. |
| Post Condition | Sesi autentikasi pengguna diakhiri sepenuhnya. Token JWT dihapus. Pengguna berada di halaman Sign In. Seluruh *protected route* tidak dapat diakses tanpa proses Sign In ulang. |

Tabel 4.x menjelaskan tahapan proses yang dilakukan pengguna dalam mengakhiri sesi autentikasi pada sistem PIXEL-T.

---

### 4.x.2.4 Reset Password

**Aktor:** Pengguna yang memiliki akun (melalui Sign In).

**Deskripsi:** Reset kata sandi berlangsung dalam dua tahap. Tahap pertama, pengguna memilih mode lupa kata sandi pada halaman `/login`; sistem mengirim tautan pemulihan ke surel terdaftar. Tahap kedua, pengguna membuka tautan tersebut dan mengakses halaman `/reset-password` untuk menetapkan kata sandi baru. *Use case* ini bersifat opsional dan dimodelkan sebagai `<<extend>>` terhadap **Sign In**.

**Tabel 4.x — Deskripsi Use Case Reset Password**

| Bagian | Keterangan |
|--------|------------|
| Actor | Pengguna yang memiliki akun |
| Trigger & Type | Pengguna memilih mode lupa kata sandi pada halaman Sign In. Tipe: *User-initiated*, *Synchronous*. |
| Pre-Conditions | Pengguna memiliki akun terdaftar dan mengakses opsi reset kata sandi. |
| Normal Course | 1. Pengguna memilih mode reset kata sandi pada halaman `/login`.<br>2. Sistem memanggil fungsi `resetPasswordUser` yang menjalankan `supabase.auth.resetPasswordForEmail()`.<br>3. Supabase mengirimkan tautan pemulihan ke alamat surel terdaftar.<br>4. Pengguna membuka tautan tersebut dan mengakses halaman `/reset-password`.<br>5. Sistem memungkinkan pengguna menetapkan kata sandi baru melalui `supabase.auth.updateUser({ password })`. |
| Post Condition | Kata sandi pengguna berhasil diperbarui dan pengguna dapat masuk kembali dengan kata sandi baru. |

Tabel 4.x menjelaskan tahapan proses yang dilakukan pengguna dalam mengatur ulang kata sandi pada sistem PIXEL-T.

---

### 4.x.2.5 Upload Image

**Aktor:** Dokter.

**Deskripsi:** Dokter memilih berkas citra endoskopi pada halaman `/analysis/new`. Sistem memvalidasi ekstensi, tipe MIME, dan ukuran berkas (maksimum 10 MB) pada sisi klien, menampilkan pratinjau, lalu mengirim berkas ke endpoint `POST /api/analysis`. Endpoint tersebut dilindungi dekorator `require_approved_doctor`, sehingga hanya dokter dengan status `approved` yang dapat mengunggah. Sistem mengembalikan HTTP 202 dan pengguna dialihkan ke halaman hasil.

**Tabel 4.x — Deskripsi Use Case Upload Image**

| Bagian | Keterangan |
|--------|------------|
| Actor | Dokter |
| Trigger & Type | Pengguna mengakses halaman New Analysis dan mengunggah citra endoskopi. Tipe: *User-initiated*, *Asynchronous*. |
| Pre-Conditions | 1. Pengguna telah masuk ke sistem (sesi autentikasi aktif).<br>2. Pengguna berada pada halaman New Analysis (`/analysis/new`).<br>3. Pengguna memiliki berkas citra endoskopi yang akan diunggah.<br>4. Akun pengguna berstatus `approved`. |
| Normal Course | 1. Pengguna membuka halaman New Analysis melalui menu navigasi atau tombol New Analysis di halaman History.<br>2. Sistem menampilkan antarmuka unggah berkas yang mendukung mekanisme seret-dan-lepas maupun pemilihan berkas melalui dialog.<br>3. Pengguna memilih atau menyeret berkas citra ke area unggah.<br>4. Sistem melakukan validasi berkas sisi klien: memeriksa ekstensi berkas (hanya `.jpg`, `.jpeg`, `.png`, `.bmp` yang diizinkan), memeriksa tipe MIME berkas, dan memastikan ukuran berkas tidak melebihi 10 MB.<br>5. Apabila validasi lolos, sistem menampilkan pratinjau citra yang dipilih beserta informasi nama dan ukuran berkas.<br>6. Pengguna menekan tombol Start Analysis untuk memulai proses.<br>7. Sistem mengirimkan permintaan HTTP `POST` ke endpoint `/api/analysis` dengan data berkas citra menggunakan `FormData`.<br>8. Backend menerima permintaan, menyimpan berkas citra ke Supabase Storage, dan membuat rekaman analisis baru pada tabel `analyses` dengan status awal `processing`. Backend mengembalikan respons HTTP 202 *Accepted* beserta `analysis_id`.<br>9. Sistem mengarahkan pengguna ke halaman detail analisis (`/analysis/:id`) untuk menunggu hasil segmentasi. |
| Post Condition | Berkas citra tersimpan di Supabase Storage. Rekaman analisis baru dibuat pada tabel `analyses` dengan `status = processing` dan antrean tugas segmentasi telah diajukan. |

Tabel 4.x menjelaskan tahapan proses yang dilakukan dokter dalam mengunggah citra endoskopi ke sistem PIXEL-T. Citra disimpan di Supabase Storage dan proses segmentasi diajukan ke antrean tugas.

---

### 4.x.2.6 Segmentation

**Aktor:** Dokter.

**Deskripsi:** Setelah citra diterima, sistem menjalankan pipeline inferensi yang terdiri atas praproses, inferensi U-Net untuk segmentasi polip, pascaproses, pembangkitan Grad-CAM, dan komposisi artefak. Halaman hasil melakukan *polling* `GET /api/analysis/<id>` sampai status analisis berubah menjadi `completed` atau `failed`. *Use case* ini mencakup **Upload Image** sebagai perilaku wajib melalui relasi `<<include>>`.

**Tabel 4.x — Deskripsi Use Case Segmentation**

| Bagian | Keterangan |
|--------|------------|
| Actor | Dokter |
| Trigger & Type | Proses segmentasi dipicu secara otomatis setelah citra berhasil diunggah dan rekaman analisis dibuat. Tipe: *System-initiated*, *Asynchronous*. |
| Pre-Conditions | 1. Pengguna telah berhasil mengunggah citra endoskopi (use case Upload Image telah selesai).<br>2. Rekaman analisis dengan `status = processing` tersedia pada tabel `analyses`.<br>3. Berkas citra tersimpan di Supabase Storage dan dapat diakses oleh layanan AI. |
| Normal Course | 1. *Background worker* mengambil tugas dari antrean pekerjaan (*JobQueue*) dan memuat berkas citra dari Supabase Storage.<br>2. Sistem memvalidasi integritas citra menggunakan pustaka Pillow: memeriksa format berkas, tipe MIME aktual, dan dimensi citra.<br>3. Sistem menjalankan model U-Net untuk menghasilkan segmentasi biner (*binary mask*) yang membedakan area polip dari jaringan sekitarnya.<br>4. Sistem menjalankan model ResNet50 secara bersamaan untuk mengklasifikasikan citra dan menghasilkan peta Grad-CAM (*Gradient-weighted Class Activation Mapping*) yang menunjukkan area perhatian model.<br>5. Sistem menghasilkan empat artefak hasil: masker biner, citra *overlay* segmentasi, peta panas Grad-CAM, dan citra *overlay* Grad-CAM.<br>6. Keempat artefak disimpan ke Supabase Storage dan URL aksesnya diperbarui pada rekaman analisis di tabel `analyses`.<br>7. Sistem memperbarui `status` rekaman analisis dari `processing` menjadi `completed` pada tabel `analyses`.<br>8. *Frontend* pada halaman detail analisis (`/analysis/:id`) mendeteksi perubahan status melalui mekanisme *polling* dan secara otomatis memuat ulang hasil.<br>9. Sistem menampilkan keempat artefak hasil beserta statistik analisis kepada pengguna. |
| Alternative Course | Apabila terjadi kegagalan komputasi, sistem memperbarui status rekaman analisis menjadi `failed` dan menampilkan pesan kegagalan kepada pengguna. |
| Post Condition | Keempat artefak hasil segmentasi dan Grad-CAM tersimpan di Supabase Storage. Rekaman analisis diperbarui dengan `status = completed`. Hasil analisis ditampilkan secara penuh kepada pengguna di halaman detail analisis. |

Tabel 4.x menjelaskan tahapan proses yang dilakukan sistem dalam segmentasi citra endoskopi menggunakan model U-Net dan ResNet50. Segmentation mencakup Upload Image sebagai perilaku wajib melalui relasi `<<include>>`.

---

### 4.x.2.7 View History

**Aktor:** Dokter.

**Deskripsi:** Dokter membuka halaman `/history` untuk melihat daftar analisis yang pernah dilakukan. Sistem mengambil data melalui `GET /api/history` yang dilindungi `require_approved_doctor` dan hanya mengembalikan rekaman milik pengguna yang bersangkutan. Setiap baris menampilkan nama berkas, tanggal, status, dan tautan menuju detail.

**Tabel 4.x — Deskripsi Use Case View History**

| Bagian | Keterangan |
|--------|------------|
| Actor | Dokter |
| Trigger & Type | Pengguna mengakses halaman Analysis History. Tipe: *User-initiated*, *Synchronous*. |
| Pre-Conditions | 1. Pengguna telah masuk ke sistem (sesi autentikasi aktif).<br>2. Sistem dapat terhubung ke layanan backend untuk mengambil data riwayat. |
| Normal Course | 1. Pengguna mengakses halaman Analysis History (`/history`) melalui menu navigasi atau tautan di Dashboard.<br>2. Sistem memanggil fungsi `listHistory()` dari layanan analisis untuk mengambil seluruh rekaman analisis milik pengguna yang sedang aktif, difilter berdasarkan `user_id`.<br>3. Sistem menampilkan indikator *loading* selama proses pengambilan data berlangsung.<br>4. Apabila tidak ada rekaman yang ditemukan, sistem menampilkan tampilan *empty state* yang menginformasikan bahwa belum ada riwayat analisis.<br>5. Apabila rekaman tersedia, sistem menampilkan daftar riwayat dalam format tabel berisi nama berkas asli, tanggal analisis, dan lencana status (`COMPLETED`, `PROCESSING`, atau `FAILED`).<br>6. Sistem menampilkan 4 rekaman per halaman (paginasi). Informasi jumlah total rekaman dan rentang halaman aktif ditampilkan di atas tabel.<br>7. Pengguna dapat menekan ikon mata atau tautan View untuk mengakses halaman detail hasil analisis tertentu (`/analysis/:id`).<br>8. Pengguna dapat menghapus rekaman riwayat dengan menekan ikon hapus, mengonfirmasi melalui modal konfirmasi, dan sistem memanggil fungsi penghapusan untuk menghapus rekaman beserta artefaknya. |
| Post Condition | Daftar riwayat analisis berhasil ditampilkan. Pengguna dapat menelusuri, melihat detail, atau menghapus rekaman riwayat sesuai kebutuhan. |

Tabel 4.x menjelaskan tahapan proses yang dilakukan pengguna dalam meninjau riwayat analisis yang telah dilakukan pada sistem PIXEL-T.

---

### 4.x.2.8 Search / Filter History

**Aktor:** Dokter.

**Deskripsi:** Pada halaman riwayat, dokter dapat mempersempit daftar menggunakan pencarian teks nama berkas, filter status (`processing`, `completed`, `failed`), dan filter tanggal. Penyaringan dilakukan pada sisi klien menggunakan `useMemo`, sehingga tidak memerlukan permintaan tambahan ke server. *Use case* ini bersifat opsional dan dimodelkan sebagai `<<extend>>` terhadap **View History**.

**Tabel 4.x — Deskripsi Use Case Search / Filter History**

| Bagian | Keterangan |
|--------|------------|
| Actor | Dokter |
| Trigger & Type | Pengguna memasukkan kriteria pencarian atau filter pada halaman riwayat. Tipe: *User-initiated*, *Synchronous*. |
| Pre-Conditions | Pengguna berada pada halaman View History dan memiliki daftar riwayat analisis yang tersedia. |
| Normal Course | 1. Pengguna mengisi kolom pencarian teks untuk mencocokkan nama berkas.<br>2. Pengguna memilih filter status melalui *dropdown*.<br>3. Pengguna memilih filter tanggal menggunakan *date picker*.<br>4. Sistem melakukan penyaringan pada sisi klien menggunakan `useMemo` tanpa mengirim permintaan tambahan ke server.<br>5. Sistem menampilkan daftar riwayat yang telah difilter sesuai kriteria yang diisi. |
| Post Condition | Daftar riwayat analisis ditampilkan sesuai kriteria pencarian dan filter yang ditetapkan pengguna. |

Tabel 4.x menjelaskan tahapan proses yang dilakukan pengguna dalam mempersempit daftar riwayat analisis menggunakan pencarian dan filter pada sistem PIXEL-T.

---

### 4.x.2.9 View Doctor Profile

**Aktor:** Dokter.

**Deskripsi:** Dokter membuka halaman `/profile` untuk melihat data profil profesional dan statistik aktivitas. Halaman dilindungi `DoctorRoute`, sehingga admin dialihkan ke `/admin` dan dokter yang belum disetujui ditolak.

**Tabel 4.x — Deskripsi Use Case View Doctor Profile**

| Bagian | Keterangan |
|--------|------------|
| Actor | Dokter |
| Trigger & Type | Pengguna mengakses halaman Doctor Profile. Tipe: *User-initiated*, *Synchronous*. |
| Pre-Conditions | 1. Pengguna telah masuk ke sistem (sesi autentikasi aktif).<br>2. Sistem dapat terhubung ke layanan backend untuk mengambil data profil. |
| Normal Course | 1. Pengguna mengakses halaman Doctor Profile (`/profile`) melalui menu navigasi atau avatar profil.<br>2. Sistem memanggil fungsi `fetchDoctorProfile()` dari layanan profil untuk mengambil data profil dari tabel `doctor_profiles` berdasarkan `user_id` pengguna aktif.<br>3. Secara bersamaan, sistem memanggil fungsi daftar analisis untuk menghitung statistik aktivitas: total analisis yang telah dilakukan dan jumlah analisis dengan status `completed`.<br>4. Sistem menampilkan indikator *loading* selama proses pengambilan data berlangsung.<br>5. Sistem menampilkan halaman profil yang memuat bagian profil pribadi berisi nama lengkap, spesialisasi, nomor lisensi, dan nomor telepon; bagian ringkasan aktivitas berisi total analisis dan jumlah analisis berhasil; serta informasi akun yaitu alamat email yang digunakan. |
| Post Condition | Data profil berhasil ditampilkan. Pengguna dapat melihat informasi profil profesional dan statistik aktivitas di halaman profil. |

Tabel 4.x menjelaskan tahapan proses yang dilakukan pengguna dalam melihat data profil profesional dan statistik aktivitas pada sistem PIXEL-T.

---

### 4.x.2.10 Edit Doctor Profile

**Aktor:** Dokter.

**Deskripsi:** Dokter membuka modal edit untuk memperbarui data profil, mengunggah avatar, atau menghapus avatar. Perubahan disimpan melalui operasi *upsert* ke tabel `doctor_profiles` dan pembaruan metadata pengguna. *Use case* ini bersifat opsional dan dimodelkan sebagai `<<extend>>` terhadap **View Doctor Profile**.

**Tabel 4.x — Deskripsi Use Case Edit Doctor Profile**

| Bagian | Keterangan |
|--------|------------|
| Actor | Dokter |
| Trigger & Type | Pengguna membuka halaman Doctor Profile dan menekan tombol Edit Profile. Tipe: *User-initiated*, *Synchronous*. |
| Pre-Conditions | Pengguna telah masuk ke sistem dan memiliki data profil pada tabel `doctor_profiles`. |
| Normal Course | 1. Pengguna membuka modal edit profil.<br>2. Sistem menampilkan formulir yang telah terisi dengan data profil aktif.<br>3. Pengguna dapat mengubah nama lengkap, spesialisasi, nomor lisensi medis, dan nomor telepon.<br>4. Pengguna menyimpan perubahan dengan menekan tombol Save Changes.<br>5. Sistem melakukan validasi data yang dimasukkan (nama tidak boleh kosong, nomor telepon jika diisi harus berformat valid).<br>6. Apabila validasi lolos, sistem melakukan operasi *upsert* ke tabel `doctor_profiles` dan memperbarui nama tampilan pada akun Supabase Auth.<br>7. Sistem menutup modal dan menampilkan notifikasi keberhasilan. Data profil pada halaman diperbarui secara langsung. |
| Post Condition | Rekaman pada tabel `doctor_profiles` diperbarui dan nama tampilan pada akun Supabase Auth ikut diperbarui. |

Tabel 4.x menjelaskan tahapan proses yang dilakukan pengguna dalam memperbarui data profil profesional pada sistem PIXEL-T.

---

### 4.x.2.11 View Admin Dashboard

**Aktor:** Admin.

**Deskripsi:** Admin membuka halaman `/admin` yang dilindungi `AdminRoute` dan dekorator `require_admin`. Sistem menampilkan agregat statistik pendaftaran dokter: total, `pending`, `approved`, dan `rejected`, yang diambil dari endpoint `GET /api/admin/doctors/stats`.

**Tabel 4.x — Deskripsi Use Case View Admin Dashboard**

| Bagian | Keterangan |
|--------|------------|
| Actor | Admin |
| Trigger & Type | Admin mengakses halaman `/admin`. Tipe: *User-initiated*, *Synchronous*. |
| Pre-Conditions | Admin memiliki akun dengan `app_metadata.role = 'admin'` dan sesi autentikasi aktif. |
| Normal Course | 1. Admin membuka halaman `/admin`.<br>2. Sistem memanggil endpoint `GET /api/admin/doctors/stats` yang dilindungi `require_admin`.<br>3. Sistem menampilkan agregat statistik pendaftaran dokter: total, `pending`, `approved`, dan `rejected`. |
| Post Condition | Dasbor statistik pendaftaran dokter berhasil ditampilkan kepada admin. |

Tabel 4.x menjelaskan tahapan proses yang dilakukan admin dalam melihat dasbor statistik pendaftaran dokter pada sistem PIXEL-T.

---

### 4.x.2.12 View Doctor Registrations

**Aktor:** Admin.

**Deskripsi:** Admin melihat daftar pendaftaran dokter beserta status akun. Daftar dapat difilter berdasarkan status melalui parameter `?status=` pada endpoint `GET /api/admin/doctors`. Setiap entri menampilkan nama, surel, rumah sakit, spesialisasi, status, dan tanggal pendaftaran.

**Tabel 4.x — Deskripsi Use Case View Doctor Registrations**

| Bagian | Keterangan |
|--------|------------|
| Actor | Admin |
| Trigger & Type | Admin mengakses daftar pendaftaran dokter pada halaman admin. Tipe: *User-initiated*, *Synchronous*. |
| Pre-Conditions | Admin memiliki akun dengan `app_metadata.role = 'admin'` dan sesi autentikasi aktif. |
| Normal Course | 1. Admin membuka halaman admin.<br>2. Sistem memanggil endpoint `GET /api/admin/doctors` yang dilindungi `require_admin`.<br>3. Sistem menampilkan daftar pendaftaran dokter beserta status akun.<br>4. Daftar dapat difilter berdasarkan status melalui parameter `?status=` pada endpoint.<br>5. Setiap entri menampilkan nama, surel, rumah sakit, spesialisasi, status, dan tanggal pendaftaran. |
| Post Condition | Daftar pendaftaran dokter beserta status akun berhasil ditampilkan kepada admin. |

Tabel 4.x menjelaskan tahapan proses yang dilakukan admin dalam melihat daftar pendaftaran dokter dan status akun pada sistem PIXEL-T.

---

### 4.x.2.13 Approve Doctor Account

**Aktor:** Admin.

**Deskripsi:** Admin menyetujui akun dokter yang berstatus `pending`. Sistem mengirim permintaan ke `POST /api/admin/doctors/<id>/approve`. Layanan backend hanya mengizinkan transisi dari `pending` menjadi `approved`; permintaan terhadap akun yang sudah diproses ditolak. Setelah disetujui, dokter memperoleh akses penuh ke fitur klinis.

**Tabel 4.x — Deskripsi Use Case Approve Doctor Account**

| Bagian | Keterangan |
|--------|------------|
| Actor | Admin |
| Trigger & Type | Admin menyetujui akun dokter yang berstatus pending. Tipe: *User-initiated*, *Synchronous*. |
| Pre-Conditions | Admin memiliki akun dengan `app_metadata.role = 'admin'` dan sesi autentikasi aktif. Terdapat akun dokter dengan status `pending`. |
| Normal Course | 1. Admin memilih akun dokter yang berstatus pending pada daftar pendaftaran.<br>2. Admin menekan tombol setujui.<br>3. Sistem mengirim permintaan ke `POST /api/admin/doctors/<id>/approve`.<br>4. Layanan backend hanya mengizinkan transisi dari status `pending` menjadi `approved`.<br>5. Setelah disetujui, dokter memperoleh akses penuh ke fitur klinis. |
| Alternative Course | Apabila akun bukan berstatus `pending` (misalnya sudah `approved` atau `rejected`), permintaan ditolak oleh layanan backend. |
| Post Condition | Status akun dokter berubah dari `pending` menjadi `approved`. Dokter memperoleh akses penuh ke fitur klinis. |

Tabel 4.x menjelaskan tahapan proses yang dilakukan admin dalam menyetujui akun dokter pada sistem PIXEL-T.

---

### 4.x.2.14 Reject Doctor Account

**Aktor:** Admin.

**Deskripsi:** Admin menolak akun dokter yang berstatus `pending` dengan mencantumkan alasan penolakan. Sistem mengirim permintaan ke `POST /api/admin/doctors/<id>/reject`. Layanan backend hanya mengizinkan transisi dari `pending` menjadi `rejected` dan menyimpan `rejection_reason`. Dokter yang ditolak tidak dapat mengakses fitur klinis.

**Tabel 4.x — Deskripsi Use Case Reject Doctor Account**

| Bagian | Keterangan |
|--------|------------|
| Actor | Admin |
| Trigger & Type | Admin menolak akun dokter yang berstatus pending dengan alasan. Tipe: *User-initiated*, *Synchronous*. |
| Pre-Conditions | Admin memiliki akun dengan `app_metadata.role = 'admin'` dan sesi autentikasi aktif. Terdapat akun dokter dengan status `pending`. |
| Normal Course | 1. Admin memilih akun dokter yang berstatus pending pada daftar pendaftaran.<br>2. Admin menekan tombol tolak dan mengisi alasan penolakan.<br>3. Sistem mengirim permintaan ke `POST /api/admin/doctors/<id>/reject`.<br>4. Layanan backend hanya mengizinkan transisi dari status `pending` menjadi `rejected` dan menyimpan `rejection_reason`.<br>5. Dokter yang ditolak tidak dapat mengakses fitur klinis. |
| Alternative Course | Apabila akun bukan berstatus `pending`, permintaan ditolak oleh layanan backend. |
| Post Condition | Status akun dokter berubah dari `pending` menjadi `rejected`. Dokter tidak dapat mengakses fitur klinis. |

Tabel 4.x menjelaskan tahapan proses yang dilakukan admin dalam menolak akun dokter pada sistem PIXEL-T.

---

## 4.x.3 Relasi `<<include>>` dan `<<extend>>`

Relasi `<<include>>` menyatakan bahwa suatu *use case* **wajib** menjalankan *use case* lain sebagai bagian dari perilakunya. Pada diagram PIXEL-T terdapat satu relasi ini, yaitu **Segmentation** `<<include>>` **Upload Image**. Segmentasi tidak mungkin dijalankan tanpa citra yang telah diunggah dan tersimpan; oleh karena itu, hubungan wajib tersebut tepat dimodelkan sebagai `<<include>>`.

Relasi `<<extend>>` menyatakan bahwa suatu *use case* **opsional** memperluas *use case* lain pada kondisi tertentu. Arah panah mengikuti kaidah UML 2.x, yakni dari *extending use case* menuju *base use case*. Terdapat tiga relasi `<<extend>>`:

1. **Reset Password** `<<extend>>` **Sign In** — reset kata sandi hanya dijalankan bila pengguna memilih opsi lupa kata sandi.
2. **Search / Filter History** `<<extend>>` **View History** — pencarian dan filter hanya aktif bila pengguna mengisi kriteria.
3. **Edit Doctor Profile** `<<extend>>` **View Doctor Profile** — pengeditan hanya terjadi bila pengguna membuka modal edit.

Tidak terdapat relasi generalisasi antara aktor pada diagram PIXEL-T. Admin dan Dokter adalah dua jalur otorisasi yang saling eksklusif; penambahan generalisasi Admin → Dokter akan menyesatkan karena admin tidak mewarisi fitur klinis dan tidak dapat mengakses fitur klinis.

**Tabel 4.x — Relasi Stereotype**

| Relasi | Jenis | Arah | Sifat |
|--------|-------|------|-------|
| Segmentation → Upload Image | `<<include>>` | Base → Included | Wajib |
| Reset Password → Sign In | `<<extend>>` | Extending → Base | Opsional |
| Search / Filter History → View History | `<<extend>>` | Extending → Base | Opsional |
| Edit Doctor Profile → View Doctor Profile | `<<extend>>` | Extending → Base | Opsional |

---

## 4.x.4 Batas Sistem

Batas sistem pada Gambar 4.x berlabel **Sistem PIXEL-T** dan mencakup seluruh *use case* yang disediakan oleh aplikasi. Batas ini memisahkan tanggung jawab internal sistem dari aktor eksternal. Seluruh aktor berada di luar batas sistem, sedangkan seluruh *use case* berada di dalamnya. Batas sistem mencakup tiga komponen yang beroperasi sebagai satu kesatuan: antarmuka *frontend* berbasis React, layanan *backend* berbasis Flask, dan pipeline inferensi AI. Aktor tidak berinteraksi langsung dengan basis data maupun model AI; seluruh interaksi dimediasi oleh *use case* di dalam batas sistem.

---

## 4.x.5 Keterkaitan Diagram dengan Implementasi

Keterlacakan antara *use case* dan implementasi disajikan pada tabel berikut. Tabel ini memudahkan pembaca memverifikasi bahwa setiap elemen diagram memiliki dasar pada kode sumber.

**Tabel 4.x — Keterlacakan Use Case ke Implementasi**

| Use Case | Berkas Utama | Mekanisme |
|----------|--------------|-----------|
| Sign Up | `Register.tsx`, `AuthContext.tsx`, `services/auth.ts` | `supabase.auth.signUp` + trigger 008 |
| Sign In | `Login.tsx`, `AuthContext.tsx`, `services/auth.ts` | `supabase.auth.signInWithPassword` |
| Sign Out | `AppShell.tsx`, `AuthContext.tsx` | `supabase.auth.signOut` |
| Reset Password | `Login.tsx`, `ResetPassword.tsx` | `resetPasswordForEmail`, `updateUser` |
| Upload Image | `NewAnalysis.tsx`, `services/analysis.ts` | `POST /api/analysis` |
| Segmentation | `analysis_service.py`, `pipeline.py` | Pipeline U-Net + Grad-CAM |
| View History | `History.tsx`, `services/analysis.ts` | `GET /api/history` |
| Search / Filter History | `History.tsx` | `useMemo` filter klien |
| View Doctor Profile | `DoctorProfile.tsx`, `services/profile.ts` | `fetchDoctorProfile` |
| Edit Doctor Profile | `DoctorProfile.tsx`, `services/profile.ts` | `saveDoctorProfile`, avatar |
| View Admin Dashboard | `AdminDashboard.tsx` | `GET /api/admin/doctors/stats` |
| View Doctor Registrations | `AdminDashboard.tsx`, `admin_service.py` | `GET /api/admin/doctors` |
| Approve Doctor Account | `AdminDashboard.tsx`, `admin_service.py` | `POST .../approve` |
| Reject Doctor Account | `AdminDashboard.tsx`, `admin_service.py` | `POST .../reject` |

---

## 4.x.6 Kesimpulan

*Use Case Diagram* PIXEL-T yang disajikan pada Gambar 4.x merepresentasikan tiga aktor dan empat belas *use case* yang seluruhnya terlacak ke implementasi aktual. Pemisahan aktor Dokter dan Admin mencerminkan pembedaan hak akses yang ditegakkan pada tiga lapisan: penjaga rute *frontend*, dekorator otorisasi *backend*, dan kebijakan basis data. Relasi `<<include>>` dan `<<extend>>` digunakan secara tepat untuk membedakan perilaku wajib dan opsional. Dengan demikian, diagram ini layak digunakan sebagai bagian dari Bab IV skripsi dan konsisten dengan perangkat lunak yang dibangun.

---

*Dokumen ini disusun berdasarkan analisis statis terhadap kode sumber web PIXEL-T dan dokumen pendukung di folder `references\bab 4`. Tidak ada kode aplikasi yang diubah dalam penyusunan dokumen ini.*
