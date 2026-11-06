#!/usr/bin/env python3
"""NATIONVK AVIATOR RESEARCH LAB — standard-library CLI."""
import argparse
import csv
import json
import sys
from pathlib import Path

from research_lab import analyze, generate_synthetic, verify_sha256_reveal, sha256_hex


def read_csv(path):
    with open(path, "r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "multiplier" not in reader.fieldnames:
            raise ValueError("CSV must contain a 'multiplier' column.")
        return [row.get("multiplier") for row in reader]


def print_report(report):
    print("\nNATIONVK AVIATOR RESEARCH LAB")
    print("=" * 44)
    print("Sample size :", report["sample_size"])
    print("Mean        :", round(report["mean"], 4))
    print("Median      :", round(report["median"], 4))
    print("Min / Max   :", report["minimum"], "/", report["maximum"])
    print("Sample SD   :", round(report["sample_sd"], 4))
    print("\nThreshold analysis")
    for threshold, item in report["thresholds"].items():
        low, high = item["wilson_95_ci"]
        print(f"  >= {threshold}x: {item['hits']}/{item['trials']} "
              f"({item['empirical_rate']:.2%}); 95% CI [{low:.2%}, {high:.2%}]")
    print("\nLag-1 correlation (exploratory):", report["lag1_correlation_exploratory"])
    print("\nNOTE:", report["warning"])


def main():
    parser = argparse.ArgumentParser(description="Educational crash-multiplier statistics toolkit")
    sub = parser.add_subparsers(dest="command", required=True)

    demo = sub.add_parser("demo", help="generate and analyze synthetic data")
    demo.add_argument("--rounds", type=int, default=1000)
    demo.add_argument("--seed", type=int, default=42)
    demo.add_argument("--house-edge", type=float, default=0.03)
    demo.add_argument("--csv", default="synthetic_rounds.csv")
    demo.add_argument("--json", default="demo_report.json")

    analyze_cmd = sub.add_parser("analyze", help="analyze a CSV with a multiplier column")
    analyze_cmd.add_argument("csv_file")
    analyze_cmd.add_argument("--json", dest="json_file")

    verify = sub.add_parser("verify-hash", help="verify SHA-256(seed) against a commitment")
    verify.add_argument("--seed", required=True)
    verify.add_argument("--commit", required=True)

    args = parser.parse_args()

    try:
        if args.command == "demo":
            values = generate_synthetic(args.rounds, args.seed, args.house_edge)
            with open(args.csv, "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(["round_id", "multiplier", "verified", "data_type"])
                for index, value in enumerate(values, 1):
                    writer.writerow([index, value, "no", "synthetic"])
            report = analyze(values)
            report["data_type"] = "synthetic"
            report["simulation_seed"] = args.seed
            with open(args.json, "w", encoding="utf-8") as handle:
                json.dump(report, handle, indent=2)
            print_report(report)
            print(f"\nSynthetic CSV saved: {args.csv}")
            print(f"JSON report saved: {args.json}")
        elif args.command == "analyze":
            values = read_csv(args.csv_file)
            report = analyze(values)
            report["source_file"] = args.csv_file
            print_report(report)
            if args.json_file:
                with open(args.json_file, "w", encoding="utf-8") as handle:
                    json.dump(report, handle, indent=2)
                print(f"\nJSON report saved: {args.json_file}")
        elif args.command == "verify-hash":
            valid = verify_sha256_reveal(args.seed, args.commit)
            print("MATCH: commitment verified" if valid else "NO MATCH: commitment not verified")
            print("Computed SHA-256:", sha256_hex(args.seed))
            return 0 if valid else 1
    except (OSError, ValueError) as exc:
        print("Error:", exc, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
