# FILE CLEANUP AUDIT — PIXEL-T

**Tanggal:** 11 November 2026  
**Branch:** `fitur/validasi-input`  
**HEAD:** `cbb5296`  
**Status:** audit read-only + cleanup tahap yang sudah disetujui; **belum ada file produksi baru yang dihapus pada tahap ini**.  
**Sifat:** daftar kandidat pembersihan berdasarkan bukti, dengan aturan “jangan hapus sebelum membuktikan”.

---

## 0. Ringkasan

| Area | Status audit | Kategori utama | Tindakan |
|---|---|---:|---|
| Build artifact/cache/log | Sudah dibersihkan sebelumnya; dibuat ulang oleh build baseline | D | Regenerable; tidak termasuk source |
| Placeholder `.gitkeep`-only | 10 file dihapus pada tahap cleanup | B/C | Selesai untuk 10; sisanya menunggu approval |
| Kode tidak terpakai | `getCurrentUser` dihapus | B | Selesai |
| Dokumentasi duplikat | Belum dihapus | C/F | Ditunda |
| Tooling diagram | Belum di-archive | E/F | Ditunda |
| Source runtime | Tidak ada file yang dihapus | A | Pertahankan |

**Kesimpulan:** tidak ada kandidat yang dihapus pada tahap audit ini. Cleanup utama telah selesai dan diverifikasi, tetapi laporan final wajib untuk memastikan status sebelum commit.

---

## 1. Kategori File

| Kode | Arti | Contoh | Status |
|---|---|---|---|
| **A** | Wajib inti | backend routes/services/AI/tests, frontend, DB migrations, entry point | Pertahankan |
| **B** | Dapat disederhanakan/dikonsolidasi | file besar, placeholder, envelope, logging | Kandidat pending approval |
| **C** | Dapat digabung | dokumen duplikat `.md`/`.txt` | Kandidat pending konfirmasi |
| **D** | Tidak diperlukan/regenerable | log, dist, tsbuildinfo, cache, artefak build | Pembersihan aman, gitignored |
| **E** | Dipindah | root diagram tools, scripts subfolder | Ditunda |
| **F** | Artefak penelitian | research, scripts/output, calibration, references, LUCIT-master, docs skripsi | Pertahankan |

---

## 2. File yang Sudah Dibersihkan/Dikoreksi (Status Saat Ini)

### 2.1 Artifact build/cache/log

| File/Path | Status | Catatan |
|---|---|---|
| `backend_foreground.log`, `backend_foreground_err.log` | D, **dibersihkan** | Log runtime; gitignored |
| `.pytest_cache/` | D, **dibersihkan** | Cache test |
| `Frontend/dist/` | D, **dibersihkan**, lalu **dibuat ulang** oleh `npm run build` baseline | Hasil build, gitignored |
| `Frontend/tsconfig.tsbuildinfo` | D, **dibersihkan**, lalu **dibuat ulang** oleh build | Cache build, gitignored |

### 2.2 Placeholder `.gitkeep`-only — 10 file

| # | Path | Status |
|---|---|---|
| 1 | `Backend/src/models/.gitkeep` | Dihapus |
| 2 | `Backend/src/schemas/.gitkeep` | Dihapus |
| 3 | `Backend/src/utils/.gitkeep` | Dihapus |
| 4 | `database/seed/.gitkeep` | Dihapus |
| 5 | `Frontend/src/components/analysis/.gitkeep` | Dihapus |
| 6 | `Frontend/src/components/history/.gitkeep` | Dihapus |
| 7 | `Frontend/src/types/.gitkeep` | Dihapus |
| 8 | `Frontend/src/utils/.gitkeep` | Dihapus |
| 9 | `scripts/deployment/.gitkeep` | Dihapus |
| 10 | `scripts/setup/.gitkeep` | Dihapus |

**Penting:** `Backend/ai/models/.gitkeep` **tidak** dihapus karena folder berisi checkpoint; `database/migrations/` tidak dihapus karena berisi migration.

### 2.3 Perubahan kode/tooling yang sudah dilakukan

| No | File | Perubahan | Status |
|---|---|---|---|
| 1 | `Frontend/src/utils/analysis.ts` | `fetchWithTimeout`, `UPLOAD_REQUEST_TIMEOUT_MS`, `DEFAULT_REQUEST_TIMEOUT_MS`, `REQUEST_TIMEOUT_ERROR_CODE`, `ApiRequestError` | Selesai |
| 2 | `Frontend/src/utils/auth.ts` | Hapus `getCurrentUser` | Selesai |
| 3 | `Backend/src/core/config.py` | `LLM_VALIDATION_TIMEOUT_S=30.0` | Selesai |
| 4 | `Backend/src/services/llm_image_validator.py` | Gemini JSON/schema/thinking/token/timeout/retry | Selesai |
| 5 | `Backend/src/services/analysis_service.py` | Fallback timeout konsisten 30.0 | Selesai |
| 6 | `Backend/requirements.txt` | `google-genai>=3.0.0,<3.1.0` | Selesai |
| 7 | `tests/Backend/test_llm_image_validator.py` | Tes timeout/config + baru | Selesai |
| 8 | `README.md` | Panduan instalasi/arsitektur | Selesai |
| 9 | `Backend/.env.example`, `Frontend/.env.example` | Template Backend/frontend baru | Selesai |

---

## 3. Kandidat Pembersihan yang Masih Pending (Belum Dieksekusi)

### 3.1 Placeholder `.gitkeep` tersisa

Pada snapshot 11 November 2026, masih ada 22 file `.gitkeep` (di luar `Frontend/node_modules`) yang tersisa:

```text
Backend/ai/config/.gitkeep
Backend/ai/inference/.gitkeep
Backend/ai/models/.gitkeep
Backend/src/controllers/.gitkeep
Backend/src/core/.gitkeep
Backend/src/repositories/.gitkeep
Backend/src/routes/.gitkeep
Backend/src/services/.gitkeep
database/migrations/.gitkeep
Frontend/src/assets/.gitkeep
Frontend/src/components/layout/.gitkeep
Frontend/src/components/ui/.gitkeep
Frontend/src/hooks/.gitkeep
Frontend/src/pages/analysis/.gitkeep
Frontend/src/pages/auth/.gitkeep
Frontend/src/pages/dashboard/.gitkeep
Frontend/src/pages/history/.gitkeep
Frontend/src/routes/.gitkeep
Frontend/src/utils/.gitkeep
tests/ai/.gitkeep
tests/Backend/.gitkeep
tests/Frontend/.gitkeep
```

**Interpretasi:** sebagian harus dipertahankan (mis. `ai/models`, `database/migrations`, folder test yang masih dipakai), sebagian mungkin redundan karena folder berisi source nyata. Pemetaan per-folder ini masih perlu review bukti sebelum penghapusan.

**Status:** **Belum dihapus/dipindah** pada tahap ini; siap jadi kandidat cleanup setelah review.

### 3.2 Root tooling skripsi

| File | Kategori | Status |
|---|---:|---|
| `generate_bab4.js` | F/E | Ditunda archive; path `__dirname + 'references/bab 4'` |
| `render_erd.mjs` | F/E | Ditunda archive |
| `rasterize_erd.py` | F/E | Ditunda archive |
| `rasterize_svg.py` | F/E | Ditunda archive |
| `test_render.mjs` | F/E | Ditunda archive |
| `test_field.puml` | F/E | Ditunda archive |
| `test_field.svg` | F/E | Ditunda archive |

**Status:** **Tidak dipindahkan**. Approval + penyesuaian path diperlukan.

### 3.3 Dokumentasi duplikat

| Pasangan | Status |
|---|---|
| `docs/APIContract.md` / `docs/APIContract.txt` | Fokus audit ke API; C/F |
| `docs/StyleGuide.md` / `docs/StyleGuide.txt` | C/F |
| `docs/DataModelSpecification.md` / `.txt` | C/F |
| `docs/AdminDashboardAndApproveForensicReport.md` / `.txt` | C/F |
| `docs/diagrams/*` vs `diagram-skripsi/*` | F |

**Status:** pertahankan; gabung hanya setelah konfirmasi skripsi/tim.

### 3.4 Skrip audit penelitian yang sebenarnya bukan unit test

| File | Status |
|---|---|
| `tests/ai/audit_domain_validator_deep.py` | F/B, di-ignore baseline |
| `tests/ai/measure_real_samples_stage2.py` | F/B, di-ignore baseline |
| `scripts/output/*` | F |

**Status:** pertahankan.

### 3.5 File lain yang belum boleh dihapus

| Path | Alasan |
|---|---|
| `.env` Backend/frontend | Secret; gitignored |
| `.env.example` root/Backend/frontend | Template; root harus dipertahankan |
| `.gitignore` | Harus diperbarui secara eksplisit bila archive dilakukan |
| `Backend/requirements.txt` | Dependency |
| `Frontend/package-lock.json` | Reproducibility |
| `Backend/ai/models/PIXEL-T_..._best.pth` | Checkpoint |
| `database/migrations/001–008.sql` | Schema |
| `research/`, `calibration_data/`, `references/` | Penelitian |
| `LUCIT-master/` | Referensi read-only |
| `Backend/.env`, `Frontend/.env` | Secret lokal |
| `Backend/set_admin_role.py` | Utilitas operasional |

---

## 4. Daftar Pembersihan yang Sudah Tidak Diprioritaskan

| No | Item | Status |
|---|---|---|
| C1 | Archive skrip diagram ke `_archive/diagram_tools/` | Menunggu approval + path fix |
| C2 | Konsolidasi `scripts/` ke subfolder | Menunggu approval + dependency/path proof |
| C3 | Hapus `getCurrentUser` | Selesai |
| C4 | Tambah timeout fetch & batas polling | Timeout selesai; batas polling pending |
| C5 | Tambah dependency upper bound | **Selesai**; saat ini `>=3.0.0,<3.1.0` |
| C6 | Konsistensi dokumen antar laporan | Pending |
| C7 | Uji manual E2E | **Belum dilakukan** |

---

## 5. Prinsip Pembersihan

1. **Jangan hapus tanpa bukti.** Untuk file kode, wajib grep statis/dinamis.
2. **Jangan ubah file yang dilindungi.** AI, DB, auth, API, skrip.
3. **Jangan hapus `.env`, `.env.example`, `.gitignore`, lockfile, checkpoint, dataset, notebook, `calibration_data`, `references/`, `LUCIT-master`, `node_modules`, `.venv`.**
4. **Jangan hapus log sebelum memastikan proses backend tidak aktif.**
5. **Jangan commit/push sebelum persetujuan eksplisit.**
6. **Tidak ada cleanup baru pada tahap audit ini.** Semua kandidat menunggu persetujuan pada `REFACTORING_PLAN.md`.

---

## 6. Kesimpulan

Cleanup tahap sebelumnya berjalan baik. Pada tahap ini, file source kritikal tidak dihapus; hanya kandidat dokumentasi/tooling/placeholder yang tercatat. Laporan ini harus menjadi acuan sebelum fase file cleanup lanjutan.
