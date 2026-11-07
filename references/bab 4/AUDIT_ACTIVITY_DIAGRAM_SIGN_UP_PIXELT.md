# AUDIT ACTIVITY DIAGRAM SIGN UP — SISTEM PIXEL-T

**Dokumen Pendukung Bab IV Skripsi S1**
Disusun berdasarkan analisis implementasi aktual kode sumber web PIXEL-T. Berkas audit ini melengkapi hasil revisi `ACTIVITY_DIAGRAM_SIGN_UP_PIXELT_FINAL.drawio` / `.png` dan dokumen penjelasan `PENJELASAN_ACTIVITY_DIAGRAM_SIGN_UP_PIXELT_FINAL.md`.

Status akhir: **TERVALIDASI DENGAN REVISI** (lihat Bagian K).

---

## A. Ringkasan Eksekutif

Audit ini memvalidasi kesesuaian *Activity Diagram* Sign Up PIXEL-T terhadap implementasi aktual sistem, dengan penekanan pada pemisahan jalur pendaftaran publik (khusus Dokter) dan pembuatan akun Admin melalui Supabase Admin API.

Temuan utama:

1. **Alur diagram sesuai implementasi.** Aktivitas dan percabangan pada diagram final — formulir enam bidang, validasi lokal, panggilan tunggal `signUp()` → `supabase.auth.signUp()`, pembuatan `auth.users`, *trigger* `handle_new_doctor_signup` yang memasukkan baris `doctor_profiles` berstatus `pending`, dua *decision node* (keberadaan sesi dan konfirmasi email), loop kesalahan, serta pengalihan ke halaman `/login` — tercermin pada `Register.tsx`, `AuthContext.tsx`, `services/auth.ts`, serta migrasi database 004, 007, dan 008.
2. **Diagram revisi sebelumnya memperbaiki cacat.** `ROLE_ADMIN_REVISED.drawio` memiliki *decision node* `a8` (instruksi konfirmasi email) yang terisolasi tanpa edge masuk/keluar dan tidak memiliki *decision node* kegagalan `signUp`; `FINAL_REVISED.drawio` memiliki alur linier tanpa percabangan, *start/end* berbentuk persegi (bukan standar UML), dan *decision* persegi. Diagram `FINAL_AUDITED` memperbaiki seluruhnya.
3. **Tidak ada aktivitas fiktif.** Setiap elemen diagram memiliki penerapan nyata pada kode sumber. Tidak ada aktivitas pembuatan akun Admin, persetujuan Admin, atau aktivitas klinis dalam alur Sign Up karena berada di luar lingkup pendaftaran publik.
4. **Admin tidak berada dalam alur pendaftaran publik.** Admin dibuat melalui Supabase Admin API (`raw_app_meta_data.role = 'admin'`) dan tidak memiliki baris pada `doctor_profiles`, sehingga tidak dimodelkan sebagai aktivitas utama, hanya sebagai catatan pendukung.
5. **Persetujuan Admin (approve/reject) di luar alur Sign Up.** Merupakan use case terpisah yang terjadi setelah pendaftaran, sehingga tidak dimodelkan pada diagram ini.

---

## B. Inventarisasi Sumber

### B.1 Frontend (React 18 + TypeScript + Vite)

| Berkas | Peran terhadap audit Sign Up |
|--------|------------------------------|
| `frontend/src/routes/AppRoutes.tsx` | Daftar rute resmi; `/register` dilindungi `PublicOnlyRoute` |
| `frontend/src/pages/auth/Register.tsx` | Halaman pendaftaran: enam bidang formulir, validasi lokal, `handleSubmit`, layar sukses + tautan ke `/login` |
| `frontend/src/context/AuthContext.tsx` | `signUp`: pemanggilan `registerUser`, penyimpanan sesi, `role = 'doctor'`, `account_status = 'pending'`, cabang `requiresEmailConfirmation` |
| `frontend/src/services/auth.ts` | `registerUser`: satu panggilan `supabase.auth.signUp` dengan metadata profesional; `formatAuthError`; `existingAccountHint` (anti-enumerasi) |
| `frontend/src/components/auth/PublicOnlyRoute.tsx` | Penjaga rute publik (`/login`, `/register`); redirect pengguna terautentikasi sesuai peran |
| `frontend/src/lib/supabase.ts` | Klien Supabase Auth (anon key), tidak menampilkan service-role key |

### B.2 Basis Data (PostgreSQL / Supabase)

| Berkas | Peran terhadap audit Sign Up |
|--------|------------------------------|
| `database/migrations/004_create_doctor_profiles.sql` | Tabel `doctor_profiles` + RLS |
| `database/migrations/007_add_role_and_account_status.sql` | Kolom `role` dan `account_status`; admin disimpan pada `raw_app_meta_data.role`, tidak ada tabel `admins` |
| `database/migrations/008_create_doctor_profile_trigger.sql` | *Trigger* `handle_new_doctor_signup` (`AFTER INSERT` pada `auth.users`): `INSERT doctor_profiles` (`role='doctor'`, `account_status='pending'`), mengecualikan Admin, gagal dicatat sebagai `WARNING` tanpa membatalkan pendaftaran |

### B.3 Ujian Unit

| Berkas | Hasil |
|--------|-------|
| `frontend/src/pages/auth/Register.test.tsx` | 25/25 tes lolos (bersama `auth.test.ts`) |
| `frontend/src/services/auth.test.ts` | 25/25 tes lolos |

### B.4 Dokumen Referensi yang Dibandingkan

| Berkas | Catatan |
|--------|---------|
| `references/bab 4/ACTIVITY_DIAGRAM_SIGN_UP_PIXELT_ROLE_ADMIN_REVISED.drawio` | Revisi peralur sebelumnya, disusul oleh FINAL |
| `references/bab 4/ACTIVITY_DIAGRAM_SIGN_UP_PIXELT_FINAL_REVISED.drawio` | Revisi linier sebelumnya, disusul oleh FINAL |
| `references/bab 4/PENJELASAN_ACTIVITY_DIAGRAM_SIGN_UP_PIXELT_FINAL.md` | Dokumen penjelasan akademik pendamping |

---

## C. Peta Implementasi

| Elemen diagram (Gambar 4.x) | Lokasi kode | Keterangan |
|-----------------------------|-------------|------------|
| Membuka halaman `/register` | `AppRoutes.tsx` rute `/register` + `PublicOnlyRoute` | Halaman publik; pengguna terautentikasi diarahkan ke halaman sesuai peran |
| Mengisi formulir pendaftaran | `Register.tsx` | Enam bidang: `fullName`, `email`, `password`, `confirmPassword`, `hospitalName`, `doctorSpecialty` |
| Memvalidasi input | `Register.tsx:35-79` (`handleSubmit`) | Nama wajib, email format, rumah sakit wajib, spesialisasi wajib, kata sandi ≥ 6, konfirmasi cocok |
| Decision "Input valid?" | `Register.tsx` early `return` | [Ya] lanjut ke `signUp`; [Tidak] tampilkan pesan kesalahan |
| [Tidak] → pesan kesalahan → kembali formulir | `Register.tsx:40-79` | `setErrorMessage`, lalu `return` tanpa memanggil `signUp` |
| Memanggil `signUp()` → `supabase.auth.signUp()` | `AuthContext.tsx:186` → `services/auth.ts:146` | Satu panggilan `signUp`; metadata profesional dikirim sebagai `user_metadata` |
| Decision "Permintaan signUp berhasil?" | `services/auth.ts:165-175` (`result.error`) | [Ya] lanjut ke pembuatan akun; [Tidak] tampilkan pesan kesalahan |
| Supabase membuat `auth.users` (+ `user_metadata`) | Supabase Auth | Berisi `full_name`, `hospital`, `hospital_name`, `primary_specialty`, `specialty`, `doctor_profile` |
| *Trigger* `handle_new_doctor_signup` → `INSERT doctor_profiles` (`role='doctor'`, `account_status='pending'`) | Migrasi `008` baris 34-70 | `AFTER INSERT` pada `auth.users`; Admin dikecualikan; idempoten; kegagalan `WARNING` tidak membatalkan pendaftaran |
| Decision "Sesi dikembalikan?" | `AuthContext.tsx:191-203` | [Ya] sesi dikembalikan; [Tidak] konfirmasi email diperlukan |
| [Ya] → perbarui status autentikasi | `AuthContext.tsx:194-196` | `role = 'doctor'`, `account_status = 'pending'` |
| [Tidak] → instruksi konfirmasi email | `AuthContext.tsx:200-203` | `requiresEmailConfirmation: true` |
| Pesan pendaftaran berhasil (menunggu persetujuan admin) | `AuthContext.tsx:197, 201`; `Register.tsx` layar sukses | Kedua cabang bergabung pada pesan yang sama |
| Mengakses halaman `/login` → akhir | `Register.tsx` tautan "Masuk ke PIXEL-T" ke `/login` | Tindakan manual pengguna melalui layar sukses, bukan *redirect* otomatis |

---

## D. Matriks Hak Akses (Konteks Sign Up)

Legenda: **Y** = diizinkan; **N** = ditolak.

| Kondisi pengguna | Dapat Sign Up? | Alasan |
|------------------|----------------|--------|
| Calon pengguna (belum login) | Y | `/register` PublikOnlyRoute, tidak ada sesi aktif |
| Dokter `pending` | N | Sudah memiliki akun; dialihkan ke `/login` |
| Dokter `rejected` | N | Sudah memiliki akun; dialihkan ke `/login` |
| Dokter `approved` | N | Sudah memiliki akun; dialihkan ke `/login` |
| Admin | N | Dibuat eksternal via Supabase Admin API; tidak ada jalur pendaftaran publik |

---

## E. Matriks Audit Activity Diagram

Seluruh elemen diagram periksa terhadap kode sumber.

| # | Elemen diagram | Status | Bukti implementasi |
|---|----------------|--------|--------------------|
| 1 | Membuka halaman `/register` | ✅ TERIMPLEMENTASI | `AppRoutes.tsx` rute `/register` dengan `PublicOnlyRoute` |
| 2 | Mengisi formulir pendaftaran (6 bidang) | ✅ TERIMPLEMENTASI | `Register.tsx`: `fullName`, `email`, `password`, `confirmPassword`, `hospitalName`, `doctorSpecialty` |
| 3 | Memvalidasi input | ✅ TERIMPLEMENTASI | `Register.tsx:35-79`: nama, email format, rumah sakit, spesialisasi, kata sandi ≥ 6, konfirmasi cocok |
| 4 | Decision "Input valid?" | ✅ TERIMPLEMENTASI | `Register.tsx` melakukan `return` awal saat validasi gagal, tidak memanggil `signUp` |
| 5 | [Tidak] → pesan kesalahan → kembali formulir | ✅ TERIMPLEMENTASI | `setErrorMessage`, ulangi pengisian |
| 6 | Memanggil `signUp()` → `supabase.auth.signUp()` | ✅ TERIMPLEMENTASI | `AuthContext.tsx:186` → `services/auth.ts:146`, satu panggilan |
| 7 | Decision "Permintaan signUp berhasil?" | ✅ TERIMPLEMENTASI | `services/auth.ts:165-175`: pemeriksaan `result.error` |
| 8 | Supabase membuat `auth.users` (+ `user_metadata`) | ✅ TERIMPLEMENTASI | Supabase Auth; metadata profesional disimpan sebagai `user_metadata` |
| 9 | *Trigger* `handle_new_doctor_signup` → `doctor_profiles` (`role='doctor'`, `account_status='pending'`) | ✅ TERIMPLEMENTASI | Migrasi `008` baris 34-70; Admin dikecualikan; idempoten; `WARNING` pada kegagalan |
| 10 | Decision "Sesi dikembalikan?" | ✅ TERIMPLEMENTASI | `AuthContext.tsx:191-203`: cabang `session` vs `requiresEmailConfirmation` |
| 11 | [Ya] → perbarui status (`role=doctor`, `account_status=pending`) | ✅ TERIMPLEMENTASI | `AuthContext.tsx:194-196` |
| 12 | [Tidak] → instruksi konfirmasi email | ✅ TERIMPLEMENTASI | `AuthContext.tsx:200-203` |
| 13 | Merge → pesan pendaftaran berhasil (menunggu persetujuan admin) | ✅ TERIMPLEMENTASI | `AuthContext.tsx:197, 201` |
| 14 | Mengakses halaman `/login` → node akhir | ✅ TERIMPLEMENTASI | `Register.tsx` tautan ke `/login` pada layar sukses |

---

## F. Audit Relasi Antar-Aktivitas dan Percabangan

| Relasi | Arah | Status | Analisis |
|--------|------|--------|----------|
| Validasi lolos | d1 → a4 [Ya] | ✅ VALID | Validasi lokal lolos, lanjut ke `signUp()` |
| Validasi gagal | d1 → aerr [Tidak] | ✅ VALID | Pesan kesalahan ditampilkan, pengguna kembali ke formulir |
| Loop kesalahan validasi | aerr → a2 | ✅ VALID | `handleSubmit` kembali ke awal formulir setelah `setErrorMessage` |
| Hasil `signUp` diperiksa | a4 → d3 | ✅ VALID | `registerUser` mengembalikan `error` atau `null` |
| `signUp` berhasil | d3 → a5 [Ya] | ✅ VALID | Tanpa error, lanjut ke pembuatan `auth.users` |
| `signUp` gagal | d3 → aerr [Tidak] | ✅ VALID | Error ditampilkan, pengguna dapat mencoba kembali |
| Pembuatan profil | a5 → a6 → d2 | ✅ VALID | *Trigger* 008 menjalankan `INSERT doctor_profiles` kemudian pemeriksaan sesi |
| Sesi ada | d2 → a7 [Ya] | ✅ VALID | `AuthContext.signUp` menyimpan sesi dan status |
| Tidak ada sesi | d2 → a8 [Tidak] | ✅ VALID | `requiresEmailConfirmation`, instruksi konfirmasi email |
| Penggabungan cabang | a7 → a9; a8 → a9 | ✅ VALID | Kedua cabang konvergen pada pesan sukses yang sama |
| Akhir proses | a9 → a10 → end | ✅ VALID | Pengguna mengakses `/login`, mencapai *final node* |

> Catatan perbaikan: pada `ROLE_ADMIN_REVISED.drawio`, node `a8` (instruksi konfirmasi email) tidak memiliki edge masuk dari d2 `[Tidak]` dan tidak ada edge keluar ke a9, sehingga cabang konfirmasi email terisolasi. Diagram `FINAL_AUDITED` memperbaiki dengan menambahkan edge e14 dan e16, serta menambahkan *decision node* d3 ("Permintaan signUp berhasil?") yang hilang pada revisi sebelumnya.

---

## G. Temuan Ketidaksesuaian

### G.1 Kritis

**G-1 — Cabang konfirmasi email terisolasi pada revisi sebelumnya.** `ROLE_ADMIN_REVISED.drawio` memiliki node `a8` "Menampilkan instruksi konfirmasi email" tanpa edge masuk dari `d2 [Tidak]` dan tanpa edge keluar ke `a9`. Secara alur kontrol, node tersebut tidak tercapai dan tidak dapat menyelesaikan alur. **Perbaikan:** `FINAL_AUDITED` menambahkan edge `d2 → a8 [Tidak]` dan `a8 → a9`.

**G-2 — Tidak ada *decision node* kegagalan `signUp` pada revisi sebelumnya.** `ROLE_ADMIN_REVISED.drawio` mengalir langsung dari pemanggilan `signUp` ke pembuatan `auth.users` tanpa memeriksa apakah permintaan berhasil. `FINAL_AUDITED` menambahkan `d3 "Permintaan signUp berhasil?"` dengan cabang `[Ya]` dan `[Tidak]`.

**G-3 — Alur linier dan node non-UML pada `FINAL_REVISED.drawio`.** Diagram sebelumnya berupa alur linier tanpa percabangan validasi/error/sesi, *decision* "Email sudah terdaftar?" berbentuk persegi (bukan diamond), *start* dan *end* berbentuk persegi (bukan *initial node* terisi dan *final node* bullseye). **Perbaikan:** `FINAL_AUDITED` menggunakan persegi panjang dengan sudut melingkar untuk aktivitas, diamond untuk keputusan, *initial node* lingkaran terisi hitam, dan *final node* bullseye.

### G.2 Tinggi

**G-4 — Aktivitas ambigu digabung pada revisi sebelumnya.** `FINAL_REVISED.drawio` menggabungkan pembuatan `auth.users`, pembuatan profil, dan status `pending` menjadi satu aktivitas "Menyimpan ke Supabase Auth (status pending)". **Perbaikan:** `FINAL_AUDITED` memisahkan menjadi aktivitas a5 (`auth.users`), a6 (*trigger* profil `pending`), dan d2 (sesi).

### G.3 Sedang

**G-5 — Jenis error Supabase tidak dibedakan pada diagram.** `formatAuthError` membedakan email terdaftar, kata sandi lemah, rate limit, email tidak valid, dan sebagainya, tetapi diagram menggabungkan semua sebagai cabang `[Tidak]` pada d3. Ini layak untuk *activity diagram* tingkat tinggi; rincian pesan error dikomentari dalam catatan diagram.

**G-6 — Tidak ada perbedaan pesan untuk akun yang sudah terdaftar.** Supabase sengaja mengaburkan respons duplikasi alamat email (anti-enumerasi melalui `existingAccountHint`), sehingga pesan pengguna tetap netral. Diagram tidak menampilkan node terpisah untuk kasus ini, sesuai kebijakan keamanan.

### G.4 Rendah

**G-7 — `/login` adalah tindakan manual, bukan *redirect* otomatis.** Node a10 "Mengakses halaman /login" merepresentasikan tautan "Masuk ke PIXEL-T" pada layar sukses `Register.tsx`; sistem tidak memindahkan pengguna secara otomatis ke `/login` setelah pendaftaran berhasil.

**G-8 — Persetujuan Admin tidak dimodelkan.** Approve/reject akun dokter adalah use case terpisah yang terjadi setelah pendaftaran dan tidak termasuk dalam alur Sign Up. Hal ini sengaja tidak dimodelkan.

---

## H. Rekomendasi Diagram

1. Gunakan `ACTIVITY_DIAGRAM_SIGN_UP_PIXELT_FINAL.drawio` / `.png` sebagai *Activity Diagram* Sign Up Bab IV (Gambar 4.x).
2. Pertahankan tiga karakteristik diagram: minimalis, monokrom, dan standar UML (lingkaran terisi untuk *initial node*, bullseye untuk *final node*, diamond untuk *decision*, guard label `[Ya]` / `[Tidak]`).
3. Jangan menambahkan aktivitas Admin atau persetujuan Akun Dokter ke dalam diagram Sign Up; keduanya berada di luar alur pendaftaran publik.
4. Jika pembimbing mengharuskan perbedaan jenis error Supabase, sampaikan sebagai catatan narasi (bukan node tambahan) untuk menjaga diagram tetap ringkas.
5. Pertahankan catatan pendukung tentang *PublicOnlyRoute*, pendaftaran publik hanya untuk Dokter, dan pembuatan Admin via Supabase Admin API tanpa baris `doctor_profiles`.

---

## I. Penjelasan Akademik

*Activity Diagram* Sign Up PIXEL-T (Gambar 4.x) memodelkan proses pendaftaran akun Dokter melalui halaman `/register`, dimulai dari *initial node* (lingkaran terisi hitam) yang menandai titik awal alur.

Pertama, pengguna membuka halaman `/register`, yang merupakan rute publik dilindungi oleh `PublicOnlyRoute`. Pengguna yang sudah terautentikasi akan diarahkan ke halaman sesuai perannya (Admin ke `/admin`, Dokter yang disetujui ke `/dashboard`), sehingga halaman pendaftaran hanya tersedia bagi calon pengguna yang belum login. Selanjutnya, pengguna mengisi formulir pendaftaran yang mencakup enam bidang yang benar-benar tersedia pada `Register.tsx`: nama lengkap, email, kata sandi, konfirmasi kata sandi, nama rumah sakit, dan spesialisasi dokter. Tidak ada bidang tambahan yang dimodelkan karena tidak ditemukan pada implementasi.

Setelah formulir diisi, sistem melakukan validasi lokal sebelum permintaan dikirim ke layanan autentikasi: nama lengkap wajib, email wajib dan memenuhi format email, nama rumah sakit wajib, spesialisasi dokter wajib, kata sandi wajib minimal 6 karakter, dan konfirmasi kata sandi harus cocok. *Decision node* "Input valid?" memercabang alur: **[Ya]** lanjut ke pembuatan akun; **[Tidak]** sistem menampilkan pesan kesalahan dan mengembalikan pengguna ke formulir untuk memperbaiki input, mencerminkan perilaku `handleSubmit` yang melakukan early `return` saat validasi gagal.

Apabila input valid, sistem memanggil `signUp()` yang menyatukan panggilan tunggal `supabase.auth.signUp()` melalui `services/auth.ts`. *Decision node* "Permintaan signUp berhasil?" kemudian memeriksa apakah panggilan tersebut mengembalikan error (dicek pada `registerUser` dalam `services/auth.ts`). **[Ya]** — tidak ada error, alur lanjut ke pembuatan akun; **[Tidak]** — terdapat error (misalnya email sudah terdaftar, kata sandi lemah, atau rate limit), sistem menampilkan pesan kesalahan dan mengembalikan pengguna ke formulir.

Apabila permintaan berhasil, Supabase Auth membuat baris baru pada `auth.users` beserta `user_metadata` yang berisi informasi profesional (nama lengkap, rumah sakit, spesialisasi, dll.). Setelah akun dibuat, *trigger database* `handle_new_doctor_signup` (migrasi 008) secara otomatis memasukkan baris baru ke `doctor_profiles` dengan `role = 'doctor'` dan `account_status = 'pending'`. *Trigger* ini secara eksplisit melewati akun Admin sehingga Admin tidak memiliki baris pada `doctor_profiles`; kegagalan pembuatan profil dicatat sebagai `WARNING` dan tidak membatalkan pendaftaran.

Setelah profil Dokter dibuat, terdapat *decision node* "Sesi dikembalikan?" yang memisahkan dua kondisi pada `AuthContext.signUp`: **[Ya]** sesi autentikasi dikembalikan, sistem menyimpan status dengan `role = 'doctor'` dan `account_status = 'pending'`; **[Tidak]** sesi tidak dikembalikan (karena konfirmasi email diperlukan atau kebijakan Supabase Auth), sistem menampilkan instruksi konfirmasi email. Kedua cabang bergabung (*merge*) pada aktivitas "Menampilkan pesan pendaftaran berhasil (menunggu persetujuan admin)".

Terakhir, sistem menampilkan pesan pendaftaran berhasil yang menyatakan akun telah dibuat dan menunggu persetujuan administrator. Pengguna kemudian mengakses halaman `/login` melalui tautan pada layar sukses untuk masuk ke aplikasi, lalu alur mencapai *final node* (lingkaran bundar dengan titik hitam di tengahnya) sesuai notasi UML standar.

Catatan pendukung pada diagram menyatakan pendaftaran publik hanya untuk Dokter, dan Admin dibuat melalui Supabase Admin API (`app_metadata.role = 'admin'`) tanpa baris pada `doctor_profiles`. Informasi ini bersifat pendukung dan tidak dimodelkan sebagai aktivitas utama karena pembuatan akun Admin berada di luar alur pendaftaran publik.

---

## J. Keterbatasan Audit

1. **Audit berbasis analisis statis kode sumber, bukan pengujian runtime.** Tidak ada pengujian browser (E2E), pengujian beban, atau pengujian penetrasi yang dijalankan. Seluruh klaim kesesuaian didasarkan pada pembacaan berkas yang tercantum pada Bagian B.
2. **Tidak ada akses ke lingkungan Supabase produksi.** Konfigurasi `app_metadata` Admin dan data `doctor_profiles` tidak diperiksa secara langsung; kesimpulan diambil dari migrasi SQL dan kode otorisasi.
3. **Validasi visual diagram terbatas.** Draw.io Desktop dan *engine* UML resmi tidak tersedia pada lingkungan audit. Validasi diagram dilakukan melalui (a) pemeriksaan *well-formedness* XML dengan `xml.etree.ElementTree`, (b) verifikasi bahwa setiap `source`/`target` edge merujuk ID node yang ada, dan (c) pemeriksaan berkas PNG (`ACTIVITY_DIAGRAM_SIGN_UP_PIXELT_FINAL.png`, 1720×2020) dengan `PIL.Image.verify()`.
4. **Kredensial tidak diungkap.** Audit tidak membaca, menyalin, atau menampilkan *service-role key*, kata sandi, atau token apa pun.
5. **Tidak ada modifikasi kode aplikasi.** Audit hanya menghasilkan artefak dokumentasi dan diagram baru; tidak ada berkas aplikasi, migrasi, atau konfigurasi yang diubah.

---

## K. Status Akhir

**Status: TERVALIDASI DENGAN REVISI.**

| Kriteria | Hasil |
|----------|-------|
| Seluruh aktivitas dan *decision node* pada diagram memiliki dasar implementasi | ✅ 14/14 elemen terverifikasi |
| Percabangan validasi, kegagalan `signUp`, sesi, dan konfirmasi email lengkap | ✅ Lengkap |
| Node awal dan akhir standar UML (*initial node* terisi, *final node* bullseye) | ✅ Terdapat |
| Tidak ada aktivitas fiktif di luar lingkup Sign Up | ✅ Tidak ditemukan |
| Admin di luar alur pendaftaran publik (benar) | ✅ Tercermin pada catatan diagram |
| Persetujuan Admin di luar lingkup diagram | ✅ Sengaja tidak dimodelkan |
| Validasi visual oleh *engine* UML resmi | ⚠️ Terbatas (lihat J-3) |
| Pengujian runtime / browser (E2E) | ⚠️ Tidak dilakukan (lihat J-1) |

**Keputusan:** `ACTIVITY_DIAGRAM_SIGN_UP_PIXELT_FINAL.drawio` / `.png` **layak** digunakan sebagai *Activity Diagram* Sign Up Bab IV (Gambar 4.x), dengan catatan keterbatasan validasi visual dan ketiadaan pengujian runtime sebagaimana diuraikan pada Bagian J. Diagram revisi sebelumnya (`ROLE_ADMIN_REVISED.drawio` dan `FINAL_REVISED.drawio`) dinyatakan **digantikan** oleh dokumen ini.

---

*Audit dilaksanakan melalui analisis statis terhadap kode sumber aktual web PIXEL-T. Seluruh temuan dapat dilacak ke berkas yang tercantum pada Bagian B. Tidak ada kode aplikasi yang diubah.*