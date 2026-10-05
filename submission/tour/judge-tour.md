# 55-second judge-facing evidence tour

This is a plan for a longer hands-on tour, separate from the 22-second launch cut and the official hackathon recordings. Use the actual recorded experiment first; demonstrate live transactions only after public signatures and program state verify.

| Time | Actual action | What the viewer learns |
|---|---|---|
| 0–7s | Open the current bounty interface; show the recorded-mode banner and product explanation. | The reward targets measured model improvement. Solana provides the escrow/settlement boundary; the named evaluator remains trusted. |
| 7–16s | Open policy; expand/copy the full policy hash and validator key. Read threshold and cutoff. | Parent, metric, threshold, deadline and evaluator are frozen before evaluation. |
| 16–25s | Show worker onboarding, then the three actual signed submissions and disclosed shuffled-label negative control. | Workers train real CPU head-LoRA adapters; this experiment used three processes on one host. A signed artifact authenticates its author, not the training claim. |
| 25–34s | Show the actual held-out comparison and best eligible row. | 84.72% → 95.28%, +10.56 percentage points on 360 held-out examples. Eligible means selected by policy; it does not mean paid. |
| 34–45s | Open the winning receipt; show the SHA-256 and expected-validator Ed25519 check, copy its full hash, then follow parent/accepted-model lineage. | Signed, content-addressed evidence is inspectable. One validator evaluates this MVP; the signature is not trustless correctness. |
| 45–51s | Show local lifecycle and honest live-mode boundary. | This run is evaluated locally. Devnet settlement is implemented; public payout evidence is pending. No Explorer link is invented. |
| 51–55s | Return to bounty and end on the product wordmark/tagline. | Measure the work. Reward the improvement. |

If a real Devnet proof becomes available, independently verify program ID, cluster, escrow state and signatures before replacing the final boundary. Preserve the local example label and scores unless the displayed live run itself contains those exact measurements.
