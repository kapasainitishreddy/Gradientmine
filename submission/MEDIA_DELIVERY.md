# Actual media delivery and remaining upload

All four MP4s exist and were decoded and reviewed end to end. Their original footage and provenance remain preserved. Large files are ignored, rather than committed to Git history. [media-delivery.json](../evidence/2026-10-05/media-delivery.json) records exact delivery filenames, byte sizes, SHA-256 hashes and the upload boundary.

| Actual file in the repository workspace | Duration | Evidence notes |
|---|---|---|
| `.local/submission-videos/presentation/final/presentation.mp4` | 150.000s | [Presentation notes](PRESENTATION_VIDEO.md); genuine continuous browser/source capture, complete English captions, silent AAC |
| `.local/submission-videos/product-demo/demo.mp4` | 165.000s | [Demo notes](DEMO_VIDEO.md); genuine continuous recorded-viewer interaction, complete English captions, no audio |
| `.local/tour/landscape/brag.mp4` | 22.000s | [Launch provenance](tour/PROVENANCE.md); original synthesized ambient sound, no voice |
| `.local/tour/vertical/brag.mp4` | 20.000s | Deliberate portrait reframe; original synthesized ambient sound, no voice |

## Actual GitHub attempt

GitHub release creation succeeded at source `dfa77c7a9a793c1ffb91ac07fef39b32baa0c7be`. The subsequent upload to `uploads.github.com` returned **HTTP 403 Forbidden**. The GitHub release API confirmed **zero uploaded assets**. No downloadable video URL or public playback is claimed. The release was converted to a **draft**, with its description corrected to identify the blocked upload. Its owner-accessible URL is https://github.com/kapasainitishreddy/Gradientmine/releases/tag/untagged-18d0a9ece37c19820507 (release ID `404167730`); this is not a judge-accessible media URL.

The exact public-only upload bundle is `.local/release-2026-10-05/`: four MP4s, two posters, two caption files, four provenance/render manifests, one strictly checked read-only viewer ZIP, a delivery manifest and SHA256SUMS. Private identities, database, authenticated checkpoints and browser originals were never included. The viewer ZIP is downloadable local evidence, not a hosted API or Devnet payment.

`uploads.github.com` was added to the saved environment network draft while preserving existing rules. Saving a draft does not publish it, apply runtime permissions or prove upload access. The observed 403 alone does not distinguish network policy from integration/account permissions. There was no unchanged retry loop.

## Owner action

From an authorized environment, check hashes with `sha256sum -c SHA256SUMS` inside the prepared public bundle, then upload the selected files to an authorized free host or the retained GitHub draft. For GitHub, locate the exact draft by ID with `gh api repos/kapasainitishreddy/Gradientmine/releases/404167730`; use that draft's actual tag when uploading, and review its corrected notes before publishing. Confirm that any judge video URL plays signed out and is accepted by the actual portal. A release-download URL alone does not establish that.

Review both longer recordings in full. Their measured durations meet the retrieved FAQ bounds, but organizer acceptance of silent English captions is not established; natural narration can be added if appropriate. All visible model scores refer only to the disclosed local job. No live Devnet payout, Phantom interaction, hosting URL, customer validation or official submission is implied.
