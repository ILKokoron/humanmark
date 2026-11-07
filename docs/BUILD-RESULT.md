# Humanmark build result (2026-11-07)

Status per deliverable, with every claim below verified by reading state
back from chain or from the service, never from a printed success line
alone. Explorer links use https://testnet.nearblocks.io/txns/<tx-hash>.

## 1. Contract: DONE, live and verified

- Address: `humanmark.bindingvow1106.testnet` (NEAR testnet)
- Wasm: 438,075 bytes, sha256 `72a44e7d0011772c51e011d0f9e5d492b8b3fe8ab48a35568dc079cd1232310c` (`contract/out/humanmark.wasm`, also in the repo)
- Unit tests: 10 of 10 passed (fee floor, unknown item, pass flow with cert mint, 2-of-5 item does not count, fail flow, wrong-salt reveal, non-examiner commit, early finalize, soulbound transfer panic, zero-reveal refund path)
- Init: owner `bindingvow1106.testnet`, examiners exam1 to exam5, min_fee 0.05 NEAR. Verified by reading back `examiners()`, `min_fee()` and `nft_metadata()` from chain after deploy: all exact. Account read-back after deploy: balance 5.497 NEAR, storage usage 438,556 bytes, code hash present.
- The deploy transaction id was not captured in the CLI output tail; the deployment is proven by the account code hash and the view read-backs above, not by a tx link.
- Accounts created for this build (all under `bindingvow1106.testnet`, keys in the local near CLI keychain): `humanmark` (funded 3 NEAR at creation, tx `Cu2D7QGrGuEsMUVW2Ahae631zE15dMxyqKmxNLsvCVzJ`, plus a 2.5 NEAR top-up for the larger wasm storage stake, tx `Def46z4Wizr1LFQMVqYC3TUGTSfRmgHv2rFfSTnsABBw`), `exam1` to `exam5` (0.3 NEAR each). The parent was topped up from a faucet-funded helper account `humanmarkfund1107.testnet` (7 NEAR, tx `GzN5cmKs16Scc8AWUtfDWcXLPdoj3XhiRKGcvSAfewaK`) because the parent's own balance did not cover a second contract deployment.

## 2. Examiners: DONE

Five Python programs in `agents/`, one per examiner account, each with its
method and verification rule published in its file header, each writing an
open JSON report per case to `agents/reports/` (copies also in
`frontend/reports/` and in the repo). Scanner models load only from the
pinned local dirs in `models/` (HF hub times out from this VM). During the
live run the FastNEAR mirror dropped connections repeatedly; `agents/near.py`
was patched with retry and backoff on RPC reads, after which all runs
completed. Examiner 1 (Scanner A) had already committed and revealed before
the patch, so examiners 2 to 5 were run individually for case-0 rather than
re-running the orchestrator (a second commit would have been rejected
onchain, correctly).

## 3. Demo run: DONE, both directions, verified from chain state

### case-0: PASS (the poster all three scanners call AI)

- Work: Squeek Arena headline poster v2, code-drawn by kokoron's project. Image sha256 `9c89c5231115409407d111ff9ea8625388e423a805ebe91069c336fffaceae67`, identical in the design folder, the calibration set, and the bundle.
- Claimed items: passkey_attestation, layered_source_file, live_redraw. Bundle: the real generator scripts gen-poster.py and gen-poster2.py, the recovered sprite grid, a fresh re-render as the layered export, an ed25519 attestation signed by the artist account over the challenge code (demo stand-in for WebAuthn, verified by the examiners against the account keys onchain), and a challenge detail redraw (region similarity 0.9268 to 0.9284 depending on the examiner's measure).
- Submit tx: `4vt7JToCCfQTgNUewMAfJubxBS7E9qLjPLdZYHRDNyKQ`. Finalize tx: `4n3Ys47vfU7D92rsr95MiY1mQDpRCU4HVkdn3JujX4Qx`.
- Votes (commit / reveal tx): exam1 `5Hh8qgh95uRUPQPk5Ae8M7UUtrWhGc2MQwqmTT51nN6R` / `61qs3vBrfyeTNeX9wMdALw3DWwfGXyM65PJqjck9f5mA`; exam2 `ApxF7RnahkNyRF3YcAZCwAWQt4F93v1tdjL2CZmqiNZx` / `62VPquuDhm5hvMQoK32me1crc9umfyVwcur3o5ddRwAZ`; exam3 `5LKPQzRw9qBdm7VQsjAuztrQf6zU2MC3wNhJzaYRpNiG` / `DmR9mJwpNMBv128UiyVBmMxudQXhYF2qzfqWAQXmx3KN`; exam4 `3TdnsiTidVwjZrXDwaQ8UG3gJEaFmePUesHwAiEP9TP7` / `9kCvCSM1PXuFMctwLMWCERzLbT7DdBt1YECA6sPwGHYd`; exam5 `6sKyUQZB5mQbeo7nz1twajJaxYUJABavb869xfVh6MVZ` / `22hWid8yCJLyo4Vcrp11mJ2ih56RHh7w8YnGXvyxz2tZ`.
- Read-back verdict: status passed, Human 5, Process 5, level 5, `cert_token_id` cert-0, fee_settled true, 5 commits, 5 reveals. `nft_token(cert-0)` returns the certificate owned by `bindingvow1106.testnet` with title "Humanmark Certificate cert-0", description "Certified at level 5 based on this evidence", and the extra JSON carrying case id, both hashes, both axis scores, the level, and all five report hashes. Total supply 1.
- The honest dissent: the Process auditor verified nothing and published why in its report: two bundle files are dated after the final image (the sprite grid was recovered on 2026-11-07 after the original /tmp file was lost, and the layered export is a fresh re-render), and its generator re-run measured 0.8705 against its 0.98 threshold. Note on that number: the auditor re-ran the first-listed generator script, gen-poster.py (the v1 script), so 0.8705 is the v1 render measured against the v2 final; the coordinator's own re-render of gen-poster2.py measures 0.979 against the shipped poster (the committed script's seam drift means it is not bit-exact). Each claimed item still reached 4 of 5 verifications from the other examiners. Scanner pixel scores on this human work were AI-leaning (0.84 to 0.94 range in calibration; recorded per report) and did not gate their item verification, per their published rule.

### case-1: FAIL (AI image, no evidence)

- Work: self-generated AI image from the calibration set (a07, fantasy floating islands), image sha256 `b9f7a50a8eb87012acb93e4449c70fc5474dbb7a0269d07e50ac55fada563a17`. Claimed passkey_attestation, continuous_timelapse and layered_source_file, but the bundle contained no attestation, no timelapse, and no source files.
- Submit tx: `HFn1QSj5BwqpGw2FRZ79Zu4pNBPy14kZgowyYBjukaLY`. Finalize tx: `6ztPGioNcv3gqcU71MoGk4HKwR6xMsAKJn8sppUknxZG`.
- Votes (commit / reveal tx): exam1 `FCfKciLCNy9cw8aeyCzGsAAiGyQNUGqyYrtMGBfRasP3` / `8HXjUUVeSmJC2nmPMaKb6JosG92RKqUznNmFgFPN2R1v`; exam2 `FG5YPuijkjAZKtuR9Az3HPh2sAwxsqAz1Dxbg1YDEs6a` / `FFwnfXjPdW2XWDwRCLLYbkUUdmwhfw8mZncNanaWLgxA`; exam3 `aTiXheSuXWMtgkj1HwF7usfurM7LhHbFLuEhZ1aj6tf` / `7RjUZwmdY3RgiUdf5NPQ4iTETKzhDqZ96aE8u8DmwLjS`; exam4 `2G2zz7hSACEeuWcwF1aDX9pPevP61bGKkyykh14BmfYp` / `8dfdwfq2pqb2EU2C7L1t4gEUnv513sFn4Jp8PoqUDqy6`; exam5 `3PfroqW1StyLSjwLuo4TThGfhZYiyHY9QSn6CeYaFXxe` / `8WV5EetX7nWLYEWSf1JRjhqHrUStTzpUCRvM9WZpCXt2`.
- Read-back verdict: status failed, Human 0, Process 0, level null, cert_token_id null, fee_settled true, 5 reveals all with empty verified lists. `nft_token(cert-1)` is null and total supply stayed 1: no NFT was minted. Scanner pixel scores on the AI image: 0.7778, 0.9913, 0.9902 AI.
- Fee still paid on a fail, proven by balances: each examiner held about 0.3095 NEAR before case-1 (0.3 funding plus their case-0 fee share minus gas) and about 0.3191 NEAR after, a net rise of about 0.0096 NEAR each (the 0.01 share minus their own commit and reveal gas).

## 4. Frontend: BUILT, deployment BLOCKED on Vercel team re-authentication

- Built: `frontend/` (index.html, app.js, wallet.js, style.css) with the four screens from the plan, NEAR Wallet Selector wired identically to the Binding Vow frontend, in-browser SHA-256, the evidence checklist with live axis totals, examiner report links, certificate view, and a functional WebAuthn passkey enrolment panel with feature detection. All 10 demo report JSONs are in `frontend/reports/`. Syntax checked with node; every element id referenced in JS exists in the HTML.
- Blocker, stated precisely: creating the Vercel project through the connected Vercel MCP fails with 403 "Not authorized: Trying to access resource under scope ilkokorons-projects. You must re-authenticate to this scope". Reads work (the binding-vow project and team `team_5tBauaMzEKXI1X6AK4M4CDJu` are visible); writes to that team scope do not. The API's own recovery text says to call `authorize_team_access` and show the user the returned link, but that tool is not present in this connector's available tool list, so the re-authentication cannot be started from this agent. What unblocks it: kokoron re-authenticates the Vercel connection to the ilkokorons-projects team scope (SSO), after which creating project `humanmark` and deploying `frontend/` is a few minutes of work. Planned URL: https://humanmark-ilkokorons-projects.vercel.app
- Consequently the read path has NOT been click-verified in a real browser (there is no deployment to click). The wallet-signed write path is likewise unverified, as expected at this stage. The chain reads the frontend performs were verified against the same FastNEAR RPC from the command line (get_case, get_cases, examiners, min_fee, nft_token all return the demo data).

## 5. Repo and disclosure: DONE

- Public repo: https://github.com/ILKokoron/humanmark (58 files pushed through the GitHub contents API, 0 failures, verified by reading back the repo root listing: README.md, BUILD-PLAN.md, agents, calibration, contract, demo, frontend; docs/BUILD-RESULT.md added with this record). The calibration image set itself is not in the repo (manifest, raw scores, and analysis are); scanner model weights are not in the repo.
- README follows the plan: anti-gadungan rules, the real calibration numbers from the gate record (0.50 / 0.75 / 0.70 single models, 0.85 ensemble, n=20), how to run the examiners, contract address, both demo case ids and tx links, known limits, roadmap, and the cross-disclosure naming Binding Vow.
- Binding Vow disclosure: the matching section was added to Binding Vow's README and pushed to https://github.com/ILKokoron/binding-vow (commit `20d733d7904d03fcc22e6ef32f83e9768c1892e2`), and the local copy at ~/workspace/binding-vow/README.md matches.

## Gaps and incidents, plainly

1. Frontend deployment and browser click-verification are outstanding for the Vercel scope reason above. Everything else is finished.
2. During the swarm self-test, a manual debug re-run of the poster generator (outside the examiner's guarded path) overwrote `~/workspace/squeek-arena/design/headline-poster-v2-led.png`; the poster itself was restored and verified byte-identical (sha256 9c89c523...), and the LED variant was regenerated from it with the script's own LED algorithm, so its pixels derive from the original poster while its byte encoding may differ from the Nov 4 file. The demo bundle does not use the LED variant. The examiner programs themselves back up and restore any absolute output path before re-running a generator.
3. The poster generator scripts read the sprite grid from the absolute path /tmp/momo.json. The grid in the bundle (`demo/pass-bundle/source/momo.json`, recovered from the v1 render) must be copied to /tmp/momo.json before a Process auditor re-run; this is a wart inherited from the original design scripts and is documented in the manifest.
4. The demo attestation is an account-key ed25519 signature standing in for a WebAuthn assertion (documented in the bundle and the README). Real WebAuthn enrolment exists in the frontend; binding an assertion into a case bundle is roadmap work.
5. Reference swarm caveat, same as Binding Vow: one operator runs all five examiner programs and holds their keys in the local keychain. The methods genuinely differ and every report is public, but examiner independence here is methodological, not organizational.

## Addendum (2026-11-07): Scanner B swap, clean-panel demo rerun, failure catalog

Appended after the original record above, which is unchanged. Everything
below was verified by reading chain state or files back.

### Scanner B swap: DONE

- `agents/examiner2_scanner_b.py` now loads `umm-maybe/AI-image-detector`
  from the pinned local dir `models/umm` (license CC BY 4.0, attribution
  in the file header and in the repo README's Credits and Licenses
  section). The swap changes only the model: same Swin family, same
  label names (artificial, human), same verification rules and
  thresholds as the hung version. Header records the calibration note
  (0.75 alone, zero false positives on human works, ensemble
  {yaya, umm, king} 0.85).
- `agents/README.md` updated with the new panel composition and the
  candidate test summary.
- Smoke test: `examiner2_scanner_b.py --case fixture --bundle fixtures
  --dry-run` ran clean and wrote `agents/reports/fixture-scanner_b.json`
  with tool `umm-maybe/AI-image-detector (local pinned model at
  /home/hatch/workspace/human-cert/models/umm, ...)`, P(AI) 0.0505 on the
  poster fixture, and verified items layered_source_file, live_redraw,
  progress_sketches, the same items the previous Scanner B verified on
  that fixture.

### Demo rerun with the clean panel: DONE, both directions

Same bundles as case-0 and case-1 (identical image and bundle hashes),
submitted fresh so the old cases stay untouched. Both read back from
chain after finalize.

- case-2: PASS. Submit tx `3EAiSPEJ8LEhMEU173EAfredi41pcoC1BC2Kj5fND55E`,
  finalize tx `5fuCn6hvuznxyzxL5abTVEEL5BwMdvmpogm6Um7r24y2`. Votes
  (commit / reveal): exam1 `HDrV61zJqjJy7Snkdtbp7mGWHD29wM5fijP73RdStNHB`
  / `5grrDviq5aMDCYjjrFwSgnJQ2ddYHmv44FZKAzTH6e9v`; exam2
  `CF5xLvDuuqgng5mXW3HVwqRikTa3fHwJfPGZMLGWrt35` /
  `EYyddyLfRQKCG5781b7iAoLNmdpMrw6VWMbwdvvYqub9`; exam3
  `CjHaTptCXUK95GKEykQndAsvsuvC7fwGCi5bQ2hNayfC` /
  `HwoAeQEC15Cm7wRuhwMpVsFd69RFzqh3pxg2oxP5BQW`; exam4
  `AwhmuEyYJLBzwKBSPVKyT9oJAgRDHRUTAW2kiNDaAg36` /
  `9QqzLCZxFEW7Fzzz353dsUhwaUhpgGZ1iyQBSEHmEbRG`; exam5
  `8mHMg5Zj4eNxE3Mfa5U2nwavECj9osz4JbEkVPfECSKx` /
  `FJ6vJAWYM3V3M1NGrwSgT7XkVJkNkCtThik4sJjfb1Cy`. Read-back verdict:
  status passed, Human 5, Process 5, level 5, cert_token_id cert-2,
  fee_settled true, 5 commits, 5 reveals. `nft_token(cert-2)` is owned
  by `bindingvow1106.testnet`; total supply 2. Scanner pixel scores:
  A 0.7617 AI, B (umm) 0.0505 AI, C 0.9435 AI. The Process auditor
  again verified nothing, for the same published reasons as case-0.
- case-3: FAIL. Submit tx `7gcKinuqgUwfhkbjigQk9xYYnUN2RisVNEp4cTh8y9D`,
  finalize tx `4GCm3RrSXtemxM4p17xj4pABhbZahC4PMsxVsA8Eg9rR`. Votes
  (commit / reveal): exam1 `8h3Wzebf63p19PVeUGyHGL1xfD2DyhbkvQQ9unPjTLqg` /
  `CZD21rZWbGCCCZeYgdj3gWEAFfvoLLWhjcUS4Jbh6QQE`; exam2
  `EUSnf8xnH7Y14fRtxfPkq3iV9CFuzyquwNmujr52198m` /
  `9PkqHRp3Z5exeRH4y7d8j9G3FQtKwk3s4WMCxZAb3M5q`; exam3
  `vTRVgJVkyJcmW9An5x5PFK8DvdvkroA3CzJRB5wqPQV` /
  `wzRWwXegt8R3EdAsenBQrCf4uPwySRS2Hc4Q9znd2nr`; exam4
  `FKukhZHbyxxkydd8RE2eP8yaqZnpej75JswpTRD9qt7G` /
  `HzwYpt29MnYoPPSyE1zLcgMgu8vHH4hxb8G1puiT4s5S`; exam5
  `FbwcwbnKpCPNJEviAmEH3bPhx8TyuseLPaN99tx2BQFy` /
  `8RKNnxaDFfaEPpPB1GTu3kkehqdUZawsZWJXSjM5MiXL`. Read-back verdict:
  status failed, Human 0, Process 0, level null, cert_token_id null,
  fee_settled true, all 5 reveals with empty verified lists.
  `nft_token(cert-3)` is null and total supply stayed 2. Fee split
  proven by balances read before and after the case: each examiner
  rose by about 0.0095 NEAR (exam1 +0.009549, exam2 +0.009543,
  exam3 +0.009538, exam4 +0.009532, exam5 +0.009526). Scanner pixel
  scores on the AI image: A 0.9272, B (umm) 0.4007, C 0.9902; umm's
  miss matches its calibration behavior on this image (0.40) and is
  recorded in the failure catalog. Pixels did not decide the case:
  the bundle contained no evidence, so nothing could be verified.

### Failure catalog: DONE

`calibration/results/FAILURE-CATALOG.md` catalogues every measured
error from both studies: per-model verdicts for all 20 images and all
six models tested, every wrong image named per model, panels old and
new, failure patterns grouped (code-drawn work defeats pixel panels,
an accuses-everything scanner, expressive classics flagged, AI food
and vaporwave passing as human, accusing candidates flagging the
artist's own files), error direction per model, and the honest
summary lines (no license-clean panel beats 0.85 on n=20; every panel
above 0.85 includes the NC model; pixel-only judgment is structurally
blind to process). The new demo reports are in `agents/reports/` and
copied to `frontend/reports/` (20 report files there now).

## Addendum 2026-11-07 12:16 WIB: frontend deployed and click-verified

The Vercel blocker is resolved. Kokoron reconnected the Vercel connector; creating the project WITHOUT an explicit teamId then succeeded where the explicit-team call had returned 403 (the default scope carries the access). Project humanmark (prj_UyJ5NQloaqvufvsYKWjxrWYNx0UL), deployment dpl_94WXY4jnZYZNcCvMEchvhNMGbskU READY, SSO protection disabled, live at https://humanmark-ilkokorons-projects.vercel.app (HTTP 200). The deployed app.js is byte-identical to the local frontend source (md5 ceb944442ea266f1aab708e50f642940).

Click verification, second pass with exact quotes (the first browser report contained invented details, examiner names alfa/beta.testnet and case list points that exist nowhere in the code or chain, and was discarded): case-0 detail shows PASSED, Human "5 points, 5 needed", Process "5 points, 5 needed", level 5, cert-0, examiners exam1 to exam5.bindingvow1106.testnet. Case-3 detail shows FAILED, 0 and 0 points, no certificate. Both match direct RPC read-backs of get_case. The wallet-signed write path remains unverified (needs a human wallet login), as with Binding Vow.
