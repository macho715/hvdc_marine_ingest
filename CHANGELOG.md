# Changelog

## [v2.7.0] - 2025-10-08

### Added - GIS Visualization Module
- **Leaflet-based real-time marine visualization** with wind vectors and wave height WMS overlay
- **6 map versions**: Option A (time-synced), Final Working (100% operational), TimeDimension variants
- **adapter.py**: Open-Meteo Marine + Forecast API parallel fetching with u/v vector conversion
- **map_leaflet.py**: Pixel-based wind arrows with zoom-stable rendering (latLngToLayerPoint)
- **Basemap fallback**: Esri World Ocean → OSM on tileerror event
- **cmocean 3-tier palette**: Low/Mid/High wind classification
- **TimeDimension integration**: 72-hour time slider with WMS synchronization
- **Playwright screenshots**: Automated PNG capture for reports
- **Integrated pipeline**: `run_integrated_viz.py` orchestrates data collection + GIS generation
- **Diagnostic tools**: test_step1_leaflet.html, test_step2_openmeteo.html for troubleshooting

### Added - Dynamic ML Pipeline
- **Config-driven RandomForest**: train_dynamic_model with flexible target/feature columns
- **7-day long-range forecasting**: predict_long_range_dynamic (168-hour horizon)
- **z-score anomaly detection**: detect_dynamic_anomalies with residual-based thresholds (3.0σ)
- **ForecastArtifacts dataclass**: Dynamic model container with RMSE tracking
- **7 ML configuration fields**: ml_history_path, ml_model_cache, ml_target_column, ml_feature_columns, ml_sqlite_table, ml_force_retrain, ml_forecast_horizon_hours
- **Dual-mode operation**: Dynamic (config-driven) + Legacy (cache fallback) with automatic switching
- **Enhanced reporting**: _resolve_prediction_column for flexible forecast output
- **SQLite + CSV support**: Multi-source historical data loading with _load_historical_dataset
- **Parallel API calls**: ThreadPoolExecutor for concurrent Open-Meteo fetching

### Changed
- **reporting.py**: "7-Day ERI Forecast" → "7-Day Long-Range Forecast" (neutral naming for dynamic targets)
- **weather_job_3d.py**: Integrated dynamic ML pipeline with legacy fallback mechanism
- **anomaly handling**: Support both dict[location, list] and DataFrame formats
- **TXT reports**: Enhanced with dynamic column detection and detailed metrics (Obs/Pred/z-score)
- **HTML reports**: Flexible prediction column rendering based on available data

### Fixed
- **PR #7 conflicts**: Resolved 5-file merge conflicts (+653/-136 lines)
- **Line endings**: Normalized to CRLF for Windows compatibility
- **Import order**: Grouped by standard-library vs third-party
- **WMS server status**: Documented PacIOOS temporary outage with 3 working alternatives

### Documentation
- **VIZ/OPTION_COMPARISON.md**: Complete comparison of 6 visualization versions
- **VIZ/PATCH_VERIFICATION.md**: Guide implementation verification (100% match)
- **VIZ/FINAL_STATUS.md**: Server status analysis and recommendations
- **VIZ/PR7_RESOLUTION.md**: PR #7 conflict resolution report
- **README.md**: Updated to v2.7 with GIS and Dynamic ML features
- **docs/SYSTEM_ARCHITECTURE.md**: Added GIS and ML pipeline sections
- **docs/en/ml_forecast.md**: English ML forecasting guide
- **docs/kr/ml_forecast.md**: Korean ML forecasting guide

---

## [Unreleased]

### Planned
- cmocean palette support for WMS servers
- Quantile-based COLORSCALERANGE automation
- Canvas heatmap layer for client-side wave rendering
- Extended time windows (past 72h + future 168h)

---

## [v2.6.0] - 2025-10-07

### Added
- Integrate RandomForest-based 7-day ERI forecasting and anomaly detection into the 72-hour job
- Provide `scripts/train_ml_model.py` and scheduled GitHub Actions workflow for weekly retraining
- Expand reporting outputs and documentation with ML forecast insights
- 3-Day GO/NO-GO Impact-Based Forecast (IBFWS) format
- Daily operational windows: D0/D+1/D+2 continuous window detection
- WMO/NOAA standards: Sea State Code 3700 + Small Craft Advisory

---

## Previous Versions

See git history for v2.5 and earlier releases.
