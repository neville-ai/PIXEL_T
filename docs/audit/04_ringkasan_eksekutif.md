# RINGKASAN EKSEKUTIF AUDIT KOMPREHENSIF WEB PIXEL-T & REKOMENDASI TINDAK LANJUT

**Tanggal:** 9 November 2026  
**Status Audit:** READ-ONLY SYSTEM AUDIT — TUNTAS  
**Dokumen:** `docs/audit/04_ringkasan_eksekutif.md`  
**Direktori Dokumen Pendukung:** [`docs/audit/`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/docs/audit/)  
- `00_peta_sistem.md` — Peta Sistem, Arsitektur, Inventaris Route, Database & RLS
- `01_tindak_lanjut_fase_b.md` — Analisis Mendalam Gerbang Validasi Domain Kolonoskopi
- `02_kesesuaian_skripsi_vs_kode.md` — Audit Kesesuaian Skripsi vs Implementasi Kode Aktual
- `03_audit_kode_dan_keamanan.md` — Audit Kualitas Rekayasa Kode, Keamanan, dan Robustness

---

## 5.1 Ringkasan Temuan & Rekomendasi Utama

1. **Keunggulan Empiris Kandidat 2 Gerbang Validasi Domain:**
   - Kandidat 2 berhasil menurunkan angka penolakan keliru (*False Rejection Rate* / FRR) pada citra kolonoskopi positif dari **8.59%** (Baseline) menjadi **3.91%** (95% CI: $[1.68\%, 8.82\%]$).
   - Sebanyak **6 citra kolonoskopi resolusi tinggi (BKAI & HyperKvasir)** yang sebelumnya salah ditolak oleh Baseline terselamatkan sepenuhnya ke status `ACCEPT`.
   - Angka penerimaan keliru (*False Acceptance Rate* / FAR) pada kelompok negatif utama tetap terkunci di **12.73%** (95% CI: $[6.30\%, 24.02\%]$) tanpa ada citra non-endoskopi (`makanan`, `orang`, `dokumen`, `medis_lain`) yang bocor menjadi `ACCEPT`.
2. **Eliminasi Artefak Ketergantungan Resolusi:**
   - Ketergantungan resolusi $G5_{warm}$ terbukti secara matematis merupakan artefak algoritma deteksi garis Hough pada citra resolusi tinggi ($r = +0.2896, p < 0.001$).
   - Penerapan **skala normalisasi kanonikal 256** berhasil memutus korelasi ini sepenuhnya ($r = +0.0404, p = 0.651$, 95% CI: $[-0.134, +0.212]$).
   - *Parameter sweep* membuktikan ambang 12.0 pada Kandidat 2 berada di zona plato aman optimal (9..14) dengan margin toleransi $\Delta = 3.70$ di atas sampel biologis maksimum (8.30).
3. **Klarifikasi Arsitektur AI (U-Net ResNet-50 Tunggal):**
   - Sistem PIXEL-T **tidak menggunakan dua model paralel** (sebagaimana kekeliruan narasi pada naskah draf skripsi awal).
   - Model adalah **satu arsitektur terpadu U-Net dengan encoder ResNet-50 dan modul atensi scSE**. Peta Grad-CAM diekstraksi langsung dari lapisan konvolusi akhir *decoder* (`decoder.blocks.4.conv2.0`) terhadap logit polip.
4. **Integritas Nol Perubahan Produksi (B0 Kuat Terverifikasi):**
   - Pengujian regresi B0 pada 12 citra kolonoskopi membuktikan selisih piksel masker biner **0 piksel**, skor Dice **1.000000**, dan selisih probabilitas **0.000000** (100% identik).
   - Seluruh 11 berkas produksi utama memiliki nilai hash SHA-256 yang identik dengan baseline awal.

---

## 5.2 Tabel Prioritas Discrepancy & Perbaikan

| Prioritas | Kategori | Deskripsi Isu | Lokasi Berkas / Bab | Rekomendasi Tindakan |
| :---: | :---: | :--- | :--- | :--- |
| **TINGGI** | **Revisi Skripsi** | Narasi naskah menyebutkan dua model paralel (U-Net untuk segmentasi dan ResNet-50 untuk klasifikasi/Grad-CAM). | Bab II, Bab IV, Bab V, `SPESIFIKASI_TUJUH_USE_CASE_PIXELT.md` | Revisi narasi menjadi satu model terpadu U-Net ber-backbone encoder ResNet-50 + scSE decoder attention. |
| **TINGGI** | **Perbaikan Kode** | Algoritma $G5_{warm}$ baseline salah menolak citra kolonoskopi HD valid akibat artefak resolusi. | `Backend/ai/inference/domain_validator.py:175-239` | Terapkan perubahan **Kandidat 2** (skala normalisasi 256 + ambang 12.0 + G4 edukatif) pada Fase C. |
| **TINGGI** | **Revisi Skripsi** | Diagram Use Case awal (7 use case) belum mencerminkan pemisahan hak akses peran Admin dan Dokter. | Bab IV (Use Case Diagram & Spesifikasi) | Adopsi diagram 14 use case hasil audit (`USE_CASE_DIAGRAM_PIXELT_AUDIT_REVISED`) yang memisahkan peran dokter dan admin. |
| **SEDANG** | **Revisi Skripsi** | Naskah belum merinci mekanisme Test-Time Augmentation (TTA) secara matematis. | Bab IV & Bab V | Tambahkan dokumentasi bahwa inferensi menjalankan 25 forward passes (5 skala $\times$ 5 orientasi) untuk kestabilan tepi polip. |
| **SEDANG** | **Perbaikan Kode** | Batas ukuran file 10 MB mengembalikan kode HTTP 400 bukannya semantik RFC 413 Payload Too Large. | `Backend/src/services/analysis_service.py:345` & `Frontend/src/pages/analysis/NewAnalysis.tsx:255` | Sinkronkan kontrak HTTP ke status 413 pada backend, penanganan error frontend, dan test suite. |
| **SEDANG** | **Revisi Skripsi** | Class diagram Bab IV memuat controller yang diimplementasikan langsung via Supabase RLS. | Bab IV (Class Diagram) | Jelaskan adopsi arsitektur hybrid BaaS (Supabase RLS untuk profil, Flask untuk pipeline AI berat). |
| **RENDAH** | **Konfigurasi** | Berkas residual `"python check_calib.py"` berada di root repositori. | Root directory | Pertahankan berkas selama masa audit; bersihkan hanya jika ada instruksi tertulis khusus git clean. |

---

## 5.3 Daftar Terpisah Rekomendasi

### DAFTAR A: Revisi Naskah Skripsi
1. **Bab II & Bab IV (Kajian Pustaka & Desain Arsitektur):**
   - Hapus klaim bahwa sistem memuat "dua model deep learning terpisah".
   - Jelaskan struktur resmi: `segmentation_models_pytorch.Unet` ber-encoder `resnet50` pra-latih ImageNet dengan `decoder_attention_type='scse'`.
   - Paparkan bahwa Grad-CAM diekstraksi dari konvolusi akhir decoder U-Net (`decoder.blocks.4.conv2.0`) dengan target fungsi objektif nilai rata-rata logit area polip.
   - Cantumkan nilai ambang klasifikasi biner $threshold = 0.55$.
2. **Bab IV (Pemodelan Sistem UML):**
   - Gunakan pembaruan **14 Use Case** (3 Aktor: Pengguna Baru, Dokter Terverifikasi, Administrator).
   - Masukkan alur pendaftaran dokter yang melewati status `pending` hingga disetujui administrator pada Activity Diagram dan Sequence Diagram.
   - Perbarui Class Diagram sesuai spesifikasi [`CLASS_DIAGRAM_FINAL_PIXELT.puml`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/references/bab 4/CLASS_DIAGRAM_FINAL_PIXELT.puml).
   - Jelaskan bahwa entitas Admin disimpan pada klaim server `app_metadata.role = 'admin'` di Supabase Auth, bukan tabel fisik terpisah.
3. **Bab V (Implementasi & Pengujian):**
   - Dokumentasikan hasil pengujian komparatif gerbang domain: penurunan FRR dari 8.59% ke 3.91% berkat normalisasi skala kanonikal 256.
   - Sajikan bukti empiris pemutusan korelasi resolusi ($r = +0.2896, p < 0.001 \to r = +0.0404, p = 0.651$).
   - Masukkan tabel pengujian Tiga Titik Gerbang Domain (Domain Input Gate $\to$ Post-Segmentation Validation $\to$ Visual Warning Flag).

---

### DAFTAR B: Rencana Perbaikan Kode (Fase C Setelah Persetujuan)
1. **Penerapan Kandidat 2 pada `domain_validator.py`:**
   - Menambahkan langkah resizing kanonikal ke `norm_scale = 256` pada fungsi deteksi garis lurus Hough ($G5$).
   - Menyesuaikan ambang $G5_{warm}$ menjadi $12.0$ dengan penalti berkelanjutan (*soft penalty*) pada skor keyakinan komposit.
   - Mengalihkan penanganan citra desaturasi $G4_{chroma}$ dari penolakan mutlak (*Hard REJECT*) menjadi status *UNCERTAIN* edukatif agar klinisi dapat meninjau citra dengan peringatan kehati-hatian.
2. **Penyempurnaan Semantik Kontrak Error:**
   - Memutakhirkan status HTTP pada `FILE_TOO_LARGE` dari 400 menjadi 413, disinkronkan dengan penanganan di `NewAnalysis.tsx` dan `test_analysis.py`.
3. **Regresi Penuh Otomatis:**
   - Menjalankan seluruh test suite (`pytest tests/ai tests/backend` dan `npm run test`) untuk memverifikasi ketiadaan efek samping (*side-effects*).

---

## 5.4 Daftar Item yang Belum Terverifikasi / Butuh Verifikasi Tambahan

1. **Citra Khusus `in_vivo_blur/calib/rbHvgkREHO...jpg`:**
   - Berkas memiliki nama sangat panjang (196 karakter, 292 karakter absolut) dan ditolak oleh gate G3 (`cool_ratio = 0.654 > 0.40`). Citra ini secara visual menampakkan penyinaran kebiruan/NBI. Perlu verifikasi visual manual oleh pengguna/klinisi untuk memastikan apakah citra ini merupakan WLE sejati dengan artefak kamera ataukah rekaman NBI murni.
2. **Subfolder `holdout` Kalibrasi:**
   - Sesuai batasan etis ketat instruksi audit, seluruh subfolder `holdout` **tidak pernah dibuka atau dibaca sama sekali**. Evaluasi pada dataset holdout akan dieksekusi secara independen pada Fase C setelah rancangan kode disetujui.

---

## 5.5 Rekomendasi Pelaksanaan Fase C

Urutan langkah implementasi teknis Fase C yang direkomendasikan:
1. **Langkah 1:** Pengguna memberikan persetujuan tertulis untuk mengadopsi **Kandidat 2**.
2. **Langkah 2:** Memperbarui berkas `Backend/ai/inference/domain_validator.py` untuk mengintegrasikan normalisasi skala 256, ambang $G5_{warm} = 12.0$, dan perlakuan $G4$ UNCERTAIN edukatif.
3. **Langkah 3:** Menjalankan `tests/ai/test_model_integration.py` dan `tests/Backend/test_analysis.py` untuk memastikan seluruh tes unit dan integrasi lulus 100%.
4. **Langkah 4:** Membuka dan mengevaluasi subfolder `holdout` pada `calibration_data` sebagai pengujian akhir *out-of-sample generalization*.
5. **Langkah 5:** Melakukan kompilasi laporan akhir Fase C.

---

## 5.6 Verifikasi Akhir Integritas Repositori

Audit ditutup dengan verifikasi independen hash kriptografis SHA-256 seluruh berkas produksi terhadap baseline awal:

```
Backend/ai/inference/pipeline.py:                      07e776fb0779760fa764c54b6535c407edc5d07c44c92f14c6c19fa44e4c0ca4 (IDENTIK)
Backend/ai/inference/postprocessing.py:                9d5f965fed2b6f87d91b76b48ca427785f1224b5e533731a49af053952ac9cf1 (IDENTIK)
Backend/src/core/config.py:                    5be1031f727d4f5b729639f0e2ca2298a172c23ce14c07d748f6c084a55def3a (IDENTIK)
Backend/src/services/analysis_service.py:       e8037b2641be4e3add0add797c81a2b98d715227118dbf48a22262db3d68e861 (IDENTIK)
Frontend/src/pages/analysis/AnalysisResult.tsx: d153369c05bbc6fb12d214fad6a566ec28424730e5ab6186c7e08e235c0bf3e8 (IDENTIK)
Frontend/src/pages/analysis/NewAnalysis.tsx:    7e1c035c5640070966cb84e04d2cf78092410dc6596f7f62bc091f2927a582b0 (IDENTIK)
Frontend/src/utils/analysis.ts:             9ee6f0e5b6a4b363f94ac48442845d82877d84d2dd03808e3639680d35f33dbf (IDENTIK)
tests/ai/test_model_integration.py:            56d226fff12ac34998be90f73c4fe37e0f36543c934bb66d7fbf1ca5666755c5 (IDENTIK)
tests/Backend/test_analysis.py:                 e79fec87cf4858888432c5f6ead7ec7da6c24100dbb7dcb92ab72874ad113818 (IDENTIK)
tests/conftest.py:                             e2fd03e02b9920fc002da07ba85fea4fca1bab876e642e22b9be13d002235b8c (IDENTIK)
Backend/ai/inference/domain_validator.py:              c6caca64d4f7166afd85af82f9f8ea5022ef8639c1aeda578ae1e778f2d03b47 (IDENTIK)

STATUS INTEGRITAS KODE PRODUKSI: 100% IDENTIK DAN BERSIH (ZERO MUTATION)
```

**STATUS TUGAS:** SELURUH DOKUMEN AUDIT TELAH SELESAI DISUSUN. SISTEM BERHENTI DI SINI DAN MENUNGGU INSTRUKSI / PERSETUJUAN TERTULIS DARI PENGGUNA SEBELUM MEMASUKI FASE C.

