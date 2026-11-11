# CLEANUP REPORT — PIXEL-T

**Tanggal:** 11 November 2026
**Branch:** `fitur/validasi-input` (HEAD `cbb5296`)
**Status:** cleanup tahap 1–6 **selesai** (perubahan di working tree, **belum di-commit**)
**Sifat:** laporan hasil tahap cleanup. Tidak ada file runtime yang dihapus kecuali placeholder/kandidat bersih yang sudah diverifikasi.

---

## 0. Ringkasan Eksekutif

Tahap cleanup berdasarkan `POST_AUDIT_REVIEW.md` dan persetujuan user dilaksanakan kelompok per kelompok
(artefak → `.gitkeep`-only → `getCurrentUser` → timeout fetch frontend → fallback LLM timeout → upper bound
`google-genai`) tanpa perubahan arsitektur, AI/ML, perilaku model, API contract, DB schema, auth, Supabase RLS,
atau alur utama aplikasi.

**Hasil regresi akhir:**

| Suite | Hasil |
|---|---|
| pytest (Backend + AI) | **190 passed, 1 skipped** (89.71 s) |
| Vitest (Frontend) | **298 passed, 19 file** (43.10 s) |
| Production build | **Sukses** (`tsc -b && vite build`) |
| Dependency check | **Sukses** (`pip check` → no broken requirements) |
| Model checkpoint | **SHA-256 cocok**: `46521AE90D12F57F77A7B9921881910B41071DBBB1EFF4D2172A2C437564C581`; size 135.644.553 B |

**KESIMPULAN CLEANUP: BERHASIL TANPA REGRESI.** Cleanup selesai; commit/push menunggu persetujuan eksplisit user.

---

## 1. File yang Dihapus

### 1.1 Folder / file placeholder (`.gitkeep`-only) — 10 file

Hanya folder-folder kosong (tanpa item lain) yang dihapus beserta `.gitkeep`-nya:

| # | Path |
|---|---|
| 1 | `Backend/src/models/.gitkeep` |
| 2 | `Backend/src/schemas/.gitkeep` |
| 3 | `Backend/src/utils/.gitkeep` |
| 4 | `database/seed/.gitkeep` |
| 5 | `Frontend/src/components/analysis/.gitkeep` |
| 6 | `Frontend/src/components/history/.gitkeep` |
| 7 | `Frontend/src/types/.gitkeep` |
| 8 | `Frontend/src/utils/.gitkeep` |
| 9 | `scripts/deployment/.gitkeep` |
| 10 | `scripts/setup/.gitkeep` |

**Tidak disentuh:** `Backend/ai/models/.gitkeep` (folder berisi checkpoint), `database/migrations/` (berisi migrasi), folder
lain yang masih memuat file lain.

### 1.2 Artefak build/cache/log (tidak ter-track, gitignored) — dihapus

- `backend_foreground.log`
- `backend_foreground_err.log`
- `.pytest_cache/` (root)
- `Frontend/dist/`
- `Frontend/tsconfig.tsbuildinfo`

### 1.3 Catatan
- **Tidak ada** file skripsi, notebook training, dataset, checkpoint, model, `calibration_data`, `references`, skrip
  diagram, artefak eksperimen yang dihapus.

---

## 2. File yang Diubah

| # | File | Perubahan | Kelompok |
|---|---|---|---|
| 1 | `Backend/src/core/config.py` | `LLM_VALIDATION_TIMEOUT_S` default `15.0` → `30.0` | pra-cleanup |
| 2 | `Backend/src/services/llm_image_validator.py` | Konfigurasi Gemini: JSON `response_schema`, tanpa `temperature`, `thinking_config` low, `max_output_tokens=1024`, retry attempts 1, timeout 30 s | pra-cleanup |
| 3 | `Backend/requirements.txt` | + `google-genai>=3.0.0` → `google-genai>=3.0.0,<3.1.0` | cleanup (6) |
| 4 | `tests/Backend/test_llm_image_validator.py` | Tes timeout di-update (15000→30000) + 2 tes baru | pra-cleanup |
| 5 | `README.md` | Dokumentasi prasyarat/instalasi/arsitektur | pra-cleanup |
| 6 | `Backend/src/services/analysis_service.py` | Fallback LLM `timeout_s = 15.0` → `30.0` | cleanup (5) |
| 7 | `Frontend/src/utils/analysis.ts` | Timeout fetch via `AbortController` + `ApiRequestError('REQUEST_TIMEOUT', ...)`; `createAnalysis` timeout 90 s | cleanup (4) |
| 8 | `Frontend/src/utils/auth.ts` | Hapus fungsi tidak terpakai `getCurrentUser` | cleanup (3) |

### 2.1 Ringkasan dampak

- **Backend:** konsistensi nilai timeout LLM (`30.0`) terjaga; fail-closed dan urutan heuristik → Gemini gate tidak berubah.
- **Frontend:** request API kini punya batas waktu (default 30 s; upload 90 s) dengan abort yang benar; timeout
  dikategorikan sebagai `REQUEST_TIMEOUT`, bukan kesalahan autentikasi.
- **Dependency:** SDK `google-genai` dibatasi pada minor `3.0.x` sesuai versi teruji (`3.0.0`).

---

## 3. Hasil Pengujian Setiap Tahap

| Tahap | Perubahan | Hasil |
|---|---|---|
| 1 | Hapus artefak log/cache/build | `pytest tests/backend`: **145 passed, 1 skipped** |
| 2 | Hapus folder `.gitkeep`-only | `pytest tests/backend`: **145 passed, 1 skipped**; vitest **298 passed**; build **sukses** |
| 3 | Hapus `getCurrentUser` | vitest **298 passed**; build **sukses** |
| 4 | Implementasi timeout fetch | build **sukses**; vitest **298 passed** |
| 5 | Konsolidasi fallback LLM timeout | `pytest tests/backend`: **145 passed, 1 skipped** |
| 6 | Upper bound `google-genai` | `pip check`: **no broken requirements**; SDK `3.0.0` terpasang cocok |

**Regresi akhir:** pytest penuh **190 passed, 1 skipped** (89.71 s pada run tahap cleanup); vitest **298 passed** (19 file, 43.10 s); production
build **sukses**; `pip check` **sukses**; SHA-256 checkpoint **cocok**. Baseline akhir pada 11 Nov 2026: pytest **190 passed, 1 skipped** (116.63 s), vitest **298 passed** (19 file, 57.80 s) — konsisten dengan kelulusan di atas.

---

## 4. Perbandingan Hasil Regresi Sebelum dan Sesudah Cleanup

- **Sebelum cleanup:** pytest 190 passed / 1 skipped; vitest 298 passed; build sukses; hash `46521AE9…B581`.
- **Sesudah cleanup:** pytest 190 passed / 1 skipped; vitest 298 passed; build sukses; hash `46521AE9…B581`.
- **Tidak ada perubahan hasil regresi.** Perubahan cleanup bersifat non-destruktif terhadap perilaku runtime yang
  diuji otomatis.

---

## 5. Risiko yang Masih Tersisa

1. Archive skrip diagram (`generate_bab4.js` bergantung path `__dirname + 'references/bab 4'`) — ditunda.
2. Batas versi `google-genai>=3.0.0,<3.1.0` masih memungkinkan patch `3.0.x` di masa depan.
3. Polling di `NewAnalysis` belum memiliki batas maksimum eksplisit (perubahan tidak dilakukan pada tahap ini).
4. Konsistensi antar-dokumen (minor) — **selesai pada Langkah 0 audit (11 Nov 2026)**: laporan diselaraskan dan diverifikasi.
5. Uji live end-to-end (Supabase + Gemini + upload → gate → storage → worker → polling → riwayat) belum dilakukan.

---

## 6. Pekerjaan yang Sengaja Ditunda

- Commit / push (wajib persetujuan eksplisit user).
- Archive skrip diagram ke `_archive/diagram_tools/`.
- Uji manual end-to-end pada lingkungan nyata.

---

## 7. Kesimpulan

Cleanup tahap ini **selesai tanpa regresi**: pytest, vitest, build, dependency check, dan hash checkpoint semuanya
hijau; tidak ada file proyek kritikal yang dihapus; tidak ada perubahan di luar scope cleanup; tidak ada staging/commit.

---

## 8. Hasil Verifikasi Final (sesi final)

1. `CLEANUP_REPORT.md` — file belum ada sebelum sesi ini; laporan ini dibuat sebagai penyempurnaan agar mencerminkan
   kondisi aktual.
2. Implementasi final `fetchWithTimeout` di `Frontend/src/utils/analysis.ts`: **satu** deklarasi `timerId`, `clearTimeout`
   di `finally`, `AbortController`, dan error timeout menghasilkan `ApiRequestError` ber-kode `REQUEST_TIMEOUT` (bukan
   error autentikasi). **Benar.**
3. Penghapusan 10 file `.gitkeep` hanya berupa placeholder; struktur direktori aplikasi/deployment tidak
   merujuknya (sudah diverifikasi via grep statis & dinamis). **Benar.**
4. `git diff --name-status`: hanya file dalam scope cleanup; tidak ada perubahan di luar scope. **Benar.**
5. `Backend/src/services/analysis_service.py`: fallback timeout konsisten `30.0`. **Benar.**
6. `Backend/requirements.txt`: satu deklarasi `google-genai>=3.0.0,<3.1.0`. **Benar.**
7. `.env`: tidak ter-track; `Backend/.env` & `Frontend/.env` di-ignore; hanya `.env.example` yang ter-track.
   **Benar.**
8. Checkpoint & protected paths (AI/ML, DB, auth, API contract) tidak berubah. **Benar.**

---

## 9. Kesimpulan Akhir

**KESIMPULAN: PIXEL-T SUDAH AMAN — cleanup berhasil tanpa regresi.**

- Daftar file modified / deleted / untracked, ringkasan perubahan, hasil tes, dan risiko tersisa: lihat bagian 1–8.
- Status staging: **kosong**; commit: **belum**; push: **belum**.
- Langkah berikutnya yang disarankan: **uji manual end-to-end** (login/auth, upload endoskopi, penolakan non-kolonoskopi,
  validasi Gemini, segmentasi Dice/IoU, Grad-CAM, riwayat + hapus, alur Supabase/Gemini nyata) sebelum commit.

**JANGAN lakukan commit, push, archive skrip diagram, atau hapus file pada tahap ini tanpa persetujuan eksplisit user.**
