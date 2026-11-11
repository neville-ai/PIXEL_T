"""
verify_b0_strong.py â€” Verifikasi Komparasi Lanjutan B0: Kode Sekarang vs Baseline HEAD
=====================================================================================
Menguji minimal 2 citra per sumber (6 sumber = 12 citra) dari folder calib:
- Dice score
- Selisih piksel mask biner
- Selisih absolut maksimum dan rata-rata peta probabilitas (probability map)
- Selisih absolut maksimum heatmap Grad-CAM
"""

from __future__ import annotations

import csv
import io
import os
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "Backend"))

from ai.config.model_config import MODEL_CONFIG
from ai.inference.gradcam import generate_gradcam
from ai.inference.pipeline import run_pipeline, _DEFAULT_MODEL_SERVICE, _heatmap_image
from ai.inference.postprocessing import postprocess_mask, resize_binary_mask
from ai.inference.preprocessing import prepare_image
from ai.inference.segmentation import predict

CALIB_ROOT = PROJECT_ROOT / "calibration_data" / "positive"
OUTPUT_DIR = PROJECT_ROOT / "scripts" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

SAMPLES = [
    ("cvc_clinicdb", ["1.png", "10.png"]),
    ("cvc_colondb", ["1.png", "10.png"]),
    ("kvasir", ["cju0s690hkp960855tjuaqvv0.jpg", "cju1b75x63ddl0799sdp0i2j3.jpg"]),
    ("bkai", ["02fa602bb3c7abacdbd7e6afd56ea7bc.jpeg", "0a0317371a966bf4b3466463a3c64db1.jpeg"]),
    ("etis", ["1.png", "10.png"]),
    ("hyperkvasir", ["cju0qoxqj9q6s0835b43399p4.jpg", "cju0roawf938n0801wzhr3ehb.jpg"]),
]

def safe_read(p: Path) -> bytes:
    abs_s = str(p.resolve())
    if len(abs_s) >= 240 and os.name == "nt" and not abs_s.startswith("\\\\?\\"):
        abs_s = "\\\\?\\" + abs_s
    with open(abs_s, "rb") as f:
        return f.read()

results = []
print("=" * 80)
print("VERIFIKASI REGRESI B0 LANJUTAN: SEKARANG VS HEAD (PROB MAP, DICE, GRAD-CAM)")
print("=" * 80)

for grp, fnames in SAMPLES:
    for fname in fnames:
        p = CALIB_ROOT / grp / "calib" / fname
        if not p.exists():
            print(f"[SKIP] {p} tidak ditemukan")
            continue
        raw = safe_read(p)

        # 1. Pipeline sekarang
        curr_res = run_pipeline(raw, MODEL_CONFIG, analysis_id=f"curr_{grp}_{fname}")
        curr_mask = np.array(Image.open(io.BytesIO(curr_res.binary_mask_png))) > 0
        curr_grad_img = np.array(Image.open(io.BytesIO(curr_res.gradcam_heatmap_png)))

        # 2. Pipeline HEAD (panggilan langsung komponen dasar inferensi tanpa penambahan)
        with Image.open(io.BytesIO(raw)) as dec:
            orig = dec.convert("RGB")
            w, h = orig.size
        seg_head = predict(orig, config=MODEL_CONFIG)
        post_512 = postprocess_mask(seg_head.binary_mask[0, 0].numpy(), MODEL_CONFIG)
        head_mask = resize_binary_mask(post_512, w, h) > 0

        # Grad-CAM HEAD
        gradcam_head = generate_gradcam(
            prepare_image(orig, MODEL_CONFIG),
            original_image=orig,
            config=MODEL_CONFIG,
            model_service=_DEFAULT_MODEL_SERVICE,
        )
        head_grad_img = np.array(_heatmap_image(gradcam_head.heatmap))

        # Komparasi Prob Map
        prob_diff_max = float(np.max(np.abs(seg_head.probability_map[0, 0].numpy() - seg_head.probability_map[0, 0].numpy())))
        prob_diff_mean = float(np.mean(np.abs(seg_head.probability_map[0, 0].numpy() - seg_head.probability_map[0, 0].numpy())))

        diff_pixels = int(np.sum(curr_mask != head_mask))
        inter = int(np.sum(curr_mask & head_mask))
        dice = (2.0 * inter) / (np.sum(curr_mask) + np.sum(head_mask)) if (np.sum(curr_mask) + np.sum(head_mask)) > 0 else 1.0

        grad_diff_max = int(np.max(np.abs(curr_grad_img.astype(np.int32) - head_grad_img.astype(np.int32))))

        print(f"[{grp:<13}] {fname:<36} | Mask Diff: {diff_pixels:<3} px | Dice: {dice:.6f} | Grad Diff: {grad_diff_max}")
        results.append({
            "group": grp,
            "filename": fname,
            "dimensions": f"{w}x{h}",
            "mask_diff_pixels": diff_pixels,
            "dice_score": round(dice, 6),
            "prob_map_max_diff": prob_diff_max,
            "prob_map_mean_diff": prob_diff_mean,
            "gradcam_max_diff": grad_diff_max,
            "is_identical": (diff_pixels == 0 and grad_diff_max == 0),
        })
        torch.cuda.empty_cache()

csv_out = OUTPUT_DIR / "b0_strong_regression.csv"
with open(csv_out, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
    writer.writeheader()
    writer.writerows(results)
print(f"\nâ†’ Hasil disimpan ke: {csv_out}")

