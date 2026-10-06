# Crypto World's Fair submission checklist

**Status: prepared documents; not submitted.** No owner registration, signed-in portal entry, successful video upload or portal confirmation has been performed in this pass. Actual captioned recordings exist; [MEDIA_DELIVERY.md](MEDIA_DELIVERY.md) documents the HTTP 403 upload attempt and retained draft.

## Official source status

Official entry: https://colosseum.com/worldsfair

Portal and FAQ: https://colosseum.com/hackathon

Rules: https://colosseum.com/legal/Crypto%20World%27s%20Fair%20Hackathon%20Rules.pdf

On October 5, 2026, after the earlier proxy block, bounded read-only requests with TLS verification retrieved all three official sources with **HTTP 200**. The event page, FAQ and extracted rules PDF were read. The earlier proxy CONNECT 403 is superseded by this successful verification. Source bodies, headers, extracted text and a SHA-256 capture manifest are retained outside Git at `/workspace/.gradientmine-setup/final/research/`; that path is machine-local provenance, not a public link. No signed-in dashboard or entrant account was accessed. Current public FAQ fields are verified; signed-in character limits and declarations remain an owner check.

## Verified rules and remaining entrant checks

| Topic | Current official source and requirement | Remaining check / product boundary |
|---|---|---|
| Deadline | Rules §5: October 12, 2026, 11:59 PM Pacific; event page also lists October 12 | October 13, 06:59 UTC / 2:59 AM America/New_York (Philadelphia). Organizer computer is official timekeeper; check for later changes |
| Event window and prior work | Rules §5: September 14, 2026, 6:00 AM PT through deadline. FAQ permits earlier development/pre-existing code with disclosure; judging covers work within the event | Disclose relevant earlier idea, ZIP/source and development accurately. FAQ distinguishes third-party open-source composition from the team's own prior development |
| Eligibility | Rules §3: majority age or 18, whichever is older at start; exclusions/sanctions and employer/entity permissions apply. FAQ: new startups without significant outside capital. Rules §12: all content in English | Owner must check exact jurisdiction, age, sanctions, funding and IP facts; no numeric funding threshold is supplied by the FAQ |
| Team | Rules §§6–7 and FAQ: every member registers; leader adds members/submits; one team per person, one product per team/person. FAQ allows solo founders | No maximum team size was found in these sources; check any signed-in portal limit without inventing one |
| Repository | FAQ requires GitHub link; open source encouraged; private repos allowed if review access is granted to `hackathon@colosseum.com` | GradientMine uses its public MIT repository. FAQ assesses significant event work, authorship and strategic priorities, rather than a specific language/framework |
| Presentation | FAQ: two-to-three-minute presentation | Prepared target 2:30; exported duration must be 120–180 seconds |
| Product demo | FAQ: no more than three minutes explaining product operation | Prepared target 2:45; exported duration ≤180 seconds |
| Fields | FAQ lists product name/brief description, blockchains/tools, all teammate backgrounds, team location, logo/graphic, GitHub, both videos, go-to-market/demand validation/distribution | These public field categories are verified. Exact signed-in field labels, character limits and declarations were not inspected |
| Judging | FAQ: founder/market fit, insight, product/execution, market size, communication, viability, traction. Rules §8: functionality, potential impact, novelty, UX, open-source/composability, business plan | No scoring weights or guaranteed prize outcome asserted; explain the startup and evidence honestly |
| Solana | Event page offers Solana track; rules §14(e) awards that track to products integrating Solana. FAQ permits all blockchain ecosystems | Native Rust/Devnet implementation is the proposed integration. No Anchor, LoRA, LLM, mainnet, token or three-GPU requirement was found |
| AI assistance | FAQ acknowledges backed founders who built MVPs entirely with AI coding tools | No specific mandatory AI-disclosure clause found in the retrieved event page/FAQ/rules. Voluntary truthful disclosure is prepared; complete any actual portal declaration |
| Procedure | FAQ: register, join current competition, access dashboard submission portal; leader completes submission before deadline. Rules §6 requires member registration/profile/consent before deadline | Actual entrant must sign in, verify team/profile facts, review declarations and retain final portal confirmation |

Submit ahead of the deadline. The official PDF is the authority for entrant exclusions and terms; this summary does not establish the owner's personal eligibility. Winning does not require accepting accelerator admission (FAQ), and no accelerator or funding commitment is invented here.

## Materials to enter

| Material | Prepared source | Remaining action |
|---|---|---|
| Product name, one line, description, chain/tools, why blockchain | [PRODUCT.md](PRODUCT.md) | Fit actual field lengths; review latest implementation/evidence |
| Founder background, location and actual team | [TEAM.md](TEAM.md) | Confirm name/location, real members, funding and rights |
| Original logo | [logo.svg](logo.svg) | File exists; upload SVG if accepted, otherwise export PNG as described in RECORDING.md |
| Repository | https://github.com/kapasainitishreddy/Gradientmine | Verify judge access to final source commit |
| Presentation video | [150-second captioned recording](PRESENTATION_VIDEO.md), [PITCH.md](PITCH.md) | Review silent candidate; optionally add natural narration; verify permitted hosting and signed-out playback |
| Product-demo video | [165-second captioned recording](DEMO_VIDEO.md), [RECORDING.md](RECORDING.md) | Review actual recorded-local evidence; verify judge-accessible hosting and signed-out playback |
| Optional short launch film | [Rendered 22-second landscape / 20-second portrait films](tour/README.md) | A separate marketing artifact; it replaces neither required video |
| Market, business model, validation and distribution | [PRODUCT.md](PRODUCT.md), [VALIDATION.md](VALIDATION.md) | Keep hypotheses separate from completed customer research |
| Prior work and AI assistance | [DISCLOSURE.md](DISCLOSURE.md) | Add factual pre-event history and required portal declarations |
| Live URL / chain evidence | https://gradientmine.pages.dev and [docs/BUILD_LEDGER.md](../docs/BUILD_LEDGER.md) | Public URL is verified signed-out as a read-only recorded evidence viewer. It is not the live API/validator and does not prove a Devnet payout. Only enter chain addresses/signatures after finalized verification. |

## Final submission steps

1. From an authorized browser, check for official changes since October 5 and inspect the signed-in fields; update this checklist for any differences.
2. Register actual entrant(s), join the event and verify the team's leader and eligibility facts. Complete TEAM.md and pre-event history in DISCLOSURE.md.
3. Fill the real dashboard fields from PRODUCT.md. Upload the original logo and enter the public repository; include a live URL only if it really works.
4. Review the actual 150-second presentation and 165-second demo, including their silent-caption format. Confirm current portal requirements, optionally add natural narration, and upload to a permitted judge-accessible playback host. Test signed-out playback; a downloadable release asset alone does not establish portal acceptance.
5. Disclose named-validator trust, public benchmark leakage, budget-limited baseline, AI assistance, pre-event work, Devnet-only funds and any unavailable live feature. State separately whether extension-wallet QA and integrated Devnet payout were completed.
6. Review declarations using your own identity and authority. Submit through the portal and retain its confirmation/submission URL. Without portal confirmation status remains **not submitted**.

Do not claim mainnet revenue, customers, independently owned nodes, GPU ownership, hidden-data security, royalties, payment without finalized evidence, a Phantom test based only on a harness, or a video based only on its script.
