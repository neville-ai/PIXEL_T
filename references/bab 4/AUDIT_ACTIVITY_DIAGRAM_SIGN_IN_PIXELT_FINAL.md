# AUDIT ACTIVITY DIAGRAM SIGN IN — SISTEM PIXEL-T

**Dokumen Pendukung Bab IV Skripsi S1**
Disusun berdasarkan analisis implementasi aktual kode sumber web PIXEL-T.

Status akhir: **TERVALIDASI — FINAL**

---

## A. Ringkasan Eksekutif

Audit ini memvalidasi kesesuaian *Activity Diagram* Sign In PIXEL-T terhadap implementasi aktual sistem dua peran (Admin + Dokter). Diagram final memodelkan alur lengkap dari pembukaan halaman `/login` hingga pengalihan ke halaman tujuan, termasuk seluruh percabangan yang diterapkan dalam kode: validasi input, autentikasi Supabase, pengecekan role mismatch, penentuan route berdasarkan role (`/admin` vs `/dashboard`), dan penanganan status akun pending/rejected.

Temuan utama:

1. **Diagram baru dibuat dari nol berdasarkan audit independen.** Diagram Sign In sebelumnya (`FINAL_REVISED.drawio` dan `ROLE_ADMIN_REVISED.drawio`) memiliki cacat struktural serius: node start/end berbentuk persegi (bukan notasi UML), decision node berbentuk persegi (bukan belah ketupat), dan beberapa node terisolasi tanpa edge masuk/keluar. Diagram baru `FINAL.drawio` memperbaiki seluruh cacat tersebut.
2. **Alur diagram sesuai implementasi.** Validasi lokal (email wajib, password wajib), panggilan `signIn()` → `supabase.auth.signInWithPassword()`, update session/role/status di AuthContext, pengecekan role mismatch, pengecekan role admin, pengecekan account_status pending/rejected, dan pengalihan ke route yang sesuai — seluruhnya tercermin dalam diagram.
3. **Tidak ada aktivitas fiktif.** Setiap elemen diagram memiliki penerapan nyata pada kode sumber. Fitur Remember Me dimodelkan sebagai catatan (bukan aktivitas) karena hanya menyimpan email di localStorage tanpa memengaruhi sesi autentikasi. Reset Password dinyatakan sebagai use case terpisah dalam catatan.
4. **Role selector adalah konteks login, bukan sumber otorisasi.** Diagram membedakan antara role yang dipilih pengguna (dropdown) dan role aktual yang ditentukan oleh `app_metadata.role` (admin) atau `doctor_profiles` (dokter). Percabangan "Role cocok dengan akun?" merefleksikan mekanisme ini.

---

## B. Inventarisasi Sumber

### B.1 Frontend

| Berkas | Baris | Peran |
|--------|-------|-------|
| `frontend/src/pages/auth/Login.tsx` | 1–521 | Halaman login: role selector, form email/password, Remember Me, submit, redirect logic |
| `frontend/src/context/AuthContext.tsx` | 132–173 | `signIn()`: panggilan `loginUser()`, set user/session, resolve role/status, role mismatch check |
| `frontend/src/services/auth.ts` | 195–225 | `loginUser()`: `signInWithPassword()`, error handling, formatAuthError |
| `frontend/src/routes/AppRoutes.tsx` | 26–33 | Rute `/login` dilindungi `PublicOnlyRoute` |
| `frontend/src/components/auth/PublicOnlyRoute.tsx` | 1–41 | Redirect authenticated users; allow pending/rejected |
| `frontend/src/components/auth/ProtectedRoute.tsx` | 1–41 | Blokir pending/rejected dari fitur klinis |
| `frontend/src/components/auth/AdminRoute.tsx` | 1–39 | Hanya admin yang bisa akses `/admin` |
| `frontend/src/lib/openingTimeline.ts` | 46–176 | Remember Me (localStorage email only), opening animation state |

### B.2 Basis Data

| Berkas | Peran |
|--------|-------|
| `database/migrations/007_add_role_and_account_status.sql` | Kolom `role` dan `account_status` di `doctor_profiles`; catatan pembuatan Admin via Supabase Admin API |

### B.3 Ujian Unit

| Berkas | Hasil | Keterangan |
|--------|-------|-----------|
| `frontend/src/pages/auth/Login.test.tsx` | **28/28 lolos** | Validasi, redirect, role selector, Remember Me, reset password, opening animation, role mismatch |
| `frontend/src/services/auth.test.ts` | **6/6 lolos** | (Dari audit Sign Up sebelumnya) |

---

## C. Peta Implementasi

| Elemen Diagram | Lokasi Kode | Keterangan |
|---------------|-------------|-----------|
| Membuka halaman `/login` | `AppRoutes.tsx:26-33` + `PublicOnlyRoute.tsx` | Halaman publik; user terautentikasi diarahkan sesuai role |
| Mengisi email, kata sandi, memilih jenis akun | `Login.tsx:56-66` | Form fields + role dropdown (default: doctor) |
| Memvalidasi input | `Login.tsx:93-101` | Email wajib, password wajib |
| Decision "Input valid?" | `Login.tsx:94-101` early return | [Ya] lanjut sign in; [Tidak] tampilkan error |
| [Tidak] → pesan kesalahan → kembali form | `Login.tsx:95,100` + `setErrorMessage` | Loop kembali ke pengisian form |
| Memanggil `signIn()` → `supabase.auth.signInWithPassword()` | `AuthContext.tsx:137` → `auth.ts:208` | Satu panggilan; selectedRole dikirim sebagai parameter konteks |
| Decision "Kredensial valid?" | `auth.ts:213` (`result.error`) | [Ya] lanjut; [Tidak] tampilkan error |
| Memperbarui sesi & state autentikasi | `AuthContext.tsx:142-155` | `setUser`, `setSession`, `setRole`, `setAccountStatus` |
| Decision "Role cocok dengan akun?" | `AuthContext.tsx:159-170` | Role mismatch check: selectedRole vs actualRole |
| [Tidak] → pesan role mismatch → kembali form | `AuthContext.tsx:160-169` + `Login.tsx:117` | Loop kembali ke pengisian form |
| Decision "Role = admin?" | `AuthContext.tsx:151` (`appMetaRole === 'admin'`) | [Ya] → /admin; [Tidak] → cek account_status |
| Mengarahkan ke /admin | `Login.tsx:127` | Admin redirect |
| Decision "Akun pending?" | `Login.tsx:128` (`accountStatus === 'pending'`) | [Ya] → kembali /login dengan pesan pending |
| Decision "Akun ditolak?" | `Login.tsx:130` (`accountStatus === 'rejected'`) | [Ya] → kembali /login dengan pesan rejected |
| Mengakses halaman tujuan | `Login.tsx:133` (`navigate(from, ...)`) | Default: /dashboard; state.from jika ada riwayat |
| Catatan: Remember Me | `openingTimeline.ts:152-176` | Hanya menyimpan email di localStorage |
| Catatan: Reset Password | `Login.tsx:142-171` | Use case terpisah, tidak dimodelkan sebagai aktivitas utama |

---

## D. Matriks Audit Elemen Diagram

| # | Elemen Diagram | Status | Bukti Implementasi |
|---|---------------|--------|--------------------|
| 1 | Initial Node (lingkaran hitam) | ✅ TERVERIFIKASI | Standar UML |
| 2 | Membuka halaman `/login` | ✅ TERVERIFIKASI | `AppRoutes.tsx:26-33` + `PublicOnlyRoute.tsx` |
| 3 | Mengisi email, kata sandi, memilih jenis akun | ✅ TERVERIFIKASI | `Login.tsx:56-66` (email, password, selectedRole default 'doctor') |
| 4 | Memvalidasi input (email wajib, kata sandi wajib) | ✅ TERVERIFIKASI | `Login.tsx:93-101` |
| 5 | Decision "Input valid?" | ✅ TERVERIFIKASI | `Login.tsx:94,100` (early return) |
| 6 | [Ya] → signIn() | ✅ TERVERIFIKASI | `Login.tsx:115` |
| 7 | [Tidak] → pesan kesalahan → kembali form | ✅ TERVERIFIKASI | `Login.tsx:95,100` (setErrorMessage + return) |
| 8 | Memanggil signIn() → supabase.auth.signInWithPassword() | ✅ TERVERIFIKASI | `AuthContext.tsx:137` → `auth.ts:208` |
| 9 | Decision "Kredensial valid?" | ✅ TERVERIFIKASI | `auth.ts:213` (result.error check) |
| 10 | [Ya] → perbarui sesi & state | ✅ TERVERIFIKASI | `AuthContext.tsx:142-155` |
| 11 | [Tidak] → pesan kesalahan → kembali form | ✅ TERVERIFIKASI | `auth.ts:214` + `Login.tsx:117` |
| 12 | Decision "Role cocok dengan akun?" | ✅ TERVERIFIKASI | `AuthContext.tsx:159-170` |
| 13 | [Tidak] → pesan role mismatch → kembali form | ✅ TERVERIFIKASI | `AuthContext.tsx:160-169` |
| 14 | Decision "Role = admin?" | ✅ TERVERIFIKASI | `AuthContext.tsx:151` (appMetaRole check) |
| 15 | [Ya] → arahkan ke /admin | ✅ TERVERIFIKASI | `Login.tsx:127` |
| 16 | [Tidak] → cek account_status | ✅ TERVERIFIKASI | `Login.tsx:128-133` |
| 17 | Decision "Akun pending?" | ✅ TERVERIFIKASI | `Login.tsx:128` |
| 18 | [Ya] → kembali /login (pending) | ✅ TERVERIFIKASI | `Login.tsx:129` |
| 19 | Decision "Akun ditolak?" | ✅ TERVERIFIKASI | `Login.tsx:130` |
| 20 | [Ya] → kembali /login (rejected) | ✅ TERVERIFIKASI | `Login.tsx:131` |
| 21 | [Tidak] → akses halaman tujuan | ✅ TERVERIFIKASI | `Login.tsx:133` (navigate from /dashboard) |
| 22 | Final Node (bullseye) | ✅ TERVERIFIKASI | Standar UML |
| 23 | UML Note (Catatan) | ✅ TERVERIFIKASI | Info PublicOnlyRoute, role selector, Remember Me, Reset Password |

**Ringkasan matriks:** 23/23 elemen **TERVERIFIKASI**. Tidak ada elemen yang **TIDAK SESUAI**.

---

## E. Audit Relasi Antar-Aktivitas dan Percabangan

| Relasi | Arah | Status | Analisis |
|--------|------|--------|----------|
| Input valid lolos | d1 → a4 [Ya] | ✅ VALID | Validasi lokal lolos, lanjut ke signIn() |
| Input tidak valid | d1 → aerr [Tidak] | ✅ VALID | Pesan error ditampilkan, kembali ke form |
| Loop kesalahan validasi | aerr → a2 | ✅ VALID | Pengguna mengisi ulang |
| Hasil signIn diperiksa | a4 → d2 | ✅ VALID | `loginUser` mengembalikan `error` atau `null` |
| Kredensial valid | d2 → a5 [Ya] | ✅ VALID | Session di-set, role/status di-resolve |
| Kredensial tidak valid | d2 → aerr [Tidak] | ✅ VALID | Error ditampilkan, pengguna dapat mencoba lagi |
| Role cocok | d3 → d4 [Ya] | ✅ VALID | selectedRole matches actualRole |
| Role tidak cocok | d3 → a6 [Tidak] | ✅ VALID | Role mismatch error, kembali ke form |
| Loop role mismatch | a6 → a2 | ✅ VALID | Pengguna memilih role berbeda atau memperbaiki input |
| Role = admin | d4 → a7 [Ya] | ✅ VALID | Redirect ke /admin |
| Role ≠ admin | d4 → d5 [Tidak] | ✅ VALID | Lanjut cek account_status |
| Akun pending | d5 → a8 [Ya] | ✅ VALID | Redirect kembali ke /login dengan status pending |
| Akun tidak pending | d5 → d6 [Tidak] | ✅ VALID | Lanjut cek rejected |
| Akun ditolak | d6 → a9 [Ya] | ✅ VALID | Redirect kembali ke /login dengan status rejected |
| Akun tidak ditolak | d6 → a10 [Tidak] | ✅ VALID | Login berhasil, akses halaman tujuan |
| Semua cabang → Final Node | a7/a8/a9/a10 → en | ✅ VALID | Setiap alur mencapai final node |

---

## F. Temuan Ketidaksesuaian pada Diagram Lama

### F.1 Kritis

**F-1 — Start/End bukan notasi UML.** Diagram `FINAL_REVISED.drawio` dan `ROLE_ADMIN_REVISED.drawio` menggunakan persegi panjang berlabel "Start"/"End" untuk initial dan final node. Notasi UML Activity Diagram standar mengharuskan initial node berupa lingkaran terisi hitam dan final node berupa bullseye (lingkaran dalam lingkaran).

**F-2 — Decision node berbentuk persegi.** Diagram lama menggunakan `shape=rectangle` untuk semua node keputusan ("Kredensial valid?", "Role = Admin?"). Decision node UML harus berbentuk belah ketupat (`rhombus`).

**F-3 — Node terisolasi tanpa edge.** Pada `ROLE_ADMIN_REVISED.drawio`, beberapa aktivitas memiliki edge masuk atau keluar yang hilang, membuat alur kontrol tidak lengkap.

**F-4 — Diagram FINAL_REVISED tidak lengkap.** Versi ini hanya memiliki 7 node dan 0 edge — sama sekali tidak memodelkan percabangan validasi, error, atau redirect.

### F.2 Tinggi

**F-5 — Tidak ada loop kesalahan.** Diagram lama tidak menggambarkan jalur kembali ke formulir setelah error validasi atau autentikasi. Implementasi aktual memiliki loop `aerr → a2` dan `a6 → a2`.

**F-6 — Tidak ada pengecekan role mismatch.** Diagram lama tidak mencakup percabangan "Role cocok dengan akun?" yang mencegah dokter meng impersonasi admin melalui dropdown.

### F.3 Sedang

**F-7 — Penanganan status pending/rejected tidak dipisahkan.** Diagram lama menggabungkan semua redirect ke satu node. Implementasi aktual membedakan tiga kondisi: admin → /admin, pending → /login (pending), rejected → /login (rejected).

**F-8 — Tidak ada catatan tentang Remember Me.** Diagram lama tidak menyertakan informasi bahwa Remember Me hanya menyimpan email di localStorage, bukan sesi autentikasi.

---

## G. Rekomendasi

1. Gunakan `ACTIVITY_DIAGRAM_SIGN_IN_PIXELT_FINAL.drawio` / `.png` sebagai *Activity Diagram* Sign In Bab IV (Gambar 4.y).
2. Pertahankan karakteristik: minimalis, monokrom, standar UML (lingkaran terisi untuk initial node, bullseye untuk final node, diamond untuk decision, guard label `[Ya]` / `[Tidak]`).
3. Desain visual konsisten dengan Activity Diagram Sign Up final.
4. Remember Me dan Reset Password dicantumkan sebagai catatan, bukan aktivitas utama.
5. Diagram lama (`FINAL_REVISED.drawio`, `ROLE_ADMIN_REVISED.drawio`) dinyatakan **digantikan**.

---

## H. Penjelasan Akademik

*Activity Diagram* Sign In PIXEL-T (Gambar 4.y) memodelkan proses masuk ke aplikasi melalui halaman `/login`, dimulai dari *initial node* (lingkaran terisi hitam) yang menandai titik awal alur.

Pertama, pengguna membuka halaman `/login`, yang merupakan rute publik dilindungi oleh `PublicOnlyRoute`. Pengguna yang sudah terautentikasi akan diarahkan ke halaman sesuai perannya (Admin ke `/admin`, Dokter yang disetujui ke `/dashboard`). Selanjutnya, pengguna mengisi formulir yang terdiri dari tiga elemen: dropdown pemilihan jenis akun (default: Dokter), bidang email, dan bidang kata sandi. Pemilihan jenis akun merupakan konteks login yang dipilih pengguna, bukan sumber otorisasi.

Setelah formulir diisi, sistem melakukan validasi lokal: alamat email wajib diisi dan kata sandi wajib diisi. *Decision node* "Input valid?" memercabang alur: **[Ya]** lanjut ke autentikasi; **[Tidak]** sistem menampilkan pesan kesalahan dan mengembalikan pengguna ke pengisian formulir.

Apabila input valid, sistem memanggil `signIn()` dari `AuthContext` yang pada gilirannya memanggil `loginUser()` di `services/auth.ts` untuk melakukan autentikasi melalui `supabase.auth.signInWithPassword()`. *Decision node* "Kredensial valid?" memeriksa apakah panggilan tersebut mengembalikan error. **[Ya]** — tanpa error, alur lanjut ke pembaruan sesi; **[Tidak]** — terdapat error (misalnya kredensial salah atau email belum dikonfirmasi), sistem menampilkan pesan kesalahan dan mengembalikan pengguna ke formulir.

Apabila kredensial valid, `AuthContext` memperbarui state autentikasi: menyimpan objek `user` dan `session`, lalu menentukan role dan status akun. Role ditentukan berdasarkan sumber terpercaya: `app_metadata.role` untuk Admin (hanya dapat ditulis oleh server) dan `doctor_profiles.role` untuk Dokter (dari database). Status akun diambil dari `doctor_profiles.account_status`. Kemudian sistem memeriksa apakah role yang dipilih pengguna cocok dengan role aktual akun (*role mismatch check*). **[Ya]** — role cocok, lanjut ke penentuan rute; **[Tidak]** — role tidak cocok (misalnya dokter memilih konteks Admin), sistem menampilkan pesan "jenis akun tidak sesuai" dan mengembalikan pengguna ke formulir.

Apabila role cocok, sistem memeriksa apakah pengguna adalah Admin melalui pengecekan `app_metadata.role === 'admin'`. **[Ya]** — pengguna Admin diarahkan ke `/admin`. **[Tidak]** — sistem memeriksa status akun Dokter. Jika `account_status === 'pending'`, pengguna dikembalikan ke `/login` dengan pesan menunggu persetujuan administrator. Jika `account_status === 'rejected'`, pengguna dikembalikan ke `/login` dengan pesan pendaftaran ditolak. Jika status adalah `approved`, pengguna diarahkan ke halaman tujuan (default `/dashboard` atau halaman sebelumnya yang tersimpan di `location.state.from`).

Semua cabang akhir menuju *final node* (bullseye: lingkaran luar putih dengan lingkaran dalam hitam).

Catatan pendukung pada diagram menyatakan bahwa halaman `/login` dilindungi `PublicOnlyRoute`, role selector adalah konteks login bukan sumber otorisasi, fitur "Remember my email" hanya menyimpan alamat email di `localStorage` tanpa memengaruhi sesi autentikasi, dan halaman Reset Password merupakan use case terpisah.

---

## I. Keterbatasan Audit

1. **Audit berbasis analisis statis kode sumber, bukan pengujian runtime.** Tidak ada pengujian browser (E2E) atau eksekusi terhadap Supabase Auth yang sebenarnya. Seluruh klaim kesesuaian didasarkan pada pembacaan berkas yang tercantum pada Bagian B.
2. **Tidak ada akses ke lingkungan Supabase produksi.** Konfigurasi `app_metadata` Admin dan data `doctor_profiles` tidak diperiksa secara langsung; kesimpulan diambil dari migrasi SQL dan kode otorisasi.
3. **Validasi visual diagram terbatas.** Draw.io Desktop dan *engine* UML resmi tidak tersedia pada lingkungan audit. Validasi diagram dilakukan melalui (a) pemeriksaan *well-formedness* XML dengan `xml.etree.ElementTree`, (b) verifikasi bahwa setiap `source`/`target` edge merujuk ID node yang ada, dan (c) pemeriksaan berkas PNG (`ACTIVITY_DIAGRAM_SIGN_IN_PIXELT_FINAL.png`, 1720×2100) dengan `PIL.Image.verify()`.
4. **Kredensial tidak diungkap.** Audit tidak membaca, menyalin, atau menampilkan *service-role key*, kata sandi, atau token apa pun.
5. **Tidak ada modifikasi kode aplikasi.** Audit hanya menghasilkan artefak dokumentasi dan diagram baru; tidak ada berkas aplikasi, migrasi, atau konfigurasi yang diubah.

---

## J. Status Akhir

**Status: TERVALIDASI — FINAL.**

| Kriteria | Hasil |
|----------|-------|
| Seluruh aktivitas dan *decision node* pada diagram memiliki dasar implementasi | ✅ 23/23 elemen terverifikasi |
| Percabangan validasi, kegagalan autentikasi, role mismatch, dan status akun lengkap | ✅ Lengkap |
| Node awal dan akhir standar UML (*initial node* terisi, *final node* bullseye) | ✅ Terdapat |
| Decision node berbentuk belah ketupat (bukan persegi) | ✅ Benar |
| Tidak ada aktivitas fiktif di luar lingkup Sign In | ✅ Tidak ditemukan |
| Remember Me dimodelkan sebagai catatan (bukan aktivitas) | ✅ Benar |
| Reset Password tidak dicampurkan ke alur Sign In | ✅ Benar |
| Desain konsisten dengan Activity Diagram Sign Up final | ✅ Konsisten |
| Validasi visual oleh *engine* UML resmi | ⚠️ Terbatas (lihat I-3) |
| Pengujian runtime / browser (E2E) | ⚠️ Tidak dilakukan (lihat I-1) |
| Ujian unit relevan | ✅ 28/28 lolos |

**Keputusan:** `ACTIVITY_DIAGRAM_SIGN_IN_PIXELT_FINAL.drawio` / `.png` **layak** digunakan sebagai *Activity Diagram* Sign In Bab IV (Gambar 4.y), dengan catatan keterbatasan validasi visual dan ketiadaan pengujian runtime sebagaimana diuraikan pada Bagian I. Diagram lama (`FINAL_REVISED.drawio` dan `ROLE_ADMIN_REVISED.drawio`) dinyatakan **digantikan**.

---

*Audit dilaksanakan melalui analisis statis terhadap kode sumber aktual web PIXEL-T. Seluruh temuan dapat dilacak ke berkas yang tercantum pada Bagian B. Tidak ada kode aplikasi yang diubah.*
