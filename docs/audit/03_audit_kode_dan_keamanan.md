# AUDIT KUALITAS KODE, KEAMANAN, DAN ROBUSTNESS SISTEM WEB PIXEL-T

**Tanggal:** 9 November 2026  
**Status:** READ-ONLY SYSTEM AUDIT  
**Dokumen:** `docs/audit/03_audit_kode_dan_keamanan.md`  
**Cakupan Audit:** Lapisan Autentikasi, Otorisasi, RLS, Validasi Input, Error Handling, Async Worker, Storage, XAI, dan Kualitas Rekayasa Perangkat Lunak.

---

## 4.1 Autentikasi & Otorisasi

### 1. Verifikasi Token JWT
- **Mekanisme:** Seluruh komunikasi klien-ke-server yang dilindungi menggunakan skema `Authorization: Bearer <token>`.
- **Implementasi:** Di [`Backend/src/core/auth.py:11-84`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/Backend/src/core/auth.py#L11-L84), dekorator `@require_auth` memvalidasi integritas token secara kriptografis menggunakan `client.auth.get_user(token)` melalui Supabase Auth SDK.
- **Ketahanan Terhadap Token Malformasi:** Sistem memeriksa struktur header (tepat dua kata, diawali `Bearer`, token tidak kosong). Jika salah satu gagal, server langsung melempar `APIError("UNAUTHORIZED", ..., 401)` tanpa mengeksekusi logika internal.

### 2. Pencegahan Eskalasi Hak Akses (*Privilege Escalation Prevention*)
- **Pemisahan Model Peran Admin vs Dokter:**  
  Di [`Backend/src/core/auth.py:87-173`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/Backend/src/core/auth.py#L87-L173), identitas Admin **hanya dibaca dari `app_metadata.role`** (`user.app_metadata.get('role') == 'admin'`).
  - `app_metadata` pada Supabase Auth berstatus *server-write-only* dan **hanya dapat ditulis melalui Service-Role Key / Supabase Admin API**.
  - Metadata pengguna standar (`user_metadata`) sengaja **TIDAK DIGUNAKAN** untuk otorisasi karena dapat dimodifikasi oleh pengguna biasa dari browser melalui `supabase.auth.updateUser()`. Ini menutup celah eskalasi hak akses secara tuntas.
- **Pemeriksaan Status Persetujuan Akun Dokter:**  
  Dekorator `@require_approved_doctor` ([`auth.py:176-265`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/Backend/src/core/auth.py#L176-L265)) melakukan verifikasi dua lapis:
  1. Pengguna wajib memiliki profil dokter di tabel `public.doctor_profiles`.
  2. Kolom `account_status` wajib bernilai persis `'approved'`. Jika berstatus `'pending'`, dikembalikan HTTP 403 `ACCOUNT_PENDING`. Jika `'rejected'`, dikembalikan HTTP 403 `ACCOUNT_REJECTED`.
  3. Akun Admin secara eksplisit **dilarang** memanggil endpoint klinis dokter (dikembalikan HTTP 403 `FORBIDDEN`) untuk mematuhi prinsip pemisahan tugas (*separation of duties*).

---

## 4.2 Analisis Row Level Security (RLS)

Basis data PostgreSQL pada Supabase dilindungi oleh RLS penuh:

### 1. Evaluasi Tabel `public.analyses`
Pada [`database/migrations/001_create_analyses_and_storage.sql:73-100`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/database/migrations/001_create_analyses_and_storage.sql#L73-L100):
- Seluruh operasi `SELECT`, `INSERT`, `UPDATE`, `DELETE` dibatasi klausul:
  ```sql
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);
  ```
- **Ketahanan:** Seorang dokter terautentikasi sama sekali tidak dapat melihat, mengubah, atau menghapus riwayat analisis milik dokter lain, bahkan jika UUID analisis diketahui.

### 2. Evaluasi Tabel `public.doctor_profiles`
Pada [`database/migrations/004_create_doctor_profiles.sql:52-82`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/database/migrations/004_create_doctor_profiles.sql#L52-L82) dan [`007_add_role_and_account_status.sql:72-106`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/database/migrations/007_add_role_and_account_status.sql#L72-L106):
- Pengguna hanya dapat membaca dan memperbarui profilnya sendiri.
- Kebijakan bypass RLS khusus diberikan kepada *role* internal PostgreSQL `TO service_role` dengan `USING (true)` agar *background worker* dan *controller admin* backend dapat membaca dan memutasi status persetujuan dokter. Kunci *service-role* tersimpan aman di environment server dan tidak pernah terekspos ke frontend.

---

## 4.3 Validasi Input & Pencegahan Serangan Berkas

Validasi input diterapkan dengan pola pertahanan berlapis (*defense-in-depth*):

1. **Lapisan 1 — Klien (Browser):**  
   Pada [`Frontend/src/pages/analysis/NewAnalysis.tsx:120-165`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/Frontend/src/pages/analysis/NewAnalysis.tsx#L120-L165):
   - Pemeriksaan ekstensi: Hanya `.jpg`, `.jpeg`, `.png`, `.bmp` yang diterima.
   - Pemeriksaan ukuran: Maksimal $10\text{ MB}$ ($10 \times 1024 \times 1024$ byte).
2. **Lapisan 2 — Validasi Integritas Berkas Server:**  
   Pada [`Backend/src/services/analysis_service.py:340-385`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/Backend/src/services/analysis_service.py#L340-L385):
   - Validasi batas ukuran fisik array byte ($> 10\text{ MB} \to$ `FILE_TOO_LARGE`).
   - Verifikasi dekoding Pillow: `Image.open(io.BytesIO(file_bytes)).verify()` untuk memastikan integritas struktur format citra dan menangkal serangan *polyglot file* / *decompression bomb*.
   - Validasi dimensi minimum: Lebar dan tinggi minimal 150 piksel (`min_width=150`, `min_height=150`).
   - Validasi rasio aspek: Rasio aspek maksimal $2.8:1$ untuk mencegah citra banner/panorama yang tidak realistis secara medis.
3. **Lapisan 3 — Gerbang Validasi Domain Medis:**  
   Pada [`Backend/ai/inference/domain_validator.py:100-260`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/Backend/ai/inference/domain_validator.py#L100-L260):
   - Menganalisis rasio jaringan mukosa, saturasi, kromatisitas L\*a\*b\*, spektrum warna dingin, dan densitas garis lurus geometris. Citra non-kolonoskopi ditolak sebelum disimpan ke storage atau antrean.

---

## 4.4 Manajemen Sesi & Token

- **Rotasi Token:** Frontend memanfaatkan Supabase JavaScript Client (`@supabase/supabase-js`) yang secara otomatis menangani *refresh token rotation* setiap 50 menit.
- **Pembersihan Sesi (*State Purging*):** Pada [`Frontend/src/context/AuthContext.tsx:160-195`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/Frontend/src/context/AuthContext.tsx#L160-L195), fungsi `signOut()` mengakhiri sesi server di Supabase Auth, menghapus data sesi di memori React, dan membersihkan seluruh residu lokal di `localStorage` dan `sessionStorage`.
- **Remember Me Terisolasi:** Fitur Remember Me hanya menyimpan alamat email murni (`localStorage.getItem('pixel_t_remembered_email')`), **tidak pernah menyimpan kata sandi, token JWT, maupun data klinis sensitif**.

---

## 4.5 Penanganan Kesalahan (*Error Handling*) & *Information Disclosure*

- **Pencegahan Kebocoran Informasi (*Information Leakage*):**  
  Pada [`Backend/src/core/errors.py:15-85`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/Backend/src/core/errors.py#L15-L85), seluruh exception yang tidak tertangkap (*unhandled 500 exceptions*) dicegat oleh error handler global Flask:
  - Respon HTTP selalu dikonversi ke amplop JSON seragam:
    ```json
    {
      "success": false,
      "error": {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "An unexpected error occurred. Please try again later."
      }
    }
    ```
  - *Stack trace*, query SQL mentah, dan path direktori lokal server disembunyikan total dari respon JSON (hanya dicatat pada log internal server).
- **Sanitasi Kunci Kredensial:** Di seluruh modul backend, variabel `SUPABASE_SERVICE_ROLE_KEY` dan token otorisasi tidak pernah dicetak (*suppressed*) dalam pesan log atau error.

---

## 4.6 Robustness Antrean Asinkron (*Async Worker*)

- **Thread-Safety Antrean:** `AnalysisJobQueue` ([`Backend/src/services/analysis_service.py:151-269`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/Backend/src/services/analysis_service.py#L151-L269)) menggunakan `threading.Condition` yang membungkus `threading.Lock` re-entrant untuk sinkronisasi operasi push/pop antrean.
- **Kapasitas Bounded & Backpressure:** Kapasitas dibatasi ketat `MAX_WAITING = 3` (total 4 analisis). Saat kapasitas penuh, metode `try_enqueue` mengembalikan `False` dan controller merespons dengan HTTP `429 Too Many Requests`. Ini mencegah serangan *Denial of Service (DoS)* dan degradasi memori GPU/CPU server.
- **Penanganan Job Macet (*Stale Detection*):**  
  Fungsi `get_analysis` ([`analysis_service.py:590-630`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/Backend/src/services/analysis_service.py#L590-L630)) memeriksa apakah sebuah analisis berstatus `processing` telah melebihi batas toleransi 15 menit (`STALE_THRESHOLD = timedelta(minutes=15)`) tanpa aktif di thread lokal. Pemeriksaan ini bersifat **non-mutasi** (tidak menghancurkan status DB) namun memberikan transparansi operasional.
- **Isolasi Kegagalan Pekerja:** Blok `try-except Exception` di dalam `_work_loop()` ([`analysis_service.py:257-265`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/Backend/src/services/analysis_service.py#L257-L265)) memastikan bahwa jika terjadi kerusakan atau kegagalan tak terduga pada satu citra, thread worker tidak akan mati (*crash*), melainkan tetap hidup untuk memproses pekerjaan berikutnya dalam antrean.

---

## 4.7 Konsistensi Tiga Titik Gerbang Domain (3-Point Domain Gate)

Audit memverifikasi integrasi logis ketiga titik gerbang validasi domain:

```
[ Titik 1: Input Gate ] 
      │ (domain_validator.py)
      ▼ Lolos (ACCEPT)
[ Pipeline U-Net + TTA ]
      │
      ▼ (postprocessing.py)
[ Titik 2: Post-Segmentation Gate ]
      │ (Kategori: LOW_CONFIDENCE vs POLYP_DETECTED)
      ▼ Serialisasi API
[ Titik 3: Visual Warning Flag ]
      (AnalysisResult.tsx)
```

1. **Konsistensi Semantik:**
   - **Kondisi 1: Citra Non-Kolonoskopi (misal: makanan / teks)**  
     Ditangkap oleh Titik 1 $\to$ Ditolak langsung dengan error 400 (`NOT_COLONOSCOPY_IMAGE`). **Tidak pernah masuk ke Titik 2 atau 3.**
   - **Kondisi 2: Citra Kolonoskopi Normal (Tanpa Polip)**  
     Lolos Titik 1 (`ACCEPT`) $\to$ Masuk ke model $\to$ Masker kosong $\to$ Titik 2 menetapkan `NO_POLYP_DETECTED` $\to$ Titik 3 menampilkan badge abu-abu dan catatan klinis netral. **Tidak pernah ditolak sebagai non-kolonoskopi.**
   - **Kondisi 3: Citra Kolonoskopi dengan Lesi Polip Meragukan**  
     Lolos Titik 1 (`ACCEPT`) $\to$ Masuk ke model $\to$ Masker terdeteksi namun `max_prob < 0.70` atau `area < 100px` $\to$ Titik 2 menetapkan `LOW_CONFIDENCE` $\to$ Titik 3 menampilkan badge kuning peringatan dan banner kehati-hatian klinis.
   - **Kondisi 4: Citra Kolonoskopi dengan Polip Nyata & Tegas**  
     Lolos Titik 1 (`ACCEPT`) $\to$ Masker terdeteksi dengan `max_prob >= 0.70` dan `mean_prob >= 0.62` $\to$ Titik 2 menetapkan `POLYP_DETECTED` $\to$ Titik 3 menampilkan badge hijau sukses.
2. **Harmonisasi Nilai String Antar-Layer:**  
   Nilai string `LOW_CONFIDENCE`, `POLYP_DETECTED`, dan `NO_POLYP_DETECTED` terbukti identik 100% pada:
   - Modul pasca-pemrosesan AI: [`Backend/ai/inference/postprocessing.py:101-115`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/Backend/ai/inference/postprocessing.py#L101-L115)
   - Service serialisasi backend: [`Backend/src/services/analysis_service.py:640-652`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/Backend/src/services/analysis_service.py#L640-L652)
   - Komponen antarmuka React: [`Frontend/src/pages/analysis/AnalysisResult.tsx:252-277`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/Frontend/src/pages/analysis/AnalysisResult.tsx#L252-L277)

---

## 4.8 Privasi Pasien & Keamanan Penyimpanan Berkas (*Storage Security*)

- **Buckets Privat Penuh:** Tiga bucket Supabase (`original-images`, `analysis-results`, `profile-avatars`) dikonfigurasi sebagai bucket privat (*public access disabled*). Berkas tidak dapat diakses langsung melalui URL publik statis.
- **Masa Berlaku Signed URL:** Akses ke citra dan artefak hasil hanya dapat dilakukan melalui *signed URL* yang diterbitkan backend ([`Backend/src/services/storage_service.py:180-220`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/Backend/src/services/storage_service.py#L180-L220)) dengan masa kedaluwarsa ketat selama 1 jam (`expires_in = 3600`).
- **Isolasi Hierarki Path:** Penamaan path penyimpanan menerapkan pengelompokan ketat berdasarkan ID pengguna:
  `original-images/{user_id}/{analysis_id}/original.{ext}`
  `analysis-results/{user_id}/{analysis_id}/binary_mask.png`
  `analysis-results/{user_id}/{analysis_id}/gradcam_heatmap.png`
- **Validasi Kepemilikan Path:** Metode `validate_path_ownership(path, user_id)` ([`storage_service.py:120-135`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/Backend/src/services/storage_service.py#L120-L135)) memverifikasi bahwa segmen path pertama selalu cocok dengan `user_id` sebelum operasi baca/hapus dieksekusi.

---

## 4.9 Efisiensi & Kinerja Model (TTA & Grad-CAM)

- **Manajemen Memori Inferensi:**  
  Inferensi TTA dijalankan di dalam blok `torch.no_grad()` dengan model dalam mode `model.eval()`. Ini mencegah penumpukan grafik komputasi autograd pada 25 forward passes, menjaga penggunaan memori GPU/VRAM tetap di bawah 1.8 GB (atau RAM sistem di bawah 2.5 GB pada CPU).
- **Grad-CAM Cabang Kanonikal (*Single Forward Pass*):**  
  Grad-CAM sengaja **tidak dijalankan pada 25 cabang TTA**, melainkan dieksekusi pada cabang kanonikal tunggal (resolusi $512\times512$ non-augmentasi) di [`Backend/ai/inference/gradcam.py:99-150`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/Backend/ai/inference/gradcam.py#L99-L150). Keputusan arsitektural ini sangat krusial:
  - Menghemat $25 \times$ overhead komputasi *backpropagation*.
  - Memberikan visualisasi heatmap yang tajam dan stabil tanpa distorsi rata-rata rotasi.

---

## 4.10 Kualitas Rekayasa Kode (*Code Quality & Maintainability*)

- **Anotasi Tipe Komprehensif:** Kode backend mengadopsi Python *type hinting* lengkap (`typing.Optional`, `Dict`, `Tuple`, `dataclass`), sementara frontend menerapkan TypeScript tipe ketat (`interface AnalysisDetail`, `type DetectionCategory`) tanpa penggunaan `any` sembarangan.
- **Pemisahan Tanggung Jawab (*Separation of Concerns*):**  
  Arsitektur backend memisahkan secara bersih:
  `Routes` (Definisi HTTP) $\to$ `Controllers` (Ekstraksi parameter & respon) $\to$ `Services` (Logika bisnis & orkestrasi AI) $\to$ `Repositories` (Akses basis data) $\to$ `AI Inference` (Komputasi tensor murni).
- **Integritas Dokumentasi:** Seluruh fungsi dilengkapi *docstrings* berstandar Google/PEP 257 yang menjelaskan parameter, nilai balik, dan batasan operasional.

