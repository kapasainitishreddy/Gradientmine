# GradientMine: final founder pitch, product demo and judge Q&A

Prepared October 11, 2026. Owner must confirm each first-person statement, and personally verify the final portal's video limits and upload-host rules. This is a narrative/recording guide, not a generated testimonial or completed submission.

## The one-sentence hook

**What if a team could put a bug bounty on what its AI model gets wrong?**

GradientMine connects a frozen, measurable model failure to competing fixes, trusted held-out verification and programmable reward rules.

## Founder-spoken presentation (roughly 2 minutes at a natural pace)

> Picture a small AI team with a support-routing model stuck at 84 percent accuracy. They need it above 92. Today, they can hire another consultant or buy more compute, but they're still paying for the attempt rather than the improvement.
>
> GradientMine is a bug bounty marketplace for models. An owner posts a frozen model, baseline, target, evaluator, deadline and reward. Independent engineers and agents submit bounded fixes. After cutoff, a named evaluator runs the same held-out test on all eligible candidates. Only the best fix that clears the predeclared rule can win.
>
> We built a working local proof. Three real worker processes trained PyTorch updates on one machine, including a deliberately disclosed negative control. The frozen Digits baseline scored 84.72 percent. The selected model scored 95.28 percent across 360 held-out examples, a 10.56-point gain. Those are measurements from a small, budget-limited educational model, not enterprise validation.
>
> The interface makes the experiment inspectable: signed manifests, exact artifact hashes, evaluator receipts and a downloadable Fix Passport. The new bounty studio lets a model owner draft an objective and inspect planned economics in the browser without pretending funds have moved.
>
> Why Solana? Two unknown parties need transparent economic rules. Our native Rust program implements escrow, recipient checks, authorized settlement and refunds, verified in a compiled local Solana VM. A named off-chain evaluator still decides quality. We do not claim a funded Devnet payout.
>
> Next, we will test real buyer demand through 3 to 5 model-owning design partners. Our planned business model is a 10 percent fee on successfully settled bounties. Today we have engineering proof, not paying customers.
>
> Compute marketplaces sell compute. Freelance platforms sell time. GradientMine is designed to buy one thing: a measurable improvement that actually checks out.

Deliver this in your own voice, or explicitly label any synthetic narration. The current caption-led released videos are an honest fallback, but a clear founder explanation is much stronger in this founder/startup competition. Do not pretend a synthesized voice is the founder.

## Product demo: 2 minutes 45 seconds maximum

| Timeline | What to show | Why it wins attention |
|---|---|---|
| 0:00-0:15 | Homepage: "AI MODEL BUG BOUNTIES", hero and actual proof | Clear category, not obscure crypto terminology |
| 0:15-0:43 | Bounty Studio: load illustrative example, set baseline 84 and target 92 | Buyer understands exactly what is purchased |
| 0:43-0:58 | Change target below baseline to show validation; restore it | A real product interaction, not a static pitch deck |
| 0:58-1:13 | Inspect hypothetical 10% fee and downloadable **unfunded** blueprint | Transparent economics without fake billing |
| 1:13-1:35 | Judge tour "Real competition": three actual workers, negative control | Actual engineering evidence |
| 1:35-2:00 | "Measured result": 84.72% to 95.28%, held-out set and lower bound | Explains precisely how winner is chosen |
| 2:00-2:25 | Main evidence inspector: immutable policy, signed receipt, Fix Passport | Concrete provenance, not an unverified benchmark image |
| 2:25-2:45 | Judge tour "Why Solana" and visible local/no-payout status | Honest Solana differentiation |

Before re-recording, verify all product pages deployed, desktop/mobile navigation, input validation, local JSON download and signed-inspection links. Never describe a hypothetical support model as customer data. Never show private keys, simulate real payouts, or imply the new Bounty Studio commits funds.

## Skeptical judge questions and grounded answers

**Why does this need crypto?**  
It may not for every private contract. The strongest use case is an unknown model owner and unknown solver who want escrow terms, recipient registration, authorized payout and timeout refunds enforced by a public program. Evaluating model quality stays off-chain with a trusted evaluator, so we do not oversell decentralization.

**Isn't this just Kaggle or Upwork?**  
Those are useful substitutes or supply channels. The proposed integrated product is buyer-defined frozen performance thresholds, private final evaluation, bounded and signed model artifacts, inspected provenance and programmable settlement. We must demonstrate that this combination saves customers money or delivers better fixes, rather than assert every competitor lacks it.

**Couldn't workers cheat the benchmark?**  
Yes, especially the reconstructible public Digits dataset. The current sample is a workflow proof, not a production anti-cheating benchmark. Real use needs licensed private held-outs, strict access control, contest boundaries and more sophisticated leakage checks.

**Who decides whether the model really improved?**  
A named evaluator selected in the contract. It scores all admitted candidates after cutoff using the frozen rules and signs receipts. The cryptography authenticates the bytes and signer, not truth of the score.

**Why is the parent classifier so weak?**  
It is deliberately budget-limited to make a small reproducible prototype. We show a real run and transparent assumptions, not a claim that GradientMine routinely achieves +10.56 points on production tasks.

**Did a payout really happen on Devnet?**  
No. The native Rust Solana escrow was compiled and exercised through local LiteSVM integration. A funded end-to-end Devnet transaction is not verified yet.

**Why won't solvers waste compute?**  
They might. Winner-take-all can be unattractive. We must cap task budgets, publish realistic problem details and test whether expected rewards justify all workers' aggregate compute. Participation payments or better incentives may be required, but none are shipped or funded today.

**What will someone pay, and have they paid?**  
The 10% success fee is a planned hypothesis. No users, paid bounties or actual marketplace fees are claimed. First test is a controlled project with consented design partners and their current alternative costs.

**How big can this get?**  
Gartner projects $64.3B of AI model/platform spending in 2026, but that is background market context, not our serviceable market. The correct estimate must be built bottom-up from teams with repeat model issues, tasks per year, reward sizes and adoption. See docs/COLOSSEUM_STARTUP_CASE_2026.md.

**What if model IP or evaluation data are sensitive?**  
The current local proof is public educational data. Broader private benchmarking is an engineering/research prototype, not enterprise-compliant operation. Production would require explicit rights, isolation, privacy, auditability and a trusted evaluator.

**Why start with classification, not every LLM and agent?**  
Narrow objectives are repeatable and cheap to audit. More general evaluation introduces subjective judges, long-lived hidden data and hard-to-sandbox arbitrary artifacts. Scope discipline is an advantage.

**What did you achieve during this competition?**  
Point to the actual commit history, exact verification workflow URLs, deployed read-only viewer, recorded evidence and live product demonstration. Describe any work before September 14 accurately and disclose assistance. Do not claim the repository history alone proves pre-event ownership or no reused code.

**Why you, personally?**  
Give your real data-science/engineering experience, examples of shipped applied-AI tools and a personal motivation. Confirm your precise education, current commitments and ability to work full-time, rather than reciting a made-up founder story.

## Submission red lines

- Do not invent interviews, users, LOIs, revenue or a real Devnet settlement.
- Do not call hypothetical fee calculation live billing.
- Do not claim the Bounty Studio creates an escrow contract. It exports an unfunded local design.
- Do not imply the research lab is an enterprise production service.
- Do not present any named evaluator as independent of the project unless verified.
- Do not say signatures prove training, correctness or generalization.
