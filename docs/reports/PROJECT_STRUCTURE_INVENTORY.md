# PROJECT STRUCTURE INVENTORY — PIXEL-T

**Tanggal audit:** 11 November 2026  
**Branch:** `fitur/validasi-input`  
**HEAD:** `cbb5296`  
**Sifat:** inventaris read-only. Tidak ada file produksi yang diubah, dipindahkan, atau dihapus untuk membuat laporan ini.  
**Referensi pembanding:** `LUCIT-master/` (read-only, tidak boleh diubah).

---

## 0. Ringkasan Eksekutif

PIXEL-T bukan sekadar aplikasi web: ia menggabungkan **aplikasi Flask**, **SPA React**, **modul inferensi PyTorch**, **migration Supabase**, **test suite**, serta **artefak penelitian skripsi**. Karena itu, struktur target tidak boleh dipaksa seluruhnya menjadi `Backend/` + `Frontend/`. Folder `ai/`, `research/`, `scripts/`, `database/`, `docs/`, `diagram-skripsi/`, dan `references/` adalah bagian sah dari proyek penelitian dan harus dipertahankan.

Pada snapshot ini:

| Metrik | Nilai | Keterangan |
|---|---:|---|
| File tracked Git | **507** | Termasuk 266 file di `references/` |
| File tracked non-references | **241** | Aplikasi, test, dokumentasi, diagram, migration |
| File kerja yang dipindai | **269** | Di luar `node_modules`, `.venv`, `.git`, cache, `dist`, `LUCIT-master`, `calibration_data`, `references` |
| File `.gitkeep` tersisa | **22** (di luar `node_modules`) | Sebagian sudah berada di folder yang berisi file nyata |
| Laporan audit root | **13 laporan wajib** | Dibuat pada tahap ini; belum di-commit |
| Status staging | **Kosong** | Belum ada commit/push |

**Kesimpulan inventaris:** struktur inti PIXEL-T sudah layering dan modular. Masalah utama bukan “salah folder”, melainkan **beberapa file terlalu besar**, **beberapa helper/error-envelope tidak konsisten**, **sisa placeholder `.gitkeep`**, **artefak build/log**, dan **tooling diagram di root**. Semua kandidat perubahan harus melewati persetujuan dan regresi.

---

## 1. Metode dan Batas Inventaris

1. Membaca pohon folder dan file tracked (`git ls-files`), file untracked, serta file yang di-ignore.
2. Mencocokkan setiap area dengan entry point dan import statis/dinamis.
3. Memeriksa pemakaian melalui `grep`, bukan hanya nama file.
4. Tidak membuka atau menyalin isi `.env`; hanya nama variabel dari `.env.example` yang dicatat.
5. Tidak menghitung `node_modules`, `.venv`, `.git`, `__pycache__`, `.pytest_cache`, `dist/`, `calibration_data/`, `references/`, dan `LUCIT-master/` sebagai kode aplikasi.
6. Kategori file:

| Kode | Arti | Tindakan default |
|---|---|---|
| **A** | Wajib / inti runtime atau keamanan | Pertahankan; perubahan hanya dengan persetujuan |
| **B** | Dapat disederhanakan | Kandidat refactor internal; belum diubah |
| **C** | Dapat digabung/dikonsolidasi | Kandidat konsolidasi; belum diubah |
| **D** | Tidak diperlukan / artefak regenerable | Kandidat pembersihan; harus dibuktikan dahulu |
| **E** | Dipindah | Kandidat relokasi; menunggu approval dan cek path |
| **F** | Artefak penelitian/skripsi | Wajib dipertahankan |

---

## 2. Peta Direktori Tingkat Atas

```text
WEB_PIXELT/
├── .env.example                  A  template root (jangan hapus)
├── .gitignore                    A  aturan ignore
├── README.md                     A  panduan proyek
├── package.json / lock           F  tooling dokumen skripsi
├── generate_bab4.js              F  generator BAB 4
├── render_erd.mjs                F  render ERD
├── rasterize_erd.py              F  rasterisasi ERD
├── rasterize_svg.py              F  rasterisasi SVG
├── test_render.mjs               F  uji render diagram
├── test_field.puml/.svg          F  artefak uji diagram
├── ai/                            A  modul AI/ML (dilindungi)
├── Backend/                       A  API Flask
├── Frontend/                      A  SPA React/Vite
├── database/                      A  migration & verifikasi SQL
├── tests/                         A  unit/integration test
├── docs/                          F  spesifikasi & audit skripsi
├── diagram-skripsi/               F  diagram final skripsi
├── research/                      F  notebook & hasil evaluasi
├── scripts/                       F  eksperimen/kalibrasi/evaluasi
├── calibration_data/              F  dataset kalibrasi (gitignored)
├── references/                    F  referensi (gitignored, 266 file)
├── LUCIT-master/                  F  proyek acuan read-only
├── node_modules/                  D  dependency (gitignored)
└── .venv/                         D  virtualenv (gitignored)
```

Catatan: `dist/`, `tsconfig.tsbuildinfo`, `.pytest_cache/`, dan log runtime bersifat **regenerable**. Keberadaannya bisa muncul kembali setelah build/test; tidak boleh dianggap source.

---

## 3. Inventaris `ai/` — Modul AI/ML (Kategori A, dilindungi)

| File | Baris | Kategori | Fungsi |
|---|---:|---|---|
| `ai/__init__.py` | kecil | A | marker package |
| `ai/README.md` | — | A/F | dokumentasi modul AI |
| `Backend/ai/config/model_config.py` | 58 | A | `MODEL_CONFIG`: U-Net+ResNet50, input 512, threshold 0.55, TTA, target Grad-CAM, hash checkpoint |
| `Backend/ai/config/model_config.example.yaml` | — | A/F | contoh konfigurasi |
| `Backend/ai/config/.gitkeep` | 0 | B | penanda folder; folder sudah berisi file |
| `Backend/ai/inference/__init__.py` | kecil | A | marker package |
| `Backend/ai/inference/preprocessing.py` | 22 | A | resize/normalisasi ImageNet |
| `Backend/ai/inference/segmentation.py` | 114 | A | `predict`, TTA 5×5, sigmoid, threshold, `count_forward_passes` |
| `Backend/ai/inference/postprocessing.py` | 109 | A | morphology, area filter, fill holes, `measure_mask` |
| `Backend/ai/inference/gradcam.py` | 153 | A | Grad-CAM deterministik, target layer dari config |
| `Backend/ai/inference/domain_validator.py` | 276 | A | heuristik domain kolonoskopi (`ACCEPT/REJECT/UNCERTAIN`) |
| `Backend/ai/inference/pipeline.py` | 155 | A | 5 fase pipeline tanpa side effect persistensi |
| `Backend/ai/inference/model_service.py` | 119 | A | lazy load checkpoint, device, verifikasi state dict/hash |
| `Backend/ai/models/.gitkeep` | 0 | A | penanda folder checkpoint; **jangan hapus** |
| `Backend/ai/models/PIXEL-T_..._best.pth` | 135.644.553 B | A | checkpoint produksi (gitignored, jangan diubah) |

**Aturan:** jangan mengubah U-Net/ResNet50, checkpoint, preprocessing, TTA, threshold `0.55`, Grad-CAM, dataset/split, atau hasil eksperimen.

---

## 4. Inventaris `Backend/` — API Flask (Kategori A)

### 4.1 Entry point dan konfigurasi

| File | Baris | Kategori | Fungsi |
|---|---:|---|---|
| `Backend/run.py` | 11 | A | `create_app()` + run server |
| `Backend/src/__init__.py` | 33 | A | application factory, CORS, error handler, blueprint |
| `Backend/src/core/config.py` | 60 | A | konfigurasi env; timeout LLM 30.0 s |
| `Backend/src/core/supabase.py` | 64 | A | client anon/service-role singleton, status config |
| `Backend/src/core/errors.py` | 108 | A | `APIError` + envelope error global |
| `Backend/src/core/auth.py` | 257 | A | Bearer token, `require_admin`, `require_approved_doctor` |
| `Backend/set_admin_role.py` | 87 | A | utilitas operasional admin |
| `Backend/requirements.txt` | — | A | dependency Python, termasuk `google-genai>=3.0.0,<3.1.0` |
| `Backend/.env` | — | A | secret lokal; **tidak dibaca/di-commit** |
| `Backend/.env.example` | — | A | template backend (tanpa secret nyata) |

### 4.2 Routes, controllers, services, repositories

| File | Baris | Kategori | Fungsi |
|---|---:|---|---|
| `Backend/src/routes/__init__.py` | 10 | A | registrasi 3 blueprint di `/api` |
| `Backend/src/routes/health.py` | 11 | A | `GET /api/health` |
| `Backend/src/routes/analysis.py` | 64 | A | 4 endpoint analisis/history |
| `Backend/src/routes/admin.py` | 33 | A | 5 endpoint admin |
| `Backend/src/controllers/analysis_controller.py` | 96 | A | validasi request & panggil service |
| `Backend/src/controllers/admin_controller.py` | 84 | A | endpoint admin; envelope error perlu diselaraskan (B) |
| `Backend/src/services/analysis_service.py` | **1147 (1029 non-kosong)** | A/B | orkestrasi upload, gate, storage, DB, queue, pipeline, progress |
| `Backend/src/services/admin_service.py` | 335 | A | listing/statistik/approve/reject |
| `Backend/src/services/storage_service.py` | 158 | A | path ownership, upload, signed URL, delete |
| `Backend/src/services/llm_image_validator.py` | 190 | A | Gemini gate fail-closed |
| `Backend/src/repositories/analysis_repository.py` | 158 | A | CRUD `analyses`, validasi lifecycle |
| `Backend/src/controllers/__init__.py` | kecil | A | marker package |
| `Backend/src/services/__init__.py` | kecil | A | marker package |
| `Backend/src/repositories/__init__.py` | kecil | A | marker package |
| `Backend/src/routes/.gitkeep`, `controllers/.gitkeep`, `core/.gitkeep`, `repositories/.gitkeep`, `services/.gitkeep` | 0 | B | penanda folder; folder sudah berisi file |

### 4.3 Endpoint contract (jangan diubah tanpa persetujuan)

| Method | Path | Guard | Bukti |
|---|---|---|---|
| GET | `/api/health` | publik | `routes/health.py:6-11` |
| POST | `/api/analysis` | `require_approved_doctor` | `routes/analysis.py:11-26` |
| GET | `/api/analysis/<id>` | `require_approved_doctor` | `routes/analysis.py:29-42` |
| GET | `/api/history` | `require_approved_doctor` | `routes/analysis.py:45-53` |
| DELETE | `/api/history/<id>` | `require_approved_doctor` | `routes/analysis.py:56-64` |
| GET | `/api/admin/doctors` | `require_admin` | `routes/admin.py:9-13` |
| GET | `/api/admin/doctors/stats` | `require_admin` | `routes/admin.py:16-20` |
| GET | `/api/admin/doctors/<id>` | `require_admin` | `routes/admin.py:23-27` |
| POST | `/api/admin/doctors/<id>/approve` | `require_admin` | `routes/admin.py:30-34` |
| POST | `/api/admin/doctors/<id>/reject` | `require_admin` | `routes/admin.py:37-45` |

---

## 5. Inventaris `Frontend/` — SPA React (Kategori A)

### 5.1 Entry, routing, context, services, lib, hooks

| File | Baris | Kategori | Fungsi |
|---|---:|---|---|
| `Frontend/index.html` | — | A | entry Vite |
| `Frontend/package.json` / lock | — | A | dependency frontend |
| `Frontend/vite.config.ts`, `tsconfig.json`, `tailwind.config.js`, `postcss.config.js` | — | A | build/config |
| `Frontend/.env` | — | A | secret lokal; tidak dibaca/di-commit |
| `Frontend/.env.example` | — | A | template `VITE_*` |
| `Frontend/src/main.tsx` | 9 | A | render root |
| `Frontend/src/App.tsx` | 58 | A | provider, theme, shell |
| `Frontend/src/routes/AppRoutes.tsx` | 107 | A | route + guard |
| `Frontend/src/context/AuthContext.tsx` | 254 | A | sesi Supabase, role/status |
| `Frontend/src/utils/analysis.ts` | 246 | A | client API + timeout + polling |
| `Frontend/src/utils/auth.ts` | 329 | A | login/register/logout/reset |
| `Frontend/src/utils/profile.ts` | 356 | A | profil/avatar |
| `Frontend/src/lib/supabase.ts` | 25 | A | client anon |
| `Frontend/src/lib/format.ts` | 69 | A | format tanggal/angka/label |
| `Frontend/src/lib/openingTimeline.ts` | 158 | A | timeline animasi |
| `Frontend/src/hooks/useTheme.ts` | 45 | A | tema |
| `Frontend/src/hooks/useOpeningAnimation.ts` | 79 | A | status animasi |
| `Frontend/src/index.css`, `styles/opening.css` | — | A | styling global |
| `Frontend/src/vite-env.d.ts` | 8 | A | tipe env Vite |

### 5.2 Komponen UI, auth guard, layout, brand

| File | Baris | Kategori | Fungsi |
|---|---:|---|---|
| `components/ui/Badge.tsx` | 55 | A | badge |
| `components/ui/Button.tsx` | 50 | A | tombol |
| `components/ui/Card.tsx` | 51 | A | kartu |
| `components/ui/EmptyState.tsx` | 33 | A | empty state |
| `components/ui/ErrorState.tsx` | 39 | A | error state |
| `components/ui/Input.tsx` | 52 | A | input |
| `components/ui/LoadingState.tsx` | 26 | A | loading |
| `components/ui/Modal.tsx` | 205 | A/B | modal; kandidat ekstraksi internal |
| `components/ui/ThemeToggle.tsx` | 22 | A | toggle tema |
| `components/auth/AdminRoute.tsx` | 32 | A | guard admin |
| `components/auth/DoctorRoute.tsx` | 41 | A | guard dokter |
| `components/auth/ProtectedRoute.tsx` | 34 | A | guard login |
| `components/auth/PublicOnlyRoute.tsx` | 35 | A | guard halaman publik |
| `components/auth/AuthLoadingState.tsx` | 13 | A | loading auth |
| `components/auth/OpeningAnimation.tsx` | 194 | A | animasi pembuka |
| `components/brand/LogoPixelT.tsx` | 117 | A | logo |
| `components/layout/AppShell.tsx` | 386 | A/B | shell global; kandidat ekstraksi |
| `components/layout/.gitkeep`, `components/ui/.gitkeep`, `assets/.gitkeep`, `hooks/.gitkeep`, `routes/.gitkeep`, `services/.gitkeep` | 0 | B | penanda folder yang sudah berisi |

### 5.3 Halaman

| File | Baris | Kategori | Catatan |
|---|---:|---|---|
| `pages/auth/Login.tsx` | 487 | A/B | besar; kandidat ekstraksi komponen |
| `pages/auth/Register.tsx` | 314 | A/B | — |
| `pages/auth/ResetPassword.tsx` | 204 | A | — |
| `pages/dashboard/Dashboard.tsx` | 274 | A/B | — |
| `pages/analysis/NewAnalysis.tsx` | **592** | A/B | upload + polling; belum ada batas polling eksplisit |
| `pages/analysis/AnalysisResult.tsx` | 329 | A/B | polling maksimum 12 |
| `pages/history/History.tsx` | **577** | A/B | riwayat + hapus |
| `pages/history/HistoryDetail.tsx` | 209 | A | detail |
| `pages/profile/DoctorProfile.tsx` | **974** | A/B | file terbesar; kandidat ekstraksi |
| `pages/admin/AdminDashboard.tsx` | **505** | A/B | kelola dokter |
| `pages/NotFound.tsx` | 35 | A | 404 |
| `pages/analysis/.gitkeep`, `auth/.gitkeep`, `dashboard/.gitkeep`, `history/.gitkeep` | 0 | B | penanda folder yang sudah berisi |

### 5.4 Test frontend dan aset

- Test vitest: `App.test.tsx`, `statusText.contrast.test.tsx`, `components/auth/OpeningAnimation.test.ts`, `components/ui/Badge.test.tsx`, `components/ui/Modal.test.tsx`, `context/AuthContext.test.tsx`, `hooks/useOpeningAnimation.test.ts`, `lib/openingTimeline.test.ts`, `pages/admin/AdminDashboard.test.tsx`, `pages/analysis/AnalysisResult.test.tsx`, `pages/analysis/NewAnalysis.test.tsx`, `pages/auth/Login.test.tsx`, `pages/auth/Register.test.tsx`, `pages/dashboard/Dashboard.test.tsx`, `pages/history/History.test.tsx`, `pages/profile/DoctorProfile.test.tsx`, `services/analysis.test.ts`, `services/auth.test.ts`, `services/profile.test.ts` — kategori **A**.
- Aset: `assets/icon-doctor.png`, `pixel-t-logo.jpg`, `pixel-t-logo-light.png`, `pixel-t-logo-transparent.png` — kategori **A**.
- `Frontend/dist/`, `Frontend/tsconfig.tsbuildinfo` — kategori **D** (regenerable, gitignored).

---

## 6. Inventaris `database/` (Kategori A/F)

| File | Kategori | Fungsi |
|---|---|---|
| `database/README.md` | A/F | dokumentasi database |
| `database/migrations/001_create_analyses_and_storage.sql` | A/F | tabel `analyses` + bucket |
| `database/migrations/002_add_ai_pipeline_metadata.sql` | A/F | metadata pipeline |
| `database/migrations/003_add_analysis_progress.sql` | A/F | progress |
| `database/migrations/004_create_doctor_profiles.sql` | A/F | profil dokter |
| `database/migrations/005_create_profile_avatars_bucket.sql` | A/F | bucket avatar |
| `database/migrations/006_add_avatar_url_to_doctor_profiles.sql` | A/F | avatar URL |
| `database/migrations/007_add_role_and_account_status.sql` | A/F | role/status |
| `database/migrations/008_create_doctor_profile_trigger.sql` | A/F | trigger profil |
| `database/migrations/.gitkeep` | B | penanda folder yang sudah berisi migration |
| `database/verify_doctor_registration.sql` | A/F | verifikasi registrasi |

**Jangan ubah** schema, RLS, atau migration pada tahap audit.

---

## 7. Inventaris `tests/` (Kategori A, kecuali script audit = F/B)

| File | Baris | Kategori | Fungsi |
|---|---:|---|---|
| `tests/conftest.py` | 21 | A | fixture app/client |
| `tests/Backend/test_analysis.py` | 849 | A | API analisis |
| `tests/Backend/test_auth.py` | 94 | A | auth/guard |
| `tests/Backend/test_admin_routes.py` | 123 | A | route admin |
| `tests/Backend/test_admin_service.py` | 395 | A | service admin |
| `tests/Backend/test_domain_validation_api.py` | 212 | A | regresi domain gate |
| `tests/Backend/test_health.py` | 54 | A | health |
| `tests/Backend/test_history.py` | 300 | A | history |
| `tests/Backend/test_llm_image_validator.py` | 759 | A | LLM gate |
| `tests/Backend/test_repository.py` | 168 | A | repository |
| `tests/Backend/test_storage_service.py` | 106 | A | storage |
| `tests/Backend/test_supabase_config.py` | 82 | A | konfigurasi Supabase |
| `tests/ai/test_domain_validator.py` | 228 | A | heuristik domain |
| `tests/ai/test_gradcam.py` | 64 | A | Grad-CAM |
| `tests/ai/test_model_integration.py` | 208 | A | integrasi model |
| `tests/ai/test_post_segmentation_validation.py` | 65 | A | pasca-segmentasi |
| `tests/Frontend/test_frontend_env_safety.py` | 62 | A | keamanan env FE |
| `tests/ai/audit_domain_validator_deep.py` | 397 | F/B | script audit, bukan unit test; di-ignore baseline |
| `tests/ai/measure_real_samples_stage2.py` | 46 | F/B | pengukuran sampel; di-ignore baseline |
| `tests/ai/.gitkeep`, `Backend/.gitkeep`, `Frontend/.gitkeep` | 0 | B | penanda folder |

---

## 8. Inventaris `scripts/`, `research/`, `docs/`, `diagram-skripsi/`

### 8.1 `scripts/` — artefak penelitian (F), jangan hapus

`calibrate_domain_gate.py`, `experiment_domain_gate.py`, `eval_llm_gate.py`, `generate_section1_data.py`, `smoke_llm_gate.py`, `evaluate_holdout.py`, `verify_b0_strong.py`, `verify_c2_calib_match.py`.

`scripts/output/*` berisi 19 CSV/TXT dan 2 JPG hasil eksperimen — **F**. Ada ketergantungan internal yang harus dijaga: `scripts/generate_section1_data.py` mengimpor `scripts.experiment_domain_gate`; beberapa skrip memakai `PROJECT_ROOT = Path(__file__).resolve().parents[1]`. Karena itu penataan subfolder `scripts/` berisiko dan ditunda.

### 8.2 `research/` — bukti penelitian (F)

- `PIXEL-T_Scenario1_Ver22_config.json`
- `PIXEL-T_Scenario1_Ver22_evaluation_results.csv`
- `segmentationcolonpolyp-unet-resnet50-gradcam.ipynb`

**Jangan hapus/ubah** tanpa persetujuan pembimbing/peneliti.

### 8.3 `docs/` — spesifikasi, audit, diagram (F)

Spesifikasi: `PRD_PIXEL-T_FINAL.md`, `FunctionalSpecification.md`, `StyleGuide.md`, `APIContract.md`, `DataModelSpecification.md`, `ModelIntegrationSpecification.md`, `CodebaseAnalysis.md`.  
Audit: `docs/audit/*` (00–04, hash, LLM, login, refactor plan).  
Forensik: `ADMIN_DASHBOARD_AND_APPROVE_FORENSIC_REPORT.md`, `APROVE_DOKTER_FIX_REPORT.md`, `DOMAIN_VALIDATION_FALSE_ACCEPTANCE_FIX_REPORT.md`.  
Pasangan `.md`/`.txt`: `APIContract`, `StyleGuide`, `DataModelSpecification`, `AdminDashboardAndApproveForensicReport` — **duplikat format, tetapi artefak skripsi; jangan hapus** sebelum konfirmasi.  
Diagram: `docs/diagrams/*.puml` (14 file) — **F**.

### 8.4 `diagram-skripsi/` — diagram final (F)

8 file PlantUML: `class/class_diagram.puml`, `sequence/sequence_*_FINAL.puml` (7 file).

---

## 9. File Root dan Tooling

| File | Kategori | Fungsi |
|---|---|---|
| `README.md` | A | panduan proyek |
| `.gitignore` | A | ignore env, dependency, model, dataset, log |
| `.env.example` | A | template root |
| `package.json`, `package-lock.json` | F | tooling dokumen (`docx`, `canvas`, `@supabase/*`) |
| `generate_bab4.js` | F | generator BAB 4; bergantung `__dirname/references/bab 4` |
| `render_erd.mjs` | F | render ERD |
| `rasterize_erd.py` | F | rasterisasi ERD |
| `rasterize_svg.py` | F | rasterisasi SVG |
| `test_render.mjs` | F | uji render |
| `test_field.puml`, `test_field.svg` | F | artefak uji diagram |
| `LUCIT-master/` | F | referensi read-only |
| `calibration_data/`, `references/` | F | data penelitian (gitignored) |
| `Frontend/dist/`, `Frontend/tsconfig.tsbuildinfo`, `.pytest_cache/`, `*.log` | D | regenerable, gitignored |

---

## 10. Jejak Alur dan Entry Point

| Area | Entry point | Bukti |
|---|---|---|
| Backend | `Backend/run.py` → `app.create_app()` | `Backend/run.py`, `Backend/src/__init__.py:8-33` |
| Frontend | `Frontend/index.html` → `src/main.tsx` → `App.tsx` → `AppRoutes.tsx` | `Frontend/src/main.tsx`, `App.tsx`, `routes/AppRoutes.tsx` |
| AI | `Backend/ai/inference/pipeline.py:run_pipeline` dipanggil `AnalysisService` | `Backend/src/services/analysis_service.py:23,908,1120,1135` |
| Database | `database/migrations/001–008` | Supabase SQL |
| Test | `tests/conftest.py` + `vitest` config di `vite.config.ts` | suite 190 pytest + 298 vitest |

---

## 11. Snapshot Baseline (Tahap 6)

| Item | Hasil | Bukti |
|---|---|---|
| pytest | **190 passed, 1 skipped** | `baseline_pytest.log`; 116.63 s |
| vitest | **298 passed, 19 file** | `baseline_vitest.log`; 57.80 s |
| `pip check` | **No broken requirements** | `baseline_pipcheck.log` |
| Build frontend | **Sukses** | `baseline_frontend_build.log`; 12.20 s |
| Hash checkpoint | **`46521AE9...C581`**, 135.644.553 B | `baseline_hash.txt` |
| Manual E2E | **NOT TESTED** | lihat `MANUAL_E2E_TEST_PLAN.md` |

---

## 12. Kesimpulan Inventaris

1. **Yang wajib dipertahankan (A):** `ai/`, `Backend/src/{core,routes,controllers,services,repositories}`, `Frontend/src`, `database/migrations`, `tests/**`, seluruh entry point/konfigurasi build.
2. **Yang dapat disederhanakan (B):** `analysis_service.py`, `core/auth.py`, beberapa halaman frontend besar, `admin_controller.py`, sisa `.gitkeep` di folder berisi.
3. **Yang dapat digabung (C):** dokumen `.md`/`.txt` (**hanya setelah konfirmasi skripsi**), duplikasi helper kecil, kelompok laporan audit lama.
4. **Yang tidak diperlukan (D):** artefak build/cache/log (gitignored, regenerable).
5. **Yang dipindah (E):** tooling diagram root (**ditunda** karena path `__dirname`), `scripts/` subfolder (**ditunda** karena import/path).
6. **Yang merupakan artefak penelitian (F):** `research/`, `scripts/`, `calibration_data/`, `references/`, `docs/`, `diagram-skripsi/`, `LUCIT-master/`, checkpoint, notebook, hasil eksperimen.

**Tidak ada file yang dihapus/dipindahkan pada tahap inventaris ini.** Keputusan perubahan menunggu persetujuan pada `REFACTORING_PLAN.md`.
