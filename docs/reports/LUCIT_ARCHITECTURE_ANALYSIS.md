# LUCIT ARCHITECTURE ANALYSIS

**Tanggal:** 11 November 2026
**Objek:** `LUCIT-master/` (proyek referensi)
**Sifat:** read-only. Tidak ada file LUCIT-master yang diubah.
**Metode:** pembacaan langsung seluruh modul backend & frontend + verifikasi path/baris.

---

## 1. Ringkasan Arsitektur

LUCIT-master adalah aplikasi web Flask + React untuk analisis citra histopatologi (klasifikasi/segmentasi) dengan chatbot AI. Arsitekturnya:

```text
Frontend (React 19 + Vite 7, routing inline, session localStorage)
        │  fetch(getApiUrl(...))
        ▼
Backend Flask (app global di main.py, port 8000)
  routes → controllers → services → repositories → config
        │
        ├─ Supabase (auth + tabel tbl_users / tbl_history)
        ├─ TensorFlow/Keras (model klasifikasi & U-Net)
        └─ Vertex AI REST (deskripsi AI + validasi) / SMTP (reset OTP)
```

Kekuatan pola LUCIT:
- Pembagian layer backend jelas dan konsisten: `routes` hanya menangani HTTP, `controllers` menangani orkestrasi/validasi, `services` menangani logika domain, `repositories` menangani Supabase.
- Konfigurasi terpusat di `config/settings.py` dan client Supabase tunggal di `config/supabase.py`.
- Frontend memiliki util terpusat: `utils/api.ts`, `utils/session.ts`, `utils/supabase.ts`, `utils/image.ts`.

Kelemahan yang **tidak boleh ditiru**:
- Tidak ada test sama sekali.
- `app = Flask(__name__)` global (sulit di-test, tidak ada application factory).
- Session disimpan di `localStorage` + Flask cookie session; dua mekanisme auth bercampur.
- `user_repository.py` menyimpan & membandingkan password plaintext di tabel `tbl_users` (legacy fallback) — **risiko keamanan besar**.
- Controller `prediction_controller.py` sangat gemuk (±277 baris) dan mencampur preprocessing, inferensi, Grad-CAM, dan AI description.
- `analysis_repository.py` menyimpan seluruh gambar sebagai base64 di database — tidak scalable.
- Entry service menggunakan `requests` dengan `timeout=60` tanpa retry/backoff.
- `requirements.txt` ber-encoding UTF-16LE (tidak portabel untuk tooling biasa).

---

## 2. Struktur Frontend & Backend

### 2.1 Backend

| Layer | File | Tanggung jawab |
|---|---|---|
| Entry | `src/main.py` | membuat `app`, CORS, registrasi blueprint, preload model, route `/` dan `/testing`, `app.run(port=8000)` |
| Config | `src/config/settings.py` | seluruh env: Vertex, Gemini, Flask session, CORS, SMTP, OTP expiry (`:1-38`) |
| Config | `src/config/supabase.py` | `create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)` (`:7-10`) |
| Routes | `src/routes/user_routes.py` | 7 endpoint auth (`/api/users`, `/login`, `/logout`, `/session/check`, reset OTP) |
| Routes | `src/routes/chatbot_routes.py` | `POST /api/chat` |
| Routes | `src/routes/prediction_routes.py` | `POST /api/predict`, `GET /api/history`, `DELETE /api/history/<id>` |
| Controllers | `src/controllers/user_controller.py` | `SignUpController`, `SignInController`, `SignOutController`, `SessionCheckController`, `PasswordResetController` |
| Controllers | `src/controllers/prediction_controller.py` | preprocessing, klasifikasi, segmentasi, Grad-CAM, simpan hasil |
| Controllers | `src/controllers/chatbot_controller.py` | validasi pesan & panggil `LLMService` |
| Services | `ai_validator_service.py` | validasi histopatologi + deskripsi AI (Vertex + fallback lokal) |
| Services | `chatbot_service.py` | filter topik & jawaban chatbot |
| Services | `gradcam_service.py` | `get_last_conv_layer`, `make_gradcam_heatmap`, `overlay_heatmap` |
| Services | `segmentation_service.py` | preprocessing, threshold 0.35, mask, overlay, area stats |
| Services | `email_service.py` | kirim OTP reset password via SMTP |
| Services | `vertex_rest_client.py` | klien REST Vertex `generateContent`, timeout 60 dtk |
| Repositories | `user_repository.py`, `analysis_repository.py` | akses Supabase |
| Models | `model_loader.py`, `user_schema.py` | cache model Keras; schema Pydantic (tidak dipakai route) |

### 2.2 Frontend

| Area | File | Tanggung jawab |
|---|---|---|
| Entry | `src/main.tsx` | `createRoot` + `<App />` + import `assets/style.css` |
| Routing | `src/App.tsx` | `BrowserRouter`, route `/`, `/analysis`, `/history`, guard manual, splash, session manager |
| Komponen | `components/<Fitur>/index.tsx` | Header, Hero, AboutUs, Features, Footer, LoginModal, ScrollReveal, SlideTransition, SmoothScroll, SplashScreen, TransitionPortal |
| Halaman | `pages/analysis/index.tsx` | upload, pilih model, prediksi, tampilan 3 citra, donut, Markdown, chatbot |
| Halaman | `pages/history/index.tsx` | daftar riwayat, pencarian, expand, hapus, chatbot per item |
| Util | `utils/api.ts` | normalisasi `VITE_API_URL`, `getApiUrl` |
| Util | `utils/session.ts` | session localStorage + timeout 30 menit + event custom |
| Util | `utils/supabase.ts` | lazy `createClient` |
| Util | `utils/image.ts` | resolve path gambar relatif ke API base |
| Styling | `assets/style.css`, `index.css`, `App.css` | CSS global (bukan Tailwind) |

---

## 3. Pola Pemanggilan API

**Bukti:** `Frontend/src/utils/api.ts:1-21`, `pages/analysis/index.tsx:265`, `pages/history/index.tsx:255,286`.

- Base URL dinormalisasi dari `VITE_API_URL`; bila kosong, gunakan path relatif.
- Pemanggilan memakai `fetch(getApiUrl("/api/..."))`.
- `POST /api/predict` mengirim `FormData` (file + `model_type` + `model_name`).
- `GET /api/history` dan `DELETE /api/history/:id` memakai `credentials: "include"` (cookie session Flask).
- Login memakai `POST /api/login`; session disimpan di cookie Flask **dan** `localStorage` (`utils/session.ts:71-75`).
- Error handling per halaman: `try/catch` + `setError`/`toast`; tidak ada wrapper error terpusat.
- Tidak ada timeout `fetch` eksplisit.

**Penilaian untuk PIXEL-T:** PIXEL-T sudah memakai `services/*.ts` terpusat dan token Bearer Supabase (lebih baik). Pola `utils/api.ts` (normalisasi base URL + `getApiUrl`) layak diadopsi sebagai helper kecil, tetapi **tidak wajib** karena `services/analysis.ts` sudah menangani base URL. Risiko rendah.

---

## 4. Pola Routing

**Bukti:** `Frontend/src/App.tsx:146-202`.

- Route didefinisikan inline di `App.tsx`; tidak ada file `routes/`.
- Guard bukan komponen route, melainkan fungsi `AnalysisRouteGuard`/`HistoryRouteGuard` (`:50-76`) yang membaca `hasActiveSession()` dan redirect ke `/`.
- Belum ada route admin/profil.
- Splash screen ditampilkan 5,6 detik sebelum aplikasi.

**Penilaian untuk PIXEL-T:** PIXEL-T sudah lebih baik: `routes/AppRoutes.tsx` terpisah + guard komponen (`ProtectedRoute`, `AdminRoute`, `DoctorRoute`, `PublicOnlyRoute`). **Jangan mundur** ke pola inline LUCIT. Tidak ada yang perlu diadopsi.

---

## 5. Pola Komponen dan Halaman

**Bukti:** struktur `Frontend/src/components/*/index.tsx`, `pages/*/index.tsx`.

- Satu folder per komponen, file `index.tsx` (konvensi barrel tanpa nama file eksplisit).
- Halaman `analysis` dan `history` masing-masing satu file besar (1297 dan 907 baris) yang mencampur UI, state, fetch, dan logika presentasi.
- Komponen presentasional kecil (Header, Footer, Hero) cukup bersih.
- Tidak ada folder `ui/` reusable; tombol/input ditulis inline dengan style objek.

**Penilaian untuk PIXEL-T:** PIXEL-T sudah memakai `components/ui/*` reusable dan halaman terpisah per fitur. **Pertahankan**. Yang bisa dipelajari dari LUCIT hanyalah konsistensi "satu folder per komponen" — tetapi PIXEL-T sudah konsisten dengan nama file eksplisit (lebih mudah dicari). Tidak perlu diubah.

---

## 6. Pengelolaan State

**Bukti:** `utils/session.ts`, `App.tsx:78-144`, `Header/index.tsx`, `pages/analysis/index.tsx`.

- Session user di `localStorage` (`lucit_user`) + timestamp aktivitas (`lucit_last_activity`), timeout 30 menit.
- Event custom `lucit:auth-changed`, `lucit:session-expired`, `lucit:open-login` untuk sinkronisasi antar komponen.
- State halaman memakai `useState` lokal; tidak ada Context/Redux.
- `SessionManager` memasang listener global dan interval 60 detik untuk cek expiry.

**Penilaian untuk PIXEL-T:** PIXEL-T memakai `AuthContext` + Supabase session (lebih aman & terpusat). **Jangan mengganti** ke localStorage manual. Tidak ada yang perlu diadopsi.

---

## 7. Pemisahan Business Logic vs Presentation

- Backend: cukup baik — controller memanggil service/repository, tetapi `prediction_controller.py` masih mencampur preprocessing + inferensi + Grad-CAM + AI description.
- Frontend: **kurang** — halaman `analysis/index.tsx` mencampur fetch, transformasi gambar (canvas), formatting, dan UI; `history/index.tsx` mencampur fetch, parsing confidence, drag-and-drop chat, dan UI.

**Penilaian untuk PIXEL-T:** PIXEL-T sudah memisahkan API ke `services/*.ts`, tetapi dua halaman besar (`DoctorProfile.tsx` 1051 baris, `NewAnalysis.tsx` 631 baris) masih padat. Kandidat refactor **internal** (ekstrak subkomponen/helper) dengan risiko sedang; harus dijaga agar tidak mengubah UI.

---

## 8. Pengelolaan Konfigurasi

**Bukti:** `Backend/src/config/settings.py:1-38`, `Frontend/src/utils/api.ts:1`.

- Backend: semua env dibaca di satu file; ada helper `_parse_csv_env`.
- Frontend: hanya `VITE_API_URL`, `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`.
- Tidak ada file `.env.example` di backend LUCIT (hanya `.env.production` di frontend).
- `requirements.txt` UTF-16LE menyulitkan pembacaan otomatis.

**Penilaian untuk PIXEL-T:** PIXEL-T sudah punya `core/config.py` terpusat + `.env.example` yang lengkap. **Pertahankan**. Perbaikan yang layak: pastikan semua dependency (termasuk `google-genai`) tercatat.

---

## 9. Penanganan Error

**Bukti:** `Backend/src/routes/*.py` (try/except per route), `src/services/vertex_rest_client.py:46-67`, frontend `pages/*` try/catch.

- Route mengembalikan `{"status":"error","message":...}` dengan status 400/401/404/500.
- Tidak ada error handler global Flask; setiap route menduplikasi `try/except`.
- Service AI memiliki fallback lokal (deskripsi) dan fallback heuristik (validasi).
- Frontend menampilkan `error`/`toast`; tidak ada tipe error terpusat.

**Penilaian untuk PIXEL-T:** PIXEL-T sudah punya `core/errors.py` + `APIError` + handler global (lebih baik). **Pertahankan**. Tidak ada yang perlu diadopsi.

---

## 10. Pengelolaan Dependency

**Bukti:** `Backend/requirements.txt`, `Backend/package.json`, `Frontend/package.json`.

- Backend Python: Flask, flask-cors, supabase, python-dotenv, numpy, tensorflow, opencv-python, Pillow, google-generativeai.
- `Backend/package.json` hanya berisi `@supabase/supabase-js` (tidak jelas dipakai; kemungkinan sisa tooling).
- Frontend: React 19, react-router-dom, supabase-js, lenis, react-markdown, sonner.
- Root `package-lock.json` kosong (`packages: {}`).

**Penilaian untuk PIXEL-T:** PIXEL-T memakai versi dependency yang lebih terkontrol (rentang versi). Tidak ada pola yang perlu diadopsi. Catatan: dependency yang tidak terpakai di LUCIT (mis. `pydantic` di `user_schema.py` tanpa import route) menunjukkan pentingnya audit dependency.

---

## 11. Penggunaan Utilities

- `utils/api.ts` — normalisasi base URL.
- `utils/session.ts` — session lokal + event.
- `utils/supabase.ts` — lazy client.
- `utils/image.ts` — resolve gambar.
- Backend tidak punya folder `utils`; helper tersebar di controller/service.

**Penilaian untuk PIXEL-T:** PIXEL-T sudah punya `lib/format.ts`, `lib/supabase.ts`, `lib/openingTimeline.ts`, `hooks/*`. Tidak perlu memaksakan `utils/`. Jika ingin konsisten, `lib/` sudah berperan sebagai utils. **Tidak ada perubahan struktur yang diperlukan.**

---

## 12. Pengujian

- LUCIT-master: **tidak ditemukan** folder test, file `test_*`, `*_test.py`, `*.test.ts`, atau konfigurasi pytest/vitest.
- Tidak ada CI/CD.

**Penilaian untuk PIXEL-T:** PIXEL-T jauh lebih baik (pytest + vitest + 19 file test FE). **Jangan meniru** LUCIT pada aspek ini.

---

## 13. Dokumentasi

- LUCIT: `README.md` (4,3 KB) + `Frontend/README.md`; tidak ada dokumen API/arsitektur formal.
- PIXEL-T: jauh lebih lengkap (`docs/PRD`, `APIContract`, `DataModelSpecification`, `StyleGuide`, dll).

**Penilaian:** PIXEL-T unggul. Tidak ada yang perlu diadopsi.

---

## 14. Pola Keamanan

**Bukti:**
- `Backend/src/config/supabase.py:7-10` memakai **service role key** untuk semua akses.
- `Backend/src/repositories/user_repository.py:13-50` menyimpan & membandingkan **password plaintext** (legacy).
- `Backend/src/routes/prediction_routes.py:18-20` memeriksa `session.get("user")`.
- `Frontend/src/utils/session.ts` menyimpan user di `localStorage` (bukan token).
- `Backend/src/main.py:18-21` mengatur cookie `Secure/HttpOnly/SameSite`.

**Penilaian untuk PIXEL-T:** PIXEL-T **lebih aman**: token Bearer Supabase diverifikasi server-side (`core/auth.py`), service role hanya untuk operasi tertentu, tidak menyimpan password. **Jangan meniru** pola password plaintext atau session localStorage LUCIT. Temuan ini menjadi bukti bahwa LUCIT bukan acuan keamanan.

---

## 15. Pola Integrasi Layanan Eksternal

- Vertex AI via REST mentah (`vertex_rest_client.py`) dengan `timeout=60`, tanpa retry/backoff, `maxOutputTokens: 8192`.
- Chatbot via `chatbot_service.py` (filter topik + Gemini).
- Email OTP via SMTP (`email_service.py`).
- Supabase via SDK.

**Penilaian untuk PIXEL-T:** PIXEL-T memakai `google-genai` SDK dengan `response_schema`, `thinking_config`, `max_output_tokens=1024`, timeout 30 dtk, retry `attempts=1`, serta fail-closed. Ini **lebih terkontrol** daripada LUCIT. Tidak ada yang perlu diadopsi. Catatan: pastikan dependency `google-genai` tercatat.

---

## 16. Tabel Penilaian Pola: Adopsi ke PIXEL-T?

| No | Pola LUCIT | Digunakan di LUCIT? | Sudah ada di PIXEL-T? | Manfaat nyata | Risiko | Keputusan |
|---|---|---|---|---|---|---|
| 1 | Layering routes→controllers→services→repositories | Ya | Ya | — | — | **Pertahankan** |
| 2 | Config terpusat | Ya | Ya | — | — | **Pertahankan** |
| 3 | Supabase client terpusat | Ya | Ya | — | — | **Pertahankan** |
| 4 | `utils/api.ts` normalisasi base URL | Ya | Sebagian (`services/analysis.ts`) | Kecil | Rendah | **Opsional**, tidak perlu |
| 5 | Satu folder per komponen (`index.tsx`) | Ya | Tidak (pakai nama eksplisit) | Kecil | Rendah | **Tidak diadopsi** (PIXEL-T lebih jelas) |
| 6 | Routing inline + guard fungsi | Ya | Tidak (lebih baik) | Negatif | — | **Tidak diadopsi** |
| 7 | Session localStorage + event | Ya | Tidak (Context+Supabase) | Negatif (keamanan) | — | **Tidak diadopsi** |
| 8 | Global `app` Flask | Ya | Tidak (factory) | Negatif (testability) | — | **Tidak diadopsi** |
| 9 | Try/except per route | Ya | Tidak (handler global) | Negatif (duplikasi) | — | **Tidak diadopsi** |
| 10 | Fallback lokal deskripsi AI | Ya | Tidak (fail-closed) | Netral | — | **Tidak diadopsi** |
| 11 | Cache model di service | Ya | Ya (`model_service.py`) | — | — | **Pertahankan** |
| 12 | Timeout & retry eksplisit pada layanan eksternal | Parsial | Ya (lebih baik) | — | — | **Pertahankan** |
| 13 | Test suite | **Tidak** | Ya | — | — | **Pertahankan PIXEL-T** |
| 14 | Dokumentasi API/arsitektur | **Tidak** | Ya | — | — | **Pertahankan PIXEL-T** |
| 15 | Password plaintext & service role menyeluruh | Ya (legacy) | Tidak | Negatif | — | **Tidak diadopsi** |

---

## 17. Kesimpulan

1. PIXEL-T **sudah menerapkan** inti pola arsitektur LUCIT yang relevan (layering, config terpusat, client Supabase, service AI terpisah).
2. Pola LUCIT yang layak dipertimbangkan hanya bersifat kosmetik/opsional (helper `getApiUrl`), bukan restrukturisasi besar.
3. Beberapa pola LUCIT justru **lebih buruk** dan tidak boleh diterapkan: routing inline, session localStorage, password plaintext, `app` global, try/except per route, tanpa test.
4. Fokus refactoring PIXEL-T sebaiknya pada **konsistensi internal** dan **pembersihan berbasis bukti** (folder kosong, artefak build/log, dependency yang belum tercatat, file besar yang bisa dipecah secara aman), bukan meniru LUCIT.
5. Setiap perubahan harus melalui baseline test dan tidak menyentuh kontrak API, schema DB, model/inferensi, Domain Validation, atau Grad-CAM.
