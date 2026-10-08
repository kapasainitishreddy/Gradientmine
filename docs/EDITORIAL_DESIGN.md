# GradientMine editorial redesign (October 2026)

## Visual brief
"Don't guess. Prove it." is a warm-mineral editorial interface based on a museum-of-evidence metaphor, inspired by the premium stage and restrained product-film motion grammar in [@brainextends's Opus 5.5 motion reference](https://github.com/yihui-dev/awesome-opus5-5-videos/blob/main/prompts/brainextends-606193.md). The work is an original UI implementation; it does not copy the original video or branded visuals.

- Warm stone (#efebe3) as the primary page surface; near-black (#0b1010) gallery and proof instrument
- Orange-red (#c64d2b) editorial headline emphasis; mint (#8ad5ab) only for observed improvement
- Overscale black type, generous space, tiny exhibit captions, thin dividers, no speculative growth metrics
- Original vector sculpture of a broken mesh evolving into ordered ribs; it illustrates the idea of improvement, not actual model weight data
- Responsive two-column hero on desktop, stacked gallery on tablet/mobile; semantic HTML, visible focus, keyboard navigation, reduced-motion behavior
- Frontend remains vanilla HTML/CSS/ES modules to preserve the existing FastAPI client, wallet binding, evidence inspector, and low-resource deployment

## Running
The public Cloudflare Pages site serves only a recorded, local CPU experiment. The existing API runs separately using instructions in README and docs/DEPLOYMENT.md. **A frontend deploy does not imply a hosted public validator or Solana Devnet payment.**

The following must remain usable after every design change: #wallet-button, #create-button, job list/filter, #detail, proof canvas, worker commands, evidence downloads, signed receipt inspector, funding intent confirmation, and all native dialogs. The recorded site disables wallet/bounty creation.

## Verification
- node --test tests/web/*.test.mjs
- npm run check
- python -m scripts.browser_qa --out evidence/browser (requires local dev server dependencies and Chromium)
- Check 1440px desktop, 1024px tablet, 390px and 360px mobile for overflow and legibility.
- Cross-check the actual public Cloudflare Pages deployment against the new commit before claiming it is live.

## License
Original vector/SVG, CSS, interface markup, and JavaScript in this repository follow its MIT license. Motion.dev is a separately MIT-licensed optional enhancement. The referenced inspiration repository's prompt license does not grant third-party video or brand-asset rights.
