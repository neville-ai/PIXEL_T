# MANUAL E2E TEST PLAN — PIXEL-T

**Tanggal:** 11 November 2026  
**Branch:** `fitur/validasi-input` (HEAD `cbb5296`)  
**Versi aplikasi:** setelah tahap cleanup (tidak ada commit/push)  
**Skala:** pengujian manual end-to-end pada lingkungan nyata (backend + frontend + Supabase + Gemini)  
**Catatan utama:** jangan mengarang hasil pengujian. Setiap baris berstatus `NOT TESTED` sampai benar-benar dijalankan dan diisi oleh penguji. Laporan ini read-only terkait kode: **tidak ada perubahan file proyek** pada tahap ini.

---

## 0. Kesiapan Lingkungan (prasyarat)

| Item | Kondisi terverifikasi |
|---|---|
| Backend `.env` (Backend/.env) | Tersedia; kredensial Supabase & Gemini terisi (nilai tidak dicetak) |
| Frontend `.env` (Frontend/.env) | Tersedia; VITE_SUPABASE_URL, VITE_SUPABASE_ANON_KEY, VITE_API_BASE_URL terisi |
| Supabase Auth health | HTTP 200 (terjangkau) |
| Supabase Storage bucket | HTTP 200 via service role (`analysis-assets`) |
| Gemini SDK | google-genai 3.0.0 terpasang; `models.list()` dan `models.get(model)` OK |
| Model checkpoint | Hash SHA-256 cocok `46521AE9…B581`, size 135.644.553 B |
| MODEL_INFERENCE_ENABLED | `true` |
| DOMAIN_VALIDATION_ENABLED | `true` |
| LLM_VALIDATION_ENABLED | `true` |
| LLM_VALIDATION_TIMEOUT_S | `30.0` s |
| Port 5000 / 5173 | Belum LISTEN (belum dijalankan) |

---

## 1. Cara Menjalankan Aplikasi (2 Terminal)

**Terminal 1 — Backend (port 5000):**
```bash
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r requirements.txt
python run.py
```
Health check: `GET http://localhost:5000/api/health`

**Terminal 2 — Frontend (port 5173):**
```bash
cd frontend
npm run dev
```
Aplikasi: `http://localhost:5173`

> Catatan: jalankan keduanya **dari direktori masing-masing** agar `Backend/.env` dan `Frontend/.env` terbaca. Model checkpoint sudah ada di `Backend/ai/models/`.

---

## 2. Daftar Pengujian Berurutan

**Keterangan status:** `NOT TESTED` | `PASS` | `FAIL` | `BLOCKED`  
**Tipe:** `A` = dapat diverifikasi otomatis (curl/skrip) | `M` = harus dilakukan melalui browser secara manual  
**Hasil aktual & bukti:** diisi oleh penguji saat menjalankan tes.

| No | Pengujian | Tipe | Langkah | Hasil yang diharapkan | Hasil aktual | Status | Bukti yang dicatat |
|---|---|---|---|---|---|---|---|
| 1 | Backend & frontend startup | A/M | (a) Jalankan backend di port 5000 dan frontend di port 5173.<br>(b) `curl -i http://localhost:5000/api/health`<br>(buka `http://localhost:5173` di browser) | Backend responde HTTP 200 di `/api/health`; frontend tampil tanpa error konsol fatal; kedua port LISTEN | | NOT TESTED | screenshot health check + halaman utama |
| 2 | Login dan autentikasi | M | Buka halaman Login; masukkan kredensial akun yang telah terdaftar di Supabase Auth | Login berhasil; redirect ke halaman yang sesuai per role; halaman terlindungi tidak bisa diakses tanpa login; sesi bertahan setelah refresh | | NOT TESTED | screenshot dashboard setelah login + pesan error jika gagal |
| 3 | Upload citra kolonoskopi | M | Pilih citra kolonoskopi valid (JPG/PNG, ≤10 MB); klik "Start analysis" | File diterima; respons HTTP 202 berisi `analysis_id` dan `status: processing`; panel progres muncul; polling ke backend berjalan otomatis | | NOT TESTED | analysis_id + status polling + waktu respons |
| 4 | Penolakan citra non-kolonoskopi | M | Unggah citra bukan kolonoskopi (mis. citra kulit, mata, dokumen, radiologi) | Ditolak dengan kode error `NOT_COLONOSCOPY_IMAGE` (Domain Validation fail-closed); citra **tidak** melewati gate ke Gemini | | NOT TESTED | kode error + pesan yang ditampilkan |
| 5 | Validasi Gemini | M | Unggah citra kolonoskopi yang lolos Domain Validation heuristik | Citra divalidasi oleh Gemini Gate (model `gemini-3.8-flash`, timeout 30 s, `min_confidence` 0.80); hasil terima/tolak sesuai respons Gemini & skema | | NOT TESTED | status Gemini (ACCEPT/REJECT/UNCERTAIN) + confidence |
| 6 | Segmentasi polip (U-Net + ResNet50) | M | Tunggu pipeline selesai (status `completed`) | Mask biner polip muncul; overlay terlihat; threshold 0.55 diterapkan (tidak diubah); TTA aktif | | NOT TESTED | screenshot mask + overlay; `segmentation_status` |
| 7 | Metrik hasil (Dice / IoU) | M | Lihat panel hasil segmentasi | Nilai metrik ditampilkan sesuai apa yang dikirim backend (tidak dicermbau/dikarang); jika backend tidak menyediakan per-citra, panel menampilkan status tersedia tanpa angka buatan | | NOT TESTED | nilai metrik yang ditampilkan + sumbernya |
| 8 | Grad-CAM | M | Lihat visualisasi penjelasan model | Grad-CAM heatmap & overlay berhasil dibuat dan ditampilkan bersamaan dengan hasil segmentasi | | NOT TESTED | screenshot Grad-CAM heatmap + overlay |
| 9 | Riwayat analisis | M | Buka halaman History setelah analisis selesai | Hasil analisis tersimpan dan dapat dibuka kembali dengan data lengkap (mask, overlay, Grad-CAM, ringkasan) | | NOT TESTED | daftar riwayat + detail analisis yang dibuka |
| 10 | Hapus analisis | M | Pilih analisis pada History; aksi hapus | Data terhapus sesuai mekanisme aplikasi (DELETE `/history/<id>`); item tidak muncul lagi di daftar | | NOT TESTED | konfirmasi penghapusan + daftar History setelahnya |

### 2.1 Skenario Khusus Fail-Closed (Gemini)

Pemeriksaan ini adalah bagian dari Tes 4–6 dan harus diuji jika memungkinkan:

| No | Skenario | Langkah singkat | Hasil yang diharapkan (fail-closed) | Status | Bukti |
|---|---|---|---|---|---|
| A | Gemini timeout | Simulasi respons Gemini melebihi batas waktu 30 s | Citra **tidak** lolos validasi; dikembalikan `UNCERTAIN_COLONOSCOPY_IMAGE` atau ditolak; tidak pernah `ACCEPT` | NOT TESTED | pesan error/waktu habis |
| B | API key Gemini tidak valid | Gunakan kunci tidak valid (tidak dicetak di laporan) | Gate gagal; citra tidak lolos validasi; tidak pernah `ACCEPT` | NOT TESTED | kode error generic (tanpa kunci) |
| C | Respons Gemini tidak sesuai skema | Respons JSON tidak memenuhi `response_schema` (`is_colonoscopy`, `confidence`, `image_type`) | Gate menolak respons; citra tidak lolos validasi | NOT TESTED | deskripsi kegagalan skema |

> Prinsip fail-closed: di semua kondisi di atas, citra **boleh ditolak** tetapi **tidak boleh lolos** ke segmentasi.

---

## 3. Otomatisasi vs Manual

| Tipe | Contoh | Cara |
|---|---|---|
| **Otomatis (A)** | Startup backend, health check `/api/health`, koneksi Supabase/Gemini | curl / skrip Python (sudah diverifikasi di tahap cleanup) |
| **Manual (M)** | Login, upload citra, penolakan non-kolonoskopi, Gemini, segmentasi, Grad-CAM, riwayat, hapus | Browser; tes ini baru akan dijalankan penguji |

---

## 4. Urutan Pelaksanaan yang Direkomendasikan

Jalankan **secara berurutan** agar sumber kegagalan mudah ditemukan:

1. Tes 1 — Startup backend & frontend (jika gagal, hentikan; periksa log & port).
2. Tes 2 — Login & autentikasi (jika gagal, periksa Supabase Auth & `.env` frontend).
3. Tes 3 — Upload citra kolonoskopi (jika gagal, periksa storage bucket & worker).
4. Tes 4 — Penolakan citra non-kolonoskopi (verifikasi Domain Validation fail-closed).
5. Tes 5 — Validasi Gemini (verifikasi gate kedua).
6. Tes 6–8 — Segmentasi, metrik, Grad-CAM (verifikasi pipeline AI).
7. Tes 9 — Riwayat analisis (verifikasi penyimpanan & pembukaan kembali).
8. Tes 10 — Hapus analisis (verifikasi DELETE).
9. Skenario A–C (fail-closed) jika memungkinkan disimulasikan.

---

## 5. Catatan

- Tidak ada file proyek yang diubah, dihapus, atau di-commit pada tahap ini.
- Nilai kredensial (API key, token, password, isi `.env`) **tidak dicetak** dalam laporan ini maupun bukti pengujian.
- Semua `Hasil aktual` dan `Status` diisi setelah pengujian nyata; status awal seluruhnya `NOT TESTED`.
