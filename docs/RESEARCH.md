# Research and differentiating scope

These are primary research or project references, with verification status made explicit below. No competing protocol implementation is vendored. No claim of being the first outcome-paid AI marketplace is made.

## Verification status, October 5, 2026

Verified-TLS, bounded read-only requests to arxiv.org (both papers), gensyn.ai (Verde), solana.com (deployment), and archive.ics.uci.edu (dataset) failed at the environment proxy with `CONNECT tunnel failed, response 403` (curl exit 56, no source HTTP response). Their descriptions and URLs below are preserved from the repository's earlier research notes; they were **not freshly verified in this pass**. The earlier notes labelled their check October 5, but no captured source response is stored here. Check those original sources from an authorized browser before using their statements as current external evidence.

Native HTTPS Git reads did succeed for the two official Wallet Standard repositories. Read-only source checkouts were inspected at `wallet-standard/wallet-standard` commit `c49b56d60fbac2e68e0f3536707fa33030652f9e` and `anza-xyz/wallet-standard` commit `c4d06f9f2668ebec3f2747c9fcf5e2382a2fc36f`. Both carry Apache-2.0 licenses. These are reference-source revisions, not bundled npm dependencies.

## Low-rank adaptation

Hu et al., **LoRA: Low-Rank Adaptation of Large Language Models** (2021), https://arxiv.org/abs/2106.09685 . LoRA freezes original weights and trains low-rank updates. GradientMine uses the underlying rank-factorization idea in an original PyTorch implementation on a small neural classifier head. It does not reproduce the paper's large-language-model experiments or performance claims. This reduces artifact size and keeps the full proof-of-function loop reproducible on a CPU.

## Proof of training is a different problem

Jia et al., **Proof-of-Learning: Definitions and Practice** (2021), https://arxiv.org/abs/2103.05633 . This studies evidence and verification of training. GradientMine does not implement that proof system. A signed recipe or checksum is only an authenticated commitment, not evidence that a particular number of training steps actually happened. Paying for an evaluated model artifact does not require pretending otherwise.

## Untrusted ML verification

Gensyn, **Verde: A Verification System for Machine Learning over Untrusted Nodes** (2025), https://www.gensyn.ai/research/verde-a-verification-system-for-machine-learning-over-untrusted-nodes . Gensyn studies verifiable training on untrusted machines, including execution disagreement. GradientMine makes a narrower tradeoff: a named central evaluator computes a held-out comparison while Solana enforces escrow and payout authorization. We have not integrated Verde, claimed its guarantees or reused its implementation.

## Wallet and chain composition

Solana's official deployment documentation, https://solana.com/docs/programs/deploying , is the deployment reference, with fresh access blocked as noted above. Wallet Standard sources are https://github.com/wallet-standard/wallet-standard and https://github.com/anza-xyz/wallet-standard . The inspected interfaces define app-ready/register-wallet discovery, `standard:connect`, account-change events, `solana:signMessage`, and `solana:signTransaction`. The signing APIs can return changed message/transaction bytes; GradientMine's narrower security contract rejects changes to its exact authentication message and transaction intent. This may reject otherwise legitimate wallet features and is not proof of compatibility with every extension.

Independent numerical experiments avoid claiming tightly synchronized distributed pretraining. The program remains small: immutable bounty terms, candidate commitments, authorized winner settlement, timeout refund. Compiled-SBF local VM execution is distinct from deployment and real Devnet evidence.

## Dataset and scientific limits

E. Alpaydin and C. Kaynak, **Optical Recognition of Handwritten Digits** (1998), UCI record https://archive.ics.uci.edu/dataset/80/optical+recognition+of+handwritten+digits , DOI https://doi.org/10.24432/C50P49 . GradientMine uses the scikit-learn packaged digits subset; attribution and the inherited CC BY 4.0 record are in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). Current UCI page access was blocked, so that license statement still needs a source check.

The 64-input / 48-hidden / 10-output classifier parent is intentionally trained on just 240 examples for 18 epochs. Its low-rank head update is a proof-of-function workload, not a strong baseline comparison or evidence of LLM performance. The evaluation API withholds scores until cutoff, but public source data and the split seed make the 360-example evaluation set reconstructible. Approximate paired-bootstrap eligibility and candidate-count correction do not repair leakage or establish generalization. A named evaluator remains trusted to report correct measurements.

## Competitive position, not invented market evidence

The distinction is **an inspectable outcome-bounty workflow**, rather than selling rented GPU-hours or minting a new token. This implementation demonstrates frozen terms, independent experiments, before/after results, authenticated evidence and settlement rules. It is not yet a decentralized verification network or a production-scale competitor to Gensyn. No competitor revenue, customer count or market-share figures are asserted without a primary source.

## Features deliberately rejected from this release

- Lineage royalties: ancestry alone does not establish marginal causal contribution or legal entitlement.
- Reputation/miner discovery: three local process IDs are not an independently operated network; a public wallet history is not a unique human or reliable reputation.
- Autonomous agent miners: the protocol can accept a compatible worker, but there is no shipped autonomous research agent.
- Giant-model distributed training: communication, device heterogeneity and verification costs are different problems from independent adapter experiments.
- A new token and “mining returns”: unnecessary for a bounty workflow and misleading for a Devnet demonstration.

## Next experiment worth testing

With consenting task owners, compare an outcome-priced bounty against ordinary contracted fine-tuning on a properly licensed, genuinely private evaluation set. Predeclare baseline strength, utility and non-regression metrics, maximum evaluator cost and winner rules. Measure total compute consumed by all entrants, not just winning compute. This is a proposed validation study, not completed traction.
