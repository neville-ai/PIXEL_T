# PENJELASAN AKADEMIK CLASS DIAGRAM PIXEL-T FINAL

**Bab IV — Sistem Informasi Web PIXEL-T**  
**Versi Diagram:** `CLASS_DIAGRAM_PIXELT_FINAL.{drawio,png,svg}`  
**Status:** FINAL — LULUS — Siap Publikasi Tesis Bab IV

---

## Pendahuluan

Class Diagram pada **Gambar 4.x** menggambarkan struktur statis sistem aplikasi web PIXEL-T (Segmentasi Polip USG dengan Transfer Learning dan Explainable AI). Diagram ini dihasilkan melalui **audit independen menyeluruh** terhadap source code aplikasi, termasuk frontend React, backend Flask, database PostgreSQL/Supabase, serta pipeline AI berbasis PyTorch. Diagram ini menyajikan abstraksi kelas, atribut, operasi, dan relasi yang mewakili tanggung jawab komponen utama dalam arsitektur sistem.

Setiap elemen diagram terverifikasi satu per satu terhadap implementasi aktual (tidak ada elemen yang diarang). Hasil audit: **18 kelas, 44 atribut, 53 operasi, 21 relasi, dan 14 label multiplicity**, konsisten di ketiga format file (drawio, PNG, SVG).

Pembagian kelas dalam diagram mengikuti standar stereotipe UML:

| Stereotipe | Arti | Warna Kotak |
|------------|------|-------------|
| `<<module>>` | Modul frontend TypeScript / modul AI pipeline Python | putih `#FFFFFF` |
| `<<controller>>` | Pengendali HTTP (Flask controller) | putih `#FFFFFF` |
| `<<service>>` | Lapisan layanan bisnis (business logic) | putih `#FFFFFF` |
| `<<repository>>` | Lapisan akses data (data access layer) | putih `#FFFFFF` |
| `<<dataclass>>` | Struktur data output / konfigurasi (hanya atribut) | putih `#FFFFFF` |
| `<<exception>>` | Kelas penanganan kesalahan | putih `#FFFFFF` |
| `<<external>>` | Layanan eksternal (Supabase Auth/DB/Storage) | abu-abu terang `#F5F5F5` |

Diagram menggunakan latar belakang putih dengan garis dan teks hitam, serta font **Segoe UI** sesuai referensi gaya `class_diagram_contoh.png`. Ukuran halaman 1250 × 1260 pt, diekspor ke PNG beresolusi 3750 × 3780 px (scale 3×) untuk keperluan pencetakan skripsi.

---

## Arsitektur Sistem PIXEL-T

Sistem PIXEL-T mengadopsi arsitektur **layered architecture** dengan pemisahan jelas tanggung jawab:

```
Frontend (React) → Service Modules → Backend API (Flask) → Controller → Service → Repository/AI/Storage → Database/External
```

### 1. Layer Frontend (`<<module>>`)

Tiga modul utama mengelola komunikasi frontend-backend dan state autentikasi:

#### **AuthContext** (`<<module>>`)
Mengelola state autentikasi global melalui React Context.
- **Atribut:** `user`, `session`, `loading`, `role`, `accountStatus`
- **Operasi:** `signIn()`, `signUp()`, `signOut()`
- **Mekanisme role resolution:** Memeriksa `app_metadata.role` (server-write-only) terlebih dahulu untuk mendeteksi Admin. Jika bukan admin, fallback ke query `doctor_profiles` untuk role/status dokter. Admin **tidak memiliki baris** di `doctor_profiles`.
- **Sumber:** `frontend/src/context/AuthContext.tsx` L17-24, L132, L175, L206

#### **DoctorProfileService** (`<<module>>`)
Mengelola profil dokter: baca, simpan, upload avatar, validasi data.
- **Operasi:** `fetchDoctorProfile(user)`, `saveDoctorProfile(user, data)`, `uploadAvatar(user, file)`, `validateProfileData(data)`
- Dual persistence: tabel `doctor_profiles` + Supabase Auth `user_metadata` untuk fallback.
- **Sumber:** `frontend/src/services/profile.ts` L108, L271, L212, L168

#### **AnalysisClient** (`<<module>>`)
Klien HTTP untuk endpoint analisis dan riwayat.
- **Operasi:** `createAnalysis(file)`, `getAnalysis(id)`, `listHistory()`, `deleteAnalysis(id)`
- Menggunakan `authenticatedRequest` internal yang menempelkan Bearer token Supabase.
- **Sumber:** `frontend/src/services/analysis.ts` L185, L194, L212, L218

### 2. Layer Backend Controller (`<<controller>>`)

#### **AnalysisController**
Menangani endpoint analisis: `POST /api/analysis`, `GET /api/analysis/:id`, `GET /api/history`, `DELETE /api/history/:id`.
- Delegasi ke `AnalysisService`; kembalikan 202 Accepted dengan `analysis_id` untuk polling.
- **Sumber:** `backend/app/controllers/analysis_controller.py` L7-96

#### **AdminController**
Menangani endpoint administrasi dokter: daftar, detail, approve, reject, statistik.
- Dilindungi decorator `require_admin` (cek `app_metadata.role === 'admin'`).
- **Sumber:** `backend/app/controllers/admin_controller.py` L6-98

### 3. Layer Backend Service (`<<service>>`)

#### **AnalysisService**
Orkestrasi inti analisis: validasi gambar, upload storage, create record, panggil pipeline AI, polling status, signed URL generation, dan manajemen antrean.
- **Dependencies:** `AnalysisRepository`, `StorageService`, `run_pipeline` (AI), `AnalysisJobQueue` (in-memory FIFO)
- Tidak melakukan inferensi AI sendiri — delegasikan ke `AIInference.run_pipeline()` (boundary TASK 08).
- **Sumber:** `backend/app/services/analysis_service.py` L269+

#### **AdminService**
Operasi administrasi dokter menggunakan service-role Supabase client (bypass RLS).
- **Method:** `list_doctors`, `get_doctor`, `approve_doctor`, `reject_doctor`, `get_statistics`
- **Validasi:** UUID guard, transisi status (`pending` → `approved`/`rejected`), verifikasi single-row update
- **Sumber:** `backend/app/services/admin_service.py` L27+

#### **StorageService**
Manajemen path & operasi Supabase Storage bucket (private).
- **Path convention:** `analysis/{user_id}/{analysis_id}/{category}/{filename}` (category: original, segmentation, gradcam)
- **Ownership validation:** `validate_path_ownership` cegah cross-user access
- **Sumber:** `backend/app/services/storage_service.py` L7+

#### **AnalysisRepository**
Data access untuk tabel `analyses` dengan enforcement ownership & lifecycle.
- **CRUD:** `create`, `get_by_id`, `list_by_user`, `update`, `delete`
- **Validasi:** `validate_lifecycle_status` (processing|completed|failed), `validate_segmentation_status` (detected|not_detected)
- **Sumber:** `backend/app/repositories/analysis_repository.py` L5+

#### **AnalysisJobQueue**
Antrean in-memory FIFO untuk tugas analisis yang menunggu diproses worker.
- **Atribut:** `MAX_WAITING`, `capacity`
- **Sumber:** `backend/app/services/analysis_service.py` L150+

### 4. AI Pipeline (`<<module>>`, `<<dataclass>>`, `<<service>>`)

#### **AIInference** (`<<module>>`)
Abstraksi modul pipeline AI end-to-end (`ai/inference/pipeline.py`).
- **Operasi:** `run_pipeline(...)`, `predict(...)` (via segmentation), `generate_gradcam(...)` (via gradcam)
- **Fase:** preprocessing → inference (TTA × multiscale) → postprocessing → Grad-CAM → komposisi artefak
- **Sumber:** `ai/inference/pipeline.py` L101+

#### **ModelService** (`<<service>>`)
Loader lazy untuk model U-Net + ResNet50 (Scenario 1 Ver.22) yang terverifikasi checkpoint SHA256.
- **Atribut:** `config: ModelConfig`, `device`, `load_count`
- **Sumber:** `ai/inference/model_service.py` L19+

#### **ModelConfig** (`<<dataclass>>`)
Konfigurasi model terverifikasi: arsitektur, encoder, input_size, threshold, TTA, checkpoint SHA256, dll. Hanya atribut.
- **Sumber:** `ai/config/model_config.py` L19+

#### **PipelineResult**, **SegmentationResult**, **GradCAMResult** (`<<dataclass>>`)
Struktur data output pipeline: daftar artefak PNG, mask, heatmap, overlay, dan ukuran/ringkasan. Hanya atribut (tanpa operasi).
- **Sumber:** `ai/inference/pipeline.py` L63, `ai/inference/segmentation.py` L25, `ai/inference/gradcam.py` L38

> Catatan: `AnalysisProgressReporter` (helper internal `AnalysisService` untuk progres throttled DB writes) tidak dipisahkan sebagai kelas sendiri dalam diagram agar tetap konsisten dengan derajat abstraksi kelas lain.

### 5. External (`<<external>>`)

#### **SupabasePlatform**
Kumpulan layanan eksternal Supabase yang digunakan seluruh lapisan: **Auth** (autentikasi & `auth.users`), **DB** (PostgreSQL/PostgREST, tabel `analyses` & `doctor_profiles` dengan RLS), dan **Storage** (bucket aset analisis).
- Digambarkan dengan kotak abu-abu terang (`#F5F5F5`) untuk membedakannya dari kelas internal sistem.

---

## Relasi Antar-Kelas (21 Relasi)

Semua relasi terbukti di source code (instansiasi, import, atau pemanggilan method) dan spesifikasi basis data.

| No | Relasi A → B | Jenis | Multiplicity | Dasar Implementasi |
|----|--------------|-------|--------------|-------------------|
| 1 | AuthContext → SupabasePlatform | Asosiasi | 1 : 1 | `AuthContext.tsx` L1-11 pakai `supabase` client |
| 2 | DoctorProfileService → SupabasePlatform | Asosiasi | 1 : 1 | `profile.ts` query/upsert `doctor_profiles` + Storage avatar |
| 3 | AnalysisClient → AnalysisController | Asosiasi | 1 : 1 | `analysis.ts` L185 `POST /api/analysis` → controller L13 |
| 4 | AnalysisClient → SupabasePlatform | Asosiasi | 1 : 1 | `analysis.ts` L101 Bearer token Supabase |
| 5 | AnalysisController → AnalysisService | Agregasi | 1 : 1 | `analysis_controller.py` L10-11 `self.service = ...AnalysisService()` |
| 6 | AnalysisController → APIError | Dependensi | — | `analysis_controller.py` L3 `from app.core.errors import APIError` |
| 7 | AdminController → AdminService | Agregasi | 1 : 1 | `admin_controller.py` L9-10 `self.service = ...AdminService()` |
| 8 | AdminController → APIError | Dependensi | — | `admin_controller.py` L2 `from app.core.errors import APIError` |
| 9 | AnalysisService → AnalysisRepository | Agregasi | 1 : 1 | `analysis_service.py` L291 `self.repository = ...AnalysisRepository()` |
| 10 | AnalysisService → StorageService | Agregasi | 1 : 1 | `analysis_service.py` L292 `self.storage_service = ...StorageService()` |
| 11 | AnalysisService → AnalysisJobQueue | Agregasi | 1 : 1 | `analysis_service.py` L296 `self.job_queue = ...AnalysisJobQueue()` |
| 12 | AnalysisService → AIInference | Dependensi | — | `analysis_service.py` L22-23 import `run_pipeline` |
| 13 | AnalysisRepository → SupabasePlatform | Asosiasi | 1 : 1 | `analysis_repository.py` L2 `get_supabase_client()` |
| 14 | StorageService → SupabasePlatform | Asosiasi | 1 : 1 | `storage_service.py` L4 `get_supabase_client()` |
| 15 | AdminService → SupabasePlatform | Asosiasi | 1 : 1 | `admin_service.py` L6 `get_supabase_client(use_service_role=True)` |
| 16 | AIInference → ModelService | Dependensi | — | `segmentation.py` L13 `from ai.inference.model_service import ModelService` |
| 17 | AIInference → PipelineResult | Dependensi | — | `pipeline.py` L101-108 `run_pipeline(...) -> PipelineResult` |
| 18 | AIInference → SegmentationResult | Dependensi | — | `segmentation.py` L98-100 `predict(...) -> SegmentationResult` |
| 19 | AIInference → GradCAMResult | Dependensi | — | `gradcam.py` L99-106 `generate_gradcam(...) -> GradCAMResult` |
| 20 | PipelineResult → GradCAMResult | Agregasi | 1 : 1 | `pipeline.py` L70 field `gradcam: GradCAMResult` |
| 21 | ModelService → ModelConfig | Agregasi | 1 : 1 | `model_service.py` L22-23 `__init__(self, config: ModelConfig)` |

**Notasi relasi:**
- **Agregasi:** garis aggregasi dengan hollow diamond (start arrow), multiplicity `1 : 1`
- **Dependensi/Asosiasi:** panah terbuka (open arrow), dashed/solid

**Multiplicity tambahan dari spesifikasi basis data (catatan pendukung, bukan relasi antar kelas diagram):**
- `auth.users 1 : doctor_profiles 0..1` — `user_id` UNIQUE NOT NULL FK (Migration 004 L12, L46)
- `auth.users 1 : analyses 1..*` — `user_id` NOT NULL FK ON DELETE CASCADE (Migration 001)
- `doctor_profiles.approved_by → auth.users 0..* : 0..1` — Migration 007 L33

---

## Model Dua-Role: Admin vs Doctor

Implementasi **tidak menggunakan inheritance** (generalization). Perbedaan role ditangani melalui metadata dan tabel terpisah:

| Aspek | Admin | Doctor |
|-------|-------|--------|
| **Penyimpanan role** | `auth.users.raw_app_meta_data.role = 'admin'` (via Supabase Admin API, service-role) | `doctor_profiles.role = 'doctor'` |
| **Account status** | Tidak ada (akses penuh) | `account_status`: pending → approved/rejected |
| **Profil dokter** | **Tidak dibuat** (trigger skip jika `raw_app_meta_data.role = 'admin'`) | Dibuat otomatis trigger (Migration 008) status `pending` |
| **Akses fitur analisis** | Tidak (decorator `require_admin` hanya untuk admin endpoint) | Ya (decorator `require_approved_doctor` cek status `approved`) |
| **Frontend role check** | `getAdminRoleFromAppMetadata(user)` prioritas tertinggi | Fallback ke `fetchUserProfileStatus` (query `doctor_profiles`) |

**Bukti kode:**
- Backend: `auth.py` `require_admin` baca `app_metadata.role`; `require_approved_doctor` query `doctor_profiles`
- Frontend: `auth.ts` `getAdminRoleFromAppMetadata`, `fetchUserProfileStatus`
- Database: Migration 008 trigger skip admin, `role='doctor'`, `status='pending'`

---

## Ketepatan Notasi UML

1. **Stereotype** digunakan konsisten untuk mengindikasikan layer arsitektur.
2. **Visibility** (`+` publik, `-` private) diterapkan pada atribut dan operasi.
3. **Aggregasi** menggunakan hollow diamond (start arrow) dengan multiplicity `1 : 1`; **dependensi** menggunakan panah terbuka.
4. **Multiplicity** ditempatkan pada ujung relasi yang benar, dibuktikan FK/UNIQUE constraint basis data.
5. **Tidak ada Generalization** untuk Admin/Doctor — sesuai implementasi aktual.
6. **Kompartemen class:** nama (stereotipe + nama), atribut (dengan tipe), operasi (dengan parameter & return). Kelas `<<dataclass>>` hanya memiliki kompartemen atribut (operasi kosong).

---

## Kesesuaian dengan Tujuh Alur Utama

| Alur | Kelas Terlibat (Sesuai Diagram) |
|------|----------------------------------|
| **Sign Up** | AuthContext → SupabasePlatform → (trigger) doctor_profiles |
| **Sign In** | AuthContext → SupabasePlatform → doctor_profiles (role/status) |
| **Upload Image** | AnalysisClient → AnalysisController → AnalysisService → StorageService |
| **Segmentation** | AnalysisService → AIInference → ModelService → ModelConfig |
| **History** | AnalysisClient → AnalysisController → AnalysisService → AnalysisRepository |
| **Doctor Profile** | DoctorProfileService → SupabasePlatform |
| **Sign Out** | AuthContext → SupabasePlatform |

Semua alur terpetakan tanpa celah pada Class Diagram.

---

## Kesesuaian dengan Diagram Bab IV Lainnya

- **ERD:** Tabel `analyses`, `doctor_profiles`, FK, UNIQUE constraint identik dengan yang digambarkan
- **Use Case Diagram:** 7 use case terwakili penuh oleh kelas di diagram
- **Activity Diagram (7):** Alur aktivitas konsisten dengan urutan pemanggilan controller → service → repository
- **Sequence Diagram (7):** Pesan antarobjek (lifeline) sesuai relasi Class Diagram

---

## Verifikasi Format dan Kualitas Visual

| Format | File | Status | Detail |
|--------|------|--------|--------|
| DrawIO XML | `CLASS_DIAGRAM_PIXELT_FINAL.drawio` | ✅ Valid | Root `<mxfile>`, 18 vertex kelas, 21 edge, 14 text multiplicity |
| PNG | `CLASS_DIAGRAM_PIXELT_FINAL.png` | ✅ Render valid | 3750 × 3780 px (scale 3×), latar putih, tidak terpotong/overlap |
| SVG | `CLASS_DIAGRAM_PIXELT_FINAL.svg` | ✅ Valid XML | Root `<svg>`, 18 class body rects, 14 multiplicity text |

Konsistensi drawio ↔ SVG ↔ PNG telah diverifikasi secara terprogram: jumlah kelas, atribut, operasi, relasi, dan label multiplicity cocok antara ketiga format.

---

## Penutup

Class Diagram PIXEL-T versi **FINAL** telah melalui verifikasi independen menyeluruh terhadap:
- **18 kelas** dengan dasar implementasi di source code
- **44 atribut** dan **53 operasi** terverifikasi baris per baris
- **21 relasi** dengan multiplicity terbukti kode dan constraint basis data
- **14 label multiplicity** konsisten di drawio dan SVG
- Konsistensi lintas tiga format file (drawio / PNG / SVG)
- Ketepatan notasi UML dan kualitas visual (latar putih, tidak overlap, tidak terpotong)

Diagram ini **layak digunakan** sebagai **Gambar 4.x** pada Bab IV skripsi S1.

---

**File Terkait:**
- `CLASS_DIAGRAM_PIXELT_FINAL.drawio` — Sumber diagram (editable)
- `CLASS_DIAGRAM_PIXELT_FINAL.png` — Export PNG (3750 × 3780)
- `CLASS_DIAGRAM_PIXELT_FINAL.svg` — Export SVG
- `AUDIT_INDEPENDEN_CLASS_DIAGRAM_PIXELT_FINAL.md` — Laporan audit lengkap
- `MATRIKS_BUKTI_AUDIT_CLASS_DIAGRAM_PIXELT_FINAL.md` — Matriks bukti detail
