# ModelIntegrationSpecification.md

# PIXEL-T — Model Integration Specification

**Status:** FINAL / LOCKED — Scenario 1 Ver.22 production model is finalized. All production model parameters are fixed and verified against the locked checkpoint. No unresolved production model parameters remain in this document.

**Product:** PIXEL-T  
**Primary Model:** U-Net + ResNet50  
**Task:** Binary semantic segmentation of intestinal/colorectal polyp regions in endoscopic images  
**XAI:** Grad-CAM  
**Runtime Boundary:** Backend AI inference service  

---

## 1. Purpose

Dokumen ini merupakan kontrak teknis antara **model final hasil penelitian** dan **implementasi AI pada web PIXEL-T**.

Tujuannya adalah memastikan bahwa model yang digunakan pada web mempunyai perilaku yang konsisten dengan model yang dipilih sebagai model final penelitian, terutama pada:

- arsitektur;
- checkpoint/model artifact;
- preprocessing;
- input/output tensor;
- output activation;
- threshold;
- post-processing;
- TTA;
- pengukuran berbasis mask;
- Grad-CAM;
- model versioning;
- runtime configuration; dan
- reproducibility.

Dokumen ini harus dibaca bersama:

1. `PRD_PIXEL-T_FINAL.md` — product requirements dan batasan produk;
2. `StyleGuide.md` — aturan visual dan UX;
3. `FunctionalSpecification.md` — perilaku sistem, API, persistence, environment, dan arsitektur aplikasi.

Jika terjadi konflik, **PRD menentukan batas produk**, `FunctionalSpecification` menentukan perilaku sistem, sedangkan dokumen ini menjadi sumber kebenaran untuk detail integrasi model AI.

---

# 2. Model Identity

## 2.1 Primary Production Model

PIXEL-T menggunakan **satu model utama** untuk inference produk:

```text
Architecture : U-Net
Encoder      : ResNet50
Task         : Binary semantic segmentation
Target       : Polyp region
XAI          : Grad-CAM
```

Model selector atau pilihan beberapa model tidak termasuk dalam product scope.

## 2.2 Model Boundary

Model AI bertanggung jawab untuk menghasilkan keluaran yang diperlukan oleh sistem:

```text
Input Image
    ↓
U-Net + ResNet50
    ↓
Segmentation Output
    ↓
Binary Mask
    ↓
Segmentation Overlay
```

Grad-CAM merupakan jalur explainability yang berasal dari model yang sama dan bukan model terpisah.

Model tidak bertanggung jawab untuk:

- diagnosis klinis;
- klasifikasi kanker/malignansi;
- rekomendasi terapi;
- keputusan klinis;
- chatbot medis; atau
- generated explanation berbasis LLM.

---

# 3. Architectural Contract

## 3.1 U-Net + ResNet50

ResNet50 digunakan sebagai encoder/backbone pada U-Net.

Secara konseptual:

```text
Input Image
     ↓
ResNet50 Encoder
     ├── feature level 1 ──┐
     ├── feature level 2 ──┤
     ├── feature level 3 ──┤── Skip Connections
     └── deep feature ─────┘
              ↓
        U-Net Decoder
              ↓
     Segmentation Head
              ↓
       Binary Output Map
```

Classification head ResNet50 tidak digunakan sebagai output product segmentation.

Detail implementasi encoder, decoder, jumlah channel, normalization, activation, block, dan upsampling **harus mengikuti kode training final**. Jangan membuat ulang arsitektur hanya berdasarkan label `U-Net + ResNet50`.

## 3.2 Architecture Fidelity

Production model harus mempunyai compatibility terhadap:

- architecture definition;
- encoder;
- layer naming/structure yang dibutuhkan Grad-CAM;
- tensor input;
- tensor output; dan
- checkpoint/state dictionary.

Checkpoint dari arsitektur lain tidak boleh dimuat hanya karena nama file atau formatnya terlihat kompatibel.

---

# 4. Model Artifact Contract

## 4.1 Required Artifact

Production/web inference harus menggunakan checkpoint/model artifact yang secara eksplisit ditetapkan sebagai final.

Minimal metadata:

```text
model_name
architecture
encoder
model_version
checkpoint/artifact
framework_version
input_size
preprocessing_version
threshold
postprocessing_version
tta_version
gradcam_target_layer
```

Contoh konfigurasi:

```yaml
model_name: UNet
encoder: ResNet50
model_version: Scenario 1 Ver.22
checkpoint: PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth
framework: PyTorch
framework_version: 2.14.0+cu126
input_size: 512
preprocessing_version: Not separately versioned; locked by Scenario 1 Ver.22 configuration.
threshold: 0.55
postprocessing_version: Not separately versioned; locked by Scenario 1 Ver.22 configuration.
tta_enabled: True
gradcam_target_layer: decoder.blocks.4.conv2.0
```

## 4.2 Artifact Integrity

Pada startup/deployment validation, sistem harus memverifikasi bahwa:

- artifact tersedia;
- architecture yang dibuat sesuai dengan artifact;
- encoder sesuai;
- state dictionary/checkpoint kompatibel;
- expected input dapat diproses;
- expected output tersedia;
- target Grad-CAM dapat ditemukan; dan
- minimal satu dry-run berhasil.

Jika validasi kritis gagal, **Model Service tidak boleh dinyatakan ready**.

Tidak boleh ada fallback diam-diam ke checkpoint/model lain.

## 4.3 Optional Reproducibility Metadata

Jika tersedia, simpan juga:

```text
checkpoint_hash
code_version
training_run_id
configuration_hash
```

Metadata ini membantu memastikan hasil history dapat ditelusuri ke model yang digunakan saat inference.

---

# 5. Input Contract

## 5.1 Product Input

Input inference adalah satu citra endoskopi/kolonoskopi yang diunggah pengguna melalui web.

Validasi file dilakukan oleh backend sebelum model dipanggil. Detail validasi file berada pada `FunctionalSpecification.md`.

## 5.2 Original Image Preservation

Original image harus dipertahankan sebelum preprocessing inference:

```text
Uploaded File
     ├── Original Image → result/storage
     └── Inference Copy → preprocessing → model
```

Original image bukan tensor inference dan tidak boleh digantikan oleh resized/normalized image pada hasil yang ditampilkan kepada pengguna.

## 5.3 Image Integrity

Preprocessing tidak boleh mengubah original stored image secara permanen.

Model pipeline dapat melakukan resize, normalization, color conversion, dan tensor conversion pada salinan inference.

---

# 6. Preprocessing Contract

Preprocessing inference **harus identik secara fungsional dengan preprocessing final saat training/evaluation model yang dipilih**.

Logical pipeline:

```text
Decode
  ↓
Color-space handling
  ↓
Resize
  ↓
Normalization
  ↓
Tensor conversion
  ↓
Batch dimension
  ↓
Model
```

Parameter final:

```text
Input size       : 512 × 512
Resize strategy  : bilinear
Color order      : RGB
Normalization    : ImageNet
Mean             : (0.485, 0.456, 0.406)
Std              : (0.229, 0.224, 0.225)
Tensor layout    : B × C × H × W
Dtype            : torch.float32
Scaling          : divide by 255.0 before normalization
Pre-normalization range : [0, 1]
```

Jangan mengambil preprocessing dari model lain atau dari default framework.

## 6.1 Preprocessing Single Source of Truth

Preprocessing harus didefinisikan pada satu konfigurasi/runtime component yang digunakan oleh inference pipeline.

Frontend tidak melakukan preprocessing model secara mandiri.

Frontend hanya mengirim image file ke backend.

---

# 7. Model Input Tensor

Expected logical input:

```text
B × C × H × W
```

atau representation equivalent sesuai framework.

Final values:

```text
Channels   : 3
Height     : 512
Width      : 512
Dtype      : torch.float32
Range      : input pixel scaling before normalization: [0, 1]
             final tensor: ImageNet-normalized torch.float32
             (not bounded to [0, 1] after normalization)
```

Exact values wajib diambil dari training code/checkpoint final.

---

# 8. Model Output Contract

Model binary segmentation secara logical menghasilkan satu spatial output:

```text
Model Input
    ↓
U-Net + ResNet50
    ↓
Segmentation Logit / Probability Map
    ↓
Threshold
    ↓
Binary Mask
```

Expected logical output:

```text
B × 1 × H × W
```

atau representation equivalent sesuai framework.

Exact output tensor shape dan dtype:

```text
Shape    : B × 1 × H × W
Dtype    : torch.float32
Channels : 1
Activation at model output : raw logits
```

## 8.1 Output Activation

Jika final model menghasilkan logits:

```text
probability = sigmoid(logit)
```

Jika final model sudah menghasilkan probability:

```text
probability = model_output
```

Sigmoid tidak boleh diterapkan dua kali.

Final convention:

```text
Model output       : raw segmentation logits
Model activation   : None / identity
Inference          : sigmoid(logits)
Probability range  : [0, 1]
Binary mask        : probability >= 0.55
```

---

# 9. Threshold Contract

Binary mask dibentuk dari probability map:

```text
mask = probability >= threshold
```

Final threshold:

```text
Production threshold : 0.55
```

Threshold harus berasal dari konfigurasi/evaluasi model final.

Threshold tidak boleh:

- memakai arbitrary default tanpa dasar;
- diubah pengguna melalui UI;
- berbeda antara backend services;
- berubah setelah result disimpan tanpa versioning; atau
- ditentukan oleh frontend.

Jika threshold diperoleh dari validation/evaluation analysis, nilai tersebut menjadi bagian dari model configuration final.

---

# 10. Post-Processing Contract

Post-processing hanya boleh diterapkan jika digunakan dan telah diputuskan untuk final model pipeline.

Contoh logical flow:

```text
Binary Probability
      ↓
Threshold
      ↓
Minimum-area filtering   [optional]
      ↓
Contour smoothing        [optional]
      ↓
Other validated operation[optional]
      ↓
Final Binary Mask
```

Final configuration:

```text
Min area         : 25 px
Contour smooth   : enabled
Morphological op : enabled (close then open, 3×3)
Other operation  : none
```

Jika training/evaluation final tidak menggunakan suatu operation, production tidak boleh menambahkannya secara diam-diam.

Setiap perubahan post-processing yang dapat mengubah hasil mask harus diperlakukan sebagai perubahan model configuration dan membutuhkan evaluasi ulang.

---

# 11. Test-Time Augmentation (TTA)

TTA hanya digunakan jika final production configuration menetapkannya.

```text
TTA enabled: True
```

Jika enabled:

```text
Input
 ↓
Generate configured transforms
 ↓
Model inference per transform
 ↓
Inverse spatial transform
 ↓
Aggregate probability maps
 ↓
Threshold
 ↓
Post-processing
 ↓
Final mask
```

Final configuration:

```text
TTA transforms      : original, horizontal flip, vertical flip,
                      rotate 90°, rotate 270°
Scales              : 0.85, 0.95, 1.00, 1.05, 1.15
Aggregation method  : mean probability maps after inverse spatial
                      transformation to canonical coordinates
Total branches      : 25
```

Frontend tidak perlu mengetahui detail internal TTA.

TTA tidak boleh diaktifkan hanya karena tersedia pada kode eksperimen.

---

# 12. Segmentation Mask Contract

Final mask adalah **produk utama model segmentation**.

Mask harus berada pada coordinate system yang dapat disejajarkan dengan image yang ditampilkan.

Jika inference dilakukan pada resized image:

```text
Original Image
     ↓
Resize
     ↓
Model
     ↓
Mask at inference size
     ↓
Resize mask to result/display coordinate system
```

Untuk mask diskrit/biner, resizing harus menggunakan nearest-neighbor atau metode equivalent yang tidak menghasilkan kelas intermediate.

Final mask harus memiliki nilai foreground/background yang eksplisit.

---

# 13. Segmentation Overlay Contract

Overlay dibentuk dari:

```text
Original Image
      +
Final Binary Mask
      ↓
Segmentation Overlay
```

Requirements:

- spatial alignment harus benar;
- original image tetap menjadi visual base;
- mask terlihat jelas;
- overlay tidak mengubah data original;
- overlay tidak boleh terlihat seperti Grad-CAM.

Visual color/opacity mengikuti `StyleGuide.md` dan tidak mengubah nilai mask model.

---

# 14. Model-Derived Measurements

Measurement dihitung **hanya dari final binary mask**, bukan dari Grad-CAM.

## 14.1 Pixel Area

```text
area_pixels = count(mask == foreground)
```

## 14.2 Area Ratio

Jika image dimensions valid:

```text
area_ratio = area_pixels / (image_width × image_height)
area_percentage = area_ratio × 100
```

Area ratio merupakan proporsi area tersegmentasi terhadap area image yang digunakan untuk measurement.

## 14.3 Bounding Box

Jika foreground tersedia:

```text
x_min
y_min
x_max
y_max
```

Derived:

```text
width_pixels  = x_max - x_min + 1
height_pixels = y_max - y_min + 1
```

Jika mask kosong:

```text
bounding_box = null
```

## 14.4 Physical Measurement Boundary

Sistem **tidak boleh mengubah pixel measurement menjadi mm/cm/physical area** tanpa physical calibration/scale yang valid.

Tidak boleh menampilkan physical size yang hanya merupakan konversi asumsi.

---

# 15. Confidence / Probability Contract

Segmentation probability map adalah output internal model dan **tidak otomatis merupakan user-facing confidence**.

Bedakan:

```text
Pixel probability
      ≠
Image confidence
      ≠
Segmentation quality metric
```

Tidak boleh menggunakan:

```text
confidence = max(pixel_probability)
```

sebagai confidence produk tanpa definisi dan validasi khusus.

Dice, IoU, Accuracy, Precision, Recall, dan HD95 dari dataset evaluasi adalah research metrics dan bukan confidence untuk satu image pengguna.

Jika tidak terdapat definisi confidence yang valid:

```text
confidence = unavailable
```

UI tidak menampilkan confidence.

---

# 16. Research Metrics vs Runtime Outputs

## 16.1 Research Evaluation

Model penelitian dapat dievaluasi dengan:

- Dice;
- IoU;
- Accuracy;
- Precision;
- Recall;
- HD95.

Metrics tersebut membutuhkan ground-truth yang sesuai untuk evaluasi.

## 16.2 Runtime User Analysis

Runtime analysis menghasilkan:

- binary mask;
- segmentation overlay;
- area pixels;
- area ratio;
- bounding box;
- Grad-CAM heatmap;
- Grad-CAM overlay;
- model metadata.

Research metrics tidak boleh dihitung seolah-olah tersedia pada image user tanpa ground-truth annotation.

---

# 17. Grad-CAM Integration Contract

## 17.1 Purpose

Grad-CAM digunakan sebagai visualisasi activation/relevance model terhadap target output yang ditentukan.

Grad-CAM bukan:

- ground-truth mask;
- segmentation mask;
- probability map;
- diagnosis;
- bukti diagnosis;
- batas polip yang presisi; atau
- rekomendasi klinis.

## 17.2 Same-Model Requirement

Grad-CAM harus berasal dari **model/checkpoint yang sama dengan model yang menghasilkan segmentation result**.

Tidak boleh:

```text
Segmentation → Model A
Grad-CAM     → Model B
```

Keduanya harus menggunakan model version yang sama untuk satu analysis result.

---

# 18. Grad-CAM Target Layer

Target layer harus merupakan feature/convolutional layer yang:

1. benar-benar ada pada final model;
2. digunakan dalam forward path;
3. memiliki spatial activation maps;
4. dapat menerima gradient untuk Grad-CAM;
5. relevan terhadap representation yang dijelaskan.

Final target layer:

```text
decoder.blocks.4.conv2.0
```

Verified against the production Scenario 1 Ver.22 checkpoint. This is the
final 3x3 Conv2d in the fifth decoder block, with spatial feature maps and 16
output channels. The decoder block container itself is not used as the hook.

Jangan memilih layer hanya karena namanya `last_conv` atau karena berada paling akhir secara tekstual.

Target layer harus diuji menggunakan checkpoint final.

---

# 19. Grad-CAM Target Objective for Segmentation

Segmentation berbeda dari image classification karena output mempunyai dimensi spatial.

Karena itu Grad-CAM harus mempunyai **scalar target objective** yang eksplisit.

Logical contract:

```text
Segmentation output
      ↓
Target region/objective selection
      ↓
Scalar objective Y
      ↓
Backward
      ↓
Grad-CAM
```

Target objective dapat berupa aggregate yang ditetapkan pada segmentation output, misalnya sum/mean dari nilai target segmentation tertentu, **hanya jika definisi tersebut dipilih dan diuji untuk final implementation**.

Final target objective:

```text
Mean selected segmentation logit over the target mask.
```

The target mask is the supplied binary mask, or the canonical sigmoid output
thresholded at 0.55 when no mask is supplied. An empty target mask produces a
zero scalar connected to the logits and therefore a deterministic zero
heatmap; it does not fall back to a different objective.

Implementasi tidak boleh menyalin target Grad-CAM classification secara otomatis tanpa menyesuaikannya dengan output segmentation.

---

# 20. Grad-CAM Calculation Contract

Logical pipeline:

```text
Input Image
    ↓
Preprocess
    ↓
Forward Pass
    ↓
Capture Target-Layer Activations
    ↓
Build Scalar Target Objective
    ↓
Backward Pass
    ↓
Capture Target-Layer Gradients
    ↓
Global Average Pooling of Gradients
    ↓
Weighted Sum of Activations
    ↓
ReLU
    ↓
Normalize
    ↓
Resize
    ↓
Heatmap
```

Logical formula:

```text
α_k = GlobalAveragePooling(∂Y / ∂A_k)

L_GradCAM = ReLU(Σ_k α_k A_k)
```

Dengan:

- `A_k` = activation channel pada target layer;
- `Y` = scalar target objective untuk segmentation;
- `α_k` = weight channel hasil aggregate gradient.

Implementasi final harus mengikuti actual framework/model graph.

---

# 21. Grad-CAM Normalization

Heatmap harus dinormalisasi secara deterministic.

Logical range:

```text
0.0 → 1.0
```

Exact normalization:

```text
ReLU, min-max normalization to [0.0, 1.0].
Constant or non-finite maps fail safely or become a finite zero map for the
constant case.
```

Normalisasi harus konsisten agar input yang sama menghasilkan visualisasi yang konsisten pada kondisi runtime yang sama.

---

# 22. Grad-CAM Heatmap

Logical generation:

```text
Normalized Grad-CAM
       ↓
Visualization Colormap
       ↓
Heatmap Image
```

Colormap dan opacity merupakan presentation concern dan harus konsisten dengan `StyleGuide.md`/implementasi final.

Heatmap tidak boleh menggunakan visual treatment yang membuatnya tampak seperti binary segmentation.

---

# 23. Grad-CAM Overlay

```text
Original Image
      +
Grad-CAM Heatmap
      ↓
Grad-CAM Overlay
```

Requirements:

- spatial alignment benar;
- original image tetap terlihat;
- activation mudah dibedakan dari segmentation;
- alpha/opacity konsisten;
- tidak ada crop/stretch/filter yang tidak diperlukan.

---

# 24. Relationship Between Segmentation and Grad-CAM

| Output | Makna teknis |
|---|---|
| Binary Mask | hasil segmentasi setelah threshold/post-processing |
| Segmentation Overlay | visualisasi binary mask pada original image |
| Grad-CAM Heatmap | visualisasi activation/relevance terhadap target objective |
| Grad-CAM Overlay | Grad-CAM di atas original image |

Aturan utama:

```text
Grad-CAM ≠ Binary Mask
Grad-CAM ≠ Ground Truth
Grad-CAM ≠ Diagnosis
```

Grad-CAM tidak boleh digunakan untuk menggantikan segmentation result.

---

# 25. Inference and Gradient Runtime Modes

Segmentation inference dan Grad-CAM mempunyai kebutuhan gradient yang berbeda.

## 25.1 Segmentation

```text
eval mode
+
inference/no_grad context
```

digunakan bila hanya membutuhkan model output.

## 25.2 Grad-CAM

```text
eval mode
+
controlled gradient context
```

Gradients hanya diaktifkan pada scope yang diperlukan.

Model tidak boleh kembali ke training mode untuk menghasilkan user result.

---

# 26. Model Runtime Lifecycle

Model dimuat secara lazy pada first inference request, protected by a loading lock, verified against the expected checkpoint SHA-256, dan placed in evaluation mode:

```text
First Inference Request
      ↓
Acquire Loading Lock
      ↓
Load Configuration
      ↓
Verify Checkpoint SHA-256
      ↓
Load Model Artifact (strict state_dict)
      ↓
Set Evaluation Mode
      ↓
Model Service Ready
```

Model tidak perlu dimuat ulang untuk setiap image kecuali terdapat deployment constraint yang memang mengharuskannya.

## 26.1 Readiness

Model Service hanya boleh menerima inference apabila seluruh critical validation berhasil.

```text
READY
```

atau

```text
NOT READY
```

Tidak ada status READY apabila checkpoint/architecture/target layer tidak tervalidasi.

---

# 27. Runtime Device

Runtime configuration menentukan device yang digunakan.

Logical policy:

```text
CUDA available
    → use configured CUDA device
else
    → CPU fallback
```

Exact deployment policy:

```text
CUDA if available; otherwise CPU.
MODEL_DEVICE environment variable may override automatic device selection.
Device selection is a deployment policy, not a model-contract requirement.
```

CPU fallback tidak boleh mengubah logical model configuration seperti threshold atau preprocessing.

Perbedaan floating-point antar device dapat terjadi dalam batas toleransi runtime, tetapi harus tidak mengubah kontrak output secara semantik.

---

# 28. Model Configuration — Single Source of Truth

Model configuration harus mempunyai satu sumber kebenaran.

Contoh logical configuration:

```python
MODEL_CONFIG = {
    "model_name": "UNet",
    "encoder": "ResNet50",
    "version": "Scenario 1 Ver.22",
    "checkpoint": "PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth",
    "framework": "PyTorch",
    "framework_version": "2.14.0+cu126",
    "input_size": 512,
    "preprocessing_version": "Not separately versioned; locked by Scenario 1 Ver.22 configuration.",
    "threshold": 0.55,
    "postprocessing_version": "Not separately versioned; locked by Scenario 1 Ver.22 configuration.",
    "tta_enabled": True,
    "tta_config": {
        "orientations": [
            "original",
            "horizontal_flip",
            "vertical_flip",
            "rotate_90",
            "rotate_270",
        ],
        "multiscale_enabled": True,
        "scales": [0.85, 0.95, 1.0, 1.05, 1.15],
    },
    "gradcam_target_layer": "decoder.blocks.4.conv2.0",
    "gradcam_target_objective": "mean selected segmentation logit over target mask",
    "checkpoint_sha256": "46521AE90D12F57F77A7B9921881910B41071DBBB1EFF4D2172A2C437564C581",
}
```

Implementasi dapat menggunakan typed configuration object, environment variables, YAML, atau mechanism lain yang sesuai dengan `FunctionalSpecification.md`.

Yang wajib adalah:

- tidak ada threshold hard-coded di beberapa service;
- tidak ada preprocessing berbeda antara service;
- TTA tidak ditentukan ulang oleh endpoint;
- Grad-CAM target tidak ditentukan ulang per request tanpa alasan;
- configuration version dapat ditelusuri.

---

# 29. Environment Configuration Boundary

`FunctionalSpecification.md` mendefinisikan environment/configuration system aplikasi.

Dokumen ini mendefinisikan **model-specific configuration** yang dipetakan ke environment/configuration system tersebut.

Contoh:

```text
FunctionalSpecification
        ↓
MODEL_PATH
MODEL_VERSION
MODEL_DEVICE
MODEL_INPUT_SIZE
MODEL_THRESHOLD
TTA_ENABLED
POSTPROCESSING_ENABLED
GRADCAM_TARGET_LAYER
        ↓
Model Configuration Loader
        ↓
MODEL_CONFIG
        ↓
Inference Service
```

Environment variables tidak boleh menjadi satu-satunya sumber metadata yang diperlukan untuk reproducibility. Nilai final model juga harus dapat ditelusuri pada model version/configuration record.

Secrets tidak boleh ditempatkan di model configuration.

---

# 30. Model Service Interface

AI service harus dipanggil oleh backend analysis service, bukan langsung oleh frontend.

Logical interface:

```text
Analysis Service
      ↓
Model Service
      ↓
Segmentation + Grad-CAM
      ↓
Structured Result
```

## 30.1 Input

Model service menerima minimal:

```text
image
model_version/configuration
```

Model version/configuration dapat berasal dari server-side configuration dan tidak harus dikirim sebagai pilihan bebas dari frontend.

## 30.2 Output

Logical result:

```json
{
  "model_version": "...",
  "segmentation": {
    "mask": "...",
    "overlay": "..."
  },
  "measurements": {
    "area_pixels": 0,
    "area_ratio": 0.0,
    "bounding_box": null
  },
  "gradcam": {
    "heatmap": "...",
    "overlay": "..."
  }
}
```

Actual transport format/storage references mengikuti `FunctionalSpecification.md`.

Confidence/probability image-level hanya boleh ditambahkan jika sudah mempunyai definisi valid dan final.

---

# 31. Model Result Consistency

Untuk satu analysis request, komponen berikut harus berasal dari model configuration/version yang sama:

```text
Binary Mask
Segmentation Overlay
Measurements
Grad-CAM Heatmap
Grad-CAM Overlay
Model Metadata
```

Tidak boleh terjadi:

```text
Mask     → model v2
Grad-CAM → model v1
Metadata → model v3
```

Jika model configuration berubah, analysis baru harus menggunakan version baru dan result lama tetap mempertahankan metadata version sebelumnya.

---

# 32. Persistence Metadata

Setiap analysis result yang disimpan minimal menyimpan:

```text
model_version
architecture
encoder
configuration_version
```

Recommended:

```text
checkpoint_hash
preprocessing_version
postprocessing_version
tta_version
gradcam_target_layer
```

Tujuannya adalah reproducibility dan traceability, bukan menampilkan seluruh detail teknis kepada user.

---

# 33. End-to-End Production Pipeline

```text
                     USER IMAGE
                         │
                         ▼
                  Secure Validation
                         │
                         ▼
                  Preserve Original
                         │
                         ▼
                    Preprocessing
                         │
                         ▼
                ┌──────────────────┐
                │ U-Net + ResNet50 │
                └────────┬─────────┘
                         │
                 Logit / Probability
                         │
                      Threshold
                         │
                  Post-processing
                         │
                         ▼
                    Binary Mask
                    │          │
                    │          └─────────────┐
                    ▼                        ▼
             Segmentation Overlay      Measurements
                    │
                    │
                    ▼
             Grad-CAM Branch
                    │
             Target Objective
                    │
          Activations + Gradients
                    │
                    ▼
             Grad-CAM Heatmap
                    │
                    ▼
             Grad-CAM Overlay
                    │
                    ▼
            Persist + API Response
```

Pipeline order harus tetap konsisten dengan final configuration.

---

# 34. Failure Handling

## 34.1 Model Load Failure

Jika model tidak berhasil dimuat:

```text
Model Service = NOT READY
```

Analysis request tidak boleh diproses.

## 34.2 Preprocessing Failure

Analysis menjadi:

```text
FAILED
```

Tidak boleh menghasilkan result palsu.

## 34.3 Inference Failure

Tidak boleh mengembalikan binary mask/overlay yang fabricated.

## 34.4 Grad-CAM Failure

Grad-CAM adalah bagian inti dari product explainability.

Jika Grad-CAM gagal, sistem harus mengikuti failure policy pada `FunctionalSpecification.md`:

- result tidak boleh mengklaim XAI berhasil;
- heatmap tidak boleh dibuat secara palsu;
- status/error harus jelas;
- partial segmentation result hanya boleh disimpan jika partial-result behavior memang diizinkan oleh functional contract.

## 34.5 Storage Failure

Model service/analysis service tidak boleh mengklaim result `Saved` apabila persistence belum berhasil.

---

# 35. Performance and Resource Considerations

Integrasi model perlu memperhatikan:

- model loading time;
- image decoding;
- tensor allocation;
- device placement;
- TTA compute cost jika digunakan;
- Grad-CAM memory usage;
- output image generation;
- storage I/O.

Optimisasi tidak boleh mengubah model behavior tanpa evaluasi.

Jangan menghapus Grad-CAM hanya untuk menurunkan latency karena XAI merupakan bagian inti PIXEL-T.

Jangan menghapus TTA/post-processing yang sudah menjadi bagian final model tanpa perubahan model configuration dan evaluasi yang sesuai.

---

# 36. Framework and Runtime Compatibility

Materi proyek mengidentifikasi Python/Flask dan Supabase sebagai bagian dari teknologi sistem, sementara framework AI telah dikunci menggunakan PyTorch. Checkpoint final dan versinya telah ditetapkan: `PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth` (SHA-256 `46521AE90D12F57F77A7B9921881910B41071DBBB1EFF4D2172A2C437564C581`). Nilai runtime di bawah ini merupakan verified runtime environment yang digunakan saat validasi production model.

Final values:

```text
Framework          : PyTorch
Framework version   : 2.14.0+cu126
Python version      : 3.11.9
CUDA version        : 12.6 (verified environment only; not a universal requirement)
Runtime device      : CUDA if available; otherwise CPU
```

Nilai versi di atas merupakan **verified runtime environment** pada saat validasi model, bukan persyaratan deployment universal. Deployment dapat memakai versi lain selama memenuhi kontrak model (PyTorch + segmentation_models_pytorch + SHA-256 checkpoint + normalisasi preprocessing yang sama). CPU fallback tidak boleh mengubah logical model configuration seperti threshold atau preprocessing.

---

# 37. Training-to-Production Verification

Sebelum model masuk ke web, lakukan checklist berikut.

## 37.1 Architecture

- [ ] Architecture final adalah U-Net.
- [ ] Encoder final adalah ResNet50.
- [ ] Classification head tidak digunakan sebagai segmentation output.
- [ ] Decoder sesuai dengan training final.
- [ ] Layer structure sesuai checkpoint.

## 37.2 Input

- [ ] Input size confirmed.
- [ ] Color order confirmed.
- [ ] Resize strategy confirmed.
- [ ] Normalization confirmed.
- [ ] Tensor dtype/layout confirmed.

## 37.3 Output

- [ ] Output shape confirmed.
- [ ] Output activation confirmed.
- [ ] Threshold confirmed.
- [ ] Post-processing confirmed.
- [ ] TTA confirmed.
- [ ] Mask coordinate alignment tested.

## 37.4 XAI

- [ ] Target layer confirmed.
- [ ] Target objective confirmed.
- [ ] Activation capture tested.
- [ ] Gradient capture tested.
- [ ] Heatmap normalization confirmed.
- [ ] Overlay alignment tested.
- [ ] Same model version used for segmentation and Grad-CAM.

## 37.5 Reproducibility

- [ ] Model version assigned.
- [ ] Checkpoint stored.
- [ ] Configuration version assigned.
- [ ] Final evaluation record stored.
- [ ] Optional checkpoint hash stored.

## 37.6 Web Integration

- [ ] Model service initializes successfully and performs lazy model loading on first inference/use.
- [ ] Readiness validation succeeds.
- [ ] Analysis endpoint can invoke model service.
- [ ] Result metadata records model version.
- [ ] History preserves model metadata.
- [ ] Failure states are surfaced correctly.

---

# 38. Experimental Values vs Final Production Values

Eksperimen training yang sudah dijalankan dapat mempunyai konfigurasi seperti:

```text
Input size      : 512
Threshold       : 0.65
EMA             : enabled
TTA             : enabled
Multi-scale TTA : configured
Min area        : 25 px
Contour smooth  : configured
```

Nilai tersebut **tidak otomatis menjadi production contract** hanya karena pernah menghasilkan hasil eksperimen.

Nilai menjadi final production value hanya setelah:

1. final model/run dipilih;
2. checkpoint final ditetapkan;
3. preprocessing final dikonfirmasi;
4. threshold final dikonfirmasi;
5. post-processing final dikonfirmasi;
6. TTA final dikonfirmasi;
7. Grad-CAM target layer/objective diuji; dan
8. seluruh konfigurasi dicatat dalam finalization record.

Dengan demikian, eksperimen dapat berubah tanpa menyebabkan dokumentasi production secara prematur mengunci nilai yang belum final.

---

# 39. Finalization Table

Tabel berikut wajib dilengkapi sebelum web deployment.

| Parameter | Final Value |
|---|---|
| Scenario | Scenario 1 |
| Experiment Version | Ver.22 |
| Model architecture | U-Net |
| Encoder | ResNet50 |
| Decoder attention | SCSE |
| Checkpoint | PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth |
| SHA-256 | 46521AE90D12F57F77A7B9921881910B41071DBBB1EFF4D2172A2C437564C581 |
| Framework | PyTorch |
| Framework version | 2.14.0+cu126 (verified environment) |
| Python version | 3.11.9 (verified environment) |
| CUDA version | 12.6 (verified runtime environment; not a universal deployment requirement) |
| Runtime device | CUDA if available; otherwise CPU |
| Input size | 512 × 512 |
| Color order | RGB |
| Resize strategy | bilinear |
| Normalization | ImageNet |
| Mean | (0.485, 0.456, 0.406) |
| Std | (0.229, 0.224, 0.225) |
| Input dtype/layout | B × C × H × W, torch.float32 |
| Output shape | B × 1 × H × W |
| Output activation | raw logits (sigmoid applied during inference) |
| Threshold | 0.55 |
| Post-processing | Enabled |
| Min area | 25 px |
| Morphological operations | close 3×3, then open 3×3 |
| Fill holes | Enabled |
| Contour smoothing | Enabled |
| Contour epsilon | 0.005 |
| TTA | Enabled |
| TTA orientations | original, horizontal flip, vertical flip, rotate 90°, rotate 270° |
| TTA scales | 0.85, 0.95, 1.00, 1.05, 1.15 |
| TTA aggregation | mean probability after inverse spatial transform |
| Grad-CAM target layer | decoder.blocks.4.conv2.0 |
| Grad-CAM target objective | mean selected segmentation logit over target mask |
| Grad-CAM normalization | ReLU + min-max to [0,1] |
| Grad-CAM branch | canonical non-TTA |
| Model version | Scenario 1 Ver.22 |
| Configuration version | Scenario 1 Ver.22 |
| Preprocessing version | Not separately versioned; locked by Scenario 1 Ver.22 configuration. |
| Postprocessing version | Not separately versioned; locked by Scenario 1 Ver.22 configuration. |
| Checkpoint hash | SHA-256: 46521AE90D12F57F77A7B9921881910B41071DBBB1EFF4D2172A2C437564C581 |

---

# 40. Relationship to LUCIT

LUCIT digunakan sebagai **referensi arsitektur dan pola implementasi**, bukan sebagai sumber kebenaran untuk model PIXEL-T.

Pola yang relevan untuk diadaptasi meliputi:

- separation frontend/backend;
- authentication dan protected workflow;
- analysis workflow;
- image preprocessing/inference;
- segmentation output;
- Grad-CAM service;
- history persistence; dan
- service/controller/repository separation.

Dokumentasi LUCIT menunjukkan workflow sign-in dan analisis, serta pemisahan fungsi sistem menjadi komponen backend yang menangani proses analisis.

LUCIT juga menyediakan pola segmentation berupa preprocessing image, inference, threshold, binary mask, dan visualization yang relevan sebagai referensi struktural.

Namun PIXEL-T **tidak menyalin**:

- classification/malignancy workflow;
- model selector;
- cancer-related prediction;
- LLM/Gemini chatbot;
- LLM-generated medical explanation; atau
- model/configuration LUCIT sebagai production model PIXEL-T.

Grad-CAM LUCIT hanya menjadi referensi pola layanan explainability. Implementasi PIXEL-T wajib menyesuaikan Grad-CAM dengan output **U-Net + ResNet50 segmentation** yang sebenarnya.

---

# 41. Implementation Guardrails for AI Coding Agent

AI coding agent **MUST NOT**:

1. mengganti U-Net + ResNet50 dengan model lain;
2. menambahkan model selector;
3. menambahkan encoder selector;
4. menggunakan LLM untuk XAI;
5. menghasilkan explanation dengan LLM;
6. membuat confidence palsu;
7. menggunakan `max(pixel_probability)` sebagai confidence tanpa definisi final;
8. menggunakan Dice/IoU/HD95 sebagai confidence image;
9. menggunakan Grad-CAM sebagai segmentation mask;
10. menggunakan segmentation mask sebagai diagnosis;
11. menghitung physical size tanpa calibration;
12. menambahkan post-processing tanpa konfigurasi/evaluasi;
13. mengaktifkan TTA tanpa konfigurasi final;
14. mengubah threshold secara diam-diam;
15. mengubah preprocessing secara diam-diam;
16. memakai checkpoint lain sebagai fallback diam-diam;
17. menggunakan model berbeda untuk segmentation dan Grad-CAM;
18. memuat model berbeda hanya karena lebih mudah dideploy;
19. hard-code configuration di banyak service;
20. menampilkan model research metrics sebagai runtime confidence.

AI coding agent **MUST**:

- membaca `FunctionalSpecification.md` sebelum implementasi;
- mengambil model-specific values dari konfigurasi final;
- menjaga original image;
- mencatat model version pada result;
- memvalidasi model saat startup;
- menjaga alignment mask/overlay;
- menggunakan Grad-CAM dari model yang sama;
- menjaga batas non-diagnostic PIXEL-T.

---

# 42. Change Control

Perubahan terhadap salah satu parameter berikut dianggap sebagai **model integration change**:

- architecture;
- encoder;
- checkpoint;
- input size;
- preprocessing;
- threshold;
- post-processing;
- TTA;
- Grad-CAM target layer;
- Grad-CAM target objective;
- output interpretation;
- model version.

Perubahan tersebut harus:

1. diperbarui pada konfigurasi model;
2. diperbarui pada finalization table;
3. diberi model/configuration version baru bila relevan;
4. diuji terhadap model final;
5. diverifikasi kembali terhadap `FunctionalSpecification.md`; dan
6. tidak dilakukan hanya di source code tanpa dokumentasi.

---

# 43. Final Model Integration Contract

Implementasi web PIXEL-T dianggap **model-correct** apabila hubungan berikut terpenuhi:

```text
                 FINAL TRAINING MODEL
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Architecture    Checkpoint    Configuration
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                  Production Model
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        Segmentation             Grad-CAM
              │                     │
       Binary Mask             Heatmap
              │                     │
       Overlay + Metrics        Overlay
              │                     │
              └──────────┬──────────┘
                         ▼
                    Web Result
```

Secara kontraktual:

```text
Training Final Model
        =
Production Architecture
        +
Production Checkpoint
        +
Production Preprocessing
        +
Production Output Interpretation
        +
Production Threshold
        +
Production Post-processing
        +
Production TTA
        +
Production Grad-CAM Target
        +
Production Model Version
```

Tidak boleh ada komponen yang berbeda tanpa versioning dan evaluasi yang sesuai.

---

# 44. Final Status

**Document status:** FINAL / LOCKED  
**Purpose:** Production-ready integration contract  
**Primary model:** U-Net + ResNet50  
**XAI:** Grad-CAM  
**Model-specific unresolved values:** None for the finalized Scenario 1 Ver.22 production model.

Dokumen ini merupakan technical contract untuk implementasi AI service menggunakan Scenario 1 Ver.22, checkpoint `PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth`, dan SHA-256 `46521AE90D12F57F77A7B9921881910B41071DBBB1EFF4D2172A2C437564C581` yang telah diverifikasi. Parameter produksi yang tercantum di dokumen ini harus dipertahankan secara konsisten pada implementation dan deployment.
