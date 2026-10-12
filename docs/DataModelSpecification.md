# DataModelSpecification.md

# PIXEL-T — Data Model Specification

**Status:** FINAL / LOCKED  
**Product:** PIXEL-T  
**Purpose:** Spesifikasi struktur data, relasi, persistence, dan storage untuk aplikasi PIXEL-T.

---

# 1. Document Status

Dokumen ini diturunkan dari:

1. `PRD_PIXEL-T_FINAL.md`
2. `FunctionalSpecification.md`
3. `ModelIntegrationSpecification.md`

`StyleGuide.md` tidak menjadi sumber struktur database.

LUCIT digunakan hanya sebagai referensi pola persistence/history yang relevan. Struktur data PIXEL-T ditentukan sendiri berdasarkan scope PIXEL-T.

---

# 2. Data Model Principles

Data model PIXEL-T harus:

- sederhana;
- memiliki ownership yang jelas;
- memisahkan metadata database dari binary object;
- mendukung history;
- menyimpan metadata model untuk reproducibility;
- tidak menyimpan informasi klinis yang tidak dibutuhkan;
- tidak menyimpan diagnosis yang tidak dihasilkan sistem;
- tidak membuat field untuk fitur yang berada di luar scope;
- dapat menelusuri sebuah result ke model configuration yang menghasilkan result tersebut.

---

# 3. Logical Data Architecture

```text
┌────────────────────┐
│       User         │
└─────────┬──────────┘
          │ 1
          │
          │ N
┌─────────▼──────────┐
│     Analysis       │
└─────────┬──────────┘
          │
          ├──────────────► Input Image Object
          │
          ├──────────────► Segmentation Objects
          │
          ├──────────────► Grad-CAM Objects
          │
          └──────────────► Model Metadata
```

Database menyimpan metadata.

Object storage menyimpan file image/result.

---

# 4. Core Entities

Entity utama:

```text
users
analyses
```

Entity metadata yang dapat berada di dalam `analyses` atau dipisahkan sesuai implementasi:

```text
model metadata
segmentation metadata
gradcam metadata
```

Untuk MVP, `DataModelSpecification.md` merupakan sumber kebenaran definitif untuk skema database. Sistem menggunakan satu tabel utama `analyses` di mana seluruh asset path (`original_image_path`, `binary_mask_path`, `segmentation_overlay_path`, `gradcam_heatmap_path`, `gradcam_overlay_path`) disimpan langsung sebagai kolom terstruktur pada tabel `analyses`. Tabel terpisah `analysis_assets` tidak digunakan pada MVP.

---

# 5. Users

## 5.1 Purpose

Menyimpan identitas application user.

Authentication credential dikelola oleh authentication system yang digunakan aplikasi.

Jika Supabase Auth digunakan, password tidak disimpan pada tabel aplikasi PIXEL-T.

---

## 5.2 Logical Fields

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | yes | Primary key / auth user identifier |
| `full_name` | string | yes | User display name |
| `email` | string | yes | User email |
| `created_at` | timestamp | yes | Creation timestamp |
| `updated_at` | timestamp | yes | Last update timestamp |

---

# 6. User Ownership

Relasi:

```text
users.id
   │
   └────< analyses.user_id
```

Satu user dapat memiliki banyak analysis.

Satu analysis hanya memiliki satu owner.

---

# 7. Analyses

## 7.1 Purpose

`analyses` adalah entity utama untuk menyimpan satu sesi analisis citra.

Satu record analysis merepresentasikan:

```text
uploaded image
+
AI inference
+
segmentation result
+
Grad-CAM result
+
model metadata
+
analysis summary
```

---

# 8. Analysis Fields

Recommended logical schema:

| Field | Type | Required | Notes |
|---|---|---:|---|
| `id` | UUID | yes | Primary key |
| `user_id` | UUID | yes | FK → users |
| `status` | enum/string | yes | processing/completed/failed |
| `original_image_path` | string | yes | Object storage reference |
| `original_filename` | string | conditional | Original uploaded filename |
| `original_mime_type` | string | conditional | Validated MIME type |
| `original_width` | integer | conditional | Original image width |
| `original_height` | integer | conditional | Original image height |
| `created_at` | timestamp | yes | Analysis creation |
| `completed_at` | timestamp | conditional | Completion time |
| `error_code` | string | conditional | Set only when failed |
| `error_message` | string | conditional | Safe user-facing error |

---

# 9. Segmentation Data

Segmentation output references should be associated with the analysis.

| Field | Type | Required | Notes |
|---|---|---:|---|
| `binary_mask_path` | string | conditional | Object storage reference |
| `segmentation_overlay_path` | string | conditional | Object storage reference |
| `segmentation_status` | string | conditional | Model-derived status enum (`"detected"`, `"not_detected"`) |
| `area_pixels` | integer | conditional | Derived from mask |
| `area_ratio` | numeric | conditional | Derived from mask |
| `bounding_width_pixels` | integer | conditional | Derived from mask |
| `bounding_height_pixels` | integer | conditional | Derived from mask |

All fields are conditional because an inference failure or unavailable measurement must not be represented with fabricated values.

---

# 10. Area and Measurement Rules

## 10.1 Area Pixels

`area_pixels` represents the number of pixels belonging to the selected segmentation mask according to the final mask-generation pipeline.

It is not a physical clinical measurement.

---

## 10.2 Area Ratio

`area_ratio` may be derived as:

```text
segmented_pixels / valid_image_pixels
```

The exact denominator must follow the final implementation.

---

## 10.3 Physical Size

The data model must not create a millimeter measurement unless a valid physical scale is available.

Therefore:

```text
area_mm2
width_mm
height_mm
```

are not part of the default PIXEL-T schema.

---

# 11. Grad-CAM Data

| Field | Type | Required | Notes |
|---|---|---:|---|
| `gradcam_heatmap_path` | string | conditional | Heatmap object reference |
| `gradcam_overlay_path` | string | conditional | Overlay object reference |
| `gradcam_target_layer` | string | conditional | Final model configuration |
| `gradcam_method` | string | conditional | Grad-CAM |
| `gradcam_config_version` | string | conditional | Configuration/version tracking |

The target layer is not an arbitrary frontend value.

It is defined by the model integration contract.

---

# 12. Model Metadata

Each completed analysis must identify the model configuration used.

| Field | Type | Required | Notes |
|---|---|---:|---|
| `model_architecture` | string | yes | `U-Net + ResNet50` |
| `model_version` | string | yes | Final model artifact version |
| `model_config_version` | string | yes | Runtime configuration version |
| `model_input_size` | integer | conditional | Finalized model input size |
| `model_threshold` | numeric | conditional | Final segmentation threshold |
| `tta_enabled` | boolean | conditional | Whether final runtime uses TTA |
| `postprocessing_enabled` | boolean | conditional | Whether final post-processing is enabled |

These values must reflect the actual inference configuration, not values guessed by the UI.

---

# 13. Finalization Boundary

The following values remain implementation/model-finalization dependent until the final model run is locked:

```text
checkpoint/artifact
input size
preprocessing
threshold
TTA
post-processing
Grad-CAM target layer
model version
model configuration version
```

The database schema may reserve fields for them, but must not hardcode experimental values as final product truth.

---

# 14. Confidence / Probability

No mandatory confidence field is defined.

If the final model pipeline establishes a valid probability/confidence definition, a field may be added:

```text
confidence
```

or equivalent explicitly defined field.

Until then, do not create a misleading confidence value.

The following are research metrics and must not be stored as per-image confidence:

```text
Dice
IoU
Accuracy
Precision
Recall
HD95
```

---

# 15. Research Metrics Boundary

Research evaluation results belong to the model evaluation/training workflow.

They are not required in the production `analyses` record.

If future implementation requires storing evaluation experiments, that should be a separate research/evaluation data model rather than mixing training metrics with user analysis history.

---

# 16. Analysis Summary

A completed analysis may contain a deterministic model-derived summary.

Logical field:

| Field | Type | Required |
|---|---|---:|
| `summary_text` | text | conditional |

The summary must not represent:

```text
medical diagnosis
cancer diagnosis
malignancy probability
treatment recommendation
clinical decision
```

---

# 17. Storage Model

Binary objects should be stored in object storage.

Recommended logical organization:

```text
analysis/
  {user_id}/
    {analysis_id}/
      original/
      segmentation/
      gradcam/
```

Example:

```text
analysis/<user_id>/<analysis_id>/original/input.jpg
analysis/<user_id>/<analysis_id>/segmentation/mask.png
analysis/<user_id>/<analysis_id>/segmentation/overlay.png
analysis/<user_id>/<analysis_id>/gradcam/heatmap.png
analysis/<user_id>/<analysis_id>/gradcam/overlay.png
```

Exact bucket naming is an environment/deployment implementation detail and must not be duplicated as a business rule in frontend code.

---

# 18. Database vs Object Storage

## Database

Store:

```text
IDs
ownership
status
timestamps
file references
model metadata
measurements
summary
error metadata
```

## Object Storage

Store:

```text
original image
binary mask
segmentation overlay
Grad-CAM heatmap
Grad-CAM overlay
```

---

# 19. Analysis Lifecycle

```text
created
  ↓
processing
  ↓
completed
```

Failure path:

```text
created
  ↓
processing
  ↓
failed
```

A failed analysis may retain safe failure metadata for debugging/history, but should not expose internal implementation details to the user.

---

# 20. History Data

History is derived primarily from `analyses`.

No separate duplicated history table is required unless implementation later demonstrates a concrete need.

History view may retrieve:

```text
analysis id
created_at
status
thumbnail/original reference
segmentation status
```

Full result is loaded from the analysis detail endpoint.

---

# 21. Deletion

When an analysis is deleted:

1. verify ownership;
2. delete or invalidate its database record according to persistence policy;
3. remove associated object-storage files where applicable;
4. ensure no orphaned result objects remain.

Deletion must not allow one user to delete another user's analysis.

---

# 22. Referential Integrity

Required logical relationship:

```text
users.id
    ↓
analyses.user_id
```

`analyses.user_id` must reference an existing authenticated user.

Deleting a user must follow the chosen authentication/database lifecycle policy and must not leave accessible orphaned analysis records.

---

# 23. Security and Row Ownership

Because the application handles medical images, ownership must be enforced server-side and, where applicable, at database/storage policy level.

Rules:

- user can read own analysis;
- user can create analysis for self;
- user can delete own analysis;
- user cannot read another user's analysis;
- user cannot modify `user_id` to obtain ownership;
- service-role credentials remain backend-only.

---

# 24. Data Minimization

PIXEL-T should store only information needed for:

- authentication;
- analysis;
- result rendering;
- history;
- reproducibility;
- system operation.

Do not add unnecessary patient-identifying information unless explicitly required by a future approved specification.

The current product scope does not require a patient-record data model.

---

# 25. No Clinical Diagnosis Entity

The schema intentionally does not define:

```text
diagnosis
cancer
malignancy
treatment
clinical_decision
```

as production entities.

This keeps the data model aligned with PIXEL-T's stated purpose as an AI analysis support system.

---

# 26. Example Completed Analysis Record

Logical representation:

```json
{
  "id": "analysis-id",
  "user_id": "user-id",
  "status": "completed",

  "original_image_path": "analysis/user-id/analysis-id/original/input.jpg",
  "original_filename": "colonoscopy.jpg",
  "original_mime_type": "image/jpeg",
  "original_width": 1920,
  "original_height": 1080,

  "binary_mask_path": "analysis/user-id/analysis-id/segmentation/mask.png",
  "segmentation_overlay_path": "analysis/user-id/analysis-id/segmentation/overlay.png",

  "segmentation_status": "detected",
  "area_pixels": 12345,
  "area_ratio": 0.123,
  "bounding_width_pixels": 150,
  "bounding_height_pixels": 120,

  "gradcam_heatmap_path": "analysis/user-id/analysis-id/gradcam/heatmap.png",
  "gradcam_overlay_path": "analysis/user-id/analysis-id/gradcam/overlay.png",

  "model_architecture": "U-Net + ResNet50",
  "model_version": "MODEL_VERSION",
  "model_config_version": "MODEL_CONFIG_VERSION",

  "summary_text": "Model menghasilkan area segmentasi pada citra yang dianalisis.",

  "created_at": "2026-01-01T00:00:00Z",
  "completed_at": "2026-01-01T00:00:05Z"
}
```

Nilai di atas adalah contoh struktur, bukan nilai eksperimen final.

---

# 27. Data Consistency

Satu analysis harus mempertahankan hubungan:

```text
analysis_id
   │
   ├── original image
   ├── binary mask
   ├── segmentation overlay
   ├── Grad-CAM heatmap
   ├── Grad-CAM overlay
   └── model metadata
```

Semua result object harus berasal dari analysis/inference yang sama.

Tidak boleh terjadi:

```text
Image A
+
Mask B
+
Grad-CAM C
```

dalam satu analysis record.

---

# 28. Reproducibility Metadata

Completed analysis sebaiknya dapat ditelusuri ke:

```text
model architecture
model version
model configuration version
input characteristics
threshold
TTA configuration
post-processing configuration
Grad-CAM configuration
```

Metadata hanya menyimpan parameter yang benar-benar digunakan.

---

# 29. Environment Configuration Boundary

Environment secrets tidak disimpan dalam database analysis.

Contoh yang tidak boleh disimpan sebagai analysis data:

```text
SUPABASE_SERVICE_ROLE_KEY
SECRET_KEY
database password
API secret
```

Model artifact path dan infrastructure configuration dikelola melalui environment/configuration layer.

Analysis hanya menyimpan metadata version/configuration yang diperlukan untuk reproducibility.

---

# 30. Database Technology

PRD/research scope menetapkan penggunaan Supabase sebagai database/storage platform.

Supabase menyediakan database PostgreSQL dan object storage untuk kebutuhan PIXEL-T. Seluruh file biner gambar disimpan di Supabase Storage, sedangkan database Supabase/PostgreSQL hanya menyimpan metadata analisis dan referensi path objek.

Implementasi schema harus tetap mengikuti logical model pada dokumen ini meskipun detail migration/DDL disusun pada tahap coding.

---

# 31. API Relationship

Data model ini menjadi persistence source untuk API:

```text
POST   /api/analysis
GET    /api/analysis/{analysis_id}
GET    /api/history
DELETE /api/history/{analysis_id}
```

Authentication resources menggunakan authentication layer.

API Contract menentukan bagaimana data diekspos; Data Model menentukan bagaimana data disimpan.

---

# 32. Change Rules

Perubahan berikut dianggap structural changes:

- penambahan entity utama;
- perubahan relationship;
- perubahan required field;
- perubahan ownership model;
- perubahan storage strategy;
- perubahan semantic field;
- perubahan model metadata contract.

Perubahan yang berdampak pada API harus memperbarui:

```text
APIContract.md
FunctionalSpecification.md
DataModelSpecification.md
```

Perubahan model runtime harus memperbarui `ModelIntegrationSpecification.md` jika mempengaruhi metadata yang disimpan.

---

# 33. Final Data Model

Model data PIXEL-T secara konseptual:

```text
USER
 │
 │ 1:N
 ▼
ANALYSIS
 │
 ├── Original Image
 ├── Segmentation Mask
 ├── Segmentation Overlay
 ├── Model Measurements
 ├── Grad-CAM Heatmap
 ├── Grad-CAM Overlay
 ├── Model Metadata
 └── Analysis Summary
```

**Status: FINAL / LOCKED**
