# Calibration Spike - Gate Decision (2026-11-07)

Set: 20 images, 10 human + 10 AI, ground truth certain (pre-1900 classics from
Wikimedia Commons, Squeek Arena human-authored design files, Commons-categorized
AI images, self-generated AI images including trap categories pixel art and
3D render style). Raw scores: results/raw_scores.json. Analysis: results/analysis.txt.
Models run locally from pinned files in ~/workspace/human-cert/models/
(HF hub HEAD requests timed out from this VM; direct GET via mirror worked).

## Per-model accuracy at threshold 0.5 (P(AI) from each model's own labels)

| Model | Accuracy | TP | FP | TN | FN | Note |
|---|---|---|---|---|---|---|
| yaya36095/ai-source-detector | 0.50 | 10 | 10 | 0 | 0 | Flags EVERYTHING as AI, classics at 0.76-0.87 confidence. Its "real" class means real photograph, so human paintings read as not-real. Useless alone as a binary detector. |
| hungnh1201/ai-image-detector | 0.75 | 7 | 2 | 8 | 3 | Best single. Misses vaporwave AI, pixel art AI, food photo AI. Flags The Scream and the code-drawn poster as AI. |
| king1oo1/deepfake-model | 0.70 | 5 | 1 | 9 | 5 | Best on human works (9/10). Trained for photo fakery, so AI paintings pass as Real (5 misses). |

## Ensemble

- Pairwise agreement: yaya-hung 0.45, yaya-king 0.30, hung-king 0.65.
  Low agreement = genuine diversity, errors are not fully correlated.
- Majority vote: accuracy 0.85 (TP 9, FP 2, TN 8, FN 1). Wrong: a02, h04, h10.
- Mean score: accuracy 0.85, same errors.
- Ensemble beats best single model by 10 points on this set (n=20, small sample).

## Key findings

1. The ensemble hypothesis holds on the mini spike: diverse weak scanners
   combined beat every single scanner.
2. All three scanners agree wrongly only on h10, kokoron's code-drawn poster
   (0.86 / 0.88 / 0.94 AI). A program-drawn human work is indistinguishable
   from AI output by pixels alone. Only process evidence (source code, git
   history, layered files) can clear it. This is the strongest demo case for
   the certificate's second axis.
3. The Scream (h04) fools 2 of 3 scanners. Expressive human texture reads as
   AI artifacts to pixel models.
4. Yaya alone demonstrates exactly the failure kokoron predicted: online
   detectors call everything AI. In the swarm it still earns its seat: it was
   the only scanner right on a02.

## Gate verdict

BUILD, with a process-evidence-first design:

- Scanner ensemble is one signal, never the verdict. Pixel-only judgment
  caps at about 0.85 here and fails hardest on exactly the works digital
  artists actually submit (code-drawn, pixel art, stylized).
- The Process axis (timelapse, layered source, live redraw, repo history)
  is the primary axis; the Human axis (passkey, aged account, live challenge)
  stays as designed in the brief.
- Yaya's role: source classifier inside the panel with its bias documented
  in the calibration report, not a standalone judge.
- Full 100-image calibration set (with modern digital art as the human class,
  not only classics) remains required before any public accuracy claim; the
  mini spike only gates the build decision, per the spike plan.
