# Crypto World's Fair final submission checklist

**Status: product and submission package prepared on the model-bug-bounty branch. Portal submission is not yet claimed.**

Official event: https://colosseum.com/worldsfair  
Official hackathon FAQ: https://colosseum.com/hackathon

Current public Colosseum guidance verified October 6, 2026:

- hackathon dates: September 14 to October 12, 2026
- submissions due October 12, 2026
- one product submission per team / individual
- pre-existing development is allowed but must be disclosed
- GitHub repository required
- presentation video: 2 to 3 minutes
- product demo: no more than 3 minutes
- portal asks for product/business context, team, blockchain/tools, logo, GitHub, videos, GTM, demand validation and distribution
- judging includes founder-market fit, insight, product/execution, market size, communication, viability and traction

## Final positioning

### Category

**AI model bug bounties**

### Tagline

**Put a bounty on your AI's worst problem.**

### One-line pitch

**GradientMine is a bug bounty marketplace for AI models: companies post measurable model failures, engineers and AI agents compete to fix them, and the best verified improvement can settle through Solana.**

### Strategic framing

Do not lead with "assurance market."

Lead with:

1. model has a measurable problem
2. owner posts a bounty
3. workers compete on fixes
4. hidden evaluation verifies the best result
5. Solana settles the economic outcome

Then show the assurance machinery as the reason the simple bounty idea can be trusted.

## Prepared materials

| Material | Source | Status |
|---|---|---|
| Product name / tagline / description | FINAL_FORM_COPY.md | Ready |
| Problem / insight / market / business | PRODUCT.md | Ready |
| Use cases and initial wedge | USE_CASES.md | Ready |
| 2–3 minute pitch | PITCH.md | Ready for recording |
| ≤3 minute product demo | DEMO.md | Ready for recording |
| Exact shot plan | RECORDING.md | Ready |
| 60-second judge brief | JUDGE_BRIEF.md | Ready |
| Repository | https://github.com/kapasainitishreddy/Gradientmine | Public |
| Public evidence viewer | https://gradientmine.pages.dev | Existing viewer; update only after merge/deploy |
| Logo | logo.svg | Ready |
| Team facts | TEAM.md | Owner review still required |
| Prior work / AI disclosure | DISCLOSURE.md | Owner review still required |

## Current engineering evidence

The checked-in proof-of-function remains:

- 84.72% frozen parent held-out accuracy
- 95.28% selected candidate
- +10.56 percentage-point improvement
- +6.11 percentage-point adjusted lower bound
- 360 held-out examples
- three real worker OS processes on one host
- one shuffled-label negative control
- content-addressed bounded model artifacts
- signed worker manifests and evaluator receipts
- native Rust Solana escrow program
- compiled-program local LiteSVM integration

## What judges should understand in 30 seconds

**Problem:** AI teams pay for people and compute when what they actually want is a model metric to improve.

**Product:** Put a bounty on a measurable model failure.

**Supply:** ML engineers and AI agents compete to fix it.

**Verification:** Public progress is separated from hidden final evaluation.

**Crypto reason:** Solana locks the reward and settlement rules between counterparties who do not need to trust one another.

**Business:** planned 10% success fee on settled bounties, with private/higher-assurance evaluation as an enterprise extension.

## Submission order

1. Re-run automated tests on the final branch.
2. Merge the branch only after CI passes.
3. Verify the deployed public viewer signed out.
4. Record a fresh 2–3 minute pitch using PITCH.md.
5. Record a fresh ≤3 minute demo using DEMO.md.
6. Use natural narration if possible. The older silent-caption videos predate this positioning and should be fallback only.
7. Upload videos to a judge-accessible host and verify signed-out playback.
8. Fill portal fields from FINAL_FORM_COPY.md.
9. Review TEAM.md and DISCLOSURE.md against actual founder/team/prior-work facts.
10. Submit before the official deadline and retain portal confirmation.

## Claims to avoid

Do not claim:

- customers or revenue that do not exist
- validated willingness to pay before interviews
- trustless or decentralized model-quality verification
- proof of training
- private benchmark security from the public Digits split
- three independent machines
- a finalized Devnet payout without exact chain evidence
- mainnet funds
- arbitrary LLM fine-tuning in the current recorded proof
- USDC support in the current implementation unless it is actually added and tested

## Strong next engineering proof

The single highest-value remaining proof is an integrated Devnet run where the same trained winning artifact is registered, selected and paid to the matching worker, with finalized Explorer evidence.

Do not delay the submission if free Devnet funding remains unavailable. The product can still be submitted honestly with the local proof and compiled program evidence.
