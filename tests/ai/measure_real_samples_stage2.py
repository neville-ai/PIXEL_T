"""STAGE 2 measurement script — real-sample comparison for the domain validator.

Runs ColonoscopyDomainValidator.validate_bytes (the exact app path used by
create_analysis) over every real sample available on this machine and prints
decision / confidence / reason / all features as CSV-ish lines.

NOT a pytest file; run directly with:
  .\.venv\Scripts\python.exe tests/ai/measure_real_samples_stage2.py
"""
import sys
from pathlib import Path

sys.path.insert(0, ".")
sys.path.insert(0, "backend")

from ai.inference.domain_validator import ColonoscopyDomainValidator

validator = ColonoscopyDomainValidator()

FEATURES = [
    "mucosal_ratio", "cool_ratio", "std_luminance", "line_density",
    "glint_ratio", "mean_luminance", "mean_chroma", "mean_saturation",
    "active_ratio", "aspect_ratio", "width", "height",
]

SAMPLES = [
    ("NEG pizza", r"C:\Users\nevil\OneDrive\Dokumen\images (2).jpg"),
    ("COL normal-folds-glint", r"C:\Users\nevil\OneDrive\Dokumen\images (1).jpg"),
    ("COL normal-lumen-OSD", r"C:\Users\nevil\OneDrive\Dokumen\images (7).jpg"),
    ("COL pathology-ulcers", r"C:\Users\nevil\OneDrive\Dokumen\images (8).jpg"),
    ("COL lesion-polyp", r"C:\Users\nevil\OneDrive\Dokumen\images (9).jpg"),
    ("NEG meat-textured-tray", r"C:\Users\nevil\OneDrive\Dokumen\images (3).jpg"),
    ("NEG tomato-retail", r"C:\Users\nevil\OneDrive\Dokumen\images (4).jpg"),
    ("NEG food-meatballs", r"C:\Users\nevil\OneDrive\Dokumen\images (5).jpg"),
    ("NEG meat-flat-steaks", r"C:\Users\nevil\OneDrive\Dokumen\images (6).jpg"),
    ("REF monitor-extracted", r"references\extracted_colonoscopy.png"),
    ("REF monitor-pure", r"references\pure_colonoscopy_frame.png"),
]

print("tag\tfile\tdecision\tconfidence\treason\t" + "\t".join(FEATURES))
for tag, path in SAMPLES:
    p = Path(path)
    if not p.is_file():
        print(f"{tag}\t{path}\tMISSING")
        continue
    data = p.read_bytes()
    try:
        r = validator.validate_bytes(data)
    except Exception as exc:  # noqa: BLE001
        print(f"{tag}\t{path}\tERROR\t{exc}")
        continue
    vals = [str(r.metrics.get(k, "")) for k in FEATURES]
    reason = "; ".join(r.reasons)
    print(f"{tag}\t{p.name}\t{r.decision.value}\t{r.confidence:.4f}\t{reason}\t" + "\t".join(vals))
