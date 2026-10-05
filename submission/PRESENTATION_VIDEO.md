# Captioned presentation candidate

A genuine **2:30 captioned presentation** has been recorded from the actual read-only local evidence viewer and repository document excerpts. It is a silent English-captioned candidate: **no narrator, generated voice, owner identity, wallet approval, public upload or portal submission is claimed**. Owner review and upload remain pending.

The presentation follows the five fixed sections of [PITCH.md](PITCH.md) and the 150-second presentation plan in [RECORDING.md](RECORDING.md). [presentation-captions.srt](presentation-captions.srt) contains the complete pitch text, with readable one- or two-line cues; subtitles are also burned into the exported MP4. The official public FAQ verified on October 5, 2026 requires a two-to-three-minute presentation. Duration alone does not establish organizer acceptance of this silent candidate; the owner should review the current portal and may replace silence with natural narration.

## Actual footage and evidence

Footage was captured continuously in a clean Playwright Chromium browser, with the actual static viewer served on an ephemeral loopback port. Browser chrome, developer tools, identities, environment values and session storage were never opened. The local server served a public web snapshot and selected repository excerpts, rather than the live API or its data volume.

The source application snapshot is `a3d3c491cc9f5b236e2eb38126cdb56e5fa3b82c` ([successful verification run](https://github.com/kapasainitishreddy/Gradientmine/actions/runs/37386118051)). The recording also retains source-file hashes, actual capture times, the raw browser video, delivered-video hash and exact public evidence manifest outside Git.

The visible recorded job is `d348dcd2-90f3-49a0-949d-4c7801699346`. Its 14 referenced public artifacts passed strict hash, worker-signature, expected-evaluator-signature, parent/adapter/result-model and deterministic-winner checks before capture. The browser separately displayed successful policy-byte and winning-receipt verification.

The actual local run shows **84.72% → 95.28%, +10.56 percentage points, 360 held-out examples**. These are that recorded run's measurements, not general benchmarks. Three worker processes ran on one host using real CPU training; the parent was deliberately budget-limited, and one worker was a disclosed shuffled-label negative control. The evaluator is explicitly trusted and the public digits benchmark is reconstructible.

Persistent burned labels identify **recorded local experiment, read-only evidence, no funds moved** and **captioned presentation, no narrator, owner review and upload pending**. The visible winner is eligible and **not paid**. Native escrow/refund source is shown as implementation evidence. No Devnet deployment or payout, public marketplace, customer traction, pricing validation or independently owned GPU fleet is implied. Customer, distribution and fee discussions are the existing document's hypotheses.

| Fixed pitch section | Actual browser footage |
|---|---|
| 0:00–0:25 — problem and proposition | Original logo, then the actual product overview and recorded-mode banner |
| 0:25–0:55 — product | Actual policy inspector with SHA-256 verification, then exact blockchain rationale/native Rust source excerpts |
| 0:55–1:25 — evidence | Recorded candidate results, followed by the actual winning receipt inspector and expected-signer verification |
| 1:25–1:55 — trust and differentiation | Actual UI trust section and exact threat-model excerpts |
| 1:55–2:30 — market and next test | Exact customer/business/traction hypothesis excerpts, actual UI return, original logo hold |

## Export and review

Machine-local output: `.local/submission-videos/presentation/final/presentation.mp4`. It is an actual rendered MP4, not a script or placeholder. Large footage stays ignored and is not committed. Its companion `provenance.json`, raw Chromium recording, source-view screenshots and final-video review images remain in the same ignored directory.

The verified export is **150.000 seconds, 4,500 video frames and 6,021,820 bytes**, using 1920×1080 H.264, 30 fps, yuv420p, fast-start MP4 and a silent 48 kHz stereo AAC track. Its SHA-256 is `032adad9556714fa45cb57f3126b5b46c0cf63783c4266b02f1d8d23ee913cb9`. Captions occupy a reserved 180-pixel band below the real 1920×900 browser viewport, so they do not cover the app's evidence.

Duration, SHA-256 and final frame-review results are recorded in the provenance file. The entire delivered MP4 decoded without video or audio errors, and a volume check confirmed a silent track. Visual review inspected 150 ordered frames across the complete timeline in `review/timeline-01.png` through `review/timeline-05.png`, with 11 full-resolution scene keyframes including `review/keyframe-058.png` (results), `review/keyframe-075.png` (verified receipt), `review/keyframe-120.png` (hypotheses) and `review/keyframe-149.png` (ending). A short final-caption flash was corrected using the same raw browser take; all pitch words remain unchanged. This review is not a substitute for the owner's final watch-through on the target upload host.

To reproduce on an environment with Chromium, Playwright's FFmpeg helper and system FFmpeg installed:

```sh
python -m scripts.record_presentation --write-captions
python -m scripts.record_presentation --out .local/submission-videos/presentation/new-take
```

The recorder refuses a nonempty destination, refuses captions that differ from the current pitch, strictly validates the public recorded evidence, and aborts on browser exceptions. This cloud capture used the installed system Chromium and system FFmpeg helper through `PLAYWRIGHT_BROWSERS_PATH=/workspace/.cache/ms-playwright`; that machine-specific cache path is not a public deployment.

## Owner handoff

Watch the delivered 2:30 file in full, review the silent-caption format and every visible claim, and optionally record natural narration using the exact captions. Upload the final presentation to a permitted judge-accessible host, confirm playback signed out, and enter the real playback URL in the official portal. Retain the delivered file's hash, duration and upload confirmation. No presentation URL or portal confirmation exists yet.
