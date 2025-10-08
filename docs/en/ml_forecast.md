# Marine Long-Range Forecast Module

## Overview

The long-range forecast plug-in extends the 72-hour marine job with:

- RandomForest-based ERI prediction out to seven days (24-hour cadence)
- IsolationForest anomaly detection on recent sea-state conditions
- Automated artifact storage under `cache/ml_forecast/`
- Weekly retraining via GitHub Actions (`ml-retrain.yml`)

## Training Workflow

```
python scripts/train_ml_model.py \
  --sources data/historical_marine_metrics.csv \
  --output cache/ml_forecast \
  --metadata cache/ml_forecast/metadata.json
```

When no historical data is available the script falls back to synthetic samples, ensuring that a
baseline model is always created. Metrics (rows trained, MAE) are stored in the metadata file.

## Pipeline Integration

- `scripts/weather_job_3d.py` loads the cached model or retrains when missing
- `render_html_3d` appends 7-day forecasts and anomaly alerts to the executive summary
- `write_side_outputs` enriches JSON/TXT/CSV exports with ML insights

## CI Automation

`ml-retrain.yml` executes weekly and publishes the refreshed artifact as a GitHub workflow
artifact. The resulting files can be downloaded from the workflow run summary.
