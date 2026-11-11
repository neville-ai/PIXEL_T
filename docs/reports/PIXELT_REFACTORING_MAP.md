# PIXELT_REFACTORING_MAP

**Tanggal:** 11 November 2026
**Mode:** Rencana eksekusi detail (Tahap C) — **belum ada perubahan source code, folder, atau file**.
**Dasar:** `PIXELT_SIMPLIFIED_STRUCTURE_PROPOSAL.md` + `LUCIT_VS_PIXELT_COMPARISON.md` + temuan `PIXELT_CURRENT_STRUCTURE.md`.
**Keterkaitan dengan Langkah Tahap 7:** ini adalah lanjutan setelah Langkah 1–2 selesai. Langkah 3 (split `analysis_service.py`) tetap ditunda.

---

## 1. Cara Membaca Peta Ini

Setiap entri = satu gerakan refactoring dengan:
- `Sumber` (lokasi sekarang), `Tujuan` (lokasi target)
- `Impor & path yang berdampak` — file yang mungkin perlu update import jika sumber dipindah
- `Risiko` — tingkat + penjelasan
- `Tes verifikasi` — yang harus lulus setelah eksekusi

**Pemberitahuan:** Peta ini adalah *rencana*, bukan perintah eksekusi. Tahap D dieksekusi satu per satu setelah persetujuan per fase.

---

## 2. Fase 1 — Backend (move murni, risiko rendah–sedang)

### 1.1 Pindah `ai/` (root) → `Backend/ai/`

| Detail | Isi |
|---|---|
| Sumber | `ai/__init__.py`, `Backend/ai/config/*.py`, `Backend/ai/inference/*.py`, `Backend/ai/models/*.pth` |
| Tujuan | `Backend/ai/__init__.py`, `Backend/Backend/ai/config/*.py`, `Backend/Backend/ai/inference/*.py`, `Backend/Backend/ai/models/*.pth` |
| Impor & path berdampak | `Backend/src/services/analysis_service.py` (5 baris `from ai...`); `Backend/ai/inference/*.py` (impor internal `from ai.config...`, `from ai.inference...`) |
| Analisis impor | Semua pakai impor absolut `ai.*`. `Backend/run.py` menyisipkan `Backend/` ke `sys.path`; `tests/conftest.py` juga menyisipkan `Backend/` (`backend_path`). Jadi `from ai.config...` tetap valid setelah pindah. |
| Checkpoint path | `Backend/ai/config/model_config.py:checkpoint_path()` pakai `Path(__file__).parents[1] / "models" / filename` — relatif terhadap folder `ai/`, aman selama `models/` dipindah bersama. SHA-256 tetap `46521AE9...`; verifikasi ulang setelah pindah. |
| Risiko | **Sedang**: semua file `ai/` pindah sekaligus; harus diuji ulang import backend dan tes `tests/ai/`. |
| Tes verifikasi | `pytest tests/backend` (190 passed target), `pytest tests/ai`, build frontend (Tidak terpengaruh langsung), manual test SHA-256 checkpoint. |

### 1.2 Pindah `Backend/set_admin_role.py` → `Backend/tools/set_admin_role.py`

| Detail | Isi |
|---|---|
| Sumber | `Backend/set_admin_role.py` (utility admin via Supabase service role) |
| Tujuan | `Backend/tools/set_admin_role.py` |
| Impor & path berdampak | Tidak ada impor dari kode aplikasi (skrip mandiri, dipanggil manual). |
| Risiko | **Rendah**. |
| Tes verifikasi | Skrip dapat dijalankan di lokasi baru (tidak ada perubahan isi); `pytest tests/backend` tidak terpengaruh. |

### 1.3 Hapus `.gitkeep` (backend)

| Detail | Isi |
|---|---|
| Sumber | `Backend/src/controllers/.gitkeep`, `Backend/src/core/.gitkeep`, `Backend/src/repositories/.gitkeep`, `Backend/src/routes/.gitkeep`, `Backend/src/services/.gitkeep`, `Backend/ai/config/.gitkeep`, `Backend/ai/inference/.gitkeep`, `Backend/ai/models/.gitkeep` (setelah pindah) |
| Tujuan | — (dihapus) |
| Impor & path berdampak | Tidak ada (file placeholder kosong). |
| Risiko | **Rendah**: folder tetap ada karena diisi file asli; git tetap melacak folder yang berisi file. |
| Tes verifikasi | Struktur folder tetap valid; `pytest` & `vitest` tidak memerlukan file `.gitkeep`. |

---

## 3. Fase 2 — Frontend (move murni + sedikit merge)

### 2.1 Pindah `statusText.contrast.test.tsx` → `src/__tests__/statusText.contrast.test.tsx`

| Detail | Isi |
|---|---|
| Sumber | `Frontend/src/statusText.contrast.test.tsx` |
| Tujuan | `Frontend/src/__tests__/statusText.contrast.test.tsx` |
| Impor & path berdampak | `import cfgSrc from '../tailwind.config.js?raw'` → harus jadi `'../../tailwind.config.js?raw'`; `@/components/...` dan `@/pages/...` tetap berfungsi (alias `src/`). |
| Risiko | **Rendah–Sedang**: satu path relative perlu koreksi; test ini hanya membaca token Tailwind + source file via `?raw`. |
| Tes verifikasi | `npx vitest run src/__tests__/statusText.contrast.test.tsx`, full vitest 19 file. |

### 2.2 Pindah `LogoPixelT.tsx` → `components/ui/` (merge `brand/`)

| Detail | Isi |
|---|---|
| Sumber | `Frontend/src/components/brand/LogoPixelT.tsx` |
| Tujuan | `Frontend/src/components/ui/LogoPixelT.tsx`; hapus `components/brand/` |
| Impor & path berdampak | 3 pemakai (grep sebelumnya): `AppShell.tsx` dan 2 halaman; update path `'@/components/brand/LogoPixelT'` → `'@/components/ui/LogoPixelT'`. |
| Risiko | **Rendah**: hanya path impor; nama komponen sama (`LogoPixelT`). |
| Tes verifikasi | Full vitest (19 file) + `npm run build` exit 0. |

### 2.3 Hapus `.gitkeep` (frontend) + `tsconfig.tsbuildinfo`

| Detail | Isi |
|---|---|
| Sumber | 10 `.gitkeep` di `Frontend/src/{assets,components/{layout,ui},hooks,pages/{analysis,auth,dashboard,history},routes,services}`, `Frontend/tsconfig.tsbuildinfo` |
| Tujuan | — (dihapus) |
| Impor & path berdampak | Tidak ada. |
| Risiko | **Rendah**. |
| Tes verifikasi | Vitest & build tidak bergantung pada `.gitkeep`; `tsconfig.tsbuildinfo` tidak diimpor. |

---

## 4. Fase 3 — Root, Dokumentasi & Tooling (tidak menyentuh source aplikasi)

### 3.1 Pindah tooling diagram → `scripts/tools/diagrams/`

| Detail | Isi |
|---|---|
| Sumber | `generate_bab4.js`, `render_erd.mjs`, `rasterize_erd.py`, `rasterize_svg.py`, `test_render.mjs`, `test_field.puml`, `test_field.svg` |
| Tujuan | `scripts/tools/diagrams/` |
| Impor & path berdampak | `generate_bab4.js` memakai `__dirname + 'references/bab 4'` → harus disesuaikan ke `path.join(__dirname, '..', '..', 'references', 'bab 4')` setelah pindah ke `scripts/tools/diagrams/`. |
| Risiko | **Sedang** pada `generate_bab4.js` (path); sisanya stand-alone. |
| Tes verifikasi | Jalankan ulang `generate_bab4.js` & `render_erd.mjs` (apabila ada npm script) atau verifikasi path manual; tidak ada tes otomatis untuk tooling ini di CI. |

### 3.2 Pindah laporan audit/status → `docs/reports/`

| Detail | Isi |
|---|---|
| Sumber | ~22 file `.md` di root (APPLICATION_FLOW_AUDIT.md, BASELINE_TEST_REPORT.md, CLEANUP_REPORT.md, CODE_SIMPLIFICATION_AUDIT.md, DEPENDENCY_MAP.md, FILE_CLEANUP_AUDIT.md, FINAL_AUDIT_REPORT.md, FINAL_PROJECT_AUDIT.md, LUCIT_ARCHITECTURE_ANALYSIS.md, LUCIT_STRUCTURE_ANALYSIS.md, MANUAL_E2E_TEST_PLAN.md, PIXELT_AUDIT_REPORT.md, PIXELT_STRUCTURE_AUDIT.md, POST_AUDIT_REVIEW.md, PROJECT_INVENTORY.md, PROJECT_STRUCTURE_INVENTORY.md, REFACTORING_CHANGELOG.md, REFACTORING_PLAN.md, REGRESSION_TEST_REPORT.md, TARGET_ARCHITECTURE.md, TARGET_PROJECT_STRUCTURE.md, UNUSED_FILES_AUDIT.md) + 5 laporan baru Tahap A–C |
| Tujuan | `docs/reports/` |
| Impor & path berdampak | Tidak ada impor; dokumen saja. Referensi lintas-file dalam dokumen masih bisa pakai `../`. |
| Risiko | **Rendah** (dokumen tidak berjalan di runtime). |
| Tes verifikasi | Tidak ada tes runtime; verifikasi hanya apakah dokumen masih terbuka. |

### 3.3 Konsolidasi duplikasi `*.md` vs `*.txt` (kandidat, **menunggu persetujuan**)

| Pasangan | Alasan hapus candidate | Tindakan |
|---|---|---|
| `APIContract.md` / `APIContract.txt` | Isi duplikat, format berbeda. | Pertahankan `.md`, hapus `.txt` (butuh perbandingan isi dulu). |
| `DataModelSpecification.md` / `DataModelSpecification.txt` | Sama. | Sama. |
| `StyleGuide.md` / `StyleGuide.txt` | Sama. | Sama. |
| `AdminDashboardAndApproveForensicReport.txt` / `ADMIN_DASHBOARD_AND_APPROVE_FORENSIC_REPORT.md` | Sama. | Sama. |
| `ApproveDoctorFixReport.txt` / `APROVE_DOKTER_FIX_REPORT.md` | Sama. | Sama. |
| Risiko | **Sedang** jika `.txt` memiliki isi yang berbeda dari `.md`. |
| Tes verifikasi | Diff isi pasangan sebelum hapus; dokumentasi tetap readable. |

---

## 5. Fase 4 — Penyederhanaan File Besar (DITUNDA, Persetujuan Terpisah)

| No | Sumber | Tujuan | Alasan ditunda |
|---|---|---|---|
| 4.1 | `Backend/src/services/analysis_service.py` (1147 baris total / 1029 non-kosong) | Modul per tanggung jawab (domain validation, LLM gate, pipeline, progress) | Langkah 3 Tahap 7 ditunda pengguna (perlu regresi penuh + approval); ingin memastikan konsistensi auth/logging/polling stabil terlebih dahulu. |
| 4.2 | `Frontend/src/pages/profile/DoctorProfile.tsx` (1051 baris), `NewAnalysis.tsx` (666), `History.tsx` (606), `AppShell.tsx` (425) | Ekstraksi komponen per halaman | Masih ditunda (diasosiasikan ke Langkah 2B–2D sebelumnya); perlu tes UI/regresi yang lebih berat. |

---

## 6. Matriks Impor yang Harus Diperiksa (sebelum eksekusi)

| File yang berubah | Impor yang perlu diupdate |
|---|---|
| `generate_bab4.js` | `path.join(__dirname, '..', '..', 'references', 'bab 4')` |
| `Frontend/src/__tests__/statusText.contrast.test.tsx` | `'../../tailwind.config.js?raw'` (dari `'../tailwind.config.js?raw'`) |
| Pemakai `LogoPixelT` (3 file) | `'@/components/ui/LogoPixelT'` |
| (tidak ada) `ai.inference...` | Tidak perlu diubah — `sys.path` backend tetap mencakup folder `ai` |

---

## 7. Tes yang Harus Lulus (Sebelum & Sesudah Setiap Fase)

| Suite | Target sebelum | Target setelah |
|---|---|---|
| `pytest tests/backend` | 190 passed, 1 skipped | Sama |
| `pytest tests/ai` | (exist) | Sama |
| `npx vitest run` frontend | 302 passed, 19 file | Sama (302 saat proposal ditulis) |
| `npm run build` | exit 0 | exit 0 |
| `pip check` | lulus | lulus |
| Hash checkpoint `46521AE9...` | cocok | cocok |
| Manual E2E | NOT TESTED | NOT TESTED (masih menunggu) |

---

## 8. Rollback

Tidak ada commit/push dilakukan selama Tahap C–D (menunggu approval terpisah). Perubahan source dapat dikembalikan secara individu melalui `git diff`/`git checkout` per file. Semua fase hanya memindahkan/menggabungkan file — tidak ada rewriting logika.

---

## 9. Pertanyaan yang Perlu Disetujui Sebelum Tahap D

1. Apakah `ai/` boleh dipindah ke `Backend/ai/` (impor tetap valid via `sys.path`)?
2. Apakah laporan audit di root dipindah ke `docs/reports/`, atau tetap di root?
3. Apakah 5 pasangan dokumen `.md`/`.txt` boleh difilter (hapus `.txt`)?
4. Apakah Fase 4 (split `analysis_service.py`, ekstrak komponen) dapat dijadwalkan setelah Tahap 1–3 selesai, atau perlu approval terpisah sekarang?

**Status:** rencana disusun; berhenti menunggu review user.
