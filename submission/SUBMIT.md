# Crypto World's Fair submission checklist

**Status: prepared documents; not submitted.** No owner registration, signed-in portal entry, video upload or portal confirmation has been performed in this pass.

## Official source status

Official entry: https://colosseum.com/worldsfair

Portal and FAQ: https://colosseum.com/hackathon

Rules: https://colosseum.com/legal/Crypto%20World%27s%20Fair%20Hackathon%20Rules.pdf

On October 5, 2026, bounded read-only requests with TLS verification to all three official URLs failed at the environment proxy: `CONNECT tunnel failed, response 403`, curl exit 56, source HTTP code `000`. This is a network-policy blocker, not evidence that Colosseum rejected the project. No source page or signed-in portal was retrieved. The guidance below preserves the prior repository's reported rules; **it is not fresh official verification**. Earlier text labelled its rules check October 5, but captured organizer responses are not stored in this repository. The owner must compare the current pages, PDF and dashboard before submitting and record any change.

## Rules to confirm before entry

| Topic | Inherited guidance / product boundary | Required current check |
|---|---|---|
| Deadline | October 12, 2026, 11:59 PM Pacific | Confirm event deadline and timezone. If unchanged: October 13, 06:59 UTC / 2:59 AM America/New_York (Philadelphia) |
| Event window and prior work | September 14–October 12; earlier development must be disclosed | Read current prior-work terms; disclose idea, ZIP/source, and code developed before the window. Commit timestamps alone do not settle eligibility |
| Eligibility | New startups without significant outside funding; English materials | Confirm funding thresholds, age, restricted jurisdictions, sanctions, rights/IP and any accelerator conditions using the entrant's own facts |
| Team | Each person registers, belongs to one team, submits one product | Confirm current team-size and membership rules in dashboard; no maximum size is invented here |
| Repository | Provide the public GitHub source and history | Confirm visibility, access, open-source/license and submission-time requirements; do not assume a push is an entry |
| Presentation | 2–3 minutes | Verify current allowed length; prepared script targets 2:30 |
| Product demo | No more than 3 minutes | Verify current allowed length; prepared walkthrough targets 2:45 |
| Fields | Product, chain/tools, team/location/background, graphic, repository, videos, market/validation/distribution | Signed-in field names, required attachments and character limits were unavailable; copy prepared text into the actual fields without inventing a portal schema |
| Judging | FAQ previously listed founder-market fit, insight, execution, market size, communication, viability, traction; rules also discussed functionality, impact, novelty, UX, open-source composability and business planning | Compare current published criteria; no scoring weights or guaranteed prize eligibility are asserted |
| Solana | Proposed ecosystem track: native Rust Solana program and Devnet escrow | Confirm current track/prize terms. Prior rules did not establish requirements for Anchor, LoRA, LLMs, mainnet, a new token or three GPUs |
| AI assistance | This project used AI for code, research, tests, design and submission drafts | Check current organizer disclosure/eligibility requirements. Our truthful disclosure is prepared regardless; no organizer-specific AI policy is invented |
| Procedure | Team leader submits via signed-in Colosseum dashboard | Confirm leader authority, all declarations, video-link access and final confirmation |

Plan to submit ahead of the reported deadline. Identity and terms must be confirmed by the actual entrant; this package does not establish their eligibility.

## Materials to enter

| Material | Prepared source | Remaining action |
|---|---|---|
| Product name, one line, description, chain/tools, why blockchain | [PRODUCT.md](PRODUCT.md) | Fit actual field lengths; review latest implementation/evidence |
| Founder background, location and actual team | [TEAM.md](TEAM.md) | Confirm name/location, real members, funding and rights |
| Original logo | [logo.svg](logo.svg) | File exists; upload SVG if accepted, otherwise export PNG as described in RECORDING.md |
| Repository | https://github.com/kapasainitishreddy/Gradientmine | Verify judge access to final source commit |
| Presentation video | [PITCH.md](PITCH.md) | Record, caption, export, upload and test signed out |
| Product-demo video | [DEMO.md](DEMO.md), [RECORDING.md](RECORDING.md) | Record actual mode and evidence; scripts are not videos |
| Optional short launch film | [PRODUCT_TOUR.md](PRODUCT_TOUR.md) | A separate marketing artifact; it replaces neither required video |
| Market, business model, validation and distribution | [PRODUCT.md](PRODUCT.md), [VALIDATION.md](VALIDATION.md) | Keep hypotheses separate from completed customer research |
| Prior work and AI assistance | [DISCLOSURE.md](DISCLOSURE.md) | Add factual pre-event history and required portal declarations |
| Live URL / chain evidence | [docs/BUILD_LEDGER.md](../docs/BUILD_LEDGER.md); public evidence files if produced | Only enter verified URLs, addresses and signatures. Recorded local viewer is read-only; chain-only smoke tests do not prove trained-artifact payout |

## Final submission steps

1. From an authorized browser, inspect the current official event page, FAQ, rules and signed-in fields; update this checklist for any differences.
2. Register actual entrant(s), join the event and verify the team's leader and eligibility facts. Complete TEAM.md and pre-event history in DISCLOSURE.md.
3. Fill the real dashboard fields from PRODUCT.md. Upload the original logo and enter the public repository; include a live URL only if it really works.
4. Record both videos following RECORDING.md, validate durations, upload to a judge-accessible host and test playback in a signed-out browser. No final video URL exists in this package.
5. Disclose named-validator trust, public benchmark leakage, budget-limited baseline, AI assistance, pre-event work, Devnet-only funds and any unavailable live feature. State separately whether extension-wallet QA and integrated Devnet payout were completed.
6. Review declarations using your own identity and authority. Submit through the portal and retain its confirmation/submission URL. Without portal confirmation status remains **not submitted**.

Do not claim mainnet revenue, customers, independently owned nodes, GPU ownership, hidden-data security, royalties, payment without finalized evidence, a Phantom test based only on a harness, or a video based only on its script.
