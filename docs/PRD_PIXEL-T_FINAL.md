# PRD.md --- PIXEL-T

# Product Requirements Document

**Product:** PIXEL-T\
**Project:** Skripsi S1\
**Product Status:** FINAL / LOCKED\
**Primary User:** Dokter / tenaga medis yang menangani polip usus\
**Primary AI Task:** Segmentasi polip pada citra endoskopi/kolonoskopi\
**Planned / Research Model:** U-Net + ResNet50\
**Primary XAI:** Grad-CAM\
**Reference Product:** LUCIT --- used only as UX, workflow, and
architectural reference\
**Last Scope Decision:** Finalized based on project discussions

------------------------------------------------------------------------

## 1. Document Purpose

Dokumen ini merupakan **source of truth** untuk kebutuhan produk
PIXEL-T.

PRD ini mendefinisikan:

-   tujuan produk;
-   target user;
-   ruang lingkup;
-   user flow;
-   fitur utama;
-   output AI;
-   Explainable AI;
-   batasan medis;
-   batasan terhadap AI coding agent;
-   prinsip implementasi produk.

Dokumen ini **tidak dimaksudkan untuk mengunci seluruh detail teknis
model** yang masih bergantung pada hasil eksperimen dan finalisasi
model.

Dokumen turunan seperti:

-   `StyleGuide.md`;
-   `FunctionalSpecification.md`;
-   `Task.md`;

harus mengikuti PRD ini dan tidak boleh bertentangan dengannya.

------------------------------------------------------------------------

# 2. Product Definition

> **PIXEL-T adalah aplikasi web untuk membantu dokter atau tenaga medis
> menganalisis citra kolonoskopi melalui segmentasi polip menggunakan
> model U-Net + ResNet50 serta Explainable AI berbasis Grad-CAM. Sistem
> menampilkan citra asli, hasil segmentasi, visualisasi Grad-CAM, dan
> informasi analisis yang dapat diturunkan dari output model. PIXEL-T
> merupakan alat bantu analisis dan bukan sistem diagnosis atau
> pengganti keputusan klinis dokter.**

------------------------------------------------------------------------

# 3. Problem Statement

Dokter atau tenaga medis yang menangani pemeriksaan kolonoskopi perlu
meninjau citra endoskopi untuk memahami area yang diindikasikan oleh
model sebagai polip dan lokasi area tersebut pada citra.

PIXEL-T dirancang untuk membantu proses tersebut dengan:

1.  menerima citra kolonoskopi;
2.  melakukan segmentasi otomatis menggunakan model AI;
3.  menampilkan hasil segmentasi;
4.  menyediakan Explainable AI melalui Grad-CAM;
5.  menyediakan informasi analisis yang dapat diturunkan secara valid
    dari output model;
6.  menyimpan hasil agar dapat ditinjau kembali.

PIXEL-T **tidak** dirancang untuk:

-   menggantikan dokter;
-   menentukan diagnosis klinis;
-   menentukan kanker atau malignansi;
-   menentukan stadium penyakit;
-   memberikan rekomendasi pengobatan;
-   memberikan keputusan klinis otomatis.

------------------------------------------------------------------------

# 4. Product Goals

## 4.1 Primary Goal

Membantu dokter atau tenaga medis memperoleh segmentasi area polip pada
citra kolonoskopi secara otomatis serta memahami fokus model melalui
visualisasi hasil segmentasi dan Explainable AI.

## 4.2 Product Goals

PIXEL-T harus:

1.  menyediakan Register dan Login;
2.  menyediakan Dashboard;
3.  menyediakan New Analysis;
4.  memungkinkan upload citra kolonoskopi;
5.  melakukan validasi dan preview citra;
6.  melakukan inference menggunakan satu model AI utama;
7.  menghasilkan segmentation mask;
8.  menampilkan Original Image;
9.  menampilkan Binary Mask;
10. menampilkan Segmentation Overlay;
11. menampilkan Grad-CAM Heatmap;
12. menampilkan Grad-CAM Overlay;
13. menampilkan Model Analysis yang berasal dari output model atau
    perhitungan valid;
14. menyediakan Analysis Summary yang deterministic/model-derived;
15. menyimpan hasil analisis;
16. menyediakan History;
17. menjaga batas antara AI output dan keputusan klinis.

------------------------------------------------------------------------

# 5. Target Users

## 5.1 Primary User

Dokter atau tenaga medis yang menangani polip usus dan menggunakan citra
kolonoskopi sebagai bagian dari pemeriksaan.

## 5.2 Non-Target Users

PIXEL-T bukan ditujukan sebagai:

-   aplikasi diagnosis mandiri pasien;
-   aplikasi konsultasi medis;
-   chatbot kesehatan;
-   aplikasi edukasi pasien;
-   sistem rekomendasi pengobatan;
-   sistem pengganti dokter.

------------------------------------------------------------------------

# 6. Product Scope

## 6.1 In Scope

### Authentication

-   Register
-   Login
-   Logout
-   Protected pages/routes

### Main Workflow

-   Dashboard
-   New Analysis
-   Upload image
-   Preview image
-   Image validation
-   AI inference
-   Result review

### Segmentation

-   Original Image
-   Binary Mask
-   Segmentation Overlay

### Explainable AI

-   Grad-CAM Heatmap
-   Grad-CAM Overlay
-   Deterministic/model-derived explanation

### Model Analysis

-   Model result status
-   Segmentation area
-   Area ratio
-   Bounding width/height jika relevan
-   Valid confidence/probability jika tersedia
-   Model/version information

### Result

-   Analysis Summary
-   Clinical Disclaimer
-   Save Result
-   New Analysis

### History

-   History list
-   Result detail
-   Delete result

------------------------------------------------------------------------

# 7. Explicitly Out of Scope

Fitur berikut **tidak termasuk** dalam PIXEL-T:

-   diagnosis kanker;
-   cancer classification;
-   malignancy classification;
-   cancer staging;
-   treatment recommendation;
-   prescription;
-   automatic clinical decision;
-   automatic clinical interpretation;
-   patient self-diagnosis;
-   chatbot medis;
-   LLM-generated XAI;
-   model selector;
-   multi-model comparison;
-   multi-task classification;
-   model tambahan di luar model utama;
-   artificial confidence score;
-   confidence yang dibuat dari Dice/IoU;
-   clinical recommendation dari Grad-CAM;
-   fitur yang menggantikan keputusan dokter.

AI coding agent tidak boleh menambahkan fitur-fitur tersebut tanpa
perubahan requirement eksplisit.

------------------------------------------------------------------------

# 8. Reference to LUCIT

LUCIT digunakan sebagai **reference product**, bukan sebagai source of
truth PIXEL-T.

## 8.1 Aspek LUCIT yang dapat dijadikan referensi

LUCIT dapat digunakan sebagai referensi untuk:

-   pola authentication;
-   struktur dashboard;
-   pola upload;
-   analysis workflow;
-   result presentation;
-   history;
-   image visualization;
-   loading state;
-   error state;
-   frontend/backend separation;
-   API/service organization;
-   penyimpanan hasil.

## 8.2 Aspek LUCIT yang tidak dibawa ke PIXEL-T

Fitur LUCIT berikut tidak menjadi scope PIXEL-T:

-   classification workflow;
-   cancer classification;
-   multi-task diagnosis;
-   medical chatbot;
-   Gemini/LLM-based explanation;
-   treatment recommendation;
-   medical conversational assistant.

## 8.3 Rule

> **LUCIT adalah referensi untuk bagaimana aplikasi dapat disusun dan
> dipresentasikan. PRD PIXEL-T menentukan apa yang harus dibuat.**

AI coding agent tidak boleh membaca referensi LUCIT lalu menambahkan
fitur LUCIT yang tidak tercantum dalam PRD PIXEL-T.

------------------------------------------------------------------------

# 9. Core User Flow

Alur utama PIXEL-T:

``` text
Register / Login
      ↓
Dashboard
      ↓
New Analysis
      ↓
Upload Colonoscopy Image
      ↓
Preview & Validation
      ↓
Analyze Image
      ↓
AI Inference
      ↓
Segmentation
      ↓
Grad-CAM / Explainable AI
      ↓
Model Analysis
      ↓
Analysis Summary
      ↓
Review Result
      ↓
Save Result
      ↓
History
```

## 9.1 Error Flow

Jika upload gagal:

``` text
Upload
  ↓
Validation Error
  ↓
Error Message
  ↓
Select Another Image
```

Jika inference gagal:

``` text
Analyze
  ↓
Inference Error
  ↓
Error Message
  ↓
Retry / Back
```

Jika optional output tidak tersedia:

``` text
Output unavailable
  ↓
Hide field
atau
Not available
```

Sistem tidak boleh mengisi output yang tidak tersedia dengan nilai
buatan.

------------------------------------------------------------------------

# 10. User Stories

## US-01 --- Authentication

**Sebagai dokter/tenaga medis, saya ingin melakukan Register/Login agar
dapat menggunakan sistem secara terautentikasi.**

Acceptance Criteria:

-   Register tersedia.
-   Login tersedia.
-   Logout tersedia.
-   Protected pages tidak dapat diakses tanpa autentikasi yang valid.

------------------------------------------------------------------------

## US-02 --- Upload Image

**Sebagai dokter/tenaga medis, saya ingin mengunggah citra kolonoskopi
agar citra dapat dianalisis oleh model AI.**

Acceptance Criteria:

-   User dapat memilih file.
-   Preview ditampilkan.
-   File divalidasi.
-   Invalid file menghasilkan error message.
-   User dapat mengganti file.
-   User dapat menjalankan analisis.

------------------------------------------------------------------------

## US-03 --- Automatic Segmentation

**Sebagai dokter/tenaga medis, saya ingin memperoleh segmentasi otomatis
agar area hasil model dapat terlihat dengan jelas.**

Acceptance Criteria:

-   Model deployment dijalankan.
-   Segmentation mask dihasilkan.
-   Original Image ditampilkan.
-   Binary Mask ditampilkan.
-   Segmentation Overlay ditampilkan.
-   Semua output berasal dari input image yang sama.

------------------------------------------------------------------------

## US-04 --- Explainable AI

**Sebagai dokter/tenaga medis, saya ingin melihat Explainable AI agar
dapat memahami area yang menjadi fokus model.**

Acceptance Criteria:

-   Grad-CAM tersedia.
-   Heatmap tersedia.
-   Overlay tersedia.
-   XAI diberi label yang jelas.
-   Penjelasan XAI berasal dari output model dan deterministic
    rules/templates.
-   Tidak menggunakan LLM.
-   Tidak menyatakan bahwa heatmap merupakan diagnosis.
-   Tidak menyatakan bahwa area heatmap tinggi pasti polip.
-   Tidak menyatakan bahwa Grad-CAM membuktikan kebenaran segmentation
    mask.

------------------------------------------------------------------------

## US-05 --- Model Analysis

**Sebagai dokter/tenaga medis, saya ingin melihat informasi yang
diturunkan dari output model agar hasil dapat ditinjau secara
terstruktur.**

Acceptance Criteria:

-   Informasi hanya ditampilkan jika tersedia atau dapat dihitung secara
    valid.
-   Segmentation area dapat ditampilkan.
-   Area ratio dapat ditampilkan.
-   Bounding dimensions dapat ditampilkan jika relevan.
-   Model/version dapat ditampilkan.
-   Confidence/probability hanya ditampilkan jika inference pipeline
    final menyediakan nilai dengan definisi yang jelas.
-   Tidak ada nilai buatan.

------------------------------------------------------------------------

## US-06 --- Analysis Summary

**Sebagai dokter/tenaga medis, saya ingin melihat ringkasan singkat dari
hasil model agar informasi utama dapat dipahami dengan cepat.**

Acceptance Criteria:

-   Summary berasal dari output model dan/atau perhitungan
    deterministic.
-   Tidak menggunakan LLM.
-   Tidak memberikan diagnosis.
-   Tidak menentukan malignansi.
-   Tidak memberikan rekomendasi pengobatan.
-   Tidak membuat klaim yang tidak didukung output model.

------------------------------------------------------------------------

## US-07 --- History

**Sebagai dokter/tenaga medis, saya ingin menyimpan hasil analisis agar
dapat melihatnya kembali.**

Acceptance Criteria:

-   Hasil dapat disimpan.
-   History dapat dilihat.
-   Detail dapat dibuka.
-   Hasil dapat dihapus dengan confirmation.
-   Data hanya dapat diakses oleh user yang berwenang.

------------------------------------------------------------------------

# 11. Functional Requirements

## 11.1 Authentication

  ID       Requirement
  -------- ---------------------------------------------------------
  FR-001   Sistem menyediakan Register.
  FR-002   Sistem menyediakan Login.
  FR-003   Sistem menyediakan Logout.
  FR-004   Sistem melindungi halaman yang membutuhkan autentikasi.

## 11.2 Dashboard

  ID       Requirement
  -------- --------------------------------------------------
  FR-005   Sistem menyediakan Dashboard.
  FR-006   Dashboard menyediakan akses New Analysis.
  FR-007   Dashboard menyediakan akses History.
  FR-008   Dashboard tidak menambahkan fitur di luar scope.

## 11.3 Upload

  ID       Requirement
  -------- -----------------------------------------------------
  FR-009   Sistem menerima upload citra.
  FR-010   Sistem menampilkan preview.
  FR-011   Sistem memvalidasi format file.
  FR-012   Sistem memvalidasi ukuran file.
  FR-013   Sistem memberikan error message untuk file invalid.
  FR-014   User dapat mengganti file sebelum inference.
  FR-015   User dapat memulai analysis.

## 11.4 AI Inference

  -----------------------------------------------------------------------
  ID                                  Requirement
  ----------------------------------- -----------------------------------
  FR-016                              Sistem menggunakan satu model AI
                                      utama.

  FR-017                              Model utama adalah U-Net +
                                      ResNet50.

  FR-018                              Preprocessing mengikuti model
                                      final.

  FR-019                              Parameter inference mengikuti model
                                      final.

  FR-020                              Threshold mengikuti model final.

  FR-021                              Post-processing hanya digunakan
                                      jika merupakan bagian dari pipeline
                                      final.

  FR-022                              Sistem menghasilkan segmentation
                                      output.
  -----------------------------------------------------------------------

### Model Configuration Rule

PRD ini tidak mengunci:

-   checkpoint/weights;
-   input size final;
-   epoch final;
-   threshold final;
-   preprocessing final;
-   post-processing final;
-   TTA;
-   inference parameters final.

Semua detail tersebut mengikuti model final setelah eksperimen selesai.

------------------------------------------------------------------------

# 12. Segmentation Output Requirements

  ID        Requirement
  --------- ---------------------------------------------------
  SEG-001   Original Image wajib tersedia.
  SEG-002   Binary Mask wajib tersedia.
  SEG-003   Segmentation Overlay wajib tersedia.
  SEG-004   Visualisasi harus berasal dari input yang sama.
  SEG-005   UI harus membedakan input image dan model output.

------------------------------------------------------------------------

# 13. Explainable AI Requirements

## 13.1 Required Output

  -----------------------------------------------------------------------
  ID                                  Requirement
  ----------------------------------- -----------------------------------
  XAI-001                             Grad-CAM wajib tersedia.

  XAI-002                             Grad-CAM Heatmap wajib tersedia.

  XAI-003                             Grad-CAM Overlay wajib tersedia.

  XAI-004                             Grad-CAM harus berasal dari model
                                      yang digunakan untuk inference.

  XAI-005                             Sistem menyediakan penjelasan
                                      singkat mengenai visualisasi.

  XAI-006                             Penjelasan harus
                                      deterministic/model-derived.

  XAI-007                             Sistem tidak menggunakan LLM untuk
                                      XAI.

  XAI-008                             Sistem tidak menganggap Grad-CAM
                                      sebagai ground truth.

  XAI-009                             Sistem tidak menganggap Grad-CAM
                                      sebagai diagnosis.
  -----------------------------------------------------------------------

## 13.2 XAI Concept

``` text
Original Image
      ↓
U-Net + ResNet50
      ↓
Model Output
      ↓
Grad-CAM
      ↓
Heatmap
      ↓
Overlay
      ↓
Model-derived Explanation
```

## 13.3 Implementation Note

Detail teknis seperti:

-   target layer;
-   activation extraction;
-   gradient handling;
-   normalization;
-   resize;
-   blending;

ditentukan pada `FunctionalSpecification.md` berdasarkan arsitektur
model final.

PRD hanya mengunci tujuan dan output XAI.

------------------------------------------------------------------------

# 14. Model Analysis Requirements

## 14.1 Allowed Information

Jika tersedia secara valid:

-   model result status;
-   segmentation area;
-   area ratio;
-   bounding width;
-   bounding height;
-   model/version;
-   confidence/probability yang benar-benar berasal dari pipeline final.

## 14.2 Confidence / Probability Rule

Confidence/probability adalah **optional**.

Sistem tidak boleh:

-   membuat angka confidence;
-   membuat angka random;
-   menggunakan hard-coded confidence;
-   mengubah Dice menjadi confidence;
-   mengubah IoU menjadi confidence;
-   mengubah area ratio menjadi confidence;
-   menyebut probability sebagai confidence tanpa definisi yang tepat.

Jika tidak tersedia:

``` text
Hide field
```

atau:

``` text
Not available
```

## 14.3 Segmentation Area

Area segmentasi dapat dihitung dari binary mask dalam satuan pixel.

## 14.4 Area Ratio

Area ratio dapat dihitung sebagai proporsi pixel segmentasi terhadap
area citra.

## 14.5 Bounding Dimensions

Bounding width dan height dapat dihitung dari segmentation mask jika
dibutuhkan.

## 14.6 Physical Size

Ukuran fisik seperti millimeter tidak boleh ditampilkan kecuali terdapat
physical scale yang valid.

------------------------------------------------------------------------

# 15. Research Metrics vs Product Output

Metrik penelitian:

-   Dice;
-   IoU;
-   Accuracy;
-   Precision;
-   Recall;
-   HD95;

digunakan untuk evaluasi model penelitian.

Metrik tersebut:

-   bukan otomatis confidence;
-   bukan otomatis output per-image;
-   bukan otomatis ditampilkan kepada user pada result page.

Jika suatu saat research metrics ditampilkan pada halaman tertentu,
konteks dan sumber nilainya harus jelas.

------------------------------------------------------------------------

# 16. Analysis Summary

Analysis Summary adalah ringkasan **deterministic/model-derived**, bukan
generative AI.

Summary dapat menggunakan:

-   segmentation status;
-   segmentation area;
-   area ratio;
-   bounding information;
-   Grad-CAM information;
-   model/version;
-   aturan/template yang telah ditentukan.

Contoh pola:

> Model menghasilkan area segmentasi pada citra. Area yang tersegmentasi
> memiliki luas sebesar X pixel atau X% dari area citra. Visualisasi
> Grad-CAM menunjukkan area yang berkontribusi terhadap output model.

Kalimat aktual harus disesuaikan dengan data yang benar-benar tersedia.

Summary tidak boleh:

-   menyatakan diagnosis kanker;
-   menyatakan malignansi;
-   menyatakan kepastian klinis;
-   memberikan treatment;
-   memberikan rekomendasi tindakan medis.

------------------------------------------------------------------------

# 17. Result Page Requirements

Halaman hasil harus menyediakan informasi berikut:

``` text
Result Header
      ↓
AI Result Status
      ↓
Original Image
      ↓
Binary Mask
      ↓
Segmentation Overlay
      ↓
Grad-CAM Heatmap
      ↓
Grad-CAM Overlay
      ↓
Model Analysis
      ↓
Explainable AI
      ↓
Analysis Summary
      ↓
Clinical Disclaimer
      ↓
Save Result / New Analysis
```

Urutan visual dapat disesuaikan pada `StyleGuide.md`, tetapi output inti
tidak boleh dihilangkan.

------------------------------------------------------------------------

# 18. History Requirements

History menyimpan hasil analisis milik user.

Record dapat menyimpan:

-   Original Image;
-   Binary Mask;
-   Segmentation Overlay;
-   Grad-CAM Heatmap;
-   Grad-CAM Overlay;
-   Model Analysis;
-   Analysis Summary;
-   Model/version;
-   timestamp.

History wajib memiliki isolasi data berdasarkan user/account.

------------------------------------------------------------------------

# 19. Non-Functional Requirements

## 19.1 Usability

-   UI harus profesional.
-   UI harus modern dan minimalis.
-   Visual identity harus sesuai konteks medical AI.
-   Medical image menjadi fokus utama.
-   Label output harus jelas.
-   Loading state harus jelas.
-   Error state harus jelas.
-   AI output dan clinical disclaimer harus mudah dibedakan.

## 19.2 Performance

-   Inference memiliki loading state.
-   Sistem tidak boleh menampilkan progress percentage palsu.
-   Waktu inference harus berdasarkan proses aktual.
-   Optimasi tidak boleh diam-diam mengubah model/pipeline.

## 19.3 Reliability

Sistem harus menangani:

-   invalid upload;
-   upload failure;
-   inference failure;
-   result loading failure;
-   history loading failure;
-   optional output unavailable.

## 19.4 Security

-   Authentication wajib pada area privat.
-   User hanya dapat mengakses data yang berwenang.
-   File upload harus divalidasi.
-   Endpoint inference dan history harus memiliki access control.
-   Credential tidak boleh disimpan secara tidak aman.

## 19.5 Maintainability

-   Model configuration dipisahkan dari UI.
-   Model version dapat ditelusuri.
-   Model-dependent parameters tidak tersebar sebagai hard-coded values.
-   Model final dapat menggantikan model eksperimen tanpa mengubah
    product flow.
-   UI tidak bergantung pada nilai eksperimen sementara.

## 19.6 Responsive Design

Aplikasi harus tetap usable pada:

-   desktop;
-   tablet;
-   layar yang lebih kecil jika memungkinkan.

Visualisasi dapat ditumpuk secara vertikal pada layar sempit tanpa
menghilangkan informasi inti.

------------------------------------------------------------------------

# 20. UX / Product Principles

## Principle 1 --- One Purpose

PIXEL-T hanya memiliki satu tujuan utama:

> Membantu tenaga medis menganalisis area polip pada citra kolonoskopi
> melalui segmentasi AI dan Explainable AI.

## Principle 2 --- One Main Model

Model utama:

> U-Net + ResNet50

Tidak ada model selector atau multi-model comparison.

## Principle 3 --- Explain, Don't Diagnose

Sistem menjelaskan output/fokus model, bukan diagnosis.

## Principle 4 --- Image First

Citra dan visualisasi AI menjadi fokus halaman analisis.

## Principle 5 --- Model-derived Information

Informasi analisis harus dapat ditelusuri ke output model atau
perhitungan valid.

## Principle 6 --- No Fake Data

Tidak boleh ada nilai placeholder yang ditampilkan seolah-olah merupakan
hasil nyata.

## Principle 7 --- Optional Means Optional

Jika output tidak tersedia, field tidak dipaksakan.

## Principle 8 --- No LLM for XAI

XAI dan Analysis Summary tidak menggunakan LLM.

## Principle 9 --- Model Can Change

Parameter eksperimen dapat berubah sampai model final ditentukan.

## Principle 10 --- Do Not Expand Scope

AI coding agent tidak boleh menambahkan fitur hanya karena dianggap
berguna.

------------------------------------------------------------------------

# 21. Medical Boundary

PIXEL-T harus selalu diposisikan sebagai:

> **Alat bantu analisis citra kolonoskopi berbasis AI untuk segmentasi
> polip dan Explainable AI.**

PIXEL-T bukan:

-   sistem diagnosis;
-   sistem diagnosis kanker;
-   sistem klasifikasi malignansi;
-   sistem rekomendasi terapi;
-   pengganti dokter.

## Clinical Disclaimer

> **Hasil yang ditampilkan merupakan keluaran analisis model AI dan
> ditujukan sebagai informasi pendukung bagi tenaga medis. Hasil ini
> tidak dimaksudkan sebagai diagnosis medis atau pengganti penilaian
> profesional tenaga medis.**

------------------------------------------------------------------------

# 22. AI Coding Agent Guardrails

Bagian ini bersifat wajib.

## 22.1 Agent Boleh

AI coding agent boleh:

-   membuat UI sesuai PRD;
-   membuat backend/API sesuai workflow;
-   menghubungkan model final;
-   melakukan preprocessing sesuai model final;
-   melakukan segmentation inference;
-   menghitung statistik dari segmentation mask;
-   membuat visualisasi;
-   membuat Grad-CAM sesuai model final;
-   membuat deterministic Analysis Summary;
-   membuat authentication;
-   membuat History;
-   menangani error/loading state.

## 22.2 Agent Tidak Boleh

Tanpa requirement baru yang eksplisit, agent tidak boleh:

1.  menambahkan model AI kedua;
2.  menambahkan cancer classifier;
3.  menambahkan malignancy prediction;
4.  menambahkan diagnosis otomatis;
5.  menambahkan chatbot;
6.  menggunakan LLM untuk XAI;
7.  membuat confidence score;
8.  membuat clinical recommendation;
9.  membuat treatment recommendation;
10. mengubah target user menjadi pasien;
11. membuat model selector;
12. membuat multi-model comparison;
13. mengubah segmentation menjadi diagnosis;
14. menganggap Grad-CAM sebagai ground truth;
15. menggunakan research metrics sebagai confidence per-image;
16. menambahkan fitur di luar scope;
17. menampilkan data buatan sebagai hasil model.

## 22.3 Ambiguous Requirement Rule

Jika requirement belum jelas:

> **Jangan menebak.**

Agent harus:

-   memilih implementasi minimal yang tetap sesuai PRD; atau
-   menandai bagian tersebut sebagai TODO/decision point.

------------------------------------------------------------------------

# 23. Current Experimental Model Information

Informasi eksperimen saat ini dicatat sebagai konteks penelitian dan
**bukan requirement final**.

Current experiment:

-   Input Size: 512 × 512
-   Best Epoch: 123
-   Validation Dice (EMA): 0.9488
-   Best Threshold: 0.65
-   Full Test Dice: 0.9475
-   Full Test IoU: 0.9092
-   Full Test Accuracy: 0.9919
-   Full Test Precision: 0.9557
-   Full Test Recall: 0.9704
-   Full Test HD95: 15.2274

**Status: EXPERIMENTAL / NOT LOCKED**

Nilai dapat berubah karena model masih dapat mengalami training, tuning,
evaluasi, atau finalisasi.

Metrik eksperimen tersebut tidak boleh di-hard-code ke UI sebagai hasil
model final.

------------------------------------------------------------------------

# 24. Model Finalization Contract

Sebelum deployment, model final harus memiliki definisi yang jelas
untuk:

-   final checkpoint;
-   model architecture;
-   input size;
-   preprocessing;
-   threshold;
-   post-processing;
-   TTA jika digunakan;
-   Grad-CAM target layer;
-   output/probability definition jika tersedia;
-   model version.

Setelah finalisasi, detail teknis tersebut menjadi input untuk
`FunctionalSpecification.md`.

Perubahan pada model eksperimen tidak mengubah tujuan produk selama
masih berada dalam scope model utama U-Net + ResNet50.

------------------------------------------------------------------------

# 25. Success Criteria

MVP PIXEL-T memenuhi PRD apabila:

1.  User dapat Register/Login.
2.  User dapat upload citra kolonoskopi.
3.  Sistem melakukan inference.
4.  Sistem menghasilkan segmentation mask.
5.  Original Image tersedia.
6.  Binary Mask tersedia.
7.  Segmentation Overlay tersedia.
8.  Grad-CAM Heatmap tersedia.
9.  Grad-CAM Overlay tersedia.
10. Model Analysis tersedia jika data valid tersedia.
11. Analysis Summary tersedia dan deterministic/model-derived.
12. Tidak ada LLM untuk XAI.
13. Tidak ada confidence buatan.
14. User dapat menyimpan hasil.
15. User dapat melihat History.
16. User dapat membuka detail hasil.
17. User dapat menghapus history sesuai authorization.
18. Sistem tidak memberikan diagnosis atau rekomendasi klinis.
19. Optional output ditangani tanpa data palsu.
20. Model final dapat diganti tanpa mengubah tujuan utama product flow.

------------------------------------------------------------------------

# 26. Change Control

Status dokumen:

> **FINAL / LOCKED**

PRD ini menjadi source of truth untuk produk PIXEL-T.

Perubahan terhadap:

-   tujuan produk;
-   target user;
-   model utama;
-   output utama;
-   XAI;
-   scope;
-   medical boundary;
-   user flow;

harus dilakukan secara eksplisit dan dicatat sebagai perubahan
requirement.

Dokumen turunan:

``` text
PRD.md
   ↓
StyleGuide.md
   ↓
FunctionalSpecification.md
   ↓
Task.md
```

Jika dokumen turunan bertentangan dengan PRD, **PRD menjadi acuan
utama**.

Perubahan parameter model penelitian seperti checkpoint, threshold,
input size, atau preprocessing tidak otomatis dianggap sebagai perubahan
PRD selama tidak mengubah product scope.

------------------------------------------------------------------------

# 27. Final Product Statement

> **PIXEL-T adalah aplikasi web berbasis AI yang membantu dokter atau
> tenaga medis menganalisis citra kolonoskopi melalui segmentasi polip
> menggunakan U-Net + ResNet50 dan Explainable AI berbasis Grad-CAM.
> PIXEL-T menampilkan Original Image, Binary Mask, Segmentation Overlay,
> Grad-CAM Heatmap, Grad-CAM Overlay, serta informasi analisis yang
> dapat diturunkan secara valid dari output model. Sistem menyediakan
> ringkasan analisis deterministic/model-derived dan penyimpanan hasil
> melalui History. PIXEL-T merupakan alat bantu analisis dan tidak
> dimaksudkan sebagai diagnosis medis, klasifikasi malignansi,
> rekomendasi pengobatan, atau pengganti keputusan profesional tenaga
> medis.**
