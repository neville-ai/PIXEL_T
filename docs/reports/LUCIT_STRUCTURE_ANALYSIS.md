# LUCIT STRUCTURE ANALYSIS — Proyek Referensi `LUCIT-master/`

**Tanggal:** 11 November 2026  
**Objek:** `LUCIT-master/`  
**Status:** pembacaan read-only. Tidak ada satu pun file di `LUCIT-master/` yang diubah.  
**Sifat:** analisis pola untuk menentukan pola yang **diadopsi**, **disesuaikan**, atau **ditolak** pada PIXEL-T.

---

## 0. Ringkasan Eksekutif

`LUCIT-master/` adalah proyek Flask + React untuk klasifikasi/segmentasi citra medis dengan chatbot. Arsritekturnya secara umum memakai pola layer yang sama dengan PIXEL-T:

```text
Frontend (React)
    → fetch(getApiUrl(...))
        → Backend Flask
            routes → controllers → services → repositories
                → Supabase / TensorFlow / Vertex / SMTP / Gemini
```

Namun, dalam **kualitas implementasi**, PIXEL-T saat ini sudah lebih matang. Pola LUCIT yang baik harus ditiru, sementara pola LUCIT yang bermasalah **harus ditolak atau tidak dipakai**.

---

## 1. Struktur Backend LUCIT — Bukti Pembacaan

| Area | File | Bukti | Catatan |
|---|---|---|---|
| Entry | `Backend/src/main.py` | `app = Flask(__name__)`, port 8000, preload model | App global; tidak disarankan ditiru ke PIXEL-T |
| Config backend | `Backend/src/config/settings.py` | env, Vertex, Gemini, Flask session, CORS, SMTP, OTP | Terpusi; namun `requirements.txt` UTF-16LE |
| Supabase | `Backend/src/config/supabase.py` | `create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)` | Service role untuk database/auth |
| Routes | `Backend/src/routes/user_routes.py`, `chatbot_routes.py`, `prediction_routes.py` | endpoint auth/predict/chat | Route mengandung try/except; error handler global tidak ada |
| Controllers | `Backend/src/controllers/*.py` | `prediction_controller.py` ±277 baris | Controller sangat gemuk: preprocessing/inferensi/Grad-CAM/AI desc |
| Services | `Backend/src/services/*.py` | validasi, chatbot, email, Grad-CAM, segmentasi, Vertex | Ada fallback yang berbeda |
| Repositories | `Backend/src/repositories/*.py` | user & analysis | Gambar mungkin disimpan base64 di DB (kurang scalable) |
| Models | `Backend/src/models/*.py` | model loader Keras, user schema | TensorFlow |

### 1.1 Analisis Layering

**Kelemahan:**
- Route berisi logika operasional cukup banyak melalui controller besar.
- Tidak ada application factory; sulit diuji independen.
- Error handling berpola duplikat per route.
- Tidak ada global error handler seragam.
- Session Flask + localStorage bercampur tanpa satu sumber kebenaran.
- Password plaintext di `tbl_users` / fallback repository.
- `requirements.txt` UTF-16LE tidak portabel.
- Chat bot dan email service menambah kompleksitas domain tidak relevan untuk PIXEL-T.

### 1.2 Analisis Validasi AI LUCIT

| Aspek | LUCIT | PIXEL-T |
|---|---|---|
| Validator | `ai_validator_service.py` | `domain_validator.py` + `llm_image_validator.py` |
| Prioritas | LLM utama → heuristik fallback | heuristik penyaring → LLM final |
| Fail-closed | Longgar jika LLM error fallback heuristik | Ketat: error LLM → UNCERTAIN, tidak ada bypass |
| Skrip | `scripts/calibrate_domain_gate.py` dsb. | `scripts/experiment_domain_gate.py` dsb. |
| Threshold | `segmentation_service.py` menggunakan threshold 0.35 | `segmentation.py` menggunakan threshold 0.55 dari `MODEL_CONFIG` |

**Temuan:** arsitektur modular PIXEL-T sudah lebih baik untuk kebutuhan validasi skripsi: pemisahan heuristik dan LLM, fail-closed, dan modular pipeline.

---

## 2. Struktur Frontend LUCIT — Bukti Pembacaan

| Area | File | Bukti | Catatan |
|---|---|---|---|
| Entry | `Frontend/src/main.tsx`, `App.tsx` | `BrowserRouter`, splash, `SessionManager` | Routing inline di App |
| Routing | `App.tsx:146-202` | `/`, `/analysis`, `/history` | Guard manual, belum admin/profile |
| Komponen | `Frontend/src/components/<Fitur>/index.tsx` | Header, Hero, Features, Footer, LoginModal, Splash | Barrel unik |
| Halaman | `Frontend/src/pages/<Fitur>/index.tsx` | analysis, history, chatbot | Mencampur fetch + UI + logic |
| Utils | `Frontend/src/utils/api.ts:1-21`, `session.ts`, `supabase.ts`, `image.ts` | normalisasi API/base URL | Seperti target adopt |
| Auth state | `utils/session.ts` + localStorage | manual timeout, event custom | Tidak disarankan dipakai PIXEL-T |
| Build | Vite 7, TS 5.9, React 19 | lebih baru dibanding PIXEL-T | — |

**Kelemahan LUCIT:**
- Routing inline membuat batas halaman kurang jelas.
- State session manual (`localStorage`) dan cookie bercampur.
- Error handling per page/halaman tanpa envelope standar global.
- No test suite.
- Chat bot dan markdown generation menambah beban domain.

---

## 3. Pola yang Disarankan untuk Diserap PIXEL-T

### 3.1 Disesuaikan / Diadopsi

| Pola LUCIT | Relevansi PIXEL-T | Tindakan |
|---|---|---|
| Backend layer routes → controllers → services → repositories | Disusun | Pertahankan; konsolidasi internal bila perlu |
| Config terpusat | Disusun | Pertahankan |
| Supabase client singleton | Disusun | Pertahankan |
| Util `api.ts` normalisasi base URL | Lebih baik | Kandidat kecil; `services/analysis.ts` sudah menyelesaikan |
| Folder komponen per fitur | Lebih baik | Pertahankan; PIXEL-T sudah lebih eksplisit |
| Route guard | Lebih baik | Pertahankan; `AppRoutes.tsx` + guard komponen lebih bersih |
| Test | Tidak ada | **Jangan tiru**; PIXEL-T sudah punya suite |

### 3.2 Ditolak / Tidak Layak Ditiru

| Pola LUCIT | Alasan |
|---|---|
| App global Flask `app = Flask(...)` | Sulit di-test; PIXEL-T sudah application factory |
| Password plaintext | Risiko keamanan; PIXEL-T menggunakan Supabase Auth/RLS |
| Base64 gambar di DB | Skalabilitas; PIXEL-T menyimpan file storage |
| Controller prediction gemuk | Tanggung jawab campuran; PIXEL-T memakai service terpisah |
| Session localStorage + cookie bercampur | Sumber kebenaran tunggal; PIXEL-T memakai Supabase session |
| Error handling route `try/except` tanpa global handler | Duplikasi; PIXEL-T sudah global `APIError` |
| Requirements UTF-16LE | Tooling tidak portable |
| Chatbot/email | Domain tidak relevan; PIXEL-T tidak memakai |

---

## 4. Perbandingan File & Fungsi Utama

| Fungsi | LUCIT | PIXEL-T | Evaluasi |
|---|---|---|---|
| Validasi domain | `ai_validator_service.py` (LLM + heuristic fallback) | `domain_validator.py` + `llm_image_validator.py` (heuristic → LLM, fail-closed) | **PIXEL-T lebih baik** |
| Segmentasi | `segmentation_service.py` threshold 0.35, overlay | `segmentation.py` threshold 0.55 dari `MODEL_CONFIG`, overlay | **Perlu dipahami**, tetapi model config dilindungi |
| Grad-CAM | `gradcam_service.py` | `gradcam.py` + model config target layer | **PIXEL-T terstruktur lebih baik** |
| Pipeline | di controller | di service + AI module | **PIXEL-T lebih baik** |
| History | repository/controller | repository/service | **PIXEL-T lebih baik** |
| Admin | belum ada di LUCIT | lengkap | **PIXEL-T unggul** |

---

## 5. Kesimpulan Analisis LUCIT

`LUCIT-master/` berisi pola arsitektur yang bisa menjadi acuan, tetapi bukan template tunggal. Pola yang disukai LUCIT — **layered backend, config terpusat, Supabase client, util API, folder fitur** — sudah diimplementasikan dengan lebih baik di PIXEL-T. Pola yang buruk — **app global, password plaintext, session campuran, error handler duplikat, base64 DB, controller gemuk** — **tidak boleh dikopi**.

**Temuan untuk laporan:**
1. LUCIT tidak memiliki test; PIXEL-T wajib menjaga.
2. LUCIT memakai TensorFlow/Vertex; PIXEL-T memakai PyTorch/Gemini — desain penelitian berbeda.
3. LUCIT chatbot/email tidak relevan untuk fitur utama PIXEL-T.

---

## 6. Catatan Konservasi

- Semua referensi di laporan ini berasal dari pembacaan langsung file.
- `LUCIT-master/` harus dibaca/tidak diubah selama audit.
- Setiap pola yang akan dipakai kembali harus ditransfer tanpa mengubah perilaku, API, model, atau skrip skripsi.
