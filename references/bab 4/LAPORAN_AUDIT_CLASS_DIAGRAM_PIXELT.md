# LAPORAN AUDIT MENYELURUH CLASS DIAGRAM — PIXEL-T

**Tanggal audit:** 2026-11-02  
**Objek audit:** `references\bab 4\class_diagram.png` (sumber utama, dikonfirmasi sebagai versi terkini/rich 14 elemen)  
**Ground truth:** `backend\app\**`, `ai\inference\**`, `frontend\src\**`, `database\migrations\*.sql`, `diagram-skripsi\class\class_diagram.puml`  
**Metode:** Pembacaan langsung PNG + PlantUML, pembacaan kode backend/frontend/AI/migrasi, pembandingan relasi satu per satu.  
**Batasan:** Audit bersifat read-only. Tidak ada sumber yang diubah. Tidak ada file `.drawio` sumber class diagram ditemukan. PlantUML render PNG/SVG tidak dilakukan (hanya Node.js tersedia, tidak ada renderer PlantUML); sediakan sumber `.puml` untuk dirender pengguna.

---

## 1. RINGKASAN EKSEKUTIF

- **Kesesuaian umum:** Diagram `class_diagram.png` **cukup akurat secara arsitektural** untuk sisi backend/layer AI/persistensi. Fokus pada struktur perangkat lunak peladen (OO backend + entitas DB), konsisten dengan tujuan Class Diagram yang dinyatakan narasi Bab IV.
- **Kekuatan utama:** Pembagian `AnalysisService` → `AnalysisRepository` / `StorageService` / `AIFlow`; penggunaan dependency (`..>`) yang tepat untuk penggunaan tanpa kepemilikan; pemodelan entitas `auth.users`/`analyses`/`doctor_profiles` sesuai skema migrasi; representasi `ModelService` sebagai singleton lazy-loader model terverifikasi; `AnalysisJobQueue` dan `PipelineResult`/`GradCAMResult`/`SegmentationResult` (`<<dataclass>>`) sudah dicantumkan.
- **Masalah utama:** Diagram **tidak menggambarkan layer presentasi/frontend** (React/TypeScript: `AuthContext`, `services/auth.ts`, `services/analysis.ts`, `services/profile.ts`, `pages/*`), **tidak menggambarkan layer HTTP** (`AnalysisController`, `routes/analysis.py`, `core/auth.py require_auth`, `core/errors.py`), dan **mencampurkan modul fungsional (`AIFlow <<module>>`) dengan kelas OO** tanpa penjelasan jelas. Ada ketidaksesuaian atribut/multiplicity dibanding skema aktual.
- **Tingkat keyakinan:** Tinggi untuk backend/AI/persistensi (berdasarkan bukti kode langsung). Sedang untuk representasi frontend (tidak ada di diagram).
- **Keputusan akhir:** **LAYAK DENGAN REVISI MINOR** — diagram perlu revisi tambahan layer HTTP + klarifikasi cakupan + penyesuaian atribut minor, bukan revisi struktural besar.

---

## 2. CAKUPAN & KELENGKAPAN AUDIT

### Sumber yang diperiksa

| ID | Berkas / Lokasi | Jenis | Status |
|----|-----------------|-------|--------|
| S-01 | `references\bab 4\class_diagram.png` | UML (sumber utama) | Diperiksa (visual) |
| S-02 | `diagram-skripsi\class\class_diagram.puml` | UML sumber (8 elemen, lebih sederhana) | Diperiksa penuh |
| S-03 | `references\bab 4\PENJELASAN_CLASS_DIAGRAM_PIXELT_BAB_IV.md` | Narasi Bab IV | Diperiksa |
| S-04 | `references\bab 4\SPESIFIKASI_REVISI_CLASS_DIAGRAM_PIXELT.md` | Klaim "FINAL" — **tidak terverifikasi** | Diperiksa (ditetapkan sebagai klaim, bukan bukti) |
| S-05 | `references\bab 4\class_diagram_contoh.png` | Gambar contoh | Tidak relevan (bukan sumber utama) |
| S-06 | `backend\app\services\analysis_service.py` (991 baris) | Backend service | Diperiksa penuh |
| S-07 | `backend\app\repositories\analysis_repository.py` (196 baris) | Backend repository | Diperiksa penuh |
| S-08 | `backend\app\services\storage_service.py` (189 baris) | Backend storage | Diperiksa penuh |
| S-09 | `backend\app\controllers\analysis_controller.py` (96 baris) | Backend controller | Diperiksa penuh |
| S-10 | `backend\app\routes\analysis.py` (60 baris) | Backend routes | Diperiksa penuh |
| S-11 | `backend\app\core\{config,auth,errors,supabase}.py` | Backend core | Diperiksa |
| S-12 | `ai\inference\{pipeline,model_service,gradcam,segmentation,postprocessing,preprocessing}.py` | AI pipeline | Diperiksa |
| S-13 | `ai\config\model_config.py` (70 baris) | AI config | Diperiksa penuh |
| S-14 | `database\migrations\{001,002,003,004}_*.sql` | Schema | Diperiksa penuh |
| S-15 | `frontend\src\services\{auth,analysis,profile}.ts` | Frontend services | Diperiksa |
| S-16 | `frontend\src\context\AuthContext.tsx` | Frontend auth | Diperiksa |
| S-17 | `frontend\src\lib\supabase.ts` | Frontend supabase client | Diperiksa |
| S-18 | `backend\run.py`, `backend\app\__init__.py` | App factory | Diperiksa |

### Sumber yang tidak ditemukan / tidak dapat diakses
- Tidak ditemukan file `.drawio` sumber class diagram di lokasi mana pun di proyek. Hanya `.puml` dan `.png`.
- Tidak ada renderer PlantUML tersedia (hanya Node.js); PNG/SVG dari revisi `.puml` tidak dapat dirender oleh agen.
- Beberapa halaman Bab IV `.docx` (Bab IV audit terpisah) tidak termasuk dalam cakupan tugas class diagram ini.

---

## 3. HASIL ANALISIS VISUAL UML

### 3.1 Elemen dalam diagram (`class_diagram.png`)

Diagram berisi 14 elemen, dikelompokkan sebagai berikut:

**Entitas (`<<entity>>`):**
- `analyses` — ~19 atribut (id, user_id, status, original_image_path, original_filename, binary_mask_path, segmentation_overlay_path, segmentation_status, area_pixels, area_ratio, gradcam_heatmap_path, gradcam_overlay_path, gradcam_status, summary_text, current_step, progress_percent, error_code, error_message, created_at, completed_at).
- `doctor_profiles` — 8 atribut (id, user_id, full_name, primary_specialty, hospital, education, experience, bio).

**Entitas eksternal (`<<external>>`):**
- `auth.users` — 1 atribut (`id: UUID`); relasi `1--0..*` ke `analyses`, `1--0..1` ke `doctor_profiles`.

**Service / Repository:**
- `AnalysisService` (`<<service>>`) — atribut: `repository`, `storage_service`, `pipeline_runner`, `job_queue`. Metode: `create_analysis`, `get_analysis`, `list_user_analyses`, `delete_analysis`.
- `AnalysisRepository` (`<<repository>>`) — metode: `create`, `get_by_id`, `list_by_user`, `update`, `delete`.
- `StorageService` (`<<service>>`) — atribut: `bucket_name`. Metode: `upload_file`, `create_signed_url`, `delete_analysis_files`.
- `ModelService` (`<<service>>`) — atribut: `config`, `device`, `load_count`. Metode: `load`, `metadata`, `predict_logits`, `get_gradcam_target_layer`.

**Modul / Data class:**
- `AI inference functions` (`<<module>>`) — fungsi: `run_pipeline`, `predict`, `postprocess_mask`, `measure_mask`, `generate_gradcam`.
- `PipelineResult` (`<<dataclass>>`) — `binary_mask_png`, `segmentation_overlay_png`, `gradcam_heatmap_png`, `gradcam_overlay_png`, `measurements`, `summary_text`, `gradcam`.
- `SegmentationResult` (`<<dataclass>>`) — `probability_map`, `binary_mask`, `threshold`.
- `GradCAMResult` (`<<dataclass>>`) — `heatmap`, `overlay`, `target_layer`, `target_objective`, `target_mask_empty`.
- `AnalysisJobQueue` (`<<service>>`) — atribut: `capacity`. Metode: `try_enqueue`, `contains`, `pending_count`, `drain_one`.
- `ModelConfig` (`<<dataclass>>`) — atribut: `architecture`, `encoder`, `decoder_attention`, `gradcam_target_layer`, `framework`, `library`, `model_version`, `input_size`, `input_channels`, `threshold`, `tta_enabled`, `multiscale_enabled`, `tta_scales`, `postprocessing_enabled`, `postprocessing_min_area`, `contour_smoothing`, `smoothing_epsilon`, `checkpoint_filename`, `checkpoint_sha256`.

**Controller:**
- `AnalysisController` (`<<controller>>`) — atribut: `service`. Metode: `create_analysis`, `get_analysis`, `list_history`, `delete_analysis`.

### 3.2 Relasi dalam diagram

| Relasi | Jenis | Multiplicity / Label | Arah |
|--------|-------|----------------------|------|
| `auth.users` ↔ `analyses` | Association (DB) | `1` -- `0..*` (FK user_id) | Dua arah |
| `auth.users` ↔ `doctor_profiles` | Association (DB) | `1` -- `0..1` (FK user_id UNIQUE) | Dua arah |
| `AnalysisService` → `AnalysisRepository` | Dependency (`..>`) | persistence | AnalysisService → AnalysisRepository |
| `AnalysisService` → `StorageService` | Dependency (`..>`) | upload / assets | AnalysisService → StorageService |
| `AnalysisService` → `AIFlow` | Dependency (`..>`) | background pipeline | AnalysisService → AI inference functions |
| `AnalysisService` → `AnalysisJobQueue` | Composition / dependency | queue | AnalysisService → AnalysisJobQueue |
| `AnalysisRepository` → `analyses` | Dependency (`..>`) | CRUD | AnalysisRepository → analyses |
| `AIFlow` → `ModelService` | Dependency (`..>`) | inference / Grad-CAM | AI inference functions → ModelService |
| `AIFlow` → `PipelineResult` | Dependency (`..>`) | predict output | AI inference functions → PipelineResult |
| `ModelService` → `ModelConfig` | Dependency / uses | uses | ModelService → ModelConfig |
| `AnalysisController` → `AnalysisService` | Dependency (`..>`) | calls | AnalysisController → AnalysisService |

### 3.3 Temuan notasi UML

| ID | Kategori | Temuan | Penjelasan |
|----|----------|--------|------------|
| N-01 | MINOR | `AI inference functions <<module>>` berisi fungsi, bukan kelas OO | Dapat diterima jika dijelaskan sebagai modul, namun bisa membingungkan pembaca yang mengharapkan kelas dengan state. Disarankan ditandai sebagai modul/paket terpisah atau diberi catatan. |
| N-02 | MINOR | `AnalysisService.pipeline_runner` bertipe `Callable[..., PipelineResult]` | Representasi tipe callable dalam UML kurang idiomatik; lebih baik direpresentasikan sebagai dependency/interface atau dilewatkan pada detail atribut. |
| N-03 | MINOR | Tidak ada penanda navigability eksplisit | Kebanyakan relasi cukup sebagai dependensi/association. Dapat diterima untuk diagram tingkat tinggi. |

---

## 4. PEMETAAN KELAS DIAGRAM KE KODE

| ID | Kelas pada diagram | Lokasi implementasi | Atribut sesuai | Metode sesuai | Status | Bukti |
|----|--------------------|---------------------|----------------|---------------|--------|-------|
| M-01 | `AnalysisService` | `backend\app\services\analysis_service.py:269-991` | Sebagian (diagram: `repository`, `storage_service`, `pipeline_runner`, `job_queue`; kode juga punya `auto_start_worker`) | Sebagian besar cocok (`create_analysis:369`, `get_analysis:502`, `list_user_analyses:635`, `delete_analysis:688`). Diagram tidak menampilkan `AnalysisJobQueue` (sudah ada di PNG), `AnalysisProgressReporter` (tidak ada di PNG), metode internal `_run_analysis_job:761`, `_execute_pipeline:781` | Sesuai sebagian | Kelas ada; atribut publik/field sesuai; metode utama ada. `AnalysisProgressReporter:64` tidak dimodelkan. |
| M-02 | `AnalysisRepository` | `backend\app\repositories\analysis_repository.py:5-196` | Tidak ditampilkan detail atribut di diagram | Cocok: `create:38`, `get_by_id:71`, `list_by_user:100`, `update:133`, `delete:172`; validasi `ALLOWED_STATUSES:12`, `ALLOWED_SEGMENTATION_STATUSES:13` | Sesuai | Tanda tangan sesuai; validasi status ada. |
| M-03 | `StorageService` | `backend\app\services\storage_service.py:7-189` | `bucket_name:19` ada | Cocok: `generate_asset_path:39`, `upload_file`, `create_signed_url`, `delete_analysis_files`. Diagram tidak mencantumkan metode pembantu path (`sanitize_id:32`, `generate_original_image_path:59`, dll.) | Sesuai sebagian | Metode inti ada; metode pembantu path tidak dicantumkan (wajar disederhanakan). |
| M-04 | `ModelService` | `ai\inference\model_service.py:19-136` | `config:23`, `device`, `load_count` ada | Cocok: `load:61`, `metadata:95`, `predict_logits:112`, `get_gradcam_target_layer:129` | Sesuai | Singleton/lazy loading, lock, device selection, validasi checkpoint sesuai diagram. |
| M-05 | `AI inference functions` (`<<module>>`) | `ai\inference\pipeline.py`, `segmentation.py`, `postprocessing.py`, `gradcam.py` | N/A (modul) | Sebagian cocok: `run_pipeline:101`, `predict:98`, `postprocess_mask:26`, `measure_mask`, `generate_gradcam:99`. Tidak ada `preprocessing`, `resize_binary_mask`, `count_forward_passes:43`; class hasil (`PipelineResult:63`, `SegmentationResult:24`, `GradCAMResult:37`) dimodelkan terpisah | Sesuai sebagian | Fungsi ada; diagram tidak mencantumkan semua fungsi pembantu (wajar disederhanakan). |
| M-06 | `auth.users` (`<<external>>`) | Dikelola Supabase Auth; referensi di migrasi & kode | Hanya `id` ditampilkan | N/A | Sesuai sebagai entitas eksternal | `database\migrations\001_create_analyses_and_storage.sql:17` (REFERENCES auth.users(id)); `004_create_doctor_profiles.sql:12` |
| M-07 | `analyses` (`<<entity>>`) | `database\migrations\001_create_analyses_and_storage.sql:14-65`, `002`, `003` | Sebagian cocok. Diagram ~19 atribut; migrasi 001+002+003 memiliki ~39 kolom | N/A | Sesuai sebagian | Lihat bagian 7 (basis data). |
| M-08 | `doctor_profiles` (`<<entity>>`) | `database\migrations\004_create_doctor_profiles.sql:10-47` | Diagram sangat minimal (8 atribut); migrasi punya 22 kolom | N/A | Sesuai sebagian | Sangat disederhanakan dibanding skema aktual. Lihat bagian 7. |
| M-09 | `AnalysisController` | `backend\app\controllers\analysis_controller.py:7-96` | `service:10` ada | Cocok: `create_analysis:13`, `get_analysis:41`, `list_history:61`, `delete_analysis:79` | **Tidak ada di diagram** | Kelas ada dan penting (MVC/controller pattern), tetapi tidak dimodelkan dalam `class_diagram.png`. |
| M-10 | `AnalysisProgressReporter` | `backend\app\services\analysis_service.py:64-148` | Atribut: `_repository`, `_analysis_id`, `_user_id`, `total_units`, `throttle`, `completed_units`, `passes_done`, `last_percent`, `last_step`, `failed_writes` | Metode: `on_phase:110`, `on_pass:116`, `percent:105`, `last_step:96` | **Tidak ada di diagram** | Kelas ada dan kritis untuk progress tracking async, tetapi tidak dimodelkan. |
| M-11 | `APIError` | `backend\app\core\errors.py:8-23` | `code`, `message`, `status_code` | `to_dict:16` | **Tidak ada di diagram** | Kelas error standar, tidak dimodelkan. |
| M-12 | `Config` | `backend\app\core\config.py:7-59` | `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_STORAGE_BUCKET`, `MAX_CONTENT_LENGTH`, dll. | `get_config()` | **Tidak ada di diagram** | Kelas konfigurasi aplikasi, tidak dimodelkan. |

**Catatan:** `AnalysisController`, `AnalysisProgressReporter`, `APIError`, `Config` ada di kode tetapi **tidak ada** di `class_diagram.png`. Ini adalah kelalaian representasi, bukan bukti mereka tidak ada. `AnalysisJobQueue` (yang sebelumnya dianggap hilang) **sudah ada** di PNG (elemen `<<service>>` dengan `capacity`, `try_enqueue`, `contains`, `pending_count`, `drain_one`).

---

## 5. HASIL AUDIT RELASI

| ID | Relasi pada diagram | Jenis | Bukti implementasi | Penilaian | Rekomendasi |
|----|---------------------|-------|--------------------|-----------|-------------|
| R-01 | `auth.users` `"1"` -- `"0..*"` `analyses` : FK user_id | Association (DB) | `analyses.user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE` (`001_create_analyses_and_storage.sql:17`) | Sesuai | Pertahankan. |
| R-02 | `auth.users` `"1"` -- `"0..1"` `doctor_profiles` : FK user_id UNIQUE | Association (DB) | `doctor_profiles.user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`; `CONSTRAINT doctor_profiles_user_id_key UNIQUE (user_id)` (`004_create_doctor_profiles.sql:12,46`) | Sesuai | Pertahankan. |
| R-03 | `AnalysisService` `..>` `AnalysisRepository` : persistence | Dependency | `AnalysisService.__init__` membuat `self.repository = repository or AnalysisRepository()` (`analysis_service.py:291`) | Sesuai (sebagai dependency, atau composition jika dianggap kepemilikan) | Pertahankan; jika ingin komposisi, gunakan `*--` konsisten. |
| R-04 | `AnalysisService` `..>` `StorageService` : upload / assets | Dependency | `self.storage_service = storage_service or StorageService()` (`analysis_service.py:292`) | Sesuai | Pertahankan. |
| R-05 | `AnalysisService` `..>` `AIFlow` : background pipeline | Dependency | `self.pipeline_runner = pipeline_runner or run_pipeline` (`analysis_service.py:293`); dipanggil dari `_execute_pipeline` (`:781-953`) | Sesuai | Pertahankan. |
| R-06 | `AnalysisService` → `AnalysisJobQueue` | Composition / dependency | `self.job_queue = job_queue or AnalysisJobQueue(...)` (`analysis_service.py:296-299`) | Sesuai (komposisi masuk akal karena service membuat instance default) | Pertahankan; konsisten dengan R-03/R-04 jika menggunakan `*--`. |
| R-07 | `AnalysisRepository` `..>` `analyses` : CRUD | Dependency | `AnalysisRepository.create/get_by_id/list_by_user/update/delete` mengoperasikan tabel `analyses` (`analysis_repository.py:38-196`) | Sesuai | Pertahankan. |
| R-08 | `AIFlow` `..>` `ModelService` : inference / Grad-CAM | Dependency | `_DEFAULT_MODEL_SERVICE = ModelService(MODEL_CONFIG)` (`segmentation.py:16`); `predict(...model_service)` (`segmentation.py:98`); `generate_gradcam(...model_service)` (`gradcam.py:99`) | Sesuai | Pertahankan. |
| R-09 | `AIFlow` `..>` `PipelineResult` : predict output | Dependency | `run_pipeline` mengembalikan `PipelineResult` (`pipeline.py:63-70,101`) | Sesuai | Pertahankan. |
| R-10 | `ModelService` → `ModelConfig` : uses | Dependency / association | `ModelService.__init__(self, config: ModelConfig = MODEL_CONFIG)` (`model_service.py:22`) | Sesuai | Pertahankan. |
| R-11 | `AnalysisController` `..>` `AnalysisService` : calls | Dependency | `self.service = service or AnalysisService()` (`analysis_controller.py:10-11`) | Sesuai | Pertahankan; namun `AnalysisController` seharusnya ada di diagram. |
| R-12 | `AnalysisService` → `AnalysisProgressReporter` (implisit) | **Tidak ada di diagram** | `AnalysisProgressReporter` dibuat di `_execute_pipeline` untuk menulis `current_step`/`progress_percent` (`analysis_service.py:64-148`) | **Tidak dimodelkan** | Tambahkan relasi dependency/composition `AnalysisService --> AnalysisProgressReporter` (lihat temuan F-02). |

**Kesimpulan audit relasi:** Tidak ada relasi yang salah jenis secara fundamental. Relasi yang hilang adalah relasi ke `AnalysisController` (diagram tidak menampilkannya) dan `AnalysisProgressReporter`. Diagram juga tidak menunjukkan `AnalysisService` menggunakan `AnalysisJobQueue` sebagai komposisi eksplisit (meskipun ada di PNG, jadi relasi ini sebagian sudah tercakup). Perbedaan `..>` vs `*--` untuk `AnalysisService`→`AnalysisRepository`/`StorageService`/`AnalysisJobQueue` dapat dipertahankan sebagai dependency karena service menerima injeksi dependensi di `__init__`; jika dimaksudkan sebagai komposisi, gunakan `*--` secara konsisten.

---

## 6. HASIL AUDIT FITUR PIXEL-T (7 FITUR)

| Fitur | Komponen yang terlibat (kode) | Representasi dalam Class Diagram | Bukti kode | Status |
|-------|-------------------------------|----------------------------------|------------|--------|
| **Sign Up** | Frontend: `Register.tsx`, `services/auth.ts` (`registerUser` → `supabase.auth.signUp`), `AuthContext` (`signUp`). Backend: tidak terlibat langsung (Supabase Auth) | Hanya `auth.users` (`<<external>>`). Tidak ada kelas frontend. | `frontend\src\services\auth.ts:131-188`; `frontend\src\context\AuthContext.tsx:19-33` | **Sesuai sebagian** — diagram tidak perlu memodelkan frontend, tetapi cakupannya perlu dijelaskan. |
| **Sign In** | Frontend: `Login.tsx`, `services/auth.ts` (`signInWithPassword`), `AuthContext` (`signIn`). Backend auth via `core/auth.py` (`require_auth`) | Tidak dimodelkan (hanya `auth.users` eksternal) | `frontend\src\services\auth.ts:193-222`; `backend\app\core\auth.py:7-80` | **Sesuai sebagian** |
| **Upload Image** | Frontend: `pages\analysis\NewAnalysis.tsx`, `services\analysis.ts` (`createAnalysis`). Backend: `routes\analysis.py`, `controllers\analysis_controller.py`, `services\analysis_service.py`, `storage_service.py`, `repositories\analysis_repository.py` | `AnalysisController` (tidak ada), `AnalysisService`, `StorageService`, `AnalysisRepository`, `analyses` | `routes\analysis.py:11-26`; `controllers\analysis_controller.py:13-40`; `services\analysis_service.py:369-500` | **Sesuai** (kecuali controller tidak dimodelkan) |
| **Segmentation** | Backend worker: `AnalysisService._execute_pipeline`, `ai\inference\pipeline.py`, `segmentation.py`, `postprocessing.py`, `gradcam.py`, `model_service.py`. Storage: `StorageService`. DB: `analyses` | `AnalysisService`, `AIFlow`, `ModelService`, `StorageService`, `AnalysisJobQueue`, `PipelineResult`, `SegmentationResult`, `GradCAMResult`, `analyses` | `services\analysis_service.py:761-953`; `ai\inference\pipeline.py:101-165`; `ai\inference\model_service.py:61-136` | **Sesuai sebagian** (diagram tidak menampilkan `AnalysisProgressReporter`) |
| **History** | Frontend: `pages\history\History.tsx`, `pages\history\HistoryDetail.tsx`, `services\analysis.ts` (`listHistory`, `deleteAnalysis`). Backend: controller/service/repo | `AnalysisService`, `AnalysisRepository`, `analyses` | `routes\analysis.py:43-60`; `controllers\analysis_controller.py:61-96`; `services\analysis_service.py:635-759` | **Sesuai** |
| **Doctor Profile** | Frontend: `pages\profile\DoctorProfile.tsx`, `services\profile.ts` (upsert `doctor_profiles`, sync `auth.updateUser`). Backend: tidak wajib untuk CRUD profil (frontend langsung Supabase) | `doctor_profiles`, `auth.users` | `frontend\src\services\profile.ts:131-299`; `database\migrations\004_create_doctor_profiles.sql` | **Sesuai sebagian** (diagram tidak menggambarkan frontend/service layer) |
| **Sign Out** | Frontend: `AuthContext.signOut()` → `logoutUser()` → `supabase.auth.signOut()`. Backend: tidak ada endpoint signout khusus | `auth.users` eksternal | `frontend\src\services\auth.ts:266-276`; `frontend\src\context\AuthContext.tsx` | **Sesuai sebagian** |

**Kesimpulan fitur:** Ketujuh fitur dapat dijelaskan melalui kelas-kelas yang ada di diagram, tetapi tiga fitur (Sign Up, Sign In, Sign Out) sepenuhnya bergantung pada layer frontend/Supabase Auth yang tidak dimodelkan. Upload Image, History, dan Segmentation paling terwakili karena komponen backend-nya ada di diagram. Doctor Profile sebagian terwakili oleh entitas `doctor_profiles`.

---

## 7. HASIL AUDIT BASIS DATA & PENYIMPANAN

### 7.1 Perbandingan `analyses` (diagram vs migrasi)

**Diagram `analyses` (subset ~19 atribut):**
`id, user_id, status, original_image_path, original_filename, binary_mask_path, segmentation_overlay_path, segmentation_status, area_pixels, area_ratio, gradcam_heatmap_path, gradcam_overlay_path, gradcam_status, summary_text, current_step, progress_percent, error_code, error_message, created_at, completed_at`

**Migrasi aktual (konsolidasi 001+002+003):**
- `001_create_analyses_and_storage.sql:14-65` — `id, user_id, status, original_image_path, original_filename, original_mime_type, original_width, original_height, binary_mask_path, segmentation_overlay_path, segmentation_status, area_pixels, area_ratio, bounding_width_pixels, bounding_height_pixels, gradcam_heatmap_path, gradcam_overlay_path, gradcam_target_layer, gradcam_method, gradcam_config_version, model_architecture, model_version, model_config_version, model_input_size, model_threshold, tta_enabled, postprocessing_enabled, summary_text, error_code, error_message, created_at, completed_at, updated_at`
- `002_add_ai_pipeline_metadata.sql:3-6` — `model_checkpoint_sha256, tta_scales, tta_orientations, gradcam_status`
- `003_add_analysis_progress.sql:6-7` — `current_step, progress_percent`

**Temuan:** Diagram **menyederhanakan** `analyses`; banyak kolom metadata model/reproduktibilitas tidak ditampilkan (`original_mime_type`, `original_width`, `original_height`, `bounding_width_pixels`, `bounding_height_pixels`, `gradcam_target_layer`, `gradcam_method`, `gradcam_config_version`, `model_architecture`, `model_version`, `model_config_version`, `model_input_size`, `model_threshold`, `tta_enabled`, `postprocessing_enabled`, `model_checkpoint_sha256`, `tta_scales`, `tta_orientations`, `updated_at`). Ini wajar untuk Class Diagram tingkat tinggi, tetapi dapat menyesatkan jika dibaca sebagai representasi skema lengkap.

### 7.2 Perbandingan `doctor_profiles` (diagram vs migrasi)

**Diagram:** `id, user_id, full_name, primary_specialty, hospital, education, experience, bio` (8 atribut)

**Migrasi `004_create_doctor_profiles.sql:10-47`:** `id, user_id, full_name, phone, birth_date, city, profession_category, academic_title, primary_specialty, subspecialty, clinical_focus, hospital, department, clinical_role, years_experience, practice_address, str_number, is_verified, bio, education, experience, created_at, updated_at` (22 kolom)

**Temuan:** Diagram menghilangkan 15 kolom (antara lain `phone`, `birth_date`, `city`, `profession_category`, `academic_title`, `subspecialty`, `clinical_focus`, `department`, `clinical_role`, `years_experience`, `practice_address`, `str_number`, `is_verified`, `created_at`, `updated_at`).

### 7.3 Penyimpanan (Supabase Storage)

| Aspek | Diagram | Kode / Konfigurasi | Status |
|-------|---------|--------------------|--------|
| Bucket | `bucket_name` di `StorageService` | `SUPABASE_STORAGE_BUCKET = 'analysis-assets'` (`backend\app\core\config.py:25`; `storage_service.py:20`) | Sesuai |
| Pola path | Tidak detail | `analysis/{user_id}/{analysis_id}/{category}/{filename}` (`storage_service.py:39-58`) | Sesuai (tidak digambarkan, wajar) |
| Kategori aset | Tidak detail | `ALLOWED_CATEGORIES = {'original','segmentation','gradcam'}` (`storage_service.py:14`) | Sesuai |
| Nama file | Tidak detail | `input.{ext}`, `mask.png`, `overlay.png`, `heatmap.png` (`storage_service.py:59-82`) | Sesuai |
| RLS | Tidak digambarkan | `ALTER TABLE ... ENABLE ROW LEVEL SECURITY` (`001:74`; `004:53`) | Sesuai (tidak digambarkan, wajar) |
| Signed URL | `create_signed_url` ada di diagram | `create_signed_url` di `storage_service.py` | Sesuai |

### 7.4 Campuran model (OO class vs entity vs ERD)

Diagram mencampurkan **entitas DB (`<<entity>>`)**, **kelas aplikasi/service**, dan **modul fungsional**. Ini masih umum dalam diagram desain terintegrasi, namun harus dipahami bahwa `analyses`/`doctor_profiles` merepresentasikan **row data**, bukan objek perilaku kaya seperti service. Pendekatan ini cukup dapat diterima untuk skripsi S1 dengan penjelasan eksplisit pada narasi.

---

## 8. KONSISTENSI DENGAN DOKUMEN SKRIPSI

| Aspek | Penilaian | Catatan |
|-------|-----------|---------|
| Konsistensi dengan Bab III (arsitektur) | **Cukup** | Diagram sesuai arsitektur service/repository + pipeline AI. |
| Konsistensi dengan Use Case / Sequence / Activity | **Cukup** | Relasi `AnalysisService`–`StorageService`–`AIFlow` konsisten dengan alur upload/segmentasi/history. |
| Konsistensi dengan ERD (Gambar 4.17) | **Perlu hati-hati** | ERD lebih lengkap untuk skema; Class Diagram lebih abstrak. Pastikan dijelaskan perbedaan fokus (OO vs relasional). |
| Narasi vs gambar | **Perlu verifikasi** | Pastikan narasi Bab IV tidak menyebut atribut yang tidak ada di diagram, atau sebaliknya. |
| Nama komponen | **Sebagian besar konsisten** | `AnalysisService`, `StorageService`, `AnalysisRepository`, `ModelService`, `AnalysisJobQueue`, `ModelConfig`, `PipelineResult`, `SegmentationResult`, `GradCAMResult` cocok dengan kode. |

**Sumber narasi yang diperiksa:** `references\bab 4\PENJELASAN_CLASS_DIAGRAM_PIXELT_BAB_IV.md` — menyatakan bahwa frontend React (komponen fungsional) tidak dimodelkan sebagai kelas OO (baris 13). Ini adalah keputusan desain yang eksplisit dan konsisten dengan isi diagram.

**Sumber klaim yang ditolak sebagai bukti:** `references\bab 4\SPESIFIKASI_REVISI_CLASS_DIAGRAM_PIXELT.md` mengklaim diagram "FINAL — LAYAK DIMASUKKAN TANPA REVISI STRUKTURAL" dan "100% terverifikasi". Klaim ini **tidak diterima sebagai bukti** dan dibantah oleh temuan F-01, F-02, dan F-03 (lihat bagian 9). Status "FINAL" pada dokumen tersebut tidak boleh dijadikan dasar keputusan tanpa verifikasi independen.

---

## 9. DAFTAR TEMUAN

| ID | Kategori | Tingkat | Temuan | Bukti | Dampak | Rekomendasi |
|----|----------|---------|--------|-------|--------|-------------|
| **F-01** | Cakupan diagram | **MAJOR** | Layer presentasi frontend (React/TypeScript: `AuthContext`, `services/auth.ts`, `services/analysis.ts`, `services/profile.ts`, `pages/*`, `components/*`, `routes/AppRoutes.tsx`) tidak dimodelkan. Diagram hanya mencakup backend/AI/DB. | `references\bab 4\class_diagram.png` (14 elemen server-side); `frontend\src\context\AuthContext.tsx`; `frontend\src\services\{auth,analysis,profile}.ts`; `frontend\src\pages\{auth,analysis,history,profile,dashboard}\*` | Diagram tidak merepresentasikan arsitektur full-stack. Pembaca dapat menyimpulkan sistem hanya backend. Fitur Sign Up/Sign In/Sign Out sepenuhnya bergantung pada layer yang tidak terlihat. | Tambahkan layer `Frontend`/`Client` sebagai paket terpisah (bukan setiap komponen React sebagai kelas), atau nyatakan cakupan eksplisit pada caption/legenda: "Class Diagram ini memodelkan lapisan peladen; frontend React dijelaskan pada narasi." Jangan memodelkan seluruh komponen React sebagai kelas. |
| **F-02** | Komponen async / progress | **MAJOR** | `AnalysisProgressReporter` (`analysis_service.py:64-148`) tidak dimodelkan, padahal kelas ini bertanggung jawab menulis `current_step` dan `progress_percent` ke tabel `analyses` selama pipeline berjalan. `AnalysisJobQueue` sudah ada di diagram, tetapi reporter progres tidak. | `backend\app\services\analysis_service.py:64-148` (`class AnalysisProgressReporter`, `on_phase:110`, `on_pass:116`, `_write:126`); kolom `current_step`/`progress_percent` (`003_add_analysis_progress.sql:6-7`) | Struktur pemrosesan asinkron tidak lengkap. Hubungan antara `AnalysisService`, `AnalysisJobQueue`, dan pembaruan progres DB tidak dapat dijelaskan dari diagram. | Tambahkan kelas `AnalysisProgressReporter <<service>>` dengan atribut (`repository`, `analysis_id`, `user_id`, `total_units`, `throttle`, `completed_units`, `failed_writes`) dan metode (`on_phase`, `on_pass`, `percent`). Hubungkan dengan dependency ke `AnalysisRepository` (menulis progres) dan asosiasi ke `AnalysisService`/`AnalysisJobQueue`. |
| **F-03** | Layer HTTP | **MINOR** | Layer HTTP tidak lengkap: `AnalysisController` sudah ada di diagram, tetapi `routes/analysis.py` (Blueprint + `@require_auth`), `core/auth.py` (`require_auth`), `core/errors.py` (`APIError`), dan `app/__init__.py` (app factory) tidak dimodelkan. | `backend\app\routes\analysis.py:7-60`; `backend\app\core\auth.py:7-80`; `backend\app\core\errors.py:8-23`; `backend\app\__init__.py:8-33` | Alur request HTTP, autentikasi Bearer, dan error envelope tidak terlihat. `AnalysisController` yang ada tidak menunjukkan batas autentikasi. | Tambahkan relasi `AnalysisController ..> APIError` dan catatan `<<route>>`/`<<auth>>`, atau tambahkan kelas `AuthMiddleware`/`Routes` ringkas. Minimal, tambahkan operasi `+create_analysis(...)` dengan tipe respons HTTP pada `AnalysisController`. |
| **F-04** | Basis data | **MINOR** | Entitas `analyses` dan `doctor_profiles` menampilkan subset atribut yang jauh lebih sedikit daripada migrasi aktual. | `001_create_analyses_and_storage.sql:14-65`; `002_add_ai_pipeline_metadata.sql:3-6`; `003_add_analysis_progress.sql:6-7`; `004_create_doctor_profiles.sql:10-47` | Metadata reproduktibilitas model (mis. `model_checkpoint_sha256`, `tta_scales`, `gradcam_target_layer`, `postprocessing_enabled`) dan sebagian besar kolom profil dokter tidak terlihat. Dapat menyesatkan jika dibaca sebagai skema lengkap. | Beri catatan bahwa atribut entitas bersifat **ilustratif/subset** dan rujuk ERD untuk skema lengkap; atau tambahkan atribut kunci yang relevan dengan penelitian (mis. `model_version`, `model_threshold`, `updated_at`). Jangan menambahkan seluruh 39/22 kolom jika membuat diagram terlalu padat. |
| **F-05** | Notasi UML | **MINOR** | `AI inference functions <<module>>` memuat fungsi, bukan kelas OO; `pipeline_runner: Callable[..., PipelineResult]` kurang idiomatik. | `ai\inference\pipeline.py:101`; `ai\inference\segmentation.py:98`; `ai\inference\gradcam.py:99`; `analysis_service.py:293` | Pembaca yang mengharapkan kelas dengan state dapat bingung; tipe callable tidak baku dalam UML. | Beri stereotype `<<module>>` dengan catatan "stateless functions" atau pisahkan menjadi paket `AI`; ganti `pipeline_runner` dengan dependency ke `AIFlow`/interface `PipelineRunner`. |
| **F-06** | Atribut | **MINOR** | `ModelConfig <<dataclass>>` hanya menampilkan sebagian atribut; kode memiliki 19 field + 2 properti/metode. | `ai\config\model_config.py:18-66` | Atribut reproduktibilitas (`postprocessing_min_area`, `contour_smoothing`, `smoothing_epsilon`, `checkpoint_filename`, `checkpoint_sha256`) dan operasi (`checkpoint_path`, `validate`, `checkpoint_sha256_matches`) tidak terlihat. | Tambahkan atribut/operasi kunci atau beri catatan subset. |
| **F-07** | Konsistensi dokumen | **BELUM TERVERIFIKASI** | Kesesuaian narasi Bab IV (`PENJELASAN_CLASS_DIAGRAM_PIXELT_BAB_IV.md`) dengan gambar dan kode belum diverifikasi baris demi baris dalam audit ini. | `references\bab 4\PENJELASAN_CLASS_DIAGRAM_PIXELT_BAB_IV.md` | Risiko narasi menyebut kelas/atribut yang tidak ada di gambar atau kode. | Lakukan pembacaan silang narasi vs gambar vs kode sebelum finalisasi. |

**Catatan tingkat:** F-01 dan F-02 diberi **MAJOR** karena memengaruhi kelengkapan representasi struktur (frontend layer dan komponen async inti). F-03–F-06 **MINOR** karena tidak mengubah struktur dasar dan mudah diperbaiki. F-07 **BELUM TERVERIFIKASI** karena keterbatasan cakupan audit ini.

---

## 10. REKOMENDASI CLASS DIAGRAM FINAL

### 10.1 Prinsip revisi

1. Pertahankan seluruh elemen yang sudah benar (backend/AI/DB core).
2. Tambahkan **hanya** komponen yang didukung kode: `AnalysisProgressReporter`, `AnalysisController` (sudah ada), relasi HTTP/auth.
3. Jangan memodelkan setiap komponen React sebagai kelas; gunakan satu paket `Frontend` atau catatan cakupan.
4. Gunakan notasi UML 2.x yang konsisten: `..>` untuk dependency, `*--` untuk composition bila service membuat instance default, `--` untuk asosiasi DB.
5. Beri catatan bahwa atribut entitas adalah subset ilustratif dan rujuk ERD.

### 10.2 Spesifikasi kelas final (tambahan/perubahan)

| Kelas | Stereotype | Atribut | Operasi | Alasan |
|-------|------------|---------|---------|--------|
| `AnalysisProgressReporter` | `<<service>>` | `-repository: AnalysisRepository`, `-analysis_id: str`, `-user_id: str`, `+total_units: int`, `+completed_units: int`, `+failed_writes: int` | `+on_phase(step: str): None`, `+on_pass(): None`, `+percent(): int`, `+last_step(): Optional[str]` | F-02: komponen progres async yang tidak boleh hilang. |
| `AnalysisController` | `<<controller>>` | `-service: AnalysisService` | `+create_analysis(): Response`, `+get_analysis(analysis_id: str): Response`, `+list_history(): Response`, `+delete_analysis(analysis_id: str): Response` | F-03: lengkapi operasi controller. |
| `APIError` | `<<exception>>` | `+code: str`, `+message: str`, `+status_code: int` | `+to_dict(): dict` | F-03: error envelope standar. |
| `Frontend (React/TS)` | `<<package>>`/`<<note>>` | — | — | F-01: nyatakan cakupan tanpa memaksakan kelas per komponen. |

### 10.3 Relasi final yang direkomendasikan

- `AnalysisController ..> AnalysisService : calls`
- `AnalysisController ..> APIError : raises`
- `AnalysisService *-- AnalysisRepository : persistence` (atau `..>` jika injeksi)
- `AnalysisService *-- StorageService : assets` (atau `..>` jika injeksi)
- `AnalysisService *-- AnalysisJobQueue : queue`
- `AnalysisService ..> AnalysisProgressReporter : reports progress`
- `AnalysisProgressReporter ..> AnalysisRepository : writes current_step/progress_percent`
- `AnalysisService ..> AIFlow : background pipeline`
- `AnalysisRepository ..> analyses : CRUD`
- `AIFlow ..> ModelService : inference / Grad-CAM`
- `AIFlow ..> PipelineResult : output`
- `PipelineResult *-- GradCAMResult : gradcam`
- `ModelService --> ModelConfig : uses`
- `auth.users "1" -- "0..*" analyses : FK user_id`
- `auth.users "1" -- "0..1" doctor_profiles : FK user_id UNIQUE`
- `Frontend ..> AnalysisController : HTTP/REST`

### 10.4 Perubahan dibandingkan diagram awal

| # | Perubahan | Alasan |
|---|-----------|--------|
| 1 | Tambah `AnalysisProgressReporter` + relasinya | F-02 (MAJOR) |
| 2 | Lengkapi `AnalysisController` (sudah ada; tambah operasi & relasi `APIError`) | F-03 |
| 3 | Tambah catatan/paket `Frontend` | F-01 |
| 4 | Beri catatan subset atribut entitas + rujuk ERD | F-04 |
| 5 | Perjelas stereotype `AIFlow` dan tipe `pipeline_runner` | F-05 |
| 6 | Lengkapi `ModelConfig` (atribut/operasi kunci) | F-06 |

### 10.5 PlantUML hasil revisi

Sumber PlantUML revisi disimpan terpisah di `references\bab 4\CLASS_DIAGRAM_FINAL_PIXELT_REVISI.puml` agar dapat dirender pengguna. Karena tidak ada renderer PlantUML di lingkungan ini, PNG/SVG belum dihasilkan; sumber `.puml` disediakan sebagai gantinya.

---

## 11. NARASI REVISI BAB IV (SIAP DIGUNAKAN SETELAH VERIFIKASI)

### 4.x Perancangan Struktur Perangkat Lunak (Class Diagram)

*Class Diagram* digunakan untuk memodelkan struktur statis perangkat lunak PIXEL-T, yaitu kelas-kelas yang menyusun sistem beserta atribut, operasi, dan hubungan antarkelas. Berbeda dengan *Use Case Diagram* yang menggambarkan kebutuhan fungsional dan *Sequence Diagram* yang menggambarkan urutan interaksi, *Class Diagram* berfokus pada organisasi komponen dan tanggung jawab masing-masing kelas pada lapisan peladen.

Sistem PIXEL-T menerapkan pemisahan tanggung jawab berdasarkan lapisan. Lapisan presentasi dibangun menggunakan React 18 dan TypeScript dengan paradigma komponen fungsional. Karena komponen fungsional React, *hook*, dan *context* tidak merepresentasikan kelas berorientasi objek dengan state dan operasi sebagaimana dimaksud UML, lapisan presentasi tidak digambarkan sebagai kelas tersendiri, melainkan dijelaskan sebagai konsumen antarmuka yang berkomunikasi dengan lapisan peladen melalui REST API. Dengan demikian, *Class Diagram* pada Gambar 4.x berfokus pada struktur kelas peladen, pipeline AI, dan entitas data yang menjadi tanggung jawab inti penelitian.

Pada lapisan kendali, kelas `AnalysisController` bertanggung jawab menerima permintaan HTTP untuk pembuatan analisis, pengambilan detail, penelusuran riwayat, dan penghapusan analisis. Kelas ini mendelegasikan logika bisnis kepada `AnalysisService` dan menggunakan `APIError` untuk menghasilkan respons kesalahan yang konsisten. Autentikasi permintaan dilakukan melalui mekanisme *Bearer token* Supabase sebelum permintaan mencapai controller.

Kelas `AnalysisService` merupakan pusat orkestrasi proses analisis. Kelas ini memiliki `AnalysisRepository` untuk operasi persistensi, `StorageService` untuk pengelolaan berkas pada Supabase Storage, `AnalysisJobQueue` untuk menjalankan pipeline AI secara asinkron, serta `AnalysisProgressReporter` untuk memperbarui `current_step` dan `progress_percent` pada tabel `analyses` selama proses berlangsung. `AnalysisService` menyediakan operasi `create_analysis`, `get_analysis`, `list_user_analyses`, dan `delete_analysis`.

Kelas `AnalysisRepository` menangani operasi CRUD pada tabel `analyses` dengan validasi status siklus hidup (`processing`, `completed`, `failed`) dan status segmentasi (`detected`, `not_detected`). Kelas `StorageService` mengelola unggah, pembuatan *signed URL*, dan penghapusan berkas dengan pola path `analysis/{user_id}/{analysis_id}/{category}/{filename}` pada bucket `analysis-assets`.

Pipeline AI direpresentasikan sebagai modul `AIFlow` yang menyediakan fungsi `run_pipeline`, `predict`, `postprocess_mask`, `measure_mask`, dan `generate_gradcam`. Modul ini bergantung pada `ModelService`, yaitu kelas yang memuat model U-Net dengan encoder ResNet50 secara *lazy* dan aman, serta pada `ModelConfig` yang menyimpan konfigurasi model seperti arsitektur, encoder, ukuran input, ambang batas, dan *scale* TTA. Hasil pipeline dimodelkan sebagai `PipelineResult`, yang memuat `SegmentationResult` dan `GradCAMResult` sebagai data kelas.

Pada lapisan data, entitas `analyses` dan `doctor_profiles` berelasi dengan `auth.users` melalui *foreign key* `user_id`. Relasi `auth.users` ke `analyses` bersifat satu-ke-banyak (`1` ke `0..*`), sedangkan relasi `auth.users` ke `doctor_profiles` bersifat satu-ke-satu opsional (`1` ke `0..1`) karena kolom `user_id` pada `doctor_profiles` memiliki *unique constraint*. Atribut entitas yang ditampilkan pada diagram merupakan subset representatif; skema lengkap dijelaskan pada ERD.

---

## 12. KESIMPULAN DAN CHECKLIST FINAL

### 12.1 Checklist kelayakan

| No | Kriteria | Status | Catatan |
|----|----------|--------|---------|
| 1 | Kelas utama backend/AI/DB ada dan sesuai kode | ✅ | `AnalysisService`, `AnalysisRepository`, `StorageService`, `ModelService`, `AnalysisJobQueue`, `ModelConfig`, dataclass hasil |
| 2 | Relasi utama benar jenis dan arah | ✅ | Dependency/composition/asosiasi DB sesuai |
| 3 | Multiplicity DB didukung constraint | ✅ | FK `user_id`, `UNIQUE(user_id)` |
| 4 | Layer HTTP terwakili | ⚠️ Sebagian | `AnalysisController` ada; routes/auth/errors tidak |
| 5 | Komponen async inti terwakili | ❌ | `AnalysisProgressReporter` tidak ada (F-02) |
| 6 | Layer frontend terwakili atau dinyatakan | ⚠️ Sebagian | Tidak dimodelkan; narasi menyatakan alasan |
| 7 | Atribut entitas sesuai skema | ⚠️ Sebagian | Subset ilustratif (F-04) |
| 8 | Notasi UML konsisten | ⚠️ Sebagian | Modul fungsional & `Callable` (F-05) |
| 9 | Narasi Bab IV konsisten | ⏳ Belum diverifikasi | F-07 |
| 10 | Tidak ada klaim tanpa bukti | ✅ | Semua temuan memiliki path/fungsi/baris |

### 12.2 Keputusan akhir

**CLASS DIAGRAM PIXEL-T: LAYAK DENGAN REVISI MINOR**

**Alasan:** Struktur inti backend, pipeline AI, dan entitas basis data sudah akurat dan didukung kode. Diagram tidak memerlukan perombakan struktural. Namun, dua temuan **MAJOR** (F-01 cakupan frontend dan F-02 `AnalysisProgressReporter` tidak dimodelkan) serta beberapa temuan **MINOR** (F-03–F-06) harus diselesaikan sebelum diagram dinyatakan final untuk skripsi. Setelah revisi minor pada `class_diagram.png`/`.puml` (menambahkan `AnalysisProgressReporter`, melengkapi `AnalysisController`/`APIError`, memberi catatan cakupan frontend, dan menyesuaikan subset atribut), diagram dapat diajukan sebagai **LAYAK DIGUNAKAN**.

### 12.3 Tindakan yang disarankan (prioritas)

1. **Wajib sebelum final:** Tambahkan `AnalysisProgressReporter` dan relasinya (F-02).
2. **Wajib sebelum final:** Beri catatan eksplisit cakupan frontend pada diagram/caption (F-01).
3. **Sangat disarankan:** Lengkapi `AnalysisController` + `APIError` dan relasi auth (F-03).
4. **Disarankan:** Catatan subset atribut + rujuk ERD (F-04); perjelas notasi `AIFlow` (F-05); lengkapi `ModelConfig` (F-06).
5. **Sebelum submit:** Verifikasi narasi Bab IV terhadap gambar final (F-07).

---

## LAMPIRAN A — DAFTAR SUMBER YANG DIPERIKSA

| Path | Peran |
|------|-------|
| `references\bab 4\class_diagram.png` | Sumber utama (14 elemen) |
| `diagram-skripsi\class\class_diagram.puml` | Sumber PlantUML lama (8 elemen) |
| `references\bab 4\PENJELASAN_CLASS_DIAGRAM_PIXELT_BAB_IV.md` | Narasi Bab IV |
| `references\bab 4\SPESIFIKASI_REVISI_CLASS_DIAGRAM_PIXELT.md` | Klaim "FINAL" (diverifikasi ulang) |
| `backend\app\services\analysis_service.py` | `AnalysisService`, `AnalysisJobQueue`, `AnalysisProgressReporter` |
| `backend\app\repositories\analysis_repository.py` | `AnalysisRepository` |
| `backend\app\services\storage_service.py` | `StorageService` |
| `backend\app\controllers\analysis_controller.py` | `AnalysisController` |
| `backend\app\routes\analysis.py` | Blueprint + `require_auth` |
| `backend\app\core\auth.py` | `require_auth` |
| `backend\app\core\errors.py` | `APIError` |
| `backend\app\core\config.py` | `Config` |
| `backend\app\core\supabase.py` | Supabase client |
| `backend\app\__init__.py` | App factory |
| `backend\run.py` | Entry point |
| `ai\inference\pipeline.py` | `run_pipeline`, `PipelineResult` |
| `ai\inference\segmentation.py` | `predict`, `SegmentationResult` |
| `ai\inference\gradcam.py` | `generate_gradcam`, `GradCAMResult` |
| `ai\inference\model_service.py` | `ModelService` |
| `ai\inference\postprocessing.py` | `postprocess_mask`, `measure_mask` |
| `ai\config\model_config.py` | `ModelConfig` |
| `database\migrations\001_create_analyses_and_storage.sql` | Skema `analyses` |
| `database\migrations\002_add_ai_pipeline_metadata.sql` | Metadata AI |
| `database\migrations\003_add_analysis_progress.sql` | Progres |
| `database\migrations\004_create_doctor_profiles.sql` | Skema `doctor_profiles` |
| `frontend\src\context\AuthContext.tsx` | Auth state |
| `frontend\src\services\auth.ts` | Auth service |
| `frontend\src\services\analysis.ts` | Analysis API client |
| `frontend\src\services\profile.ts` | Profile service |
| `frontend\src\lib\supabase.ts` | Supabase client |

*Laporan ini bersifat read-only; tidak ada kode/diagram asli yang diubah.*
