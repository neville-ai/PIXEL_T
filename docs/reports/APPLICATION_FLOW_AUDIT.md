# APPLICATION FLOW AUDIT — PIXEL-T

**Tanggal:** 11 November 2026  
**Branch:** `fitur/validasi-input`  
**HEAD:** `cbb5296`  
**Sifat:** audit read-only; tidak ada perubahan kode.  
**Status pengujian manual:** **NOT TESTED** untuk seluruh skenario E2E. Hasil otomatis: pytest 190 passed / 1 skipped, vitest 298 passed, build sukses.

---

## 0. Ringkasan Alur

```text
Browser
  ├─ Register/Login ── Supabase Auth ── profile doctor_profiles
  ├─ Protected/Doctor/Admin Route
  ├─ Upload (FormData image)
  │    └─ POST /api/analysis (Bearer token)
  │         ├─ require_approved_doctor
  │         ├─ validasi gambar
  │         ├─ Domain Validation heuristik
  │         ├─ Gemini LLM gate (fail-closed)
  │         ├─ upload original ke Supabase Storage
  │         ├─ insert analyses status=processing
  │         ├─ enqueue worker (max capacity)
  │         └─ 202 {analysis_id,status}
  ├─ Poll GET /api/analysis/<id>
  │    └─ status processing → completed/failed
  ├─ Hasil: original, mask, overlay, Grad-CAM, measurements, summary
  ├─ GET /api/history
  └─ DELETE /api/history/<id>
```

---

## 1. Startup Aplikasi

### 1.1 Backend

1. `Backend/run.py` memanggil `create_app()`.
2. `Backend/src/__init__.py:8-33` memuat config, CORS `/api/*`, mendaftarkan error handler, dan blueprint.
3. `Backend/src/routes/__init__.py:6-10` mendaftarkan `health`, `analysis`, `admin` di prefix `/api`.
4. Model AI **tidak** dimuat saat startup; `ModelService` lazy-load saat pipeline pertama berjalan.

**Status:** sesuai desain; tidak ada inisialisasi eksternal saat factory.

### 1.2 Frontend

1. `Frontend/src/main.tsx` me-render `<App />`.
2. `App.tsx` memasang `BrowserRouter`, `AuthProvider`, `ThemeBootstrap`, dan `AppShellSwitch`.
3. `routes/AppRoutes.tsx` menangani route publik, protected, doctor, admin, dan 404.
4. `AuthContext` memulihkan sesi Supabase dan memuat role/status.

**Status:** sesuai; route guard terpisah dari halaman.

---

## 2. Flow Autentikasi

### 2.1 Register

| Langkah | Komponen | Bukti |
|---|---|---|
| User mengisi form | `pages/auth/Register.tsx` | form metadata dokter |
| Frontend memanggil Supabase | `services/auth.ts:131-188` | `supabase.auth.signUp` |
| Metadata profil dikirim | `services/auth.ts:146-163` | `full_name`, `hospital`, `specialty`, `doctor_profile` |
| Trigger DB membuat profil | `database/migrations/008_create_doctor_profile_trigger.sql` | profil otomatis |
| Status awal | `doctor_profiles.account_status` default `pending` | migration 007/008 |
| UI | `AuthContext` menampilkan status pending | `context/AuthContext.tsx` |
| Admin approval | `POST /api/admin/doctors/<id>/approve` | `routes/admin.py:30-34` |

**Catatan:** register tidak membuat akun kedua dan tidak menulis baris profil dari frontend; ini menghindari orphan profile.

### 2.2 Login

| Langkah | Komponen | Bukti |
|---|---|---|
| User memilih role + submit | `pages/auth/Login.tsx` | form |
| Supabase sign-in | `services/auth.ts:195-225` | `signInWithPassword` |
| Resolusi role | `AuthContext.tsx:143-194` | admin dari `app_metadata.role`, dokter dari `doctor_profiles` |
| Pemeriksaan kecocokan role | `services/auth.ts:330-335` | `isRoleMatch` |
| Status akun | `AuthContext.tsx:166-168` | `approved/pending/rejected` |
| Route guard | `ProtectedRoute`, `DoctorRoute`, `AdminRoute` | `components/auth/*` |

**Aturan role:**
- Admin: `app_metadata.role === 'admin'` (server-write-only; tidak dapat diubah user).
- Dokter: baris `doctor_profiles` dengan `role='doctor'`; harus `account_status='approved'` untuk endpoint analisis.
- Admin tidak memiliki akses klinis; `require_approved_doctor` menolak role `None`.

### 2.3 Backend authorization

| Decorator | Bukti | Perilaku |
|---|---|---|
| `require_auth` | `core/auth.py:11-85` | validasi Bearer token; isi `g.current_user` |
| `require_admin` | `core/auth.py:87-174` | cek admin dari `app_metadata`/profil |
| `require_approved_doctor` | `core/auth.py:176-275` | cek role dokter + status approved; 401/403 |
| `_get_user_role_and_status` | `core/auth.py:278-304` | query `doctor_profiles` service-role |

**Status:** sesuai dengan guard frontend; API contract tidak berubah.

---

## 3. Flow Upload dan Pembuatan Analisis

### 3.1 Frontend

1. `NewAnalysis.tsx` memvalidasi ekstensi/MIME/ukuran di klien.
2. `createAnalysis(file)` di `services/analysis.ts:232-246` mengirim `FormData` field `image`.
3. Request memakai `fetchWithTimeout` (`analysis.ts:55-…`):
   - default 30 detik;
   - upload 90 detik (`UPLOAD_REQUEST_TIMEOUT_MS`);
   - timeout → `ApiRequestError('REQUEST_TIMEOUT', ...)`.
4. Respons `202` berisi `analysis_id` dan `status='processing'`.
5. Frontend mulai polling `getAnalysis`.

### 3.2 Backend

`POST /api/analysis` (`routes/analysis.py:11-26`) → `AnalysisController.create_analysis` → `AnalysisService.create_analysis` (`analysis_service.py:400-607`).

| Urutan | Langkah | Perilaku gagal | Bukti |
|---:|---|---|---|
| 1 | Validasi file & decode gambar | `INVALID_IMAGE` 400 | `analysis_service.py:332-398` |
| 2 | Domain heuristik | `NOT_COLONOSCOPY_IMAGE` / `UNCERTAIN...` 400; tidak ada file/DB/job | `:427-450` |
| 3 | LLM Gemini gate | REJECT → 400; ERROR/timeout → `UNCERTAIN_COLONOSCOPY_IMAGE` 400 | `:455-498` |
| 4 | Upload original ke storage | `STORAGE_ERROR` 500; hapus file best-effort | `:507-530` |
| 5 | Insert DB `processing` | `DATABASE_ERROR` 500; rollback storage + record | `:532-568` |
| 6 | Enqueue worker | `QUEUE_FULL` 429; hapus record + file | `:570-599` |
| 7 | Respons | `202 {analysis_id,status:'processing'}` | `:604-607` |

**Prinsip penting:** gate domain dijalankan **sebelum** storage/DB/job; ini mencegah citra non-kolonoskopi meninggalkan artefak. `run_pipeline` juga memvalidasi domain lagi (`Backend/ai/inference/pipeline.py:135`) sebagai defense-in-depth.

### 3.3 Validasi LLM

- Modul: `Backend/src/services/llm_image_validator.py`.
- Konfigurasi: JSON schema ketat, thinking low, `max_output_tokens=1024`, timeout 30.0 s, retry 1.
- Fail-closed: kegagalan jaringan/timeout/kuota/respons tidak valid **tidak** meloloskan citra.
- Error user: `MSG_LLM_SERVICE_ERROR` (konstanta tunggal).
- Heuristik tetap berjalan lebih dulu; LLM tidak dapat meloloskan hasil yang sudah ditolak heuristik.

---

## 4. Flow Worker dan Pipeline AI

### 4.1 Queue

- `AnalysisJobQueue` (`analysis_service.py:151-268`) memakai worker thread dengan antrean terbatas.
- Jika penuh: `QUEUE_FULL` (429) dan kompensasi record/file.
- Worker memanggil `_run_analysis_job` → `_execute_pipeline`.

### 4.2 Pipeline

```text
prepare_image (512×512, ImageNet)
  → domain gate (pipeline, ACCEPT saja)
  → U-Net + ResNet50
  → TTA 5 skala × 5 orientasi
  → sigmoid + threshold 0.55
  → postprocess (close/open, area ≥25, fill holes, smoothing)
  → measure mask (area, bbox, status)
  → Grad-CAM (target decoder.blocks.4.conv2.0)
  → komposisi artefak PNG
```

Bukti: `Backend/ai/inference/pipeline.py:102-155`, `segmentation.py`, `postprocessing.py`, `gradcam.py`, `model_config.py`.

### 4.3 Progress

- `AnalysisProgressReporter` (`analysis_service.py:65-149`) menghitung unit fase + TTA forward pass.
- Progress ditulis throttled; tidak pernah memfabrikasi 100%.
- `100%` hanya ditulis saat status `completed`.
- `total_units = 6 + count_forward_passes(MODEL_CONFIG)` (`analysis_service.py:927`).

### 4.4 Penyimpanan hasil

- 4 artefak wajib: binary mask, segmentation overlay, Grad-CAM heatmap, Grad-CAM overlay.
- Semua harus berhasil diunggah sebelum DB berubah ke `completed`.
- DB menyimpan path, measurements, status segmentasi, metadata model, dan summary.
- Bila gagal: status `failed` + `error_code`/`error_message`, artefak yang sudah diunggah dibersihkan best-effort.

**Status:** sesuai; perubahan pipeline tidak diizinkan pada refactor ini.

---

## 5. Flow Polling dan Hasil

### 5.1 `GET /api/analysis/<id>`

- Route: `routes/analysis.py:29-42`, guard `require_approved_doctor`.
- Service: `get_analysis` (`analysis_service.py:609-760`).
- Ownership: `repository.get_by_id(analysis_id, user_id, ...)`.
- Signed URL 3600 s untuk original/mask/overlay/heatmap/Grad-CAM.
- Status `failed` mengembalikan kode `ANALYSIS_FAILED` dan pesan aman.
- Progress disertakan untuk `processing`.

### 5.2 Frontend polling

| Halaman | Perilaku | Bukti |
|---|---|---|
| `NewAnalysis` | polling 2 detik; berhenti saat `completed`/`failed`/401; **belum ada batas maksimum eksplisit** | `NewAnalysis.tsx:21,167-209` |
| `AnalysisResult` | polling 5 detik; `MAX_POLL_ATTEMPTS=12` | `AnalysisResult.tsx:9-10,80-106` |

**Temuan:** perbedaan batas polling adalah kandidat perbaikan UX, bukan perubahan API.

### 5.3 Tampilan hasil

- Original image, binary mask, segmentation overlay, Grad-CAM heatmap/overlay.
- `detection_category`: `POLYP_DETECTED`, `NO_POLYP_DETECTED`, `LOW_CONFIDENCE`.
- Summary text dari backend; frontend tidak menghitung ulang inferensi.
- `AnalysisResult` menangani gambar gagal muat dan polling timeout.

---

## 6. Flow Riwayat dan Hapus

### 6.1 Riwayat

- `GET /api/history` (`routes/analysis.py:45-53`).
- `list_user_analyses` (`analysis_service.py:762-813`).
- Query dibatasi `user_id`; thumbnail signed URL; pagination/metadata sesuai kontrak.

### 6.2 Hapus

- `DELETE /api/history/<id>` (`routes/analysis.py:56-64`).
- `delete_analysis` (`analysis_service.py:815-886`):
  1. verifikasi ownership;
  2. hapus record DB terlebih dahulu;
  3. hapus objek storage best-effort;
  4. kegagalan storage tidak “menghidupkan” record kembali (DECISION A).
- Frontend `deleteAnalysis` memakai `expectData: false`.

**Status:** perilaku konsisten dan teruji.

---

## 7. Flow Admin

| Alur | Endpoint | Service | Bukti |
|---|---|---|---|
| Daftar dokter | `GET /api/admin/doctors` | `AdminService.list_doctors` | `routes/admin.py:9-13` |
| Statistik | `GET /api/admin/doctors/stats` | `get_statistics` | `:16-20` |
| Detail | `GET /api/admin/doctors/<id>` | `get_doctor` | `:23-27` |
| Approve | `POST /api/admin/doctors/<id>/approve` | `approve_doctor` | `:30-34` |
| Reject | `POST /api/admin/doctors/<id>/reject` | `reject_doctor` | `:37-45` |

**Catatan:** `AdminController` mengembalikan envelope error berbeda dari handler global. Perlu normalisasi setelah memastikan `AdminDashboard.tsx` tidak bergantung pada bentuk lama.

---

## 8. Transisi Status

```text
Analysis:
  processing ──pipeline sukses──> completed
      └────── pipeline gagal ───> failed

Segmentation:
  detected | not_detected

Doctor account:
  pending ──approve──> approved
      └────reject────> rejected
```

Aturan:
- `processing` adalah status awal setelah DB insert.
- `completed` hanya setelah 4 artefak tersimpan.
- `failed` membawa error aman (tidak membocorkan internal).
- `100%` hanya pada `completed`.
- `approved` wajib untuk endpoint analisis.

---

## 9. Error Handling

| Lapisan | Mekanisme | Bukti |
|---|---|---|
| Backend domain | `APIError` + kode `NOT_COLONOSCOPY_IMAGE` / `UNCERTAIN...` | `analysis_service.py:439-498` |
| Backend umum | handler global `{success:false,error:{code,message}}` | `core/errors.py` |
| Admin | envelope tidak seragam | `admin_controller.py:26,46,63,84,98` |
| Frontend API | `ApiRequestError` dengan `code` | `services/analysis.ts` |
| Frontend UI | `ErrorState`, toast/alert per halaman | `components/ui/ErrorState.tsx`, pages |
| Timeout | `REQUEST_TIMEOUT` | `services/analysis.ts:40-63` |

---

## 10. Matriks Status Pengujian

| Skenario | Otomatis | Manual E2E |
|---|---|---|
| Backend health | Lulus (pytest) | **NOT TESTED** |
| Auth login/register/guard | Lulus (pytest/vitest) | **NOT TESTED** |
| Upload valid | Lulus (mock/unit) | **NOT TESTED** |
| Tolak non-kolonoskopi (heuristik) | Lulus | **NOT TESTED** |
| Tolak/uncertain LLM | Lulus | **NOT TESTED** |
| Storage/DB/queue compensation | Lulus (unit) | **NOT TESTED** |
| Pipeline segmentation/TTA/threshold | Lulus (AI test) | **NOT TESTED** |
| Grad-CAM | Lulus | **NOT TESTED** |
| Polling/hasil | Lulus (vitest) | **NOT TESTED** |
| History/delete | Lulus | **NOT TESTED** |
| Admin approve/reject | Lulus | **NOT TESTED** |

**Catatan:** “Lulus otomatis” berarti suite memakai mock/fixture; bukan bukti integrasi Supabase/Gemini nyata. Status E2E tetap **NOT TESTED** sampai dijalankan manual pada environment nyata.

---

## 11. Kesimpulan

Alur utama PIXEL-T konsisten dari frontend ke backend hingga AI dan kembali ke UI. Tidak ditemukan alur yang hilang atau endpoint tanpa layer. Risiko utama ada pada **service besar**, **polling tanpa batas**, **envelope admin**, dan **validasi E2E yang belum dijalankan** — bukan pada perubahan arsitektur besar.
