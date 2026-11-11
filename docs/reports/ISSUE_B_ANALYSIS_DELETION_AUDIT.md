# AUDIT ISU B — PENGHAPUSAN ANALISIS SAAT PIPELINE SEDANG BERJALAN

**Tanggal:** 11 November 2026  
**Status:** Audit **hanya (read-only)**. Tidak ada kode yang diubah pada tahap ini.  
**Scope:** Mekanisme penghapusan analisis (`DELETE /api/history/<id>`) terhadap job yang masih menunggu dalam antrean maupun sedang diproses worker.

---

## 1. Diagram Lifecycle Aktual

```text
HTTP LAYER                          SERVICE LAYER                        QUEUE / WORKER                    STORAGE / DB
------------                          -------------                        ----------------                    -------------
POST /api/analysis                           │
 controller.create_analysis                  │
   → AnalysisService.create_analysis         │
      ├─ validate_and_decode_image           │
      ├─ validate_domain (+ Gemini gate)     │
      ├─ storage.upload_file (original)      │───────────────┐
      ├─ repository.create (status=processing)│               │
      └─ job_queue.try_enqueue({id,user,bytes}) │          │
                                                │             │
                                                ▼             │
                                          AnalysisJobQueue   │
                                          (in-memory,        │
                                           MAX_WAITING=3,    │
                                           capacity=4 total) │
                                                │             │
                           active job + up to 3 waiting jobs │
                                                │             │
                            worker pops job     │             │
                            _active_analysis_id │             │
                                                ▼             │
                                  _run_analysis_job(job)      │
                                                │             │
                                                ▼             │
                            AnalysisPipelineService.execute   │
                                                │             │
                  pipeline_runner (run_pipeline)              │
                  → preprocess → TTA inference → postprocess  │
                  → Grad-CAM                                  │
                                                │             │
                  upload 4 artifacts (mask, overlay,          │
                   heatmap, gradcam overlay) → storage        │──────────────┐
                                                │             │                │
                                                ▼             │                │
                                 repository.update            │                │
                                 (status=completed,           │                │
                                  progress=100, assets…)      │                │
                                                │             │                │
                                                ▼             │                │
                                          202 Accepted      GET /api/analysis/<id>
                                                            repository.get_by_id
                                                            (404 if missing)

DELETE /api/history/<id>                          │
 controller.delete_analysis                       │
   → AnalysisService.delete_analysis              │
      ├─ repository.get_by_id (404 if missing)    │
      ├─ repository.delete (record removed)       │◄────────────┐
      ├─ storage.delete_analysis_files (best-effort)│          │
      └─ return True → 200                        │          │
                                                  │          │
                                                  ▼          │
                                          (no coordination  │
                                           with queue/worker)│
                                                  │          │
                                                  ▼          │
                                          Worker still runs│
                                          job → DB update   │
                                          returns None →    │
                                          cleanup + failed  │
```

---

## 2. Alur Komponen (Referensial)

| Komponen | File | Peran dalam lifecycle |
|---|---|---|
| Controller | `Backend/src/controllers/analysis_controller.py` | Terima HTTP, panggil service |
| `create_analysis` | `analysis_service.py` | Validasi, upload original, buat record `processing`, `try_enqueue` job berisi `file_bytes` |
| Queue | `analysis_queue_service.py` | In-memory FIFO per-process, `MAX_WAITING=3`, satu worker thread daemon, `_active_analysis_id` melacak in-flight |
| `_run_analysis_job` | `analysis_service.py` | Panggil `_execute_pipeline`, tangkap & log semua exception (jangan bagi worker) |
| `_execute_pipeline` | `analysis_service.py` | Delegate ke `AnalysisPipelineService` |
| `AnalysisPipelineService.execute` | `analysis_pipeline_service.py` | Progress reporter, jalankan `pipeline_runner`, upload 4 artefak, `update(completed)`; pada error: hapus artefak, `update(failed)`, raise `APIError` |
| Pipeline AI | `Backend/ai/inference/pipeline.py` | Domain gate internal, preprocess, TTA, postprocess, Grad-CAM (tidak diubah tahap ini) |
| Progress | `analysis_progress_service.py` | Tulis `current_step`/`progress_percent` ke DB, throttled, gagal-swalah |
| `delete_analysis` | `analysis_service.py` | `get_by_id` → `repository.delete` → `storage.delete_analysis_files` (best-effort) → 200 walaupun storage gagal (DECISION A) |
| Repository | `analysis_repository.py` | Supabase CRUD dengan ownership `eq("user_id")`; `update`/`delete` mencocokkan 0 baris → `None`/`False` |
| Storage | `storage_service.py` | `upload_file`, `delete_file`, `delete_analysis_files` dengan `validate_path_ownership` |
| GET | `get_analysis` | Baca record; tanda `stale` hanya bila `status=processing`, tidak ada di antrean proses ini, dan > `STALE_THRESHOLD` (15 menit) — non-mutating |

**Tidak ada mekanisme pembatalan (cancellation), tidak ada tombstone, dan tidak ada koordinasi lock antara `delete_analysis` dan worker/pipeline.** Antrian menyimpan `file_bytes` dalam memori proses.

---

## 3. Temuan per Skenario A–H

### A. Job masih menunggu dalam antrean, lalu pengguna menghapus analisis
- `delete_analysis` menghapus record DB dan membersihkan storage (best-effort), lalu mengembalikan `200`.
- Job **tetap ada** di dalam `AnalysisJobQueue._jobs` karena `delete_analysis` **tidak menyentuh antrean sama sekali**.
- Saat worker mengambil job tersebut, `_execute_pipeline` berjalan hingga `repository.update(status=completed)`. Karena record sudah dihapus, `update(..., eq("user_id"))` mencocokkan 0 baris → mengembalikan `None` → `raise RuntimeError("analysis database update returned no record")` → jalur gagal pipeline: hapus artefak yang sudah diunggah, coba `update(status=failed)` (juga 0 baris, ditangkap & di-log), raise `APIError` yang ditelan `_run_analysis_job`.
- Hasil: record tetap hilang, artefak pipeline diunggah lalu dibersihkan, antrean mengonsumsi satu slot untuk pekerjaan sia-sia, pengguna mendapat `404` saat GET.

### B. Worker sudah mengambil job, pipeline belum dimulai, lalu pengguna menghapus
- Sama dengan A: pekerjaan sudah keluar dari antrean (`_active_analysis_id` diset), tidak dapat ditarik kembali oleh `delete_analysis`.
- Pipeline berjalan sepenuhnya (inferensi TTA + Grad-CAM dijalankan) sebelum gagal pada langkah persisten terakhir karena record sudah hilang. Sisa artifacts diunggah kemudian dibersihkan pada jalur `except`.

### C. Pipeline sedang menjalankan inferensi, lalu pengguna menghapus
- Inferensi TTA/Grad-CAM berjalan hingga selesai (tidak dapat diinterupsi di tengah eksekusi karena tidak ada flag pembatalan yang dicek di antara forward pass).
- Hasil diunggah ke storage, lalu `update(completed)` gagal (record sudah dihapus) → jalur gagal → artefak dihapus → worker melanjutkan ke job berikutnya.
- Risiko: komputasi AI + storage I/O sia-sia; jika proses dihentikan paksa di tengah, status tidak diperbarui karena record sudah tidak ada.

### D. Pipeline sedang mengunggah artefak, lalu pengguna menghapus
- `AnalysisPipelineService.execute` unggah 4 artefak secara sekuensial. `delete_analysis` memanggil `storage.delete_analysis_files` pada 5 path dari record (termasuk path artefak yang mungkin belum ada atau sedang ditulis).
- Tidak ada koordinasi antara `upload_file` (pipeline) dan `remove` (penghapusan) pada objek storage yang sama. Urutan non-deterministik:
  - `remove` sebelum `upload`: artefak baru muncul tanpa record (orphan).
  - `upload` sebelum `remove`: artefak dihapus — aman.
- Karena record sudah dihapus, orphan tidak dapat ditelusuli melalui API (path bersifat ownership-scoped), tetapi tetap menempati kuota Supabase Storage hingga dibersihkan secara terpisah.

### E. Pipeline selesai ketika proses penghapusan sedang berlangsung
Tiga urutan interleaving:
1. **Delete lebih dulu** (`get_by_id` + `repository.delete` selesai sebelum `update(completed)` pipeline): pipeline update → 0 baris → RuntimeError → cleanup → `404` untuk pengguna. Aman (tidak ada resurreksi).
2. **Pipeline lebih dulu** (`update(completed)` terkomit sebelum `repository.delete`): status `completed` tersimpan, lalu `delete_analysis` menghapus record lengkap + storage. Bersih.
3. **Berinterleave**: `delete_analysis` baca record (`get_by_id`), pipeline menulis `completed`, kemudian `repository.delete` dieksekusi → menghapus record yang sudah completed. Tidak ada resurreksi karena pipeline tidak pernah membuat record baru.

### F. Penghapusan database berhasil, tetapi penghapusan storage gagal
- `delete_analysis` mengembalikan `True` → HTTP `200` (DECISION A, terkunci oleh pemilik proyek).
- Record hilang dari DB, objek storage **tinggal orphan**. Tidak bisa diakses melalui API (path ownership-scoped dan record hilang), tetapi masih menempati storage sampai dibersihkan secara terpisah (tidak ada garbage collector dalam kode saat ini).
- Sudah terkunci oleh tes `test_delete_case_c_storage_false_still_returns_success_record_deleted` dan `test_delete_case_d_storage_exception_still_returns_success_record_deleted`.

### G. Penghapusan database gagal setelah sebagian artefak storage dihapus
- Tidak mungkin terjadi dalam implementasi saat ini: `repository.delete` dijalankan **sebelum** `storage.delete_analysis_files`. Jika DB gagal → `500 DATABASE_ERROR`, record utuh, storage **belum disentuh** (`storage.removed == []`, tersurat dalam tes `test_delete_case_a_database_failure_keeps_record_and_storage`). Tidak ada parcial-storage-then-DB-failure.

### H. Pengguna mencoba membaca analisis yang sudah dihapus sementara worker masih berjalan
- Jika hapus lebih dulu: `get_analysis` → `get_by_id` tidak menemukan record → `404 ANALYSIS_NOT_FOUND`. Worker yang masih berjalan akan gagal pada `update` terakhir dan tidak dapat menulis kembali record.
- Jika hapus belum selesai/tidak terjadi: `get_analysis` mengembalikan record `processing` dengan `current_step`/`progress_percent` jika ada. Tanda `stale` hanya ditetapkan bila job **tidak ada di antrean proses ini** dan lebih lama dari 15 menit — itu hanya tanda informasi, tidak mengubah status dan tidak mematikan worker.

---

## 4. Race Condition yang Ditemukan

| # | Race | Dampak |
|---|------|--------|
| R1 | `delete_analysis` vs worker: record dihapus sebelum `update(completed/failed)` pipeline | Pipeline berjalan sia-sia, artefak diunggah lalu dibersihkan, `update` mengembalikan `None`, worker melanjutkan. Tidak ada resurreksi. |
| R2 | `delete_analysis` (storage.remove) vs pipeline (storage.upload) pada path artefak yang sama | Urutan storage tidak terjamin → orphaned object possible (D). |
| R3 | `delete_analysis` vs `try_enqueue` | Job yang akan dihapus tetap masuk antrean dan mengonsumsi kapasitas (MAX_WAITING+1 = 4 total). |
| R4 | `get_analysis` (`job_queue.contains`) vs worker start/completion | Hanya mempengaruhi flag `stale` (non-mutating), aman tetapi informasi bisa tidak akurat sejenak. |
| R5 | Worker thread daemon + restart proses | Antrian hilang saat restart; record yang statusnya `processing` ditinggalkan tanpa penyelesaian sampai pemeriksaan `stale` (yang hanya menandai, tidak menyelesaikan). |
| R6 | `delete_analysis` non-atomik DB+storage (DECISION A) | Storage gagal → record hilang tapi objek storage orphan (F). Ini adalah keputusan sengaja, bukan race baru, tetapi merupakan risiko konsistensi. |

**Operasi yang membutuhkan atomicity/kompensasi:** pasangan (DB delete ↔ storage cleanup) dan (pipeline DB write ↔ delete). Saat ini tidak ada transaksi lintas komponen; kompensasi ada hanya satu arah (pipeline membersihkan artefaknya sendiri saat gagal).

---

## 5. Risiko Database dan Storage

**Database:**
- `repository.update` dan `delete` menggunakan `eq("id").eq("user_id")`; jika record sudah tidak ada, keduanya kembali `None`/`False` tanpa exception — aman dari segi crash, tetapi pipeline tidak dapat membedakan "record sudah dihapus pengguna" dari "error DB lain".
- `ALLOWED_STATUSES = {'processing', 'completed', 'failed'}`; tidak ada status `deleted` / `cancelling`. Menambah status memerlukan perubahan skema DB (melanggar batasan tanpa persetujuan desain).

**Storage:**
- Path artefak bersifat ownership-scoped (`analysis/{user}/{analysis}/{category}/...`) dan divalidasi `validate_path_ownership`. Orphan dari penghapusan tidak dapat diakses melalui API oleh pengguna lain, tetapi masih terlihat dalam bucket Supabase.
- Tidak ada daftar pemindaian (list/prefix sweep) untuk membersihkan orphan secara berkala.

**UX:**
- Pengguna selalu mendapat `200` setelah DELETE, walaupun worker masih menjalankan pipeline dan artefak akan diunggah lalu dibersihkan. Tidak ada indikasi bahwa penghapusan sedang "menunggu" pipeline selesai.

---

## 6. Alternatif Desain dan Perbandingan

| Alternatif | Keuntungan | Risiko | Kompleksitas Implementasi | Dampak Queue | Dampak DB & Storage | Dampak UX |
|---|---|---|---|---|---|---|
| **1. Hapus job menunggu; tolak hapus saat job aktif** | Tidak ada pekerjaan sia-sia untuk job menunggu; tidak ada race pada job yang belum dimulai | Pengguna tidak dapat menghapus analisis yang sedang diproses (UX buruk untuk inferensi lama); perlu mekanisme antrian untuk menarik job dari tengah deque | Tinggi (modifikasi `AnalysisJobQueue` untuk hapus job menunggu + status "sedang diproses" yang dicek `delete_analysis`) | Queue perlu operasi hapus dari antrean yang aman secara thread | DB/storage tidak berubah | Buruk: tombol hapus kadang ditolak tanpa estimasi waktu |
| **2. Soft delete + cancellation flag** | Worker dapat berhenti lebih awal; record tetap terlacak | Perlu kolom/status baru di DB (melanggar batasan skema tanpa persetujuan); inferensi TTA berjalan panjang dan tidak dapat dihentikan di tengah forward pass tanpa membunuh thread | Tinggi (ubah skema DB, flag, pemeriksaan di berbagai titik pipeline) | Queue tetap menjalankan job aktif hingga akhir | Perlu update status tambahan; risiko status konsisten | Baik jika diberi respons "sedang dibatalkan" |
| **3. Cooperative cancellation pada batas tahapan pipeline** (pemeriksaan flag di antara phase) | Terkontain dalam lapisan service; tidak mengubah `Backend/ai/`; worker berhenti segera setelah fase selesai | Tidak dapat menghentikan inferensi yang sedang berjalan (TTA/Grad-CAM tetap sampai selesai fase); flag harus diperiksa sebelum setiap write DB untuk mencegah resurreksi | Sedang (tambahkan tombstone set di `AnalysisService`, dicek sebelum `update(completed/failed)`) | Job aktif tetap habis, tapi write hasil dapat dicegah | DB tidak ditimpa setelah tombstone; storage masih orphan risk (DECISION A) | Cukup baik: hapus segera diterima, hasil tidak muncul |
| **4. Tombstone / deletion state** | Mencegah pipeline menulis kembali ke analisis yang dihapus dengan jelas | Memerlukan status baru atau tabel sampingan (ubah skema DB — melanggar batasan) | Tinggi (skema DB + semua pemanggil status) | Queue perlu mengetahui tombstone | DB/storage perlu koordinasi tambahan | Baik |
| **5. Kombinasi** (tombstone in-memory + purge antrean + fence write pipeline) | Cakupan terbaik dalam batasan kode saat ini; tidak mengubah skema DB atau `Backend/ai/` | Masih memerlukan pengambilan keputusan tentang berapa lama tombstone diingat (memori per-process); proses restart hilang tombstone | Sedang–Tinggi | Waiting job dengan tombstone dapat diabaikan saat di-dequeue; job aktif tetap berjalan tapi write dicegah | Write fence mencegah resurreksi; orphan storage tetap risiko residual | Terbaik yang tersedia sekarang |

**Peringatan:** Alternatif 2 dan 4 mengubah skema DB / status lifecycle, yang melanggar batasan audit ini ("Struktur database tanpa persetujuan desain"). Alternatif 3 dan 5 paling sesuai dengan batasan yang ada.

---

## 7. Rekomendasi Desain

Berdasarkan batasan (tidak mengubah `Backend/ai/`, skema DB, kapasitas antrean, progress reporter, format API) dan prinsip "jangan mengorbankan keamanan lifecycle demi kecepatan tombol hapus", rekomendasi:

1. **Tandai penghapusan (tombstone) di memori `AnalysisService`** sebelum `repository.delete`, dengan kunci internal, sehingga pipeline/worker dapat mengetahui bahwa analisis telah ditandai untuk dihapus.
2. **Purge antrean menunggu** saat `delete_analysis`: hapus job yang masih menunggu dengan `analysis_id` yang sama dari `AnalysisJobQueue._jobs` (dengan kunci antrean). Job yang sudah aktif (`_active_analysis_id`) tidak dapat ditarik keluar — ini dapat diterima, sebagai longgaran terhadap alternatif 1.
3. **Write fence di `AnalysisPipelineService.execute`:** sebelum menulis `update(completed)` maupun `update(failed)`, verifikasi apakah analisis masih layak (tombstone belum diatur / record masih ada). Jika ditandai dihapus: bersihkan artefak yang diunggah lalu kembali tanpa menulis DB — mencegah resurreksi (R1).
4. **Terapkan `job_queue.contains` sebagai acuan write fence?** Tidak cukup karena `contains` hanya melacak proses ini dan berubah saat worker mulai; gunakan tombstone eksplisit di `AnalysisService`.
5. **Terapkan DECISION A tanpa perubahan:** DB-delete dulu, storage cleanup best-effort, kembali `200`. Orphan storage ditanggulangi nanti oleh garbage collector terpisah (di luar lingkup ini).
6. **Tidak ubah `run_pipeline` di `Backend/ai/`** dan tidak tambah status DB baru.

Hasil akhir yang diinginkan: DELETE segera mengembalikan `200`; record dan storage dibersihkan; job yang masih menunggu dibuang; job aktif menyelesaikan inferensi tetapi **tidak menulis hasil kembali** ke analisis yang sudah dihapus; pengguna melihat `404` saat GET setelah hapus.

---

## 8. Daftar File yang Perlu Diubah (Implementasi Nanti)

1. `Backend/src/services/analysis_service.py`
   - Tambah mekanisme tombstone/cancellation set (in-memory, dilindungi kunci).
   - `delete_analysis`: set tombstone, purge job menunggu dari antrean, lalu `repository.delete` + storage cleanup.
   - `_execute_pipeline` / `_run_analysis_job`: hosekan write fence sebelum persisten akhir (atau lewat parameter ke `AnalysisPipelineService`).
2. `Backend/src/services/analysis_queue_service.py`
   - Tambah operasi aman-thread untuk menghapus job menunggu berdasarkan `analysis_id` (tidak mengubah kapasitas `MAX_WAITING`).
3. `Backend/src/services/analysis_pipeline_service.py`
   - Terima/write fence: sebelum `repository.update(completed)` dan `update(failed)`, periksa apakah analisis masih valid; jika tombstone, bersihkan artefak dan keluar tanpa write DB.
4. `Backend/src/services/storage_service.py`
   - Tidak perlu diubah (sudah ada `delete_analysis_files` + `validate_path_ownership`).
5. `Backend/src/repositories/analysis_repository.py`
   - Tidak perlu diubah (tidak ada perubahan skema).

File yang **tidak** boleh diubah: `Backend/ai/*`, `analysis_progress_service.py`, skema DB, format API, kapasitas antrean.

---

## 9. Test yang Perlu Dibuat (Implementasi Nanti)

1. Hapus saat job menunggu → job tidak dieksekusi, record hilang, slot antrean dilepaskan, `200`.
2. Hapus saat worker aktif (pipeline berjalan) → `200` segera, worker tidak menulis `completed` ke DB (record tetap hilang), artefak dibersihkan, GET → `404`.
3. Hapus saat pipeline sedang mengunggah artefak → tidak ada artefak orphan yang terkait record yang dihapus (atau artefak diunggah lalu dibersihkan).
4. Race: pipeline selesai tepat ketika penghapusan berlangsung → tidak ada resurreksi (record tetap hilang atau completed lalu dihapus, keduanya konsisten).
5. `delete_analysis` sambil job lain berbeda aktif di antrean → job lain tetap berjalan normal (tidak ada gangguan).
6. DB delete gagal → `500 DATABASE_ERROR`, record utuh, storage tidak disentuh (regressi terhadap tes lama Case A).
7. Storage gagal setelah DB berhasil → `200`, record hilang, orphan dicatat (regressi terhadap tes lama Case C/D).
8. `get_analysis` setelah hapus → `404` bahkan jika worker masih menyelesaikan pipeline di latar belakang.
9. Tidak ada circular import baru antara service dan queue.
10. Semua test lama tentang delete (`test_history.py` Case A–E, `test_analysis.py`) tetap lolos tanpa diubah.
