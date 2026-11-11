# DEPENDENCY MAP — PIXEL-T

**Tanggal:** 11 November 2026  
**Branch:** `fitur/validasi-input` (HEAD `cbb5296`)  
**Sifat:** peta ketergantungan read-only. Tidak ada import, dependency, atau file yang diubah.  
**Tujuan:** memastikan setiap file yang diusulkan untuk disederhanakan/dipindah memiliki bukti pemakai dan tidak memutus jalur runtime, test, CLI, deployment, atau penelitian.

---

## 0. Ringkasan

| Lapisan | Ketergantungan utama | Status |
|---|---|---|
| Entry backend | `Backend/run.py` → `app.create_app()` | Stabil |
| API | routes → controllers → services → repositories/core | Stabil |
| AI | service → `ai.inference.pipeline` → model/preprocessing/segmentation/postprocessing/Grad-CAM | Stabil, dilindungi |
| Frontend | pages → services → `lib/supabase` / `fetch` backend | Stabil |
| Database | repository/service → Supabase; migration terpisah | Stabil |
| Test | pytest + vitest + mock | 190 + 298 lulus |
| Tooling skripsi | root script → `references/`, `canvas`, `docx` | Tidak runtime |

**Tidak ditemukan import melingkar runtime** pada modul Backend/AI/frontend yang diperiksa.

---

## 1. Peta Backend

```text
Backend/run.py
└── app.create_app()                         app/__init__.py
    ├── app.core.config                     config env
    ├── app.core.errors                     APIError + handler global
    ├── app.routes.register_blueprints      routes/__init__.py
    │   ├── routes/health.py
    │   ├── routes/analysis.py
    │   │   ├── app.core.auth               require_approved_doctor
    │   │   └── app.controllers.analysis_controller
    │   │       └── app.services.analysis_service
    │   │           ├── app.repositories.analysis_repository
    │   │           ├── app.services.storage_service
    │   │           ├── app.services.llm_image_validator (lazy)
    │   │           └── ai.inference.pipeline / gradcam / segmentation / domain
    │   └── routes/admin.py
    │       ├── app.core.auth               require_admin
    │       └── app.controllers.admin_controller
    │           └── app.services.admin_service
    │               └── app.core.supabase
    └── app.core.supabase                   anon + service role client
```

### 1.1 Tabel edge backend

| Dari | Ke | Bukti / catatan |
|---|---|---|
| `run.py` | `app.create_app` | entry point |
| `app/__init__.py` | `core.config`, `core.errors`, `routes` | factory |
| `routes/analysis.py` | `core.auth`, `controllers.analysis_controller` | thin route |
| `routes/admin.py` | `core.auth`, `controllers.admin_controller` | thin route |
| `controllers.analysis_controller` | `services.analysis_service`, `core.errors` | request handling |
| `controllers.admin_controller` | `services.admin_service`, `core.errors` | request handling |
| `services.analysis_service` | `repositories.analysis_repository`, `storage_service` | persistensi/storage |
| `services.analysis_service` | `ai.inference.pipeline`, `segmentation`, `gradcam`, `domain_validator`, `preprocessing` | inferensi |
| `services.analysis_service` | `core.errors`, `core.config` | error + timeout/config |
| `services.llm_image_validator` | `google.genai` | lazy import |
| `services.storage_service` | `core.supabase`, `core.config` | file storage |
| `repositories.analysis_repository` | `core.supabase` | tabel `analyses` |
| `services.admin_service` | `core.supabase`, `core.errors` | admin DB |
| `core.auth` | `core.supabase`, `core.errors` | verifikasi token + query profil |

### 1.2 Modul yang tidak boleh diputus

- `AnalysisService` mengimpor `run_pipeline`, `predict`, `count_forward_passes`, `generate_gradcam`, `prepare_image`, `ColonoscopyDomainValidator`, `MODEL_CONFIG`.
- `PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth` dibaca oleh `ModelService`; hash diverifikasi.
- Semua route publik tetap di `/api` (blueprint prefix).

---

## 2. Peta Modul AI

```text
Backend/ai/config/model_config.py
  └── MODEL_CONFIG (frozen): arsitektur, checkpoint, threshold 0.55,
      TTA scales/orientations, target layer Grad-CAM, postprocessing

Backend/ai/inference/model_service.py
  └── load checkpoint + device (lazy)

Backend/ai/inference/preprocessing.py
  └── prepare_image: resize 512, ImageNet normalization

Backend/ai/inference/segmentation.py
  ├── ModelService
  ├── preprocessing
  └── TTA 5×5 + sigmoid + threshold + count_forward_passes

Backend/ai/inference/postprocessing.py
  └── morphology, area filter, fill holes, measure_mask

Backend/ai/inference/gradcam.py
  ├── ModelService
  └── target layer dari MODEL_CONFIG; heatmap/overlay

Backend/ai/inference/domain_validator.py
  └── heuristik warna/tekstur -> DomainDecision

Backend/ai/inference/pipeline.py
  ├── domain_validator
  ├── preprocessing
  ├── segmentation.predict
  ├── postprocessing
  ├── gradcam
  └── komposisi artefak PNG
```

**Aturan:** `ai/**` adalah inti penelitian. Tidak ada file di `ai/` yang boleh dipindah/diubah pada refactor struktur. `tests/ai/**` mengunci perilaku ini.

---

## 3. Peta Frontend

```text
main.tsx
└── App.tsx
    ├── BrowserRouter
    ├── AuthProvider (context/AuthContext.tsx)
    │   ├── services/auth.ts -> lib/supabase.ts
    │   └── fetchUserProfileStatus -> Supabase doctor_profiles
    ├── AppRoutes.tsx
    │   ├── components/auth/{Protected,Admin,Doctor,PublicOnly}Route
    │   ├── pages/auth/{Login,Register,ResetPassword}
    │   ├── pages/dashboard/Dashboard
    │   ├── pages/analysis/{NewAnalysis,AnalysisResult}
    │   │   └── services/analysis.ts -> fetch backend /api
    │   ├── pages/history/{History,HistoryDetail}
    │   ├── pages/profile/DoctorProfile -> services/profile.ts
    │   ├── pages/admin/AdminDashboard -> services/profile.ts/auth
    │   └── pages/NotFound
    ├── components/layout/AppShell
    ├── components/ui/*
    ├── components/brand/LogoPixelT
    └── hooks/useTheme, useOpeningAnimation -> lib/openingTimeline
```

### 3.1 Edge frontend

| Dari | Ke | Catatan |
|---|---|---|
| `services/analysis.ts` | `lib/supabase.ts` | ambil sesi untuk Bearer |
| `services/analysis.ts` | backend `/api/analysis`, `/api/history` | upload/poll/history/delete |
| `services/auth.ts` | `lib/supabase.ts` | signUp/signIn/signOut/reset |
| `services/auth.ts` | Supabase `doctor_profiles` | role/status |
| `services/profile.ts` | Supabase / backend | profil/avatar |
| `context/AuthContext.tsx` | `services/auth.ts` | state auth |
| halaman | `components/ui/*` | komponen presentasional |
| `AppShell` | `hooks/useTheme`, `LogoPixelT` | layout |
| `OpeningAnimation` | `lib/openingTimeline`, hook | animasi |

**Catatan:** `services/analysis.ts` sudah memiliki `fetchWithTimeout` dan `ApiRequestError`; jangan mengganti dengan pemanggilan `fetch` langsung.

---

## 4. Dependency Eksternal

### 4.1 Backend Python

| Paket | Dipakai oleh | Kritis | Catatan |
|---|---|---|---|
| Flask | seluruh API | A | app factory |
| Flask-Cors | `app/__init__.py` | A | CORS `/api/*` |
| python-dotenv | `core/config.py` | A | env |
| supabase | `core/supabase.py`, repositories, auth | A | DB/Auth/Storage |
| torch | AI | A | U-Net/ResNet50 |
| torchvision | AI/model service | A | backbone |
| segmentation-models-pytorch | model service | A | `smp.Unet` |
| numpy | AI | A | array |
| scipy | postprocessing (jika dipakai) | A | operasi ilmiah |
| opencv-python-headless | preprocessing/domain/postprocessing | A | CV |
| Pillow | image validation/pipeline | A | PNG/JPEG |
| google-genai | `llm_image_validator.py` | A | Gemini gate, versi `>=3.0.0,<3.1.0` |
| pytest, pytest-mock | test | A | suite 190 |
| `uvicorn`/`fastapi`? | **tidak dipakai** | — | Jangan tambah tanpa kebutuhan |

### 4.2 Frontend

| Paket | Dipakai oleh | Kritis | Catatan |
|---|---|---|---|
| react, react-dom | seluruh UI | A | React 18 |
| react-router-dom | `AppRoutes` | A | routing/guard |
| `@supabase/supabase-js` | auth/session/profile | A | anon key saja |
| lucide-react | ikon UI | A | presentasional |
| `sharp` | aset/gambar (build/tooling) | B | jangan hapus tanpa cek script |
| vite, @vitejs/plugin-react | build | A | dev/build |
| typescript | typecheck | A | `tsc -b` |
| vitest, jsdom, @testing-library/react | test | A | 298 tes |
| tailwindcss, postcss, autoprefixer | styling | A | build CSS |

### 4.3 Root / tooling skripsi

| Paket | Dipakai oleh | Kategori | Catatan |
|---|---|---|---|
| `docx` | `generate_bab4.js` | F | generator dokumen |
| `canvas` | rasterisasi/render | F | tooling diagram |
| `@supabase/*` | script/tooling (jika ada) | F | bukan runtime utama |
| `sharp` (frontend) | aset | B | cek pemakaian sebelum hapus |

---

## 5. Dependency Test dan Build

| Perintah | Dependency | Bukti hasil |
|---|---|---|
| `python -m pytest tests/ -x --ignore=...` | pytest, pytest-mock, app, AI modules | 190 passed, 1 skipped |
| `npm test` | vitest, jsdom, testing-library | 298 passed, 19 file |
| `npm run build` | tsc, vite, tailwind/postcss | sukses, 12.20 s |
| `pip check` | seluruh paket Python | no broken requirements |

---

## 6. Ketergantungan yang Rapuh / Perlu Perhatian

| ID | Ketergantungan | Risiko | Bukti |
|---|---|---|---|
| D1 | `generate_bab4.js` → `path.join(__dirname, 'references', 'bab 4')` | Pindah folder memutus path | root script |
| D2 | `scripts/generate_section1_data.py` → `scripts.experiment_domain_gate` | Pindah subfolder memutus import | `scripts/generate_section1_data.py` |
| D3 | Skrip kalibrasi → `PROJECT_ROOT = Path(__file__).resolve().parents[1]` | Pindah ke subfolder mengubah root | `scripts/*` |
| D4 | `scripts/verify_c2_calib_match.py` → `scripts/output/b1_1_decision_differences.csv` | Path output relatif | scripts/output |
| D5 | `analysis_service.py` → 7 modul `ai/inference` | Nama/signature publik dilindungi | `analysis_service.py:20-25` |
| D6 | `Frontend/src/utils/analysis.ts` → env `VITE_API_BASE_URL` | Perubahan base URL memutus API | `analysis.ts` |
| D7 | Checkpoint path dari `MODEL_CHECKPOINT_PATH` | Path absolut/relatif; test hash | `model_config.py`, `core/config.py` |

**Tindakan:** jangan pindahkan D1–D4 tanpa penyesuaian path dan test; jangan ubah D5–D7 tanpa persetujuan.

---

## 7. Matriks “Aman Diubah vs Tidak”

| Area | Dapat diubah tanpa memutus dependency? | Syarat |
|---|---|---|
| Komponen internal `AnalysisService` | Ya, jika facade dan signature tetap | Regresi penuh |
| `core/auth.py` helper internal | Ya, jika perilaku/error code sama | Test auth |
| `admin_controller.py` envelope | Ya, jika frontend tidak bergantung bentuk lama | Test admin + UI |
| Halaman frontend besar | Ya, jika DOM/route/teks sama | Vitest + build |
| `docs/*.txt` | Tidak sebelum konfirmasi skripsi | Persetujuan |
| Root diagram tools | Tidak sebelum path `__dirname` diperbaiki | Uji render |
| `scripts/` subfolder | Tidak sebelum import/path diverifikasi | Uji skrip |
| `ai/**` | **Tidak** | Dilindungi |
| `database/migrations/**` | **Tidak** | Schema/RLS |
| `Backend/src/routes/**` | **Tidak** tanpa approval | API contract |

---

## 8. Kesimpulan

Dependency map menunjukkan PIXEL-T memiliki jalur yang jelas dan tidak ada import melingkar runtime. Titik paling rapuh adalah **path tooling skripsi** dan **service AI besar**, bukan struktur routing. Tidak ada dependency yang dihapus/ditambah pada audit ini.
