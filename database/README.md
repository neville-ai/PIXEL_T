# PIXEL-T — Database Layer

Directory ini berisi skrip migrasi dan skema basis data untuk sistem PIXEL-T.

## 1. Specification
- **Database:** PostgreSQL (melalui Supabase)
- **Object Storage:** Supabase Storage (untuk menyimpan citra asli, binary mask, segmentation overlay, Grad-CAM heatmap, dan Grad-CAM overlay)
- **Definitive Schema:** Mengacu pada `docs/DataModelSpecification.md`

## 2. Directory Structure
- `migrations/` : Berisi skrip SQL DDL / migrasi skema tabel (untuk MVP menggunakan tabel utama `analyses` dengan asset path sebagai kolom).
- `seed/`       : Berisi data awal/seed untuk pengujian lokal jika diperlukan.

## 3. Important Notes
- Seluruh file citra medis biner disimpan di Supabase Storage, bukan sebagai data biner/base64 di database.
- Database hanya menyimpan metadata analisis, status pemrosesan, dan referensi path objek.
