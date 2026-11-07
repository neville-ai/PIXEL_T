# PENJELASAN USE CASE DIAGRAM PIXEL-T (FINAL REVISI)

## DOKUMEN NARASI BAB IV SKRIPSI S1

**Judul Skripsi:** TRANSFER LEARNING DAN EXPLAINABLE AI UNTUK SEGMENTASI POLIP USUS MENGGUNAKAN CITRA ENDOSKOPI BERBASIS WEB

**Sistem:** PIXEL-T (Sistem Informasi Web Segmentasi Polip Kolonoskopi dengan Transfer Learning dan Explainable AI)

**File Diagram:** `Use Case Diagram PIXELT.png` (raster, batas sistem: **Sistem PIXEL-T**)

**Status Akhir:** FINAL REVISI — layak digunakan dengan catatan perbaikan diagram

**Tanggal Penyusunan:** 6 November 2026

---

## A. Ringkasan Pemeriksaan

Use Case Diagram sistem PIXEL-T telah diperiksa terhadap sumber implementasi aktual (kode sumber frontend, backend, basis data, migrasi, dan pipeline AI). Hasil pemeriksaan ringkas:

- **Jumlah aktor:** 3 (Calon Pengguna, Dokter / Tenaga Medis, Admin)
- **Jumlah use case:** 14 (termasuk Sign Up, Sign In, Sign Out, Reset Password, Upload Image, Segmentation, View History, Search / Filter History, View Doctor Profile, Edit Doctor Profile, View Admin Dashboard, View Doctor Registration, Approve Doctor Account, Reject Doctor Account)
- **Relasi utama:** 14 asosiasi aktor–use case, 1 relasi `<<include>>` (Segmentation → Upload Image), 3 relasi `<<extend>>` (Reset Password → Sign In; Search / Filter History → View History; Edit Doctor Profile → View Doctor Profile)
- **Batas sistem:** satu kotak berlabel "Sistem PIXEL-T" yang mencakup seluruh use case; ketiga aktor berada di luar batas sistem.
- **Kesesuaian dengan implementasi:** seluruh 14 use case dan seluruh asosiasi diverifikasi melalui kode sumber (endpoint, service, halaman frontend, trigger basis data).
- **Bagian yang belum dapat diverifikasi pada diagram visual:** dua node "History" yang saling terhubung dengan `<<extend>>` pada gambar raster adalah duplikasi label; relasi `Reset Password <<extend>> Sign Out` pada gambar raster tidak sesuai arah logis (harusnya `<<extend>> Sign In`); asosiasi `Calon Pengguna → Sign Out` dan ketidakterkaitan `Admin → Sign In` pada gambar raster perlu disesuaikan dengan revisi audit yang tervalidasi.

---

## B. Matriks Validasi Aktor dan Use Case

| No. | Aktor / Use Case | Keterangan pada Diagram | Bukti dari Sumber PIXEL-T | Kesesuaian | Catatan |
|-----|------------------|-------------------------|---------------------------|------------|---------|
| 1 | Calon Pengguna | Aktor tanpa sesi autentikasi; terhubung ke Sign Up dan Sign In (revisi audit) | `Register.tsx`, `AuthContext.tsx`, `services/auth.ts` | TERVERIFIKASI | Hanya layanan publik; tidak ada jalur pendaftaran publik untuk Admin |
| 2 | Dokter / Tenaga Medis | Aktor klinis; terhubung ke Sign In, Sign Out, Upload Image, Segmentation, View History, View Doctor Profile | `ProtectedRoute`, `DoctorRoute`, `require_approved_doctor`, `doctor_profiles` | TERVERIFIKASI | Akses penuh hanya setelah `account_status = 'approved'` |
| 3 | Admin | Aktor manajemen sistem; terhubung ke Sign In, Sign Out, View Admin Dashboard, View Doctor Registration, Approve Doctor Account, Reject Doctor Account | `AdminRoute`, `require_admin`, `app_metadata.role = 'admin'` | TERVERIFIKASI | Tidak memiliki fitur klinis; tidak ada baris pada `doctor_profiles` |
| 4 | Sign Up | Pendaftaran akun baru melalui `/register` | `Register.tsx` → `registerUser` → `supabase.auth.signUp` + trigger 008 | TERVERIFIKASI | Khusus calon dokter; status awal `pending` |
| 5 | Sign In | Masuk ke sistem melalui `/login` untuk semua peran | `Login.tsx` → `loginUser` → `supabase.auth.signInWithPassword` | TERVERIFIKASI | Satu halaman login untuk Calon Pengguna, Dokter, dan Admin |
| 6 | Sign Out | Akhiri sesi autentikasi melalui modal konfirmasi | `AppShell.tsx` → `signOut` → `supabase.auth.signOut` | TERVERIFIKASI | Dilakukan oleh Dokter dan Admin setelah terautentikasi |
| 7 | Reset Password | Lupa kata sandi dalam dua tahap (mode reset pada login + halaman `/reset-password`) | `resetPasswordUser`, `supabase.auth.updateUser` | TERVERIFIKASI | Opsional; dimodelkan sebagai `<<extend>>` terhadap Sign In |
| 8 | Upload Image | Unggah citra endoskopi pada `/analysis/new` | `NewAnalysis.tsx` → `createAnalysis` → `POST /api/analysis` | TERVERIFIKASI | Hanya dokter `approved`; validasi ekstensi, MIME, ukuran ≤ 10 MB |
| 9 | Segmentation | Pipeline inferensi citra (U-Net + Grad-CAM) setelah unggahan | `analysis_service.py` + `ai/inference/pipeline.py` | TERVERIFIKASI | Memerlukan citra tersimpan ⇒ `<<include>>` Upload Image |
| 10 | View History | Lihat daftar riwayat analisis pada `/history` | `History.tsx` → `listHistory` → `GET /api/history` | TERVERIFIKASI | Hanya rekaman milik pengguna yang bersangkutan (`user_id`) |
| 11 | Search / Filter History | Pencarian dan filter riwayat pada sisi klien | `History.tsx` baris 118–136 (`useMemo`) | TERVERIFIKASI | Opsional; dimodelkan sebagai `<<extend>>` terhadap View History |
| 12 | View Doctor Profile | Lihat profil profesional dan statistik aktivitas pada `/profile` | `DoctorProfile.tsx` → `fetchDoctorProfile` | TERVERIFIKASI | Dilindungi `DoctorRoute`; admin dialihkan ke `/admin` |
| 13 | Edit Doctor Profile | Perbarui data profil dan avatar pada modal edit | `DoctorProfile.tsx` baris 445 → `saveDoctorProfile`, avatar | TERVERIFIKASI | Opsional; dimodelkan sebagai `<<extend>>` terhadap View Doctor Profile |
| 14 | View Admin Dashboard | Lihat dasbor statistik pendaftaran dokter pada `/admin` | `AdminDashboard.tsx` → `GET /api/admin/doctors/stats` | TERVERIFIKASI | Hanya Admin; agregat total/pending/approved/rejected |
| 15 | View Doctor Registration | Lihat daftar pendaftaran dokter beserta status akun | `AdminDashboard.tsx` → `GET /api/admin/doctors` (+`?status=`) | TERVERIFIKASI | Hanya Admin; menampilkan nama, surel, rumah sakit, spesialisasi, status |
| 16 | Approve Doctor Account | Setujui akun dokter dari status `pending` | `POST /api/admin/doctors/<id>/approve` → `admin_service.approve_doctor` | TERVERIFIKASI | Hanya Admin; hanya dari status `pending` |
| 17 | Reject Doctor Account | Tolak akun dokter dari status `pending` dengan alasan | `POST /api/admin/doctors/<id>/reject` → `admin_service.reject_doctor` | TERVERIFIKASI | Hanya Admin; hanya dari status `pending`; menyimpan `rejection_reason` |
| 18 | Relasi `<<include>>` | Segmentation `<<include>>` Upload Image | `POST /api/analysis` menolak tanpa berkas (`MISSING_FILE`) | TERVERIFIKASI | Wajib; segmentasi tidak dapat berjalan tanpa citra |
| 19 | Relasi `<<extend>>` | Reset Password `<<extend>>` Sign In | `Login.tsx` mode `reset` | TERVERIFIKASI | Opsional; arah extending → base sesuai UML 2.x |
| 20 | Relasi `<<extend>>` | Search / Filter History `<<extend>>` View History | `History.tsx` filter klien | TERVERIFIKASI | Opsional; hanya bila kriteria diisi |
| 21 | Relasi `<<extend>>` | Edit Doctor Profile `<<extend>>` View Doctor Profile | `DoctorProfile.tsx` modal edit | TERVERIFIKASI | Opsional; hanya bila modal edit dibuka |
| 22 | Generalisasi | Tidak ada generalisasi aktor pada diagram | Tidak ada tabel `admins`; Admin dan Dokter saling eksklusif | TERVERIFIKASI | Generalisasi Admin → Dokter akan menyesatkan (dua jalur otorisasi eksklusif) |
| 23 | Batas Sistem | Satu kotak "Sistem PIXEL-T" mencakup semua use case | Frontend React + Backend Flask + Pipeline AI | TERVERIFIKASI | Komponen internal tidak digambarkan sebagai aktor |

**Catatan Tambahan:**
- Tiga artefak internal AI (Validate Image, Generate Overlay, Generate Grad-CAM) **tidak** dimodelkan sebagai use case aktor karena tidak dapat diinisiasi secara independen oleh pengguna; ketiganya merupakan tahapan internal dalam Segmentation.
- Dua node "History" yang saling terhubung `<<extend>>` pada gambar raster adalah duplikasi label; seharusnya satu node adalah "Search / Filter History".
- Relasi `Reset Password <<extend>> Sign Out` pada gambar raster tidak sesuai arah logis; harusnya `Reset Password <<extend>> Sign In`.

---

## C. Penjelasan Akademik Final

### 4.x Use Case Diagram

Use Case Diagram merupakan salah satu diagram *Unified Modeling Language* (UML) yang digunakan untuk memodelkan interaksi antara aktor dengan sistem pada tingkat perilaku fungsional. Diagram ini tidak menjelaskan urutan eksekusi maupun rincian teknis, melainkan menegaskan **siapa** yang berinteraksi dengan sistem dan **apa** layanan yang disediakan sistem bagi aktor tersebut.

Pada penelitian ini, *Use Case Diagram* disusun berdasarkan implementasi aktual aplikasi web PIXEL-T, bukan berdasarkan asumsi perancangan. Setiap aktor, *use case*, asosiasi, dan relasi *stereotype* ditelusuri langsung ke berkas kode sumber, sehingga diagram yang dihasilkan dapat dipertanggungjawabkan secara akademik dan konsisten dengan perangkat lunak yang dibangun.

Diagram final ditampilkan pada **Gambar 4.x**. Diagram tersebut memuat tiga aktor, empat belas *use case*, satu relasi `<<include>>`, dan tiga relasi `<<extend>>` di dalam satu batas sistem berlabel **Sistem PIXEL-T**.

#### Aktor dan Peran

Aktor merepresentasikan entitas eksternal yang berinteraksi dengan sistem. PIXEL-T memiliki tiga aktor yang dibedakan berdasarkan status autentikasi dan hak aksesnya.

**Calon Pengguna** adalah individu yang belum memiliki sesi autentikasi aktif. Aktor ini merepresentasikan dokter yang bermaksud mendaftar ke sistem. Calon Pengguna hanya dapat menjalankan **Sign Up** dan **Sign In**. Pendaftaran melalui halaman `/register` bersifat khusus dokter: formulir meminta nama lengkap, alamat surel, kata sandi, nama rumah sakit, dan spesialisasi. Tidak terdapat jalur pendaftaran publik untuk peran admin.

**Dokter / Tenaga Medis** adalah tenaga medis yang telah memiliki akun pada tabel `public.doctor_profiles` dengan `role = 'doctor'`. Dokter hanya memperoleh akses penuh setelah `account_status` berubah dari `pending` menjadi `approved` oleh admin. Dokter yang masih berstatus `pending` atau `rejected` dapat melakukan **Sign In** dan **Sign Out**, tetapi tidak dapat menjalankan fitur klinis. Dokter yang telah disetujui dapat menjalankan **Upload Image**, **Segmentation**, **View History**, **Search / Filter History**, **View Doctor Profile**, dan **Edit Doctor Profile**, serta **Sign In** dan **Sign Out**.

**Admin** adalah pengelola sistem yang tidak memiliki fitur klinis. Peran admin direpresentasikan secara eksklusif melalui `auth.users.app_metadata.role = 'admin'`, yang hanya dapat ditulis melalui Supabase Admin API menggunakan *service-role key*. Admin tidak memiliki tabel tersendiri dan tidak memiliki baris pada `doctor_profiles`; trigger basis data secara eksplisit mengecualikan akun admin dari pembuatan profil dokter. Admin menjalankan **View Admin Dashboard**, **View Doctor Registration**, **Approve Doctor Account**, dan **Reject Doctor Account**, serta **Sign In** dan **Sign Out**.

Tabel berikut meringkasan aktor dan hak akses utamanya:

| Aktor | Representasi pada Sistem | Hak Akses Utama |
|-------|--------------------------|-----------------|
| Calon Pengguna | Tanpa sesi autentikasi | Sign Up, Sign In |
| Dokter / Tenaga Medis | `doctor_profiles.role = 'doctor'`, `account_status = 'approved'` | Fitur klinis + profil |
| Admin | `auth.users.app_metadata.role = 'admin'` | Manajemen pendaftaran dokter |

#### Use Case dan Deskripsi

Berikut diuraikan empat belas *use case* beserta aktor utama dan ringkasan perilakunya.

**Sign Up**  \nAktor: Calon Pengguna. Calon pengguna membuka halaman `/register`, mengisi formulir pendaftaran, dan mengirimkannya. Sistem memvalidasi format surel dan panjang kata sandi pada sisi klien, kemudian memanggil layanan autentikasi Supabase. Apabila pendaftaran berhasil, trigger basis data membuat baris `doctor_profiles` dengan `role = 'doctor'` dan `account_status = 'pending'`. Akun belum dapat mengakses fitur klinis sampai disetujui admin.

**Sign In**  \nAktor: Calon Pengguna, Dokter, Admin. Pengguna memasukkan surel dan kata sandi pada halaman `/login`. Sistem memverifikasi kredensial melalui Supabase Auth, kemudian menentukan peran pengguna. Penentuan peran mendahulukan `app_metadata.role` untuk admin, lalu membaca `doctor_profiles.role` dan `account_status` untuk dokter. Setelah peran diketahui, sistem mengalihkan pengguna ke beranda yang sesuai: `/admin` untuk admin dan `/dashboard` untuk dokter yang telah disetujui.

**Sign Out**  \nAktor: Dokter, Admin. Pengguna terautentikasi memilih tombol keluar pada bilah navigasi. Sistem menampilkan modal konfirmasi, menghapus sesi melalui Supabase Auth, dan mengalihkan pengguna ke halaman `/login`.

**Reset Password**  \nAktor: Pengguna yang memiliki akun (melalui Sign In). Reset kata sandi berlangsung dalam dua tahap. Tahap pertama, pengguna memilih mode lupa kata sandi pada halaman `/login`; sistem mengirim tautan pemulihan ke surel terdaftar. Tahap kedua, pengguna membuka tautan tersebut dan mengakses halaman `/reset-password` untuk menetapkan kata sandi baru. *Use case* ini bersifat opsional dan dimodelkan sebagai `<<extend>>` terhadap **Sign In**.

**Upload Image**  \nAktor: Dokter. Dokter memilih berkas citra endoskopi pada halaman `/analysis/new`. Sistem memvalidasi ekstensi, tipe MIME, dan ukuran berkas (maksimum 10 MB) pada sisi klien, menampilkan pratinjau, lalu mengirim berkas ke endpoint `POST /api/analysis`. Endpoint tersebut dilindungi dekorator `require_approved_doctor`, sehingga hanya dokter dengan status `approved` yang dapat mengunggah. Sistem mengembalikan HTTP 202 dan pengguna dialihkan ke halaman hasil.

**Segmentation**  \nAktor: Dokter. Setelah citra diterima, sistem menjalankan pipeline inferensi yang terdiri atas praproses, inferensi U-Net untuk segmentasi polip, pascaproses, pembangkitan Grad-CAM, dan komposisi artefak. Halaman hasil melakukan *polling* `GET /api/analysis/<id>` sampai status analisis berubah menjadi `completed` atau `failed`. *Use case* ini mencakup **Upload Image** sebagai perilaku wajib melalui relasi `<<include>>`.

**View History**  \nAktor: Dokter. Dokter membuka halaman `/history` untuk melihat daftar analisis yang pernah dilakukan. Sistem mengambil data melalui `GET /api/history` yang dilindungi `require_approved_doctor` dan hanya mengembalikan rekaman milik pengguna yang bersangkutan. Setiap baris menampilkan nama berkas, tanggal, status, dan tautan menuju detail.

**Search / Filter History**  \nAktor: Dokter. Pada halaman riwayat, dokter dapat mempersempit daftar menggunakan pencarian teks nama berkas, filter status (`processing`, `completed`, `failed`), dan filter tanggal. Penyaringan dilakukan pada sisi klien menggunakan `useMemo`, sehingga tidak memerlukan permintaan tambahan ke server. *Use case* ini bersifat opsional dan dimodelkan sebagai `<<extend>>` terhadap **View History**.

**View Doctor Profile**  \nAktor: Dokter. Dokter membuka halaman `/profile` untuk melihat data profil profesional dan statistik aktivitas. Halaman dilindungi `DoctorRoute`, sehingga admin dialihkan ke `/admin` dan dokter yang belum disetujui ditolak.

**Edit Doctor Profile**  \nAktor: Dokter. Dokter membuka modal edit untuk memperbarui data profil, mengunggah avatar, atau menghapus avatar. Perubahan disimpan melalui operasi *upsert* ke tabel `doctor_profiles` dan pembaruan metadata pengguna. *Use case* ini bersifat opsional dan dimodelkan sebagai `<<extend>>` terhadap **View Doctor Profile**.

**View Admin Dashboard**  \nAktor: Admin. Admin membuka halaman `/admin` yang dilindungi `AdminRoute` dan dekorator `require_admin`. Sistem menampilkan agregat statistik pendaftaran dokter: total, `pending`, `approved`, dan `rejected`, yang diambil dari endpoint `GET /api/admin/doctors/stats`.

**View Doctor Registration**  \nAktor: Admin. Admin melihat daftar pendaftaran dokter beserta status akun. Daftar dapat difilter berdasarkan status melalui parameter `?status=` pada endpoint `GET /api/admin/doctors`. Setiap entri menampilkan nama, surel, rumah sakit, spesialisasi, status, dan tanggal pendaftaran.

**Approve Doctor Account**  \nAktor: Admin. Admin menyetujui akun dokter yang berstatus `pending`. Sistem mengirim permintaan ke `POST /api/admin/doctors/<id>/approve`. Layanan backend hanya mengizinkan transisi dari `pending` menjadi `approved`; permintaan terhadap akun yang sudah diproses ditolak. Setelah disetujui, dokter memperoleh akses penuh ke fitur klinis.

**Reject Doctor Account**  \nAktor: Admin. Admin menolak akun dokter yang berstatus `pending` dengan mencantumkan alasan penolakan. Sistem mengirim permintaan ke `POST /api/admin/doctors/<id>/reject`. Layanan backend hanya mengizinkan transisi dari `pending` menjadi `rejected` dan menyimpan `rejection_reason`. Dokter yang ditolak tidak dapat mengakses fitur klinis.

Tabel berikut meringkasan *use case* dan aktor yang terkait:

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
| 12 | View Doctor Registration | Admin |
| 13 | Approve Doctor Account | Admin |
| 14 | Reject Doctor Account | Admin |

#### Relasi `<<include>>` dan `<<extend>>`

Relasi `<<include>>` menyatakan bahwa suatu *use case* **wajib** menjalankan *use case* lain sebagai bagian dari perilakunya. Pada diagram PIXEL-T terdapat satu relasi ini, yaitu **Segmentation** `<<include>>` **Upload Image**. Segmentasi tidak mungkin dijalankan tanpa citra yang telah diunggah dan tersimpan; oleh karena itu, hubungan wajib tersebut tepat dimodelkan sebagai `<<include>>`.

Relasi `<<extend>>` menyatakan bahwa suatu *use case* **opsional** memperluas *use case* lain pada kondisi tertentu. Arah panah mengikuti kaidah UML 2.x, yakni dari *extending use case* menuju *base use case*. Terdapat tiga relasi `<<extend>>`:

1. **Reset Password** `<<extend>>` **Sign In** — reset kata sandi hanya dijalankan bila pengguna memilih opsi lupa kata sandi.
2. **Search / Filter History** `<<extend>>` **View History** — pencarian dan filter hanya aktif bila pengguna mengisi kriteria.
3. **Edit Doctor Profile** `<<extend>>` **View Doctor Profile** — pengeditan hanya terjadi bila pengguna membuka modal edit.

#### Batas Sistem

Batas sistem pada **Gambar 4.x** berlabel **Sistem PIXEL-T** dan mencakup seluruh *use case* yang disediakan oleh aplikasi. Batas ini memisahkan tanggung jawab internal sistem dari aktor eksternal. Seluruh aktor berada di luar batas sistem, sedangkan seluruh *use case* berada di dalamnya. Batas sistem mencakup tiga komponen yang beroperasi sebagai satu kesatuan: antarmuka *frontend* berbasis React, layanan *backend* berbasis Flask, dan pipeline inferensi AI. Aktor tidak berinteraksi langsung dengan basis data maupun model AI; seluruh interaksi dimediasi oleh *use case* di dalam batas sistem.

#### Keterkaitan Diagram dengan Implementasi

Keterlacakan antara *use case* dan implementasi disajikan pada tabel berikut. Tabel ini memudahkan pembaca memverifikasi bahwa setiap elemen diagram memiliki dasar pada kode sumber.

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
| View Doctor Registration | `AdminDashboard.tsx`, `admin_service.py` | `GET /api/admin/doctors` |
| Approve Doctor Account | `AdminDashboard.tsx`, `admin_service.py` | `POST .../approve` |
| Reject Doctor Account | `AdminDashboard.tsx`, `admin_service.py` | `POST .../reject` |

#### Kesimpulan Narasi

*Use Case Diagram* PIXEL-T yang disajikan pada **Gambar 4.x** merepresentasikan tiga aktor dan empat belas *use case* yang seluruhnya terlacak ke implementasi aktual. Pemisahan aktor Dokter dan Admin mencerminkan pembedaan hak akses yang ditegakkan pada tiga lapisan: penjaga rute *frontend*, dekorator otorisasi *backend*, dan kebijakan basis data. Relasi `<<include>>` dan `<<extend>>` digunakan secara tepat untuk membedakan perilaku wajib dan opsional. Dengan demikian, diagram ini layak digunakan sebagai bagian dari Bab IV skripsi dan konsisten dengan perangkat lunak yang dibangun.

---

## D. Catatan Kesesuaian

### Bagian yang telah sesuai dengan diagram dan sumber implementasi

1. Tiga aktor (Calon Pengguna, Dokter / Tenaga Medis, Admin) sesuai dengan implementasi otorisasi pada tiga lapisan (frontend route guard, backend decorator, basis data RLS + trigger).
2. Semua 14 use case memiliki bukti implementasi dalam kode sumber (halaman frontend, service, endpoint backend, dan migrasi basis data).
3. Relasi `<<include>>` Segmentation → Upload Image valid karena segmentasi memerlukan citra tersimpan.
4. Tiga relasi `<<extend>>` (Reset Password → Sign In; Search / Filter History → View History; Edit Doctor Profile → View Doctor Profile) valid dan arah panah sesuai UML 2.x.
5. Tidak ada generalisasi aktor yang menyesatkan; Admin dan Dokter adalah dua jalur otorisasi saling eksklusif.
6. Batas sistem "Sistem PIXEL-T" mencakup seluruh use case; komponen internal tidak digambarkan sebagai aktor.

### Bagian yang perlu diperbaiki pada diagram

1. **Duplikasi node "History":** Gambar raster menunjukkan dua node "History" yang saling terhubung dengan `<<extend>>`. Seharusnya satu node adalah "Search / Filter History" untuk mencerminkan relasi `<<extend>>` terhadap View History.
2. **Arah relasi `Reset Password <<extend>> Sign Out`:** Pada gambar raster, relasi ini menunjuk ke Sign Out. Secara logis dan sesuai revisi audit, harusnya `Reset Password <<extend>> Sign In`.
3. **Asosiasi `Calon Pengguna → Sign Out`:** Calon Pengguna belum login, sehingga tidak dapat melakukan Sign Out. Asosiasi ini seharusnya `Calon Pengguna → Sign In` (sesuai revisi audit).
4. **Ketidakterkaitan `Admin → Sign In`:** Admin juga perlu Sign In. Asosiasi ini hilang pada gambar raster dan perlu ditambahkan.

### Bagian yang belum dapat dipastikan

1. Tidak tersedia file sumber `.drawio` untuk Use Case Diagram, hanya file raster PNG. Perubahan diagram memerlukan menggambar ulang atau menggunakan file generator Python (`_gen_use_case_audit_png.py`).
2. Tidak ada pengujian runtime (browser/end-to-end) yang dilakukan untuk memverifikasi alur Sign Up, Sign In, Upload Image, Segmentation, History, Doctor Profile, dan Sign Out secara menyeluruh melalui antarmuka pengguna.

### Rekomendasi sebelum penjelasan dimasukkan ke skripsi

1. **Perbaiki diagram visual:** Perbaiki keempat masalah di atas (duplikasi History, arah Reset Password, asosiasi Calon Pengguna, dan asosiasi Admin → Sign In) agar diagram konsisten dengan revisi audit yang tervalidasi (`USE_CASE_DIAGRAM_PIXELT_FINAL_AUDITED`).
2. **Sesuaikan nomor gambar dan tabel:** Ganti placeholder `Gambar 4.x` dan `Tabel 4.x` dengan nomor akhir sesuai urutan penyajian pada Bab IV.
3. **Pertahankan penamaan use case dalam bahasa Inggris** agar konsisten dengan istilah teknis pada kode sumber. Apabila pembimbing mensyaratkan bahasa Indonesia penuh, gunakan padanan terjemah tanpa mengubah struktur dan relasi.
4. **Sertakan prasyarat status akun (approve/reject hanya dari `pending`) pada narasi atau tabel spesifikasi**, bukan ditambahkan sebagai elemen diagram, agar diagram tetap ringkas dan sesuai kaidah UML.
5. **Tandai dokumen audit lama yang bertentangan** (`LAPORAN_AUDIT_USE_CASE_PIXELT.md` dan catatan `/reset-password` pada `AUDIT_DAMPAK_ROLE_ADMIN_DOKTER_PIXELT.md`) sebagai digantikan oleh revisi ini.

---

*Dokumen ini disusun berdasarkan analisis statis terhadap kode sumber web PIXEL-T dan dokumen pendukung di folder `references\bab 4`. Tidak ada kode aplikasi, migrasi, konfigurasi, kredensial, atau file referensi asli yang diubah dalam penyusunan dokumen ini.*