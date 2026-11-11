# UNUSED FILES AUDIT — PIXEL-T

**Tanggal:** 11 November 2026  
**Branch:** `fitur/validasi-input`  
**Sumber:** `PROJECT_INVENTORY.md` (scan inventaris), `PIXELT_AUDIT_REPORT.md`, `LUCIT_ARCHITECTURE_ANALYSIS.md`, grep terverifikasi di `Frontend/src` dan `backend`.  
**Sifat:** catatan audit — **tidak ada file yang dihapus** pada fase ini. Setiap item membuktikan atau membuktikan ulang terlebih dahulu sebelum pembersihan (Fase 6).  
**Prinsip:** jangan menghapus file sebelum membuktikan tidak digunakan.

---

## 0. Ringkasan Hasil Audit

Dari inventansi total **273 file** (eksklusif `node_modules`, `.venv`, `.git`, cache, `LUCIT-master`, `calibration_data`, `references`), tidak ditemukan **file kode aplikasi yang terkonfirmasi tidak terpakai**. Kandidat pembersihan terbatas pada artefak build/log (gitignored, regenerable), folder `.gitkeep`-only, dan file tooling skripsi.

---

## 1. Kandidat Pembersihan Artefak (aman, gitignored/regenerable)

| Kandidat | Alasan | Status | Buyang? |
|---|---|---|---|
| `backend_foreground.log` | Log runtime backend di root | Kandidat | Jangan — log mungkin masih berjalan; hapus setelah konfirmasi |
| `backend_foreground_err.log` | Log error runtime backend di root | Kandidat | idem |
| `Frontend/dist/` | Hasil `npm run build` (tsc + vite) | Kandidat | Gitignored; regenerable |
| `Frontend/tsconfig.tsbuildinfo` | Cache `tsc -b` | Kandidat | Gitignored; regenerable |

**Kesimpulan:** aman dibersihkan jika file log tidak lagi digunakan oleh proses aktif; ini non-kode dan tidak berdampak runtime.

---

## 2. Folder Kosong (hanya `.gitkeep`) — kandidat konsolidasi struktural

| Folder | Keterangan | Status |
|---|---|---|
| `Backend/src/models/.gitkeep` | repo model (hanya `.gitkeep`) | Kandidat konsolidasi |
| `Backend/src/schemas/.gitkeep` | schema (hanya `.gitkeep`) | Kandidat konsolidasi |
| `Backend/src/utils/.gitkeep` | util backend (hanya `.gitkeep`) | Kandidat konsolidasi |
| `database/seed/.gitkeep` | seed DB (hanya `.gitkeep`) | Kandidat konsolidasi |
| `Backend/ai/config/.gitkeep` | config AI (hanya `.gitkeep`) | Kandidat konsolidasi |
| `Backend/ai/inference/.gitkeep` | inference (hanya `.gitkeep`) | Kandidat konsolidasi |
| `Backend/ai/models/.gitkeep` | models AI (hanya `.gitkeep` + checkpoint gitignored) | **Jangan** — penanda checkpoint |
| `Frontend/src/components/analysis/.gitkeep` | (kosong) | Kandidat konsolidasi |
| `Frontend/src/components/history/.gitkeep` | (kosong) | Kandidat konsolidasi |
| `Frontend/src/components/layout/.gitkeep` | AppShell ada di luar folder ini | Kandidat konsolidasi |
| `Frontend/src/components/ui/.gitkeep` | ui diisi (tidak kosong) | Bukan kandidat |
| `Frontend/src/hooks/.gitkeep` | hooks ada di luar folder ini | Kandidat konsolidasi |
| `Frontend/src/pages/analysis/.gitkeep` | halaman diisi | bukan |
| `Frontend/src/routes/.gitkeep` | routes diisi | bukan |
| `Frontend/src/types/.gitkeep` | types kosong | Kandidat isi/hapus |
| `Frontend/src/utils/.gitkeep` | utils kosong | Kandidat isi/hapus |
| `scripts/deployment/.gitkeep` | (tidak terlihat di inventory langsung) | — |
| `scripts/setup/.gitkeep` | (tidak terlihat di inventory langsung) | — |
| `database/migrations/.gitkeep` | migrasi diisi | bukan |

**Kesimpulan:** 10+ folder `.gitkeep`-only. Tidak ada file di dalamnya; konsolidasi dapat dilakukan Fase 6 tanpa risiko perilaku, asalkan path impor tidak merujuk ke folder tersebut (belum diverifikasi).

---

## 3. File Potensi Tidak Digunakan (perlu pembuktian lebih lanjut)

| Kandidat | Alasan awal | Bukti awal | Penilaian |
|---|---|---|---|
| `Frontend/src/utils/auth.ts` — `getCurrentUser` | Diekspor (`auth.ts:284`, sebelum cleanup) | Subagent eksplorasi tidak menemukan pemanggil di `Frontend/src` | **Terbukti tidak terpakai dan dihapus** pada cleanup |
| `tests/Frontend/test_frontend_env_safety.py` | Satu-satunya test Python "frontend" | Memeriksa `ROOT_DIR / ".env.example"` | Terpakai (test keamanan env); **pertahankan** |
| `test_field.puml`, `test_field.svg`, `test_render.mjs` | Artefak uji render di root | File skrip uji diagram | Kandidat archive (Langkah 1 R1 — ditunda karena risiko path) |
| `generate_bab4.js`, `rasterize_erd.py`, `rasterize_svg.js`, `render_erd.mjs` | Tooling skripsi di root | Berada di root; `generate_bab4.js` pakai `path.join(__dirname, 'references', 'bab 4')` | **Pindah ke archive** menyisakan risiko path; perlu penyesuaian path sebelum dijalankan ulang |

---

## 4. Dokumen Duplikat (pasangan `.md` / `.txt`) — pertahankan

| Pasangan | Lokasi | Penilaian |
|---|---|---|
| `APIContract.md` / `.txt` | `docs/` | Artefak skripsi; pertahankan |
| `StyleGuide.md` / `.txt` | `docs/` | Artefak skripsi; pertahankan |
| `DataModelSpecification.md` / `.txt` | `docs/` | Artefak skripsi; pertahankan |
| `ADMIN_DASHBOARD_AND_APPROVE_FORENSIC_REPORT.md` / `.txt` | `docs/` | Artefak skripsi; pertahankan |

**Kesimpulan:** semua dipertahankan sampai konfirmasi tim skripsi.

---

## 5. File yang DILINDUNGI (dilarang dihapus/diubah)

| Kelompok | File/Folder |
|---|---|
| Model & inferensi | `Backend/ai/models/PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth` (+ SHA-256), `Backend/ai/config/model_config.py`, seluruh `Backend/ai/inference/*` |
| Database | seluruh `database/migrations/*.sql`, `verify_doctor_registration.sql` |
| Auth & keamanan | `Backend/src/core/auth.py`, `Backend/src/core/supabase.py`, `.env` (BE & FE, gitignored), `.env.example` (root, tidak dihapus) |
| API contract | `Backend/src/routes/*`, `Backend/src/controllers/*`, `Frontend/src/utils/*` |
| Domain Validation | `Backend/ai/inference/domain_validator.py`, `llm_image_validator.py`, gate di `analysis_service.py` |
| Tests | seluruh `tests/**` dan `Frontend/src/**/*.test.*` |
| Artefak penelitian | `research/*`, `scripts/output/*`, `calibration_data/*`, `references/*`, `LUCIT-master/` |
| Dokumen skripsi | `docs/PRD_PIXEL-T_FINAL.md`, `docs/StyleGuide.md`, `docs/FunctionalSpecification.md`, `docs/APIContract.md`, `docs/DataModelSpecification.md`, `docs/ModelIntegrationSpecification.md`, `diagram-skripsi/*` |
| Entry & build | `Backend/run.py`, `Frontend/src/main.tsx`, `Frontend/src/App.tsx`, `Frontend/src/routes/AppRoutes.tsx`, `Frontend/vite.config.ts`, `Frontend/tsconfig.json`, `Frontend/tailwind.config.js`, `Frontend/postcss.config.js`, `Frontend/index.html` |

---

## 6. Rekomendasi Pembersihan Fase 6

| Prioritas | Aksi | Risiko | Bukti yang wajib dicek |
|---|---|---|---|
| 1 | Bersihkan `backend_foreground*.log` (jika proses backend tidak aktif) | Rendah | Konfirmasi tidak ada proses yang menulis log |
| 2 | Biarkan `Frontend/dist/` & `tsconfig.tsbuildinfo` (gitignored, regenerable) | Rendah | `npm run build` sukses |
| 3 | Konsolidasikan folder `.gitkeep`-only atau biarkan | Rendah | Cek impor dinamis tidak merujuk path folder ini |
| 4 | Hapus `getCurrentUser` dari `auth.ts` — **SELESAI (cleanup)** | Rendah | Grep menyeluruh: tidak ada pemanggil di `Frontend/src` |
| **Status** | **Dihapus** pada cleanup; grep menyeluruh di seluruh root tidak menemukan pemanggil. | | |
| 5 | Archive skrip diagram | Sedang | Penyesuaikan path `generate_bab4.js` (`__dirname`) terlebih dahulu |
| 6 | Hapus duplikat dokumen `.txt` | N/A (artefak skripsi) | Konfirmasi tim skripsi — **jangan** tanpa persetujuan |

**Kesimpulan sementara:** tidak ada file aplikasi yang terkonfirmasi tidak terpakai. Pembersihan terbatas pada artefak build/log dan kandidat struktural dengan pembuktian referensi.
