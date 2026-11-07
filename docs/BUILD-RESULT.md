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
