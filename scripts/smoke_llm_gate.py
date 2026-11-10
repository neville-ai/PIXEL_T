import os
import sys
import time
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import dotenv_values
from PIL import Image
from pydantic import BaseModel, Field

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ai.inference.domain_validator import ColonoscopyDomainValidator, DomainDecision

# Structured response schema for Gemini
class GateDecision(BaseModel):
    decision: str = Field(description="Strictly either 'ACCEPT' or 'REJECT'")
    reason: str = Field(description="A concise one-sentence clinical/visual explanation")

PROMPT = (
    "You are a clinical domain verification gate for PIXEL-T, an AI colorectal polyp analysis system.\n"
    "Determine whether the provided image is a genuine internal optical endoscopic view of gastrointestinal mucosa "
    "(such as colonoscopy, colon, rectum, or terminal ileum) [ACCEPT], "
    "or an invalid non-colonoscopy image (such as raw meat, butchery, non-endoscopic medical photography/imaging, "
    "radiology, laparoscopy, external body skin/face, objects, room, text document, diagram, histology, or other non-endoscopic photo) [REJECT].\n"
    "Respond strictly with DECISION ('ACCEPT' or 'REJECT') and a brief REASON."
)

def load_env_config():
    env_path = PROJECT_ROOT / "backend" / ".env"
    cfg = dotenv_values(str(env_path))
    api_key = cfg.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")
    model_name = cfg.get("GEMINI_MODEL", "gemini-3.8-flash")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not configured in backend/.env or environment.")
    return api_key, model_name

def get_subset_files() -> List[Dict[str, Any]]:
    base_dir = PROJECT_ROOT / "calibration_data"
    
    # 7 Negatif lolos
    negatives = [
        {"file": base_dir / "negative" / "merah_organik" / "calib" / "images (39).jpg", "group": "negatif_lolos"},
        {"file": base_dir / "negative" / "merah_organik" / "calib" / "images (43).jpg", "group": "negatif_lolos"},
        {"file": base_dir / "negative" / "merah_organik" / "calib" / "images (44).jpg", "group": "negatif_lolos"},
        {"file": base_dir / "negative" / "medis_lain" / "calib" / "images (69).jpg", "group": "negatif_lolos"},
        {"file": base_dir / "negative" / "medis_lain" / "calib" / "images (72).jpg", "group": "negatif_lolos"},
        {"file": base_dir / "negative" / "medis_lain" / "calib" / "images (73).jpg", "group": "negatif_lolos"},
        {"file": base_dir / "negative" / "orang_ruangan" / "calib" / "images (50).jpg", "group": "negatif_lolos"},
    ]
    
    # 6 Positif bersih (first alphabetical per source)
    pos_clean = [
        {"file": base_dir / "positive" / "kvasir" / "calib" / "cju0s690hkp960855tjuaqvv0.jpg", "group": "positif_bersih"},
        {"file": base_dir / "positive" / "cvc_clinicdb" / "calib" / "1.png", "group": "positif_bersih"},
        {"file": base_dir / "positive" / "cvc_colondb" / "calib" / "1.png", "group": "positif_bersih"},
        {"file": base_dir / "positive" / "etis" / "calib" / "1.png", "group": "positif_bersih"},
        {"file": base_dir / "positive" / "bkai" / "calib" / "02fa602bb3c7abacdbd7e6afd56ea7bc.jpeg", "group": "positif_bersih"},
        {"file": base_dir / "positive" / "hyperkvasir" / "calib" / "cju0qkwl35piu0993l0dewei2.jpg", "group": "positif_bersih"},
    ]
    
    # 2 Positif resolusi tinggi (dulu ditolak G5b, kini ACCEPT)
    pos_highres = [
        {"file": base_dir / "positive" / "bkai" / "calib" / "0a5f3601ad4f13ccf1f4b331a412fc44.jpeg", "group": "positif_res_tinggi"},
        {"file": base_dir / "positive" / "hyperkvasir" / "calib" / "cju0sr5ghl0nd08789uzf1raf.jpg", "group": "positif_res_tinggi"},
    ]
    
    # 4 Positif nyata (in_vivo_blur ACCEPT)
    pos_invivo = [
        {"file": base_dir / "positive" / "in_vivo_blur" / "calib" / "images (11).jpg", "group": "positif_nyata"},
        {"file": base_dir / "positive" / "in_vivo_blur" / "calib" / "images (12).jpg", "group": "positif_nyata"},
        {"file": base_dir / "positive" / "in_vivo_blur" / "calib" / "images (20).jpg", "group": "positif_nyata"},
        {"file": base_dir / "positive" / "in_vivo_blur" / "calib" / "images (21).jpg", "group": "positif_nyata"},
    ]
    
    # 2 Ileum (endoskopi_non_kolon)
    ileum = [
        {"file": base_dir / "negative" / "endoskopi_non_kolon" / "calib" / "normal_ileum_000001.jpg", "group": "ileum"},
        {"file": base_dir / "negative" / "endoskopi_non_kolon" / "calib" / "normal_ileum_000002.jpg", "group": "ileum"},
    ]
    
    return negatives + pos_clean + pos_highres + pos_invivo + ileum

def call_gemini_with_retry(client, model_name: str, pil_img: Image.Image, config_obj) -> Dict[str, Any]:
    max_retries = 1
    for attempt in range(max_retries + 1):
        try:
            t0 = time.perf_counter()
            response = client.models.generate_content(
                model=model_name,
                contents=[pil_img, PROMPT],
                config=config_obj
            )
            lat_ms = (time.perf_counter() - t0) * 1000.0
            
            raw_text = response.text.strip()
            
            # Parse json or markdown codeblock json
            dec = "REJECT"
            reason = ""
            try:
                cleaned = re.sub(r"^```(?:json)?\s*", "", raw_text)
                cleaned = re.sub(r"\s*```$", "", cleaned)
                data = json.loads(cleaned)
                dec = data.get("decision", "REJECT").strip().upper()
                reason = data.get("reason", "").strip()
            except Exception:
                if "ACCEPT" in raw_text.upper() and "REJECT" not in raw_text.upper():
                    dec = "ACCEPT"
                else:
                    dec = "REJECT"
                reason = raw_text[:120]
            
            prompt_tokens = getattr(response.usage_metadata, "prompt_token_count", None)
            cand_tokens = getattr(response.usage_metadata, "candidates_token_count", None)
            
            return {
                "decision": dec,
                "reason": reason,
                "latency_ms": lat_ms,
                "tokens_in": prompt_tokens,
                "tokens_out": cand_tokens,
                "error": None
            }
        except Exception as e:
            err_msg = str(e)
            if "RESOURCE_EXHAUSTED" in err_msg or "429" in err_msg:
                # Quota exceeded; immediate retry won't succeed
                return {
                    "decision": "ERROR",
                    "reason": "429 RESOURCE_EXHAUSTED (Quota per day exceeded)",
                    "latency_ms": 0.0,
                    "tokens_in": None,
                    "tokens_out": None,
                    "error": "429 RESOURCE_EXHAUSTED"
                }
            if attempt < max_retries:
                time.sleep(1.0)
                continue
            return {
                "decision": "ERROR",
                "reason": err_msg[:100],
                "latency_ms": 0.0,
                "tokens_in": None,
                "tokens_out": None,
                "error": err_msg[:100]
            }

def main():
    api_key, model_name = load_env_config()
    from google import genai
    from google.genai import types
    
    # Configure client without infinite internal retries
    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(
            retry_options=types.HttpRetryOptions(attempts=1),
            timeout=15000
        )
    )
    
    cfg = types.GenerateContentConfig(
        temperature=0.0,
        response_mime_type="application/json",
        response_schema=GateDecision
    )
    
    # 1. Production heuristic validator (same path as backend upload)
    validator = ColonoscopyDomainValidator()
    
    subset = get_subset_files()
    results = []
    all_latencies = []
    
    for idx, item in enumerate(subset):
        p: Path = item["file"]
        group = item["group"]
        file_bytes = p.read_bytes()
        
        # Production heuristic validation
        heuristic_res = validator.validate_bytes(file_bytes)
        heuristic_dec = heuristic_res.decision.value
        
        called_llm = (heuristic_dec == DomainDecision.ACCEPT.value)
        llm_runs = []
        
        if called_llm:
            with Image.open(p) as pil_img:
                img_rgb = pil_img.convert("RGB")
                for run_idx in range(3):
                    res = call_gemini_with_retry(client, model_name, img_rgb, cfg)
                    llm_runs.append(res)
                    if res["latency_ms"] > 0:
                        all_latencies.append(res["latency_ms"])
        else:
            for _ in range(3):
                llm_runs.append({
                    "decision": "-",
                    "reason": "-",
                    "latency_ms": 0.0,
                    "tokens_in": None,
                    "tokens_out": None,
                    "error": None
                })
        
        # Determine final decision
        if not called_llm:
            final_dec = heuristic_dec
        else:
            decisions = [r["decision"] for r in llm_runs]
            accept_count = decisions.count("ACCEPT")
            reject_count = decisions.count("REJECT")
            if accept_count > reject_count:
                final_dec = "ACCEPT"
            elif reject_count > accept_count:
                final_dec = "REJECT"
            else:
                final_dec = "ERROR" if all(d == "ERROR" for d in decisions) else "UNCERTAIN"
        
        results.append({
            "name": p.name,
            "group": group,
            "heuristic": heuristic_dec,
            "llm_called": "YA" if called_llm else "TIDAK",
            "llm_runs": llm_runs,
            "final_decision": final_dec
        })

    # Print Table
    print("\n" + "="*126)
    print(f"{'NAMA BERKAS':<40} | {'KELOMPOK':<18} | {'HEURISTIK':<9} | {'LLM CALL':<8} | {'LLM (RUN 1/2/3)':<17} | {'AKHIR':<8} | {'LATENSI (ms)':<15} | {'TOKEN IN/OUT'}")
    print("-" * 126)
    
    for r in results:
        decisions_str = "/".join(run["decision"] for run in r["llm_runs"])
        lats_str = "/".join(f"{run['latency_ms']:.0f}" for run in r["llm_runs"]) if r["llm_called"] == "YA" else "-"
        tok_str = "/".join(f"{run['tokens_in'] or 0}+{run['tokens_out'] or 0}" for run in r["llm_runs"]) if r["llm_called"] == "YA" else "-"
        
        print(f"{r['name']:<40} | {r['group']:<18} | {r['heuristic']:<9} | {r['llm_called']:<8} | {decisions_str:<17} | {r['final_decision']:<8} | {lats_str:<15} | {tok_str}")
    
    print("="*126)
    
    # Reasons for 7 negative images
    print("\nALASAN SINGKAT LLM UNTUK 7 NEGATIF LOLOS:")
    for r in results:
        if r["group"] == "negatif_lolos":
            reasons = [run["reason"] for run in r["llm_runs"] if run["reason"]]
            first_reason = reasons[0] if reasons else "-"
            print(f"- {r['name']} ({r['final_decision']}): {first_reason}")
    
    # Summary calculation
    neg_stopped = sum(1 for r in results if r["group"] == "negatif_lolos" and r["final_decision"] == "REJECT")
    pos_accepted = sum(1 for r in results if r["group"] in ("positif_bersih", "positif_res_tinggi", "positif_nyata", "ileum") and r["final_decision"] == "ACCEPT")
    
    variance_count = 0
    for r in results:
        if r["llm_called"] == "YA":
            decs = set(run["decision"] for run in r["llm_runs"])
            if len(decs) > 1:
                variance_count += 1
                
    avg_latency = (sum(all_latencies) / len(all_latencies)) if all_latencies else 0.0
    
    print("\nRINGKASAN:")
    print(f"negatif tertahan {neg_stopped}/7, positif tetap ACCEPT {pos_accepted}/14, gambar yang keputusannya berubah antar-run {variance_count}, rata-rata latensi {avg_latency:.1f} ms\n")

if __name__ == "__main__":
    main()
