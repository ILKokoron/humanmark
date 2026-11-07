#!/usr/bin/env python3
"""Run candidate replacement scanners over the SAME 20-image mini set.
Mirrors run_scanners.py: saves RAW label scores per image per model to
results/candidates/raw_scores_<short>.json. Mapping to P(AI) happens in
analyze_candidates.py, after seeing each model's actual label set.
Usage: python run_candidates.py [substring-filter]
"""
import json, os, sys, time
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "results", "candidates")
os.makedirs(OUT, exist_ok=True)
MODELS = [
    ("umm-maybe/AI-image-detector", os.path.expanduser("~/workspace/human-cert/models/umm"), "umm"),
    ("Ateeqq/ai-vs-human-image-detector", os.path.expanduser("~/workspace/human-cert/models/ateeqq"), "ateeqq"),
    ("abacusai/Smaug-AI-Image-Detector", os.path.expanduser("~/workspace/human-cert/models/smaug"), "smaug"),
]

from transformers import pipeline

manifest = json.load(open(os.path.join(BASE, "set", "manifest.json")))
only = sys.argv[1] if len(sys.argv) > 1 else None

for model_id, local_dir, short in MODELS:
    if only and only not in short:
        continue
    print(f"=== loading {model_id} from {local_dir} ===", flush=True)
    t0 = time.time()
    try:
        clf = pipeline("image-classification", model=local_dir, device=-1)
    except Exception as e:
        print(f"LOAD FAILED for {model_id}: {type(e).__name__}: {e}", flush=True)
        json.dump({"error": f"{type(e).__name__}: {e}"},
                  open(os.path.join(OUT, f"raw_scores_{short}.json"), "w"), indent=1)
        continue
    print("id2label:", clf.model.config.id2label, flush=True)
    entry = {"id2label": {str(k): v for k, v in clf.model.config.id2label.items()}, "scores": {}}
    for m in manifest:
        path = os.path.join(BASE, m["file"])
        img = Image.open(path).convert("RGB")
        out = clf(img, top_k=None)
        entry["scores"][m["id"]] = [
            {"label": o["label"], "score": round(float(o["score"]), 4)} for o in out
        ]
        top = max(out, key=lambda o: o["score"])
        print(f"{m['id']} truth={m['truth']:5s} top={top['label']} {top['score']:.3f}", flush=True)
    print(f"--- {model_id} done in {time.time()-t0:.0f}s ---", flush=True)
    json.dump({model_id: entry}, open(os.path.join(OUT, f"raw_scores_{short}.json"), "w"), indent=1)
    print(f"saved results/candidates/raw_scores_{short}.json", flush=True)
