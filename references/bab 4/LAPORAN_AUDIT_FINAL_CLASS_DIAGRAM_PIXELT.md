# LAPORAN AUDIT FINAL CLASS DIAGRAM — PIXEL-T

**Tanggal audit:** 2026-11-02  
**Objek audit:** `CLASS_DIAGRAM_FINAL_PIXELT.puml` / `.png` / `.svg` (diagram final setelah audit ulang)  
**Ground truth:** seluruh kode sumber aktual `backend/app/**`, `ai/inference/**`, `ai/config/model_config.py`, `database/migrations/001–004_*.sql`, `frontend/src/**`, `tests/**`  
**Metode:** pembacaan langsung setiap berkas kode, penelusuran alur runtime, verifikasi visual hasil render terhadap referensi `class_diagram_contoh.png`.  
**Batasan:** audit bersifat read-only — tidak ada kode aplikasi yang diubah. Setiap klaim disertai path dan nomor baris yang dapat ditelusuri.

---

## 1. RINGKASAN EKSEKUTIF

| Aspek | Hasil |
|---|---|
| Kondisi sebelum audit | Diagram memiliki 19 kelas/representasi dalam 4 package; sebagian atribut/metode tidak sesuai signature kode; representasi frontend memakai tiga kelas yang tidak ada sebagai class di kode (`AnalysisClient`, `DoctorProfileService`, `AuthContext` adalah module/function); `StorageService.upload_file` ditulis dengan parameter yang tidak ada. |
| Temuan penting | (a) Frontend layer dipaksa menjadi kelas OO padahal implementasi berbasis fungsi module React/TS; (b) signature `StorageService.upload_file` salah; (c) relasi `*--` composition pada `AnalysisService -> repository/storage/queue` tidak didukung lifecycle eksklusif (dependency injection mengizinkan injeksi luar); (d) entitas `analyses` dan `doctor_profiles` sudah penuh tetapi perlu penandaan subset/ilustratif; (e) `ModelConfig` sudah lengkap (19 field dataclass + `checkpoint_path` sebagai `@property` + 2 operasi). |
| Perbaikan yang diterapkan | (a) Frontend dipresentasikan sebagai package `Frontend` berisi 3 representasi modul fungsional yang jelas; (b) signature `StorageService` dikoreksi; (c) composition diganti asosiasi berarah (`-->`) yang sesuai dengan pola DI; (d) seluruh atribut entitas diverifikasi terhadap migration; (e) `ModelConfig` dipertahankan lengkap. |
| Temuan terbuka | Tidak ada temuan struktural yang terbuka. Batasan minor dicatat pada §7. |
| **Status akhir** | **LAYAK DENGAN REVISI MINOR** |

---

## 2. AUDIT ELEMEN KELAS

### 2.1 Kelas Backend

| # | Kelas | File | Baris | Atribut | Metode | Status |
|---|---|---|---|---|---|---|
| 1 | `AnalysisController` | `backend/app/controllers/analysis_controller.py` | 7–96 | `- service: AnalysisService` | `create_analysis`, `get_analysis`, `list_history`, `delete_analysis` | ✅ Terverifikasi |
| 2 | `AnalysisService` | `backend/app/services/analysis_service.py` | 269–991 | `repository`, `storage_service`, `pipeline_runner`, `job_queue` | `validate_and_decode_image`, `create_analysis`, `get_analysis`, `list_user_analyses`, `delete_analysis`, `_run_analysis_job`, `_execute_pipeline`, `_last_progress_percent`, `run_segmentation` (static), `run_gradcam` (static) | ✅ Terverifikasi |
| 3 | `AnalysisRepository` | `backend/app/repositories/analysis_repository.py` | 5–196 | `_client` | `create`, `get_by_id`, `list_by_user`, `update`, `delete`, `validate_lifecycle_status`, `validate_segmentation_status` | ✅ Terverifikasi |
| 4 | `StorageService` | `backend/app/services/storage_service.py` | 7–189 | `_client`, `bucket_name` | `generate_original_image_path`, `generate_binary_mask_path`, `generate_segmentation_overlay_path`, `generate_gradcam_heatmap_path`, `generate_gradcam_overlay_path`, `get_analysis_asset_paths`, `validate_path_ownership`, `upload_file`, `download_file`, `create_signed_url`, `delete_file`, `delete_analysis_files`, `sanitize_id` (static) | ✅ Terverifikasi (signature dikoreksi) |
| 5 | `AnalysisJobQueue` | `backend/app/services/analysis_service.py` | 150–266 | `_runner`, `_jobs`, `_lock`, `_not_empty`, `_active_analysis_id`, `MAX_WAITING` | `capacity`, `try_enqueue`, `contains`, `pending_count`, `drain_one`, `_ensure_worker`, `_work_loop` | ✅ Terverifikasi |
| 6 | `AnalysisProgressReporter` | `backend/app/services/analysis_service.py` | 64–148 | `_repository`, `_analysis_id`, `_user_id`, `_completed_units`, `_passes_done`, `_last_percent`, `_last_step`, `total_units`, `failed_writes` | `last_step`, `completed_units`, `percent`, `on_phase`, `on_pass`, `_write` | ✅ Terverifikasi |
| 7 | `APIError` | `backend/app/core/errors.py` | 8–23 | `code`, `message`, `status_code` | `to_dict` | ✅ Terverifikasi |

### 2.2 Kelas AI

| # | Kelas | File | Baris | Atribut | Metode | Status |
|---|---|---|---|---|---|---|
| 8 | `AIInferenceFunctions <<module>>` | `ai/inference/pipeline.py`, `segmentation.py`, `postprocessing.py`, `gradcam.py`, `preprocessing.py` | berbagai | — (module) | `run_pipeline`, `predict`, `postprocess_mask`, `measure_mask`, `generate_gradcam`, `prepare_image`, `count_forward_passes` | ✅ Terverifikasi (stereotype `<<module>>`) |
| 9 | `ModelService` | `ai/inference/model_service.py` | 19–136 | `_model`, `_device`, `_lock`, `config`, `load_count` | `device`, `load`, `metadata`, `predict_logits`, `get_gradcam_target_layer`, `_build_model`, `_select_device` | ✅ Terverifikasi |
| 10 | `ModelConfig` | `ai/config/model_config.py` | 19–66 | 20 atribut (19 field dataclass + `checkpoint_path` sebagai `@property` read-only) | `validate`, `checkpoint_sha256_matches` | ✅ Terverifikasi (lengkap) |
| 11 | `PipelineResult` | `ai/inference/pipeline.py` | 63–70 | `binary_mask_png`, `segmentation_overlay_png`, `gradcam_heatmap_png`, `gradcam_overlay_png`, `measurements`, `summary_text`, `gradcam` | — (frozen dataclass) | ✅ Terverifikasi |
| 12 | `SegmentationResult` | `ai/inference/segmentation.py` | 24–29 | `probability_map`, `binary_mask`, `threshold` | — (frozen dataclass) | ✅ Terverifikasi |
| 13 | `GradCAMResult` | `ai/inference/gradcam.py` | 37–44 | `heatmap`, `overlay`, `target_layer`, `target_objective`, `target_mask_empty` | — (frozen dataclass) | ✅ Terverifikasi |

### 2.3 Entitas Basis Data

| # | Entitas | File migrasi | Atribut pada diagram | Status |
|---|---|---|---|---|
| 14 | `analyses <<entity>>` | `001_create_analyses_and_storage.sql`, `002_add_ai_pipeline_metadata.sql`, `003_add_analysis_progress.sql` | 39 atribut (semua kolom dari migrasi 001–003) | ✅ Terverifikasi (lengkap) |
| 15 | `doctor_profiles <<entity>>` | `004_create_doctor_profiles.sql` | 23 atribut (semua kolom migrasi 004) | ✅ Terverifikasi (lengkap) |
| 16 | `auth_users <<external>>` | Referensi FK di `001:17` dan `004:12` | `id: UUID` | ✅ Terverifikasi (tabel eksternal Supabase Auth) |

### 2.4 Frontend (Package)

| # | Representasi | File | Isi | Status |
|---|---|---|---|---|
| 17 | `package "Frontend"` | `frontend/src/services/**`, `frontend/src/context/AuthContext.tsx` | `AnalysisClient <<module>>`, `AuthContext <<module>>`, `DoctorProfileService <<module>>` | ✅ Package dipresentasikan sebagai package; tiga class di dalamnya adalah representasi modul fungsional (bukan class OO sesungguhnya). Dijelaskan pada §5. |

---

## 3. AUDIT RELASI

| # | Relasi | Jenis UML | Bukti | Status |
|---|---|---|---|---|
| 1 | `AnalysisController "1" --> "1" AnalysisService` | Association (directed) | `self.service = service or AnalysisService()` — `analysis_controller.py:11` | ✅ Valid |
| 2 | `AnalysisController ..> APIError` | Dependency | `raise APIError(...)` — `analysis_controller.py:23, 46, 74` | ✅ Valid |
| 3 | `AnalysisService "1" --> "1" AnalysisRepository` | Association (directed) | `self.repository = repository or AnalysisRepository()` — `analysis_service.py:291`. Referensi disimpan sebagai atribut; DI memungkinkan injeksi eksternal sehingga bukan composition. | ✅ Valid |
| 4 | `AnalysisService "1" --> "1" StorageService` | Association (directed) | `self.storage_service = storage_service or StorageService()` — `analysis_service.py:292` | ✅ Valid |
| 5 | `AnalysisService "1" --> "1" AnalysisJobQueue` | Association (directed) | `self.job_queue = job_queue or AnalysisJobQueue(...)` — `analysis_service.py:296–299` | ✅ Valid |
| 6 | `AnalysisService ..> AnalysisProgressReporter` | Dependency | Dibuat lokal di `_execute_pipeline` — `analysis_service.py:801–806` | ✅ Valid |
| 7 | `AnalysisProgressReporter "1" --> "1" AnalysisRepository` | Association (directed) | `self._repository = repository` disimpan sebagai atribut; `self._repository.update(...)` — `analysis_service.py:133` | ✅ Valid |
| 8 | `AnalysisService ..> AIInferenceFunctions` | Dependency | `self.pipeline_runner = pipeline_runner or run_pipeline` — `analysis_service.py:293`; dipanggil di `_execute_pipeline:808–814` | ✅ Valid |
| 9 | `AIInferenceFunctions ..> ModelService` | Dependency | `predict(..., model_service=...)` — `segmentation.py:98`; `generate_gradcam(..., model_service=...)` — `gradcam.py:99` | ✅ Valid |
| 10 | `AIInferenceFunctions ..> PipelineResult` | Dependency | `run_pipeline` mengembalikan `PipelineResult` — `pipeline.py:101` | ✅ Valid |
| 11 | `AIInferenceFunctions ..> SegmentationResult` | Dependency | `predict` mengembalikan `SegmentationResult` — `segmentation.py:98` | ✅ Valid |
| 12 | `AIInferenceFunctions ..> GradCAMResult` | Dependency | `generate_gradcam` mengembalikan `GradCAMResult` — `gradcam.py:99` | ✅ Valid |
| 13 | `PipelineResult "1" --> "1" GradCAMResult` | Association (directed) | Field `gradcam: GradCAMResult` pada frozen dataclass — `pipeline.py:69`; referensi disimpan, bukan kepemilikan lifecycle. | ✅ Valid |
| 14 | `ModelService --> ModelConfig` | Association (directed) | `def __init__(self, config: ModelConfig = MODEL_CONFIG)` — `model_service.py:22` | ✅ Valid |
| 15 | `AnalysisRepository ..> analyses` | Dependency | Operasi CRUD tabel `analyses` — `analysis_repository.py:38–196` | ✅ Valid |
| 16 | `auth_users "1" -- "0..*" analyses` | Association | FK `user_id REFERENCES auth.users(id)` — `001:17` | ✅ Valid |
| 17 | `auth_users "1" -- "0..1" doctor_profiles` | Association | FK UNIQUE `user_id` — `004:12, 46` | ✅ Valid |
| 18 | `AnalysisClient ..> AnalysisController` | Dependency | `fetch(\`${API_BASE_URL}/analysis\`, ...)` — `analysis.ts:185` (POST), `:194` (GET) | ✅ Valid |
| 19 | `AuthContext ..> auth_users` | Dependency | `supabase.auth.signInWithPassword(...)` — `AuthContext.tsx:96` via `auth.ts:205` | ✅ Valid |
| 20 | `DoctorProfileService ..> doctor_profiles` | Dependency | `supabase.from('doctor_profiles').upsert(...)` — `profile.ts:287–289` | ✅ Valid |

**Koreksi dari versi sebelumnya:**  
- Signature `StorageService.upload_file` sebelumnya salah (`filepath`, `content`, `user_id`, `analysis_id`); sekarang sudah disesuaikan dengan parameter aktual `upload_file(path, file_bytes, content_type, user_id, use_service_role)`.  
- Jenis relasi `AnalysisService -> repository/storage/queue` diubah dari composition (`*--`) menjadi asosiasi berarah (`-->`) karena dependency injection memungkinkan injeksi eksternal; service tidak memiliki lifecycle eksklusif atas objek yang diinjeksi.

---

## 4. AUDIT ALUR RUNTIME

Alur berikut ditelusuri dari kode aktual (bukan disimpulkan dari nama kelas):

### 4.1 Alur Autentikasi (Lengkap)
1. **Frontend:** `Login.tsx` → `AuthContext.signIn` → `auth.ts:loginUser` → `supabase.auth.signInWithPassword` (baris 205)
2. **Backend:** route `@require_auth` → `auth.py:15–78` → `get_supabase_client().auth.get_user(token)` → `g.current_user = {id, email, role}`
3. **Kegagalan:** `APIError("UNAUTHORIZED", ..., 401)` → error handler → response `{success: false, error: {code, message}}`
4. **Status:** ✅ Terverifikasi

### 4.2 Alur Unggah Citra (Lengkap)
1. **Frontend:** `NewAnalysis.tsx` → `createAnalysis(file)` → `POST /api/analysis` (`analysis.ts:185`)
2. **Backend route:** `analysis.py:11–25` → `@require_auth` → `controller.create_analysis()`
3. **Controller:** `analysis_controller.py:13–39` → `self.service.create_analysis(file_storage, user_id)`
4. **Service:** `analysis_service.py:369–501`:
   - `validate_and_decode_image` (validasi MIME, ukuran, format Pillow) → `APIError` jika gagal
   - `generate_original_image_path` → `upload_file` ke Supabase Storage
   - `repository.create` (status `processing`)
   - `job_queue.try_enqueue` → jika `False`, rollback + `APIError("QUEUE_FULL", 429)`
5. **Respons:** HTTP 202 dengan `analysis_id` stabil
6. **Status:** ✅ Terverifikasi

### 4.3 Alur Analisis AI (Lengkap)
1. **Background worker:** `AnalysisJobQueue._work_loop` → `self._runner(job)` → `_run_analysis_job` (`analysis_service.py:761`)
2. **Eksekusi pipeline:** `_execute_pipeline` (baris 781–958):
   - Membuat `AnalysisProgressReporter` (baris 805)
   - Memanggil `pipeline_runner(file_bytes, config, on_phase, on_pass, analysis_id)` (baris 815)
   - Pipeline berjalan 5 fase: `preprocessing`, `inference`, `postprocessing`, `gradcam`, `artifact_composition`
   - Setiap fase → `progress.on_phase(step)` → `_write` → `repository.update(... current_step, progress_percent ...)`
   - Setiap forward pass → `progress.on_pass()` → throttled write setiap 5 pass
3. **Penyimpanan hasil:** upload 4 artefak (mask, overlay, heatmap, gradcam overlay) → `repository.update(status="completed", ...)`
4. **Kegagalan:** `except` → `repository.update(status="failed", error_code="AI_PIPELINE_ERROR", ...)` → re-raise `APIError`
5. **Status:** ✅ Terverifikasi

### 4.4 Alur Pelaporan Progres (Lengkap)
- **Mekanisme:** Database write (bukan WebSocket/SSE); frontend polling `GET /api/analysis/<id>` setiap 5 detik (`AnalysisResult.tsx:9`, `POLL_INTERVAL_MS = 5000`)
- **Reporter:** `AnalysisProgressReporter` → `repository.update(current_step, progress_percent)` (`analysis_service.py:133`)
- **Frontend:** `NewAnalysis.tsx:169–215` memanggil `getAnalysis(id)` berulang hingga status terminal
- **Status:** ✅ Terverifikasi

### 4.5 Alur Riwayat dan Detail (Lengkap)
1. **Riwayat:** `History.tsx` → `listHistory()` → `GET /api/history` → `controller.list_history()` → `service.list_user_analyses(user_id)` → `repository.list_by_user(...)`
2. **Detail:** `HistoryDetail.tsx` → `getAnalysis(id)` → `GET /api/analysis/<id>` → ownership check via `repository.get_by_id(analysis_id, user_id)`
3. **Hapus:** `deleteAnalysis(id)` → `DELETE /api/history/<id>` → `service.delete_analysis(...)` → DB-first deletion → best-effort storage cleanup
4. **Status:** ✅ Terverifikasi

### 4.6 Alur Profil Dokter (Lengkap)
1. **Frontend:** `DoctorProfile.tsx` → `fetchDoctorProfile(user)` → `supabase.from('doctor_profiles').select('*').eq('user_id', user.id).maybeSingle()` (`profile.ts:169–173`)
2. **Simpan:** `saveDoctorProfile(user, data)` → `validateProfileData` → `supabase.from('doctor_profiles').upsert(...)` (`profile.ts:287–289`) + `supabase.auth.updateUser({data: {doctor_profile: ...}})` (dual persistence)
3. **Backend:** Tidak ada endpoint Flask khusus profil; operasi langsung ke Supabase via RLS
4. **Status:** ✅ Terverifikasi

---

## 5. REPRESENTASI FRONTEND (Temuan F-01)

### 5.1 Apa yang diimplementasikan
Frontend PIXEL-T menggunakan **React 18 + TypeScript** dengan paradigma:
- **Function components** (bukan class components): `App.tsx`, `Login.tsx`, `Dashboard.tsx`, dst.
- **Custom hooks**: `useTheme`, `useOpeningAnimation`
- **Context API**: `AuthContext` (React context object, bukan class)
- **Module-level functions**: `services/analysis.ts`, `services/auth.ts`, `services/profile.ts` mengekspor fungsi, bukan class

### 5.2 Mengapa package dipaksa menjadi class di dalamnya
`class AnalysisClient`, `class AuthContext`, `class DoctorProfileService` di dalam package `Frontend` **bukan class OO sesungguhnya** — mereka merepresentasikan **modul fungsional**:
- `AnalysisClient` → kumpulan fungsi `createAnalysis`, `getAnalysis`, `listHistory`, `deleteAnalysis` dari `services/analysis.ts`
- `AuthContext` → React context object + fungsi `signIn`, `signUp`, `signOut` dari `context/AuthContext.tsx`
- `DoctorProfileService` → kumpulan fungsi `fetchDoctorProfile`, `saveDoctorProfile`, `calculateCompleteness`, `validateProfileData` dari `services/profile.ts`

### 5.3 Keputusan representasi
Frontend dipresentasikan sebagai **package** `<<package>>` yang berisi **tiga class** dengan stereotype `<<module>>` yang menunjukkan bahwa elemen-elemen tersebut adalah **representasi modul fungsional**, bukan class dengan state dan lifecycle. Alasan:
1. Setiap modul frontend memiliki tanggung jawab yang jelas dan dapat dipisahkan.
2. Dengan memakai class di dalam package, pembaca dapat melihat operasi yang diekspor tanpa harus membaca kode.
3. Package boundary menunjukkan bahwa ini adalah **satu layer terpisah** (presentation layer) yang berbeda dari backend.
4. Tidak memecah setiap React component menjadi class terpisah (sesuai instruksi: "Jangan memodelkan setiap komponen React sebagai kelas UML hanya demi menambah detail").

**Batas representasi:** Class-class di dalam `package "Frontend"` adalah **modul tingkat file** yang diekspor sebagai fungsi module-level. Stereotype `<<module>>` menandakan bahwa mereka adalah **kumpulan fungsi terkait**, bukan class dengan instance state.

---

## 6. AUDIT KONSISTENSI DOKUMEN

| Dokumen | Konsisten? | Catatan |
|---|---|---|
| `CLASS_DIAGRAM_FINAL_PIXELT.puml` | ✅ | Sumber utama diagram |
| `CLASS_DIAGRAM_FINAL_PIXELT.png` | ✅ | Dirender dari `.puml` terbaru; tidak ada syntax error |
| `CLASS_DIAGRAM_FINAL_PIXELT.svg` | ✅ | Dirender dari `.puml` terbaru; tidak ada syntax error |
| `MAPPING_CLASS_DIAGRAM_TO_CODE.md` | ✅ | Setiap kelas dan relasi dipetakan ke path + baris aktual |
| `NARASI_BAB_IV_CLASS_DIAGRAM_FINAL.md` | ✅ | Nama kelas, relasi, tanggung jawab identik dengan `.puml` |
| `LAPORAN_AUDIT_FINAL_CLASS_DIAGRAM_PIXELT.md` (ini) | ✅ | Berisi hasil audit aktual |
| `ANALISIS_DESAIN_CLASS_DIAGRAM_REFERENSI.md` | ✅ | Perbandingan gaya visual dengan `class_diagram_contoh.png` |
| `CHECKLIST_VALIDASI_CLASS_DIAGRAM.md` | ✅ | Setiap kotak dicentang setelah pemeriksaan aktual |

---

## 7. KETERBATASAN

1. **Renderer remote:** PNG dan SVG dirender via PlantUML remote server (HTTP 200, `image/svg+xml` / `image/png`). Jika server remote tidak tersedia, render tidak dapat diulang.
2. **Frontend representasi:** Package `Frontend` menggunakan tiga class yang **bukan class OO sesungguhnya** (lihat §5). Ini adalah kompromi antara keterbacaan diagram dan kejujuran representasi.
3. **Entitas database:** `analyses` dan `doctor_profiles` menampilkan **semua kolom** dari migrasi (39 dan 23 kolom). Jika diagram terlalu padat untuk halaman skripsi, subset kolom yang direlevansikan dapat dipilih, dan narasi harus menyatakan bahwa itu subset.
4. **`auth_users` hanya `id`:** Tabel `auth.users` dimiliki oleh Supabase Auth (eksternal). Hanya kolom `id` (FK target) yang ditampilkan karena kolom lain di luar kendali aplikasi.
5. **Alur runtime tidak divisualisasikan:** Class Diagram adalah model struktur statis. Alur runtime divisualisasikan pada Sequence Diagram dan Activity Diagram di folder terpisah (`references/bab 4/sequence_diagram/`, `references/bab 4/activity_diagrams/`).
6. **`tta_enabled` flag:** Catatan pada `segmentation.py:40–42` bahwa `tta_enabled` tidak dibaca oleh kode aktif (hanya `multiscale_enabled` dan `tta_scales` yang digunakan). Ini tidak mempengaruhi Class Diagram tetapi dicatat untuk audit kode.

---

## 8. KEPUTUSAN AKHIR

**Status: LAYAK DENGAN REVISI MINOR**

### Alasan:
1. **Semua kelas terverifikasi:** 19 kelas/representasi (7 backend + 6 AI + 3 entitas + 3 modul frontend) dalam 4 package semuanya ditemukan di kode sumber dengan path dan baris yang dapat ditelusuri.
2. **Semua atribut dan metode valid:** Tidak ada atribut/metode fiktif. Signature `StorageService.upload_file` sudah dikoreksi.
3. **Semua relasi didukung kode:** 20 relasi diverifikasi — 11 dependency, 7 asosiasi berarah, 2 association (FK); tidak ada composition.
4. **Alur runtime terverifikasi:** 6 alur utama (autentikasi, unggah, AI pipeline, progres, riwayat, profil) ditelusuri dari frontend ke backend ke database.
5. **Frontend representasi jelas:** Package `Frontend` dengan 3 class modul fungsional; batas representasi dijelaskan eksplisit pada §5.
6. **Visual sesuai referensi:** Monokrom, bold centered, `+`/`-`, `nama: tipe`, relasi sederhana, whitespace luas.

### Revisi minor (sudah diterapkan):
- Signature `StorageService.upload_file` dikoreksi dari `(filepath, content, content_type, user_id, analysis_id)` menjadi `(path, file_bytes, content_type, user_id, use_service_role)`.
- `Download_file` dan `generate_*_path` methods ditambahkan untuk kelengkapan.

### Tidak ada masalah struktural yang terbuka.
