#!/usr/bin/env python3
"""Run abacusai/Smaug-AI-Image-Detector over the SAME 20-image mini set.
This model is NOT an image-classification pipeline: it is a
SentenceTransformer (EmbeddingGemma2 backbone + Pooling + Normalize +
Dense 768->1) whose encode() returns one logit per crop; the authors'
own smaug_image_detect.py (downloaded with the model) converts it to
P(AI) = sigmoid(mean of 3 crop logits). That published output IS the
score, so it is stored in the same raw format as two labels:
ai = P(AI), human = 1 - P(AI). id2label does not exist for this model;
the mapping comes from the authors' docstring, not from a label guess.
"""
import importlib.util, json, os, sys, time
from PIL import Image

BASE = os.path.dirname(os.path.abspath(__file__))
LOCAL = os.path.expanduser("~/workspace/human-cert/models/smaug")
MODEL_ID = "abacusai/Smaug-AI-Image-Detector"
OUT = os.path.join(BASE, "results", "candidates", "raw_scores_smaug.json")

spec = importlib.util.spec_from_file_location("smaug_image_detect", os.path.join(LOCAL, "smaug_image_detect.py"))
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

manifest = json.load(open(os.path.join(BASE, "set", "manifest.json")))
print(f"=== loading {MODEL_ID} from {LOCAL} (SentenceTransformer, cpu) ===", flush=True)
t0 = time.time()
det = mod.SmaugImageDetect.from_pretrained(LOCAL, device="cpu")
print(f"loaded in {time.time()-t0:.0f}s; id2label: none (direct P(AI) output)", flush=True)

imgs, ids = [], []
for m in manifest:
    imgs.append(Image.open(os.path.join(BASE, m["file"])).convert("RGB"))
    ids.append(m["id"])
t0 = time.time()
probs = det(imgs, crops=3, batch_size=8)
print(f"scored {len(imgs)} images in {time.time()-t0:.0f}s", flush=True)

scores = {}
for m, p in zip(manifest, probs):
    p = round(float(p), 4)
    scores[m["id"]] = [{"label": "ai", "score": p}, {"label": "human", "score": round(1 - p, 4)}]
    print(f"{m['id']} truth={m['truth']:5s} P(AI)={p:.3f}", flush=True)

entry = {"id2label": {"0": "ai", "1": "human"},
         "mapping_note": "No classifier labels; authors' script returns P(AI) directly. Stored as ai=P(AI), human=1-P(AI).",
         "scores": scores}
json.dump({MODEL_ID: entry}, open(OUT, "w"), indent=1)
print("saved", OUT, flush=True)
