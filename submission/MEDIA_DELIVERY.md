# Colosseum 2026 public submission media (October 10, 2026)

## Public judge assets

A **new, public, non-draft GitHub release** now hosts caption-led recordings captured from the actual deployed read-only local-evidence viewer.

- Release: https://github.com/kapasainitishreddy/Gradientmine/releases/tag/colosseum-submission-2026
- 120-second presentation: https://github.com/kapasainitishreddy/Gradientmine/releases/download/colosseum-submission-2026/gradientmine-pitch-colosseum-2026.mp4
- 165-second product walkthrough: https://github.com/kapasainitishreddy/Gradientmine/releases/download/colosseum-submission-2026/gradientmine-demo-colosseum-2026.mp4
- 2026 product graphic: https://github.com/kapasainitishreddy/Gradientmine/releases/download/colosseum-submission-2026/gradientmine-colosseum-graphic.jpg
- Recording provenance, file sizes and SHA-256: https://github.com/kapasainitishreddy/Gradientmine/releases/download/colosseum-submission-2026/media-manifest.json
- Standalone English subtitle files: `pitch.srt` and `demo.srt` from the same release.

The GitHub Action [Publish Colosseum submission media](https://github.com/kapasainitishreddy/Gradientmine/actions/workflows/colosseum-media.yml) captures genuine page navigation and actual policy/receipt inspectors against `https://gradientmine.pages.dev`, not synthesized app activity. It produces H.264/1080p/30fps recordings, metadata, independent SRT captions and burned-on captions. The video producer uses **an explicit 1920x1080 ASS resolution and a reserved black footer for subtitles** to prevent covering the app. Run outputs and GitHub release assets must be verified again after any future render.

**The public viewer remains read-only recorded evidence.** The videos are not live training or a real Devnet payout, do not show paying users and do not prove the hosted API. The recordings are caption-led, with no human voice or founder face. They are review candidates for the actual portal, not proof of organizer acceptance. A founder-narrated pitch may be stronger and the portal may ask for YouTube, Loom or another supported video URL. Test anonymous playback in a supported host before entering a final link.

## What is left for the founder

1. Watch both current release videos end-to-end and confirm legible captions, correct sequence, no private information, and acceptable audio/narration requirements.
2. Confirm the logged-in Colosseum form accepts the links. If it specifically requires streamed playback from YouTube/Loom/Vimeo, upload the MP4s to a supported host, verify anonymously and enter those links.
3. Confirm real registered team members, name/location, prior work, entity/funding and IP/eligibility declarations, and any contact details required by the owner profile and final survey.
4. Enter the final video and demo links and graphic in the signed-in dashboard; click final Submit and retain receipt before October 12, 2026, 11:59 PM Pacific.
5. A real funded Solana Devnet payout would strengthen the evidence but is not claimed and must not be fabricated.

## Historical October 5 delivery

Previous silent-captioned local video exports, original screen footage and hashes remain documented at [presentation](PRESENTATION_VIDEO.md) and [demo](DEMO_VIDEO.md). An **earlier** release creation and upload attempt failed with HTTP 403 and was kept as a draft with zero uploaded assets. That historical failure does **not** describe the new public `colosseum-submission-2026` release, which has hosted assets.

Previous local-source recording files remain under ignored `.local/` and are not committed to Git history. The new Actions-recorded footage is stored in an expiring run artifact and released separately; no private keys or evaluator databases are uploaded.
