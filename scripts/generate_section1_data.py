"""
generate_section1_data.py â€” Menghasilkan Data Lengkap untuk Dokumen 01_tindak_lanjut_fase_b.md
=============================================================================================
1.1 Rincian perpindahan keputusan Baseline vs Kandidat 2 (per-image breakdown).
1.2 Sensitivitas ambang G5 (line_density 6..16) pada norm 256 dan norm 512.
1.3 Koreksi korelasi resolusi per kelompok positif dan negatif (Pearson, Spearman, 95% CI).
1.4 Wilson score 95% confidence interval untuk FRR dan FAR.
1.5 Grayscale: simpan mask, overlay, dan Grad-CAM heatmap images (22) dan (23).
"""

from __future__ import annotations

import csv
import io
import math
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import cv2
import numpy as np
import scipy.stats as stats
import torch
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "Backend"))

from ai.config.model_config import MODEL_CONFIG
from ai.inference.domain_validator import DomainDecision
from ai.inference.gradcam import generate_gradcam
from ai.inference.pipeline import _heatmap_image, _DEFAULT_MODEL_SERVICE
from ai.inference.postprocessing import measure_mask, postprocess_mask, resize_binary_mask
from ai.inference.preprocessing import prepare_image
from ai.inference.segmentation import predict
from scripts.experiment_domain_gate import evaluate_candidate_gate, safe_open_image

CALIB_ROOT = PROJECT_ROOT / "calibration_data"
OUTPUT_DIR = PROJECT_ROOT / "scripts" / "output"
GRAYSCALE_DIR = OUTPUT_DIR / "grayscale_test"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
GRAYSCALE_DIR.mkdir(parents=True, exist_ok=True)

POSITIVE_GROUPS = ["kvasir", "cvc_clinicdb", "cvc_colondb", "etis", "bkai", "hyperkvasir", "in_vivo_blur"]
NEGATIVE_GROUPS = ["makanan", "merah_organik", "orang_ruangan", "dokumen_screenshot", "medis_lain", "endoskopi_non_kolon"]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

# ---------------------------------------------------------------------------
# 1. Muat seluruh calib images
# ---------------------------------------------------------------------------
print("[1] Memuat seluruh citra calib...")
all_images = []

for side, groups in [("positive", POSITIVE_GROUPS), ("negative", NEGATIVE_GROUPS)]:
    for grp in groups:
        p_dir = CALIB_ROOT / side / grp / "calib"
        if not p_dir.exists():
            continue
        abs_p = str(p_dir.resolve())
        ext_p = "\\\\?\\" + abs_p if os.name == "nt" and len(abs_p) >= 240 else abs_p
        
        file_list = []
        for entry in os.scandir(ext_p):
            if entry.is_file():
                ext = Path(entry.name).suffix.lower()
                if ext in IMAGE_EXTENSIONS:
                    file_list.append(entry.name)
        file_list.sort()
        
        for fname in file_list:
            full_p = p_dir / fname
            try:
                img = safe_open_image(full_p)
                all_images.append({
                    "side": side,
                    "group": grp,
                    "filename": fname,
                    "path": full_p,
                    "img": img,
                    "width": img.size[0],
                    "height": img.size[1],
                    "min_dim": min(img.size),
                    "total_pixels": img.size[0] * img.size[1],
                })
            except Exception as e:
                print(f"  [ERROR] {grp}/{fname}: {e}")

print(f"  Total citra calib terbaca: {len(all_images)} (Positif: {len([x for x in all_images if x['side']=='positive'])}, Negatif: {len([x for x in all_images if x['side']=='negative'])})")

# ---------------------------------------------------------------------------
# 1.1 Rincian Perpindahan Keputusan Baseline vs Kandidat 2
# ---------------------------------------------------------------------------
print("\n[1.1] Menghitung rincian perpindahan keputusan Baseline vs Kandidat 2...")
decision_diffs = []

for item in all_images:
    b_dec, b_gate, b_conf, b_m = evaluate_candidate_gate(item["img"], "baseline")
    c_dec, c_gate, c_conf, c_m = evaluate_candidate_gate(item["img"], "cand_2")
    
    if b_dec != c_dec:
        diff_entry = {
            "side": item["side"],
            "group": item["group"],
            "filename": item["filename"],
            "dimensions": f"{item['width']}x{item['height']}",
            "base_decision": b_dec.value,
            "base_gate": b_gate,
            "cand2_decision": c_dec.value,
            "cand2_gate": c_gate,
            "cand2_conf": c_conf,
            "cool_ratio": round(c_m.get("cool_ratio", 0), 4),
            "mucosal_ratio": round(c_m.get("mucosal_ratio", 0), 4),
            "line_density_orig": round(b_m.get("line_density", 0), 2),
            "line_density_norm256": round(c_m.get("line_density", 0), 2),
            "mean_chroma": round(c_m.get("mean_chroma", 0), 1),
            "mean_saturation": round(c_m.get("mean_saturation", 0), 2),
        }
        # Mechanism explanation
        if b_gate == "G5_line_warm" and c_dec == DomainDecision.ACCEPT:
            mech = "Normalisasi G5 (skala 256) menurunkan line_density ke bawah 8.35, lolos ke ACCEPT"
        elif b_gate == "G4_chroma" and c_dec == DomainDecision.UNCERTAIN:
            mech = "Perlakuan G4 dialihkan dari Hard REJECT ke UNCERTAIN edukatif"
        elif b_dec == DomainDecision.REJECT and c_dec == DomainDecision.UNCERTAIN:
            mech = "Soft penalty G5b/Confidence menaikkan status dari Reject ke Uncertain"
        else:
            mech = f"Perubahan ambang ({b_gate} -> {c_gate})"
        diff_entry["mechanism"] = mech
        decision_diffs.append(diff_entry)

csv_diff_path = OUTPUT_DIR / "b1_1_decision_differences.csv"
with open(csv_diff_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(decision_diffs[0].keys()))
    writer.writeheader()
    writer.writerows(decision_diffs)
print(f"  â†’ Total citra berpindah keputusan: {len(decision_diffs)} berkas. Disimpan ke: {csv_diff_path}")

# ---------------------------------------------------------------------------
# 1.2 Sensitivitas Ambang G5 (line_density 6..16)
# ---------------------------------------------------------------------------
print("\n[1.2] Menghitung sweep sensitivitas ambang G5 (6..16) pada norm 256 dan 512...")

def evaluate_custom_g5(img: Image.Image, norm_scale: int, g5_threshold: float, g4_uncertain: bool = True) -> DomainDecision:
    w, h = img.size
    min_dim = min(w, h)
    if w < 150 or h < 150 or max(w/h, h/w) > 2.8:
        return DomainDecision.REJECT
    rgb = np.asarray(img, dtype=np.uint8)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    
    active_mask = gray > 18
    active_pixels = int(np.sum(active_mask))
    if active_pixels < (w * h * 0.12):
        return DomainDecision.REJECT

    h_chan, s_chan, v_chan = hsv[:,:,0], hsv[:,:,1], hsv[:,:,2]
    a_chan, b_chan = lab[:,:,1], lab[:,:,2]
    
    mean_v = float(np.mean(v_chan[active_mask])) / 255.0
    std_v = float(np.std(v_chan[active_mask]))
    mean_s = float(np.mean(s_chan[active_mask])) / 255.0
    a_dev = a_chan[active_mask].astype(np.float32) - 128.0
    b_dev = b_chan[active_mask].astype(np.float32) - 128.0
    mean_chroma = float(np.mean(np.sqrt(a_dev**2 + b_dev**2)))

    warm_hue_mask = ((h_chan <= 22) | (h_chan >= 160)) & (s_chan >= 28) & (v_chan >= 28)
    lab_mucosal_mask = (a_chan >= 134) & (b_chan >= 130)
    mucosal_mask = (warm_hue_mask | lab_mucosal_mask) & active_mask
    mucosal_ratio = float(np.sum(mucosal_mask)) / active_pixels

    cool_mask = ((h_chan >= 36) & (h_chan <= 140)) & (s_chan >= 35) & (v_chan >= 30) & active_mask
    cool_ratio = float(np.sum(cool_mask)) / active_pixels

    glint_mask = (v_chan >= 240) & (s_chan <= 45) & active_mask
    glint_ratio = float(np.sum(glint_mask)) / active_pixels

    # G5 normalized
    scale = float(norm_scale) / float(min_dim)
    w_n = max(1, int(round(w * scale)))
    h_n = max(1, int(round(h * scale)))
    interp = cv2.INTER_AREA if scale < 1.0 else cv2.INTER_LINEAR
    gray_n = cv2.resize(gray, (w_n, h_n), interpolation=interp)
    edges = cv2.Canny(gray_n, 50, 150)
    min_len = 25 if norm_scale == 256 else 50
    gap = 8 if norm_scale == 256 else 15
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=40, minLineLength=min_len, maxLineGap=gap)
    cnt = len(lines) if lines is not None else 0
    line_density = (cnt * float(min_len)) / (2.0 * (w_n + h_n))

    # G3
    if cool_ratio > 0.40:
        return DomainDecision.REJECT
    # G4
    if mean_chroma < 10.0 or mean_s < 0.10:
        return DomainDecision.UNCERTAIN if g4_uncertain else DomainDecision.REJECT
    # G5a
    if line_density > 1.0 and mucosal_ratio < 0.55:
        return DomainDecision.REJECT
    # G5b
    if line_density > g5_threshold and mucosal_ratio > 0.55:
        return DomainDecision.REJECT
    # G6
    if mucosal_ratio < 0.32:
        return DomainDecision.REJECT
    # G7
    if std_v < 8.5 and glint_ratio < 0.0001:
        return DomainDecision.UNCERTAIN
    # G8
    if mean_v < 0.18:
        return DomainDecision.UNCERTAIN
    # G9
    if mucosal_ratio < 0.55:
        return DomainDecision.UNCERTAIN
    # Confidence
    cool_penalty = min(0.60, cool_ratio * 2.0)
    line_penalty = min(0.40, max(0.0, line_density - 2.5) * 0.10)
    confidence = float(mucosal_ratio * (1.0 - cool_penalty) * (1.0 - line_penalty))
    if confidence >= 0.55:
        return DomainDecision.ACCEPT
    return DomainDecision.UNCERTAIN

sensitivity_results = []
for scale in [256, 512]:
    for th in range(6, 17):
        pos_total = 0
        pos_rej = 0
        pos_unc = 0
        pos_acc = 0
        neg_main_total = 0
        neg_main_acc = 0
        neg_main_rej = 0
        neg_main_unc = 0
        
        for item in all_images:
            dec = evaluate_custom_g5(item["img"], scale, float(th), g4_uncertain=True)
            if item["side"] == "positive":
                pos_total += 1
                if dec == DomainDecision.ACCEPT:
                    pos_acc += 1
                elif dec == DomainDecision.UNCERTAIN:
                    pos_unc += 1
                else:
                    pos_rej += 1
            elif item["group"] != "endoskopi_non_kolon":
                neg_main_total += 1
                if dec == DomainDecision.ACCEPT:
                    neg_main_acc += 1
                elif dec == DomainDecision.UNCERTAIN:
                    neg_main_unc += 1
                else:
                    neg_main_rej += 1
        
        frr = (pos_rej + pos_unc) / pos_total * 100.0
        far = neg_main_acc / neg_main_total * 100.0
        sensitivity_results.append({
            "norm_scale": scale,
            "threshold": th,
            "pos_accept": pos_acc,
            "pos_uncertain": pos_unc,
            "pos_reject": pos_rej,
            "pos_frr_pct": round(frr, 2),
            "neg_main_accept": neg_main_acc,
            "neg_main_uncertain": neg_main_unc,
            "neg_main_reject": neg_main_rej,
            "neg_main_far_pct": round(far, 2),
        })

csv_sens_path = OUTPUT_DIR / "b1_2_g5_sensitivity_sweep.csv"
with open(csv_sens_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(sensitivity_results[0].keys()))
    writer.writeheader()
    writer.writerows(sensitivity_results)
print(f"  â†’ Sensitivitas G5 disimpan ke: {csv_sens_path}")

# ---------------------------------------------------------------------------
# 1.3 Koreksi Analisis Korelasi Resolusi
# ---------------------------------------------------------------------------
print("\n[1.3] Menghitung korelasi resolusi terpisah (Positif vs Negatif)...")

def calc_corr(x, y):
    n = len(x)
    r, p = stats.pearsonr(x, y)
    rho, sp = stats.spearmanr(x, y)
    # Fisher z-transformation for 95% CI of Pearson r
    z = np.arctanh(r)
    se = 1.0 / np.sqrt(n - 3)
    z_low, z_high = z - 1.96 * se, z + 1.96 * se
    r_low, r_high = np.tanh(z_low), np.tanh(z_high)
    return {
        "n": n,
        "pearson_r": round(r, 4),
        "pearson_ci95": f"[{r_low:.4f}, {r_high:.4f}]",
        "pearson_p": f"{p:.2e}",
        "spearman_rho": round(rho, 4),
        "spearman_p": f"{sp:.2e}",
    }

# Baca data G5 dari b1_g5_resolution_analysis.csv
g5_df_rows = []
with open(OUTPUT_DIR / "b1_g5_resolution_analysis.csv", "r", encoding="utf-8") as f:
    for row in csv.DictReader(f):
        g5_df_rows.append(row)

pos_subset = [r for r in g5_df_rows if r["side"] == "positive"]
neg_subset = [r for r in g5_df_rows if r["side"] == "negative"]

corr_records = []
for subset_name, subset in [("Positif Saja", pos_subset), ("Negatif Saja", neg_subset)]:
    min_dims = [float(r["min_dim"]) for r in subset]
    log_pixels = [np.log(float(r["width"]) * float(r["height"])) for r in subset]
    
    for metric_name in ["ld_original", "ld_norm_256", "ld_norm_512", "ld_fractional"]:
        vals = [float(r[metric_name]) for r in subset]
        # vs min_dim
        c_dim = calc_corr(min_dims, vals)
        c_dim["subset"] = subset_name
        c_dim["metric"] = metric_name
        c_dim["res_type"] = "min_dimension"
        corr_records.append(c_dim)
        # vs log_pixels
        c_log = calc_corr(log_pixels, vals)
        c_log["subset"] = subset_name
        c_log["metric"] = metric_name
        c_log["res_type"] = "log_total_pixels"
        corr_records.append(c_log)

csv_corr_path = OUTPUT_DIR / "b1_3_resolution_correlations.csv"
with open(csv_corr_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(corr_records[0].keys()))
    writer.writeheader()
    writer.writerows(corr_records)
print(f"  â†’ Koreksi korelasi resolusi disimpan ke: {csv_corr_path}")

# ---------------------------------------------------------------------------
# 1.4 Wilson Score Interval 95% untuk FRR dan FAR
# ---------------------------------------------------------------------------
print("\n[1.4] Menghitung Wilson Score 95% Confidence Interval...")

def wilson_ci(k: int, n: int, confidence: float = 0.95) -> Tuple[float, float, float]:
    if n == 0:
        return 0.0, 0.0, 0.0
    p_hat = float(k) / float(n)
    z = stats.norm.ppf(1.0 - (1.0 - confidence) / 2.0)
    denom = 1.0 + (z**2) / n
    center = (p_hat + (z**2) / (2.0 * n)) / denom
    margin = (z * np.sqrt((p_hat * (1.0 - p_hat) / n) + ((z**2) / (4.0 * (n**2))))) / denom
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    return round(p_hat * 100.0, 2), round(lower * 100.0, 2), round(upper * 100.0, 2)

# Hitung Wilson CI untuk Baseline vs Cand 1 vs Cand 2 vs Cand 3
candidates_summary = [
    ("Baseline", 11, 128, 7, 55),
    ("Kandidat 1", 6, 128, 7, 55),
    ("Kandidat 2", 5, 128, 7, 55),  # 2 reject + 3 uncertain = 5 non-accept
    ("Kandidat 3", 8, 128, 7, 55),  # 4 reject + 4 uncertain = 8 non-accept
]

wilson_records = []
for c_name, pos_fail, pos_n, neg_fail, neg_n in candidates_summary:
    frr, frr_l, frr_u = wilson_ci(pos_fail, pos_n)
    far, far_l, far_u = wilson_ci(neg_fail, neg_n)
    wilson_records.append({
        "candidate": c_name,
        "pos_n": pos_n,
        "pos_failures": pos_fail,
        "frr_pct": frr,
        "frr_ci95": f"[{frr_l}%, {frr_u}%]",
        "neg_main_n": neg_n,
        "neg_main_failures": neg_fail,
        "far_pct": far,
        "far_ci95": f"[{far_l}%, {far_u}%]",
    })

csv_wilson_path = OUTPUT_DIR / "b1_4_wilson_ci.csv"
with open(csv_wilson_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(wilson_records[0].keys()))
    writer.writeheader()
    writer.writerows(wilson_records)
print(f"  â†’ Wilson Score CI disimpan ke: {csv_wilson_path}")

# ---------------------------------------------------------------------------
# 1.5 Grayscale: Visualisasi Mask, Overlay, & Grad-CAM Heatmap
# ---------------------------------------------------------------------------
print("\n[1.5] Menghasilkan mask biner, overlay, dan Grad-CAM heatmap untuk citra grayscale...")

for g_fname in ["images (22).jpg", "images (23).jpg"]:
    g_p = CALIB_ROOT / "in_vivo_blur" / "calib" / g_fname
    if not g_p.exists():
        continue
    img_g = safe_open_image(g_p)
    w, h = img_g.size
    
    # 1. Model inference
    seg = predict(img_g, config=MODEL_CONFIG)
    post_512 = postprocess_mask(seg.binary_mask[0, 0].numpy(), MODEL_CONFIG)
    mask_g = resize_binary_mask(post_512, w, h)
    
    # 2. Grad-CAM
    grad = generate_gradcam(
        prepare_image(img_g, MODEL_CONFIG),
        original_image=img_g,
        config=MODEL_CONFIG,
        model_service=_DEFAULT_MODEL_SERVICE,
    )
    heat_img = _heatmap_image(grad.heatmap).resize((w, h), Image.BILINEAR)
    
    # 3. Simpan artefak
    mask_out = GRAYSCALE_DIR / f"mask_{g_fname.replace('.jpg', '.png')}"
    overlay_out = GRAYSCALE_DIR / f"overlay_{g_fname}"
    heatmap_out = GRAYSCALE_DIR / f"gradcam_{g_fname.replace('.jpg', '.png')}"
    
    # Mask Image
    Image.fromarray((mask_g * 255).astype(np.uint8), mode="L").save(mask_out)
    
    # Overlay Image
    arr_orig = np.array(img_g).copy()
    arr_orig[mask_g > 0, 0] = np.clip(arr_orig[mask_g > 0, 0] * 0.5 + 255 * 0.5, 0, 255)
    Image.fromarray(arr_orig).save(overlay_out)
    
    # Heatmap Image
    heat_img.save(heatmap_out)
    
    print(f"  [{g_fname}] Disimpan: {mask_out.name}, {overlay_out.name}, {heatmap_out.name}")
    torch.cuda.empty_cache()

print("\n" + "=" * 80)
print("SELURUH DATA BAGIAN 1 BERHASIL DIHASILKAN!")
print("=" * 80)


