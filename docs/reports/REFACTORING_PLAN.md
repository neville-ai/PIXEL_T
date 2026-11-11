# REFACTORING PLAN — PIXEL-T

**Tanggal:** 11 November 2026  
**Branch:** `fitur/validasi-input`  
**HEAD:** `cbb5296`  
**Status:** **RENCANA — DIEKSEKUSI (sesuai persetujuan pengguna 11 Nov 2026).** Tahap 7 dimulai dengan urutan **0 → 1 → 2 → 5** saja; Langkah 3 (split `analysis_service.py`), Langkah 4 (archive tooling diagram), dan rapikan `scripts/` **ditunda**.  
**Dasar:** `PIXELT_STRUCTURE_AUDIT.md`, `CODE_SIMPLIFICATION_AUDIT.md`, `APPLICATION_FLOW_AUDIT.md`, `TARGET_PROJECT_STRUCTURE.md`, baseline test.  
**Prinsip:** safety > functionality > correctness > maintainability > simplicity.  
**Larangan:** jangan commit/push, hapus, pindah, atau refactor sebelum persetujuan eksplisit.

---

## 0. Baseline yang Dikunci

| Item | Baseline | Status |
|---|---|---|
| pytest | **190 passed, 1 skipped** (116.63 s) | Lulus |
| vitest | **298 passed, 19 file** (57.80 s) | Lulus |
| Build frontend | **Sukses** (12.20 s; warning chunk >500 kB non-fatal) | Lulus |
| `pip check` | **No broken requirements** | Lulus |
| Hash checkpoint | **`46521AE9...C581`**, 135.644.553 B | Cocok |
| API contract | Tidak berubah | Terverifikasi |
| Manual E2E | **NOT TESTED** | Belum dijalankan |

**Aturan:** setiap langkah di bawah harus dimulai dari baseline ini dan diakhiri dengan regresi yang sama atau lebih baik.

---

## 1. Gerbang Persetujuan

Refactoring **tidak boleh dimulai** sebelum:

1. Pengguna menyetujui ruang lingkup dan urutan langkah.
2. Baseline test dianggap sah.
3. Rencana rollback dipahami.
4. File yang dilindungi disepakati (lihat `TARGET_PROJECT_STRUCTURE.md`).
5. Manual E2E dijadwalkan (boleh sesudah refactor, tetapi sebelum commit final).

**Status saat ini: DISETUJUI** (subset Tahap 7: Langkah 0–2 dan 5; Langkah 3/4/scripts ditunda). Tanpa persetujuan eksplisit, pekerjaan berhenti sebelum langkah berikutnya.

---

## 2. Urutan Langkah

### Langkah 0 — Sinkronisasi laporan (dokumentasi saja)

**Tujuan:** memastikan 13 laporan konsisten, tidak ada klaim yang bertentangan.  
**File:** laporan `.md` di root; tidak menyentuh source.  
**Tindakan:** perbaiki angka baseline, status cleanup, dan daftar file.  
**Risiko:** sangat rendah.  
**Verifikasi:** review manual; tidak ada test kode yang terpengaruh.  
**Rollback:** git checkout laporan.

---

### Langkah 1 — Low-risk backend consistency

**Tujuan:** mengurangi duplikasi tanpa mengubah perilaku.

| Sub-langkah | File | Perubahan yang diusulkan | Risiko |
|---|---|---|---|
| 1A | `Backend/src/core/auth.py` | Ekstrak helper parsing Bearer token; ketiga decorator memakainya | Rendah |
| 1B | `Backend/src/controllers/admin_controller.py` | Samakan envelope error dengan handler global | Sedang |
| 1C | `Backend/src/services/analysis_service.py` | Ganti `print` korelasi/timing dengan logger/helper | Rendah |

**Syarat 1A:** pesan error, status code, dan urutan validasi **identik**.  
**Syarat 1B:** cek `Frontend/src/pages/admin/AdminDashboard.tsx` dan test; jangan mengubah kontrak jika client bergantung pada bentuk lama.  
**Syarat 1C:** tidak mengubah alur; correlation ID tetap.

**Test:**
```powershell
.venv\Scripts\python.exe -m pytest tests/Backend/test_auth.py tests/Backend/test_admin_routes.py tests/Backend/test_admin_service.py tests/Backend/test_analysis.py -x
```

**Kriteria lulus:** semua tes backend lulus; envelope admin teruji; tidak ada error baru.

---

### Langkah 2 — Frontend resiliency

**Tujuan:** mencegah polling tanpa henti; tidak mengubah UI/route/API.

| Sub-langkah | File | Perubahan | Risiko |
|---|---|---|---|
| 2A | `Frontend/src/pages/analysis/NewAnalysis.tsx` | `PROGRESS_POLL_MAX_ATTEMPTS = 300` (~10 menit @2 s); pemisahan error server/timeout/jaringan; berhenti saat batas/unmount | **Selesai (Langkah 2)** |
| 2B | `Frontend/src/pages/analysis/NewAnalysis.tsx` | Ekstrak komponen dropzone/preview/progress | Sedang |
| 2C | `Frontend/src/pages/profile/DoctorProfile.tsx` | Ekstrak form/avatar/modal bila diperlukan | Sedang |
| 2D | `Frontend/src/pages/history/History.tsx`, `AdminDashboard.tsx` | Ekstrak list row/stat/table | Sedang |

**Syarat:** teks, DOM, class Tailwind, route, dan kontrak API tidak berubah.

**Test:**
```powershell
cd frontend
npm test
npm run build
```

**Kriteria lulus:** vitest 298+ lulus, build sukses, tidak ada perubahan perilaku yang tidak disetujui.

---

### Langkah 3 — Pemecahan `AnalysisService` (risiko tinggi)

**Tujuan:** memecah 1147 baris (1029 baris non-kosong) menjadi modul internal tanpa mengubah API/nama publik.

**Rencana modul:**

```text
Backend/src/services/analysis/
├── __init__.py          # re-export AnalysisService
├── service.py           # facade AnalysisService
├── progress.py          # AnalysisProgressReporter
├── queue.py             # AnalysisJobQueue
├── validation.py        # validate + domain/LLM gate
├── pipeline_runner.py   # _execute_pipeline + upload artifact
└── queries.py           # get/list/delete
```

**Yang tidak boleh berubah:**
- Signature `AnalysisService`, `AnalysisJobQueue`, `AnalysisProgressReporter`.
- Urutan langkah upload → gate → storage → DB → queue.
- Error code (`NOT_COLONOSCOPY_IMAGE`, `UNCERTAIN...`, `STORAGE_ERROR`, `DATABASE_ERROR`, `QUEUE_FULL`).
- Status lifecycle `processing/completed/failed`.
- Progress unit dan `100%` hanya saat `completed`.
- Semua nama kelas yang disebut di skripsi.

**Test wajib:**
```powershell
.venv\Scripts\python.exe -m pytest tests/ -x --ignore=tests/ai/audit_domain_validator_deep.py --ignore=tests/ai/measure_real_samples_stage2.py
```
Plus manual E2E upload/poll/history/delete.

**Kriteria lulus:** 190 passed/1 skipped, tidak ada regresi; review kode oleh pemilik proyek.

**Rollback:** `git restore` seluruh folder service; karena perubahan belum di-commit, rollback langsung.

---

### Langkah 4 — Cleanup/arsip terbatas

| Sub-langkah | Perubahan | Risiko | Syarat |
|---|---|---|---|
| 4A | Hapus sisa `.gitkeep` yang terbukti redundan | Rendah | grep path/impor |
| 4B | Bersihkan `dist/`, `tsconfig.tsbuildinfo`, `.pytest_cache`, log | Rendah | pastikan tidak ada proses aktif |
| 4C | Archive tooling diagram ke `_archive/diagram_tools/` | Sedang | perbaiki path `__dirname` + render test |
| 4D | Rapikan `scripts/` ke subfolder | Tinggi | buktikan import/path tetap; **opsional** |

**4A–4B** aman secara fungsional; **4C–4D** tidak boleh dijalankan tanpa bukti.

**Test:** build, pytest, render diagram, skrip kalibrasi (jika 4D).

---

### Langkah 5 — Regresi penuh dan validasi manual

| Pemeriksaan | Perintah/aksi |
|---|---|
| pytest | `pytest tests/ ...` (190/1) |
| vitest | `npm test` (298/19) |
| build | `npm run build` |
| dependency | `pip check` |
| hash | SHA-256 checkpoint |
| API contract | bandingkan route/FE |
| AI config | threshold 0.55, TTA, Grad-CAM, checkpoint |
| Manual E2E | login, upload valid, tolak non-kolonoskopi, LLM uncertain, hasil, history, delete, admin |

**Status manual:** **NOT TESTED** sampai benar-benar dijalankan.

---

## 3. Matriks Risiko

| Langkah | Risiko | Dampak | Mitigasi |
|---|---|---|---|
| 0 | Sangat rendah | Dokumentasi | Review |
| 1A | Rendah | Auth | Test auth |
| 1B | Sedang | Kontrak admin/FE | Cek client + test |
| 1C | Rendah | Logging | Test backend |
| 2A | Sedang | UX polling | Test UI |
| 2B–2D | Sedang | UI/DOM | Test + review visual |
| 3 | Tinggi | Upload/pipeline/DB | Regresi penuh + manual E2E |
| 4A–4B | Rendah | Artefak | Gitignored |
| 4C–4D | Sedang–tinggi | Tooling/skrip | Path fix + render test |
| 5 | — | Validasi | Checklist |

---

## 4. Rollback

- Semua perubahan belum di-commit; rollback via `git restore <path>` atau `git checkout -- <path>`.
- File baru (laporan/template) dapat dihapus manual jika disetujui.
- Jangan `git reset --hard`, `git clean -fd`, atau force push tanpa persetujuan.
- Untuk pemecahan `AnalysisService`, rollback folder `services/analysis/` dan kembalikan `analysis_service.py` dari git.

---

## 5. Definition of Done

Refactoring dinyatakan selesai hanya jika:

1. Tidak ada perubahan API contract, DB schema/RLS, auth, atau AI/ML.
2. pytest ≥190 passed, 1 skipped, 0 failed.
3. vitest ≥298 passed, 0 failed.
4. Build sukses.
5. `pip check` sukses.
6. Hash checkpoint cocok.
7. Manual E2E dijalankan dan dicatat (bukan “NOT TESTED”).
8. `git status` hanya berisi perubahan yang disetujui.
9. `.env` tidak ter-track.
10. Laporan `FINAL_PROJECT_AUDIT.md` diperbarui.

---

## 6. Keputusan yang Diminta dari Pengguna

| No | Keputusan | Keputusan pengguna |
|---|---|---|
| 1 | Setujui refactor dimulai? | **Ya** — hanya subset yang disebut |
| 2 | Urutan langkah | **0 → 1 → 2 → 5** |
| 3 | Langkah 3 (`AnalysisService`) | **Tunda** — split AnalysisService ditunda (risiko tinggi) |
| 4 | Archive tooling diagram | **Tunda** — `generate_bab4.js` / `references/bab 4` tidak dipindah |
| 5 | Rapikan `scripts/` | **Nanti** — jangan memindah/hapus skrip di `scripts/` |
| 6 | Manual E2E | **Sebelum commit**, setelah refactoring yang disetujui |
| 7 | Commit/push | **Belum diizinkan** — butuh persetujuan terpisah |

**Tanpa jawaban eksplisit, pekerjaan berhenti di sini.** (Langkah 0 — sinkronisasi dokumentasi — sedang dikerjakan.)
