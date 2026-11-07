# DOKUMEN PENJELASAN AKADEMIK TUJUH SEQUENCE DIAGRAM PIXEL-T
## Naskah Siap Salin untuk Bab IV Skripsi S1

> **Catatan Penomoran bagi Penulis Skripsi:**  
> Penomoran subbab `4.x` dan nomor gambar `Gambar 4.x` pada naskah ini merupakan placeholder penomoran standar. Sesuaikan digit `x` dengan urutan nomor subbab dan gambar yang berlaku pada draf Bab IV skripsi Anda (misalnya `4.3`, `Gambar 4.15`, dst.).

---

### 4.x Sequence Diagram

Sequence Diagram digunakan untuk memodelkan aspek dinamis dari sistem web PIXEL-T dengan menggambarkan urutan interaksi dan komunikasi antarobjek atau antarkomponen secara kronologis berdasarkan garis waktu (*lifeline*). Pada sistem PIXEL-T, Sequence Diagram memetakan kolaborasi antara pengguna (*User*), antarmuka pengguna berbasis React (*Frontend*), perantara status autentikasi (*AuthContext*), pustaka layanan (*Service Layer*), server web API berbasis Flask (*Backend*), mesin inferensi kecerdasan buatan (*Pipeline AI U-Net + ResNet50*), serta sistem backend-as-a-service Supabase yang mengelola autentikasi, basis data PostgreSQL, dan penyimpanan objek citra medis (*Supabase Storage*).

Pembahasan Sequence Diagram pada sistem web PIXEL-T dibagi menjadi tujuh skenario proses utama, yaitu proses pendaftaran akun (*Sign Up*), proses masuk sistem (*Sign In*), proses pengunggahan citra (*Upload Image*), proses analisis dan segmentasi citra medis (*Segmentation*), proses penelusuran riwayat analisis (*History*), proses pengelolaan profil dokter (*Doctor Profile*), dan proses keluar dari sistem (*Sign Out*).

---

#### 4.x.1 Sequence Diagram Sign Up

Gambar 4.x menunjukkan Sequence Diagram Sign Up yang memodelkan rangkaian interaksi dalam proses registrasi akun baru pada sistem web PIXEL-T.

```
[Sisipkan Gambar: Sequence Diagram - Sign Up.drawio.png]
Gambar 4.x Sequence Diagram Sign Up
```

Proses pendaftaran dimulai saat calon pengguna mengakses halaman registrasi (`accessFormSignUp`). Antarmuka pengguna (*SignUp*) merespons dengan menampilkan formulir pendaftaran yang memuat isian nama lengkap, alamat email, kata sandi, konfirmasi kata sandi, nama rumah sakit, dan spesialisasi dokter. Pengguna kemudian melengkapi seluruh data dan menekan tombol pendaftaran (`submitFormSignUp`). Komponen antarmuka pengguna secara internal menjalankan validasi formulir sisi klien (*inputValidation*) untuk memastikan seluruh kolom wajib terisi, alamat email memenuhi format regex standar, kata sandi memiliki panjang minimal 6 karakter, serta nilai kata sandi identik dengan konfirmasi kata sandi. 

Apabila data yang dimasukkan tidak memenuhi kriteria validasi (*Validation Failed*), antarmuka pengguna langsung menampilkan pesan kesalahan validasi spesifik kepada pengguna tanpa melanjutkan permintaan ke server. Sebaliknya, apabila seluruh input dinyatakan valid (*Validation Passed*), komponen antarmuka meneruskan data pendaftaran dengan memanggil fungsi `signUp` pada lapisan manajemen status aplikasi (*AuthContext*), yang selanjutnya memanggil fungsi `registerUser` pada layanan autentikasi (*AuthService*).

Layanan autentikasi terlebih dahulu melakukan verifikasi kesiapan konfigurasi koneksi Supabase. Apabila kredensial lingkungan Supabase belum terkonfigurasi (*Not Yet Configured*), layanan mengembalikan pesan kesalahan konfigurasi ke antarmuka untuk diinformasikan kepada pengguna. Jika koneksi telah terkonfigurasi (*Passed*), layanan autentikasi meneruskan permintaan pembuatan akun ke Supabase Auth (`signUpMetadata`) menggunakan fungsi bawaan `supabase.auth.signUp`. Pada pemanggilan ini, data email dan kata sandi dikirim bersama atribut metadata pengguna yang mencakup nama lengkap, institusi rumah sakit, spesialisasi dokter, serta objek profil dokter awal.

Pihak Supabase Auth memproses permintaan dan mengembalikan respons hasil pendaftaran. Apabila terjadi kegagalan dari sisi Supabase Auth (*From Supabase*), seperti format email ditolak atau alamat email telah terdaftar sebelumnya, layanan autentikasi mengonversi kode kesalahan teknis tersebut melalui fungsi `formatAuthError` menjadi pesan kesalahan bahasa Indonesia yang informatif, lalu meneruskannya secara berjenjang hingga ditampilkan pada layar pengguna. 

Sebaliknya, apabila pendaftaran akun berhasil (*Success*), Supabase Auth mengembalikan data akun pengguna. Pada kondisi sistem Supabase mengaktifkan sesi login langsung (*Active Session*), *AuthContext* secara otomatis memperbarui status pengguna (`setUserSession`), dan antarmuka menampilkan pesan keberhasilan pembuatan akun serta langsung mengarahkan pengguna ke sesi aktif aplikasi. Namun, apabila sistem Supabase menerapkan mekanisme verifikasi email sebelum sesi dapat diterbitkan (*Confirmation Required*), antarmuka menampilkan notifikasi bahwa proses pendaftaran telah diproses dan meminta pengguna memeriksa kotak masuk email untuk mengonfirmasi akun sebelum dapat melakukan proses masuk sistem.

---

#### 4.x.2 Sequence Diagram Sign In

Gambar 4.x menunjukkan Sequence Diagram Sign In yang memodelkan alur autentikasi pengguna saat melakukan proses masuk ke dalam sistem web PIXEL-T.

```
[Sisipkan Gambar: Sequence Diagram - Sign In.drawio.png]
Gambar 4.x Sequence Diagram Sign In
```

Alur masuk sistem diawali ketika pengguna membuka halaman login (`accessFormSignIn`), di mana antarmuka pengguna (*SignIn*) merespons dengan menampilkan formulir masukan alamat email dan kata sandi. Pengguna kemudian memasukkan kredensial akun dan menekan tombol masuk (`submitFormSignIn`). Antarmuka pengguna terlebih dahulu melakukan validasi masukan lokal (*inputValidation*) untuk memastikan kolom email dan kata sandi tidak berada dalam kondisi kosong.

Setelah masukan tervalidasi, komponen antarmuka memanggil fungsi `signIn` pada *AuthContext*, yang kemudian meneruskan permintaan tersebut dengan memanggil fungsi `loginUser` pada *AuthService*. Pustaka layanan autentikasi mengeksekusi fungsi resmi `supabase.auth.signInWithPassword` (`signInWithEmailPassword`) ke server Supabase Auth dengan menyertakan alamat email dan kata sandi pengguna.

Server Supabase Auth memverifikasi kredensial akun terhadap basis data autentikasi terenkripsi dan mengembalikan hasil autentikasi (*Authentication Result*). Apabila autentikasi ditolak karena email tidak ditemukan, kata sandi keliru, atau akun belum dikonfirmasi, *AuthService* menangkap objek galat dan menyaringnya melalui fungsi `formatAuthError` untuk menghasilkan pesan berbahasa Indonesia yang aman tanpa membocorkan rincian basis data sistem. Informasi kegagalan (*Login Failed*) kemudian diteruskan ke antarmuka pengguna untuk menampilkan notifikasi galat pada layar.

Sebaliknya, apabila kredensial akun terbukti sah (*Login Successful*), Supabase Auth menerbitkan token akses JWT dan objek sesi pengguna. Hasil ini diterima oleh *AuthContext* yang kemudian memperbarui variabel status pengguna secara global (`setUserSession`) serta menyimpan token ke penyimpanan lokal peramban. Terakhir, antarmuka pengguna menerima konfirmasi keberhasilan masuk, memperbarui status tampilan (*UI Update*), dan secara otomatis mengarahkan navigasi pengguna ke halaman utama sistem (*Dashboard*).

---

#### 4.x.3 Sequence Diagram Upload Image

Gambar 4.x menunjukkan Sequence Diagram Upload Image yang menggambarkan proses pengunggahan berkas citra ultrasonografi (USG) tiroid oleh pengguna ke server sistem PIXEL-T.

```
[Sisipkan Gambar: Sequence Diagram - Upload Image.drawio.png]
Gambar 4.x Sequence Diagram Upload Image
```

Proses pengunggahan dimulai saat pengguna memilih berkas citra medis dari perangkat lokal (`selectImage`) pada halaman analisis baru. Komponen antarmuka pengguna (*Frontend*) segera melakukan validasi awal berkas (*Image Validation*) yang mencakup pemeriksaan ekstensi berkas (`.jpg`, `.jpeg`, `.png`), pencocokan tipe MIME (`image/jpeg`, `image/png`), serta batas ukuran maksimal berkas sebesar 10 MB. 

Apabila berkas yang dipilih tidak memenuhi kriteria (*Invalid File*), antarmuka menampilkan pesan kesalahan validasi kepada pengguna dan menolak pemrosesan berkas. Apabila berkas dinyatakan valid (*Valid File*), antarmuka menampilkan pratinjau citra dan indikator status bahwa berkas siap untuk dianalisis (*Show Success Message*). Pengguna selanjutnya menekan tombol untuk memulai analisis citra (`clickStartAnalysis`).

Tindakan pengguna tersebut memicu antarmuka untuk menyusun berkas citra ke dalam format `FormData` dan mengirimkannya bersama token otorisasi Bearer JWT ke server backend Flask (`postImageAndAuthentication`) melalui endpoint `POST /api/analysis`. Di sisi server, komponen *Backend* memverifikasi keabsahan identitas pengguna melalui tanda tangan token JWT serta melakukan validasi integritas struktur biner citra medis menggunakan pustaka pemrosesan citra.

Jika proses verifikasi identitas atau validasi berkas pada backend gagal (*Processing Failed*), server mengembalikan respons kesalahan HTTP 400 Bad Request atau 401 Unauthorized, yang diterjemahkan antarmuka menjadi notifikasi galat kepada pengguna. Sebaliknya, apabila pemrosesan awal berhasil (*Processing Successful*), backend mengeksekusi operasi penyimpanan berkas citra mentah (`saveImage`) ke dalam ember penyimpanan privat (*Supabase Storage*) pada jalur kepemilikan terisolasi, sekaligus mendaftarkan baris identitas analisis baru dengan status awal `processing` pada tabel basis data `analyses`. Backend selanjutnya mengirimkan respons HTTP 200/202 Accepted yang berisi pengenal unik analisis (*analysis_id*) kepada frontend (*Analysis Accepted*), menandakan bahwa berkas telah berhasil diterima dan siap dialirkan ke antrean inferensi model kecerdasan buatan.

---

#### 4.x.4 Sequence Diagram Segmentation

Gambar 4.x menunjukkan Sequence Diagram Segmentation yang memodelkan siklus lengkap proses inferensi segmentasi kecerdasan buatan dan visualisasi interpretasi Grad-CAM yang berjalan secara asinkron (*asynchronous*) pada sistem web PIXEL-T.

```
[Sisipkan Gambar: Sequence Diagram - Segmentation.drawio.png]
Gambar 4.x Sequence Diagram Segmentation
```

Alur segmentasi berkesinambungan dengan proses pengunggahan citra, di mana pengguna menekan tombol mulai analisis (`clickStartAnalysis`). Antarmuka pengguna (*Frontend*) melakukan validasi awal citra dan mengirimkan permintaan pengujian citra ke server backend Flask (`postAPIAnalysis`). Server backend memvalidasi kembali dimensi dan format citra. Apabila validasi tidak terpenuhi (*Validation Failed*), backend mengirimkan pesan penolakan yang ditampilkan langsung pada layar pengguna.

Apabila validasi dan otorisasi pengguna dinyatakan sah (*Validation Passed*), server backend menyimpan citra mentah ke Supabase Storage serta mencatat rekaman analisis baru dengan status awal `processing` pada basis data Supabase (`saveImageSaveRecord`). Segera setelah rekaman terdaftar, backend langsung mengembalikan respons HTTP 200/202 Accepted kepada frontend untuk mengonfirmasi bahwa tugas analisis telah diterima dalam antrean sistem, sehingga pengguna tidak mengalami pemblokiran antarmuka (*non-blocking UI*).

Secara bersamaan di latar belakang (*background worker*), backend memulai eksekusi pipa komputasi kecerdasan buatan (`startAnalysisPipeline`) menuju komponen *Pipeline AI*. Komponen ini menjalankan serangkaian tahapan inferensi yang mencakup prapemrosesan citra, segmentasi area nodul tiroid menggunakan model arsitektur *U-Net* dengan tulang punggung *ResNet50*, pascapemrosesan kontur poligon, perhitungan metrik luasan piksel, serta pembangkitan peta panas penjelasan visual menggunakan metode *Grad-CAM*.

Komponen *Pipeline AI* mengembalikan hasil komputasi (*Pipeline Result*) kepada backend. Apabila pemrosesan model berhasil diselesaikan (*Pipeline Successful*), backend mengunggah empat artefak keluaran (masker biner, kontur overlay segmentasi, peta panas Grad-CAM, dan overlay Grad-CAM) ke Supabase Storage, serta memperbarui rekaman basis data analisis dengan status `completed` beserta parameter metrik luasan nodul (`saveResultAndStatusCompleted`). Namun, apabila terjadi kegagalan komputasi pada model (*Pipeline Failed*), backend memperbarui status rekaman pada basis data menjadi `failed` dan mencatat kode galat yang terjadi (`clearResultsAndStatusFailed`).

Sementara proses latar belakang berlangsung, antarmuka pengguna melakukan pemantauan berkala (*polling*) status dengan mengirimkan permintaan `GET /api/analysis/<id>` (`getAPIAnalysis`) ke backend. Backend merespons dengan rincian status analisis terkini beserta tautan akses berbatas waktu (*signed URL*) ke berkas hasil segmentasi. Jika status yang diterima adalah gagal (*Status Failed*), antarmuka menampilkan pesan bahwa analisis tidak dapat diselesaikan. Sebaliknya, jika status terkonfirmasi selesai (*Status Successful*), antarmuka secara otomatis beralih ke halaman hasil dan menyajikan visualisasi citra segmentasi, peta Grad-CAM, serta metrik pengukuran nodul kepada pengguna.

---

#### 4.x.5 Sequence Diagram History

Gambar 4.x menunjukkan Sequence Diagram History yang menggambarkan alur penelusuran daftar riwayat pengujian, pemeriksaan rincian hasil analisis terdahulu, dan pengelolaan penghapusan sesi analisis pada sistem web PIXEL-T.

```
[Sisipkan Gambar: Sequence Diagram - History.drawio.png]
Gambar 4.x Sequence Diagram History
```

Proses penelusuran riwayat diawali saat pengguna membuka menu atau halaman riwayat (`openHistoryPage`). Halaman antarmuka pengguna (*History*) mengirimkan permintaan data riwayat analisis (`sendRequestHistory`) melalui endpoint `GET /api/history` kepada pengendali server (*HistoryController*). Pengendali server melakukan kueri ke basis data PostgreSQL Supabase (`getHistory`) untuk mengambil seluruh daftar analisis yang dimiliki secara eksklusif oleh pengguna yang sedang aktif, yang diurutkan dari waktu pembuatan terbaru (*created_at DESC*). Basis data mengembalikan kumpulan data riwayat (*Data History*), yang kemudian dikemas oleh pengendali server menjadi respons JSON (*Response History*) ke antarmuka pengguna.

Komponen antarmuka mengevaluasi data yang diterima melalui tiga kemungkinan kondisi (*Alt*). Apabila terjadi gangguan koneksi atau kegagalan server (*Failed to Load*), sistem menampilkan status kesalahan (*Display Error State*). Apabila kueri berhasil tetapi pengguna belum pernah melakukan pengujian citra (*Empty List*), sistem menampilkan halaman status kosong (*No Analysis History Yet*). Sedangkan apabila rekaman data ditemukan (*List Available*), sistem menyajikan tabel daftar riwayat analisis yang memuat nama berkas, status pemrosesan, tanggal analisis, dan cuplikan gambar (*Show List History*).

Pada diagram, terdapat blok interaksi opsional pertama (*Opt: Users Browse and Open Results*), di mana pengguna dapat mencari atau memilih salah satu item sesi riwayat (`searchResult`). Antarmuka mengirimkan permintaan detail sesi (`sendRequestAnalysis`) via endpoint `GET /api/analysis/<id>` ke pengendali backend. Pengendali server mengambil rekaman detail dari basis data (`getAnalysisResult`), men-generate tautan privat bertanda tangan (*signed URL*) untuk seluruh aset citra, dan mengembalikannya ke frontend (*Get History Detail*), sehingga pengguna dapat melihat kembali laporan visual segmentasi dan metrik nodul secara lengkap (*Show Result*).

Blok interaksi opsional kedua (*Opt: The User Chooses to Delete History*) memodelkan penghapusan rekaman riwayat. Saat pengguna menekan ikon hapus pada salah satu sesi (`clickClearHistory`), antarmuka memunculkan kotak dialog konfirmasi ("Delete this Analysis Session?"). Jika pengguna memilih membatalkan tindakan (`clickCancel`), dialog ditutup tanpa ada data yang dihapus (*Close Dialog*). Namun, apabila pengguna mengonfirmasi persetujuan hapus (`clickYesDelete`), antarmuka mengirimkan permintaan `DELETE /api/history/<id>` (`sendRequestDelete`) ke backend. Pengendali backend memvalidasi kepemilikan data, menghapus rekaman terkait pada tabel basis data `analyses` (`verificationDelete`), serta menghapus berkas-berkas aset citra terkait pada Supabase Storage. Backend kemudian mengembalikan status hasil penghapusan (*Deletion Result*), dan antarmuka memperbarui daftar riwayat dengan menghapus baris item tersebut dari layar pengguna.

---

#### 4.x.6 Sequence Diagram Doctor Profile

Gambar 4.x menunjukkan Sequence Diagram Doctor Profile yang memodelkan alur pemuatan informasi profil dokter, penyajian ringkasan statistik analisis, serta proses pengubahan dan penyimpanan data profil dokter pada sistem web PIXEL-T.

```
[Sisipkan Gambar: Sequence Diagram - Doctor Profile.drawio.png]
Gambar 4.x Sequence Diagram Doctor Profile
```

Alur dimulai saat pengguna mengakses halaman profil dokter (`accessProfilePage`). Komponen antarmuka pengguna (*Frontend*) segera memanggil fungsi `fetchDoctorProfile` pada layanan profil (*Profile Service*), yang kemudian melakukan kueri langsung ke tabel `doctor_profiles` pada Supabase (`selectDoctorProfiles`) berdasarkan identitas unik pengguna (*user_id*). Apabila baris profil belum ditemukan di dalam tabel basis data, layanan secara cerdas memanfaatkan data cadangan (*Fallback User Metadata*) yang tersimpan pada metadata akun Supabase Auth pengguna untuk mengisi informasi awal profil dokter.

Bersamaan dengan pemuatan profil dasar, komponen antarmuka juga memanggil endpoint `GET /api/history` ke server *Backend* (`getAPIHistory`) untuk mengambil riwayat pengujian citra pengguna dari basis data Supabase (`queryUserHistory`). Log riwayat analisis tersebut dikembalikan ke antarmuka (*Analysis History Log*), di mana sistem secara otomatis menghitung metrik agregat seperti total pengujian yang dilakukan, tingkat keberhasilan segmentasi, dan rasio deteksi nodul. Pengguna selanjutnya disajikan tampilan lengkap halaman profil yang memadukan identitas personal, informasi profesional, serta kartu ringkasan statistik klinis (*View Profile & Statistical Summary*).

Ketika dokter bermaksud memperbarui data profilnya, pengguna membuka modal formulir pengeditan, menyunting informasi yang diinginkan, dan menekan tombol simpan (`editProfileClickSave`). Komponen antarmuka meneruskan data formulir baru ke *Profile Service* (`saveDoctorProfile`). Layanan profil secara ketat melakukan validasi format data (*Validate Profile Data*) untuk memastikan keabsahan nama lengkap, struktur teks, dan integritas data riwayat pendidikan serta pengalaman.

Jika masukan tidak memenuhi aturan validasi (*Validation Failed*), layanan mengembalikan pesan galat dan antarmuka menampilkan notifikasi kesalahan validasi pada formulir modal (*Display Validation Error Messages*). Sebaliknya, apabila data dinyatakan valid (*Validation Passed*), layanan profil mengeksekusi operasi `upsert` ke tabel basis data `doctor_profiles` di Supabase (`upsertDoctorProfile`), yang akan memperbarui rekaman lama atau menyisipkan rekaman baru berdasarkan kunci unik pengguna (*user_id*), sekaligus menyinkronkan nama terbaru ke metadata Supabase Auth. 

Apabila operasi penyimpanan ke basis data mengalami kendala jaringan (*Save Failed*), sistem memunculkan pemberitahuan gagal simpan pada modal formulir. Namun, apabila penyimpanan sukses diselesaikan (*Save Successful*), antarmuka menutup modal formulir, memperbarui status tampilan profil pada halaman utama, dan menampilkan notifikasi keberhasilan pembaruan data dokter (*Display Success Message*).

---

#### 4.x.7 Sequence Diagram Sign Out

Gambar 4.x menunjukkan Sequence Diagram Sign Out yang memodelkan alur pemutusan sesi kerja aktif pengguna dan pembersihan status autentikasi dari sistem web PIXEL-T.

```
[Sisipkan Gambar: Sequence Diagram - Sign Out.drawio.png]
Gambar 4.x Sequence Diagram Sign Out
```

Proses keluar dari sistem diawali ketika pengguna yang sedang berada di dalam aplikasi menekan tombol atau menu keluar (*Sign Out*) pada bilah navigasi antarmuka induk aplikasi (*AppShell*). Untuk mencegah tindakan keluar yang tidak disengaja, komponen antarmuka terlebih dahulu memunculkan kotak dialog konfirmasi kepada pengguna (*Show Sign Out Confirmation*). Pengguna kemudian memberikan persetujuan keluar dengan menekan tombol konfirmasi pada dialog (`Confirm Sign Out`).

Antarmuka *AppShell* merespons persetujuan tersebut dengan memanggil fungsi `signOut` pada lapisan *AuthContext*, yang kemudian meneruskan pemanggilan fungsi `logoutUser` (`signOutUser`) menuju *AuthService*. Pada lapisan layanan autentikasi, sistem mengeksekusi fungsi terminasi sesi resmi dari SDK Supabase, yaitu `supabase.auth.signOut` (`supabaseAuthSignOut`), untuk membatalkan keabsahan token JWT dan mengakhiri sesi aktif pengguna pada server Supabase Auth.

Server Supabase Auth merespons dengan mengembalikan status hasil terminasi sesi (`{ error : string | null }`). Layanan autentikasi meneruskan respons tersebut ke *AuthContext*. *AuthContext* selanjutnya membersihkan variabel status pengguna dan status sesi menjadi bernilai kosong/null (`Sign Out Success`), yang secara serentak menghapus kredensial tersimpan pada *Local Storage* peramban.

Pembersihan sesi pada konteks global secara otomatis memicu penjaga rute privat (*ProtectedRoute*) pada aplikasi web. Antarmuka *AppShell* menutup seluruh sesi kerja aktif dan mengalihkan navigasi pengguna secara langsung kembali ke halaman masuk (*Go to the Sign In Page* / `/login`), sehingga seluruh rute dan data privat di dalam sistem kembali terlindungi dari akses tanpa izin.

