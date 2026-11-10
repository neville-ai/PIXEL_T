"""C4 Holdout Evaluation — RUN EXACTLY ONCE.
Evaluates the production ColonoscopyDomainValidator on the holdout partition.
"""
import sys
import csv
import math
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from ai.inference.domain_validator import ColonoscopyDomainValidator, DomainDecision
from PIL import Image

CALIB_ROOT = PROJECT_ROOT / "calibration_data"
OUTPUT_DIR = PROJECT_ROOT / "scripts" / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def safe_open_image(path: Path) -> Image.Image:
    """Open image handling Windows MAX_PATH length limits (>260 chars)."""
    try:
        return Image.open(path)
    except FileNotFoundError:
        resolved = str(path.resolve())
        if not resolved.startswith("\\\\?\\"):
            resolved = "\\\\?\\" + resolved
        return Image.open(resolved)

def wilson_ci(successes: int, n: int, z: float = 1.96):
    if n == 0:
        return float("nan"), float("nan")
    p = successes / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    margin = (z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2))) / denom
    return max(0.0, center - margin), min(1.0, center + margin)

validator = ColonoscopyDomainValidator()

results = []
for group_dir in sorted(CALIB_ROOT.iterdir()):
    if not group_dir.is_dir():
        continue
    split = group_dir.name  # positive or negative
    for dataset_dir in sorted(group_dir.iterdir()):
        if not dataset_dir.is_dir():
            continue
        dataset = dataset_dir.name
        holdout_dir = dataset_dir / "holdout"
        if not holdout_dir.exists():
            continue
        for img_path in sorted(holdout_dir.glob("*")):
            if img_path.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}:
                continue
            try:
                with safe_open_image(img_path) as img:
                    result = validator.validate_image(img)
                decision = result.decision.value
                confidence = result.confidence
                reasons = "; ".join(result.reasons)
                metrics = result.metrics
            except Exception as e:
                decision = "ERROR"
                confidence = 0.0
                reasons = str(e)
                metrics = {}
            results.append({
                "split": split,
                "dataset": dataset,
                "filename": img_path.name,
                "decision": decision,
                "confidence": confidence,
                "reasons": reasons,
                "mucosal_ratio": metrics.get("mucosal_ratio", float("nan")),
                "cool_ratio": metrics.get("cool_ratio", float("nan")),
                "mean_chroma": metrics.get("mean_chroma", float("nan")),
                "line_density": metrics.get("line_density", float("nan")),
                "mean_luminance": metrics.get("mean_luminance", float("nan")),
            })

output_path = OUTPUT_DIR / "c4_holdout_evaluation.csv"
with open(output_path, "w", newline="", encoding="utf-8") as f:
    fieldnames = ["split", "dataset", "filename", "decision", "confidence", "reasons",
                  "mucosal_ratio", "cool_ratio", "mean_chroma", "line_density", "mean_luminance"]
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(results)

print(f"Total holdout images processed: {len(results)}")
print(f"Results saved to: {output_path}")

# Summary per group
positives = [r for r in results if r["split"] == "positive"]
negatives_main = [r for r in results if r["split"] == "negative" and r["dataset"] != "endoskopi_non_kolon"]
ileum = [r for r in results if r["dataset"] == "endoskopi_non_kolon"]

print("\n" + "="*70)
print("RINGKASAN HOLDOUT — POSITIF (citra kolonoskopi sesungguhnya)")
print("="*70)

datasets = sorted(set(r["dataset"] for r in positives))
total_pos = 0
total_frr_num = 0
total_accept = 0
total_unc = 0
total_rej = 0

for ds in datasets:
    group = [r for r in positives if r["dataset"] == ds]
    n = len(group)
    if n == 0:
        continue
    total_pos += n
    accept = sum(1 for r in group if r["decision"] == "ACCEPT")
    uncertain = sum(1 for r in group if r["decision"] == "UNCERTAIN")
    reject = sum(1 for r in group if r["decision"] == "REJECT")
    total_accept += accept
    total_unc += uncertain
    total_rej += reject
    frr_n = reject + uncertain
    total_frr_num += frr_n
    frr = frr_n / n
    lo, hi = wilson_ci(frr_n, n)
    note = " [tidak dapat disimpulkan: n<10]" if n < 10 else ""
    print(f"  {ds:20s}  n={n:3d}  ACCEPT={accept:3d}  UNC={uncertain:2d}  REJ={reject:2d}  FRR={frr*100:5.1f}% [{lo*100:4.1f}%-{hi*100:4.1f}%]{note}")

if total_pos > 0:
    frr_total = total_frr_num / total_pos
    lo_t, hi_t = wilson_ci(total_frr_num, total_pos)
    print("-" * 70)
    print(f"  {'TOTAL':20s}  n={total_pos:3d}  ACCEPT={total_accept:3d}  UNC={total_unc:2d}  REJ={total_rej:2d}  FRR={frr_total*100:5.1f}% [{lo_t*100:4.1f}%-{hi_t*100:4.1f}%]")

print("\n" + "="*70)
print("RINGKASAN HOLDOUT — NEGATIF UTAMA (bukan kolonoskopi)")
print("="*70)

neg_datasets = sorted(set(r["dataset"] for r in negatives_main))
total_neg = 0
total_fa = 0
total_neg_rej = 0
total_neg_unc = 0

for ds in neg_datasets:
    group = [r for r in negatives_main if r["dataset"] == ds]
    n = len(group)
    if n == 0:
        continue
    total_neg += n
    accept = sum(1 for r in group if r["decision"] == "ACCEPT")
    uncertain = sum(1 for r in group if r["decision"] == "UNCERTAIN")
    reject = sum(1 for r in group if r["decision"] == "REJECT")
    total_fa += accept
    total_neg_rej += reject
    total_neg_unc += uncertain
    far = accept / n
    lo, hi = wilson_ci(accept, n)
    note = " [tidak dapat disimpulkan: n<10]" if n < 10 else ""
    print(f"  {ds:20s}  n={n:3d}  REJECT={reject:3d}  UNC={uncertain:2d}  ACCEPT={accept:2d}  FAR={far*100:5.1f}% [{lo*100:4.1f}%-{hi*100:4.1f}%]{note}")

if total_neg > 0:
    far_t = total_fa / total_neg
    lo_f, hi_f = wilson_ci(total_fa, total_neg)
    print("-" * 70)
    print(f"  {'TOTAL':20s}  n={total_neg:3d}  REJECT={total_neg_rej:3d}  UNC={total_neg_unc:2d}  ACCEPT={total_fa:2d}  FAR={far_t*100:5.1f}% [{lo_f*100:4.1f}%-{hi_f*100:4.1f}%]")

if ileum:
    print("\n" + "="*70)
    print("RINGKASAN HOLDOUT — ILEUM / ENDOSKOPI NON-KOLON (kontrol terpisah)")
    print("="*70)
    n = len(ileum)
    accept = sum(1 for r in ileum if r["decision"] == "ACCEPT")
    uncertain = sum(1 for r in ileum if r["decision"] == "UNCERTAIN")
    reject = sum(1 for r in ileum if r["decision"] == "REJECT")
    note = " [tidak dapat disimpulkan: n<10]" if n < 10 else ""
    print(f"  endoskopi_non_kolon  n={n:2d}  ACCEPT={accept:2d}  UNC={uncertain:2d}  REJ={reject:2d}{note}")

print("\n" + "="*70)
print("CITRA POSITIF YANG REJECT atau UNCERTAIN di HOLDOUT")
print("="*70)
for r in [x for x in positives if x["decision"] in ("REJECT", "UNCERTAIN")]:
    print(f"  [{r['decision']:9s}] {r['dataset']}/{r['filename']}")
    print(f"    mucosa={r['mucosal_ratio']:.3f} cool={r['cool_ratio']:.3f} chroma={r['mean_chroma']:.1f} lines={r['line_density']:.3f} lum={r['mean_luminance']:.3f}")
    print(f"    alasan: {r['reasons']}")

print("\n" + "="*70)
print("CITRA NEGATIF YANG ACCEPT (FALSE ACCEPTANCE) di HOLDOUT")
print("="*70)
for r in [x for x in negatives_main if x["decision"] == "ACCEPT"]:
    print(f"  [ACCEPT   ] {r['dataset']}/{r['filename']}")
    print(f"    mucosa={r['mucosal_ratio']:.3f} cool={r['cool_ratio']:.3f} chroma={r['mean_chroma']:.1f} lines={r['line_density']:.3f}")

