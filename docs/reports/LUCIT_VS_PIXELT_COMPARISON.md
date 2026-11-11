# LUCIT_VS_PIXELT_COMPARISON

**Tanggal:** 11 November 2026
**Modus:** Audit read-only (Tahap A–B) — tidak ada source code yang diubah.
**Referensi:** `LUCIT-master/` (tidak pernah dimodifikasi).

---

## 1. Tujuan Perbandingan

PIXEL-T ingin disederhanakan dengan menggunakan LUCIT-master sebagai *referensi struktural*, bukan sebagai *template yang harus meniru semua pola*. Perbandingan ini menjawab: mana pola LUCIT yang layak diadopsi, dan mana yang **sengaja tidak diadopsi** karena berisiko merusak fitur penelitian PIXEL-T.

---

## 2. Struktur LUCIT-master (saat ini)

```
LUCIT-master/
├── Backend/
│   ├── .gitignore, .python-version, package.json/package-lock.json, requirements.txt
│   └── src/
│       ├── config/         settings.py, supabase.py
│       ├── controllers/    chatbot, prediction, user
│       ├── models/         model_loader.py, user_schema.py
│       ├── repositories/   analysis_repository.py, user_repository.py
│       ├── routes/         chatbot, prediction, user
│       ├── services/       ai_validator, chatbot, email, gradcam, segmentation, vertex_rest_client
│       └── main.py         (entrypoint di dalam src/)
├── Frontend/
│   ├── .env.production, eslint.config.js, index.html, package*.json, README.md
│   ├── public/images/ + src/assets/images/  (duplikasi aset!)
│   └── src/
│       ├── App.tsx, App.css, index.css, main.tsx
│       ├── components/{AboutUs, Features, Footer, Header, Hero, LoginModal, ScrollReveal, SlideTransition, SplashScreen, TransitionPortal}/index.tsx
│       ├── pages/{analysis, history}/index.tsx
│       ├── utils/{api, image, session, supabase}.ts
│       └── tsconfig.app.json, tsconfig.json, tsconfig.node.json
```

Karakteristik LUCIT: `src/` prefix di kedua stack; komponen/halaman dalam folder dengan `index.tsx`; `utils/` untuk shared client/image/session; `models/` untuk schema + loader; entrypoint `main.py` di dalam `src`.

---

## 3. Perbandingan Secara Langsung

### 3.1 Root & Entry Point

| Aspek | LUCIT-master | PIXEL-T | Catatan |
|---|---|---|---|
| Backend entrypoint | `Backend/src/main.py` | `Backend/run.py` | PIXEL-T lebih sederhana (tidak perlu `src/` prefix). Pertahankan `run.py`. |
| Backend layer root | `Backend/src/*` | `Backend/src/*` | Sama; PIXEL-T lebih pendek (`app` vs `src`). |
| Frontend entrypoint | `Frontend/src/main.tsx` | `Frontend/src/main.tsx` | Sama. |
| Vite root package | `Frontend/package.json` | `Frontend/package.json` | Sama; PIXEL-T punya package.json di root untuk tooling diagram (`docx`, `canvas`). |

### 3.2 Backend Layering

| Layer | LUCIT `src/` | PIXEL-T `app/` | Keputusan |
|---|---|---|---|
| Config | `config/settings.py`, `config/supabase.py` | `core/config.py`, `core/supabase.py` | Sama; nama beda saja. Pertahankan `core/`. |
| Error handling | dipangkas di route/controller | `core/errors.py` APIError global | PIXEL-T lebih baik (handler global). Pertahankan. |
| Auth | `controllers/user_controller.py` | `core/auth.py` + decorators | PIXEL-T lebih bersih. Pertahankan. |
| Models / schema | `models/model_loader.py`, `models/user_schema.py` | **tidak ada folder formal** | Model U-Net/ResNet50/Gemini di `ai/`; DB via Supabase migrations. Tidak perlu buat `models/`. |
| Repository | `repositories/*` | `repositories/*` | Sama. Pertahankan. |
| Routes | `routes/*_routes.py` (blueprint-ish) | `routes/*.py` + `__init__.py` | PIXEL-T lebih sederhana. Pertahankan. |
| Controllers | `controllers/*_controller.py` | `controllers/*_controller.py` | Sama. Pertahankan. |
| Services | `services/*` (ai_validator, segmentation, gradcam) | `services/*` + `Backend/ai/inference/*` | PIP: pemisahan `ai/` sebagai modul AI eksternal adalah keputusan arsitektur PIXEL-T (model checkpoint di dalamnya). Pindahkan `ai/` → `Backend/ai/` untuk konsensi lokasi, jangan inisialisasi ulang. |

Catatan penting dari `FINAL_AUDIT_REPORT.md`: **LUCIT menyimpan password plaintext, pakai app global, dan tidak punya tes** — pola ini **TIDAK** layak ditiru. PIXEL-T layak dipertahankan di area tersebut.

### 3.3 Frontend Layout

| Aspek | LUCIT Frontend | PIXEL-T Frontend | Keputusan |
|---|---|---|---|
| Halaman | `pages/analysis/index.tsx` | `pages/analysis/NewAnalysis.tsx` (per route) | PIXEL-T lebih jelas (nama file = route). Pertahankan per-halaman. |
| Komponen | `components/{Feature}/index.tsx` (per fitur) | `components/{kategori}/{Nama}.tsx` (per jenis) | PIXEL-T lebih konsisten untuk UI reusable. Pertahankan kategori, gabungkan `brand/` ke `ui/` (rendah risiko). |
| Utils/ | `utils/{api, image, session, supabase}.ts` | `lib/{format, openingTimeline, supabase}.ts` + `services/*` | PIXEL-T sudah lebih baik (pisah klien Supabase vs layanan bisnis). Pertahankan `lib` + `services`. |
| Tema/styling | `src/assets/style.css` | `src/styles/opening.css` + tailwind | Tidak perlu ubah. |
| Aset | `public/images` **dan** `src/assets/images` (duplikasi!) | `src/assets/` tunggal | PIXEL-T lebih bersih. Pertahankan. |

### 3.4 Pengelompokan File Python

| Item | LUCIT | PIXEL-T | Catatan |
|---|---|---|---|
| Folder layer | `controllers`, `models`, `repositories`, `routes`, `services` | `core`, `controllers`, `repositories`, `routes`, `services` | PIXEL-T sudah lengkap untuk kebutuhan API. |
| Model checkpoint | tidak ada di repo | `Backend/ai/models/*.pth` | Harus tetap di `Backend/ai/models/` — jangan dipindahkan atau dihapus. |
| Database | tidak ada folder migrasi | `database/migrations/` | Pertahankan. |
| Tes | tidak ada | `tests/Backend/`, `tests/ai/`, `tests/Frontend/` | PIXEL-T lebih baik. Pertahankan dua model tes (pytest di `tests/`, Vitest colocated). |

### 3.5 Pemetaan File Analog (PIXEL-T ↔ LUCIT)

| PIXEL-T | LUCIT | Paduan? |
|---|---|---|
| `Backend/src/core/auth.py` | `Backend/src/controllers/user_controller.py` | ≈ |
| `Backend/src/core/errors.py` | (tidak ada di LUCIT) | PIXEL-T lebih baik |
| `Backend/src/routes/analysis.py` | `Backend/src/routes/prediction_routes.py` | ≈ |
| `Backend/src/services/analysis_service.py` | `Backend/src/services/ai_validator_service.py` + `segmentation_service.py` + `gradcam_service.py` | PIXEL-T satu file besar vs LUCIT pecah (LUCIT lebih sederhana per-file, tapi PIXEL-T satu entri tetap valid) |
| `Backend/ai/inference/domain_validator.py` | `Backend/src/services/ai_validator_service.py` | ≈ |
| `Backend/ai/inference/pipeline.py` | `Backend/src/services/*` | ≈ |
| `Frontend/src/pages/analysis/NewAnalysis.tsx` | `Frontend/src/pages/analysis/index.tsx` | ≈ |
| `Frontend/src/pages/history/History.tsx` | `Frontend/src/pages/history/index.tsx` | ≈ |
| `Frontend/src/utils/auth.ts` | `Frontend/src/utils/session.ts` + `supabase.ts` | ≈ |
| `Frontend/src/lib/supabase.ts` | `Frontend/src/utils/supabase.ts` | ≈ |

---

## 4. Apa yang Layak Diadopsi dari LUCIT

1. **Pemisahan file service per tanggung jawab** — LUCIT memisahkan `ai_validator_service`, `segmentation_service`, `gradcam_service`, `vertex_rest_client`. PIXEL-T boleh ikut pola ini dalam tahap lanjutan (split `analysis_service.py` sesuai Langkah 3 yang **ditunda**, tapi dilabeli dalam proposal).
2. **`services/` di backend untuk semua logika bisnis** — sudah ada di PIXEL-T.
3. **Backend entrypoint menyatu dengan layer** — LUCIT `main.py` di dalam `src/`, PIXEL-T `run.py` di luar `app/`. Pertahankan `run.py` (sudah berfungsi, lebih pendek).

---

## 5. Apa yang Sengaja TIDAK Diadopsi (Berdasarkan Audit Sebelumnya)

Dari `FINAL_AUDIT_REPORT.md` dan `LUCIT_ARCHITECTURE_ANALYSIS.md`:

| Pola LUCIT | Alasan tidak diadopsi |
|---|---|
| Password plaintext | PIXEL-T pakai Supabase Auth + token Bearer. Keamanan lebih baik. |
| Flask app global | PIXEL-T pakai `create_app` factory. Lebih baik untuk testing. |
| Tidak ada tes | PIXEL-T punya pytest 190 + Vitest 302. Harus dijaga. |
| `components/{Feature}/index.tsx` semua halaman | PIXEL-T sudah per-file per-route; cukup untuk skala ini. |
| Duplikasi aset `public/` + `src/assets/` | PIXEL-T hanya `src/assets/`. |

---

## 6. Ukuran & Kompleksitas Kuantitatif

| Metrik | LUCIT-master | PIXEL-T | Catatan |
|---|---|---|---|
| Backend .py (tanpa venv) | 18 | ~16 | Sama orde. |
| Frontend .ts/.tsx di `src/` | ~21 | ~50 | PIXEL-T lebih banyak karena per-halaman + tes colocated. |
| Backend LOC | ~2.269 | ~3.190 | PIXEL-T lebih besar (ai_service god service + analisis lengkap). |
| Frontend LOC (src) | ~4.659 | ~14.692 | PIXEL-T lebih besar (UI lengkap + tes). |
| Folder layer backend | 5 | 5 | Sama. |
| `models/` formal | ada | tidak ada | PIXEL-T pakai `ai/`; tidak masalah. |

---

## 7. Kesimpulan Perbandingan

PIXEL-T sudah memiliki struktur yang **lebih bersih dari LUCIT** di beberapa aspek (app factory, error handler global, auth terpusat, tes otomatis, aset tunggal), tetapi struktur masih belum "sederhana" karena:

1. `analysis_service.py` god-service (1147 baris) — belum dipecah.
2. Root project masih tertumpuk laporan audit + tooling diagram.
3. `statusText.contrast.test.tsx` di root `src` (tidak colocated).
4. `.gitkeep` residu di banyak folder.
5. Dokumen duplikasi `.md`/`.txt`.

Rekomendasi struktural dalam `PIXELT_SIMPLIFIED_STRUCTURE_PROPOSAL.md` mengacu pada pola LUCIT **tanpa meniru pola berisiko** dan tanpa membuat lapisan abstraksi berlebihan.
