from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from math import sqrt
from statistics import mean, pstdev
from typing import Iterable


@dataclass(slots=True)
class MetricPoint:
    timestamp: datetime
    metric: str
    value: float


@dataclass(slots=True)
class AlertRule:
    metric: str
    direction: str
    threshold: float
    window: str
    severity: str
    expression: str
    justification: str


class AlertCalibrator:
    """Learns baseline behavior from historical metrics and generates alert rules."""

    def __init__(self, sensitivity: float = 2.8, min_samples: int = 120) -> None:
        self.sensitivity = sensitivity
        self.min_samples = min_samples

    def generate_rules(self, points: Iterable[MetricPoint]) -> list[AlertRule]:
        metrics: dict[str, list[float]] = {}
        for point in points:
            metrics.setdefault(point.metric, []).append(point.value)

        rules: list[AlertRule] = []
        for metric, values in metrics.items():
            if len(values) < self.min_samples:
                continue

            avg = mean(values)
            sigma = pstdev(values) if len(values) > 1 else 0.0
            spread = max(sigma, max(avg * 0.05, 0.01))

            high_threshold = avg + self.sensitivity * spread
            low_threshold = avg - self.sensitivity * spread

            volatility = spread / max(abs(avg), 0.01)
            window = "5m" if volatility < 0.20 else "10m"
            severity = self._severity(volatility)

            rules.append(
                AlertRule(
                    metric=metric,
                    direction="high",
                    threshold=round(high_threshold, 3),
                    window=window,
                    severity=severity,
                    expression=f"avg_over_time({metric}[{window}]) > {high_threshold:.3f}",
                    justification=(
                        f"High alert on {metric}: baseline mean={avg:.3f}, spread={spread:.3f}, "
                        f"threshold=mean+{self.sensitivity}σ to keep noise low while catching anomalies."
                    ),
                )
            )

            if low_threshold > 0:
                rules.append(
                    AlertRule(
                        metric=metric,
                        direction="low",
                        threshold=round(low_threshold, 3),
                        window=window,
                        severity=severity,
                        expression=f"avg_over_time({metric}[{window}]) < {low_threshold:.3f}",
                        justification=(
                            f"Low alert on {metric}: baseline mean={avg:.3f}, spread={spread:.3f}, "
                            f"threshold=mean-{self.sensitivity}σ to catch brownouts and silent failures."
                        ),
                    )
                )

        return rules

    def tune_from_feedback(self, rules: list[AlertRule], false_positive_rate: float) -> list[AlertRule]:
        """Self-tune thresholds based on observed false positives."""
        if false_positive_rate > 0.25:
            adjustment = 1.10
        elif false_positive_rate < 0.05:
            adjustment = 0.95
        else:
            adjustment = 1.0

        tuned: list[AlertRule] = []
        for rule in rules:
            distance = abs(rule.threshold) * (adjustment - 1.0)
            threshold = rule.threshold + distance if rule.direction == "high" else rule.threshold - distance
            tuned.append(
                AlertRule(
                    metric=rule.metric,
                    direction=rule.direction,
                    threshold=round(threshold, 3),
                    window=rule.window,
                    severity=rule.severity,
                    expression=self._rewrite_expression(rule.expression, threshold),
                    justification=rule.justification
                    + f" Auto-tuned with FPR={false_positive_rate:.2%}, adjustment={adjustment:.2f}.",
                )
            )
        return tuned

    @staticmethod
    def _rewrite_expression(expression: str, new_threshold: float) -> str:
        head, _, _ = expression.rpartition(" ")
        return f"{head} {new_threshold:.3f}"

    @staticmethod
    def _severity(volatility: float) -> str:
        index = min(int(sqrt(max(volatility, 0.0)) * 10), 10)
        return "critical" if index <= 3 else "warning"
