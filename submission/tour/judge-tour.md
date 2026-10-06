# 60-second judge-facing evidence tour

This is the fastest path through the public product at https://gradientmine.pages.dev . It is separate from the required 2–3 minute presentation and ≤3 minute technical demo.

| Time | Actual action | What the judge should learn |
|---|---|---|
| 0–7s | Open the site and leave the recorded-mode banner visible. | This is real recorded local evidence, not a fake live network or fake payment. |
| 7–17s | Stop on **ASSURANCE CONTRACT**. Show the primary metric, minimum delta, family-wise target, candidate budget, assurance-set commitment, named evaluator and numeric-adapter policy. | GradientMine defines what evidence is required before choosing a winner. |
| 17–30s | Scroll to **GRADIENTMINE ARENA**. Compare development and assurance scores. Point out the 95.28% winner and 25.00% disclosed negative control. | Workers can report public validation, but the named evaluator independently recomputes held-out assurance after cutoff. |
| 30–39s | Show +10.56 pp observed improvement, +6.11 pp adjusted lower bound and 360 held-out examples. | A point-estimate leaderboard is not enough; the current v1 contract includes an explicit statistical gate. |
| 39–49s | Show **ARTIFACT FIREWALL**. | This task accepts bounded numeric adapters, hashes and signed manifests against a known architecture instead of executing arbitrary worker code. |
| 49–57s | Show **MODEL PASSPORT** and click **Download JSON**. | The accepted result has inspectable provenance linking parent, artifact, worker, evaluator, policy, assurance commitment and measured evidence. |
| 57–60s | Return to the mode banner / lineage. | Solana settlement is a separate economic layer. This recorded run does not invent a payout. |

## If integrated Devnet proof is completed before submission

After independently verifying the deployed program, funding, registration, settlement, winner and recipient balance delta, replace the final three seconds with the real Explorer transaction. Do not replace the local recorded scores unless the live Devnet run itself produced those exact measurements.

## Reviewer links

- Product: https://gradientmine.pages.dev
- Source: https://github.com/kapasainitishreddy/Gradientmine
- Paste-ready application copy: ../FINAL_FORM_COPY.md
- Technical demo script: ../DEMO.md
- Pitch script: ../PITCH.md
- Assurance research synthesis: ../../docs/ASSURANCE_RESEARCH.md
