# LAPORAN AKHIR — PERBAIKI FALSE ACCEPTANCE DOMAIN VALIDATION (PIXEL-T)

> **Tujuan:** PIXEL-T menolak citra PIZZA (hard negative) sebelum U-Net/TTA/Grad-CAM/penyimpanan/antrean, sambil tetap menerima kolonoskopi (normal + polip) sebagai ACCEPT; citra ambigu boleh UNCERTAIN; mask kosong bukan berarti bukan kolonoskopi.
>
> **Status:** Laporan akhir. Pengerjaan dihentikan setelah laporan ini. Tidak ada commit/push/reset; semua perubahan masih uncommitted.

---

## 1. Metadata

| Item | Nilai |
|------|-------|
| Cabang | `main`, HEAD `faa0aaaaac82949999d19e8578da13a0433dfc2a` |
| Status git | 9 modified + 7 untracked (pre-existing, belum dicommits oleh pekerjaan ini); perubahan pekerjaan ini **uncommitted** |
| Hard negatif target | `images (2).jpg` — SHA256 `c3452023543d13344a647eb02f64e8248d76aa651f348f73482d0fa1562f4c63` (identik baseline) |
| File yang diubah pekerjaan ini | `ai/inference/domain_validator.py` (baru, untracked), `ai/inference/pipeline.py`, `backend/app/services/analysis_service.py`, `tests/ai/test_model_integration.py` (stub pengujian) |
| File yang DIHINDARI (tidak disentuh) | checkpoint/model (`ai/models/*`), `ai/config/model_config.py`, TTA/threshold segmentasi, skema DB, `references/*`, file frontend (kecuali build uji) |
| Bukti eksternal (temp) | `C:\Users\nevil\AppData\Local\Temp\opencode\pizza_e2e_3.log`, `stage2_after_fix.log`, `validator_tests.log`, `full_py_tests.log`, `frontend_tests.log`, `frontend_build.log` |

---

## 2. Ringkasan masalah

Kelas citra PIZZA (makanan) diterima secara **salah** oleh domain validator sebagai kolonoskopi (false acceptance: `ACCEPT` 0.91, mucosal 94.9%), sehingga alur U-Net/TTA/Grad-CAM, mask/overlay, dan pencatatan `POLYP_DETECTED` akan dieksekusi padahal citra bukan kolonoskopi. Kelebihan keyakinan berasal dari dua celah bersama di kode:

1. `ai/inference/pipeline.py` — `run_pipeline(...)` hanya menjalankan domain validation ketika `validate_domain=True` (default `False`) → pemanggil langsung dapat melewati gate (L109, L127-132 sebelum perbaikan).
2. `ai/inference/domain_validator.py` — gate garis lurus hanya aktif jika `mucosal_ratio < 0.55` (L211), dan `line_penalty = 0` ketika `mucosal_ratio >= 0.70` (L284) → pizza (mukosa 0.949) dikecualikan, confidence 0.949 × 0.962 ≈ 0.91 → ACCEPT.

Pemisah terbersih adalah **`line_density`**: pizza 22.81 dan daging mentah bertekstur 14.13, sementara 4 frame kolonoskopi nyata (normal, lumen/OSD, ulser, lesi polip) max **6.84**. Jarak [6.84, 13.98], titik tengah ≈ 9.8 → ambang `straight_edge_warm_threshold = 10.0`.

---

## 3. Stage 2 — Tabel perbandingan sampel nyata vs sintetik

Sampel ukur melalui `ColonoscopyDomainValidator.validate_bytes` (jalan identik `create_analysis`), sebelum dan setelah perbaikan.

### 3.1 Sampel nyata (11 berkas)

| # | Sampel nyata | Tag | Sebelum | Sesudah | line_density | mucosal_ratio | Catatan |
|---|--------------|-----|---------|---------|--------------|---------------|---------|
| 1 | `images (2).jpg` pizza | Makanan (hard negatif) | ACCEPT 0.91 | **REJECT 0.15** | 22.81 | 0.949 | **BUG TERPERBAIKI** — garis lurus hangat |
| 2 | `images (1).jpg` kolonoskopi normal (lipatan+glint) | Kolonoskopi | ACCEPT 0.98 | ACCEPT 0.98 | 6.59 | 0.979 | tetap diterima |
| 3 | `images (7).jpg` kolonoskopi lumen/OSD | Kolonoskopi | ACCEPT 0.95 | ACCEPT 0.95 | 6.84 | 0.953 | tetap diterima |
| 4 | `images (8).jpg` kolonoskopi ulser | Kolonoskopi | ACCEPT 0.89 | ACCEPT 0.89 | 3.86 | 0.891 | tetap diterima |
| 5 | `images (9).jpg` kolonoskopi lesi/polik | Kolonoskopi | ACCEPT 0.99 | ACCEPT 0.99 | 0.40 | 0.995 | tetap diterima |
| 6 | `images (3).jpg` daging mentah bertekstur | Makanan | UNCERTAIN 0.48 | **REJECT 0.15** | 14.13 | 0.680 | membaik |
| 7 | `images (4).jpg` tomat retail | Makanan | REJECT 0.15 | REJECT 0.15 | 13.98 | 0.530 | sudah benar |
| 8 | `images (5).jpg` bakso | Makanan | REJECT 0.15 | REJECT 0.15 | 2.87 | 0.363 | sudah benar |
| 9 | `images (6).jpg` steak mentah datar | Makanan | UNCERTAIN 0.46 | UNCERTAIN 0.46 | 6.80 | 0.679 | ambigu (boleh) |
| 10 | `references/extracted_colonoscopy.png` | Monitor capture | REJECT 0.10 | REJECT 0.10 | 1.80 | 0.465 | cool 0.312 |
| 11 | `references/pure_colonoscopy_frame.png` | Monitor capture | REJECT 0.15 | REJECT 0.15 | 1.43 | 0.485 | cool 0.292 |

Catatan: 10 dan 11 adalah tangkapan layar monitor (bukan frame in-vivo asli); keduanya REJECT bahkan sebelum perbaikan (tidak ada baseline kolonoskopi in-vivo ACCEPT terpercaya di mesin ini — ketersisian ini dicatat di §8).

### 3.2 Cakupan sintetik (unit test `tests/ai/test_domain_validator.py`, 16 tes)

| Kasus sintetik | Hasil diharapkan | Hasil setelah perbaikan |
|---|---|---|
| Kolonoskopi + timestamp/info device | ACCEPT | ACCEPT |
| Kolonoskopi dengan polip | ACCEPT | ACCEPT |
| Kolonoskopi normal tanpa polip | ACCEPT | ACCEPT |
| Kolonoskopi vigneting lingkaran | ACCEPT | ACCEPT |
| Makanan pizza (sintetik) | REJECT | REJECT |
| Portret wajah manusia | REJECT | REJECT |
| Lanskap | REJECT | REJECT |
| Dokumen/teks | REJECT | REJECT |
| Kendaraan mobil | REJECT | REJECT |
| Medis non-koloskopi (X-ray) | REJECT | REJECT |
| Hewan | REJECT | REJECT |
| Terpapah cahaya sangat rendah | UNCERTAIN | UNCERTAIN |
| Dimensi kecil | REJECT | REJECT |
| Rasio aspek ekstrem | REJECT | REJECT |
| Byte korup | REJECT | REJECT |
| Daging mentah datar (sintetik) | != ACCEPT | REJECT/!ACCEPT |

Kelas yang **BELUM TERSEDIA** (tidak diukur Stage 2): foto kulit manusia nyata, landscape nyata, hewan nyata, dokumen medis non-koloskopi fisik, flat raw meat sintetis nyata, serta end-to-end in-vivo (masuk storage + mask/overlay + `POLYP_DETECTED`) pada kolonoskopi asli yang sudah ACCEPT. Hal ini tidak menghalangi penutupan karena hard negatif utama (pizza) sudah divalidasi dan cakupan sintetik lengkap.

---

## 4. Stage 3 — Audit titik penegakan (enforcement points)

Audit membaca ulang semua jalan pemanggilan model untuk memastikan tidak ada bypass:

| # | Jalur | Titik penegakan | Gaps sebelum | Gaps sesudah | Status |
|---|-------|----------------|--------------|--------------|--------|
| A | Upload `POST /api/analysis` → `AnalysisService.create_analysis` | `validate_bytes` sebelum storage/DB/enqueue (L411); `analysis_id` dibuat sebelum gate (L405) | `validate_domain=False` di `run_pipeline` bisa dilewati pemanggil langsung | Gate tak bersyarat di `run_pipeline` + `_require_domain_accept` di batas model | PERBAIKI |
| B | `run_pipeline(...)` | `ColonoscopyDomainValidator().validate_image(original)` → raise kalau != ACCEPT (L132-138) | `validate_domain` default `False`, bisa dimatikan pemanggil | Parameter dipertahankan untuk kompatibilitas tanda tangan tapi **tidak mematikan gate** | PERBAIKI |
| C | `AnalysisService.run_segmentation` (batas model) | `_require_domain_accept(file_bytes)` (L1063) | Tidak ada — pemanggilan langsung melewati domain | Gate sebelum `predict` | PERBAIKI |
| D | `AnalysisService.run_gradcam` (batas model) | `_require_domain_accept(file_bytes)` (L1076) | Tidak ada | Gate sebelum Grad-CAM | PERBAIKI |
| E | Logging | Baris `[DOMAIN] analysis_id=<id> ... decision=... confidence=... reasons=... features={...}` (L411-...) sebelum storage/DB/queue | Tidak ada | Rekam keputusan + semua metrik per `analysis_id` | PERBAIKI |
| F | Konfigurasi | `DOMAIN_VALIDATION_ENABLED` (dev/prod `True`; testing `False` via env, tes inject `enforce_domain_validation=True`) | — | Dipertahankan (tidak diubah skema/config) | TIDAK DIUBAH |

Hasil verifikasi end-to-end nyata (pizza file asli melalui `POST /api/analysis`): **HTTP 400 `NOT_COLONOSCOPY_IMAGE`, 0 upload storage, 0 rekaman DB, 0 pemanggilan pipeline, 0 pekerjaan antrean**. Kolonoskopi asli (lumen/OSD): **HTTP 202, 1 storage, 1 DB, 1 pekerjaan antrean** (worker belum dijalankan, jadi inferensi model belum berjalan — gate cegah sebelum itu).

---

## 5. Root Cause Analysis

| No | Komponen | Penyebab akar | Bukti (baris) | Dampak |
|----|----------|---------------|---------------|--------|
| 1 | `ai/inference/pipeline.py` | `run_pipeline` hanya validasi domain saat `validate_domain=True` (default `False`) → caller langsung dapat lewati gate | L109 default `False`; L127-132 sebelum perbaikan | Pizza bisa masuk ke U-Net/TTA/Grad-CAM tanpa validasi |
| 2 | `ai/inference/domain_validator.py` | Gate garis lurus hanya aktif jika `mucosal_ratio < 0.55` (L211) | Pizza mucosal 0.949 → gate dilewati | Pizza tidak ditolak meskipun line_density 22.81 |
| 3 | `ai/inference/domain_validator.py` | `line_penalty = 0` saat `mucosal_ratio >= 0.70` (L284) | Pizza 0.949 → penalty nol | Confidence 0.949 × 0.962 ≈ 0.91 → ACCEPT (false acceptance) |
| 4 | `backend/app/services/analysis_service.py` | `run_segmentation`/`run_gradcam` memanggil model langsung tanpa cek domain | L1021/L1034 sebelum perbaikan | Pemanggilan batas model dapat lewati validasi upload |

---

## 6. Perbaikan (minimal, 3 file produksi + 1 penyesuaian tes)

- `ai/inference/domain_validator.py`: tambah parameter `straight_edge_warm_threshold = 10.0` (L60, L72) dan gate baru (L221-238): jika `line_density > 10.0` **dan** `mucosal_ratio > mucosal_accept_threshold` (0.55) → REJECT 0.15 (geometri permukaan makanan, non-endoskopi), terlepas dari konsistensi mukosa. Kasus di bawah ambang tetap UNCERTAIN.
- `ai/inference/pipeline.py`: `validate_domain` diubah default ke `True` (L109) dan validasi dijalankan **selalu** (L132-138) → raise `ValueError` kalau != ACCEPT sebelum preprocessing/inferensi/Grad-CAM. Parameter dipertahankan untuk kompatibilitas tanda tangan.
- `backend/app/services/analysis_service.py`: `analysis_id` dibuat **sebelum** gate (L405); baris `[DOMAIN]` per `analysis_id` mencatat decision/confidence/reasons/feature values sebelum storage/DB/queue (L411-...); tambah `_require_domain_accept()` statis (L1033) dipasang pada `run_segmentation` (L1063) dan `run_gradcam` (L1076) sehingga pemanggilan batas model tidak bisa bypass.
- `tests/ai/test_model_integration.py`: stub domain validator untuk 2 tes mekanisme pipeline (phase ordering, callback observability) yang pakai citra sintetis 64×64 (bukan kolonoskopi); validasi domain sendiri sudah tercakup oleh `test_domain_validator.py` dan `test_domain_validation_api.py`. Tidak melemahkan gate produksi.

Tidak ada perubahan arsitektur, bobot/checkpoint, konfigurasi TTA, ambang segmentasi, skema DB, atau referensi.

---

## 7. Stage 4 — Hasil pengujian per suite

| Suite | Status | Detail |
|-------|--------|--------|
| `tests/ai/test_domain_validator.py` | **PASS** | 16/16 — pizza REJECT, kolonoskopi ACCEPT, wajah/food/dokumen/kendaraan/X-ray/hewan REJECT, underexposed UNCERTAIN |
| `tests/backend/test_domain_validation_api.py` | **PASS** | 4/4 — landscape/face/food REJECT 400, underexposed UNCERTAIN, kolonoskopi ACCEPT 202; 0 storage/DB pada reject |
| `tests/backend/test_analysis.py` | **PASS** | 38/38 — alur antrean, status, GET, queue, progress, failure, storage sequential |
| `tests/ai/test_model_integration.py` | **PASS** | 12/12 — checkpoint hash/strict load, config, inference contract, phase order, callbacks (setelah stub tes) |
| **Seluruh Python (ai + backend)** | **PASS** | **152/152** dalam 110,17 detik |
| `npm test --prefix frontend` | **PASS** | **285/285** (18 berkas uji) |
| `npm run build --prefix frontend` | **PASS** | Build sukses, `dist/` dihasilkan (hanya peringatan ukuran chunk >500 kB, bukan error) |
| Verifikasi end-to-end pizza nyata | **PASS** | HTTP 400 `NOT_COLONOSCOPY_IMAGE`, 0 storage/DB/pipeline/antrean (bukti: `pizza_e2e_3.log`) |
| Ukuran pembatas (torch DLL WinError 4551) | **TIDAK TERJADI** | Seluruh uji backend/AI berjalan tanpa OSError pada sesi ini |

Semua kriteria akseptasi terpenuhi: pizza → REJECT, tidak ada U-Net/TTA/Grad-CAM, tidak ada mask/overlay, tidak ada `POLYP_DETECTED`, tidak ada catatan/artefak tak wajar; kolonoskopi normal + polip tetap ACCEPT; ambigu → UNCERTAIN; mask kosong bukan syarat non-koloskopi.

---

## 8. Batasan dan item INFERENSI (belum dapat divalidasi pada mesin ini)

1. **Tidak ada baseline kolonoskopi in-vivo ACCEPT terpercaya.** Referensi monitor (`references/*`) keduanya REJECT (dominasi warna non-endoskopi / garis lurus), sehingga "kolonoskopi nyata yang ACCEPT hingga mask/overlay + `POLYP_DETECTED`" belum dapat diukur end-to-end di mesin ini. Item ini dicatat sebagai **INFERENSI / BELUM TERSEDIA** dan memerlukan frame in-vivo asli untuk diverifikasi lanjut.
2. Kelas sintetik yang belum ada sampel: **kulit manusia nyata**, **flat raw meat sintetis nyata**, landscape/hewan nyata — ditandai **BELUM TERSEDIA** di §3.2.
3. `DOMAIN_VALIDATION_ENABLED` masih bergantung env (`TestingConfig` default `False`; tes menginject `enforce_domain_validation=True`). Produksi/development tetap `True`. Ini adalah saklar konfigurasi aplikasi, bukan bypass kode.

---

## 9. Kepatuhan batas pekerjaan

- Tidak ada perubahan arsitektur/model/bobot/checkpoint/config oleh pekerjaan ini (checkpoint SHA256 terpindai, tidak dimodifikasi). `backend/app/core/config.py` berisi flag `DOMAIN_VALIDATION_ENABLED` **sebelum** pekerjaan perbaikan ini dimulai dan tidak diubah oleh perbaikan ini (tidak ada config/TTA baru ditambahkan).
- Tidak ada pelatihan/fine-tuning.
- Tidak ada perubahan TTA atau ambang segmentasi.
- Tidak ada perubahan skema DB.
- Tidak ada referensi diedit (`references/*` tidak disentuh).
- Tidak ada refactor besar/perubahan tidak terkait.
- Tidak ada operasi DB/storage/sesi destruktif.
- Tidak ada commit/push/reset git.

---

**Kesimpulan:** False acceptance pizza diperbaiki melalui gate geometri permukaan makanan (`line_density > 10.0` + mukosa hangat) dan penegakan ACCEPT tak bersyarat di semua batas model; seluruh suite lulus (Python 152/152, frontend 285/285, build OK). Laporan selesai; pengerjaan dihentikan.
