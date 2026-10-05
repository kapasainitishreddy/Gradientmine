# Product demo: at most 3 minutes

For the short launch film and continuous visual product-tour grammar, also read [PRODUCT_TOUR.md](PRODUCT_TOUR.md). The prepared submission demo is an evidence-first walkthrough; a stylized launch clip does not replace the required product demo.

Target 2:45 under the prior reported ≤3-minute limit; verify current rules as described in SUBMIT.md. The exact narration, screen actions, time-cut captions and export checks are in [RECORDING.md](RECORDING.md). **Script and recording instructions, not a recorded or uploaded video.** Use only the mode that is actually running. Do not splice simulated transactions into a Devnet claim.

## 0:00–0:15 | Establish what is real

Show the app's mode banner. Say: “GradientMine turns a measurable model improvement into a bounty with explicit evaluation evidence.” State whether the session is a live Devnet run, live local run or a recorded local result. Keep the banner visible.

## 0:15–0:45 | Terms and wallet

On a live server, connect your actual Wallet Standard wallet, create a bounty and inspect the fixed parent, improvement threshold and deadline. For a verified Devnet deployment, show the full program ID, reward, rent and fee in the review dialog, approve in your wallet and open the **actual finalized funding transaction**. Connecting or creating a draft alone is not escrow.

For a local-only recording, explicitly say “No funds move in this local demonstration” and show the immutable policy instead. Do not enter a fake transaction signature.

## 0:45–1:20 | Actual experiments

Show the real worker commands and their logs. Three processes can run on one host; say so. They train numeric low-rank adapters. Identify the shuffled-label worker as a disclosed negative control, not a caught cheater. It is acceptable to cut a waiting period, but label the cut “After training and submission cutoff”; never show a fabricated live training speed.

## 1:20–1:55 | Evidence before a reward

Return to the actual results table. Read the measured baseline, eligible candidate and improvement in **percentage points** from that run, not an invented example. Open one winning receipt. Show the browser's SHA-256 check and expected-signer Ed25519 verification. Explain that the evaluator remains trusted and the statistical comparison has limitations.

## 1:55–2:25 | Settlement or honest local boundary

On Devnet, show the finalized payout link, recipient and reward, then compare the app's state with Explorer. Include only signatures present in the evidence bundle. If the transaction is pending or failed, show that rather than claiming success.

For a local-only recording, say “This run verifies training and evaluation, not an on-chain payout.” Show the native program's SBF test evidence, labelled local VM testing, and mark deployment/payment unfinished.

## 2:25–2:45 | Lineage and failure handling

Show the parent-to-winner model relationship and downloadable artifacts. Point out the timeout refund and explicit validator trust. End: “Compute is not the outcome. An inspectable improvement is.”

## Exact recording procedure

Use OBS, a browser recording tool or your operating system's screen recorder. Capture 1920x1080 at 30fps, crop to the app and terminal and hide notifications, private identity files, bearer tokens and wallet recovery phrases. Record the session with a dedicated test wallet only. Keep transaction approval visible without exposing secrets. Add captions for any time cuts. Export H.264 MP4 and verify duration with `ffprobe -v error -show_entries format=duration -of default=nw=1 demo.mp4`. It must not exceed 180 seconds. Upload it and test the resulting URL without your login.

A developer browser harness is useful QA, but is not a substitute for recording an actual Phantom interaction. No final demo URL is asserted in this file.
