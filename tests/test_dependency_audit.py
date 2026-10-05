from types import SimpleNamespace

import pytest

from scripts.audit_dependencies import inventory


def test_audit_includes_transitives_pip_and_cpu_torch_release():
    distributions = [SimpleNamespace(metadata={"Name": name}, version=version) for name, version in (
        ("torch", "2.14.1+cpu"), ("pip", "26.2.1"), ("gradientmine", "0.2.0"), ("httpcore", "1.0.9")
    )]
    assert inventory(distributions) == "httpcore==1.0.9\npip==26.2.1\ntorch==2.14.1\n"


def test_audit_refuses_unknown_local_build_instead_of_silently_skipping_it():
    with pytest.raises(ValueError):
        inventory([SimpleNamespace(metadata={"Name": "torch"}, version="2.10.0+unknown")])
