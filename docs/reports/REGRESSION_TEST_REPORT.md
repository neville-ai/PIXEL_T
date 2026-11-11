# REGRESSION TEST REPORT — PIXEL-T

**Tanggal:** 11 November 2026  
**Branch:** `fitur/validasi-input` (HEAD `cbb5296`)  
**Sifat:** read-only; **tidak ada refactoring yang dilakukan setelah baseline ini.**  
**Prinsip:** setiap perubahan refactor nanti harus diverifikasi ulang dan rollback via Git jika regresi.  
**Status:** BASELINE / REGRESI BELUM ADA (belum ada perubahan baru setelah baseline).

---

## 0. Ringkasan Hasil

| Suite | File | Hasil | Durasi | Perintah |
|---|---:|---|---:|---|
| pytest backend + AI | 20 file test (+1 env safety) | **190 passed, 1 skipped** | 116.63 s | `pytest tests/ ...` |
| vitest frontend | 19 file test | **298 passed, 0 failed** | 57.80 s | `npm test` |
| Build frontend | — | **Sukses** | 12.20 s | `npm run build` |
| Checkpoint model | 1 file | **SHA-256 cocok** | — | verifikasi lokal |

**Status regresi:** HIJAU pada baseline. Belum ada regresi karena belum ada refactoring baru.

---

## 1. Perintah yang Digunakan

### pytest

```powershell
.venv\Scripts\python.exe -m pytest tests/ -x `
  --ignore=tests/ai/audit_domain_validator_deep.py `
  --ignore=tests/ai/measure_real_samples_stage2.py
```

### vitest

```powershell
cd frontend
npm test
```

### Build

```powershell
cd frontend
npm run build
```

### Dependency

```powershell
.venv\Scripts\python.exe -m pip check
```

### Hash checkpoint

```powershell
Get-FileHash Backend/ai/models/PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth -Algorithm SHA256
```

---

## 2. Baseline vs Hasil Verifikasi

| Suite | Baseline dokumen lama | Hasil verifikasi 11 Nov 2026 | Delta |
|---|---:|---:|---|
| pytest | 188 passed, 1 skipped | **190 passed, 1 skipped** | +2 tes Gemini |
| vitest | 298 passed (19 file) | **298 passed (19 file)** | 0 |
| Build | sukses | **sukses** | 0 |
| Hash checkpoint | cocok | **cocok** | 0 |

**Catatan:** dokumen lama (188) berasal dari sebelum tes Gemini baru. 190 adalah baseline aktual.

---

## 3. Tes yang Diabaikan

| Tes | Alasan |
|---|---|
| `tests/ai/audit_domain_validator_deep.py` | Audit mendalam, bukan unit test |
| `tests/ai/measure_real_samples_stage2.py` | Pengukuran sampel nyata, bukan unit test |

---

## 4. Bukti Konsistensi API Contract

| Kontrak | Bukti | Hasil |
|---|---|---|
| `POST /api/analysis` — `FormData image` | `routes/analysis.py:11` vs `Frontend/src/utils/analysis.ts` | Konsisten |
| `GET /api/analysis/<id>` | `routes/analysis.py:29` vs `services/analysis.ts` | Konsisten |
| `GET /api/history` | `routes/analysis.py:45` vs `services/analysis.ts` | Konsisten |
| `DELETE /api/history/<id>` (`expectData: false`) | `routes/analysis.py:56` vs `services/analysis.ts` | Konsisten |
| Guard `require_approved_doctor` / `require_admin` | `core/auth.py` vs `components/auth/*Route.tsx` | Konsisten |
| Envelope error `{"success":false,"error":{code,message}}` | `core/errors.py` vs `services/analysis.ts` `ApiRequestError` | Konsisten |

---

## 5. Bukti Arsitektur AI Tetap Terjaga

| Item | Nilai | Bukti |
|---|---|---|
| Arsitektur | U-Net + ResNet50 (`smp.Unet`) | `Backend/ai/config/model_config.py` |
| Checkpoint SHA-256 | `46521AE9...C581` | verifikasi hash |
| Input size | 512×512 | `model_config.py:27` |
| Threshold | 0.55 | `model_config.py:29` |
| TTA | 5 skala × 5 orientasi | `model_config.py:31-32`, `segmentation.py` |
| Grad-CAM layer | `decoder.blocks.4.conv2.0` | `model_config.py:23` |
| Domain gate | heuristik → LLM fail-closed | `domain_validator.py`, `llm_image_validator.py` |
| LLM config | JSON schema + thinking low + token 1024 + timeout 30.0 | `llm_image_validator.py`, `config.py` |

---

## 6. Hasil Build

- Exit code: 0
- Durasi: 12.20 s
- Bundel JS: ~591.87 kB
- Peringatan: chunk >500 kB — non-fatal, tidak diubah.

---

## 7. Manual E2E

**Status: NOT TESTED.**

Lihat `MANUAL_E2E_TEST_PLAN.md`. Tidak ada hasil yang dikarang.

---

## 8. Kriteria Regresi untuk Perubahan Refactor

Sebelum commit setiap langkah refactor, wajib memenuhi:

1. pytest ≥190 passed, 1 skipped, 0 failed.
2. vitest ≥298 passed, 0 failed.
3. Build sukses.
4. `pip check` sukses.
5. Hash checkpoint cocok.
6. API contract tidak berubah.
7. Arsitektur AI tidak berubah.

Jika salah satu gagal, lakukan `git restore` file yang dicurigai dan ulang kembali sebelum lanjut.

---

## 9. Kesimpulan

Baseline regresi HIJAU. Tidak ada regresi baru karena refactoring implementasi belum dijalankan. Laporan ini akan diperbarui setelah setiap langkah refactor.
