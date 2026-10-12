# PIXEL-T — AI Layer

Directory ini bertanggung jawab untuk komponen model kecerdasan buatan (AI) pada sistem PIXEL-T.

## 1. Specification & Framework
- **Framework:** PyTorch
- **Primary Model:** U-Net + ResNet50
- **Task:** Segmentasi semantik biner polip usus dari citra endoskopi/kolonoskopi
- **Explainable AI (XAI):** Grad-CAM

## 2. Directory Structure
- `inference/` : Modul pemrosesan inferensi, preprocessing, post-processing, dan visualisasi.
- `config/`    : Konfigurasi model runtime (input size, threshold, target layer).
- `models/`    : Folder penyimpanan bobot/checkpoint model (.pt, .pth). File bobot model biner di-ignore oleh `.gitignore` dan tidak boleh di-commit ke repository.

## 3. Verified TASK 10 Runtime Boundary

The verified artifact currently used by the model loader is:

```text
ai/models/PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth
```

Its SHA-256 is:

```text
46521AE90D12F57F77A7B9921881910B41071DBBB1EFF4D2172A2C437564C581
```

The loader instantiates the notebook-compatible SMP U-Net with a ResNet50
encoder, SCSE decoder attention, three RGB input channels, one logit output
channel, strict state-dict loading, and `eval()` mode. Preprocessing uses RGB,
512x512 resize, and ImageNet normalization. Raw segmentation uses sigmoid,
threshold 0.55, and the verified five-orientation/five-scale TTA settings.

TASK 10 does not implement Grad-CAM, complete post-processing, measurement
persistence, or final AI response/database lifecycle updates. Those remain
later pipeline boundaries.

## 4. Implementation Boundary
- Tidak menambahkan classifier kanker atau prediksi malignansi.
- Tidak menggunakan framework di luar PyTorch.
- Checkpoint dan hyperparameter final mengacu pada `docs/ModelIntegrationSpecification.md`.
