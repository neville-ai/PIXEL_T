# LAPORAN AUDIT & PERBAIKAN: KESESUAIAN "MASUK SEBAGAI" PADA HALAMAN LOGIN PIXEL-T

**Tanggal:** 9 November 2026  
**Status:** Selesai, Terverifikasi Otomatis, Uncommitted  
**Dokumen Referensi Skripsi:** Bab 4.2 (Activity Diagram Sign In), Bab 4.3 (Sequence Diagram Sign In), Tabel 4.2 (Use Case Sign In), Bab 5.5 (Halaman Login).

---

## 1. AKAR MASALAH

Pada implementasi sebelumnya, ketika pengguna memilih opsi **"Dokter"** pada dropdown *"Masuk sebagai"* lalu memasukkan kredensial akun dengan peran **ADMIN**, login **berhasil** dan pengguna diarahkan ke `/admin`. Hal ini bertentangan dengan aturan otorisasi dua arah.

### Kutipan Kode Sebelum Perbaikan (`Frontend/src/context/AuthContext.tsx` baris 141–171):

```tsx
    if (result.data) {
      setUser(result.data.user);
      setSession(result.data.session);

      // Resolve the actual role and status from trusted sources:
      const appMetaRole = getAdminRoleFromAppMetadata(result.data.user);
      const profileInfo = await fetchUserProfileStatus(result.data.user);

      const actualRole = appMetaRole === 'admin' ? 'admin' : profileInfo?.role ?? null;
      const actualStatus = profileInfo?.accountStatus ?? null;

      setRole(actualRole);
      setAccountStatus(actualStatus);

      // Role mismatch: user selected a context that doesn't match their actual role.
      if (selectedRole === 'admin' && actualRole !== 'admin') {
        return {
          error:
            'Jenis akun tidak sesuai dengan hak akses akun Anda. Silakan pilih jenis akun yang benar.',
        };
      }
      if (selectedRole === 'doctor' && actualRole === 'admin') {
        return {
          error:
            'Jenis akun tidak sesuai dengan hak akses akun Anda. Silakan pilih jenis akun yang benar.',
        };
      }
    }
```

### Analisis Akar Masalah:
1. **Pencemaran State Sebelum Verifikasi:**  
   State `user` dan `session` (baris 142–143) serta `role` dan `accountStatus` (baris 154–155) telah di-commit ke state React `AuthContext` **SEBELUM** evaluasi kecocokan role dijalankan.
2. **Pengambilalihan Rute oleh `PublicOnlyRoute` (*Hijack Redirect*):**  
   Halaman `/login` dibungkus oleh `<PublicOnlyRoute>` (`Frontend/src/routes/AppRoutes.tsx:29`). Begitu `user` terisi dan `role === 'admin'`, `PublicOnlyRoute` langsung mengevaluasi `if (user && role === 'admin') return <Navigate to="/admin" replace />;` pada render cycle berikutnya. Komponen `<Login />` seketika di-unmount dan pengguna terlempar ke `/admin` sebelum pesan error sempat ditampilkan.
3. **Ketiadaan Pembersihan Sesi (`signOut` Tidak Dipanggil):**  
   Saat blok mismatch mengembalikan objek `{ error: ... }`, fungsi `logoutUser()` atau `supabase.auth.signOut()` **sama sekali tidak dipanggil**. Akibatnya, sesi Supabase Auth tetap aktif tersimpan di `localStorage` peramban. Jika pengguna me-refresh halaman, pengguna langsung dikenali sebagai admin terotentikasi.
4. **Race Condition pada Listener `onAuthStateChange`:**  
   Pemanggilan `supabase.auth.signInWithPassword` di dalam `loginUser` secara asinkron memicu event `SIGNED_IN` pada listener `onAuthStateChange` (`AuthContext.tsx:99`). Listener ini secara independen memperbarui `user`, `session`, dan `role`, mendahului penanganan error di `signIn`.

---

## 2. DIFF RINGKAS PERUBAHAN & PENJELASAN

Perbaikan dirancang minimalis dan ketat pada 3 file kode utama:

### 1. `Frontend/src/utils/auth.ts`
- **Penambahan fungsi `isRoleMatch` (baris 336–347):**
  ```ts
  export function isRoleMatch(
    selected: 'admin' | 'doctor',
    actual: string | null
  ): boolean {
    return selected === actual;
  }
  ```
  *Alasan:* Menyediakan fungsi perbandingan tegas dua arah (*strict equality*) tanpa percabangan khusus, memastikan `'doctor'` hanya cocok dengan `'doctor'` dan `'admin'` hanya cocok dengan `'admin'`.

### 2. `Frontend/src/context/AuthContext.tsx`
- **Penambahan `isVerifyingRoleRef` & Proteksi `onAuthStateChange` (baris 56, 107–111):**  
  Mencegah listener `onAuthStateChange` memperbarui state React saat alur `signIn` sedang memvalidasi kecocokan peran.
- **Pengecekan Dua Arah Sebelum Commit State & Pembersihan Penuh (baris 171–193):**  
  Resolusi role dilakukan terlebih dahulu. Jika `!isRoleMatch(targetSelectedRole, actualRole)`:
  1. Memanggil `await logoutUser()` untuk membatalkan sesi Supabase.
  2. Mereset seluruh state: `setUser(null)`, `setSession(null)`, `setRole(null)`, `setAccountStatus(null)`.
  3. Mengembalikan pesan netral: `"Jenis akun yang dipilih tidak sesuai dengan akun ini. Silakan pilih jenis akun yang benar."` (tanpa membocorkan peran asli akun).
  4. State `user` dan `session` hanya di-commit jika `isRoleMatch` mengembalikan `true`.
- **Pembaruan signature `signIn` (baris 25–29):**  
  Mengembalikan `{ error?: string; role?: string | null; accountStatus?: string | null }` agar komponen pemanggil dapat membaca role hasil resolusi tanpa bergantung pada closure render lama.

### 3. `Frontend/src/pages/auth/Login.tsx`
- **Penyelarasan Navigasi Berdasarkan Hasil Resolusi (baris 126–128):**  
  Menggunakan `const resolvedRole = result.role ?? role;` dan `const resolvedStatus = result.accountStatus ?? accountStatus;` sehingga navigasi admin ke `/admin` atau dokter approved ke `/dashboard` tidak mengalami *stale closure*.

---

## 3. TABEL PENGUJIAN BARU & HASIL SUITE LENGKAP

### Pengujian Unit Baru:

| File Tes | Nama Tes | Skenario | Hasil |
| :--- | :--- | :--- | :---: |
| `src/services/auth.test.ts` | `strict equality match` | `isRoleMatch('admin','admin')` dan `isRoleMatch('doctor','doctor')` $\rightarrow$ `true` | **PASSED** |
| `src/services/auth.test.ts` | `two-way enforcement mismatch` | `isRoleMatch('admin','doctor')` dan `isRoleMatch('doctor','admin')` $\rightarrow$ `false` | **PASSED** |
| `src/services/auth.test.ts` | `null / unknown role check` | `isRoleMatch` dengan `null` atau `patient` $\rightarrow$ `false` | **PASSED** |
| `src/context/AuthContext.test.tsx` | `pilih Dokter + akun admin` | Input selected='doctor', akun admin $\rightarrow$ Error netral, `logoutUser` dipanggil 1x, state user/session null, tidak redirect | **PASSED** |
| `src/context/AuthContext.test.tsx` | `pilih Admin + akun dokter` | Input selected='admin', akun dokter $\rightarrow$ Error netral, `logoutUser` dipanggil 1x, state user/session null, tidak redirect | **PASSED** |
| `src/context/AuthContext.test.tsx` | `pilih Dokter + dokter approved` | Input selected='doctor', akun approved $\rightarrow$ Berhasil, state tersimpan, role='doctor' | **PASSED** |
| `src/context/AuthContext.test.tsx` | `pilih Admin + admin` | Input selected='admin', akun admin $\rightarrow$ Berhasil, state tersimpan, role='admin' | **PASSED** |
| `src/context/AuthContext.test.tsx` | `pilih Dokter + dokter pending` | Role match berhasil, status pending dipertahankan | **PASSED** |
| `src/context/AuthContext.test.tsx` | `kredensial salah` | Error kredensial diteruskan, `logoutUser` tidak dipanggil berlebih, state null | **PASSED** |
| `src/pages/auth/Login.test.tsx` | `menolak login Dokter jika admin` | UI Login menampilkan banner alert error netral, form tetap terbuka, tidak ada redirect | **PASSED** |
| `src/pages/auth/Login.test.tsx` | `menolak login Admin jika dokter` | UI Login menampilkan banner alert error netral, form tetap terbuka, tidak ada redirect | **PASSED** |

### Perbandingan Hasil Test Suite:

| Suite Pengujian | Baseline Sebelum Perbaikan | Hasil Sesudah Perbaikan | Status |
| :--- | :---: | :---: | :---: |
| **Frontend Vitest** (`Frontend/`) | 285 passed (18 files) | **294 passed (19 files)** | **LULUS 100% (+9 tests baru)** |
| **Backend Pytest** (`tests/`) | 159 passed | **159 passed** | **LULUS 100% (No Regression)** |
| **Typecheck & Build** (`tsc -b && vite build`) | — | **0 errors, built in 15.13s** | **LULUS 100%** |

---

## 4. HASIL PEMERIKSAAN REGRESI HALAMAN LAIN

Dilakukan audit kode pemanggil terhadap fungsi yang dimodifikasi (`signIn`, `AuthContext`, `isRoleMatch`):
1. **Sign Up (`/register`):** Memanggil `signUp()` di `AuthContext`. Alur pendaftaran dokter tidak tersentuh dan tetap berjalan normal.
2. **Sign Out (`AppShell.tsx`):** Memanggil `signOut()` di `AuthContext`. Alur logout tetap memanggil `logoutUser()` dan membersihkan state.
3. **Route Guards (`ProtectedRoute`, `AdminRoute`, `DoctorRoute`, `PublicOnlyRoute`):** Tidak ada perubahan kontrak API `useAuth()`. Seluruh guard tetap berfungsi normal sesuai perannya masing-masing.
4. **Doctor Profile (`/profile`):** Membaca `user` dari `useAuth()`. Berfungsi normal.
5. **Admin Dashboard (`/admin`):** Membaca `user` dan `session` dari `useAuth()`. Akses admin tetap terjaga.

---

## 5. TEMUAN TAMBAHAN DI LUAR LINGKUP

Berikut adalah temuan arsitektural yang dicatat selama audit tanpa diubah pada perbaikan minimal ini:

1. **Otorisasi Sisi Server (Backend Flask):**  
   - *Status:* **AMAN / ROBUST**. Endpoint `/api/admin/*` diverifikasi ketat oleh decorator `@require_admin` di `Backend/src/core/auth.py` yang memeriksa klaim token `app_metadata.role == 'admin'`. Bahkan jika seorang dokter membobol proteksi frontend, panggilan API ke admin route akan menerima HTTP 403 Forbidden.
2. **Pengecekan Peran pada `ProtectedRoute`:**  
   - *Severity:* **LOW (Peningkatan Arsitektural)**.  
   - *Observasi:* `ProtectedRoute` (`Frontend/src/components/auth/ProtectedRoute.tsx`) saat ini memeriksa `!user`, `accountStatus === 'pending'`, dan `accountStatus === 'rejected'`. Karena admin memiliki `accountStatus === null`, admin secara teknis diizinkan oleh `ProtectedRoute` jika mengakses URL `/dashboard` secara langsung (meskipun tombol menu disembunyikan di `AppShell`).  
   - *Rekomendasi:* Di masa mendatang, `ProtectedRoute` dapat ditambahkan klausul `if (role === 'admin') return <Navigate to="/admin" replace />;` sebagaimana yang sudah ada di `DoctorRoute`.

---

## 6. REKOMENDASI REVISI DOKUMEN SKRIPSI

1. **Bab 4.2 (Activity Diagram Sign In):**  
   - Pada alur setelah validasi kredensial Supabase, diagram perlu memperjelas urutan:
     `Membaca app_metadata.role dan doctor_profiles` $\rightarrow$ `Decision: Role cocok dengan akun?` $\rightarrow$ Jika **Tidak**: `Memanggil signOut(), membersihkan sesi, dan menampilkan pesan jenis akun tidak sesuai` $\rightarrow$ Kembali ke form Sign In.
2. **Bab 4.3 (Sequence Diagram Sign In):**  
   - Pesan balikan saat role mismatch harus mencatat pemanggilan `supabase.auth.signOut()` oleh `AuthContext` sebelum mengembalikan pesan error ke `LoginView`.
3. **Tabel 4.2 (Use Case Sign In):**  
   - Menambahkan skenario alternatif:  
     *2b. Pengguna memilih jenis akun yang tidak sesuai dengan peran aktual akun (mis. Akun Admin memilih Dokter, atau Akun Dokter memilih Admin). Sistem membatalkan sesi, menampilkan pesan "Jenis akun yang dipilih tidak sesuai dengan akun ini. Silakan pilih jenis akun yang benar", dan mempertahankan pengguna pada halaman Sign In.*
4. **Bab 5.5 (Implementasi Antarmuka Halaman Login):**  
   - Memastikan teks pesan kesalahan role mismatch tercatat konsisten:  
     *"Jenis akun yang dipilih tidak sesuai dengan akun ini. Silakan pilih jenis akun yang benar."*

---

## 7. ITEM TIDAK TERVERIFIKASI & CARA MEMVERIFIKASI

- **TIDAK TERVERIFIKASI:** Interaksi riil langsung dengan instans Supabase produksi menggunakan akun dokter dan admin ber-kredensial nyata (karena dilarang oleh aturan kerja).
- **Cara Verifikasi:**  
  Dapat diverifikasi secara manual di lingkungan pengujian lokal (`localhost`) dengan:
  1. Membuka peramban di `http://localhost:5173/login`.
  2. Memilih dropdown "Dokter", memasukkan email & password akun admin lokal $\rightarrow$ pastikan muncul pesan error merah, URL tetap `/login`, dan tab /admin tidak terbuka.
  3. Memilih dropdown "Admin", memasukkan email & password akun dokter lokal $\rightarrow$ pastikan muncul pesan error merah, URL tetap `/login`, dan tab /dashboard tidak terbuka.

---

## 8. KONFIRMASI INTEGRITAS DAN HASH

### Tabel Hash SHA-256 Sebelum vs Sesudah:

| File Path | SHA-256 Sebelum Perbaikan | SHA-256 Sesudah Perbaikan |
| :--- | :--- | :--- |
| `Frontend/src/utils/auth.ts` | `58e20b99215bec279d3c2a50d12b0912974b7974b4199bdbcb9e86df5ba589f3` | `156f84986d592ca758eaab08870d902fba26761e985bcc9fc1d23a5bb661f65b` |
| `Frontend/src/context/AuthContext.tsx` | `6f886e5f01f27270e6f7525a6d307493c71757d05859587d5db2933d4ee56572` | `80ece6d8828eaacf2a0a62a57d5f16761ebde840f7cfb26c2f71650e68722366` |
| `Frontend/src/pages/auth/Login.tsx` | `46d5aee154c0889681b01964cbea71812e0eb9f02678cb895a02bf1be9066921` | `59cc00b0e0872fad5fe8c8f8625e8ca2e2c5f67df4f8b81b9c5cd042545e5229` |
| `Frontend/src/utils/auth.test.ts` | `e1e95559f342ca16d5986a9a86c59d16ec0a8075cceee617d8ccfa8ea7b52fb9` | `43f00a27d3e100fde830e3b321681d5763b3b3401b2e8010cecf05c758dc952b` |
| `Frontend/src/pages/auth/Login.test.tsx` | `b663791534c23e82e89bf54d3e7866a9d472f596ac8e80b9f2242e3588b4987c` | `0e38135d6a45fcba1fa83a5d05415e10b75f1d2c3434fa67b3f07b39faf47d96` |
| `Frontend/src/context/AuthContext.test.tsx` | *(Berkas baru)* | `c8ac193c1a228f269ee3a25aa3cb7c76deae36f853d9d0afff93d93bef8e9d68` |

- **Pernyataan:** **TIDAK ADA COMMIT GIT** yang dibuat. Seluruh perubahan dibiarkan uncommitted di working tree sesuai instruksi.

