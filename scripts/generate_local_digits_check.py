"""Reproduce a non-financial local Digits-model measurement artifact.

This runner exercises the repository's actual CPU-friendly Digits task and
rank-limited adapter. It never creates identities, calls the API, signs auth,
or touches a wallet, RPC endpoint, or transaction.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gradientmine.crypto import digest  # noqa: E402
from gradientmine.ml import make_task, merge_adapter, predict, train_adapter  # noqa: E402
from gradientmine.scoring import assess  # noqa: E402


def build_report(source_sha: str) -> dict:
    task = make_task()
    adapter, losses = train_adapter(task["model"], task["train"])
    baseline_predictions = predict(task["model"], task["test"]["x"])
    candidate_predictions = predict(merge_adapter(task["model"], adapter), task["test"]["x"])
    score = assess(
        task["test"]["y"],
        baseline_predictions,
        candidate_predictions,
        max_candidates=task["manifest"]["max_submissions"],
    )

    negative_adapter, negative_losses = train_adapter(task["model"], task["train"], shuffle_labels=True)
    negative_predictions = predict(merge_adapter(task["model"], negative_adapter), task["test"]["x"])
    negative_score = assess(
        task["test"]["y"],
        baseline_predictions,
        negative_predictions,
        max_candidates=task["manifest"]["max_submissions"],
    )
    if score["n"] != len(task["test"]["y"]) or not score["eligible"] or negative_score["eligible"]:
        raise RuntimeError("Expected positive candidate and ineligible shuffled-label negative control.")

    return {
        "source_sha": source_sha,
        "status": "passed",
        "experiment": "Local public Digits rank-limited head adaptation using repository deterministic test fixture",
        "torch_version": torch.__version__,
        "synthetic_ui_fixture": False,
        "remote_submission": False,
        "wallet_or_auth_operation": False,
        "chain_rpc_or_transaction": False,
        "baseline_sha256": digest(task["model"]),
        "training_data_sha256": task["manifest"]["train_sha256"],
        "held_out_evaluation_sha256": task["manifest"]["evaluation_sha256"],
        "candidate_sha256": digest(adapter),
        "candidate_training": {
            "steps": len(losses), "first_loss": losses[0], "last_loss": losses[-1], "rank": adapter["rank"]
        },
        "candidate_evaluation": score,
        "negative_control": {
            "steps": len(negative_losses),
            "first_loss": negative_losses[0],
            "last_loss": negative_losses[-1],
            "evaluation": negative_score,
        },
        "limitations": [
            "Digits is a public dataset that can be reconstructed; not a secret or anti-leakage guarantee.",
            "The paired bootstrap interval is approximate and assumes IID examples.",
            "This local measurement is separate from the browser synthetic receipt; it is not a signed bounty receipt or settlement.",
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("evidence/proposal-2026-10-28/local-journey/digits-local-model-check.json"),
    )
    args = parser.parse_args(argv)
    root = ROOT
    source_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=root, text=True).strip()
    report = build_report(source_sha)
    output = args.out if args.out.is_absolute() else root / args.out
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "source_sha": source_sha,
        "output": str(output),
        "baseline_accuracy": report["candidate_evaluation"]["baseline_accuracy"],
        "candidate_accuracy": report["candidate_evaluation"]["candidate_accuracy"],
        "delta": report["candidate_evaluation"]["delta"],
        "lower_bound": report["candidate_evaluation"]["bootstrap_lower_bound"],
        "n": report["candidate_evaluation"]["n"],
        "candidate_eligible": report["candidate_evaluation"]["eligible"],
        "negative_control_eligible": report["negative_control"]["evaluation"]["eligible"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
