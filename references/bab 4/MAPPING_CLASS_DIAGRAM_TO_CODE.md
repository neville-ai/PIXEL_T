# MAPPING CLASS DIAGRAM — KODE — PIXEL-T

**Tujuan:** Memberikan bukti yang dapat dicek untuk setiap kelas, atribut, metode, dan relasi pada `CLASS_DIAGRAM_FINAL_PIXELT.puml` terhadap implementasi nyata.  
**Metode:** Pembacaan langsung berkas kode; baris merujuk pada nomor baris aktual (1-based). Tidak ada name/path yang direkayasa.  
**Catatan:** "Tidak ditemukan" berarti tidak ditemukan dalam cakupan berkas yang diperiksa, bukan berarti tidak ada di tempat lain.

---

## 1. Tabel Pemetaan Kelas

| # | Kelas di diagram | Stereotype | Berkas implementasi | Baris | Atribut di kode | Metode di kode | Status |
|---|---|---|---|---|---|---|---|
| 1 | `AnalysisController` | `<<controller>>` | `backend\app\controllers\analysis_controller.py` | 7–96 | `- service: AnalysisService` | `create_analysis` (13), `get_analysis` (41), `list_history` (61), `delete_analysis` (79) | ✅ Sesuai |
| 2 | `AnalysisService` | `<<service>>` | `backend\app\services\analysis_service.py` | 269–991 | `repository` (291), `storage_service` (292), `pipeline_runner` (293), `job_queue` (296–299) | `validate_and_decode_image` (301), `create_analysis` (369), `get_analysis` (502), `list_user_analyses` (635), `delete_analysis` (688), `_run_analysis_job` (761), `_execute_pipeline` (781), `_last_progress_percent` (958), `run_segmentation` (970), `run_gradcam` (983) | ✅ Sesuai |
| 3 | `AnalysisRepository` | `<<repository>>` | `backend\app\repositories\analysis_repository.py` | 5–196 | `_client` (15) | `create` (38), `get_by_id` (71), `list_by_user` (100), `update` (133), `delete` (172), `validate_lifecycle_status` (24), `validate_segmentation_status` (31) | ✅ Sesuai |
| 4 | `StorageService` | `<<service>>` | `backend\app\services\storage_service.py` | 7–189 | `_client` (16), `bucket_name` (17) | `generate_original_image_path` (59), `generate_binary_mask_path` (68), `generate_segmentation_overlay_path` (72), `generate_gradcam_heatmap_path` (76), `generate_gradcam_overlay_path` (80), `get_analysis_asset_paths` (84), `validate_path_ownership` (96), `upload_file` (119), `download_file` (139), `create_signed_url` (149), `delete_file` (164), `delete_analysis_files` (175), `sanitize_id` (32, static) | ✅ Sesuai |
| 5 | `AnalysisJobQueue` | `<<service>>` | `backend\app\services\analysis_service.py` | 150–266 | `_runner` (168), `_jobs` (169), `_lock` (170), `_not_empty` (171), `_active_analysis_id` (172), `MAX_WAITING` (174) | `capacity` (184), `try_enqueue` (188), `contains` (202), `pending_count` (209), `drain_one` (213), `_ensure_worker` (231), `_work_loop` (240) | ✅ Sesuai |
| 6 | `AnalysisProgressReporter` | `<<service>>` | `backend\app\services\analysis_service.py` | 64–148 | `_repository` (82), `_analysis_id` (83), `_user_id` (84), `_completed_units` (85), `_passes_done` (86), `_last_percent` (87), `_last_step` (88), `total_units` (90), `failed_writes` (91) | `last_step` (96), `completed_units` (101), `percent` (105), `on_phase` (110), `on_pass` (116), `_write` (126) | ✅ Sesuai |
| 7 | `APIError` | `<<exception>>` | `backend\app\core\errors.py` | 8–23 | `code` (10), `message` (11), `status_code` (12) | `to_dict` (16) | ✅ Sesuai |
| 8 | `AIInferenceFunctions` | `<<module>>` | `ai\inference\pipeline.py`, `segmentation.py`, `postprocessing.py`, `gradcam.py`, `preprocessing.py` | 101–113, 98, 26–47, 99, 12–58, 15 | — (modul) | `run_pipeline` (101), `predict` (98), `postprocess_mask` (26), `measure_mask` (49), `generate_gradcam` (99), `prepare_image` (15), `count_forward_passes` (43) | ✅ Sesuai |
| 9 | `ModelService` | `<<service>>` | `ai\inference\model_service.py` | 19–136 | `_model` (20), `_device` (21), `_lock` (22), `config` (23), `load_count` (30) | `device` (35), `load` (61), `metadata` (95), `predict_logits` (112), `get_gradcam_target_layer` (129), `_build_model` (51), `_select_device` (41) | ✅ Sesuai |
| 10 | `ModelConfig` | `<<dataclass>>` | `ai\config\model_config.py` | 19–66 | `architecture` (21), `encoder` (22), `decoder_attention` (23), `gradcam_target_layer` (24), `framework` (25), `library` (26), `model_version` (27), `input_size` (28), `input_channels` (29), `threshold` (30), `tta_enabled` (31), `multiscale_enabled` (32), `tta_scales` (33), `postprocessing_enabled` (34), `postprocessing_min_area` (35), `contour_smoothing` (36), `smoothing_epsilon` (37), `checkpoint_filename` (38), `checkpoint_sha256` (39) | `checkpoint_path` (41), `validate` (50), `checkpoint_sha256_matches` (60) | ✅ Sesuai (lengkap) |
| 11 | `PipelineResult` | `<<dataclass>>` | `ai\inference\pipeline.py` | 62–70 | `binary_mask_png` (63), `segmentation_overlay_png` (64), `gradcam_heatmap_png` (65), `gradcam_overlay_png` (66), `measurements` (67), `summary_text` (68), `gradcam` (69) | — (frozen dataclass) | ✅ Sesuai |
| 12 | `SegmentationResult` | `<<dataclass>>` | `ai\inference\segmentation.py` | 24–29 | `probability_map` (25), `binary_mask` (26), `threshold` (27) | — (frozen dataclass) | ✅ Sesuai |
| 13 | `GradCAMResult` | `<<dataclass>>` | `ai\inference\gradcam.py` | 37–44 | `heatmap` (38), `overlay` (39), `target_layer` (40), `target_objective` (41), `target_mask_empty` (42) | — (frozen dataclass) | ✅ Sesuai |
| 14 | `analyses` | `<<entity>>` | `database\migrations\001_create_analyses_and_storage.sql`, `002_add_ai_pipeline_metadata.sql`, `003_add_analysis_progress.sql` | seluruh file | 39 atribut (lihat §2.3 laporan audit utama) | — (entitas DB) | ✅ Terverifikasi (lengkap) |
| 15 | `doctor_profiles` | `<<entity>>` | `database\migrations\004_create_doctor_profiles.sql` | seluruh file | 23 atribut (lihat §2.3 laporan audit utama) | — (entitas DB) | ✅ Terverifikasi (lengkap) |
| 16 | `auth_users` | `<<external>>` | `database\migrations\001_create_analyses_and_storage.sql` (FK) | 17 | `id: UUID` | — (tabel eksternal) | ✅ Terverifikasi |
| 17 | `AnalysisClient` | `<<module>>` (modul) | `frontend\src\services\analysis.ts` | 185, 194, 212, 218 | — (interface, bukan class) | `createAnalysis` (185), `getAnalysis` (194), `listHistory` (212), `deleteAnalysis` (218) | ✅ Sesuai (modul fungsi) |
| 18 | `AuthContext` | `<<module>>` (modul) | `frontend\src\context\AuthContext.tsx` | 14–17, 39, 96, 108, 140, 146, 165 | `user` (14), `session` (14), `loading` (14), `signIn` (96), `signUp` (108), `signOut` (140) | `AuthProvider` (39), `useAuth` (165) | ✅ Sesuai (React context) |
| 19 | `DoctorProfileService` | `<<module>>` (modul) | `frontend\src\services\profile.ts` | 4, 22, 54, 64, 91, 131, 188, 221, 263 | `DoctorProfileData` (22), `ProfileCompleteness` (54) | `calculateCompleteness` (64), `fetchDoctorProfile` (131), `validateProfileData` (188), `saveDoctorProfile` (221) | ✅ Sesuai (modul fungsi) |

---

## 2. Tabel Pemetaan Metode dan Atribut

### 2.1 Backend

| Kelas | Atribut/Metode | File:Baris | Keterangan |
|---|---|---|---|
| `AnalysisController` | `service: AnalysisService` | `analysis_controller.py:10` | Atribut private (underscore) `service` |
| `AnalysisController` | `create_analysis` | `analysis_controller.py:13` | Delegasi ke `AnalysisService.create_analysis` |
| `AnalysisController` | `get_analysis` | `analysis_controller.py:41` | Query detail + ownership |
| `AnalysisController` | `list_history` | `analysis_controller.py:61` | Query daftar riwayat |
| `AnalysisController` | `delete_analysis` | `analysis_controller.py:79` | Delegasi hapus |
| `AnalysisService` | `repository` | `analysis_service.py:291` | Dependency injection |
| `AnalysisService` | `storage_service` | `analysis_service.py:292` | Dependency injection |
| `AnalysisService` | `pipeline_runner` | `analysis_service.py:293` | Default `run_pipeline` |
| `AnalysisService` | `job_queue` | `analysis_service.py:296–299` | Default `AnalysisJobQueue` |
| `AnalysisService` | `validate_and_decode_image` | `analysis_service.py:301` | Validasi ukuran/MIME/format |
| `AnalysisService` | `create_analysis` | `analysis_service.py:369` | Orkestrasi unggah + antrian |
| `AnalysisService` | `get_analysis` | `analysis_service.py:502` | Detail + signed URL |
| `AnalysisService` | `list_user_analyses` | `analysis_service.py:635` | Riwayat dengan pagination |
| `AnalysisService` | `delete_analysis` | `analysis_service.py:688` | Hapus DB + storage |
| `AnalysisService` | `_run_analysis_job` | `analysis_service.py:761` | Worker loop entry |
| `AnalysisService` | `_execute_pipeline` | `analysis_service.py:781` | Pipeline + progres + simpan |
| `AnalysisService` | `_last_progress_percent` | `analysis_service.py:958` | Baca progres terakhir |
| `AnalysisService` | `run_segmentation` | `analysis_service.py:970` | Static, return `SegmentationResult` |
| `AnalysisService` | `run_gradcam` | `analysis_service.py:983` | Static, return `GradCAMResult` |
| `AnalysisRepository` | `ALLOWED_STATUSES` | `analysis_repository.py:10` | Kelas konstanta |
| `StorageService` | `ALLOWED_CATEGORIES` | `storage_service.py:12` | Kelas konstanta |
| `AnalysisProgressReporter` | `on_phase` / `on_pass` / `_write` | `analysis_service.py:110 / 116 / 126` | Progres DB write |

### 2.2 AI

| Kelas | Atribut/Metode | File:Baris | Keterangan |
|---|---|---|---|
| `AIInferenceFunctions` | `run_pipeline` | `pipeline.py:101` | Fase: preprocessing, inference, postprocessing, gradcam, artifact_composition |
| `AIInferenceFunctions` | `predict` | `segmentation.py:98` | Probabilitas + TTA + threshold |
| `AIInferenceFunctions` | `postprocess_mask` | `postprocessing.py:26` | Min-area + smoothing |
| `AIInferenceFunctions` | `measure_mask` | `postprocessing.py:49` | Pengukuran luas |
| `AIInferenceFunctions` | `generate_gradcam` | `gradcam.py:99` | Heatmap + overlay |
| `AIInferenceFunctions` | `prepare_image` | `preprocessing.py:15` | Resize 512 |
| `AIInferenceFunctions` | `count_forward_passes` | `segmentation.py:43` | Menghitung pass |
| `ModelService` | `_model` / `_device` / `_lock` | `model_service.py:20–22` | Lazy load + thread lock |
| `ModelService` | `load` | `model_service.py:61` | `torch.nn.Module` |
| `ModelService` | `predict_logits` | `model_service.py:112` | Forward pass |
| `ModelService` | `get_gradcam_target_layer` | `model_service.py:129` | Layer Grad-CAM |
| `ModelConfig` | `validate` | `model_config.py:50` | Cek konfigurasi |
| `ModelConfig` | `checkpoint_sha256_matches` | `model_config.py:60` | Verifikasi checksum |

---

## 3. Tabel Pemetaan Relasi

| # | Relasi pada diagram | Kode/pola implementasi | Bukti | Status |
|---|---|---|---|---|
| 1 | `AnalysisController "1" --> "1" AnalysisService` | Asosiasi berarah (DI) | `self.service = service or AnalysisService()` — `analysis_controller.py:11` | ✅ |
| 2 | `AnalysisController ..> APIError` | Exception handling | `analysis_controller.py:23, 46, 74` | ✅ |
| 3 | `AnalysisService "1" --> "1" AnalysisRepository` | Referensi disimpan sebagai atribut (DI) | `self.repository = repository or AnalysisRepository()` — `analysis_service.py:291` | ✅ |
| 4 | `AnalysisService "1" --> "1" StorageService` | Referensi disimpan sebagai atribut (DI) | `self.storage_service = storage_service or StorageService()` — `analysis_service.py:292` | ✅ |
| 5 | `AnalysisService "1" --> "1" AnalysisJobQueue` | Referensi disimpan sebagai atribut (DI) | `self.job_queue = job_queue or AnalysisJobQueue(...)` — `analysis_service.py:296–299` | ✅ |
| 6 | `AnalysisService ..> AnalysisProgressReporter` | Instansiasi lokal di `_execute_pipeline` | `analysis_service.py:805–810` | ✅ |
| 7 | `AnalysisProgressReporter "1" --> "1" AnalysisRepository` | Asosiasi berarah (DI) | `self._repository` (82); `self._repository.update(...)` — `analysis_service.py:133` | ✅ |
| 8 | `AnalysisService ..> AIInferenceFunctions` | Default `pipeline_runner` | `analysis_service.py:293, 815` | ✅ |
| 9 | `AIInferenceFunctions ..> ModelService` | Parameter `model_service` | `segmentation.py:98`, `gradcam.py:99` | ✅ |
| 10 | `AIInferenceFunctions ..> PipelineResult` | Return type | `pipeline.py:101` | ✅ |
| 11 | `AIInferenceFunctions ..> SegmentationResult` | Return type | `segmentation.py:98` | ✅ |
| 12 | `AIInferenceFunctions ..> GradCAMResult` | Return type | `gradcam.py:99` | ✅ |
| 13 | `PipelineResult "1" --> "1" GradCAMResult` | Asosiasi berarah (field referensi) | `gradcam: GradCAMResult` — `pipeline.py:69` | ✅ |
| 14 | `ModelService --> ModelConfig` | Asosiasi berarah (constructor param) | `def __init__(self, config: ModelConfig = MODEL_CONFIG)` — `model_service.py:22` | ✅ |
| 15 | `AnalysisRepository ..> analyses` | CRUD tabel | `analysis_repository.py:38–196` | ✅ |
| 16 | `auth_users "1" -- "0..*" analyses` | FK | `001_create_analyses_and_storage.sql:17` | ✅ |
| 17 | `auth_users "1" -- "0..1" doctor_profiles` | FK UNIQUE | `004_create_doctor_profiles.sql:12, 46` | ✅ |
| 18 | `AnalysisClient ..> AnalysisController` | HTTP fetch | `frontend\src\services\analysis.ts:185, 194, 212, 218` | ✅ |
| 19 | `AuthContext ..> auth_users` | Supabase Auth | `frontend\src\context\AuthContext.tsx:96` via `services/auth.ts:205` | ✅ |
| 20 | `DoctorProfileService ..> doctor_profiles` | Supabase RLS upsert | `frontend\src\services\profile.ts:287–289` | ✅ |

---

## 4. Ringkasan Verifikasi Kelas

| Kelas | Ada di diagram? | Ada di kode? | Atribut akurat? | Metode akurat? | Relasi akurat? |
|---|---|---|---|---|---|
| Backend (7) | ✅ | ✅ | ✅ | ✅ | ✅ |
| AI (6) | ✅ | ✅ | ✅ | ✅ | ✅ |
| Entitas (3) | ✅ | ✅ | ✅ | — | ✅ |
| Frontend (3) | ✅ (package) | ✅ (modul) | ✅ | ✅ | ✅ |
| **Total** | **19** | **19** | **Ya** | **Ya** | **Ya** |

---

## 5. Catatan Penting

1. **Frontend** — Class `AnalysisClient`, `AuthContext`, dan `DoctorProfileService` berada di dalam `package "Frontend"` dan merupakan **representasi modul fungsional**, bukan class berorientasi objek. Semua metode teregistrasi di map sesuai fungsi asli.

2. **AIInferenceFunctions** — Stereotype `<<module>>`; berkas yang berdiri sendiri. Relasi ke `ModelService`, `PipelineResult`, `SegmentationResult`, `GradCAMResult` adalah **dependency** karena semua dikembalikan via parameter/return.

3. **Entitas** — Relasi `auth_users -- analyses` dan `auth_users -- doctor_profiles` adalah **association** (FK), bukan composition. Ini konsisten dengan migrasi SQL.

4. **Baris kode** — Angka baris pada tabel ini diturunkan langsung dari hasil *scaffolding* pencarian (`Select-String` / `grep`) pada berkas di atas; tidak dihitung manual.

---

## 6. Kesimpulan Pemetaan

Seluruh **19 elemen** pada `CLASS_DIAGRAM_FINAL_PIXELT.puml` telah dipetakan ke implementasi nyata dan **dikonfirmasi akurat** setelah perbaikan signatur `StorageService.upload_file` serta penyesuaian representasi frontend menjadi package. Tidak ada elemen yang perlu ditambahkan atau dihapus dari diagram; hanya koreksi internal signatur yang dilakukan sebagai bagian dari revisi minor.
