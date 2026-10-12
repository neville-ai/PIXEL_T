# APIContract.md

# PIXEL-T — API Contract Specification

**Status:** FINAL / LOCKED  
**Product:** PIXEL-T  
**Purpose:** Kontrak komunikasi resmi antara Frontend PIXEL-T dan Backend PIXEL-T.

---

## 1. Document Status

Dokumen ini merupakan kontrak API final untuk implementasi aplikasi web PIXEL-T.

API Contract diturunkan dari:

1. `PRD_PIXEL-T_FINAL.md`
2. `FunctionalSpecification.md`
3. `ModelIntegrationSpecification.md`

`StyleGuide.md` tidak menjadi sumber struktur API karena Style Guide mengatur presentasi/UI, bukan perilaku backend.

LUCIT digunakan hanya sebagai referensi pola arsitektur/interaksi. Endpoint, payload, istilah, dan fitur PIXEL-T ditentukan oleh spesifikasi PIXEL-T sendiri.

---

# 2. API Principles

API PIXEL-T harus:

- menggunakan HTTP API;
- menggunakan JSON untuk request/response metadata;
- menggunakan `multipart/form-data` untuk upload file;
- menggunakan authentication untuk resource milik pengguna;
- tidak mengekspos secret key atau service-role credential ke frontend;
- mengembalikan error dengan format konsisten;
- tidak mengklaim diagnosis medis;
- tidak menghasilkan confidence/probability yang tidak didukung pipeline model;
- tidak menambahkan fitur classification, malignancy, cancer prediction, treatment recommendation, chatbot, atau model selector;
- mengembalikan output model yang benar-benar dihasilkan pipeline inference.

---

# 3. API Base Structure

Logical base path:

```text
/api
```

Resource utama:

```text
/api/auth
/api/analysis
/api/history
```

Authentication menggunakan **Supabase Auth**. Pada endpoint privat, Frontend mengirimkan token pada header HTTP:

```http
Authorization: Bearer <supabase_access_token>
```

Backend Flask memverifikasi token tersebut melalui middleware/decorator autentikasi sebelum memproses request:

```text
Frontend
    ↓
mengirim Supabase access token (header Authorization: Bearer <supabase_access_token>)
    ↓
Flask menerima Authorization header
    ↓
Flask melakukan verifikasi token
    ↓
Flask menentukan authenticated user
    ↓
authorization/ownership check (request.user.id == analysis.user_id)
    ↓
request diproses
```

---

# 4. Authentication

## 4.1 Register

### Endpoint

```http
POST /api/auth/register
```

### Request

```json
{
  "full_name": "Doctor Name",
  "email": "doctor@example.com",
  "password": "********"
}
```

### Required

| Field | Type | Required |
|---|---|---|
| `full_name` | string | yes |
| `email` | string | yes |
| `password` | string | yes |

### Success

```http
201 Created
```

```json
{
  "success": true,
  "message": "Registration successful"
}
```

### Errors

- `400` invalid input
- `409` email already registered
- `500` server error

Password tidak pernah dikembalikan dalam response.

---

# 5. Sign In

### Endpoint

```http
POST /api/auth/login
```

### Request

```json
{
  "email": "doctor@example.com",
  "password": "********"
}
```

### Success

```http
200 OK
```

```json
{
  "success": true,
  "message": "Login successful"
}
```

Authentication token/session dikelola oleh authentication layer yang digunakan aplikasi.

### Errors

- `400` invalid input
- `401` authentication failed
- `500` server error

---

# 6. Current User

### Endpoint

```http
GET /api/auth/me
```

### Authentication

Required (`Authorization: Bearer <supabase_access_token>`).

### Success

```http
200 OK
```

```json
{
  "success": true,
  "data": {
    "id": "user-id",
    "full_name": "Doctor Name",
    "email": "doctor@example.com"
  }
}
```

Jangan mengembalikan password atau credential sensitif.

---

# 7. Logout

### Endpoint

```http
POST /api/auth/logout
```

### Authentication

Required (`Authorization: Bearer <supabase_access_token>`).

### Success

```http
200 OK
```

```json
{
  "success": true,
  "message": "Logout successful"
}
```

---

# 8. Analysis Resource

Analysis adalah resource utama PIXEL-T.

Satu analysis menghubungkan:

```text
User
  ↓
Uploaded Image
  ↓
AI Inference
  ├── Segmentation
  ├── Model Analysis
  └── Grad-CAM
  ↓
Analysis Result
```

---

# 9. Create Analysis

### Endpoint

```http
POST /api/analysis
```

### Authentication

Required (`Authorization: Bearer <supabase_access_token>`).

### Content-Type

```http
multipart/form-data
```

### Form Field

```text
image=<image-file>
```

Tidak ada field `model_selector`.

PIXEL-T menggunakan model utama yang telah ditetapkan:

```text
U-Net + ResNet50
```

---

# 10. Upload Validation

Backend harus melakukan validasi sebelum inference.

Minimal:

- file tersedia;
- file benar-benar merupakan image;
- MIME type sesuai;
- file dapat didecode;
- ukuran file berada dalam batas konfigurasi;
- dimensi image valid;
- file tidak diproses jika validasi gagal.

Validasi frontend tidak menggantikan validasi backend.

### Validation Error

```http
400 Bad Request
```

Contoh:

```json
{
  "success": false,
  "error": {
    "code": "INVALID_IMAGE",
    "message": "Uploaded file is not a valid image."
  }
}
```

---

# 11. Analysis Processing

Setelah validasi berhasil:

```text
Receive Image
    ↓
Preserve Original
    ↓
Preprocess
    ↓
U-Net + ResNet50
    ↓
Segmentation Output
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
Heatmap + Overlay
    ↓
Analysis Summary
    ↓
Persist Result
```

Detail parameter model mengikuti `ModelIntegrationSpecification.md`.

Parameter yang masih ditandai `[FINALIZE]` di Model Integration Specification tidak boleh di-hardcode sebagai nilai final sebelum checkpoint/model run final dikunci.

---

# 12. Successful Analysis Response

### Status

```http
200 OK
```

atau `201 Created` apabila implementation memperlakukan analysis sebagai resource baru yang langsung tersimpan.

Implementasi harus memilih satu convention dan menggunakannya secara konsisten.

### Response

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

---

# 13. Segmentation Output Contract

Output segmentation dapat berisi:

- binary mask;
- segmentation overlay;
- model-derived measurements.

### Binary Mask

Representasi area hasil segmentasi dalam bentuk mask biner.

### Segmentation Overlay

Overlay mask terhadap citra asli.

Overlay tidak boleh mengubah citra asli yang disimpan sebagai original image.

---

# 14. Model Analysis Contract

Model analysis hanya boleh berisi informasi yang benar-benar dapat diturunkan dari output model.

Contoh field:

| Field | Type | Availability | Notes |
|---|---|---|---|
| `segmentation_status` | string | required | Enum: `"detected"`, `"not_detected"` |
| `area_pixels` | integer | conditional | Area dalam satuan pixel |
| `area_ratio` | number | conditional | Proporsi area tersegmentasi |
| `bounding_width_pixels` | integer | conditional | Lebar bounding box dalam pixel |
| `bounding_height_pixels` | integer | conditional | Tinggi bounding box dalam pixel |
| `model_version` | string | required | Versi model final |

Tidak boleh mengembalikan:

```text
cancer_probability
malignancy_probability
diagnosis
treatment_recommendation
clinical_decision
```

---

# 15. Confidence / Probability Contract

Confidence atau probability **bukan field wajib**.

Field hanya boleh ditambahkan jika final model pipeline memang mendefinisikan probability/confidence yang valid.

Jika pipeline tidak mendukung definisi tersebut:

```text
confidence
probability
```

tidak boleh dibuat-buat.

Dice, IoU, Accuracy, Precision, Recall, dan HD95 merupakan research evaluation metrics, bukan confidence per-image.

---

# 16. Grad-CAM Contract

Grad-CAM merupakan XAI utama PIXEL-T.

Response:

```json
{
  "gradcam": {
    "heatmap_url": "...",
    "overlay_url": "..."
  }
}
```

Grad-CAM harus berasal dari model yang digunakan untuk inference.

Target layer, target objective, preprocessing, dan metode normalisasi mengikuti `ModelIntegrationSpecification.md`.

Grad-CAM tidak boleh dibuat oleh LLM atau text-generation model.

---

# 17. Analysis Summary Contract

Analysis summary harus bersifat:

- model-derived;
- deterministic/template-based;
- non-diagnostic;
- ringkas.

Contoh:

```json
{
  "summary": {
    "text": "Model menghasilkan area segmentasi pada citra yang dianalisis dan visualisasi Grad-CAM menunjukkan area fokus model."
  }
}
```

Summary tidak boleh berubah menjadi diagnosis medis.

---

# 18. Get Analysis Detail

### Endpoint

```http
GET /api/analysis/{analysis_id}
```

### Authentication

Required (`Authorization: Bearer <supabase_access_token>`).

Pengguna hanya boleh mengakses analysis miliknya sendiri.

### Success

```http
200 OK
```

Response menggunakan struktur `Analysis Response` yang sama dengan endpoint create analysis.

### Errors

```text
401 UNAUTHORIZED
403 FORBIDDEN
404 ANALYSIS_NOT_FOUND
500 INTERNAL_ERROR
```

---

# 19. Analysis Status

Analysis dapat menggunakan status:

```text
processing
completed
failed
```

Optional frontend presentation statuses seperti `Ready` atau `Saved` merupakan UI concern dan tidak harus menjadi database processing state.

### Processing

```json
{
  "status": "processing"
}
```

### Completed

```json
{
  "status": "completed"
}
```

### Failed

```json
{
  "status": "failed"
}
```

---

# 20. History

## 20.1 List History

### Endpoint

```http
GET /api/history
```

### Authentication

Required (`Authorization: Bearer <supabase_access_token>`).

### Success

```http
200 OK
```

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "analysis-id",
        "created_at": "2026-01-01T00:00:00Z",
        "status": "completed",
        "thumbnail_url": "...",
        "segmentation_status": "detected"
      }
    ]
  }
}
```

History hanya menampilkan resource milik authenticated user.

---

# 21. Delete Analysis

### Endpoint

```http
DELETE /api/history/{analysis_id}
```

### Authentication

Required (`Authorization: Bearer <supabase_access_token>`).

### Success

```http
200 OK
```

```json
{
  "success": true,
  "message": "Analysis deleted successfully"
}
```

Deletion harus menjaga konsistensi database dan object storage sesuai persistence policy.

---

# 22. Error Contract

Semua API error menggunakan struktur:

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message"
  }
}
```

Optional internal detail tidak boleh mengekspos:

- secret;
- stack trace;
- filesystem path;
- database credential;
- model private path;
- internal infrastructure detail.

---

# 23. Standard HTTP Status

| Status | Meaning |
|---|---|
| `200` | Successful request |
| `201` | Resource created |
| `400` | Invalid request |
| `401` | Not authenticated |
| `403` | Not authorized |
| `404` | Resource not found |
| `409` | Resource conflict |
| `413` | Payload/file too large |
| `415` | Unsupported media type |
| `422` | Validation failed |
| `500` | Internal server error |
| `503` | AI/model service unavailable |

---

# 24. Ownership and Authorization

Setiap analysis memiliki owner.

```text
authenticated_user
       │
       └── analysis.user_id
```

Backend harus memastikan:

```text
request.user.id == analysis.user_id
```

sebelum:

- membaca analysis;
- membaca history;
- menghapus analysis;
- mengakses result resource.

Frontend tidak boleh menjadi satu-satunya lapisan authorization.

---

# 25. File and Storage Contract

Storage dapat digunakan untuk:

```text
original image
binary mask
segmentation overlay
Grad-CAM heatmap
Grad-CAM overlay
```

Database menyimpan metadata dan reference/path terhadap object storage.

File binary tidak perlu disimpan sebagai base64 di database kecuali ada alasan implementasi khusus yang telah disetujui.

---

# 26. URL Contract

URL file yang dikembalikan kepada frontend harus mengikuti access policy storage.

Untuk resource privat, gunakan mekanisme secure/private access yang sesuai.

Jangan mengekspos service-role credential.

---

# 27. API and Model Version Consistency

Setiap completed analysis harus dapat ditelusuri ke model configuration yang digunakan.

Minimal metadata:

```text
model_architecture
model_version
model_config_version
```

Parameter runtime penting mengikuti Model Integration Specification.

Tujuannya adalah menjaga reproducibility dan mencegah hasil lama menjadi ambigu ketika model diperbarui.

---

# 28. Idempotency and Duplicate Requests

Inference adalah operasi yang dapat mahal.

Backend harus menghindari penyimpanan result ganda akibat retry request yang sama apabila mekanisme idempotency diterapkan.

Jika idempotency key digunakan, format dan lifecycle harus konsisten di frontend/backend.

Implementasi tidak boleh menghasilkan dua history records secara tidak sengaja hanya karena satu request mengalami network retry.

---

# 29. Security Contract

Backend wajib:

- memvalidasi upload;
- membatasi ukuran file;
- memvalidasi MIME/type dan decode;
- mengisolasi file processing;
- menjaga credential server;
- menerapkan authorization;
- tidak mempercayai `user_id` dari request body sebagai sumber ownership;
- melakukan logging tanpa menyimpan secret;
- tidak mengembalikan internal exception detail.

---

# 30. Medical Boundary

API PIXEL-T hanya menyediakan:

```text
AI analysis
segmentation result
model-derived measurements
Grad-CAM visualization
analysis summary
```

API tidak menyediakan:

```text
medical diagnosis
cancer diagnosis
malignancy prediction
treatment recommendation
clinical decision
```

Clinical disclaimer yang ditampilkan aplikasi:

> “Hasil yang ditampilkan merupakan keluaran analisis model AI dan ditujukan sebagai informasi pendukung bagi tenaga medis. Hasil ini tidak dimaksudkan sebagai diagnosis medis atau pengganti penilaian profesional tenaga medis.”

---

# 31. API Contract Change Rules

Perubahan berikut dianggap breaking change:

- perubahan endpoint;
- perubahan authentication requirement;
- perubahan required request field;
- perubahan nama response field;
- perubahan tipe field;
- perubahan semantic output;
- perubahan ownership rule.

Perubahan harus memperbarui:

```text
APIContract.md
FunctionalSpecification.md
DataModelSpecification.md
ModelIntegrationSpecification.md
```

jika perubahan tersebut mempengaruhi dokumen terkait.

---

# 32. Final API Contract

Kontrak final PIXEL-T berpusat pada:

```text
Authentication
     ↓
Image Upload
     ↓
Analysis
     ↓
U-Net + ResNet50
     ↓
Segmentation
     ↓
Grad-CAM
     ↓
Analysis Result
     ↓
History
```

Tidak ada endpoint untuk fitur yang berada di luar product scope PIXEL-T.

**Status: FINAL / LOCKED**
