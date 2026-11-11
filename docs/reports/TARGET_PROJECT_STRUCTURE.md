# TARGET PROJECT STRUCTURE — PIXEL-T

**Tanggal:** 11 November 2026  
**Branch:** `fitur/validasi-input` (HEAD `cbb5296`)  
**Status:** rancangan target. **Belum ada file yang dipindahkan/diubah/dihapus.**  
**Prinsip:** safety > functionality > correctness > maintainability > simplicity.  
**Batasan:** PIXEL-T bukan hanya aplikasi web; struktur target harus mempertahankan komponen penelitian (AI, data, skrip, dokumentasi, diagram, referensi).

---

## 0. Keputusan Utama

1. **Tidak memaksa seluruh proyek masuk `Backend/` + `Frontend/`.**
2. **Tidak menyalin kelemahan LUCIT** (app global, password plaintext, base64 DB, error handling per-route, tanpa test).
3. **Tidak mengubah** API contract, DB schema/RLS, auth, Supabase, atau AI/ML.
4. **Tidak menghapus** checkpoint, dataset, notebook, `.env`, `.env.example`, `.gitignore`, lockfile, migration, `references`, kalibrasi, skrip diagram, `LUCIT-master`, `node_modules`, `.venv`.
5. **Perubahan hanya boleh dilakukan setelah approval eksplisit** dan regresi penuh.

---

## 1. Struktur Target (To-Be)

```text
WEB_PIXELT/
├── README.md                         # panduan 2-terminal + arsitektur 3 pilar
├── .env.example                      # template root (dipertahankan)
├── .gitignore                        # env/dependency/model/dataset/log
├── Backend/
│   ├── .env.example                  # template backend
│   ├── requirements.txt              # termasuk google-genai
│   ├── run.py                        # entry point
│   ├── set_admin_role.py             # utilitas operasional
│   └── app/
│       ├── __init__.py               # create_app factory
│       ├── core/
│       │   ├── auth.py               # Bearer + role/status
│       │   ├── config.py             # config env
│       │   ├── errors.py             # APIError + handler global
│       │   └── supabase.py           # client anon/service-role
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── health.py
│       │   ├── analysis.py
│       │   └── admin.py
│       ├── controllers/
│       │   ├── analysis_controller.py
│       │   └── admin_controller.py
│       ├── services/
│       │   ├── analysis_service.py   # facade publik tetap
│       │   ├── admin_service.py
│       │   ├── storage_service.py
│       │   └── llm_image_validator.py
│       └── repositories/
│           └── analysis_repository.py
├── Frontend/
│   ├── .env.example                  # template VITE_*
│   ├── package.json / lock
│   ├── index.html
│   ├── vite.config.ts / tsconfig.json / tailwind.config.js / postcss.config.js
│   └── src/
│       ├── main.tsx / App.tsx
│       ├── routes/AppRoutes.tsx
│       ├── context/AuthContext.tsx
│       ├── services/{analysis,auth,profile}.ts
│       ├── lib/{supabase,format,openingTimeline}.ts
│       ├── hooks/{useTheme,useOpeningAnimation}.ts
│       ├── components/
│       │   ├── ui/*
│       │   ├── auth/*Route.tsx
│       │   ├── layout/AppShell.tsx
│       │   └── brand/LogoPixelT.tsx
│       ├── pages/{auth,dashboard,analysis,history,profile,admin,NotFound}
│       ├── assets/*
│       └── styles/opening.css
├── ai/                               # DILINDUNGI — jangan diubah/dipindah
│   ├── config/
│   │   ├── model_config.py
│   │   └── model_config.example.yaml
│   ├── inference/
│   │   ├── model_service.py
│   │   ├── preprocessing.py
│   │   ├── segmentation.py
│   │   ├── postprocessing.py
│   │   ├── gradcam.py
│   │   ├── domain_validator.py
│   │   └── pipeline.py
│   └── models/
│       ├── .gitkeep
│       └── PIXEL-T_..._best.pth      # checkpoint (gitignored)
├── database/
│   ├── README.md
│   ├── migrations/001–008.sql
│   └── verify_doctor_registration.sql
├── tests/
│   ├── conftest.py
│   ├── Backend/*.py                  # 145 passed, 1 skipped
│   ├── ai/*.py                       # AI unit/integration
│   └── Frontend/test_frontend_env_safety.py
├── research/                         # F — bukti penelitian
│   ├── ...config.json
│   ├── ...evaluation_results.csv
│   └── ...notebook.ipynb
├── scripts/                          # F — eksperimen/kalibrasi
│   ├── calibrate_domain_gate.py
│   ├── experiment_domain_gate.py
│   ├── eval_llm_gate.py
│   ├── generate_section1_data.py
│   ├── smoke_llm_gate.py
│   ├── evaluate_holdout.py
│   ├── verify_b0_strong.py
│   ├── verify_c2_calib_match.py
│   └── output/*.csv|*.txt|*.jpg
├── docs/                             # F — spesifikasi/audit skripsi
│   ├── PRD, FunctionalSpecification, StyleGuide,
│   │   APIContract, DataModelSpecification,
│   │   ModelIntegrationSpecification, CodebaseAnalysis
│   ├── audit/*.md
│   ├── forensic reports
│   └── diagrams/*.puml
├── diagram-skripsi/                  # F — diagram final
│   ├── class/class_diagram.puml
│   └── sequence/*_FINAL.puml
├── references/                       # F — referensi (gitignored)
├── calibration_data/                 # F — dataset kalibrasi (gitignored)
├── LUCIT-master/                     # F — referensi read-only
├── node_modules/                     # D — dependency
└── .venv/                            # D — virtualenv
```

**Catatan:** `_archive/` **tidak** dimasukkan ke target wajib. Relokasi tooling diagram root ditunda; jika nanti dilakukan, path `generate_bab4.js` harus disesuaikan lebih dahulu.

---

## 2. File/Folder yang Tetap di Tempat

| Area | Alasan |
|---|---|
| `Backend/ai/config/model_config.py`, `Backend/ai/inference/*` | Model, threshold, TTA, Grad-CAM — dilindungi |
| `Backend/ai/models/*.pth` | Checkpoint produksi |
| `Backend/src/routes/*` | API contract |
| `Backend/src/controllers/*` | Request handling; admin envelope diselaraskan internal |
| `Backend/src/core/*` | Auth, config, error, Supabase |
| `Frontend/src/**` | UI yang sudah berfungsi |
| `database/migrations/*` | Schema/RLS |
| `tests/**` | Bukti regresi |
| `research/`, `scripts/`, `docs/`, `diagram-skripsi/`, `references/` | Artefak penelitian/skripsi |
| `.env`, `.env.example`, `.gitignore`, lockfile | Konfigurasi lingkungan/keamanan |
| `LUCIT-master/` | Referensi read-only |

---

## 3. Perubahan Target yang Diusulkan (belum dieksekusi)

### 3.1 Prioritas rendah — pembersihan non-perilaku

| No | Perubahan | Kategori | Risiko | Alasan |
|---|---|---|---|---|
| T1 | Hapus sisa `.gitkeep` di folder yang sudah berisi file | B/D | Rendah | Tidak ada import |
| T2 | Bersihkan `dist/`, `tsconfig.tsbuildinfo`, `.pytest_cache/`, log | D | Rendah | Regenerable |
| T3 | Sinkronkan dokumentasi laporan (tanpa hapus) | C | Rendah | Konsistensi |
| T4 | Verifikasi `.gitignore` dan `.env.example` | A | Rendah | Keamanan |

### 3.2 Prioritas sedang — simplifikasi internal

| No | Perubahan | Kategori | Risiko | Syarat |
|---|---|---|---|---|
| T5 | Ekstrak helper Bearer token di `core/auth.py` | B | Rendah | Test auth lulus |
| T6 | Normalisasi envelope error `admin_controller.py` | B | Sedang | Cek `AdminDashboard`/test |
| T7 | Tambah batas polling `NewAnalysis` | B | Sedang | Test UI |
| T8 | Ekstrak subkomponen halaman besar | B | Sedang | UI/DOM tidak berubah |

### 3.3 Prioritas tinggi — hanya setelah approval khusus

| No | Perubahan | Kategori | Risiko | Syarat |
|---|---|---|---|---|
| T9 | Pecah `analysis_service.py` menjadi modul internal dengan facade tetap | B | Tinggi | Regresi penuh + review nama publik |
| T10 | Relokasi tooling diagram root | E/F | Sedang | Path `__dirname` diperbaiki + render test |
| T11 | Rapikan `scripts/` ke subfolder | E/F | Tinggi | Import antar-skrip + root path diverifikasi |

**T9–T11 tidak boleh dijalankan pada tahap ini.**

---

## 4. Aturan Struktur untuk Mencegah “Kembali Berantakan”

1. **Satu entry point:** backend `run.py`; frontend `main.tsx`; AI `pipeline.py`.
2. **Satu sumber config:** `Backend/src/core/config.py`, `Frontend/.env`, `Backend/ai/config/model_config.py`.
3. **Satu client Supabase per konteks:** backend `core/supabase.py`; frontend `lib/supabase.ts`.
4. **Route tipis:** route hanya dekorator, parsing request minimal, dan panggil controller.
5. **Controller tidak mengakses DB langsung:** gunakan service/repository.
6. **Service AI tidak menyentuh HTTP:** pipeline hanya menghasilkan artefak.
7. **Test berada di `tests/` atau berdampingan sebagai `*.test.ts(x)`;** jangan campur script audit dengan unit test.
8. **File >500 baris wajib punya alasan**; jika tidak, kandidat ekstraksi internal.
9. **Jangan menaruh file tooling skripsi di root** setelah path diperbaiki; gunakan folder tooling yang jelas.
10. **Jangan menghapus artefak penelitian** tanpa persetujuan tertulis.

---

## 5. Perbandingan Target vs LUCIT

| Area | LUCIT | Target PIXEL-T | Alasan |
|---|---|---|---|
| Entry backend | global app | application factory | testability |
| Model | TensorFlow/Vertex | PyTorch/U-Net+ResNet50 | penelitian |
| Frontend routing | inline | `AppRoutes.tsx` | keterbacaan |
| Auth | localStorage + cookie | Supabase Bearer + guard | keamanan |
| Error | per route | global envelope | konsistensi |
| Tests | tidak ada | pytest + vitest | kualitas |
| Riset | tidak ada | `research/`, `scripts/`, `docs/`, `diagram-skripsi/` | skripsi |

---

## 6. Kriteria Keberhasilan Struktur Target

| Kriteria | Target |
|---|---|
| `pytest` | ≥190 passed, 1 skipped, 0 failed |
| `vitest` | ≥298 passed, 0 failed |
| `npm run build` | sukses, 0 error |
| `pip check` | no broken requirements |
| SHA-256 checkpoint | cocok `46521AE9...C581` |
| API contract | tidak berubah |
| AI config | threshold 0.55, TTA, Grad-CAM, preprocessing tetap |
| `.env` | tidak ter-track |
| File penelitian | utuh |
| Manual E2E | dijalankan sebelum commit final (status saat ini **NOT TESTED**) |

---

## 7. Kesimpulan

Target struktur mempertahankan semua pilar PIXEL-T: backend, frontend, AI, database, test, dan penelitian. Perubahan yang diusulkan bersifat **pembersihan dan simplifikasi internal**, bukan migrasi besar. Tidak ada file yang dipindahkan/diubah/dihapus sampai persetujuan eksplisit.
