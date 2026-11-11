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
├── Frontend/
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
├── Backend/
│   ├── requirements.txt
│   ├── src/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   ├── controllers/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── schemas/
│   │   ├── models/
│   │   ├── core/
│   │   └── utils/
│   └── src/main.py
│
│   ├── ai/
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
│   ├── Frontend/
│   ├── Backend/
│   └── ai/
│
└── scripts/
    ├── setup/
    └── deployment/
```

## 5. Prasyarat
- **Python 3.11** (backend & AI module)
- **Node.js 18+** (frontend)
- **Git**
- Akun **Supabase** (Auth, Postgres, Storage) — proyek Supabase aktif

## 6. Instalasi & Menjalankan (2 Terminal)

### Terminal 1 — Backend (port 5000)
```bash
cd Backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS
pip install -r requirements.txt

cp .env.example .env            # lalu isi nilai sesungguhnya
python src/main.py
```

Backend dapat diakses pada `http://localhost:5000` (health check: `GET /api/health`).

### Terminal 2 — Frontend (port 5173)
```bash
cd Frontend
npm install
cp .env.example .env            # lalu isi nilai sesungguhnya
npm run dev
```

Frontend dapat diakses pada `http://localhost:5173`.

> **Catatan:** Model checkpoint berada di `Backend/ai/models/PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth` dan tidak ikut ter-clone (di-`gitignore`). Salin file checkpoint lokal sebelum menjalankan inferensi.

## 7. Arsitektur (3 Pilar)
1. **Frontend (React + Vite + Tailwind):** UI aplikasi, autentikasi Supabase Auth, polling status analisis, tampilan hasil (mask, overlay, Grad-CAM).
2. **Backend (Flask):** REST API (`/api/analysis`, `/api/history`, `/api/admin/*`), validasi gambar, gerbang Domain Validation (heuristik + LLM Gemini fail-closed), penanganan storage/DB Supabase, worker background inferensi.
3. **AI Module (PyTorch):** pipeline inferensi U-Net + ResNet50 (TTA 5×5, threshold 0.55, postprocessing) + Grad-CAM + Domain Validation heuristik.

## 8. Project Status
- **Status:** Foundation / implementation in progress (Task 01).

## 9. Medical Disclaimer
> **Hasil yang ditampilkan merupakan keluaran analisis model AI dan ditujukan sebagai informasi pendukung bagi tenaga medis. Hasil ini tidak dimaksudkan sebagai diagnosis medis atau pengganti penilaian profesional tenaga medis.**
