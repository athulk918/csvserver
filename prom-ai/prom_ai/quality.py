from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(slots=True)
class AlertEvent:
    rule_name: str
    fired_at: datetime
    resolved_at: datetime
    incident_confirmed: bool


class QualityMonitor:
    """Tracks alert quality KPIs and suggests rule health actions."""

    def __init__(self, lookback_days: int = 30) -> None:
        self.lookback = timedelta(days=lookback_days)

    def score(self, events: list[AlertEvent], now: datetime) -> dict[str, float]:
        recent = [e for e in events if now - e.fired_at <= self.lookback]
        if not recent:
            return {"precision": 1.0, "noise_index": 0.0, "mean_time_to_resolve_min": 0.0}

        confirmed = [e for e in recent if e.incident_confirmed]
        precision = len(confirmed) / len(recent)
        noise_index = 1 - precision

        mtt_resolve = (
            sum((e.resolved_at - e.fired_at).total_seconds() for e in recent) / len(recent) / 60
        )
        return {
            "precision": round(precision, 3),
            "noise_index": round(noise_index, 3),
            "mean_time_to_resolve_min": round(mtt_resolve, 2),
        }

    def recommendation(self, quality: dict[str, float]) -> str:
        if quality["noise_index"] > 0.25:
            return "Increase threshold band by 10% and extend evaluation window by 2m."
        if quality["precision"] > 0.95 and quality["mean_time_to_resolve_min"] > 20:
            return "Tighten thresholds by 5% to detect incidents earlier."
        return "No tuning needed."
