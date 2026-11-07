#!/usr/bin/env python3
"""Analysis for the mini calibration spike.
Reads results/raw_scores.json + set/manifest.json.
Per model: maps raw labels to an AI-probability (mapping printed for audit),
then computes confusion matrix, accuracy, pairwise agreement, and
ensemble (majority vote and mean-score) accuracy vs the best single model.
"""
import json, os
from itertools import combinations

BASE = os.path.dirname(os.path.abspath(__file__))
manifest = {m["id"]: m for m in json.load(open(os.path.join(BASE, "set", "manifest.json")))}
raw = json.load(open(os.path.join(BASE, "results", "raw_scores.json")))

AI_WORDS = ("ai", "artificial", "fake", "generated", "synthetic", "stable", "midjourney",
            "dalle", "dall", "sdxl", "diffusion", "other_ai", "label_1")
HUMAN_WORDS = ("real", "human", "natural", "authentic", "label_0")

def ai_prob(model_id, scores):
    """Return P(ai) for one image under one model, with the mapping used."""
    total_ai = 0.0
    used = []
    for s in scores:
        lab = s["label"].lower().replace(" ", "_").replace("-", "_")
        if any(w in lab for w in HUMAN_WORDS) and not any(w in lab for w in ("fake",)):
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
    _, used = ai_prob(mid, raw[mid]["scores"][sample_id])
    print(mid, "->", used)
    per_model_prob[mid] = {i: ai_prob(mid, s)[0] for i, s in raw[mid]["scores"].items()}

print("\n== per-model results (threshold 0.5) ==")
model_acc = {}
for mid in models:
    verdicts = {i: p >= 0.5 for i, p in per_model_prob[mid].items()}
    c = confusion(verdicts)
    model_acc[mid] = c["accuracy"]
    print(f"{mid}: {c}")
    wrong = [i for i, v in verdicts.items() if v != (manifest[i]['truth'] == 'ai')]
    print("   wrong on:", wrong)

print("\n== pairwise agreement rate ==")
for a, b in combinations(models, 2):
    va = {i: p >= 0.5 for i, p in per_model_prob[a].items()}
    vb = {i: p >= 0.5 for i, p in per_model_prob[b].items()}
    agree = sum(1 for i in va if va[i] == vb[i]) / len(va)
    print(f"{a.split('/')[0]} vs {b.split('/')[0]}: {agree:.2f}")

print("\n== ensemble ==")
ids = list(manifest.keys())
maj = {}
soft = {}
for i in ids:
    votes = [per_model_prob[m][i] >= 0.5 for m in models]
    maj[i] = sum(votes) >= 2
    soft[i] = (sum(per_model_prob[m][i] for m in models) / len(models)) >= 0.5
print("majority vote:", confusion(maj), "wrong:", [i for i in ids if maj[i] != (manifest[i]['truth'] == 'ai')])
print("mean score   :", confusion(soft), "wrong:", [i for i in ids if soft[i] != (manifest[i]['truth'] == 'ai')])
print("\nbest single model accuracy:", max(model_acc.values()), "| models:", model_acc)

print("\n== per-image detail ==")
for i in ids:
    row = " ".join(f"{per_model_prob[m][i]:.2f}" for m in models)
    print(f"{i} truth={manifest[i]['truth']:5s} [{row}] kind={manifest[i]['kind'][:60]}")
