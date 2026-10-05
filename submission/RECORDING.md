# Recording sheet: presentation and product demo

**Recording instructions for the official presentation and demo.** [SUBMIT.md](SUBMIT.md) records freshly verified official rules: presentation 2–3 minutes; product demo ≤3 minutes. Captioned capture candidates, when produced, have their own provenance sheets; no upload or portal confirmation follows from a local MP4. Check for later rule changes before upload.

## Capture preparation

1. Read [BUILD_LEDGER.md](../docs/BUILD_LEDGER.md), [PITCH.md](PITCH.md), [DEMO.md](DEMO.md), and the current public evidence. Choose a single demonstration mode: live local, recorded local, or an actually verified integrated Devnet run. Never use chain-only smoke evidence as the payout for an unrelated trained artifact.
2. Use a clean browser profile and 1920×1080 capture canvas at 30 fps. Increase the browser zoom until policy, results and receipt text are readable at 1080p. Pre-open only the app, the public repo, public verification output, and Explorer if real finalized signatures exist. Disable notifications. Do not capture private JSON identities, recovery phrases, browser storage, Authorization headers or CI secret panels.
3. Record a 10-second microphone/cursor test. Use natural owner narration, with no music needed. Use licensed music only if rights have been confirmed. A face camera is optional; no founder photo is needed. Record the whole UI take and keep the original privately so cuts can be checked against it.
4. Prefer the existing original [logo.svg](logo.svg). If the portal needs PNG, export that SVG at 1024×1024 in a vector editor; preserve its square proportions and verify the resulting image. The logo is an original geometric mark, not a Colosseum, Solana or wallet endorsement.
5. For a new local capture on an installed checkout, run the following **before capture**, with shell pipe failure enabled. These generate real training evidence; they do not make a video or a public deployment. Do not record the private output directory listing.

```sh
set -o pipefail
python -m gradientmine.cli demo --out .local/recording-run 2>&1 | tee .local/recording-training.log
python -m scripts.publish_demo --run .local/recording-run/run.json
```

The local demo creates separate worker processes and public results alongside private identities; only publish through the repository's artifact allowlist. Serve the prepared recorded viewer separately from a live API, following the current runbook. Verify the visible mode rather than assuming that an empty live server is the recorded result. If using the checked-in snapshot, identify it as recorded and do not fabricate contemporaneous logs.

## Presentation: exact 2:30 shot plan

Read the exact spoken paragraphs in [PITCH.md](PITCH.md) at a relaxed pace. Each row is a fixed edit boundary, leaving short click/pause space. Rehearse and trim pauses to 150 seconds; never speed the voice to hide missing content.

| Time | Screen action | On-screen caption |
|---|---|---|
| 0:00–0:25 | Start with original logo for 2 seconds, then actual app overview and mode badge. Deliver “Problem and proposition.” | “Pay for measurable model improvement” + persistent actual mode label |
| 0:25–0:55 | Open the policy; point at parent commitment, minimum improvement, cutoff, evaluator. Show native-program source or actual evidence when discussing escrow; do not imply a deployment from source. Deliver “Product.” | “Committed terms → independent candidates → named evaluator” |
| 0:55–1:25 | Show the actual experiment results and winning receipt; keep hash/signer verification legible. Deliver “Evidence.” | “Real CPU training · numeric adapters · inspectable receipts” |
| 1:25–1:55 | Show the trust/benchmark warning and briefly the threat-model table. Deliver “Trust and differentiation.” | “Trusted evaluator · public reconstructible benchmark” |
| 1:55–2:30 | Show the proposed customer/validation paragraph, then return to actual UI and logo. Deliver “Market and next test.” Finish at 2:30, including the final hold. | “Customer and pricing hypotheses · no validated traction” then “GradientMine — reward the improvement” |

Use truthful state labels alongside the footage: “Recorded local experiment — no funds moved,” “Live local — no funds move,” or “Live Solana Devnet — test funds only,” as applicable. Presentation narration about implemented escrow rules does not imply a completed payment.

## Product demo: exact 2:45 local narration and actions

This is the ready-to-record local version. Read the quoted narration verbatim, except replace measured values if recording a different run. Leave enough pause for every click. The checked-in example inspected during this pass is job `d348dcd2-90f3-49a0-949d-4c7801699346` in `web/assets/recorded-run.json`: 84.72% baseline, 95.28% winner, +10.56 **percentage points**, 360 evaluation examples, `EVALUATED`, no funding or settlement signature. These are that snapshot's measurements only.

| Time | Screen action and exact narration | Caption |
|---|---|---|
| 0:00–0:15 | Show mode badge and actual bounty. “GradientMine pays for measurable model improvement. This is a recorded local CPU experiment. No funds moved, and this page is read-only evidence.” If recording live local, replace “recorded”/“read-only” with the actual state. | “Recorded local experiment · read-only · no funds moved” |
| 0:15–0:45 | Open policy, copy the full policy hash, point at parent, cutoff and threshold. “The owner commits a frozen parent, evaluation rules and deadline before workers enter. The hash binds these terms. This classifier's parent is deliberately budget-limited. The evaluator is named, and the public digits benchmark can be reconstructed.” | “Immutable policy · trusted evaluator · public benchmark” |
| 0:45–1:20 | Show public real worker output from the captured run, then candidate table. For the checked-in snapshot without corresponding logs, show its recorded process disclosure and artifacts instead. “Three independent worker processes on one host trained numeric low-rank updates using PyTorch. This is real CPU optimization, not an LLM or three independently owned GPUs. One worker shuffled labels as a disclosed negative control. The evaluator waits until cutoff. Any waiting time omitted from this recording is labelled.” Show only an actual labelled cut. | “Three processes · one host · disclosed negative control”; at a real cut: “After training and submission cutoff — elapsed time omitted” |
| 1:20–1:55 | Open winner and receipt, open the browser receipt inspector and show its automatic hash/signature verification result. “In this recorded run, accuracy rose from 84.72 to 95.28 percent on 360 held-out examples: 10.56 percentage points. The browser checks the receipt hash and the expected evaluator's signature. Eligibility uses a declared approximate paired-bootstrap comparison. A valid signature authenticates the report; it does not prove training or remove evaluator trust.” | “This run: 84.72% → 95.28% · +10.56 pp · n=360”; then “Hash + expected-signer verification” |
| 1:55–2:25 | Show `EVALUATED`, absence of payout, and public compiled-SBF test evidence only if passed for the cited build. “An eligible winner is not a paid worker. This local run has no on-chain payout. The native Rust program's local VM tests exercise escrow, registration, payout and refund rules. A local VM is not Devnet. A real payment claim needs the exact trained artifact, registered worker, signed receipt and finalized payout evidence together.” | “Eligible ≠ paid · local VM ≠ Devnet”; include test commit/build identifier from current evidence |
| 2:25–2:45 | Show parent/winner relationship, download an artifact, point to refund/trust explanation and hold on app. “The evidence links parent, adapter, evaluator receipt and resulting model. Devnet escrow has a creator timeout refund; this local job has no escrow. Next comes private-task customer validation. Compute is not the outcome. An inspectable improvement is.” | “Downloadable evidence · explicit trust · customer hypothesis” |

The first-round snapshot has no earlier-round ancestors (`lineage: []`). Show its parent/winner model relationship; do not invent a multi-round graph. Use subsequent-round lineage only if that round actually exists.

## Devnet substitutions: only after the integrated proof exists

Keep the same 165-second timeline. Replace the opening sentence with “This is a verified Solana Devnet run using test SOL.” During 0:15–0:45 show the dedicated real wallet's authentication, transaction review and actual finalized funding link, saying: “This review names the exact program, reward, rent and fee. The owner's wallet signs; finalized evidence confirms escrow.” Label any time cut to a completed approval/confirmation.

During 0:45–1:20 show the actual trained adapter and matching on-chain registration, saying: “This worker's artifact commitment was registered before cutoff.” During 1:55–2:25 replace the local-boundary paragraph with: “The registered worker selected by this receipt received the committed Devnet reward. Here are the finalized payout, recipient and chain state. The winning artifact and receipt hashes match the public evidence bundle. This is test SOL, not revenue.” Open the real Explorer link and compare recipient/reward with the UI and bundle. If any match is missing, pending or failed, retain the local version or describe that exact failure; no success sentence may be used.

Wallet footage must be the actual extension interaction. A Playwright test wallet can be labelled a harness in engineering evidence; it cannot stand in for Phantom. Do not expose the extension's recovery settings.

## Captions, edit and export

Add complete spoken-word captions from the final narration, with manually corrected terms: “GradientMine,” “Solana Devnet,” “PyTorch,” “low-rank,” “Ed25519,” and “percentage points.” Break captions into one or two readable lines, usually 32–42 characters per line, time them to the real speech, and avoid covering the mode badge or verification result. Use the table's captions as separate evidence labels, not a substitute for accessible speech captions. Keep every claim visible long enough to inspect. Cut only waits/navigation, label elapsed time, and never reorder footage to imply an unperformed approval or payment.

Export separate `presentation.mp4` (target 150 s) and `demo.mp4` (target 165 s): 1920×1080, 30 fps, H.264, yuv420p, AAC 48 kHz stereo, approximately 8–12 Mbps video, 160–192 kbps audio, fast-start enabled. Export both a corrected `.srt` file and burned-in captions if supported. For an already recorded and edited master, this optional command transcodes the real footage; it does not generate footage:

```sh
ffmpeg -i edited-master.mov -vf 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,fps=30' -c:v libx264 -pix_fmt yuv420p -b:v 10M -c:a aac -b:a 192k -ar 48000 -movflags +faststart presentation.mp4
ffprobe -v error -show_entries format=duration -show_entries stream=codec_name,width,height,r_frame_rate -of json presentation.mp4
ffprobe -v error -show_entries format=duration -show_entries stream=codec_name,width,height,r_frame_rate -of json demo.mp4
```

Check the entire exported file, including black frames and end card: presentation 120–180 seconds under verified official guidance; demo ≤180 seconds, preferably 165. These are instructions, not commands claimed executed in this environment. Watch both exports with sound and captions. Confirm that addresses/hashes remain legible and no secret appears in a frame.

## Upload and portal handoff

Owner chooses a permitted judge-accessible host, uploads both distinct videos, adds corrected captions, and tests each URL signed out on desktop and phone. Avoid a login gate, expired link, private cloud folder or processing-in-progress page. Retain filename, exact duration, upload date, playback URL and visibility setting privately until ready to enter the portal. Enter the two URLs in the actual dashboard and save final portal confirmation. Do not substitute a script, launch clip, repository link or localhost address for a video URL.
