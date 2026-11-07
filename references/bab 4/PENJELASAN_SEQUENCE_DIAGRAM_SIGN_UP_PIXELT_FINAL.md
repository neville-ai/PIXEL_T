# Penjelasan Sequence Diagram Sign Up PIXEL-T (FINAL)

## 1. Pendahuluan

Diagram sequence ini menggambarkan alur registrasi akun dokter pada aplikasi web **PIXEL-T** — sistem informasi manajemen rumah sakit berbasis React + Supabase. Diagram ini telah diaudit secara independen terhadap source code aktual dan memenuhi standar akademik untuk tugas akhir/skripsi.

## 2. Aktor / Lifeline

| No | Lifeline | Peran |
|---|---|---|
| 1 | **User** | Dokter/pengguna baru yang mendaftar melalui halaman `/register` |
| 2 | **Register Page** | Komponen React `Register.tsx` — menangani form, validasi, dan feedback UI |
| 3 | **AuthContext** | Context provider `AuthContext.tsx` — mengelola state auth global aplikasi |
| 4 | **AuthService** | Service layer `auth.ts` — abstraction dari Supabase Auth SDK |
| 5 | **Supabase Auth** | Backend authentication service (Supabase) + database trigger otomatis |

> **Catatan:** Database trigger tidak ditampilkan sebagai lifeline terpisah karena merupakan mekanisme internal Supabase yang dipicu secara otomatis oleh event `AFTER INSERT` pada tabel `auth.users`.

## 3. Alur Utama (Main Flow)

### 3.1 Tahap 1 — Akses Halaman Registrasi

```
User → Register Page : buka /register
Register Page → User : tampilkan formulir
```

Pengguna mengakses rute `/register` yang dilindungi oleh `PublicOnlyRoute` (hanya accessible untuk guest/user belum login). Register Page merender form dengan 6 field input:

1. **Nama Lengkap** (`fullName`) — wajib
2. **Email** (`email`) — wajib, format validasi regex
3. **Password** (`password`) — wajib, minimal 6 karakter
4. **Konfirmasi Password** (`confirmPassword`) — wajib, harus sama dengan password
5. **Nama Rumah Sakit** (`hospitalName`) — wajib
6. **Spesialisasi** (`doctorSpecialty`) — wajib

### 3.2 Tahap 2 — Submit & Validasi

```
User → Register Page : submit(form data)
Register Page → Register Page : validasi input
```

Saat tombol "Daftar" diklik, fungsi `handleSubmit()` dipanggil. Sebelum mengirim ke server, validasi client-side dilakukan:

| Rule | Implementasi | Error Message |
|---|---|---|
| Email kosong | `if (!email.trim())` | "Email wajib diisi" |
| Password kosong | `if (!password)` | "Password wajib diisi" |
| Password < 6 karakter | `if (password.length < 6)` | "Password minimal 6 karakter" |
| Confirm password ≠ password | `if (password !== confirmPassword)` | "Konfirmasi password tidak cocok" |
| Hospital name kosong | `if (!hospitalName.trim())` | "Nama rumah sakit wajib diisi" |
| Specialty kosong | `if (!doctorSpecialty.trim())` | "Spesialisasi wajib diisi" |

Jika validasi gagal, error message ditampilkan di setiap field input tanpa mengirim data ke server.

### 3.3 Tahap 3 —呼叫 Auth Context

```
Register Page → AuthContext : signUp(email, password, fullName, hospitalName, doctorSpecialty)
```

Jika validasi lolos, fungsi `signUp()` dari `useAuth()` hook dipanggil dengan 5 parameter. AuthContext adalah singleton context yang menyediakan state auth global ke seluruh aplikasi.

### 3.4 Tahap 4 — Service Layer Call

```
AuthContext → AuthService : registerUser(email, password, fullName, hospitalName, doctorSpecialty)
```

AuthContext meneruskan panggilan ke `registerUser()` di `auth.ts` — service layer yang berisi abstraction dari Supabase Auth SDK. Service ini menangani error mapping, sanitasi pesan error, dan transformasi response.

### 3.5 Tahap 5 — Supabase Auth API

```
AuthService → Supabase Auth : auth.signUp(email, password, options.data)
```

Service memanggil `supabase.auth.signUp()` dengan payload:
- `email`: string email pengguna
- `password`: string password
- `options.data`: metadata JSON { full_name, hospital_name, doctor_specialty }

### 3.6 Tahap 6 — Database Trigger (Internal)

```
Supabase Auth → Supabase Auth : buat auth.users → AFTER INSERT trigger
```

Setelah akun berhasil dibuat di `auth.users`, Supabase secara otomatis memicu trigger `handle_new_doctor_signup()` yang:

1. Mengecek apakah `raw_user_meta_data->>'full_name'` ada (untuk mengecualikan akun Admin)
2. Jika ada, INSERT baris baru ke tabel `doctor_profiles` dengan:
   - `id` = UID dari auth.users
   - `full_name` = dari metadata
   - `hospital_name` = dari metadata
   - `specialty` = dari metadata
   - `role` = `'doctor'` (default)
   - `account_status` = `'pending'` (default)

> **Penting:** Trigger berjalan di sisi database (PostgreSQL), bukan di frontend. Kegagalan trigger hanya menghasilkan Postgres WARNING log, tidak memblokir proses registrasi.

### 3.7 Tahap 7 — Response Chain (Kembali ke Atas)

```
Supabase Auth → AuthService : { user, session }
AuthService → AuthContext : { data, error: null }
AuthContext → AuthContext : set session → fetchUserProfileStatus()
AuthContext → Register Page : { message, requiresEmailConfirmation }
Register Page → User : tampilkan status berhasil
```

**Detail response chain:**

1. **Supabase Auth** mengembalikan objek `{ user, session }` — user object berisi metadata akun, session object berisi access token.

2. **AuthService** membungkus response dalam format `{ data, error }` standar. Jika sukses: `{ data: { user, session }, error: null }`.

3. **AuthContext** menerima response dan:
   - Men-set session ke state global (`setCurrentSession(session)`)
   - Memanggil `fetchUserProfileStatus(userId)` untuk mengambil status akun dari tabel `doctor_profiles`
   - Menyiapkan response message berdasarkan konfigurasi email verification Supabase

4. **Register Page** menerima `{ message, requiresEmailConfirmation }` dan:
   - Menyimpan ke state `registrationSuccess`
   - Menampilkan feedback UI sesuai kondisi (lihat Alt 1 & Alt 3 di bawah)

## 4. Fragment Kondisi (Alt)

### 4.1 Alt 1 — Session Tersedia vs Session Null

**Kondisi:** Apakah Supabase mengaktifkan auto-confirm email?

| Kondisi | Perilaku |
|---|---|
| `[alt] session tersedia` | Akun langsung aktif, user otomatis login, dapat langsung mengakses aplikasi |
| `[else] session null` | Akun dibuat tapi belum dikonfirmasi email, user harus klik link di email untuk aktivasi |

**Implementasi kode:**
```typescript
if (result.data?.session) {
  // Auto-login successful
  setCurrentSession(result.data.session);
} else {
  // Email confirmation required
  showSuccessMessage("Pendaftaran berhasil! Cek email Anda untuk konfirmasi.");
}
```

### 4.2 Alt 2 — Registrasi Berhasil vs Gagal

**Kondisi:** Apakah Supabase Auth menerima permintaan registrasi?

| Kondisi | Perilaku |
|---|---|
| `[alt] registrasi berhasil` | Lanjut ke Alt 1 (cek session) |
| `[else] registrasi gagal` | Tampilkan pesan error ke user |

**Sumber error:**
- Email sudah terdaftar → `"Email already registered"`
- Password terlalu lemah → `"Password should be at least 6 characters"`
- Invalid email format → `"Invalid email"`
- Network error → `"Connection error, please try again"`

### 4.3 Alt 3 — Navigasi Pasca-Success

**Kondisi:** Apa yang terjadi setelah registrasi berhasil?

| Kondisi | Perilaku |
|---|---|
| `[alt] session tersedia` | User tetap di halaman register, bisa klik "Masuk ke PIXEL-T" untuk manual login jika mau |
| `[else] session null` | User tetap di halaman register, melihat pesan "Cek email untuk konfirmasi", klik "Masuk ke PIXEL-T" untuk ke halaman login |

> **⚠️ PENTING — Koreksi dari FINAL_AUDITED:**
> 
> Diagram FINAL_AUDITED sebelumnya mengklaim adanya "auto-redirect ke /dashboard". **Ini salah.** Setelah registrasi berhasil, **tidak ada** auto-redirect. User harus secara manual mengklik tombol "Masuk ke PIXEL-T" yang mengarah ke `/login`. Kode sumber `Register.tsx` tidak mengandung statement `navigate('/...')` atau `window.location.href` apa pun setelah registrasi berhasil.

## 5. Catatan Teknis Penting

### 5.1 Peran Trigger Database

Trigger `handle_new_doctor_signup()` adalah komponen kunci arsitektur PIXEL-T:

| Aspek | Detail |
|---|---|
| **Waktu eksekusi** | AFTER INSERT pada `auth.users` |
| **Security definer** | Ya — berjalan dengan privilege owner tabel |
| **Pengecualian** | Akun dengan `raw_user_meta_data` null (Admin dibuat via API) |
| **Error handling** | Soft fail — log warning, tidak memblokir registrasi |
| **Default role** | `role = 'doctor'` untuk semua akun user |
| **Default status** | `account_status = 'pending'` (menunggu approval admin) |

### 5.2 Perbedaan Akun User vs Admin

| Aspek | Akun User (Dokter) | Akun Admin |
|---|---|---|
| **Cara pembuatan** | Sign-up publik via form | Supabase Admin API (manual) |
| **Trigger** | ✅ Dipicu | ❌ Dilewati (no `full_name` metadata) |
| **Role default** | `doctor` | `admin` |
| **Status default** | `pending` | `approved` |
| **Email confirmation** | Optional (tergantung config) | Tidak diperlukan |

### 5.3 Alur Approval Dokter

Setelah registrasi berhasil, alur selanjutnya (di luar scope diagram ini):

1. Dokter menunggu email konfirmasi (jika email verification aktif)
2. Dokter klik link konfirmasi di email
3. Admin rumah sakit men-review profil dokter di dashboard admin
4. Admin menyetujui (`account_status = 'approved'`) atau menolak (`rejected`)
5. Setelah approved, dokter dapat login dan mengakses sistem

## 6. Justifikasi Akademik

Diagram ini memenuhi standar UML Sequence Diagram berdasarkan:

1. **Standar OMG UML 2.5** — penggunaan lifeline, activation bar, message, alt fragment sesuai spesifikasi.
2. **Konsistensi dengan Sign In Diagram** — gaya visual (hitam-putih, font Segoe UI, frame swimlane) seragam dengan diagram Sign In FINAL_AUDITED.
3. **Traceability ke source code** — setiap pesan dan fragment dapat dilacak ke baris kode spesifik.
4. **Keakuratan teknis** — tidak ada klaim yang bertentangan dengan implementasi sesungguhnya.
5. **Kejelasan komunikasi** — notasi cukup sederhana untuk dipahami pembaca non-teknis namun detail untuk reviewer teknis.

---

*Catatan: File ini adalah penjelasan pendamping dari SEQUENCE_DIAGRAM_SIGN_UP_PIXELT_FINAL.png dan SEQUENCE_DIAGRAM_SIGN_UP_PIXELT_FINAL.drawio.*
