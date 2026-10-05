# Launch-film provenance and review

These are actual rendered local deliverables, produced on 2026-10-05. The source/evidence capture is pinned to `a3d3c491cc9f5b236e2eb38126cdb56e5fa3b82c`; later Docker-only commits do not relabel that footage. The coordinator verified [CI run 37386118051](https://github.com/kapasainitishreddy/Gradientmine/actions/runs/37386118051) succeeded for that exact source via GitHub API. The film itself makes no CI claim.

## Actual experiment

- Job: `d348dcd2-90f3-49a0-949d-4c7801699346`, recorded local, EVALUATED, no chain funding/registration/settlement signatures.
- Strict `scripts.public_evidence.checked_artifacts` loaded **14 actual public JSON blobs** and passed exact content hashes, worker/validator signatures, cross-artifact provenance, numerical model merge and deterministic eligible-winner verification before capture and again after final renders.
- Baseline `0.8472222222222222`, winner `0.9527777777777777`, delta `0.10555555555555556` on 360 held-out examples. The film rounds to 84.72%, 95.28%, +10.56 percentage points.
- Actual winning-worker 60-epoch losses and public log were captured from `.local/final-verification/worker-1`, matched to the winning adapter manifest and first/last metrics. They are preserved as small public evidence with their loss-file hash in evidence-manifest.json. Three independent processes ran on one CPU host; the third is a disclosed shuffled-label negative control.
- Actual UI policy, submission table, score panel, receipt inspector and lineage were captured with Playwright against the existing vanilla-JS app. The winning receipt displayed the successful SHA-256 and **expected-validator** Ed25519 check. No wallet session/private identity was opened.
- The earlier export's exact merged-model bytes did not reproduce under the upgraded PyTorch numerical runtime; it was rejected for this film. A fresh run supplied the current export. Prior history was preserved, not quietly relabeled.

## Final outputs

| Film | Actual format | Duration / frames | SHA-256 |
|---|---|---|---|
| `.local/tour/landscape/brag.mp4` | H.264, 1920×1080, 30fps, AAC | 22.000000s / 660 | `a25bd417cef28c125f773d86ea59e49c07507656305edc3e043c92f5d7b655a0` |
| `.local/tour/vertical/brag.mp4` | H.264, 1080×1920, 30fps, AAC | 20.000000s / 600 | `feb47886a953f1441dfdceeb20f04483775b42a5f7bba1ee5b0b5b5337a88917` |

The full-resolution landscape poster is a settled evidence scene at **11.8s**, not an intro fade. `poster.jpg` is 117,172 bytes. The vertical poster is its deliberate portrait score scene at 11.4s. Delivery baked the matching image only into frame zero using the official FFmpeg overlay approach. Both films retain exact duration and frame count; raw AAC packet SHA-256 is unchanged. Frame-zero/poster SSIM is 0.997767 landscape and 0.997725 vertical after H.264 encoding. Full FFmpeg video/audio decode completed with zero reported errors. Machine-readable ffprobe, hashes and checks are in render-manifest.json and ignored `.local/tour/delivery.json`.

## Validation and end-to-end review

Hyperframes **0.8.134**, high-quality, 30fps, strict render, workers=2. Landscape rendered in 51.9 seconds; vertical in 38.9 seconds. Tool doctor passed required Node/FFmpeg/browser capabilities; optional voice is unused. The local usage command returned unknown/no subscription login, so no free-tier usage balance is claimed. No remote publishing occurred.

Both `hyperframes check --json` reports have zero lint/runtime/layout/contrast errors, with **40/40 text contrast checks passing**. Each has eight nonblocking structural advisories: seven suggestions to split timeline sections into subcompositions and one discovery warning for the persistent/final logo's shared image. This original single-timeline composition rendered both logo uses correctly. The separate motion check was disabled; it is not reported as passed.

Push-transition canvas wrappers intentionally allow overflow while traveling beyond the frame; that means the automated layout pass alone is insufficient. Manual review covered all seven settled beats and actual rendered one-second sequences end-to-end, plus receipt/score/poster frames at full resolution. It caught a portrait hook overflow and evidence-thread intersections with training/score text; those were corrected before the final portrait check/render. The final headline, actual loss curve, score panel, verified receipt/lineage and closing disclosure fit and remain legible. Supplemental screenshot microtext is supporting evidence; the main claims remain large on both canvases.

Sound is original deterministic synthesis, not bundled music or generated speech. The 22s source peaks at −21.8dBFS (mean −33.5dBFS) before the composition's 0.6 gain. It has controlled onset/end envelopes; the portrait cue is trimmed to 20s with a final 0.9s fade, and its own 600-frame audio analysis drives only restrained line opacity. No payment sound or fake transaction signal is used. No licensed-library track with uncertain terms is redistributed.

Closing text remains **“Devnet settlement path implemented / Live payout evidence pending.”** Neither film shows a fabricated program ID, Explorer page, airdrop, escrow balance, validator independence, payment, or real Phantom-extension success. Live Devnet settlement evidence and actual Phantom user testing remain separate product limitations.

## Command/output evidence

Exact reproducible commands are in README.md. Original scripts are capture.py, sound.py, build.py and deliver.py. Outputs of the executed tool calls are preserved locally:

- `.local/tour/check-landscape.json`, `.local/tour/check-vertical.json`: zero-error reports including contrast counts.
- `.local/tour/keyframes-landscape.json`: seekable keyframe inspection output.
- `.local/tour/landscape/render.log`, `.local/tour/vertical/render.log`: final successful high-quality render traces.
- `.local/tour/deliver.log`, `.local/tour/delivery.json`: poster bake, dimensions, exact duration/frame count, unchanged AAC packets, SSIM and full-decode verification.
- `.local/tour/{landscape,vertical}/snapshots/`: deliberate settled-frame screenshots.
- `.local/tour/{landscape,vertical}/review.jpg`: actual final-video frame sequences; `frame-zero.jpg` independently decodes the baked thumbnail.

Initial sandbox-path failures caused by the CLI's default home cache/state were corrected using documented browser/cache/state environment overrides. Local final commands completed successfully. Generated AGENTS/CLAUDE, downloaded dependency code, skill/cache directories, audio and large renders are excluded from Git; only original source, plans/provenance, small public epoch evidence and a lightweight poster are intended for commit.
