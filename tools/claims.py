import argparse
import json
import operator
import subprocess
import tomllib
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent

ops = {
    "eq": operator.eq,
    "ge": operator.ge,
    "le": operator.le,
}

status_rank = {
    "reported": 1,
    "certified": 2,
}


def load_evidence(claim_id: str, claim: dict[str, Any]) -> dict[str, Any]:
    evidence_config = claim.get("evidence", {})

    output_path = Path(evidence_config.get("output", f"bench/out/{claim_id}.json"))

    if not output_path.is_absolute():
        output_path = ROOT / output_path

    if not output_path.is_file():
        raise FileNotFoundError(f"Evidence file '{output_path}' does not exist")

    with output_path.open("r", encoding="utf-8") as file:
        evidence = json.load(file)

    if not isinstance(evidence, dict):
        raise TypeError("Evidence must be a JSON object")

    if "metrics" not in evidence:
        raise ValueError("Evidence is missing 'metrics'")

    if not isinstance(evidence["metrics"], dict):
        raise TypeError("Evidence metrics must be an object")

    if "claim_id" in evidence and evidence["claim_id"] != claim_id:
        raise ValueError(
            f"Expected claim '{claim_id}', but evidence belongs to '{evidence['claim_id']}'"
        )

    # ===== Tier Based =====
    if "tier" in claim:
        required_fields = {
            "claim_id",
            "status",
            "sample_size",
            "protocol",
        }

        missing_fields = required_fields - evidence.keys()

        if missing_fields:
            raise ValueError(f"Evidence is missing fields: {sorted(missing_fields)}")

        if evidence["status"] not in status_rank:
            raise ValueError(f"Unknown evidence status: {evidence['status']}")

        sample_size = evidence["sample_size"]

        if isinstance(sample_size, bool) or not isinstance(sample_size, int) or sample_size < 0:
            raise ValueError(f"Invalid sample size: {sample_size}")

        if not isinstance(evidence["protocol"], dict):
            raise TypeError("Evidence protocol must be an object")

    return evidence


def validate_claim(args: argparse.Namespace):
    claims_file = Path(args.file)

    if not claims_file.is_absolute():
        claims_file = ROOT / claims_file

    if not claims_file.is_file():
        raise FileNotFoundError(f"Claim file '{claims_file}' does not exist")

    with claims_file.open("rb") as file:
        data = tomllib.load(file)

    claim_id = args.claim

    if claim_id not in data:
        raise KeyError(f"Claim ID '{claim_id}' not found in '{claims_file}'")

    claim = data[claim_id]

    if "tier" in claim:
        if args.tier is None:
            raise ValueError(f"Claim '{claim_id}' requires --tier reported|certified")

        tier_name = args.tier

        if tier_name not in claim["tier"]:
            raise ValueError(f"Unknown tier '{tier_name}' for claim '{claim_id}'")

        tier = claim["tier"][tier_name]

        target = tier["target"]
        minimum_samples = tier["min_n"]

        checks = claim["check"]

    else:
        if args.tier is not None:
            raise ValueError(f"Claim '{claim_id}' does not support tiers")

        target = claim["target"]
        minimum_samples = None

        checks = [
            {
                "name": claim["metric"],
                "metric": claim["metric"],
                "op": claim["op"],
                "value": claim["value"],
            }
        ]

    print(f"Checking {claim_id}")
    print(f"Running target: make {target}")

    subprocess.run(
        ["make", target],
        cwd=ROOT,
        check=True,
    )

    evidence = load_evidence(claim_id, claim)

    if minimum_samples is not None:
        actual_status = evidence["status"]

        if status_rank[actual_status] < status_rank[tier_name]:
            raise ValueError(
                f"Required status '{tier_name}', but evidence only reached '{actual_status}'"
            )

        actual_samples = evidence["sample_size"]

        if actual_samples < minimum_samples:
            raise ValueError(f"Insufficient samples: {actual_samples} / {minimum_samples}")

    metrics = evidence["metrics"]

    for check in checks:
        metric_name = check["metric"]
        operation = ops[check["op"]]
        threshold = check["value"]

        if metric_name not in metrics:
            raise KeyError(f"Metric '{metric_name}' is missing from evidence")

        actual_value = metrics[metric_name]

        if not operation(actual_value, threshold):
            raise ValueError(
                f"FAILED: {check['name']} - got {actual_value}, expected {check['op']} {threshold}"
            )

        print(f"PASS: {check['name']} ({actual_value} {check['op']} {threshold})")

    print(f"PASS: {claim_id}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate LunarStream claims and gates")

    parser.add_argument(
        "-f",
        "--file",
        default="claims.toml",
        help="Path to claims TOML file",
    )

    sub_parser = parser.add_subparsers(
        dest="lunar_commands",
        required=True,
        help="Available commands",
    )

    parser_check = sub_parser.add_parser(
        "check",
        help="Checks a claim",
    )

    parser_check.add_argument(
        "claim",
        help="The claim ID to check (e.g. C01)",
    )

    parser_check.add_argument(
        "--tier",
        choices=["reported", "certified"],
        default=None,
        help="Minimum status tier required for validation",
    )

    parser_check.set_defaults(func=validate_claim)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
