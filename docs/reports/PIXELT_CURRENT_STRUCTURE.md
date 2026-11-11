# PIXELT_CURRENT_STRUCTURE

**Tanggal:** 11 November 2026
**Branch:** `fitur/validasi-input`
**HEAD:** `cbb5296`
**Mode:** Audit read-only (Tahap A) — tidak ada source code, folder, file, maupun refactoring yang diubah.
**Cara pengumpulan:** peninjauan langsung pada filesystem (Get-ChildItem) dan pembacaan isi file.

---

## 1. Ringkasan Eksekutif

Struktur PIXEL-T saat ini sudah mengadopsi pola *layered* (routes → controllers → services → repositories, core untuk cross-cutting) yang sejalan dengan LUCIT-master, namun masih menyimpan sisa kognitif dari proses audit dan cleanup:

1. Backend sudah punya `app/{core,controllers,routes,repositories,services}` — pola ini **disarankan** dan dipertahankan.
2. Backend belum mempunyai folder `models`, `schemas`, `utils` formal (level `ai/` dipakai untuk model/domain logic) — keputusan desain, bukan kekacauan.
3. `Backend/src/services/analysis_service.py` masih **god service** (1147 baris total / 1029 baris non-kosong), sehingga perbaikan konsistensi di Tahap 0–2 tidak mengubah struktur tetap.
4. Frontend sudah terorganisir per-layer (`pages`, `components`, `services`, `context`, `hooks`, `lib`, `routes`, `styles`) dengan tes Vitest yang *colocated*.
5. Root project masih berisi file tooling + laporan audit yang akan menjadi target konsolidasi.

---

## 2. Struktur Root PIXEL-T (saat ini)

```
WEB_PIXELT/
├── .freebuff/                  (runtime/cache)
├── .git/, .pytest_cache/, .venv/, .vscode/
├── ai/                         # AI module (config + inference + models) — DI LUAR Backend/
├── Backend/                    # Flask API (app factory, layers, run.py, set_admin_role.py)
├── calibration_data/           # data hasil kalibrasi
├── database/                   # migrasi SQL + README
├── diagram-skripsi/            # plantuml + screenshot diagram
├── docs/                       # spesifikasi & laporan audit teknis
├── Frontend/                   # React/Vite SPA
├── LUCIT-master/               # REFERENSI LUCIT (tidak disentuh)
├── node_modules/               # (frontend + root tooling)
├── references/                 # notebook penelitian + aset bab 4
├── research/                   # notebook + konfigurasi scenario
├── scripts/                    # tooling eksperimen AI + output CSV
├── tests/                      # pytest (backend, ai, frontend-env-safety)
├── *.md, *.txt, *.js, *.py, *.mjs, *.puml, *.svg   # laporan audit, tooling, artefak diagram
└── (tersembunyi: .env.example, .gitignore)
```

Komentar per bagian:
- **Backend & frontend** adalah sumber aplikasi nyata.
- **`ai/`** adalah modul domain AI yang diimpor absolut (`from ai.inference...`) ke `Backend/src/services/analysis_service.py`.
- **Root-level file .md/.txt** adalah laporan audit/status (sengaja dibuat oleh tim audit, konsisten keberadaan di root).
- **Tooling root** (`generate_bab4.js`, `rasterize_erd.py`, `render_erd.mjs`, `test_render.mjs`, `test_field.puml/.svg`) sempat ditarget arsip (`FILE_CLEANUP_AUDIT.md` — status *ditunda*).

---

## 3. Struktur Backend (saat ini)

```
Backend/
├── .env, .env.example, requirements.txt, run.py, set_admin_role.py
└── app/
    ├── __init__.py               # create_app factory
    ├── controllers/              # admin_controller.py, analysis_controller.py (+ __init__)
    ├── core/                     # auth.py, config.py, errors.py, supabase.py
    ├── repositories/             # analysis_repository.py
    ├── routes/                   # admin.py, analysis.py, health.py, __init__.py
    └── services/                 # analysis_service.py (god), admin_service.py, llm_image_validator.py, storage_service.py
```

- **Layer**: `routes (blueprint) → controller → service → repository` dengan `core` cross-cutting (auth/errors/config/supabase).
- **Catatan**: tidak ada folder `models`, `schemas`, `utils` formal di `Backend/src/`; logika model (U-Net/ResNet50/Gemini/domain validator) hidup di `ai/`.
- **Entrypoint**: `Backend/run.py` (application factory); `Backend/set_admin_role.py` (utility skrip admin via Supabase service role).

---

## 4. Struktur Frontend (saat ini)

```
Frontend/
├── *.config, package.json, vite.config.ts, tsconfig*.json, index.html
└── src/
    ├── main.tsx, App.tsx, AppRoutes.tsx, index.css
    ├── assets/ (ikon/logo + .gitkeep)
    ├── components/
    │   ├── auth/ (Admin, Doctor, Protected, PublicOnly, AuthLoading, OpeningAnimation)
    │   ├── brand/ (LogoPixelT)
    │   ├── layout/ (AppShell)
    │   └── ui/ (Badge, Button, Card, EmptyState, ErrorState, Input, LoadingState, Modal, ThemeToggle)
    ├── context/ (AuthContext)
    ├── hooks/ (useOpeningAnimation, useTheme)
    ├── lib/ (format.ts, openingTimeline.ts, supabase.ts)
    ├── pages/ (admin, analysis, auth, dashboard, history, profile, NotFound)
    ├── routes/ (AppRoutes)
    ├── services/ (analysis, auth, profile + *.test)
    ├── styles/ (opening.css)
    └── *.test.tsx (statusText.contrast)   # TES DI ROOT SRC — cross-cutting regression test
```

---

## 5. Struktur lain penting

- **tests/**: `tests/Backend/` (pytest API), `tests/ai/` (domain/inference tests), `tests/Frontend/` (env-safety pytest — satu-satunya pytest di frontend).
- **docs/**: APIContract, DataModel, Functional/PRD, audit teknis, StyleGuide.
- **database/**: migrasi SQL + README.
- **scripts/**: eksperimen AI (domain gate, LLM gate, eval, calib) + `output/` CSV.
- **ai/**: `Backend/ai/config/`, `Backend/ai/inference/` (preprocessing, segmentation, gradcam, postprocessing, pipeline, domain_validator, model_service), `Backend/ai/models/` (checkpoint).

---

## 6. Ukuran & Ringkasan

| Area | File | Baris |
|---|---|---|
| Backend | `Backend/src/services/analysis_service.py` | **1147** (1029 non-kosong) |
| Backend | `Backend/src/services/admin_service.py` | 378 |
| Backend | `Backend/src/core/auth.py` | 252 |
| Backend | `Backend/src/services/llm_image_validator.py` | 232 |
| Frontend | `Frontend/src/pages/profile/DoctorProfile.tsx` | 1051 |
| Frontend | `Frontend/src/pages/analysis/NewAnalysis.tsx` | 666 |
| Frontend | `Frontend/src/pages/history/History.tsx` | 606 |
| Frontend | `Frontend/src/components/layout/AppShell.tsx` | 425 |
| Frontend | `Frontend/src/App.test.tsx` | 741 |
| Backend | total Python di `Backend/` | ~3.190 |

---

## 7. Temuan Struktur yang Sudah Terkonfirmasi dari Kode Aktual

1. **God service backend** — `analysis_service.py` menguasai validasi, domain gate, LLM gate, storage, DB, queue, worker, pipeline, progress (temuan R1/S1 audit).
2. **Duplikasi auth backend berkurang** — setelah Tahap 1 (helper `_extract_bearer_token`/`_resolve_authenticated_user`), `core/auth.py` 252→232 baris dengan sedikit penyederhanaan; tiga decorator kini berbagi helper.
3. **Banyak file frontend besar** — beberapa halaman >600 baris (NewAnalysis 666, History 606, AppShell 425, DoctorProfile 1051); ini alasan eksplorasi split/ekstraksi per komponen (2B–2D, ditunda).
4. **Sisa placeholder `.gitkeep`** di folder layer Backend/Frontend/tests/database.
5. **Duplikasi dokumen** — pasangan `*.md`/`*.txt` (APIContract, StyleGuide, DataModelSpecification, laporan forensic).
6. **Tooling di root** — skrip + artefak diagram + `generate_bab4.js` tertinggal rename path (ditunda archive).
7. **Tes cross-cutting di root `src`** — `statusText.contrast.test.tsx` bukan colocated dengan subject-nya.
8. **Backend/Tes** — pytest berakar `tests/` sedangkan Vitest colocated; tidak konsisten satu model test per stack, tetapi sudah berfungsi.

---

**Kesimpulan Tahap A:** Struktur PIXEL-T saat ini **fungsional dan layering-nya sudah benar**, tetapi belum "sederhana". Tahap B akan memproduksi proposal target tanpa perubahan source.
