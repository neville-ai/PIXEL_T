# LAPORAN AUDIT DAN PENYUSUNAN BAB IV — SKRIPSI PIXEL-T
**Tanggal:** 2026-11-02  
**Dokumen yang Dihasilkan:** `BAB 4 - PIXEL-T.docx`  
**Ukuran File:** ±1.87 MB  

---

## A. RINGKASAN KONDISI AWAL

Sebelum penyusunan dimulai, dilakukan inventarisasi dan audit terhadap seluruh sumber yang tersedia.

### Dokumen Revisi yang Tersedia (semua terverifikasi ADA)

| Dokumen | Ukuran | Status |
|---------|--------|--------|
| `PENJELASAN_CLASS_DIAGRAM_PIXELT_BAB_IV.md` | 12.778 bytes | ✅ Digunakan |
| `PENJELASAN_ERD_PIXELT_BAB_IV.md` | 9.599 bytes | ✅ Digunakan |
| `PENJELASAN_TUJUH_ACTIVITY_DIAGRAM_PIXELT.md` | 12.687 bytes | ✅ Digunakan |
| `PENJELASAN_TUJUH_SEQUENCE_DIAGRAM_PIXELT_BAB_IV.md` | 13.331 bytes | ✅ Digunakan |
| `SPESIFIKASI_TUJUH_USE_CASE_PIXELT.md` | 14.240 bytes | ✅ Digunakan |

### Gambar Diagram yang Digunakan

| Gambar | File | Status |
|--------|------|--------|
| Use Case Diagram | `use_case_diagram.png` | ✅ Embedded |
| Activity - Sign Up | `activity_diagrams/Activity Diagram - Sign Up.drawio.png` | ✅ Embedded |
| Activity - Sign In | `activity_diagrams/Activity Diagram - Sign In.drawio.png` | ✅ Embedded |
| Activity - Upload Image | `activity_diagrams/Activity Diagram - Upload Image.drawio.png` | ✅ Embedded |
| Activity - Segmentation | `activity_diagrams/Activity Diagram - Segmentation.drawio.png` | ✅ Embedded |
| Activity - History | `activity_diagrams/Activity Diagram - History.drawio.png` | ✅ Embedded |
| Activity - Doctor Profile | `activity_diagrams/Activity Diagram - Doctor Profile.drawio.png` | ✅ Embedded |
| Activity - Sign Out | `activity_diagrams/Activity Diagram - Sign Out.drawio.png` | ✅ Embedded |
| Sequence - Sign Up | `sequence_diagram/sequence_diagram_sign_up.png` | ✅ Embedded |
| Sequence - Sign In | `sequence_diagram/sequence_diagram_sign_in.png` | ✅ Embedded |
| Sequence - Upload Image | `sequence_diagram/sequence_diagram_upload_image.png` | ✅ Embedded |
| Sequence - Segmentation | `sequence_diagram/sequence_diagram_segmentation.png` | ✅ Embedded |
| Sequence - History | `sequence_diagram/sequence_diagram_history.png` | ✅ Embedded |
| Sequence - Doctor Profile | `sequence_diagram/sequence_diagram_doctor_profile.png` | ✅ Embedded |
| Sequence - Sign Out | `sequence_diagram/sequence_diagram_sign_out.png` | ✅ Embedded |
| Class Diagram | `class_diagram.png` | ✅ Embedded |
| ERD | `ERD_PIXELT_FINAL.png` | ✅ Embedded |

**Total gambar yang berhasil diembed: 17 gambar**

### Referensi Gaya Penulisan
- `LUCIT - BAB 4.docx` ✅ Dibaca dan dipelajari gaya penulisannya

---

## B. TEMUAN AUDIT

### B.1 Terverifikasi ✅

| Fakta | Sumber |
|-------|--------|
| Formulir Sign Up memiliki 6 kolom (fullName, email, hospitalName, doctorSpecialty, password, confirmPassword) | `frontend/src/pages/auth/Register.tsx` |
| Password minimum 6 karakter (BUKAN 8) | `Register.tsx` baris 69 |
| Pipeline AI berjalan SEKUENSIAL, bukan paralel | `ai/inference/pipeline.py` |
| Domain PIXEL-T: kolonoskopi + polip kolorektal (BUKAN USG tiroid) | Seluruh kode backend |
| History.tsx menggunakan useMemo untuk filter client-side | `frontend/src/pages/history/History.tsx` |
| Paginasi History: PAGE_SIZE = 4 rekaman per halaman | `History.tsx` |
| Sequence Diagram History tidak memiliki lifeline "HistoryController" — menggunakan "Backend (Flask API)" | `diagram-skripsi/sequence/history_final.puml` |
| Semua relasi Class Diagram adalah `..>` (dependensi) kecuali relasi DB yang `--` | `diagram-skripsi/class/class_diagram.puml` |
| ERD tidak memiliki kolom `updated_at` pada tabel `analyses` | `database/migrations/001_create_analyses_and_storage.sql` |
| Doctor Profile menggunakan upsert ke `doctor_profiles` + `supabase.auth.updateUser()` | `frontend/src/pages/profile/DoctorProfile.tsx` |

### B.2 Sebagian Terverifikasi ⚠️

| Item | Catatan |
|------|---------|
| Gambar Class Diagram (class_diagram.png) | File tersedia dan digunakan. Konten visual tidak dapat diperiksa secara programatik dari file raster PNG, tetapi telah diverifikasi terhadap `class_diagram.puml`. |
| Ukuran gambar dalam docx | Disesuaikan secara proporsional. Penyesuaian akhir mungkin diperlukan saat membuka di Word. |

### B.3 Belum Terverifikasi 🔲

| Item | Alasan |
|------|--------|
| Hasil pengujian model AI (akurasi, precision, recall) | Tidak ada file hasil pengujian dalam workspace. **Bagian pengujian tidak dimasukkan ke docx untuk menghindari klaim tanpa bukti.** |
| Tampilan antarmuka (screenshots) | Tidak diminta dalam task ini. |

### B.4 Koreksi yang Dilakukan

| Error Asli | Koreksi |
|-----------|---------|
| "8 karakter" → seharusnya "6 karakter" untuk password minimum | ✅ Dikoreksi ke "minimal 6 karakter" |
| "USG tiroid / nodul tiroid" → domain SALAH | ✅ Dikoreksi ke "kolonoskopi / polip kolorektal" |
| Pipeline "paralel/simultan" → seharusnya sekuensial | ✅ Dikoreksi ke "tahapan sekuensial" |
| "HistoryController" → lifeline tidak ada dalam PUML | ✅ Diganti ke "Backend (Flask API)" |

---

## C. STRUKTUR DOKUMEN YANG DIHASILKAN

```
BAB IV ANALISIS DAN PERANCANGAN SISTEM
│
├── 4.1 Use Case Diagram
│   ├── Gambar 4.1 (use_case_diagram.png)
│   └── 4.1.1 Spesifikasi Use Case (7 tabel)
│       ├── Tabel 4.1 Sign Up
│       ├── Tabel 4.2 Sign In
│       ├── Tabel 4.3 Upload Image
│       ├── Tabel 4.4 Segmentation
│       ├── Tabel 4.5 View History
│       ├── Tabel 4.6 View Doctor Profile
│       └── Tabel 4.7 Sign Out
│
├── 4.2 Activity Diagram
│   ├── 4.2.1 Sign Up (Gambar 4.2)
│   ├── 4.2.2 Sign In (Gambar 4.3)
│   ├── 4.2.3 Upload Image (Gambar 4.4)
│   ├── 4.2.4 Segmentation (Gambar 4.5)
│   ├── 4.2.5 History (Gambar 4.6)
│   ├── 4.2.6 Doctor Profile (Gambar 4.7)
│   └── 4.2.7 Sign Out (Gambar 4.8)
│
├── 4.3 Sequence Diagram
│   ├── 4.3.1 Sign Up (Gambar 4.9)
│   ├── 4.3.2 Sign In (Gambar 4.10)
│   ├── 4.3.3 Upload Image (Gambar 4.11)
│   ├── 4.3.4 Segmentation (Gambar 4.12)
│   ├── 4.3.5 History (Gambar 4.13)
│   ├── 4.3.6 Doctor Profile (Gambar 4.14)
│   └── 4.3.7 Sign Out (Gambar 4.15)
│
├── 4.4 Perancangan Struktur Perangkat Lunak (Class Diagram)
│   ├── Gambar 4.16 (class_diagram.png)
│   ├── 4.4.1 Lapisan Layanan Bisnis dan Infrastruktur
│   ├── 4.4.2 Lapisan Mesin Kecerdasan Buatan
│   ├── 4.4.3 Lapisan Persistensi Basis Data
│   └── 4.4.4 Relasi Antarkomponen
│
└── 4.5 Perancangan Basis Data (ERD)
    ├── Gambar 4.17 (ERD_PIXELT_FINAL.png)
    ├── 4.5.1 Entitas users (auth.users)
    ├── 4.5.2 Entitas doctor_profiles
    ├── 4.5.3 Entitas analyses
    ├── 4.5.4 Relasi Antartabel
    └── 4.5.5 Arsitektur Penyimpanan dan Keamanan Data
```

**Statistik dokumen:**
- Paragraf: 212
- Gambar diembed: 17
- Tabel: 7
- Ukuran file: ~1.87 MB

---

## D. GAYA PENULISAN YANG DITERAPKAN (Berdasarkan LUCIT)

| Karakteristik | Implementasi |
|--------------|-------------|
| Pengantar gambar dengan nomor | "Gambar 4.x menunjukkan..." |
| Penjelasan setelah gambar | Langsung ke alur/komponen, tidak mengulang judul |
| Kalimat penutup tabel | "Tabel 4.x menjelaskan tahapan proses..." |
| Ringkas dan langsung | Tidak ada filler ("dapat kita lihat bahwa", "pada dasarnya") |
| Bahasa akademik baku | Konsisten sepanjang dokumen |
| Tidak ada klaim performa | Tidak ada "optimal", "efisien", "akurat" tanpa bukti |

---

## E. REKOMENDASI UNTUK PENULIS

### Segera lakukan:
1. **Buka `BAB 4 - PIXEL-T.docx` di Microsoft Word** dan periksa visual setiap gambar.
2. **Sesuaikan ukuran gambar** jika ada yang terlalu besar/kecil untuk halaman A4.
3. **Update penomoran gambar dan tabel** sesuai penomoran akhir skripsi (saat ini sudah final: Gambar 4.1 s.d. 4.17, Tabel 4.1 s.d. 4.7).
4. **Tambahkan bagian Implementasi dan Pengujian** jika skripsi Anda memerlukannya — pastikan menggunakan data pengujian aktual.
5. **Periksa konsistensi dengan Bab I–III** terutama terminologi dan ruang lingkup.

### Penting:
- Nomor gambar `4.16` (Class Diagram) dan `4.17` (ERD) diletakkan setelah Sequence Diagram karena mengikuti pola LUCIT. Sesuaikan jika pembimbing menginginkan urutan berbeda.
- Jika ada tampilan antarmuka (screenshots) yang perlu ditambahkan, sisipkan setelah bagian ERD atau buat subbab baru 4.6 Implementasi Antarmuka.

---

## F. SUMBER YANG DIGUNAKAN

| Sumber | Digunakan Untuk |
|--------|----------------|
| `PENJELASAN_CLASS_DIAGRAM_PIXELT_BAB_IV.md` | Konten 4.4 Class Diagram |
| `PENJELASAN_ERD_PIXELT_BAB_IV.md` | Konten 4.5 ERD |
| `PENJELASAN_TUJUH_ACTIVITY_DIAGRAM_PIXELT.md` | Konten 4.2 Activity Diagram (7 sub-subbab) |
| `PENJELASAN_TUJUH_SEQUENCE_DIAGRAM_PIXELT_BAB_IV.md` | Konten 4.3 Sequence Diagram (7 sub-subbab) |
| `SPESIFIKASI_TUJUH_USE_CASE_PIXELT.md` | Konten 4.1 Use Case Diagram + 7 tabel spesifikasi |
| `LUCIT - BAB 4.docx` | Gaya penulisan, pola kalimat, struktur subbab |
| `frontend/src/pages/auth/Register.tsx` | Verifikasi 6 kolom & password min 6 karakter |
| `ai/inference/pipeline.py` | Verifikasi pipeline sekuensial |
| `database/migrations/001_create_analyses_and_storage.sql` | Verifikasi skema tabel analyses |
| `database/migrations/004_create_doctor_profiles.sql` | Verifikasi skema tabel doctor_profiles |
| `diagram-skripsi/class/class_diagram.puml` | Verifikasi relasi dan kelas Class Diagram |
| `references/bab 4/ERD_PIXELT_FINAL.puml` | Verifikasi kolom ERD |
| Seluruh 7 PUML Sequence Diagram final | Verifikasi lifeline dan pesan |

---

*Laporan ini dihasilkan secara otomatis pada 2026-11-02 sebagai bagian dari proses penyusunan BAB 4 - PIXEL-T.docx.*

