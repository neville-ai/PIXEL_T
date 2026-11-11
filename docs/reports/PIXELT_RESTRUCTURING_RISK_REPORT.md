# PIXELT_RESTRUCTURING_RISK_REPORT

**Tanggal:** 11 November 2026
**Mode:** Penilaian risiko (Tahap C) — **belum ada perubahan source code, folder, atau file**.
**Status:** Menunggu persetujuan user sebelum Tahap D (eksekusi bertahap).

---

## 1. Ringkasan

Rencana restrukturisasi yang diusulkan bersifat **konsolidasi dan pemindahan file**, bukan penulisan ulang logika. Risiko terbesar bukan pada perubahan kode aplikasi (hampir tidak ada), melainkan pada:

1. **Import path** setelah `ai/` dipindah dan `LogoPixelT` di-relokasi.
2. **Path relatif tooling** (`generate_bab4.js`) dan `?raw` test.
3. **Dokumentasi** yang terpindah/hapus (non-runtime, tetapi bisa memengaruhi jejak audit skripsi).
4. **Verifikasi ulang model checkpoint** setelah lokasi berubah (risiko operasional).

Fitur inti (login, role, Supabase, API, upload, domain/Gemini validation, U-Net+ResNet50, checkpoint, preprocessing, TTA, threshold 0.55, Grad-CAM, Dice/IoU, history, UI) **tidak disentuh** oleh rencana ini.

---

## 2. Register Risiko

| ID | Risiko | Peluang | Dampak | Mitigasi | Verifikasi |
|---|---|---|---|---|---|
| R-01 | `ai/` → `Backend/ai/` membuat `from ai...` gagal di satu jalur eksekusi | Rendah | Tinggi | `Backend/run.py` dan `tests/conftest.py` sudah menambahkan `Backend/` ke `sys.path`; verifikasi manual `python -c "import ai..."` dari backend. | `pytest tests/backend`, `pytest tests/ai`, jalankan `Backend/run.py` (import app) |
| R-02 | Checkpoint path berubah karena `parents[1]` | Rendah | Tinggi | `checkpoint_path()` relatif `ai/models`; pindah `ai/` sebagai satu unit termasuk `models/`. | Bandingkan SHA-256 (`46521AE9...`), pastikan `checkpoint_sha256_matches()` True |
| R-03 | Import `LogoPixelT` rusak di 3 pemakai | Rendah | Rendah | Update ketiga impor ke `@/components/ui/LogoPixelT`; grep ulang. | Vitest full + build |
| R-04 | `statusText.contrast.test.tsx` gagal karena path `?raw` | Sedang | Rendah | Sesuaikan `'../tailwind.config.js?raw'` → `'../../tailwind.config.js?raw'`. | Vitest file terkait |
| R-05 | `generate_bab4.js` gagal setelah tooling dipindah | Sedang | Rendah | Sesuaikan `__dirname` relatif ke `references/bab 4`. | Jalankan script manual |
| R-06 | `.gitkeep` dihapus menyebabkan folder "hilang" dari Git | Rendah | Rendah | Semua folder tujuan berisi file nyata; Git melacak folder berisi file. | `git status` setelah eksekusi |
| R-07 | Memindahkan laporan audit membuat referensi lama tidak ditemukan | Rendah | Rendah | Pindah, bukan hapus; perbarui referensi internal bila perlu. | Pemeriksaan dokumentasi |
| R-08 | Menghapus `.txt` duplikat menghilangkan informasi unik | Sedang | Sedang | **Wajib diff isi** `.md` vs `.txt`; jika ada perbedaan, jangan hapus (merge manual). | Review diff sebelum hapus |
| R-09 | `analysis_service.py` displit dan mengubah perilaku | Tinggi | Tinggi | **Dilabeli ditunda**; membutuhkan approval terpisah + regresi penuh + manual E2E. | Tidak dijadwalkan pada Tahap D awal |
| R-10 | Ekstraksi komponen halaman mengubah UI/DOM | Sedang | Sedang | Ditunda; perlu tes UI + snapshot perilaku. | Tidak dijadwalkan pada Tahap D awal |
| R-11 | Perubahan yang tidak sengaja terjadi pada LUCIT-master | Rendah | Tinggi | Hanya membaca; verifikasi `LUCIT-master` tidak muncul di `git status` (folder referensi tetap utuh). | `git status` sebelum/sesudah |
| R-12 | Konflik dengan pekerjaan manual pengguna di working tree | Sedang | Sedang | Working tree saat ini berisi perubahan pre-existing (Langkah 0–2). Jangan reset/checkout global; hanya sentuh file rencana. | `git diff` per file sebelum eksekusi |

---

## 3. Zona yang Tidak Boleh Disentuh (Hard Constraints)

| Area | Alasan |
|---|---|
| `Backend/ai/models/*.pth` (isi) | Checkpoint model; SHA-256 `46521AE90D12F57F77A7B9921881910B41071DBBB1EFF4D2172A2C437564C581`. |
| `Backend/ai/inference/*`, `Backend/ai/config/*` (logika) | Preprocessing, TTA, threshold 0.55, Grad-CAM, model loading. |
| Autentikasi (`core/auth.py`, `AuthContext.tsx`, route guards) | Login, role, permission, session. |
| Supabase / DB (migrasi, RLS) | Keamanan dan data. |
| API contract & endpoint | Frontend & dokumentasi bergantung. |
| `references/`, `research/`, `diagram-skripsi/`, `calibration_data/` | Materi skripsi/penelitian. |
| `LUCIT-master/` | Referensi, tidak boleh diubah. |

---

## 4. Rencana Mitigasi per Fase

### Fase 1 — Backend
- Buat baseline verifikasi **sebelum** eksekusi (pytest penuh, hash checkpoint).
- Pindahkan `ai/` sebagai satu operasi, lalu langsung uji impor:
  ```powershell
  .venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'backend'); from ai.config.model_config import MODEL_CONFIG; print(MODEL_CONFIG.checkpoint_path()); print(MODEL_CONFIG.checkpoint_sha256_matches())"
  ```
- Jalankan `pytest tests/ai tests/backend`.
- Jika ada kegagalan impor: rollback move `ai/` dan hentikan (jangan lanjut fase berikutnya).

### Fase 2 — Frontend
- Grep ulang `components/brand` dan `statusText` setelah edit.
- Jalankan tes file terkait dulu, lalu full vitest, lalu build.

### Fase 3 — Root/Docs/Tooling
- Tooling: jalankan script setelah path fix; verifikasi tidak ada error path.
- Docs: pindah (bukan hapus) terlebih dahulu; hapus `.txt` hanya setelah diff manual menunjukkan isi sama.
- Root `.md` yang aktif dirujuk oleh proses kerja (mis. `REFACTORING_PLAN.md`) dipindah terakhir agar alur tidak terganggu.

### Fase 4 — Ditunda
- Tidak dieksekusi pada tahap ini. Wajib persetujuan terpisah + rencana tes detail (termasuk manual E2E untuk UI).

---

## 5. Matriks Verifikasi Wajib (gate per fase)

| Gate | Perintah | Kriteria lulus |
|---|---|---|
| Backend tests | `.venv\Scripts\python.exe -m pytest tests/ -q` | 190 passed, 1 skipped |
| AI tests | `.venv\Scripts\python.exe -m pytest tests/ai -q` | semua passed |
| Frontend tests | `cd frontend; npx vitest run` | 302 passed, 19 file |
| Build | `cd frontend; npm run build` | exit 0 |
| Dependency check | `.venv\Scripts\python.exe -m pip check` | no broken requirements |
| Checkpoint hash | skrip hash / `checkpoint_sha256_matches()` | `46521AE9...` cocok |
| Struktur | `git status`, `git diff` | hanya file yang direncanakan berubah |
| LUCIT untouched | `git status` (tidak ada entri di `LUCIT-master/`) | tidak ada perubahan |

---

## 6. Rollback Plan

1. **Tanpa commit**: semua perubahan bisa dikembalikan per file/folder dengan `git checkout -- <path>` (untuk file tracked) atau dengan memindahkan balik folder (untuk move yang belum di-stage).
2. **Per fase**: jika verifikasi fase gagal, hentikan dan rollback fase tersebut sebelum lanjut.
3. **Tidak ada** operasi destruktif tanpa backup (tidak ada `git reset --hard`, tidak ada `git clean -fd`).
4. **Manual E2E** tetap `NOT TESTED` sampai dijalankan; commit/push belum diizinkan.

---

## 7. Risiko Sisa Setelah Seluruh Fase (jika disetujui)

1. **Split `analysis_service.py`** tetap belum dilakukan → god service tetap ada (risiko maintainability tinggi, tetapi terkontrol oleh tes).
2. **Halaman frontend besar** (DoctorProfile, NewAnalysis, History) tetap belum dipecah.
3. **Manual E2E** belum dijalankan → klaim fungsional hanya didukung tes otomatis.
4. **Dokumentasi** yang dipindah/dikonsolidasi tetap memerlukan verifikasi manual pembaca.

---

## 8. Kesimpulan Risiko

Rencana Fase 1–3 **rendah–sedang** dan dapat dieksekusi bertahap dengan gate verifikasi yang jelas. Satu-satunya perubahan yang menyentuh jalur eksekusi runtime adalah pemindahan `ai/` (Fase 1.1) — sudah dianalisis aman karena mekanisme `sys.path` dan path checkpoint relatif. Fase 4 (split service & komponen) berisiko tinggi dan **tetap ditunda** sampai persetujuan terpisah.

**Status:** laporan risiko selesai; berhenti menunggu review dan persetujuan user.
