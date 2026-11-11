# PIXEL-T — Analisis Codebase Menyeluruh

**Status:** hasil audit baca-saja (tidak ada kode aplikasi yang diubah)
**Tanggal audit:** 25 Oktober 2026
**Metode:** penelusuran langsung struktur repositori, pembacaan implementasi, penelusuran pemanggilan fungsi, pembacaan migrasi SQL, konfigurasi (nama variabel saja, tanpa nilai), dokumentasi, dan eksekusi test frontend.
**Aturan bukti:** setiap klaim diberi lokasi file/fungsi. Hal yang tidak dapat dibuktikan ditandai **Belum terverifikasi**.

---

## A. Ringkasan Eksekutif

PIXEL-T adalah aplikasi web tiga lapis untuk segmentasi polip pada citra endoskopi/kolonoskopi:

1. **Frontend SPA** (React 18 + TypeScript + Vite + Tailwind) — menangani seluruh autentikasi pengguna melalui Supabase Auth (anon key), unggah citra, polling status, tampilan hasil, riwayat, dan profil dokter.
2. **Backend Flask** — satu-satunya pemegang *service role key*. Memverifikasi Bearer token Supabase, memvalidasi citra dua lapis, menyimpan citra asli, membuat record `analyses`, lalu menjalankan pipeline AI di **worker thread dalam proses yang sama** (bukan queue eksternal).
3. **Lapisan AI** (PyTorch + `segmentation_models_pytorch`) — U-Net + ResNet50 (SCSE decoder attention), input 512×512, threshold 0,55, TTA 5 skala × 5 orientasi (25 forward pass), post-processing morfologi + filter area + hole filling + contour smoothing, pengukuran area/bbox, dan Grad-CAM kustom.

Penyimpanan: Supabase PostgreSQL (`analyses`, `doctor_profiles`) + bucket privat `analysis-assets` dengan struktur path `analysis/{user_id}/{analysis_id}/{category}/{filename}` dan URL bertanda tangan (signed URL) berumur 3600 detik.

**Temuan paling penting (rinci di §K):**

| # | Temuan | Prioritas |
|---|---|---|
| 1 | Membuka tab baru memicu `logoutUser()` sehingga sesi Supabase global ikut berakhir (semua tab) | Tinggi |
| 2 | `GET /api/history` selalu mengembalikan maksimal 20 record; record ke-21 dan seterusnya tidak dapat diakses dari UI maupun API | Tinggi |
| 3 | Halaman hasil berhenti polling setelah 12 percobaan (±60 detik) dan dapat menampilkan "processing" selamanya | Tinggi |
| 4 | RLS mengizinkan pengguna menulis/mengubah baris `analyses` miliknya langsung lewat PostgREST, melewati seluruh validasi backend | Tinggi (integritas) |
| 5 | Flag `tta_enabled` disimpan & dilaporkan tetapi tidak dibaca oleh loop inferensi | Sedang |
| 6 | Dokumentasi API mencantumkan `/api/auth/*` yang tidak ada di kode | Sedang |
| 7 | `is_verified` pada `doctor_profiles` dapat ditulis sendiri oleh pemilik profil | Sedang |

**Status verifikasi eksekusi:** 17 file test frontend / **245 test lulus**. Test backend & AI **tidak dapat dijalankan** di mesin ini karena kebijakan Application Control Windows memblokir `torch/lib/c10_cuda.dll` (`OSError WinError 4551`) — bukan kegagalan kode.

---

## B. Struktur Direktori dan Fungsi

```text
PIXEL-T/
├── .env.example                 template env (tanpa nilai)
├── package.json                 dependensi root (@supabase/ssr, supabase-js) — tidak dipakai kode
├── README.md                    ringkasan produk & stack
├── ai/                          lapisan inferensi
│   ├── config/model_config.py   ModelConfig (konstanta terverifikasi) + validasi + SHA-256
│   ├── inference/preprocessing.py  RGB → resize 512 → ImageNet normalize → tensor [1,3,512,512]
│   ├── inference/model_service.py  lazy loader SMP Unet, SHA-256 gate, device selection, target layer
│   ├── inference/segmentation.py   TTA, sigmoid, threshold, mask dasar, penghitung forward pass
│   ├── inference/postprocessing.py close/open, filter area, fill holes, smoothing, pengukuran
│   ├── inference/gradcam.py        Grad-CAM kustom (hook forward/backward)
│   ├── inference/pipeline.py       orkestrasi 5 fase produksi artefak PNG
│   └── models/PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth  checkpoint (~129 MB, gitignored)
├── Backend/
│   ├── run.py                   entry point (create_app + app.run)
│   ├── requirements.txt         Flask, supabase, torch, smp, opencv, pytest
│   └── app/
│       ├── __init__.py          application factory, CORS, error handler, blueprint
│       ├── core/config.py       Config/Development/Testing/Production + get_config()
│       ├── core/auth.py         @require_auth (verifikasi Bearer token Supabase)
│       ├── core/errors.py       APIError + envelope error standar
│       ├── core/supabase.py     singleton client anon & service-role
│       ├── routes/health.py     GET /api/health
│       ├── routes/analysis.py   4 endpoint analisis/history + logging korelasi
│       ├── controllers/analysis_controller.py  HTTP ↔ service, ekstraksi user_id
│       ├── services/analysis_service.py        orkestrasi, validasi, queue, progress, persistensi
│       ├── services/storage_service.py         path ownership, upload/download/signed/delete
│       └── repositories/analysis_repository.py CRUD `analyses` + validasi status
├── database/migrations/         001 tabel+bucket+RLS, 002 metadata AI, 003 progress, 004 profil dokter
├── Frontend/
│   ├── vite.config.ts, tsconfig.json, tailwind.config.js, postcss.config.js
│   └── src/
│       ├── main.tsx / App.tsx   bootstrap; AppShell di semua rute kecuali /login
│       ├── routes/AppRoutes.tsx 9 rute (publik, terlindungi, 404)
│       ├── context/AuthContext.tsx  sesi + startup reset + signIn/signUp/signOut
│       ├── components/auth/     ProtectedRoute, PublicOnlyRoute, AuthLoadingState, OpeningAnimation
│       ├── components/layout/AppShell.tsx  header, nav, menu pengguna, modal sign out
│       ├── components/ui/       Button, Card, Input, Modal, Badge, Empty/Error/LoadingState, ThemeToggle
│       ├── pages/auth/          Login (sign in + reset request), Register
│       ├── pages/dashboard/     ringkasan + 4 kartu analisis terbaru
│       ├── pages/analysis/      NewAnalysis (validasi + polling), AnalysisResult (hasil + polling)
│       ├── pages/history/       History (filter/pagination klien, hapus), HistoryDetail (rute tanpa tautan)
│       ├── pages/profile/       DoctorProfile (1588 baris: tampilan + modal 5 tab)
│       ├── services/            auth.ts, analysis.ts, profile.ts (semua akses data)
│       ├── lib/                 supabase.ts (singleton), openingTimeline.ts, format.ts
│       └── hooks/               useTheme, useOpeningAnimation
├── tests/                       backend (7 file), ai (2 file), frontend (1 file env)
├── research/                    notebook training, config Ver.22, hasil evaluasi CSV
├── references/                  tangkapan layar referensi desain (bukan aset produksi)
├── docs/                        PRD, FunctionalSpec, APIContract, DataModelSpec, StyleGuide, ModelIntegration, diagrams/
└── scripts/                     hanya .gitkeep (kosong)
```

### File penting dan perannya

| File | Peran |
|---|---|
| `Backend/src/services/analysis_service.py` | Inti backend: validasi citra, kompensasi kegagalan, queue in-memory, progress reporter, eksekusi pipeline, persistensi hasil |
| `Backend/src/services/storage_service.py` | Satu-satunya jalur penulisan/penghapusan objek; menegakkan kepemilikan path |
| `Backend/ai/inference/segmentation.py` | Definisi perilaku inferensi sebenarnya (TTA & threshold) |
| `Backend/ai/config/model_config.py` | Sumber tunggal hyperparameter & checkpoint; `validate()` dijalankan saat import |
| `Frontend/src/utils/analysis.ts` | Klien API tunggal (auth header, refresh 401 sekali, envelope error) |
| `Frontend/src/context/AuthContext.tsx` | Sumber kebenaran sesi di klien |
| `Frontend/src/pages/analysis/NewAnalysis.tsx` | Validasi klien + orkestrasi polling pasca-202 |

### Artefak yang tidak termasuk kode aplikasi

- `backend_foreground.log`, `backend_foreground_err.log` — log runtime di root (gitignored).
- `Frontend/dist/`, `Frontend/tsconfig.tsbuildinfo` — hasil build (gitignored).
- `package.json` + `package-lock.json` di root hanya berisi `@supabase/ssr` dan `@supabase/supabase-js`; **tidak ada impor `@supabase/ssr`** di seluruh repo. Dependensi yatim.

---

## C. Arsitektur

```text
Browser (React SPA)
 ├─ supabase-js (anon key) ──────────────► Supabase Auth  (signUp/signIn/reset/signOut)
 │                                          └─ sesi disimpan di localStorage klien
 └─ fetch + Bearer access_token ─────────► Flask /api
                                             ├─ @require_auth: auth.get_user(token)
                                             ├─ AnalysisController
                                             ├─ AnalysisService
                                             │   ├─ StorageService ──► Supabase Storage (service role)
                                             │   ├─ AnalysisRepository ──► PostgreSQL (service role)
                                             │   └─ AnalysisJobQueue (thread, kapasitas 4)
                                             │        └─ run_pipeline → U-Net/ResNet50 + Grad-CAM
                                             └─ envelope JSON { success, data | error }
```

### C.1 Frontend

- **Entry:** `src/main.tsx` → `App.tsx`. `BrowserRouter` → `AuthProvider` → `ThemeBootstrap` → `AppShellSwitch`.
- **Shell:** `AppShell` membungkus semua rute **kecuali `/login`** (`isBareLogin`), sehingga halaman login tampil tanpa header/footer.
- **Routing:** `AppRoutes.tsx`; `/` dialihkan ke `/login`. Rute publik dibungkus `PublicOnlyRoute` (redirect ke `/dashboard` bila sudah login), rute klinis dibungkus `ProtectedRoute` (redirect ke `/login` sambil menyimpan `state.from`).
- **State:** tidak ada library state global; hanya `AuthContext` (user/session/loading) + state lokal per halaman.
- **Tema:** `useTheme` menulis kelas `dark`; `ThemeBootstrap` hanya membaca preferensi sekali sebelum paint agar `/login` (di luar shell) tetap bertema benar.
- **Panggilan jaringan:** semua melalui `services/*`, tidak ada `fetch` langsung di komponen (kecuali tidak ditemukan).

### C.2 Backend

- **Factory:** `create_app()` di `Backend/src/__init__.py`; konfigurasi dari `get_config()` berbasis `APP_ENV`.
- **CORS:** hanya untuk `/api/*`, origin dari `CORS_ALLOWED_ORIGINS` (default `http://localhost:5173,http://127.0.0.1:5173`), `supports_credentials=True`.
- **Autentikasi:** dekorator `require_auth` (`core/auth.py`) mem-parse header, memanggil `client.auth.get_user(token)` dengan klien **anon**, lalu menaruh `g.current_user` dan `request.user`.
- **Error:** `APIError` + handler HTTP 400/401/403/404/405/413/500 + catch-all. Semua respons error memakai `{success:false, error:{code,message}}`; traceback tidak dibocorkan.
- **Batas ukuran:** `MAX_CONTENT_LENGTH = 11 MB` (Flask menolak body lebih besar dengan 413 `FILE_TOO_LARGE`), sedangkan validasi aplikasi membatasi **byte isi file** 10 MB.
- **Observability:** `print` berformat `[CORRELATION]`/`[TIMING]` (request id, analysis id, durasi per tahap) — bukan logging terstruktur.

### C.3 Lapisan AI

Lihat §G. Ringkas: satu proses, satu model di memori, dieksekusi di worker thread; hasil dikembalikan sebagai byte PNG + dict pengukuran.

### C.4 Database & storage

Lihat §H.

---

## D. Peta Dependensi dan Aliran Data

### D.1 Alur unggah → hasil (happy path)

1. `NewAnalysis.selectFile` memvalidasi ekstensi/MIME/ukuran/nama file, lalu `createImageBitmap` memastikan citra dapat didekode (klien).
2. `handleSubmit` → `createAnalysis(file)` (`services/analysis.ts`) → `POST /api/analysis` multipart field `image` + Bearer token.
3. `require_auth` memverifikasi token → `AnalysisController.create_analysis` mengambil `user_id` dari `g.current_user`.
4. `AnalysisService.create_analysis`:
   a. `validate_and_decode_image` → nama file, kosong, ≤10 MB, MIME deklarasi ∈ {jpeg,png}, `Image.verify()` + `Image.load()`, MIME isi = MIME deklarasi, dimensi > 0.
   b. `analysis_id = uuid4()`; path `analysis/{user}/{analysis_id}/original/input.{ext}`.
   c. Upload ke storage (service role). Gagal → `STORAGE_ERROR` 500, objek dibersihkan.
   d. Insert baris `analyses` status `processing`. Gagal → hapus objek + record, `DATABASE_ERROR` 500.
   e. `job_queue.try_enqueue({analysis_id,user_id,file_bytes})`. Penuh → hapus record + objek, `QUEUE_FULL` **429**.
   f. Kembalikan **202** `{analysis_id, status:"processing"}`.
5. Worker mengambil job → `_execute_pipeline` → `run_pipeline` (5 fase) dengan `on_phase`/`on_pass` → progress reporter menulis `current_step`/`progress_percent`.
6. `run_pipeline` menghasilkan 4 PNG (mask, overlay segmentasi, heatmap Grad-CAM, overlay Grad-CAM) + `measurements` + `summary_text`.
7. Service mengunggah 4 artefak **berurutan**; setelah semua sukses `progress.on_phase('uploading_results')`.
8. Update record: `status=completed`, `progress_percent=100`, `current_step=completed`, seluruh path, metrik, metadata model, `summary_text`, `completed_at`, `updated_at`.
9. Klien (`NewAnalysis`) polling `GET /api/analysis/{id}` tiap 2 detik; pada status terminal → navigasi ke `/analysis/{id}`.
10. `AnalysisResult` memuat detail: metadata, citra asli, mask, overlay, Grad-CAM, model analysis, ringkasan, disclaimer; signed URL berlaku 1 jam.

### D.2 Alur kegagalan pipeline

`_execute_pipeline` menangkap exception → menghapus artefak yang sudah terunggah → menulis `status=failed`, `error_code=AI_PIPELINE_ERROR`, `gradcam_status=failed`, `updated_at`, dan **hanya** menaikkan `progress_percent` bila nilainya lebih tinggi dari yang tersimpan → melempar `APIError` yang ditelan `_run_analysis_job` (tidak ada pemanggil HTTP).

### D.3 Ketergantungan antarmodul (ringkas)

```text
routes → controllers → services → { repositories → supabase, storage_service → supabase, ai.inference.pipeline }
ai.inference.pipeline → { preprocessing, segmentation, postprocessing, gradcam → model_service → model_config }
frontend pages → services → { lib/supabase, VITE_API_BASE_URL }
frontend pages → context/AuthContext → services/auth
```

Tidak ada siklus impor yang ditemukan. `ai` diimpor backend lewat `sys.path` root (backend dijalankan dari root atau `Backend/`), sehingga **backend bergantung pada direktori kerja** saat start — lihat §K.

---

## E. Analisis Fitur

Format tiap fitur: tujuan · aktor · prasyarat · bukti implementasi · alur · kegagalan.

### E.1 Sign Up

- **Tujuan:** membuat akun tenaga medis dan menyimpan atribut profesional awal.
- **Aktor:** calon pengguna. **Prasyarat:** belum login (`PublicOnlyRoute`).
- **Bukti:** `pages/auth/Register.tsx:15-130`, `services/auth.ts:131-190` (`registerUser`), `context/AuthContext.tsx` (`signUp`).
- **Alur:** validasi berurutan **nama → email kosong → format email → rumah sakit → bidang keahlian → kata sandi kosong → panjang ≥6 → konfirmasi**; `supabase.auth.signUp` sekali dengan metadata `full_name`, `hospital`, `hospital_name`, `primary_specialty`, `specialty`, dan objek `doctor_profile`.
- **Hasil:** bila `session` ada → state diisi, `PublicOnlyRoute` mengarahkan ke `/dashboard`. Bila tidak ada session → kartu "Registrasi Berhasil" + (jika `requiresEmailConfirmation`) keterangan email konfirmasi, lalu tombol "Masuk ke PIXEL-T" (`/login`) atau "Daftar dengan akun lain" (reset form).
- **Anti-enumerasi:** `existingAccountHint` dihitung di service tetapi **tidak** ditampilkan; copy identik untuk akun baru maupun email yang sudah terdaftar.
- **Kegagalan:** pesan dari `formatAuthError` (kredensial, email belum dikonfirmasi, duplikat, password lemah, rate limit, jaringan, signup disabled). Tidak ada rollback karena tidak ada baris profil terpisah saat registrasi.
- **Catatan:** `doctor_profiles` **tidak** dibuat saat registrasi; hanya `user_metadata`.

### E.2 Sign In

- **Bukti:** `Login.tsx:40-120`, `services/auth.ts:193-234`.
- **Alur:** validasi email & password tidak kosong → simpan/hapus email "remember" → `signIn` → `supabase.auth.signInWithPassword` → set user/session → `navigate(from, {replace:true})` dengan `from = location.state.from.pathname || '/dashboard'`.
- **Halaman:** dua panel; animasi pembuka mengunci form (`inert`, `disabled`) sampai stage reveal selesai; animasi tidak melakukan autentikasi.
- **Kegagalan:** pesan `formatAuthError`; password dikosongkan dari state setelah sukses; error tak terduga ditangkap.

### E.3 Remember my email

- **Bukti:** `lib/openingTimeline.ts:47,152-176`; `Login.tsx:58,90-96`.
- **Perilaku:** hanya email yang disimpan di `localStorage` kunci `pixel-t-remembered-email-v1`; **tidak pernah** password. Uncheck → kunci dihapus.
- **Batas:** checkbox tidak mengubah persistensi sesi Supabase (`persistSession: true` selalu aktif). Test memverifikasi hanya satu kunci tersimpan dan tidak memuat password.

### E.4 Forgot / Reset Password

- **Bukti:** `services/auth.ts:236-260`; `Login.tsx:118-150`.
- **Alur:** mode `reset` pada halaman yang sama → validasi format email → `supabase.auth.resetPasswordForEmail(email, {redirectTo: window.location.origin})` → pesan netral "If an account exists …".
- **Keterbatasan penting:** aplikasi **belum memiliki rute/flow penyelesaian reset** (halaman `updateUser({password})`). Tautan pemulihan mengarah ke origin aplikasi, dan tidak ada handler yang menangkap token recovery. Fitur ini baru "mengirim permintaan", belum "mengubah kata sandi". **Belum terverifikasi** apakah template email Supabase diarahkan ke halaman lain.

### E.5 Upload Image & validasi citra

- **Bukti klien:** `NewAnalysis.tsx:15-120` (`validateFile`), `selectFile`.
- **Validasi klien:** ekstensi ∈ {`.jpg`,`.jpeg`,`.png`}; MIME harus cocok dengan ekstensi; ukuran ≠ 0; ≤ 10 MB; nama file tanpa `..`, tanpa `/`/`\`, tanpa karakter kontrol; `createImageBitmap` harus berhasil dan dimensi > 0.
- **Validasi server:** `validate_and_decode_image` (`analysis_service.py:370-450`) — nama file, kosong, ≤ 10 MB, MIME deklarasi, `verify()` + `load()`, MIME isi harus sama, format JPEG/PNG, dimensi > 0.
- **Preview:** `URL.createObjectURL` dibersihkan pada perubahan/unmount.
- **Hasil:** panel status ("Image file ready for inference"), lalu tombol "Start analysis".

### E.6 Mulai analisis & status

- **Bukti:** `NewAnalysis.handleSubmit`, `services/analysis.createAnalysis`.
- **Alur:** POST → 202 → simpan `acceptedId` → panel progres + polling 2 detik.
- **Kegagalan:** `QUEUE_FULL` → pesan khusus; sesi berakhir → polling berhenti + instruksi login; error jaringan → notifikasi "retrying" dan polling berlanjut.
- **Catatan:** selama `acceptedId` aktif, tombol mulai dinonaktifkan dan file tidak dapat diganti.

### E.7 Pemrosesan & segmentasi polip

Lihat §G. Bukti: `Backend/ai/inference/segmentation.py:74-130`, `pipeline.py:88-140`.

### E.8 Grad-CAM

- **Bukti:** `Backend/ai/inference/gradcam.py:96-200`; dipanggil `pipeline.py` fase `gradcam`.
- **Metode:** forward pass kanonik (tanpa TTA) pada tensor 512; hook pada `decoder.blocks.4.conv2.0`; objektif = rata-rata logit pada area mask (mask dari prediksi threshold atau `target_mask`); bobot = rata-rata gradien spasial; `relu(sum(w·A))`; normalisasi min–max; kolormap "jet" deterministik; overlay alpha 0,45.
- **Mask kosong:** objektif `logits.sum()*0.0` → heatmap nol deterministik, bukan error.
- **Kegagalan:** target layer hilang → `GRADCAM_TARGET_LAYER_ERROR`; gradien hilang → `GRADCAM_GRADIENT_ERROR`; keduanya **menggagalkan seluruh job** (bukan non-blocking).

### E.9 Overlay visualisasi

- **Segmentasi:** `pipeline._segmentation_overlay` — piksel area mask dicampur 55% citra + 45% warna (R0,G190,B120).
- **Grad-CAM:** hasil `GradCAMResult.overlay`.
- **Mask biner:** PNG mode `L` nilai 0/255, di-resize ke ukuran citra asli dengan interpolasi NEAREST.

### E.10 Metrik segmentasi

- **Bukti:** `postprocessing.measure_mask`.
- **Field:** `segmentation_status` (`detected` bila area > 0), `area_pixels`, `area_ratio` (0–1), `bounding_box` (x_min,y_min,x_max,y_max), `bounding_width_pixels`, `bounding_height_pixels`.
- **Ditampilkan:** `area_pixels`, `area_ratio`, lebar/tinggi bbox. IoU/Dice/HD95 **tidak** dihitung per citra dan tidak ada di API — konsisten dengan `NEXT_STEPS` di UI yang sengaja tidak menjanjikannya.

### E.11 Penyimpanan & pengambilan hasil

- **Bukti:** `_execute_pipeline` (update), `get_analysis` (baca + signed URL).
- **Penyimpanan:** 5 objek per analisis (original + 4 artefak), path deterministik; `upsert=true` saat upload.
- **Pengambilan:** signed URL 3600 detik untuk citra asli, mask, overlay, heatmap, overlay Grad-CAM; kegagalan signed URL didegradasi menjadi `null` (tidak menggagalkan respons).

### E.12 History

- **Bukti:** `pages/history/History.tsx:68-200`; `AnalysisService.list_user_analyses`; `AnalysisRepository.list_by_user`.
- **Alur:** `GET /api/history` → repository `.order('created_at', desc).range(0,19)` → signed thumbnail per item → tabel/kartu.
- **Filter:** pencarian nama file, status, tanggal, dan pagination 10 baris — **semuanya di sisi klien** atas data yang dimuat.
- **Hapus:** modal konfirmasi → `DELETE /api/history/{id}` → item dihapus dari state.
- **Kegagalan:** `ErrorState` + retry; `EmptyState` bila kosong; state khusus "No matching analyses found" bila filter tidak cocok.

### E.13 Detail hasil analisis

- **Bukti:** `pages/analysis/AnalysisResult.tsx`.
- **Isi:** badge status, ID, nama file, waktu dibuat, dimensi asli, panel citra (asli/mask/overlay/Grad-CAM), tabel model analysis, ringkasan, disclaimer.
- **Polling:** 5 detik, maksimal 12 kali selama `processing`.
- **Kegagalan citra:** `onError` → placeholder "Image could not be loaded".

### E.14 Doctor Profile

- **Bukti:** `pages/profile/DoctorProfile.tsx`; `services/profile.ts`.
- **Baca:** `fetchDoctorProfile` → `doctor_profiles` via anon client (RLS) `.maybeSingle()`; jika error/kosong → fallback `user_metadata.doctor_profile` + field metadata registrasi.
- **Tampilan:** identitas + gelar, kelengkapan profil 11 kriteria (`calculateCompleteness`), afiliasi, pendidikan, pengalaman, biografi, statistik aktivitas (`listHistory`), data pribadi, UUID + copy.
- **Edit:** modal 5 tab; `editFormData` disalin dari profil (deep copy list); tambah/hapus entri dinamis dengan id `edu_/exp_<timestamp>_<random>`.
- **Validasi:** `fullName` wajib ≤150, `phone` ≤30, `bio` ≤1000, `strNumber` ≤50.
- **Simpan:** `saveDoctorProfile` → upsert `doctor_profiles` (`onConflict: user_id`) **dan** `auth.updateUser({data:{full_name, doctor_profile}})`. Bila salah satu berhasil → dianggap sukses; error hanya bila keduanya gagal.
- **Sukses:** state profil diperbarui, modal ditutup, banner 4 detik.

### E.15 Sign Out

- **Bukti:** `AppShell.tsx:113-134,366-394`.
- **Alur:** menu pengguna/menu mobile → modal "Sign out of PIXEL-T?" → "Yes" → `signOut()` → `supabase.auth.signOut()` + state lokal dikosongkan → `navigate('/login',{replace:true})`.
- **Kegagalan:** error dari Supabase tidak ditampilkan; navigasi tetap terjadi (state lokal sudah dikosongkan).

### E.16 Proteksi rute & otorisasi

- **Klien:** `ProtectedRoute` menunggu `loading`, lalu redirect ke `/login` dengan `state.from`. `PublicOnlyRoute` mencegah halaman auth diakses saat login.
- **Server:** setiap endpoint analisis memakai `@require_auth`; `user_id` selalu diambil dari token, **tidak pernah** dari body/query.
- **Kepemilikan data:** semua query repository memakai `.eq('user_id', user_id)`; record milik orang lain menghasilkan 404 (bukan 403) agar tidak membocorkan keberadaan data. Diuji di `tests/Backend/test_analysis.py::test_cross_user_get_is_hidden_as_not_found` dan `test_history.py::test_delete_case_e_foreign_id_is_hidden_as_not_found`.
- **Storage:** `validate_path_ownership` memastikan path 5 segmen, segmen[1] = user, kategori valid, nama file aman.

### E.17 Error handling, loading, polling, retry

| Area | Perilaku |
|---|---|
| Envelope API | `{success, data}` / `{success:false, error:{code,message}}` |
| 401 saat request | `authenticatedRequest` me-refresh sesi sekali lalu mengulang; gagal → "Sesi Anda telah berakhir" |
| Polling NewAnalysis | 2 detik, tanpa batas, berhenti pada status terminal atau unmount; error jaringan → lanjut |
| Polling AnalysisResult | 5 detik, **maksimal 12 kali**; berhenti tanpa pesan tambahan |
| Queue penuh | 429 `QUEUE_FULL` → pesan khusus di UI |
| Progress DB gagal | Ditelan & dihitung (`failed_writes`), tidak menggagalkan inferensi |
| Job gagal | `status=failed` + `error_code=AI_PIPELINE_ERROR`; detail teknis tidak dikirim |
| Stale | Backend menandai `stale:true` untuk record `processing` > 15 menit yang tidak ada di queue proses ini |

### E.18 Fitur yang **tidak** ada (dinyatakan eksplisit)

- Klasifikasi kanker/malignansi, skor keyakinan/probabilitas, rekomendasi terapi — tidak ada di kode (sesuai batas produk).
- Ekspor PDF/cetak rekam medis — tidak ada.
- Notifikasi email hasil analisis — tidak ada.
- Multi-user/rumah sakit/admin, pembagian peran — tidak ada (semua pengguna setara).
- Verifikasi STR oleh admin — tidak ada; `is_verified` hanya kolom.
- Endpoint `/api/auth/*` — tidak ada (lihat §I).

---

## F. Autentikasi dan Manajemen Akun

| Aspek | Implementasi | Bukti |
|---|---|---|
| Sign up | `supabase.auth.signUp` + metadata profesional | `services/auth.ts:131` |
| Session dari sign up | Ada → langsung masuk; tidak ada → kartu konfirmasi | `AuthContext.signUp` |
| Konfirmasi email | Tidak dikonfigurasi di repo; perilaku bergantung setelan proyek Supabase | **Belum terverifikasi** |
| Sign in | `signInWithPassword` | `services/auth.ts:193` |
| Reset password | Hanya permintaan email; tidak ada halaman penyelesaian | `services/auth.ts:236` |
| Penyimpanan sesi | `persistSession:true`, `autoRefreshToken:true`, `detectSessionInUrl:true` | `lib/supabase.ts` |
| Pemulihan sesi | `getSession()` saat mount + satu listener `onAuthStateChange` | `AuthContext` |
| Startup reset | **Sekali per sesi tab** (`sessionStorage`), memanggil `logoutUser()` sebelum restore | `AuthContext:33-60` |
| Remember email | `localStorage`, email saja | `lib/openingTimeline.ts:152` |
| Sign out | `signOut()` → state kosong → `/login` | `AppShell:123` |
| Proteksi halaman | `ProtectedRoute` + verifikasi token di setiap endpoint | `ProtectedRoute.tsx`, `core/auth.py` |
| Pengaitan user | `analyses.user_id` dan `doctor_profiles.user_id` = `auth.users(id)` | migrasi 001 & 004 |
| Isolasi lintas pengguna | Filter `user_id` di semua query + RLS + validasi path storage | §J |

**Perilaku startup reset (penting).** Pada mount pertama per tab, `AuthContext` menjalankan `logoutUser()`, yang memanggil `supabase.auth.signOut()`. Karena Supabase menyimpan sesi di `localStorage` bersama, membuka tab baru **mengakhiri sesi di semua tab** dan menghapus sesi tersimpan. Setelah itu `restoreSession()` berjalan dan (biasanya) tidak menemukan sesi. Konsekuensi: pengguna yang membuka PIXEL-T di tab kedua harus login ulang, dan tab pertama ikut ter-logout pada navigasi/refresh berikutnya. Ini bukan bug kosmetik, melainkan perubahan perilaku autentikasi.

---

## G. Pipeline AI dan Segmentasi

### G.1 Model yang benar-benar dipakai aplikasi

| Properti | Nilai | Bukti |
|---|---|---|
| Arsitektur | `smp.Unet`, encoder `resnet50`, `decoder_attention_type="scse"`, `classes=1`, `activation=None` | `model_service._build_model` |
| Bobot encoder saat load | `encoder_weights=None` (bobot berasal dari checkpoint, bukan unduhan ImageNet) | idem |
| Input | RGB, resize 512×512 BILINEAR, ImageNet mean/std | `preprocessing.py` |
| Checkpoint | `PIXEL-T_Scenario1_UNet_ResNet50_Ver22_best.pth` | `model_config.py:10` |
| Integritas | SHA-256 wajib cocok (konstanta `46521AE9…C581`) | `checkpoint_sha256_matches` |
| Load | `torch.load(weights_only=True)` + `load_state_dict(strict=True)` + `eval()` | `model_service.load` |
| Device | `MODEL_DEVICE` ∈ {auto,cpu,cuda,gpu}; auto → CUDA bila tersedia | `_select_device` |
| Threshold | 0,55 | `ModelConfig.threshold` |
| TTA | 5 skala (0,85;0,95;1,0;1,05;1,15) × 5 orientasi = **25 forward pass** | `segmentation.predict`, `count_forward_passes` |
| Postprocessing | close→open (kernel 3×3) → filter komponen <25 px → fill holes → approxPolyDP ε=0,005×perimeter | `postprocessing.py` |
| Grad-CAM layer | `decoder.blocks.4.conv2.0` | `ModelConfig.gradcam_target_layer` |

### G.2 Alur inferensi (detail)

1. `predict()` menyiapkan tensor 512 dan, untuk setiap skala ≠ 1,0, meng-interpolasi ke `round(512×scale/32)×32` (min 32) agar aman untuk stride ResNet50.
2. Untuk setiap skala, lima orientasi dijalankan: original, horizontal flip, vertical flip, rot90, rot270.
3. Setiap output logit → sigmoid → orientasi dipulihkan → diinterpolasi ke 512×512 → dikumpulkan.
4. Seluruh 25 peta dirata-rata; `binary_mask = probability >= 0,55` (uint8).
5. Postprocessing diterapkan pada mask 512, lalu `resize_binary_mask` ke ukuran citra asli (NEAREST).
6. Pengukuran & status dari mask final.
7. Grad-CAM dijalankan terpisah pada satu forward pass kanonik 512 (tanpa TTA).

### G.3 Training vs evaluasi vs inferensi (dibedakan tegas)

| Tahap | Bukti | Catatan |
|---|---|---|
| Training | `research/segmentationcolonpolyp-unet-resnet50-gradcam.ipynb` | 130 epoch, batch 16, LR 1e-4, encoder dibekukan sampai epoch 5, EMA 0,999, loss BCE 0,10 + Dice 0,40 + Tversky 0,35 (α=0,3; β=0,7; γ=0,75) + Lovasz 0,15, `pos_weight`≈15,87, AMP, gradient clipping 1,0 |
| Dataset | Notebook Cell 3 | **4.178 citra, 6 sumber**: BKAI-IGH-NeoPolyp (1.000), CVC-ClinicDB (612), CVC-ColonDB (380), ETIS-LaribPolypDB (196), Kvasir (1.000), HyperKvasir Polyp (990) — **semua citra berisi polip** ("tanpa citra normal") |
| Evaluasi | `research/PIXEL-T_Scenario1_Ver22_evaluation_results.csv` | Best epoch 83; Dice validasi (EMA) 0,9507; threshold terpilih 0,55; **Test Dice 0,9510; Test IoU 0,9136; Accuracy 0,9918; Precision 0,9568; Recall 0,9685; HD95 12,9049** (TTA + postproc) |
| Inferensi web | `Backend/ai/inference/*`, `Backend/ai/config/model_config.py` | Hyperparameter sama dengan config Ver.22 (kecuali `tta_enabled` tidak dibaca — §K) |

**Implikasi dataset tanpa citra normal (penting untuk BAB IV/pembahasan):** model tidak pernah belajar konsep "tidak ada polip". Status `not_detected` hanya muncul bila seluruh probabilitas < 0,55, bukan karena model mengenali kelas negatif. Karena itu, klaim performa pada citra tanpa polip tidak didukung evaluasi yang ada, dan risiko *false positive* pada citra normal belum terukur. Ini juga menjelaskan mengapa `Precision ≈ 0,9568` hanya berlaku pada distribusi data uji yang seluruhnya berpolip.

### G.4 Penanganan kondisi & error

| Kondisi | Perilaku |
|---|---|
| Checkpoint tidak ada | `ModelLoadError("Verified model checkpoint was not found.")` → job gagal |
| SHA-256 tidak cocok | `MODEL_CHECKPOINT_MISMATCH` → job gagal |
| Bentuk tensor tidak sesuai kontrak | `ModelConfigurationError` sebelum forward pass |
| Output bukan 1 kanal | `ModelLoadError` |
| Mask kosong | `segmentation_status=not_detected`, area 0, bbox null; Grad-CAM heatmap nol |
| Grad-CAM gagal | Seluruh job `failed` (blocking) |
| Upload artefak gagal | Artefak yang sudah terunggah dihapus; job `failed` |
| Update DB hasil gagal (return None) | `RuntimeError` → jalur gagal |

### G.5 GPU/CPU

Pemilihan device dapat diverifikasi dari kode. Pada mesin audit, `torch` tidak dapat dimuat sama sekali (DLL diblokir kebijakan OS), sehingga **tidak dapat diverifikasi** device yang benar-benar dipakai saat runtime di lingkungan ini. Waktu inferensi 25 pass pada CPU diperkirakan puluhan detik hingga beberapa menit; tidak diukur di sini.

---

## H. Struktur Database dan Storage

### H.1 `public.analyses` (migrasi 001–003)

| Kelompok | Kolom | Tipe/Catatan |
|---|---|---|
| Identitas | `id` | UUID PK, default `gen_random_uuid()` |
| Kepemilikan | `user_id` | UUID NOT NULL → `auth.users(id)` ON DELETE CASCADE |
| Siklus hidup | `status` | `processing`/`completed`/`failed` (CHECK) |
| Input | `original_image_path` (NOT NULL), `original_filename`, `original_mime_type`, `original_width`, `original_height` | |
| Segmentasi | `binary_mask_path`, `segmentation_overlay_path`, `segmentation_status` (CHECK detected/not_detected), `area_pixels`, `area_ratio` NUMERIC(7,4), `bounding_width_pixels`, `bounding_height_pixels` | |
| Grad-CAM | `gradcam_heatmap_path`, `gradcam_overlay_path`, `gradcam_target_layer`, `gradcam_method`, `gradcam_config_version`, `gradcam_status` (CHECK completed/failed) | 002 |
| Model | `model_architecture`, `model_version`, `model_config_version`, `model_input_size`, `model_threshold` NUMERIC(4,3), `tta_enabled`, `postprocessing_enabled`, `model_checkpoint_sha256`, `tta_scales` JSONB, `tta_orientations` JSONB | 002 |
| Ringkasan/error | `summary_text`, `error_code`, `error_message` | |
| Waktu | `created_at`, `completed_at`, `updated_at` | |
| Progres | `current_step` VARCHAR(64), `progress_percent` SMALLINT CHECK 0–100 | 003, nullable |

Indeks: `user_id`, `status`, `created_at DESC`, `(user_id, created_at DESC)`.

### H.2 `public.doctor_profiles` (migrasi 004)

`id` UUID PK; `user_id` UUID UNIQUE NOT NULL → `auth.users(id)` CASCADE; `full_name` NOT NULL; `phone`, `birth_date`, `city`; `profession_category`, `academic_title`, `primary_specialty`, `subspecialty`, `clinical_focus`, `hospital`, `department`, `clinical_role`, `years_experience`, `practice_address`, `str_number`; `is_verified` BOOLEAN default false; `bio`; `education` JSONB default `[]`; `experience` JSONB default `[]`; `created_at`, `updated_at`.

### H.3 Relasi

```text
auth.users (1) ──< analyses (N)          via analyses.user_id
auth.users (1) ─── doctor_profiles (1)   via doctor_profiles.user_id UNIQUE
analyses tidak memiliki relasi FK ke doctor_profiles.
```

Tidak ada tabel `users` aplikasi terpisah; profil dasar pengguna hidup di `auth.users.raw_user_meta_data`.

### H.4 Storage

- Bucket: `analysis-assets`, **privat**, batas 10 MB/file, MIME diizinkan `image/jpeg`, `image/png` (migrasi 001).
- Layout: `analysis/{user_id}/{analysis_id}/original/input.{jpg|png}`, `.../segmentation/mask.png`, `.../segmentation/overlay.png`, `.../gradcam/heatmap.png`, `.../gradcam/overlay.png`.
- Akses baca: signed URL 3600 detik yang dibuat backend dengan service role.
- **Orphan risk:** `ON DELETE CASCADE` pada `auth.users` menghapus baris `analyses` tanpa menyentuh objek storage.

### H.5 RLS (ringkas)

| Objek | SELECT | INSERT | UPDATE | DELETE |
|---|---|---|---|---|
| `analyses` | own | own | own | own |
| `doctor_profiles` | own | own | own | own |
| `storage.objects` (`analysis-assets`) | own folder | own folder | **tidak ada policy** | own folder |

Implikasi: klien dengan anon key + token pengguna dapat menulis langsung ke tabel dan folder miliknya tanpa melalui backend (lihat §J.3).

---

## I. API dan Kontrak Request–Response

### I.1 Endpoint yang benar-benar ada

| Method | Path | Auth | Sukses | Error utama |
|---|---|---|---|---|
| GET | `/api/health` | tidak | 200 `{success:true,data:{status:"ok"}}` | — |
| POST | `/api/analysis` | Bearer | **202** `{success:true,data:{analysis_id,status:"processing"}}` | 400 `MISSING_FILE`/`INVALID_IMAGE`/`EMPTY_FILE`/`FILE_TOO_LARGE`; 401 `UNAUTHORIZED`; 413 `FILE_TOO_LARGE`; 429 `QUEUE_FULL`; 500 `STORAGE_ERROR`/`DATABASE_ERROR` |
| GET | `/api/analysis/{id}` | Bearer | 200 `{success:true,data:{analysis,input,segmentation?,gradcam?,model_analysis?,model?,summary?}}` | 404 `ANALYSIS_NOT_FOUND` |
| GET | `/api/history` | Bearer | 200 `{success:true,data:{items:[…]}}` | 500 `DATABASE_ERROR` |
| DELETE | `/api/history/{id}` | Bearer | 200 `{success:true,message:"Analysis deleted successfully"}` | 404 `ANALYSIS_NOT_FOUND`; 500 `DATABASE_ERROR` |

Contoh `GET /api/analysis/{id}` (bentuk aktual, field opsional hanya muncul bila tersimpan):

```json
{
  "success": true,
  "data": {
    "analysis": {
      "id": "…", "status": "completed",
      "created_at": "…", "completed_at": "…",
      "original_filename": "case_01.png",
      "current_step": "completed", "progress_percent": 100
    },
    "input": {"original_image_url": "https://…", "width": 1024, "height": 768, "mime_type": "image/png"},
    "segmentation": {"binary_mask_url": "https://…", "overlay_url": "https://…"},
    "gradcam": {"heatmap_url": "https://…", "overlay_url": "https://…"},
    "model_analysis": {"segmentation_status": "detected", "area_pixels": 12345, "area_ratio": 0.0157, "bounding_width_pixels": 140, "bounding_height_pixels": 96},
    "model": {"architecture": "UNet", "version": "Scenario 1 Ver.22", "threshold": 0.55, "checkpoint_sha256": "…", "input_size": 512, "tta_enabled": true, "postprocessing_enabled": true, "gradcam_target_layer": "decoder.blocks.4.conv2.0", "gradcam_status": "completed"},
    "summary": {"text": "Model menghasilkan area segmentasi …"}
  }
}
```

### I.2 Selisih dokumentasi vs kode

| Item | `docs/APIContract.md` | Kode | Status |
|---|---|---|---|
| Register | `POST /api/auth/register` | tidak ada; klien memanggil Supabase langsung | **Selisih** |
| Login | `POST /api/auth/login` | tidak ada | **Selisih** |
| Current user | `GET /api/auth/me` | tidak ada; klien memakai `supabase.auth.getUser` | **Selisih** |
| Logout | `POST /api/auth/logout` | tidak ada; `supabase.auth.signOut` di klien | **Selisih** |
| Create analysis | 202 + polling | sesuai | Sesuai |
| History | tanpa parameter pagination | `limit=20` hard-coded di pemanggil | Sesuai kontrak, terbatas |
| Delete | 200 tanpa `data` | sesuai (`expectData:false`) | Sesuai |
| Error envelope | `{success:false,error:{code,message}}` | sesuai | Sesuai |

Dokumentasi juga menyebut `POST /api/analysis` dapat mengembalikan 413; kode memenuhi lewat `MAX_CONTENT_LENGTH` dan handler 413.

---

## J. Keamanan dan Otorisasi

### J.1 Yang sudah baik

- Service role key hanya ada di backend; frontend hanya memakai anon key (`lib/supabase.ts`).
- Token diverifikasi di server pada setiap endpoint analisis; `user_id` tidak pernah diambil dari input klien.
- Query kepemilikan memakai filter `user_id`; record asing → 404.
- Path storage divalidasi terhadap pola dan kepemilikan sebelum upload/download/signed/delete.
- Nama file diperiksa terhadap traversal (`..`, `/`, `\`, karakter kontrol) di klien dan server.
- MIME dideklarasikan harus sama dengan MIME hasil deteksi Pillow; file harus lolos `verify()` dan `load()`.
- Pesan error tidak membocorkan traceback, token, atau path internal.
- `formatAuthError` mencegah enumerasi akun pada registrasi dan reset.
- `.env` tidak dilacak git (hanya `.env.example`); log dan `dist/` juga tidak.

### J.2 Risiko

| Risiko | Bukti | Dampak |
|---|---|---|
| Startup reset mengakhiri sesi global saat tab baru dibuka | `AuthContext` | Ketersediaan/UX; sesi pengguna lain di perangkat sama ikut berakhir |
| RLS `analyses` mengizinkan INSERT/UPDATE/DELETE milik sendiri via PostgREST | migrasi 001 | Pengguna dapat membuat baris `completed` palsu, mengubah metrik, atau menghapus record tanpa melalui backend — integritas data ilmiah dapat dipertanyakan |
| RLS storage mengizinkan INSERT ke folder sendiri | migrasi 001 | Unggahan langsung melewati validasi MIME/ukuran aplikasi (batas bucket 10 MB & MIME tetap berlaku) |
| `is_verified` dapat diubah pemilik | migrasi 004 + `saveDoctorProfile` | Klaim verifikasi STR tanpa otoritas |
| Service role dipakai untuk semua operasi setelah verifikasi token | `analysis_service` | Bila ada bug filter, tidak ada lapisan RLS kedua yang menahan |
| Queue in-memory | `AnalysisJobQueue` | Restart proses meninggalkan record `processing` permanen; kapasitas 4 memungkinkan penolakan saat beban |
| Tidak ada rate limit per pengguna | tidak ditemukan di kode | Penyalahgunaan CPU (25 pass per unggahan) |
| `SECRET_KEY` default dev | `core/config.py:10` | Tidak dipakai Flask session, jadi dampak rendah; tetap sebaiknya diwajibkan di produksi |
| CORS `split(',')` tanpa `strip()` | `core/config.py:16` | Spasi setelah koma membuat origin tidak cocok |

---

## K. Bug Potensial dan Inkonsistensi

| # | Temuan | Bukti | Kepastian | Dampak | Prioritas | Saran (tidak diterapkan) |
|---|---|---|---|---|---|---|
| K1 | Tab baru memicu logout global | `AuthContext.tsx` startup reset | Tinggi | Pengguna ter-logout tanpa sebab; sesi tab lain berakhir | Tinggi | Batasi reset pada flag sekali seumur aplikasi, atau jangan panggil `signOut` (cukup jangan restore) |
| K2 | Riwayat maksimal 20 record | `analysis_controller.list_history` → `list_user_analyses(user_id)` (default 20); UI mem-paginate data ≤20 | Tinggi | Analisis ke-21 dst. tidak dapat diakses | Tinggi | Teruskan `limit`/`offset` dari query string; tambah tombol "load more" atau pagination server |
| K3 | Polling hasil berhenti di 12×5 s | `AnalysisResult.tsx:MAX_POLL_ATTEMPTS` | Tinggi | Halaman dapat menampilkan "processing" selamanya pada inferensi CPU yang lambat | Tinggi | Perpanjang/beri batas berbasis waktu + tombol "Refresh" |
| K4 | `tta_enabled` tidak dibaca | `segmentation.count_forward_passes` & `_predict_scale` (komentar eksplisit) | Tinggi | Metadata DB melaporkan `tta_enabled:true` padahal perilaku dikendalikan `multiscale_enabled` | Sedang | Hormati flag atau hapus dari skema/metadata |
| K5 | `stale` diabaikan klien | `get_analysis` menambah `stale`; tipe `AnalysisDetail` tidak punya field itu | Tinggi | Record macet tidak pernah ditandai ke pengguna | Sedang | Tambahkan field + banner "analisis macet" |
| K6 | `error_code` API selalu `ANALYSIS_FAILED` | `get_analysis` menimpa `record.error_code` | Tinggi | Kehilangan kode penyebab (`AI_PIPELINE_ERROR`, dll.) | Rendah | Teruskan `error_code` tersimpan |
| K7 | Penyimpanan profil parsial dianggap sukses | `saveDoctorProfile` (error hanya bila keduanya gagal) | Tinggi | Data DB dan metadata dapat berbeda tanpa peringatan | Sedang | Laporkan status per jalur atau jadikan metadata fallback eksplisit |
| K8 | `/history/:id` tidak tertaut dari mana pun | `AppRoutes.tsx:73`; tidak ada `Link`/`navigate` ke rute itu | Tinggi | Dua UI detail (HistoryDetail vs AnalysisResult) membingungkan; rute hanya bisa diakses manual | Rendah | Hapus rute atau tautkan dari tabel History |
| K9 | `@supabase/ssr` tidak dipakai | `package.json` root | Tinggi | Dependensi & lockfile yatim | Rendah | Hapus dari root |
| K10 | `run_segmentation`/`run_gradcam` tidak dipakai | `analysis_service.py:970,983` | Tinggi | Dead code; membingungkan pembaca skripsi | Rendah | Hapus atau dokumentasikan sebagai hook |
| K11 | Variabel env di `.env.example` tidak dibaca kode | `MODEL_PATH`, `MODEL_VERSION`, `MODEL_CONFIG_VERSION`, `MODEL_INPUT_SIZE`, `MODEL_THRESHOLD`, `TTA_ENABLED`, `POSTPROCESSING_ENABLED`, `GRADCAM_TARGET_LAYER`, `MODEL_INFERENCE_ENABLED` | Tinggi (kecuali `MODEL_CHECKPOINT_PATH`, `MODEL_DEVICE`) | Ekspektasi "konfigurasi lewat env" tidak terpenuhi; hyperparameter konstan | Sedang | Samakan: baca env di `ModelConfig` atau hapus dari template |
| K12 | Migrasi 002/003 tidak idempoten | `ADD CONSTRAINT` tanpa `IF NOT EXISTS` | Tinggi | Re-run migrasi gagal | Rendah | Bungkus dalam `DO $$ … $$` atau cek katalog |
| K13 | Objek storage yatim saat user dihapus | `ON DELETE CASCADE` tanpa trigger storage | Tinggi (skema) | Biaya & sisa data medis | Sedang | Trigger/cleanup job |
| K14 | Cleanup artefak best-effort | `_execute_pipeline` menghapus di `except` dengan `pass` | Tinggi | Artefak parsial dapat tertinggal bila storage gagal | Rendah | Catat kegagalan cleanup |
| K15 | Job `processing` permanen setelah restart | desain queue in-memory (didokumentasikan) | Tinggi | UI menunggu tanpa akhir | Sedang | Tandai `failed` saat startup untuk record tanpa job |
| K16 | `listHistory` dipanggil di DoctorProfile tanpa cek user | `DoctorProfile.loadActivity` pada mount | Sedang | Jika tanpa sesi → error ditampilkan di kartu aktivitas | Rendah | Guard `if (!user) return` |
| K17 | `MAX_CONTENT_LENGTH` 11 MB vs batas 10 MB | `config.py:13` vs `MAX_FILE_SIZE_BYTES` | Tinggi | Konsisten secara desain (header multipart), tetapi pesan 413 berbunyi "10 MB" | Rendah | Samakan angka/pesan |
| K18 | Cleanup setelah `QUEUE_FULL` best-effort | `create_analysis` | Tinggi | Record `processing` yatim bila dua pembersihan gagal | Rendah | Sudah ditangani penanda `stale`; dokumentasikan |

---

## L. Terverifikasi vs Belum Terverifikasi

### Terverifikasi dari kode/konfigurasi/migrasi

- Daftar endpoint, bentuk request/response, dan kode error.
- Skema tabel, constraint, indeks, dan policy RLS.
- Struktur path storage dan validasi kepemilikan.
- Hyperparameter model, nilai threshold, jumlah forward pass, urutan postprocessing.
- Metrik evaluasi Ver.22 (CSV) dan konfigurasi training (JSON + notebook).
- Perilaku polling, validasi klien, state UI, dan pesan pengguna.
- 245 test frontend lulus di mesin audit.

### Terverifikasi dari eksekusi

| Pemeriksaan | Hasil |
|---|---|
| `cd frontend && npm test` | **17 file, 245 test lulus**, 33 detik |
| `.venv/Scripts/python.exe -m pytest tests/backend -q` | **Gagal saat import**, bukan karena asersi: `OSError [WinError 4551]` — `torch/lib/c10_cuda.dll` diblokir Application Control |
| Test AI (`tests/ai`) | Tidak dijalankan (alasan sama) |
| `npm run build` / `tsc -b` | Tidak dijalankan (di luar lingkup audit baca-saja) |

### Belum terverifikasi

- Konfigurasi proyek Supabase yang sebenarnya (email confirmation, template reset, batas rate limit, kebijakan password).
- Apakah migrasi 001–004 sudah diterapkan pada database aktif.
- Device (CPU/GPU) dan waktu inferensi nyata di lingkungan pengguna.
- Apakah `stale` pernah muncul pada data produksi.
- Apakah storage benar-benar privat pada proyek Supabase aktif (migrasi menyatakan privat).
- Perilaku email konfirmasi dan tautan recovery.
- Kualitas klinis keluaran model (di luar lingkup audit kode; memerlukan evaluasi terpisah).

---

## M. Indeks Bukti

| Topik | Lokasi |
|---|---|
| Factory & CORS | `Backend/src/__init__.py` |
| Konfigurasi | `Backend/src/core/config.py` |
| Middleware auth | `Backend/src/core/auth.py::require_auth` |
| Envelope error | `Backend/src/core/errors.py` |
| Klien Supabase | `Backend/src/core/supabase.py` |
| Endpoint | `Backend/src/routes/analysis.py`, `routes/health.py` |
| Controller | `Backend/src/controllers/analysis_controller.py` |
| Validasi citra | `analysis_service.py::validate_and_decode_image` |
| Kompensasi & queue | `analysis_service.py::create_analysis`, `AnalysisJobQueue` |
| Progress | `analysis_service.py::AnalysisProgressReporter` |
| Eksekusi pipeline | `analysis_service.py::_execute_pipeline` |
| Baca detail | `analysis_service.py::get_analysis` |
| Riwayat (limit 20) | `analysis_service.py::list_user_analyses`, `analysis_repository.py::list_by_user` |
| Hapus | `analysis_service.py::delete_analysis` |
| Path & signed URL | `Backend/src/services/storage_service.py` |
| CRUD & validasi status | `Backend/src/repositories/analysis_repository.py` |
| Konfigurasi model | `Backend/ai/config/model_config.py` |
| Loader & device | `Backend/ai/inference/model_service.py` |
| Preprocessing | `Backend/ai/inference/preprocessing.py::prepare_image` |
| TTA & threshold | `Backend/ai/inference/segmentation.py::predict`, `_predict_scale`, `count_forward_passes` |
| Postprocessing & metrik | `Backend/ai/inference/postprocessing.py` |
| Grad-CAM | `Backend/ai/inference/gradcam.py::generate_gradcam` |
| Orkestrasi 5 fase | `Backend/ai/inference/pipeline.py::run_pipeline` |
| Skema & RLS | `database/migrations/001…004` |
| Klien API | `Frontend/src/utils/analysis.ts` |
| Auth klien | `Frontend/src/utils/auth.ts`, `context/AuthContext.tsx` |
| Profil | `Frontend/src/utils/profile.ts`, `pages/profile/DoctorProfile.tsx` |
| Validasi + polling unggah | `Frontend/src/pages/analysis/NewAnalysis.tsx` |
| Hasil + polling 12× | `Frontend/src/pages/analysis/AnalysisResult.tsx` |
| Riwayat & hapus | `Frontend/src/pages/history/History.tsx` |
| Sign out | `Frontend/src/components/layout/AppShell.tsx` |
| Rute | `Frontend/src/routes/AppRoutes.tsx`, `components/auth/ProtectedRoute.tsx`, `PublicOnlyRoute.tsx` |
| Remember email | `Frontend/src/lib/openingTimeline.ts` |
| Metrik model | `research/PIXEL-T_Scenario1_Ver22_evaluation_results.csv`, `…_config.json` |
| Dataset & training | `research/segmentationcolonpolyp-unet-resnet50-gradcam.ipynb` (Cell 3) |

---

## N. Rekomendasi Urutan Pekerjaan Berikutnya

1. **Perbaiki kebenaran perilaku yang memengaruhi demo skripsi:** startup logout (K1), batas 20 riwayat (K2), polling berhenti (K3). Ketiganya terlihat langsung oleh penguji.
2. **Selaraskan metadat dengan perilaku:** `tta_enabled` (K4), `stale` (K5), `error_code` (K6), env yang tidak dibaca (K11).
3. **Perkuat integritas data:** cabut INSERT/UPDATE/DELETE langsung pada `analyses` untuk peran `authenticated` (biarkan backend dengan service role yang menulis), dan jaga `is_verified` agar tidak dapat diubah klien.
4. **Selaraskan dokumentasi:** perbarui `APIContract.md` agar tidak mencantumkan `/api/auth/*`, atau implementasikan endpoint tersebut bila memang diinginkan.
5. **Lengkapi flow reset password** (halaman `updateUser({password})` + penanganan token recovery) atau nyatakan sebagai batasan sistem pada skripsi.
6. **Jalankan test Backend/AI** di lingkungan yang mengizinkan DLL PyTorch (mis. WSL/Linux) agar klaim pengujian lengkap.
7. **Untuk BAB IV:** gunakan `docs/diagrams/*.puml` yang sudah ada; perbaiki dua hal yang telah dikoreksi — Grad-CAM bersifat *blocking*, dan History memiliki fitur hapus.
