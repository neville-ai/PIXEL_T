# PIXEL-T

## 1. Description & Purpose
PIXEL-T adalah aplikasi web berbasis AI yang membantu dokter atau tenaga medis menganalisis citra endoskopi/kolonoskopi melalui segmentasi polip usus menggunakan model **U-Net + ResNet50** dan Explainable AI (**Grad-CAM**). Sistem menampilkan citra asli, binary mask, segmentation overlay, visualisasi Grad-CAM, serta ringkasan analisis yang diturunkan secara valid dari output model.

## 2. Target Users
- Dokter dan tenaga medis yang menangani pemeriksaan kolonoskopi/endoskopi polip usus.

## 3. Technology Stack
- **Frontend:** React, TypeScript, Vite, Tailwind CSS
- **Backend:** Python, Flask, Flask-CORS
- **Database:** Supabase / PostgreSQL
- **Authentication:** Supabase Auth
- **Storage:** Supabase Storage
- **AI Framework:** PyTorch
- **Primary Model:** U-Net + ResNet50
- **Explainable AI (XAI):** Grad-CAM

## 4. Repository Structure
```text
PIXEL-T/
├── README.md
├── .gitignore
├── .env.example
│
├── docs/
│   ├── PRD_PIXEL-T_FINAL.md
│   ├── StyleGuide.md
│   ├── FunctionalSpecification.md
│   ├── ModelIntegrationSpecification.md
│   ├── APIContract.md
│   └── DataModelSpecification.md
│
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── src/
│       ├── assets/
│       ├── components/
│       │   ├── ui/
│       │   ├── layout/
│       │   ├── analysis/
│       │   └── history/
│       ├── pages/
│       │   ├── auth/
│       │   ├── dashboard/
│       │   ├── analysis/
│       │   └── history/
│       ├── services/
│       ├── hooks/
│       ├── types/
│       ├── utils/
│       ├── routes/
│       ├── App.tsx
│       └── main.tsx
│
├── backend/
│   ├── requirements.txt
│   ├── app/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   ├── controllers/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── models/
│   │   ├── core/
│   │   └── utils/
│   └── run.py
│
├── ai/
│   ├── inference/
│   ├── config/
│   ├── models/
│   │   └── .gitkeep
│   └── README.md
│
├── database/
│   ├── migrations/
│   ├── seed/
│   └── README.md
│
├── tests/
│   ├── frontend/
│   ├── backend/
│   └── ai/
│
└── scripts/
    ├── setup/
    └── deployment/
```

## 5. Project Status
- **Status:** Foundation / implementation in progress (Task 01).

## 6. Medical Disclaimer
> **Hasil yang ditampilkan merupakan keluaran analisis model AI dan ditujukan sebagai informasi pendukung bagi tenaga medis. Hasil ini tidak dimaksudkan sebagai diagnosis medis atau pengganti penilaian profesional tenaga medis.**
