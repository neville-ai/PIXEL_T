# PIXEL-T AUDIT REPORT

**Tanggal:** 11 November 2026  
**Branch aktif:** `fitur/validasi-input`  
**HEAD:** `cbb5296`  
**Status saat audit awal:** 3 file termodifikasi belum di-commit (`Backend/src/core/config.py`, `Backend/src/services/llm_image_validator.py`, `tests/Backend/test_llm_image_validator.py`); **status terkini (11 Nov 2026):** 18 file modified/deleted (hasil cleanup tahap 5–6) + 24 file untracked (13 laporan audit wajib baru + 9 laporan audit lama dari fase sebelumnya + `Backend/.env.example`, `Frontend/.env.example`), staging kosong — lihat `FINAL_PROJECT_AUDIT.md` §3.  
**Sumber bukti:** baca langsung file, grep terverifikasi, `PROJECT_INVENTORY.md`, `LUCIT_ARCHITECTURE_ANALYSIS.md`  
**Sifat:** read-only. Tidak ada file PIXEL-T yang diubah pada fase ini.  
**Prinsip:** SAFETY > FUNCTIONALITY > CORRECTNESS > MAINTAINABILITY > SIMPLICITY

---

## 0. Ringkasan Eksekutif

PIXEL-T adalah aplikasi web analisis citra kolonoskopi dengan pipeline: **upload → Domain Validation (heuristik + LLM/Gemini gate, fail-closed) → penyimpanan original ke Supabase Storage → rekaman DB 'processing' → worker background (U-Net+ResNet50, TTA, postprocessing, Grad-CAM) → status 'completed' → polling frontend → hasil (binary mask, overlay, Grad-CAM, ringkasan)**. Autentikasi via Supabase Bearer token; role admin/dokter dengan status pending/approved/rejected; ownership pada storage & DB.

Audit menemukan bahwa **struktur PIXEL-T sudah setara dengan (dan di beberapa aspek lebih baik dari) LUCIT-master** — layering routes→controllers→services→repositories, config terpusat, client Supabase terpusat, error handler global, serta test suite yang ada. Tidak ada fitur yang terlihat tidak berfungsi secara struktural.

Temuan utama untuk perhatian (tidak diubah pada fase ini, hanya didokumentasikan):

| # | Temuan | Lokasi | Risiko | Tindakan |
|---|--------|--------|--------|----------|
| F1 | `analysis_service.py` sangat besar (1147 baris total saat ini; 1029 baris non-kosong; 1145 pada HEAD `cbb5296`) - orchestrasi validation, domain gate, LLM gate, storage, DB, queue, worker, pipeline, progress | `Backend/src/services/analysis_service.py` | Pemeliharaan; risiko regresi tinggi jika diubah tanpa cakupan test | Kandidat pemecahan bertahap Fase 5-6, hanya jika aman |
| F2 | `fetch` di `analysis.ts` tidak menetapkan timeout (temuan awal) | `Frontend/src/utils/analysis.ts`, `Backend/src/core/config.py` | Polling/request bisa macet lama tanpa feedback | **SELESAI (cleanup):** `fetchWithTimeout` + `ApiRequestError('REQUEST_TIMEOUT')`, timeout default 30 s, upload 90 s; tidak mengubah perilaku inference |
| F3 | Fallback timeout LLM hardcoded `15.0` detik (temuan awal) vs `Config.LLM_VALIDATION_TIMEOUT_S` default `30.0` | `Backend/src/services/analysis_service.py`, `Backend/src/core/config.py:38` | Inkonstensi kecil | **SELESAI (cleanup):** fallback diselaraskan ke `30.0` |
| F4 | Folder kosong berisi `.gitkeep` (10 direktori) — bukan bug, hanya konsistensi struktur (temuan awal) | `Backend/src/{models,schemas,utils}`, `database/seed`, `Frontend/src/components/{analysis,history}`, `Frontend/src/{types,utils}`, `scripts/{deployment,setup}` | Rendah | **SELESAI (cleanup):** 10 file `.gitkeep`-only dihapus; 22 file tersisa yang masih perlu dipetakan (kandidat pending) |
| F5 | Artefak build & log ada di working tree (gitignored) | `Frontend/dist`, `Frontend/tsconfig.tsbuildinfo`, `backend_foreground*.log` | Rendah | **SELESAI (cleanup):** dibersihkan, kemudian dibuat ulang oleh build baseline (`npm run build` exit 0); artefak bersifat regenerable |
| F6 | `google-genai` terimpor tetapi belum tercatat di `Backend/requirements.txt` (temuan awal) | `llm_image_validator.py` vs `Backend/requirements.txt` | Reproducibility | **SELESAI (cleanup):** ditambahkan `google-genai>=3.0.0,<3.1.0`; `pip check` lulus |
| F7 | `getCurrentUser` diekspor di `auth.ts` tetapi tidak terpakai (temuan awal) | `Frontend/src/utils/auth.ts` (sebelum cleanup) | Rendah | **SELESAI (cleanup):** dihapus setelah grep menyeluruh tidak menemukan pemanggil |
| F8 | `NewAnalysis.tsx` polling tidak mencantumkan batas maksimum eksplisit terlihat (berbeda `AnalysisResult.tsx` MAX_POLL_ATTEMPTS=12) | `Frontend/src/pages/analysis/NewAnalysis.tsx:167` | Polling bisa berjalan lama jika backend macet | Periksa batas polling; dokumentasi |
| F9 | Dokumentasi `.md` memiliki pasangan `.txt` duplikat (APIContract, StyleGuide, DataModelSpecification, AdminDashboardAndApproveForensicReport) | `docs/*.md` vs `docs/*.txt` | Artefak skripsi; pertahankan sampai konfirmasi | Jangan hapus |

---

## A. Audit Frontend

### A.1 Struktur `src/`

`Frontend/src/` berisi 87 file terlacak (tanpa `.gitkeep`, build cache, dan `dist/`). Kategori:

| Kategori | File/Folder | Catatan |
|---|---|---|
| Entry | `main.tsx`, `App.tsx`, `AppRoutes.tsx` | Factory React + router + guard |
| Konteks | `context/AuthContext.tsx` | Sesi Supabase, role, account status |
| Services | `services/{analysis,auth,profile}.ts` | Klien API terpusat |
| Lib | `lib/{supabase,format,openingTimeline}.ts` | Utilitas |
| Hooks | `hooks/{useOpeningAnimation,useTheme}.ts` | State |
| UI | `components/ui/{Badge,Button,Card,EmptyState,ErrorState,Input,LoadingState,Modal,ThemeToggle}.tsx` | Komponen presentasi dapat dipakai ulang |
| Auth guard | `components/auth/{Protected,Admin,Doctor,PublicOnly}Route.tsx`, `AuthLoadingState`, `OpeningAnimation` | Guard per role |
| Layout | `components/layout/AppShell.tsx` | Header/footer global (tidak pada `/login`) |
| Brand | `components/brand/LogoPixelT.tsx` | Logo PIXEL-T |
| Pages | `pages/{auth/{Login,Register,ResetPassword}, dashboard/Dashboard, analysis/{NewAnalysis,AnalysisResult}, history/{History,HistoryDetail}, profile/DoctorProfile, admin/AdminDashboard, NotFound}` | 11 halaman |
| Aset | `assets/{pixel-t-logo.jpg, pixel-t-logo-light.png, pixel-t-logo-transparent.png, icon-doctor.png}` | Logo & ikon |

Folder yang hanya berisi `.gitkeep` (kosong): `components/analysis`, `components/history`, `components/layout` (hanya AppShell), `components/ui` (diisi), `hooks`, `pages/analysis` (diisi), `pages/auth` (diisi), `pages/dashboard` (diisi), `pages/history` (diisi), `pages/profile` (diisi), `pages/admin` (diisi), `routes`, `services`, `types`, `utils`.  
`types` dan `utils` kosong → kandidat konsolidasi atau hapus jika tidak akan diisi (Fase 6).

### A.2 Routing

**Bukti:** `Frontend/src/routes/AppRoutes.tsx:19-113`.

- `/` → redirect `/login`
- `/login`, `/register`, `/reset-password` → `PublicOnlyRoute`
- `/dashboard`, `/analysis/new`, `/analysis/:id`, `/history`, `/history/:id` → `ProtectedRoute`
- `/profile` → `DoctorRoute` (tolak admin)
- `/admin` → `AdminRoute`
- `*` → `NotFound`

Guard cocok dengan backend `require_approved_doctor` dan `require_admin`. Konsisten.

### A.3 Services/API

**Bukti:** `Frontend/src/utils/analysis.ts:1-225`.

- `API_BASE_URL` dari `VITE_API_BASE_URL` atau fallback `http://localhost:5000/api` (`:3-5`).
- `authenticatedRequest` mengambil sesi Supabase, mengirim `Authorization: Bearer <token>`, mencoba refresh sekali pada 401, lalu throw (`:95-174`).
- `ApiRequestError` bawa `code` kontrak backend (`QUEUE_FULL`, `NOT_COLONOSCOPY_IMAGE`, dsb.).
- `createAnalysis` → `POST /api/analysis`, body `FormData` field `image` (`:186-193`). **Perhatian:** backend `create_analysis` (`analysis_service.py:417`) membaca `file_storage` dari `request.files` — nama field di Flask otomatis cocok dengan `formData.append('image', file)`.
- `getAnalysis` → `GET /api/analysis/{id}`.
- `listHistory` → `GET /api/history`.
- `deleteAnalysis` → `DELETE /api/history/{id}`, `expectData: false`.
- **Tidak ada `timeout` pada `fetch`**; hanya timeout LLM di backend SDK (30 detik) dan retry `attempts=1`.

### A.4 Auth & Protected Route

**Bukti:** `context/AuthContext.tsx`, `components/auth/ProtectedRoute.tsx`, `DoctorRoute.tsx`, `AdminRoute.tsx`.

- Supabase-based; `getCurrentSession`, `onAuthStateChange`; role dari `app_metadata.role` (admin, server-write-only) lalu `doctor_profiles` (dokter).
- `ProtectedRoute` blokir `pending`/`rejected`; `DoctorRoute` blokir admin; `AdminRoute` hanya `role === 'admin'`.
- Konsisten dengan `Backend/src/core/auth.py:176-275` (`require_approved_doctor`) dan `:87-173` (`require_admin`).

### A.5 Polling & Loading

**Bukti:** `Frontend/src/pages/analysis/NewAnalysis.tsx:160-215`, `AnalysisResult.tsx:80-106`.

- `NewAnalysis.tsx`: polling `getAnalysis` setelah `POST /api/analysis` mengembalikan `202 processing`; `pollCount` dicatat; henti pada status terminal (`completed`/`failed`) atau 401 → minta login ulang. Error jaringan sementara tetap polling.
- `AnalysisResult.tsx`: `MAX_POLL_ATTEMPTS = 12` (`:10`), henti setelah kuota tercapai (`:105-106`).
- `NewAnalysis.tsx` **tidak mencantumkan batas maksimum eksplisit terlihat** (bukan `MAX_POLL_ATTEMPTS`) → polling bisa berjalan terus selama status `processing`. Risiko sedang jika backend macet.
- Tidak ada `AbortController`/timeout pada fetch polling (lihat F2).

### A.6 Duplikasi & Kode Tidak Terpakai (frontend)

| Item | Bukti | Penilaian |
|---|---|---|
| `getCurrentUser` diekspor | `auth.ts:284` (sebelum cleanup) | **Dihapus** setelah grep menyeluruh tidak menemukan pemanggil |
| `format.ts` | `lib/format.ts:34-81` (format tanggal, display name, initials) | Digunakan halaman history/profile; terpakai |
| `ThemeToggle`, `useTheme` | `components/ui/ThemeToggle.tsx`, `hooks/useTheme.ts` | Digunakan `App.tsx` + `ThemeToggle` di AppShell; terpakai |
| `OpeningAnimation` | 218 baris; digunakan App.tsx | Terpakai (opening sequence) |
| `formatPredictionLabel` (LUCIT) | Hanya di LUCIT, tidak di PIXEL-T | PIXEL-T pakai `detection_category` dari backend; tidak duplikat |

### A.7 Temuan Frontend

1. Struktur sudah terorganisir per fitur; guard per role jelas.
2. Tidak ada `.env` di repo (gitignored); `VITE_API_BASE_URL` fallback `localhost:5000`.
3. Risiko utama (sisa): `NewAnalysis` tanpa batas polling eksplisit → polling bisa berjalan lama tanpa feedback pengguna; `fetch` sudah diberi timeout pada cleanup.
4. Folder `types/` dan `utils/` (dulu hanya `.gitkeep`) sudah dihapus pada cleanup.
5. `getCurrentUser` dihapus pada cleanup.

---

## B. Audit Backend

### B.1 Struktur & Entry Point

- `Backend/run.py` → `app.create_app()` → Flask application factory (`Backend/src/__init__.py:8-33`).
- Factory: load config, CORS (`/api/*`), error handlers, register blueprints. Tidak ada inisialisasi DB/AI saat factory (di-lazy di service).
- Blueprint di `routes/__init__.py:6-10` dengan prefix `/api`.

### B.2 Endpoint API

| Method | Path | Guard | Controller | Sumber |
|---|---|---|---|---|
| GET | `/api/health` | publik | — | `routes/health.py:6-14` |
| POST | `/api/analysis` | `require_approved_doctor` | `AnalysisController.create_analysis` | `routes/analysis.py:11-26` |
| GET | `/api/analysis/<id>` | `require_approved_doctor` | `AnalysisController.get_analysis` | `routes/analysis.py:29-42` |
| GET | `/api/history` | `require_approved_doctor` | `AnalysisController.list_history` | `routes/analysis.py:45-53` |
| DELETE | `/api/history/<id>` | `require_approved_doctor` | `AnalysisController.delete_analysis` | `routes/analysis.py:56-64` |
| GET | `/api/admin/doctors` | `require_admin` | `AdminController.list_doctors` | `routes/admin.py:9-13` |
| GET | `/api/admin/doctors/stats` | `require_admin` | `AdminController.get_statistics` | `routes/admin.py:16-20` |
| GET | `/api/admin/doctors/<id>` | `require_admin` | `AdminController.get_doctor` | `routes/admin.py:23-27` |
| POST | `/api/admin/doctors/<id>/approve` | `require_admin` | `AdminController.approve_doctor` | `routes/admin.py:30-34` |
| POST | `/api/admin/doctors/<id>/reject` | `require_admin` | `AdminController.reject_doctor` | `routes/admin.py:37-45` |

Kontrak konsisten dengan `Frontend/src/utils/analysis.ts` (path, method, `expectData` untuk DELETE).

### B.3 Auth & Keamanan

**Bukti:** `Backend/src/core/auth.py`, `core/supabase.py`, `core/errors.py`.

- `require_auth`, `require_admin`, `require_approved_doctor`: verifikasi Bearer token via `supabase.auth.get_user(token)`; admin lewat `app_metadata.role` (server-write-only, tidak bisa diubah user via client); dokter lewat `doctor_profiles` (`role`, `account_status`).
- Ownership: `AnalysisRepository.get_by_id(analysis_id, user_id, ...)` memfilter `user_id`; `StorageService.validate_path_ownership` memastikan path milik user.
- Service role key hanya untuk operasi server (storage upload/signed URL, DB admin).
- Error envelope standar: `{"success": false, "error": {"code", "message"}}`; HTTPException tidak bocor detail teknis.
- Tidak ada secret hardcode di source; `.env` gitignored.

### B.4 AnalysisService (god service, 1147 baris total; 1029 baris non-kosong)

Tanggung jawab (terverifikasi baris):

| Fungsi | Baris | Tanggung jawab |
|---|---|---|
| `validate_and_decode_image` | 332 | validasi filename, ukuran ≤10 MB, MIME, integritas Pillow, dimensi |
| `create_analysis` | 400 | validasi → domain gate → LLM gate → upload original → DB 'processing' → enqueue job |
| `get_analysis` | 607 | detail + signed URL + progres + model info + gradcam + summary |
| `list_user_analyses` | 760 | riwayat + thumbnail signed URL |
| `delete_analysis` | 813 | hapus DB dulu, storage best-effort (DECISION A) |
| `_run_analysis_job` | 886 | worker background; swallow error setelah status 'failed' |
| `_execute_pipeline` | 906 | jalankan `run_pipeline`, upload 4 artefak, update DB 'completed' |
| `run_segmentation` / `run_gradcam` | 1118/1132 | boundary model yang dipanggil di luar jalur upload, dengan gate domain |

- Kompensasi gagal pada setiap langkah (hapus file/record yang sebagian dibuat).
- Queue penuh → `QUEUE_FULL` 429 dengan cleanup record + file.
- Progres: `AnalysisProgressReporter` (unit = fase + forward pass TTA), throttle 5 forward pass, tidak pernah menfabrikasi 100%.
- STALE_THRESHOLD 15 menit, non-mutating.

### B.5 Domain Validation (heuristik + LLM)

**Bukti:** `Backend/ai/inference/domain_validator.py`, `Backend/src/services/llm_image_validator.py`, `analysis_service.py:427-496`.

- Heuristik (`ColonoscopyDomainValidator.validate_bytes`): REJECT/UNCERTAIN → tidak ada file/record/job.
- LLM (Gemini): `response_mime_type="application/json"`, `response_schema`, `thinking_config` low, `max_output_tokens=1024`, timeout 30 s, retry `attempts=1`, fail-closed (ERROR → UNCERTAIN_COLONOSCOPY_IMAGE).
- Urutan: heuristik dulu; jika ACCEPT → LLM. LLM REJECT → NOT_COLONOSCOPY_IMAGE; ERROR → UNCERTAIN_COLONOSCOPY_IMAGE.
- Prinsip: LLM **tidak boleh meloloskan** citra yang sudah ditolak heuristik.

### B.6 Storage

**Bukti:** `Backend/src/services/storage_service.py`.

- Path: `analysis/{user_id}/{analysis_id}/{category}/{filename}`; kategori `original`, `segmentation`, `gradcam`.
- `sanitize_id` mencegah path traversal; `validate_path_ownership` memastikan kepemilikan.
- Upload/download/signed URL/delete dengan opsi service role.

### B.7 Config

**Bukti:** `Backend/src/core/config.py:1-76`.

- `APP_ENV`, `SECRET_KEY`, host/port, `MAX_CONTENT_LENGTH` 10 MB, CORS origins, Supabase URL/anon/service role/bucket.
- Model: checkpoint path, device, inference enabled, domain validation enabled.
- LLM: model, min conf 0.80, timeout **30.0 s** (default).
- Env classes: Development/Testing/Production.

**Catatan:** `google-genai` kini tercantum di `requirements.txt` sebagai `google-genai>=3.0.0,<3.1.0` (ditambahkan cleanup); diimpor oleh `llm_image_validator.py`.

---

## C. Audit AI & Machine Learning

### C.1 Struktur `ai/`

| File | Fungsi |
|---|---|
| `config/model_config.py` | `ModelConfig` frozen dataclass: U-Net + ResNet50 (smp), input 512, threshold 0.55, TTA scales (0.85, 0.95, 1.0, 1.05, 1.15), postprocessing, Grad-CAM layer `decoder.blocks.4.conv2.0`, checkpoint SHA-256 terverifikasi |
| `inference/model_service.py` | `ModelService`: lazy load SMP `smp.Unet`, `torch.load(weights_only=True)`, strict state dict, device auto CPU/CUDA |
| `inference/preprocessing.py` | `prepare_image`: resize 512×512 bilinear, normalize ImageNet mean/std |
| `inference/segmentation.py` | `predict`: TTA 5 skala × 5 orientasi, sigmoid, threshold 0.55; `count_forward_passes` |
| `inference/postprocessing.py` | `postprocess_mask`: close/open, area filter ≥25 px, fill holes, smoothing; `measure_mask`: metrik + kategori POLYP_DETECTED/NO_POLYP_DETECTED/LOW_CONFIDENCE |
| `inference/gradcam.py` | `generate_gradcam`: hook target layer, objective mean logit over mask, all-zero heatmap saat mask kosong, colormap jet deterministik |
| `inference/domain_validator.py` | `ColonoscopyDomainValidator`: heuristik warna/tekstur citra kolonoskopi |
| `inference/pipeline.py` | `run_pipeline`: domain gate ACCEPT wajib → preprocessing → inferensi → postprocessing → Grad-CAM → komposisi artefak |

### C.2 Garansi yang dipertahankan (JANGAN diubah)

- Arsitektur U-Net + ResNet50 (`smp.Unet`, encoder_weights=None).
- Checkpoint `PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth` + SHA-256 verifikasi (`checkpoint_sha256_matches`).
- Threshold 0.55; input 512×512; normalisasi ImageNet.
- TTA: 5 skala × 5 orientasi; `multiscale_enabled`; catatan: `tta_enabled` flag tidak dibaca loop aktif (dokumentasi di `segmentation.py:18-21`, **tidak diubah**).
- Postprocessing: close/open, area ≥25, fill holes, contour smoothing.
- Grad-CAM target layer `decoder.blocks.4.conv2.0`.
- Pipeline domain gate: REJECT/UNCERTAIN mencegah inferensi.
- Format output: binary mask PNG, segmentation overlay PNG, Grad-CAM heatmap/overlay PNG, measurements, summary text.

### C.3 Integrasi AI-Backend

- `analysis_service.py` mengimpor 7 modul `ai/inference` + `ai/config` (`:20-25`).
- `run_pipeline` dipakai worker background (`_execute_pipeline:906`).
- `run_segmentation`/`run_gradcam` exposed sebagai static method dengan gate domain (`_require_domain_accept` di `:1097`) untuk pemanggilan di luar jalur upload.

---

## D. Audit Database & Supabase

### D.1 Migrasi

| File | Isi |
|---|---|
| `001_create_analyses_and_storage.sql` | tabel `analyses` + bucket storage |
| `002_add_ai_pipeline_metadata.sql` | metadata pipeline AI |
| `003_add_analysis_progress.sql` | progres analisis |
| `004_create_doctor_profiles.sql` | profil dokter |
| `005_create_profile_avatars_bucket.sql` | bucket avatar |
| `006_add_avatar_url_to_doctor_profiles.sql` | kolom avatar |
| `007_add_role_and_account_status.sql` | role & status akun |
| `008_create_doctor_profile_trigger.sql` | trigger profil otomatis |
| `verify_doctor_registration.sql` | verifikasi registrasi |

**Jangan diubah** (schema/RLS/Auth).

### D.2 Repository & Supabase Client

- `AnalysisRepository` (`Backend/src/repositories/analysis_repository.py:5-196`): `create`, `get_by_id`, `list_by_user`, `update`, `delete` dengan opsi `use_service_role`; validasi lifecycle/status segmentasi.
- `get_supabase_client` (`core/supabase.py:45-83`): singleton anon + service role; `is_supabase_configured` cek env.
- Ownership query pada `get_by_id`/`list_by_user`/`delete` memfilter `user_id`.

---

## E. Audit Integrasi Frontend-Backend

| Alur | Frontend | Backend | Status |
|---|---|---|---|
| Upload | `createAnalysis` POST `/api/analysis` FormData `image` | `create_analysis` 202 `{analysis_id, status}` | Konsisten (`analysis.ts:186`, `routes/analysis.py:11`) |
| Polling | `getAnalysis` GET `/api/analysis/{id}` | `get_analysis` detail + signed URL | Konsisten |
| History | `listHistory` GET `/api/history` | `list_history` items + thumbnail | Konsisten |
| Delete | `deleteAnalysis` DELETE `/api/history/{id}` `expectData:false` | `delete_analysis` 200 `{success}` | Konsisten |
| Auth | Bearer token dari Supabase sesi | `require_approved_doctor` / `require_admin` | Konsisten |
| Error | `ApiRequestError` bawa `code` | `APIError` envelope `success:false` | Konsisten |

**Masalah kecil:** `NewAnalysis.tsx` polling masih tanpa batas maksimum eksplisit; `fetch` sudah bertimeout (cleanup). Tidak mengubah kontrak, hanya UX/resiliensi.

---

## F. Audit Alur Fitur

### F.1 Authentication

- Registrasi: `Register.tsx` → `auth.ts:registerUser` → Supabase sign_up; role default doctor, status pending; email konfirmasi.
- Login: `Login.tsx` → `auth.ts:loginUser(email, password, selectedRole)`; cek `app_metadata.role` admin atau `doctor_profiles`; `isRoleMatch` two-way.
- Logout: `logoutUser` → Supabase signOut + clear context.
- Session: `AuthContext` restore + `onAuthStateChange`; startup reset per tab (`sessionStorage` key).
- Protected routes: guard per role/status.
- Ownership: backend filter `user_id`; frontend signed URL milik user.

### F.2 Upload & Analisis

1. Frontend validasi file (tipe, ukuran di UI) → `POST /api/analysis`.
2. Backend `validate_and_decode_image`: filename, kosong, ≤10 MB, MIME (jpeg/png), integritas Pillow, dimensi, MIME cocok konten.
3. Domain heuristik: REJECT/UNCERTAIN → gagal 400, **tidak ada file/record/job**.
4. LLM gate (jika ACCEPT): REJECT → 400; ERROR → UNCERTAIN 400; PASS → lanjut.
5. Upload original ke Storage `analysis/{user}/{id}/original/input.ext` (service role).
6. DB record `status='processing'` (service role).
7. Enqueue job background; `QUEUE_FULL` 429 dengan cleanup.
8. Frontend polling `GET /api/analysis/{id}` sampai terminal.

### F.3 Domain Validation

- Citra non-kolonoskopi ditolak pada gerbang heuristik sebelum storage/DB/job.
- Citra kolonoskopi valid ACCEPT → lanjut LLM.
- Ambigu: UNCERTAIN → gagal, tidak disimpan.
- Tidak ada bypass: `run_segmentation`/`run_gradcam` juga memanggil `_require_domain_accept`.
- Error response konsisten (`NOT_COLONOSCOPY_IMAGE`, `UNCERTAIN_COLONOSCOPY_IMAGE`).

### F.4 Segmentation

Input → `prepare_image` (512, ImageNet) → `predict` (TTA 5×5, sigmoid, threshold 0.55) → `postprocess_mask` (close/open, area ≥25, fill holes, smoothing) → `measure_mask` (area, bbox, probabilitas, kategori) → artefak PNG (mask, overlay) → Grad-CAM → upload 4 artefak → DB 'completed' 100%.

**Tidak ada dua implementasi inferensi yang bertentangan; tidak ada preprocessing ganda.**

### F.5 Grad-CAM

- Target layer `decoder.blocks.4.conv2.0` (dari config, tidak dari request).
- Forward pass dengan grad; objective mean logit over mask; all-zero heatmap jika mask kosong.
- Heatmap disesuaikan ukuran asli; overlay alpha 0.45; colormap jet.
- Disimpan `gradcam_heatmap_path`, `gradcam_overlay_path`; ditampilkan frontend.

### F.6 Result & History

- Status: `processing` → `completed`/`failed`; progres `current_step` + `progress_percent`.
- Polling: `NewAnalysis` (upload) dan `AnalysisResult` (buka hasil).
- Signed URL 3600 detik untuk original, mask, overlay, heatmap, gradcam overlay.
- Summary: `[POLYP_DETECTED]` / `[NO_POLYP_DETECTED]` / `[LOW_CONFIDENCE]`.
- History: daftar + thumbnail; delete memverifikasi ownership; storage cleanup best-effort.

### F.7 Halaman & Fitur Lain

| Halaman | Fungsi |
|---|---|
| Login/Register/ResetPassword | Auth |
| Dashboard | Ringkasan dokter |
| NewAnalysis | Upload + polling |
| AnalysisResult | Hasil segmentasi + Grad-CAM |
| History | Riwayat + hapus |
| HistoryDetail | Detail satu analisis |
| DoctorProfile | Profil dokter + avatar |
| AdminDashboard | Kelola dokter (approve/reject/stats) |
| NotFound | 404 |

Semua fitur yang ada terduga berfungsi (terdokumentasi baseline test). Tidak ada halaman yang hilang dari struktur.

---

## G. Temuan Keamanan (hanya temukan & laporkan, jangan ubah)

1. `SUPABASE_SERVICE_ROLE_KEY` digunakan server-side untuk storage/DB admin — benar, tidak Bocor ke frontend (`core/supabase.py:73-77`, `storage_service.py`).
2. `auth.py` verifikasi token via Supabase, bukan trust client — benar.
3. Role admin dari `app_metadata` (server-write-only) — benar, mencegah escalasi.
4. Storage path sanitize + ownership validation — benar.
5. Tidak ada secret hardcode di source yang terlihat (`grep` API key / password tidak ditemukan di source selain env loader).
6. `.env` gitignored; `.env.example` hanya template.

---

## H. Ringkasan Temuan untuk Tindak Lanjut (Fase 4–6)

| ID | Area | Temuan | Rekomendasi | Risiko jika diubah |
|---|---|---|---|---|
| T1 | Dependency | `google-genai` tercantum di `requirements.txt` (sesudah cleanup) | **SELESAI:** `google-genai>=3.0.0,<3.1.0` | Rendah |
| T2 | Backend | `analysis_service.py` 1147 baris total (1029 non-kosong) (god service) | **DITUNDA** pada Tahap 7 (keputusan pengguna); pecah hanya jika disetujui | Tinggi - cakupan test penuh wajib |
| T3 | Backend | Fallback LLM timeout 15.0 vs config 30.0 | **SELESAI (cleanup):** fallback diselaraskan 30.0 | Rendah |
| T4 | Frontend | `fetch` sudah bertimeout (cleanup); `NewAnalysis` masih tanpa batas polling | **Timeout selesai**; batas polling = Langkah 2 Tahap 7 (disetujui) | Sedang (UX) |
| T5 | Struktur | 10 folder `.gitkeep`-only sudah dihapus; 22 `.gitkeep` tersisa | **Sebagian selesai**; konsolidasi lanjutan pending approval | Rendah |
| T6 | Artefak | `Frontend/dist`, `tsconfig.tsbuildinfo`, log root di working tree | **SELESAI (cleanup):** dibersihkan; artefak regenerable dibuat ulang oleh build baseline | Rendah |
| T7 | Kode potensi tidak terpakai | `getCurrentUser` di `auth.ts` | **SELESAI (cleanup):** dihapus setelah grep menyeluruh | Rendah |
| T8 | Dokumentasi | Duplikat `.md`/`.txt` di `docs/` | Pertahankan (artefak skripsi) | N/A |

Temuan F1–F9 adalah catatan audit awal. F2–F7 telah ditindaklanjuti pada cleanup (lihat status di tabel); F1 (split `AnalysisService`) **ditunda** pada Tahap 7, sedangkan F8/F9 tetap pending.

---

## I. Catatan Baseline Pengujian (untuk Fase 3)

Dari `docs/audit/refactor_lucit_plan.md`:

| Suite | Hasil Baseline | Perintah |
|---|---|---|
| pytest (Backend + AI) | **190 passed, 1 skipped** (dokumen lama Fase 3 mencatat 188; aktual 11 Nov 2026 = 190 passed, 1 skipped) | `python -m pytest tests/ -x --ignore=tests/ai/audit_domain_validator_deep.py --ignore=tests/ai/measure_real_samples_stage2.py` |
| vitest (Frontend) | 298 passed (19 file) | `npx vitest run` |
| Frontend build | berhasil (`dist/` generated) | `npm run build` (`tsc -b && vite build`) |

Angka tersebut sudah diverifikasi langsung pada 11 November 2026: pytest **190 passed, 1 skipped** (116,63 s) dan vitest **298 passed, 0 failed** (57,80 s) — lulus sebelum Tahap 7 dimulai.
