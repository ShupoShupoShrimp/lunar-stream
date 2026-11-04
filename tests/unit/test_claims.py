import argparse
import json

import pytest
from tools.claims import load_evidence, validate_claim


def test_load_valid_C01_evidences(tmp_path):

    evidence = {
        "claim_id": "C01",
        "status": "reported",
        "sample_size": 500,
        "protocol": {},
        "metrics": {
            "fraction_above_800ms_upper_bound": 0.04,
        },
    }

    evidence_path = tmp_path / "C01.json"

    evidence_path.write_text(json.dumps(evidence))

    claim = {
        "tier": {
            "reported": {
                "target": "bench-ttfa-cp",
                "min_n": 500,
            },
        },
        "evidence": {
            "output": str(evidence_path),
        },
    }

    loaded = load_evidence(evidence["claim_id"], claim)

    assert loaded["claim_id"] == "C01"
    assert loaded["sample_size"] == 500


def test_absent_metrics_C01(tmp_path):

    evidence = {
        "claim_id": "C23",
    }

    evidence_path = tmp_path / "C23"
    evidence_path.write_text(json.dumps(evidence))

    claim = {
        "tier": {
            "certify": {
                "target": "certify",
                "min_n": 2000,
            },
        },
        "evidence": {
            "output": str(evidence_path),
        },
    }

    with pytest.raises(ValueError, match="Evidence is missing 'metrics'"):
        load_evidence(evidence["claim_id"], claim)


def test_reject_wrong_claim_id(tmp_path):
    evidence = {
        "claim_id": "C23",
        "metrics": {},
    }

    evidence_path = tmp_path / "C01.json"
    evidence_path.write_text(json.dumps(evidence))

    claim = {
        "evidence": {
            "output": str(evidence_path),
        },
    }

    with pytest.raises(ValueError, match="belongs to"):
        load_evidence("C01", claim)


def test_unsatisfied_target(tmp_path, monkeypatch):

    monkeypatch.setattr("subprocess.run", lambda *args, **kwargs: None)

    evidence = {
        "claim_id": "C01",
        "status": "certified",
        "sample_size": 1999,
        "protocol": {},
        "metrics": {"fraction_above_800ms_upper_bound": 0.04},
    }

    evidence_path = tmp_path / "C01.json"
    evidence_path.write_text(json.dumps(evidence))

    claim_path = tmp_path / "claims.toml"
    claim_path.write_text(f"""
    [C01]
    check = []
    [C01.tier.certified]
    target = "certify"
    min_n = 2000
    [C01.evidence]
    output = "{evidence_path}"
    """)

    args = argparse.Namespace(
        file=str(claim_path),
        claim="C01",
        tier="certified",
    )

    with pytest.raises(ValueError, match="Insufficient samples: 1999 / 2000"):
        validate_claim(args)
