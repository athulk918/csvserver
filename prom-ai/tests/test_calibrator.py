from datetime import datetime, timedelta

from prom_ai.calibrator import AlertCalibrator, MetricPoint
from prom_ai.quality import AlertEvent, QualityMonitor


def test_generate_rules_emits_high_and_low():
    base = datetime(2026, 1, 1)
    points = [
        MetricPoint(timestamp=base + timedelta(minutes=i), metric="cpu_usage", value=50 + (i % 5))
        for i in range(500)
    ]
    calibrator = AlertCalibrator()

    rules = calibrator.generate_rules(points)

    assert any(r.direction == "high" for r in rules)
    assert any(r.direction == "low" for r in rules)


def test_tune_from_feedback_adjusts_thresholds():
    base = datetime(2026, 1, 1)
    points = [
        MetricPoint(timestamp=base + timedelta(minutes=i), metric="cpu_usage", value=50 + (i % 3))
        for i in range(300)
    ]
    calibrator = AlertCalibrator()
    rules = calibrator.generate_rules(points)

    tuned = calibrator.tune_from_feedback(rules, false_positive_rate=0.4)

    assert tuned[0].threshold != rules[0].threshold


def test_quality_monitor_scores_and_recommendations():
    now = datetime(2026, 4, 1)
    events = [
        AlertEvent("cpu_high", now - timedelta(hours=4), now - timedelta(hours=3, minutes=40), True),
        AlertEvent("cpu_high", now - timedelta(hours=2), now - timedelta(hours=1, minutes=40), False),
    ]
    monitor = QualityMonitor()

    score = monitor.score(events, now)

    assert score["precision"] == 0.5
    assert "Increase threshold" in monitor.recommendation(score)
