# AUDIT PENGUJIAN DAN VALIDITAS FUNGSI PIXELT

**Dokumen :** AUDIT_PENGUJIAN_DAN_VALIDITAS_FUNGSI_PIXELT.md  
**Posisi :** Pendukung penulisan BAB V subbab 5.1 "Pengujian dan Validitas Fungsionalitas Aplikasi Web PIXEL-T"  
**Judul skripsi :** "TRANSFER LEARNING DAN EXPLAINABLE AI UNTUK SEGMENTASI POLIP USUS MENGGUNAKAN CITRA ENDOSKOPI BERBASIS WEB"  
**Sumber :** Hanya sumber internal proyek PIXEL-T (tidak ada sumber web atau referensi eksternal)  
**Tanggal audit :** 6 November 2026

---

## 1. Ringkasan Kondisi Pengujian

| Aspek | Hasil Audit |
|---|---|
| Pengujian otomatis frontend | **18 berkas tes lulus (18)**, **285 tes lulus (285)**, 0 gagal, 0 dilewati; waktu eksekusi 47,68 detik (vitest v5.0.2, environment jsdom) |
| Perintah pengujian frontend | `npm test --prefix frontend` (skrip `vitest run` pada `frontend/package.json`) |
| Pengujian otomatis backend | 9 berkas tes, **104 fungsi tes** — tersedia sebagai kode, **tidak dapat dieksekusi** pada mesin audit |
| Pengujian otomatis AI | 2 berkas tes, **17 fungsi tes** — tersedia sebagai kode, **tidak dapat dieksekusi** pada mesin audit |
| Pengujian manual | Belum dilakukan (**NOT RUN**) |
| Pengujian end-to-end (frontend nyata ke backend nyata) | Belum dilakukan (**NOT VERIFIED**) |
| Kendala utama | Kontrol aplikasi sistem operasi Windows memblokir berkas pustaka `torch/lib/c10_cuda.dll` (OSError WinError 4551), sehingga pustaka PyTorch tidak dapat dimuat dan tes backend serta AI yang bergantung pada lapisan AI tidak terpicu |

Kesingkat: hasil pengujian yang dapat diperhitungkan pada waktu audit berasal esclusiva dari eksekusi suite frontend. Pengujian backend dan AI tetap dalam bentuk berkas tes yang ditulis tetapi belum dijalankan, sehingga statusnya adalah **NOT RUN / BLOCKED**, bukan PASS.

---

## 2. Inventaris Sumber Bukti

| No. | Sumber | Lokasi | Keterangan | Status Verifikasi |
|---|---|---|---|---|
| 1 | Berkas tes frontend Sign Up | `frontend/src/pages/auth/Register.test.tsx` | 14 tes unit alur pendaftaran | Diperiksa |
| 2 | Berkas tes frontend Sign In | `frontend/src/pages/auth/Login.test.tsx` | 41 tes unit autentikasi dan role | Diperiksa |
| 3 | Berkas tes frontend Upload Image | `frontend/src/pages/analysis/NewAnalysis.test.tsx` | 28 tes unit upload dan polling | Diperiksa |
| 4 | Berkas tes frontend Segmentation (hasil) | `frontend/src/pages/analysis/AnalysisResult.test.tsx` | 7 tes unit status dan penyajian hasil | Diperiksa |
| 5 | Berkas tes frontend History | `frontend/src/pages/history/History.test.tsx` | 22 tes unit riwayat analisis | Diperiksa |
| 6 | Berkas tes frontend Doctor Profile | `frontend/src/pages/profile/DoctorProfile.test.tsx` | 23 tes unit profil dan statistik | Diperiksa |
| 7 | Berkas tes frontend Admin Dashboard | `frontend/src/pages/admin/AdminDashboard.test.tsx` | 17 tes unit dashboard dan persetujuan dokter | Diperiksa |
| 8 | Berkas tes frontend App shell | `frontend/src/App.test.tsx` | 35 tes shell, navigasi, ProtectedRoute, Sign Out | Diperiksa |
| 9 | Berkas tes frontend komponen/UI | `frontend/src/components/...`, `hooks/...`, `lib/...`, `services/...`, `statusText.contrast.test.tsx` | 11 berkas tes komponen, layanan, dan desain token | Diperiksa |
| 10 | Berkas tes backend | `tests/backend/*.py` (9 berkas) | tes autentikasi, analisis, admin, histori, health, repository, storage, supabase config | Tersedia, belum dijalankan |
| 11 | Berkas tes AI | `tests/ai/*.py` (2 berkas) | tes Grad-CAM dan integrasi model | Tersedia, belum dijalankan |
| 12 | Implementasi autentikasi | `frontend/src/context/AuthContext.tsx` | signIn/signUp/signOut, role, accountStatus, startup reset | Diperiksa |
| 13 | Implementasi layanan analisis | `frontend/src/services/analysis.ts` | createAnalysis/getAnalysis/listHistory/deleteAnalysis; kontrak status processing/completed/failed | Diperiksa |
| 14 | Implementasi endpoint analisis | `backend/app/routes/analysis.py` | dua taham: 202 processing, penyelesaian asinkron, pipeline AI | Diperiksa (statis) |
| 15 | Implementasi endpoint admin | `backend/app/routes/admin.py` | `/api/admin/doctors*` dengan `require_admin` | Diperiksa (statis) |
| 16 | Implementasi dashboard admin | `frontend/src/pages/admin/AdminDashboard.tsx` | daftar dokter, statistik, approve/reject dokter | Diperiksa |
| 17 | Dokumen pendukung | `docs/PRD_PIXEL-T_FINAL.md`, `docs/ModelIntegrationSpecification.md`, `docs/FunctionalSpecification.md`, `docs/CodebaseAnalysis.md` | ruang lingkup, spesifikasi model, spesifikasi fungsional, analisis implementasi | Diperiksa |

---

## 3. Daftar Fungsi yang Diperiksa

Delapan fungsi yang diperiksa dalam audit ini:

1. **Sign Up** — pendaftaran akun (email, sandi, nama lengkap, rumah sakit, spesialisasi dokter), validasi input, respons signUp termasuk `requiresEmailConfirmation`, status akun awal `pending`.
2. **Sign In** — autentikasi kredensial melalui Supabase Auth dengan pemilihan role (`admin` | `doctor`), navigasi berdasarkan role (`/admin` bagi admin, `/dashboard` bagi dokter), penolakan jika role tidak cocok, pesan menunggu persetujuan bagi dokter `pending`.
3. **Upload Image** — pemilihan file, validasi ekstensi JPEG/PNG, konsistensi MIME, ukuran maksimal 10 MB, berkas kosong, berkas yang tidak dapat didekode, pengiriman ke backend, respons 202 dengan `analysis_id` dan status `processing`.
4. **Segmentation** — pemantauan status melalui polling `getAnalysis`, status `processing` → `completed` / `failed`, penyajian aset dan pengukuran hanya sesuai API, tidak ada hasil yang diusulkan, penanganan kegagalan Grad-CAM yang menandai seluruh pekerjaan analisis gagal.
5. **History** — riwayat analisis milik pengguna yang terautentikasi (user_id dari token, bukan input klien), riwayat kosong, paginasi 4 item per halaman, filter, penghapusan dengan konfirmasi.
6. **Doctor Profile** — muat profil berdasarkan sesi terautentikasi, fallback "Not available", penyimpanan per bagian (A/B/C) secara terpisah, statistik dihitung dari `listHistory`, maksimal 3 rekaman terbaru.
7. **Sign Out** — dialog konfirmasi, pembatalan tidak memanggil layanan logout, konfirmasi memanggil logout sekali dan mengalihkan halaman.
8. **Admin (pengelolaan dokter)** — daftar dokter, statistik registrasi, approve dan reject dengan alasan penolakan, akses dibatasi oleh `require_admin`.

---

## 4. Metode Pengujian yang Ditemukan

| Metode | Bukti Penerapan | Bagian yang Diuji | Hasil | Keterbatasan |
|---|---|---|---|---|
| Unit testing otomatis (frontend) | vitest v5.0.2 + `@testing-library/react`, environment jsdom; skrip `vitest run` | Komponen dan layanan frontend (autentikasi, upload, riwayat, profil, admin, shell) | **PASS** (285 tes lulus) | Semua tes menggunakan dependensi tiruan (mock); verifikasi pada level komponen, bukan integrasi runtime nyata dengan Supabase Auth |
| API / integration testing (backend) | pytest; berkas tes di `tests/backend/` | Endpoint Flask (analisis, autentikasi, admin, histori, health, repository, storage) | **NOT RUN / BLOCKED** | Tidak dapat dijalankan karena blokir pustaka PyTorch oleh kontrol aplikasi Windows |
| Testing lapisan AI | pytest; berkas tes di `tests/ai/` | Grad-CAM, integrasi model, pipeline inferensi | **NOT RUN / BLOCKED** | Sama seperti di atas |
| Pengujian manual | Tidak ditemukan bukti eksekusi | — | **NOT RUN** | Tidak dilakukan |
| Pemeriksaan source code (statis) | Bacaan implementasi kode | Skema validasi, rute, middleware role, status analisis | Digunakan sebagai pendukung | Tidak sama dengan pengujian runtime |

Tidak ditemukan dokumentasi pengujian black-box terstruktur, dan tidak ada laporan code coverage yang tersedia. Oleh karena itu, istilah seperti "black-box testing" tidak digunakan dalam naskah karena tidak terdapat bukti penerapannya dalam proyek.

---

## 5. Matriks Skenario Pengujian

Detail skenario per fungsi, bukti implementasi, bukti pengujian, hasil aktual, dan status tersedia dalam Dokumen 2 (`MATRIKS_BUKTI_PENGUJIAN_FUNGSI_PIXELT.md`).

Ringkasan skenario utama yang teridentifikasi:

1. **Sign Up** — input valid, input kosong, pengiriman registrasi, kartu sukses, banner kesalahan saat `signUp` gagal.
2. **Sign In** — kredensial valid admin/dokter, redirect berdasarkan role, role tidak cocok ditolak, dokter `pending` melihat pesan menunggu, validasi email/sandi kosong, error autentikasi ditampilkan tanpa pindah halaman, loading mencegah submit ganda.
3. **Sign Out** — dialog konfirmasi, batal tidak memanggil logout, konfirmasi memanggil logout sekali.
4. **Upload Image** — berkas JPEG/PNG valid diterima, format tidak didukung ditolak, ukuran > 10 MB ditolak, berkas kosong dan tidak dapat didekode ditolak, konsistensi ekstensi/MIME divalidasi, respons 202 `processing` bukan berarti selesai, antrean penuh mengembalikan HTTP 429.
5. **Segmentation** — polling status hingga `completed` / `failed`, penyajian aset sesuai API, progress 100% hanya setelah selesai, kegagalan jaringan sementara tidak terminal.
6. **History** — riwayat per pengguna, riwayat kosong, paginasi, filter, hapus dengan konfirmasi.
7. **Doctor Profile** — muat profil, fallback metadata, simpan per bagian, statistik dari `listHistory`, maksimal 3 rekaman terbaru, upload/hapus avatar.
8. **Admin** — daftar dan statistik dokter, approve/reject, tombol aksi hanya pada akun `pending`, akses dibatasi `require_admin`.

---

## 6. Hasil Automated Testing

| Suite | Berkas Tes | Fungsi Tes | Dijalankan | Lulus | Gagal | Dilewati | Status |
|---|---|---|---|---|---|---|---|
| Frontend (vitest) | 18 | 285 | Ya | 285 | 0 | 0 | PASS |
| Backend (pytest) | 9 | 104 | Tidak | 0 | 0 | 0 | NOT RUN / BLOCKED |
| AI (pytest) | 2 | 17 | Tidak | 0 | 0 | 0 | NOT RUN / BLOCKED |

Catatan eksekusi frontend terakhir: 18 berkas tes lulus, 285 tes lulus, durasi 47,68 detik, environment jsdom dibuat 18 kali. Eksekusi dilakukan tanpa perubahan pada kode aplikasi.

---

## 7. Hasil Manual Testing

Tidak ada bukti pengujian manual yang tersedia dalam proyek. Tidak ada screenshot hasil pengujian manual, log eksplorasi aplikasi runtime, atau catatan uji coba pengguna. Oleh karena itu, setiap pernyataan mengenai perilaku aplikasi pada naskah 5.1 harus didasarkan pada hasil tes otomatis frontend atau pemeriksaan source code, dan harus dicatat sebagai **NOT RUN** untuk bagian yang hanya diperiksa secara statis.

---

## 8. Bukti Pendukung

1. Output eksekusi vitest: `Test Files 18 passed (18)`, `Tests 285 passed (285)`, `Duration 47.68s`.
2. Daftar lengkap 18 berkas tes frontend (tertera pada Inventaris Sumber Bukti, poin 1–9).
3. Implementasi `AuthContext.tsx` (signIn/signUp/signOut, role, accountStatus, startup reset).
4. Implementasi `services/analysis.ts` (kontrak status `processing` / `completed` / `failed`, respons 202).
5. Implementasi `backend/app/routes/analysis.py` dan `admin.py` (endpoint, `require_admin`).
6. Implementasi `frontend/src/pages/admin/AdminDashboard.tsx` (persetujuan dokter).
7. Berkas tes backend `tests/backend/test_analysis.py`, `test_auth.py`, `test_admin_routes.py`, `test_admin_service.py`, `test_history.py`, dan lain-lain (tidak dijalankan).
8. Berkas tes AI `tests/ai/test_gradcam.py`, `tests/ai/test_model_integration.py` (tidak dijalankan).

---

## 9. Kendala Pengujian

1. **Blokir pustaka PyTorch.** Kontrol aplikasi sistem operasi Windows mencegah pemuatan `torch/lib/c10_cuda.dll` (OSError WinError 4551). Akibatnya, seluruh tes backend dan AI tidak dapat dieksekusi pada mesin audit, meskipun kode tes telah ditulis lengkap (121 fungsi tes dalam bentuk kode).
2. **Pengujian dengan dependensi tiruan.** Tes frontend memanggil fungsi `signIn`, `signUp`, `createAnalysis`, `getAnalysis`, `listHistory` yang ditiru (mock). Hasil PASS menunjukkan perilaku komponen dalam isolasi, bukan integrasi runtime nyata dengan Supabase Auth dan backend Flask.
3. **Tidak ada pengujian manual maupun end-to-end.** Tidak dapat diklaim bahwa seluruh alur sign up → login → upload → segmentasi → riwayat telah diuji secara bersamaan pada runtime nyata.
4. **Tidak ada laporan coverage.** Tidak dapat diungkapkan persentase cakupan kode yang diuji.

---

## 10. Temuan dan Keterbatasan

| No. | Temuan / Keterbatasan | Keterangan |
|---|---|---|
| 1 | HTTP 202 `processing` bukan penyelesaian | Tes `NewAnalysis` secara eksplisit memverifikasi bahwa respons 202 membawa `analysis_id` dan status `processing`, dan **"belum dianggap selesai"**. Hasil segmentasi hanya tersedia setelah status berubah menjadi `completed`. |
| 2 | Kegagalan Grad-CAM blokir seluruh pekerjaan | Implementasi pipeline menunjukkan bahwa kegagalan lapisan Grad-CAM menyebabkan pekerjaan analisis ditandai gagal; tidak ada mekanisme fallback yang menyaring Grad-CAM dari alur utama. |
| 3 | Akses Admin dan Dokter dipisah | Role `admin` dan `doctor` diverifikasi secara terpisah; admin diarahkan ke `/admin`, dokter approved ke `/dashboard`, dokter `pending` melihat pesan menunggu persetujuan. Login dengan role yang tidak cocok ditolak. |
| 4 | Validasi file sesuai spesifikasi | Upload menerima JPEG/PNG, membatasi ukuran maksimal 10 MB, dan menolak konsistensi ekstensi/MIME yang tidak cocok serta berkas yang tidak dapat didekode. |
| 5 | Tes backend dan AI belum diverifikasi runtime | 104 fungsi tes backend dan 17 fungsi tes AI tersedia dalam bentuk kode tetapi belum dijalankan. Tidak dapat diklaim bahwa backend atau lapisan AI telah lulus pengujian pada mesin audit. |
| 6 | Tidak ada klaim validitas klinis | Pengujian ini mencakup fungsionalitas aplikasi web saja. Evaluasi model AI (Dice, IoU, presisi, recall, HD95) merupakan pembahasan terpisah dan tidak dicampurkan ke dalam validitas fungsionalitas aplikasi. Tidak ada klaim mengenai manfaat klinis atau kesiapan penggunaan dalam lingkungan klinis produksi. |

---

## 11. Kesimpulan Audit

Berdasarkan audit yang dilakukan terhadap sumber internal PIXEL-T:

1. Pengujian fungsionalitas frontend aplikasi web PIXEL-T telah dieksekusi dan terverifikasi: **18 berkas tes, 285 tes lulus, 0 gagal**, mencakup Sign Up, Sign In, Upload Image, Segmentation, History, Doctor Profile, Sign Out, Admin Dashboard, serta navigasi dan perlindungan rute.
2. Pengujian backend dan lapisan AI **tidak dapat dieksekusi** pada mesin audit karena blokir pustaka PyTorch oleh kontrol aplikasi Windows. Statusnya adalah **NOT RUN / BLOCKED**, dan klaim keberhasilan pada bagian tersebut tidak dapat diajukan.
3. Tidak ditemukan bukti pengujian manual maupun end-to-end, dan tidak ada laporan coverage.
4. Validitas fungsionalitas aplikasi web terbukti pada lingkup unit testing frontend yang dijalankan. Validitas ini **tidak setara** dengan validitas klinis, akurasi model segmentasi, atau kesiapan penggunaan dalam praktek medis produksi.

Dokumen ini tidak dimaksudkan sebagai bagian dari naskah akademik utama skripsi, melainkan sebagai catatan verifikasi bukti bagi penyusunan subbab 5.1.

---

## Lampiran: Daftar Berkas Tes Frontend yang Dieksekusi

1. `pages/admin/AdminDashboard.test.tsx`
2. `pages/analysis/AnalysisResult.test.tsx`
3. `pages/analysis/NewAnalysis.test.tsx`
4. `pages/auth/Login.test.tsx`
5. `pages/auth/Register.test.tsx`
6. `pages/dashboard/Dashboard.test.tsx`
7. `pages/history/History.test.tsx`
8. `pages/profile/DoctorProfile.test.tsx`
9. `App.test.tsx`
10. `components/auth/OpeningAnimation.test.ts`
11. `components/ui/Badge.test.tsx`
12. `components/ui/Modal.test.tsx`
13. `hooks/useOpeningAnimation.test.ts`
14. `lib/openingTimeline.test.ts`
15. `services/analysis.test.ts`
16. `services/auth.test.ts`
17. `services/profile.test.ts`
18. `statusText.contrast.test.tsx`
