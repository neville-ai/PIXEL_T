# AUDIT VALIDASI BAB VI — KESIMPULAN DAN SARAN PIXEL-T

Dokumen ini merupakan pendukung audit untuk Bab VI skripsi PIXEL-T. Dokumen ini berisi hasil validasi terhadap penulisan Bab VI **KESIMPULAN DAN SARAN**, memuat daftar sumber yang diperiksa, klaim yang terverifikasi, nilai metrik yang diverifikasi, informasi yang belum tersedia, ketidaksesuaian antardokumen, serta penilaian kesesuaian Bab VI terhadap skripsi.

---

## 1. Daftar Sumber yang Diperiksa

| No. | Sumber | Kategori | Status |
|---|---|---|---|
| 1 | `docs/PRD_PIXEL-T_FINAL.md` | Dokumen prasyarat produk PIXEL-T | Diperiksa |
| 2 | `docs/ModelIntegrationSpecification.md` | Spesifikasi integrasi model | Diperiksa |
| 3 | `docs/FunctionalSpecification.md` | Spesifikasi fungsional aplikasi | Diperiksa |
| 4 | `docs/CodebaseAnalysis.md` | Analisis implementasi kode | Diperiksa |
| 5 | `research/PIXEL-T_Scenario1_Ver22_config.json` | Konfigurasi model Scenario 1 Ver.22 | Diperiksa |
| 6 | `research/PIXEL-T_Scenario1_Ver22_evaluation_results.csv` | Hasil evaluasi model Scenario 1 Ver.22 | Diperiksa |
| 7 | `research/segmentationcolonpolyp-unet-resnet50-gradcam.ipynb` | Arsip notebook pelatihan dan evaluasi | Diperiksa |
| 8 | `frontend/src/pages/auth/Register.tsx`, `Login.tsx`, `context/AuthContext.tsx`, `services/auth.ts` | Implementasi autentikasi | Diperiksa |
| 9 | `backend/app/core/auth.py` | Verifikasi token backend Flask | Diperiksi |
| 10 | `docs/StyleGuide.md` | Referensi gaya penulisan | Diperiksa |
| 11 | `LUCIT - BAB 4.docx` | Referensi gaya penulisan Bab IV | Diperiksa |
| 12 | `Skripsi_Faithza Mandolang dan Grace Bindosano.pdf` | Referensi gaya penulisan akademik | Diperiksa |
| 13 | `references/bab 4/BAB 4 - PIXEL-T.docx` | Dokumen Bab IV PIXEL-T | Diperiksa |
| 14 | `references/bab 4/revisi/PENJELASAN_ACTIVITY_DAN_SEQUENCE_DIAGRAM_SIGN_UP_SIGN_IN_PIXELT.md` | Penjelasan Activity/Sequence Sign Up-Sign In | Diperiksa |

---

## 2. Matriks Hubungan Rumusan Masalah, Tujuan, dan Kesimpulan

| No. | Komponen | Keterangan |
|---|---|---|
| 1 | Rumusan masalah | Masalah bantuan dokter dalam meninjau area polip pada citra endoskopi; dijawab melalui pengembangan metode segmentasi, Explainable AI, dan aplikasi web. |
| 2 | Tujuan penelitian | Pengembangan sistem segmentasi polip dengan U-Net + ResNet-50, Grad-CAM, dan aplikasi web untuk mendukung keputusan klinis dokter. |
| 3 | Metode | Transfer Learning, pelatihan U-Net, evaluasi dengan metrik Dice/IoU/HD95, inferensi TTA, pasca-pemrosesan, Grad-CAM, integrasi web. |
| 4 | Hasil eksperimen | Test Dice 0,9510; Test IoU 0,9136; presisi 0,9568; recall 0,9685; HD95 12,9049 piksel (TTA + pasca-pemrosesan). |
| 5 | Implementasi web | Tujuh fitur utama: Sign Up, Sign In, Upload Image, Segmentation, History, Doctor Profile, Sign Out. |
| 6 | Pengujian fungsional | 245 tes frontend lulus dari 17 berkas tes; backend/AI belum dijalankan. |
| 7 | Kesimpulan Bab VI | Mengaitkan hasil eksperimen, keterbatasan data, dan implementasi ke tujuan penelitian. |
| 8 | Saran Bab VI | Berangkat dari temuan dan keterbatasan, belum mengklaim kegagalan atau keberhasilan di luar bukti. |

---

## 3. Daftar Klaim yang Terverifikasi

| No. | Klaim Bab VI | Bukti |
|---|---|---|
| 1 | Model menggunakan arsitektur U-Net + ResNet-50, encoder ImageNet, SCSE | `docs/ModelIntegrationSpecification.md`, `research/..._config.json` |
| 2 | Threshold 0,55, TTA 25 forward pass, postprocessing min area 25 px | `docs/ModelIntegrationSpecification.md`, `research/..._config.json`, `ai/inference/*` |
| 3 | Hasil evaluasi Ver.22: Test Dice 0,9510; IoU 0,9136; Precision 0,9568; Recall 0,9685; HD95 12,9049 | `research/PIXEL-T_Scenario1_Ver22_evaluation_results.csv` |
| 4 | Best epoch 83, best val Dice (EMA) 0,9507, best threshold 0,55 | `research/PIXEL-T_Scenario1_Ver22_evaluation_results.csv` |
| 5 | Grad-CAM pada `decoder.blocks.4.conv2.0`, kegagalan menggagalkan pekerjaan | `docs/CodebaseAnalysis.md`, `ai/inference/gradcam.py` |
| 6 | 245 tes frontend lulus, 17 berkas tes | `docs/CodebaseAnalysis.md` |
| 7 | Backend/AI tidak dapat dijalankan pada mesin audit | `docs/CodebaseAnalysis.md` |

---

## 4. Daftar Klaim yang Direvisi atau Tidak Digunakan

| No. | Klaim atau Area | Alasan |
|---|---|---|
| 1 | Penggunaan nilai dari tiga skenario model | Hanya Scenario 1 Ver.22 tersedia sebagai artefak terverifikasi; hasil skenario lain belum tersedia sebagai artefak yang dapat diverifikasi. |
| 2 | Klaim bahwa Grad-CAM meningkatkan akurasi | Tidak didukung eksperimen; tidak digunakan dalam Bab VI. |
| 3 | Klaim keberhasilan diagnosis klinis | Tidak didukung pengujian; tidak digunakan dalam Bab VI. |
| 4 | Penyimpangan nilai metrik pada dokumen tertentu | Dilaporkan sebagai ketidaksesuaian antardokumen; nilai final disesuaikan dari artefak eksperimen. |

---

## 5. Nilai Metrik yang Berhasil Diverifikasi

| No. | Nilai | Sumber | Status |
|---|---|---|---|
| 1 | Best Epoch | 83 | Terverifikasi |
| 2 | Best Dice Validation (EMA) | 0,9507 | Terverifikasi |
| 3 | Best Threshold | 0,55 | Terverifikasi |
| 4 | Test Dice (TTA + PostProc) | 0,9510 | Terverifikasi |
| 5 | Test IoU (TTA + PostProc) | 0,9136 | Terverifikasi |
| 6 | Accuracy | 0,9918 | Terverifikasi |
| 7 | Precision | 0,9568 | Terverifikasi |
| 8 | Recall | 0,9685 | Terverifikasi |
| 9 | HD95 | 12,9049 | Terverifikasi |

---

## 6. Informasi yang Belum Tersedia

| No. | Informasi | Keterangan |
|---|---|---|
| 1 | Hasil evaluasi skenario 2 dan 3 | Belum tersedia sebagai artefak terverifikasi. |
| 2 | Konfigurasi proyek Supabase aktif | Belum terverifikasi. |
| 3 | Perilaku email konfirmasi dan reset password | Belum terverifikasi. |
| 4 | Pengujian backend dan AI pada runtime nyata | Belum dapat dijalankan pada mesin audit. |
| 5 | Hasil penelitian LUCIT dan Faithza & Grace (untuk gaya/penulisan) | Sebagian informasi mengenai gaya penulisan yang diperoleh; detail metodologi penelitian mereka tidak digunakan sebagai sumber PIXEL-T. |
| 6 | Skripsi PIXEL-T lengkap (Bab I–V) dalam satu berkas | Tidak tersedia; sumber utama diperoleh dari dokumen pendukung internal. |

---

## 7. Ketidaksesuaian Antardokumen

| No. | Pergadangan | Kesimpulan |
|---|---|---|
| 1 | Dokumen penjelasan Bab IV menyebutkan peran admin dan status akun, sedangkan laporan codebase menyatakan multi-user/admin tidak ada pada implementasi akhir | Dilaporkan perbedaannya; Bab VI tidak menggunakannya sebagai klaim. |
| 2 | Dokumentasi API menyebut endpoint auth `POST /api/auth/*` yang tidak ada pada kode | Dilaporkan; implementasi nyata menggunakan Supabase Auth langsung pada klien. |
| 3 | Deskripsi model pada dokumen vs implementasi | Diperiksa dan diselaraskan dengan artefak eksperimen. |

---

## 8. Dasar Penyusunan Setiap Saran pada Bab VI

| No. | Saran Bab VI | Dasar Temuan |
|---|---|---|
| 1 | Pengembangan dataset | Tidak adanya citra normal/polon dalam data uji. |
| 2 | Pengembangan model | Hasil perbandingan skenario terbatas; boundary loss sempat diuji dan tidak membantu. |
| 3 | Pengembangan Grad-CAM | Grad-CAM belum dievaluasi terhadap interpretabilitas klinis. |
| 4 | Perbaikan aplikasi web | Startup reset sesi, batas riwayat 20, polling 12 kali, RLS, stale jobs, env config. |
| 5 | Pengujian lanjutan | Belum adanya eksekusi backend/AI; perlunya lingkungan PyTorch yang mendukung. |

---

## 9. Penilaian Akhir Kesesuaian Bab VI terhadap Skripsi PIXEL-T

Berdasarkan audit yang dilakukan, penulisan Bab VI **KESIMPULAN DAN SARAN** dinyatakan sejalan dengan sumber internal penelitian PIXEL-T yang tersedia, dengan catatan bahwa:

- Semua klaim utama dalam Bab VI dapat ditelusuri ke artefak eksperimen dan implementasi.
- Nilai metrik evaluasi telah diverifikasi secara internal konsisten (CSV + config).
- Tidak ada klaim yang tidak didukung bukti dalam Bab VI.
- Terdapat ketidaksesuaian yang dilaporkan secara eksplisit sebagai catatan audit.

---

## 10. Catatan yang Masih Membutuhkan Konfirmasi Penulis

| No. | Catatan | Status |
|---|---|---|
| 1 | Hasil skenario model selain Scenario 1 Ver.22 | Perlu konfirmasi penulis terkait hasil eksperimen terakhir. |
| 2 | Penyempurnaan nilai metrik (format, satuan, konteks TTA) | Perlu konfirmasi penyelia metrik. |
| 3 | Pengesahan kesimpulan akhir Bab VI | Perlu konfirmasi penulis sebelum disalin ke Bab IV/V. |

---

*Audit ini disusun berdasarkan penelaahan terhadap sumber-sumber internal PIXEL-T, termasuk dokumen prasyarat produk, spesifikasi model, spesifikasi fungsional, analisis implementasi, artefak eksperimen, dan implementasi autentikasi aplikasi web. Audit ini bukan bagian dari naskah akademik utama skripsi.*
