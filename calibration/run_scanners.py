#!/usr/bin/env python3
"""Run the 3 Hugging Face scanners over the mini calibration set.
Saves RAW label scores per image per model to results/raw_scores.json.
No verdict mapping here on purpose: mapping is decided in the analysis
step after seeing each model's actual label set.
"""
import json, os, sys, time
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
MODELS = [
    ("yaya36095/ai-source-detector", os.path.expanduser("~/workspace/human-cert/models/yaya")),
    ("hungnh1201/ai-image-detector", os.path.expanduser("~/workspace/human-cert/models/hung")),
    ("king1oo1/deepfake-model", os.path.expanduser("~/workspace/human-cert/models/king")),
]

from transformers import pipeline

manifest = json.load(open(os.path.join(BASE, "set", "manifest.json")))
results = {}
only = sys.argv[1] if len(sys.argv) > 1 else None

for model_id, local_dir in MODELS:
    if only and only not in model_id:
        continue
    print(f"=== loading {model_id} from {local_dir} ===", flush=True)
    t0 = time.time()
    clf = pipeline("image-classification", model=local_dir, device=-1)
    print("id2label:", clf.model.config.id2label, flush=True)
    results[model_id] = {"id2label": clf.model.config.id2label, "scores": {}}
    for m in manifest:
        path = os.path.join(BASE, m["file"])
        img = Image.open(path).convert("RGB")
        out = clf(img, top_k=None)
        results[model_id]["scores"][m["id"]] = [
            {"label": o["label"], "score": round(float(o["score"]), 4)} for o in out
        ]
        top = max(out, key=lambda o: o["score"])
        print(f"{m['id']} truth={m['truth']:5s} top={top['label']} {top['score']:.3f}", flush=True)
    print(f"--- {model_id} done in {time.time()-t0:.0f}s ---", flush=True)
    json.dump(results, open(os.path.join(BASE, "results", "raw_scores.json"), "w"), indent=1)

print("saved results/raw_scores.json")
