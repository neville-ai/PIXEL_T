# MATRIKS BUKTI PENGUJIAN FUNGSI PIXELT

**Dokumen :** MATRIKS_BUKTI_PENGUJIAN_FUNGSI_PIXELT.md  
**Posisi :** Pendukung penulisan BAB V subbab 5.1 "Pengujian dan Validitas Fungsionalitas Aplikasi Web PIXEL-T"  
**Sumber :** Hanya sumber internal proyek PIXEL-T  
**Tanggal :** 6 November 2026

Status yang digunakan:

- **PASS** : skenario diuji secara otomatis (frontend vitest) dan hasil aktual sesuai yang diharapkan.
- **NOT RUN** : skenario tersedia dalam bentuk kode tes atau rencana, tetapi belum dieksekusi.
- **BLOCKED** : pengujian tidak dapat dijalankan karena kendala lingkungan (blokir pustaka PyTorch oleh kontrol aplikasi Windows).
- **NOT VERIFIED** : bukti tidak cukup untuk memastikan hasilnya (misalnya integrasi runtime nyata yang hanya diperiksa secara statis).

Catatan: tes frontend menggunakan dependensi tiruan (mock) terhadap layanan autentikasi dan analisis. Hasil PASS menunjukkan verifikasi perilaku komponen dalam isolasi, bukan integrasi runtime nyata dengan Supabase Auth maupun backend Flask.

---

## Matriks Bukti Pengujian per Fungsi

| No. | Fitur | Pernyataan atau Skenario | Bukti Implementasi | Bukti Pengujian | Hasil Aktual | Status |
|---|---|---|---|---|---|---|
| 1 | Sign Up | Formulir pendaftaran menampilkan input email, sandi, nama lengkap, rumah sakit, dan spesialisasi dokter; semua kolom wajib divalidasi | `frontend/src/pages/auth/Register.tsx`, `frontend/src/context/AuthContext.tsx` | `Register.test.tsx` (14 tes) | 14 tes lulus | PASS |
| 2 | Sign Up | Pengiriman registrasi berhasil menampilkan kartu sukses dengan tindakan Login sebagai aksi utama; `signUp` mengembalikan `requiresEmailConfirmation` | `AuthContext.tsx` (`signUp`) | `Register.test.tsx` | Tes submit dan kartu sukses lulus | PASS |
| 3 | Sign Up | Saat `signUp` mengembalikan kesalahan, banner kesalahan ditampilkan dan pengguna tetap di halaman pendaftaran | `Register.tsx` | `Register.test.tsx` | Tes banner kesalahan lulus | PASS |
| 4 | Sign In | Autentikasi kredensial melalui Supabase Auth dengan pemilihan role (`admin` atau `doctor`); redirect ke `/admin` bagi admin dan `/dashboard` bagi dokter approved | `AuthContext.tsx` (`signIn` dengan `selectedRole`), `frontend/src/pages/auth/Login.tsx` | `Login.test.tsx` (41 tes) | 41 tes lulus | PASS |
| 5 | Sign In | Login ditolak jika role yang dipilih tidak cocok dengan jenis akun pada server (misalnya user adalah dokter tetapi memilih Admin) | `AuthContext.tsx` | `Login.test.tsx` ("menolak login Admin ketika user sebenarnya adalah dokter" dan sebaliknya) | Tes penolakan role lulus | PASS |
| 6 | Sign In | Dokter dengan status `pending` menampilkan pesan menunggu persetujuan dan tidak diarahkan ke dasbor | `AuthContext.tsx` (`accountStatus`) | `Login.test.tsx` ("dokter pending tetap melihat pesan tunggu persetujuan") | Tes pesan pending lulus | PASS |
| 7 | Sign In | Validasi email dan sandi kosong mencegah pemanggilan `signIn`; pesan kesalahan ditampilkan melalui elemen alert | `Login.tsx` | `Login.test.tsx` ("signIn tidak dipanggil saat email kosong", "pesan error ketika password kosong") | Tes validasi lulus | PASS |
| 8 | Sign Out | Klik Sign Out membuka dialog konfirmasi; membatalkan dialog tidak memanggil layanan logout; mengonfirmasi memanggil logout satu kali dan menutup dialog | `App.tsx`, `AuthContext.tsx` (`signOut`) | `App.test.tsx` (tes Sign Out dan dialog konfirmasi) | 35 tes App shell lulus, termasuk alur Sign Out | PASS |
| 9 | Upload Image | Formulir unggah hanya menerima berkas JPEG/PNG; format yang tidak didukung ditolak dan tombol tetap nonaktif | `services/analysis.ts`, `routes/analysis.py` | `NewAnalysis.test.tsx` (tes validasi berkas) | Tes penolakan format, ukuran > 10 MB, berkas kosong, tidak dapat didekode, dan konsistensi ekstensi/MIME lulus | PASS |
| 10 | Upload Image | Berkas .jpeg dengan MIME `image/jpeg` dan .jpg tanpa MIME diterima melalui ekstensi | `services/analysis.ts` | `NewAnalysis.test.tsx` | Tes penerimaan berkas valid lulus | PASS |
| 11 | Upload Image | Respons backend 202 membawa `analysis_id` dan status `processing`; status ini **belum dianggap selesai** | `routes/analysis.py` (dua taham terima lalu proses) | `NewAnalysis.test.tsx` ("respons 202 ... belum dianggap selesai") | Tes status awal processing lulus | PASS |
| 12 | Upload Image | Antrean penuh mengembalikan HTTP 429 `QUEUE_FULL` tanpa menambah rekalan yang menyesatkan; pengguna dapat mencoba lagi | `routes/analysis.py` | `tests/backend/test_analysis.py` (`test_queue_full_returns_429...`) | Berkas tes tersedia, **tidak dijalankan** | NOT RUN / BLOCKED |
| 13 | Segmentation | Frontend memantau status melalui polling `getAnalysis` pada interval terbatas dan berhenti setelah status `completed` atau `failed` | `services/analysis.ts` (`getAnalysis`) | `AnalysisResult.test.tsx`, `NewAnalysis.test.tsx` | Tes polling berhenti pada completed/failed lulus | PASS |
| 14 | Segmentation | Progress 100% hanya ditampilkan setelah penyelesaian; `current_step` tanpa persentase tidak diisi dengan angka buatan; persentase di luar rentang kontrakt tidak dirender | `AnalysisResult.tsx`, `NewAnalysis.tsx` | `AnalysisResult.test.tsx`, `NewAnalysis.test.tsx` | Tes render progres lulus | PASS |
| 15 | Segmentation | Hasil disajikan hanya aset dan pengukuran yang tersedia dari API; tidak ada hasil segmentasi yang diusulkan; status gagal tidak menampilkan detail kegagalan mentah | `AnalysisResult.tsx` | `AnalysisResult.test.tsx` ("renders only completed assets and measurements supplied by the API", "renders a safe failed state without exposing stored error details") | Tes penyajian aman lulus | PASS |
| 16 | Segmentation | Kegagalan Grad-CAM menandai seluruh pekerjaan analisis gagal; tidak ada fallback yang memisahkan Grad-CAM dari alur utama | `routes/analysis.py`, lapisan pipeline AI | `tests/ai/test_model_integration.py` (`test_failed_forward_pass_is_not_reported_as_completed`) | Berkas tes tersedia, **tidak dijalankan** | NOT RUN / BLOCKED |
| 17 | History | Riwayat analisis hanya mencakup milik pengguna yang terautentikasi; `user_id` diambil dari token, tidak pernah dari input klien | `routes/history.py`, kebijakan tingkat baris (RLS) | `History.test.tsx` (22 tes) | 22 tes lulus | PASS |
| 18 | History | Riwayat kosong menampilkan EmptyState; paginasi klien 4 item per halaman dengan hitungan yang jujur; filter nama file, status inferensi, dan tanggal analisis | `frontend/src/pages/history/History.tsx` | `History.test.tsx` | Tes empty state, paginasi, dan filter lulus | PASS |
| 19 | History | Penghapusan riwayat melalui dialog konfirmasi; item tetap tersimpan dan ditampilkan aman saat penghapusan gagal | `History.tsx` | `History.test.tsx` | Tes dialog konfirmasi dan kegagalan penghapusan lulus | PASS |
| 20 | Doctor Profile | Profil dimuat berdasarkan pengguna terautentikasi dengan data sesi auth; fallback "Not available" saat metadata pengguna tidak memiliki nama | `services/profile.ts`, `AuthContext.tsx` | `DoctorProfile.test.tsx` (23 tes) | 23 tes lulus | PASS |
| 21 | Doctor Profile | Perubahan disimpan per bagian (A/B/C) secara terpisah tanpa mempengaruhi bagian lain; statistik dihitung jujur dari `listHistory`; maksimal 3 rekaman terbaru ditampilkan dengan tautan ke analisis | `services/profile.ts` | `DoctorProfile.test.tsx` | Tes simpan per bagian dan statistik lulus | PASS |
| 22 | Doctor Profile | Upload dan penghapusan avatar diblokir saat tidak ada sesi aktif dan menampilkan kesalahan autentikasi | `services/profile.ts` | `DoctorProfile.test.tsx` | Tes upload/hapus avatar dengan dan tanpa sesi lulus | PASS |
| 23 | Admin | Dashboard admin menampilkan daftar dokter dengan tombol Setujui/Tolak hanya pada akun `pending`; statistik registrasi ditampilkan | `frontend/src/pages/admin/AdminDashboard.tsx`, `backend/app/routes/admin.py` | `AdminDashboard.test.tsx` (17 tes) | 17 tes lulus (level frontend) | PASS |
| 24 | Admin | Approve dan reject dokter dilindungi oleh `require_admin`; reject menyertakan alasan penolakan | `routes/admin.py` (`require_admin`), `AdminController` | `tests/backend/test_admin_routes.py`, `tests/backend/test_admin_service.py` | Berkas tes tersedia, **tidak dijalankan** | NOT RUN / BLOCKED |
| 25 | Akses terproteksi | Halaman `/profile` dilindungi ProtectedRoute (dirender hanya setelah login); halaman publik `/login` tanpa AppShell global; navigasi menu sesuai halaman aktif | `App.tsx` (`ProtectedRoute`, `PublicOnlyRoute`) | `App.test.tsx` (tes route dan menu aktif) | Tes ProtectedRoute dan navigasi lulus | PASS |

---

## Ringkasan Status

| Fitur | Jumlah Skenario | PASS | NOT RUN / BLOCKED | NOT VERIFIED |
|---|---|---|---|---|
| Sign Up | 3 | 3 | 0 | 0 |
| Sign In | 4 | 4 | 0 | 0 |
| Sign Out | 1 | 1 | 0 | 0 |
| Upload Image | 4 | 3 | 1 | 0 |
| Segmentation | 4 | 3 | 1 | 0 |
| History | 3 | 3 | 0 | 0 |
| Doctor Profile | 3 | 3 | 0 | 0 |
| Admin | 2 | 1 | 1 | 0 |
| Akses terproteksi | 1 | 1 | 0 | 0 |
| **Total** | **25** | **23** | **2** | **0** |

Catatan: dua skenario dengan status NOT RUN / BLOCKED (antrean penuh HTTP 429 pada backend, dan kegagalan Grad-CAM pada pipeline AI) tersedia sebagai berkas tes pytest tetapi tidak dapat dieksekusi pada mesin audit karena blokir pustaka PyTorch. Hasil PASS di atas adalah hasil tes unit frontend dengan dependensi tiruan, bukan bukti integrasi runtime end-to-end.

---

## Catatan Akses Admin vs Dokter

Setiap skenario login, unggah, riwayat, dan profil telah diperiksa dengan pemisahan role yang jelas: `admin` diarahkan ke halaman admin (`/admin`) dan mengelola pendaftaran dokter, sedangkan `doctor` diarahkan ke dasbor dokter (`/dashboard`) dan hanya mengelola analisis serta profilnya sendiri. Tidak ada skenario dalam matriks ini yang mencampur hak akses keduanya.
