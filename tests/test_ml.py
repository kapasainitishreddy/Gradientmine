import numpy as np
import pytest
from gradientmine.ml import make_task, train_adapter, merge_adapter, predict, validate_adapter, dataset_json
from gradientmine.crypto import digest
from gradientmine.scoring import assess, select_winner


@pytest.fixture(scope="module")
def task():
    return make_task()


def test_task_has_disjoint_splits_and_reproducible_hashes(task):
    groups = [set(task[k]["ids"]) for k in ("train", "validation", "test")]
    assert sum(len(x) for x in groups) == 1797
    assert not groups[0] & groups[1] and not groups[1] & groups[2] and not groups[0] & groups[2]
    assert digest(task["model"]) == task["manifest"]["parent_sha256"]
    assert digest(dataset_json(task["test"])) == task["manifest"]["evaluation_sha256"]


def test_actual_training_improves_and_negative_control_fails(task):
    adapter, losses = train_adapter(task["model"], task["train"], seed=7)
    assert len(losses) == 60 and losses[-1] < losses[0]
    before = predict(task["model"], task["test"]["x"])
    after = predict(merge_adapter(task["model"], adapter), task["test"]["x"])
    assert assess(task["test"]["y"], before, after)["eligible"]
    bad, _ = train_adapter(task["model"], task["train"], shuffle_labels=True)
    assert not assess(
        task["test"]["y"], before, predict(merge_adapter(task["model"], bad), task["test"]["x"])
    )["eligible"]


@pytest.mark.parametrize("bad", ["pickle", "wrong-parent", "rank", "nan", "oversized-tensor", "code"])
def test_numeric_artifact_validation(task, bad):
    artifact, _ = train_adapter(task["model"], task["train"], epochs=1)
    if bad == "pickle":
        artifact["format"] = "pickle"
    elif bad == "wrong-parent":
        artifact["parent_sha256"] = "0" * 64
    elif bad == "rank":
        artifact["rank"] = True
    elif bad == "nan":
        artifact["a"][0][0] = float("nan")
    elif bad == "oversized-tensor":
        artifact["a"].append(artifact["a"][0])
    elif bad == "code":
        artifact["python"] = "print(1)"
    with pytest.raises(ValueError):
        validate_adapter(artifact, digest(task["model"]))


def test_no_improvement_not_eligible_and_repeatable():
    y = np.array([0, 1] * 50)
    assert not assess(y, y, y)["eligible"]
    before = y.copy()
    before[:30] = 1 - before[:30]
    a = assess(y, before, y)
    assert a == assess(y, before, y)
    assert a["delta"] == 0.3 and a["per_candidate_alpha"] == 0.00625


def test_tie_breaker_is_commitment_not_arrival():
    rows = [{"eligible": True, "candidate_accuracy": 0.9, "artifact_sha256": x} for x in ["bb", "aa"]]
    assert select_winner(rows)["artifact_sha256"] == "aa"
    assert select_winner([]) is None
