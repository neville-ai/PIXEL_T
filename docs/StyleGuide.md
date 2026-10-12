# StyleGuide.md — PIXEL-T

**Status:** FINAL / LOCKED  
**Product:** PIXEL-T  
**Design Direction:** Clinical + Modern AI (Hybrid)  
**Theme:** Light + Dark, user-switchable  
**Primary Palette:** Deep Medical Navy + Medical Teal  
**Logo:** Belum tersedia; gunakan wordmark `PIXEL-T` sebagai identitas sementara  
**LUCIT:** Reference-level only, bukan template dan bukan source of truth

---

## 1. Tujuan Dokumen

StyleGuide ini merupakan **source of truth untuk desain UI/UX PIXEL-T** dan diturunkan dari PRD PIXEL-T yang telah dikunci.

Dokumen ini menentukan bagaimana kebutuhan produk diterjemahkan menjadi:

- visual identity,
- design tokens,
- typography,
- color system,
- component system,
- page layout,
- interaction states,
- medical-image presentation,
- Explainable AI presentation,
- responsive behavior,
- accessibility,
- terminology,
- serta batasan visual agar implementasi tetap konsisten.

AI coding agent **tidak boleh membuat keputusan desain utama di luar aturan dokumen ini tanpa alasan teknis yang jelas**.

PRD menentukan **apa yang harus dilakukan produk**.  
StyleGuide menentukan **bagaimana produk tersebut harus terlihat dan berinteraksi**.  
Functional Specification nantinya menentukan **bagaimana fitur tersebut diimplementasikan secara teknis**.

---

# 2. Product Design Identity

## 2.1 Design Direction

PIXEL-T menggunakan arah desain:

> **Clinical + Modern AI**

Karakter visual harus terasa seperti **clinical workstation yang dipadukan dengan teknologi AI modern**.

Desain harus:

- profesional,
- tenang,
- bersih,
- informatif,
- image-first,
- mudah dipahami tenaga medis,
- modern tetapi tidak futuristik berlebihan.

### Hindari

PIXEL-T tidak boleh terlihat seperti:

- dashboard gaming,
- aplikasi consumer health,
- SaaS marketing yang terlalu dekoratif,
- software rumah sakit lama yang terlalu padat,
- AI dashboard futuristik dengan neon/glow berlebihan,
- aplikasi dengan terlalu banyak gradient,
- aplikasi yang menampilkan AI seolah-olah memiliki kepastian klinis absolut.

---

# 3. Design Principles

## 3.1 Clinical First

Informasi medis dan hasil analisis harus selalu lebih penting daripada dekorasi visual.

## 3.2 Image First

Citra kolonoskopi merupakan pusat pengalaman pada halaman analisis.

Urutan prioritas visual:

1. Original Image
2. Segmentation Overlay
3. Binary Mask
4. Grad-CAM
5. Model Analysis
6. XAI Explanation
7. Analysis Summary
8. Clinical Disclaimer

## 3.3 Explainability First

Grad-CAM merupakan fitur inti, bukan ornamen tambahan.

Pengguna harus dapat memahami:

- citra yang dianalisis,
- area hasil segmentasi,
- area yang menjadi fokus/aktivasi model,
- hubungan antara hasil segmentasi dan visualisasi XAI.

## 3.4 Minimal but Informative

Gunakan elemen visual secukupnya. Jangan memenuhi layar dengan card, badge, chart, atau statistik yang tidak dibutuhkan.

## 3.5 Professional AI

AI harus terlihat canggih melalui **kejelasan hasil dan kualitas visualisasi**, bukan melalui efek visual berlebihan.

## 3.6 Medical Integrity

UI tidak boleh mengubah persepsi terhadap citra atau output model secara menyesatkan.

---

# 4. Brand Identity

## 4.1 Brand Name

Gunakan:

> **PIXEL-T**

Untuk sementara, gunakan wordmark teks `PIXEL-T` sampai logo resmi tersedia.

## 4.2 Brand Personality

PIXEL-T harus terasa:

- trustworthy,
- precise,
- clinical,
- intelligent,
- modern,
- calm,
- professional.

Jangan menggunakan bahasa visual yang terasa:

- playful,
- aggressive,
- sensational,
- entertainment-oriented.

---

# 5. Color System

## 5.1 Primary — Deep Medical Navy

| Token | Hex | Penggunaan |
|---|---|---|
| `primary-900` | `#0F3D56` | Primary action, header emphasis |
| `primary-800` | `#164B65` | Hover / active |
| `primary-700` | `#1C5B76` | Secondary emphasis |
| `primary-100` | `#EAF4F8` | Soft background |
| `primary-50` | `#F4FAFC` | Very light surface |

Deep Medical Navy adalah warna utama identitas PIXEL-T.

## 5.2 Accent — Medical Teal

| Token | Hex | Penggunaan |
|---|---|---|
| `accent-700` | `#147F80` | Dark accent |
| `accent-600` | `#18A6A6` | Main accent |
| `accent-500` | `#29B8B8` | Highlight |
| `accent-100` | `#E6F7F6` | Accent surface |
| `accent-50` | `#F2FBFA` | Very light accent surface |

Teal digunakan sebagai accent, bukan sebagai pengganti semua warna primary.

## 5.3 Neutral

| Token | Hex | Penggunaan |
|---|---|---|
| `neutral-950` | `#0F1F2A` | Strongest text |
| `neutral-900` | `#172B3A` | Primary text |
| `neutral-700` | `#334A59` | Strong secondary text |
| `neutral-600` | `#64748B` | Secondary text |
| `neutral-400` | `#94A3B8` | Placeholder / muted |
| `neutral-300` | `#CBD5E1` | Disabled / subtle border |
| `neutral-200` | `#D9E4EA` | Default border |
| `neutral-100` | `#EAF0F3` | Subtle surface |
| `neutral-50` | `#F7FAFC` | App background |
| `white` | `#FFFFFF` | Surface |

## 5.4 Semantic Colors

| Token | Hex | Penggunaan |
|---|---|---|
| `success` | `#2E8B70` | Completed / success |
| `warning` | `#D99A2B` | Warning |
| `error` | `#C94A4A` | Error / destructive |
| `info` | `#2878A8` | Informational |

Semantic colors hanya digunakan ketika memiliki makna semantik.

## 5.5 Medical Visualization Colors

Warna brand/UI **dipisahkan** dari warna visualisasi medis.

Segmentation dan Grad-CAM harus memiliki visual language yang dapat dibedakan.

Aturan:

- Segmentation Overlay harus jelas membedakan area tersegmentasi dari citra asli.
- Binary Mask harus sangat mudah dibedakan dari citra asli.
- Grad-CAM harus tetap menggunakan karakteristik visual heatmap.
- Grad-CAM tidak boleh dipaksa mengikuti warna navy/teal brand.
- Warna visualisasi tidak boleh digunakan untuk menyiratkan diagnosis klinis.
- Detail implementasi warna final untuk mask/heatmap ditetapkan pada Functional Specification setelah pipeline model final.

---

# 6. Theme System

PIXEL-T mendukung:

- Light Mode
- Dark Mode

Pengguna dapat berpindah theme.

Theme tidak boleh mengubah:

- model,
- hasil segmentasi,
- hasil Grad-CAM,
- threshold,
- nilai model,
- data analisis.

## 6.1 Light Theme

| Role | Value |
|---|---|
| App Background | `#F7FAFC` |
| Surface | `#FFFFFF` |
| Primary Text | `#172B3A` |
| Secondary Text | `#64748B` |
| Border | `#D9E4EA` |
| Primary Action | `#0F3D56` |
| Primary Hover | `#164B65` |
| Accent | `#18A6A6` |

## 6.2 Dark Theme

| Role | Value |
|---|---|
| App Background | `#0B1720` |
| Surface | `#10232E` |
| Elevated Surface | `#142B37` |
| Primary Text | `#EAF4F8` |
| Secondary Text | `#A9BBC5` |
| Border | `#29404C` |
| Primary | `#2C6C88` |
| Accent | `#29B8B8` |
| Accent Surface | `#123A3B` |

Jangan menggunakan pure black sebagai default background dark mode.

---

# 7. Typography

## 7.1 Font

Gunakan:

> **Inter, sans-serif**

Jika Inter tidak tersedia, gunakan fallback sans-serif yang konsisten.

## 7.2 Type Scale

| Level | Size | Weight | Penggunaan |
|---|---:|---:|---|
| Display | 32–40px | 700 | Hero / major heading |
| H1 | 28–32px | 700 | Page title |
| H2 | 22–26px | 600–700 | Section |
| H3 | 18–20px | 600 | Card / subsection |
| Body Large | 16px | 400 | Intro / important body |
| Body | 14–16px | 400 | Main content |
| Label | 13–14px | 500–600 | Form / metadata |
| Caption | 12px | 400–500 | Supporting text |

## 7.3 Typography Rules

- Heading harus singkat.
- Jangan menggunakan ALL CAPS untuk paragraf.
- Gunakan weight untuk hierarchy, bukan terlalu banyak warna.
- Jangan menggunakan terlalu banyak font size dalam satu halaman.

---

# 8. Spacing System

Gunakan prinsip **8-point spacing**.

Token dasar:

```text
4px
8px
12px
16px
24px
32px
40px
48px
64px
```

Prioritaskan spacing konsisten daripada nilai arbitrer.

Contoh:

- icon ↔ text: 8px
- input internal padding: 12–16px
- card padding: 16–24px
- section gap: 24–32px
- major section gap: 40–48px

---

# 9. Border Radius

| Token | Value | Penggunaan |
|---|---:|---|
| Small | 6px | Small controls |
| Default | 8px | Input / button |
| Card | 12px | Standard card |
| Large | 12–16px | Image container |
| Modal | 16px | Modal/dialog |
| Pill | 999px | Badge/status |

Radius harus terasa modern tetapi tetap profesional.

---

# 10. Elevation & Shadow

Gunakan shadow secara halus.

### Level 1 — Subtle

Untuk card normal.

### Level 2 — Elevated

Untuk dropdown, popover, important card.

### Level 3 — Overlay

Untuk modal/dialog.

Jangan menggunakan shadow besar, glow, atau neon effect sebagai dekorasi utama.

---

# 11. Layout System

## 11.1 Global Container

Desktop:

- horizontal padding sekitar 24–40px.

Mobile:

- horizontal padding sekitar 16px.

Content harus memiliki maximum readable width, tetapi halaman analisis boleh menggunakan area lebih lebar karena citra membutuhkan ruang.

## 11.2 Visual Hierarchy

Setiap halaman harus memiliki:

1. Page context
2. Primary action/content
3. Supporting information
4. Secondary action

Jangan membuat semua elemen terlihat sama penting.

---

# 12. Navigation

Primary navigation:

- Dashboard
- New Analysis
- History

Secondary user actions:

- Profile / account
- Theme switcher
- Logout

Navigation harus sederhana dan ringan.

Tidak perlu sidebar yang terlalu kompleks kecuali kebutuhan implementasi benar-benar memerlukannya.

---

# 13. Header

Header harus memuat:

- PIXEL-T identity
- current context/navigation
- user access
- theme switcher

Karakter:

- lightweight,
- clean,
- tidak terlalu tinggi,
- tidak mengambil terlalu banyak vertical space.

---

# 14. Dashboard

Dashboard bukan admin analytics dashboard.

Fokus:

- welcome/context,
- akses cepat ke New Analysis,
- recent analyses,
- akses ke History.

Primary CTA:

> **New Analysis**

Dashboard tidak perlu dipenuhi chart atau statistik yang tidak mendukung workflow utama.

---

# 15. Authentication

Authentication terdiri dari:

- Login
- Register

Form harus:

- sederhana,
- jelas,
- memiliki label,
- memiliki validation state,
- memiliki focus state,
- memiliki error message yang actionable.

Jangan menambahkan field yang tidak diperlukan oleh kebutuhan produk.

---

# 16. New Analysis / Upload Flow

Flow:

```text
Select Image
    ↓
Preview
    ↓
Validation
    ↓
Analyze
```

## Upload UI

Dapat menggunakan:

- drag & drop,
- file picker.

Setelah file dipilih:

- tampilkan preview,
- tampilkan filename jika relevan,
- berikan opsi replace/remove,
- tampilkan validation error bila tidak valid.

Jangan menggunakan ilustrasi dekoratif besar yang mengambil perhatian dari image preview.

---

# 17. Analysis Page

Halaman Analysis adalah **halaman terpenting PIXEL-T**.

## 17.1 Visual Priority

Urutan prioritas:

```text
Original Image
        ↓
Segmentation Overlay
        ↓
Binary Mask
        ↓
Grad-CAM
        ↓
Model Analysis
        ↓
XAI Explanation
        ↓
Analysis Summary
        ↓
Clinical Disclaimer
```

## 17.2 Desktop Layout

Layout utama yang direkomendasikan:

```text
┌───────────────────────┬───────────────────────┐
│ Original Image        │ Segmentation Overlay  │
├───────────────────────┼───────────────────────┤
│ Binary Mask           │ Grad-CAM Overlay      │
└───────────────────────┴───────────────────────┘

┌───────────────────────────────────────────────┐
│ Model Analysis                               │
└───────────────────────────────────────────────┘

┌───────────────────────────────────────────────┐
│ XAI / Grad-CAM Explanation                   │
└───────────────────────────────────────────────┘

┌───────────────────────────────────────────────┐
│ Analysis Summary                             │
└───────────────────────────────────────────────┘

Clinical Disclaimer
```

Heatmap Grad-CAM dapat ditampilkan sebagai visual tersendiri jika dibutuhkan oleh implementasi final.

---

# 18. Image Result Cards

Setiap image card harus memiliki:

1. Title
2. Optional short description
3. Image
4. Optional metadata/action

Contoh title:

- Original Image
- Segmentation Overlay
- Binary Mask
- Grad-CAM Heatmap
- Grad-CAM Overlay

## Image Card Rules

- gunakan aspect ratio yang tidak merusak citra,
- jangan melakukan crop yang menghilangkan area penting,
- jangan melakukan stretching yang menyebabkan distorsi,
- gunakan object-fit yang sesuai,
- sediakan zoom/viewer bila diperlukan,
- pertahankan spatial relationship terhadap original image.

---

# 19. Original Image

Original Image harus:

- mempertahankan visual asli,
- tidak diberi filter,
- tidak diberi tint,
- tidak diberi overlay,
- tidak diberi decorative color grading.

Tujuannya adalah menyediakan reference visual yang jujur.

---

# 20. Segmentation Overlay

Segmentation Overlay harus:

- mempertahankan original image sebagai konteks,
- menunjukkan area yang dihasilkan model,
- memiliki contrast yang cukup,
- tidak terlihat seperti Grad-CAM,
- tidak memberikan kesan certainty klinis.

Overlay harus tetap memungkinkan pengguna melihat struktur citra asli.

---

# 21. Binary Mask

Binary Mask merupakan representasi hasil segmentasi.

Harus:

- jelas foreground/background,
- sederhana,
- tidak bercampur dengan heatmap,
- mudah dibandingkan dengan original image.

Jangan menambahkan efek visual yang membuat binary mask terlihat seperti diagnosis.

---

# 22. Grad-CAM

Grad-CAM merupakan bagian inti XAI PIXEL-T.

UI harus membedakan:

- **Grad-CAM Heatmap**
- **Grad-CAM Overlay**

Heatmap:

- fokus pada visualisasi activation/focus model,
- menggunakan karakteristik heatmap.

Overlay:

- menggabungkan heatmap dengan original image,
- tetap mempertahankan konteks citra.

Grad-CAM harus dijelaskan sebagai **visualisasi fokus/aktivasi model**, bukan bukti diagnosis.

---

# 23. Model Analysis

Model Analysis menggunakan card yang ringkas.

Informasi yang dapat ditampilkan jika tersedia dan valid:

- Segmentation Status
- Area
- Area Ratio
- Bounding Width / Height
- Model Version
- Model Output Information yang memang tersedia

## Confidence / Probability

Confidence atau probability **tidak boleh dibuat-buat**.

Jika pipeline final tidak menyediakan definisi confidence/probability yang valid:

- jangan tampilkan,
- atau tampilkan sebagai unavailable hanya jika dibutuhkan untuk konteks.

Metrik penelitian seperti:

- Dice,
- IoU,
- Accuracy,
- Precision,
- Recall,
- HD95

bukan otomatis merupakan confidence per-image dan tidak boleh dipresentasikan sebagai confidence.

## Physical Measurement

Jangan menampilkan ukuran fisik dalam mm apabila tidak tersedia physical scale yang valid.

---

# 24. XAI Explanation

Bagian XAI harus memiliki:

### Heading

> Explainable AI

### Visual

Grad-CAM reference.

### Explanation

Gunakan penjelasan singkat dan model-derived.

Contoh gaya:

> “Grad-CAM menunjukkan area citra yang memperoleh aktivasi relatif lebih tinggi dari model pada proses analisis.”

Bahasa harus:

- informatif,
- singkat,
- non-diagnostic,
- tidak menyatakan sebab klinis yang tidak dihasilkan model.

## Tidak boleh

- menggunakan LLM untuk menghasilkan penjelasan XAI,
- membuat narasi klinis dari heatmap,
- menyatakan bahwa area tersebut pasti polip berdasarkan Grad-CAM,
- membuat klaim diagnosis.

---

# 25. Analysis Summary

Analysis Summary bukan diagnosis report.

Tujuannya adalah merangkum output sistem.

Contoh struktur:

```text
Model:
U-Net + ResNet50

Segmentation:
Area tersegmentasi tersedia

Explainability:
Grad-CAM tersedia

Summary:
Model menghasilkan segmentasi pada area citra yang ditampilkan,
disertai visualisasi Grad-CAM untuk membantu memahami fokus
aktivasi model.
```

Gunakan istilah:

> model output / analysis result / segmented area / detected / not detected

Hindari:

> confirmed polyp / cancer detected / diagnosis confirmed

---

# 26. Clinical Disclaimer

Disclaimer harus terlihat jelas pada result page.

Gunakan:

> **Hasil yang ditampilkan merupakan keluaran analisis model AI dan ditujukan sebagai informasi pendukung bagi tenaga medis. Hasil ini tidak dimaksudkan sebagai diagnosis medis atau pengganti penilaian profesional tenaga medis.**

Disclaimer tidak boleh disembunyikan di tempat yang sulit ditemukan.

---

# 27. History

History menampilkan analisis yang telah disimpan.

Setiap item dapat memuat:

- thumbnail,
- date/time,
- status,
- metadata singkat,
- view,
- delete.

History harus tetap sederhana.

## History Detail

Saat pengguna membuka history:

- pertahankan visual hierarchy result page,
- tampilkan hasil analisis yang sama,
- jangan mengubah output model.

## Delete

Delete harus memiliki confirmation dialog.

---

# 28. Component System

Komponen bersama minimal:

```text
Button
Input
Select
Card
Badge
Modal
Toast
Navigation
Header
ImageViewer
ResultCard
LoadingState
ErrorState
EmptyState
ThemeSwitcher
```

Semua komponen harus:

- memiliki state yang konsisten,
- menggunakan design tokens,
- mendukung Light/Dark jika relevan,
- memiliki accessibility state.

---

# 29. Button Rules

## Primary

Gunakan Deep Medical Navy.

Untuk action utama:

> Analyze Image  
> New Analysis  
> Save Result

## Secondary

Gunakan neutral/outlined treatment.

## Destructive

Gunakan semantic error hanya untuk action destructive seperti delete.

Jangan menggunakan warna merah sebagai primary brand/action.

---

# 30. Form Rules

Input harus memiliki:

- label,
- placeholder jika benar-benar diperlukan,
- focus state,
- error state,
- disabled state,
- helper text bila diperlukan.

Jangan menggunakan placeholder sebagai satu-satunya label.

---

# 31. Status Badge

Status yang dapat digunakan:

- Ready
- Processing
- Completed
- Error
- Saved

Status tidak boleh hanya dibedakan melalui warna.

Gunakan kombinasi:

- warna,
- icon,
- text.

---

# 32. Loading State

Gunakan:

- spinner,
- skeleton,
- atau progress indicator jika progress benar-benar tersedia.

Untuk analisis AI, contoh copy:

> Analyzing image...

atau:

> Processing segmentation and Explainable AI...

Jangan menampilkan persentase progres palsu.

---

# 33. Error State

Error harus:

- singkat,
- jelas,
- actionable.

Contoh:

> Image could not be analyzed. Please check the file and try again.

Jangan menampilkan stack trace atau technical error detail kepada pengguna umum.

---

# 34. Empty State

Empty state harus menjelaskan:

1. apa yang belum tersedia,
2. mengapa,
3. tindakan berikutnya.

Contoh:

> No analysis history yet.  
> Start a new analysis to see your results here.

---

# 35. Interaction Rules

## Hover

Hover harus subtle.

## Focus

Focus state harus jelas untuk keyboard navigation.

## Active

Active state harus menggunakan accent/primary yang konsisten.

## Disabled

Disabled harus terlihat non-interactive tetapi tetap readable.

## Modal

Modal hanya digunakan untuk:

- confirmation,
- important contextual information,
- focused actions.

Jangan menggunakan modal untuk seluruh workflow analisis.

---

# 36. Image Interaction

Image viewer dapat mendukung:

- zoom,
- fit-to-container,
- reset zoom.

Jika image diperbesar:

- jangan mengubah pixel content,
- jangan mengubah mask,
- jangan mengubah heatmap,
- jangan melakukan visual enhancement yang tidak ditentukan.

---

# 37. Responsive Design

## Desktop

Gunakan layout dua kolom untuk image comparison jika ruang mencukupi.

## Tablet

Gunakan dua kolom hanya jika setiap image tetap readable.

Jika tidak:

- stack secara bertahap.

## Mobile

Urutan:

```text
Original Image
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
XAI Explanation
↓
Analysis Summary
↓
Disclaimer
```

Jangan memaksakan dua image berdampingan pada layar sempit jika menyebabkan image terlalu kecil.

---

# 38. Accessibility

PIXEL-T harus:

- memiliki contrast yang cukup,
- memiliki visible focus state,
- menggunakan semantic HTML,
- menyediakan label yang jelas,
- menyediakan alt text untuk image,
- tidak mengandalkan warna saja untuk status,
- mendukung keyboard navigation pada interactive elements.

Untuk hasil visual:

- title harus menjelaskan jenis visualisasi,
- jangan hanya menggunakan warna sebagai legenda.

---

# 39. Animation

Animation harus:

- subtle,
- cepat,
- membantu memahami perubahan state.

Gunakan animation untuk:

- loading,
- transition,
- modal,
- theme switch,
- feedback.

Hindari:

- animation dekoratif berlebihan,
- continuous floating elements,
- excessive glow,
- flashy transitions.

---

# 40. Iconography

Gunakan icon set yang konsisten.

Karakter icon:

- simple,
- clean,
- outline-oriented,
- professional.

Jangan mencampurkan banyak gaya icon.

Icon tidak boleh menggantikan label penting.

---

# 41. Data Visualization

PIXEL-T tidak membutuhkan dashboard chart-heavy.

Chart hanya boleh digunakan jika:

- memiliki tujuan jelas,
- membantu memahami output,
- datanya benar-benar tersedia.

Jangan menambahkan:

- AI score chart,
- confidence gauge,
- risk meter,
- diagnostic probability visualization

jika pipeline tidak menyediakan data yang valid.

---

# 42. Medical Image Integrity

Ini merupakan aturan wajib.

UI **tidak boleh**:

- memberikan decorative filter,
- memberikan arbitrary color grading,
- melakukan crop yang menutupi area penting,
- melakukan stretching,
- membuat citra terlihat lebih abnormal,
- menambahkan visual effect untuk dramatisasi,
- mengubah hasil model untuk tujuan estetika.

Visualisasi harus membantu interpretasi, bukan memanipulasi persepsi.

---

# 43. Model Output Integrity

UI **tidak boleh** membuat output AI terlihat lebih pasti daripada data/model sebenarnya.

Dilarang:

- fake confidence,
- fake probability,
- fake diagnosis,
- fake medical measurement,
- fake model explanation,
- fake progress,
- clinical recommendation yang tidak berasal dari pipeline.

Jika data tidak tersedia:

> jangan dibuat-buat.

Jika fitur optional tidak tersedia:

- sembunyikan, atau
- tampilkan “Not available” bila konteks membutuhkan transparansi.

---

# 44. Terminology

## Preferred

Gunakan:

- AI Analysis
- Analysis Result
- Segmentation Result
- Segmentation Mask
- Segmentation Overlay
- Binary Mask
- Grad-CAM
- Grad-CAM Heatmap
- Grad-CAM Overlay
- Model Analysis
- Model Output
- Analysis Summary
- Explainable AI
- Status: Detected (enum `detected`)
- Status: Not Detected (enum `not_detected`)

## Avoid

Hindari:

- Diagnosis
- Confirmed Polyp
- Cancer Detected
- Malignancy Probability
- Treatment Recommendation
- Clinical Decision
- Guaranteed Detection

---

# 45. Model-Specific UI Boundary

PIXEL-T menggunakan satu model utama:

> **U-Net + ResNet50**

UI tidak boleh menyediakan:

- model selector,
- multi-model comparison,
- model leaderboard,
- model switching untuk pengguna.

Model version dapat ditampilkan sebagai metadata bila relevan.

---

# 46. XAI Boundary

XAI PIXEL-T:

- menggunakan Grad-CAM,
- berasal dari model yang digunakan untuk inference,
- bersifat visual,
- deterministic/model-derived,
- tidak menggunakan LLM sebagai generator penjelasan.

UI tidak boleh menyediakan:

- chatbot XAI,
- conversational medical explanation,
- generative medical diagnosis,
- prompt box untuk meminta AI menafsirkan hasil.

---

# 47. LUCIT Reference Boundary

LUCIT hanya digunakan sebagai **reference-level source**.

Yang dapat dijadikan referensi:

- pola authentication,
- navigation,
- analysis workflow,
- history,
- image visualization,
- loading/error state,
- frontend/backend organization,
- segmentation workflow,
- Grad-CAM workflow.

Yang **tidak** boleh dibawa menjadi fitur PIXEL-T:

- branding LUCIT,
- warna LUCIT,
- cancer workflow,
- malignancy classification,
- chatbot,
- Gemini/LLM explanation,
- diagnosis workflow,
- model selector,
- fitur yang tidak ada dalam PRD PIXEL-T.

Prinsip:

> **Borrow interaction patterns, not product identity or scope.**

---

# 48. Design Do / Don't

## Do

- Prioritaskan citra.
- Gunakan navy + teal sebagai brand system.
- Gunakan white space.
- Gunakan card secara terukur.
- Pertahankan visual hierarchy.
- Gunakan Grad-CAM sebagai fitur inti.
- Gunakan terminology non-diagnostic.
- Tampilkan hanya data model yang benar-benar tersedia.
- Pastikan Light/Dark konsisten.
- Buat responsive behavior eksplisit.

## Don't

- Jangan membuat dashboard terlalu ramai.
- Jangan menggunakan neon AI aesthetic.
- Jangan menggunakan merah sebagai brand utama.
- Jangan membuat confidence palsu.
- Jangan membuat diagnosis.
- Jangan membuat clinical recommendation.
- Jangan menggunakan LLM untuk XAI.
- Jangan mengubah citra medis demi estetika.
- Jangan menambahkan fitur hanya karena terlihat bagus pada template.
- Jangan menyalin LUCIT secara visual.

---

# 49. Design Tokens Summary

Implementasi frontend harus menggunakan token terpusat, bukan hard-coded styling yang tersebar.

Contoh struktur:

```text
colors/
  primary/
  accent/
  neutral/
  semantic/
  visualization/

typography/
  font-family
  font-size
  font-weight
  line-height

spacing/
  4
  8
  12
  16
  24
  32
  40
  48
  64

radius/
  small
  default
  card
  large
  modal
  pill

shadow/
  subtle
  elevated
  overlay
```

Nilai visualisasi medis yang bersifat pipeline-dependent ditetapkan pada Functional Specification.

---

# 50. Page Design Acceptance Criteria

## Dashboard

- [ ] User memahami tujuan PIXEL-T.
- [ ] New Analysis menjadi primary entry point.
- [ ] Recent analysis tersedia jika ada.
- [ ] Tidak terlihat seperti admin dashboard.

## Authentication

- [ ] Login/Register sederhana.
- [ ] Validation jelas.
- [ ] Focus state tersedia.
- [ ] Tidak ada field tidak perlu.

## New Analysis

- [ ] Upload mudah dipahami.
- [ ] Preview tersedia.
- [ ] Validation jelas.
- [ ] User dapat replace/remove image.
- [ ] Primary Analyze action jelas.

## Analysis

- [ ] Original Image paling mudah ditemukan.
- [ ] Segmentation Overlay jelas.
- [ ] Binary Mask jelas.
- [ ] Grad-CAM jelas.
- [ ] Grad-CAM berbeda secara visual dari segmentation.
- [ ] Model Analysis ringkas.
- [ ] XAI explanation tersedia.
- [ ] Summary bukan diagnosis.
- [ ] Disclaimer terlihat.

## History

- [ ] Analisis tersimpan dapat ditemukan.
- [ ] Thumbnail/metadata cukup.
- [ ] Detail result konsisten dengan Analysis.
- [ ] Delete memiliki confirmation.

## Theme

- [ ] Light mode konsisten.
- [ ] Dark mode konsisten.
- [ ] Contrast tetap memadai.
- [ ] Theme tidak mengubah model output.

## Responsive

- [ ] Desktop nyaman.
- [ ] Tablet tetap readable.
- [ ] Mobile menggunakan stacked image-first flow.
- [ ] Tidak ada horizontal overflow yang tidak diperlukan.

---

# 51. AI Coding Agent Guardrails

AI coding agent harus mengikuti aturan berikut:

1. **PRD adalah sumber kebenaran untuk scope dan behavior produk.**
2. **StyleGuide ini adalah sumber kebenaran untuk UI/UX.**
3. Functional Specification adalah sumber kebenaran untuk detail teknis fitur.
4. Jangan menambahkan fitur baru hanya karena terlihat menarik.
5. Jangan mengubah terminology tanpa alasan yang jelas.
6. Jangan mengganti palette tanpa alasan desain yang kuat.
7. Jangan membuat fake data model.
8. Jangan membuat fake confidence.
9. Jangan membuat clinical claims.
10. Jangan menggunakan LLM untuk XAI.
11. Jangan menambahkan cancer/malignancy classifier.
12. Jangan membuat model selector.
13. Jangan menyalin branding LUCIT.
14. Jangan membuat medical image visualization yang menyesatkan.
15. Jika sebuah requirement belum ditentukan, gunakan prinsip paling konservatif dan pertahankan konsistensi dengan dokumen ini.
16. Jika keputusan tersebut memengaruhi scope atau output model, jangan mengarang; tandai sebagai requirement yang perlu ditentukan.

---

# 52. Relationship dengan Dokumen PIXEL-T

Urutan dokumen:

```text
PRD.md
  │
  ├── menentukan WHAT
  │
  ▼
StyleGuide.md
  │
  ├── menentukan HOW IT SHOULD LOOK & FEEL
  │
  ▼
FunctionalSpecification.md
  │
  ├── menentukan HOW IT WORKS TECHNICALLY
  │
  ▼
Task.md
  │
  ├── menentukan HOW TO BUILD IT
  │
  ▼
AI Coding Agent
```

Tidak ada template eksternal yang menjadi source of truth.

Template atau referensi visual eksternal hanya boleh digunakan sebagai inspirasi/validasi dan tidak boleh mengubah keputusan produk yang telah dikunci.

---

# 53. Final Design Statement

PIXEL-T harus tampil sebagai:

> **A professional clinical AI workstation for visual colonoscopy analysis, centered on segmentation and explainability.**

Pengalaman pengguna harus terasa:

**Clinical → Clear → Image-first → Explainable → Professional → Calm**

Bukan:

**Decorative → Futuristic → Dashboard-heavy → Diagnostic → Entertainment-oriented**

Prinsip utama:

> **Jika sebuah elemen visual tidak membantu pengguna memahami citra, hasil segmentasi, Grad-CAM, atau workflow analisis, elemen tersebut tidak perlu ditambahkan.**

---

## Status

**FINAL / LOCKED**

Perubahan terhadap dokumen ini harus mengikuti Change Control pada PRD PIXEL-T.

**StyleGuide.md adalah design source of truth untuk implementasi UI/UX PIXEL-T.**
