# LAPORAN AKHIR — PERBAIKAN HTTP 500 FITUR APPROVE DOKTER (PIXEL-T)

> **STATUS SUPERSI/EKSPIRASI:** Laporan ini disusun setelah perbaikan awal
> (`.error` → `PostgrestAPIError`). Menjelang sesi forensik lanjutan, **ditemukan
> penyebab sebenarnya** yang menyebabkan HTTP 500 tetap terjadi: SDK Python
> (`postgrest`/`supabase` 2.31.0) memakai method **`maybe_single()`**, sedangkan
> kode memanggil **`maybeSingle()`** (camelCase) yang tidak ada.
>
> Hasil forensik lengkap ada di:
> **[LAPORAN FORENSIK — APPROVE DOKTER & ADMIN DASHBOARD PIXEL-T](ADMIN_DASHBOARD_AND_APPROVE_FORENSIC_REPORT.md)**

**Commit:** `79fd2e9` — `fix(admin): perbaiki HTTP 500 saat approve/reject dokter` (4 file, 1.219 baris baru)

## A. Ringkasan masalah

Ketika admin menekan tombol **Setujui (Approve)** pada akun dokter dengan status `pending` (mis. dr. Kharis, `kharisneville@gmail.com`), backend mengembalikan **HTTP 500 Internal Server Error**. Alur gagal pada tahap **backend**, bukan database dan bukan frontend:

1. Admin Dashboard → `POST /api/admin/doctors/{doctor_id}/approve` → controller → `AdminService.approve_doctor()`.
2. Service mengeksekusi `UPDATE doctor_profiles ... WHERE id = ...` melalui postgrest-py.
3. Service lalu mengakses atribut **`.error`** pada objek respons (`update_result.error`).
4. Objek respons sukses dari postgrest-py 2.31.0 adalah `APIResponse` (Pydantic `BaseModel` yang hanya punya field `data` dan `count`) — **tidak ada atribut `.error`** → `AttributeError`.
5. `AttributeError` tidak tertangkap → Flask error handler → **HTTP 500**.

Masalah serupa ada pada `reject_doctor`. Perbaikan sebelumnya sudah menghapus kolom nonexistent `email` dari `select()` dan memperbaiki `_get_user_email()`; bug `.error` adalah akar penyebab HTTP 500 saat ini.

## B. Root Cause Analysis

| No. | Komponen | Penyebab | Bukti | Dampak |
|-----|----------|----------|-------|--------|
| 1 | `backend/app/services/admin_service.py` (`approve_doctor` dan `reject_doctor`) | Pengecekan `if update_result.error:` pada objek `APIResponse` milik postgrest-py 2.31.0. `APIResponse` hanyalah Pydantic model dengan field `data` + `count` — **tidak memiliki atribut `.error`**. Aksesnya memicu `AttributeError` (unhandled → Flask → 500). | `inspect.getsource(postgrest.types.APIResponse)` → field hanya `data`, `count`. `execute()` sukses mengembalikan `APIResponse`; gagal melempar `postgrest.exceptions.APIError` (terdapat `.message`, `.code`). | Setiap aksi Approve/Reject berhasil di database (update telah terkirim), tetapi responsnya 500 dan frontend tidak merefresh tabel/statistik. |
| 2 | `frontend/src/pages/admin/AdminDashboard.tsx` | Gejala: `throw new Error('HTTP ' + res.status)` menampilkan "HTTP 500" ke user. | Baris 76 fungsi `approveDoctor` | User menampilkan `ERROR — HTTP 500`; bukan akar penyebab. |

Beda antara akar masalah dan gejala: akar = penanganan response postgrest yang salah di backend service; gejala = pesan HTTP 500 yang tampil di Admin Dashboard.

## C. File yang diperiksa

**Frontend:** `frontend/src/pages/admin/AdminDashboard.tsx`, `AdminDashboard.test.tsx`, `frontend/src/components/auth/AdminRoute.tsx`, `ProtectedRoute.tsx`, `PublicOnlyRoute.tsx`, `DoctorRoute.tsx`, `context/AuthContext.tsx`, `components/ui/{Button,Input,Modal,ErrorState}.tsx`, `routes/AppRoutes.tsx`.

**Backend:** `backend/app/routes/admin.py`, `controllers/admin_controller.py`, `services/admin_service.py`, `core/auth.py` (`require_admin`, role dari `app_metadata.role`), `core/errors.py` (envelope respons terstruktur), `core/supabase.py`, `app/__init__.py`.

**Database:** `database/migrations/004_create_doctor_profiles.sql`, `006_add_avatar_url_to_doctor_profiles.sql`, `007_add_role_and_account_status.sql` (`account_status`, `approved_by UUID REFERENCES auth.users(id)`, `approved_at`), `008_create_doctor_profile_trigger.sql` (sudah dijalankan, tidak dijalankan ulang), `database/verify_doctor_registration.sql` (read-only).

**Library:** `postgrest` 2.31.0 (sumber kode `APIResponse` dan `exceptions.APIError` diverifikasi langsung dari `.venv`).

## D. File yang diubah (commit 79fd2e9)

| File | Perubahan | Alasan |
|------|-----------|--------|
| `backend/app/services/admin_service.py` | Hapus `if update_result.error:`; `approve_doctor` dan `reject_doctor` sekarang bungkus `.update(...).execute()` dalam `try/except PostgrestAPIError` → `APIError(code="UPDATE_FAILED", status_code=500)`. `approved_by` diisi dari parameter `approved_by_user_id` (yang diisi controller dari `g.current_user['id']` / token terverifikasi), tidak dari input frontend. `approved_at` diisi `datetime.now(timezone.utc)`. | Mengganti deteksi kegagalan yang salah (`.error` yang tidak ada) dengan penanganan exception yang benar; response sukses kini 200 dengan data terbaru melalui `get_doctor()`. |
| `tests/backend/test_admin_service.py` | `FakeQuery.execute` meniru perilaku asli postgrest-py (sukses → objek tanpa `.error`; gagal → `raise PostgrestAPIError`); ditambahkan 4 tes regresi: sukses tanpa atribut error, metadata `approved_by`/`approved_at` tersimpan, DB error → `UPDATE_FAILED` 500 (approve & reject). | Memastikan regresi HTTP 500 tidak kembali; `approved_by` tidak boleh dipercaya dari frontend (terjaga dari token). |
| `tests/backend/test_admin_routes.py` | File baru: 7 tes endpoint (autentikasi 401, token invalid 401, doctor dilarang 403 untuk approve & reject, admin sukses, `approved_by` berasal dari token admin yang terautentikasi, DB gagal → 500 `UPDATE_FAILED`, reject admin masih bekerja). | Memverifikasi otorisasi dan kontrak endpoint. |
| `frontend/src/pages/admin/AdminDashboard.test.tsx` | +3 tes: tombol Setujui/Tolak tidak muncul pada akun non-pending, pesan error ditampilkan saat Approve gagal, flow Reject mengirim `rejection_reason` via POST. | Cakupan fase VII.B (tombol kondisional, error handling, reject flow). |

**Tidak diubah:** migration 007 dan 008 tidak dijalankan ulang; tidak ada migration baru; `require_admin`, `require_approved_doctor`, RLS, dan fitur non-Admin tidak disentuh.

## E. Hasil pengujian

| Pengujian | Hasil | Keterangan |
|-----------|-------|------------|
| Backend unit (`tests/backend/test_admin_service.py`) | 16/16 lulus | Termasuk regresi `.error` → `AttributeError` dan DB error `UPDATE_FAILED`. |
| Backend endpoint (`tests/backend/test_admin_routes.py`) | 7/7 lulus | Otorisasi admin/doctor/anonim, contract respons. |
| Backend + AI keseluruhan (`tests/backend/`, `tests/ai/test_gradcam.py`) | 109/109 lulus | Tidak ada regresi. |
| `py_compile` admin_service + routes + controller | Lulus (exit 0) | Kompilasi bersih. |
| Frontend unit (`vitest run`) | 279/279 lulus, 18 file | Sebelumnya 276; +3 tes baru. |
| `tsc --noEmit` | Lulus (exit 0) | TypeScript tanpa error. |
| `vite build` | Lulus (✓ built in 11.7s) | Production build sukses, final state. |
| Integrasi database nyata (Supabase) | **Tidak dijalankan** | Tidak ada akses credentials Supabase dari lingkungan ini; lihat bagian H. |
| Skenario manual 1–4 (dr. Kharis) | **Belum dijalankan** | Diperlukan login Admin dan aplikasi berjalan; langkah ada di bagian G. |

## F. Dampak terhadap fitur lain (regresi)

- **Admin Dashboard:** statistik (total/pending/approved/rejected), tab Semua/Pending/Disetujui/Ditolak, daftar, detail, dan refresh setelah aksi tidak berubah — diuji oleh 279 tes frontend + tes service daftar/statistik.
- **Autentikasi:** Sign Up/In/Out, restore session, role admin dari `app_metadata.role` (`auth.py` tidak diubah) — tidak ada dampak.
- **Routing:** `AdminRoute`, `ProtectedRoute`, `DoctorRoute`, `PublicOnlyRoute` tidak diubah.
- **Fitur dokter:** Doctor Dashboard, profile, upload image, segmentation, history — tidak ada perubahan kode yang terkait; tes AI dan backend history tetap lulus.
- **Reject:** masih bekerja dengan pola yang sama (`try/except PostgrestAPIError`); diuji oleh tes service dan route.
- **Pembatasan pending/rejected:** service menolak approve/reject pada status non-pending dengan `INVALID_STATUS` (400); middleware `require_approved_doctor` mematuhi status klinis.

## G. Langkah pengujian manual (untuk penulis aplikasi)

**Skenario 1 — Approve akun pending (dr. Kharis)**
1. Login sebagai Admin, buka Admin Dashboard.
2. Temukan `dr. Kharis` (status Pending). Tekan **Setujui**.
3. Pastikan tidak ada HTTP 500; respons sukses dan tabel/statistik merefresh otomatis; status menjadi Disetujui.
4. Refresh halaman; status tetap Disetujui.

**Skenario 2 — Verifikasi database** (Supabase SQL Editor, gunakan `database/verify_doctor_registration.sql` atau query setara)
- `account_status = 'approved'`
- `approved_by` terisi dengan `id` admin yang login (cocok `auth.users.id`; FK ke `auth.users`)
- `approved_at` tidak NULL
- `user_id` dan data profil lain tidak berubah secara tidak sengaja

**Skenario 3 — Hak akses dokter**
1. Logout Admin, login sebagai `dr. Kharis`.
2. Pastikan fitur klinis dokter dapat diakses (Dashboard, Upload Image, Segmentation, History).
3. Pastikan Admin Dashboard **tidak** dapat diakses sebagai Doctor.

**Skenario 4 — Pembatasan pending**
1. Gunakan akun dokter `pending` lain.
2. Pastikan tidak dapat mengakses fitur klinis (navigasi frontend maupun request langsung ke backend).
3. Pastikan tombol Setujui/Tolak **tidak muncul** untuk akun yang bukan pending pada Admin Dashboard.

**Catatan:** endpoint Reject memanfaatkan pola yang sama dan diuji otomatis; verifikasi manual opsional.

## H. Hal yang belum terverifikasi

1. Transisi status pada database nyata (Supabase) untuk `dr. Kharis` — butuh kredensial Supabase dan SQL Editor; belum dapat dilakukan dari lingkungan ini.
2. Pengamatan langsung HTTP 500 hilang pada aplikasi berjalan (butuh backend aktif + login Admin).
3. Skenario manual 1–4 di bagian G.
4. Kesinambungan FK `approved_by` ke `auth.users(id)` saat insert aktual — migration 007 mendefinisikan `approved_by UUID REFERENCES auth.users(id)`, tapi belum diuji terhadap data nyata.

Migration 007 dan 008 **tidak dijalankan ulang**; trigger `on_auth_user_created_doctor_profile` (Migration 008) tetap aktif dan tidak disentuh.
