# FunctionalSpecification.md

# PIXEL-T — Functional Specification

**Status:** FINAL / LOCKED  
**Product:** PIXEL-T  
**Thesis:** *TRANSFER LEARNING DAN EXPLAINABLE AI UNTUK SEGMENTASI POLIP USUS MENGGUNAKAN CITRA ENDOSKOPI BERBASIS WEB*  
**Primary Model:** U-Net + ResNet50  
**Primary AI Task:** Semantic segmentation of colorectal/intestinal polyps  
**XAI:** Grad-CAM  
**Document Role:** Technical functional contract between PRD, model integration, UI implementation, backend implementation, and testing.

---

## 1. Document Purpose

Dokumen ini menerjemahkan kebutuhan yang telah dikunci pada `PRD_PIXEL-T_FINAL.md` menjadi spesifikasi perilaku sistem yang dapat diimplementasikan.

Pembagian tanggung jawab dokumen:

- **PRD** = apa yang harus dilakukan PIXEL-T dan batas produk.
- **StyleGuide** = bagaimana PIXEL-T harus terlihat dan berinteraksi secara visual.
- **Functional Specification** = bagaimana fitur PIXEL-T bekerja.
- **Model Integration Specification** = bagaimana model U-Net + ResNet50 dan Grad-CAM diintegrasikan secara teknis.
- **Task** = urutan pekerjaan implementasi.
- **Testing Specification** = cara memverifikasi implementasi.

Dokumen ini tidak boleh digunakan untuk memperluas scope produk di luar PRD.

---

# 2. Product Functional Boundary

## 2.1 Fungsi Utama

PIXEL-T harus menyediakan alur end-to-end:

```text
User
  ↓
Authentication
  ↓
Dashboard
  ↓
New Analysis
  ↓
Upload Colonoscopy Image
  ↓
Input Validation
  ↓
AI Inference
  ↓
Segmentation Mask
  ↓
Segmentation Overlay
  ↓
Grad-CAM
  ↓
Model Analysis
  ↓
Analysis Summary
  ↓
Save Result
  ↓
History
```

## 2.2 Fungsi yang Termasuk

1. Register.
2. Login.
3. Logout.
4. Dashboard.
5. Upload satu citra endoskopi.
6. Preview citra.
7. Validasi input.
8. Menjalankan model U-Net + ResNet50.
9. Menghasilkan segmentation mask.
10. Menghasilkan segmentation overlay.
11. Menghasilkan Grad-CAM heatmap.
12. Menghasilkan Grad-CAM overlay.
13. Menghasilkan informasi analisis yang benar-benar dapat dihitung dari output model.
14. Menampilkan analysis summary yang model-derived.
15. Menyimpan hasil analisis.
16. Menampilkan history milik pengguna.
17. Membuka detail hasil history.
18. Menghapus history/result sesuai implementasi yang ditetapkan.
19. Theme switch light/dark.
20. Menampilkan clinical disclaimer.

## 2.3 Fungsi yang Tidak Termasuk

Jangan implementasikan:

- cancer classification;
- malignancy prediction;
- cancer probability;
- diagnosis medis;
- treatment recommendation;
- clinical decision recommendation;
- chatbot;
- LLM-based explanation;
- model selector;
- multi-model comparison;
- model ranking;
- fabricated confidence score;
- fabricated probability;
- fabricated physical size in millimeters;
- fitur yang berasal dari LUCIT tetapi tidak tercantum dalam PRD.

---

# 3. Actors and Access

## 3.1 Primary Actor

**Dokter / tenaga medis yang menangani polip usus/kolorektal.**

PIXEL-T merupakan alat bantu analisis citra, bukan pengganti penilaian profesional tenaga medis.

## 3.2 Authentication State

### Unauthenticated

Dapat mengakses:

- landing/authentication pages;
- register;
- login.

Tidak dapat mengakses:

- dashboard;
- new analysis;
- history;
- analysis detail milik pengguna.

### Authenticated

Dapat mengakses:

- dashboard;
- new analysis;
- history;
- analysis result;
- profile/session actions;
- theme switch.

---

# 4. System Architecture

## 4.1 System Architecture Overview

PIXEL-T menggunakan arsitektur web berlapis dengan pemisahan tanggung jawab antara frontend, backend API, AI/model service, persistence, dan object storage. Pola pemisahan ini dapat dipelajari dari struktur LUCIT, tetapi implementasi PIXEL-T tetap mengikuti scope dan model yang telah dikunci pada PRD.

```text
┌──────────────────────────────────────────────────────────────┐
│                         MEDICAL USER                         │
│                  Dokter / Tenaga Medis                      │
└──────────────────────────────┬───────────────────────────────┘
                               │ HTTPS
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                     PIXEL-T FRONTEND                         │
│                                                              │
│ Auth │ Dashboard │ New Analysis │ Result │ History │ Theme   │
└──────────────────────────────┬───────────────────────────────┘
                               │ HTTP API
                               ▼
┌──────────────────────────────────────────────────────────────┐
│                      PIXEL-T BACKEND                         │
│                                                              │
│ Authentication │ Validation │ Analysis │ History │ Storage   │
│                         Service Layer                        │
└───────────────┬──────────────────────────────┬───────────────┘
                │                              │
                │ AI inference                 │ Persistence
                ▼                              ▼
┌──────────────────────────────┐   ┌───────────────────────────┐
│        AI / MODEL LAYER      │   │     DATA LAYER            │
│                              │   │                           │
│ U-Net + ResNet50             │   │ PostgreSQL / Supabase DB  │
│ Segmentation                 │   │ Object Storage            │
│ Grad-CAM                     │   │ Analysis Metadata         │
└──────────────────────────────┘   └───────────────────────────┘
```

## 4.2 Component Architecture

### Frontend

Frontend bertanggung jawab terhadap:

- authentication UI;
- dashboard;
- image selection dan preview;
- input validation feedback;
- analysis submission;
- loading, success, error, dan empty states;
- visualisasi original image;
- visualisasi segmentation mask dan overlay;
- visualisasi Grad-CAM;
- model analysis;
- analysis summary;
- history;
- theme switching.

Frontend **tidak boleh** menjalankan checkpoint model, preprocessing model, Grad-CAM computation, atau business logic inference sebagai sumber kebenaran.

### Backend API

Backend menjadi boundary utama antara frontend dan AI/data layer. Backend bertanggung jawab terhadap:

- authentication dan authorization;
- validasi file di sisi server;
- penerimaan request analysis;
- preprocessing;
- pemanggilan model;
- post-processing;
- Grad-CAM;
- perhitungan model-derived measurements;
- penyimpanan metadata;
- penyimpanan/retrieval asset;
- pembentukan response yang stabil;
- error handling.

### AI / Model Layer

AI layer hanya menggunakan model yang ditetapkan oleh `ModelIntegrationSpecification.md`. Untuk produk PIXEL-T, arsitektur utama adalah U-Net + ResNet50 dan XAI utama adalah Grad-CAM.

Detail checkpoint, preprocessing, threshold, TTA, post-processing, dan target layer **tidak didefinisikan ulang di dokumen ini**; detail tersebut merupakan kontrak model dan harus berasal dari `ModelIntegrationSpecification.md` setelah model final dikunci.

### Data Layer

Data layer terdiri atas:

- database untuk metadata pengguna dan analysis;
- object storage untuk image artifacts;
- access control berdasarkan kepemilikan analysis.

PRD/project materials menetapkan Supabase/PostgreSQL sebagai pendekatan persistence yang direncanakan. Detail implementasi database/storage dapat mengikuti stack tersebut tanpa memperluas scope produk.

## 4.3 Request and Data Flow

Alur normal sebuah analysis:

```text
User selects image
        ↓
Frontend preview
        ↓
Client-side validation
        ↓
POST /api/analysis
        ↓
Backend authentication check
        ↓
Server-side file validation
        ↓
Decode image
        ↓
Preserve original
        ↓
Model preprocessing
        ↓
U-Net + ResNet50 inference
        ↓
Segmentation output
        ├──────────────→ Threshold / post-processing
        │                         ↓
        │                    Binary Mask
        │                         ↓
        │                 Segmentation Overlay
        │                         ↓
        │                 Model Measurements
        │
        └──────────────→ Grad-CAM computation
                                  ↓
                           Heatmap + Overlay
        ↓
Analysis Summary
        ↓
Persist metadata + assets
        ↓
API response
        ↓
Frontend Result Page
```

## 4.4 AI Inference Architecture

AI inference harus diperlakukan sebagai satu pipeline yang konsisten. Frontend tidak boleh menghitung ulang output model dengan aturan yang berbeda.

```text
                 UPLOADED IMAGE
                       │
                       ▼
              Secure Validation
                       │
                       ▼
                 Image Decode
                       │
             ┌─────────┴─────────┐
             │ Preserve Original │
             └─────────┬─────────┘
                       │
                       ▼
                Preprocessing
                       │
                       ▼
              U-Net + ResNet50
                       │
             ┌─────────┴──────────┐
             │                    │
             ▼                    ▼
       Segmentation           Grad-CAM
       probability/logit      objective
             │                    │
             ▼                    ▼
       Threshold +           Gradients +
       Post-processing        Activations
             │                    │
             ▼                    ▼
        Binary Mask         Heatmap / Overlay
             │
             ▼
     Segmentation Overlay
             │
             ▼
     Model-derived Metrics
```

The exact numerical and model-specific rules belong to `ModelIntegrationSpecification.md`.

## 4.5 Deployment / Environment Architecture

PIXEL-T harus dapat dijalankan dengan konfigurasi yang berbeda untuk development dan production tanpa mengubah source code untuk nilai rahasia atau deployment-specific values.

```text
                    ┌─────────────────────┐
                    │ Environment Config  │
                    │ .env / deployment   │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
       ┌────────────┐   ┌────────────┐   ┌──────────────┐
       │ Frontend   │   │ Backend API│   │ AI Runtime  │
       │ Web App    │──▶│            │──▶│ Model        │
       └────────────┘   └─────┬──────┘   └──────────────┘
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
              ┌───────────┐      ┌──────────────┐
              │ Database  │      │ Object       │
              │ Supabase  │      │ Storage      │
              └───────────┘      └──────────────┘
```

## 4.6 Environment & Configuration Specification

### 4.6.1 Configuration Principles

1. Environment-specific values tidak boleh di-hard-code di source code.
2. Secret/key tidak boleh dikirim ke frontend kecuali memang secara desain merupakan public client configuration.
3. Model configuration harus mempunyai satu sumber kebenaran di backend/model runtime.
4. Frontend tidak boleh menentukan checkpoint, threshold, TTA, atau target layer model.
5. Nilai yang belum dikunci diberi status `[FINALIZE]` atau `[TBD]`, bukan ditebak oleh coding agent.
6. Production configuration harus dapat diaudit terhadap model artifact yang benar-benar digunakan.

### 4.6.2 Configuration Categories

```text
Environment
├── Application
│   ├── APP_ENV
│   ├── Backend host/port
│   └── Frontend API base URL
│
├── Authentication / Security
│   ├── Auth configuration
│   ├── Server-side secret
│   ├── CORS allowed origins
│   └── Session/token configuration
│
├── Database / Storage
│   ├── Supabase URL
│   ├── Supabase public client configuration
│   ├── Server-side service credential
│   └── Storage bucket/path configuration
│
└── AI / Model
    ├── MODEL_PATH / artifact reference
    ├── MODEL_VERSION
    ├── MODEL_CONFIG_VERSION
    ├── MODEL_DEVICE
    ├── MODEL_INPUT_SIZE [FINALIZE]
    ├── MODEL_THRESHOLD [FINALIZE]
    ├── TTA_ENABLED [FINALIZE]
    ├── POSTPROCESSING_ENABLED [FINALIZE]
    └── GRADCAM_TARGET_LAYER [FINALIZE]
```

### 4.6.3 Canonical Environment Variable Set

Nama berikut merupakan **logical configuration contract**. Nilai aktual harus diisi pada deployment configuration dan model finalization; jangan memasukkan placeholder ke production.

```env
APP_ENV=development
BACKEND_HOST=0.0.0.0
BACKEND_PORT=[TBD]
FRONTEND_API_BASE_URL=[TBD]

SUPABASE_URL=[TBD]
SUPABASE_ANON_KEY=[TBD]
SUPABASE_SERVICE_ROLE_KEY=[SECRET]

SECRET_KEY=[SECRET]
CORS_ALLOWED_ORIGINS=[TBD]

MODEL_PATH=[TBD]
MODEL_VERSION=[FINALIZE]
MODEL_CONFIG_VERSION=[FINALIZE]
MODEL_DEVICE=auto
MODEL_INPUT_SIZE=[FINALIZE]
MODEL_THRESHOLD=[FINALIZE]
TTA_ENABLED=[FINALIZE]
POSTPROCESSING_ENABLED=[FINALIZE]
GRADCAM_TARGET_LAYER=[FINALIZE]
```

`SUPABASE_SERVICE_ROLE_KEY`, `SECRET_KEY`, dan secret lain yang setara **hanya boleh berada di server-side environment/secret manager** dan tidak boleh masuk bundle frontend atau repository publik.

### 4.6.4 Configuration Ownership

| Configuration | Owner | Used By | Source of Truth |
|---|---|---|---|
| API base URL | Deployment | Frontend | Environment |
| Auth/session configuration | Backend | Backend | Environment + auth provider configuration |
| Database/storage configuration | Backend | Backend | Environment |
| Model artifact | AI runtime | Backend/AI service | Model integration contract |
| Model version | AI runtime | Backend + persistence | Final model contract |
| Input size | AI runtime | Preprocessing/model | Model integration contract |
| Threshold | AI runtime | Segmentation | Model integration contract |
| TTA | AI runtime | Inference | Model integration contract |
| Post-processing | AI runtime | Segmentation | Model integration contract |
| Grad-CAM target layer | AI runtime | XAI service | Model integration contract |

### 4.6.5 Development vs Production

Development dan production harus menggunakan struktur configuration yang sama tetapi nilai dapat berbeda.

Development boleh menggunakan:

- local frontend URL;
- local backend URL;
- development database/storage;
- development model artifact yang telah ditentukan;
- debug logging yang tidak membocorkan secret atau medical image data.

Production harus menggunakan:

- HTTPS;
- production database/storage;
- production secret management;
- production model artifact yang telah diverifikasi;
- restrictive CORS;
- non-debug error responses;
- controlled logging.

### 4.6.6 Configuration Validation at Startup

Backend harus memvalidasi konfigurasi kritis sebelum menerima request analysis. Minimal:

```text
Start application
      ↓
Load environment configuration
      ↓
Validate required variables
      ↓
Validate model artifact reference
      ↓
Validate model/config compatibility
      ↓
Initialize database/storage clients
      ↓
Load model
      ↓
Run readiness checks
      ↓
Accept analysis requests
```

Jika konfigurasi kritis tidak valid, aplikasi harus menghasilkan startup/readiness failure yang jelas pada server log dan **tidak boleh diam-diam menggunakan default yang tidak diketahui**.

### 4.6.7 Configuration Change Rule

Perubahan berikut dianggap perubahan teknis yang harus direview terhadap `ModelIntegrationSpecification.md`:

- checkpoint/model artifact;
- model version;
- input size;
- preprocessing;
- threshold;
- TTA;
- post-processing;
- Grad-CAM target layer;
- definisi probability/confidence.

Perubahan tersebut tidak boleh dilakukan hanya dari frontend configuration.

## 4.7 Architecture Boundaries

| Layer | Boleh | Tidak Boleh |
|---|---|---|
| Frontend | UI, upload, state, visualization | Model inference, secret handling |
| Backend API | Auth, validation, orchestration, response | Menambah fitur di luar PRD |
| AI Service | Inference, segmentation, Grad-CAM | Diagnosis/treatment recommendation |
| Database | Metadata, ownership, status | Menyimpan secret sebagai plaintext |
| Object Storage | Image artifacts | Uncontrolled public medical-image access |

## 4.8 Architecture Principle

Frontend tidak boleh menjalankan model AI secara langsung.

Backend bertanggung jawab terhadap:

- validation;
- preprocessing;
- model loading;
- inference;
- post-processing;
- Grad-CAM;
- calculation of model-derived measurements;
- persistence;
- response formatting.

Frontend bertanggung jawab terhadap:

- input;
- upload;
- loading state;
- result visualization;
- history visualization;
- user interaction.

# 5. Authentication

## 5.1 Register

### Input

- full name;
- email;
- password;
- confirmation password jika digunakan oleh implementasi.

### Validation

- required fields tidak kosong;
- email memiliki format valid;
- password memenuhi minimum policy;
- password confirmation cocok jika field digunakan;
- email belum terdaftar.

### Success

Account dibuat dan user dapat login.

### Error

Frontend menampilkan pesan yang jelas tanpa membocorkan detail internal database.

---

## 5.2 Login

### Input

- email;
- password.

### Success

Server membuat/menetapkan authenticated session/token sesuai mekanisme implementasi.

Frontend mengarahkan user ke Dashboard.

### Failure

Tampilkan pesan autentikasi gagal secara umum.

Jangan membocorkan apakah email tertentu terdaftar jika security policy yang dipilih mengharuskan generic authentication error.

---

## 5.3 Logout

1. User menekan logout.
2. Sistem dapat menampilkan confirmation.
3. Session/token dihapus atau diinvalidasi sesuai mekanisme.
4. User diarahkan ke authentication page.

---

# 6. Dashboard

Dashboard adalah entry point aplikasi, bukan dashboard analytics administratif.

## 6.1 Required Content

- greeting/context;
- primary CTA `New Analysis`;
- recent analyses;
- link ke `History`;
- user/session access;
- theme switch.

## 6.2 Recent Analysis

Jika tersedia:

- thumbnail;
- tanggal/waktu;
- status;
- metadata singkat;
- action untuk membuka hasil.

Jika belum tersedia:

- empty state;
- CTA `New Analysis`.

---

# 7. New Analysis

## 7.1 Flow

```text
Open New Analysis
      ↓
Select Image
      ↓
Preview
      ↓
Validate
      ↓
Analyze
      ↓
Processing
      ↓
Result
```

## 7.2 Upload Requirements

Sistem harus menerima satu citra untuk satu analisis.

Input harus:

- merupakan file gambar;
- dapat dibaca oleh backend;
- memiliki format yang didukung;
- tidak melebihi size limit yang ditetapkan konfigurasi;
- tidak corrupt.

Format dan size limit harus berada di environment/configuration, bukan hard-coded pada frontend saja.

## 7.3 Preview

Setelah file dipilih:

- tampilkan preview;
- tampilkan nama file;
- tampilkan informasi dasar bila tersedia;
- berikan `Replace`/`Remove`;
- tombol `Analyze` aktif hanya jika validation berhasil.

## 7.4 Input Validation

Validation minimal:

1. file exists;
2. MIME/content dapat diverifikasi;
3. image decoder berhasil membuka file;
4. dimensi valid;
5. file size valid;
6. file tidak corrupt.

Validation tidak boleh menggunakan LLM.

Jika input tidak valid:

```text
Status: Invalid Input
Action: pilih citra lain
```

---

# 8. Analysis Processing

## 8.1 Processing Stages

Backend menjalankan pipeline:

```text
Receive File
   ↓
Secure Validation
   ↓
Decode Image
   ↓
Preserve Original
   ↓
Preprocess
   ↓
U-Net + ResNet50 Inference
   ↓
Probability / Logit Output
   ↓
Threshold
   ↓
Post-processing
   ↓
Binary Mask
   ↓
Segmentation Overlay
   ↓
Model-derived Measurements
   ↓
Grad-CAM
   ↓
Grad-CAM Heatmap
   ↓
Grad-CAM Overlay
   ↓
Analysis Summary
   ↓
Persist Result
   ↓
Return Response
```

Detail model harus mengikuti `ModelIntegrationSpecification.md`.

---

# 9. Image Integrity

## 9.1 Original Image

Original Image harus:

- mempertahankan visual asli;
- tidak diberi artificial color grading;
- tidak diberi heatmap;
- tidak diberi segmentation mask;
- tidak dipotong secara misleading;
- tidak di-stretch secara misleading.

Jika preprocessing memerlukan resize, resize hanya digunakan untuk inference dan tidak menggantikan original image yang ditampilkan.

## 9.2 Internal Preprocessing

Preprocessing harus menggunakan konfigurasi final model.

Frontend tidak boleh melakukan preprocessing yang mengubah input model secara berbeda dari preprocessing training/inference final.

---

# 10. Segmentation

## 10.1 Output

Primary output:

- binary segmentation mask;
- segmentation overlay.

## 10.2 Binary Mask

Mask merepresentasikan output segmentasi model setelah threshold dan post-processing.

Konvensi internal harus konsisten:

- background = 0;
- polyp = 1.

Jika disimpan sebagai image, representasi visual dapat menggunakan background hitam dan foreground putih atau skema lain yang ditentukan implementasi, tetapi makna pixel harus konsisten.

## 10.3 Segmentation Overlay

Overlay menggabungkan:

- original image;
- binary mask.

Overlay harus:

- mempertahankan konteks citra asli;
- membuat area segmentasi mudah terlihat;
- tidak menyerupai Grad-CAM;
- menggunakan visual convention yang konsisten.

## 10.4 Empty Segmentation

Jika model menghasilkan mask kosong:

- sistem tetap mengembalikan hasil valid;
- area = 0;
- area ratio = 0 jika denominator valid;
- bounding box tidak tersedia;
- UI tidak boleh mengubah kondisi tersebut menjadi `confirmed no polyp` atau diagnosis.

Gunakan status model-derived terstandarisasi:

`not_detected` (dengan UI label non-diagnostik seperti "Not Detected" atau "Area Tidak Terdeteksi")

bukan klaim diagnosis klinis seperti:

`No polyp confirmed`.

---

# 11. Model Analysis

Model Analysis hanya boleh berisi informasi yang dapat dihitung secara valid dari output model dan pipeline.

## 11.1 Candidate Metrics

Jika dapat dihitung:

- segmentation status;
- segmented pixel area;
- area ratio;
- bounding box width;
- bounding box height;
- model version;
- processing time jika sistem memang mengukurnya.

## 11.2 Physical Size

Jangan menampilkan ukuran dalam mm/cm kecuali terdapat physical scale/calibration yang valid.

Pixel area boleh ditampilkan sebagai `px` atau istilah setara.

## 11.3 Confidence / Probability

Confidence/probability bersifat **optional**.

Untuk semantic segmentation, sistem tidak boleh menampilkan nilai confidence hanya karena tersedia nilai sigmoid/probability pada pixel output.

Jika definisi confidence belum ditetapkan secara ilmiah dan konsisten pada final pipeline:

- jangan tampilkan confidence;
- jangan mengubah Dice/IoU menjadi confidence;
- jangan menggunakan max probability secara otomatis sebagai confidence.

---

# 12. Explainable AI

## 12.1 Method

PIXEL-T menggunakan **Grad-CAM** sebagai visual explainability.

Grad-CAM harus berasal dari model yang benar-benar digunakan untuk inference.

Tidak boleh menggunakan:

- LLM;
- teks generatif;
- aturan eksternal yang mengklaim sebagai alasan model;
- Grad-CAM dari model lain.

## 12.2 Outputs

Required:

1. Grad-CAM Heatmap.
2. Grad-CAM Overlay.

## 12.3 Heatmap

Heatmap menunjukkan distribusi aktivasi/relevansi pada feature representation target layer yang dipilih.

Visualisasi harus:

- mempertahankan ukuran/spatial alignment dengan original;
- dibedakan secara jelas dari segmentation mask;
- diberi label `Grad-CAM Heatmap`.

## 12.4 Overlay

Overlay:

```text
Original Image + Grad-CAM Heatmap
```

Harus mempertahankan konteks citra asli.

## 12.5 Text Explanation

Jika terdapat text explanation, text tersebut harus dibuat dari output model dengan template/rules deterministik.

Contoh bentuk:

> `Grad-CAM menunjukkan area dengan aktivasi model yang lebih tinggi pada bagian citra tertentu. Visualisasi ini merupakan interpretasi model dan bukan diagnosis medis.`

Jangan membuat klaim anatomi atau diagnosis yang tidak dapat didukung output.

---

# 13. Analysis Summary

Analysis Summary bukan diagnostic report.

Summary harus:

- singkat;
- model-derived;
- non-diagnostic;
- menjelaskan bahwa sistem menghasilkan segmentasi dan visualisasi XAI;
- menyebut keterbatasan jika output tertentu tidak tersedia.

Contoh struktur:

```text
AI Analysis Summary

Segmentation:
[model-derived status]

Segmented Region:
[area / ratio if available]

Explainability:
Grad-CAM visualization is available to show model activation.

Note:
Results are AI model outputs intended to support medical personnel
and are not a medical diagnosis or replacement for professional judgment.
```

Tidak boleh:

- menyimpulkan kanker;
- menyatakan malignancy;
- memberikan terapi;
- menyarankan tindakan klinis;
- menyatakan diagnosis final.

---

# 14. Result Page

## 14.1 Priority Order

Urutan informasi:

1. Original Image.
2. Segmentation Overlay.
3. Binary Mask.
4. Grad-CAM Heatmap.
5. Grad-CAM Overlay.
6. Model Analysis.
7. XAI explanation.
8. Analysis Summary.
9. Clinical disclaimer.

## 14.2 Image Cards

Setiap image card minimal memiliki:

- title;
- image;
- optional short description;
- optional metadata.

## 14.3 Image Viewer

Jika image viewer diterapkan:

- zoom;
- pan;
- reset;
- fit-to-view.

Viewer tidak boleh mengubah underlying analysis result.

---

# 15. Save Analysis

## 15.1 Save Timing

Result dapat disimpan setelah inference dan semua required outputs berhasil dibuat.

## 15.2 Stored Data

Minimal logical record:

- analysis ID;
- user ID;
- created timestamp;
- original image reference;
- binary mask reference;
- segmentation overlay reference;
- Grad-CAM heatmap reference;
- Grad-CAM overlay reference;
- model version;
- model configuration identifier;
- derived analysis metadata;
- processing status;
- error information jika gagal.

## 15.3 Atomicity

Jika required output gagal dibuat, sistem tidak boleh menyimpan record sebagai `Completed`.

Status harus menunjukkan failure/partial failure sesuai implementasi.

---

# 16. History

## 16.1 List

History menampilkan analisis milik authenticated user.

Item dapat berisi:

- thumbnail;
- date/time;
- status;
- short segmentation metadata;
- open/view action;
- delete action jika enabled.

## 16.2 Ownership

User hanya boleh melihat/mengakses result yang dimilikinya.

Backend harus melakukan authorization, bukan hanya frontend filtering.

## 16.3 Detail

History detail mempertahankan visual hierarchy result page.

## 16.4 Delete

Jika delete diaktifkan:

1. user memilih delete;
2. confirmation dialog;
3. backend memverifikasi ownership;
4. database record dihapus;
5. associated stored artifacts dihapus sesuai storage policy;
6. frontend refreshes history.

---

# 17. API Contract

Endpoint names menggunakan prefix `/api` dan kontrak komunikasi resmi berikut wajib dipenuhi.

## 17.1 Authentication

```text
POST /api/auth/register
POST /api/auth/login
POST /api/auth/logout
GET  /api/auth/me
```

Autentikasi menggunakan Supabase Auth. Untuk endpoint yang membutuhkan autentikasi, frontend mengirimkan header HTTP:

```http
Authorization: Bearer <supabase_access_token>
```

Alur verifikasi dan otorisasi:

```text
Frontend
    ↓
mengirim Supabase access token (header Authorization: Bearer <supabase_access_token>)
    ↓
Flask menerima Authorization header
    ↓
Flask melakukan verifikasi token melalui middleware/decorator authentication
    ↓
Flask menentukan authenticated user
    ↓
authorization/ownership check (request.user.id == analysis.user_id)
    ↓
request diproses
```

## 17.2 Analysis

```text
POST /api/analysis
GET  /api/analysis/{analysis_id}
```

`POST /api/analysis` menerima multipart image upload (`image: <image file>`).

## 17.3 History

```text
GET    /api/history
DELETE /api/history/{analysis_id}
```

Filtering/search dapat ditambahkan jika memang dibutuhkan, tetapi bukan alasan untuk memperluas product scope.

---

# 18. Analysis API Request

Logical request:

```text
multipart/form-data

image: <image file>
```

Tidak diperlukan:

- model selector;
- diagnosis type;
- cancer type;
- LLM prompt;
- explanation prompt.

Model version/configuration ditentukan oleh backend deployment configuration.

---

# 19. Analysis API Success Response

Logical structure selaras dengan `APIContract.md`:

```json
{
  "success": true,
  "data": {
    "analysis": {
      "id": "analysis-id",
      "status": "completed",
      "created_at": "2026-01-01T00:00:00Z"
    },
    "input": {
      "original_image_url": "..."
    },
    "segmentation": {
      "binary_mask_url": "...",
      "overlay_url": "..."
    },
    "gradcam": {
      "heatmap_url": "...",
      "overlay_url": "..."
    },
    "model_analysis": {
      "segmentation_status": "detected",
      "area_pixels": 12345,
      "area_ratio": 0.123,
      "bounding_width_pixels": 150,
      "bounding_height_pixels": 120
    },
    "model": {
      "architecture": "U-Net + ResNet50",
      "version": "MODEL_VERSION"
    },
    "summary": {
      "text": "Model menghasilkan area segmentasi pada citra yang dianalisis."
    }
  }
}
```

Catatan:
- `segmentation_status` menggunakan enum terstandarisasi: `"detected"` | `"not_detected"`.
- Fields yang tidak memiliki nilai valid dihilangkan atau direpresentasikan sebagai unavailable sesuai kontrak frontend tanpa membuat nilai palsu.

---

# 20. Error Contract

Standard logical statuses:

| Condition | HTTP concept | UI |
|---|---:|---|
| Invalid input | 400 | Invalid image/input |
| Unauthorized | 401 | Please sign in |
| Forbidden | 403 | Access denied |
| Not found | 404 | Result not found |
| Processing failure | 422/500 | Analysis failed |
| Server failure | 500 | Temporary processing error |

Error response standard structure:

```json
{
  "success": false,
  "error": {
    "code": "ANALYSIS_FAILED",
    "message": "Analysis could not be completed."
  }
}
```

Technical stack traces must not be returned to end users.

---

# 21. Persistence

## 21.1 Database

The thesis/project materials specify Supabase/PostgreSQL as the intended persistence approach. Untuk MVP, `DataModelSpecification.md` menjadi sumber kebenaran definitif untuk skema database.

Logical entities:

### users

Handled through Supabase Auth (metadata profile tersinkronisasi jika diperlukan).

### analyses

Merupakan satu-satunya tabel utama untuk MVP. Seluruh asset paths disimpan langsung sebagai kolom pada tabel `analyses`:

```text
id (UUID, PK)
user_id (UUID, FK -> users)
status (processing | completed | failed)
created_at
completed_at

original_image_path
original_filename
original_mime_type
original_width
original_height

binary_mask_path
segmentation_overlay_path
segmentation_status (detected | not_detected)
area_pixels
area_ratio
bounding_width_pixels
bounding_height_pixels

gradcam_heatmap_path
gradcam_overlay_path
gradcam_target_layer

model_architecture
model_version
model_config_version

summary_text
error_code
error_message
```

Tabel terpisah `analysis_assets` **tidak digunakan untuk MVP** guna menjaga kesederhanaan dan kejelasan skema sesuai `DataModelSpecification.md`. Asset biner disimpan di Supabase Storage, sedangkan database hanya menyimpan metadata dan object path.

---

# 22. Storage

Image artifacts should be stored in object storage rather than embedding large binary image data directly in database records.

Storage access must be controlled so that one authenticated user cannot access another user's private analysis artifacts.

If public URLs are used, the decision must be explicit; private/signed access is preferred for medical-image data.

---

# 23. Model Loading

The backend should load the finalized model once per worker/process rather than loading the checkpoint for every request.

Logical lifecycle:

```text
Application Start
      ↓
Load Model Artifact
      ↓
Validate Architecture/Config
      ↓
Model Ready
      ↓
Receive Requests
      ↓
Inference
```

A missing or incompatible model artifact must fail fast during deployment/startup or produce a controlled service-unavailable state.

---

# 24. Concurrency and Resource Control

The inference service must avoid uncontrolled concurrent GPU/CPU jobs.

Requirements:

- one request must not corrupt another request's inference state;
- model must be treated as shared read-only during inference unless implementation explicitly requires otherwise;
- temporary files must be isolated per analysis;
- output filenames must be collision-safe;
- memory-intensive preprocessing and Grad-CAM must be bounded.

---

# 25. Loading and Progress

Frontend states:

```text
idle
uploading
validating
processing
completed
error
```

During processing:

- show loading indicator;
- disable duplicate submit;
- provide concise status;
- do not display fake percentage progress.

Allowed:

`Analyzing image...`

`Processing segmentation and Explainable AI...`

Not allowed:

`87% complete`

unless actual measurable progress exists.

---

# 26. Security

Minimum requirements:

- authentication required for protected endpoints;
- authorization by user ownership;
- server-side input validation;
- MIME/content verification;
- file size limits;
- safe file naming;
- no execution of uploaded files;
- secure secrets through environment variables;
- no API keys in frontend source;
- no sensitive stack traces;
- protected storage access.

---

# 27. Medical Data Integrity

PIXEL-T processes medical images and therefore must preserve result integrity.

The implementation must not:

- modify original image for presentation;
- silently alter image orientation;
- apply decorative filters;
- stretch/crop in a way that changes interpretation;
- present heatmap as segmentation;
- present segmentation as diagnosis;
- fabricate metrics.

---

# 28. Clinical Boundary

The following disclaimer must be visible in the result context:

> **Hasil yang ditampilkan merupakan keluaran analisis model AI dan ditujukan sebagai informasi pendukung bagi tenaga medis. Hasil ini tidak dimaksudkan sebagai diagnosis medis atau pengganti penilaian profesional tenaga medis.**

Terminology:

### Preferred

- AI Analysis
- Segmentation Result
- Segmentation Mask
- Segmentation Overlay
- Grad-CAM
- Model Analysis
- Model Output
- Analysis Summary
- Segmentation Status (detected / not_detected)
- Segmented Area

### Avoid

- Diagnosis
- Confirmed Polyp
- Cancer Detected
- Malignancy Probability
- Treatment Recommendation
- Clinical Decision

---

# 29. LUCIT Adaptation Boundary

LUCIT digunakan sebagai **reference-level product**, bukan sebagai source of truth.

## 29.1 Patterns That May Be Adapted

Dari LUCIT, pola berikut dapat digunakan:

- frontend/backend separation;
- page-based frontend structure;
- authentication flow;
- analysis page pattern;
- history page pattern;
- service layer;
- controller layer;
- repository/persistence separation;
- image upload → preprocessing → inference → visualization pipeline;
- binary mask generation;
- overlay generation;
- Grad-CAM visualization pattern;
- loading/error/empty states.

LUCIT mendokumentasikan alur sign-up/sign-in, analysis, segmentation, dan history yang berguna sebagai referensi struktur interaksi.

## 29.2 What Must Not Be Adapted

Jangan membawa:

- cancer classification;
- lung/colon tissue classification;
- malignancy workflow;
- Gemini/LLM;
- chatbot;
- treatment recommendation;
- LUCIT branding;
- LUCIT color system;
- model selector;
- multi-model analysis;
- LUCIT terminology.

LUCIT memang menggunakan classification, segmentation, Grad-CAM, dan LLM dalam satu sistem; PIXEL-T secara sengaja menyederhanakan arsitektur produk menjadi segmentasi polip + Grad-CAM tanpa LLM.

---

# 30. Frontend Component Responsibilities

Suggested shared components:

```text
Button
Input
FileUpload
ImagePreview
Card
Badge
Modal
Toast
Navigation
ThemeSwitcher
ImageViewer
ResultCard
AnalysisImageCard
LoadingState
ErrorState
EmptyState
Disclaimer
```

Component tidak boleh mengandung business logic AI.

---

# 31. Backend Service Responsibilities

Suggested logical services:

```text
AuthService
ImageValidationService
ImagePreprocessingService
SegmentationService
GradCAMService
AnalysisMetricsService
AnalysisPersistenceService
HistoryService
StorageService
```

## 31.1 SegmentationService

Bertanggung jawab terhadap:

- model inference;
- threshold;
- post-processing;
- binary mask.

## 31.2 GradCAMService

Bertanggung jawab terhadap:

- target layer;
- forward pass;
- gradient capture;
- activation capture;
- Grad-CAM computation;
- heatmap generation;
- overlay.

Detailnya berada pada `ModelIntegrationSpecification.md`.

## 31.3 AnalysisMetricsService

Menghitung hanya metrics yang valid dari mask:

- pixel area;
- area ratio;
- bounding box.

Tidak mengubah research metrics menjadi per-image confidence.

---

# 32. State Machine

## 32.1 Analysis

```text
CREATED
  ↓
VALIDATING
  ↓
PROCESSING
  ↓
COMPLETED
```

Failure:

```text
CREATED → FAILED
VALIDATING → FAILED
PROCESSING → FAILED
```

## 32.2 UI

```text
EMPTY
 ↓
IMAGE_SELECTED
 ↓
VALID
 ↓
PROCESSING
 ↓
RESULT
```

Invalid input:

```text
IMAGE_SELECTED → INVALID
```

---

# 33. Idempotency and Duplicate Submission

Frontend must prevent accidental duplicate submissions by disabling the analyze action during processing.

Backend should generate a unique `analysis_id` for every accepted analysis.

If retry mechanisms are implemented, they must not accidentally create multiple completed records for one logical retry without explicit policy.

---

# 34. Model Versioning

Every completed result must identify the deployed model version.

At minimum:

```text
model_name
encoder
model_version
model_config_id
```

The model version must correspond to the actual artifact used during inference.

Do not hard-code a thesis experiment result as the web model version.

---

# 35. Final Model Contract Dependency

The functional implementation cannot finalize the following values until the final trained model is selected:

- checkpoint path/artifact;
- exact architecture implementation;
- input size;
- preprocessing normalization;
- output activation;
- threshold;
- post-processing;
- TTA configuration, if any;
- Grad-CAM target layer;
- confidence/probability definition, if exposed.

These values are governed by `ModelIntegrationSpecification.md`.

---

# 36. Non-Functional Requirements

## 36.1 Usability

- clear primary action;
- no unnecessary steps;
- readable result hierarchy;
- medical image remains dominant.

## 36.2 Responsiveness

Desktop:

- two-column result layout where readable.

Mobile:

- stacked result layout.

Required mobile order:

```text
Original
↓
Segmentation Overlay
↓
Binary Mask
↓
Grad-CAM Heatmap
↓
Grad-CAM Overlay
↓
Model Analysis
↓
XAI
↓
Summary
```

## 36.3 Accessibility

- keyboard-accessible controls;
- visible focus;
- semantic labels;
- alt text;
- status not represented only by color;
- sufficient contrast.

## 36.4 Theme

Light and dark themes must both support:

- image readability;
- mask readability;
- Grad-CAM readability;
- sufficient text contrast;
- consistent component behavior.

---

# 37. Functional Acceptance Criteria

## Authentication

- [ ] User can register.
- [ ] User can login.
- [ ] Protected routes reject unauthenticated requests.
- [ ] User can logout.

## Upload

- [ ] Valid image can be selected.
- [ ] Preview is shown.
- [ ] Invalid file is rejected.
- [ ] Analyze is disabled while invalid.

## AI

- [ ] Backend loads final U-Net + ResNet50 artifact.
- [ ] Inference uses final preprocessing.
- [ ] Binary mask is generated.
- [ ] Segmentation overlay is generated.
- [ ] Grad-CAM heatmap is generated.
- [ ] Grad-CAM overlay is generated.
- [ ] Model-derived measurements are correct.

## Result

- [ ] Original image is preserved.
- [ ] All required outputs are labeled.
- [ ] No fake confidence is shown.
- [ ] No diagnosis is presented.
- [ ] Disclaimer is visible.

## History

- [ ] Completed analysis can be saved.
- [ ] User can see own history.
- [ ] User cannot access another user's result.
- [ ] Detail page reproduces the result.
- [ ] Delete works if enabled.

---

# 38. Implementation Guardrails for AI Coding Agent

The coding agent MUST:

1. Read `PRD_PIXEL-T_FINAL.md`.
2. Read `StyleGuide.md`.
3. Read this document.
4. Read `ModelIntegrationSpecification.md`.
5. Treat model finalization values as authoritative only after they are marked FINAL.
6. Never add LUCIT features merely because they exist in the reference.
7. Never add an LLM.
8. Never add cancer classification.
9. Never add treatment recommendations.
10. Never invent confidence values.
11. Never invent physical measurements.
12. Never expose research metrics as per-image confidence.
13. Keep AI logic on backend.
14. Preserve original image integrity.
15. Keep model version tied to the actual artifact.
16. Keep frontend terminology within the approved vocabulary.
17. Fail safely when optional outputs are unavailable.
18. Never silently replace the final model with another architecture.

---

# 39. Final Functional Statement

PIXEL-T is a web-based medical-image analysis system in which an authenticated medical user uploads a colonoscopy/endoscopic image, the backend processes it using the finalized U-Net + ResNet50 segmentation model, and the system presents the original image, segmentation mask, segmentation overlay, Grad-CAM heatmap, Grad-CAM overlay, valid model-derived measurements, and a concise non-diagnostic analysis summary. Results can be persisted and revisited through history.

The system supports medical personnel; it does not replace professional diagnosis or clinical judgment.

**Status: FINAL / LOCKED**
