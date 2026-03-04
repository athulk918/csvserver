from __future__ import annotations

import argparse
import csv
import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from .calibrator import AlertCalibrator, MetricPoint


def parse_points(csv_path: Path) -> list[MetricPoint]:
    points: list[MetricPoint] = []
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            points.append(
                MetricPoint(
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    metric=row["metric"],
                    value=float(row["value"]),
                )
            )
    return points


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate calibrated Prometheus/Azure rules")
    parser.add_argument("metrics_csv", type=Path, help="CSV with timestamp, metric, value")
    parser.add_argument("--sensitivity", type=float, default=2.8)
    args = parser.parse_args()

    points = parse_points(args.metrics_csv)
    calibrator = AlertCalibrator(sensitivity=args.sensitivity)
    rules = calibrator.generate_rules(points)

    print(
        json.dumps(
            [asdict(rule) for rule in rules],
            indent=2,
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
