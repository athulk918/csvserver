# prom-ai ("Prometheus Whisperer")

`prom-ai` is a starter implementation of an AI-assisted alert calibration system:

1. Ingest ~90 days of metrics history.
2. Learn metric-specific baselines and volatility.
3. Generate calibrated Prometheus/Azure Monitor alert rules with justification.
4. Monitor alert quality and self-tune thresholds over time.

## Why this exists

Static alert thresholds create two bad outcomes:
- **Too tight**: alert fatigue.
- **Too loose**: missed incidents.

This project adds an adaptive calibration layer that can be integrated into CI or scheduled jobs.

## Input format

CSV with columns:

```csv
timestamp,metric,value
2026-01-01T00:00:00,cpu_usage,57.2
2026-01-01T00:00:00,request_latency_ms,201.8
```

## Quickstart

```bash
cd prom-ai
python -m venv .venv && source .venv/bin/activate
pip install -e .
prom-ai examples/sample_metrics.csv > rules.json
```

## Design notes

### Rule generation

`AlertCalibrator` computes:
- baseline mean
- standard deviation-derived spread (with floor for low-variance signals)
- high/low thresholds as `mean ± sensitivity * spread`
- evaluation window and severity from signal volatility

Each rule includes a human-readable **justification** documenting how the threshold was derived.

### Self-tuning loop

`QualityMonitor` tracks:
- precision (confirmed incidents / alerts)
- noise index (1 - precision)
- mean time to resolve

`AlertCalibrator.tune_from_feedback(...)` then widens or tightens threshold bands based on measured false-positive rate.

## Example output

```json
[
  {
    "metric": "cpu_usage",
    "direction": "high",
    "threshold": 73.412,
    "window": "5m",
    "severity": "warning",
    "expression": "avg_over_time(cpu_usage[5m]) > 73.412",
    "justification": "High alert on cpu_usage: baseline mean=58.292, spread=5.400, threshold=mean+2.8σ to keep noise low while catching anomalies."
  }
]
```

## Next steps

- Plug into Prometheus recording rules and Alertmanager routes.
- Add seasonality decomposition (weekday/weekend, business-hour profiles).
- Replace heuristic thresholds with probabilistic forecasting.
- Persist quality metrics and run auto-tuning as a daily job.
