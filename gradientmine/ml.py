"""Real CPU-friendly neural-network training. Only fixed-shape numeric artifacts are accepted."""

from __future__ import annotations
import copy
import numpy as np
import torch
from sklearn.datasets import load_digits
from sklearn.model_selection import train_test_split
from .crypto import canonical, digest

torch.set_num_threads(1)
FORMAT = "gradientmine.adapter.v1"


def _array(value, shape):
    try:
        array = np.asarray(value, dtype=np.float32)
    except (ValueError, TypeError) as exc:
        raise ValueError("Artifact must contain numeric tensors") from exc
    if array.shape != shape or not np.isfinite(array).all() or np.abs(array).max(initial=0) > 100:
        raise ValueError(f"Invalid tensor; expected finite bounded shape {shape}")
    return array


def validate_model(model: dict) -> None:
    if not isinstance(model, dict) or set(model) != {"format", "w1", "b1", "w2", "b2"}:
        raise ValueError("Unexpected model fields")
    if model["format"] != "gradientmine.model.v1":
        raise ValueError("Unsupported model format")
    for key, shape in [("w1", (48, 64)), ("b1", (48,)), ("w2", (10, 48)), ("b2", (10,))]:
        _array(model[key], shape)


def validate_adapter(adapter: dict, parent: str) -> None:
    if not isinstance(adapter, dict) or set(adapter) != {"format", "parent_sha256", "rank", "a", "b"}:
        raise ValueError("Unexpected adapter fields; executable model formats are not allowed")
    if adapter["format"] != FORMAT or adapter["parent_sha256"] != parent:
        raise ValueError("Wrong format or parent-model commitment")
    rank = adapter["rank"]
    if type(rank) is not int or not 1 <= rank <= 16:
        raise ValueError("Rank must be an integer between 1 and 16")
    _array(adapter["a"], (rank, 48))
    _array(adapter["b"], (10, rank))
    canonical(adapter)  # rejects NaN/Infinity before persistence


def predict(model: dict, x: np.ndarray) -> np.ndarray:
    validate_model(model)
    x = np.asarray(x, dtype=np.float32)
    if x.ndim != 2 or x.shape[1] != 64 or not np.isfinite(x).all():
        raise ValueError("Expected finite 64-feature examples")
    h = np.maximum(x @ np.asarray(model["w1"], dtype=np.float32).T + model["b1"], 0)
    return (h @ np.asarray(model["w2"], dtype=np.float32).T + model["b2"]).argmax(axis=1)


def merge_adapter(parent: dict, adapter: dict) -> dict:
    validate_model(parent)
    validate_adapter(adapter, digest(parent))
    model = copy.deepcopy(parent)
    model["w2"] = (
        np.asarray(parent["w2"], dtype=np.float32)
        + np.asarray(adapter["b"], dtype=np.float32) @ np.asarray(adapter["a"], dtype=np.float32)
    ).tolist()
    validate_model(model)
    return model


def make_task(seed: int = 42) -> dict:
    """Build one reproducible educational benchmark; never market its public data as secret-proof."""
    digits = load_digits()
    x = (digits.data / 16).astype(np.float32)
    y = digits.target.astype(np.int64)
    ids = np.arange(len(y))
    train_ids, remaining = train_test_split(ids, test_size=0.4, stratify=y, random_state=seed)
    validation_ids, test_ids = train_test_split(
        remaining, test_size=0.5, stratify=y[remaining], random_state=seed + 1
    )
    groups = {
        name: {"x": x[index], "y": y[index], "ids": index.tolist()}
        for name, index in [("train", train_ids), ("validation", validation_ids), ("test", test_ids)]
    }
    with torch.random.fork_rng():
        torch.manual_seed(seed)
        model = torch.nn.Sequential(torch.nn.Linear(64, 48), torch.nn.ReLU(), torch.nn.Linear(48, 10))
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
        # Deliberately budget-limited starting model. This choice is disclosed, not an SOTA baseline.
        bx = torch.from_numpy(groups["train"]["x"][:240])
        by = torch.from_numpy(groups["train"]["y"][:240])
        for _ in range(18):
            optimizer.zero_grad()
            loss = torch.nn.functional.cross_entropy(model(bx), by)
            loss.backward()
            optimizer.step()
        state = model.state_dict()
        artifact = {
            "format": "gradientmine.model.v1",
            "w1": state["0.weight"].tolist(),
            "b1": state["0.bias"].tolist(),
            "w2": state["2.weight"].tolist(),
            "b2": state["2.bias"].tolist(),
        }
    manifest = {
        "format": "gradientmine.task.v1",
        "task": "digits-lora-v1",
        "dataset": "UCI Optical Recognition of Handwritten Digits, scikit-learn 1797-image subset",
        "dataset_license": "CC-BY-4.0",
        "dataset_doi": "10.24432/C50P49",
        "model": "64-48-10 ReLU classifier, rank-limited head adaptation",
        "baseline_training": {"examples": 240, "epochs": 18, "optimizer": "Adam", "learning_rate": 0.01},
        "parent_sha256": digest(artifact),
        "train_sha256": digest(dataset_json(groups["train"])),
        "validation_sha256": digest(dataset_json(groups["validation"])),
        "evaluation_sha256": digest(dataset_json(groups["test"])),
        "metric": "accuracy",
        "direction": "maximize",
        "max_submissions": 8,
        "statistical_rule": "paired-multinomial-bootstrap-v1",
        "bootstrap_resamples": 20000,
        "familywise_alpha": 0.05,
        "bootstrap_seed": 7301,
        "warning": "Public-source benchmark: withheld from worker API, NOT resistant to dataset reconstruction.",
    }
    return {**groups, "model": artifact, "manifest": manifest}


def dataset_json(group: dict) -> dict:
    return {"x": np.asarray(group["x"]).tolist(), "y": np.asarray(group["y"]).tolist(), "ids": group["ids"]}


def train_adapter(
    parent: dict,
    train: dict,
    epochs: int = 60,
    lr: float = 0.03,
    seed: int = 7,
    rank: int = 8,
    shuffle_labels: bool = False,
) -> tuple[dict, list[float]]:
    validate_model(parent)
    if not 1 <= epochs <= 300 or not 0 < lr <= 0.1 or not 1 <= rank <= 16:
        raise ValueError("Unsupported training budget, learning rate or rank")
    x = torch.tensor(np.asarray(train["x"], dtype=np.float32))
    y = torch.tensor(np.asarray(train["y"], dtype=np.int64))
    if x.shape[1:] != (64,) or y.shape != (len(x),) or not 1 <= len(x) <= 10000:
        raise ValueError("Invalid training dataset dimensions")
    if not torch.isfinite(x).all() or not ((0 <= y) & (y < 10)).all():
        raise ValueError("Invalid training data")
    with torch.random.fork_rng():
        torch.manual_seed(seed)
        if shuffle_labels:
            y = y[torch.randperm(len(y))]
        features = torch.relu(x @ torch.tensor(parent["w1"]).T + torch.tensor(parent["b1"]))
        base_logits = features @ torch.tensor(parent["w2"]).T + torch.tensor(parent["b2"])
        a = torch.nn.Parameter(torch.randn(rank, 48) * 0.02)
        b = torch.nn.Parameter(torch.zeros(10, rank))
        optimizer = torch.optim.Adam([a, b], lr=lr)
        losses = []
        for _ in range(epochs):
            optimizer.zero_grad()
            logits = base_logits + features @ a.T @ b.T
            loss = torch.nn.functional.cross_entropy(logits, y)
            if not torch.isfinite(loss):
                raise ValueError("Training diverged; no artifact will be submitted")
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach()))
        artifact = {
            "format": FORMAT,
            "parent_sha256": digest(parent),
            "rank": rank,
            "a": a.detach().tolist(),
            "b": b.detach().tolist(),
        }
    validate_adapter(artifact, digest(parent))
    return artifact, losses
