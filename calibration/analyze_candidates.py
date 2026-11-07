#!/usr/bin/env python3
"""Candidate scanner analysis, same basis as analyze.py (threshold 0.5).
Merges the baseline results/raw_scores.json (yaya, hung, king) with the
candidate raw scores in results/candidates/raw_scores_<short>.json.
Prints: per-model confusion/accuracy, pairwise agreement of each
candidate with yaya and king, and an ensemble table (majority vote and
mean score) for every combo the task requires.
"""
import json, os
from itertools import combinations

BASE = os.path.dirname(os.path.abspath(__file__))
manifest = {m["id"]: m for m in json.load(open(os.path.join(BASE, "set", "manifest.json")))}
raw = json.load(open(os.path.join(BASE, "results", "raw_scores.json")))
CAND_DIR = os.path.join(BASE, "results", "candidates")
for fn in sorted(os.listdir(CAND_DIR)):
    if fn.startswith("raw_scores_") and fn.endswith(".json"):
        d = json.load(open(os.path.join(CAND_DIR, fn)))
        for mid, entry in d.items():
            if "scores" in entry:
                raw[mid] = entry

AI_WORDS = ("ai", "artificial", "fake", "generated", "synthetic", "stable", "midjourney",
            "dalle", "dall", "sdxl", "diffusion", "other_ai", "label_1")
HUMAN_WORDS = ("real", "human", "natural", "authentic", "label_0")

def ai_prob(scores):
    total_ai = 0.0
    used = []
    for s in scores:
        lab = s["label"].lower().replace(" ", "_").replace("-", "_")
        if lab == "hum":
            used.append((s["label"], "human", s["score"]))
        elif any(w in lab for w in HUMAN_WORDS) and "fake" not in lab:
            used.append((s["label"], "human", s["score"]))
        elif any(w in lab for w in AI_WORDS):
            used.append((s["label"], "ai", s["score"]))
            total_ai += s["score"]
        else:
            used.append((s["label"], "UNKNOWN", s["score"]))
    return total_ai, used

def confusion(verdicts):
    tp = fp = tn = fn = 0
    for img_id, is_ai in verdicts.items():
        truth_ai = manifest[img_id]["truth"] == "ai"
        if is_ai and truth_ai: tp += 1
        elif is_ai and not truth_ai: fp += 1
        elif not is_ai and truth_ai: fn += 1
        else: tn += 1
    acc = (tp + tn) / max(1, tp + fp + tn + fn)
    return {"TP": tp, "FP": fp, "TN": tn, "FN": fn, "accuracy": round(acc, 3)}

models = list(raw.keys())
per_model_prob = {}
print("== label mappings (audit) ==")
for mid in models:
    sample_id = next(iter(raw[mid]["scores"]))
    _, used = ai_prob(raw[mid]["scores"][sample_id])
    print(mid, "->", used)
    per_model_prob[mid] = {i: ai_prob(s)[0] for i, s in raw[mid]["scores"].items()}

print("\n== per-model results (threshold 0.5) ==")
model_acc = {}
for mid in models:
    verdicts = {i: p >= 0.5 for i, p in per_model_prob[mid].items()}
    c = confusion(verdicts)
    model_acc[mid] = c["accuracy"]
    print(f"{mid}: {c}")
    print("   wrong on:", [i for i, v in verdicts.items() if v != (manifest[i]["truth"] == "ai")])

print("\n== pairwise agreement rate (all pairs) ==")
agree = {}
for a, b in combinations(models, 2):
    va = {i: p >= 0.5 for i, p in per_model_prob[a].items()}
    vb = {i: p >= 0.5 for i, p in per_model_prob[b].items()}
    agree[(a, b)] = round(sum(1 for i in va if va[i] == vb[i]) / len(va), 3)
    print(f"{a} vs {b}: {agree[(a, b)]:.2f}")

ids = list(manifest.keys())
def ensemble(mids):
    k = len(mids)
    need = k // 2 + 1
    maj, soft = {}, {}
    for i in ids:
        maj[i] = sum(per_model_prob[m][i] >= 0.5 for m in mids) >= need
        soft[i] = (sum(per_model_prob[m][i] for m in mids) / k) >= 0.5
    return confusion(maj), confusion(soft), \
        [i for i in ids if maj[i] != (manifest[i]["truth"] == "ai")], \
        [i for i in ids if soft[i] != (manifest[i]["truth"] == "ai")]

YAYA = "yaya36095/ai-source-detector"
HUNG = "hungnh1201/ai-image-detector"
KING = "king1oo1/deepfake-model"
CANDS = [m for m in models if m not in (YAYA, HUNG, KING)]

combos = [("baseline {yaya,hung,king}", [YAYA, HUNG, KING])]
for c in CANDS:
    combos.append((f"{{yaya,{c.split('/')[0]},king}}", [YAYA, c, KING]))
for c in CANDS:
    combos.append((f"4-model {{yaya,hung,{c.split('/')[0]},king}}", [YAYA, HUNG, c, KING]))
if len(CANDS) >= 2:
    combos.append(("4-model license-clean {yaya," + ",".join(c.split("/")[0] for c in CANDS[:2]) + ",king}",
                   [YAYA] + CANDS[:2] + [KING]))

print("\n== ensembles ==")
summary = {}
for name, mids in combos:
    cmaj, csoft, wmaj, wsoft = ensemble(mids)
    summary[name] = (cmaj["accuracy"], csoft["accuracy"])
    print(f"{name}\n  majority: {cmaj} wrong={wmaj}\n  mean    : {csoft} wrong={wsoft}")

print("\n== per-image P(AI) detail ==")
hdr = " ".join(f"{m.split('/')[0][:8]:>8s}" for m in models)
print(f"id truth {hdr}")
for i in ids:
    row = " ".join(f"{per_model_prob[m][i]:8.2f}" for m in models)
    print(f"{i} {manifest[i]['truth']:5s} {row}")

json.dump({"model_acc": model_acc,
           "agreement": {f"{a} vs {b}": v for (a, b), v in agree.items()},
           "ensembles": {k: {"majority_acc": v[0], "mean_acc": v[1]} for k, v in summary.items()}},
          open(os.path.join(CAND_DIR, "summary.json"), "w"), indent=1)
print("\nsaved results/candidates/summary.json")
