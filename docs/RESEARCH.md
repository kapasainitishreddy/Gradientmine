# Research and differentiating scope

Sources checked October 5, 2026. These are primary research or project sources. No code from competing protocols has been copied. No claim of being the first outcome-paid AI marketplace is made.

## Low-rank adaptation

Hu et al., **LoRA: Low-Rank Adaptation of Large Language Models** (2021), https://arxiv.org/abs/2106.09685 . LoRA freezes original weights and trains low-rank updates. GradientMine uses the underlying rank-factorization idea in an original PyTorch implementation on a small neural classifier head. It does not reproduce the paper's large-language-model experiments or performance claims. This reduces artifact size and keeps the full proof-of-function loop reproducible on a CPU.

## Proof of training is a different problem

Jia et al., **Proof-of-Learning: Definitions and Practice** (2021), https://arxiv.org/abs/2103.05633 . This studies evidence and verification of training. GradientMine does not implement that proof system. A signed recipe or checksum is only an authenticated commitment, not evidence that a particular number of training steps actually happened. Paying for an evaluated model artifact does not require pretending otherwise.

## Untrusted ML verification

Gensyn, **Verde: A Verification System for Machine Learning over Untrusted Nodes** (2025), https://www.gensyn.ai/research/verde-a-verification-system-for-machine-learning-over-untrusted-nodes . Gensyn studies verifiable training on untrusted machines, including execution disagreement. GradientMine makes a narrower tradeoff: a named central evaluator computes a held-out comparison while Solana enforces escrow and payout authorization. We have not integrated Verde, claimed its guarantees or reused its implementation.

## Wallet and chain composition

Solana's official deployment documentation, https://solana.com/docs/programs/deploying , and maintained Wallet Standard interfaces, https://github.com/anza-xyz/wallet-standard , inform the integration. Independent numerical experiments avoid claiming tightly synchronized distributed pretraining. The program remains small: immutable bounty terms, candidate commitments, authorized winner settlement, timeout refund.

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
