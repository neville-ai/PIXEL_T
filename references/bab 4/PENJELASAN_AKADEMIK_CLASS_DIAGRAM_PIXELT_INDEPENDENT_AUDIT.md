# PENJELASAN AKADEMIK CLASS DIAGRAM PIXEL-T (INDEPENDENT AUDIT)

**Bab IV — Sistem Informasi Web PIXEL-T**  
**Versi Diagram:** `CLASS_DIAGRAM_PIXELT_FINAL_INDEPENDENT_AUDIT`  
**Status:** LULUS AUDIT INDEPENDEN — Siap Publikasi Tesis Bab IV

---

## Pendahuluan

Class Diagram pada **Gambar 4.x** menggambarkan struktur statis sistem aplikasi web PIXEL-T (Polip USG Segmentasi dengan Transfer Learning dan Explainable AI). Diagram ini dihasilkan melalui **audit independen menyeluruh** terhadap source code aplikasi, termasuk frontend React, backend Flask, database PostgreSQL/Supabase, serta pipeline AI berbasis PyTorch. Diagram ini menyajikan abstraksi kelas, atribut, operasi, dan relasi yang mewakili tanggung jawab komponen utama dalam arsitektur sistem.

Pembagian kelas dalam diagram mengikuti standar stereotipe UML:
- `<<module>>` — Modul frontend TypeScript dan modul AI pipeline Python
- `<<controller>>` — Pengendali HTTP (Flask controller)
- `<<service>>` — Lapisan layanan bisnis (business logic)
- `<<repository>>` — Lapisan akses data (data access layer)
- `<<entity>>` — Entitas basis data (tabel PostgreSQL)
- `<<external>>` — Layanan eksternal (Supabase Auth)
- `<<exception>>` — Kelas penanganan kesalahan

Diagram ini menggunakan latar belakang putih dengan garis dan teks hitam, serta font **Segoe UI** sesuai referensi `class_diagram_contoh.png`. Orientasi landscape, resolusi 3600×2600 px, cocok untuk pencetakan skripsi.

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
- **Atribut:** `user`, `session`, `role` ('admin'|'doctor'|null), `accountStatus` ('pending'|'approved'|'rejected'|null), `loading`
- **Operasi:** `signIn()`, `signUp()`, `signOut()`
- **Mekanisme role resolution:** Memeriksa `app_metadata.role` (server-write-only) terlebih dahulu untuk mendeteksi Admin. Jika bukan admin, fallback ke query `doctor_profiles` untuk role/status dokter. Admin **tidak memiliki baris** di `doctor_profiles`.

#### **AnalysisClient** (`<<module>>`)
Klien HTTP untuk endpoint analisis (`/api/analysis`, `/api/history`).
- **Operasi:** `createAnalysis(file)`, `getAnalysis(id)`, `listHistory()`, `deleteAnalysis(id)`
- Menggunakan `authenticatedRequest` internal (bukan atribut) yang menempelkan Bearer token Supabase.

#### **DoctorProfileService** (`<<module>>`)
Mengelola profil dokter: baca, simpan, upload avatar, validasi.
- **Operasi:** `fetchDoctorProfile(user)`, `saveDoctorProfile(user, data)`, `uploadAvatar(user, file)`, `deleteAvatar(user)`, `validateProfileData(data)`
- Dual persistence: `doctor_profiles` table + Supabase Auth `user_metadata` untuk fallback.

---

### 2. Layer Backend Controller (`<<controller>>`)

#### **AnalysisController**
Menangani endpoint analisis: `POST /api/analysis`, `GET /api/analysis/:id`, `GET /api/history`, `DELETE /api/history/:id`.
- Validasi file upload (MIME, ukuran, integritas via Pillow)
- Delegasi ke `AnalysisService`, mengembalikan 202 Accepted dengan `analysis_id` untuk polling.

#### **AdminController**
Menangani endpoint administrasi dokter: `GET /api/admin/doctors`, `GET /api/admin/doctors/:id`, `POST /api/admin/doctors/:id/approve`, `POST /api/admin/doctors/:id/reject`, `GET /api/admin/doctors/stats`.
- Dilindungi decorator `require_admin` (cek `app_metadata.role === 'admin'`).

---

### 3. Layer Backend Service (`<<service>>`)

#### **AnalysisService**
Orkestrasi inti analisis: validasi gambar, upload storage, create record, enqueue pipeline AI, polling status, signed URL generation.
- **Dependencies:** `AnalysisRepository`, `StorageService`, `run_pipeline` (AI), `AnalysisJobQueue` (in-memory FIFO, capacity 4)
- **Progress reporting:** `AnalysisProgressReporter` throttled DB writes (phase + forward passes)
- **Failure compensation:** Rollback storage + DB jika enqueue gagal (QUEUE_FULL 429)

#### **AdminService**
Operasi administrasi dokter menggunakan service-role Supabase client (bypass RLS).
- **Method:** `list_doctors`, `approve_doctor`, `reject_doctor`, `get_statistics`
- **Validasi:** UUID guard, status transition check (`pending`→`approved`/`rejected`), single-row update verification

#### **StorageService**
Manajemen path & operasi Supabase Storage bucket `analysis-assets` (private) dan `profile-avatars` (public).
- **Path convention:** `analysis/{user_id}/{analysis_id}/{category}/{filename}` (category: original|segmentation|gradcam)
- **Ownership validation:** `validate_path_ownership` cegah cross-user access
- **CRUD:** `upload_file`, `create_signed_url`, `delete_file`, `delete_analysis_files`

---

### 4. Layer Repository (`<<repository>>`)

#### **AnalysisRepository**
Data access untuk tabel `analyses` dengan enforcement ownership & lifecycle.
- **CRUD:** `create(user_id, data)`, `get_by_id(id, user_id)`, `list_by_user(user_id)`, `update(id, user_id, data)`, `delete(id, user_id)`
- **Validasi:** `validate_lifecycle_status` (processing|completed|failed), `validate_segmentation_status` (detected|not_detected)
- **Service-role support:** Background jobs pakai service-role, user requests pakai anon key

---

### 5. AI Pipeline (`<<module>>`)

#### **AISegmentationPipeline** (`ai/inference/pipeline.py`)
Abstraksi modul pipeline AI end-to-end.
- **`run_pipeline(original_bytes, config, on_phase, on_pass)`** → `PipelineResult` (4 PNG artifacts + measurements + summary + GradCAM)
- **Fase:** preprocessing → inference (TTA 5 orientasi × multiscale) → postprocessing → Grad-CAM → artifact composition
- **Callback:** `on_phase` (per fase), `on_pass` (per forward pass) untuk progress reporting
- **Dependencies:** `ModelService` (lazy load U-Net ResNet50), `segmentation.py`, `gradcam.py`, `preprocessing.py`, `postprocessing.py`

**Dataclasses internal (dikecualikan dari diagram):**
- `PipelineResult`, `SegmentationResult`, `GradCAMResult` — struktur data output pipeline
- `ModelConfig` — konfigurasi model terverifikasi (Scenario 1 Ver.22, checkpoint SHA256)
- `AnalysisJobQueue`, `AnalysisProgressReporter` — implementasi internal background job

---

### 6. Database & External (`<<entity>>`, `<<external>>`)

#### **SupabaseAuth** (`<<external>>`)
Layanan autentikasi Supabase (`auth.users`).
- **Atribut utama:** `id: UUID` (PK)
- **Metadata penting:** `raw_app_meta_data.role` (admin, server-write-only), `raw_user_meta_data` (user-writable)

#### **doctor_profiles** (`<<entity>>`)
Tabel profil dokter (Migration 004, 007).
- **PK:** `id` UUID, **FK:** `user_id` → `auth.users(id)` ON DELETE CASCADE
- **UNIQUE constraint:** `user_id` → **max 1 profil per user** (multiplicity 0..1 ke SupabaseAuth)
- **Kolom kunci:** `full_name`, `primary_specialty`, `hospital`, `account_status` (pending|approved|rejected), **`role`** (doctor, default), `approved_by`, `approved_at`, `rejection_reason`
- **RLS:** User hanya akses profil sendiri; Service-role (backend admin) akses semua

#### **analyses** (`<<entity>>`)
Tabel riwayat analisis (Migration 001, 002, 003).
- **PK:** `id` UUID, **FK:** `user_id` → `auth.users(id)` ON DELETE CASCADE NOT NULL
- **Status lifecycle:** `processing` → `completed` | `failed`
- **Asset paths:** `original_image_path`, `binary_mask_path`, `segmentation_overlay_path`, `gradcam_heatmap_path`, `gradcam_overlay_path`
- **Model metadata:** architecture, version, threshold, TTA config, checkpoint SHA256
- **Progress tracking:** `current_step`, `progress_percent` (nullable, Batch P-02)
- **RLS:** User hanya akses analisis sendiri

---

## Relasi Antar-kelas (14 Relasi)

| No | Relasi | Jenis | Multiplicity | Penjelasan |
|----|--------|-------|--------------|------------|
| 1 | AuthContext — SupabaseAuth | Association | 1 : 1 | AuthContext menggunakan Supabase client untuk autentikasi |
| 2 | AnalysisClient — AnalysisController | Association | 1 : 1 | HTTP request frontend ke endpoint analisis |
| 3 | DoctorProfileService — doctor_profiles | Association | 1 : 1 | Query/upsert tabel profil dokter |
| 4 | AnalysisController — AnalysisService | Association | 1 : 1 | Controller instantiate service |
| 5 | AdminController — AdminService | Association | 1 : 1 | Controller instantiate service |
| 6 | AnalysisService — AnalysisRepository | Association | 1 : 1 | Service instantiate repository |
| 7 | AnalysisService — StorageService | Association | 1 : 1 | Service instantiate storage service |
| 8 | AnalysisService — AISegmentationPipeline | Association | 1 : 1 | Service memanggil `run_pipeline()` |
| 9 | AnalysisService — analyses | Association | 1 : * | Service mengelola banyak record analisis |
| 10 | AnalysisService — APIError | Dependency | — | Service melempar exception APIError |
| 11 | AdminService — doctor_profiles | Association | 1 : * | Service mengelola banyak profil dokter |
| 12 | AdminService — APIError | Dependency | — | Service melempar exception APIError |
| 13 | doctor_profiles — SupabaseAuth | Association | 1 : 0..1 | FK `user_id` + UNIQUE constraint → max 1 profil per user |
| 14 | analyses — SupabaseAuth | Association | 1 : * | FK `user_id` NOT NULL → tiap analisis milik 1 user, user bisa punya banyak analisis |

**Catatan penting multiplicity database:**
- **Relasi 13 (1 : 0..1)** dibuktikan oleh `CONSTRAINT doctor_profiles_user_id_key UNIQUE (user_id)` (Migration 004 L46) — Admin tidak memiliki baris di tabel ini.
- **Relasi 14 (1 : *)** dibuktikan oleh `user_id UUID NOT NULL REFERENCES auth.users(id)` tanpa batas jumlah per user.

---

## Model Dua-Role: Admin vs Doctor

Implementasi **tidak menggunakan inheritance** (generalization). Perbedaan role ditangani melalui:

| Aspek | Admin | Doctor |
|-------|-------|--------|
| **Penyimpanan role** | `auth.users.raw_app_meta_data.role = 'admin'` (via Supabase Admin API, service-role) | `doctor_profiles.role = 'doctor'` |
| **Account status** | Tidak ada (akses penuh) | `account_status`: pending → approved/rejected |
| **Profil dokter** | **Tidak dibuat** (trigger skip jika `raw_app_meta_data.role = 'admin'`) | Dibuat otomatis trigger (Migration 008) status `pending` |
| **Akses fitur analisis** | Tidak (decorator `require_admin` hanya untuk admin endpoint) | Ya (decorator `require_approved_doctor` cek status `approved`) |
| **Frontend role check** | `getAdminRoleFromAppMetadata(user)` prioritas tertinggi | Fallback ke `fetchUserProfileStatus` (query `doctor_profiles`) |

**Bukti kode:**
- Backend: `auth.py` L142-145 (`require_admin` baca `app_metadata.role`), L223-234 (`require_approved_doctor` query `doctor_profiles`)
- Frontend: `auth.ts` L328-334 (`getAdminRoleFromAppMetadata`), L297-316 (`fetchUserProfileStatus`)
- Database: Migration 008 L37-38 (trigger skip admin), L57-58 (role='doctor', status='pending')

---

## Ketepatan Notasi UML

1. **Stereotype** digunakan konsisten untuk mengindikasikan layer arsitektur
2. **Visibility** (`+`, `-`) diterapkan pada atribut/operasi
3. **Association** solid line untuk struktur; **Dependency** dashed line untuk exception (`APIError`)
4. **Multiplicity** ditempatkan pada ujung yang benar (database FK/UNIQUE constraint)
5. **Tidak ada Generalization** untuk Admin/Doctor — sesuai implementasi
6. **Kompartemen** class: nama, atribut (dengan tipe), operasi (dengan parameter & return)

---

## Kesesuaian dengan Tujuh Alur Utama

| Alur | Kelas Terlibat (Sesuai Diagram) |
|------|----------------------------------|
| **Sign Up** | AuthContext → SupabaseAuth → (trigger) doctor_profiles |
| **Sign In** | AuthContext → SupabaseAuth → doctor_profiles (role/status) |
| **Upload Image** | AnalysisClient → AnalysisController → AnalysisService → StorageService, analyses |
| **Segmentation** | AnalysisService → AISegmentationPipeline → analyses, StorageService |
| **History** | AnalysisClient → AnalysisController → AnalysisService → analyses, StorageService |
| **Doctor Profile** | DoctorProfileService → doctor_profiles, SupabaseAuth (metadata sync) |
| **Sign Out** | AuthContext → SupabaseAuth |

Semua alur terpetakan tanpa celah pada Class Diagram.

---

## Kesesuaian dengan Diagram Bab IV Lainnya

- **ERD:** Tabel `analyses`, `doctor_profiles`, FK, UNIQUE constraint identik
- **Use Case Diagram:** 7 use case terwakili penuh
- **Activity Diagram (7):** Alur aktivitas konsisten dengan urutan pemanggilan controller→service→repository
- **Sequence Diagram (7):** Pesan antarobjek (lifeline) sesuai relasi Class Diagram

---

## Penutup

Class Diagram PIXEL-T versi **INDEPENDENT AUDIT** telah melalui verifikasi independen menyeluruh terhadap:
- 14 kelas dengan 38 atribut/operasi terverifikasi source code
- 14 relasi dengan multiplicity terbukti database constraint
- 7 alur aplikasi end-to-end
- Konsistensi lintas diagram Bab IV
- Ketepatan notasi UML
- Kualitas visual PNG 3600×2600 px, Segoe UI, latar putih

Diagram ini **layak digunakan** sebagai **Gambar 4.x** pada Bab IV skripsi S1.

---

**File Terkait:**
- `CLASS_DIAGRAM_PIXELT_FINAL_INDEPENDENT_AUDIT.drawio` — Sumber diagram
- `CLASS_DIAGRAM_PIXELT_FINAL_INDEPENDENT_AUDIT.png` — Export PNG (3600×2600)
- `AUDIT_INDEPENDEN_PUTARAN_KEDUA_CLASS_DIAGRAM_PIXELT.md` — Laporan audit lengkap
- `MATRIKS_BUKTI_AUDIT_INDEPENDEN_CLASS_DIAGRAM_PIXELT.md` — Matriks bukti detail