"""Bounded autonomous candidate-search worker for GradientMine Research Lab.

Searches ONLY public development examples. The held-out evaluation split stays
encrypted on the operator, and the agent never receives it. No LLM is trusted
to write executable evaluator code or sign on behalf of a worker.
"""

from __future__ import annotations

import argparse
import itertools
import json
import re
import time
from collections import Counter

from .cli import client_for, login, request
from .crypto import Identity, digest
from .lab_evaluation import BASE, KINDS, evaluate_case, tokens, validate_artifact


def candidate_options(kind, docs, development, max_proposals=18):
    """Search a small, reproducible set of bounded declarative candidates."""
    original = BASE[kind]
    proposals = [dict(original)]
    if kind in ("retrieval", "grounded_qa"):
        basic = dict(original)
        for top_k, title_boost in itertools.product((1, 2, 3, 4), (1, 2, 3)):
            options = dict(basic, top_k=top_k, title_boost=title_boost)
            if kind == "grounded_qa":
                options["min_overlap"] = 1
            proposals.append(options)
        # Infer candidate synonyms from *public* training labels, not test examples.
        by_id = {doc["id"]: doc for doc in docs}
        relations = Counter()
        for case in development:
            query = case.get("query") or case.get("question", "")
            for source in case["relevant_ids"]:
                if source not in by_id:
                    continue
                related = set(tokens(by_id[source]["title"] + " " + by_id[source]["text"]))
                for term in set(tokens(query)) - related:
                    for word in related:
                        if re.fullmatch(r"[a-z0-9]{2,24}", word) and re.fullmatch(r"[a-z0-9]{2,24}", term):
                            relations[(term, word)] += 1
        synonyms = {}
        for (term, word), _ in relations.most_common(15):
            synonyms.setdefault(term, word)
            if len(synonyms) >= 8:
                break
        if synonyms:
            proposals.extend(
                dict(original, top_k=k, title_boost=2, expansion=synonyms)
                for k in (1, 2, 3)
            )
    elif kind == "safety_refusal":
        refusals = Counter()
        normals = Counter()
        for case in development:
            phrase = set(tokens(case["prompt"]))
            target = refusals if case["should_refuse"] else normals
            for token in phrase:
                if re.fullmatch(r"[a-z0-9]{2,24}", token):
                    target[token] += 1
        selected = [word for word, count in refusals.most_common()
                    if count > normals[word] and word not in {"please", "tell", "about", "request"}]
        for count in (1, 3, 6, 12, 20):
            terms = sorted(set(selected[:count]))
            if terms:
                proposals.append(dict(original, block_terms=terms, allow_terms=[]))
    elif kind == "efficiency":
        for width, top_k in itertools.product((1, 2, 4, 8, 16), (1, 2, 4)):
            proposals.append(dict(original, max_docs=width, top_k=top_k))
    elif kind == "llm_prompt":
        prompts = [
            "Given the following evidence: {context}\nAnswer this question precisely: {question}\nAnswer:",
            "Question: {question}\nSupporting information: {context}\nGive a short factual answer:",
            "You are answering a benchmark. Use only these facts: {context}\nQ: {question}\nA:",
        ]
        for template in prompts:
            proposals.append(dict(original, template=template, max_new_tokens=48))
    seen = set()
    for proposal in proposals:
        try:
            validate_artifact(kind, proposal)
        except ValueError:
            continue
        sha = digest(proposal)
        if sha not in seen:
            seen.add(sha)
            yield proposal
        if len(seen) >= max_proposals:
            break


def development_score(kind, docs, examples, candidate, model_dir=""):
    successes, work_units = [], []
    for case in examples:
        correct, work, _ = evaluate_case(kind, case, docs, candidate, model_dir)
        successes.append(correct)
        work_units.append(work)
    accuracy = sum(successes) / len(successes)
    units = sum(work_units) / len(work_units)
    return (accuracy, -units)


def search(kind, docs, development, max_proposals=18, model_dir=""):
    if kind not in KINDS:
        raise ValueError("Unsupported research type")
    if not 1 <= max_proposals <= 40:
        raise ValueError("Proposal budget must be between 1 and 40")
    evaluated = []
    for artifact in candidate_options(kind, docs, development, max_proposals):
        accuracy, negative_work = development_score(kind, docs, development, artifact, model_dir)
        evaluated.append((accuracy, negative_work, digest(artifact), artifact))
    if not evaluated:
        raise ValueError("No admissible adapter candidates")
    best = sorted(evaluated, key=lambda row: (-row[0], -row[1], row[2]))[0]
    return {
        "artifact": best[3], "public_development_accuracy": best[0],
        "mean_work_units": -best[1], "proposals_tested": len(evaluated),
        "privacy": "Only the public development split was inspected; no held-out feedback was used",
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description="GradientMine bounded public-development research worker")
    parser.add_argument("--api", required=True, help="Exact local or HTTPS operator origin")
    parser.add_argument("--benchmark", required=True, help="Benchmark UUID")
    parser.add_argument("--identity", required=True, help="Existing private worker identity file")
    parser.add_argument("--max-proposals", type=int, default=18)
    parser.add_argument("--model-dir", default="", help="Already cached trusted model, required for llm_prompt")
    parser.add_argument("--submit", action="store_true", help="Explicitly submit the selected signed adapter")
    args = parser.parse_args(argv)
    identity = Identity.load(__import__("pathlib").Path(args.identity))
    client, origin = client_for(args.api)
    with client:
        login(client, identity, origin)
        item = request(client, "GET", "/api/lab/benchmarks/" + args.benchmark)
        if item["state"] != "OPEN":
            raise ValueError("Competition is not accepting candidates")
        if digest(item["policy"]) != item["policy_sha256"]:
            raise ValueError("Frozen policy digest mismatch")
        if digest(item["documents"]) != item["policy"]["documents_sha256"]:
            raise ValueError("Document commitment mismatch")
        if digest(item["development"]) != item["policy"]["development_sha256"]:
            raise ValueError("Public development commitment mismatch")
        result = search(item["kind"], item["documents"], item["development"],
                        args.max_proposals, args.model_dir)
        artifact = result["artifact"]
        claim = {
            "format": "gradientmine.lab-submission.v1",
            "benchmark_id": item["id"], "policy_sha256": item["policy_sha256"],
            "artifact_sha256": digest(artifact), "submitted_at": int(time.time()),
        }
        if args.submit:
            result["submission"] = request(
                client, "POST", f"/api/lab/benchmarks/{item['id']}/submissions",
                json={"artifact": artifact, "manifest": identity.sign(claim)},
            )
        else:
            result["submission"] = None
        result["worker_address"] = identity.address
        print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
