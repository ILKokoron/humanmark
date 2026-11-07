# Candidate Scanner B replacement test (2026-11-07)

Same 20-image mini calibration set as the original spike (10 human, 10 AI,
set/manifest.json), same threshold 0.5 basis as analyze.py, same P(AI)
mapping rules. Baseline to beat or match: ensemble {yaya, hung, king}
at 0.85 (majority vote and mean score). hung must leave for license
reasons, so every recommendation below is license-clean.

Raw scores: raw_scores_umm.json, raw_scores_ateeqq.json,
raw_scores_smaug.json in this folder. Full analyzer output:
analysis_candidates.txt. Extra combos: extra_combos.txt.
Runners: ../../run_candidates.py and ../../run_smaug.py,
analyzer: ../../analyze_candidates.py.

## Licenses (verified from the HF API on 2026-11-07)

| Model | License | Commercial use |
|---|---|---|
| yaya36095/ai-source-detector (current Scanner A) | apache-2.0 | yes |
| hungnh1201/ai-image-detector (current Scanner B) | cc-by-nc-3.0 | NO, this is why it is being replaced |
| king1oo1/deepfake-model (current Scanner C) | apache-2.0 | yes |
| umm-maybe/AI-image-detector | cc-by-4.0 | yes, with attribution |
| Ateeqq/ai-vs-human-image-detector | apache-2.0 | yes |
| abacusai/Smaug-AI-Image-Detector | apache-2.0 | yes |

All three candidates are license-clean. None had to be flagged unusable
on license grounds.

## How each candidate was run

All models were downloaded as pinned local files from the HF mirror
(HEAD requests to the hub time out from this VM) and run fully offline.

- umm-maybe: SwinForImageClassification, weights in pytorch_model.bin.
  id2label {0: artificial, 1: human}, the same label set as hung (hung
  is a fine-tune of this model family). Standard image-classification
  pipeline, about 1.5 s per image on CPU.
- Ateeqq: SiglipForImageClassification. id2label {0: ai, 1: hum}. The
  short label "hum" was mapped to human (documented in the analyzer);
  P(AI) is the score of the "ai" label. Standard pipeline, about 1 s
  per image.
- abacusai/Smaug: NOT a classification pipeline. It is a
  SentenceTransformer (EmbeddingGemma2 backbone, pooling, normalize,
  dense head 768 to 1 logit) with no id2label. It was run with the
  authors' own smaug_image_detect.py shipped in the repo, which returns
  P(AI) directly as sigmoid of the mean logit over 3 crops of the
  image. Stored in raw form as ai = P(AI), human = 1 - P(AI). Setup
  cost was real: sentence-transformers and torchvision had to be
  installed into the venv, the 3_Dense folder and the chat template
  file are easy to miss in the repo file list, and scoring took 641 s
  for 20 images on this VM (about 32 s per image, versus 1 to 2 s for
  the other models).

## Per-model results (threshold 0.5)

| Model | Accuracy | TP | FP | TN | FN | Wrong on |
|---|---|---|---|---|---|---|
| yaya36095 (Scanner A, current) | 0.50 | 10 | 10 | 0 | 0 | all 10 human |
| hungnh1201 (Scanner B, NC, leaving) | 0.75 | 7 | 2 | 8 | 3 | a02, a08, a10, h04, h10 |
| king1oo1 (Scanner C, current) | 0.70 | 5 | 1 | 9 | 5 | a01, a02, a04, a05, a06, h10 |
| umm-maybe | 0.75 | 5 | 0 | 10 | 5 | a01, a05, a07, a08, a10 |
| Ateeqq | 0.65 | 9 | 6 | 4 | 1 | a04, h02, h04, h06, h08, h09, h10 |
| abacusai/Smaug | 0.75 | 10 | 5 | 5 | 0 | h02, h05, h08, h09, h10 |

Reading: umm never flags a human work (FP 0, the only model besides
none with a clean human side) but misses half the AI images. Smaug
catches every AI image (FN 0) but flags half the human works,
including all three of kokoron's own design files (h08, h09, h10).
Ateeqq leans AI on almost everything and is the weakest candidate.

## Pairwise agreement (share of identical verdicts at 0.5)

| Candidate | vs yaya | vs king |
|---|---|---|
| umm-maybe | 0.25 | 0.65 |
| Ateeqq | 0.75 | 0.55 |
| abacusai/Smaug | 0.75 | 0.55 |
| hung (reference) | 0.45 | 0.65 |

umm disagrees with yaya the most of any model measured so far (0.25,
even lower than hung at 0.45), which is what an ensemble wants: its
errors land where the others are right. Ateeqq and Smaug mostly echo
yaya (0.75), so they add little diversity.

## Ensembles

Majority rule: 3-model panels need 2 of 3, 4-model panels need 3 of 4,
5-model panels need 3 of 5. Mean rule: mean P(AI) at 0.5.

### Three-model panels (direct Scanner B swap)

| Panel | Majority acc | Mean acc | Wrong (majority) |
|---|---|---|---|
| {yaya, hung, king} baseline, has NC model | 0.85 | 0.85 | a02, h04, h10 |
| {yaya, umm, king} license-clean | 0.85 | 0.85 | a01, a05, h10 |
| {yaya, Smaug, king} license-clean | 0.75 | 0.75 | h02, h05, h08, h09, h10 |
| {yaya, Ateeqq, king} license-clean | 0.65 | 0.65 | a04, h02, h04, h06, h08, h09, h10 |

### Four-model panels including hung (reference only, still NC-tainted)

| Panel | Majority acc | Mean acc |
|---|---|---|
| {yaya, hung, Smaug, king} | 0.90 | 0.90 |
| {yaya, hung, umm, king} | 0.70 | 0.90 |
| {yaya, hung, Ateeqq, king} | 0.80 | 0.75 |

### Four-model panels excluding hung (license-clean)

| Panel | Majority acc | Mean acc |
|---|---|---|
| {yaya, Smaug, umm, king} | 0.85 | 0.80 |
| {yaya, Ateeqq, umm, king} | 0.80 | 0.75 |
| {yaya, Ateeqq, Smaug, king} | 0.75 | 0.75 |

### Five-model panels (from extra_combos.txt)

| Panel | Majority acc | Mean acc |
|---|---|---|
| {yaya, hung, Smaug, umm, king} has NC model | 0.95 | 0.95 |
| {yaya, Ateeqq, Smaug, umm, king} license-clean | 0.80 | 0.80 |

Honest note: every combo that beats 0.85 (the 0.90 and 0.95 rows)
includes hung, the NC-licensed model that has to go. On this 20-image
set, removing hung costs real accuracy that no single clean candidate
fully repays inside a bigger panel. And h10, the code-drawn poster,
is still called AI by every panel above, exactly as the gate record
said: pixels alone cannot clear it, process evidence has to.

## Recommendation

Replace Scanner B (hungnh1201/ai-image-detector, cc-by-nc-3.0) with
umm-maybe/AI-image-detector (cc-by-4.0, attribution required).

- {yaya, umm, king} scores 0.85 majority and 0.85 mean, identical to
  the current baseline, so the swap is accuracy-neutral on this set
  while removing the only NC license in the stack.
- Its error profile is arguably better for a certificate product: the
  ensemble false positives drop from 2 (h04, h10) to 1 (h10), and umm
  itself never flags a human work. Wrongly accusing a human artist is
  the expensive error direction for Humanmark; missing an AI image is
  what the process-evidence axis exists to catch.
- Best diversity measured: agreement with yaya is 0.25, the lowest of
  any pair in the whole study.
- Drop-in cost is minimal: same Swin architecture, same label names
  (artificial, human), same pipeline code path as hung, same speed.
- Caveat to record, not hide: umm is the parent model of the same
  family hung was fine-tuned from, so the swap keeps one model lineage
  in the panel. The diversity numbers above are measured against yaya
  and king, not against hung, and they are strong. If a future
  calibration on the full 100-image set wants a second clean scanner
  from a different family, Smaug is the candidate to revisit, but only
  where its roughly 32 s per image CPU cost is acceptable.

Rejected: Ateeqq (ensemble drops to 0.65, flags human art
aggressively, echoes yaya), Smaug as Scanner B (ensemble drops to
0.75, heavy runtime and fragile loading, flags all of kokoron's own
design files). Smaug stays interesting as an optional fourth opinion
for photo-like images, not as a panel member at this set size.

Sample size warning, unchanged from the gate record: n = 20. These
numbers gate a license decision, they do not support a public accuracy
claim. The full 100-image calibration is still required for that.
