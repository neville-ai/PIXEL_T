# LAPORAN FORENSIK — APPROVE DOKTER & ADMIN DASHBOARD PIXEL-T

**Tanggal:** 2026-11-04
**Lingkungan yang diuji:** Supabase nyata (project dari `backend/.env`) + server Flask berjalan di `http://127.0.0.1:5000`
**Commit terkait:** `e1aeb33` (perbaikan utama) + `3e83d2a` (test FK error) + commit audit single-target (hardening UUID & verifikasi 1 baris)
**Status ringkas:** HTTP 500 = **TERBUKTI & DIPERBAIKI**; approve pada DB nyata = **LULUS PENGUJIAN**; **single-target (hanya akun terpilih yang berubah) = TERBUKTI pada DB nyata**; pengujian klik browser = **BELUM DIVERIFIKASI** (tidak ada browser automation di sesi ini).

---

## 1. Ringkasan masalah

| Masalah | Gejala | Temuan |
|---|---|---|
| A. Approve dokter | Tombol Setujui → `HTTP 500`, status tetap `pending`, `approved_by`/`approved_at` NULL | **Bukan** masalah `.error`/PostgREST seperti perbaikan sebelumnya. Penyebab: pemanggilan method SDK Python yang **tidak ada** (`maybeSingle`) sehingga `AttributeError` terjadi **sebelum** UPDATE dikirim. |
| B. Admin Dashboard | Dashboard "sering bermasalah" (kosong/statistik aneh/detail tidak termuat) | Tiga cacat kode frontend (race condition penghapusan error, satu kegagalan statistik mengosongkan seluruh daftar, response filter kadaluarsa menimpa data baru) + endpoint detail yang juga terkena bug `maybeSingle` + `auth.py` ikut terkena bug yang sama dan menelan exception secara diam-diam. |

Akun target `dr. Kharis` (`83973d49-...`, profil `d2b74384-...`) sekarang **approved** di Supabase nyata (lihat §4).

---

## 2. Akar penyebab HTTP 500 — TERBUKTI

**TERBUKTI** dari eksekusi nyata terhadap Supabase (bukan mock):

```
EXCEPTION TYPE: AttributeError
EXCEPTION STR: 'SyncSelectRequestBuilder' object has no attribute 'maybeSingle'
  File "backend/app/services/admin_service.py", line 140, in approve_doctor
    .maybeSingle()
    ^^^^^^^^^^^
```

Fakta pendukung:

1. SDK terpasang di runtime: `postgrest 2.31.0`, `supabase 2.31.0`.
2. Method yang tersedia pada `SyncSelectRequestBuilder` adalah **`maybe_single`** (snake_case). `maybeSingle` tidak ada — lihat `dir(SyncSelectRequestBuilder)`.
3. Karena exception terjadi pada **fetch** (`select ... maybe_single`), UPDATE tidak pernah dikirim. Ini menjelaskan mengapa di Supabase: `account_status` tetap `pending`, `approved_by` NULL, `approved_at` NULL.
4. Exception tidak tertangkap (tidak ada `try/except` di sekitar fetch) → Flask generic handler → **HTTP 500 INTERNAL_ERROR**.
5. `require_admin` berjalan normal (kalau gagal akan 401/403, bukan 500).
6. Endpoint lain yang memakai `maybeSingle` juga rusak: `GET /api/admin/doctors/:id` (detail) dan `_get_user_role_and_status()` di `core/auth.py`.

### Mengapa perbaikan sebelumnya (`79fd2e9`) belum menyelesaikan masalah

- Perbaikan sebelumnya mengganti `if update_result.error:` menjadi `try/except PostgrestAPIError`. Itu **bug laten yang nyata**, tetapi **tidak pernah tercapai** karena eksekusi sudah gagal di `maybeSingle()`.
- Unit test memakai `FakeQuery` yang **mendefinisikan `maybeSingle`** sendiri, sehingga test hijau padahal SDK asli tidak punya method tersebut. Ini contoh klasik "mock menutupi bug integrasi".
- Server yang berjalan saat laporan sebelumnya dibuat masih memuat kode lama (proses reloader baru tercipta setelah file diubah pada sesi ini).

### Bug kedua pada `auth.py` — TERBUKTI

`_get_user_role_and_status()` memakai `.maybeSingle()` di dalam `try/except Exception: pass`. Akibatnya:

- Setiap pemanggilan gagal → return `{'role': None, 'account_status': None}`.
- `require_approved_doctor` kemudian menolak **semua** dokter dengan `403 FORBIDDEN` — termasuk dokter yang sudah approved.

**DIPERBAIKI** menjadi `maybe_single()` + `logger.exception(...)` agar kegagalan tercatat, bukan hilang.

---

## 3. Akar penyebab masalah Admin Dashboard — TERBUKTI (audit kode) & DIPERBAIKI

| No | Temuan | Bukti kode | Dampak | Status |
|---|---|---|---|---|
| B1 | `loadStats` sukses memanggil `setError(null)`, menghapus error daftar dokter | `AdminDashboard.tsx` lama: `loadStats` → `setError(null)` | Jika request daftar gagal tetapi statistik sukses (race), error hilang dan UI menampilkan **"Belum ada pendaftaran"** padahal data gagal dimuat | **DIPERBAIKI** |
| B2 | Kegagalan statistik memakai `error` global | `setError('Gagal memuat statistik.')` | Satu request statistik gagal → **seluruh tabel dokter diganti ErrorState** meski data dokter berhasil dimuat | **DIPERBAIKI** (banner non-blokir) |
| B3 | Tidak ada guard response kadaluarsa saat filter berubah | `loadDoctors` tanpa sequencing | Klik filter cepat (Semua→Pending) → response lama bisa menimpa data filter baru (tabel/statistik tidak cocok) | **DIPERBAIKI** (`listSeqRef`) |
| B4 | Statistik di-fetch ulang setiap filter berubah | `useEffect(..., [filter, loadDoctors, loadStats])` | Request ganda yang tidak perlu, menambah peluang race | **DIPERBAIKI** (effect dipisah) |
| B5 | Error approve/reject menampilkan kode mentah `HTTP 500` | `setError(e.message)` | Pesan tidak informatif; 401/403/404/409/5xx tidak dibedakan | **DIPERBAIKI** (`describeApiError`) |
| B6 | `GET /api/admin/doctors/:id` selalu 500 | `get_doctor` → `.maybeSingle()` | Modal Detail jatuh ke fallback diam-diam (data tidak ter-refresh) | **DIPERBAIKI** |
| B7 | Kegagalan aksi mengosongkan tabel | error aksi memakai `error` global | Setelah Approve gagal, daftar dokter hilang | **DIPERBAIKI** (banner aksi non-blokir) |

Catatan: tidak ditemukan indikasi RLS, duplikasi baris, atau selisih sumber data statistik. Di DB nyata: 1 baris per `user_id` (unique), statistik dihitung dari tabel yang sama dengan daftar (`doctor_profiles`), dan filter daftar memakai kolom `account_status` yang sama.

**BELUM DIVERIFIKASI:** analisis tab Network browser secara langsung dan reproduksi race di browser (lihat §11).

---

## 4. Bukti traceback, log, dan verifikasi database nyata

### 4.1 Sebelum perbaikan (eksekusi nyata, service layer)

```
== 1) read target profile ==
{'id': 'd2b74384-...', 'account_status': 'pending', 'approved_by': None, 'approved_at': None}

== 5) call AdminService.approve_doctor (real) ==
EXCEPTION TYPE: AttributeError
EXCEPTION STR: 'SyncSelectRequestBuilder' object has no attribute 'maybeSingle'
```

### 4.2 Sesudah perbaikan (eksekusi nyata, service layer — jalur yang sama dengan controller)

```
BEFORE: {'account_status': 'pending', 'approved_by': None, 'approved_at': None}
admin_id resolved: True
approve_doctor returned account_status: approved
AFTER: {'account_status': 'approved',
        'approved_by': '3ec75b70-84d1-4143-9e79-2f5aabaae951',
        'approved_at': '2026-11-03T19:17:07.773831+00:00',
        'updated_at': '2026-11-03T19:17:07.773831+00:00'}

== role/status resolution (require_approved_doctor) ==
{'role': 'doctor', 'account_status': 'approved'}

== list_doctors (email enrichment) ==
{'full_name': 'dr. Kharis', 'email': 'kharisneville@gmail.com', 'account_status': 'approved'}

== statistics ==
{'total': 3, 'pending': 1, 'approved': 2, 'rejected': 0}
```

- `approved_by` = id admin yang terverifikasi (`auth.users`), **bukan** input frontend.
- `approved_at` dihasilkan backend (UTC).
- Hanya akun target yang diubah; tidak ada akun dokter lain yang tersentuh.

### 4.2b Bukti khusus: UPDATE hanya mengenai satu akun (single-target)

Audit ini memisahkan dua dugaan yang sering tercampur: (a) bug tampilan dashboard, dan (b) update database yang benar-benar massal. Bukti yang dikumpulkan:

| Uji | Metode | Hasil |
|---|---|---|
| Update langsung satu baris | `UPDATE ... SET account_status='approved' WHERE id=<satu UUID>` (idempotent pada baris yang sudah approved), snapshot seluruh tabel sebelum/sesudah | `UPDATE_ROWS=1`, `CHANGED_ROW_COUNT=0` → **tidak ada baris lain berubah** |
| Guard status | `UPDATE ... WHERE id=<satu UUID> AND account_status='pending'` pada baris approved | `GUARD_ROWS=0` → guard mencegah update status yang salah |
| Transisi nyata `pending → approved` | Insert **satu** profil pending sementara (memakai auth user yang belum punya profil), approve lewat `AdminService.approve_doctor`, snapshot semua baris, lalu hapus | `TEMP_AFTER={account_status: approved, approved_by: <admin>, approved_at: <terisi>}`, `UNRELATED_ROWS_CHANGED=0`, cleanup `TEMP_PROFILES_REMAINING=0` → **PASS_SINGLE_TARGET** |

Catatan: `auth.admin.create_user` pada project ini gagal `HTTP 500 "Database error creating new user"` bahkan **tanpa** metadata (bug terpisah di project Supabase, bukan bug approve). Karena itu isolasi multi-user dilakukan dengan insert satu profil sementara pada auth user yang sudah ada dan belum punya profil, bukan dengan membuat user baru. Tidak ada akun dokter nyata yang diubah selama uji transisi.

### 4.3 Verifikasi HTTP end-to-end ke server yang berjalan (Supabase nyata)

Server Flask di `127.0.0.1:5000` (mode development + reloader) otomatis restart saat file diperbaiki (proses baru tercipta 03:15:51). Kode baru terbukti aktif karena endpoint detail yang sebelumnya 500 kini 200.

| Request | Hasil | Keterangan |
|---|---|---|
| `GET /api/admin/doctors` | **200**, 3 baris | email `kharisneville@gmail.com` terisi |
| `GET /api/admin/doctors?status=pending` | **200**, 1 baris | filter bekerja |
| `GET /api/admin/doctors/stats` | **200**, `{approved:2, pending:1, rejected:0, total:3}` | konsisten dengan daftar |
| `GET /api/admin/doctors/{kharis}` | **200**, `approved` | sebelumnya 500 (`maybeSingle`) |
| `POST .../approve` (akun sudah approved) | **400 `INVALID_STATUS`** | guard status bekerja, bukan 500 |
| `POST .../reject` (akun sudah approved) | **400 `INVALID_STATUS`** | idem |
| `GET /api/admin/doctors` tanpa token | **401** | otorisasi tetap aktif |

Token admin diperoleh sementara via Supabase Admin API (`generate_link` + `verify`); tidak ada password/token yang dicetak atau disimpan.

---

## 5. Endpoint yang diperiksa

| Endpoint | Method | Fungsi Frontend | Route Backend | Service | Response | Status |
|---|---|---|---|---|---|---|
| `/api/admin/doctors` | GET | `fetchAdminDoctors` | `routes/admin.py::list_doctors` | `AdminService.list_doctors` | `{success, data[]}` (email di-enrich dari `auth.users`) | LULUS PENGUJIAN |
| `/api/admin/doctors?status=` | GET | filter tab | idem | idem | data terfilter | LULUS PENGUJIAN |
| `/api/admin/doctors/stats` | GET | `fetchAdminStats` | `get_doctor_statistics` | `get_statistics` | `{total,pending,approved,rejected}` | LULUS PENGUJIAN |
| `/api/admin/doctors/:id` | GET | `fetchAdminDoctorDetail` | `get_doctor` | `get_doctor` | profil lengkap + email | LULUS PENGUJIAN (sebelumnya 500) |
| `/api/admin/doctors/:id/approve` | POST | `approveDoctor` | `approve_doctor` | `AdminService.approve_doctor` | 200 + profil baru; 400 `INVALID_STATUS`; 404; 409 `UPDATE_CONFLICT`; 500 `UPDATE_FAILED` | DIPERBAIKI & LULUS PENGUJIAN |
| `/api/admin/doctors/:id/reject` | POST | `rejectDoctor` | `reject_doctor` | `reject_doctor` | idem + `rejection_reason` | DIPERBAIKI & LULUS PENGUJIAN |

ID yang dipakai: **`doctor_profiles.id`** (bukan `user_id`, bukan `auth.users.id`). `approve`/`reject` menerima `doctor_profiles.id` dari frontend; `approved_by` diisi backend dari `g.current_user['id']` (JWT terverifikasi).

---

## 6. File yang diperiksa

**Frontend:** `frontend/src/pages/admin/AdminDashboard.tsx`, `AdminDashboard.test.tsx`, `components/auth/AdminRoute.tsx`, `DoctorRoute.tsx`, `ProtectedRoute.tsx`, `context/AuthContext.tsx`, `services/auth.ts`, `routes/AppRoutes.tsx`, `components/ui/{ErrorState,Modal,Button}.tsx`.

**Backend:** `backend/app/routes/admin.py`, `controllers/admin_controller.py`, `services/admin_service.py`, `core/auth.py`, `core/errors.py`, `core/supabase.py`, `core/config.py`, `run.py`.

**Database:** `database/migrations/004_create_doctor_profiles.sql`, `006`, `007_add_role_and_account_status.sql` (`approved_by UUID REFERENCES auth.users(id)`), `008_create_doctor_profile_trigger.sql` (tidak dijalankan ulang), `database/verify_doctor_registration.sql`.

**SDK/dependency (runtime, bukan hanya requirements):** `postgrest 2.31.0`, `supabase 2.31.0` dari `.venv`.

**Proses server:** memastikan proses `backend.run` yang melayani port 5000 memuat kode terbaru (reloader restart terverifikasi lewat endpoint detail 200).

---

## 7. File yang diubah

| File | Perubahan | Alasan |
|---|---|---|
| `backend/app/services/admin_service.py` | 3× `.maybeSingle()` → `.maybe_single()` (get_doctor, approve, reject) | Method camelCase tidak ada di SDK Python → AttributeError → HTTP 500 |
| `backend/app/services/admin_service.py` | Update memakai `.eq('account_status','pending')` + verifikasi `result.data` (0 baris → 409 `UPDATE_CONFLICT`; status tidak sesuai → 500 `UPDATE_FAILED`) | Jangan kembalikan 200 jika status tidak benar-benar berubah |
| `backend/app/core/auth.py` | `.maybeSingle()` → `.maybe_single()`; `except: pass` → `logger.exception(...)` | `require_approved_doctor` selalu menolak dokter approved karena exception ditelan; kegagalan kini tercatat |
| `tests/backend/test_admin_service.py` | Fake SDK hanya menyediakan `maybe_single` (bukan `maybeSingle`); flag `fail_no_rows`; flag `update_error` + 3 test baru (0 baris → 409, DB error → 500 `UPDATE_FAILED`, FK error → 500 `UPDATE_FAILED`) | Agar regresi nama method SDK tertangkap test, bukan di produksi; FK violation harus ditangkap sebagai APIError, bukan crash HTTP 500 |
| `backend/app/services/admin_service.py` | Validasi `doctor_id` harus UUID (`_is_valid_uuid`) → `400 INVALID_ID` sebelum menyentuh DB | Mencegah parameter kosong/asing menyentuh query; target selalu `doctor_profiles.id` (PK), bukan `user_id` |
| `backend/app/services/admin_service.py` | Update difilter `.eq('id', doctor_id).eq('account_status','pending')` dan **wajib** `len(updated_rows) == 1` (0 atau >1 → `409 UPDATE_CONFLICT`) | Tidak boleh melaporkan sukses bila baris yang berubah bukan tepat satu; mencegah update massal tersamarkan sebagai sukses |
| `frontend/src/pages/admin/AdminDashboard.tsx` | `rejectTarget` — modal konfirmasi Tolak menampilkan nama + email akun yang benar | Admin harus melihat akun yang persis akan ditolak, bukan deskripsi generik |
| `frontend/src/pages/admin/AdminDashboard.test.tsx` | +3 test single-target: approve baris A hanya memanggil `/doctors/doc-A/approve`; approve baris B hanya `doc-B`; modal tolak menyebut Dr. A dan hanya memanggil `doc-A/reject` | Membuktikan identitas per-baris tidak tertukar |
| `tests/backend/test_admin_service.py` | Fake SDK mencatat filter `eq`; +3 test: filter update tepat `id`+`account_status=pending`, ID non-UUID → `400 INVALID_ID` (approve & reject), ID valid tak ditemukan → `404 NOT_FOUND` | Membuktikan target filter dan validasi ID di lapisan service |
| `frontend/src/pages/admin/AdminDashboard.tsx` | `statsError` & `actionError` terpisah; `listSeqRef` guard; effect statistik/daftar dipisah; `describeApiError` | Memperbaiki race/penghapusan error, mencegah satu kegagalan mengosongkan dashboard, pesan error informatif |
| `frontend/src/pages/admin/AdminDashboard.test.tsx` | Update assertion; +3 test (statistik gagal ≠ daftar kosong; filter tidak refetch statistik; reload setelah approve) | Bukti perilaku dashboard yang diperbaiki |
| `docs/ADMIN_DASHBOARD_AND_APPROVE_FORENSIC_REPORT.md` | Laporan ini | Dokumentasi forensik |

**Tidak diubah:** migration 007/008 (tidak dijalankan ulang), RLS/policy, `require_admin`, kebijakan transisi status, fitur dokter/AI.

---

## 8. Penjelasan perubahan

1. **`maybe_single()`** — satu-satunya nama method yang valid pada postgrest-py 2.31.0. Ini memperbaiki fetch di approve/reject/get_doctor dan lookup role/status dokter.
2. **Verifikasi hasil UPDATE** — `update().eq(id).eq(account_status,'pending').execute()` mengembalikan baris yang diperbarui (`return=representation`). Bila `data` kosong → `409 UPDATE_CONFLICT`; bila status hasil bukan target → `500 UPDATE_FAILED`. Dengan begitu tidak ada lagi "200 palsu".
3. **`auth.py`** — lookup role/status memakai method yang benar; exception dicatat ke log server tanpa membocorkan detail ke klien.
4. **Dashboard** — tiga kanal error terpisah: `error` (daftar, blokir area tabel), `statsError` (banner), `actionError` (banner aksi). `listSeqRef` membuang response lama. Statistik hanya dimuat saat mount/perubahan token dan setelah aksi.
5. **`describeApiError`** — memetakan 401/403/404/409/422/5xx/jaringan ke pesan yang aman dan informatif.

---

## 9. Hasil pengujian

| Pengujian | Jenis | Hasil | Keterangan |
|---|---|---|---|
| `pytest tests/backend/test_admin_service.py` | Unit + mock | **22/22 LULUS** | Termasuk regresi `maybe_single`, 0/>1 baris → 409, DB error → 500 `UPDATE_FAILED`, FK error → 500 `UPDATE_FAILED`, filter `id`+`account_status=pending`, ID non-UUID → 400, ID valid tak ditemukan → 404 |
| `pytest tests/backend/test_admin_routes.py` | Integration (Flask test client, service fake) | **7/7 LULUS** | 401/403/200/500, `approved_by` dari token |
| `pytest tests/backend/ tests/ai/test_gradcam.py` | Suite backend + AI | **112/112 LULUS** | `py_compile` exit 0 |
| `vitest run src/pages/admin/AdminDashboard.test.tsx` | Unit frontend (dashboard) | **17/17 LULUS** | Termasuk 3 test single-target (approve A / approve B / modal tolak A) |
| `vitest run` | Unit frontend (seluruh suite) | **282/282 LULUS** (18 file) | |
| `tsc --noEmit` | Type check | **LULUS** (exit 0) | |
| `vite build` | Build produksi | **LULUS** (✓ built in 17.7s) | |
| Verifikasi service terhadap Supabase nyata | **Integration nyata** | **LULUS** | pending → approved; `approved_by` & `approved_at` terisi; email & statistik benar |
| Verifikasi HTTP ke server berjalan + Supabase nyata | **Integration nyata** | **LULUS** | 200 list/filter/stats/detail; 400 untuk status non-pending; 401 tanpa token |
| **Uji single-target pada DB nyata** | **Integration nyata (isolated)** | **LULUS — PASS_SINGLE_TARGET** | Insert 1 profil pending sementara → approve → hanya baris itu berubah; `UNRELATED_ROWS_CHANGED=0`; cleanup 0 sisa |
| Pengujian klik di browser (UI) | Manual | **BELUM DIVERIFIKASI** | Lihat §11; checklist ada di §12 |
| Approve 200 untuk akun pending via HTTP | Integration nyata | **BELUM DIVERIFIKASI via HTTP** | Jalur service yang sama sudah terbukti (uji transisi + HTTP guard); akun pending nyata sengaja tidak diubah |

---

## 10. Dampak terhadap fitur lain

| Area | Status | Keterangan |
|---|---|---|
| Admin Dashboard (statistik, tab, daftar, detail) | **LULUS PENGUJIAN** | 282 test frontend + HTTP nyata 200; statistik/daftar konsisten |
| Approve / Reject | **DIPERBAIKI & LULUS PENGUJIAN** | Termasuk guard status dan verifikasi hasil update |
| Autentikasi & role admin | **TIDAK BERUBAH** | Tetap `app_metadata.role`; `require_admin` tidak disentuh; 401/403 terverifikasi |
| Dokter approved mengakses fitur klinis | **DIPERBAIKI** | `_get_user_role_and_status` kini mengembalikan `doctor/approved` (sebelumnya selalu `None/None` → 403) |
| Dokter pending/rejected | **TIDAK BERUBAH** | Decorator tetap menolak; tidak ada pelonggaran aturan |
| Doctor Profile / Upload Image / Segmentation / History | **TIDAK BERUBAH** (kode) | Suite backend/AI lulus; tidak ada perubahan pada modul tersebut |
| Routing (AdminRoute/DoctorRoute/ProtectedRoute) | **TIDAK BERUBAH** | Tidak ada perubahan |
| RLS / migration | **TIDAK BERUBAH** | Tidak ada migration baru; 007/008 tidak dijalankan ulang |

---

## 11. Hal yang belum terverifikasi

1. **Pengujian manual lewat browser** (klik Setujui di UI, refresh halaman, tab filter, modal detail, logout/login) — belum dijalankan oleh agent; langkah ada di §12.
2. **Tampilan Network tab** — tidak dianalisis langsung dari browser; temuan dashboard berasal dari audit kode + test perilaku.
3. **Approve 200 via HTTP untuk akun pending** — tidak dilakukan terhadap akun dokter nyata agar tidak mengubah data produksi. Transition pending→approved **sudah dibuktikan** pada DB nyata dengan profil pending sementara (isolasi) dan lewat service yang sama persis dipanggil controller; seluruh HTTP GET/guard sudah 200/400.
4. **Kebijakan transisi status** — saat ini hanya `pending → approved/rejected`; `rejected → approved`, `approved → rejected`, dsb. ditolak `400 INVALID_STATUS`. Tidak diubah karena belum ada kebutuhan bisnis yang jelas. **MEMERLUKAN KEPUTUSAN** bila penulis ingin mengizinkan re-approval akun yang ditolak.
4. **Race condition filter di browser nyata** — sudah diberi guard dan dicakup test, tetapi belum direproduksi manual di browser.
5. **Kinerja `list_doctors`** — email diambil per baris via `auth.admin.get_user_by_id` (N+1). Fungsional benar, tetapi bisa lambat bila jumlah dokter besar. **MEMERLUKAN KEPUTUSAN** apakah perlu optimasi (di luar scope perbaikan bug).
6. **Kebijakan transisi status** — saat ini hanya `pending → approved/rejected`; `rejected → approved`, `approved → rejected`, dsb. ditolak `400 INVALID_STATUS`. Tidak diubah karena belum ada kebutuhan bisnis yang jelas. **MEMERLUKAN KEPUTUSAN** bila penulis ingin mengizinkan re-approval akun yang ditolak.
7. **Akun dr. Kharis sudah approved** oleh verifikasi ini (`approved_at` 2026-11-03T19:17:07Z); pastikan UI setelah login menampilkan status tersebut.

---

## 12. Langkah pengujian manual

**Prasyarat:** restart backend (jika tidak memakai reloader) agar memuat kode terbaru, lalu buka Admin Dashboard.

1. Login sebagai admin → buka **Admin Dashboard**.
2. Pastikan daftar dokter, statistik (total/pending/approved/rejected), dan tab filter konsisten. Klik tiap tab; tidak ada error dan tidak ada request statistik berulang (cek Network).
3. **dr. Kharis** seharusnya sudah **Approved** (hasil verifikasi ini). Untuk menguji approve baru, gunakan akun dokter `pending` lain:
   - Klik **Setujui** → respons 200 → status berubah menjadi Approved tanpa refresh manual.
   - Refresh halaman → status tetap Approved (bukan kembali pending).
4. Buka **Detail** pada salah satu dokter → modal terisi (endpoint detail 200).
5. Uji **Tolak** pada akun pending: isi alasan → konfirmasi → status Rejected dan `rejection_reason` tersimpan.
6. Uji kegagalan: matikan backend sementara → dashboard menampilkan pesan ramah (bukan `HTTP 500` mentah) dan tabel tetap ada; nyalakan kembali → tombol **Coba lagi** berfungsi.
7. Verifikasi DB (Supabase SQL Editor) memakai `database/verify_doctor_registration.sql`:
   - `account_status`, `approved_by` (id admin), `approved_at` (tidak NULL), `user_id` tidak berubah.
8. Login sebagai dokter approved → fitur klinis dapat diakses; Admin Dashboard tidak dapat diakses.
9. Login sebagai dokter pending → fitur klinis ditolak (403 `ACCOUNT_PENDING`).
