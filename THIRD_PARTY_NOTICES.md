# Research, data and dependency notices

Original application code, Rust escrow, browser adapter, scripts and geometric logo are MIT-licensed under LICENSE. No competitor implementation was copied. Calling dependency APIs is not a claim that we authored those libraries. Source packages retain their own notices; distribute those notices when redistributing dependency binaries.

## Dataset attribution

E. Alpaydin and C. Kaynak (1998), **Optical Recognition of Handwritten Digits**, UCI Machine Learning Repository, DOI [10.24432/C50P49](https://doi.org/10.24432/C50P49). Official dataset record: https://archive.ics.uci.edu/dataset/80/optical+recognition+of+handwritten+digits . The record identifies **CC BY 4.0**, https://creativecommons.org/licenses/by/4.0/ . Accessed October 5, 2026. No endorsement is implied.

The packaged scikit-learn digits subset is used. GradientMine normalizes pixel values by 16, performs deterministic stratified train/validation/test splitting, and trains numeric model weights. Public artifacts are outputs of this training, not the original authors' weights. This is a public and reconstructible dataset, unsuitable as a secret real-money evaluation set.

## Libraries

Versions are pinned in pyproject.toml / program/Cargo.lock. Python license metadata was inspected in the installed distributions during this release.

| Dependency | Version used | License / primary project |
|---|---|---|
| PyTorch | 2.10.0, CPU build | BSD-style; https://github.com/pytorch/pytorch/blob/main/LICENSE |
| scikit-learn | 1.8.0 | BSD-3-Clause; https://github.com/scikit-learn/scikit-learn/blob/main/COPYING |
| NumPy | 2.3.5 | BSD-3-Clause with bundled notices; https://numpy.org/doc/stable/license.html |
| FastAPI | 0.142.2 | MIT; https://github.com/fastapi/fastapi/blob/master/LICENSE |
| Pydantic | 2.13.5 | MIT; https://github.com/pydantic/pydantic/blob/main/LICENSE |
| HTTPX | 0.28.1 | BSD-3-Clause; https://github.com/encode/httpx/blob/master/LICENSE.md |
| Uvicorn | 0.48.0 | BSD-3-Clause; https://github.com/encode/uvicorn/blob/main/LICENSE.md |
| cryptography | 50.0.2 | Apache-2.0 OR BSD-3-Clause; https://github.com/pyca/cryptography/blob/main/LICENSE |
| solders | 0.29.0 | MIT; https://github.com/kevinheavey/solders/blob/main/LICENSE |
| Solana program crates | Locked in program/Cargo.lock | Apache-2.0 / individual crate metadata; https://github.com/anza-xyz/solana-sdk |
| Ruff | 0.14.10, development only | MIT; https://github.com/astral-sh/ruff/blob/main/LICENSE |
| Playwright | 1.57.0, development only | Apache-2.0; https://github.com/microsoft/playwright/blob/main/LICENSE |

Wallet Standard discovery and signing interfaces were checked against the maintained official specifications, not copied as an implementation: https://github.com/wallet-standard/wallet-standard and https://github.com/anza-xyz/wallet-standard . The browser adapter is original, deliberately restricted to legacy single-instruction transactions. No wallet or sponsor logo is bundled. No external font files are bundled.

For research credits and precisely limited claims, read docs/RESEARCH.md. The paper licenses are not used as licenses for any third-party implementation. New tasks/models must separately document model and dataset licenses before use.


## Video-production references

- **latent-spaces/brag** — https://github.com/latent-spaces/brag — MIT. Used as an optional development-time agent skill for planning/rendering a short launch video. It is not a GradientMine runtime dependency.
- **feitangyuan/onetake** — https://github.com/feitangyuan/onetake — PolyForm Noncommercial 1.0.0. GradientMine documentation uses its publicly described continuity/carry ideas only as creative reference. Do not copy, vendor, modify, or execute OneTake code for a commercial/promotional deliverable unless the intended use is confirmed to comply with its license.

No OneTake source code or assets are vendored into GradientMine.
