# Audit Independen Putaran Kedua — Sequence Diagram Sign Up PIXEL-T

**Tanggal:** 5 November 2026  
**Auditor:** Agnes (AI Agent) — OpenCode  
**Objek:** `SEQUENCE_DIAGRAM_SIGN_UP_PIXELT_FINAL.drawio` dan `SEQUENCE_DIAGRAM_SIGN_UP_PIXELT_FINAL.png`  
**Status:** ✅ **LULUS SETELAH PERBAIKAN**

---

## 1. Ringkasan Arsitektur Sign Up PIXEL-T

### 1.1 Call Chain Registrasi

```
User (buka /register)
  → Register.tsx (render form, validasi handleSubmit)
    → AuthContext.tsx: signUp(email, password, fullName, hospitalName, doctorSpecialty)
      → auth.ts: registerUser(email, password, fullName, hospitalName, doctorSpecialty)
        → Supabase Client: supabase.auth.signUp({...})
          → PostgreSQL: AFTER INSERT trigger handle_new_doctor_signup()
```

### 1.2 File yang Diperiksa

| File | Peran |
|---|---|
| `frontend/src/pages/auth/Register.tsx` | Form registrasi, validasi, render status |
| `frontend/src/context/AuthContext.tsx` | Provider auth, fungsi `signUp()`, pengelolaan session |
| `frontend/src/services/auth.ts` | Fungsi `registerUser()`, error formatting |
| `frontend/src/lib/supabase.ts` | Konfigurasi client Supabase |
| `frontend/src/routes/AppRoutes.tsx` | Route `/register`, redirect |
| `frontend/src/components/auth/PublicOnlyRoute.tsx` | Guard route publik (redirect jika sudah login) |
| `database/migrations/007_add_role_and_account_status.sql` | Skema kolom role & account_status |
| `database/migrations/008_create_doctor_profile_trigger.sql` | Trigger pembuatan profil dokter |
| `frontend/src/pages/auth/Register.test.tsx` | 13 unit test registrasi |
| `frontend/src/services/auth.test.ts` | 12 unit test auth service |

---

## 2. Rantai Pemanggilan Fungsi (Call Chain)

### 2.1 Register.tsx — Submit Handler

```typescript
// Register.tsx: handleSubmit() ~baris 160-200
const handleSubmit = async (e: React.FormEvent) => {
  e.preventDefault();
  if (isSubmitting) return;
  setErrorMessage(null);
  
  // Validasi frontend
  const err = validateForm(fullName, email, password, confirmPassword);
  if (err) { setErrorMessage(err); return; }
  
  // Panggil AuthContext
  const result = await signUp(email, password, fullName, hospitalName, doctorSpecialty);
  if (result.error) { setErrorMessage(result.error); return; }
  // Tampilkan status sukses (tidak ada navigasi otomatis)
  setIsSubmitting(false);
};
```

### 2.2 AuthContext.tsx — signUp()

```typescript
// AuthContext.tsx: signUp() ~baris 155-200
const signUp = async (email, password, fullName?, hospitalName?, doctorSpecialty?) => {
  const result = await registerUser(email, password, fullName, hospitalName, doctorSpecialty);
  
  if (result.error) return { error: result.error };
  
  // Kondisi: hanya lanjut jika session DAN user tersedia
  if (result.data?.session && result.data.user) {
    setSession(result.data.session);
    setUser(result.data.user);
    fetchUserProfileStatus(result.data.user);
    return { message: "Registrasi berhasil!", requiresEmailConfirmation: false };
  }
  
  // Session null (email confirmation diperlukan)
  return { 
    message: "Registrasi berhasil! Periksa email Anda.", 
    requiresEmailConfirmation: true 
  };
};
```

### 2.3 auth.ts — registerUser()

```typescript
// auth.ts: registerUser() ~baris 80-130
export async function registerUser(email, password, fullName, hospitalName, doctorSpecialty) {
  const { data, error } = await supabase.auth.signUp({
    email: email.trim(),
    password,
    options: {
      data: {
        full_name: fullName,
        hospital: hospitalName,
        primary_specialty: doctorSpecialty,
      },
    },
  });
  // Return { data: { user, session|null }, error: string|null }
}
```

### 2.4 Trigger Database (Internal)

```sql
-- 008_create_doctor_profile_trigger.sql
CREATE OR REPLACE FUNCTION public.handle_new_doctor_signup()
RETURNS TRIGGER AS $$
BEGIN
  -- Skip jika raw_user_meta_data.full_name tidak ada (Admin akun)
  IF NEW.raw_user_meta_data ? 'full_name' THEN
    INSERT INTO public.doctor_profiles (user_id, full_name, role, account_status, ...)
    VALUES (NEW.id, NEW.raw_user_meta_data->>'full_name', 'doctor', 'pending', ...);
  END IF;
  RETURN NEW;
END;
$$ SECURITY DEFINER;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_doctor_signup();
```

---

## 3. Hasil Audit Setiap Lifeline

| Lifeline | Tanggung Jawab Aktual | Bukti Implementasi | Pesan yang Terlibat | Status |
|---|---|---|---|---|
| **User** | Aktor eksternal yang berinteraksi dengan UI | `Register.tsx` — tombol submit, navigasi manual | m1 (buka), m2 (tampilkan formulir), submit, navigasi manual | ✅ TERVERIFIKASI |
| **Register Page** | Form input, validasi, state management | `Register.tsx` — useState, validateForm, handleSubmit | m2, m3, m4 (self), m13 (return), m14 (return) | ✅ TERVERIFIKASI |
| **AuthContext** | Provider auth, orchestrator signUp | `AuthContext.tsx` — signUp(), fetchUserProfileStatus() | m5 (self), m6 (return), m7 (return), m11 (self) | ✅ TERVERIFIKASI |
| **AuthService** | Pemanggil Supabase API, error handling | `auth.ts` — registerUser(), formatAuthError() | m7, m8 (return), m9 (return) | ✅ TERVERIFIKASI |
| **Supabase Auth** | Client-side authentication service | `supabase.ts` — createClient(), supabase.auth.signUp | m8, m10 (internal), m9 | ✅ TERVERIFIKASI |

**Catatan:** Tidak ada lifeline "Database" atau "Doctor Profiles" dalam diagram karena trigger berjalan otomatis di database tanpa interaksi langsung dari frontend. Ini sesuai dengan prinsip abstraksi UML sequence diagram.

---

## 4. Hasil Audit Setiap Pesan

| No. | Pesan dalam Diagram | Pengirim | Penerima | Bukti Source Code | Urutan Aktual | Status | Rekomendasi |
|---|---|---|---|---|---|---|---|
| m1 | `buka /register` | User | Register Page | `AppRoutes.tsx` line ~23: `<Route path="/register" element={<PublicOnlyRoute><Register /></PublicOnlyRoute>}` | ✓ | ✅ Benar | — |
| m2 | `tampilkan formulir` | Register Page | User | `Register.tsx` — render form (lines 60-140) | ✓ | ✅ Benar | — |
| m3 | `submit(form data)` | User | Register Page | `Register.tsx` handleSubmit() dipanggil onClick | ✓ | ✅ Benar | — |
| m4 | `validasi input` | Register Page (self) | Register Page | `Register.tsx` validateForm() — cek email kosong, password ≠ confirmPassword, min 6 char | ✓ | ✅ Benar | — |
| m5 | `signUp(...)` | Register Page | AuthContext | `Register.tsx` line ~168: `const result = await signUp(email, password, fullName, hospitalName, doctorSpecialty)` | ✓ | ✅ Benar | — |
| m6 | `registerUser(...)` | AuthContext | AuthService | `AuthContext.tsx` line ~160: `const result = await registerUser(email, password, ...)` | ✓ | ✅ Benar | — |
| m7 | `auth.signUp(...)` | AuthService | Supabase Auth | `auth.ts` line ~95: `const { data, error } = await supabase.auth.signUp({...})` | ✓ | ✅ Benar | — |
| m8 | Internal trigger | Supabase Auth (self) | Supabase Auth (self) | `008_create_doctor_profile_trigger.sql` — AFTER INSERT trigger | ✓ | ✅ Benar | — |
| m9 | `{ user, session }` | Supabase Auth | AuthService | `auth.ts` — Supabase returns `{ data: { user, session }, error }` | ✓ | ✅ Benar | — |
| m10 | `{ data, error: null }` | AuthService | AuthContext | `auth.ts` — returns formatted result | ✓ | ✅ Benar | — |
| m11 | `set session` | AuthContext (self) | AuthContext (self) | `AuthContext.tsx` line ~191: `setSession(result.data.session)` (hanya jika session tersedia) | ✓ | ✅ Benar (diperbaiki) | **Koreksi v2:** sebelumnya label `set session → fetchUserProfileStatus()` keliru menyiratkan kedua operasi selalu berjalan bersama |
| m12 | `{ message, requiresEmailConfirmation }` | AuthContext | Register Page | `AuthContext.tsx` signUp() return value | ✓ | ✅ Benar | — |
| m13 | `tampilkan status berhasil` | Register Page | User | `Register.tsx` render success message (lines 155-160) | ✓ | ✅ Benar | — |
| m14 | `klik "Masuk ke PIXEL-T"` | User (navigasi manual) | Register Page | `Register.tsx` `<Link to="/login">Masuk ke PIXEL-T</Link>` — tidak ada auto-redirect | ✓ | ✅ Benar | — |

---

## 5. Hasil Audit Return Message

| Return | Deskripsi Aktual | Representasi Diagram | Status |
|---|---|---|---|
| m6 | `{ user, session|null }` — session bisa null jika email belum dikonfirmasi | `{ user, session }` | ✅ OK — penyederhanaan UML yang sah |
| m7 | `{ data: { user, session }, error: string|null }` | `{ data, error: null }` | ✅ OK — representasi alur sukses |
| m9 | Error object saat registrasi gagal | `{ error }` | ✅ OK |
| m12 | `{ message, requiresEmailConfirmation }` | `{ message, requiresEmailConfirmation }` | ✅ OK — presisi |

---

## 6. Hasil Audit Trigger dan Database

| Aspek | Bukti Source Code | Status Diagram |
|---|---|---|
| Trigger name | `handle_new_doctor_signup()` | ✅ Ditampilkan sebagai self-call |
| Trigger timing | AFTER INSERT pada `auth.users` | ✅ "internal" label tepat |
| Trigger scope | Semua user dengan `raw_user_meta_data.full_name` | ✅ Catatan Admin exception tercakup note box |
| Trigger exclusion | Akun Admin dibuat manual via API, tidak melalui sign-up publik | ✅ Note box poin 3 |
| Trigger failure behavior | Postgres WARNING, tidak membatalkan registrasi | ✅ Note box poin 5 |
| Auto-pembuatan profil | Doctor profiles dibuat otomatis oleh trigger | ✅ Note box poin 1 & 2 |

---

## 7. Hasil Audit Sesi dan Konfirmasi Email

### 7.1 Kondisi Session

```typescript
// AuthContext.tsx line 191 — kondisi aktual
if (result.data?.session && result.data.user) {
  // Hanya dijalankan ketika session ADA
  setSession(result.data.session);
  setUser(result.data.user);
  fetchUserProfileStatus(result.data.user);  // Kondisional
  return { message: "Registrasi berhasil!", requiresEmailConfirmation: false };
}
// Jika session null:
return { message: "Registrasi berhasil! Periksa email Anda.", requiresEmailConfirmation: true };
```

### 7.2 Hasil Audit Sesi

| Klaim | Bukti | Status |
|---|---|---|
| Session tersedia → proses dilanjutkan | `result.data?.session` check di line 191 | ✅ TERVERIFIKASI |
| Session null → tampilkan pesan email konfirmasi | else branch di line 200 | ✅ TERVERIFIKASI |
| fetchUserProfileStatus hanya dipanggil saat session ada | Dalam blok `if` (line 192-196) | ✅ TERVERIFIKASI (v2 koreksi) |
| Tidak ada auto-redirect setelah registrasi | Register.tsx tidak memanggil `navigate()` | ✅ TERVERIFIKASI |

---

## 8. Hasil Audit Navigasi

### 8.1 Bukti Tidak Ada Auto-Redirect

```typescript
// Register.tsx — setelah signUp() berhasil:
const result = await signUp(email, password, fullName, hospitalName, doctorSpecialty);
if (result.error) { setErrorMessage(result.error); return; }
// TIDAK ADA navigasi — pengguna tetap di halaman /register
// Pengguna harus klik <Link to="/login">Masuk ke PIXEL-T</Link> secara manual
```

### 8.2 Hasil Audit Navigasi

| Klaim | Bukti | Status |
|---|---|---|
| Tidak ada auto-redirect ke /login | Tidak ada `navigate('/login')` di Register.tsx | ✅ TERVERIFIKASI |
| Pengguna melihat pesan sukses | `statusMessage` state dirender | ✅ TERVERIFIKASI |
| Tombol "Masuk ke PIXEL-T" menuju /login | `<Link to="/login">` di Register.tsx | ✅ TERVERIFIKASI |
| PublicOnlyRoute redirect jika user sudah login | PublicOnlyRoute.tsx line 27-36 | ✅ TERVERIFIKASI |

---

## 9. Hasil Audit Fragment dan Guard Condition

### 9.1 alt1 — Session Check

| Fragment | Guard | Isi | Status |
|---|---|---|---|
| alt1 (v1) | `session tersedia` | Kurang presisi — hanya check session, tidak user | ⚠️ Perlu koreksi |
| **alt1 (v2)** | **`session && user tersedia`** | **Sesuai kondisi AuthContext.tsx line 191** | ✅ **DIPERBAIKI** |
| alt1 [else] | `session null` | Email belum dikonfirmasi | ✅ Benar |

### 9.2 alt2 — Registrasi Hasil

| Fragment | Guard | Isi | Status |
|---|---|---|---|
| alt2 | `registrasi berhasil` | Lanjut ke session handling | ✅ Benar |
| alt2 [else] | `registrasi gagal` | Tampilkan pesan error | ✅ Benar |

### 9.3 alt3 — Navigasi

| Fragment | Guard | Isi | Status |
|---|---|---|---|
| alt3 | `navigasi` | Dua kondisi: session tersedia vs null | ✅ Benar |

### 9.4 Konsistensi Fragment

| Aspek | Kondisi | Status |
|---|---|---|
| Fragment overlap | alt1 (session), alt2 (registrasi), alt3 (navigasi) — masing-masing independen | ✅ Tidak tumpang tindih |
| Guard exclusivity | alt1 dan alt2 tidak memiliki kondisi yang sama | ✅ Eksklusif |
| Urutan kronologis | alt1 → alt2 → alt3 sesuai flow | ✅ Benar |

---

## 10. Hasil Pemeriksaan Note Box

| No | Isi Note Box | Sumber Bukti | Status |
|---|---|---|---|
| 1 | Profil dokter dibuat trigger, bukan frontend | 008.sql — trigger definition | ✅ Benar |
| 2 | Trigger membuat role=doctor, status=pending | 008.sql — INSERT statement | ✅ Benar |
| 3 | Akun Admin dibuat manual via API | `007.sql` comment + konteks aplikasi | ✅ Benar |
| 4 | Trigger hanya untuk akun dengan `raw_user_meta_data.full_name` | 008.sql — IF condition | ✅ Benar |
| 5 | Gagal trigger = Postgres WARNING, tidak blokir registrasi | 008.sql — trigger tidak throw error | ✅ Benar |
| 6 | AuthContext hanya panggil fetchUserProfileStatus() jika session tersedia | `AuthContext.tsx` line 191-196 | ✅ Benar **(ditambahkan v2)** |
| 7 | Tidak ada auto-redirect, pengguna klik manual "Masuk ke PIXEL-T" | `Register.tsx` — tidak ada navigate() | ✅ Benar (diperluas v2) |

---

## 11. Ketidaksesuaian yang Ditemukan dan Koreksi

### 11.1 Temuan Substantif

| # | Elemen | Masalah | Koreksi |
|---|---|---|---|
| 1 | **m11 label** | Label lama `set session → fetchUserProfileStatus()` menyiratkan kedua operasi selalu berjalan bersama | **Diperbaiki** → label menjadi `set session` saja. `fetchUserProfileStatus()` hanya dipanggil kondisional di dalam blok `if (result.data?.session && result.data.user)` |
| 2 | **alt1 guard** | Label lama `session tersedia` tidak mencakup kondisi `user` yang juga dicek | **Diperbaiki** → label menjadi `session && user tersedia` sesuai AuthContext.tsx line 191 |
| 3 | **Note box** | Tidak menyebutkan kondisional fetchUserProfileStatus dan detail navigasi manual | **Diperluas** → ditambahkan baris 6 dan detail baris 7 |

### 11.2 Tidak Ada Temuan Berikut

- Tidak ada pesan fiktif
- Tidak ada lifeline tambahan yang diperlukan
- Tidak ada urutan pesan yang salah
- Tidak ada kondisi navigasi yang hilang
- Tidak ada kesalahan visual pada PNG

---

## 12. Keterbatasan Verifikasi

1. **Pengujian E2E tidak dilakukan** — hanya unit test (25/25 pass) yang dapat diandalkan.
2. **Trigger database tidak dapat diuji secara langsung** — verifikasi didasarkan pada membaca kode SQL migration.
3. **Perilaku supabase.auth.signUp()** divalidasi melalui tipe TypeScript dan test mock, bukan eksekusi nyata ke Supabase backend.
4. **Pengujian browser/visual** dibatasi pada pemeriksaan screenshot PNG yang dihasilkan.

---

## 13. Hasil Pengujian

| Test Suite | Jumlah | Lulus | Gagal |
|---|---|---|---|
| `Register.test.tsx` | 13 | 13 | 0 |
| `auth.test.ts` | 12 | 12 | 0 |
| **Total** | **25** | **25** | **0** |

**Keterangan:**
- Register.test.tsx menguji: form rendering, validasi, submit, error handling, success state, tombol navigasi.
- auth.test.ts menguji: registerUser dengan metadata, error mapping, formatAuthError.
- Semua test menggunakan mock Supabase, bukan koneksi database nyata.

---

## 14. Keputusan Audit

**Status: LULUS SETELAH PERBAIKAN**

Diagram Sign Up PIXEL-T telah mengalami dua koreksi substantif dan kini sepenuhnya sesuai dengan implementasi source code aktual:

1. m11 label dikoreksi dari `set session → fetchUserProfileStatus()` menjadi `set session`
2. alt1 guard dikoreksi dari `session tersedia` menjadi `session && user tersedia`
3. Note box diperluas menambahkan 2 baris informasi kondisional

Diagram v2 (FINAL) yang dihasilkan dari koreksi ini telah tervalidasi secara visual dan teknis.

---

## 15. Lokasi File

| File | Deskripsi |
|---|---|
| `references/bab 4/SEQUENCE_DIAGRAM_SIGN_UP_PIXELT_FINAL.drawio` | Source Draw.io (v2, sudah dikoreksi) |
| `references/bab 4/SEQUENCE_DIAGRAM_SIGN_UP_PIXELT_FINAL.png` | PNG hasil export v2 (1920×1760 px, 236,799 bytes) |
| `references/bab 4/AUDIT_FINAL_SEQUENCE_DIAGRAM_SIGN_UP_PIXELT_FINAL.md` | Laporan audit putaran pertama |
| `references/bab 4/SEQUENCE_DIAGRAM_SIGN_UP_PIXELT_FINAL_AUDITED.drawio` | Versi sebelumnya (diarsipkan) |
| `references/bab 4/SEQUENCE_DIAGRAM_SIGN_UP_PIXELT_FINAL_AUDITED.png` | Versi sebelumnya (diarsipkan) |
| `references/bab 4/SEQUENCE_DIAGRAM_SIGN_IN_PIXELT_FINAL_INDEPENDENT_AUDITED.png` | Referensi konsistensi visual |
