# GradientMine: reviewer fast path

**One-line product:** Put a bounty on a measurable AI model failure. Competing engineers and agents submit fixes. A trusted held-out evaluator chooses the best eligible improvement; native Solana escrow enforces economic settlement rules when genuinely funded.

## First 90 seconds

1. **[Start the guided judge walkthrough](https://gradientmine.pages.dev/judge.html).** It loads actual before/after results and workers from a recorded JSON run. You can review all six sections using buttons or keyboard arrows.
2. **[Try the Bounty Studio](https://gradientmine.pages.dev/bounty.html).** Load the illustrative support-routing example. Set baseline 84, target 92, candidate score 95 and inspect the rule and hypothetical 10% fee. Change target to 82 to watch validation refuse a regressive metric. Confirm your rights only if applicable before downloading an unfunded JSON draft. No network write, billing or on-chain call happens.
3. **[Inspect exact evidence in the public product](https://gradientmine.pages.dev/#workspace).** Open the immutable policy, signed worker manifest, winning evaluation receipt, and downloadable Fix Passport. The viewer is read-only.
4. **[Watch the captioned presentation and real-website demo](https://github.com/kapasainitishreddy/Gradientmine/releases/tag/colosseum-submission-2026).** These recordings predate the final studio/tour feature. They are evidence videos, not live Devnet payouts.

## Numbers that are actually supported

| Dimension | Recorded local proof | Limitation |
|---|---|---|
| Frozen model baseline | 84.72% Digits accuracy | Deliberately budget-limited educational parent |
| Selected candidate | 95.28% held-out accuracy | Not a production customer model |
| Improvement | +10.56 percentage points | 360 held-out examples on a reconstructible public benchmark |
| Adjusted lower bound | +6.11 percentage points | Approximate paired-bootstrap comparison, not generalization guarantee |
| Workers | Three independent OS processes, one host | Third is disclosed shuffled-label negative control |
| Artifacts | Hashes, signed worker manifests/receipts, bounded numeric adapters | Does not cryptographically prove training or freedom from backdoors |
| Blockchain | Native Rust escrow, compiled local LiteSVM integration | No finalized funded Devnet training-to-payout proof |
| Business | Planned 10% success fee | No current fee collection, customers, revenue or paid pilots |

The application **does not mine tokens** and has no investment cryptocurrency.

## What makes it a product instead of a benchmark screenshot

- The buyer-side Bounty Studio validates measurable goals, metric direction, reward/candidate terms, an evaluator field and model/data-rights acknowledgement. It exports a clearly labeled local **unfunded** design blueprint. It is not a live escrow creation endpoint.
- The judge tour shows actual recorded candidate results, not fixed invented leaderboard entries. It fails closed when the recorded source is unavailable.
- The main evidence viewer verifies exact artifact bytes, hashes and signatures against expected signers, with explicit evaluator authority and no fake transaction links.
- The production roadmap intentionally separates a useful objective market from privacy/security work needed for arbitrary private LLM bounties.

## Solana and engineering proof

- [Escrow source](../program/src/lib.rs)
- [Implementation and tests](BUILD_LEDGER.md)
- [Architecture and trusted boundary](ARCHITECTURE.md)
- [Threat model](THREAT_MODEL.md)
- [Research Lab limitations](RESEARCH_LAB.md)
- [Open-source dependencies and attributions](../THIRD_PARTY_NOTICES.md)

Repo run commands are in [README](../README.md). Automated Node/browser checks are maintained in [tests](../tests/web/bounty-studio.test.mjs) and [browser QA](../scripts/studio_browser_qa.py).

## Startup case

- **Customer:** small AI teams owning a narrow performance metric.
- **Seller:** independent ML engineers and bounded research agents.
- **Economic product:** buyer-defined success contract and verified winner.
- **Business:** proposed 10% settled-bounty fee, optional private evaluator.
- **Initial validation:** 3–5 consented design partners, controlled tasks, track the full cost of all attempts and evaluations.
- **Current traction:** no external buyers, revenue, LOIs, interviews or paid pilots claimed.
- **Market:** Gartner's 2026 AI model/platform spending forecast is background context, not a GradientMine TAM. Bottom-up demand remains unmeasured.
- **Risks:** evaluator trust, data leakage, solver entry economics and product willingness to pay.

Detailed honest business argument: [Colosseum startup case](COLOSSEUM_STARTUP_CASE_2026.md). Pitch and skeptical judge Q&A: [founder presentation guide](../submission/FOUNDER_PITCH_AND_JUDGE_QA_2026.md).

## Development-time disclosure

Only work completed within the event's judging window counts; earlier ideas or code must be truthfully disclosed. AI assistance used for research, implementation, debugging, testing, design and draft writing is documented in [disclosures](../submission/DISCLOSURE.md). This file does **not** assert a completed portal submission. The founder must confirm ownership, legal/IP and eligibility facts in the authenticated Colosseum portal.
