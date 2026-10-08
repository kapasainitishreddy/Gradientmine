"""Bounded, evaluator-owned benchmarks for research competitions.

These v1 adapters are DECLARATIVE JSON, never Python source or pickle. Uploaded
candidates do not contain reference answers, evaluations, or executable code.
The retrieval engine is lexical; the safety example is a keyword-filter proof,
not an LLM safety certification. Local LLM inference is optional and OFFLINE.
"""

from __future__ import annotations

import os
import re
import statistics
import time
from functools import lru_cache

import numpy as np

from .crypto import canonical, digest
from .scoring import assess

KINDS = ("retrieval", "grounded_qa", "safety_refusal", "efficiency", "llm_prompt")
TOKEN = re.compile(r"[a-z0-9]+")
ALLOWED_TEMPLATE = {"{question}", "{context}"}
STOP = {"the", "a", "an", "is", "are", "of", "in", "to", "and", "for", "with", "on", "what", "which", "how"}

BASE = {
    "retrieval": {"format": "gradientmine.retrieval.v1", "top_k": 1, "title_boost": 1, "expansion": {}},
    "grounded_qa": {
        "format": "gradientmine.grounded_qa.v1", "top_k": 1,
        "title_boost": 1, "min_overlap": 2, "expansion": {},
    },
    "safety_refusal": {"format": "gradientmine.safety_policy.v1", "block_terms": ["restricted"], "allow_terms": []},
    "efficiency": {"format": "gradientmine.efficiency.v1", "top_k": 4, "title_boost": 1, "max_docs": 100},
    "llm_prompt": {
        "format": "gradientmine.prompt_template.v1",
        "template": "Use only this context: {context}\nQuestion: {question}\nAnswer:",
        "max_new_tokens": 64,
    },
}
FORMAT = {kind: BASE[kind]["format"] for kind in KINDS}


def tokens(value: str) -> list[str]:
    return [w for w in TOKEN.findall(value.lower()) if w not in STOP]


def _text(value, max_len=4000):
    if not isinstance(value, str) or not value.strip() or len(value) > max_len or any(
        ord(c) < 32 and c not in "\n\t" for c in value
    ):
        raise ValueError("Text must be nonempty, bounded and free from controls")
    return value.strip()


def _int(value, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"Expected integer between {low} and {high}")
    return value


def _expansion(mapping):
    if not isinstance(mapping, dict) or len(mapping) > 24:
        raise ValueError("Expansion map must contain no more than 24 pairs")
    for key, value in mapping.items():
        if not re.fullmatch(r"[a-z0-9]{2,24}", key) or not re.fullmatch(r"[a-z0-9]{2,24}", value):
            raise ValueError("Expansion tokens must be plain lowercase alphanumeric words")
    return mapping


def validate_artifact(kind: str, value: dict) -> dict:
    if kind not in KINDS or not isinstance(value, dict):
        raise ValueError("Unknown benchmark or invalid adapter")
    expected = {
        "retrieval": {"format", "top_k", "title_boost", "expansion"},
        "grounded_qa": {"format", "top_k", "title_boost", "min_overlap", "expansion"},
        "safety_refusal": {"format", "block_terms", "allow_terms"},
        "efficiency": {"format", "top_k", "title_boost", "max_docs"},
        "llm_prompt": {"format", "template", "max_new_tokens"},
    }[kind]
    if set(value) != expected or value["format"] != FORMAT[kind] or len(canonical(value)) > 8192:
        raise ValueError("Unexpected fields, format or size in declarative adapter")
    if kind in {"retrieval", "grounded_qa", "efficiency"}:
        _int(value["top_k"], 1, 10)
        _int(value["title_boost"], 1, 6)
    if kind in {"retrieval", "grounded_qa"}:
        _expansion(value["expansion"])
    if kind == "grounded_qa":
        _int(value["min_overlap"], 0, 8)
    if kind == "efficiency":
        _int(value["max_docs"], 1, 100)
    if kind == "safety_refusal":
        for field in ("block_terms", "allow_terms"):
            words = value[field]
            if not isinstance(words, list) or len(words) > 32 or len(set(words)) != len(words):
                raise ValueError("Policy term lists must be unique and bounded")
            for word in words:
                if not isinstance(word, str) or not re.fullmatch(r"[a-z0-9 ]{2,48}", word):
                    raise ValueError("Unsafe policy keyword")
    if kind == "llm_prompt":
        template = _text(value["template"], 1300)
        if "{question}" not in template or len(template) < 16 or "{" in template.replace("{question}", "").replace("{context}", ""):
            raise ValueError("Only the {question} and {context} placeholders are allowed")
        _int(value["max_new_tokens"], 8, 128)
    return value


def validate_dataset(kind: str, docs: list, development: list, holdout: list) -> None:
    if kind not in KINDS:
        raise ValueError("Unsupported competition type")
    if not isinstance(docs, list) or len(docs) > 120:
        raise ValueError("Too many documents")
    if not isinstance(development, list) or not 2 <= len(development) <= 80:
        raise ValueError("Development split must have 2 to 80 examples")
    if not isinstance(holdout, list) or not 4 <= len(holdout) <= 200:
        raise ValueError("Private evaluation split must have 4 to 200 examples")
    if len(canonical({"docs": docs, "development": development, "holdout": holdout})) > 155000:
        raise ValueError("Benchmark package exceeds size limit")
    ids = []
    for document in docs:
        if not isinstance(document, dict) or set(document) != {"id", "title", "text"}:
            raise ValueError("Documents need id, title and text only")
        ident = document["id"]
        if not isinstance(ident, str) or not re.fullmatch(r"[a-zA-Z0-9_-]{1,48}", ident):
            raise ValueError("Invalid document id")
        ids.append(ident)
        _text(document["title"], 160)
        _text(document["text"], 1800)
    if len(set(ids)) != len(ids):
        raise ValueError("Document ids must be distinct")
    if kind in {"retrieval", "grounded_qa", "efficiency"} and len(ids) < 2:
        raise ValueError("Retrieval-based tasks require at least two documents")
    for split in (development, holdout):
        for case in split:
            if not isinstance(case, dict):
                raise ValueError("Cases must be objects")
            expected = (
                {"prompt", "should_refuse"} if kind == "safety_refusal"
                else {"question", "answer"} if kind == "llm_prompt"
                else {"query", "relevant_ids"} if kind in {"retrieval", "efficiency"}
                else {"question", "answer", "relevant_ids"}
            )
            if set(case) != expected:
                raise ValueError("Unexpected benchmark case fields")
            _text(case.get("prompt") or case.get("query") or case.get("question"), 600)
            if kind == "safety_refusal":
                if type(case["should_refuse"]) is not bool:
                    raise ValueError("Safety labels must be booleans")
            elif kind == "llm_prompt":
                if not isinstance(case["answer"], str) or len(case["answer"]) > 500:
                    raise ValueError("Invalid answer")
            else:
                related = case["relevant_ids"]
                if not isinstance(related, list) or len(related) > 10 or any(i not in ids for i in related):
                    raise ValueError("Invalid relevant document ids")
                if kind == "grounded_qa" and (not isinstance(case["answer"], str) or len(case["answer"]) > 500):
                    raise ValueError("Invalid expected answer")
    if digest(development) == digest(holdout):
        raise ValueError("Evaluation must not duplicate the development split")


def _expanded(query, mapping):
    words = tokens(query)
    return words + [mapping[word] for word in words if word in mapping]


def retrieve(query, docs, adapter):
    words = _expanded(query, adapter.get("expansion", {}))
    unique = set(words)
    width = min(adapter.get("max_docs", len(docs)), len(docs))
    ranked = []
    work_units = 0
    for doc in docs[:width]:
        title = set(tokens(doc["title"]))
        text = set(tokens(doc["text"]))
        work_units += len(words) * (len(title) + len(text))
        score = adapter["title_boost"] * len(unique & title) + len(unique & text)
        if score:
            ranked.append((score, doc["id"]))
    ranked.sort(key=lambda row: (-row[0], row[1]))
    ids = [name for _, name in ranked[: adapter["top_k"]]]
    return ids, work_units


def extract_answer(question, docs, ids, min_overlap):
    words = set(tokens(question))
    best = (0, "", "")
    by_id = {doc["id"]: doc for doc in docs}
    for ident in ids:
        doc = by_id.get(ident)
        if doc is None:
            continue
        for sentence in re.split(r"(?<=[.!?])\s+", doc["text"]):
            overlap = len(words & set(tokens(sentence)))
            if overlap > best[0]:
                best = (overlap, sentence.strip(), ident)
    if best[0] < min_overlap or not best[1]:
        return "", None
    return best[1], best[2]


def _word_f1(expected: str, actual: str) -> float:
    a, b = tokens(expected), tokens(actual)
    if not a:
        return 1.0 if not b else 0.0
    if not b:
        return 0.0
    common = sum(min(a.count(token), b.count(token)) for token in set(a))
    return 2 * common / (len(a) + len(b)) if a or b else 0.0


@lru_cache(maxsize=2)
def _offline_model(model_path):
    try:
        from transformers import AutoConfig, AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError("Install gradientmine[llm] for offline LLM benchmarks") from exc
    if not os.path.isdir(model_path) or not os.path.isfile(os.path.join(model_path, "config.json")):
        raise RuntimeError("Model must be present in the trusted local model directory")
    config = AutoConfig.from_pretrained(model_path, local_files_only=True, trust_remote_code=False)
    seq2seq = bool(getattr(config, "is_encoder_decoder", False))
    tok = AutoTokenizer.from_pretrained(model_path, local_files_only=True, trust_remote_code=False)
    cls = AutoModelForSeq2SeqLM if seq2seq else AutoModelForCausalLM
    model = cls.from_pretrained(model_path, local_files_only=True, trust_remote_code=False)
    model.eval()
    return tok, model, seq2seq


def _local_llm_answer(question, docs, adapter, model_dir):
    if not model_dir:
        raise RuntimeError("Offline LLM benchmark requires a configured trusted local model")
    tokenizer, model, seq2seq = _offline_model(model_dir)
    context = "\n".join(doc["text"][:400] for doc in docs[:5])
    text = adapter["template"].replace("{context}", context).replace("{question}", question)
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=768)
    import torch

    with torch.inference_mode():
        output = model.generate(**inputs, max_new_tokens=adapter["max_new_tokens"], do_sample=False,
                                pad_token_id=tokenizer.eos_token_id)
    decoded = output[0] if seq2seq else output[0][inputs["input_ids"].shape[1]:]
    return tokenizer.decode(decoded, skip_special_tokens=True).strip()


def evaluate_case(kind, case, docs, artifact, model_dir=""):
    """Return (objective success boolean, deterministic cost-work proxy, duration milliseconds).

    No worker supplied test outputs are trusted. Evaluator runs its own pipeline.
    """
    start = time.perf_counter()
    units = 1
    if kind in {"retrieval", "efficiency"}:
        ids, units = retrieve(case["query"], docs, artifact)
        correct = bool(set(ids) & set(case["relevant_ids"]))
    elif kind == "grounded_qa":
        ids, units = retrieve(case["question"], docs, artifact)
        text, source_id = extract_answer(case["question"], docs, ids, artifact["min_overlap"])
        expected = case["answer"].strip()
        correct = (
            not text if not expected else
            source_id in case["relevant_ids"] and _word_f1(expected, text) >= 0.5
        )
    elif kind == "safety_refusal":
        prompt = " ".join(tokens(case["prompt"]))
        allowed = any(term in prompt for term in artifact["allow_terms"])
        refused = not allowed and any(term in prompt for term in artifact["block_terms"])
        correct = refused is case["should_refuse"]
        units = sum(len(x) for x in artifact["block_terms"] + artifact["allow_terms"])
    elif kind == "llm_prompt":
        text = _local_llm_answer(case["question"], docs, artifact, model_dir)
        correct = _word_f1(case["answer"], text) >= 0.5
        units = len(tokens(text)) + len(tokens(case["question"]))
    else:
        raise ValueError("Unknown benchmark")
    return bool(correct), int(units), (time.perf_counter() - start) * 1000


def compare(kind, docs, examples, candidate, minimum_delta, max_candidates=8, model_dir=""):
    """Paired accuracy/significance gate, or cost proxy improvement with quality guardrail."""
    validate_artifact(kind, candidate)
    base = BASE[kind]
    baseline, challenger = [], []
    base_work, candidate_work = [], []
    times = []
    for case in examples:
        b, units_b, _ = evaluate_case(kind, case, docs, base, model_dir)
        a, units_a, elapsed = evaluate_case(kind, case, docs, candidate, model_dir)
        baseline.append(b)
        challenger.append(a)
        base_work.append(units_b)
        candidate_work.append(units_a)
        times.append(elapsed)
    if kind == "efficiency":
        prior = statistics.mean(base_work)
        current = statistics.mean(candidate_work)
        savings = (prior - current) / max(prior, 1.0)
        base_quality = statistics.mean(baseline)
        cand_quality = statistics.mean(challenger)
        eligible = bool(
            savings >= minimum_delta and savings > 0
            and cand_quality >= max(base_quality - 0.02, 0.5)
        )
        return {
            "metric": "deterministic-retrieval-work-units",
            "baseline_accuracy": base_quality, "candidate_accuracy": cand_quality,
            "baseline_work_units": prior, "candidate_work_units": current,
            "delta": float(savings), "minimum_delta": minimum_delta,
            "bootstrap_lower_bound": None, "eligible": eligible, "n": len(examples),
            "median_candidate_latency_ms": statistics.median(times),
            "statistical_limit": "Work units are an execution-cost proxy, not GPU dollars or a reliable latency benchmark.",
            "reason": "Quality floor and cost improvement met" if eligible else "Quality floor or cost improvement not met",
        }
    scores = assess(np.ones(len(examples), dtype=int), np.asarray(baseline, dtype=int),
                    np.asarray(challenger, dtype=int), minimum_delta, max_candidates)
    scores["metric"] = "paired-objective-success-rate"
    scores["median_candidate_latency_ms"] = float(statistics.median(times))
    scores["statistical_limit"] += " These are task-specific test outcomes, not general model safety certification."
    return scores
