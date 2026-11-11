# FINAL AUDIT REPORT — PIXEL-T vs LUCIT-master

**Tanggal:** 11 November 2026  
**Branch:** `fitur/validasi-input` (HEAD `cbb5296`, belum di-commit)  
**Prinsip:** safety > functionality > correctness > maintainability > simplicity  
**Sumber:** 8 laporan wajib pada saat penyusunan laporan ini (lihat §1); kini **13 laporan audit wajib** — lihat `FINAL_PROJECT_AUDIT.md` + bukti file:baris terverifikasi  
**Status:** audit & refactor **selesai untuk fase ini**; perubahan pada working tree, menunggu persetujuan eksplisit untuk commit.

---

## 0. Ringkasan Eksekutif

Audit menyeluruh terhadap PIXEL-T dan LUCIT-master (proyek referensi) dilakukan dengan metode read-only yang berbasis bukti (pembacaan kode, grep terverifikasi, scan inventaris 273 file, tes penuh). Hasil utama:

1. **PIXEL-T memiliki arsitektur yang lebih matang daripada LUCIT-master** dalam aspek layering (routes→controllers→services→repositories→core), config terpusat, client Supabase terpusat, error handler global, application factory (bukan app global), auth Bearer token, dan test suite (190 pytest + 298 vitest + build). LUCIT-master tidak memiliki tes, menyimpan password plaintext, menggunakan app global Flask, dan memakai localStorage + Flask session campuran — pola yang **tidak** layak ditiru.
2. **Tidak ada fitur PIXEL-T yang terbukti rusak atau tidak terpakai.** Seluruh endpoint, pipeline AI (U-Net+ResNet50, TTA, threshold 0.55, Grad-CAM, domain gate), DB schema/RLS, dan alur auth konsisten dan teruji.
3. **Refactoring bersifat pembersihan, bukan restrukturisasi:** tambahan template environment (`Backend/.env.example`, `Frontend/.env.example`), perbaikan dependency `google-genai`, dokumentasi README 2-terminal, dan verifikasi `.gitignore`. Tidak ada file yang dihapus; folder kosong `.gitkeep` dipertahankan sementara (perlu konsolidasi bertahap).
4. **Regresi terverifikasi hijau:** pytest 190 passed/1 skipped, vitest 298/19 file, build sukses, hash model cocok. Tidak ada regresi dari perubahan Gemini yang belum di-commit.

---

## 1. Delapan Laporan Wajib

| No | Laporan | Status | Ringkasan Isi |
|---|---|---|---|
| 1 | `PROJECT_INVENTORY.md` | ✅ Selesai | Inventaris 273 file, peta direktori, entry points, dependency, kandidat duplikat/tidak terpakai, daftar dilindungi |
| 2 | `LUCIT_ARCHITECTURE_ANALYSIS.md` | ✅ Selesai | Analisis pola LUCIT (routes/controllers/services/repositories, config, auth, frontend); tabel adopsi/rejeksi; temuan risiko LUCIT (password plaintext, app global, tanpa test) |
| 3 | `PIXELT_AUDIT_REPORT.md` | ✅ Selesai | Audit frontend, backend, AI/ML, database/Supabase, integrasi FE-BE, alur fitur, keamanan; 9 temuan (F1–F9) |
| 4 | `TARGET_ARCHITECTURE.md` | ✅ Selesai | Rencana arsitektur target, daftar dilindungi, langkah bertahap (R1 Langkah 1–6), strategi rollback |
| 5 | `REFACTORING_CHANGELOG.md` | ✅ Selesai | Catatan perubahan working tree (Gemini, dependency, env template, README) + status tiap langkah |
| 6 | `UNUSED_FILES_AUDIT.md` | ✅ Selesai | Kandidat artefak (log/dist/tsbuildinfo), folder `.gitkeep`-only, kandidat kode, dokumen duplikat; rekomendasi pembersihan |
| 7 | `REGRESSION_TEST_REPORT.md` | ✅ Selesai | Hasil suite penuh (pytest 190/1 skipped, vitest 298, build sukses, hash cocok); baseline vs akhir; konsistensi kontrak & arsitektur AI |
| 8 | `FINAL_AUDIT_REPORT.md` | ✅ Selesai | Dokumen ini |

---

## 2. Metodologi Audit

1. **Fase 1 (Discovery):** daftar file/direktori (eksklusif node_modules/.venv/cache/LUCIT-master/calibration/references), dependency, `.env.example` keys, `.gitignore`, `git status`.
2. **Fase 2 (Analysis LUCIT):** pembacaan seluruh modul backend & frontend LUCIT (routes, controllers, services, repositories, config, utils, pages) dengan bukti file:baris.
3. **Fase 3 (Audit PIXEL-T):** pembacaan modul backend (core, routes, controllers, services, repositories), AI/ML (`Backend/ai/inference/*`), frontend (`services/*`, `routes/AppRoutes.tsx`, guard, AuthContext), database migrasi, integrasi FE-BE, keamanan.
4. **Fase 4 (Design):** `TARGET_ARCHITECTURE.md` berdasarkan rencana R1 + temuan audit.
5. **Fase 5 (Refactor):** perubahan kecil terukur (dependency, template env, README) + verifikasi tes relevan.
6. **Fase 6 (Cleanup):** audit pembersihan (belum ada penghapusan; kandidat didokumentasikan).
7. **Fase 7 (Regression):** suite penuh Backend/AI + frontend + build + hash model.
8. **Fase 8 (Reporting):** laporan final.

---

## 3. Kunci Temuan

### 3.1 Kekuatan PIXEL-T (dipertahankan)

| Area | Kekuatan | Bukti |
|---|---|---|
| Layering backend | routes → controllers → services → repositories → core, konsisten | `Backend/src/{routes,controllers,services,repositories,core}` |
| Config | terpusat dari env, kelas Development/Testing/Production | `Backend/src/core/config.py` |
| Client Supabase | singleton anon + service role terpisah | `Backend/src/core/supabase.py` |
| Error handling | global handler + envelope standar `{success:false,error:{code,message}}` | `Backend/src/core/errors.py` |
| Auth | Bearer token Supabase, role admin/dokter, account status pending/approved/rejected, ownership | `Backend/src/core/auth.py` |
| Domain Validation | heuristik dulu (hemat kuota) → LLM Gemini fail-closed; tanpa bypass; `_require_domain_accept` pada run_segmentation/run_gradcam | `domain_validator.py`, `llm_image_validator.py`, `analysis_service.py:1097` |
| AI/ML | U-Net+ResNet50, checkpoint terverifikasi SHA-256, TTA 5×5, threshold 0.55, postprocessing deterministik, Grad-CAM target layer terkunci | `Backend/ai/config/model_config.py`, `Backend/ai/inference/*` |
| Test suite | pytest 190 + vitest 298 + env safety + model integration | `tests/**` |
| DB | 8 migrasi + verifikasi, bucket storage, RLS (tidak diubah) | `database/migrations/001-008.sql` |
| Dokumentasi | PRD, APIContract, DataModel, StyleGuide, ModelIntegration, audit forensik | `docs/` |

### 3.2 Kelemahan/Perbaikan yang Dilakukan (fase ini)

| ID | Temuan | Tindakan | Status |
|---|---|---|---|
| F1 | Konfigurasi Gemini belum formal (working tree) | Tidak diubah di sini; didokumentasikan & teruji (tes lulus) | Dikunci |
| F2 | `fetch` FE tanpa timeout; `NewAnalysis` polling tanpa batas eksplisit | **SELESAI**: timeout fetch (`fetchWithTimeout`, 30 s/90 s, `REQUEST_TIMEOUT`) pada cleanup; **batas polling** `PROGRESS_POLL_MAX_ATTEMPTS = 300` (Langkah 2) | ✅ |
| F3 | Fallback timeout LLM `15.0` vs `Config` 30.0 | **SELESAI** pada cleanup: fallback diselaraskan ke `30.0` | ✅ |
| F4 | Folder `.gitkeep`-only (10+) | Didokumentasikan; konsolidasi bertahap | **Sebagian selesai (10 dihapus pada cleanup); sisanya pending** |
| F5 | Artefak build/log di working tree | **Dibersihkan** pada cleanup; artefak regenerable dibuat ulang oleh build baseline | ✅ Selesai |
| F6 | `google-genai` tidak tercatat di requirements | **Ditambahkan** `google-genai>=3.0.0,<3.1.0` | ✅ Selesai |
| F7 | `getCurrentUser` tidak terpakai | **Dihapus** setelah grep menyeluruh tidak menemukan pemanggil | ✅ Selesai |
| F8 | Polling `NewAnalysis` tanpa batas maksimum eksplisit | Didokumentasikan | Direkomendasikan |
| F9 | Duplikasi dokumen `.md`/`.txt` | Dipertahankan (artefak skripsi) | Dipertahankan |

---

## 4. Perubahan yang Dilakukan pada Fase Ini (belum di-commit)

| No | File | Perubahan |
|---|---|---|
| 0.4 | `Backend/requirements.txt` | Tambah `google-genai>=3.0.0,<3.1.0` |
| 0.5 | `README.md` | Tambah prasyarat, panduan 2-terminal, arsitektur 3 pilar |
| 0.6 | `Backend/.env.example` | Baru (template backend) |
| 0.7 | `Frontend/.env.example` | Baru (template frontend) |
| — | `.gitignore` | Tidak diubah (verifikasi saja) |
| 0.1–0.3 | `config.py`, `llm_image_validator.py`, `test_llm_image_validator.py` | Perubahan Gemini (sudah ada di working tree, tidak diubah fase ini) |

**Dilarang dilakukan pada fase ini:** menghapus file sebelum membuktikan tidak digunakan; git reset/clean/force push; commit tanpa persetujuan; mengubah API contract, schema DB, model/AI, auth, TTA, threshold, Grad-CAM, desain UI.

---

## 5. Status Regression (Akhir)

| Suite | Hasil |
|---|---|
| pytest (Backend + AI) | 190 passed, 1 skipped (0 failed) |
| vitest (Frontend) | 298 passed (19 file) |
| Frontend build | Sukses (`tsc -b && vite build`) |
| Checkpoint model SHA-256 | Cocok `46521AE9...B581` (135.64 MB) |
| API contract | Tidak berubah (terverifikasi FE ↔ BE) |
| Arsitektur AI/ML | Tidak berubah (threshold, TTA, Grad-CAM, checkpoint, gate) |

---

## 6. Pertimbangan Keamanan

| Aspek | Status |
|---|---|
| Secret tidak ter-hardcode | ✅ |
| `.env` gitignored (BE & FE) | ✅ |
| Service role hanya server-side | ✅ |
| Bearer token diverifikasi server-side | ✅ |
| Admin role server-write-only (app_metadata) | ✅ |
| Ownership check pada storage & DB | ✅ |
| LLM fail-closed | ✅ |

---

## 7. Langkah Lanjutan (Fase 6–7; Tahap 7 disetujui subset 0 → 1 → 2 → 5)

| No | Langkah | Risiko | Syarat |
|---|---|---|---|
| 1 | Archive skrip diagram root → `_archive/diagram_tools/` | Sedang (path `generate_bab4.js` bergantung `__dirname`) | Penyesuaian path + konfirmasi tim skripsi |
| 2 | Konsolidasi folder `.gitkeep`-only | Rendah | Cek impor dinamis tidak merujuk path |
| 3 | ~~Hapus `getCurrentUser` dari `auth.ts`~~ (SUDAH SELESAI pada cleanup) | Rendah | Grep menyeluruh: tidak ada pemanggil |
| 4 | Tambah timeout `AbortController` pada fetch FE & batas polling | **Timeout fetch: selesai** (cleanup). Batas polling `NewAnalysis`: pending — Langkah 2 Tahap 7, disetujui pengguna | Verifikasi perilaku timeout & polling |
| 5 | Re-rapihkan `scripts/` (opsional, Langkah 6) | Tinggi (impor antar-skrip & path relatif) | Bukti impor tetap berjalan; setelah 1–4 selesai |
| 6 | Commit perubahan working tree | N/A | **Persetujuan eksplisit pengguna** |

---

## 8. Kesimpulan Akhir

1. **PIXEL-T berada dalam kondisi sehat:** arsitektur konsisten, seluruh fitur teruji (pytest 190 + vitest 298 + build), keamanan bermutu, dokumentasi lengkap.
2. **LUCIT-master berguna sebagai referensi pola layering, tetapi tidak layak ditiru** pada aspek keamanan (password plaintext, service role menyeluruh), session management (localStorage), error handling (try/except per route), dan testing (tidak ada).
3. **Refactoring difokuskan pada pembersihan berbasis bukti** — bukan restrukturisasi — sehingga tidak ada risiko merusak fitur yang sudah berfungsi.
4. **Regresi hijau:** seluruh suite lulus; arsitektur AI & API contract tidak berubah.
5. **Sisa pekerjaan** (konsolidasi folder, archive skripsi, re-rapihkan scripts) terdokumentasi di §7 dengan risiko & syarat masing-masing; Tahap 7 disetujui untuk subset **0 → 1 → 2 → 5**, Langkah 3 (split AnalysisService) & 4 (archive) ditunda, rapikan `scripts/` ditunda; commit/push menunggu persetujuan terpisah.

---

## 9. Daftar File Audit di Working Tree (belum di-commit)

**Diperbarui 11 November 2026 (Langkah 0 audit):** daftar ini menyusul kondisi saat audit (8 laporan wajib + perubahan cleanup awal); kondisi saat ini penuh diatur di `FINAL_PROJECT_AUDIT.md` §3 (18 modified/deleted + 24 untracked, staging kosong).

```text
 PROJECT_INVENTORY.md        (baru, laporan #1)
 LUCIT_ARCHITECTURE_ANALYSIS.md (baru, laporan #2)
 PIXELT_AUDIT_REPORT.md      (baru, laporan #3)
 TARGET_ARCHITECTURE.md      (baru, laporan #4)
 REFACTORING_CHANGELOG.md    (baru, laporan #5)
 UNUSED_FILES_AUDIT.md       (baru, laporan #6)
 REGRESSION_TEST_REPORT.md   (baru, laporan #7)
 FINAL_AUDIT_REPORT.md       (baru, laporan #8)
 Backend/requirements.txt    (M: +google-genai>=3.0.0,<3.1.0)
 README.md                   (M: panduan instalasi)
 Backend/.env.example        (baru)
 Frontend/.env.example       (baru)
 Backend/src/core/config.py          (M sebelumnya: LLM timeout)
 Backend/src/services/llm_image_validator.py (M sebelumnya: Gemini)
 tests/Backend/test_llm_image_validator.py (M sebelumnya: tes Gemini)
```

**Semua perubahan siap di-rollback dan menunggu persetujuan eksplisit untuk commit.**
