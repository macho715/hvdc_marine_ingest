# 장기 예측 기능 업데이트

3일 마린 파이프라인에 72시간 이후를 커버하는 머신러닝 예측기가 추가되었습니다.
`src/marine_ops/pipeline/ml_forecast.py` 모듈은 다음 기능을 제공합니다.

- CSV 또는 SQLite 형식의 히스토리 데이터를 최근 융합 프레임과 함께 적재합니다.
- 유의파고를 목표 변수로 하는 RandomForest 회귀 모델을 학습하고 캐싱합니다.
- `scripts/weather_job_3d.py` 실행 시 생성되는 HTML/JSON/CSV 보고서에 7일 전망을
  포함합니다.
- 잔차 기반 이상치를 탐지하여 의심스러운 과거 관측을 강조합니다.

`weather_job_3d.py` 오케스트레이터는 보고서를 렌더링하기 전에 모델을 학습하거나
캐시된 아티팩트를 재사용합니다. 출력물에는 “7-Day Forecast Outlook”과 “Model Anomaly
Alerts” 섹션이 추가되며, 기존 결과물과 동일한 경로에 장기 전망 및 이상치 CSV가
생성되어 후속 자동화에 활용할 수 있습니다.
