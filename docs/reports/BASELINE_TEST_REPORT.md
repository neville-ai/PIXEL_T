# BASELINE TEST REPORT — PIXEL-T

**Tanggal:** 11 November 2026  
**Branch:** `fitur/validasi-input` (HEAD `cbb5296`)  
**Tujuan:** mengunci kondisi awal sebelum refactoring Tahap 7.  
**Status:** **BASELINE LOCKED / LULUS.** Tidak ada refactoring kode yang dilakukan setelah baseline ini.  
**Prinsip:** hasil ditulis apa adanya; tidak ada klaim E2E yang belum dijalankan.

---

## 0. Ringkasan Hasil

| Suite | Hasil | Durasi | Status |
|---|---:|---:|---|
| pytest backend + AI | **190 passed, 1 skipped, 0 failed** | 116.63 s | PASS |
| vitest frontend | **298 passed, 19 file, 0 failed** | 57.80 s | PASS |
| `pip check` | **No broken requirements found** | — | PASS |
| Production build | **Sukses**, exit code 0 | 12.20 s | PASS |
| SHA-256 checkpoint | **Cocok**, 135.644.553 B | — | PASS |
| Manual E2E | **NOT TESTED** | — | PENDING |

**Kesimpulan:** baseline otomatis HIJAU. Semua perubahan refactor nanti harus mempertahankan angka ini.

---

## 1. Lingkungan

| Item | Nilai |
|---|---|
| OS | Windows (win32) |
| Python | 3.11.9 |
| Virtualenv | `.venv` di root proyek |
| pytest | 9.1.1 |
| Node/Vitest | Vitest 5.0.2 |
| Frontend | React 18 + Vite 6 + TypeScript 5.7 |
| Backend | Flask 3 + PyTorch |
| Database/Auth | Supabase (test memakai mock/config) |
| Git branch | `fitur/validasi-input` |
| HEAD | `cbb5296` |

---

## 2. pytest

### 2.1 Perintah

```powershell
.venv\Scripts\python.exe -m pytest tests/ -x `
  --ignore=tests/ai/audit_domain_validator_deep.py `
  --ignore=tests/ai/measure_real_samples_stage2.py
```

### 2.2 Hasil

```text
collected 191 items
...
================= 190 passed, 1 skipped in 116.63s (0:01:56) =================
```

- **Passed:** 190
- **Skipped:** 1
- **Failed:** 0
- **Collected:** 191
- **Exit code:** 0

### 2.3 Cakupan

| Area | File | Catatan |
|---|---|---|
| Backend auth | `tests/Backend/test_auth.py` | 5 tes |
| Backend analysis | `tests/Backend/test_analysis.py` | 849 baris |
| Backend admin | `test_admin_routes.py`, `test_admin_service.py` | route + service |
| Backend history | `test_history.py` | 13 tes |
| Backend domain | `test_domain_validation_api.py` | 4 tes |
| Backend LLM | `test_llm_image_validator.py` | 22 tes + 1 skip |
| Backend repository/storage | `test_repository.py`, `test_storage_service.py` | 9 + 8 tes |
| Backend health/config | `test_health.py`, `test_supabase_config.py` | 5 + 3 tes |
| AI | `test_domain_validator.py`, `test_gradcam.py`, `test_model_integration.py`, `test_post_segmentation_validation.py` | domain, Grad-CAM, model, pasca-segmentasi |
| Frontend env safety | `tests/Frontend/test_frontend_env_safety.py` | 4 tes |

### 2.4 Tes yang Sengaja Diabaikan

| File | Alasan |
|---|---|
| `tests/ai/audit_domain_validator_deep.py` | Script audit mendalam, bukan unit test biasa |
| `tests/ai/measure_real_samples_stage2.py` | Pengukuran sampel nyata stage 2, bukan unit test |

**Catatan:** 1 skipped berasal dari kondisi tes LLM yang membutuhkan lingkungan/opsi tertentu; bukan kegagalan.

---

## 3. vitest

### 3.1 Perintah

```powershell
cd frontend
npm test
# = vitest run
```

### 3.2 Hasil

```text
Test Files  19 passed (19)
     Tests  298 passed (298)
  Duration  57.80s
```

- **Test files:** 19
- **Tests:** 298
- **Failed:** 0
- **Exit code:** 0

### 3.3 Catatan performa

Vitest memberi saran environment `jsdom` dibuat 19 kali; ini hanya saran optimasi, bukan kegagalan. Tidak diubah pada tahap ini.

---

## 4. Production Build

### 4.1 Perintah

```powershell
cd frontend
npm run build
# tsc -b && vite build
```

### 4.2 Hasil

| Artefak | Ukuran |
|---|---:|
| `dist/index.html` | 0.49 kB |
| `dist/assets/index-*.css` | 47.01 kB |
| `dist/assets/index-*.js` | 591.87 kB (gzip 160.80 kB) |
| Aset logo/ikon | 38.69–73.06 kB |

- **Exit code:** 0
- **Durasi:** 12.20 s
- **Warning:** chunk JS >500 kB; non-fatal, tidak mengubah fungsi.
- `dist/` dan `tsconfig.tsbuildinfo` adalah artefak gitignored; dibuat ulang oleh build.

---

## 5. Dependency Check

```powershell
.venv\Scripts\python.exe -m pip check
```

```text
No broken requirements found.
```

**Exit code:** 0.

---

## 6. Model Checkpoint

| Item | Nilai |
|---|---|
| File | `Backend/ai/models/PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth` |
| SHA-256 | `46521AE90D12F57F77A7B9921881910B41071DBBB1EFF4D2172A2C437564C581` |
| Size | **135.644.553 byte** |
| Status | Cocok dengan config/hash acuan |

**Catatan:** hash harus tetap sama setelah refactor; perubahan hash berarti checkpoint/konfigurasi berubah dan **tidak boleh terjadi**.

---

## 7. Perbandingan Baseline Lama vs Baseline Ini

| Suite | Dokumen lama (`refactor_lucit_plan.md`) | Baseline ini (11 Nov 2026) | Delta |
|---|---:|---:|---|
| pytest | 188 passed, 1 skipped | **190 passed, 1 skipped** | +2 tes (tes Gemini baru) |
| vitest | 298 passed, 19 file | **298 passed, 19 file** | 0 |
| Build | sukses | **sukses** | 0 |
| Hash | cocok | **cocok** | 0 |

**Penjelasan:** 188 pada dokumen lama berasal dari kondisi sebelum dua tes Gemini ditambahkan. Angka **190** adalah baseline aktual saat ini.

---

## 8. Batas Validitas Baseline

1. Tes backend memakai mock/fixture untuk Supabase/Gemini; bukan integrasi live.
2. Tes AI memverifikasi kontrak/unit; bukan evaluasi kualitas klinis.
3. Build sukses bukan bukti semua halaman bebas bug visual.
4. **Manual E2E belum dijalankan**: login, upload nyata, gate Gemini live, storage, worker, polling, history, delete, admin.
5. Warning chunk >500 kB belum ditangani (bukan kegagalan).

---

## 9. Manual E2E — Status

**Status: NOT TESTED.**

Rencana pengujian ada di `MANUAL_E2E_TEST_PLAN.md`. Tidak ada hasil yang dikarang. Pengujian manual harus dilakukan pada environment dengan Supabase/Gemini yang valid sebelum commit final.

Skenario minimum:

- [ ] Login dokter approved.
- [ ] Login dokter pending → ditolak.
- [ ] Login admin → dashboard admin.
- [ ] Upload gambar kolonoskopi valid.
- [ ] Upload gambar non-kolonoskopi → ditolak.
- [ ] LLM timeout/error → UNCERTAIN, fail-closed.
- [ ] Segmentasi + Grad-CAM tampil.
- [ ] History dan hapus.
- [ ] Admin approve/reject.
- [ ] Responsivitas dasar UI.

---

## 10. Kesimpulan

Baseline otomatis **LULUS** dan siap menjadi acuan. Refactoring kode belum dimulai (Langkah 0 Tahap 7 = sinkronisasi dokumentasi saja, tanpa perubahan perilaku); setiap perubahan kode harus mempertahankan hasil ini. Satu-satunya status yang masih **NOT TESTED** adalah pengujian manual end-to-end.
