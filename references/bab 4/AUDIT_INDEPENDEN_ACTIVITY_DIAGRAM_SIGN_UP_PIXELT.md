# AUDIT INDEPENDEN ACTIVITY DIAGRAM SIGN UP PIXEL-T

**Audit Independen terhadap `ACTIVITY_DIAGRAM_SIGN_UP_PIXELT_FINAL.png` / `.drawio`**
Disusun berdasarkan pemeriksaan mandiri implementasi aktual web PIXEL-T (per 4 November 2026).

Status audit: **TERVERIFIKASI — TIDAK ADA PERUBAHAN DIAGRAM YANG DIPERLUKAN**

---

## 1. Ringkasan Eksekutif

Audit independen ini memeriksa kesesuaian *Activity Diagram* Sign Up PIXEL-T (Gambar 4.x) terhadap implementasi aktual sistem. Seluruh sumber yang diperiksa — *source code* frontend, *migrasi* database, *trigger* PostgreSQL, *routing*, dan *ujian unit* — menunjukkan bahwa diagram **sudah akurat** dan **layak** digunakan dalam Bab IV skripsi.

**Keputusan:** Tidak ada revisi diagram yang diperlukan. File `ACTIVITY_DIAGRAM_SIGN_UP_PIXELT_FINAL.drawio` / `.png` dipertahankan sebagaimana adanya.

---

## 2. Sumber yang Diperiksa

### 2.1 Frontend

| Berkas | Baris | Peran dalam audit |
|--------|-------|-------------------|
| `frontend/src/pages/auth/Register.tsx` | 1–343 | Formulir 6 bidang, 8 kondisi validasi, `handleSubmit`, layar sukses, tautan `/login` |
| `frontend/src/context/AuthContext.tsx` | 175–204 | `signUp()`: cabang sesi vs tanpa sesi, update state, `requiresEmailConfirmation` |
| `frontend/src/services/auth.ts` | 131–188 | `registerUser()`: satu panggilan `supabase.auth.signUp()`, `formatAuthError`, `existingAccountHint` |
| `frontend/src/routes/AppRoutes.tsx` | 35–41 | Rute `/register` dilindungi `PublicOnlyRoute` |
| `frontend/src/components/auth/PublicOnlyRoute.tsx` | 1–41 | Redirect pengguna terautentikasi; izin pending/rejected stays |
| `frontend/src/components/auth/ProtectedRoute.tsx` | 1–41 | Route guard klinis; blokir `pending`/`rejected` |
| `frontend/src/components/auth/DoctorRoute.tsx` | 1–49 | Route guard khusus dokter; blokir admin ke halaman klinis |
| `frontend/src/components/auth/AdminRoute.tsx` | 1–39 | Route guard admin; blokir non-admin |

### 2.2 Database

| Berkas | Baris | Peran dalam audit |
|--------|-------|-------------------|
| `database/migrations/004_create_doctor_profiles.sql` | 1–82 | Tabel `doctor_profiles`; RLS; `user_id` FK ke `auth.users` |
| `database/migrations/007_add_role_and_account_status.sql` | 1–106 | Kolom `role` + `account_status`; catatan pembuatan Admin via Supabase Admin API |
| `database/migrations/008_create_doctor_profile_trigger.sql` | 1–106 | Fungsi `handle_new_doctor_signup()`; `AFTER INSERT` pada `auth.users`; `EXCEPTION → RAISE WARNING`; backfill |

### 2.3 Ujian Unit

| Berkas | Hasil | Keterangan |
|--------|-------|-----------|
| `frontend/src/pages/auth/Register.test.tsx` | **19/19 lolos** | Validasi 6 kondisi, submit sukses, layar sukses, toggle password |
| `frontend/src/services/auth.test.ts` | **6/6 lolos** | `registerUser` single call, metadata, error mapping, anti-enumeration |
| **Total** | **25/25 lolos** | Dijalankan dengan `npx vitest run` per 4 Nov 2026 |

---

## 3. Peta Alur Aktual vs Diagram

```
User: Membuka /register
  → PublicOnlyRoute memeriksa autentikasi
  → Formulir 6 bidang muncul

User: Mengisi formulir
  → Validasi lokal (8 kondisi)
  → [Gagal] → Pesan error → Kembali ke formulir
  → [Lolos] → Lanjut

System: signUp() → registerUser() → supabase.auth.signUp()
  → [Error] → Pesan error → Kembali ke formulir
  → [Sukses] → auth.users dibuat (+ user_metadata)

System: Trigger handle_new_doctor_signup (AFTER INSERT)
  → INSERT doctor_profiles (role='doctor', account_status='pending')
  → [Gagal] → RAISE WARNING (tidak membatalkan signup)

System: AuthContext.signUp() memeriksa session
  → [Session ada] → setUser, setSession, setRole('doctor'), setAccountStatus('pending')
  → [Tidak ada session] → requiresEmailConfirmation=true

Kedua cabang → Pesan "Pendaftaran berhasil (menunggu persetujuan admin)"
  → User klik "Masuk ke PIXEL-T" → /login
  → Final Node
```

**Kesesuaian dengan diagram:** ✅ 100% — setiap langkah dalam peta di atas memiliki elemen diagram yang setara.

---

## 4. Matriks Audit Elemen Diagram

| # | Elemen Diagram | Kode Sumber | Kesesuaian | Masalah | Rekomendasi |
|---|---------------|-------------|------------|---------|-------------|
| 1 | Initial Node (lingkaran hitam) | — | ✅ TERVERIFIKASI | — | — |
| 2 | Membuka halaman `/register` | `AppRoutes.tsx:35-41` + `PublicOnlyRoute.tsx` | ✅ TERVERIFIKASI | — | — |
| 3 | Mengisi formulir (6 bidang) | `Register.tsx:18-23` | ✅ TERVERIFIKASI | — | — |
| 4 | Memvalidasi input | `Register.tsx:35-79` | ✅ TERVERIFIKASI | — | — |
| 5 | Decision "Input valid?" (d1) | `Register.tsx:40-79` early return | ✅ TERVERIFIKASI | — | — |
| 6 | [Ya] → signUp() | `Register.tsx:83-89` | ✅ TERVERIFIKASI | — | — |
| 7 | [Tidak] → pesan error → kembali formulir | `Register.tsx:41-78` (setErrorMessage + return) | ✅ TERVERIFIKASI | — | — |
| 8 | Memanggil signUp() → supabase.auth.signUp() | `AuthContext.tsx:186` → `auth.ts:146` | ✅ TERVERIFIKASI | — | — |
| 9 | Decision "Permintaan signUp berhasil?" (d3) | `auth.ts:165` (result.error check) | ✅ TERVERIFIKASI | — | — |
| 10 | [Ya] → auth.users dibuat | Supabase Auth | ✅ TERVERIFIKASI | — | — |
| 11 | [Tidak] → pesan error → kembali formulir | `auth.ts:166` + `AuthContext.tsx:188` | ✅ TERVERIFIKASI | — | — |
| 12 | Trigger → INSERT doctor_profiles | `008.sql:44-60` | ✅ TERVERIFIKASI | — | — |
| 13 | Decision "Sesi dikembalikan?" (d2) | `AuthContext.tsx:191` | ✅ TERVERIFIKASI | — | — |
| 14 | [Ya] → update state (role=doctor, status=pending) | `AuthContext.tsx:192-196` | ✅ TERVERIFIKASI | — | — |
| 15 | [Tidak] → instruksi konfirmasi email | `AuthContext.tsx:200-203` | ✅ TERVERIFIKASI | — | — |
| 16 | Merge → pesan pendaftaran berhasil | `AuthContext.tsx:197, 201` | ✅ TERVERIFIKASI | — | — |
| 17 | Mengakses halaman `/login` | `Register.tsx:159-165` (Link to /login) | ✅ TERVERIFIKASI | — | — |
| 18 | Final Node (bullseye) | — | ✅ TERVERIFIKASI | — | — |
| 19 | UML Note (Admin exception) | `007.sql:52-70` + `008.sql:37-38` | ✅ TERVERIFIKASI | — | — |

**Ringkasan matriks:** 19/19 elemen **TERVERIFIKASI**. Tidak ada elemen yang **TIDAK SESUAI**, **SEBAGIAN TERVERIFIKASI**, atau **BELUM TERVERIFIKASI**.

---

## 5. Audit Detail per Area

### 5.1 Formulir Pendaftaran (6 Bidang)

**Kode aktual** (`Register.tsx:18-23`):
```typescript
const [fullName, setFullName] = useState('');
const [email, setEmail] = useState('');
const [password, setPassword] = useState('');
const [confirmPassword, setConfirmPassword] = useState('');
const [hospitalName, setHospitalName] = useState('');
const [doctorSpecialty, setDoctorSpecialty] = useState('');
```

**Diagram** (a2): *"Mengisi formulir pendaftaran (nama lengkap, email, kata sandi, konfirmasi kata sandi, rumah sakit, spesialisasi dokter)"*

**Verdict:** ✅ Sesuai — 6 bidang field identifier sama persis.

### 5.2 Validasi Lokal (8 Kondisi)

**Kode aktual** (`Register.tsx:40-79`):
1. Nama kosong → error
2. Email kosong → error
3. Format email salah → error
4. Rumah sakit kosong → error
5. Spesialisasi kosong → error
6. Kata sandi kosong → error
7. Kata sandi < 6 karakter → error
8. Konfirmasi ≠ kata sandi → error

**Diagram** (a3): *"Memvalidasi input (wajib, format email, kata sandi >= 6, konfirmasi cocok)"*

**Verdict:** ✅ Sesuai — diagram merangkum 8 kondisi menjadi satu aktivitas validasi. Tidak ada validasi fiktif.

### 5.3 Panggilan SignUp

**Kode aktual** (`AuthContext.tsx:186`):
```typescript
const result = await registerUser(email, password, fullName, hospitalName, doctorSpecialty);
```

**Kode aktual** (`auth.ts:146`):
```typescript
const { data, error } = await supabase.auth.signUp({
  email: email.trim(),
  password,
  options: { data: { full_name, hospital, hospital_name, primary_specialty, specialty, doctor_profile } },
});
```

**Diagram** (a4): *"Memanggil signUp() → supabase.auth.signUp()"*

**Verdict:** ✅ Sesuai — satu panggilan tunggal, metadata profesional dikirim sebagai `user_metadata`.

### 5.4 Trigger Database

**Kode aktual** (`008.sql:28-71`):
- `AFTER INSERT ON auth.users`
- Hanya untuk `raw_user_meta_data ? 'full_name'` DAN `raw_app_meta_data->>'role' <> 'admin'`
- `INSERT INTO doctor_profiles (role='doctor', account_status='pending')`
- Idempoten (skip jika profil sudah ada)
- `EXCEPTION WHEN OTHERS THEN RAISE WARNING` — **tidak membatalkan signup**

**Diagram** (a6): *"Trigger handle_new_doctor_signup INSERT doctor_profiles (role='doctor', account_status='pending')"*

**UML Note:** *"Admin dibuat via Supabase Admin API (app_metadata.role='admin') dan tidak memiliki baris doctor_profiles. Kegagalan trigger dicatat sebagai WARNING dan tidak membatalkan pendaftaran."*

**Verdict:** ✅ Sesuai — semua detail trigger terwakili secara akurat.

### 5.5 Percabangan Sesi

**Kode aktual** (`AuthContext.tsx:191-203`):
```typescript
if (result.data?.session && result.data.user) {
  // [Ya] — simpan sesi, set role/status, kembalikan pesan sukses
  return { message: 'Akun PIXEL-T Anda berhasil dibuat...' };
}
// [Tidak] — tidak ada sesi
return { message: 'Pendaftaran ... telah diproses...', requiresEmailConfirmation: true };
```

**Diagram** (d2): *"Sesi dikembalikan?"* dengan [Ya] → a7, [Tidak] → a8, keduanya merge ke a9.

**Verdict:** ✅ Sesuai — percabangan tepat, guard condition benar, merge node berfungsi.

### 5.6 Routing dan Perilaku Akhir

**Kode aktual** (`PublicOnlyRoute.tsx:19-39`):
- Pengguna terautentikasi → redirect ke `/admin` (admin) atau `/dashboard` (doctor approved)
- Pending/rejected → tetap di `/register`
- Belum login → tetap di `/register`

**Kode aktual** (`Register.tsx:159-165`):
- Tautan "Masuk ke PIXEL-T" → `/login` (tindakan manual pengguna)

**Diagram** (a10): *"Mengakses halaman /login"* → Final Node

**Verdict:** ✅ Sesuai — tidak ada auto-redirect; pengguna mengklik tautan secara manual.

---

## 6. Audit Notasi UML

| Aspek UML | Status | Keterangan |
|-----------|--------|-----------|
| Initial Node (lingkaran terisi hitam) | ✅ Benar | `st`: `ellipse;fillColor=#000000` |
| Final Node (bullseye / lingkaran bertingkat) | ✅ Benar | `en`: outer ellipse white fill + `en_in`: inner ellipse black fill |
| Activity Node (persegi panjang rounded) | ✅ Benar | Semua a1–a10, aerr menggunakan `rounded=1;arcSize=20` |
| Decision Node (belah ketupat / rhombus) | ✅ Benar | d1, d2, d3 menggunakan `rhombus` |
| Guard Condition | ✅ Benar | e5 `[Ya]`, e6 `[Tidak]`, e9 `[Ya]`, e10 `[Tidak]`, e13 `[Ya]`, e14 `[Tidak]` |
| Merge Node | ✅ Benar | a9 menerima edge dari a7 (e15) dan a8 (e16) |
| UML Note (segitigaAttached rectangle) | ✅ Benar | `note`: `dashed=1`, berisi info Admin |
| Edge arah (open arrow, endFill=0) | ✅ Benar | Semua 18 edge menggunakan `endArrow=open;endFill=0` |
| Tidak ada jalur mati | ✅ Benar | Setiap alur mencapai Final Node |

### Simulasi Jalur Diagram

**Jalur utama (sukses dengan sesi):**
`st → a1 → a2 → a3 → d1[Ya] → a4 → d3[Ya] → a5 → a6 → d2[Ya] → a7 → a9 → a10 → en`

**Jalur validasi gagal:**
`st → a1 → a2 → a3 → d1[Tidak] → aerr → a2` (loop)

**Jalur signUp gagal:**
`st → a1 → a2 → a3 → d1[Ya] → a4 → d3[Tidak] → aerr → a2` (loop)

**Jalur tanpa sesi (konfirmasi email):**
`st → a1 → a2 → a3 → d1[Ya] → a4 → d3[Ya] → a5 → a6 → d2[Tidak] → a8 → a9 → a10 → en`

Semua jalur lengkap dan mencapai Final Node. ✅

---

## 7. Audit Visual

| Aspek | Hasil |
|-------|-------|
| Format PNG | ✅ PNG |
| Dimensi | ✅ 1720 × 2020 pixel |
| Color mode | ✅ RGB |
| Gaya monokrom | ✅ Hitam putih, latar putih, garis hitam |
| Font sederhana & formal | ✅ Font default Draw.io, ukuran 9–10 |
| Jarak antar elemen | ✅ Proporsional, tidak terlalu rapat |
| Label guard terbaca | ✅ `[Ya]` / `[Tidak]` jelas di setiap decision edge |
| Tidak ada teks terpotong | ✅ Semua nilai termuat utuh |
| Tidak ada overlap panah | ✅ Orthogonal edge style, tidak bersilangan bermakna |

---

## 8. Perbandingan dengan Artefak Sebelumnya

| Artefak | Status |
|---------|--------|
| `ROLE_ADMIN_REVISED.drawio` | ❌ Digantikan — memiliki `a8` terisolasi tanpa edge, tidak ada `d3` |
| `FINAL_REVISED.drawio` | ❌ Digantikan — alur linier tanpa percabangan, node non-UML |
| `FINAL_AUDITED.drawio` | ✅ Identik dengan `FINAL.drawio` — bukan versi baru, hanya duplikat |
| **`FINAL.drawio`** | ✅ **Tetap digunakan** |

---

## 9. Keterbatasan Audit

1. **Analisis statis, bukan runtime.** Tidak ada pengujian browser (E2E) atau eksekusi terhadap Supabase Auth yang sebenarnya. Seluruh klaim didasarkan pada pembacaan kode sumber.
2. **Tidak ada akses ke basis data produksi.** Struktur `auth.users`, `doctor_profiles`, dan eksekusi trigger tidak diuji secara langsung di lingkungan hidup.
3. **Validasi visual terbatas.** Draw.io Desktop dan engine UML resmi tidak tersedia. Validasi XML dan geometri dilakukan via skrip Python.
4. **Kredensial tidak diungkap.** Service-role key, API key, dan token tidak dibaca.

---

## 10. Kesimpulan

| Kriteria | Hasil |
|----------|-------|
| Seluruh aktivitas sesuai implementasi | ✅ 19/19 elemen terverifikasi |
| Percabangan (validasi, signUp, sesi) lengkap | ✅ Lengkap |
| Notasi UML standar (initial/final/decision/merge) | ✅ Benar |
| Tidak ada aktivitas fiktif | ✅ Tidak ditemukan |
| Admin di luar alur publik (benar) | ✅ Tercermin pada UML Note |
| Persetujuan Admin di luar lingkup | ✅ Sengaja tidak dimodelkan |
| Validasi visual oleh engine UML resmi | ⚠️ Terbatas (lihat §9) |
| Pengujian runtime / E2E | ⚠️ Tidak dilakukan (lihat §9) |
| Ujian unit relevan | ✅ 25/25 lolos |

**Status akhir: ✅ TERVERIFIKASI — TIDAK ADA PERUBAHAN DIAGRAM YANG DIPERLUKAN**

`ACTIVITY_DIAGRAM_SIGN_UP_PIXELT_FINAL.drawio` / `.png` **layak** digunakan sebagai *Activity Diagram* Sign Up Bab IV (Gambar 4.x).

---

*Audit ini dilaksanakan secara independen per 4 November 2026 berdasarkan pemeriksaan langsung terhadap source code, migrasi database, trigger PostgreSQL, dan ujian unit yang tersedia. Tidak ada kode aplikasi yang diubah.*
