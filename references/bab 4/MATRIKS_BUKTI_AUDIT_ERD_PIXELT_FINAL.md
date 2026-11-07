# Matriks Bukti Audit Independen ERD PIXEL-T Final

**Tanggal:** 5 November 2026  
**Sumber kebenaran:** `database/migrations/001–008.sql`, source code backend/frontend, dan uji backend  
**Objek audit:** `references/bab 4/ERD_PIXELT_FINAL.*` dan revisi `ERD_PIXELT_FINAL_AUDITED.*`  
**Prinsip:** setiap klaim ERD harus memiliki bukti migration dan/atau source code. Tidak ada kredensial dalam dokumen ini.

Legenda status: ✅ DIVERIFIKASI · ⚠️ DIVERIFIKASI DENGAN CATATAN · ❌ TIDAK SESUAI

---

## A. Matriks Entitas

| No. | Bagian ERD | Klaim | Elemen | Bukti Migration | Bukti Source Code | Bukti Diagram | Status | Dampak | Rekomendasi |
|---|---|---|---|---|---|---|---|---|---|
| A-1 | Entitas | Ada entitas User | `User (auth.users)` | Layanan Supabase Auth; direferensikan FK dari `analyses.user_id` (001 L17) dan `doctor_profiles.user_id` (004 L12) | `auth.ts` signUp/signIn; `AuthContext.tsx` | `ent_user`, 5 atribut | ✅ | Entitas eksternal terwakili | Pertahankan |
| A-2 | Entitas | Ada entitas doctor_profiles | `doctor_profiles` | 004 L10–47 (+006, +007) | `profile.ts` upsert; `admin_service.py` | `ent_doctor`, 29 atribut | ✅ | Tabel profil klinisi | Pertahankan |
| A-3 | Entitas | Ada entitas analyses | `analyses` | 001 L14–64 (+002, +003) | `analysis_repository.py`; `analysis_service.py` | `ent_analyses`, 39 atribut | ✅ | Tabel analisis citra | Pertahankan |
| A-4 | Bukan entitas | Storage bucket tidak dimodelkan sebagai entitas | `analysis-assets`, `profile-avatars` | 001 L107–118; 005 L15–18 | `storage_service.py` | Tidak ada vertex bucket | ✅ | Mencegah ERD salah kategori | Catat di narasi akademik |
| A-5 | Bukan entitas | Controller/service/repository bukan entitas ERD | Flask layers | — | `backend/app/**` | Tidak ada vertex layer | ✅ | Sesuai lingkup model data | Pertahankan |

---

## B. Matriks Atribut

### B.1 `User (auth.users)` — 5 atribut

| No. | Bagian ERD | Klaim | Elemen | Bukti Migration | Bukti Source Code | Bukti Diagram | Status | Dampak | Rekomendasi |
|---|---|---|---|---|---|---|---|---|---|
| B1-1 | Atribut | PK User | `id : uuid (PK)` | Supabase Auth `auth.users.id` | `user.id` di `auth.ts` L306 | `ent_user_a0` | ✅ | Identitas pengguna | Pertahankan |
| B1-2 | Atribut | Email pengguna | `email : varchar` | Supabase Auth | `registerUser` signUp email | `ent_user_a1` | ✅ | Login/kontak | Pertahankan |
| B1-3 | Atribut | Metadata pendaftaran | `raw_user_meta_data : jsonb` | Dibaca trigger 008 L37, L54–56, L95–97 | `registerUser` metadata (L150–161) | `ent_user_a2` | ✅ | Sumber data trigger | Pertahankan |
| B1-4 | Atribut | App metadata (role admin) | `raw_app_meta_data : jsonb` | 007 L53–70; 008 L38 | `auth.ts` L328–334 (`app_metadata.role`) | `ent_user_a3` | ✅ | Otorisasi admin | Pertahankan |
| B1-5 | Atribut | Waktu pembuatan akun | `created_at : timestamptz` | Supabase Auth | — | `ent_user_a4` | ✅ | Audit akun | Pertahankan |

### B.2 `doctor_profiles` — 29 atribut

| No. | Bagian ERD | Klaim | Elemen | Bukti Migration | Bukti Source Code | Bukti Diagram | Status | Dampak | Rekomendasi |
|---|---|---|---|---|---|---|---|---|---|
| B2-1 | Atribut | PK profil | `id : uuid (PK)` | 004 L11 | `admin_service` eq('id', doctor_id) | `ent_doctor_a0` | ✅ | Identitas profil | Pertahankan |
| B2-2 | Atribut | FK pemilik + unik | `user_id : uuid (FK, UNIQUE)` | 004 L12, L46 | `profile.ts` L149–163 (onConflict user_id) | `ent_doctor_a1` | ✅ | Relasi 1:0..1 | Pertahankan |
| B2-3 | Atribut | Nama lengkap | `full_name : text` | 004 L15 | `profile.ts` payload | `ent_doctor_a2` | ✅ | Data klinisi | Pertahankan |
| B2-4 | Atribut | Telepon | `phone : text` | 004 L16 | `profile.ts` | `ent_doctor_a3` | ✅ | Kontak | Pertahankan |
| B2-5 | Atribut | Tanggal lahir | `birth_date : date` | 004 L17 | `profile.ts` | `ent_doctor_a4` | ✅ | Demografi | Pertahankan |
| B2-6 | Atribut | Kota | `city : text` | 004 L18 | `profile.ts` | `ent_doctor_a5` | ✅ | Domisili | Pertahankan |
| B2-7 | Atribut | Kategori profesi | `profession_category : text` | 004 L21 | `profile.ts` | `ent_doctor_a6` | ✅ | Klasifikasi | Pertahankan |
| B2-8 | Atribut | Gelar akademik | `academic_title : text` | 004 L22 | `profile.ts` | `ent_doctor_a7` | ✅ | Profil | Pertahankan |
| B2-9 | Atribut | Spesialisasi utama | `primary_specialty : text` | 004 L23 | trigger 008 L56; `profile.ts` | `ent_doctor_a8` | ✅ | Profil klinis | Pertahankan |
| B2-10 | Atribut | Subspesialisasi | `subspecialty : text` | 004 L24 | `profile.ts` | `ent_doctor_a9` | ✅ | Profil klinis | Pertahankan |
| B2-11 | Atribut | Fokus klinis | `clinical_focus : text` | 004 L25 | `profile.ts` | `ent_doctor_a10` | ✅ | Profil klinis | Pertahankan |
| B2-12 | Atribut | Rumah sakit | `hospital : text` | 004 L26 | trigger 008 L55 | `ent_doctor_a11` | ✅ | Afiliasi | Pertahankan |
| B2-13 | Atribut | Departemen | `department : text` | 004 L27 | `profile.ts` | `ent_doctor_a12` | ✅ | Afiliasi | Pertahankan |
| B2-14 | Atribut | Peran klinis | `clinical_role : text` | 004 L28 | `profile.ts` | `ent_doctor_a13` | ✅ | Profil | Pertahankan |
| B2-15 | Atribut | Pengalaman (tahun) | `years_experience : text` | 004 L29 | `profile.ts` | `ent_doctor_a14` | ✅ | Profil | Pertahankan |
| B2-16 | Atribut | Alamat praktik | `practice_address : text` | 004 L30 | `profile.ts` | `ent_doctor_a15` | ✅ | Profil | Pertahankan |
| B2-17 | Atribut | Nomor STR | `str_number : text` | 004 L31 | `profile.ts` | `ent_doctor_a16` | ✅ | Legalitas | Pertahankan |
| B2-18 | Atribut | Status verifikasi | `is_verified : boolean` | 004 L32 (default false) | trigger 008 L59 | `ent_doctor_a17` | ✅ | Verifikasi | Pertahankan |
| B2-19 | Atribut | Bio | `bio : text` | 004 L35 | `profile.ts` | `ent_doctor_a18` | ✅ | Profil | Pertahankan |
| B2-20 | Atribut | Riwayat pendidikan | `education : jsonb` | 004 L38 (`[]`) | `profile.ts` | `ent_doctor_a19` | ✅ | Profil | Pertahankan |
| B2-21 | Atribut | Riwayat pengalaman | `experience : jsonb` | 004 L39 (`[]`) | `profile.ts` | `ent_doctor_a20` | ✅ | Profil | Pertahankan |
| B2-22 | Atribut | URL avatar | `avatar_url : text` | 006 L14–15 | `profile.ts` L124, L360 | `ent_doctor_a21` | ✅ | Foto profil | Pertahankan |
| B2-23 | Atribut | Peran akun | `role : text` | 007 L24–25 (default 'doctor') | `fetchUserProfileStatus` `auth.ts` L310 | `ent_doctor_a22` | ✅ | Otorisasi dokter | Pertahankan |
| B2-24 | Atribut | Status akun | `account_status : text` | 007 L28–29 (default 'pending') | `auth.ts` L311; `admin_service` | `ent_doctor_a23` | ✅ | Gerbang akses | Pertahankan |
| B2-25 | Atribut | FK penyetuju | `approved_by : uuid (FK)` | 007 L33 (`REFERENCES auth.users(id)`, nullable) | `admin_service.py` L192, L288 | `ent_doctor_a24` | ⚠️ | Relasi ke admin | Digambar eksplisit di revisi audited |
| B2-26 | Atribut | Waktu persetujuan | `approved_at : timestamptz` | 007 L34 | `admin_service.py` L193, L289 | `ent_doctor_a25` | ✅ | Jejak audit | Pertahankan |
| B2-27 | Atribut | Alasan penolakan | `rejection_reason : text` | 007 L35 | `admin_service.py` L290 | `ent_doctor_a26` | ✅ | Jejak audit | Pertahankan |
| B2-28 | Atribut | Waktu dibuat | `created_at : timestamptz` | 004 L42 | — | `ent_doctor_a27` | ✅ | Audit | Pertahankan |
| B2-29 | Atribut | Waktu diperbarui | `updated_at : timestamptz` | 004 L43 | `admin_service.py` L195, L291 | `ent_doctor_a28` | ✅ | Audit | Pertahankan |

### B.3 `analyses` — 39 atribut

| No. | Bagian ERD | Klaim | Elemen | Bukti Migration | Bukti Source Code | Bukti Diagram | Status | Dampak | Rekomendasi |
|---|---|---|---|---|---|---|---|---|---|
| B3-1 | Atribut | PK analisis | `id : uuid (PK)` | 001 L16 | `analysis_repository.py` L71–98 | `ent_analyses_a0` | ✅ | Identitas analisis | Pertahankan |
| B3-2 | Atribut | FK pemilik | `user_id : uuid (FK)` | 001 L17 | `analysis_repository.py` L53 | `ent_analyses_a1` | ✅ | Relasi 1:* | Pertahankan |
| B3-3 | Atribut | Status siklus hidup | `status : varchar(20)` | 001 L20–21 | `analysis_repository.py` L56–58 | `ent_analyses_a2` | ✅ | State machine | Pertahankan |
| B3-4 | Atribut | Path citra asli | `original_image_path : text` | 001 L24 | `analysis_service.py` L369+ | `ent_analyses_a3` | ✅ | Storage | Pertahankan |
| B3-5 | Atribut | Nama file asli | `original_filename : text` | 001 L25 | `create_analysis` | `ent_analyses_a4` | ✅ | Metadata | Pertahankan |
| B3-6 | Atribut | MIME type | `original_mime_type : varchar(50)` | 001 L26 | `analysis_service.py` validasi | `ent_analyses_a5` | ✅ | Metadata | Pertahankan |
| B3-7 | Atribut | Lebar citra | `original_width : integer` | 001 L27 | — | `ent_analyses_a6` | ✅ | Metadata | Pertahankan |
| B3-8 | Atribut | Tinggi citra | `original_height : integer` | 001 L28 | — | `ent_analyses_a7` | ✅ | Metadata | Pertahankan |
| B3-9 | Atribut | Path binary mask | `binary_mask_path : text` | 001 L31 | `analysis_repository.py` L133+ | `ent_analyses_a8` | ✅ | Artefak segmentasi | Pertahankan |
| B3-10 | Atribut | Path overlay segmentasi | `segmentation_overlay_path : text` | 001 L32 | `analysis_repository.py` | `ent_analyses_a9` | ✅ | Artefak | Pertahankan |
| B3-11 | Atribut | Status segmentasi | `segmentation_status : varchar(20)` | 001 L33–34 | `analysis_repository.py` L31, L61–62 | `ent_analyses_a10` | ✅ | State segmentasi | Pertahankan |
| B3-12 | Atribut | Luas area (piksel) | `area_pixels : integer` | 001 L35 | pipeline AI | `ent_analyses_a11` | ✅ | Metrik | Pertahankan |
| B3-13 | Atribut | Rasio area | `area_ratio : numeric(7,4)` | 001 L36 | pipeline AI | `ent_analyses_a12` | ✅ | Metrik | Pertahankan |
| B3-14 | Atribut | Lebar bounding box | `bounding_width_pixels : integer` | 001 L37 | pipeline AI | `ent_analyses_a13` | ✅ | Metrik | Pertahankan |
| B3-15 | Atribut | Tinggi bounding box | `bounding_height_pixels : integer` | 001 L38 | pipeline AI | `ent_analyses_a14` | ✅ | Metrik | Pertahankan |
| B3-16 | Atribut | Path heatmap Grad-CAM | `gradcam_heatmap_path : text` | 001 L41 | pipeline AI | `ent_analyses_a15` | ✅ | Artefak XAI | Pertahankan |
| B3-17 | Atribut | Path overlay Grad-CAM | `gradcam_overlay_path : text` | 001 L42 | pipeline AI | `ent_analyses_a16` | ✅ | Artefak XAI | Pertahankan |
| B3-18 | Atribut | Target layer Grad-CAM | `gradcam_target_layer : varchar(100)` | 001 L43 | pipeline AI | `ent_analyses_a17` | ✅ | Konfigurasi XAI | Pertahankan |
| B3-19 | Atribut | Metode Grad-CAM | `gradcam_method : varchar(50)` | 001 L44 | pipeline AI | `ent_analyses_a18` | ✅ | Konfigurasi XAI | Pertahankan |
| B3-20 | Atribut | Versi konfig Grad-CAM | `gradcam_config_version : varchar(50)` | 001 L45 | pipeline AI | `ent_analyses_a19` | ✅ | Reproducibility | Pertahankan |
| B3-21 | Atribut | Status Grad-CAM | `gradcam_status : varchar(20)` | 002 L6–9 | pipeline AI | `ent_analyses_a20` | ✅ | State XAI | Pertahankan |
| B3-22 | Atribut | Arsitektur model | `model_architecture : varchar(100)` | 001 L48 | pipeline AI | `ent_analyses_a21` | ✅ | Reproducibility | Pertahankan |
| B3-23 | Atribut | Versi model | `model_version : varchar(50)` | 001 L49 | pipeline AI | `ent_analyses_a22` | ✅ | Reproducibility | Pertahankan |
| B3-24 | Atribut | Versi konfig model | `model_config_version : varchar(50)` | 001 L50 | pipeline AI | `ent_analyses_a23` | ✅ | Reproducibility | Pertahankan |
| B3-25 | Atribut | Ukuran input model | `model_input_size : integer` | 001 L51 | pipeline AI | `ent_analyses_a24` | ✅ | Reproducibility | Pertahankan |
| B3-26 | Atribut | Ambang model | `model_threshold : numeric(4,3)` | 001 L52 | pipeline AI | `ent_analyses_a25` | ✅ | Reproducibility | Pertahankan |
| B3-27 | Atribut | SHA-256 checkpoint | `model_checkpoint_sha256 : varchar(64)` | 002 L3 | pipeline AI | `ent_analyses_a26` | ✅ | Reproducibility | Pertahankan |
| B3-28 | Atribut | TTA aktif | `tta_enabled : boolean` | 001 L53 | pipeline AI | `ent_analyses_a27` | ✅ | Reproducibility | Pertahankan |
| B3-29 | Atribut | Skala TTA | `tta_scales : jsonb` | 002 L4 | pipeline AI | `ent_analyses_a28` | ✅ | Reproducibility | Pertahankan |
| B3-30 | Atribut | Orientasi TTA | `tta_orientations : jsonb` | 002 L5 | pipeline AI | `ent_analyses_a29` | ✅ | Reproducibility | Pertahankan |
| B3-31 | Atribut | Postprocessing aktif | `postprocessing_enabled : boolean` | 001 L54 | pipeline AI | `ent_analyses_a30` | ✅ | Reproducibility | Pertahankan |
| B3-32 | Atribut | Ringkasan teks | `summary_text : text` | 001 L57 | `analysis_service.py` | `ent_analyses_a31` | ✅ | Hasil | Pertahankan |
| B3-33 | Atribut | Kode error | `error_code : varchar(50)` | 001 L58 | `analysis_service.py` | `ent_analyses_a32` | ✅ | Diagnostik | Pertahankan |
| B3-34 | Atribut | Pesan error | `error_message : text` | 001 L59 | `analysis_service.py` | `ent_analyses_a33` | ✅ | Diagnostik | Pertahankan |
| B3-35 | Atribut | Langkah saat ini | `current_step : varchar(64)` | 003 L6 | instrumentasi progres | `ent_analyses_a34` | ✅ | Progres | Pertahankan |
| B3-36 | Atribut | Persen progres | `progress_percent : smallint` | 003 L7, L9–11 | instrumentasi progres | `ent_analyses_a35` | ✅ | Progres | Pertahankan |
| B3-37 | Atribut | Waktu dibuat | `created_at : timestamptz` | 001 L62 | `analysis_repository.py` list | `ent_analyses_a36` | ✅ | Urutan riwayat | Pertahankan |
| B3-38 | Atribut | Waktu selesai | `completed_at : timestamptz` | 001 L63 | `analysis_service.py` | `ent_analyses_a37` | ✅ | Metrik waktu | Pertahankan |
| B3-39 | Atribut | Waktu diperbarui | `updated_at : timestamptz` | 001 L64 | `analysis_repository.py` update | `ent_analyses_a38` | ✅ | Audit | Pertahankan |

---

## C. Matriks Primary Key, Foreign Key, Constraint

| No. | Bagian ERD | Klaim | Elemen | Bukti Migration | Bukti Source Code | Bukti Diagram | Status | Dampak | Rekomendasi |
|---|---|---|---|---|---|---|---|---|---|
| C-1 | PK | PK doctor_profiles | `doctor_profiles.id` | 004 L11 | `admin_service` eq('id', ...) | `ent_doctor_a0` | ✅ | Unik | Pertahankan |
| C-2 | PK | PK analyses | `analyses.id` | 001 L16 | `analysis_repository.py` L71 | `ent_analyses_a0` | ✅ | Unik | Pertahankan |
| C-3 | FK | doctor_profiles → auth.users | `user_id` NOT NULL + CASCADE | 004 L12 | `profile.ts`; trigger 008 L44–60 | `ent_doctor_a1` + garis | ✅ | Kepemilikan | Pertahankan |
| C-4 | FK | analyses → auth.users | `user_id` NOT NULL + CASCADE | 001 L17 | `analysis_repository.py` L53 | `ent_analyses_a1` + garis | ✅ | Kepemilikan | Pertahankan |
| C-5 | FK | doctor_profiles → auth.users | `approved_by` nullable | 007 L33 | `admin_service.py` L192, L288 | `ent_doctor_a24` + garis (audited) | ⚠️ | Jejak admin | Garis ditambahkan di revisi audited |
| C-6 | UNIQUE | Satu profil per user | `doctor_profiles_user_id_key` | 004 L46 | `profile.ts` onConflict | Label `0..1` | ✅ | Kardinalitas | Pertahankan |
| C-7 | CHECK | Status siklus hidup | `processing/completed/failed` | 001 L20–21 | `analysis_repository.py` L24–29 | — | ✅ | Integritas | Pertahankan |
| C-8 | CHECK | Status segmentasi | `segmentation_status` | 001 L33–34 | `analysis_repository.py` L31 | — | ✅ | Integritas | Pertahankan |
| C-9 | CHECK | Status Grad-CAM | `gradcam_status` | 002 L8–10 | pipeline AI | — | ✅ | Integritas | Pertahankan |
| C-10 | CHECK | Rentang progres | 0–100 | 003 L9–11 | instrumentasi | — | ✅ | Integritas | Pertahankan |
| C-11 | INDEX | Indeks kinerja | 7 index | 001 L68–71; 004 L50; 007 L47–48 | query repository | — | ✅ | Kinerja | Pertahankan |

---

## D. Matriks Relasi & Kardinalitas

| No. | Bagian ERD | Klaim | Elemen | Bukti Migration | Bukti Source Code | Bukti Diagram | Status | Dampak | Rekomendasi |
|---|---|---|---|---|---|---|---|---|---|
| D-1 | Relasi | User — doctor_profiles | garis `rel_user_doctor` | 004 L12, L46 | `profile.ts` | label `1` / `0..1` | ✅ | 1:0..1 | Pertahankan |
| D-2 | Relasi | User — analyses | garis `rel_user_analyses` | 001 L17 | `analysis_repository.py` list/delete | label `1` / `*` | ✅ | 1:* | Pertahankan |
| D-3 | Relasi | doctor_profiles — User (`approved_by`) | garis `rel_doctor_approved_by` | 007 L33 | `admin_service.py` L188–199 | label `0..*` / `0..1`, nama `approved_by` | ⚠️ | Melengkapi FK nyata | Gunakan versi audited |
| D-4 | Kardinalitas | Satu user nol/satu profil | `0..1` | 004 L46 UNIQUE | upsert satu baris | teks `0..1` | ✅ | Benar | Pertahankan |
| D-5 | Kardinalitas | Satu user nol/banyak analisis | `*` | 001 L17 tanpa UNIQUE | list by user | teks `*` | ✅ | Benar | Pertahankan |
| D-6 | Kardinalitas | Satu admin menyetujui banyak profil | `0..*` | 007 L33 nullable | `approved_by` nilai admin | teks `0..*` (audited) | ✅ | Benar | Pertahankan |

---

## E. Matriks Trigger, Function, RLS, Storage

| No. | Bagian ERD | Klaim | Elemen | Bukti Migration | Bukti Source Code | Bukti Diagram | Status | Dampak | Rekomendasi |
|---|---|---|---|---|---|---|---|---|---|
| E-1 | Trigger | Profil dokter dibuat otomatis saat signup | `on_auth_user_created_doctor_profile` | 008 L76–79 (AFTER INSERT ON auth.users) | `auth.ts` signUp | Tidak digambar (perilaku) | ✅ | Konsistensi data | Catat di narasi |
| E-2 | Function | Fungsi trigger idempoten & non-fatal | `handle_new_doctor_signup()` | 008 L28–71 (SECURITY DEFINER; EXCEPTION → WARNING) | — | — | ✅ | Ketahanan signup | Pertahankan |
| E-3 | Trigger | Admin dilewati | `raw_app_meta_data->>'role' <> 'admin'` | 008 L38 | `auth.ts` L328–334 | — | ✅ | Admin tanpa profil | Pertahankan |
| E-4 | RLS | RLS aktif analyses | `ENABLE ROW LEVEL SECURITY` | 001 L74 (+4 policy L77–99) | user-scoped query | Tidak digambar | ✅ | Keamanan | Pertahankan |
| E-5 | RLS | RLS aktif doctor_profiles | `ENABLE ROW LEVEL SECURITY` | 004 L53 (+4 policy L56–78) | user-scoped query | Tidak digambar | ✅ | Keamanan | Pertahankan |
| E-6 | RLS | Service role baca/ubah semua | 2 policy service role | 007 L81–98 | backend service key | Tidak digambar | ✅ | Operasi admin | Pertahankan |
| E-7 | Storage | Bucket `profile-avatars` + policy pemilik | bucket publik + 4 policy | 005 L15–88 | `profile.ts` upload | Tidak digambar | ✅ | Foto profil | Catat sebagai non-entitas |
| E-8 | Storage | Bucket asset analisis + policy pemilik | 3 policy | 001 L107–145 | `storage_service.py` | Tidak digambar | ✅ | Artefak analisis | Catat sebagai non-entitas |

---

## F. Matriks Ketujuh Alur

| No. | Bagian ERD | Klaim | Elemen | Bukti Migration | Bukti Source Code | Bukti Diagram | Status | Dampak | Rekomendasi |
|---|---|---|---|---|---|---|---|---|---|
| F-1 | Alur | Sign Up membuat auth.users + doctor_profiles | User, doctor_profiles, trigger | 008 L28–79 | `auth.ts` L131–161; `AuthContext.tsx` L148–149 | 2 entitas + relasi | ✅ | Alur utama | Pertahankan |
| F-2 | Alur | Sign In membaca role/status | doctor_profiles | 007 L24–35 | `auth.ts` L297–316; `AuthContext.tsx` L78–84 | 2 entitas | ✅ | Gerbang akses | Pertahankan |
| F-3 | Alur | Upload citra membuat baris analyses | analyses | 001 L14–64 | `analysis_service.py` L369; `analysis_repository.py` L38–107 | entitas analyses | ✅ | Analisis | Pertahankan |
| F-4 | Alur | Segmentasi memperbarui analyses | analyses | 001; 003 | `analysis_repository.py` L133–162 | entitas analyses | ✅ | Pipeline AI | Pertahankan |
| F-5 | Alur | Riwayat query/hapus analyses | analyses | 001 L17, L99 | `analysis.ts` L212–222; routes L45–56 | entitas analyses | ✅ | Riwayat | Pertahankan |
| F-6 | Alur | Profil dokter upsert | doctor_profiles | 004; 006 | `profile.ts` L149–163, L344–345 | entitas doctor_profiles | ✅ | Profil | Pertahankan |
| F-7 | Alur | Sign Out tidak mengubah data | — | — | `AuthContext.tsx` L59 | — | ✅ | Tidak relevan ERD | Pertahankan |
| F-8 | Alur | Approval/reject admin menulis approved_by | doctor_profiles, User | 007 L33–34 | `admin_service.py` L188–199, L284–294; `admin_controller.py` L55–56 | relasi audited | ⚠️ | Jejak persetujuan | Gunakan versi audited |

---

## G. Matriks Konsistensi Visual & Format

| No. | Bagian ERD | Klaim | Elemen | Bukti Migration | Bukti Source Code | Bukti Diagram | Status | Dampak | Rekomendasi |
|---|---|---|---|---|---|---|---|---|---|
| G-1 | Visual | 3 entitas konsisten | drawio/PNG/SVG | — | generator satu sumber | 3/3/3 | ✅ | Konsistensi | Pertahankan |
| G-2 | Visual | 73 atribut konsisten | drawio/PNG/SVG | 001–008 | `_audit_verify*.js` | 73/73/73 | ✅ | Konsistensi | Pertahankan |
| G-3 | Visual | Relasi asli 2 garis | drawio/PNG/SVG | 001/004 | — | 2/2/2 | ✅ | Konsistensi | Pertahankan |
| G-4 | Visual | Revisi audited menambah 1 garis | relasi `approved_by` | 007 L33 | `admin_service.py` | 3 edge, 1 polyline | ✅ | Kelengkapan | Gunakan audited |
| G-5 | Visual | File asli tidak berubah | ukuran/timestamp | — | — | 27922/433318/11618 B | ✅ | Integritas | Pertahankan |
| G-6 | Format | PUML konsisten dengan diagram | `.puml` | 004/007 | — | 16 field, `user_metadata`, tanpa approved_by | ❌ | Menyesatkan pembaca | Sinkronkan atau hapus |

---

## H. Ringkasan Temuan & Rekomendasi

| No. | Temuan | Tingkat | Status | Dampak | Rekomendasi |
|---|---|---|---|---|---|
| H-1 | FK `approved_by` tidak digambar sebagai relasi di ERD final | Sedang | ⚠️ | Diagram kurang lengkap; FK nyata & dipakai kode | Gunakan `ERD_PIXELT_FINAL_AUDITED` (sudah diperbaiki) |
| H-2 | Komentar 007 L17 salah menyebut `raw_user_meta_data.role` | Rendah | ⚠️ | Dokumentasi kode menyesatkan | Ubah ke `raw_app_meta_data.role` |
| H-3 | `.puml` usang (16 field, `user_metadata`, tanpa approved_by) | Tinggi (dokumen) | ❌ | Tidak konsisten dengan gambar | Sinkronkan atau hapus |
| H-4 | Tidak ada E2E browser; verifikasi statis | Rendah | ⚠️ | Keterbatasan akademik | Catat di bab keterbatasan |
| H-5 | Storage/session sengaja bukan entitas | Informasi | ✅ | Sesuai lingkup | Catat di narasi |

**Kesimpulan matriks:** seluruh elemen kritis ERD memiliki bukti migration + source code. Satu catatan fungsional (FK `approved_by`) telah diselesaikan melalui revisi audited, dan satu catatan dokumen (`.puml`) perlu tindakan.

---
*Dokumen ini dihasilkan dari audit independen. Tidak memuat kredensial, token, atau data rahasia.*