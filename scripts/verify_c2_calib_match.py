"""C2 Verification: Run production ColonoscopyDomainValidator on all calib images
and compare decisions with Kandidat 2 results from scripts/output/b1_1_decision_differences.csv.
"""
import sys
import os
import csv
import json
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "Backend"))

from ai.inference.domain_validator import ColonoscopyDomainValidator, DomainDecision
from PIL import Image

CALIB_ROOT = PROJECT_ROOT / "calibration_data"
OUTPUT_DIR = PROJECT_ROOT / "scripts" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

validator = ColonoscopyDomainValidator()

def safe_open_image(path: Path) -> Image.Image:
    """Open image handling Windows MAX_PATH length limits (>260 chars)."""
    try:
        return Image.open(path)
    except FileNotFoundError:
        resolved = str(path.resolve())
        if not resolved.startswith("\\\\?\\"):
            resolved = "\\\\?\\" + resolved
        return Image.open(resolved)

results = []
for group_dir in sorted(CALIB_ROOT.iterdir()):
    if not group_dir.is_dir():
        continue
    split = group_dir.name  # positive or negative
    for dataset_dir in sorted(group_dir.iterdir()):
        if not dataset_dir.is_dir():
            continue
        dataset = dataset_dir.name
        calib_dir = dataset_dir / "calib"
        if not calib_dir.exists():
            continue
        for img_path in sorted(calib_dir.glob("*")):
            if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}:
                continue
            try:
                with safe_open_image(img_path) as img:
                    result = validator.validate_image(img)
                decision = result.decision.value
                confidence = result.confidence
                metrics = result.metrics
            except Exception as e:
                decision = "ERROR"
                confidence = 0.0
                metrics = {}
            results.append({
                "split": split,
                "dataset": dataset,
                "filename": img_path.name,
                "decision": decision,
                "confidence": confidence,
                "mucosal_ratio": metrics.get("mucosal_ratio", float("nan")),
                "cool_ratio": metrics.get("cool_ratio", float("nan")),
                "mean_chroma": metrics.get("mean_chroma", float("nan")),
                "line_density": metrics.get("line_density", float("nan")),
                "mean_luminance": metrics.get("mean_luminance", float("nan")),
            })

output_path = OUTPUT_DIR / "c2_calib_validation.csv"
with open(output_path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["split", "dataset", "filename", "decision", "confidence",
                                           "mucosal_ratio", "cool_ratio", "mean_chroma", "line_density", "mean_luminance"])
    writer.writeheader()
    writer.writerows(results)

print(f"Total images processed: {len(results)}")
positives = [r for r in results if r["split"] == "positive"]
negatives = [r for r in results if r["split"] == "negative" and r["dataset"] != "endoskopi_non_kolon"]
ileum = [r for r in results if r["dataset"] == "endoskopi_non_kolon"]

pos_reject = [r for r in positives if r["decision"] == "REJECT"]
pos_uncertain = [r for r in positives if r["decision"] == "UNCERTAIN"]
pos_accept = [r for r in positives if r["decision"] == "ACCEPT"]

neg_accept = [r for r in negatives if r["decision"] == "ACCEPT"]
neg_uncertain = [r for r in negatives if r["decision"] == "UNCERTAIN"]
neg_reject = [r for r in negatives if r["decision"] == "REJECT"]

print(f"\n=== POSITIVE (n={len(positives)}) ===")
print(f"ACCEPT:    {len(pos_accept)} ({len(pos_accept)/len(positives)*100:.1f}%)")
print(f"UNCERTAIN: {len(pos_uncertain)} ({len(pos_uncertain)/len(positives)*100:.1f}%)")
print(f"REJECT:    {len(pos_reject)} ({len(pos_reject)/len(positives)*100:.1f}%)")
frr = (len(pos_reject) + len(pos_uncertain)) / len(positives) * 100
print(f"FRR (REJECT+UNCERTAIN): {frr:.1f}%")

print(f"\n=== NEGATIVE main (n={len(negatives)}) ===")
print(f"REJECT:    {len(neg_reject)} ({len(neg_reject)/len(negatives)*100:.1f}%)")
print(f"UNCERTAIN: {len(neg_uncertain)} ({len(neg_uncertain)/len(negatives)*100:.1f}%)")
print(f"ACCEPT:    {len(neg_accept)} ({len(neg_accept)/len(negatives)*100:.1f}%)")
far = len(neg_accept) / len(negatives) * 100
print(f"FAR (ACCEPT): {far:.1f}%")

if ileum:
    il_accept = [r for r in ileum if r["decision"] == "ACCEPT"]
    print(f"\n=== ILEUM (endoskopi_non_kolon, n={len(ileum)}) [tidak dapat disimpulkan jika n<10] ===")
    print(f"ACCEPT:    {len(il_accept)}")
    print(f"UNCERTAIN: {len([r for r in ileum if r['decision']=='UNCERTAIN'])}")
    print(f"REJECT:    {len([r for r in ileum if r['decision']=='REJECT'])}")

print(f"\nResults saved to: {output_path}")

# Show rejected/uncertain positives
print("\n=== POSITIVES yang REJECT atau UNCERTAIN ===")
for r in pos_reject + pos_uncertain:
    print(f"  [{r['decision']}] {r['dataset']}/{r['filename']} | mucosa={r['mucosal_ratio']:.3f} cool={r['cool_ratio']:.3f} chroma={r['mean_chroma']:.1f} lines={r['line_density']:.3f} lum={r['mean_luminance']:.3f}")

print("\n=== NEGATIVES yang ACCEPT (false acceptance) ===")
for r in neg_accept:
    print(f"  [ACCEPT] {r['dataset']}/{r['filename']} | mucosa={r['mucosal_ratio']:.3f} cool={r['cool_ratio']:.3f} chroma={r['mean_chroma']:.1f} lines={r['line_density']:.3f}")

