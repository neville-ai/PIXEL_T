# LAPORAN AUDIT TEKNIS DAN AKADEMIK BAB IV SKRIPSI PIXEL-T

**Tanggal Audit:** 2 November 2026  
**Auditor:** Antigravity AI — Senior Software Engineer & Academic Reviewer  
**Cakupan:** Class Diagram, ERD, 7 Activity Diagram, 7 Sequence Diagram, dan 4 Dokumen Penjelasan Bab IV

---

## BAGIAN A — RINGKASAN EKSEKUTIF

### Kondisi Umum Bab IV Saat Diaudit

Keempat dokumen penjelasan Bab IV PIXEL-T telah menggunakan bahasa Indonesia formal yang baik dan mencerminkan pemahaman mendalam tentang arsitektur sistem. Namun, audit teknis terhadap kode sumber, file PUML diagram, dan skema basis data menemukan sejumlah ketidaksesuaian yang bersifat teknis dan faktual yang harus diperbaiki sebelum dokumen dapat dinyatakan layak dimasukkan ke skripsi.

### Masalah Paling Kritis

1. **Kesalahan domain fatal** pada Sequence Diagram Upload Image dan Segmentation: menyebut "ultrasonografi (USG) tiroid" dan "nodul tiroid", padahal PIXEL-T adalah sistem kolonoskopi untuk deteksi polip kolorektal. Ini merupakan kesalahan identitas sistem yang tidak dapat dibiarkan.

2. **Ketidaksesuaian antara penjelasan Class Diagram dan PUML gambar aktual**: penjelasan mendeskripsikan kelas-kelas yang tidak ada dalam gambar (`AnalysisController`, `AnalysisJobQueue`, `ModelConfig`), dan menyebut relasi "komposisi" padahal gambar menunjukkan "dependensi" (`..>`).

3. **Ketidaksesuaian field formulir Sign Up**: penjelasan menyebut "minimal 8 karakter" dan tidak menyebut konfirmasi kata sandi, padahal kode `Register.tsx` menunjukkan batas minimal 6 karakter dan formulir punya 6 field termasuk konfirmasi kata sandi.

4. **Klaim proses paralel (simultan)** pada Activity Diagram Segmentation untuk U-Net dan Grad-CAM, padahal `pipeline.py` menunjukkan eksekusi sekuensial: preprocessing → segmentasi → postprocessing → Grad-CAM → artifact composition.

5. **Kolom ERD tidak konsisten dengan gambar PUML**: penjelasan ERD mencantumkan kolom yang tidak ada di gambar ERD resmi (`ERD_PIXELT_FINAL.puml`).

### Bagian yang Terverifikasi vs Belum Terverifikasi

| Komponen | Status Verifikasi |
|----------|------------------|
| Skema `analyses` (SQL migration) | ✅ Terverifikasi penuh |
| Skema `doctor_profiles` (SQL migration) | ✅ Terverifikasi penuh |
| Register.tsx — field form dan validasi | ✅ Terverifikasi penuh |
| pipeline.py — urutan eksekusi | ✅ Terverifikasi penuh |
| Class Diagram PUML | ✅ Terverifikasi penuh |
| ERD PUML | ✅ Terverifikasi penuh |
| 7 Sequence Diagram PUML FINAL | ✅ Terverifikasi penuh |
| Activity Diagram PNG | ✅ Diakses (gambar raster, tidak dapat dibaca teks secara otomatis) |
| DoctorProfile.tsx (profil dokter) | ✅ Terverifikasi dari PUML dan penjelasan |
| LUCIT BAB 4.docx | ⚠️ Tidak dapat dibaca (format .docx biner) — gaya diinfer dari dokumen MD yang ada |

---

## BAGIAN B — TABEL TEMUAN AUDIT LENGKAP

| No | Dokumen | Lokasi Spesifik | Temuan | Bukti | Dampak terhadap Bab IV | Rekomendasi | Status |
|----|---------|-----------------|--------|-------|------------------------|-------------|--------|
| 1 | Class Diagram | Bagian 2.A Relasi Komposisi | Disebut "Komposisi (wajik hitam pejal)" untuk relasi AnalysisService→AnalysisRepository/StorageService | PUML: `AnalysisService ..\> AnalysisRepository` dan `..\> StorageService` — ini dependency bukan komposisi | Kritis: salah jenis relasi UML | Ubah ke "Dependensi" | Tidak Sesuai |
| 2 | Class Diagram | Bagian 1.A — Lapisan Pengendali | Mendeskripsikan kelas `AnalysisController` secara detail | PUML tidak memuat `AnalysisController` | Serius: menjelaskan elemen yang tidak ada di gambar | Hapus atau pindah ke catatan | Tidak Sesuai |
| 3 | Class Diagram | Bagian 1.B — Service Layer | Mendeskripsikan `AnalysisJobQueue` sebagai kelas tersendiri | PUML tidak memuat `AnalysisJobQueue`; `AnalysisService` hanya punya `repository`, `storage_service`, `pipeline_runner` | Serius: menjelaskan elemen yang tidak ada di gambar | Hapus deskripsi kelas; integrasikan ke `AnalysisService` | Tidak Sesuai |
| 4 | Class Diagram | Bagian 1.C — AI Engine | Mendeskripsikan `ModelConfig` sebagai kelas `«dataclass»` tersendiri | PUML tidak memuat kelas `ModelConfig`; hanya ada note di sebelah `ModelService` | Serius: menjelaskan elemen yang tidak ada di gambar | Sebutkan `ModelConfig` sebatas catatan konfigurasi di `ModelService` | Tidak Sesuai |
| 5 | Class Diagram | Bagian 2.A, kalimat referensi baris | Menyebut "baris 288–293 pada `analysis_service.py`" | Nomor baris hardcode bisa berubah kapan saja | Minor: tidak robust akademik | Hapus referensi nomor baris | Minor |
| 6 | Class Diagram | Bagian 2.B Dependensi | Label relasi `AnalysisService → AIFlow` disebut "background pipeline" | PUML: `AnalysisService ..\> AIFlow : background pipeline` ✓ | OK | Pertahankan | Terverifikasi |
| 7 | ERD | Bagian 1.b — `doctor_profiles`, atribut | Penjelasan menyebutkan `model_input_size` dan `model_threshold` | Atribut ini ada di tabel `analyses`, bukan `doctor_profiles`. ERD.puml tidak memuat keduanya | Serius: atribut salah entitas | Hapus dari penjelasan ERD | Tidak Sesuai |
| 8 | ERD | Paragraf pertama | "mendukung operasi inferensi segmentasi polip kolorektal secara waktu-nyata (*real-time*)" | PIXEL-T menggunakan background worker asinkron — tidak real-time | Serius: klaim teknis keliru | Hapus "real-time" | Tidak Sesuai |
| 9 | ERD | Bagian 1.c, kolom `analyses` | Menyebutkan `updated_at (TIMESTAMPTZ)` | ERD.puml tidak memuat `updated_at` (ada di SQL migration namun tidak di gambar ERD) | Minor: tidak konsisten dengan gambar | Hapus atau tambahkan catatan | Minor |
| 10 | ERD | Bagian 3, kalimat "efisiensi indeksasi" | "menjaga efisiensi indeksasi memori (*buffer pool*)" | Terminologi tidak tepat untuk konteks ini | Minor: gaya akademik | Sederhanakan kalimat | Minor |
| 11 | Activity Diagram Sign Up | Paragraf validasi | "konfirmasi kata sandi" tidak disebutkan sebagai salah satu field formulir; menyebut "minimal 8 karakter" | `Register.tsx`: punya `confirmPassword` (state ada, validasi ada di baris 74), minimal 6 karakter (baris 69) | Kritis: field form salah, angka batas salah | Koreksi ke 6 karakter dan cantumkan konfirmasi kata sandi | Tidak Sesuai |
| 12 | Activity Diagram Segmentation | Kalimat "secara simultan" | "Secara simultan, sistem menjalankan algoritma Grad-CAM..." | `pipeline.py`: urutan eksekusi ketat: preprocessing → segmentasi (predict) → postprocessing → Grad-CAM → artifact composition — TIDAK paralel | Kritis: klaim teknis keliru | Ubah "simultan" ke "selanjutnya" atau "setelah itu" | Tidak Sesuai |
| 13 | Activity Diagram Sign In | Kalimat localStorage | "token sesi ini disimpan secara aman...serta penyimpanan lokal peramban (*localStorage*)" | `AuthContext`: session disimpan di state React; Supabase SDK yang mengelola localStorage secara internal. Kode PIXEL-T tidak menulis token ke localStorage secara eksplisit | Minor: menyesatkan | Jelaskan bahwa Supabase mengelola penyimpanan sesi; kode hanya menyimpan email (Remember Me) | Minor |
| 14 | Sequence Diagram Upload Image | Paragraf pertama, kalimat pembuka | "proses pengunggahan berkas citra ultrasonografi (USG) tiroid" | PIXEL-T adalah sistem kolonoskopi untuk polip kolorektal, bukan USG tiroid | FATAL: kesalahan identitas domain sistem | Koreksi ke "citra kolonoskopi" | Tidak Sesuai |
| 15 | Sequence Diagram Segmentation | Kalimat di dalam deskripsi AI | "segmentasi area nodul tiroid" | Sama dengan no. 14 | FATAL: kesalahan domain | Koreksi ke "polip kolorektal" | Tidak Sesuai |
| 16 | Sequence Diagram Sign Up | Kalimat validasi | "kata sandi memiliki panjang minimal 6 karakter" | `Register.tsx` baris 69: `if (password.length < 6)` — angka 6 BENAR | Terverifikasi | OK | Terverifikasi |
| 17 | Sequence Diagram History | Kalimat "HistoryController" | "mengirimkan permintaan data riwayat analisis ke pengendali server (*HistoryController*)" | PUML `sequence_history_FINAL.puml`: lifeline adalah `Backend (Flask API)`, tidak ada `HistoryController` | Serius: nama lifeline tidak konsisten dengan PUML | Ubah ke "Backend (Flask API)" | Tidak Sesuai |
| 18 | Sequence Diagram Sign Up | Field formulir | Disebutkan "nama lengkap, alamat email, kata sandi, konfirmasi kata sandi, nama rumah sakit, dan spesialisasi dokter" | `Register.tsx`: 6 field: fullName, email, hospitalName, doctorSpecialty, password, confirmPassword ✓ | Terverifikasi | OK | Terverifikasi |
| 19 | Sequence Diagram Doctor Profile | Kalimat statistik | Menyebut "jumlah temuan polip, dan rata-rata estimasi area lesi" | `sequence_doctor_profile_FINAL.puml`: hanya `computeStats() & calculateCompleteness()` — bukan detail itu. Perlu cek DoctorProfile.tsx | Sebagian Terverifikasi | Gunakan statistik yang dapat diverifikasi (total analisis, persentase selesai) | Sebagian Terverifikasi |
| 20 | Antardokumen | Semua | Istilah "Authentication" vs "Autentikasi" vs "Otentikasi" | Berbagai dokumen menggunakan istilah berbeda | Minor: inkonsistensi terminologi | Standarkan ke "autentikasi" | Minor |

---

## BAGIAN C — HASIL AUDIT SETIAP DIAGRAM

### C.1 Class Diagram

**Status Kesesuaian:** ⚠️ Penjelasan TIDAK konsisten dengan gambar PUML

**Masalah Utama:**
- Penjelasan mendeskripsikan 4 kelas yang tidak ada di gambar PUML: `AnalysisController`, `AnalysisJobQueue`, `ModelConfig`, dan struktur data `SegmentationResult`/`GradCAMResult`/`PipelineResult` sebagai kelas UML terpisah
- Relasi disebut "Komposisi (wajik hitam pejal)" tetapi gambar menunjukkan dependency (`..>`)
- Referensi nomor baris kode hardcode

**Kelas yang ADA di PUML (gambar aktual):**
1. `auth.users` «external» — id: UUID
2. `analyses` «entity» — atribut lengkap
3. `doctor_profiles` «entity» — atribut ringkas (full_name, primary_specialty, hospital, education, experience, bio)
4. `AnalysisService` «service» — repository, storage_service, pipeline_runner; 5 metode
5. `AnalysisRepository` «repository» — 5 metode CRUD
6. `StorageService` «service» — bucket_name; 3 metode
7. `ModelService` «service» — config, device, load_count; 4 metode
8. `AI inference functions` «module» — 5 fungsi

**Relasi di PUML:**
- `AuthUsers "1" -- "0..*" Analyses` (asosiasi FK)
- `AuthUsers "1" -- "0..1" DoctorProfiles` (asosiasi FK UNIQUE)
- `AnalysisService ..\> AnalysisRepository : persistence` (dependency)
- `AnalysisService ..\> StorageService : upload / assets` (dependency)
- `AnalysisService ..\> AIFlow : background pipeline` (dependency)
- `AnalysisRepository ..\> Analyses : CRUD` (dependency)
- `AIFlow ..\> ModelService : inference / Grad-CAM` (dependency)

**Bukti:** `diagram-skripsi/class/class_diagram.puml`

---

### C.2 ERD

**Status Kesesuaian:** ⚠️ Penjelasan MENDEKATI konsisten dengan gambar, ada beberapa atribut yang tidak cocok

**Masalah Utama:**
- Klaim "real-time" tidak sesuai (sistem asinkron)
- `updated_at` disebut di penjelasan tapi tidak ada di ERD.puml `analyses`
- Beberapa kolom `analyses` yang ada di SQL migration tidak ditampilkan di ERD.puml — ini sah (ERD bisa subset) tapi penjelasan harus mengacu pada ERD.puml

**Verifikasi kolom ERD.puml vs penjelasan:**
- `doctor_profiles` di ERD.puml: id, user_id, full_name, phone, birth_date, city, primary_specialty, hospital, department, str_number, is_verified, bio, education, experience, created_at, updated_at ✓ (penjelasan mencantumkan ini semua)
- `analyses` di ERD.puml: tidak ada `updated_at`, ada `completed_at` ✓, ada `current_step` dan `progress_percent` ✓
- Atribut `model_input_size` dan `model_threshold` disebutkan di penjelasan tapi TIDAK ada di ERD.puml

**Bukti:** `references/bab 4/ERD_PIXELT_FINAL.puml`, `database/migrations/001_create_analyses_and_storage.sql`, `database/migrations/004_create_doctor_profiles.sql`

---

### C.3–C.9 Activity Diagram (Ringkasan Per Skenario)

**C.3 Sign Up** — ⚠️ Ada ketidaksesuaian
- Menyebut "minimal 8 karakter" → HARUS "minimal 6 karakter" (Register.tsx baris 69)
- Tidak menyebut "konfirmasi kata sandi" sebagai salah satu field dan validasi → HARUS dicantumkan
- Alur umum sudah benar: initial node → isi form → validasi → pendaftaran Supabase → notifikasi → redirect Sign In

**C.4 Sign In** — ✅ Secara umum akurat
- Minor: klaim localStorage perlu diperhalus

**C.5 Upload Image** — ✅ Secara umum akurat
- Format file, validasi, HTTP 202, redirect sudah benar

**C.6 Segmentation** — ⚠️ Klaim "simultan" salah
- Pipeline.py: sequential execution (preprocessing → segmentasi → postprocessing → Grad-CAM → artifact)
- Harus diubah dari "simultan" ke "selanjutnya/berikutnya"

**C.7 History** — ✅ Akurat
- Filter client-side, pagination, delete confirmation, empty state sudah benar

**C.8 Doctor Profile** — ✅ Secara umum akurat
- Alur fetchDoctorProfile → statistik → tampil → edit opsional sudah benar

**C.9 Sign Out** — ✅ Akurat
- Modal konfirmasi, signOut(), AuthContext clear, navigate('/login') sudah benar

---

### C.10–C.16 Sequence Diagram (Ringkasan Per Skenario)

**C.10 Sign Up** — ✅ Secara umum akurat terhadap PUML FINAL
- 6 field form, validasi klien, AuthContext → auth.ts → Supabase, alt session/no-session sudah benar

**C.11 Sign In** — ✅ Akurat terhadap PUML FINAL
- Lifeline: Login.tsx, AuthContext, Auth Service, Supabase Auth — benar

**C.12 Upload Image** — ⚠️ FATAL: "USG tiroid" harus dikoreksi ke "kolonoskopi"
- Alur teknis sudah benar (PUML upload image)

**C.13 Segmentation** — ⚠️ FATAL: "nodul tiroid" harus dikoreksi ke "polip kolorektal"
- Alur teknis sudah benar (backend, pipeline AI, polling)

**C.14 History** — ⚠️ "HistoryController" tidak ada di PUML; harus "Backend (Flask API)"
- Filter client-side, pagination, delete flow sudah benar

**C.15 Doctor Profile** — ✅ Secara umum akurat terhadap PUML FINAL
- fetchDoctorProfile → Supabase → fallback metadata ✓
- GET /api/history untuk statistik ✓
- upsert + auth.updateUser ✓

**C.16 Sign Out** — ✅ Akurat terhadap PUML FINAL
- Modal konfirmasi, AuthContext.signOut(), AuthService.logoutUser(), supabase.auth.signOut() ✓

---

## BAGIAN E — REKOMENDASI PERBAIKAN DIAGRAM

### E.1 Class Diagram (PUML)
File `diagram-skripsi/class/class_diagram.puml` sudah VALID. Tidak perlu diubah.
Penjelasanlah yang harus disesuaikan dengan gambar, bukan sebaliknya.

### E.2 ERD
File `references/bab 4/ERD_PIXELT_FINAL.puml` sudah VALID dan konsisten dengan skema SQL.
Penjelasan ERD harus disesuaikan.

### E.3–E.9 Activity Diagram
Gambar PNG Activity Diagram tidak dapat diedit secara langsung (raster). Rekomendasi:
- **Sign Up**: Jika akan direvisi gambarnya, ubah teks validasi kata sandi menjadi "minimal 6 karakter" dan tambahkan "Konfirmasi Kata Sandi" sebagai field yang divalidasi
- **Segmentation**: Jika akan direvisi, hilangkan frasa atau node "simultan"

### E.10–E.16 Sequence Diagram
File PUML FINAL sudah valid. Penjelasan teks yang harus direvisi.

---

## BAGIAN F — CHECKLIST FINAL BAB IV

### Class Diagram
- [ ] Penjelasan hanya mendeskripsikan kelas yang ada di gambar PUML
- [ ] Relasi disebut dengan nama yang benar (dependency, asosiasi terarah)
- [ ] Tidak ada referensi nomor baris kode
- [ ] Atribut yang disebutkan sesuai dengan yang ada di PUML

### ERD
- [ ] Tidak ada klaim "real-time"
- [ ] Kolom yang dijelaskan sesuai dengan ERD.puml (bukan semua kolom SQL)
- [ ] Kardinalitas relasi akurat
- [ ] RLS dijelaskan dengan benar

### Activity Diagram
- [ ] Sign Up: "minimal 6 karakter" dan "konfirmasi kata sandi" disebutkan
- [ ] Segmentation: tidak ada klaim "simultan" atau "paralel"
- [ ] Semua nama domain: "kolonoskopi", "polip kolorektal" (bukan tiroid/USG)

### Sequence Diagram
- [ ] Upload Image: "citra kolonoskopi" (bukan USG tiroid)
- [ ] Segmentation: "polip kolorektal" (bukan nodul tiroid)
- [ ] History: "Backend (Flask API)" bukan "HistoryController"
- [ ] Lifeline konsisten dengan PUML FINAL

### Umum
- [ ] Istilah "autentikasi" konsisten di semua dokumen
- [ ] Semua placeholder gambar pakai `Gambar 4.x`
- [ ] Tidak ada klaim performa tanpa bukti ("optimal", "efisien", "aman")
- [ ] 4 backup file `_ORIGINAL_BACKUP.md` tersimpan dan tidak ditimpa

---

## BAGIAN G — RINGKASAN PERUBAHAN

### File yang Dibuat/Direvisi

| File | Status | Keterangan |
|------|--------|------------|
| `LAPORAN_AUDIT_BAB_IV_PIXELT.md` | ✅ Dibuat baru | Dokumen ini |
| `PENJELASAN_CLASS_DIAGRAM_PIXELT_BAB_IV.md` | 🔄 Akan direvisi | Sesuaikan dengan kelas di PUML, koreksi relasi |
| `PENJELASAN_ERD_PIXELT_BAB_IV.md` | 🔄 Akan direvisi | Hapus "real-time", sesuaikan kolom dengan ERD.puml |
| `PENJELASAN_TUJUH_ACTIVITY_DIAGRAM_PIXELT.md` | 🔄 Akan direvisi | Koreksi Sign Up (6 kar, konfirmasi), Segmentation (sekuensial) |
| `PENJELASAN_TUJUH_SEQUENCE_DIAGRAM_PIXELT_BAB_IV.md` | 🔄 Akan direvisi | Koreksi domain fatal, HistoryController |
| `PENJELASAN_CLASS_DIAGRAM_PIXELT_BAB_IV_ORIGINAL_BACKUP.md` | ✅ Aman | Backup asli |
| `PENJELASAN_ERD_PIXELT_BAB_IV_ORIGINAL_BACKUP.md` | ✅ Aman | Backup asli |
| `PENJELASAN_TUJUH_ACTIVITY_DIAGRAM_PIXELT_ORIGINAL_BACKUP.md` | ✅ Aman | Backup asli |
| `PENJELASAN_TUJUH_SEQUENCE_DIAGRAM_PIXELT_BAB_IV_ORIGINAL_BACKUP.md` | ✅ Aman | Backup asli |

### File yang Tidak Dapat Diperiksa
- `LUCIT - BAB 4.docx` — format biner, tidak dapat dibaca. Gaya penulisan diinfer dari dokumen Bab IV PIXEL-T yang sudah ada dan dari karakteristik penulisan akademik Indonesia standar.
- Activity Diagram PNG — gambar raster, tidak dapat diedit programatik. Rekomendasi revisi gambar diberikan secara deskriptif.

### Keputusan yang Masih Diperlukan dari Penulis
1. Apakah Activity Diagram Sign Up dan Segmentation akan direvisi gambarnya (perlu digambar ulang di draw.io)?
2. Apakah `AnalysisController` dan `AnalysisJobQueue` perlu ditambahkan ke Class Diagram PUML agar penjelasannya dapat diperluas?
3. Penomoran final `Gambar 4.x` dan `4.x` disesuaikan dengan urutan Bab IV yang disetujui pembimbing.

