# NARASI BAB IV — CLASS DIAGRAM PIXEL-T

> **Petunjuk bagi Penulis:** Nomor subbab `4.x` dan nomor gambar `Gambar IV.x` merupakan *placeholder* yang disesuaikan dengan penomoran akhir skripsi. Gambar yang dirujuk adalah `references/bab 4/CLASS_DIAGRAM_FINAL_PIXELT.png` (atau `.svg`).

---

## 4.x Perancangan Struktur Perangkat Lunak (Class Diagram)

Setelah memodelkan aspek fungsionalitas melalui *Use Case Diagram* dan urutan interaksi melalui *Sequence Diagram*, tahap perancangan berikutnya adalah mendefinisikan struktur statis perangkat lunak menggunakan *Class Diagram*. *Class Diagram* menggambarkan kelas-kelas yang menyusun sistem beserta atribut, operasi, dan relasi antarkelas, sehingga menjadi acuan implementasi dan dokumentasi arsitektur perangkat lunak PIXEL-T.

Antarmuka pengguna (*frontend*) PIXEL-T dibangun menggunakan React 18 dan TypeScript dengan paradigma komponen fungsional (*functional components*), *custom hooks*, dan *context*. Dalam rekayasa perangkat lunak modern, memaksakan komponen fungsional React ke dalam kelas berorientasi objek merupakan kesalahan pemodelan karena komponen tersebut tidak memiliki state dan operasi dalam pengertian UML. Oleh karena itu, *Class Diagram* PIXEL-T difokuskan pada lapisan **backend** (Flask), **AI pipeline** (PyTorch), dan **persistensi** (Supabase/PostgreSQL), sedangkan *frontend* direpresentasikan sebagai satu **package** yang berisi tiga modul fungsional (lihat Gambar IV.x). Setiap kelas, atribut, metode, dan relasi dalam diagram ini diverifikasi langsung terhadap kode sumber aktual; tidak ada elemen yang direkayasa.

Gambar IV.x menyajikan *Class Diagram* PIXEL-T dalam gaya monokrom dengan whitespace luas, mirip dengan diagram referensi `class_diagram_contoh.png`. Diagram terdiri dari 19 elemen (7 kelas backend, 6 kelas AI, 3 entitas basis data, dan 3 modul frontend) yang disusun dalam empat package.

### 4.x.1 Kelas Backend (Lapisan Kontrol dan Layanan)

Kelas-kelas backend disusun dalam pola **MVC (Model-View-Controller)** dengan pemisahan tanggung jawab:

1. **`AnalysisController <<controller>>`** — Menangani *request* HTTP dari *frontend*. Memiliki atribut `service: AnalysisService` dan empat operasi: `create_analysis()`, `get_analysis(analysis_id)`, `list_history()`, dan `delete_analysis(analysis_id)`. Setiap operasi memvalidasi identitas pengguna via `require_auth`, lalu mendelegasikan ke `AnalysisService`. Jika identitas tidak valid, melempar `APIError` (UNAUTHORIZED, 401).

2. **`AnalysisService <<service>>`** — Inti logika bisnis. Memiliki empat dependensi: `repository: AnalysisRepository`, `storage_service: StorageService`, `pipeline_runner: Callable`, dan `job_queue: AnalysisJobQueue`. Operasi utamanya:
   - `validate_and_decode_image(file_storage)` — validasi MIME, ukuran, dan format Pillow.
   - `create_analysis(file_storage, user_id)` — orkestrasi validasi, unggah, persistensi, dan antrian.
   - `get_analysis(analysis_id, user_id)` — pengambilan detail dengan signed URL.
   - `list_user_analyses(user_id, limit, offset)` — daftar riwayat.
   - `delete_analysis(analysis_id, user_id)` — penghapusan DB-first dengan pembersihan *storage* best-effort.
   - `_run_analysis_job(job)` dan `_execute_pipeline(analysis_id, user_id, file_bytes)` — eksekusi *background*.
   - `_last_progress_percent(analysis_id, user_id)` — pembacaan progres terakhir.
   - `run_segmentation(file_bytes)` dan `run_gradcam(file_bytes)` — *static method* untuk inferensi langsung.

3. **`AnalysisRepository <<repository>>`** — Abstraksi persistensi tabel `analyses`. Operasi CRUD: `create`, `get_by_id`, `list_by_user`, `update`, `delete`. Memiliki validasi status lifecycle (`validate_lifecycle_status`, `validate_segmentation_status`).

4. **`StorageService <<service>>`** — Pengelola aset Supabase Storage dengan path *ownership-aware* `analysis/{user_id}/{analysis_id}/{category}/{filename}`. Operasi: `generate_*_path`, `get_analysis_asset_paths`, `validate_path_ownership`, `upload_file`, `download_file`, `create_signed_url`, `delete_file`, `delete_analysis_files`, `sanitize_id` (static).

5. **`AnalysisJobQueue <<service>>`** — Antrian pekerjaan *background* (FIFO, kapasitas 4 = `MAX_WAITING` 3 + 1 job aktif) dengan satu worker thread. Operasi: `capacity`, `try_enqueue`, `contains`, `pending_count`, `drain_one`. Internal: `_ensure_worker`, `_work_loop`.

6. **`AnalysisProgressReporter <<service>>`** — Pelapor progres berbasis database write (bukan WebSocket/SSE). Operasi: `last_step`, `completed_units`, `percent`, `on_phase`, `on_pass`, `_write`. Atribut: `total_units`, `failed_writes`.

7. **`APIError <<exception>>`** — Pengecualian terstruktur dengan `code`, `message`, `status_code`. Operasi: `to_dict()`.

### 4.x.2 Kelas AI (Lapisan Kecerdasan Buatan)

Kelas-kelas AI menyusun *pipeline* segmentasi semantik:

1. **`AIInferenceFunctions <<module>>`** — Representasi modul-level yang menggabungkan fungsi dari `ai/inference/pipeline.py`, `segmentation.py`, `postprocessing.py`, `gradcam.py`, dan `preprocessing.py`. Operasi: `run_pipeline`, `predict`, `postprocess_mask`, `measure_mask`, `generate_gradcam`, `prepare_image`, `count_forward_passes`. Stereotype `<<module>>` menandakan bahwa ini adalah kumpulan fungsi, bukan kelas OO.

2. **`ModelService <<service>>`** — Pengelola model PyTorch (U-Net + ResNet50). Memuat model sekali (*lazy loading*), mengunci thread-safe dengan `Lock`, dan mengekspos `predict_logits`, `get_gradcam_target_layer`. Atribut: `_model`, `_device`, `_lock`, `config`, `load_count`.

3. **`ModelConfig <<dataclass>>`** — Konfigurasi beku (*frozen dataclass*) dengan 19 atribut (arsitektur, encoder, *threshold*, TTA, *postprocessing*, *checkpoint*) dan 3 operasi (`checkpoint_path`, `validate`, `checkpoint_sha256_matches`).

4. **`PipelineResult <<dataclass>>`**, **`SegmentationResult <<dataclass>>`**, **`GradCAMResult <<dataclass>>`** — Struktur data hasil inferensi (frozen dataclass).

### 4.x.3 Entitas Basis Data

Tiga entitas dari migrasi SQL:

1. **`auth_users <<external>>`** — Tabel `auth.users` milik Supabase Auth (eksternal). Hanya kolom `id: UUID` yang ditampilkan karena kolom lain di luar kendali aplikasi.

2. **`analyses <<entity>>`** — Tabel utama dengan 39 kolom: identitas (*id*, *user_id*), status lifecycle (*status*, *current_step*, *progress_percent*), metadata citra asli, output segmentasi (path, status, area, bounding box), output Grad-CAM (path, target layer, method, config version, status), metadata model (arsitektur, versi, config, checkpoint SHA-256, *input size*, *threshold*, TTA, *postprocessing*), *summary text*, error, dan *timestamps*.

3. **`doctor_profiles <<entity>>`** — Tabel profil dokter dengan 23 kolom: identitas, data pribadi, data profesional, data kerja, *metadata*, dan *timestamps*.

### 4.x.4 Package Frontend

*Frontend* direpresentasikan sebagai `package "Frontend"` yang berisi tiga class modul fungsional:

1. **`AnalysisClient <<module>>`** — Modul `services/analysis.ts` yang mengekspor `createAnalysis`, `getAnalysis`, `listHistory`, `deleteAnalysis` (HTTP ke backend).
2. **`AuthContext <<module>>`** — Modul `context/AuthContext.tsx` yang mengekspor `signIn`, `signUp`, `signOut` (React context).
3. **`DoctorProfileService <<module>>`** — Modul `services/profile.ts` yang mengekspor `fetchDoctorProfile`, `saveDoctorProfile`, `calculateCompleteness`, `validateProfileData` (Supabase RLS).

### 4.x.5 Relasi Antar Kelas

Relasi utama dalam diagram (20 relasi: 11 dependency, 7 asosiasi berarah, 2 association FK; tidak ada composition):

- **Dependency (garis putus-putus, `..>`):** `AnalysisController ..> APIError`, `AnalysisService ..> AnalysisProgressReporter`, `AnalysisService ..> AIInferenceFunctions`, `AIInferenceFunctions ..> ModelService`, `AIInferenceFunctions ..> PipelineResult/SegmentationResult/GradCAMResult`, `AnalysisRepository ..> analyses`, `AnalysisClient ..> AnalysisController`, `AuthContext ..> auth_users`, `DoctorProfileService ..> doctor_profiles`.

- **Association berarah (garis solid, `-->`):** `AnalysisController "1" --> "1" AnalysisService`, `AnalysisService "1" --> "1" AnalysisRepository`, `AnalysisService "1" --> "1" StorageService`, `AnalysisService "1" --> "1" AnalysisJobQueue`, `AnalysisProgressReporter "1" --> "1" AnalysisRepository`, `PipelineResult "1" --> "1" GradCAMResult`, `ModelService --> ModelConfig`.

- **Association (garis solid, `--`):** `auth_users "1" -- "0..*" analyses` (FK), `auth_users "1" -- "0..1" doctor_profiles` (FK UNIQUE).

- **Composition (`*--`):** tidak digunakan. `AnalysisService` dan `AnalysisProgressReporter` menerima dependensi melalui dependency injection sehingga tidak memiliki lifecycle eksklusif atas repository/storage/queue.

### 4.x.6 Penjelasan Alur Runtime (untuk validasi diagram)

Diagram ini adalah model struktur statis. Alur runtime (autentikasi, unggah, analisis AI, pelaporan progres, riwayat, profil) divisualisasikan pada *Sequence Diagram* dan *Activity Diagram* di folder terpisah. Namun, struktur kelas yang ditampilkan di sini adalah **prasyarat** dari alur-alur tersebut: setiap interaksi pada *Sequence Diagram* merujuk ke kelas dan operasi yang didefinisikan di sini.

---

## 4.x.7 Catatan Representasi (Penting)

1. **Frontend bukan kelas OO sesungguhnya.** Class-class di dalam `package "Frontend"` adalah **representasi modul fungsional**. Stereotype `<<module>>` menandakan bahwa elemen-elemen tersebut adalah kumpulan operasi terkait, bukan kelas dengan instance state.

2. **AIInferenceFunctions adalah modul, bukan kelas.** Stereotype `<<module>>` menandakan bahwa ini adalah kumpulan fungsi dari beberapa berkas Python.

3. **auth_users adalah tabel eksternal.** Milik Supabase Auth; hanya kolom `id` yang ditampilkan.

4. **Entitas database menampilkan semua kolom.** Jika diagram terlalu padat, subset kolom dapat dipilih dengan catatan eksplisit.

5. **Tidak ada catatan kuning atau ikon warna.** Gaya visual mengikuti `class_diagram_contoh.png`: monokrom, bold centered, `+`/`-`, `nama: tipe`, relasi sederhana, whitespace luas.