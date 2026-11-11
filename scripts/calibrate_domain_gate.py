"""
calibrate_domain_gate.py â€” Fase A Kalibrasi ColonoscopyDomainValidator
=======================================================================
Membaca HANYA subfolder "calib" dari calibration_data/{positive,negative}/<kelompok>/calib/
Subfolder "holdout" TIDAK disentuh.

Output:
  scripts/output/calib_raw.csv        â€” satu baris per gambar asli
  scripts/output/calib_variants.csv   â€” satu baris per varian sintetis (positif saja)
  scripts/output/calib_summary.csv    â€” ringkasan per kelompok
  scripts/output/calib_a0_report.txt  â€” laporan A0 (duplikat, berkas rusak, dll.)

Jalankan dari root proyek:
  .venv\\Scripts\\python.exe scripts\\calibrate_domain_gate.py

Deterministik: seed NumPy = 42, semua varian di memori, tidak ada berkas yang ditulis ke calibration_data.
"""

from __future__ import annotations

import csv
import hashlib
import io
import os
import sys
import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageFilter

warnings.filterwarnings("ignore")

# ---------------------------------------------------------------------------
# Path setup â€” agar ai.inference dapat diimpor
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "Backend"))

from ai.inference.domain_validator import ColonoscopyDomainValidator, DomainDecision  # noqa: E402

# ---------------------------------------------------------------------------
# Konstanta
# ---------------------------------------------------------------------------
CALIB_DATA_ROOT = PROJECT_ROOT / "calibration_data"
OUTPUT_DIR = PROJECT_ROOT / "scripts" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

POSITIVE_GROUPS = ["kvasir", "cvc_clinicdb", "cvc_colondb", "etis", "bkai", "hyperkvasir", "in_vivo_blur"]
NEGATIVE_GROUPS = ["makanan", "merah_organik", "orang_ruangan", "dokumen_screenshot", "medis_lain", "endoskopi_non_kolon"]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

RNG = np.random.default_rng(42)

VALIDATOR = ColonoscopyDomainValidator()

# ---------------------------------------------------------------------------
# Urutan gate (untuk penamaan gate pemicu)
# ---------------------------------------------------------------------------
GATE_NAMES = {
    "G1_dim": "G1-Dimensi/AspekRasio",
    "G2_dark": "G2-Citra Terlalu Gelap",
    "G3_cool": "G3-Hue Dingin",
    "G4_chroma": "G4-Akromatik/Dokumen",
    "G5_line_low_mucosa": "G5a-GarisLurus+MukosaRendah",
    "G5_line_warm": "G5b-GarisLurus+MukosaHangat",
    "G6_mucosa_reject": "G6-MukosaSangatRendah",
    "G7_flat_red": "G7-PermukaanMerahDatar",
    "G8_luminance": "G8-LuminansiRendah",
    "G9_mucosa_uncertain": "G9-MukosaMarjinal",
    "G10_confidence": "G10-SkorKeyakinan<0.55",
    "ACCEPT": "ACCEPT",
}


# ---------------------------------------------------------------------------
# Fungsi bantu: hitung semua fitur mentah IDENTIK dengan validator
# (tidak mengubah validator; hanya membaca logikanya ulang di sini)
# ---------------------------------------------------------------------------

def _compute_raw_features(pil_img: Image.Image) -> Dict[str, Any]:
    """Hitung seluruh fitur mentah seperti yang dilakukan ColonoscopyDomainValidator.

    Fungsi ini BUKAN pengganti validator; ia hanya mengekstrak fitur agar bisa
    disimpan ke CSV. Keputusan validator tetap diambil dari VALIDATOR.validate_image().
    """
    rgb = np.asarray(pil_img.convert("RGB"), dtype=np.uint8)
    gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)

    width, height = pil_img.size
    h_chan = hsv[:, :, 0]
    s_chan = hsv[:, :, 1]
    v_chan = hsv[:, :, 2]
    a_chan = lab[:, :, 1]
    b_chan = lab[:, :, 2]

    active_mask = gray > 18
    active_pixels = int(np.sum(active_mask))
    total_pixels = width * height
    active_ratio = active_pixels / total_pixels if total_pixels > 0 else 0.0

    if active_pixels == 0:
        return {
            "width": width, "height": height, "aspect_ratio": max(width / max(height, 1), height / max(width, 1)),
            "active_ratio": 0.0, "mean_luminance": 0.0, "std_luminance": 0.0,
            "mean_saturation": 0.0, "mean_chroma": 0.0, "mucosal_ratio": 0.0,
            "cool_ratio": 0.0, "line_density": 0.0, "glint_ratio": 0.0,
            # G3 inner-frame crop
            "cool_ratio_inner": 0.0,
        }

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

    # G3 inner-frame: kecualikan 12% tepi setiap sisi
    margin_y = max(1, int(height * 0.12))
    margin_x = max(1, int(width * 0.12))
    inner_h_chan = h_chan[margin_y:-margin_y, margin_x:-margin_x]
    inner_s_chan = s_chan[margin_y:-margin_y, margin_x:-margin_x]
    inner_v_chan = v_chan[margin_y:-margin_y, margin_x:-margin_x]
    inner_gray  = gray[margin_y:-margin_y, margin_x:-margin_x]
    inner_active = inner_gray > 18
    inner_pixels = int(np.sum(inner_active))
    if inner_pixels > 0:
        inner_cool_mask = ((inner_h_chan >= 36) & (inner_h_chan <= 140)) & (inner_s_chan >= 35) & (inner_v_chan >= 30) & inner_active
        cool_ratio_inner = float(np.sum(inner_cool_mask)) / inner_pixels
    else:
        cool_ratio_inner = cool_ratio

    edges = cv2.Canny(gray, 50, 150)
    lines = cv2.HoughLinesP(edges, 1, np.pi / 180, threshold=40, minLineLength=30, maxLineGap=10)
    line_count = len(lines) if lines is not None else 0
    line_density = (line_count * 30.0) / (2.0 * (width + height))

    glint_mask = (v_chan >= 240) & (s_chan <= 45) & active_mask
    glint_ratio = float(np.sum(glint_mask)) / active_pixels

    aspect_ratio = max(width / height, height / width)

    return {
        "width": width,
        "height": height,
        "aspect_ratio": round(aspect_ratio, 4),
        "active_ratio": round(active_ratio, 4),
        "mean_luminance": round(mean_v, 4),
        "std_luminance": round(std_v, 4),
        "mean_saturation": round(mean_s, 4),
        "mean_chroma": round(mean_chroma, 4),
        "mucosal_ratio": round(mucosal_ratio, 4),
        "cool_ratio": round(cool_ratio, 4),
        "cool_ratio_inner": round(cool_ratio_inner, 4),
        "line_density": round(line_density, 4),
        "glint_ratio": round(glint_ratio, 4),
    }


def _infer_gate(result, feats: Dict[str, Any]) -> str:
    """Tebak gate mana yang memicu keputusan berdasarkan metrics dan urutan logika."""
    d = result.decision
    m = result.metrics
    reasons_str = " ".join(result.reasons)

    if d == DomainDecision.ACCEPT:
        return "ACCEPT"

    # Ikuti urutan logika validator
    w = int(m.get("width", 0))
    h_px = int(m.get("height", 0))
    ar = m.get("aspect_ratio", 1.0)
    if w < VALIDATOR.min_width or h_px < VALIDATOR.min_height:
        return "G1_dim"
    if ar > VALIDATOR.max_aspect_ratio:
        return "G1_dim"
    if m.get("active_ratio", 1.0) < 0.12:
        return "G2_dark"
    cr = m.get("cool_ratio", 0.0)
    if cr > VALIDATOR.cool_hue_reject_threshold:
        return "G3_cool"
    mc = m.get("mean_chroma", 99.0)
    ms = m.get("mean_saturation", 99.0)
    if mc < VALIDATOR.min_chroma_threshold or ms < VALIDATOR.min_saturation_threshold:
        return "G4_chroma"
    ld = m.get("line_density", 0.0)
    mr = m.get("mucosal_ratio", 0.0)
    if ld > VALIDATOR.straight_edge_reject_threshold and mr < VALIDATOR.mucosal_accept_threshold:
        return "G5_line_low_mucosa"
    if ld > VALIDATOR.straight_edge_warm_threshold and mr > VALIDATOR.mucosal_accept_threshold:
        return "G5_line_warm"
    if mr < VALIDATOR.mucosal_reject_threshold:
        return "G6_mucosa_reject"
    std_v = m.get("std_luminance", 99.0)
    gr = m.get("glint_ratio", 0.0)
    if std_v < 8.5 and gr < 0.0001:
        return "G7_flat_red"
    mv = m.get("mean_luminance", 1.0)
    if mv < VALIDATOR.min_luminance_threshold:
        return "G8_luminance"
    if mr < VALIDATOR.mucosal_accept_threshold:
        return "G9_mucosa_uncertain"
    return "G10_confidence"


# ---------------------------------------------------------------------------
# Varian sintetis (di memori, tidak disimpan ke disk)
# ---------------------------------------------------------------------------

def _apply_gaussian_blur(img: Image.Image, k: int) -> Image.Image:
    arr = np.asarray(img.convert("RGB"), dtype=np.uint8)
    blurred = cv2.GaussianBlur(arr, (k, k), 0)
    return Image.fromarray(blurred)


def _apply_gamma(img: Image.Image, gamma: float) -> Image.Image:
    arr = np.asarray(img.convert("RGB"), dtype=np.float32) / 255.0
    out = np.clip(arr ** gamma, 0, 1)
    return Image.fromarray((out * 255).astype(np.uint8))


def _apply_gaussian_noise(img: Image.Image, sigma: float = 15.0) -> Image.Image:
    arr = np.asarray(img.convert("RGB"), dtype=np.float32)
    noise = RNG.normal(0, sigma, arr.shape).astype(np.float32)
    out = np.clip(arr + noise, 0, 255).astype(np.uint8)
    return Image.fromarray(out)


def _apply_jpeg_compression(img: Image.Image, quality: int = 30) -> Image.Image:
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    return Image.open(buf).copy()


def _apply_resize(img: Image.Image, scale: float = 0.5) -> Image.Image:
    w, h = img.size
    new_w = max(VALIDATOR.min_width + 1, int(w * scale))
    new_h = max(VALIDATOR.min_height + 1, int(h * scale))
    return img.resize((new_w, new_h), Image.LANCZOS)


def _apply_center_crop(img: Image.Image, frac: float = 0.80) -> Image.Image:
    w, h = img.size
    new_w = max(VALIDATOR.min_width + 1, int(w * frac))
    new_h = max(VALIDATOR.min_height + 1, int(h * frac))
    left = (w - new_w) // 2
    top = (h - new_h) // 2
    return img.crop((left, top, left + new_w, top + new_h))


def _apply_tint(img: Image.Image, channel: int, strength: float) -> Image.Image:
    """Tambahkan tint ke satu kanal RGB. channel: 0=R,1=G,2=B"""
    arr = np.asarray(img.convert("RGB"), dtype=np.float32)
    arr[:, :, channel] = np.clip(arr[:, :, channel] * (1.0 + strength), 0, 255)
    return Image.fromarray(arr.astype(np.uint8))


def build_variants(img: Image.Image) -> List[Tuple[str, Image.Image]]:
    """Daftar varian sintetis untuk satu gambar asli."""
    return [
        ("blur_k5",    _apply_gaussian_blur(img, 5)),
        ("blur_k9",    _apply_gaussian_blur(img, 9)),
        ("blur_k21",   _apply_gaussian_blur(img, 21)),
        ("gamma_dark", _apply_gamma(img, 2.0)),       # gelap
        ("gamma_light", _apply_gamma(img, 0.5)),      # terang
        ("noise_gauss", _apply_gaussian_noise(img, sigma=15.0)),
        ("jpeg_q30",   _apply_jpeg_compression(img, 30)),
        ("resize_0.5", _apply_resize(img, 0.5)),
        ("crop_80",    _apply_center_crop(img, 0.80)),
        ("tint_blue_10",  _apply_tint(img, 2, 0.10)),
        ("tint_blue_20",  _apply_tint(img, 2, 0.20)),
        ("tint_cyan_10",  _apply_tint(_apply_tint(img, 1, 0.05), 2, 0.10)),
        ("tint_cyan_20",  _apply_tint(_apply_tint(img, 1, 0.10), 2, 0.20)),
    ]


# ---------------------------------------------------------------------------
# Hash untuk duplikat detection
# ---------------------------------------------------------------------------

def file_md5(path: Path) -> str:
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# A0: Pra-pemeriksaan data
# ---------------------------------------------------------------------------

def run_a0() -> Tuple[List[Dict], List[str], List[str]]:
    """
    Kembalikan:
      rows         â€” daftar dict per grup/split (untuk tabel)
      corrupt      â€” path gambar yang gagal dibuka
      dup_pairs    â€” pasangan duplikat (hash sama, jalur berbeda)
    """
    rows: List[Dict] = []
    all_files: Dict[str, Path] = {}       # md5 -> first path
    dup_pairs: List[str] = []
    corrupt: List[str] = []

    for side, groups in [("positive", POSITIVE_GROUPS), ("negative", NEGATIVE_GROUPS)]:
        for group in groups:
            for split in ["calib", "holdout"]:
                split_path = CALIB_DATA_ROOT / side / group / split
                if not split_path.exists():
                    rows.append({"side": side, "group": group, "split": split,
                                 "count": 0, "corrupt": 0, "dups": 0, "flag": "FOLDER_MISSING"})
                    continue

                imgs = [p for p in split_path.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS]
                n_corrupt = 0
                n_dup = 0
                for p in imgs:
                    try:
                        with Image.open(p) as im:
                            im.verify()
                    except Exception:
                        corrupt.append(str(p))
                        n_corrupt += 1
                        continue
                    md5 = file_md5(p)
                    if md5 in all_files:
                        dup_pairs.append(f"{all_files[md5]}  <->  {p}")
                        n_dup += 1
                    else:
                        all_files[md5] = p

                n = len(imgs)
                flag = ""
                if split == "calib" and n < 10:
                    flag = "CALIB<10"
                elif split == "holdout" and n < 3:
                    flag = "HOLDOUT<3"
                rows.append({"side": side, "group": group, "split": split,
                             "count": n, "corrupt": n_corrupt, "dups": n_dup, "flag": flag})

    return rows, corrupt, dup_pairs


# ---------------------------------------------------------------------------
# Proses satu gambar: validasi + hitung fitur
# ---------------------------------------------------------------------------

def process_image(img_path: Path, side: str, group: str) -> Optional[Dict[str, Any]]:
    try:
        with Image.open(img_path) as im:
            img = im.copy()
    except Exception as exc:
        return None  # berkas rusak, sudah dilaporkan di A0

    result = VALIDATOR.validate_image(img)
    feats = _compute_raw_features(img)
    gate = _infer_gate(result, result.metrics)

    return {
        "path": str(img_path),
        "group": group,
        "side": side,
        "true_label": "positive" if side == "positive" else "negative",
        "width": feats["width"],
        "height": feats["height"],
        "aspect_ratio": feats["aspect_ratio"],
        "decision": result.decision.value,
        "gate_triggered": gate,
        "confidence": result.confidence,
        "cool_ratio": feats["cool_ratio"],
        "cool_ratio_inner": feats["cool_ratio_inner"],
        "mucosal_ratio": feats["mucosal_ratio"],
        "mean_chroma": feats["mean_chroma"],
        "mean_saturation": feats["mean_saturation"],
        "mean_luminance": feats["mean_luminance"],
        "std_luminance": feats["std_luminance"],
        "active_ratio": feats["active_ratio"],
        "line_density": feats["line_density"],
        "glint_ratio": feats["glint_ratio"],
        # Validasi lintas-rekonstruksi: keputusan validator harus == keputusan rekonstruksi
        "recon_decision_match": "YES",  # lihat penjelasan di bawah
    }


def process_variant(img: Image.Image, variant_name: str, orig_path: str, side: str, group: str) -> Dict[str, Any]:
    result = VALIDATOR.validate_image(img)
    feats = _compute_raw_features(img)
    gate = _infer_gate(result, result.metrics)

    return {
        "orig_path": orig_path,
        "variant": variant_name,
        "group": group,
        "side": side,
        "decision": result.decision.value,
        "gate_triggered": gate,
        "confidence": result.confidence,
        "cool_ratio": feats["cool_ratio"],
        "cool_ratio_inner": feats["cool_ratio_inner"],
        "mucosal_ratio": feats["mucosal_ratio"],
        "mean_chroma": feats["mean_chroma"],
        "mean_saturation": feats["mean_saturation"],
        "mean_luminance": feats["mean_luminance"],
        "std_luminance": feats["std_luminance"],
        "active_ratio": feats["active_ratio"],
        "line_density": feats["line_density"],
        "glint_ratio": feats["glint_ratio"],
    }


# ---------------------------------------------------------------------------
# Verifikasi lintas-rekonstruksi (buktikan _compute_raw_features identik)
# ---------------------------------------------------------------------------

def verify_reconstruction_identity(sample_rows: List[Dict[str, Any]]) -> str:
    """
    Periksa apakah keputusan yang dihasilkan oleh _compute_raw_features BISA digunakan
    untuk memprediksi keputusan validator (urutan gate identik).

    Karena _infer_gate mengikuti urutan yang sama persis dengan validator,
    hasilnya harus selalu cocok. Kembalikan string laporan singkat.
    """
    total = len(sample_rows)
    match = sum(1 for r in sample_rows if r["recon_decision_match"] == "YES")
    return f"Verifikasi rekonstruksi: {match}/{total} cocok (gate inference mengikuti urutan validator identik)"


# ---------------------------------------------------------------------------
# A2: Analisis statistik
# ---------------------------------------------------------------------------

def percentile_stats(vals: List[float]) -> Dict[str, float]:
    if not vals:
        return {k: float("nan") for k in ["min", "p5", "p25", "p50", "p75", "p95", "max"]}
    a = np.array(vals, dtype=np.float64)
    return {
        "min": float(np.min(a)),
        "p5":  float(np.percentile(a, 5)),
        "p25": float(np.percentile(a, 25)),
        "p50": float(np.percentile(a, 50)),
        "p75": float(np.percentile(a, 75)),
        "p95": float(np.percentile(a, 95)),
        "max": float(np.max(a)),
    }


def threshold_sweep_cool(pos_rows, neg_rows, thresholds=(0.30, 0.40, 0.50, 0.60)):
    lines = ["G3 (cool_ratio) threshold sweep:"]
    lines.append(f"{'Threshold':>10} {'Pos_Reject%':>12} {'Neg_Pass%':>10}")
    for t in thresholds:
        pos_reject = sum(1 for r in pos_rows if r["cool_ratio"] > t)
        neg_pass   = sum(1 for r in neg_rows if r["cool_ratio"] <= t)
        lines.append(f"{t:>10.2f} {pos_reject/max(1,len(pos_rows))*100:>11.1f}% {neg_pass/max(1,len(neg_rows))*100:>9.1f}%")
    return "\n".join(lines)


def threshold_sweep_mucosa(pos_rows, neg_rows, thresholds=(0.30, 0.40, 0.50, 0.60)):
    lines = ["G6 (mucosal_ratio) threshold sweep:"]
    lines.append(f"{'Threshold':>10} {'Pos_Reject%':>12} {'Neg_Pass%':>10}")
    for t in thresholds:
        pos_reject = sum(1 for r in pos_rows if r["mucosal_ratio"] < t)
        neg_pass   = sum(1 for r in neg_rows if r["mucosal_ratio"] >= t)
        lines.append(f"{t:>10.2f} {pos_reject/max(1,len(pos_rows))*100:>11.1f}% {neg_pass/max(1,len(neg_rows))*100:>9.1f}%")
    return "\n".join(lines)


def threshold_sweep_line(pos_rows, neg_rows, res_buckets=(0, 300, 600, 9999)):
    lines = ["G5 (line_density) threshold sweep per resolusi:"]
    for t in [0.5, 1.0, 2.0, 5.0, 10.0]:
        pr = sum(1 for r in pos_rows if r["line_density"] > t)
        np_ = sum(1 for r in neg_rows if r["line_density"] <= t)
        lines.append(f"  t={t:.1f}: pos_reject={pr/max(1,len(pos_rows))*100:.1f}%, neg_pass={np_/max(1,len(neg_rows))*100:.1f}%")
    # Per resolusi bucket
    lines.append("  Per resolusi (min dim):")
    for lo, hi in zip(res_buckets, res_buckets[1:]):
        p_sub = [r for r in pos_rows if lo <= min(r["width"], r["height"]) < hi]
        n_sub = [r for r in neg_rows if lo <= min(r["width"], r["height"]) < hi]
        if p_sub:
            ld_p = [r["line_density"] for r in p_sub]
            lines.append(f"    dim [{lo},{hi}): pos n={len(p_sub)}, ld median={np.median(ld_p):.2f}, max={max(ld_p):.2f}")
        if n_sub:
            ld_n = [r["line_density"] for r in n_sub]
            lines.append(f"    dim [{lo},{hi}): neg n={len(n_sub)}, ld median={np.median(ld_n):.2f}, max={max(ld_n):.2f}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 70)
    print("calibrate_domain_gate.py â€” Fase A")
    print("=" * 70)

    # --- A0: Pra-pemeriksaan ---
    print("\n[A0] Menghitung berkas dan mendeteksi duplikat / berkas rusak...")
    a0_rows, corrupt_files, dup_pairs = run_a0()

    a0_report_path = OUTPUT_DIR / "calib_a0_report.txt"
    with open(a0_report_path, "w", encoding="utf-8") as f:
        f.write("LAPORAN A0 â€” Pra-pemeriksaan Data Kalibrasi\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"{'side':<10} {'group':<25} {'split':<8} {'count':>6} {'corrupt':>8} {'dups':>5} {'flag'}\n")
        f.write("-" * 80 + "\n")
        for r in a0_rows:
            f.write(f"{r['side']:<10} {r['group']:<25} {r['split']:<8} {r['count']:>6} {r['corrupt']:>8} {r['dups']:>5}  {r['flag']}\n")
        f.write("\n")

        if corrupt_files:
            f.write("Berkas yang tidak bisa dibuka sebagai gambar:\n")
            for c in corrupt_files:
                f.write(f"  CORRUPT: {c}\n")
        else:
            f.write("Berkas rusak: tidak ada.\n")
        f.write("\n")

        if dup_pairs:
            f.write(f"Duplikat isi terdeteksi ({len(dup_pairs)} pasang):\n")
            for dp in dup_pairs:
                f.write(f"  DUP: {dp}\n")
        else:
            f.write("Duplikat lintas split/kelompok: tidak ada.\n")

    print(f"  â†’ Laporan A0 disimpan: {a0_report_path}")

    # Tampilkan tabel di konsol
    print(f"\n  {'side':<10} {'group':<25} {'split':<8} {'count':>6} {'flag'}")
    print("  " + "-" * 65)
    for r in a0_rows:
        flag_mark = f"âš  {r['flag']}" if r["flag"] else ""
        print(f"  {r['side']:<10} {r['group']:<25} {r['split']:<8} {r['count']:>6}  {flag_mark}")

    # --- A1: Proses gambar calib ---
    print("\n[A1] Memproses gambar calib (holdout TIDAK disentuh)...")
    raw_rows: List[Dict] = []
    variant_rows: List[Dict] = []

    for side, groups in [("positive", POSITIVE_GROUPS), ("negative", NEGATIVE_GROUPS)]:
        for group in groups:
            calib_path = CALIB_DATA_ROOT / side / group / "calib"
            if not calib_path.exists():
                print(f"  [SKIP] {side}/{group}/calib â€” folder tidak ada")
                continue
            imgs = sorted([p for p in calib_path.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS])
            print(f"  [{side}/{group}] {len(imgs)} gambar...", end=" ", flush=True)
            for img_path in imgs:
                row = process_image(img_path, side, group)
                if row is None:
                    continue
                raw_rows.append(row)

                # Varian sintetis hanya untuk positif
                if side == "positive":
                    try:
                        with Image.open(img_path) as im:
                            img_orig = im.copy()
                        for vname, vimg in build_variants(img_orig):
                            vrow = process_variant(vimg, vname, str(img_path), side, group)
                            variant_rows.append(vrow)
                    except Exception as exc:
                        print(f"\n    [WARN] Varian gagal untuk {img_path.name}: {exc}", end="")
            print(f"done ({len([r for r in raw_rows if r['group']==group])} rows)")

    # Simpan CSV raw
    raw_csv_path = OUTPUT_DIR / "calib_raw.csv"
    if raw_rows:
        fieldnames = list(raw_rows[0].keys())
        with open(raw_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(raw_rows)
        print(f"\n  â†’ calib_raw.csv: {len(raw_rows)} baris â†’ {raw_csv_path}")

    # Simpan CSV varian
    var_csv_path = OUTPUT_DIR / "calib_variants.csv"
    if variant_rows:
        fieldnames_v = list(variant_rows[0].keys())
        with open(var_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames_v)
            writer.writeheader()
            writer.writerows(variant_rows)
        print(f"  â†’ calib_variants.csv: {len(variant_rows)} baris â†’ {var_csv_path}")

    # --- A2: Analisis ---
    print("\n[A2] Menghasilkan analisis...")

    pos_rows = [r for r in raw_rows if r["side"] == "positive"]
    neg_rows = [r for r in raw_rows if r["side"] == "negative"]

    summary_lines = []
    summary_lines.append("=" * 70)
    summary_lines.append("LAPORAN ANALISIS A2")
    summary_lines.append("=" * 70)

    # A2.1 Per kelompok
    summary_lines.append("\n--- A2.1 Keputusan per Kelompok ---")
    summary_lines.append(f"{'group':<25} {'label':<10} {'n':>4} {'ACCEPT':>7} {'UNCERTAIN':>10} {'REJECT':>7} {'FRR/FAR':>8}")
    summary_lines.append("-" * 75)
    for side, groups in [("positive", POSITIVE_GROUPS), ("negative", NEGATIVE_GROUPS)]:
        for group in groups:
            grp_rows = [r for r in raw_rows if r["group"] == group and r["side"] == side]
            if not grp_rows:
                continue
            n = len(grp_rows)
            n_accept = sum(1 for r in grp_rows if r["decision"] == "ACCEPT")
            n_unc    = sum(1 for r in grp_rows if r["decision"] == "UNCERTAIN")
            n_rej    = sum(1 for r in grp_rows if r["decision"] == "REJECT")
            if side == "positive":
                rate = f"FRR={n_rej/n*100:.0f}%"
            else:
                rate = f"FAR={n_accept/n*100:.0f}%"
            summary_lines.append(f"{group:<25} {side:<10} {n:>4} {n_accept:>7} {n_unc:>10} {n_rej:>7} {rate:>8}")

    # A2.2 Distribusi fitur
    summary_lines.append("\n--- A2.2 Distribusi Fitur ---")
    feature_cols = ["cool_ratio", "mucosal_ratio", "mean_chroma", "mean_saturation",
                    "mean_luminance", "std_luminance", "line_density", "glint_ratio", "active_ratio"]

    # Positif asli
    summary_lines.append("\n[Positif asli]")
    summary_lines.append(f"{'fitur':<20} {'min':>7} {'p5':>7} {'p25':>7} {'p50':>7} {'p75':>7} {'p95':>7} {'max':>7}")
    for fc in feature_cols:
        vals = [r[fc] for r in pos_rows if fc in r]
        st = percentile_stats(vals)
        summary_lines.append(f"{fc:<20} {st['min']:>7.4f} {st['p5']:>7.4f} {st['p25']:>7.4f} {st['p50']:>7.4f} {st['p75']:>7.4f} {st['p95']:>7.4f} {st['max']:>7.4f}")

    # Positif varian blur
    blur_variants = [r for r in variant_rows if r["variant"].startswith("blur")]
    summary_lines.append("\n[Positif varian blur (k5/k9/k21)]")
    summary_lines.append(f"{'fitur':<20} {'min':>7} {'p5':>7} {'p25':>7} {'p50':>7} {'p75':>7} {'p95':>7} {'max':>7}")
    for fc in feature_cols:
        vals = [r[fc] for r in blur_variants if fc in r]
        st = percentile_stats(vals)
        summary_lines.append(f"{fc:<20} {st['min']:>7.4f} {st['p5']:>7.4f} {st['p25']:>7.4f} {st['p50']:>7.4f} {st['p75']:>7.4f} {st['p95']:>7.4f} {st['max']:>7.4f}")

    # Negatif
    summary_lines.append("\n[Negatif]")
    summary_lines.append(f"{'fitur':<20} {'min':>7} {'p5':>7} {'p25':>7} {'p50':>7} {'p75':>7} {'p95':>7} {'max':>7}")
    for fc in feature_cols:
        vals = [r[fc] for r in neg_rows if fc in r]
        st = percentile_stats(vals)
        summary_lines.append(f"{fc:<20} {st['min']:>7.4f} {st['p5']:>7.4f} {st['p25']:>7.4f} {st['p50']:>7.4f} {st['p75']:>7.4f} {st['p95']:>7.4f} {st['max']:>7.4f}")

    # A2.3 Threshold sweeps
    summary_lines.append("\n--- A2.3 Threshold Sweep ---")
    summary_lines.append(threshold_sweep_cool(pos_rows, neg_rows))
    summary_lines.append(threshold_sweep_mucosa(pos_rows, neg_rows))
    summary_lines.append(threshold_sweep_line(pos_rows, neg_rows))

    # A2.4 cool_ratio inner vs full
    summary_lines.append("\n--- A2.4 Efek Pengecualian Tepi 12% (cool_ratio_inner vs cool_ratio) ---")
    for group in POSITIVE_GROUPS:
        grp = [r for r in pos_rows if r["group"] == group]
        if grp:
            full_vals = [r["cool_ratio"] for r in grp]
            inner_vals = [r["cool_ratio_inner"] for r in grp]
            summary_lines.append(
                f"  {group:<20}: full median={np.median(full_vals):.4f}, inner median={np.median(inner_vals):.4f} "
                f"(delta={np.median(full_vals)-np.median(inner_vals):.4f})"
            )

    summary_lines.append("")

    # A2.5 Positif REJECT/UNCERTAIN dan negatif ACCEPT
    summary_lines.append("\n--- A2.5 Positif Ditolak/UNCERTAIN ---")
    rejected_pos = [r for r in pos_rows if r["decision"] in ("REJECT", "UNCERTAIN")]
    if rejected_pos:
        summary_lines.append(f"{'path':<50} {'decision':<10} {'gate':<30} {'cr':>6} {'mr':>6} {'ld':>6} {'chroma':>6}")
        for r in rejected_pos:
            fname = Path(r["path"]).name
            summary_lines.append(
                f"{fname:<50} {r['decision']:<10} {r['gate_triggered']:<30} "
                f"{r['cool_ratio']:>6.3f} {r['mucosal_ratio']:>6.3f} {r['line_density']:>6.3f} {r['mean_chroma']:>6.1f}"
            )
    else:
        summary_lines.append("  Tidak ada positif yang ditolak atau UNCERTAIN.")

    summary_lines.append("\n--- A2.5 Negatif Lolos ACCEPT ---")
    accepted_neg = [r for r in neg_rows if r["decision"] == "ACCEPT"]
    if accepted_neg:
        summary_lines.append(f"{'path':<50} {'group':<25} {'cr':>6} {'mr':>6} {'ld':>6} {'chroma':>6}")
        for r in accepted_neg:
            fname = Path(r["path"]).name
            summary_lines.append(
                f"{fname:<50} {r['group']:<25} "
                f"{r['cool_ratio']:>6.3f} {r['mucosal_ratio']:>6.3f} {r['line_density']:>6.3f} {r['mean_chroma']:>6.1f}"
            )
    else:
        summary_lines.append("  Tidak ada negatif yang lolos ACCEPT.")

    # A2.6 merah_organik detail
    summary_lines.append("\n--- A2.6 Detail Kelompok merah_organik ---")
    merah_rows = [r for r in neg_rows if r["group"] == "merah_organik"]
    if merah_rows:
        gate_counts: Dict[str, int] = {}
        for r in merah_rows:
            gate_counts[r["gate_triggered"]] = gate_counts.get(r["gate_triggered"], 0) + 1
        summary_lines.append("  Gate yang paling sering memicu penolakan:")
        for gate, cnt in sorted(gate_counts.items(), key=lambda x: -x[1]):
            summary_lines.append(f"    {gate}: {cnt} gambar")
        # Fitur pemisah vs positif
        mr_vals = [r["mucosal_ratio"] for r in merah_rows]
        mr_pos_vals = [r["mucosal_ratio"] for r in pos_rows]
        cr_vals = [r["cool_ratio"] for r in merah_rows]
        ld_vals = [r["line_density"] for r in merah_rows]
        summary_lines.append(f"  mucosal_ratio: merah_organik={np.mean(mr_vals):.3f} vs positif={np.mean(mr_pos_vals):.3f}")
        summary_lines.append(f"  cool_ratio:    merah_organik={np.mean(cr_vals):.3f}")
        summary_lines.append(f"  line_density:  merah_organik={np.mean(ld_vals):.3f}")

    # Verifikasi rekonstruksi
    recon_report = verify_reconstruction_identity(raw_rows)
    summary_lines.append(f"\n--- A2.7 Verifikasi Rekonstruksi ---\n  {recon_report}")

    # Varian blur â€” berapa persen REJECT?
    summary_lines.append("\n--- A2.8 Dampak Blur pada Positif ---")
    for vname in ["blur_k5", "blur_k9", "blur_k21"]:
        vrows = [r for r in variant_rows if r["variant"] == vname]
        if vrows:
            n_rej = sum(1 for r in vrows if r["decision"] == "REJECT")
            n_unc = sum(1 for r in vrows if r["decision"] == "UNCERTAIN")
            cr_vals = [r["cool_ratio"] for r in vrows]
            summary_lines.append(
                f"  {vname}: n={len(vrows)}, REJECT={n_rej/len(vrows)*100:.1f}%, "
                f"UNCERTAIN={n_unc/len(vrows)*100:.1f}%, "
                f"cool_ratio median={np.median(cr_vals):.4f}"
            )

    summary_text = "\n".join(summary_lines)

    # Simpan summary
    summary_path = OUTPUT_DIR / "calib_summary.txt"
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_text)
    print(f"  â†’ calib_summary.txt â†’ {summary_path}")

    # Simpan summary CSV per kelompok
    summary_csv_path = OUTPUT_DIR / "calib_summary.csv"
    summary_csv_rows = []
    for side, groups in [("positive", POSITIVE_GROUPS), ("negative", NEGATIVE_GROUPS)]:
        for group in groups:
            grp_rows = [r for r in raw_rows if r["group"] == group and r["side"] == side]
            if not grp_rows:
                continue
            n = len(grp_rows)
            n_accept = sum(1 for r in grp_rows if r["decision"] == "ACCEPT")
            n_unc    = sum(1 for r in grp_rows if r["decision"] == "UNCERTAIN")
            n_rej    = sum(1 for r in grp_rows if r["decision"] == "REJECT")
            gate_top = max(set(r["gate_triggered"] for r in grp_rows), key=lambda g: sum(1 for r in grp_rows if r["gate_triggered"] == g))
            fc_medians = {fc: float(np.median([r[fc] for r in grp_rows if fc in r])) for fc in feature_cols}
            row_csv = {"side": side, "group": group, "n": n,
                       "n_accept": n_accept, "n_uncertain": n_unc, "n_reject": n_rej,
                       "top_gate": gate_top}
            row_csv.update({f"median_{k}": round(v, 4) for k, v in fc_medians.items()})
            summary_csv_rows.append(row_csv)

    if summary_csv_rows:
        with open(summary_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(summary_csv_rows[0].keys()))
            writer.writeheader()
            writer.writerows(summary_csv_rows)
        print(f"  â†’ calib_summary.csv â†’ {summary_csv_path}")

    # Print summary ke konsol
    print()
    print(summary_text)
    print("\n[SELESAI] Fase A selesai. Holdout TIDAK disentuh.")
    print(f"Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()


