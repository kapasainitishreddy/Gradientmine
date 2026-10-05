# Threat model and known limits

**Release boundary: Devnet demonstration, not audited financial infrastructure.** Real-money use is intentionally unsupported. The named evaluator, its host and the selected RPC are trusted. No security audit, validator consensus, zero-knowledge proof, proof of learning, anti-Sybil guarantee or protected training-data license is claimed.

| Risk | Implemented control | Remaining limitation |
|---|---|---|
| Wallet message replay / cross-origin login | Exact domain, wallet, random nonce and expiry; Ed25519 signature; one-time nonce; hashed bearer-session storage | Compromised frontend, wallet or same-origin host can still mislead the user |
| Transaction substitution | Browser inspects one exact legacy instruction and signer permissions; refuses modified wallet message; API independently reconstructs and verifies signed bytes | Users must independently verify program identity and trust a deployment. Priority-fee instructions added by wallets are intentionally rejected |
| Wrong network / placeholder deployment | Client pins Devnet genesis and requires an executable non-System program | Bytecode is not intrinsically Devnet-only. Network RPC and program upgrade authority are trust assumptions |
| Fabricated worker score | Held-out scoring is recomputed from the numeric adapter; worker's local score is not paid on trust | A malicious evaluator can sign false scores. The on-chain program cannot judge ML correctness |
| Untrusted artifacts / code execution | Size limits, strict JSON, shape/rank/numeric bounds, SHA-256 checks; no pickle or arbitrary model code | Supported task is deliberately narrow; large-model loaders require a new security design |
| Benchmark leakage / adaptive overfitting | Frozen dataset commitments, no held-out download API, evaluation after cutoff, capped candidates | Dataset and split seed are public and reconstructible. This does NOT prevent benchmark gaming. Repeated rounds further select against the same test set |
| Statistical overclaim | Paired accuracy comparison, bounded candidate family, explicit bootstrap method/seed | Approximate IID procedure on a small sample, not exact finite-sample coverage or confidence about generalization. Bonferroni-style adjustment does not fix leaked data |
| Copying work / Sybil wallets | One artifact and one entry per wallet; exact duplicate artifact rejection | No proof of GPU ownership, work performed or unique human. Equivalent or stolen weights may evade exact duplicate checks |
| Validator refuses / crashes | Creator-only timeout refund, API-independent refund CLI | Winner can lose payout if evaluator stalls until timeout; refund race is resolved by the chain. No adjudication or compensation mechanism |
| Double or misdirected payout | Named validator authorization, registered recipient, policy/receipt bindings, on-chain terminal state, exact finalized transaction and balances | Off-chain eligibility remains centralized; a validator can favor a registered candidate |
| RPC timeout / expired transaction | Persist-before-send, identical-byte retries, explicit expired-attempt recovery, retained signatures | RPC correctness and availability remain trusted; missing response is never interpreted as payment |
| Artifact availability | Durable volume, content hashes, browser download verification, export allowlist | A hash is not storage. Losing the volume may make evidence unavailable even if the hash survives on-chain |
| Server abuse | Authentication, rate limits, bounded jobs/submissions/artifacts, numeric-only execution, no remote user code | No production-grade DDoS protection, separate tenant queues or permissionless costly evaluation. Wallets are cheap |
| Secret exposure | Identities stay local, 0600 files, private data directory, no API key export, public artifact allowlist, CI avoids key artifacts | Operators must protect encrypted backups and host access. Do not mount the entire data directory under static hosting |

## Storage and availability

Back up SQLite, artifacts and the private validator identity together, encrypted and offline. A snapshot must preserve a consistent transaction state. Never make the backup, worker identities, private-task.json or environment secrets publicly downloadable. Restoring an identity alone is not restoring the evidence or database.

## Escrow economics and rent

Rewards are native Devnet SOL, not USDC or a custom token. The winner receives the full committed reward; there is no live protocol commission or lineage royalty. The creator and workers pay testnet account rent and fees. Timeout refund returns only the reward; this version has no account-close/rent-reclaim instruction. No profit, yield or monetary valuation is implied by Devnet SOL.

One winner means other honest workers may receive no reward. The marketplace is not yet validated as an economically efficient way to buy improvements. Any later paid version needs private, independently governed evaluation; a stronger baseline; anti-collusion and dispute design; proper artifact licensing; an audit; and actual customer research.

## Reporting

Do not test against another person's bounty or wallet. Reproduce locally or on dedicated Devnet identities. Report a reproducible issue with public hashes, redacted logs and version identifiers. Never post a private key, seed phrase, test-set records or a session token to a public issue.
