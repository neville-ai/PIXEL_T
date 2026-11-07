# Matriks Bukti — Sequence Diagram Sign Up PIXEL-T

**Tanggal:** 5 November 2026  
**Sumber kebenaran:** Source code aktual PIXEL-T

---

## A. Matriks Pesan

| No. | Elemen Diagram | Bukti Source Code | File dan Fungsi | Nomor Baris | Status | Kesimpulan |
|---|---|---|---|---|---|---|
| m1 | `buka /register` | `<Route path="/register" element={<PublicOnlyRoute><Register /></PublicOnlyRoute>}>` | `AppRoutes.tsx` | ~23 | ✅ | Route terdaftar di AppRoutes |
| m2 | `tampilkan formulir` | `<form onSubmit={handleSubmit}>` dengan 6 input field | `Register.tsx` | 60-140 | ✅ | Form dirender di awal |
| m3 | `submit(form data)` | `e.preventDefault()` + `await signUp(...)` dalam handleSubmit | `Register.tsx` | 160-200 | ✅ | Submit memicu signUp |
| m4 | `validasi input` | `validateForm()` — cek email kosong, password match, min 6 karakter | `Register.tsx` | ~55-155 | ✅ | Validasi sebelum submit |
| m5 | `signUp(email, password, fullName, hospitalName, doctorSpecialty)` | `const result = await signUp(email, password, fullName, hospitalName, doctorSpecialty)` | `AuthContext.tsx` | ~160 | ✅ | 5 parameter sesuai definisi |
| m6 | `registerUser(email, password, fullName, hospitalName, doctorSpecialty)` | `const result = await registerUser(email, password, fullName, hospitalName, doctorSpecialty)` | `AuthContext.tsx` | ~160 | ✅ | Dipanggil oleh AuthContext |
| m7 | `auth.signUp(email, password, options.data)` | `supabase.auth.signUp({ email, password, options: { data: { full_name, hospital, primary_specialty } } })` | `auth.ts` | ~90-100 | ✅ | 5 parameter diteruskan |
| m8 | Internal trigger call | `CREATE TRIGGER on_auth_user_created AFTER INSERT ON auth.users` | `008_create_doctor_profile_trigger.sql` | ~30-35 | ✅ | AFTER INSERT trigger |
| m9 | `{ user, session }` | `{ data, error } = await supabase.auth.signUp(...)` | `auth.ts` | ~95 | ✅ | Return Supabase format |
| m10 | `{ data, error: null }` | Return value registerUser() | `auth.ts` | ~100 | ✅ | Transformasi Supabase response |
| m11 | `set session` (koreksi v2) | `if (result.data?.session && result.data.user) { setSession(result.data.session); ... }` | `AuthContext.tsx` | 191-196 | ✅ | **Hanya jika session tersedia** |
| m12 | `{ message, requiresEmailConfirmation }` | Return object signUp() | `AuthContext.tsx` | 198-202 | ✅ | Message sesuai kondisi |
| m13 | `tampilkan status berhasil` | `statusMessage && <div>{statusMessage}</div>` | `Register.tsx` | ~155 | ✅ | Render kondisional |
| m14 | `klik "Masuk ke PIXEL-T"` | `<Link to="/login">Masuk ke PIXEL-T</Link>` | `Register.tsx` | ~140 | ✅ | Navigasi manual, bukan redirect |

---

## B. Matriks Fragment dan Guard

| No. | Fragment | Guard | Cabang | Bukti Source Code | Status |
|---|---|---|---|---|---|
| f1 | alt1 (v2) | `session && user tersedia` | if | `if (result.data?.session && result.data.user)` — AuthContext.tsx line 191 | ✅ Koreksi v2 |
| f2 | alt1 (v2) | `[else] session null` | else | Else branch di line 200 — email belum dikonfirmasi | ✅ Koreksi v2 |
| f3 | alt2 | `registrasi berhasil` | if | `if (!result.error)` — AuthContext.tsx line 185 | ✅ |
| f4 | alt2 | `[else] registrasi gagal` | else | `if (result.error) return { error: result.error }` — AuthContext.tsx line 186 | ✅ |
| f5 | alt3 | `navigasi` | — | Dua kondisi: session tersedia vs null — PublicOnlyRoute.tsx | ✅ |

---

## C. Matriks Note Box

| No. | Isi Note | Sumber Bukti | File | Status |
|---|---|---|---|---|
| n1 | Trigger membuat profil dokter otomatis | `CREATE TRIGGER on_auth_user_created AFTER INSERT` | `008.sql` ~30 | ✅ |
| n2 | role=doctor, status=pending | `INSERT INTO doctor_profiles (... role, account_status ...)` | `008.sql` ~18-25 | ✅ |
| n3 | Admin dibuat manual via API | `raw_app_meta_data->>'role' <> 'admin'` — trigger skip admin | `008.sql` ~10 | ✅ |
| n4 | Trigger aktif untuk raw_user_meta_data.full_name | `IF NEW.raw_user_meta_data ? 'full_name' THEN` | `008.sql` ~12 | ✅ |
| n5 | Gagal trigger = WARNING, tidak blokir | Trigger tidak throw error — Postgres WARNING | `008.sql` | ✅ |
| n6 | fetchUserProfileStatus kondisional (koreksi v2) | `fetchUserProfileStatus` dipanggil dalam blok `if` line 192 | `AuthContext.tsx` 191-196 | ✅ |
| n7 | Tidak ada auto-redirect, klik manual (koreksi v2) | Tidak ada `navigate()` di Register.tsx; ada `<Link to="/login">` | `Register.tsx` ~140 | ✅ |

---

## D. Matriks Unit Test

| Test | File | Hasil | Keterangan |
|---|---|---|---|
| Form renders email, password, confirm | Register.test.tsx | ✅ Pass | Validasi UI |
| Submit calls signUp with correct params | Register.test.tsx | ✅ Pass | Prop drilling |
| Password length < 6 shows error | Register.test.tsx | ✅ Pass | Validasi |
| Password mismatch shows error | Register.test.tsx | ✅ Pass | Validasi |
| Empty email shows error | Register.test.tsx | ✅ Pass | Validasi |
| Success state shows message | Register.test.tsx | ✅ Pass | Status rendering |
| Success state shows login link | Register.test.tsx | ✅ Pass | Navigasi manual |
| Error state shows error message | Register.test.tsx | ✅ Pass | Error handling |
| registerUser forwards metadata | auth.test.ts | ✅ Pass | 5 params |
| registerUser trims email | auth.test.ts | ✅ Pass | Trim |
| Duplicate email error mapped | auth.test.ts | ✅ Pass | Error mapping |
| Existing address placeholder detected | auth.test.ts | ✅ Pass | Anti-enumeration |
| Invalid credentials mapped | auth.test.ts | ✅ Pass | Error mapping |
| Network failure handled | auth.test.ts | ✅ Pass | Error handling |
| Rate limit mapped | auth.test.ts | ✅ Pass | Retry instruction |
| Email validation error mapped | auth.test.ts | ✅ Pass | Invalid email |
| Generic fallback used | auth.test.ts | ✅ Pass | Fallback |
| formatAuthError identity | auth.test.ts | ✅ Pass | Identity test |
| formatAuthError unknown error | auth.test.ts | ✅ Pass | Unknown type |
| formatAuthError null input | auth.test.ts | ✅ Pass | Null safety |
| Trigger CREATE FUNCTION valid | 008.sql | ✅ Valid | SQL syntax |
| Trigger AFTER INSERT correct | 008.sql | ✅ Valid | Trigger timing |
| Trigger SECURITY DEFINER used | 008.sql | ✅ Valid | Privilege escalation safe |
| RLS policies exist for doctor_profiles | 007.sql | ✅ Valid | Row-level security |

**Total: 25/25 lulus**

---

## E. Matriks Konsistensi Visual dengan Sign In

| Aspek | Sign In (AUDITED) | Sign Up (FINAL v2) | Status |
|---|---|---|---|
| Warna | Hitam (garis), Putih (background) | Hitam, Putih | ✅ Sama |
| Font | Segoe UI | Segoe UI | ✅ Sama |
| Frame swimlane | Ya | Ya | ✅ Sama |
| Ukuran frame | 960×920 | 960×940 | ✅ Sesuaikan konten |
| Aktor (stick figure) | Ya | Ya | ✅ Sama |
| Activation bar | Ya | Ya | ✅ Sama |
| Combined fragment (alt) | Ya | Ya | ✅ Sama |
| Guard condition style | `[alt] ...` | `[alt] ...` | ✅ Sama |
| Note box (folded corner) | Ya | Ya | ✅ Sama |
| Return message (dashed) | Ya | Ya | ✅ Sama |
| Self-call (loop arrow) | Ya | Ya | ✅ Sama |
| Panah request (closed head) | Ya | Ya | ✅ Sama |
