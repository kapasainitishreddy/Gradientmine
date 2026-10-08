"""Optional offline PEFT LoRA training for locally cached Hugging Face models.

Runs only trusted LOCAL model files and text examples. A saved safetensors adapter
is NOT automatically admitted to a bounty: remote binary uploads and a
production-grade holdout evaluator require a separate audited protocol.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

from .crypto import canonical, digest
from .store import atomic_write


def _load_optional():
    try:
        import torch
        from peft import LoraConfig, TaskType, get_peft_model
        from transformers import AutoConfig, AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer
    except ImportError as exc:
        raise RuntimeError(
            "Offline LoRA training requires: pip install -e '.[llm]' plus a pre-cached trusted model"
        ) from exc
    return torch, LoraConfig, TaskType, get_peft_model, AutoConfig, AutoModelForCausalLM, AutoModelForSeq2SeqLM, AutoTokenizer


def _training_rows(rows):
    if not isinstance(rows, list) or not 2 <= len(rows) <= 64:
        raise ValueError("Require 2-64 public supervised examples")
    validated = []
    for example in rows:
        if not isinstance(example, dict) or set(example) != {"prompt", "answer"}:
            raise ValueError("Each training example must contain prompt and answer")
        for value in example.values():
            if not isinstance(value, str) or not value.strip() or len(value) > 900:
                raise ValueError("Training text must be nonempty and bounded to 900 characters")
        validated.append({"prompt": example["prompt"].strip(), "answer": example["answer"].strip()})
    if len(canonical(validated)) > 58000:
        raise ValueError("Training package too large")
    return validated


def _target_modules(model):
    """Require known attention projection names; never train arbitrary uploaded code."""
    names = {name.split(".")[-1] for name, _ in model.named_modules()}
    for set_of_names in (("q_proj", "v_proj"), ("q", "v"), ("c_attn",)):
        if all(name in names for name in set_of_names):
            return list(set_of_names)
    raise ValueError("Model architecture lacks supported LoRA attention modules (q_proj/v_proj, q/v, c_attn)")


def train_offline(model_dir, examples, output, *, epochs=1, rank=4, learning_rate=0.0003, seed=47):
    """Train a REAL local LoRA update using only bounded trusted examples.

    Supported families: locally cached causal language models and encoder-decoder
    text-generation models that expose standard attention projection modules.
    """
    if type(epochs) is not int or not 1 <= epochs <= 3:
        raise ValueError("Epochs must be between 1 and 3")
    if type(rank) is not int or not 1 <= rank <= 8:
        raise ValueError("LoRA rank must be between 1 and 8")
    if type(learning_rate) is not float or not 0.000001 <= learning_rate <= 0.005:
        raise ValueError("Invalid learning rate")
    rows = _training_rows(examples)
    root = Path(model_dir).resolve(strict=True)
    if not root.is_dir() or not (root / "config.json").is_file():
        raise ValueError("Use an already downloaded trusted LOCAL model directory")
    destination = Path(output).resolve()
    if destination.exists() or destination == root or root in destination.parents:
        raise ValueError("Choose a fresh private adapter output directory separate from the model")
    torch, LoraConfig, TaskType, get_peft_model, AutoConfig, Causal, Seq2Seq, Tokenizer = _load_optional()
    torch.set_num_threads(min(2, max(1, os.cpu_count() or 1)))
    torch.manual_seed(seed)
    config = AutoConfig.from_pretrained(str(root), local_files_only=True, trust_remote_code=False)
    seq2seq = bool(getattr(config, "is_encoder_decoder", False))
    family = "seq2seq" if seq2seq else "causal"
    tok = Tokenizer.from_pretrained(str(root), local_files_only=True, trust_remote_code=False)
    model = (Seq2Seq if seq2seq else Causal).from_pretrained(
        str(root), local_files_only=True, trust_remote_code=False
    )
    if not tok.pad_token:
        if not tok.eos_token:
            raise ValueError("Tokenizer requires an EOS or pad token for bounded training")
        tok.pad_token = tok.eos_token
    modules = _target_modules(model)
    lora = LoraConfig(
        r=rank, lora_alpha=rank * 2, lora_dropout=0.0,
        target_modules=modules,
        bias="none",
        task_type=TaskType.SEQ_2_SEQ_LM if seq2seq else TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, lora)
    model.train()
    optimizer = torch.optim.AdamW(
        (param for param in model.parameters() if param.requires_grad),
        lr=learning_rate,
    )
    first_loss, last_loss = None, None
    steps = 0
    for _ in range(epochs):
        for row in rows:
            prompt = row["prompt"]
            answer = row["answer"]
            if seq2seq:
                inputs = tok(prompt, return_tensors="pt", truncation=True, max_length=256)
                targets = tok(answer, return_tensors="pt", truncation=True, max_length=128)
                labels = targets["input_ids"]
                labels = labels.masked_fill(labels == tok.pad_token_id, -100)
            else:
                p = tok.encode(prompt + "\nAnswer: ", add_special_tokens=True, truncation=True, max_length=256)
                a = tok.encode(answer, add_special_tokens=False, truncation=True, max_length=128)
                suffix = [tok.eos_token_id] if tok.eos_token_id is not None else []
                joined = (p + a + suffix)[:384]
                if len(joined) <= len(p):
                    raise ValueError("Training example truncated away the target answer")
                inputs = {"input_ids": torch.tensor([joined]), "attention_mask": torch.ones(1, len(joined), dtype=torch.long)}
                labels = torch.tensor([[-100] * len(p) + joined[len(p):]], dtype=torch.long)
            optimizer.zero_grad(set_to_none=True)
            loss = model(**inputs, labels=labels).loss
            if not torch.isfinite(loss):
                raise ValueError("LoRA training diverged; no artifact saved")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                [p for p in model.parameters() if p.requires_grad], max_norm=1.0,
            )
            optimizer.step()
            value = float(loss.detach())
            first_loss = value if first_loss is None else first_loss
            last_loss = value
            steps += 1
            if steps > 192:
                raise ValueError("Exceeded training budget")
    destination.mkdir(parents=True, exist_ok=False, mode=0o700)
    try:
        model.save_pretrained(str(destination), safe_serialization=True)
        adapter = destination / "adapter_model.safetensors"
        if not adapter.exists():
            raise RuntimeError("Expected safe tensor adapter was not created")
        raw = adapter.read_bytes()
        if not raw or len(raw) > 25_000_000:
            raise ValueError("Refusing empty or unexpectedly large LoRA adapter")
        manifest = {
            "format": "gradientmine.local-lora.v1",
            "family": family,
            "base_directory_name": root.name,
            "base_config_sha256": hashlib.sha256((root / "config.json").read_bytes()).hexdigest(),
            "adapter_sha256": hashlib.sha256(raw).hexdigest(),
            "training_data_sha256": digest(rows),
            "examples": len(rows), "steps": steps,
            "rank": rank, "learning_rate": learning_rate, "epochs": epochs,
            "first_loss": first_loss, "last_loss": last_loss,
            "target_modules": modules, "device": "cpu",
            "public_evaluation": None,
            "notice": "Locally trained safe-tensor adapter only. NOT an accepted remote bounty submission or a verified improvement.",
        }
        atomic_write(destination / "gradientmine-manifest.json", canonical(manifest))
        return manifest
    except BaseException:
        # Never leave a partial adapter directory that could be mistaken for a completed result.
        import shutil
        shutil.rmtree(destination, ignore_errors=True)
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline LoRA training; no uploads, billing or private test access")
    parser.add_argument("--model-dir", required=True)
    parser.add_argument("--train-json", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--epochs", type=int, default=1)
    parser.add_argument("--rank", type=int, default=4)
    parser.add_argument("--learning-rate", type=float, default=.0003)
    args = parser.parse_args(argv)
    train_data = json.loads(Path(args.train_json).read_text(encoding="utf-8"))
    result = train_offline(args.model_dir, train_data, args.out,
                           epochs=args.epochs, rank=args.rank, learning_rate=float(args.learning_rate))
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
