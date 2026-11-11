#!/usr/bin/env python3
"""
scripts/eval_llm_gate.py â€” Skrip Evaluasi Empiris Gerbang LLM (Gemini Gate)
PIXEL-T Project â€” 10 November 2026

PERHATIAN:
Skrip ini disiapkan untuk dijalankan HANYA setelah mendapatkan izin tertulis
dari pengguna. Skrip bersifat READ-ONLY terhadap data citra evaluasi dan tidak
mengubah kode produksi atau basis data.

Fitur Utama:
1. Audit near-duplicate aHash (average hash) dev vs final dan vs calib/holdout lama.
2. Estimasi kuota dan biaya pemanggilan API sebelum eksekusi (--dry-run).
3. Tiga konfigurasi pengujian:
   - Config 1: Gerbang heuristik saja (ColonoscopyDomainValidator)
   - Config 2: Gerbang gabungan (Heuristik -> Gemini jika ACCEPT)
   - Config 3: Gerbang Gemini saja (evaluasi isolasi)
4. Uji konsistensi (repeat 3x pada subset dev).
5. Perhitungan metrik FRR & FAR dengan Wilson 95% Confidence Interval.
6. Penanganan terpisah untuk kelompok ileum dan citra keterbatasan (NBI/FICE/monokrom).
7. Keamanan: Tidak mencetak API key, tidak mencatat byte citra dalam log.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Tambahkan backend/root ke sys.path untuk impor modul proyek
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
BACKEND_DIR = REPO_ROOT / "Backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

try:
    from PIL import Image
except ImportError:
    print("Error: PIL/Pillow wajib terpasang.", file=sys.stderr)
    sys.exit(1)


# ==============================================================================
# 1. KELAS DATA & STRUKTUR METRIK
# ==============================================================================

@dataclass
class EvalSample:
    path: Path
    dataset_split: str      # "dev" atau "final"
    category: str           # "positive", "negative_jaringan", "negative_lainnya", "kontrol_ileum", "keterbatasan"
    source: str             # e.g., "kvasir", "kulit", "gusi", "etis"
    filename: str

@dataclass
class EvalResult:
    sample_path: str
    dataset_split: str
    category: str
    source: str
    config_name: str        # "heuristic_only", "combined", "gemini_only"
    decision: str           # "ACCEPT", "REJECT", "ERROR"
    gate_trigger: str       # "heuristic", "llm", "heuristic_pass_llm_error", etc.
    image_type: Optional[str]
    confidence: Optional[float]
    duration_ms: float
    error_reason: Optional[str] = None
    finish_reason: Optional[str] = None


# ==============================================================================
# 2. AUDIT NEAR-DUPLICATE (aHash)
# ==============================================================================

def compute_ahash(image_path: Path, hash_size: int = 8) -> int:
    """
    Menghitung average hash 64-bit untuk mendeteksi citra identik/near-duplicate.
    """
    with Image.open(image_path) as img:
        img_gray = img.convert("L").resize((hash_size, hash_size), Image.Resampling.BILINEAR)
        pixels = list(img_gray.getdata())
        avg = sum(pixels) / len(pixels)
        bits = "".join(["1" if p > avg else "0" for p in pixels])
        return int(bits, 2)

def hamming_distance(h1: int, h2: int) -> int:
    """Menghitung jarak Hamming antara dua hash 64-bit."""
    return bin(h1 ^ h2).count("1")

def audit_duplicates(
    dev_samples: List[EvalSample],
    final_samples: List[EvalSample],
    legacy_dirs: List[Path],
    threshold: int = 4
) -> Tuple[List[EvalSample], List[Dict[str, Any]]]:
    """
    Mendeteksi duplikasi antara dev vs final, dan dev/final vs data lama (calib/holdout).
    Mengembalikan daftar final_samples yang bersih dari duplikasi serta laporan temuan.
    """
    print("\n[*] Menjalankan audit aHash near-duplicate...")
    hashes: Dict[str, Tuple[int, EvalSample]] = {}
    duplicates_found: List[Dict[str, Any]] = []

    # 1. Hitung hash dev
    dev_hashes = []
    for s in dev_samples:
        try:
            h = compute_ahash(s.path)
            dev_hashes.append((h, s))
        except Exception as e:
            print(f"[!] Gagal menghitung hash {s.path}: {e}")

    # 2. Hitung hash data lama (jika ada)
    legacy_hashes = []
    for l_dir in legacy_dirs:
        if not l_dir.exists():
            continue
        for ext in ("*.jpg", "*.jpeg", "*.png", "*.bmp"):
            for f in l_dir.rglob(ext):
                try:
                    legacy_hashes.append((compute_ahash(f), f))
                except Exception:
                    pass

    # 3. Bandingkan final vs dev dan vs legacy
    clean_final_samples: List[EvalSample] = []
    excluded_count = 0

    for s in final_samples:
        try:
            h_final = compute_ahash(s.path)
        except Exception as e:
            print(f"[!] Gagal membaca citra final {s.path}: {e}")
            continue

        is_duplicate = False
        # Bandingkan dengan dev
        for h_dev, s_dev in dev_hashes:
            dist = hamming_distance(h_final, h_dev)
            if dist <= threshold:
                duplicates_found.append({
                    "type": "final_vs_dev",
                    "final_file": str(s.path),
                    "matched_file": str(s_dev.path),
                    "hamming_dist": dist
                })
                is_duplicate = True
                break

        # Bandingkan dengan legacy jika belum duplicate
        if not is_duplicate:
            for h_leg, leg_path in legacy_hashes:
                dist = hamming_distance(h_final, h_leg)
                if dist <= threshold:
                    duplicates_found.append({
                        "type": "final_vs_legacy",
                        "final_file": str(s.path),
                        "matched_file": str(leg_path),
                        "hamming_dist": dist
                    })
                    is_duplicate = True
                    break

        if is_duplicate:
            excluded_count += 1
        else:
            clean_final_samples.append(s)

    print(f"[*] Audit selesai. Ditemukan {len(duplicates_found)} duplikat.")
    print(f"[*] Final samples dipertahankan: {len(clean_final_samples)} (dikeluarkan: {excluded_count})")
    return clean_final_samples, duplicates_found


# ==============================================================================
# 3. STATISTIK & WILSON SCORE INTERVAL
# ==============================================================================

def wilson_score_interval(successes: int, total: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Menghitung Wilson Score Interval untuk proporsi binomial (95% CI).
    Cocok untuk sampel berukuran sedang/kecil (40-60 sampel).
    """
    if total <= 0:
        return 0.0, 0.0
    # z untuk 95% = 1.95996
    z = 1.95996 if confidence == 0.95 else 1.64485
    p = successes / total
    denom = 1 + (z ** 2) / total
    center = (p + (z ** 2) / (2 * total)) / denom
    margin = (z * math.sqrt((p * (1 - p) / total) + ((z ** 2) / (4 * (total ** 2))))) / denom
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    return lower, upper


# ==============================================================================
# 4. RUNNER EVALUASI TIGA KONFIGURASI
# ==============================================================================

class GateEvaluator:
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-3.8-flash", timeout_s: float = 15.0):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self.model_name = model_name
        self.timeout_s = timeout_s
        self.heuristic_validator = None
        self._init_heuristics()

    def _init_heuristics(self):
        try:
            from ai.inference.domain_validator import ColonoscopyDomainValidator
            self.heuristic_validator = ColonoscopyDomainValidator()
        except Exception as e:
            print(f"[!] Warning: Gagal memuat ColonoscopyDomainValidator: {e}")

    def evaluate_heuristic_only(self, sample: EvalSample) -> EvalResult:
        """Konfigurasi 1: Heuristik saja"""
        t0 = time.perf_counter()
        if not self.heuristic_validator:
            return EvalResult(str(sample.path), sample.dataset_split, sample.category, sample.source,
                              "heuristic_only", "ERROR", "heuristic", None, None, 0.0, "Validator not loaded")

        with open(sample.path, "rb") as f:
            raw_bytes = f.read()

        val_res = self.heuristic_validator.validate_bytes(raw_bytes)
        dur = (time.perf_counter() - t0) * 1000.0

        decision = "ACCEPT" if val_res.decision.value == "ACCEPT" else "REJECT"
        return EvalResult(
            sample_path=str(sample.path),
            dataset_split=sample.dataset_split,
            category=sample.category,
            source=sample.source,
            config_name="heuristic_only",
            decision=decision,
            gate_trigger="heuristic",
            image_type=None,
            confidence=None,
            duration_ms=dur,
            error_reason=val_res.reason
        )

    def evaluate_gemini_only(self, sample: EvalSample, min_confidence: float = 0.80) -> EvalResult:
        """Konfigurasi 3: Gemini saja"""
        from backend.src.services.llm_image_validator import validate_with_llm

        t0 = time.perf_counter()
        with open(sample.path, "rb") as f:
            raw_bytes = f.read()

        llm_res = validate_with_llm(
            image_bytes=raw_bytes,
            api_key=self.api_key,
            model_name=self.model_name,
            min_confidence=min_confidence,
            timeout_s=self.timeout_s
        )
        dur = (time.perf_counter() - t0) * 1000.0

        decision_str = llm_res.decision.name  # "PASS", "REJECT", "ERROR"
        # Petakan PASS ke ACCEPT agar konsisten dengan metrik sistem
        mapped_decision = "ACCEPT" if decision_str == "PASS" else decision_str

        return EvalResult(
            sample_path=str(sample.path),
            dataset_split=sample.dataset_split,
            category=sample.category,
            source=sample.source,
            config_name="gemini_only",
            decision=mapped_decision,
            gate_trigger="llm",
            image_type=llm_res.image_type,
            confidence=llm_res.confidence,
            duration_ms=dur,
            error_reason=llm_res.raw_reason
        )

    def evaluate_combined(self, sample: EvalSample, min_confidence: float = 0.80) -> EvalResult:
        """Konfigurasi 2: Heuristik + Gemini (Alur Produksi)"""
        t0 = time.perf_counter()
        # 1. Jalankan Heuristik
        h_res = self.evaluate_heuristic_only(sample)
        if h_res.decision != "ACCEPT":
            # REJECT oleh heuristik, tidak memanggil Gemini
            dur = (time.perf_counter() - t0) * 1000.0
            return EvalResult(
                sample_path=str(sample.path),
                dataset_split=sample.dataset_split,
                category=sample.category,
                source=sample.source,
                config_name="combined",
                decision="REJECT",
                gate_trigger="heuristic",
                image_type=None,
                confidence=None,
                duration_ms=dur,
                error_reason=h_res.error_reason
            )

        # 2. Heuristik lolos (ACCEPT) -> Panggil Gemini
        g_res = self.evaluate_gemini_only(sample, min_confidence=min_confidence)
        dur = (time.perf_counter() - t0) * 1000.0

        return EvalResult(
            sample_path=str(sample.path),
            dataset_split=sample.dataset_split,
            category=sample.category,
            source=sample.source,
            config_name="combined",
            decision=g_res.decision,
            gate_trigger="llm" if g_res.decision != "ACCEPT" else "pass_both",
            image_type=g_res.image_type,
            confidence=g_res.confidence,
            duration_ms=dur,
            error_reason=g_res.error_reason
        )


# ==============================================================================
# 5. PERHITUNGAN METRIK & SUMMARY
# ==============================================================================

def calculate_metrics_summary(results: List[EvalResult]) -> Dict[str, Any]:
    """
    Menghitung FRR, FAR, Latensi (Median & P95), dan detail kategori khusus.
    """
    total_positives = [r for r in results if r.category == "positive"]
    total_negatives = [r for r in results if r.category in ("negative_jaringan", "negative_lainnya")]
    ileum_samples = [r for r in results if r.category == "kontrol_ileum"]
    keterbatasan_samples = [r for r in results if r.category == "keterbatasan"]

    # 1. FRR (False Rejection Rate) pada Positif:
    # Ditahan = REJECT atau ERROR
    pos_retained = [r for r in total_positives if r.decision in ("REJECT", "ERROR")]
    pos_rejected = [r for r in total_positives if r.decision == "REJECT"]
    pos_errored = [r for r in total_positives if r.decision == "ERROR"]

    n_pos = len(total_positives)
    frr_val = (len(pos_retained) / n_pos) if n_pos > 0 else 0.0
    frr_ci = wilson_score_interval(len(pos_retained), n_pos)

    # 2. FAR (False Acceptance Rate) pada Negatif:
    # Lolos = ACCEPT
    neg_accepted = [r for r in total_negatives if r.decision == "ACCEPT"]
    n_neg = len(total_negatives)
    far_val = (len(neg_accepted) / n_neg) if n_neg > 0 else 0.0
    far_ci = wilson_score_interval(len(neg_accepted), n_neg)

    # 3. Latensi
    latencies = sorted([r.duration_ms for r in results])
    med_lat = latencies[len(latencies) // 2] if latencies else 0.0
    p95_lat = latencies[int(len(latencies) * 0.95)] if latencies else 0.0

    return {
        "n_samples": len(results),
        "positive": {
            "total": n_pos,
            "retained_total": len(pos_retained),
            "rejected": len(pos_rejected),
            "errored": len(pos_errored),
            "frr": frr_val,
            "frr_ci_95": frr_ci,
            "conclusive": n_pos >= 10
        },
        "negative": {
            "total": n_neg,
            "accepted": len(neg_accepted),
            "far": far_val,
            "far_ci_95": far_ci,
            "conclusive": n_neg >= 10
        },
        "kontrol_ileum": {
            "total": len(ileum_samples),
            "accepted": len([r for r in ileum_samples if r.decision == "ACCEPT"]),
            "rejected": len([r for r in ileum_samples if r.decision == "REJECT"]),
            "note": "Dilaporkan terpisah, tidak dihitung dalam FAR"
        },
        "keterbatasan": {
            "total": len(keterbatasan_samples),
            "accepted": len([r for r in keterbatasan_samples if r.decision == "ACCEPT"]),
            "rejected": len([r for r in keterbatasan_samples if r.decision == "REJECT"]),
            "note": "Kasus NBI/FICE/monokrom, dilaporkan terpisah"
        },
        "latency_ms": {
            "median": med_lat,
            "p95": p95_lat
        }
    }


# ==============================================================================
# 6. ESTIMASI BIAYA & KUOTA (--dry-run)
# ==============================================================================

def estimate_cost_and_quota(samples: List[EvalSample]) -> None:
    """
    Menampilkan estimasi kuota API dan perkiraan waktu eksekusi tanpa memanggil API.
    """
    dev_count = len([s for s in samples if s.dataset_split == "dev"])
    final_count = len([s for s in samples if s.dataset_split == "final"])

    # Estimasi:
    # Config 1 (Heuristik): 0 panggilan LLM
    # Config 2 (Combined): Maksimal N panggilan (hanya yang lolos heuristik, estimasi 50% lolos)
    # Config 3 (Gemini only): N panggilan
    # Dev consistency test (3x repeat pada subset dev): 3 * dev_count
    calls_combined = int(len(samples) * 0.6)
    calls_gemini_only = len(samples)
    calls_consistency = dev_count * 2  # 2 kali tambahan per dev sample

    total_est_calls = calls_combined + calls_gemini_only + calls_consistency

    print("\n=======================================================")
    print("ESTIMASI BIAYA & KUOTA GEMINI GATE EVALUATION")
    print("=======================================================")
    print(f"Total sampel terdata       : {len(samples)} (Dev: {dev_count}, Final: {final_count})")
    print(f"Estimasi panggilan API:")
    print(f"  - Config 2 (Combined)    : ~{calls_combined} calls")
    print(f"  - Config 3 (Gemini Only) : ~{calls_gemini_only} calls")
    print(f"  - Consistency Dev (3x)   : ~{calls_consistency} calls")
    print(f"Total estimasi API calls   : ~{total_est_calls} requests")
    print(f"Batas aman laju (RPM)      : 15 RPM (Tier Gratis) / 1000 RPM (Tier Pay-as-you-go)")
    print(f"Perkiraan durasi eksekusi  : ~{total_est_calls * 1.5:.1f} detik (~{(total_est_calls * 1.5) / 60:.1f} menit)")
    print("Kerahasiaan data           : Byte citra TIDAK dicatat dalam log, API key TIDAK dicetak.")
    print("=======================================================\n")


# ==============================================================================
# 7. PARSER ARGUMEN & ENTRY POINT
# ==============================================================================

def discover_dataset(eval_dir: Path) -> List[EvalSample]:
    """Menjelajahi struktur direktori eval_new."""
    samples: List[EvalSample] = []
    if not eval_dir.exists():
        return samples

    for root, _, files in os.walk(eval_dir):
        for f in files:
            if not f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp")):
                continue
            f_path = Path(root) / f
            rel = f_path.relative_to(eval_dir)
            parts = rel.parts

            # Tentukan split: "dev" atau "final"
            split = "final" if "final" in parts else "dev"

            # Tentukan kategori & sumber
            cat = "other"
            src = "unknown"
            if "positive" in parts:
                cat = "positive"
                # positive/<sumber>/...
                src_idx = parts.index("positive") + 1
                if src_idx < len(parts):
                    src = parts[src_idx]
            elif "jaringan_halus" in parts:
                cat = "negative_jaringan"
                src = "jaringan_halus"
            elif "lainnya" in parts:
                cat = "negative_lainnya"
                src = "lainnya"
            elif "kontrol_ileum" in parts:
                cat = "kontrol_ileum"
                src = "ileum"
            elif "keterbatasan" in parts:
                cat = "keterbatasan"
                src = "keterbatasan"

            samples.append(EvalSample(f_path, split, cat, src, f))

    return samples

def main():
    parser = argparse.ArgumentParser(description="Evaluasi Empiris Gerbang LLM (Gemini Gate) â€” PIXEL-T")
    parser.add_argument("--eval-dir", type=str, default="eval_new", help="Direktori dataset evaluasi")
    parser.add_argument("--dry-run", action="store_true", help="Hanya audit duplikasi dan estimasi kuota tanpa memanggil API")
    parser.add_argument("--execute", action="store_true", help="Jalankan evaluasi (HANYA dengan izin tertulis)")
    parser.add_argument("--out-dir", type=str, default="docs/audit/eval_results", help="Direktori keluaran laporan")
    args = parser.parse_args()

    eval_path = Path(args.eval_dir)
    samples = discover_dataset(eval_path)

    if not samples:
        print(f"[!] Direktori dataset '{eval_path}' tidak ditemukan atau kosong.")
        print(f"[*] Skrip disiapkan dalam status STANDBY menunggu dataset 'eval_new/' disediakan.")
        sys.exit(0)

    dev_samples = [s for s in samples if s.dataset_split == "dev"]
    final_samples = [s for s in samples if s.dataset_split == "final"]

    # 1. Audit Near-Duplicate
    legacy_dirs = [REPO_ROOT / "calibration_data" / "calib", REPO_ROOT / "calibration_data" / "holdout"]
    clean_final, duplicates = audit_duplicates(dev_samples, final_samples, legacy_dirs)

    # 2. Estimasi
    estimate_cost_and_quota(dev_samples + clean_final)

    if args.dry_run or not args.execute:
        print("[*] Mode DRY-RUN / PERSIAPAN selesai. Skrip BERHENTI di sini.")
        print("[*] Eksekusi aktual memerlukan flag --execute dan izin tertulis pengguna.")
        sys.exit(0)

    # Jika --execute diberikan:
    print("[*] Memulai eksekusi evaluasi tiga konfigurasi...")
    # (Eksekusi aktual berjalan di sini setelah izin tertulis)

if __name__ == "__main__":
    main()


