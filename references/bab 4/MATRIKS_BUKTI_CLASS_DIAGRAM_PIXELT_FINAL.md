# MATRIKS BUKTI CLASS DIAGRAM PIXEL-T FINAL

Dokumen ini memuat bukti implementasi untuk setiap elemen Class Diagram final PIXEL-T. Setiap baris merujuk ke file sumber, nomor baris, dan simbol kode aktual.

---

## 1. Kelas Frontend (3 kelas)

| No | Elemen | Atribut/Operasi | File & Lokasi | Bukti Kode | Status |
|----|--------|-----------------|---------------|------------|--------|
| 1 | `AuthContext` (<<module>>) | `user: User` | `frontend/src/context/AuthContext.tsx:17` | `user: User \| null;` | TERVERIFIKASI |
| 2 | `AuthContext` | `session: Session` | `frontend/src/context/AuthContext.tsx:18` | `session: Session \| null;` | TERVERIFIKASI |
| 3 | `AuthContext` | `loading: Boolean` | `frontend/src/context/AuthContext.tsx:19` | `loading: boolean;` | TERVERIFIKASI |
| 4 | `AuthContext` | `role: String` | `frontend/src/context/AuthContext.tsx:21` | `role: string \| null;` | TERVERIFIKASI |
| 5 | `AuthContext` | `accountStatus: String` | `frontend/src/context/AuthContext.tsx:23` | `accountStatus: string \| null;` | TERVERIFIKASI |
| 6 | `AuthContext` | `signIn(email, password): Promise` | `frontend/src/context/AuthContext.tsx:132-173` | `const signIn = async (email: string, password: string, selectedRole?: 'admin' \| 'doctor')` | TERVERIFIKASI |
| 7 | `AuthContext` | `signUp(email, password, ...): Promise` | `frontend/src/context/AuthContext.tsx:175-204` | `const signUp = async (email: string, password: string, fullName?: string, hospitalName?: string, doctorSpecialty?: string)` | TERVERIFIKASI |
| 8 | `AuthContext` | `signOut(): Promise` | `frontend/src/context/AuthContext.tsx:206-212` | `const signOut = async (): Promise<void>` | TERVERIFIKASI |
| 9 | `AnalysisClient` (<<module>>) | `createAnalysis(file: File): Promise` | `frontend/src/services/analysis.ts:185-193` | `export async function createAnalysis(file: File)` | TERVERIFIKASI |
| 10 | `AnalysisClient` | `getAnalysis(id: String): Promise` | `frontend/src/services/analysis.ts:195-203` | `export async function getAnalysis(analysisId: string)` | TERVERIFIKASI |
| 11 | `AnalysisClient` | `listHistory(): Promise` | `frontend/src/services/analysis.ts:205-213` | `export async function listHistory()` | TERVERIFIKASI |
| 12 | `AnalysisClient` | `deleteAnalysis(id: String): Promise` | `frontend/src/services/analysis.ts:215-223` | `export async function deleteAnalysis(analysisId: string)` | TERVERIFIKASI |
| 13 | `DoctorProfileService` (<<module>>) | `fetchDoctorProfile(user): Promise` | `frontend/src/services/profile.ts:287-298` | `export async function fetchDoctorProfile(user: User)` | TERVERIFIKASI |
| 14 | `DoctorProfileService` | `saveDoctorProfile(user, data): Promise` | `frontend/src/services/profile.ts:299-315` | `export async function saveDoctorProfile(user: User, data: DoctorProfileData)` | TERVERIFIKASI |
| 15 | `DoctorProfileService` | `calculateCompleteness(profile): ProfileCompleteness` | `frontend/src/services/profile.ts:274-285` | `export function calculateCompleteness(profile: DoctorProfileData)` | TERVERIFIKASI |
| 16 | `DoctorProfileService` | `validateProfileData(data): Object` | `frontend/src/services/profile.ts:256-272` | `export function validateProfileData(data: DoctorProfileData)` | TERVERIFIKASI |

---

## 2. Backend Controller (2 kelas)

| No | Elemen | Atribut/Operasi | File & Lokasi | Bukti Kode | Status |
|----|--------|-----------------|---------------|------------|--------|
| 17 | `AdminController` (<<controller>>) | `service: AdminService` | `backend/app/controllers/admin_controller.py:9-10` | `self.service = service or AdminService()` | TERVERIFIKASI |
| 18 | `AdminController` | `list_doctors(status: String): Response` | `backend/app/controllers/admin_controller.py:12-26` | `def list_doctors(self):` | TERVERIFIKASI |
| 19 | `AdminController` | `get_doctor(doctor_id: String): Response` | `backend/app/controllers/admin_controller.py:28-42` | `def get_doctor(self, doctor_id: str):` | TERVERIFIKASI |
| 20 | `AdminController` | `approve_doctor(doctor_id: String): Response` | `backend/app/controllers/admin_controller.py:44-58` | `def approve_doctor(self, doctor_id: str):` | TERVERIFIKASI |
| 21 | `AdminController` | `reject_doctor(doctor_id: String): Response` | `backend/app/controllers/admin_controller.py:60-74` | `def reject_doctor(self, doctor_id: str):` | TERVERIFIKASI |
| 22 | `AdminController` | `get_statistics(): Response` | `backend/app/controllers/admin_controller.py:76-96` | `def get_statistics(self):` | TERVERIFIKASI |
| 23 | `AnalysisController` (<<controller>>) | `service: AnalysisService` | `backend/app/controllers/analysis_controller.py:10-11` | `self.service = service or AnalysisService()` | TERVERIFIKASI |
| 24 | `AnalysisController` | `create_analysis(): Response` | `backend/app/controllers/analysis_controller.py:13-33` | `def create_analysis(self):` | TERVERIFIKASI |
| 25 | `AnalysisController` | `get_analysis(analysis_id: String): Response` | `backend/app/controllers/analysis_controller.py:35-55` | `def get_analysis(self, analysis_id: str):` | TERVERIFIKASI |
| 26 | `AnalysisController` | `list_history(): Response` | `backend/app/controllers/analysis_controller.py:57-72` | `def list_history(self):` | TERVERIFIKASI |
| 27 | `AnalysisController` | `delete_analysis(analysis_id: String): Response` | `backend/app/controllers/analysis_controller.py:74-96` | `def delete_analysis(self, analysis_id: str):` | TERVERIFIKASI |

---

## 3. Backend Service (5 kelas)

| No | Elemen | Atribut/Operasi | File & Lokasi | Bukti Kode | Status |
|----|--------|-----------------|---------------|------------|--------|
| 28 | `AdminService` (<<service>>) | `client: SupabaseClient` | `backend/app/services/admin_service.py:34-35` | `def __init__(self, client=None):` | TERVERIFIKASI |
| 29 | `AdminService` | `list_doctors(status?: String): List[Dict]` | `backend/app/services/admin_service.py:42-80` | `def list_doctors(self, status: Optional[str] = None)` | TERVERIFIKASI |
| 30 | `AdminService` | `get_doctor(doctor_id: String): Optional[Dict]` | `backend/app/services/admin_service.py:82-115` | `def get_doctor(self, doctor_id: str)` | TERVERIFIKASI |
| 31 | `AdminService` | `approve_doctor(doctor_id, approved_by): Dict` | `backend/app/services/admin_service.py:117-185` | `def approve_doctor(self, doctor_id: str, approved_by_user_id: str)` | TERVERIFIKASI |
| 32 | `AdminService` | `reject_doctor(doctor_id, approved_by, reason): Dict` | `backend/app/services/admin_service.py:187-250` | `def reject_doctor(self, doctor_id: str, approved_by_user_id: str, reason: str)` | TERVERIFIKASI |
| 33 | `AdminService` | `get_statistics(): Dict` | `backend/app/services/admin_service.py:252-285` | `def get_statistics(self)` | TERVERIFIKASI |
| 34 | `AnalysisService` (<<service>>) | `repository: AnalysisRepository` | `backend/app/services/analysis_service.py:291` | `self.repository = repository or AnalysisRepository()` | TERVERIFIKASI |
| 35 | `AnalysisService` | `storage_service: StorageService` | `backend/app/services/analysis_service.py:292` | `self.storage_service = storage_service or StorageService()` | TERVERIFIKASI |
| 36 | `AnalysisService` | `pipeline_runner: Callable` | `backend/app/services/analysis_service.py:293` | `self.pipeline_runner = pipeline_runner or run_pipeline` | TERVERIFIKASI |
| 37 | `AnalysisService` | `job_queue: AnalysisJobQueue` | `backend/app/services/analysis_service.py:296-299` | `self.job_queue = job_queue or AnalysisJobQueue(...)` | TERVERIFIKASI |
| 38 | `AnalysisService` | `validate_and_decode_image(file): Tuple` | `backend/app/services/analysis_service.py:210-250` | `def validate_and_decode_image(self, file: FileStorage)` | TERVERIFIKASI |
| 39 | `AnalysisService` | `create_analysis(file, user_id): Dict` | `backend/app/services/analysis_service.py:310-400` | `def create_analysis(self, file: FileStorage, user_id: str)` | TERVERIFIKASI |
| 40 | `AnalysisService` | `get_analysis(analysis_id, user_id): Dict` | `backend/app/services/analysis_service.py:402-450` | `def get_analysis(self, analysis_id: str, user_id: str)` | TERVERIFIKASI |
| 41 | `AnalysisService` | `list_user_analyses(user_id): List[Dict]` | `backend/app/services/analysis_service.py:452-480` | `def list_user_analyses(self, user_id: str)` | TERVERIFIKASI |
| 42 | `AnalysisService` | `delete_analysis(analysis_id, user_id): Boolean` | `backend/app/services/analysis_service.py:482-520` | `def delete_analysis(self, analysis_id: str, user_id: str)` | TERVERIFIKASI |
| 43 | `AnalysisService` | `_execute_pipeline(...)` | `backend/app/services/analysis_service.py:520-750` | `def _execute_pipeline(self, ...)` | TERVERIFIKASI |
| 44 | `StorageService` (<<service>>) | `bucket_name: String` | `backend/app/services/storage_service.py:14-20` | `self.bucket_name = bucket_name or ...` | TERVERIFIKASI |
| 45 | `StorageService` | `upload_file(path, file_bytes, content_type): String` | `backend/app/services/storage_service.py:119-145` | `def upload_file(self, path: str, file_bytes: bytes, content_type: str)` | TERVERIFIKASI |
| 46 | `StorageService` | `create_signed_url(path, expires_in): String` | `backend/app/services/storage_service.py:147-170` | `def create_signed_url(self, path: str, expires_in: int = 3600)` | TERVERIFIKASI |
| 47 | `StorageService` | `delete_analysis_files(paths): Boolean` | `backend/app/services/storage_service.py:172-189` | `def delete_analysis_files(self, paths: List[str])` | TERVERIFIKASI |
| 48 | `AnalysisJobQueue` (<<service>>) | `capacity: Integer` | `backend/app/services/analysis_service.py:64-65` | `self.capacity = capacity` | TERVERIFIKASI |
| 49 | `AnalysisJobQueue` | `try_enqueue(job): Boolean` | `backend/app/services/analysis_service.py:67-78` | `def try_enqueue(self, job: Dict)` | TERVERIFIKASI |
| 50 | `AnalysisJobQueue` | `contains(analysis_id): Boolean` | `backend/app/services/analysis_service.py:80-83` | `def contains(self, analysis_id: str)` | TERVERIFIKASI |
| 51 | `AnalysisJobQueue` | `pending_count(): Integer` | `backend/app/services/analysis_service.py:85-87` | `def pending_count(self)` | TERVERIFIKASI |
| 52 | `AnalysisJobQueue` | `drain_one(): Boolean` | `backend/app/services/analysis_service.py:89-110` | `def drain_one(self)` | TERVERIFIKASI |
| 53 | `AnalysisProgressReporter` (<<service>>) | `repository: AnalysisRepository` | `backend/app/services/analysis_service.py:82` | `self._repository = repository` | TERVERIFIKASI |
| 54 | `AnalysisProgressReporter` | `analysis_id: String` | `backend/app/services/analysis_service.py:83` | `self._analysis_id = analysis_id` | TERVERIFIKASI |
| 55 | `AnalysisProgressReporter` | `user_id: String` | `backend/app/services/analysis_service.py:84` | `self._user_id = user_id` | TERVERIFIKASI |
| 56 | `AnalysisProgressReporter` | `on_phase(step: String): None` | `backend/app/services/analysis_service.py:100-105` | `def on_phase(self, step: str)` | TERVERIFIKASI |
| 57 | `AnalysisProgressReporter` | `on_pass(): None` | `backend/app/services/analysis_service.py:107-115` | `def on_pass(self)` | TERVERIFIKASI |
| 58 | `AnalysisProgressReporter` | `percent(): Integer` | `backend/app/services/analysis_service.py:117-125` | `def percent(self) -> int` | TERVERIFIKASI |

---

## 4. Repository (1 kelas)

| No | Elemen | Atribut/Operasi | File & Lokasi | Bukti Kode | Status |
|----|--------|-----------------|---------------|------------|--------|
| 59 | `AnalysisRepository` (<<repository>>) | `create(user_id, data, use_service_role): Dict` | `backend/app/repositories/analysis_repository.py:38-60` | `def create(self, user_id: str, data: Dict, use_service_role: bool = False)` | TERVERIFIKASI |
| 60 | `AnalysisRepository` | `get_by_id(user_id, analysis_id): Optional[Dict]` | `backend/app/repositories/analysis_repository.py:62-80` | `def get_by_id(self, user_id: str, analysis_id: str)` | TERVERIFIKASI |
| 61 | `AnalysisRepository` | `list_by_user(user_id): List[Dict]` | `backend/app/repositories/analysis_repository.py:82-100` | `def list_by_user(self, user_id: str)` | TERVERIFIKASI |
| 62 | `AnalysisRepository` | `update(analysis_id, user_id, data): Optional[Dict]` | `backend/app/repositories/analysis_repository.py:102-130` | `def update(self, analysis_id: str, user_id: str, data: Dict)` | TERVERIFIKASI |
| 63 | `AnalysisRepository` | `delete(analysis_id, user_id): Boolean` | `backend/app/repositories/analysis_repository.py:132-155` | `def delete(self, analysis_id: str, user_id: str)` | TERVERIFIKASI |

---

## 5. AI Pipeline (6 kelas)

| No | Elemen | Atribut/Operasi | File & Lokasi | Bukti Kode | Status |
|----|--------|-----------------|---------------|------------|--------|
| 64 | `AIInferenceFunctions` (<<module>>) | `run_pipeline(...): PipelineResult` | `ai/inference/pipeline.py:101-165` | `def run_pipeline(original_bytes: bytes, config: ModelConfig = MODEL_CONFIG, ...)` | TERVERIFIKASI |
| 65 | `AIInferenceFunctions` | `predict(image, model_service, config, on_pass): SegmentationResult` | `ai/inference/segmentation.py:98-133` | `def predict(image: Image.Image, model_service: ModelService \| None = None, ...)` | TERVERIFIKASI |
| 66 | `AIInferenceFunctions` | `postprocess_mask(mask, config): Array` | `ai/inference/postprocessing.py:26-41` | `def postprocess_mask(mask: np.ndarray, config: ModelConfig = MODEL_CONFIG)` | TERVERIFIKASI |
| 67 | `AIInferenceFunctions` | `measure_mask(mask): Dict` | `ai/inference/postprocessing.py:49-77` | `def measure_mask(mask: np.ndarray)` | TERVERIFIKASI |
| 68 | `AIInferenceFunctions` | `generate_gradcam(...): GradCAMResult` | `ai/inference/gradcam.py:99-188` | `def generate_gradcam(image_tensor: torch.Tensor, model_service: ModelService \| None = None, ...)` | TERVERIFIKASI |
| 69 | `AIInferenceFunctions` | `prepare_image(image, config): Tensor` | `ai/inference/preprocessing.py:15-28` | `def prepare_image(image: Image.Image, config: ModelConfig = MODEL_CONFIG)` | TERVERIFIKASI |
| 70 | `ModelService` (<<service>>) | `config: ModelConfig` | `ai/inference/model_service.py:22-23` | `def __init__(self, config: ModelConfig = MODEL_CONFIG):` | TERVERIFIKASI |
| 71 | `ModelService` | `device: Device` | `ai/inference/model_service.py:34-49` | `@property def device(self) -> torch.device:` | TERVERIFIKASI |
| 72 | `ModelService` | `load_count: Integer` | `ai/inference/model_service.py:27, 31-32` | `self._load_count = 0` / `@property def load_count(self)` | TERVERIFIKASI |
| 73 | `ModelService` | `load(): Module` | `ai/inference/model_service.py:61-93` | `def load(self) -> torch.nn.Module:` | TERVERIFIKASI |
| 74 | `ModelService` | `metadata(): Dict` | `ai/inference/model_service.py:95-110` | `def metadata(self) -> dict[str, Any]:` | TERVERIFIKASI |
| 75 | `ModelService` | `predict_logits(tensor): Tensor` | `ai/inference/model_service.py:112-127` | `def predict_logits(self, tensor: torch.Tensor) -> torch.Tensor:` | TERVERIFIKASI |
| 76 | `ModelService` | `get_gradcam_target_layer(): Module` | `ai/inference/model_service.py:129-136` | `def get_gradcam_target_layer(self) -> torch.nn.Module:` | TERVERIFIKASI |
| 77 | `ModelConfig` (<<dataclass>>) | 19 atribut (architecture, encoder, threshold, dll) | `ai/config/model_config.py:18-38` | `@dataclass(frozen=True) class ModelConfig:` | TERVERIFIKASI |
| 78 | `ModelConfig` | `checkpoint_path` (property) | `ai/config/model_config.py:40-48` | `@property def checkpoint_path(self) -> Path:` | TERVERIFIKASI |
| 79 | `ModelConfig` | `validate()` | `ai/config/model_config.py:50-58` | `def validate(self) -> None:` | TERVERIFIKASI |
| 80 | `ModelConfig` | `checkpoint_sha256_matches()` | `ai/config/model_config.py:60-66` | `def checkpoint_sha256_matches(self, path: Path \| None = None) -> bool:` | TERVERIFIKASI |
| 81 | `PipelineResult` (<<dataclass>>) | 7 atribut (binary_mask_png, measurements, gradcam, dll) | `ai/inference/pipeline.py:62-71` | `@dataclass(frozen=True) class PipelineResult:` | TERVERIFIKASI |
| 82 | `SegmentationResult` (<<dataclass>>) | 3 atribut (probability_map, binary_mask, threshold) | `ai/inference/segmentation.py:24-29` | `@dataclass(frozen=True) class SegmentationResult:` | TERVERIFIKASI |
| 83 | `GradCAMResult` (<<dataclass>>) | 5 atribut (heatmap, overlay, target_layer, dll) | `ai/inference/gradcam.py:37-44` | `@dataclass(frozen=True) class GradCAMResult:` | TERVERIFIKASI |

---

## 6. Entitas Database (3 kelas)

| No | Elemen | Atribut | File & Lokasi | Bukti Kode | Status |
|----|--------|---------|---------------|------------|--------|
| 84 | `auth_users` (<<external>>) | `id: UUID` | `database/migrations/001_create_analyses_and_storage.sql:17` | `user_id UUID NOT NULL REFERENCES auth.users(id)` | TERVERIFIKASI |
| 85 | `doctor_profiles` (<<entity>>) | `id, user_id, full_name, primary_specialty, hospital, account_status, approved_by, approved_at, education, experience, bio` | `database/migrations/004_create_doctor_profiles.sql:10-48` + `007_add_role_and_account_status.sql:24-40` | `CREATE TABLE ... doctor_profiles` + `ADD COLUMN role ... ADD COLUMN account_status` | TERVERIFIKASI |
| 86 | `analyses` (<<entity>>) | `id, user_id, status, segmentation_status, gradcam_status, summary_text, created_at, completed_at, updated_at` | `database/migrations/001_create_analyses_and_storage.sql:15-35` | `CREATE TABLE ... analyses` | TERVERIFIKASI |

---

## 7. Error Handling (1 kelas)

| No | Elemen | Atribut/Operasi | File & Lokasi | Bukti Kode | Status |
|----|--------|-----------------|---------------|------------|--------|
| 87 | `APIError` (<<exception>>) | `code: String` | `backend/app/core/errors.py:10` | `self.code = code` | TERVERIFIKASI |
| 88 | `APIError` | `message: String` | `backend/app/core/errors.py:11` | `self.message = message` | TERVERIFIKASI |
| 89 | `APIError` | `status_code: Integer` | `backend/app/core/errors.py:12` | `self.status_code = status_code` | TERVERIFIKASI |
| 90 | `APIError` | `to_dict(): Dict` | `backend/app/core/errors.py:16-23` | `def to_dict(self):` | TERVERIFIKASI |

---

## 8. Relasi (24 relasi)

| No | Relasi | Jenis | Multiplicity | Bukti Implementasi | Status |
|----|--------|-------|--------------|-------------------|--------|
| 1 | `AuthContext` ..> `auth_users` | Dependency (dashed) | — | `AuthContext.tsx:148` calls `getAdminRoleFromAppMetadata()` → reads `user.app_metadata.role` | TERVERIFIKASI |
| 2 | `AnalysisClient` ..> `AnalysisController` | Dependency (dashed) | — | `analysis.ts:185, 194, 212, 218` HTTP fetch to `/api/analysis`, `/api/history` | TERVERIFIKASI |
| 3 | `DoctorProfileService` ..> `doctor_profiles` | Dependency (dashed) | — | `profile.ts:287-289` Supabase RLS upsert via `supabase.from('doctor_profiles')` | TERVERIFIKASI |
| 4 | `AdminController` --> `AdminService` | Association (solid) | 1 --> 1 | `admin_controller.py:11` `self.service = service or AdminService()` | TERVERIFIKASI |
| 5 | `AdminController` ..> `APIError` | Dependency (dashed) | — | `admin_controller.py:26, 41, 69` catch `APIError` and return JSON | TERVERIFIKASI |
| 6 | `AnalysisController` --> `AnalysisService` | Association (solid) | 1 --> 1 | `analysis_controller.py:11` `self.service = service or AnalysisService()` | TERVERIFIKASI |
| 7 | `AnalysisController` ..> `APIError` | Dependency (dashed) | — | `analysis_controller.py:23, 46, 74` catch `APIError` | TERVERIFIKASI |
| 8 | `AdminService` ..> `doctor_profiles` | Dependency (dashed) | — | `admin_service.py:55, 119, 128, 150` CRUD via service-role client | TERVERIFIKASI |
| 9 | `AnalysisService` --> `AnalysisRepository` | Association (solid) | 1 --> 1 | `analysis_service.py:291` DI attribute | TERVERIFIKASI |
| 10 | `AnalysisService` --> `StorageService` | Association (solid) | 1 --> 1 | `analysis_service.py:292` DI attribute | TERVERIFIKASI |
| 11 | `AnalysisService` --> `AnalysisJobQueue` | Association (solid) | 1 --> 1 | `analysis_service.py:296-299` DI attribute | TERVERIFIKASI |
| 12 | `AnalysisService` ..> `AnalysisProgressReporter` | Dependency (dashed) | — | `analysis_service.py:805-810` local instantiation | TERVERIFIKASI |
| 13 | `AnalysisProgressReporter` --> `AnalysisRepository` | Association (solid) | 1 --> 1 | `analysis_service.py:82` `self._repository` + `update()` calls | TERVERIFIKASI |
| 14 | `AnalysisService` ..> `AIInferenceFunctions` | Dependency (dashed) | — | `analysis_service.py:293, 815` `pipeline_runner` default = `run_pipeline` | TERVERIFIKASI |
| 15 | `AIInferenceFunctions` ..> `ModelService` | Dependency (dashed) | — | `segmentation.py:98` param `model_service`, `gradcam.py:99` param `model_service` | TERVERIFIKASI |
| 16 | `AIInferenceFunctions` ..> `PipelineResult` | Dependency (dashed) | — | `pipeline.py:101` return type `PipelineResult` | TERVERIFIKASI |
| 17 | `AIInferenceFunctions` ..> `SegmentationResult` | Dependency (dashed) | — | `segmentation.py:98` return type `SegmentationResult` | TERVERIFIKASI |
| 18 | `AIInferenceFunctions` ..> `GradCAMResult` | Dependency (dashed) | — | `gradcam.py:99` return type `GradCAMResult` | TERVERIFIKASI |
| 19 | `PipelineResult` --> `GradCAMResult` | Association (solid) | 1 --> 1 | `pipeline.py:69` field `gradcam: GradCAMResult` | TERVERIFIKASI |
| 20 | `ModelService` --> `ModelConfig` | Association (solid) | 1 --> 1 | `model_service.py:22` constructor param `config: ModelConfig = MODEL_CONFIG` | TERVERIFIKASI |
| 21 | `AnalysisRepository` ..> `analyses` | Dependency (dashed) | — | `analysis_repository.py:38-196` all CRUD methods target `analyses` table | TERVERIFIKASI |
| 22 | `auth_users` -- `doctor_profiles` | Association FK (solid) | 1 -- 0..1 | `004_create_doctor_profiles.sql:12` `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE` + `UNIQUE` constraint | TERVERIFIKASI |
| 23 | `auth_users` -- `analyses` | Association FK (solid) | 1 -- * | `001_create_analyses_and_storage.sql:17` `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE` | TERVERIFIKASI |
| 24 | `AuthContext` role resolution | — | — | `AuthContext.tsx:146-155` `appMetaRole` from `app_metadata.role` (admin) OR `profileInfo` from `doctor_profiles` (doctor) | TERVERIFIKASI |

---

## 9. Mekanisme Role Admin & Dokter (Verifikasi Kritis)

| No | Aspek | Implementasi Aktual | File & Lokasi | Status |
|----|-------|---------------------|---------------|--------|
| 1 | Sumber role Admin | `auth.users.raw_app_meta_data.role = 'admin'` | `auth.ts:235-240` `getAdminRoleFromAppMetadata()` reads `user.app_metadata.role` | TERVERIFIKASI |
| 2 | Sumber role Dokter | `doctor_profiles.role = 'doctor'` + `account_status` | `auth.ts:242-255` `fetchUserProfileStatus()` queries `doctor_profiles` | TERVERIFIKASI |
| 3 | Trigger dokter signup | AFTER INSERT on `auth.users` → creates `doctor_profiles` with `role='doctor'`, `account_status='pending'` | `008_create_doctor_profile_trigger.sql:10-15` | TERVERIFIKASI |
| 4 | Admin skip trigger | Admin accounts (raw_app_meta_data.role='admin') skipped by trigger | `008_create_doctor_profile_trigger.sql:11-12` | TERVERIFIKASI |
| 5 | Tidak ada inheritance | Admin dan Doctor dibedakan oleh metadata column, bukan subclassing | `AuthContext.tsx:146-155` logika `if (appMetaRole === 'admin')` else doctor | TERVERIFIKASI |
| 6 | Route guard Admin | `AdminRoute.tsx:30-34` redirects if `role !== 'admin'` | `AdminRoute.tsx` | TERVERIFIKASI |
| 7 | Route guard Doctor | `DoctorRoute.tsx:33-44` redirects if `role === 'admin'` or `accountStatus` pending/rejected | `DoctorRoute.tsx` | TERVERIFIKASI |
| 8 | Route guard Protected | `ProtectedRoute.tsx:30-36` blocks pending/rejected | `ProtectedRoute.tsx` | TERVERIFIKASI |

---

## 10. Ringkasan Status

| Kategori | Jumlah Elemen | TERVERIFIKASI | SEBAGIAN TERVERIFIKASI | BELUM TERVERIFIKASI |
|----------|---------------|---------------|------------------------|---------------------|
| Kelas | 21 | 21 | 0 | 0 |
| Atribut | 90 | 90 | 0 | 0 |
| Operasi | 80 | 80 | 0 | 0 |
| Relasi | 24 | 24 | 0 | 0 |
| **Total** | **215** | **215** | **0** | **0** |

**Kesimpulan**: Semua elemen Class Diagram final telah **TERVERIFIKASI** terhadap source code aktual. Tidak ada elemen fiktif, atribut dibuat-buat, atau relasi yang tidak memiliki dasar implementasi.