# Failure catalog: every measured error of the Humanmark scanner panel (2026-11-07)

This catalog exists on purpose. Kokoron's rule for this project is that
failures are recorded, not hidden, and this file is the literature of
everything the scanners got wrong in both calibration studies. Every
number here can be re-checked against the raw scores in the same
folders:

- Original spike (yaya, hung, king): `calibration/results/raw_scores.json`,
  analysis in `calibration/results/analysis.txt`, gate record in
  `calibration/results/GATE-DECISION.md`.
- Candidate study (umm, Smaug, Ateeqq): `calibration/results/candidates/raw_scores_umm.json`,
  `raw_scores_smaug.json`, `raw_scores_ateeqq.json`, analysis in
  `calibration/results/candidates/RESULTS.md`.
- The image set and its ground truth: `calibration/set/manifest.json`
  (10 human, 10 AI, ground truth certain by source).

Method, identical for both studies: a model's verdict on an image is
AI when its P(AI) is at least 0.5, human below 0.5. P(AI) is computed
from the raw label scores with the mapping in `calibration/analyze.py`
(AI labels summed; Ateeqq's short label "hum" counts as human; Smaug
has no labels and returns P(AI) directly). A wrong verdict on a human
image is a false positive (FP, a false accusation). A wrong verdict
on an AI image is a false negative (FN, a miss). n = 20 throughout:
these numbers gate design and license decisions, they are not a
public accuracy claim.

## Scoreboard and error direction

| Model | License | Acc | TP | FP | TN | FN | Error direction |
|---|---|---|---|---|---|---|---|
| yaya36095/ai-source-detector (Scanner A) | apache-2.0 | 0.50 | 10 | 10 | 0 | 0 | Accuses everything. Every human work flagged, no AI missed. Its "real" class behaves like "real photograph", so paintings and drawn work read as not-real. |
| hungnh1201/ai-image-detector (old Scanner B, removed) | cc-by-nc-3.0 | 0.75 | 7 | 2 | 8 | 3 | Mixed, leans accusing on stylized human work. Removed for its non-commercial license, not for its score. |
| king1oo1/deepfake-model (Scanner C) | apache-2.0 | 0.70 | 5 | 1 | 9 | 5 | Protects humans, passes AI. Trained for photo fakery, so AI paintings and illustrations pass as real. |
| umm-maybe/AI-image-detector (Scanner B since 2026-11-07) | cc-by-4.0 | 0.75 | 5 | 0 | 10 | 5 | Never accuses a human (FP 0, the only model with a clean human side). All its errors are missed AI images. |
| abacusai/Smaug-AI-Image-Detector (candidate, rejected) | apache-2.0 | 0.75 | 10 | 5 | 5 | 0 | Catches every AI image, accuses half the humans, including all three Squeek design files. |
| Ateeqq/ai-vs-human-image-detector (candidate, rejected) | apache-2.0 | 0.65 | 9 | 6 | 4 | 1 | Leans AI on almost everything, weakest candidate. |

Panels (majority vote; 3-model panels need 2 of 3, 5-model panels need 3 of 5):

| Panel | Acc | TP | FP | TN | FN | Wrong on |
|---|---|---|---|---|---|---|
| {yaya, hung, king} original panel (has the NC model) | 0.85 | 9 | 2 | 8 | 1 | a02, h04, h10 |
| {yaya, umm, king} current panel, license-clean | 0.85 | 8 | 1 | 9 | 2 | a01, a05, h10 |
| {yaya, umm, king, Smaug, Ateeqq} license-clean 5-model | 0.80 | 10 | 4 | 6 | 0 | h02, h08, h09, h10 |
| {yaya, hung, king, Smaug, umm} 5-model with the NC model | 0.95 | 10 | 1 | 9 | 0 | h10 |

## Every wrong image, named per model

False accusations (human works called AI). These are the expensive
errors for a certificate product, because the accused party is a real
artist:

- yaya flags all ten human works: h01, h02, h03, h04, h05, h06, h07,
  h08, h09, h10. Confidence is high while wrong: 0.75 to 0.87 P(AI)
  on the classics.
- hung flags h04 (The Scream, P(AI) 1.00) and h10 (headline poster,
  0.88).
- king flags only h10 (0.94).
- umm flags none. Zero false accusations in the whole study.
- Smaug flags h02 (Great Wave, 1.00), h05 (The Kiss, 0.90), h08
  (battle preview mock, 1.00), h09 (hamster design sheet, 1.00) and
  h10 (headline poster, 0.91).
- Ateeqq flags h02 (1.00), h04 (1.00), h06 (Impression, Sunrise, 0.99),
  h08 (1.00), h09 (1.00) and h10 (1.00).

Misses (AI images called human):

- yaya misses none.
- hung misses a02 (vaporwave sunset, P(AI) 0.00), a08 (pixel art robot
  cat, 0.43) and a10 (food photo burger, 0.00).
- king misses a01 (Commons banner graphic, 0.46), a02 (0.24), a04
  (opera digital painting, 0.23), a05 (anime illustration, 0.44) and
  a06 (photorealistic fisherman portrait, 0.34).
- umm misses a01 (0.00), a05 (0.01), a07 (fantasy floating islands,
  0.40), a08 (0.05) and a10 (0.10).
- Smaug misses none.
- Ateeqq misses only a04 (0.00).

## Full per-image table

P(AI) per model at threshold 0.5. OK = correct verdict, FP = human
wrongly called AI, FN = AI wrongly called human. Panels: B =
{yaya, hung, king} original, C = {yaya, umm, king} current, C5 =
license-clean 5-model, H5 = 5-model with hung.

| ID | Truth | Category | yaya | hung | king | umm | Smaug | Ateeqq | B | C | C5 | H5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| a01 | ai | AI graphic, Commons category | 0.87 OK | 1.00 OK | 0.46 FN | 0.00 FN | 0.99 OK | 1.00 OK | OK | FN | OK | OK |
| a02 | ai | AI vaporwave sunset, Commons | 0.80 OK | 0.00 FN | 0.24 FN | 0.99 OK | 1.00 OK | 1.00 OK | FN | OK | OK | OK |
| a03 | ai | Midjourney, Theatre D'opera Spatial | 0.87 OK | 1.00 OK | 0.90 OK | 0.86 OK | 1.00 OK | 1.00 OK | OK | OK | OK | OK |
| a04 | ai | self-generated opera digital painting | 0.86 OK | 0.77 OK | 0.23 FN | 0.87 OK | 1.00 OK | 0.00 FN | OK | OK | OK | OK |
| a05 | ai | self-generated anime illustration | 0.77 OK | 1.00 OK | 0.44 FN | 0.01 FN | 1.00 OK | 1.00 OK | OK | FN | OK | OK |
| a06 | ai | self-generated photorealistic portrait | 0.89 OK | 0.97 OK | 0.34 FN | 0.53 OK | 1.00 OK | 1.00 OK | OK | OK | OK | OK |
| a07 | ai | self-generated fantasy digital painting | 0.87 OK | 0.99 OK | 0.99 OK | 0.40 FN | 1.00 OK | 1.00 OK | OK | OK | OK | OK |
| a08 | ai | self-generated pixel art (trap) | 0.86 OK | 0.43 FN | 0.92 OK | 0.05 FN | 1.00 OK | 1.00 OK | OK | OK | OK | OK |
| a09 | ai | self-generated 3D render style (trap) | 0.86 OK | 1.00 OK | 0.94 OK | 0.79 OK | 1.00 OK | 1.00 OK | OK | OK | OK | OK |
| a10 | ai | self-generated food photo style | 0.87 OK | 0.00 FN | 0.72 OK | 0.10 FN | 1.00 OK | 0.99 OK | OK | OK | OK | OK |
| h01 | human | Van Gogh, The Starry Night (pre-1900) | 0.84 FP | 0.00 OK | 0.06 OK | 0.27 OK | 0.01 OK | 0.00 OK | OK | OK | OK | OK |
| h02 | human | Hokusai, The Great Wave (pre-1900) | 0.80 FP | 0.00 OK | 0.02 OK | 0.04 OK | 1.00 FP | 1.00 FP | OK | OK | FP | OK |
| h03 | human | Vermeer, Girl with a Pearl Earring (pre-1900) | 0.87 FP | 0.00 OK | 0.08 OK | 0.01 OK | 0.00 OK | 0.00 OK | OK | OK | OK | OK |
| h04 | human | Munch, The Scream (pre-1900) | 0.85 FP | 1.00 FP | 0.03 OK | 0.01 OK | 0.01 OK | 1.00 FP | FP | OK | OK | OK |
| h05 | human | Klimt, The Kiss (pre-1900) | 0.84 FP | 0.00 OK | 0.01 OK | 0.48 OK | 0.90 FP | 0.00 OK | OK | OK | OK | OK |
| h06 | human | Monet, Impression, Sunrise (pre-1900) | 0.76 FP | 0.02 OK | 0.32 OK | 0.02 OK | 0.00 OK | 0.99 FP | OK | OK | OK | OK |
| h07 | human | Leonardo, Virgin and Child with St Anne (pre-1900) | 0.87 FP | 0.00 OK | 0.20 OK | 0.01 OK | 0.00 OK | 0.00 OK | OK | OK | OK | OK |
| h08 | human | Squeek Arena battle preview mock, code-drawn | 0.75 FP | 0.04 OK | 0.16 OK | 0.37 OK | 1.00 FP | 1.00 FP | OK | OK | FP | OK |
| h09 | human | Squeek Arena hamster design sheet, human pixel art | 0.77 FP | 0.05 OK | 0.42 OK | 0.01 OK | 1.00 FP | 1.00 FP | OK | OK | FP | OK |
| h10 | human | Squeek Arena headline poster v2, code-drawn | 0.86 FP | 0.88 FP | 0.94 FP | 0.05 OK | 0.91 FP | 1.00 FP | FP | FP | FP | FP |

## Failure patterns

1. **Code-drawn human work defeats pixel judgment as a class.** h10,
   the headline poster drawn by code, is called AI by five of six
   models and by every panel composition tested, including the 0.95
   panel. h08 and h09, the other two code-drawn or pixel design
   files, are flagged by yaya, Smaug and Ateeqq. No threshold tuning
   fixes this, because the pixels of a program-drawn poster genuinely
   resemble generated output. The only evidence that clears h10 is
   process evidence (the generator scripts, the re-render, the signed
   attestation), which is exactly the second axis of this system.
   This single image is the strongest argument in the project.
2. **One scanner accuses everything.** yaya's false positive rate on
   human work is 100 percent while its miss rate is 0. As a lone
   detector it is a coin flip (0.50). Inside an ensemble it still
   earns its seat because it is right exactly where others are wrong
   (a02), but no verdict may ever rest on it alone.
3. **Expressive classic art reads as AI artifacts.** The Scream (h04)
   is flagged by yaya, hung (at 1.00) and Ateeqq. Heavy texture and
   distortion in real paintings resemble generation artifacts to
   models trained mostly on photographs and digital output.
4. **Photorealistic and stylized AI passes as human.** The food photo
   (a10) is missed by hung (0.00) and umm (0.10); the vaporwave sunset
   (a02) by hung (0.00) and king (0.24); the anime illustration (a05)
   by king (0.44) and umm (0.01). king, trained on photo fakery,
   misses five AI images, all of them paintings or illustrations.
5. **The accusing candidates accuse the artist's own files.** Smaug
   and Ateeqq both flag all three Squeek design files (h08, h09, h10)
   at 0.91 to 1.00. A panel built from them would systematically
   accuse exactly the kind of digital artist this product exists to
   certify. This, plus the ensemble drop, is why both were rejected
   as Scanner B despite clean licenses.
6. **Error direction is a design choice, not a detail.** umm and
   Smaug both score 0.75 alone with opposite failure shapes: umm
   never accuses a human and misses half the AI; Smaug never misses
   AI and accuses half the humans. For a certificate, a miss costs
   little (the process axis can still catch it) and a false
   accusation costs trust, so the panel keeps the model that errs
   toward silence.

## Honest summary lines

- No license-clean panel beats 0.85 on this 20-image set. The swap to
  umm holds accuracy at 0.85 while removing the non-commercial model;
  it does not raise it.
- Every panel measured above 0.85 (the 0.90 four-model and the 0.95
  five-model) includes hung, the CC BY-NC 3.0 model that had to
  leave. Quoting those numbers for the current product would be
  dishonest, so they are recorded here as history, not as claims.
- Pixel-only judgment is structurally blind to process. It cannot
  distinguish a human who drew with code from a generator, and it
  cannot see a timelapse, a layered file, or a redraw. That blindness
  is measured above, not asserted: h10 defeats every panel.
- The set is small (n = 20) and heavy on classic paintings. A full
  100-image calibration with modern digital art on the human side is
  still required before any public accuracy claim, and this catalog
  will be extended, not replaced, when that set runs.
