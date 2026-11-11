# PIXEL-T STRUCTURE AUDIT — Audit Struktur PIXEL-T vs LUCIT-master

**Tanggal:** 11 November 2026  
**Branch:** `fitur/validasi-input`  
**HEAD:** `cbb5296`  
**Sifat:** audit read-only berdasarkan pembacaan file dan verifikasi import. Tidak ada perubahan file.  
**Referensi:** `LUCIT_STRUCTURE_ANALYSIS.md`, `PROJECT_STRUCTURE_INVENTORY.md`, `TARGET_PROJECT_STRUCTURE.md`.

---

## 0. Ringkasan Eksekutif

PIXEL-T sudah memiliki struktur terorganisir yang setara, dan di beberapa aspek lebih baik, daripada `LUCIT-master`. Layering backend sudah lengkap, konfigurasi terpusat, klien Supabase terpadu, error handler global, dan test suite lengkap. Masalah utama bukan arsitektur besar, melainkan **beberapa file terlalu besar**, **tidak konsistensi envelope error**, **sisa placeholder `.gitkeep`**, **artefak build/log**, dan **tooling diagram di root**.

Semua fitur utama masih dipelihara:
- Upload → Domain Validation (heuristik → LLM fail-closed) → Storage → DB `processing` → antrean background → U-Net/ResNet50 → Grad-CAM → polling → hasil.
- Auth/login/register dengan role admin/dokter dan status akun.
- Admin approve/reject dokter.

---

## 1. Struktur Layer Backend PIXEL-T

```text
Backend/
├── run.py                              entry point
├── app/
│   ├── __init__.py                     application factory
│   ├── core/
│   │   ├── config.py                   konfigurasi central
│   │   ├── supabase.py                 client tunggal (anon + service role)
│   │   ├── errors.py                   envelope APIError global
│   │   └── auth.py                     Bearer token + require_admin/require_approved_doctor
│   ├── routes/
│   │   ├── __init__.py                 register blueprints di /api
│   │   ├── health.py
│   │   ├── analysis.py
│   │   └── admin.py
│   ├── controllers/
│   │   ├── analysis_controller.py
│   │   └── admin_controller.py
│   ├── services/
│   │   ├── analysis_service.py         orkestrasi utama, 1147 baris total (1029 non-kosong) (candidate disederhanakan)
│   │   ├── admin_service.py
│   │   ├── storage_service.py
│   │   └── llm_image_validator.py      Gemini fail-closed
│   └── repositories/
│       └── analysis_repository.py
```

**Kekuatan:**
- Route adalah thin wrapper; controller memanggil service; service memanggil repository/core/AI.
- Factory `create_app` memungkinkan test dan konfigurasi per env.
- Error envelope seragam di `core/errors.py`.
- Semua endpoint terlindungi dengan `require_approved_doctor` atau `require_admin`.

**Kelemahan:**
1. `analysis_service.py` memiliki 1147 baris total (1029 baris non-kosong) dan bertanggung jawab atas validasi gambar, gate domain, gate LLM, penyimpanan, DB, antrean, worker, pipeline, dan progres. Risiko pemeliharaan tinggi; pemecahan hanya setelah persetujuan dan regresi penuh.
2. `admin_controller.py` menghasilkan envelope error berbeda dari handler global di `core/errors.py` (5 lokasi: `{success: false, error: string, code}` vs `{success: false, error: {code, message}}`).
3. `core/auth.py` memiliki 3 decorator yang masing-masing mem-parsing header `Authorization` secara duplikat. Ekstraksi helper kecil memungkinkan, tetapi auth tidak boleh berubah.

---

## 2. Struktur Frontend PIXEL-T

```text
Frontend/src/
├── main.tsx / App.tsx
├── routes/AppRoutes.tsx                routing terpusat + guard
├── context/AuthContext.tsx             sesi, role, status akun
├── services/
│   ├── analysis.ts                     client API + fetchWithTimeout + polling
│   ├── auth.ts
│   └── profile.ts
├── lib/
│   ├── supabase.ts / format.ts / openingTimeline.ts
├── hooks/useTheme.ts / useOpeningAnimation.ts
├── components/
│   ├── ui/*                            komponen reusable
│   ├── auth/*Route.tsx                 guard per role
│   ├── layout/AppShell.tsx
│   └── brand/LogoPixelT.tsx
├── pages/
│   ├── auth/Login.tsx / Register.tsx / ResetPassword.tsx
│   ├── dashboard/Dashboard.tsx
│   ├── analysis/NewAnalysis.tsx / AnalysisResult.tsx
│   ├── history/History.tsx / HistoryDetail.tsx
│   ├── profile/DoctorProfile.tsx
│   ├── admin/AdminDashboard.tsx
│   └── NotFound.tsx
├── assets/ ...
└── styles/opening.css
```

**Kekuatan:**
- Routing terpisah dan guard per eksplisit.
- API terpusat di `services/*.ts`, tidak ada pemanggilan fetch berserak.
- File UI kecil dan reusable.

**Kelemahan:**
- `DoctorProfile.tsx` (974 baris), `NewAnalysis.tsx` (592 baris), `History.tsx` (577 baris), `AdminDashboard.tsx` (505 baris) cukup besar. Ekstraksi komponen internal memungkinkan, tetapi UI tidak boleh berubah.
- Sebelum cleanup: `fetch` tanpa batas waktu dan `NewAnalysis` tanpa batas polling eksplisit. Setelah cleanup: `fetchWithTimeout` sudah diterapkan, polling tanpa batas maksimum masih tersisa.

---

## 3. Modul AI (Tidak Boleh Diubah)

| File | Baris | Fungsi |
|---|---:|---|
| `Backend/ai/config/model_config.py` | 58 | ModelConfig, threshold 0.55, TTA, target layer, hash |
| `Backend/ai/inference/pipeline.py` | 155 | 5 fase |
| `Backend/ai/inference/preprocessing.py` | 22 | siap model |
| `Backend/ai/inference/segmentation.py` | 114 | TTA 5×5 |
| `Backend/ai/inference/postprocessing.py` | 109 | morfologi dan metrik |
| `Backend/ai/inference/gradcam.py` | 153 | Grad-CAM |
| `Backend/ai/inference/domain_validator.py` | 276 | heuristik |
| `Backend/ai/inference/model_service.py` | 119 | load checkpoint |
| `Backend/ai/inference/__init__.py` | kecil | package |
| `Backend/ai/models/.gitkeep` | 0 | penanda checkpoint |

**Kesimpulan:** struktur AI cukup baik dan tidak perlu digabungkan atau dipindahkan. `ai/` harus tetap dilindungi sebagai bagian penelitian.

---

## 4. Database dan Supabase

| File | Fungsi |
|---|---|
| `migrations/001–008.sql` | tabel, bucket, trigger, role/status |
| `verify_doctor_registration.sql` | verifikasi registrasi |

Repository dan klien Supabase terpusat di `core/supabase.py`. Keamanan: kunci service role hanya server-side; RLS/ownership diwajibkan.

---

## 5. Test Suite (Sudah Ada, Wajib Pertahankan)

| Suite | File | Hasil baseline |
|---|---|---|
| pytest | 20 file test + env safety | 190 passed, 1 skipped |
| vitest | 19 file test | 298 passed |
| Frontend build | — | sukses |

Non-unit test `tests/ai/audit_domain_validator_deep.py` dan `tests/ai/measure_real_samples_stage2.py` diabaikan secara disengaja pada baseline.

---

## 6. Perbandingan Struktur: PIXEL-T vs LUCIT

| Aspek | LUCIT-master | PIXEL-T | Hasil Audit |
|---|---|---|---|
| Entry backend | `main.py` app global | `run.py` → factory | **PIXEL-T lebih baik** |
| Layering | routes → controllers → services → repositories | sama, lebih lengkap | **Setara / lebih baik** |
| Config | `config/settings.py` | `core/config.py` | **Setara** |
| Supabase | `config/supabase.py` | `core/supabase.py` | **Setara** |
| Error handling | `try/except` per route | global `APIError` | **PIXEL-T lebih baik** |
| Auth | session Flask + localStorage | Supabase Bearer + role/status | **PIXEL-T lebih baik** |
| AI validasi | validator multifungsi, fallback LLM → heuristic | heuristic → LLM fail-closed | **PIXEL-T lebih baik** |
| Segmentasi | threshold 0.35 | threshold 0.55 dari config model | **Domain berbeda, tidak diubah** |
| Grad-CAM | service | service + target layer dari config | **PIXEL-T lebih baik** |
| Frontend routing | inline di App.tsx | `AppRoutes.tsx` terpisah | **PIXEL-T lebih baik** |
| Frontend test | tidak ada | 19 file / 298 tes | **PIXEL-T lebih baik** |
| Dokumentasi | README dasar | PRD + spec + audit forensik | **PIXEL-T lebih baik** |

---

## 7. Kategori Setiap File dan Folder

| Kode | Arti |
|---|---|
| **A** | Wajib inti runtime, keamanan, atau test |
| **B** | Dapat disederhanakan intern |
| **C** | Dapat digabung/dikonsolidasi |
| **D** | Tidak diperlukan / regenerable |
| **E** | Dipindah |
| **F** | Artefak penelitian / skripsi |

### 7.1 Kategori umum

| Area | Kategori | Keterangan |
|---|---|---|
| `ai/**` | **A / F** | Model dan inferensi wajib dilindungi |
| `Backend/src/core/**` | **A** | auth/config/errors/supabase; edit hanya dengan approval |
| `Backend/src/routes/**` | **A** | API contract; jangan diubah tanpa persetujuan |
| `Backend/src/controllers/**` | **A / B** | admin_controller perlu diselaraskan envelope |
| `Backend/src/services/**` | **A / B** | analysis_service candidate pemecahan internal |
| `Backend/src/repositories/**` | **A** | CRUD + ownership |
| `Frontend/src/**` | **A / B** | halaman besar candidate ekstraksi komponen |
| `database/migrations/**` | **A / F** | tidak boleh diubah |
| `tests/**` | **A** | wajib dipertahankan |
| `docs/**`, `diagram-skripsi/`, `research/`, `scripts/` | **F** | artefak skripsi; hapus setelah konfirmasi |
| `calibration_data/`, `references/`, `LUCIT-master/` | **F** | referensi dan penelitian |
| `node_modules/`, `.venv/`, `dist/`, `.pytest_cache/` | **D** | regenerable/gitignored |

### 7.2 File dengan indikasi penyederhanaan (belum diubah)

| File | Kategori | Temuan | Rekomendasi |
|---|---|---|---|
| `Backend/src/services/analysis_service.py` | A/B | 1147 baris total (1029 non-kosong), banyak `print` korelasi | Split internal di belakang facade yang stabil, setelah persetujuan |
| `Backend/src/core/auth.py` | A/B | 3 duplikasi parsing Bearer | Ekstrak helper, jangan ubah perilaku auth |
| `Backend/src/controllers/admin_controller.py` | A/B | envelope error tidak konsisten (5 lokasi) | Normalisasi, verifikasi FE tidak bergantung versi lama |
| `Frontend/src/pages/DoctorProfile.tsx` | A/B | 974 baris | Ekstraksi subkomponen internal, UI tidak berubah |
| `Frontend/src/pages/NewAnalysis.tsx` | A/B | polling tanpa batas maksimum eksplisit | Tambah batas polling, tidak mengubah API |
| `Frontend/src/pages/History.tsx` / `AdminDashboard.tsx` | A/B | 577/505 baris | Ekstraksi internal jika diperlukan |
| `docs/APIContract.md` vs `.txt` | C | duplikasi format | Gabungkan hanya setelah konfirmasi tim skripsi |
| Folder `.gitkeep`-only yang kosong | B/C | 10 folder dibersihkan sebelumnya; 21 tersisa | Konsolidasi bertahap, verifikasi impor |
| Root diagram tools | E/F | `generate_bab4.js` bergantung `__dirname` | Pindah ke `_archive/diagram_tools/` setelah penyesuaian path |

---

## 8. Risiko yang Teridentifikasi

| ID | Risiko | Lokasi | Level | Tindakan |
|---|---|---|---|---|
| R1 | Service analysis sangat besar | `analysis_service.py` | Tinggi | Pemecahan bertahap, regresi penuh |
| R2 | Envelope error admin tidak konsisten | `admin_controller.py` | Sedang | **Selesai (Langkah 1B)** |
| R3 | Parsing token duplikat | `core/auth.py` | Rendah | Ekstraksi helper, jangan ubah auth |
| R4 | Sisa `.gitkeep` di folder berisi | beberapa folder | Rendah | Hapus konsolidasikan |
| R5 | Artefak build/log | `dist/`, `.pytest_cache/` | Rendah | Pembersihan (gitignored) |
| R6 | Root diagram tools | 7 file | Sedang | Archive setelah path disesuaikan |

---

## 9. Kesimpulan Audit Struktur

Struktur PIXEL-T sudah layak dan tidak memerlukan restrukturisasi besar. Penyederhanaan harus difokuskan pada pemecahan file besar, konsistensi error, pembersihan artefak, dan konsol folder `.gitkeep`. Semua perubahan harus diapit oleh regresi: **pytest 190 / 1 skipped, vitest 298, build sukses, hash model cocok.**
