# GradientMine short films

Original `/brag --tone polished --format landscape --duration 22 --title "GradientMine"` production using the official MIT brag skill and Hyperframes. The companion is a deliberate 20-second vertical reframe. No voice, account signup, remote publishing, paid dependency or synthetic network is used.

Final local outputs are `.local/tour/landscape/brag.mp4` and `.local/tour/vertical/brag.mp4`, with adjacent `brag.jpg` posters. The tracked `poster.jpg` is the landscape evidence scene at 11.8 seconds. It is baked into frame zero of the corresponding film; all timing and audio remain unchanged. Plans, original source, small public epoch-loss/log evidence and provenance are versioned; runtime assets and video/audio remain ignored.

The film source is job `d348dcd2-90f3-49a0-949d-4c7801699346` from source `a3d3c491cc9f5b236e2eb38126cdb56e5fa3b82c`. It shows the actual local 84.72%→95.28% held-out result. Fourteen public artifacts passed strict hash/signature/provenance/model-merge checks before capture. It never claims a blockchain payment. `evidence-manifest.json` pins the complete source; `PROVENANCE.md` records verification and render results.

## Reproduce locally

Use the repository Python environment (including Playwright), Node 22+, FFmpeg and Chromium. Run commands from the repository root. Runtime/cache paths below are appropriate for this managed workspace; use your own writable paths elsewhere. Hyperframes `doctor` passed required tools; optional voice is unnecessary.

```bash
source /workspace/.gradientmine-setup/activate.sh
export HYPERFRAMES_BROWSER_PATH=/usr/bin/chromium
export XDG_CACHE_HOME=/workspace/.gradientmine-tools/cache
export XDG_STATE_HOME=/workspace/.gradientmine-tools/state
export NPM_CONFIG_CACHE=/workspace/.gradientmine-tools/npm
npm ci --ignore-scripts --prefix submission/tour/composition
python -m submission.tour.capture
python -m submission.tour.sound
```

Capture strictly checks the current public export before touching screenshots. It loads only public logs/losses from a matching local verification run, or the preserved matching public evidence in this directory. If the job changes, fresh matching real worker evidence is required. Recapture updates the source SHA and resets current CI to pending; check CI for that new source before making a new success claim. Do not relabel the existing captured film as evidence from a later source.

Read the original audio helper from the official Hyperframes repository at commit `f835f8316402dc75c51d4d4c355047457ca930b1`. In this workspace it is available at the following path:

```bash
python /workspace/.gradientmine-tools/hyperframes-source/skills/hyperframes-creative/scripts/extract-audio-data.py .local/tour/evidence-bed.wav --fps 30 --bands 16 -o .local/tour/audio-data.json
ffmpeg -y -v error -i .local/tour/evidence-bed.wav -t 20 -af afade=t=out:st=19.1:d=0.9 .local/tour/evidence-bed-vertical.wav
python /workspace/.gradientmine-tools/hyperframes-source/skills/hyperframes-creative/scripts/extract-audio-data.py .local/tour/evidence-bed-vertical.wav --fps 30 --bands 16 -o .local/tour/audio-data-vertical.json
python -m submission.tour.build
python -m submission.tour.build --vertical
npx --yes hyperframes@0.8.134 check submission/tour/composition --json
npx --yes hyperframes@0.8.134 check .local/tour/vertical/composition --json
npx --yes hyperframes@0.8.134 render submission/tour/composition --output .local/tour/landscape/brag.mp4 --fps 30 --quality high --workers 2 --strict
npx --yes hyperframes@0.8.134 render .local/tour/vertical/composition --output .local/tour/vertical/brag.mp4 --fps 30 --quality high --workers 2 --strict
python -m submission.tour.deliver
```

Delete ignored `brag-unbaked.mp4` files when intentionally rendering a new version: delivery preserves those originals so repeated poster bakes are stable. Review settled snapshots and actual rendered frames before sharing. `deliver.py` verifies dimensions, duration, frame count, unchanged AAC packet bytes, frame-zero/poster similarity, and full decode; its machine-readable output is `.local/tour/delivery.json`.

The canonical launch caption is `share-copy.txt`. `judge-tour.md` supplies a separate 55-second hands-on tour plan. Third-party and original-media notices are in `THIRD_PARTY_NOTICES.md`.
