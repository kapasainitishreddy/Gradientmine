# Recorded product-demo video

A genuine caption-led product demo was recorded on October 5, 2026. It is a continuous Chromium capture of the actual read-only recorded viewer, with real policy/manifest/receipt inspections and an actual winning-adapter download. It is not a live training session, wallet-extension demonstration or Devnet payment.

The local export is `.local/submission-videos/product-demo/demo.mp4`: **165.000 seconds, 1920×1080, 30 fps, H.264, yuv420p, fast-start**. Complete English captions are burned in; [demo-captions.srt](demo-captions.srt) provides the separate accessible caption file. There is **no audio track, synthesized narrator, music or sound effect**. This caption-led demo and the separate [150-second captioned presentation](PRESENTATION_VIDEO.md) exist. Owner review and judge-accessible delivery remain pending; silent captions do not by themselves establish organizer acceptance.

File size: **32,265,686 bytes**. MP4 SHA-256: `905c042931c648a1ae6ff241761d1ac1ef5f8e3270dfa6f79bee2244e2a709c8`.

## Evidence and provenance

- App/run source: `a3d3c491cc9f5b236e2eb38126cdb56e5fa3b82c`.
- Recorded local job: `d348dcd2-90f3-49a0-949d-4c7801699346`.
- Actual measured result: **84.72% → 95.28%, +10.56 percentage points, 360 held-out examples**.
- Three real worker processes on one host; the shuffled-label worker is an explicitly disclosed negative control.
- All **14** referenced public artifacts passed SHA-256, expected-signer signature and cross-artifact provenance checks through `scripts.public_evidence.checked_artifacts` before capture.
- The browser checked the actual winning receipt's SHA-256 and expected-validator Ed25519 signature; the recorder checked the copied full policy hash and downloaded adapter bytes independently.
- Browser JavaScript errors: **zero**. Non-GET requests during recording: **zero**. No wallet harness, API mocks, private identities or sessions were used.
- Local compiled-SBF VM testing cited in captions: **31 local tests** during this engineering pass, with baseline source `19578cf7d01009ed8c427dafba6a3824799307d8`. This is local program testing, not Devnet.
- Source CI: [successful run 37386118051](https://github.com/kapasainitishreddy/Gradientmine/actions/runs/37386118051) at `a3d3c49`; the 31-test count above comes from local execution, not downloaded CI logs.

The original WebM, exact MP4 hash, caption hash, verified artifact list, browser actions, tool versions and export probe are retained in the ignored `.local/submission-videos/product-demo/provenance.json` and `original/` directory. The large rendered video is intentionally outside Git; it has no public playback URL yet.

Export QA decoded the complete 165 seconds successfully. Every second was visually reviewed across six contact sheets, and policy, results, receipt verification, trust, lineage and final-hold frames were inspected at full resolution. Captions remain clear of the receipt verification status. The last contact sheet has unused black grid cells after the final sampled frame; these are contact-sheet padding, not black frames in the MP4. The capture contains public app evidence only.

## Reproduce the actual capture

Install the repository's documented Python dependencies and Playwright. Chromium and FFmpeg with libass must be available. The recorder serves only `web/` over a temporary loopback static HTTP server, validates the public artifact allowlist, records the real viewer for 166 seconds, then exports the 165-second portion after initial navigation. It does not start a marketplace API or replay training as contemporaneous footage.

```bash
python -m playwright install ffmpeg
python -m scripts.record_demo --out .local/submission-videos/new-product-demo
```

In this cloud environment the Playwright encoder CDN returned 403. The already-installed system FFmpeg was used through an explicit workspace-only executable link; no downloaded encoder artifact or checksum verification was bypassed:

```bash
mkdir -p /workspace/.cache/ms-playwright/ffmpeg-1011
ln -s /usr/bin/ffmpeg /workspace/.cache/ms-playwright/ffmpeg-1011/ffmpeg-linux
PLAYWRIGHT_BROWSERS_PATH=/workspace/.cache/ms-playwright \
  python -m scripts.record_demo --out .local/submission-videos/new-product-demo
```

The `ffmpeg-1011` path matches the pinned Playwright release used for this capture. Keep the original and provenance when re-recording. Human narration can be recorded separately and deliberately synchronized; no human voice is claimed here. Before submission, the owner must upload the actual file to an authorized judge-accessible host, test signed-out playback, and enter the final URL in the portal. This product demo does not replace the separate presentation video.
