# PENJELASAN USE CASE DIAGRAM PIXEL-T (FINAL AUDITED)

**Dokumen Narasi Bab IV Skripsi S1**
Sistem: PIXEL-T (*Polyp Identification with eXplainable Intelligence for Early-stage Local Tissue detection*)
Berkas diagram: `USE_CASE_DIAGRAM_PIXELT_FINAL_AUDITED.drawio` / `USE_CASE_DIAGRAM_PIXELT_FINAL_AUDITED.png`
Status: final, tervalidasi dengan revisi (lihat `DEEP_AUDIT_WEB_PIXELT_USE_CASE.md`).

---

## 1. Pendahuluan

*Use Case Diagram* merupakan salah satu diagram *Unified Modeling Language* (UML) yang digunakan untuk memodelkan interaksi antara aktor dengan sistem pada tingkat perilaku fungsional. Diagram ini tidak menjelaskan urutan eksekusi maupun rincian teknis, melainkan menegaskan **siapa** yang berinteraksi dengan sistem dan **apa** layanan yang disediakan sistem bagi aktor tersebut.

Pada penelitian ini, *Use Case Diagram* disusun berdasarkan implementasi aktual aplikasi web PIXEL-T, bukan berdasarkan asumsi perancangan. Setiap aktor, *use case*, asosiasi, dan relasi *stereotype* ditelusuri langsung ke berkas kode sumber, sehingga diagram yang dihasilkan dapat dipertanggungjawabkan secara akademik dan konsisten dengan perangkat lunak yang dibangun.

Diagram final ditampilkan pada **Gambar 4.x**. Diagram tersebut memuat tiga aktor, empat belas *use case*, satu relasi `<<include>>`, dan tiga relasi `<<extend>>` di dalam satu batas sistem berlabel **Sistem PIXEL-T**.

---

## 2. Aktor dan Peran

Aktor merepresentasikan entitas eksternal yang berinteraksi dengan sistem. PIXEL-T memiliki tiga aktor yang dibedakan berdasarkan status autentikasi dan hak aksesnya.

### 2.1 Calon Pengguna

**Calon Pengguna** adalah individu yang belum memiliki sesi autentikasi aktif. Aktor ini merepresentasikan dokter yang bermaksud mendaftar ke sistem. Calon Pengguna hanya dapat menjalankan **Sign Up** dan **Sign In**. Pendaftaran melalui halaman `/register` bersifat khusus dokter: formulir meminta nama lengkap, alamat surel, kata sandi, nama rumah sakit, dan spesialisasi. Tidak terdapat jalur pendaftaran publik untuk peran admin.

### 2.2 Dokter

**Dokter** adalah tenaga medis yang telah memiliki akun pada tabel `public.doctor_profiles` dengan `role = 'doctor'`. Dokter hanya memperoleh akses penuh setelah `account_status` berubah dari `pending` menjadi `approved` oleh admin. Dokter yang masih berstatus `pending` atau `rejected` dapat melakukan **Sign In** dan **Sign Out**, tetapi tidak dapat menjalankan fitur klinis. Dokter yang telah disetujui dapat menjalankan **Upload Image**, **Segmentation**, **View History**, **Search / Filter History**, **View Doctor Profile**, dan **Edit Doctor Profile**.

### 2.3 Admin

**Admin** adalah pengelola sistem yang tidak memiliki fitur klinis. Peran admin direpresentasikan secara eksklusif melalui `auth.users.app_metadata.role = 'admin'`, yang hanya dapat ditulis melalui Supabase Admin API menggunakan *service-role key*. Admin tidak memiliki tabel tersendiri dan tidak memiliki baris pada `doctor_profiles`; trigger basis data secara eksplisit mengecualikan akun admin dari pembuatan profil dokter. Admin menjalankan **View Admin Dashboard**, **View Doctor Registrations**, **Approve Doctor Account**, dan **Reject Doctor Account**, serta **Sign In** dan **Sign Out**.

**Tabel 4.x — Ringkasan Aktor**

| Aktor | Representasi pada Sistem | Hak Akses Utama |
|-------|--------------------------|-----------------|
| Calon Pengguna | Tanpa sesi autentikasi | Sign Up, Sign In |
| Dokter | `doctor_profiles.role = 'doctor'`, `account_status = 'approved'` | Fitur klinis + profil |
| Admin | `auth.users.app_metadata.role = 'admin'` | Manajemen pendaftaran dokter |

---

## 3. Use Case dan Deskripsi

Berikut diuraikan keempat belas *use case* beserta aktor utama dan ringkasan perilakunya.

### 3.1 Sign Up

**Aktor:** Calon Pengguna.
**Deskripsi:** Calon pengguna membuka halaman `/register`, mengisi formulir pendaftaran, dan mengirimkannya. Sistem memvalidasi format surel dan panjang kata sandi pada sisi klien, kemudian memanggil layanan autentikasi Supabase. Apabila pendaftaran berhasil, trigger basis data membuat baris `doctor_profiles` dengan `role = 'doctor'` dan `account_status = 'pending'`. Akun belum dapat mengakses fitur klinis sampai disetujui admin.

### 3.2 Sign In

**Aktor:** Calon Pengguna, Dokter, Admin.
**Deskripsi:** Pengguna memasukkan surel dan kata sandi pada halaman `/login`. Sistem memverifikasi kredensial melalui Supabase Auth, kemudian menentukan peran pengguna. Penentuan peran mendahulukan `app_metadata.role` untuk admin, lalu membaca `doctor_profiles.role` dan `account_status` untuk dokter. Setelah peran diketahui, sistem mengalihkan pengguna ke beranda yang sesuai: `/admin` untuk admin dan `/dashboard` untuk dokter yang telah disetujui.

### 3.3 Sign Out

**Aktor:** Dokter, Admin.
**Deskripsi:** Pengguna terautentikasi memilih tombol keluar pada bilah navigasi. Sistem menampilkan modal konfirmasi, menghapus sesi melalui Supabase Auth, dan mengalihkan pengguna ke halaman `/login`.

### 3.4 Reset Password

**Aktor:** Pengguna yang memiliki akun (melalui Sign In).
**Deskripsi:** Reset kata sandi berlangsung dalam dua tahap. Tahap pertama, pengguna memilih mode lupa kata sandi pada halaman `/login`; sistem mengirim tautan pemulihan ke surel terdaftar. Tahap kedua, pengguna membuka tautan tersebut dan mengakses halaman `/reset-password` untuk menetapkan kata sandi baru. *Use case* ini bersifat opsional dan dimodelkan sebagai `<<extend>>` terhadap **Sign In**.

### 3.5 Upload Image

**Aktor:** Dokter.
**Deskripsi:** Dokter memilih berkas citra endoskopi pada halaman `/analysis/new`. Sistem memvalidasi ekstensi, tipe MIME, dan ukuran berkas (maksimum 10 MB) pada sisi klien, menampilkan pratinjau, lalu mengirim berkas ke endpoint `POST /api/analysis`. Endpoint tersebut dilindungi dekorator `require_approved_doctor`, sehingga hanya dokter dengan status `approved` yang dapat mengunggah. Sistem mengembalikan HTTP 202 dan pengguna dialihkan ke halaman hasil.

### 3.6 Segmentation

**Aktor:** Dokter.
**Deskripsi:** Setelah citra diterima, sistem menjalankan pipeline inferensi yang terdiri atas praproses, inferensi U-Net untuk segmentasi polip, pascaproses, pembangkitan Grad-CAM, dan komposisi artefak. Halaman hasil melakukan *polling* `GET /api/analysis/<id>` sampai status analisis berubah menjadi `completed` atau `failed`. *Use case* ini mencakup **Upload Image** sebagai perilaku wajib melalui relasi `<<include>>`.

### 3.7 View History

**Aktor:** Dokter.
**Deskripsi:** Dokter membuka halaman `/history` untuk melihat daftar analisis yang pernah dilakukan. Sistem mengambil data melalui `GET /api/history` yang dilindungi `require_approved_doctor` dan hanya mengembalikan rekaman milik pengguna yang bersangkutan. Setiap baris menampilkan nama berkas, tanggal, status, dan tautan menuju detail.

### 3.8 Search / Filter History

**Aktor:** Dokter.
**Deskripsi:** Pada halaman riwayat, dokter dapat mempersempit daftar menggunakan pencarian teks nama berkas, filter status (`processing`, `completed`, `failed`), dan filter tanggal. Penyaringan dilakukan pada sisi klien menggunakan `useMemo`, sehingga tidak memerlukan permintaan tambahan ke server. *Use case* ini bersifat opsional dan dimodelkan sebagai `<<extend>>` terhadap **View History**.

### 3.9 View Doctor Profile

**Aktor:** Dokter.
**Deskripsi:** Dokter membuka halaman `/profile` untuk melihat data profil profesional dan statistik aktivitas. Halaman dilindungi `DoctorRoute`, sehingga admin dialihkan ke `/admin` dan dokter yang belum disetujui ditolak.

### 3.10 Edit Doctor Profile

**Aktor:** Dokter.
**Deskripsi:** Dokter membuka modal edit untuk memperbarui data profil, mengunggah avatar, atau menghapus avatar. Perubahan disimpan melalui operasi *upsert* ke tabel `doctor_profiles` dan pembaruan metadata pengguna. *Use case* ini bersifat opsional dan dimodelkan sebagai `<<extend>>` terhadap **View Doctor Profile**.

### 3.11 View Admin Dashboard

**Aktor:** Admin.
**Deskripsi:** Admin membuka halaman `/admin` yang dilindungi `AdminRoute` dan dekorator `require_admin`. Sistem menampilkan agregat statistik pendaftaran dokter: total, `pending`, `approved`, dan `rejected`, yang diambil dari endpoint `GET /api/admin/doctors/stats`.

### 3.12 View Doctor Registrations

**Aktor:** Admin.
**Deskripsi:** Admin melihat daftar pendaftaran dokter beserta status akun. Daftar dapat difilter berdasarkan status melalui parameter `?status=` pada endpoint `GET /api/admin/doctors`. Setiap entri menampilkan nama, surel, rumah sakit, spesialisasi, status, dan tanggal pendaftaran.

### 3.13 Approve Doctor Account

**Aktor:** Admin.
**Deskripsi:** Admin menyetujui akun dokter yang berstatus `pending`. Sistem mengirim permintaan ke `POST /api/admin/doctors/<id>/approve`. Layanan backend hanya mengizinkan transisi dari `pending` menjadi `approved`; permintaan terhadap akun yang sudah diproses ditolak. Setelah disetujui, dokter memperoleh akses penuh ke fitur klinis.

### 3.14 Reject Doctor Account

**Aktor:** Admin.
**Deskripsi:** Admin menolak akun dokter yang berstatus `pending` dengan mencantumkan alasan penolakan. Sistem mengirim permintaan ke `POST /api/admin/doctors/<id>/reject`. Layanan backend hanya mengizinkan transisi dari `pending` menjadi `rejected` dan menyimpan `rejection_reason`. Dokter yang ditolak tidak dapat mengakses fitur klinis.

**Tabel 4.x — Daftar Use Case dan Aktor**

| No | Use Case | Aktor |
|----|----------|-------|
| 1 | Sign Up | Calon Pengguna |
| 2 | Sign In | Calon Pengguna, Dokter, Admin |
| 3 | Sign Out | Dokter, Admin |
| 4 | Reset Password | (melalui Sign In) |
| 5 | Upload Image | Dokter |
| 6 | Segmentation | Dokter |
| 7 | View History | Dokter |
| 8 | Search / Filter History | Dokter |
| 9 | View Doctor Profile | Dokter |
| 10 | Edit Doctor Profile | Dokter |
| 11 | View Admin Dashboard | Admin |
| 12 | View Doctor Registrations | Admin |
| 13 | Approve Doctor Account | Admin |
| 14 | Reject Doctor Account | Admin |

---

## 4. Relasi `<<include>>` dan `<<extend>>`

### 4.1 Relasi `<<include>>`

Relasi `<<include>>` menyatakan bahwa suatu *use case* **wajib** menjalankan *use case* lain sebagai bagian dari perilakunya. Pada diagram PIXEL-T terdapat satu relasi ini, yaitu **Segmentation** `<<include>>` **Upload Image**. Segmentasi tidak mungkin dijalankan tanpa citra yang telah diunggah dan tersimpan; oleh karena itu, hubungan wajib tersebut tepat dimodelkan sebagai `<<include>>`.

### 4.2 Relasi `<<extend>>`

Relasi `<<extend>>` menyatakan bahwa suatu *use case* **opsional** memperluas *use case* lain pada kondisi tertentu. Arah panah mengikuti kaidah UML 2.x, yakni dari *extending use case* menuju *base use case*. Terdapat tiga relasi `<<extend>>`:

1. **Reset Password** `<<extend>>` **Sign In** — reset kata sandi hanya dijalankan bila pengguna memilih opsi lupa kata sandi.
2. **Search / Filter History** `<<extend>>` **View History** — pencarian dan filter hanya aktif bila pengguna mengisi kriteria.
3. **Edit Doctor Profile** `<<extend>>` **View Doctor Profile** — pengeditan hanya terjadi bila pengguna membuka modal edit.

**Tabel 4.x — Relasi Stereotype**

| Relasi | Jenis | Arah | Sifat |
|--------|-------|------|-------|
| Segmentation → Upload Image | `<<include>>` | Wajib | Tidak dapat dilewati |
| Reset Password → Sign In | `<<extend>>` | Opsional | Aktif atas pilihan pengguna |
| Search / Filter History → View History | `<<extend>>` | Opsional | Aktif bila kriteria diisi |
| Edit Doctor Profile → View Doctor Profile | `<<extend>>` | Opsional | Aktif bila modal edit dibuka |

---

## 5. Batas Sistem

Batas sistem pada **Gambar 4.x** berlabel **Sistem PIXEL-T** dan mencakup seluruh *use case* yang disediakan oleh aplikasi. Batas ini memisahkan tanggung jawab internal sistem dari aktor eksternal. Seluruh aktor berada di luar batas sistem, sedangkan seluruh *use case* berada di dalamnya. Batas sistem mencakup tiga komponen yang beroperasi sebagai satu kesatuan: antarmuka *frontend* berbasis React, layanan *backend* berbasis Flask, dan pipeline inferensi AI. Aktor tidak berinteraksi langsung dengan basis data maupun model AI; seluruh interaksi dimediasi oleh *use case* di dalam batas sistem.

---

## 6. Keterkaitan Diagram dengan Implementasi

Keterlacakan antara *use case* dan implementasi disajikan pada **Tabel 4.x**. Tabel ini memudahkan pembaca memverifikasi bahwa setiap elemen diagram memiliki dasar pada kode sumber.

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

## 7. Catatan Penulisan Bab IV

1. **Gambar 4.x** pada dokumen ini merujuk pada `USE_CASE_DIAGRAM_PIXELT_FINAL_AUDITED.png`. Penomoran gambar disesuaikan dengan urutan penyajian pada Bab IV.
2. **Tabel 4.x** pada dokumen ini merupakan penomoran sementara; sesuaikan dengan urutan tabel pada Bab IV.
3. **Penamaan *use case* menggunakan bahasa Inggris** agar konsisten dengan istilah teknis pada kode sumber. Apabila pembimbing mensyaratkan bahasa Indonesia penuh, gunakan padanan: *View Admin Dashboard* → *Melihat Dasbor Admin*, *View Doctor Registrations* → *Melihat Pendaftaran Dokter*, *Approve Doctor Account* → *Menyetujui Akun Dokter*, *Reject Doctor Account* → *Menolak Akun Dokter*, tanpa mengubah struktur dan relasi.
4. **Artefak pipeline AI** (validasi citra, pembuatan *overlay*, Grad-CAM) tidak digambarkan sebagai *use case* aktor. Artefak tersebut dijelaskan pada narasi **Segmentation** sebagai tahapan internal.
5. **Prasyarat status akun** (misalnya approve/reject hanya dari `pending`) dijelaskan pada narasi *use case*, bukan ditambahkan sebagai elemen diagram, agar diagram tetap ringkas dan sesuai kaidah UML.
6. **Diagram tidak memuat generalisasi aktor.** Admin dan Dokter adalah dua jalur otorisasi yang saling eksklusif; generalisasi Admin → Dokter akan menyesatkan pembaca.

---

## 8. Kesimpulan Narasi

*Use Case Diagram* PIXEL-T yang disajikan pada **Gambar 4.x** merepresentasikan tiga aktor dan empat belas *use case* yang seluruhnya terlacak ke implementasi aktual. Pemisahan aktor Dokter dan Admin mencerminkan pembedaan hak akses yang ditegakkan pada tiga lapisan: penjaga rute *frontend*, dekorator otorisasi *backend*, dan kebijakan basis data. Relasi `<<include>>` dan `<<extend>>` digunakan secara tepat untuk membedakan perilaku wajib dan opsional. Dengan demikian, diagram ini layak digunakan sebagai bagian dari Bab IV skripsi dan konsisten dengan perangkat lunak yang dibangun.

---

*Dokumen ini disusun berdasarkan analisis statis terhadap kode sumber web PIXEL-T dan pengujian unit lokal. Tidak ada kode aplikasi yang diubah dalam penyusunan dokumen ini.*
