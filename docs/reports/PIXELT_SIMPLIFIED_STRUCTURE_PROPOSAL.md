# PIXELT_SIMPLIFIED_STRUCTURE_PROPOSAL

**Tanggal:** 11 November 2026
**Mode:** Proposal only (Tahap B) — **belum ada perubahan source code, folder, atau file**.
**Dasar:** Pola struktural LUCIT-master + kebutuhan maintainabilitas PIXEL-T.
**Status:** Menunggu persetujuan sebelum Tahap C (rencana eksekusi) dan Tahap D (eksekusi).

---

## 1. Prinsip Penyusunan Target

1. **Sederhana, tidak berlebihan**: tanpa folder baru hanya demi mengikuti nama pola; folder baru hanya bila menambah nilai pemahaman.
2. **Layered tetap**: backend tetap `app/{core,controllers,routes,repositories,services}`; AI tetap di `ai/` (dipindah ke `Backend/ai/`).
3. **Naming by content, bukan by pattern**: `pages/<route>/<Page>.tsx` tetap dipakai (lebih jelas dari `index.tsx` semua halaman).
4. **Tidak ada barrel/`index.ts` untuk komponen kecil** — hanya per-file + folder grouping yang sudah ada.
5. **Satu model layout**: backend Python di `Backend/`, frontend TS di `Frontend/`, AI di `Backend/ai/`, penelitian di `ai/`, notebook di `research/`, aset skripsi di `references/`, diagram di `diagram-skripsi/`, tooling diagram di `scripts/tools/`.
6. **Tes**: backend pytest di `tests/{backend,ai,frontend}`; frontend Vitest colocated di `src/**/__tests__/` atau bersama subject.

---

## 2. Struktur Target yang Diusulkan

```
WEB_PIXELT/
├── Backend/
│   ├── run.py
│   ├── set_admin_role.py        → Backend/tools/set_admin_role.py   (Fase 1)
│   ├── requirements.txt
│   ├── .env.example
│   └── app/
│       ├── __init__.py
│       ├── core/{auth,config,errors,supabase}.py
│       ├── controllers/{admin,analysis}_controller.py
│       ├── repositories/analysis_repository.py
│       ├── routes/{admin,analysis,health}.py
│       └── services/{analysis,admin,llm_image_validator,storage}_service.py
├── Backend/ai/                  # ← DARI ROOT `ai/` (Fase 1, move murni)
│   ├── __init__.py, config/{model_config.py,model_config.example.yaml}, inference/*.py, models/*.pth
├── Frontend/
│   └── src/
│       ├── __tests__/statusText.contrast.test.tsx   (Dari src root → Fase 2)
│       ├── components/{ui/, layout/, auth/}
│       │   └── ui/LogoPixelT.tsx                     (DARI components/brand/ → Fase 2)
│       ├── context/, hooks/, lib/, pages/, routes/, services/, styles/
├── database/{migrations/,README.md}
├── docs/                         # (Laporan audit dipindahkan sementara, lanjut Fase 3)
├── scripts/{experiment/, tools/}  # tools/: generate_bab4.js, render_erd.mjs, rasterize_erd.py, rasterize_svg.py, test_render.mjs, test_field.puml/.svg
├── tests/{backend,ai,frontend}/
├── research/, references/, diagram-skripsi/, calibration_data/
├── README.md, .env.example, .gitignore, package.json (tooling)
└── (clean root: tanpa laporan audit & skrip diagram; keputusan final dalam Fase 3)
```

Catatan: `Backend/ai/` dipindah **sebagai satu gerakan folder** (bukan file per file) supaya `from ai.* import` tetap valid karena `Backend/` sudah masuk `sys.path` (`Backend/run.py`, `tests/conftest.py`).

---

## 3. Daftar Perubahan Per Tahap

### Tahap 1 — Backend (disusun, belum dijalankan)

| No | Sumber | Tujuan | Tindakan | Alasan |
|---|---|---|---|---|
| 1.1 | `ai/` (root) | `Backend/ai/` | Pindah folder (move) | Konsistensi satu stack backend Python; import absolut tetap valid via sys.path backend. |
| 1.2 | `Backend/set_admin_role.py` | `Backend/tools/set_admin_role.py` | Pindah file | Utility skrip, bukan bagian aplikasi; memisahkan tool admin dari layer app. |
| 1.3 | `Backend/src/{controllers,core,repositories,routes,services}` + `Backend/ai/models/` | — | Hapus `.gitkeep` | Folder semua terisi (bukti: file nyata). |

### Tahap 2 — Frontend (disusun, belum dijalankan)

| No | Sumber | Tujuan | Tindakan | Alasan |
|---|---|---|---|---|
| 2.1 | `Frontend/src/statusText.contrast.test.tsx` | `Frontend/src/__tests__/statusText.contrast.test.tsx` | Pindah file | Test cross-cutting, bukan colocated. |
| 2.2 | `Frontend/src/components/brand/LogoPixelT.tsx` | `Frontend/src/components/ui/LogoPixelT.tsx` | Pindah + merge folder | Satu konsep ikon/logo + token UI; folder `brand` hanya menampung 1 file. |
| 2.3 | `Frontend/src/{...}` placeholder `.gitkeep` | — | Hapus | Folder terisi. |
| 2.4 | `Frontend/tsconfig.tsbuildinfo` | — | Hapus (gitignored) | Build artifact regenerable. |

### Tahap 3 — Root / Dokumentasi / Tooling (disusun, belum dijalankan)

| No | Sumber | Tujuan | Tindakan | Alasan |
|---|---|---|---|
| 3.1 | Root-level tooling & artefak | `scripts/tools/diagrams/` | Pindah | `generate_bab4.js` (butuh path update `__dirname`), `render_erd.mjs`, `rasterize_erd.py`, `rasterize_svg.py`, `test_render.mjs`, `test_field.puml`, `test_field.svg`. |
| 3.2 | Root-level laporan audit | `docs/reports/` | Pindah (dengan konten tetap; rename sesuai kebijakan) | Menyederhanakan root. |
| 3.3 | Duplikasi `*.md` vs `*.txt` | — | Kandidat hapus, perlu persetujuan & perbandingan isi | Pastikan tidak menghapus informasi penting. |
| 3.4 | Root `package.json` | `scripts/tools/` | Pindah (opsional) | Hanya untuk tooling diagram/docx; keputusan minimal perubahan. |

### Tahap 4 — Penyederhanaan file besar (DISPENDED, menunggu persetujuan terpisah)

| No | Sumber | Tujuan | Arah |
|---|---|---|---|
| 4.1 | `Backend/src/services/analysis_service.py` (1147 baris) | per tanggung jawab | Split seperti LUCIT (domain validation / LLM gate / pipeline / progress) — **masih ditunda (Langkah 3 Tahap 7)**. |
| 4.2 | `Frontend/src/pages/profile/DoctorProfile.tsx` (1051) | komponen | Ekstrak section — **ditunda (2B–2D)**. |

---

## 4. File / Folder yang PERTAHANKAN (tidak diubah)

| Item | Alasan |
|---|---|
| `Backend/src/{core,controllers,routes,repositories,services}` | Layering sudah benar & teruji. |
| `Backend/ai/{config,inference,models}` | Modul AI yang sudah diverifikasi (SHA-256 checkpoint). |
| `Frontend/src/{pages,services,context,hooks,lib,routes,styles,components}` | Konsep sudah jelas & fitur belum melebihi ukuran. |
| `Frontend/src/utils/{analysis,auth,profile}.ts` | Pemisah klien Supabase vs layanan bisnis. |
| `tests/{backend,ai,frontend}` | Dua model tes sudah berfungsi & diverifikasi. |
| `database/`, `research/`, `references/`, `diagram-skripsi/`, `calibration_data/` | Materi skripsi/penelitian — **tidak boleh disentuh tanpa persetujuan**. |

---

## 5. Perubahan yang TIDAK Kamiusulkan (anti-over-engineering)

- Tidak membuat folder `models/`, `schemas/`, `utils/` di `Backend/src/` secara paksa (tidak ada kebutuhan nyata; `ai/` sudah menampung domain AI, `core/` menangani utilitas server).
- Tidak membuat barrel `index.ts` untuk tiap komponen/halaman (hanya folder-based naming yang sudah dipakai).
- Tidak memakai pola `src/` di backend atau folder `components/{Feature}/index.tsx` ala LUCIT untuk komponen kecil — PIXEL-T lebih bersih dengan kategori + nama file.
- Tidak memindahkan `Frontend/src/lib` → `utils` (perlu nilai yang sudah terbukti).
- Tidak melakukan rename massal (mis. `src/` prefix) — akan mengubah puluhan import tanpa nilai tambah.

---

## 6. Ringkasan Target vs Saat Ini

| Area | Saat ini | Target proposal |
|---|---|---|
| Backend stack | `Backend/{app,ai(root),run,set_admin}` | `Backend/{app,ai,run,tools}` |
| Frontend layout | `src/{components/pages/services/lib...}`, tes di root src | +`__tests__/`, `ui/LogoPixelT.tsx`, hapus `.gitkeep` + tsbuildinfo |
| Root hygiene | laporan audit/tooling di root | laporan → `docs/reports/`, tooling → `scripts/tools/` |
| Layering | benar | tetap benar (tidak berubah) |
| AI model | `ai/` | `Backend/ai/` (path relatif checkpoint aman) |

---

## 7. Kesimpulan Awal Tahap B

Struktur PIXEL-T saat ini **relatif baik** dan lebih bersih dari LUCIT pada beberapa dimensi (factory, error handler, auth, tes). Rencana sederhana yang ditawarkan hanya menghapus **ketidakcocokan nyata** (placeholder `.gitkeep`, tes di root, brand folder satu file, tooling root, laporan root) plus **konsolidasi AI ke dalam backend** (move murni). Tidak ada reorganisasi yang menciptakan lapisan baru.

**Status:** proposal disusun; menunggu persetujuan user sebelum Tahap C (rencana eksekusi detail) & Tahap D (eksekusi bertahap).
