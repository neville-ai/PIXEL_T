# AUDIT KESESUAIAN SKRIPSI VS IMPLEMENTASI KODE AKTUAL WEB PIXEL-T

**Tanggal:** 9 November 2026  
**Status:** READ-ONLY / AUDIT KOMPARATIF AKADEMIK VS KODE PRODUKSI  
**Dokumen:** `docs/audit/02_kesesuaian_skripsi_vs_kode.md`  
**Sumber Kebenaran (Ground Truth):** Repositori web PIXEL-T, checkpoint model `ai/models/`, migrasi `database/migrations/`, dan notebook pelatihan `references/`.

---

## 3A. Kesesuaian Model & Inferensi (Skripsi vs Notebook vs Kode)

### 1. Arsitektur Model: U-Net ResNet-50 Tunggal vs Narasi "Dua Model"
- **Temuan Discrepancy Kritis pada Narasi Skripsi:**  
  Pada draf naskah skripsi awal dan deskripsi *use case* (misalnya [`references/bab 4/SPESIFIKASI_TUJUH_USE_CASE_PIXELT.md:50`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/references/bab 4/SPESIFIKASI_TUJUH_USE_CASE_PIXELT.md#L50)), terdapat narasi yang keliru menyatakan:  
  *"Sistem menjalankan model U-Net untuk menghasilkan segmentasi biner... Sistem menjalankan model ResNet50 secara bersamaan untuk mengklasifikasikan citra dan menghasilkan peta Grad-CAM."*
- **Fakta Implementasi Kode & Notebook Pelatihan:**  
  Pada kode sumber aktual [`ai/config/model_config.py:18-39`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/ai/config/model_config.py#L18-L39), [`ai/inference/model_service.py:35-65`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/ai/inference/model_service.py#L35-L65), dan notebook pelatihan Kaggle [`references/PIXEL-T_Scenario1_Ver22_Ver1NoNormal_4_Dice0.9510_IoU0.9136_Kaggle.ipynb`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/references/PIXEL-T_Scenario1_Ver22_Ver1NoNormal_4_Dice0.9510_IoU0.9136_Kaggle.ipynb):
  - Sistem **TIDAK MENGGUNAKAN DUA MODEL TERPISAH**.
  - Model adalah **satu arsitektur terpadu**: `smp.Unet(encoder_name="resnet50", encoder_weights="imagenet", decoder_attention_type="scse", in_channels=3, classes=1)`.
  - ResNet-50 berperan sebagai **encoder backbone** yang mengekstraksi representasi fitur hierarkis, sedangkan U-Net bertindak sebagai *decoder* dengan modul atensi scSE (*Spatial and Channel Squeeze & Excitation*).
  - Grad-CAM diaplikasikan **langsung pada lapisan konvolusi terakhir decoder U-Net** (`decoder.blocks.4.conv2.0`), bukan pada model klasifikasi terpisah ([`ai/inference/gradcam.py:99-150`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/ai/inference/gradcam.py#L99-L150)).
- **Tindakan Perbaikan Naskah Skripsi:**  
  Seluruh narasi di Bab 2, Bab 4, dan Bab 5 yang menyebutkan "dua model paralel" WAJIB DIREVISI menjadi: *"Satu model U-Net terintegrasi dengan backbone encoder ResNet-50 dan mekanisme atensi scSE, di mana visualisasi Grad-CAM dihitung langsung dari lapisan konvolusi akhir decoder U-Net terhadap logit area polip."*

### 2. Parameter Inferensi, TTA, dan Pasca-Pemrosesan

| Parameter | Naskah Skripsi (Draf Awal) | Notebook Pelatihan | Kode Produksi Aktual (`MODEL_CONFIG`) | Status Kesesuaian |
| :--- | :--- | :--- | :--- | :---: |
| **Arsitektur** | U-Net & ResNet50 (disebut 2 model) | U-Net (backbone ResNet-50) | U-Net (`encoder: resnet50`) | **DISCREPANCY (Perlu revisi naskah)** |
| **Decoder Attention** | Tidak selalu dirinci | scSE (Spatial & Channel S&E) | `decoder_attention: "scse"` | **Sesuai** |
| **Ukuran Citra Input** | $512 \times 512$ piksel | $512 \times 512$ piksel | `input_size: 512`, `channels: 3` | **Sesuai Sempurna** |
| **Ambang Probabilitas** | 0.50 (asumsi biner standar) | 0.55 (optimal threshold) | `threshold: 0.55` | **DISCREPANCY KECIL (Perlu penegasan 0.55)** |
| **Test-Time Augmentation (TTA)** | Sering digambarkan flip horizontal saja | Multi-scale + multi-orientation | 5 Skala (0.85, 0.95, 1.0, 1.05, 1.15) $\times$ 5 Orientasi = 25 Forward Passes | **DISCREPANCY (Naskah skripsi harus memperjelas 25 forward passes)** |
| **Pasca-Pemrosesan Masker** | Morphological opening/closing umum | Closing + Opening + Area filter | Closing $(3\times3) \to$ Opening $(3\times3) \to$ Area Filter ($\ge 25\text{px}) \to$ Fill Holes $\to$ Contour Smoothing ($\epsilon = 0.005$) | **Sesuai Sempurna** ([`ai/inference/postprocessing.py:26-42`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/ai/inference/postprocessing.py#L26-L42)) |
| **Checkpoint Model** | Disebut "Scenario 1" | Ver22 (Best) | `PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth` (SHA-256: `46521AE9...C581`) | **Sesuai Sempurna** |

---

## 3B. Kesesuaian Use Case (Bab 4 vs Implementasi Kode Aktual)

Pada Bab 4 versi awal terdapat 7 use case yang belum memisahkan peran **Admin** dan **Dokter**. Setelah audit mendalam di [`references/bab 4/AUDIT_USE_CASE_DIAGRAM_PIXELT.md`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/references/bab 4/AUDIT_USE_CASE_DIAGRAM_PIXELT.md), sistem aktual memuat **3 Aktor** (Pengguna Belum Terdaftar, Dokter Terverifikasi, Administrator) dan **14 Use Case** terverifikasi pada kode:

| No | Nama Use Case Bab 4 | Aktor Utama | Status Kode Aktual | File & Baris Bukti Implementasi |
| :- | :--- | :--- | :---: | :--- |
| 1 | **Sign Up** | Calon Dokter | Terverifikasi | [`frontend/src/pages/auth/Register.tsx:18`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/auth/Register.tsx#L18), [`database/migrations/008_create_doctor_profile_trigger.sql:1-40`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/database/migrations/008_create_doctor_profile_trigger.sql#L1-L40) (status `pending`) |
| 2 | **Sign In** | Dokter & Admin | Terverifikasi | [`frontend/src/pages/auth/Login.tsx:18`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/auth/Login.tsx#L18), [`frontend/src/context/AuthContext.tsx:102-150`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/context/AuthContext.tsx#L102-L150) |
| 3 | **Reset Password** | Dokter & Admin | Terverifikasi | [`frontend/src/pages/auth/ResetPassword.tsx:11`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/auth/ResetPassword.tsx#L11), [`frontend/src/services/auth.ts:140-175`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/services/auth.ts#L140-L175) |
| 4 | **View Dashboard** | Dokter | Terverifikasi | [`frontend/src/pages/dashboard/Dashboard.tsx:21`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/dashboard/Dashboard.tsx#L21) |
| 5 | **Upload Image** | Dokter (`approved`) | Terverifikasi | [`frontend/src/pages/analysis/NewAnalysis.tsx:32`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/analysis/NewAnalysis.tsx#L32), [`backend/app/routes/analysis.py:13`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/routes/analysis.py#L13) |
| 6 | **Segmentation** | Dokter (`approved`) | Terverifikasi | [`backend/app/services/analysis_service.py:270-490`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/services/analysis_service.py#L270-L490) (async pipeline via queue) |
| 7 | **View Segmentation Result** | Dokter (`approved`) | Terverifikasi | [`frontend/src/pages/analysis/AnalysisResult.tsx:55`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/analysis/AnalysisResult.tsx#L55), [`backend/app/routes/analysis.py:31`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/routes/analysis.py#L31) |
| 8 | **View History** | Dokter (`approved`) | Terverifikasi | [`frontend/src/pages/history/History.tsx:22`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/history/History.tsx#L22), [`backend/app/routes/analysis.py:47`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/routes/analysis.py#L47) |
| 9 | **Search & Filter History** | Dokter (`approved`) | Terverifikasi | [`frontend/src/pages/history/History.tsx:120-175`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/history/History.tsx#L120-L175) (client-side `useMemo` search/filter/date) |
| 10 | **Delete History** | Dokter (`approved`) | Terverifikasi | [`frontend/src/pages/history/History.tsx:210-245`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/history/History.tsx#L210-L245), [`backend/app/routes/analysis.py:58`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/routes/analysis.py#L58) |
| 11 | **View Doctor Profile** | Dokter (`approved`) | Terverifikasi | [`frontend/src/pages/profile/DoctorProfile.tsx:16`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/profile/DoctorProfile.tsx#L16), [`frontend/src/services/profile.ts:25-60`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/services/profile.ts#L25-L60) |
| 12 | **Edit Doctor Profile** | Dokter (`approved`) | Terverifikasi | [`frontend/src/pages/profile/DoctorProfile.tsx:180-280`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/profile/DoctorProfile.tsx#L180-L280), [`frontend/src/services/profile.ts:65-120`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/services/profile.ts#L65-L120) |
| 13 | **View Admin Dashboard** | Administrator | Terverifikasi | [`frontend/src/pages/admin/AdminDashboard.tsx:23`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/admin/AdminDashboard.tsx#L23), [`backend/app/routes/admin.py:9-28`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/routes/admin.py#L9-L28) |
| 14 | **Approve/Reject Doctor** | Administrator | Terverifikasi | [`frontend/src/pages/admin/AdminDashboard.tsx:110-185`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/admin/AdminDashboard.tsx#L110-L185), [`backend/app/routes/admin.py:30-45`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/routes/admin.py#L30-L45) |

---

## 3C. Kesesuaian Activity Diagram & Sequence Diagram

### 1. Alur Sign In
- **Di Skripsi:** Pengguna memasukkan email/password $\to$ diverifikasi $\to$ masuk dashboard.
- **Di Kode Aktual:**
  1. Frontend memanggil `supabase.auth.signInWithPassword()` ([`frontend/src/context/AuthContext.tsx:115`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/context/AuthContext.tsx#L115)).
  2. Supabase Auth mengembalikan objek user beserta JWT.
  3. `AuthContext` memeriksa apakah user memiliki `app_metadata.role === 'admin'`:
     - Jika Admin: dialihkan ke `/admin`.
     - Jika bukan Admin: query ke `doctor_profiles` untuk mengecek `account_status`:
       - `approved`: dialihkan ke `/dashboard`.
       - `pending`: sesi ditahan dan ditampilkan notifikasi menunggu persetujuan admin.
       - `rejected`: sesi diakhiri dan ditampilkan pesan penolakan dengan alasan dari admin.

### 2. Alur Sign Up
- **Di Skripsi:** Form pendaftaran $\to$ data tersimpan $\to$ langsung aktif.
- **Di Kode Aktual:**
  1. Frontend memanggil `supabase.auth.signUp()` membawa metadata `full_name`, `hospital`, `primary_specialty` ([`frontend/src/pages/auth/Register.tsx:65-95`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/auth/Register.tsx#L65-L95)).
  2. Database Trigger PostgreSQL [`database/migrations/008_create_doctor_profile_trigger.sql`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/database/migrations/008_create_doctor_profile_trigger.sql) secara otomatis membuat baris baru di `public.doctor_profiles` dengan `role = 'doctor'` dan `account_status = 'pending'`.
  3. Akun baru **tidak dapat langsung menggunakan fitur analisis** sebelum disetujui oleh admin di `/admin`.

### 3. Alur Upload Image & Segmentasi
- **Di Skripsi:** Citra diunggah $\to$ U-Net dan ResNet-50 memproses bersamaan $\to$ hasil ditampilkan.
- **Di Kode Aktual (Multi-stage Verification Flow):**
  1. Frontend memeriksa tipe MIME dan ukuran $\le 10$ MB, lalu mengirim `multipart/form-data` ke `POST /api/analysis`.
  2. **Gerbang 1 (Input Domain Gate):** `AnalysisService` memanggil `ColonoscopyDomainValidator.validate_bytes()`. Jika REJECT atau UNCERTAIN, dibatalkan seketika dengan status 400.
  3. Citra valid diunggah ke *private bucket* Supabase Storage `original-images`.
  4. Baris sesi dibuat di tabel `analyses` dengan status `processing`.
  5. Pekerjaan dimasukkan ke in-memory FIFO queue (`AnalysisJobQueue`, max waiting 3).
  6. *Background worker thread* mengambil job dan menjalankan `run_pipeline()`:
     - Preprocessing (512x512 ImageNet tensor).
     - Inferensi U-Net dengan 25 forward passes TTA.
     - Pasca-pemrosesan morfologi & smoothing.
     - **Gerbang 2 (Post-Segmentation Validator):** Evaluasi keyakinan masker (`max_prob < 0.70` atau `mean_prob < 0.62` atau `area < 100px` $\to$ `LOW_CONFIDENCE`).
     - Pembuatan Grad-CAM terarah.
     - Penyimpanan 4 artefak PNG ke Supabase Storage `analysis-results`.
  7. Rekaman DB diperbarui menjadi `completed`.
  8. **Gerbang 3 (Visual Warning Flag):** Frontend yang melakukan polling setiap 2 detik mendeteksi selesai dan menampilkan badge serta banner peringatan kuning jika tergolong `LOW_CONFIDENCE`.

---

## 3D. Audit Class Diagram (17 Kelas Bab 4 vs Kode Aktual)

Pemeriksaan silang 17 kelas dari [`references/bab 4/CLASS_DIAGRAM_FINAL_PIXELT.puml`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/references/bab 4/CLASS_DIAGRAM_FINAL_PIXELT.puml) terhadap implementasi fisik:

| No | Nama Kelas di Bab 4 | Tipe / Stereotype | Keberadaan Fisik di Kode Aktual | Catatan Arsitektural & Perbedaan Implementasi |
| :- | :--- | :--- | :---: | :--- |
| 1 | `AuthController` | `<<controller>>` | Absen sebagai kelas backend | Di backend ditangani dekorator `@require_auth` di [`backend/app/core/auth.py:11`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/core/auth.py#L11). Autentikasi utama dilakukan langsung oleh Supabase Auth SDK di frontend ([`frontend/src/services/auth.ts`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/services/auth.ts)). |
| 2 | `AdminController` | `<<controller>>` | **Ada** | [`backend/app/controllers/admin_controller.py:10`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/controllers/admin_controller.py#L10) |
| 3 | `AnalysisController` | `<<controller>>` | **Ada** | [`backend/app/controllers/analysis_controller.py:14`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/controllers/analysis_controller.py#L14) |
| 4 | `DoctorProfileController` | `<<controller>>` | Absen di backend | Operasi profil dokter dilakukan langsung dari klien ke Supabase Database menggunakan RLS di [`frontend/src/services/profile.ts`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/services/profile.ts). |
| 5 | `HistoryController` | `<<controller>>` | Terintegrasi | Menjadi metode `list_history()` dan `delete_analysis()` di dalam `AnalysisController` ([`analysis_controller.py:45-75`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/controllers/analysis_controller.py#L45-L75)), bukan kelas controller terpisah. |
| 6 | `AuthService` | `<<service>>` | Terintegrasi | Fungsi logika autentikasi berada di `backend/app/core/auth.py` dan `frontend/src/context/AuthContext.tsx`. |
| 7 | `AdminService` | `<<service>>` | **Ada** | [`backend/app/services/admin_service.py:10`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/services/admin_service.py#L10) |
| 8 | `AnalysisService` | `<<service>>` | **Ada** | [`backend/app/services/analysis_service.py:270`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/services/analysis_service.py#L270) |
| 9 | `DoctorProfileService` | `<<service>>` | Ada di Frontend | [`frontend/src/services/profile.ts:15-180`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/services/profile.ts#L15-L180) |
| 10 | `StorageService` | `<<service>>` | **Ada** | [`backend/app/services/storage_service.py:15`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/services/storage_service.py#L15) |
| 11 | `AnalysisRepository` | `<<repository>>` | **Ada** | [`backend/app/repositories/analysis_repository.py:10`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/backend/app/repositories/analysis_repository.py#L10) |
| 12 | `DoctorProfileRepository`| `<<repository>>` | Terintegrasi | Klien Supabase langsung di frontend dan service role query di `admin_service.py`. |
| 13 | `AdminRepository` | `<<repository>>` | Terintegrasi | Logika persistensi admin terintegrasi di `admin_service.py` memanggil Supabase service-role client. |
| 14 | `AnalysisSession` (Model) | `<<entity>>` | **Ada (Tabel DB)** | Tabel `public.analyses` ([`database/migrations/001_create_analyses_and_storage.sql`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/database/migrations/001_create_analyses_and_storage.sql)) |
| 15 | `DoctorProfile` (Model) | `<<entity>>` | **Ada (Tabel DB)** | Tabel `public.doctor_profiles` ([`database/migrations/004_create_doctor_profiles.sql`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/database/migrations/004_create_doctor_profiles.sql)) |
| 16 | `AdminUser` (Model) | `<<entity>>` | Virtual di Supabase | Disimpan pada atribut `raw_app_meta_data.role = 'admin'` di tabel `auth.users`, bukan tabel `admins` terpisah ([`007_add_role_and_account_status.sql:50-70`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/database/migrations/007_add_role_and_account_status.sql#L50-L70)). |
| 17 | `AIInferenceService` / Pipeline | `<<module>>` | **Ada** | Diimplementasikan melalui modul fungsional [`ai/inference/pipeline.py`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/ai/inference/pipeline.py) dan kelas `ModelService` di [`ai/inference/model_service.py`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/ai/inference/model_service.py). |

**Rekomendasi Revisi Class Diagram Skripsi:**
Diagram kelas pada `CLASS_DIAGRAM_FINAL_PIXELT.puml` telah merefleksikan arsitektur aktual secara akurat dengan menandai kelas-kelas di frontend, backend, dan entitas basis data Supabase. Penjelasan di Bab IV skripsi harus menjelaskan secara gamblang bahwa PIXEL-T mengadopsi arsitektur *Backend-as-a-Service (BaaS)* modern di mana operasi profil dokter didelegasikan langsung ke Supabase dengan perlindungan RLS, sementara komputasi intensif analisis didelegasikan ke backend Flask.

---

## 3E. Kesesuaian Entity Relationship Diagram (ERD) vs Migrasi Database

Berdasarkan naskah Bab 4 dan berkas migrasi [`database/migrations/001_create_analyses_and_storage.sql`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/database/migrations/001_create_analyses_and_storage.sql) s.d. `008_create_doctor_profile_trigger.sql`:

```
+------------------------------------+
|             auth.users             |
|------------------------------------|
| PK id: UUID                        |
|    email: VARCHAR                  |
|    raw_app_meta_data: JSONB        |  <-- role='admin'
+------------------------------------+
             | 1
             |
             +-----------------------+
             | 1                     | 1
             v 0..*                  v 0..1
+-----------------------------+  +--------------------------------+
|       public.analyses       |  |     public.doctor_profiles     |
|-----------------------------|  |--------------------------------|
| PK id: UUID                 |  | PK id: UUID                    |
| FK user_id: UUID (CASCADE)  |  | FK user_id: UUID (UNIQUE)      |
|    status: VARCHAR(20)      |  |    full_name: TEXT             |
|    current_step: VARCHAR    |  |    role: TEXT ('doctor')       |
|    progress_percent: INT    |  |    account_status: TEXT        |
|    original_image_path: TXT |  |    approved_by: UUID (FK)      |
|    binary_mask_path: TEXT   |  |    approved_at: TIMESTAMPTZ    |
|    segmentation_overlay:... |  |    rejection_reason: TEXT      |
|    segmentation_status: ... |  |    education: JSONB            |
|    area_pixels: INT         |  |    experience: JSONB           |
|    gradcam_heatmap_path: ...|  |    str_number: TEXT            |
|    model_architecture: TEXT |  |    hospital: TEXT              |
|    model_checkpoint_sha256  |  |    avatar_url: TEXT            |
+-----------------------------+  +--------------------------------+
```

### Analisis Kesesuaian:
1. **Tidak Ada Tabel `admins` Terpisah:** Pada beberapa draf skripsi mahasiswa sering digambarkan tabel `admins` atau `users` umum. Di implementasi nyata, entitas admin melekat langsung pada `auth.users` Supabase melalui klaim `app_metadata.role = 'admin'`, sehingga integritas keamanan terjamin tanpa redundansi tabel.
2. **Kardinalitas Sempurna:**
   - `auth.users` $\to$ `analyses`: $1$ ke $0..\ast$ (Satu akun dokter memiliki banyak riwayat analisis).
   - `auth.users` $\to$ `doctor_profiles`: $1$ ke $0..1$ (Dibatasi oleh `CONSTRAINT doctor_profiles_user_id_key UNIQUE (user_id)`). Akun admin tidak memiliki baris profil dokter.

---

## 3F. Kesesuaian Antarmuka Pengguna (Bab 5.5 vs Frontend React)

Pemeriksaan komparatif tampilan bab 5.5 terhadap komponen React:
1. **Halaman Login & Register:**  
   Komponen [`Login.tsx`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/auth/Login.tsx) dan [`Register.tsx`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/auth/Register.tsx) memuat logo PIXEL-T, *opening animation*, penanganan pesan error kontras tinggi, dan formulir pendaftaran calon dokter lengkap dengan spesialisasi klinis.
2. **Halaman Analisis Baru:**  
   Komponen [`NewAnalysis.tsx`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/analysis/NewAnalysis.tsx) mengimplementasikan zona seret-unggah (*drag-drop*), pratinjau citra, dan penanganan spesifik error penolakan gerbang domain (`NOT_COLONOSCOPY_IMAGE` dan `UNCERTAIN_COLONOSCOPY_IMAGE`).
3. **Halaman Hasil Analisis:**  
   Komponen [`AnalysisResult.tsx`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/analysis/AnalysisResult.tsx) menyajikan layout empat panel: Citra Asli, Masker Biner, Overlay Segmentasi, dan Heatmap Grad-CAM, disertai metrik kuantitatif (luas piksel, rasio bidang pandang, bounding box) serta badge kategori deteksi dan banner klinis.
4. **Halaman Riwayat:**  
   Komponen [`History.tsx`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/history/History.tsx) memuat tabel paginasi dengan filter interaktif nama berkas, status analisis, dan rentang tanggal tanpa perlu me-reload halaman.
5. **Halaman Dasbor Admin:**  
   Komponen [`AdminDashboard.tsx`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/frontend/src/pages/admin/AdminDashboard.tsx) menampilkan kartu statistik pendaftaran dokter, tabel verifikasi registrasi, modal penolakan beralasan, dan tombol persetujuan satu-klik.

---

## 3G. Status Pengujian Perangkat Lunak (Backend & Frontend)

- **Backend Unit & Integration Tests (Pytest):**  
  Terletak di [`tests/`](file:///c:/Users/nevil/OneDrive/Dokumen/SKRIPSI/WEB_PIXELT/tests/):
  - `tests/ai/test_model_integration.py`: Pengujian verifikasi arsitektur U-Net ResNet-50, kesesuaian checkpoint SHA-256, determinisme inferensi, dan konsistensi Grad-CAM.
  - `tests/backend/test_analysis.py`: Pengujian endpoint API analisis, otentikasi dokter, validasi batas ukuran file, dan penolakan gerbang domain.
  - `tests/backend/test_admin.py` & `test_auth.py`: Pengujian otorisasi berbasis peran admin dan alur verifikasi dokter.
- **Frontend Unit & Component Tests (Vitest):**  
  - Mencakup pengujian komponen rute (`AdminRoute.test.tsx`, `ProtectedRoute.test.tsx`), pengujian kontras warna aksesibilitas WCAG (`statusText.contrast.test.tsx`), dan pengujian logika pembantu antarmuka.

