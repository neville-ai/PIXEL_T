# Rencana Penataan Struktur Kode dan Folder PIXEL-T Mengikuti Pola LUCIT (R0, R0b, & R1 Terkonsolidasi)

**Proyek:** PIXEL-T  
**Branch:** `refactor/struktur-lucit`  
**Status:** Tahap R0, R0b, dan R1 Selesai — **MENUNGGU PERSETUJUAN EKSPLISIT PENGGUNA SEBELUM LANGKAH 1**  
**Tanggal:** 10 November 2026  

---

## 0. BASELINE AKTUAL TERVERIFIKASI (SEBELUM LANGKAH REFACTOR)

Diukur langsung pada branch `refactor/struktur-lucit` pada 10 November 2026:

| Metrik Baseline | Hasil Aktual | Perintah / Bukti | Status |
|---|---|---|---|
| **pytest Suite** (Backend & AI) | **188 passed, 1 skipped** (0 failed) | `python -m pytest tests/ -x --ignore=tests/ai/audit_domain_validator_deep.py --ignore=tests/ai/measure_real_samples_stage2.py` (durasi: 113.67s) | ✅ Lulus 100% |
| **vitest Suite** (Frontend) | **298 passed** (0 failed) | `npx vitest run` (19 test files, durasi: 74.47s) | ✅ Lulus 100% |
| **Frontend Production Build** | **Berhasil** (`dist/` generated) | `npm run build` (`tsc -b && vite build`, durasi: 19.64s) | ✅ 0 error |
| **Model Checkpoint SHA-256** | `46521ae90d12f57f77a7b9921881910b41071dbbb1eff4d2172a2c437564c581` | File: `ai/models/PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth` (135.644.553 bytes) | ✅ Checksum Terkunci |
| **Git Working Branch** | `refactor/struktur-lucit` | `git branch --show-current` | ✅ Terisolasi dari main |

---

## R0. INVENTARISASI (READ-ONLY)

### 1. Pohon Folder 3 Tingkat
*(Mengabaikan `node_modules`, `venv`, `.venv`, `.git`, `__pycache__`, `dist/build`)*

```text
=== PIXEL-T ===
PIXEL-T/
├── ai/
│   ├── config/ (model_config.py, model_config.example.yaml)
│   ├── inference/ (pipeline.py, segmentation.py, gradcam.py, postprocessing.py, preprocessing.py, domain_validator.py, model_service.py)
│   └── models/ (PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth)
├── backend/
│   ├── app/ (controllers, core, models, repositories, routes, schemas, services, utils)
│   ├── requirements.txt
│   └── run.py
├── database/
│   ├── migrations/ (001 s/d 008)
│   └── seed/ (seed_doctor_profiles.sql)
├── frontend/
│   ├── src/ (assets, components, context, hooks, lib, pages, routes, services, types, utils)
│   ├── package.json, tsconfig.json, vite.config.ts
├── tests/ (ai, backend, frontend, conftest.py)
├── scripts/ (deployment, setup, output, skrip kalibrasi & evaluasi)
├── docs/ (audit, diagrams, spesifikasi)
├── diagram-skripsi/ & references/
└── (file root: README.md, .gitignore, .env.example, serta beberapa skrip diagram dan log)

=== LUCIT (Proyek Acuan) ===
LUCIT-master/
├── Backend/
│   ├── src/
│   │   ├── config/ (settings.py, supabase.py)
│   │   ├── controllers/ (chatbot_controller.py, prediction_controller.py, user_controller.py)
│   │   ├── models/ (model_loader.py, user_schema.py)
│   │   ├── repositories/ (analysis_repository.py, user_repository.py)
│   │   ├── routes/ (chatbot_routes.py, prediction_routes.py, user_routes.py)
│   │   └── services/ (ai_validator_service.py, chatbot_service.py, segmentation_service.py, etc.)
│   ├── inspect_table.py, requirements.txt, main.py
├── Frontend/
│   ├── public/
│   ├── src/
│   │   ├── assets/images/
│   │   ├── components/ (subfolder per komponen: Hero/index.tsx, Header/index.tsx, etc.)
│   │   ├── pages/ (analysis/index.tsx, history/index.tsx)
│   │   └── utils/ (api.ts, image.ts, session.ts, supabase.ts)
│   ├── .env.example, .env.production, index.html, package.json, vite.config.ts
└── README.md
```

---

## R0b. ANALISIS PERBANDINGAN: `ai_validator_service.py` (LUCIT) VS GERBANG VALIDASI PIXEL-T

Berdasarkan pembacaan kode riil pada `LUCIT-master/Backend/src/services/ai_validator_service.py` dan titik pemanggilannya di `LUCIT-master/Backend/src/controllers/prediction_controller.py:212`:

### 1. Cara Kerja dan Logika Arsitektur
| Aspek | LUCIT (`ai_validator_service.py`) | PIXEL-T (`domain_validator.py` + `llm_image_validator.py`) |
|---|---|---|
| **Peran & Tanggung Jawab** | **Multifungsi (Campuran):** Menggabungkan validasi input citra histopatologi (`validate_histopathology`), generasi deskripsi teks AI untuk klasifikasi (`generate_ai_description`), deskripsi teks segmentasi (`generate_ai_description_segmentation`), dan fallback lokal teks. | **Single Responsibility (Modular):** Terpisah tegas antara gerbang statistik warna/tekstur citra endoskopi (`ColonoscopyDomainValidator`) dan gerbang pemahaman semantik LLM (`validate_with_llm`). Tidak membuat deskripsi klinis buatan (sesuai batasan skripsi). |
| **Hierarki Alur Validasi** | **LLM Utama $\rightarrow$ Heuristik Fallback:** Memanggil Gemini terlebih dahulu melalui Vertex REST API. Jika Gemini gagal/error, baru jatuh ke fallback fungsi `_heuristic_histopathology_check` (warna HSV H&E stain ratio $\ge 0.16$). | **Heuristik Penyaring $\rightarrow$ LLM Final:** Heuristik lokal (nol biaya, ~30-50 ms) dijalankan terlebih dahulu. Jika REJECT, request langsung ditolak tanpa memanggil API LLM (hemat kuota & latensi). HANYA jika heuristik ACCEPT, citra divalidasi oleh Gemini. |
| **Titik Pemanggilan** | Langsung di Controller (`ImageController.predict_image` baris 212). Controller menangani pesan error `Not Histopathology Image`. | Di Service Layer (`AnalysisService.create_analysis` baris 420–496) dalam alur transaksi sebelum citra diunggah ke storage Supabase, dicatat di database, atau di-enqueue ke job queue. |
| **Keamanan & Fail-Closed** | Longgar: Jika LLM error, fungsi heuristik meloloskan jika stain ratio $\ge 0.16$. Format respons berupa teks generik tanpa status kode domain spesifik. | Ketat (*Fail-Closed*): Format kode error terstandarisasi (`NOT_COLONOSCOPY_IMAGE` status 400 dan `UNCERTAIN_COLONOSCOPY_IMAGE` status 400 jika LLM timeout/error). |

### 2. Temuan dan Usulan Penamaan / Penempatan
- Di LUCIT, penamaan `ai_validator_service.py` berada di dalam `Backend/src/services/`.
- Di PIXEL-T saat ini:
  - `ai/inference/domain_validator.py` (Domain Heuristic Validator)
  - `backend/app/services/llm_image_validator.py` (LLM Semantic Validator)
- **Usulan:** Penamaan dan penempatan modular di PIXEL-T saat ini **jauh lebih baik, bersih, dan sesuai standar Clean Architecture** dibandingkan LUCIT yang mencampurkan prompt generator teks ke dalam validator.
- **Sesuai instruksi pengguna:** Modul validasi ini **TIDAK AKAN DIPINDAHKAN** pada refactor ini untuk melindungi integritas naskah skripsi Bab IV dan pengujian suite.

---

## R1. RENCANA PEMETAAN & REVISI ATURAN REFACTOR

### 1. Aturan Khusus yang Ditetapkan (Wajib Dipatuhi)
1. **Perlindungan Naskah Skripsi (Daftar R0 butir 4):**
   Seluruh nama kelas, fungsi, dan berkas yang tercantum dalam naskah skripsi Bab IV & V **DILINDUNGI PENUH** dan tidak diubah (`AnalysisController`, `AnalysisService`, `AnalysisRepository`, `StorageService`, `AnalysisJobQueue`, `AnalysisProgressReporter`, `APIError`, `AIInferenceFunctions`, `ModelService`, `ModelConfig`, `PipelineResult`, `SegmentationResult`, `GradCAMResult`, `analyses`, `doctor_profiles`, `auth_users`, `AnalysisClient`, `AuthContext`, `DoctorProfileService`).
2. **Pengarsipan File:**
   - File ter-track di root yang tidak dipakai kode produksi dipindahkan dengan `git mv` ke folder `_archive/`.
   - **`_archive/` TIDAK dimasukkan ke dalam `.gitignore`** agar riwayat dan keberadaan file arsip tetap terlacak di git repository.
   - File log lokal (`backend_foreground.log`, `backend_foreground_err.log`) dan folder `.freebuff/` **HANYA ditambahkan ke `.gitignore`**, TIDAK dipindahkan ke `_archive/`.
3. **Pengecualian Eksplisit pada `.gitignore`:**
   File `.gitignore` di root wajib memuat secara eksplisit baris-baris berikut:
   ```gitignore
   calibration_data/
   references/
   scripts/output/
   *.log
   .freebuff/
   .env
   ```
4. **Verifikasi Pemuatan `.env` & `.env.example`:**
   - Frontend memuat file `.env` di direktori `frontend/.env` via bundler Vite (`VITE_*`).
   - Backend memuat `.env` via `load_dotenv()` di `backend/app/core/config.py`.
   - Pengujian keamanan `tests/frontend/test_frontend_env_safety.py` secara eksplisit memeriksa file `ROOT_DIR / ".env.example"`.
   - **Keputusan:** File `.env.example` di root **TIDAK BOLEH DIHAPUS**. Kita hanya menambahkan `backend/.env.example` dan `frontend/.env.example` sebagai template pendamping spesifik sub-proyek.
5. **Branching & Commit:**
   - Seluruh pekerjaan dilakukan di branch `refactor/struktur-lucit`.
   - **Satu commit per langkah** dengan pesan jelas.
   - Dilarang `git push` dan dilarang `git merge`.

---

### 2. Rencana Langkah Bertahap (Eksekusi R2)

#### Langkah 1: Pengarsipan File Skrip Diagram di Root ke `_archive/diagram_tools/`
- Pindahkan dengan `git mv`:
  - `generate_bab4.js` $\rightarrow$ `_archive/diagram_tools/generate_bab4.js`
  - `rasterize_erd.py` $\rightarrow$ `_archive/diagram_tools/rasterize_erd.py`
  - `rasterize_svg.py` $\rightarrow$ `_archive/diagram_tools/rasterize_svg.py`
  - `render_erd.mjs` $\rightarrow$ `_archive/diagram_tools/render_erd.mjs`
  - `test_render.mjs` $\rightarrow$ `_archive/diagram_tools/test_render.mjs`
  - `test_field.puml` $\rightarrow$ `_archive/diagram_tools/test_field.puml`
  - `test_field.svg` $\rightarrow$ `_archive/diagram_tools/test_field.svg`
- Verifikasi: Root bersih dari file skrip sementara, suite tes lulus, commit Langkah 1.

#### Langkah 2: Pembaruan `.gitignore` Eksplisit
- Tambahkan eksplisit ke `.gitignore`:
  `calibration_data/`, `references/`, `scripts/output/`, `*.log`, `.freebuff/`, `.env`.
- Pastikan `_archive/` **TIDAK** ada di `.gitignore`.
- Verifikasi: `git status` tidak lagi melacak file log dan `.freebuff/`, suite tes lulus, commit Langkah 2.

#### Langkah 3: Penyediaan Template Lingkungan Pendamping (`backend/.env.example` & `frontend/.env.example`)
- Buat `backend/.env.example` berisi variabel spesifik backend (Flask, Supabase Service Role, Model, Gemini).
- Buat `frontend/.env.example` berisi variabel spesifik frontend (`VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_URL`).
- Pertahankan file `.env.example` di root tanpa modifikasi yang merusak `test_frontend_env_safety.py`.
- Verifikasi: `test_frontend_env_safety.py` lulus, commit Langkah 3.

#### Langkah 4: Pembaruan `README.md` Mengadopsi Pola Panduan 2-Terminal LUCIT
- Rombak `README.md` dengan instruksi jelas dan ramah:
  - Prasyarat: Python 3.11, Node.js 18+, Git
  - **Terminal 1 (Backend):** `cd backend` $\rightarrow$ setup venv $\rightarrow$ `pip install -r requirements.txt` $\rightarrow$ `python run.py` (Port 5000).
  - **Terminal 2 (Frontend):** `cd frontend` $\rightarrow$ `npm install` $\rightarrow$ `npm run dev` (Port 5173).
  - Penjelasan arsitektur 3 pilar: Backend, Frontend, AI Module.
- Verifikasi: Panduan akurat terhadap kode aktual, commit Langkah 4.

#### Langkah 5: Verifikasi Penuh Seluruh Suite & Model Hash Check
- Jalankan ulang: pytest (harus $\ge 188$ passed, 1 skipped), vitest ($\ge 298$ passed), build frontend, cek hash SHA-256 model (`46521ae9...`), dan uji regresi. Commit Langkah 5 (finalisasi penataan).

---

### 3. Analisis Khusus: Langkah 6 (Opsional - Penataan `scripts/`)
Instruksi pengguna: *"Langkah 6 (opsional, laporkan dulu sebelum dikerjakan): rapikan scripts/ ke subfolder (calibration, evaluation, deployment, setup) dan buktikan semua skrip serta impor antar-skrip tetap berjalan."*

**Temuan Analisis Ketergantungan `scripts/`:**
1. **Impor Antar-Skrip:**
   `scripts/generate_section1_data.py:37` memiliki impor:
   `from scripts.experiment_domain_gate import evaluate_candidate_gate, safe_open_image`
   Jika `experiment_domain_gate.py` dipindahkan ke `scripts/calibration/`, maka impor ini akan patah (`ModuleNotFoundError`).
2. **Ketergantungan Path Relatif Root:**
   Semua skrip di `scripts/` menggunakan konstruksi:
   `PROJECT_ROOT = Path(__file__).resolve().parents[1]` (naik 1 tingkat ke root proyek).
   Jika skrip dipindahkan ke dalam subfolder (misal `scripts/calibration/foo.py`), maka `parents[1]` menjadi `scripts/` dan bukan root proyek, sehingga akses ke `calibration_data/`, `ai/`, dan `backend/` akan gagal.
3. **Ketergantungan Output:**
   File `scripts/verify_c2_calib_match.py` membaca `scripts/output/b1_1_decision_differences.csv`.
- **Rekomendasi:** Langkah 6 dilaporkan sebagai opsional dan **TIDAK DIJALANKAN terlebih dahulu** pada penataan utama agar tidak menimbulkan risiko regresi pada skrip-skrip kalibrasi. Kita fokus menyelesaikan Langkah 1 s/d 5 terlebih dahulu secara sempurna.

---

> [!IMPORTANT]
> **MENUNGGU PERSETUJUAN EKSPLISIT:**
> Laporan R0b dan revisi R1 di atas telah selesai dan siap dieksekusi.
> Sesuai instruksi, saya **BERHENTI DI SINI** dan menunggu **persetujuan eksplisit Anda** sebelum mengeksekusi Langkah 1.
