# TARGET ARCHITECTURE — PIXEL-T Refactoring Roadmap

**Tanggal:** 11 November 2026  
**Branch kerja:** `fitur/validasi-input` (HEAD `cbb5296`)  
**Sumber:** `docs/audit/refactor_lucit_plan.md` (R0–R5, diverifikasi 10 Nov 2026) + hasil audit Fase 1–3  
**Sifat:** rencana desain target — belum ada file produksi yang diubah pada fase ini. Semua perubahan fisik menunggu persetujuan eksplisit; tidak ada commit sebelum persetujuan.  
**Prinsip:** safety > functionality > correctness > maintainability > simplicity. Tidak merusak fitur yang berfungsi.

---

## 0. Ringkasan Eksekutif

PIXEL-T sudah menerapkan inti pola arsitektur LUCIT yang relevan (routes → controllers → services → repositories → core, config terpusat, Supabase client tunggal, error handler global, service AI terpisah). Arsitektur inti **tidak perlu restrukturisasi besar**. Refactoring target berfokus pada:

1. **Pembersihan berbasis bukti:** archive script diagram root, `.gitignore` eksplisit, `.env.example` per sub-proyek, README 2-terminal, verifikasi hash model.
2. **Penyelesaian perubahan Gemini** yang belum di-commit di branch `fitur/validasi-input` (config.py, llm_image_validator.py, test).
3. **Pembersihan opsional `scripts/`** (kalibrasi/evaluasi) — dilaporkan terlebih dahulu, tidak dijalankan sebelum disetujui.
4. **Pembersihan artefak build/log** yang gitignored.

Yang **TIDAK berubah**: API contract, database schema/RLS, Supabase auth/storage, arsitektur model (U-Net+ResNet50), checkpoint, threshold, preprocessing, TTA, postprocessing, target layer Grad-CAM, Domain Validation gate, LLM fail-closed gate, dan desain UI.

---

## 1. Keadaan Saat Ini (As-Is) — Ringkasan Bukti

| Area | Kondisi | Bukti |
|---|---|---|
| Backend | Flask app factory di `Backend/run.py` → `app.create_app()`; layering lengkap | `Backend/run.py:7-15`, `Backend/src/__init__.py:8-33` |
| Routes | 3 blueprint: health, analysis, admin (`/api`) | `Backend/src/routes/__init__.py:6-10` |
| Config | `core/config.py` terpusat dari `.env`; LLM timeout default 30.0 s | `Backend/src/core/config.py:1-76` |
| AI | `Backend/ai/inference/*`: U-Net+ResNet50, TTA 5×5, threshold 0.55, Grad-CAM layer `decoder.blocks.4.conv2.0`, checkpoint SHA-256 terverifikasi | `Backend/ai/config/model_config.py`, `Backend/ai/inference/*` |
| Domain/ LLM gate | Heuristik dulu, LLM (Gemini) fail-closed, tanpa bypass | `Backend/ai/inference/domain_validator.py`, `llm_image_validator.py` |
| Auth | Supabase Bearer token, role admin/dokter, account status pending/approved/rejected | `Backend/src/core/auth.py` |
| Frontend | React 18 + Vite 6, guard per role, `services/*.ts` terpusat | `Frontend/src/{AppRoutes.tsx,AuthContext.tsx,services/*.ts}` |
| Database | 8 migrasi SQL + verifikasi, Supabase Auth/Storage | `database/migrations/001-008.sql` |
| Tests | pytest 190 passed / 1 skipped; vitest 298 passed / 19 file | Fase 3 (dijalankan ulang) |
| Build | `tsc -b && vite build` sukses | Fase 3 |
| Root | Berisi skrip diagram, log runtime, build artifacts (gitignored) | `PROJECT_INVENTORY.md` |

### Kelemahan yang akan ditangani target arsitektur

| ID | Masalah | Lokasi | Dampak |
|---|---|---|---|
| A1 | Skrip diagram tooling di root (7 file) bercampur dengan berkas proyek | root: `generate_bab4.js`, `rasterize_erd.py`, `rasterize_svg.py`, `render_erd.mjs`, `test_render.mjs`, `test_field.puml`, `test_field.svg` | Root terlihat kacau; tidak ada dampak runtime |
| A2 | `.gitignore` tidak mencakup secara eksplisit `calibration_data/`, `references/`, `scripts/output/`, `*.log`, `.freebuff/`, `.env` | `.gitignore` | File log/artefak bisa terlacak secara tidak sengaja |
| A3 | Tidak ada `Backend/.env.example` dan `Frontend/.env.example`; hanya root `.env.example` | root `.env.example` | Template spesifik sub-proyek tidak tersedia |
| A4 | `README.md` belum memberikan instruksi 2-terminal yang jelas (backend port 5000, frontend port 5173) | `README.md` | Developer onboarding kurang terstruktur |
| A5 | Folder `.gitkeep`-only (10 direktori) + `types/` dan `utils/` kosong di frontend | `Backend/src/{models,schemas,utils}`, `Frontend/src/{types,utils}`, dll. | Konsistensi struktur |
| A6 | Artefak build dan log di working tree (gitignored, regenerable) | `Frontend/dist`, `Frontend/tsconfig.tsbuildinfo`, `backend_foreground*.log` | Noise di working tree |

---

## 2. Keadaan Target (To-Be)

Arsitektur target **pertahankan setiap layer, endpoint, fungsi, dan nama kelas yang tercantum dalam naskah skripsi** (lihat daftar terlindungi di bagian 3). Target hanya menambahkan struktur pendukung dan membersihkan noise.

```text
WEB_PIXELT/
├── .env.example              # root template (pertahankan, tidak diubah secara merusak)
├── .gitignore                # ditambahkan: calibration_data/, references/, scripts/output/, *.log, .freebuff/, .env
├── README.md                 # ditambahkan: instruksi 2-terminal (backend port 5000, frontend port 5173)
├── _archive/                 # BARU — hasil `git mv` dari skrip diagram root
│   └── diagram_tools/
│       ├── generate_bab4.js
│       ├── rasterize_erd.py
│       ├── rasterize_svg.py
│       ├── render_erd.mjs
│       ├── test_render.mjs
│       ├── test_field.puml
│       └── test_field.svg
├── Backend/
│   ├── .env.example          # BARU — template spesifik backend
│   ├── .env                  # di-gitignore (tidak di-commit)
│   ├── run.py                # tidak berubah
│   ├── app/                  # tidak berubah struktur layering
│   └── requirements.txt      # ditambahkan: google-genai>=3.0.0,<3.1.0 (kompatibilitas reproducibility)
├── Frontend/
│   ├── .env.example          # BARU — template spesifik frontend (VITE_*)
│   ├── .env                  # di-gitignore (tidak di-commit)
│   ├── dist/                 # build artifact (gitignored, regenerable)
│   └── src/                  # tidak berubah; folder types/ & utils/ sudah dihapus via cleanup (.gitkeep-only)
├── database/                 # tidak berubah (migrasi + verifikasi)
├── ai/                       # tidak berubah (model, config, inference — dilindungi)
├── tests/                    # tidak berubah (suite penuh dipertahankan)
├── scripts/                  # pertahankan saat ini; re-rapihkan opsional (Langkah 6)
├── docs/, diagram-skripsi/, research/  # pertahankan (artefak skripsi)
└── calibration_data/, references/  # di-gitignore, tidak diubah
```

### Perubahan spesifik per komponen

| Komponen | Perubahan Target | Justifikasi |
|---|---|---|
| Root skrip diagram | Dipindahkan (`git mv`) ke `_archive/diagram_tools/` | **DITUNDA** (audit: Langkah 4 skrip diagram; ditunda karena path `generate_bab4.js` bergantung `__dirname`) |
| `.gitignore` | Tambahkan baris eksplisit: `calibration_data/`, `references/`, `scripts/output/`, `*.log`, `.freebuff/`, `.env` | Mencegah file log/data terlacak secara tidak sengaja; `_archive/` **tidak** di-ignore |
| `Backend/.env.example` | Baru, berisi variabel Flask, Supabase, model, Gemini | Template pendamping spesifik sub-proyek |
| `Frontend/.env.example` | Baru, berisi `VITE_*` | Template pendamping spesifik sub-proyek |
| `README.md` | Tambah instruksi 2-terminal (Backend: venv → `pip install` → `python run.py` port 5000; Frontend: `npm install` → `npm run dev` port 5173) | Panduan developer akurat terhadap kode aktual |
| `Backend/requirements.txt` | Tambah `google-genai>=3.0.0,<3.1.0` | Paket diimpor `llm_image_validator.py:116,181` tapi belum tercantum pada saat perubahan; reproducibility (sudah ada di working tree) |
| `Backend/src/core/config.py` + `llm_image_validator.py` + tes | Terapkan perubahan Gemini yang belum di-commit (response_mime_type JSON, response_schema, thinking_config low, max_output_tokens 1024, timeout 30.0 s, retry attempts=1) | Sudah ada di working tree branch `fitur/validasi-input`; diformalisasikan |
| `scripts/` | Pertahankan; re-rapihkan ke subfolder **opsional**, hanya setelah bukti impor antar-skrip tetap berjalan | Risiko regresi tinggi pada skrip kalibrasi/evaluasi |

---

## 3. File, Fitur, dan Arsitektur yang DILINDUNGI (Tidak Diubah)

Daftar berikut **tidak boleh diubah, dipindahkan, atau dihapus** dalam refactoring ini, karena tercantum dalam naskah skripsi Bab IV & V atau merupakan inti keamanan/ML:

1. **Nama kelas & fungsi backend:** `AnalysisController`, `AnalysisService`, `AnalysisRepository`, `StorageService`, `AnalysisJobQueue`, `AnalysisProgressReporter`, `APIError`, `AIInferenceFunctions`, `ModelService`, `ModelConfig`, `PipelineResult`, `SegmentationResult`, `GradCAMResult`.
2. **Database & tabel:** `analyses`, `doctor_profiles`, `auth_users`; seluruh `database/migrations/*.sql` dan `verify_doctor_registration.sql`.
3. **AI/ML:** `Backend/ai/models/PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth` (+ SHA-256 `46521AE90D12F57F77A7B9921881910B41071DBBB1EFF4D2172A2C437564C581`), `Backend/ai/config/model_config.py`, seluruh `Backend/ai/inference/*` (preprocessing, segmentation, postprocessing, gradcam, domain_validator, pipeline, model_service).
4. **AI gate & threshold:** threshold 0.55, input 512×512, normalisasi ImageNet, TTA 5 skala × 5 orientasi, Grad-CAM target layer `decoder.blocks.4.conv2.0`, domain validation gate heuristik→LLM fail-closed.
5. **Auth & keamanan:** `Backend/src/core/auth.py`, `Backend/src/core/supabase.py`, `.env` (backend & frontend, tidak di-commit), `.env.example` root.
6. **API contract:** `Backend/src/routes/*`, `Backend/src/controllers/*`, `Frontend/src/utils/*` (path, method, respons, nama field FormData).
7. **Entry point & build:** `Backend/run.py`, `Frontend/src/main.tsx`, `Frontend/src/App.tsx`, `Frontend/src/routes/AppRoutes.tsx`, `Frontend/vite.config.ts`, `Frontend/tsconfig.json`, `Frontend/tailwind.config.js`, `Frontend/postcss.config.js`, `Frontend/index.html`.
8. **Tests:** seluruh `tests/**` dan `Frontend/src/**/*.test.*`.
9. **Artefak penelitian:** `research/*`, `scripts/output/*`, `calibration_data/*`, `references/*`, `LUCIT-master/`.
10. **Dokumentasi skripsi:** `docs/PRD_PIXEL-T_FINAL.md`, `docs/StyleGuide.md`, `docs/FunctionalSpecification.md`, `docs/APIContract.md`, `docs/DataModelSpecification.md`, `docs/ModelIntegrationSpecification.md`, `diagram-skripsi/*`.

---

## 4. Rencana Langkah Bertahap (Eksekusi)

Dikasihkan dari `docs/audit/refactor_lucit_plan.md` R1, disesuaikan dengan branch `fitur/validasi-input`. Setiap langkah **dikelompokkan perubahan kecil**, didahului baseline, dan dapat di-rollback melalui git. **Tidak ada commit sebelum persetujuan eksplisit pengguna.**

### Langkah 1: Pengarsipan Skrip Diagram Root → `_archive/diagram_tools/`

- `git mv` 7 file: `generate_bab4.js`, `rasterize_erd.py`, `rasterize_svg.py`, `render_erd.mjs`, `test_render.mjs`, `test_field.puml`, `test_field.svg`.
- Verifikasi: root bersih dari skrip diagram; `git status` menunjukkan `_archive/` terlacak; suite tes lulus.

### Langkah 2: Pembaruan `.gitignore` Eksplisit

- Tambahkan baris: `calibration_data/`, `references/`, `scripts/output/`, `*.log`, `.freebuff/`, `.env`.
- Pastikan `_archive/` **tidak** masuk `.gitignore`.
- Verifikasi: `git status` tidak melacak log dan `.freebuff/`; suite tes lulus.

### Langkah 3: Template Lingkungan Pendamping

- Buat `Backend/.env.example`: variabel Flask (APP_ENV, SECRET_KEY, host, port, CORS), Supabase URL/anon/service role/bucket, model path/device/inference, Gemini model/timeout/conf.
- Buat `Frontend/.env.example`: `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_URL`.
- Pertahankan root `.env.example` tanpa merusak `tests/Frontend/test_frontend_env_safety.py`.
- Verifikasi: `test_frontend_env_safety.py` lulus.

### Langkah 4: Pembaruan `README.md` (Panduan 2-Terminal)

- Prasyarat: Python 3.11, Node.js 18+, Git.
- Terminal 1 (Backend): `cd backend` → venv → `pip install -r requirements.txt` → `python run.py` (Port 5000).
- Terminal 2 (Frontend): `cd frontend` → `npm install` → `npm run dev` (Port 5173).
- Penjelasan arsitektur 3 pilar: Backend, Frontend, AI Module.
- Verifikasi: panduan akurat terhadap kode aktual.

### Langkah 5: Verifikasi Penuh & Finalisasi Penataan

- Jalankan ulang seluruh suite: pytest (≥190 passed, 1 skipped), vitest (≥298 passed), build frontend, cek hash SHA-256 model checkpoint.
- Uji regresi alur upload → domain gate → storage → polling → hasil.
- Langkah ini finalisasi penataan struktur (tidak merubah perilaku).

### Langkah 6 (Opsional): Penataan `scripts/`

- Rapihkan `scripts/` ke subfolder (calibration, evaluation, deployment, setup).
- **Wajib buktikan:** semua skrip dan impor antar-skrip tetap berjalan (`scripts/generate_section1_data.py:37` mengimpor `scripts.experiment_domain_gate`; path relatif root `parents[1]`).
- **Tidak dijalankan** sebelum Langkah 1–5 selesai dan disetujui.

---

## 5. Strategi Rollback & Keamanan

- Semua perubahan dilakukan di working tree branch `fitur/validasi-input`; rollback melalui `git checkout -- <file>` atau `git restore`.
- `_archive/` dibuat via `git mv` (dapat dikembalikan via `git mv` sebaliknya).
- Setiap langkah dipisah dan diverifikasi dengan suite tes sebelum langkah berikutnya.
- Tidak ada `git push`, tidak ada `git merge`, tidak ada `git reset/clean/force push`.
- Commit hanya dilakukan setelah persetujuan eksplisit pengguna.

---

## 6. Kriteria Sukses Target Arsitektur

| Kriteria | Target | Verifikasi |
|---|---|---|
| pytest | ≥190 passed, 1 skipped, 0 failed | `python -m pytest tests/ ...` |
| vitest | ≥298 passed, 0 failed | `npm test` |
| Build frontend | 0 error | `npm run build` |
| Hash model checkpoint | cocok SHA-256 terverifikasi | `Backend/ai/config/model_config.py` |
| API contract | tidak ada perubahan path/method/respons | bandingkan `routes/*` vs `services/*.ts` |
| Fitur AI/ML | identik (threshold, TTA, Grad-CAM, checkpoint) | tes AI tetap lulus |
| Root bersih | tidak ada skrip diagram di root | `ls root` |
| `.gitignore` | mencakup baris eksplisit target | `.gitignore` |
| `.env.example` | backend + frontend tersedia | file ada di masing-masing sub-folder |

---

## 7. Catatan

- Baseline aktual (Fase 3) lebih baik dari angka di `docs/audit/refactor_lucit_plan.md` (188 → 190 pytest; vitest tetap 298) karena tes Gemini baru. Angka aktual menjadi acuan.
- Perubahan Gemini belum di-commit di branch `fitur/validasi-input` **dipastikan ikut teruji dalam baseline** dan diformalisasikan dalam target ini.
- Tidak ada fitur yang dihapus dalam target arsitektur ini; semua kandidat pembersihan (folder kosong, artefak, kode potensi tidak terpakai) ditangani melalui bukti referensi pada fase cleanup berikutnya.
