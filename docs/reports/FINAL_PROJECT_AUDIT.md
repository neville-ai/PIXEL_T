# FINAL PROJECT AUDIT — PIXEL-T

**Tanggal:** 11 November 2026  
**Branch:** `fitur/validasi-input`  
**HEAD:** `cbb5296`  
**Staging:** kosong  
**Status:** Tahap 1–6 **SELESAI**. Tahap 7 **DISETUJUI (subset 0 → 1 → 2 → 5)** per keputusan pengguna 11 Nov 2026; **Langkah 0 sedang dikerjakan**; Langkah 3 (split AnalysisService) dan Langkah 4 (archive tooling diagram) **ditunda**; rapikan `scripts/` **ditunda**; commit/push menunggu persetujuan terpisah.  
**Sifat:** laporan penutup audit; tidak ada source, dependency, database, AI/ML, atau file penelitian yang diubah pada pembuatan laporan ini.  
**Prinsip:** SAFETY > FUNCTIONALITY > CORRECTNESS > MAINTAINABILITY > SIMPLICITY.

---

## 0. Ringkasan Eksekutif

Audit struktur PIXEL-T dengan `LUCIT-master/` sebagai pembanding read-only telah selesai. Hasil utamanya:

1. **Struktur inti PIXEL-T sudah baik** dan tidak memerlukan restrukturisasi besar. Layering `routes → controllers → services → repositories → core` lengkap; config terpusat; Supabase client tunggal; error handler global; application factory; auth Bearer dengan role/status; dan test suite berjalan penuh.
2. **PIXEL-T lebih matang daripada LUCIT-master** pada aspek yang paling berisiko: LUCIT memakai Flask app global, password plaintext, gambar base64 di database, error handling per-route, dan tidak punya test suite. Pola-pola itu **tidak boleh ditiru**.
3. **Masalah nyata PIXEL-T bersifat lokal dan terukur:** `analysis_service.py` terlalu besar (1147 baris total / 1029 baris non-kosong), beberapa halaman frontend besar, envelope error admin tidak seragam, parsing Bearer duplikat, polling `NewAnalysis` tanpa batas maksimum, sisa placeholder `.gitkeep`, artefak build/cache, dan tooling diagram di root.
4. **Baseline otomatis HIJAU:** pytest **190 passed / 1 skipped**, vitest **298 passed / 19 file**, build frontend **exit 0**, `pip check` lulus, dan SHA-256 checkpoint **cocok** (`46521AE9…C581`, 135.644.553 byte).
5. **Pengujian manual E2E belum dijalankan.** Status seluruh skenario tetap **NOT TESTED**. Hasil suite otomatis memakai mock/fixture dan **bukan** bukti integrasi live Supabase/Gemini.
6. **Tidak ada commit atau push.** Working tree memuat perubahan cleanup yang sudah disetujui sebelumnya (18 file modified/deleted, **24 file untracked**: 13 laporan audit wajib baru termasuk `FINAL_PROJECT_AUDIT.md` ini + 9 laporan audit lama dari fase sebelumnya + 2 `.env.example` baru), staging kosong.

**Keputusan pengguna (11 Nov 2026):** Tahap 7 DISETUJUI untuk Langkah 0 → 1 → 2 → 5 saja; Langkah 3 (split AnalysisService) dan Langkah 4 (archive tooling diagram) ditunda; rapikan `scripts/` ditunda; commit/push belum diizinkan (butuh persetujuan terpisah). Langkah 0 sedang dikerjakan.

---

## 1. Daftar 13 Laporan Wajib

| No | Laporan | Isi pokok | Status |
|---:|---|---|---|
| 1 | `PROJECT_STRUCTURE_INVENTORY.md` | Inventaris 507 file tracked, 269 file kerja dipindai, kategori A–F per area | Selesai |
| 2 | `LUCIT_STRUCTURE_ANALYSIS.md` | Analisis read-only `LUCIT-master/`; pola diadopsi vs ditolak | Selesai |
| 3 | `PIXELT_STRUCTURE_AUDIT.md` | Audit struktur PIXEL-T, perbandingan lapis demi lapis | Selesai |
| 4 | `CODE_SIMPLIFICATION_AUDIT.md` | Temuan S1–S13, level risiko, rekomendasi tanpa eksekusi | Selesai |
| 5 | `APPLICATION_FLOW_AUDIT.md` | Alur auth, upload, gate, worker, polling, history, admin, status | Selesai |
| 6 | `DEPENDENCY_MAP.md` | Peta import Backend/AI/frontend, dependency eksternal, titik rapuh D1–D7 | Selesai |
| 7 | `TARGET_PROJECT_STRUCTURE.md` | Struktur target, file yang tetap, usulan T1–T11, kriteria sukses | Selesai |
| 8 | `FILE_CLEANUP_AUDIT.md` | File yang sudah dibersihkan, kandidat pending, daftar yang dilindungi | Selesai |
| 9 | `REFACTORING_PLAN.md` | Urutan Langkah 0–5, matriks risiko, rollback, definition of done | Selesai |
| 10 | `BASELINE_TEST_REPORT.md` | Bukti baseline pytest/vitest/build/pip/hash + batas validitas | Selesai |
| 11 | `REFACTORING_CHANGELOG.md` | Perubahan cleanup yang sudah ada di working tree | Selesai |
| 12 | `REGRESSION_TEST_REPORT.md` | Status regresi baseline; belum ada refactor baru | Selesai |
| 13 | `FINAL_PROJECT_AUDIT.md` | Laporan ini; ringkasan, risiko, dan gerbang persetujuan | Selesai |

Laporan audit lama (`PROJECT_INVENTORY.md`, `PIXELT_AUDIT_REPORT.md`, `LUCIT_ARCHITECTURE_ANALYSIS.md`, `TARGET_ARCHITECTURE.md`, `CLEANUP_REPORT.md`, `POST_AUDIT_REVIEW.md`, `FINAL_AUDIT_REPORT.md`, `UNUSED_FILES_AUDIT.md`, `MANUAL_E2E_TEST_PLAN.md`) tetap dipertahankan; tidak dihapus dan tidak digabung.

---

## 2. Baseline yang Dikunci

| Item | Hasil | Bukti |
|---|---|---|
| pytest backend + AI | **190 passed, 1 skipped, 0 failed** (116.63 s) | `baseline_pytest.log` |
| vitest frontend | **298 passed, 19 file, 0 failed** (57.80 s) | `baseline_vitest.log` |
| Frontend production build | **exit 0** (12.20 s); warning chunk JS 591.87 kB non-fatal | `baseline_frontend_build.log` |
| `pip check` | **No broken requirements found** | `baseline_pipcheck.log` |
| Model checkpoint SHA-256 | **`46521AE90D12F57F77A7B9921881910B41071DBBB1EFF4D2172A2C437564C581`** | `baseline_hash.txt` |
| Model checkpoint size | **135.644.553 byte** | `baseline_hash.txt` |
| API contract | Tidak berubah | `APPLICATION_FLOW_AUDIT.md`, `REGRESSION_TEST_REPORT.md` |
| Manual E2E | **NOT TESTED** | `MANUAL_E2E_TEST_PLAN.md` |

**Aturan baseline:** setiap langkah Tahap 7 harus mempertahankan atau memperbaiki angka ini. Jika ada kegagalan, rollback file terkait sebelum melanjutkan.

---

## 3. Kondisi Working Tree Saat Ini

**Branch:** `fitur/validasi-input`  
**HEAD:** `cbb5296`  
**Staging:** kosong (tidak ada commit/push).

### 3.1 Modified / deleted (18 entri)

```text
M  README.md
M  Backend/src/core/config.py
M  Backend/src/services/analysis_service.py
M  Backend/src/services/llm_image_validator.py
M  Backend/requirements.txt
M  Frontend/src/utils/analysis.ts
M  Frontend/src/utils/auth.ts
M  tests/Backend/test_llm_image_validator.py
D  Backend/src/models/.gitkeep
D  Backend/src/schemas/.gitkeep
D  Backend/src/utils/.gitkeep
D  database/seed/.gitkeep
D  Frontend/src/components/analysis/.gitkeep
D  Frontend/src/components/history/.gitkeep
D  Frontend/src/types/.gitkeep
D  Frontend/src/utils/.gitkeep
D  scripts/deployment/.gitkeep
D  scripts/setup/.gitkeep
```

### 3.2 Untracked (24 entri)

13 laporan audit wajib baru (termasuk `FINAL_PROJECT_AUDIT.md`), 9 laporan audit lama dari fase sebelumnya, serta:

```text
Backend/.env.example
Frontend/.env.example
```

Tidak ada isi `.env` yang dibaca, dicetak, atau di-commit.

---

## 4. Kategori A–F

| Kode | Arti | Contoh pada PIXEL-T | Tindakan |
|---|---|---|---|
| **A** | Wajib / inti runtime, keamanan, API, test | `Backend/src/{core,routes,controllers,services,repositories}`, `Frontend/src/**`, `ai/**`, `database/migrations/**`, `tests/**` | Pertahankan; ubah hanya dengan persetujuan |
| **B** | Dapat disederhanakan internal | `analysis_service.py`, `core/auth.py`, `admin_controller.py`, halaman frontend besar, sisa `.gitkeep` | Kandidat refactor; belum diubah |
| **C** | Dapat digabung/dikonsolidasi | pasangan dokumen `.md`/`.txt` di `docs/`, laporan audit lama | Tunggu konfirmasi skripsi |
| **D** | Tidak diperlukan / regenerable | `Frontend/dist/`, `tsconfig.tsbuildinfo`, `.pytest_cache/`, log runtime | Pembersihan aman (gitignored) |
| **E** | Dipindah | tooling diagram root (`generate_bab4.js`, dll.), subfolder `scripts/` | **Ditunda** karena path/import rapuh |
| **F** | Artefak penelitian/skripsi | `research/`, `scripts/`, `docs/`, `diagram-skripsi/`, `calibration_data/`, `references/`, `LUCIT-master/`, checkpoint, notebook | Wajib dipertahankan |

---

## 5. Temuan Utama dan Risiko

| ID | Temuan | Lokasi | Risiko | Status |
|---|---|---|---|---|
| R1 | Service analisis 1147 baris total (1029 non-kosong); validasi, gate, storage, DB, queue, pipeline, progress bercampur | `Backend/src/services/analysis_service.py` | **Tinggi** | Belum diubah; menunggu approval |
| R2 | Envelope error admin berbeda dari handler global (5 lokasi) | `Backend/src/controllers/admin_controller.py` | Sedang | **Selesai (Langkah 1B)**: `APIError.to_dict()` konsisten dengan handler global; tes backend lulus |
| R3 | Tiga decorator auth menduplikasi parsing Bearer | `Backend/src/core/auth.py` | Rendah | **Selesai (Langkah 1A)**: helper `_extract_bearer_token` + `_resolve_authenticated_user`; pesan/status/urutan identik; tes backend lulus |
| R4 | Polling `NewAnalysis` tanpa batas maksimum eksplisit | `Frontend/src/pages/analysis/NewAnalysis.tsx` | Sedang | **Selesai (Langkah 2)**: `PROGRESS_POLL_MAX_ATTEMPTS = 300`; error server/timeout/jaringan dipisah; tes polling 36 lulus |
| R5 | Halaman frontend besar (974/592/577/505/487 baris) | `Frontend/src/pages/**` | Sedang | Belum diubah |
| R6 | 22 `.gitkeep` tersisa; sebagian di folder berisi nyata | beberapa folder | Rendah | Kandidat cleanup |
| R7 | Tooling diagram root bergantung `__dirname + 'references/bab 4'` | root | Sedang | Ditunda |
| R8 | Skrip `scripts/` saling bergantung (`experiment_domain_gate`, `parents[1]`) | `scripts/**` | Tinggi | Ditunda |
| R9 | Manual E2E belum dijalankan | seluruh alur | **Tinggi (bukti)** | **NOT TESTED** |

### 5.1 Risiko yang sengaja **tidak** diubah

- Domain gate ganda (upload + `pipeline.py`) adalah defense-in-depth.
- Threshold **0.55**, TTA 5×5, preprocessing, Grad-CAM, checkpoint, dan dataset/split adalah bagian penelitian yang dilindungi.
- `tta_enabled` yang tidak dibaca loop aktif sudah didokumentasikan; tidak diubah.
- API contract, DB schema/RLS, auth, dan alur utama tidak diubah.

---

## 6. Perbandingan Ringkas dengan LUCIT-master

| Aspek | LUCIT-master | PIXEL-T | Keputusan |
|---|---|---|---|
| Entry backend | Flask app global | application factory | Pertahankan PIXEL-T |
| Layering | routes → controllers → services → repositories | sama, lebih lengkap | Pertahankan |
| Auth | session/localStorage, password plaintext | Supabase Auth + Bearer + role/status | Pertahankan PIXEL-T |
| Gambar | berpotensi base64 di DB | Supabase Storage + path | Pertahankan PIXEL-T |
| Error handling | try/except per route | `APIError` global | Pertahankan PIXEL-T |
| Test | tidak ada | 190 pytest + 298 vitest | Pertahankan PIXEL-T |
| Chatbot/email | ada | tidak relevan | Tidak diadopsi |
| Threshold/model | TensorFlow, threshold 0.35 | PyTorch, U-Net+ResNet50, threshold 0.55 | Tidak disamakan |

**Kesimpulan:** PIXEL-T mengadopsi pola baik LUCIT (layering, config terpusat, Supabase client, folder fitur) dan menolak pola buruknya.

---

## 7. File dan Area yang Dilindungi

Tidak boleh dihapus, dipindah, atau diubah tanpa persetujuan eksplisit:

- `.env`, `.env.example`, `.gitignore`, lockfile (`package-lock.json`).
- `Backend/ai/models/PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth` dan seluruh `ai/**`.
- `database/migrations/001–008.sql`, `database/verify_doctor_registration.sql`.
- `tests/**`.
- `research/**`, `scripts/**` beserta `scripts/output/**`, `calibration_data/**`, `references/**`.
- `docs/**`, `diagram-skripsi/**`, `LUCIT-master/**`.
- `node_modules/**`, `.venv/**`.
- Semua route/endpoint dan kontrak API yang ada.

---

## 8. Rencana Tahap 7 (Subset 0 → 1 → 2 → 5; Langkah 0 sedang dikerjakan)

Ringkasan dari `REFACTORING_PLAN.md`:

| Langkah | Fokus | Risiko | Syarat |
|---|---|---|---|
| 0 | Sinkronisasi dokumentasi | Sangat rendah | Review manual |
| 1 | Konsistensi backend: helper Bearer, envelope admin, logging | Rendah–sedang | Test backend |
| 2 | Resiliency frontend: batas polling, ekstraksi komponen | Sedang | Vitest + build |
| 3 | Pemecahan `AnalysisService` di balik facade | **Tinggi** | Regresi penuh + E2E |
| 4 | Cleanup terbatas: `.gitkeep`, artefak, archive tooling | Rendah–tinggi | Bukti path/import |
| 5 | Regresi penuh + manual E2E | — | Checklist DoD |

**Gerbang:** disetujui pengguna pada 11 November 2026 dengan subset **0 → 1 → 2 → 5**; Langkah 3 dan 4 ditunda. Lihat §9.

---

## 9. Keputusan yang Diminta

| No | Keputusan | Keputusan pengguna (11 Nov 2026) |
|---:|---|---|
| 1 | Setujui Tahap 7 dimulai? | **Ya**, subset terbatas |
| 2 | Urutan langkah | **0 → 1 → 2 → 5** |
| 3 | Langkah 3 (`AnalysisService`) | **Tunda** |
| 4 | Archive tooling diagram | **Tunda** |
| 5 | Rapikan `scripts/` | **Nanti** |
| 6 | Manual E2E | **Sebelum commit**, setelah refactoring |
| 7 | Commit/push | **Belum diizinkan** — approval terpisah |

---

## 10. Definition of Done (Tahap 7)

Tahap 7 dinyatakan selesai hanya jika:

1. Tidak ada perubahan API contract, DB schema/RLS, auth, atau AI/ML.
2. pytest ≥ **190 passed, 1 skipped, 0 failed**.
3. vitest ≥ **298 passed, 0 failed**.
4. `npm run build` sukses.
5. `pip check` sukses.
6. SHA-256 checkpoint tetap **`46521AE9…C581`**.
7. Manual E2E dijalankan dan dicatat (bukan `NOT TESTED`).
8. `git status` hanya memuat perubahan yang disetujui.
9. `.env` tidak ter-track.
10. Laporan ini diperbarui dengan hasil akhir.

---

## 11. Pernyataan Status

- Tahap 1–6: **SELESAI**.
- Tahap 7: **DISETUJUI (subset)** — Langkah 0 sedang dikerjakan; Langkah 3/4/scripts **ditunda**.
- Tidak ada commit, push, reset, clean, atau force push.
- Tidak ada file produksi, AI/ML, database, atau penelitian yang diubah pada pembuatan laporan ini.
- Pengujian manual E2E: **NOT TESTED**.

**Pekerjaan berhenti di sini sampai pengguna memberikan persetujuan eksplisit.**
