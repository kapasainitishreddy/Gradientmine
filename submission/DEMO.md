# Product demo: maximum 3 minutes

Target: 2 minutes 45 seconds. This video answers “how does the product work?” rather than repeating the startup pitch.

## 0:00–0:12 | Establish truth

Open the actual deployment or https://gradientmine.pages.dev.

Say: “This page is a read-only recording of a verified local experiment. It is not a live decentralized network and no blockchain payment occurred in this run.”

Keep the mode banner visible.

## 0:12–0:42 | Assurance Contract

Open the selected bounty and pause on **ASSURANCE CONTRACT**.

Explain:
- primary metric: accuracy
- minimum required improvement
- named evaluator
- predeclared eight-candidate budget
- 20,000 bootstrap resamples
- committed assurance-set hash
- bounded numeric adapter policy

Say: “These terms are committed before the result is known. Solana will ultimately bind the economic terms; the evaluator still judges model quality.”

If a verified live Devnet session exists, create the bounty with a dedicated test wallet and show the exact transaction review. Otherwise stay in the recorded viewer.

## 0:42–1:20 | Arena

Show **GRADIENTMINE ARENA**.

Use the real recorded values:
- frozen parent: 84.72%
- worker A assurance: 95.00%
- worker B assurance: 95.28%, winner
- disclosed shuffled-label negative control: 25.00%

Point out that development scores are worker-reported public validation, while assurance scores are held-out evaluator results released after cutoff.

Say: “Workers cannot make themselves eligible by posting a flattering public score. The named evaluator recomputes the held-out result.”

## 1:20–1:52 | Statistical gate

Show:
- observed winner delta: +10.56 pp
- adjusted lower confidence bound: +6.11 pp
- 360 held-out examples

Say: “A higher point estimate is not enough. The current v1 policy requires the minimum delta and a positive, multiple-candidate-adjusted paired-bootstrap lower bound. It is an approximate finite-sample check, not a guarantee of generalization.”

## 1:52–2:18 | Artifact Firewall + Passport

Scroll to **ARTIFACT FIREWALL**.

Show that this release accepts a bounded numeric adapter, verifies content hashes and signed manifests, requires the known model architecture and validates merged weights, and does not execute arbitrary worker code.

Then show **MODEL PASSPORT** and download the JSON.

Say: “The passport links the parent, accepted model, worker, evaluator, policy commitment, assurance-set commitment and measured evidence. Provenance is evidence, not a declaration that the model is trustworthy.”

## 2:18–2:36 | Solana boundary

If an integrated Devnet run has been completed, show the real finalized funding/registration/settlement links and winner address.

If it has not, say:

“This recorded run verifies the training and assurance workflow, not a blockchain payout. The native Solana program has been compiled and exercised locally in LiteSVM; integrated Devnet settlement remains pending and the UI does not invent a transaction.”

## 2:36–2:45 | Close

Show the lineage from parent to accepted candidate.

End:

“Compute is an input. The product is an assured improvement.”

## Recording safety

Use only dedicated test wallets. Never expose a seed phrase, private key, bearer token, validator database or private evaluation data. Do not call the negative control a detected cheater. Do not claim customer traction, decentralized verification or a Devnet payout without the corresponding evidence.
