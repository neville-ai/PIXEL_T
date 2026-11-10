# PETA SISTEM DAN ARSITEKTUR LENGKAP WEB PIXEL-T

**Tanggal Audit:** 9 November 2026  
**Status Audit:** READ-ONLY SYSTEM AUDIT  
**Dokumen:** `docs/audit/00_peta_sistem.md`  
**Tujuan:** Peta komprehensif seluruh sistem web PIXEL-T mencakup arsitektur, API routes, halaman antarmuka, basis data, pipeline AI, antrean latar belakang, dan konfigurasi.

---

## 2.1 Ringkasan Arsitektur & Stack Teknologi

PIXEL-T adalah aplikasi web berbasis *deep learning* untuk segmentasi polip kolorektal dan visualisasi *explainable AI* (Grad-CAM) dari citra endoskopi kolonoskopi. Sistem ini menerapkan arsitektur *three-tier decoupled* yang terbagi menjadi:

```
[ Klien Web (React + TS + Vite) ]
             |
             | HTTP/REST (Bearer JWT)
             v
[ Server Backend (Python Flask) ] <---> [ Basis Data & Storage (Supabase) ]
             |
             v
[ AI Inference Engine (PyTorch + SMP) ]
```

### Rincian Stack Teknologi
1. **Frontend:**
   - **Framework:** React 18.2.0 dengan TypeScript 5.2.2, di-bundle menggunakan Vite 5.1.4.
   - **Styling:** Tailwind CSS 3.4.1 dengan dukungan tema *light/dark mode*.
   - **Komponen Ikon:** `lucide-react` (0.344.0).
   - **Routing:** `react-router-dom` (v6.22.3) dengan pemisahan *Route Guards* (`PublicOnlyRoute`, `ProtectedRoute`, `DoctorRoute`, `AdminRoute`).
   - **Testing:** Vitest + React Testing Library + `@testing-library/jest-dom`.

2. **Backend:**
   - **Bahasa & Framework:** Python 3.11, Flask 3.0.2 (*Application Factory pattern*).
   - **Cross-Origin Resource Sharing:** Flask-CORS 4.0.0.
   - **Autentikasi & Otorisasi:** Integrasi Supabase Auth JWT dengan dekorator peran (`@require_auth`, `@require_approved_doctor`, `@require_admin`).
   - **Arsitektur Kode:** Pola Controller-Service-Repository modular.

3. **Mesin AI (Inference Engine):**
   - **Deep Learning Framework:** PyTorch 2.1.2 + CUDA/CPU auto-select.
   - **Model Backbone:** `segmentation_models_pytorch` (smp) U-Net dengan *encoder* ResNet-50 dan *decoder attention* scSE (*Spatial and Channel Squeeze & Excitation*).
   - **Ekstraksi Fitur & Domain Gate:** OpenCV (`cv2`) 4.9.0, SciPy 1.11.4, NumPy 1.26.4, Pillow 10.2.0.
   - **Explainability:** Grad-CAM terarah (*mask-guided target objective*) pada lapisan akhir *decoder* (`decoder.blocks.4.conv2.0`).

4. **Basis Data & Cloud Storage:**
   - **Platform:** Supabase (PostgreSQL 15.1).
   - **Row Level Security (RLS):** Aktif pada seluruh tabel operasional (`analyses`, `doctor_profiles`).
   - **Penyimpanan Berkas (Supabase Storage):** Tiga *bucket* privat:
     - `original-images`: Citra kolonoskopi asli yang diunggah klinisi.
     - `analysis-results`: Artefak biner (`binary_mask.png`, `segmentation_overlay.png`, `gradcam_heatmap.png`, `gradcam_overlay.png`).
     - `profile-avatars`: Foto avatar profil dokter terverifikasi.

---

## 2.2 Inventaris Endpoint / API Route

Seluruh *endpoint* API terdaftar di bawah prefiks `/api` melalui Blueprints di [`backend/app/routes/__init__.py:6-10`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/routes/__init__.py#L6-L10).

| Method | Path | Handler (File:Baris) | Auth & Role | Status | Keterangan |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | [`backend/app/routes/health.py:7`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/routes/health.py#L7) | Public (Tanpa Auth) | Aktif | Health check kesiapan server backend |
| `POST` | `/api/analysis` | [`backend/app/routes/analysis.py:13`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/routes/analysis.py#L13) | Bearer Token, Dokter (`approved`) | Aktif | Unggah citra, validasi gerbang domain, simpan storage, antrekan job |
| `GET` | `/api/analysis/<id>` | [`backend/app/routes/analysis.py:31`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/routes/analysis.py#L31) | Bearer Token, Dokter (`approved`) | Aktif | Polling status, progres %, metrik & signed URL artefak |
| `GET` | `/api/history` | [`backend/app/routes/analysis.py:47`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/routes/analysis.py#L47) | Bearer Token, Dokter (`approved`) | Aktif | Daftar paginasi riwayat analisis milik user terautentikasi |
| `DELETE` | `/api/history/<id>` | [`backend/app/routes/analysis.py:58`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/routes/analysis.py#L58) | Bearer Token, Dokter (`approved`) | Aktif | Hapus rekaman sesi analisis dan artefak storage terkait |
| `GET` | `/api/admin/doctors` | [`backend/app/routes/admin.py:11`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/routes/admin.py#L11) | Bearer Token, Admin (`app_metadata.role='admin'`) | Aktif | Daftar seluruh pendaftaran dokter (filter status opsional) |
| `GET` | `/api/admin/doctors/stats` | [`backend/app/routes/admin.py:18`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/routes/admin.py#L18) | Bearer Token, Admin (`app_metadata.role='admin'`) | Aktif | Statistik agregat pendaftaran dokter (total, pending, approved, rejected) |
| `GET` | `/api/admin/doctors/<id>` | [`backend/app/routes/admin.py:25`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/routes/admin.py#L25) | Bearer Token, Admin (`app_metadata.role='admin'`) | Aktif | Detail profil dokter individual untuk verifikasi |
| `POST` | `/api/admin/doctors/<id>/approve` | [`backend/app/routes/admin.py:32`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/routes/admin.py#L32) | Bearer Token, Admin (`app_metadata.role='admin'`) | Aktif | Persetujuan akun dokter pending oleh administrator |
| `POST` | `/api/admin/doctors/<id>/reject` | [`backend/app/routes/admin.py:38`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/routes/admin.py#L38) | Bearer Token, Admin (`app_metadata.role='admin'`) | Aktif | Penolakan akun dokter pending disertai alasan penolakan |

---

## 2.3 Halaman & Navigasi Frontend

Konfigurasi rute frontend dikelola secara terpusat di [`frontend/src/routes/AppRoutes.tsx:20-112`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/routes/AppRoutes.tsx#L20-L112).

| Path URL | Komponen (File:Baris) | Proteksi / Guard | Fitur Utama |
| :--- | :--- | :--- | :--- |
| `/` | `Navigate to="/login"` | Public | Pengalihan otomatis ke halaman Login |
| `/login` | [`frontend/src/pages/auth/Login.tsx:18`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/auth/Login.tsx#L18) | `PublicOnlyRoute` | Form Sign In dokter/admin, Remember Me, tautan lupa kata sandi |
| `/register` | [`frontend/src/pages/auth/Register.tsx:18`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/auth/Register.tsx#L18) | `PublicOnlyRoute` | Registrasi akun calon dokter (masuk status `pending`) |
| `/reset-password` | [`frontend/src/pages/auth/ResetPassword.tsx:11`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/auth/ResetPassword.tsx#L11) | Public | Form pembaruan kata sandi dari token pemulihan Supabase |
| `/dashboard` | [`frontend/src/pages/dashboard/Dashboard.tsx:21`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/dashboard/Dashboard.tsx#L21) | `ProtectedRoute` | Metrik ringkasan aktivitas dokter, tautan cepat, status akun |
| `/analysis/new` | [`frontend/src/pages/analysis/NewAnalysis.tsx:32`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/analysis/NewAnalysis.tsx#L32) | `ProtectedRoute` | Drag-and-drop unggah citra, validasi klien, penanganan error 400 domain gate |
| `/analysis/:id` | [`frontend/src/pages/analysis/AnalysisResult.tsx:55`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/analysis/AnalysisResult.tsx#L55) | `ProtectedRoute` | Tampilan hasil segmentasi, Grad-CAM, metrik polip, badge verifikasi pasca-segmentasi |
| `/history` | [`frontend/src/pages/history/History.tsx:22`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/history/History.tsx#L22) | `ProtectedRoute` | Tabel riwayat analisis dengan pencarian nama, filter status, filter tanggal, paginasi |
| `/history/:id` | [`frontend/src/pages/history/HistoryDetail.tsx:18`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/history/HistoryDetail.tsx#L18) | `ProtectedRoute` | Detail riwayat analisis statis |
| `/profile` | [`frontend/src/pages/profile/DoctorProfile.tsx:16`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/profile/DoctorProfile.tsx#L16) | `DoctorRoute` | Manajemen profil dokter (spesialisasi, lisensi, RS, bio, avatar) |
| `/admin` | [`frontend/src/pages/admin/AdminDashboard.tsx:23`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/admin/AdminDashboard.tsx#L23) | `AdminRoute` | Verifikasi pendaftaran dokter, persetujuan/penolakan registrasi |
| `*` | [`frontend/src/pages/NotFound.tsx:8`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/NotFound.tsx#L8) | Public | Tampilan 404 Not Found dengan tombol kembali |

---

## 2.4 Skema Database & Row Level Security (RLS)

Basis data dikelola melalui skrip migrasi berurutan di [`database/migrations/`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/database/migrations/).

### 1. Tabel `public.analyses`
Dibuat pada migrasi [`001_create_analyses_and_storage.sql`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/database/migrations/001_create_analyses_and_storage.sql), diperluas oleh `002_add_ai_pipeline_metadata.sql` dan `003_add_analysis_progress.sql`.
- **Primary Key:** `id UUID DEFAULT gen_random_uuid()`
- **Foreign Key:** `user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE`
- **Kolom Kunci:**
  - `status VARCHAR(20) CHECK (status IN ('processing', 'completed', 'failed'))`
  - `current_step VARCHAR(64)`, `progress_percent SMALLINT CHECK (0..100)`
  - `original_image_path TEXT NOT NULL`, `original_filename TEXT`, `original_width INT`, `original_height INT`
  - `binary_mask_path TEXT`, `segmentation_overlay_path TEXT`
  - `segmentation_status VARCHAR(20) CHECK (segmentation_status IS NULL OR segmentation_status IN ('detected', 'not_detected'))`
  - `area_pixels INTEGER`, `area_ratio NUMERIC(7,4)`, `bounding_width_pixels INT`, `bounding_height_pixels INT`
  - `gradcam_heatmap_path TEXT`, `gradcam_overlay_path TEXT`, `gradcam_status VARCHAR(20)`
  - `model_architecture`, `model_version`, `model_checkpoint_sha256`, `tta_scales JSONB`, `summary_text TEXT`
  - `error_code VARCHAR(50)`, `error_message TEXT`
- **Kebijakan RLS (Semua TO authenticated):**
  - SELECT: `auth.uid() = user_id`
  - INSERT: `auth.uid() = user_id`
  - UPDATE: `auth.uid() = user_id`
  - DELETE: `auth.uid() = user_id`

### 2. Tabel `public.doctor_profiles`
Dibuat pada migrasi [`004_create_doctor_profiles.sql`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/database/migrations/004_create_doctor_profiles.sql), diperluas oleh `006_add_avatar_url_to_doctor_profiles.sql` dan `007_add_role_and_account_status.sql`.
- **Primary Key:** `id UUID DEFAULT gen_random_uuid()`
- **Foreign Key:** `user_id UUID NOT NULL UNIQUE REFERENCES auth.users(id) ON DELETE CASCADE`
- **Kolom Kunci:**
  - `full_name TEXT NOT NULL`, `primary_specialty TEXT`, `str_number TEXT`, `hospital TEXT`
  - `role TEXT NOT NULL DEFAULT 'doctor'`
  - `account_status TEXT NOT NULL DEFAULT 'pending'` (`pending`, `approved`, `rejected`)
  - `approved_by UUID REFERENCES auth.users(id)`, `approved_at TIMESTAMPTZ`, `rejection_reason TEXT`
- **Kebijakan RLS:**
  - Authenticated user hanya dapat membaca dan memperbarui baris miliknya (`auth.uid() = user_id`).
  - Backend Service-Role memiliki izin bypass RLS penuh untuk operasi admin (`007_add_role_and_account_status.sql:72-106`).
- **Database Trigger:** [`008_create_doctor_profile_trigger.sql`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/database/migrations/008_create_doctor_profile_trigger.sql) secara otomatis membuat baris `doctor_profiles` saat akun baru dibuat pada `auth.users`, kecuali akun bertanda `app_metadata.role = 'admin'`.

---

## 2.5 Alur Pipeline AI End-to-End

Pipeline AI dieksekusi secara sinkron di dalam thread *background worker* melalui pemanggilan [`ai/inference/pipeline.py:102-180`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/ai/inference/pipeline.py#L102-L180).

```
[ Citra Asli (Bytes) ]
        |
        v
[ Tahap 1: Validasi Domain Input (Gerbang 1) ]
        |---> REJECT / UNCERTAIN  ==> Raise ValueError (Domain Rejection)
        v ACCEPT
[ Tahap 2: Preprocessing ] (Resize 512x512, Normalisasi ImageNet, Tensor RGB)
        |
        v
[ Tahap 3: Inferensi Segmentasi + TTA ] (U-Net ResNet-50, 5 Skala x 5 Orientasi = 25 Pass)
        |
        v
[ Tahap 4: Pasca-Pemrosesan Masker ] (Closing, Opening, Area Filter >= 25px, Fill Holes, Contour Smoothing)
        |
        v
[ Tahap 5: Pengukuran & Validasi Pasca-Segmentasi (Gerbang 2) ]
        |---> max_prob < 0.70 OR mean_prob < 0.62 OR area < 100 px ==> LOW_CONFIDENCE
        |---> area == 0 ==> NO_POLYP_DETECTED
        |---> area >= 100 & prob >= ambang ==> POLYP_DETECTED
        v
[ Tahap 6: Explainable AI (Grad-CAM) ] (Target layer: decoder.blocks.4.conv2.0)
        |
        v
[ Tahap 7: Komposisi Artefak PNG & Upload Storage ]
        |---> binary_mask.png, segmentation_overlay.png, gradcam_heatmap.png, gradcam_overlay.png
```

Rincian file dan baris implementasi tiap tahap:
1. **Tahap 1 (Validasi Domain):** [`ai/inference/domain_validator.py:91-305`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/ai/inference/domain_validator.py#L91-L305). Dieksekusi ganda: pertama di *service gate* [`backend/app/services/analysis_service.py:410-435`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/services/analysis_service.py#L410-L435), kedua di dalam pipeline [`ai/inference/pipeline.py:134-138`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/ai/inference/pipeline.py#L134-L138).
2. **Tahap 2 (Preprocessing):** [`ai/inference/preprocessing.py:1-45`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/ai/inference/preprocessing.py#L1-L45).
3. **Tahap 3 (Inferensi & TTA):** [`ai/inference/segmentation.py:1-120`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/ai/inference/segmentation.py#L1-L120).
4. **Tahap 4 (Pasca-Pemrosesan Masker):** [`ai/inference/postprocessing.py:26-42`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/ai/inference/postprocessing.py#L26-L42).
5. **Tahap 5 (Pengukuran & Validasi Pasca-Segmentasi):** [`ai/inference/postprocessing.py:52-126`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/ai/inference/postprocessing.py#L52-L126).
6. **Tahap 6 (Grad-CAM):** [`ai/inference/gradcam.py:99-188`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/ai/inference/gradcam.py#L99-L188).
7. **Tahap 7 (Komposisi & Penyimpanan):** [`ai/inference/pipeline.py:165-180`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/ai/inference/pipeline.py#L165-L180) dan [`backend/app/services/analysis_service.py:500-560`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/services/analysis_service.py#L500-L560).

---

## 2.6 Alur Async Worker / Background Task

Sistem pemrosesan latar belakang dirancang menggunakan *pure Python standard library* (tanpa Celery/Redis) untuk menjaga portabilitas deployment:
- **Kelas:** `AnalysisJobQueue` di [`backend/app/services/analysis_service.py:151-269`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/services/analysis_service.py#L151-L269).
- **Mekanisme Antrean:** In-memory FIFO berbasis `collections.deque` dengan koordinasi *thread-safety* menggunakan `threading.Condition` dan `threading.Lock`.
- **Kapasitas:** Dibatasi ketat dengan `MAX_WAITING = 3` (total kapasitas antrean 4 job: 1 aktif + 3 menunggu). Jika antrean penuh, endpoint `POST /api/analysis` mengembalikan status HTTP `429 Too Many Requests`.
- **Worker Thread:** Satu thread daemon mandiri (`analysis-worker`) yang mengambil job satu per satu secara sekuensial.
- **Progress Reporting:** Kelas `AnalysisProgressReporter` ([`analysis_service.py:65-149`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/services/analysis_service.py#L65-L149)) memperbarui kolom `progress_percent` dan `current_step` di database PostgreSQL dengan *write throttling* (maksimal tiap 5 forward pass TTA) agar tidak membebani basis data.
- **Deteksi Job Macet (*Stale Detection*):** Waktu henti 15 menit (`STALE_THRESHOLD = timedelta(minutes=15)` di [`analysis_service.py:32`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/services/analysis_service.py#L32)). Jika job berstatus `processing` lebih dari 15 menit dan tidak sedang aktif di thread lokal, sistem menandainya sebagai berpotensi macet tanpa mengubah status DB secara destruktif.

---

## 2.7 Tiga Titik Gerbang Domain (Domain Validation Architecture)

Arsitektur validasi domain pada PIXEL-T terdiri dari tiga komponen yang saling terkoordinasi:

```
[ Input Citra ] 
      |
      v
( Titik 1: Input Domain Gate )  =======> REJECT / UNCERTAIN (HTTP 400, Tolak Sebelum DB/Storage)
      | ACCEPT
      v
[ Pipeline U-Net ]
      |
      v
( Titik 2: Post-Segmentation Gate ) ===> Klasifikasi deteksi (POLYP_DETECTED vs LOW_CONFIDENCE vs NO_POLYP_DETECTED)
      |
      v
( Titik 3: Visual Warning Flag ) ======> Banner Peringatan Kuning & Badge Khusus di Frontend
```

1. **Titik 1: Input Domain Gate**  
   - **Lokasi Kode:** [`ai/inference/domain_validator.py`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/ai/inference/domain_validator.py) & [`backend/app/services/analysis_service.py:410-435`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/services/analysis_service.py#L410-L435).
   - **Fungsi:** Memfilter input non-kolonoskopi (makanan, lanskap, orang, tangkapan layar, organ medis lain).
   - **Keputusan:** Tiga status (`ACCEPT`, `REJECT`, `UNCERTAIN`).
   - **Perilaku:** Jika `REJECT`, mengembalikan error `NOT_COLONOSCOPY_IMAGE` (400). Jika `UNCERTAIN`, mengembalikan error `UNCERTAIN_COLONOSCOPY_IMAGE` (400). Citra yang tidak lolos tidak pernah disimpan ke Supabase Storage dan tidak membuat rekaman sesi analisis.

2. **Titik 2: Post-Segmentation Validation**  
   - **Lokasi Kode:** [`ai/inference/postprocessing.py:96-113`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/ai/inference/postprocessing.py#L96-L113).
   - **Fungsi:** Mengevaluasi keyakinan statistik masker polip hasil inferensi U-Net.
   - **Kriteria Evaluasi:**
     1. Probabilitas puncak polip: `max_prob < 0.70`
     2. Probabilitas rata-rata area polip: `mean_prob < 0.62`
     3. Luas area deteksi sangat kecil (*tiny speckle*): `area_pixels < 100`
   - **Keluaran:** Memberi kategori `LOW_CONFIDENCE` apabila salah satu kriteria terpenuhi, atau `POLYP_DETECTED` jika seluruh kriteria terlampaui.

3. **Titik 3: Visual Warning Flag**  
   - **Lokasi Kode:** [`frontend/src/pages/analysis/AnalysisResult.tsx:250-278`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/analysis/AnalysisResult.tsx#L250-L278) dan serialisasi API di [`backend/app/services/analysis_service.py:637-653`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/services/analysis_service.py#L637-L653).
   - **Fungsi:** Menampilkan indikator visual yang membedakan polip meyakinkan, polip marjinal, dan ketiadaan deteksi:
     - `POLYP_DETECTED`: Badge hijau `"Polyp Detected"`.
     - `LOW_CONFIDENCE`: Badge kuning `"Low Confidence"` disertai banner peringatan klinis: *"Model mendeteksi area polip dengan tingkat keyakinan rendah atau marjinal. Hasil segmentasi kurang meyakinkan dan memerlukan verifikasi serta peninjauan visual langsung oleh dokter spesialis."*
     - `NO_POLYP_DETECTED`: Badge abu-abu `"No Polyp Detected"` disertai catatan klinis: *"Ketiadaan deteksi oleh AI bukan merupakan diagnosis medis normal atau jaminan ketiadaan lesi."*

---

## 2.8 Ringkasan Environment Variable & Konfigurasi

Daftar seluruh variabel lingkungan yang digunakan backend diatur pada [`backend/app/core/config.py:15-85`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/core/config.py#L15-L85):

| Variabel Lingkungan | Nilai Default | Wajib / Opsional | Keterangan |
| :--- | :--- | :--- | :--- |
| `SUPABASE_URL` | Kosong | **Wajib** | URL instans Supabase (`https://<project>.supabase.co`) |
| `SUPABASE_KEY` | Kosong | **Wajib** | Anon public API key Supabase |
| `SUPABASE_SERVICE_ROLE_KEY` | Kosong | **Wajib** | Service-role secret key (bypass RLS untuk worker & admin) |
| `BACKEND_HOST` | `127.0.0.1` | Opsional | Host pengikatan server Flask |
| `BACKEND_PORT` | `5000` | Opsional | Port pengikatan server Flask |
| `DEBUG` | `False` | Opsional | Mode debug Flask |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Opsional | Daftar origin yang diizinkan untuk CORS |
| `MODEL_CHECKPOINT_PATH` | `models/PIXEL-T_...pth` | Opsional | Lokasi absolut/relatif file checkpoint bobot model |
| `ENFORCE_DOMAIN_VALIDATION` | `True` | Opsional | Flag penegakan gerbang validasi domain pada backend |
| `VITE_SUPABASE_URL` | Kosong | **Wajib (Frontend)** | URL Supabase pada environment frontend (`.env`) |
| `VITE_SUPABASE_ANON_KEY` | Kosong | **Wajib (Frontend)** | Anon Key Supabase pada environment frontend (`.env`) |
| `VITE_API_URL` | `http://localhost:5000/api` | Opsional (Frontend) | Base URL endpoint API backend |

