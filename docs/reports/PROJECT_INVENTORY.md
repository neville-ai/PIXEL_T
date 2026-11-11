# PROJECT INVENTORY — PIXEL-T & LUCIT-master

**Tanggal:** 11 November 2026
**Branch aktif:** `fitur/validasi-input`
**HEAD:** `cbb5296`
**Status working tree:** 3 file termodifikasi belum di-commit (`Backend/src/core/config.py`, `Backend/src/services/llm_image_validator.py`, `tests/Backend/test_llm_image_validator.py`) **pada saat inventaris (belum dihitungkan 10 file `.gitkeep`-only yang dihapus pada cleanup)**; **status terkini:** 18 file modified/deleted + 24 file untracked, staging kosong — lihat `FINAL_PROJECT_AUDIT.md` §3.
**Sifat dokumen:** inventarisasi read-only (belum ada file proyek yang diubah/dihapus pada fase ini).

---

## 0. Ringkasan Eksekutif

| Aspek | PIXEL-T | LUCIT-master |
|---|---|---|
| Tujuan | Analisis segmentasi polip kolonoskopi + Grad-CAM untuk dokter | Klasifikasi/segmentasi citra medis + chatbot |
| Frontend | React 18 + TypeScript + Vite 6 + Tailwind 3 | React 19 + TypeScript + Vite 7 + Tailwind-ish CSS |
| Backend | Flask 3 (application factory) | Flask 3 (module-level app) |
| AI Framework | PyTorch (U-Net + ResNet50, `segmentation-models-pytorch`) | TensorFlow/Keras + Gemini/Vertex |
| Database/Auth | Supabase (Postgres, Auth, Storage) | Supabase (Postgres, Auth) |
| Struktur | `Backend/src/{routes,controllers,services,repositories,core}` + `ai/inference` | `Backend/src/{routes,controllers,services,repositories,models,config}` |
| Tests | 188 pytest + 298 vitest (baseline dokumen) | Tidak ditemukan folder test |
| Entry point FE | `Frontend/src/main.tsx` → `App.tsx` → `AppRoutes.tsx` | `Frontend/src/main.tsx` → `App.tsx` (routing inline) |
| Entry point BE | `Backend/run.py` → `create_app()` | `Backend/src/main.py` (app global) |

Kesimpulan awal: PIXEL-T **sudah** menerapkan layering yang serupa dengan LUCIT (routes → controllers → services → repositories → core). Perbedaan terbesar bukan pada pola layering, melainkan pada **ukuran file/service**, **duplikasi dokumen**, **folder kosong (.gitkeep)**, **artefak build/log**, dan **beberapa file utilitas root** yang bukan bagian runtime. Refactoring harus fokus pada konsistensi & pembersihan berbasis bukti, bukan menyalin struktur LUCIT.

---

## 1. Struktur PIXEL-T Saat Ini

### 1.1 Peta direktori tingkat atas

```text
WEB_PIXELT/
├── .env.example              # template env (di-track)
├── .gitignore                # mengabaikan .env, node_modules, .venv, model, dataset, log, LUCIT-master
├── .vscode/settings.json     # setting editor
├── README.md                 # deskripsi proyek & stack
├── package.json              # dependency utilitas root (docx, canvas, supabase-js, ssr)
├── package-lock.json
├── generate_bab4.js          # generator dokumen BAB 4 (artefak skripsi, 53.6 KB)
├── render_erd.mjs            # render ERD (artefak skripsi)
├── rasterize_erd.py          # rasterisasi ERD ke gambar
├── rasterize_svg.py          # rasterisasi SVG
├── test_render.mjs           # uji render (artefak skripsi)
├── test_field.puml / .svg    # artefak uji diagram
├── backend_foreground.log    # log runtime (gitignored)
├── backend_foreground_err.log# log runtime (gitignored)
├── ai/                       # modul AI/ML (PyTorch)
├── Backend/                  # API Flask
├── database/                 # migration & SQL Supabase
├── diagram-skripsi/          # diagram PlantUML skripsi
├── docs/                     # dokumen spesifikasi & audit
├── Frontend/                 # SPA React/Vite
├── research/                 # notebook & hasil evaluasi model (bukti penelitian)
├── scripts/                  # script eksperimen/ kalibrasi/ evaluasi
├── tests/                    # pytest Backend/AI + test frontend env safety
├── calibration_data/         # dataset kalibrasi (gitignored)
├── references/               # referensi (gitignored)
├── LUCIT-master/             # proyek referensi (gitignored, JANGAN dihapus)
├── node_modules/             # dependency root (gitignored)
└── .venv/                    # virtualenv Python (gitignored)
```

### 1.2 Statistik file (tanpa `node_modules`, `.venv`, `.git`, cache, `LUCIT-master`, `calibration_data`, `references`)

- **Total file:** 273
- **Berdasarkan ekstensi:** `.py` 60, `.tsx` 45, tanpa ekstensi 35, `.md` 23, `.puml` 23, `.ts` 16, `.csv` 15, `.txt` 12, `.sql` 9, `.json` 7, `.png` 6, `.js` 4, `.css` 3, `.jpg` 3, `.log` 2, `.mjs` 2, `.html` 2, `.example` 1, `.svg` 1, `.yaml` 1
- **Berdasarkan area:** `frontend` 95, `docs` 42, `backend` 31, `scripts` 29, `tests` 22, `ai` 16, root 14, `database` 12, `diagram-skripsi` 8, `research` 3, `.vscode` 1

---

## 2. Struktur LUCIT-master (Referensi)

```text
LUCIT-master/
├── README.md
├── package-lock.json
├── .gitattributes
├── .vscode/settings.json
├── Backend/
│   ├── .gitignore / .python-version / inspect_table.py
│   ├── package.json / package-lock.json   # hanya @supabase/supabase-js
│   ├── requirements.txt                   # UTF-16LE: Flask 3.0.0, flask-cors 4.0.0,
│   │                                      # supabase 2.13.0, numpy 1.26.0, tensorflow>=2.16.1,
│   │                                      # opencv-python 4.8.1.78, Pillow 10.1.0,
│   │                                      # google-generativeai 0.8.6
│   └── src/
│       ├── main.py                        # entry point, app global, port 8000
│       ├── config/{settings.py, supabase.py}
│       ├── routes/{user_routes.py, chatbot_routes.py, prediction_routes.py}
│       ├── controllers/{user_controller.py, chatbot_controller.py, prediction_controller.py}
│       ├── services/{ai_validator_service.py, chatbot_service.py, email_service.py,
│       │             gradcam_service.py, segmentation_service.py, vertex_rest_client.py}
│       ├── repositories/{user_repository.py, analysis_repository.py}
│       └── models/{model_loader.py, user_schema.py}
└── Frontend/
    ├── .env.production / .gitignore / eslint.config.js
    ├── index.html / package.json / package-lock.json
    ├── public/images/*                    # aset publik
    ├── README.md
    └── src/
        ├── main.tsx / App.tsx             # routing INLINE di App.tsx (/, /analysis, /history)
        ├── index.css / App.css
        ├── assets/{images/*, style.css}
        ├── components/<NamaFitur>/index.tsx
        │   # Header, Hero, AboutUs, Features, Footer, LoginModal,
        │   # ScrollReveal, SlideTransition, SmoothScroll, SplashScreen, TransitionPortal
        ├── pages/analysis/index.tsx
        ├── pages/history/index.tsx
        └── utils/{api.ts, image.ts, session.ts, supabase.ts}
```

### 2.1 Pola LUCIT yang terverifikasi

| Pola | Bukti | Relevansi untuk PIXEL-T |
|---|---|---|
| Layering routes → controllers → services → repositories | `Backend/src/routes/*.py`, `controllers/*.py`, `services/*.py`, `repositories/*.py` | **Sudah diterapkan** di PIXEL-T |
| Config terpusat dari `.env` | `Backend/src/config/settings.py:1-38` | Sudah ada `Backend/src/core/config.py` |
| Supabase client terpusat | `Backend/src/config/supabase.py` | Sudah ada `Backend/src/core/supabase.py` |
| `utils/api.ts` untuk normalisasi base URL API | `Frontend/src/utils/api.ts:1-21` | PIXEL-T memakai `services/analysis.ts`; bisa dipertimbangkan helper serupa |
| Folder komponen per fitur (`components/NamaFitur/index.tsx`) | `Frontend/src/components/*/index.tsx` | PIXEL-T memakai `components/{auth,brand,layout,ui}` — sudah lebih granular |
| Route guard berbasis session lokal | `Frontend/src/App.tsx:50-76` | PIXEL-T memakai `ProtectedRoute/AdminRoute/DoctorRoute` — lebih eksplisit |
| Tidak ada folder test | seluruh `LUCIT-master` | **Jangan ditiru**: PIXEL-T sudah punya test suite |
| `app = Flask(__name__)` global | `Backend/src/main.py:17` | **Jangan ditiru**: PIXEL-T sudah memakai application factory |
| `tensorflow` + Vertex/Gemini + SMTP | `requirements.txt`, `services/*` | **Tidak relevan**: PIXEL-T memakai PyTorch + Gemini SDK, tanpa chatbot/email |

---

## 3. Fungsi Setiap Direktori Penting PIXEL-T

### 3.1 `ai/` — Modul AI/ML

| Path | Isi | Fungsi |
|---|---|---|
| `ai/__init__.py` | kosong | marker package |
| `Backend/ai/config/model_config.py` | 70 baris | Konfigurasi model (`MODEL_CONFIG`) dari env/YAML |
| `Backend/ai/config/model_config.example.yaml` | 782 B | contoh konfigurasi model |
| `Backend/ai/inference/preprocessing.py` | 28 baris | `prepare_image` (resize/normalisasi) |
| `Backend/ai/inference/segmentation.py` | 133 baris | `predict`, `count_forward_passes`, `SegmentationResult` (U-Net+ResNet50, TTA) |
| `Backend/ai/inference/postprocessing.py` | 126 baris | threshold 0.55, morfologi, komponen terbesar, metrik |
| `Backend/ai/inference/gradcam.py` | 188 baris | `generate_gradcam`, `GradCAMResult` |
| `Backend/ai/inference/domain_validator.py` | 314 baris | `ColonoscopyDomainValidator`, `DomainDecision` (heuristik domain) |
| `Backend/ai/inference/model_service.py` | 136 baris | pemuatan model/checkpoint & device |
| `Backend/ai/inference/pipeline.py` | 180 baris | `run_pipeline`, `PipelineResult`, fase inferensi |
| `Backend/ai/models/` | `.gitkeep` + checkpoint 135.6 MB | checkpoint produksi (gitignored, **jangan dihapus**) |
| `ai/README.md` | 1.7 KB | dokumentasi modul AI |

### 3.2 `Backend/` — API Flask

| Path | Baris | Fungsi |
|---|---|---|
| `run.py` | 15 | entry point: `create_app()` + `app.run()` |
| `app/__init__.py` | 33 | application factory, CORS, error handler, blueprint |
| `app/routes/health.py` | 14 | `GET /api/health` |
| `app/routes/analysis.py` | 64 | `POST /api/analysis`, `GET /api/analysis/<id>`, `GET /api/history`, `DELETE /api/history/<id>` |
| `app/routes/admin.py` | 45 | 5 endpoint admin |
| `app/controllers/analysis_controller.py` | 96 | validasi request & panggil `AnalysisService` |
| `app/controllers/admin_controller.py` | 98 | validasi request & panggil `AdminService` |
| `app/services/analysis_service.py` | **1147 total (1029 non-kosong)** | inti pipeline: validasi gambar, domain gate, LLM gate, storage, DB, queue worker, segmentation, Grad-CAM |
| `app/services/admin_service.py` | 378 | listing/statistik/detail/approve/reject dokter |
| `app/services/storage_service.py` | 189 | upload, signed URL, delete Supabase Storage |
| `app/services/llm_image_validator.py` | 232 | Gemini gate untuk validasi domain (config, schema, thinking, timeout) |
| `app/repositories/analysis_repository.py` | 196 | CRUD tabel analyses + validasi lifecycle status |
| `app/core/config.py` | 76 | konfigurasi env (termasuk LLM timeout/conf) |
| `app/core/auth.py` | 304 | verifikasi token Supabase, `require_approved_doctor`, `require_admin`, ownership |
| `app/core/errors.py` | 125 | `APIError` + handler error konsisten |
| `app/core/supabase.py` | 83 | inisialisasi client Supabase (service role & anon) |
| `app/models/`, `app/schemas/`, `app/utils/` | hanya `.gitkeep` | **folder kosong** — kandidat konsolidasi |
| `Backend/requirements.txt` | 399 B | dependency Python |
| `Backend/set_admin_role.py` | 3.4 KB | utilitas operasional set role admin |
| `Backend/.env` | 532 B | secret lokal (JANGAN dibaca/diubah/di-commit) |

### 3.3 `Frontend/` — SPA React

| Path | Baris | Fungsi |
|---|---|---|
| `src/main.tsx` | 10 | render `<App />` |
| `src/App.tsx` | 65 | `BrowserRouter` + `AuthProvider` + `ThemeBootstrap` + `AppShellSwitch` |
| `src/routes/AppRoutes.tsx` | 113 | seluruh route & guard |
| `src/context/AuthContext.tsx` | 277 | sesi Supabase, profil, role, status akun |
| `src/services/analysis.ts` | 225 | client API analisis & polling |
| `src/services/auth.ts` | 371 | registrasi/login/logout/reset |
| `src/services/profile.ts` | 391 | profil dokter & avatar |
| `src/lib/supabase.ts` | 28 | client Supabase FE |
| `src/lib/format.ts` | 81 | format tanggal/angka/label |
| `src/lib/openingTimeline.ts` | 176 | timeline animasi pembuka |
| `src/hooks/useTheme.ts` | 52 | tema dark/light |
| `src/hooks/useOpeningAnimation.ts` | 88 | state animasi pembuka |
| `src/components/layout/AppShell.tsx` | 425 | header/footer/nav global |
| `src/components/auth/*` | — | `ProtectedRoute`, `AdminRoute`, `DoctorRoute`, `PublicOnlyRoute`, `AuthLoadingState`, `OpeningAnimation` |
| `src/components/ui/*` | — | `Badge`, `Button`, `Card`, `EmptyState`, `ErrorState`, `Input`, `LoadingState`, `Modal`, `ThemeToggle` |
| `src/components/brand/LogoPixelT.tsx` | 126 | logo PIXEL-T |
| `src/pages/auth/Login.tsx` | 523 | halaman login |
| `src/pages/auth/Register.tsx` | 343 | registrasi dokter |
| `src/pages/auth/ResetPassword.tsx` | — | reset password |
| `src/pages/dashboard/Dashboard.tsx` | 297 | dashboard dokter |
| `src/pages/analysis/NewAnalysis.tsx` | **631** | upload, validasi file, submit, polling |
| `src/pages/analysis/AnalysisResult.tsx` | 356 | polling hasil, tampilan segmen/Grad-CAM |
| `src/pages/history/History.tsx` | 606 | riwayat + hapus |
| `src/pages/history/HistoryDetail.tsx` | 221 | detail riwayat |
| `src/pages/profile/DoctorProfile.tsx` | **1051** | profil dokter + avatar |
| `src/pages/admin/AdminDashboard.tsx` | **547** | kelola pendaftaran dokter |
| `src/pages/NotFound.tsx` | 39 | 404 |

### 3.4 `database/`

| Path | Fungsi |
|---|---|
| `migrations/001_create_analyses_and_storage.sql` | tabel analyses + bucket storage |
| `002_add_ai_pipeline_metadata.sql` | metadata pipeline AI |
| `003_add_analysis_progress.sql` | progres analisis |
| `004_create_doctor_profiles.sql` | profil dokter |
| `005_create_profile_avatars_bucket.sql` | bucket avatar |
| `006_add_avatar_url_to_doctor_profiles.sql` | kolom avatar |
| `007_add_role_and_account_status.sql` | role & status akun |
| `008_create_doctor_profile_trigger.sql` | trigger profil otomatis |
| `verify_doctor_registration.sql` | verifikasi registrasi |
| `README.md` | dokumentasi database |

### 3.5 `docs/`

Dokumen spesifikasi: `PRD_PIXEL-T_FINAL.md`, `FunctionalSpecification.md`, `StyleGuide.md`, `APIContract.md`, `DataModelSpecification.md`, `ModelIntegrationSpecification.md`, `CodebaseAnalysis.md`.
Dokumen audit: `docs/audit/*` (peta sistem, tindak lanjut, audit keamanan, hash, LLM gate, login fix, rencana refactor LUCIT).
Dokumen forensik admin: `ADMIN_DASHBOARD_AND_APPROVE_FORENSIC_REPORT.md`, `APROVE_DOKTER_FIX_REPORT.md`, `DOMAIN_VALIDATION_FALSE_ACCEPTANCE_FIX_REPORT.md`.
Diagram: `docs/diagrams/*.puml` (activity/sequence/use-case) dan duplikat di `diagram-skripsi/`.
Beberapa dokumen punya pasangan `.md` + `.txt` (APIContract, StyleGuide, DataModelSpecification, AdminDashboardAndApproveForensicReport) → **kandidat duplikat**, tetapi merupakan artefak skripsi sehingga harus dipertahankan sampai dikonfirmasi.

### 3.6 `tests/`

| Path | Fungsi |
|---|---|
| `tests/conftest.py` | fixture pytest |
| `tests/Backend/test_analysis.py` | API analisis |
| `tests/Backend/test_auth.py` | auth & guard |
| `tests/Backend/test_admin_routes.py`, `test_admin_service.py` | admin |
| `tests/Backend/test_domain_validation_api.py` | regresi domain validation |
| `tests/Backend/test_history.py` | history |
| `tests/Backend/test_llm_image_validator.py` | Gemini gate (sedang diubah) |
| `tests/Backend/test_repository.py` | repository |
| `tests/Backend/test_storage_service.py` | storage |
| `tests/Backend/test_supabase_config.py` | konfigurasi Supabase |
| `tests/ai/test_domain_validator.py`, `test_gradcam.py`, `test_model_integration.py`, `test_post_segmentation_validation.py` | AI |
| `tests/ai/audit_domain_validator_deep.py`, `measure_real_samples_stage2.py` | script audit (bukan unit test biasa; di-ignore pada baseline pytest) |
| `tests/Frontend/test_frontend_env_safety.py` | keamanan env FE |
| Frontend: 19 file `*.test.ts(x)` di `Frontend/src/**` | vitest |

### 3.7 `scripts/`

`calibrate_domain_gate.py` (34.7 KB), `experiment_domain_gate.py` (29 KB), `eval_llm_gate.py` (20.7 KB), `generate_section1_data.py` (17.7 KB), `smoke_llm_gate.py` (12 KB), `evaluate_holdout.py`, `verify_b0_strong.py`, `verify_c2_calib_match.py`, serta `scripts/output/*` (CSV hasil eksperimen). **Semua adalah artefak penelitian/eksperimen — jangan hapus.**

### 3.8 `research/`

`PIXEL-T_Scenario1_Ver22_config.json`, `PIXEL-T_Scenario1_Ver22_evaluation_results.csv`, `segmentationcolonpolyp-unet-resnet50-gradcam.ipynb`. **Bukti penelitian — jangan hapus.**

---

## 4. File Entry Point

| Proyek | Entry point | Bukti |
|---|---|---|
| PIXEL-T Backend | `Backend/run.py` → `app.create_app()` | `Backend/run.py:7-15`, `Backend/src/__init__.py:8-33` |
| PIXEL-T Frontend | `Frontend/index.html` → `Frontend/src/main.tsx` → `App.tsx` | `Frontend/src/main.tsx:1-10`, `Frontend/src/App.tsx:54-65` |
| PIXEL-T AI | `Backend/ai/inference/pipeline.py:run_pipeline` (dipanggil `AnalysisService`) | `Backend/src/services/analysis_service.py:23,906,1118,1133` |
| LUCIT Backend | `LUCIT-master/Backend/src/main.py` | `main.py:17-56` |
| LUCIT Frontend | `LUCIT-master/Frontend/src/main.tsx` → `App.tsx` | `App.tsx:146-202` |

---

## 5. Dependency Utama

### 5.1 Backend PIXEL-T (`Backend/requirements.txt`)

- Web: `Flask>=3.0.0,<4`, `Flask-Cors>=4,<6`, `python-dotenv>=1.0`
- Supabase: `supabase>=2.10,<3`
- AI/CV: `torch>=2.2`, `torchvision>=0.17`, `segmentation-models-pytorch>=0.5,<0.6`, `numpy>=1.26,<2.2`, `scipy>=1.13,<2`, `opencv-python-headless>=4.10,<5`, `Pillow>=10.2`
- Test: `pytest>=8`, `pytest-mock>=3.12`
- **Catatan:** import `google.genai` dipakai `llm_image_validator.py`; paket `google-genai` **sudah tercantum** di `requirements.txt` sebagai `google-genai>=3.0.0,<3.1.0` (ditambahkan pada cleanup).

### 5.2 Frontend PIXEL-T (`Frontend/package.json`)

- Runtime: `react ^18.3.1`, `react-dom ^18.3.1`, `react-router-dom ^7.18.4`, `@supabase/supabase-js ^2.48.1`, `lucide-react ^0.475.0`, `sharp ^0.35.5`
- Dev: `vite ^6.1.0`, `typescript ~5.7.2`, `vitest ^5.0.2`, `@testing-library/react ^16.3.3`, `jsdom ^30.1.1`, `tailwindcss ^3.4.17`, `postcss ^8.5.2`, `autoprefixer ^10.4.20`, `@vitejs/plugin-react ^4.3.4`

### 5.3 Root (`package.json`)

`@supabase/ssr`, `@supabase/supabase-js`, `canvas`, `docx` — dipakai oleh script skripsi (`generate_bab4.js`, `render_erd.mjs`, rasterize). **Bukan runtime aplikasi**, tetapi diperlukan untuk reproduksi dokumen.

### 5.4 LUCIT-master

- Backend: Flask 3.0.0, flask-cors 4.0.0, supabase 2.13.0, python-dotenv 1.0.0, numpy 1.26.0, tensorflow>=2.16.1, opencv-python 4.8.1.78, Pillow 10.1.0, google-generativeai 0.8.6 (requirements UTF-16LE)
- Frontend: React 19.2, react-dom 19.2, react-router-dom 7.13, @supabase/supabase-js 2.101, lenis, react-markdown, sonner; dev: Vite 7.2, TypeScript 5.9, ESLint 9

---

## 6. Hubungan Antar Modul (PIXEL-T)

```text
Frontend
  App.tsx
   └─ AppRoutes.tsx
       ├─ AuthContext.tsx ── lib/supabase.ts
       ├─ services/auth.ts
       ├─ services/analysis.ts ── fetch /api/*
       └─ services/profile.ts
              │  HTTP (Bearer token Supabase)
              ▼
Backend
  run.py → app.create_app()
   ├─ core/config.py, core/errors.py, core/supabase.py
   ├─ routes/{health,analysis,admin}.py
   │    └─ core/auth.py (require_approved_doctor / require_admin)
   ├─ controllers/{analysis,admin}_controller.py
   ├─ services/{analysis,admin,storage,llm_image_validator}.py
   │    └─ Backend/ai/inference/{pipeline,segmentation,preprocessing,
   │                      postprocessing,gradcam,domain_validator,
   │                      model_service}.py
   └─ repositories/analysis_repository.py ── Supabase Postgres
```

**Ketergantungan penting:**
- `analysis_service.py` mengimpor 7 modul `ai/inference` + `ai/config` (lihat `analysis_service.py:20-25`).
- `llm_image_validator.py` mengimpor `google.genai` secara lazy (`:116`, `:181`).
- `analysis_repository.py` memakai `get_supabase_client` dengan opsi `use_service_role` (`:19-23`).
- `storage_service.py` memakai `get_supabase_client` (`:4`).
- Frontend memanggil API melalui `services/*.ts`; tidak ada pemanggilan langsung Supabase untuk tabel analisis (hanya auth/session dan signed URL).

---

## 7. Kontrak API (Ringkas, terverifikasi)

| Method | Path | Guard | Sumber |
|---|---|---|---|
| GET | `/api/health` | publik | `routes/health.py:6-14` |
| POST | `/api/analysis` | `require_approved_doctor` | `routes/analysis.py:11-26` |
| GET | `/api/analysis/<analysis_id>` | `require_approved_doctor` | `routes/analysis.py:29-42` |
| GET | `/api/history` | `require_approved_doctor` | `routes/analysis.py:45-53` |
| DELETE | `/api/history/<analysis_id>` | `require_approved_doctor` | `routes/analysis.py:56-64` |
| GET | `/api/admin/doctors` | `require_admin` | `routes/admin.py:9-13` |
| GET | `/api/admin/doctors/stats` | `require_admin` | `routes/admin.py:16-20` |
| GET | `/api/admin/doctors/<doctor_id>` | `require_admin` | `routes/admin.py:23-27` |
| POST | `/api/admin/doctors/<doctor_id>/approve` | `require_admin` | `routes/admin.py:30-34` |
| POST | `/api/admin/doctors/<doctor_id>/reject` | `require_admin` | `routes/admin.py:37-45` |

Blueprint terdaftar di `/api` (`routes/__init__.py:6-10`).

---

## 8. File yang Berpotensi Duplikat

| Kelompok | Bukti | Penilaian |
|---|---|---|
| `.gitkeep` (24 file total; 22 di luar `node_modules`) | scan hash identik | **Bukan duplikat kode**; penanda folder kosong |
| Aset `Frontend/dist/assets/*` vs `Frontend/src/assets/*` | hash identik (`icon-doctor`, logo light/transparent) | `dist/` adalah hasil build → **regenerable**, bukan sumber |
| `package.json` root vs `Frontend/package.json` | nama & isi berbeda | Bukan duplikat; root untuk tooling skripsi |
| `docs/APIContract.md` vs `.txt` | pasangan dokumen | Duplikat format; pertahankan sampai dikonfirmasi |
| `docs/StyleGuide.md` vs `.txt` | pasangan dokumen | idem |
| `docs/DataModelSpecification.md` vs `.txt` | pasangan dokumen | idem |
| `docs/ADMIN_DASHBOARD_AND_APPROVE_FORENSIC_REPORT.md` vs `.txt` | pasangan dokumen | idem |
| `diagram-skripsi/*` vs `docs/diagrams/*` | diagram serupa (activity/sequence) | Duplikat artefak; pertahankan |
| `Frontend/dist/index.html` vs `Frontend/index.html` | hasil build | regenerable |
| `tests/Frontend/test_frontend_env_safety.py` | satu-satunya test Python "frontend" | bukan duplikat; menjaga keamanan env |

---

## 9. File yang Berpotensi Tidak Digunakan (perlu pembuktian lebih lanjut)

> **Status: BELUM DIHAPUS.** Semua item di bawah hanya kandidat; keputusan akhir menunggu Fase 5–6 dengan bukti referensi.

| Kandidat | Alasan awal | Bukti yang harus dicek |
|---|---|---|
| `backend_foreground.log`, `backend_foreground_err.log` | log runtime, gitignored | bukan kode; aman dibersihkan setelah konfirmasi |
| `Frontend/dist/` | hasil build | gitignored; regenerate via `npm run build` |
| `Frontend/tsconfig.tsbuildinfo` | cache build | gitignored; regenerate |
| Folder `.gitkeep`-only: `Backend/src/models`, `Backend/src/schemas`, `Backend/src/utils`, `database/seed`, `Frontend/src/components/{analysis,history}`, `Frontend/src/{types,utils}`, `scripts/{deployment,setup}` | folder kosong | cek import/dynamic path sebelum konsolidasi |
| `test_field.puml`, `test_field.svg`, `test_render.mjs` | artefak uji render di root | cek apakah bagian bukti skripsi |
| `generate_bab4.js`, `rasterize_erd.py`, `rasterize_svg.py`, `render_erd.mjs` | tooling skripsi | **JANGAN hapus** tanpa konfirmasi; bagian reproduksi dokumen |
| `scripts/output/*` | hasil eksperimen | bukti penelitian; pertahankan |
| `docs/*.txt` pasangan `.md` | duplikat format | pertahankan sampai dikonfirmasi |

**Kesimpulan sementara:** tidak ada file kode aplikasi yang terbukti tidak terpakai dari inventaris ini. Kandidat pembersihan utama hanya artefak build/log yang gitignored dan dapat diregenerasi.

---

## 10. File yang TIDAK BOLEH Diubah / Dihapus

1. **Model & inferensi:** `Backend/ai/models/PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth`, `Backend/ai/config/model_config.py`, `Backend/ai/inference/*` — jangan ubah arsitektur, checkpoint, threshold, preprocessing, TTA, postprocessing, target layer Grad-CAM.
2. **Database:** seluruh `database/migrations/*.sql`, `database/verify_doctor_registration.sql` — jangan ubah schema/RLS.
3. **Auth & keamanan:** `Backend/src/core/auth.py`, `Backend/src/core/supabase.py`, `.env` (backend & frontend), `.env.example` (kecuali penambahan key baru yang disetujui).
4. **API contract:** path/method/response di `Backend/src/routes/*`, `Backend/src/controllers/*`, `Frontend/src/utils/*`.
5. **Domain Validation:** `Backend/ai/inference/domain_validator.py`, `Backend/src/services/llm_image_validator.py`, gate di `analysis_service.py`.
6. **Tests:** seluruh `tests/**` dan `Frontend/src/**/*.test.*`.
7. **Artefak penelitian:** `research/*`, `scripts/output/*`, `calibration_data/*`, `references/*`.
8. **LUCIT-master/** — jangan dihapus/diubah (referensi).
9. **Entry point & konfigurasi build:** `Backend/run.py`, `Frontend/src/main.tsx`, `Frontend/vite.config.ts`, `Frontend/tsconfig.json`, `Frontend/tailwind.config.js`, `Frontend/postcss.config.js`, `Frontend/index.html`.
10. **Dokumentasi skripsi:** `docs/PRD_PIXEL-T_FINAL.md`, `docs/StyleGuide.md`, `docs/FunctionalSpecification.md`, `docs/APIContract.md`, `docs/DataModelSpecification.md`, `docs/ModelIntegrationSpecification.md`, `diagram-skripsi/*`.

---

## 11. Baseline Git & Pengujian (kondisi awal)

| Item | Nilai | Sumber |
|---|---|---|
| Branch | `fitur/validasi-input` | `git branch --show-current` |
| HEAD | `cbb5296` | `git log --oneline -5` |
| File termodifikasi (saat inventaris) | 3 (config, llm_image_validator, test_llm_image_validator); status terkini: 18 modified/deleted + 24 untracked | `git status --short`; `FINAL_PROJECT_AUDIT.md` §3 |
| pytest baseline | **190 passed, 1 skipped** (aktual 11 Nov 2026; dokumen lama mencatat 188) | `BASELINE_TEST_REPORT.md`; `baseline_pytest.log` |
| vitest baseline | 298 passed (19 file) | `docs/audit/refactor_lucit_plan.md:17` |
| Build frontend baseline | berhasil | `docs/audit/refactor_lucit_plan.md:18` |
| Perubahan Gemini belum di-commit | ya | working tree |

**Catatan:** baseline di atas berasal dari dokumen perencanaan refactor sebelumnya. Fase 3 (BASELINE) akan menjalankan ulang test secara langsung untuk memverifikasi angka aktual sebelum refactoring.

---

## 12. Temuan Inventaris yang Perlu Tindak Lanjut (belum diubah)

1. **`google-genai` tidak tercantum di `Backend/requirements.txt`** meskipun diimpor `llm_image_validator.py`. Risiko reproducibility. → kandidat perbaikan aman (menambah dependency, bukan mengubah perilaku).
2. **`analysis_service.py` 1147 baris total saat ini (1029 baris non-kosong; 1145 pada HEAD `cbb5296`)** - tanggung jawab sangat luas (validasi, gate, storage, DB, queue, pipeline, progress). Kandidat pemecahan bertahap **hanya jika** dapat dibuktikan tidak mengubah perilaku; **DITUNDA** pada Tahap 7 (keputusan pengguna).
3. **Folder kosong:** 10 direktori `.gitkeep`-only sudah dihapus pada cleanup; 22 file `.gitkeep` masih tersisa dan dipetakan — dapat dikonsolidasi/dipertahankan sesuai kebutuhan struktur target.
4. **Duplikasi dokumen `.md`/`.txt`** — perlu konfirmasi apakah bagian skripsi.
5. **`Frontend/dist` & `tsconfig.tsbuildinfo`** ada di working tree (gitignored) — artefak build, bukan sumber.
6. **Log runtime di root** — artefak, bukan kode.
7. **Root tooling skripsi** (`generate_bab4.js` dkk.) — bukan runtime; jangan dihapus tanpa konfirmasi.
8. **Kontrak API** sudah konsisten antara `routes/*` dan `services/*.ts` (akan diverifikasi detail pada Fase 2–3).

---

## 13. Ringkasan untuk Fase Berikutnya

- **Fase 2 (Analysis):** bandingkan pola LUCIT vs PIXEL-T secara mendalam; konfirmasi bahwa layering PIXEL-T sudah setara/better; identifikasi pola LUCIT yang layak diadopsi (mis. helper `utils/api.ts`, folder per fitur) tanpa mengubah perilaku.
- **Fase 3 (Baseline):** jalankan `pytest`, `vitest`, `tsc -b`, `vite build`; catat hasil aktual.
- **Fase 4 (Design):** susun `TARGET_ARCHITECTURE.md`; tentukan file pindah/gabung/hapus dengan peta import.
- **Fase 5–6 (Refactor & Cleanup):** perubahan kecil, dapat di-rollback, didahului bukti referensi.
- **Fase 7–8 (Regression & Reporting):** uji seluruh alur dan tulis laporan akhir.

> Dokumen ini **belum** menyatakan ada fitur yang boleh dihapus. Semua kandidat pembersihan wajib melalui pembuktian referensi pada fase berikutnya.
