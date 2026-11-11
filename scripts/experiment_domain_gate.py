"""
experiment_domain_gate.py â€” Fase B Eksperimen Gerbang Validasi Kolonoskopi
===========================================================================
Membaca HANYA subfolder "calib" dari calibration_data/{positive,negative}/<kelompok>/calib/
Subfolder "holdout" DILARANG dibaca / dibuka / dijalankan.

Tujuan:
  B0. Verifikasi regresi pipeline sekarang vs HEAD (Dice score, mask differences)
  B1. Normalisasi resolusi G5 (Hough) dan evaluasi korelasi resolusi
  B2. Analisis G3 (images 19), G4 (grayscale images 22, 23 + run model), dan jaringan merah muda halus
  B3. Konsistensi pesan & titik pemanggilan
  B4. Evaluasi 3 kandidat konfigurasi keputusan akhir
"""

from __future__ import annotations

import csv
import io
import math
import os
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
import torch
from PIL import Image
from scipy.stats import pearsonr, spearmanr

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Path setup
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "Backend"))

from ai.config.model_config import MODEL_CONFIG
from ai.inference.domain_validator import ColonoscopyDomainValidator, DomainDecision
from ai.inference.pipeline import run_pipeline
from ai.inference.postprocessing import measure_mask, postprocess_mask, resize_binary_mask
from ai.inference.preprocessing import prepare_image
from ai.inference.segmentation import predict

CALIB_DATA_ROOT = PROJECT_ROOT / "calibration_data"
OUTPUT_DIR = PROJECT_ROOT / "scripts" / "output"
GRAYSCALE_OUT_DIR = OUTPUT_DIR / "grayscale_test"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
GRAYSCALE_OUT_DIR.mkdir(parents=True, exist_ok=True)

POSITIVE_GROUPS = ["kvasir", "cvc_clinicdb", "cvc_colondb", "etis", "bkai", "hyperkvasir", "in_vivo_blur"]
NEGATIVE_GROUPS = ["makanan", "merah_organik", "orang_ruangan", "dokumen_screenshot", "medis_lain", "endoskopi_non_kolon"]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

# ---------------------------------------------------------------------------
# Helper: baca file aman Windows MAX_PATH
# ---------------------------------------------------------------------------
def safe_open_image(path: Path) -> Image.Image:
    abs_str = str(path.resolve())
    if len(abs_str) >= 240 and os.name == "nt" and not abs_str.startswith("\\\\?\\"):
        extended_path = "\\\\?\\" + abs_str
        with open(extended_path, "rb") as f:
            return Image.open(f).convert("RGB")
    with open(abs_str, "rb") as f:
        return Image.open(f).convert("RGB")

def safe_read_bytes(path: Path) -> bytes:
    abs_str = str(path.resolve())
    if len(abs_str) >= 240 and os.name == "nt" and not abs_str.startswith("\\\\?\\"):
        extended_path = "\\\\?\\" + abs_str
        with open(extended_path, "rb") as f:
            return f.read()
    with open(abs_str, "rb") as f:
        return f.read()

# ---------------------------------------------------------------------------
# B0.2: Uji Regresi Pipeline Sekarang vs HEAD
# ---------------------------------------------------------------------------
def run_b0_regression_experiment() -> List[Dict[str, Any]]:
    print("\n" + "="*70)
    print("[B0.2] Menjalankan Uji Regresi Pipeline (Kode Sekarang vs HEAD Baseline)")
    print("="*70)

    sample_images = [
        ("cvc_clinicdb", "1.png"),
        ("cvc_colondb", "1.png"),
        ("kvasir", "cju0s690hkp960855tjuaqvv0.jpg"),
        ("bkai", "02fa602bb3c7abacdbd7e6afd56ea7bc.jpeg"),
    ]

    results = []

    for grp, fname in sample_images:
        img_path = CALIB_DATA_ROOT / "positive" / grp / "calib" / fname
        if not img_path.exists():
            continue

        raw_bytes = safe_read_bytes(img_path)

        # 1. Pipeline sekarang
        curr_res = run_pipeline(raw_bytes, MODEL_CONFIG, analysis_id=f"curr_{grp}")
        curr_mask = np.array(Image.open(io.BytesIO(curr_res.binary_mask_png))) > 0

        # 2. Pipeline baseline HEAD
        with Image.open(io.BytesIO(raw_bytes)) as decoded:
            orig = decoded.convert("RGB")
            w, h = orig.size
        seg = predict(orig, config=MODEL_CONFIG)
        post_512 = postprocess_mask(seg.binary_mask[0, 0].numpy(), MODEL_CONFIG)
        head_mask = resize_binary_mask(post_512, w, h) > 0

        diff_pixels = int(np.sum(curr_mask != head_mask))
        intersection = int(np.sum(curr_mask & head_mask))
        dice = (2.0 * intersection) / (np.sum(curr_mask) + np.sum(head_mask)) if (np.sum(curr_mask) + np.sum(head_mask)) > 0 else 1.0

        print(f"  [{grp:<14}] {fname:<36} | Diff Pixels: {diff_pixels:<4} | Dice: {dice:.6f} | Identical: {diff_pixels == 0}")
        results.append({
            "group": grp,
            "filename": fname,
            "image_size": f"{w}x{h}",
            "curr_mask_area": int(np.sum(curr_mask)),
            "head_mask_area": int(np.sum(head_mask)),
            "diff_pixels": diff_pixels,
            "dice_similarity": round(dice, 6),
            "identical": diff_pixels == 0,
        })
        torch.cuda.empty_cache()

    csv_path = OUTPUT_DIR / "b0_pipeline_regression.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)
    print(f"  â†’ Disimpan ke: {csv_path}")
    return results

# ---------------------------------------------------------------------------
# B1: Normalisasi Resolusi G5 (Hough)
# ---------------------------------------------------------------------------
def compute_g5_variants(gray: np.ndarray, width: int, height: int) -> Dict[str, float]:
    min_dim = min(width, height)

    # 1. Original
    edges_orig = cv2.Canny(gray, 50, 150)
    lines_orig = cv2.HoughLinesP(edges_orig, 1, np.pi / 180, threshold=40, minLineLength=30, maxLineGap=10)
    cnt_orig = len(lines_orig) if lines_orig is not None else 0
    ld_orig = (cnt_orig * 30.0) / (2.0 * (width + height))

    # 2. Resize sisi terpendek = 256
    scale_256 = 256.0 / float(min_dim)
    w_256 = max(1, int(round(width * scale_256)))
    h_256 = max(1, int(round(height * scale_256)))
    interp_256 = cv2.INTER_AREA if scale_256 < 1.0 else cv2.INTER_LINEAR
    gray_256 = cv2.resize(gray, (w_256, h_256), interpolation=interp_256)
    edges_256 = cv2.Canny(gray_256, 50, 150)
    lines_256 = cv2.HoughLinesP(edges_256, 1, np.pi / 180, threshold=40, minLineLength=25, maxLineGap=8)
    cnt_256 = len(lines_256) if lines_256 is not None else 0
    ld_256 = (cnt_256 * 25.0) / (2.0 * (w_256 + h_256))

    # 3. Resize sisi terpendek = 512
    scale_512 = 512.0 / float(min_dim)
    w_512 = max(1, int(round(width * scale_512)))
    h_512 = max(1, int(round(height * scale_512)))
    interp_512 = cv2.INTER_AREA if scale_512 < 1.0 else cv2.INTER_LINEAR
    gray_512 = cv2.resize(gray, (w_512, h_512), interpolation=interp_512)
    edges_512 = cv2.Canny(gray_512, 50, 150)
    lines_512 = cv2.HoughLinesP(edges_512, 1, np.pi / 180, threshold=40, minLineLength=50, maxLineGap=15)
    cnt_512 = len(lines_512) if lines_512 is not None else 0
    ld_512 = (cnt_512 * 50.0) / (2.0 * (w_512 + h_512))

    # 4. Parameter Hough Fraksional (pada gambar asli)
    min_len_frac = max(15, int(min_dim * 0.06))
    max_gap_frac = max(5, int(min_dim * 0.02))
    lines_frac = cv2.HoughLinesP(edges_orig, 1, np.pi / 180, threshold=40, minLineLength=min_len_frac, maxLineGap=max_gap_frac)
    cnt_frac = len(lines_frac) if lines_frac is not None else 0
    ld_frac = (cnt_frac * min_len_frac) / (2.0 * (width + height))

    return {
        "ld_original": round(ld_orig, 4),
        "ld_norm_256": round(ld_256, 4),
        "ld_norm_512": round(ld_512, 4),
        "ld_fractional": round(ld_frac, 4),
    }

def run_b1_g5_analysis() -> Dict[str, Any]:
    print("\n" + "="*70)
    print("[B1] Analisis Normalisasi Resolusi G5 (Hough Line Density)")
    print("="*70)

    rows = []
    res_list = []
    ld_orig_list = []
    ld_256_list = []
    ld_512_list = []
    ld_frac_list = []

    for side, groups in [("positive", POSITIVE_GROUPS), ("negative", NEGATIVE_GROUPS)]:
        for grp in groups:
            p_dir = CALIB_DATA_ROOT / side / grp / "calib"
            if not p_dir.exists():
                continue
            for img_file in sorted(p_dir.iterdir()):
                if img_file.suffix.lower() not in IMAGE_EXTENSIONS:
                    continue
                try:
                    img = safe_open_image(img_file)
                except Exception as e:
                    print(f"  [ERROR] {img_file.name}: {e}")
                    continue

                w, h = img.size
                min_dim = min(w, h)
                gray = cv2.cvtColor(np.asarray(img), cv2.COLOR_RGB2GRAY)
                g5_res = compute_g5_variants(gray, w, h)

                res_list.append(min_dim)
                ld_orig_list.append(g5_res["ld_original"])
                ld_256_list.append(g5_res["ld_norm_256"])
                ld_512_list.append(g5_res["ld_norm_512"])
                ld_frac_list.append(g5_res["ld_fractional"])

                row = {
                    "path": str(img_file),
                    "filename": img_file.name,
                    "side": side,
                    "group": grp,
                    "width": w,
                    "height": h,
                    "min_dim": min_dim,
                }
                row.update(g5_res)
                rows.append(row)

    # Korelasi
    r_orig, p_orig = pearsonr(res_list, ld_orig_list)
    rho_orig, sp_orig = spearmanr(res_list, ld_orig_list)

    r_256, p_256 = pearsonr(res_list, ld_256_list)
    rho_256, sp_256 = spearmanr(res_list, ld_256_list)

    r_512, p_512 = pearsonr(res_list, ld_512_list)
    rho_512, sp_512 = spearmanr(res_list, ld_512_list)

    r_frac, p_frac = pearsonr(res_list, ld_frac_list)
    rho_frac, sp_frac = spearmanr(res_list, ld_frac_list)

    print(f"  Korelasi line_density dengan Resolusi (min_dim):")
    print(f"    - Original       : Pearson r = {r_orig:+.4f} (p={p_orig:.2e}), Spearman rho = {rho_orig:+.4f}")
    print(f"    - Norm Sisi 256  : Pearson r = {r_256:+.4f} (p={p_256:.2e}), Spearman rho = {rho_256:+.4f}")
    print(f"    - Norm Sisi 512  : Pearson r = {r_512:+.4f} (p={p_512:.2e}), Spearman rho = {rho_512:+.4f}")
    print(f"    - Fraksional     : Pearson r = {r_frac:+.4f} (p={p_frac:.2e}), Spearman rho = {rho_frac:+.4f}")

    # Simpan CSV
    csv_path = OUTPUT_DIR / "b1_g5_resolution_analysis.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print(f"  â†’ Data detail disimpan ke: {csv_path}")

    # Cek khusus 7 citra BKAI/HyperKvasir yang sebelumnya ditolak G5b
    print("\n  Periksa 7 Citra Positif yang Sebelumnya Ditolak G5b:")
    rejected_7_names = [
        "0a5f3601ad4f13ccf1f4b331a412fc44.jpeg",
        "1ad4f13ccf1f4b331a412fc44655fb51.jpeg",
        "1b62f15ec83b97bb11e8e0c4416c1931.jpeg",
        "3dd311a65d2b46d0a6085835c525af63.jpeg",
        "4c1711b62f15ec83b97bb11e8e0c4416.jpeg",
        "cju0qkwl35piu0993l0dewei2.jpg",
        "cju0sr5ghl0nd08789uzf1raf.jpg",
    ]
    for r in rows:
        if r["filename"] in rejected_7_names:
            print(f"    {r['filename'][:32]} | Res: {r['width']}x{r['height']} | ld_orig: {r['ld_original']:>6.2f} | ld_256: {r['ld_norm_256']:>6.2f} | ld_512: {r['ld_norm_512']:>6.2f}")

    return {
        "correlation": {
            "original": (r_orig, rho_orig),
            "norm_256": (r_256, rho_256),
            "norm_512": (r_512, rho_512),
            "fractional": (r_frac, rho_frac),
        },
        "rows": rows,
    }

# ---------------------------------------------------------------------------
# B2: Analisis Khusus images (19), Grayscale (22, 23), dan Jaringan Merah Muda
# ---------------------------------------------------------------------------
def run_b2_special_images_analysis():
    print("\n" + "="*70)
    print("[B2] Analisis Mendalam: images (19) (Blue), Grayscale (22, 23), & Jaringan Merah Muda")
    print("="*70)

    # 1. Analisis images (19)
    p_19 = CALIB_DATA_ROOT / "positive" / "in_vivo_blur" / "calib" / "images (19).jpg"
    if p_19.exists():
        img_19 = safe_open_image(p_19)
        rgb_19 = np.asarray(img_19)
        hsv_19 = cv2.cvtColor(rgb_19, cv2.COLOR_RGB2HSV)
        lab_19 = cv2.cvtColor(rgb_19, cv2.COLOR_RGB2LAB)
        print(f"  images (19) Dimensions: {img_19.size}")
        print(f"  Mean RGB: R={rgb_19[:,:,0].mean():.1f}, G={rgb_19[:,:,1].mean():.1f}, B={rgb_19[:,:,2].mean():.1f}")
        print(f"  Mean HSV: H={hsv_19[:,:,0].mean():.1f}, S={hsv_19[:,:,1].mean():.1f}, V={hsv_19[:,:,2].mean():.1f}")
        print(f"  Mean Lab: L={lab_19[:,:,0].mean():.1f}, a*={lab_19[:,:,1].mean():.1f}, b*={lab_19[:,:,2].mean():.1f}")

    # 2. Uji Model Segmentasi pada images (22) dan (23) (Grayscale)
    grayscale_eval = []
    for g_fname in ["images (22).jpg", "images (23).jpg"]:
        p_g = CALIB_DATA_ROOT / "positive" / "in_vivo_blur" / "calib" / g_fname
        if not p_g.exists():
            continue
        img_g = safe_open_image(p_g)
        w, h = img_g.size
        seg = predict(img_g, config=MODEL_CONFIG)
        post_512 = postprocess_mask(seg.binary_mask[0, 0].numpy(), MODEL_CONFIG)
        mask_g = resize_binary_mask(post_512, w, h)
        prob_map = seg.probability_map[0, 0].numpy()
        meas = measure_mask(mask_g, probability_map=prob_map)

        overlay = np.array(img_g).copy()
        overlay[mask_g > 0, 0] = np.clip(overlay[mask_g > 0, 0] * 0.5 + 255 * 0.5, 0, 255)
        out_img_path = GRAYSCALE_OUT_DIR / f"overlay_{g_fname}"
        Image.fromarray(overlay).save(out_img_path)

        grayscale_eval.append({
            "filename": g_fname,
            "dimensions": f"{w}x{h}",
            "area_pixels": meas["area_pixels"],
            "area_percentage": meas["area_percentage"],
            "mean_prob": meas["mean_probability"],
            "max_prob": meas["max_probability"],
            "detection_category": meas["detection_category"],
            "saved_overlay": str(out_img_path),
        })
        print(f"  Grayscale {g_fname} | Area: {meas['area_pixels']} px ({meas['area_percentage']:.2f}%) | Max Prob: {meas['max_probability']:.2f} | Mean Prob: {meas['mean_probability']:.2f} | Category: {meas['detection_category']}")
        torch.cuda.empty_cache()

    csv_path = OUTPUT_DIR / "b2_grayscale_evaluation.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(grayscale_eval[0].keys()))
        writer.writeheader()
        writer.writerows(grayscale_eval)
    print(f"  â†’ Evaluasi grayscale disimpan ke: {csv_path}")

    # 3. Analisis Jaringan Merah Muda Halus
    fine_pink_samples = [
        ("makanan", "images (39).jpg", "tomat"),
        ("merah_organik", "images (43).jpg", "gusi"),
        ("merah_organik", "images (44).jpg", "gusi"),
        ("orang_ruangan", "images (50).jpg", "ruangan gelap lampu merah"),
        ("medis_lain", "images (69).jpg", "kulit lengan manusia"),
        ("medis_lain", "images (72).jpg", "retina mata"),
        ("medis_lain", "images (73).jpg", "retina mata"),
    ]
    print("\n  Analisis Karakteristik Jaringan Merah Muda Halus vs Positif Kolonoskopi:")
    for grp, fname, label in fine_pink_samples:
        p_s = CALIB_DATA_ROOT / "negative" / grp / "calib" / fname
        if not p_s.exists():
            continue
        img_s = safe_open_image(p_s)
        rgb_s = np.asarray(img_s)
        gray_s = cv2.cvtColor(rgb_s, cv2.COLOR_RGB2GRAY)
        lap_var = cv2.Laplacian(gray_s, cv2.CV_64F).var()
        hsv_s = cv2.cvtColor(rgb_s, cv2.COLOR_RGB2HSV)
        lab_s = cv2.cvtColor(rgb_s, cv2.COLOR_RGB2LAB)
        print(f"    [{grp:<13}] {fname:<15} ({label:<25}) | LapVar: {lap_var:>7.1f} | Std_V: {hsv_s[:,:,2].std():>5.1f} | Mean_S: {hsv_s[:,:,1].mean()/255.0:>4.2f}")

# ---------------------------------------------------------------------------
# B4: Evaluasi Tiga Kandidat Konfigurasi Keputusan Akhir
# ---------------------------------------------------------------------------
def evaluate_candidate_gate(
    img: Image.Image,
    candidate: str, # "baseline", "cand_1", "cand_2", "cand_3"
) -> Tuple[DomainDecision, str, float, Dict[str, float]]:
    w, h = img.size
    min_dim = min(w, h)
    aspect_ratio = max(w / h, h / w)

    metrics = {"width": float(w), "height": float(h), "aspect_ratio": float(aspect_ratio)}

    if w < 150 or h < 150:
        return DomainDecision.REJECT, "G1_dim", 0.0, metrics
    if aspect_ratio > 2.8:
        return DomainDecision.REJECT, "G1_dim", 0.0, metrics

    rgb = np.asarray(img, dtype=np.uint8)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)

    active_mask = gray > 18
    active_pixels = int(np.sum(active_mask))
    total_pixels = w * h
    active_ratio = active_pixels / total_pixels if total_pixels > 0 else 0.0
    metrics["active_ratio"] = float(active_ratio)

    if active_pixels < (total_pixels * 0.12):
        return DomainDecision.REJECT, "G2_dark", 0.0, metrics

    h_chan = hsv[:, :, 0]
    s_chan = hsv[:, :, 1]
    v_chan = hsv[:, :, 2]
    a_chan = lab[:, :, 1]
    b_chan = lab[:, :, 2]

    mean_v = float(np.mean(v_chan[active_mask])) / 255.0
    std_v = float(np.std(v_chan[active_mask]))
    mean_s = float(np.mean(s_chan[active_mask])) / 255.0
    a_dev = a_chan[active_mask].astype(np.float32) - 128.0
    b_dev = b_chan[active_mask].astype(np.float32) - 128.0
    mean_chroma = float(np.mean(np.sqrt(a_dev**2 + b_dev**2)))
    metrics["mean_luminance"] = mean_v
    metrics["std_luminance"] = std_v
    metrics["mean_saturation"] = mean_s
    metrics["mean_chroma"] = mean_chroma

    warm_hue_mask = ((h_chan <= 22) | (h_chan >= 160)) & (s_chan >= 28) & (v_chan >= 28)
    lab_mucosal_mask = (a_chan >= 134) & (b_chan >= 130)
    mucosal_mask = (warm_hue_mask | lab_mucosal_mask) & active_mask
    mucosal_ratio = float(np.sum(mucosal_mask)) / active_pixels
    metrics["mucosal_ratio"] = mucosal_ratio

    cool_mask = ((h_chan >= 36) & (h_chan <= 140)) & (s_chan >= 35) & (v_chan >= 30) & active_mask
    cool_ratio = float(np.sum(cool_mask)) / active_pixels
    metrics["cool_ratio"] = cool_ratio

    glint_mask = (v_chan >= 240) & (s_chan <= 45) & active_mask
    glint_ratio = float(np.sum(glint_mask)) / active_pixels
    metrics["glint_ratio"] = glint_ratio

    # Hitung line density sesuai kandidat
    if candidate == "baseline":
        edges = cv2.Canny(gray, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=40, minLineLength=30, maxLineGap=10)
        cnt = len(lines) if lines is not None else 0
        line_density = (cnt * 30.0) / (2.0 * (w + h))
    elif candidate in ("cand_1", "cand_2"):
        scale = 256.0 / float(min_dim)
        w_n = max(1, int(round(w * scale)))
        h_n = max(1, int(round(h * scale)))
        interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
        gray_n = cv2.resize(gray, (w_n, h_n), interpolation=interp)
        edges = cv2.Canny(gray_n, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=40, minLineLength=25, maxLineGap=8)
        cnt = len(lines) if lines is not None else 0
        line_density = (cnt * 25.0) / (2.0 * (w_n + h_n))
    elif candidate == "cand_3":
        scale = 512.0 / float(min_dim)
        w_n = max(1, int(round(w * scale)))
        h_n = max(1, int(round(h * scale)))
        interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
        gray_n = cv2.resize(gray, (w_n, h_n), interpolation=interp)
        edges = cv2.Canny(gray_n, 50, 150)
        lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=40, minLineLength=50, maxLineGap=15)
        cnt = len(lines) if lines is not None else 0
        line_density = (cnt * 50.0) / (2.0 * (w_n + h_n))

    metrics["line_density"] = float(line_density)

    # G3: Cool Hue Penalty
    cool_threshold = 0.30 if candidate in ("baseline", "cand_1") else 0.40
    if cool_ratio > cool_threshold:
        return DomainDecision.REJECT, "G3_cool", 0.10, metrics

    # G4: Akromatik / Grayscale
    is_achromatic = (mean_chroma < 10.0 or mean_s < 0.10)
    if is_achromatic:
        if candidate in ("cand_2", "cand_3"):
            return DomainDecision.UNCERTAIN, "G4_chroma_uncertain", 0.40, metrics
        else:
            return DomainDecision.REJECT, "G4_chroma", 0.10, metrics

    # G5a: Line density tinggi pada mukosa rendah
    straight_edge_reject = 0.50 if candidate == "baseline" else 1.0
    if line_density > straight_edge_reject and mucosal_ratio < 0.55:
        return DomainDecision.REJECT, "G5_line_low_mucosa", 0.15, metrics

    # G5b: Line density tinggi pada mukosa hangat
    if candidate == "baseline":
        if line_density > 10.0 and mucosal_ratio > 0.55:
            return DomainDecision.REJECT, "G5_line_warm", 0.15, metrics
    elif candidate == "cand_1":
        if line_density > 8.0 and mucosal_ratio > 0.55:
            return DomainDecision.REJECT, "G5_line_warm", 0.15, metrics
    elif candidate in ("cand_2", "cand_3"):
        extreme_th = 12.0 if candidate == "cand_2" else 15.0
        if line_density > extreme_th and mucosal_ratio > 0.55:
            return DomainDecision.REJECT, "G5_line_extreme", 0.15, metrics

    # G6: Mukosa sangat rendah
    if mucosal_ratio < 0.32:
        return DomainDecision.REJECT, "G6_mucosa_reject", 0.20, metrics

    # G7: Permukaan merah datar seragam
    if std_v < 8.5 and glint_ratio < 0.0001:
        return DomainDecision.UNCERTAIN, "G7_flat_red", 0.45, metrics

    # G8: Luminansi sangat rendah
    if mean_v < 0.18:
        return DomainDecision.UNCERTAIN, "G8_luminance", 0.48, metrics

    # G9: Mukosa marjinal
    if mucosal_ratio < 0.55:
        return DomainDecision.UNCERTAIN, "G9_mucosa_uncertain", 0.52, metrics

    # Skor Keyakinan Komposit
    cool_penalty = min(0.60, cool_ratio * 2.0)
    if candidate in ("cand_2", "cand_3"):
        line_penalty = min(0.40, max(0.0, line_density - 2.5) * 0.10)
    else:
        line_penalty = min(0.30, max(0.0, line_density - 0.30) * 1.5) if mucosal_ratio < 0.70 else 0.0

    confidence = float(mucosal_ratio * (1.0 - cool_penalty) * (1.0 - line_penalty))
    confidence = max(0.0, min(1.0, confidence))

    if confidence >= 0.55:
        return DomainDecision.ACCEPT, "ACCEPT", round(confidence, 2), metrics

    return DomainDecision.UNCERTAIN, "G10_confidence", round(confidence, 2), metrics

def run_b4_comparison() -> List[Dict[str, Any]]:
    print("\n" + "="*70)
    print("[B4] Menjalankan Evaluasi 3 Kandidat Konfigurasi pada Seluruh Data Calib")
    print("="*70)

    candidates = ["baseline", "cand_1", "cand_2", "cand_3"]
    summary_results = []

    all_calib_imgs = []
    for side, groups in [("positive", POSITIVE_GROUPS), ("negative", NEGATIVE_GROUPS)]:
        for grp in groups:
            p_dir = CALIB_DATA_ROOT / side / grp / "calib"
            if not p_dir.exists():
                continue
            for img_file in sorted(p_dir.iterdir()):
                if img_file.suffix.lower() not in IMAGE_EXTENSIONS:
                    continue
                try:
                    img = safe_open_image(img_file)
                    all_calib_imgs.append((side, grp, img_file.name, img))
                except Exception as e:
                    print(f"  [ERROR] {img_file.name}: {e}")

    print(f"  Total gambar calib terbaca: {len(all_calib_imgs)}")

    for cand in candidates:
        stats = {
            "candidate": cand,
            "pos_total": 0,
            "pos_accept": 0,
            "pos_uncertain": 0,
            "pos_reject": 0,
            "pos_frr": 0.0,
            "neg_main_total": 0,    # Tanpa ileum
            "neg_main_reject": 0,
            "neg_main_uncertain": 0,
            "neg_main_accept": 0,
            "neg_main_far": 0.0,
            "ileum_total": 0,
            "ileum_accept": 0,
            "ileum_reject": 0,
        }

        grp_breakdown = {}

        for side, grp, fname, img in all_calib_imgs:
            dec, gate, conf, metrics = evaluate_candidate_gate(img, cand)

            if grp not in grp_breakdown:
                grp_breakdown[grp] = {"n": 0, "accept": 0, "uncertain": 0, "reject": 0}
            grp_breakdown[grp]["n"] += 1
            if dec == DomainDecision.ACCEPT:
                grp_breakdown[grp]["accept"] += 1
            elif dec == DomainDecision.UNCERTAIN:
                grp_breakdown[grp]["uncertain"] += 1
            else:
                grp_breakdown[grp]["reject"] += 1

            if side == "positive":
                stats["pos_total"] += 1
                if dec == DomainDecision.ACCEPT:
                    stats["pos_accept"] += 1
                elif dec == DomainDecision.UNCERTAIN:
                    stats["pos_uncertain"] += 1
                else:
                    stats["pos_reject"] += 1
            else:
                if grp == "endoskopi_non_kolon":
                    stats["ileum_total"] += 1
                    if dec == DomainDecision.ACCEPT:
                        stats["ileum_accept"] += 1
                    else:
                        stats["ileum_reject"] += 1
                else:
                    stats["neg_main_total"] += 1
                    if dec == DomainDecision.ACCEPT:
                        stats["neg_main_accept"] += 1
                    elif dec == DomainDecision.UNCERTAIN:
                        stats["neg_main_uncertain"] += 1
                    else:
                        stats["neg_main_reject"] += 1

        stats["pos_frr"] = round(float(stats["pos_reject"] + stats["pos_uncertain"]) / stats["pos_total"] * 100.0, 1) if stats["pos_total"] > 0 else 0.0
        stats["neg_main_far"] = round(float(stats["neg_main_accept"]) / stats["neg_main_total"] * 100.0, 1) if stats["neg_main_total"] > 0 else 0.0
        stats["breakdown"] = grp_breakdown
        summary_results.append(stats)

        print(f"\n  === KANDIDAT: {cand.upper()} ===")
        print(f"    Positif (n={stats['pos_total']}) : ACCEPT={stats['pos_accept']}, UNCERTAIN={stats['pos_uncertain']}, REJECT={stats['pos_reject']} | FRR = {stats['pos_frr']}%")
        print(f"    Negatif Utama (n={stats['neg_main_total']}) : REJECT={stats['neg_main_reject']}, UNCERTAIN={stats['neg_main_uncertain']}, ACCEPT={stats['neg_main_accept']} | FAR = {stats['neg_main_far']}%")
        print(f"    Ileum (n={stats['ileum_total']}) : ACCEPT={stats['ileum_accept']}, REJECT={stats['ileum_reject']} (dilaporkan terpisah)")

        for grp, cnts in grp_breakdown.items():
            mark = " [n<10: TIDAK DAPAT DISIMPULKAN]" if cnts["n"] < 10 else ""
            print(f"      - {grp:<20} (n={cnts['n']:>2}): ACCEPT={cnts['accept']:>2}, UNC={cnts['uncertain']:>2}, REJ={cnts['reject']:>2}{mark}")

    # Simpan perbandingan CSV
    csv_rows = []
    for s in summary_results:
        row = {
            "candidate": s["candidate"],
            "pos_total": s["pos_total"],
            "pos_accept": s["pos_accept"],
            "pos_uncertain": s["pos_uncertain"],
            "pos_reject": s["pos_reject"],
            "pos_frr_pct": s["pos_frr"],
            "neg_main_total": s["neg_main_total"],
            "neg_main_reject": s["neg_main_reject"],
            "neg_main_uncertain": s["neg_main_uncertain"],
            "neg_main_accept": s["neg_main_accept"],
            "neg_main_far_pct": s["neg_main_far"],
            "ileum_total": s["ileum_total"],
            "ileum_accept": s["ileum_accept"],
        }
        csv_rows.append(row)

    csv_path = OUTPUT_DIR / "b4_candidates_comparison.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(csv_rows[0].keys()))
        writer.writeheader()
        writer.writerows(csv_rows)
    print(f"\n  â†’ Ringkasan kandidat disimpan ke: {csv_path}")

    return summary_results

# ---------------------------------------------------------------------------
# Main Runner
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    print("="*70)
    print("EXPERIMENT DOMAIN GATE â€” FASE B (READ-ONLY CALIB DATA)")
    print("="*70)

    # B0.2
    run_b0_regression_experiment()

    # B1
    run_b1_g5_analysis()

    # B2
    run_b2_special_images_analysis()

    # B4
    run_b4_comparison()

    print("\n" + "="*70)
    print("SEMUA EKSPERIMEN FASE B SELESAI DENGAN SUKSES!")
    print("="*70)

