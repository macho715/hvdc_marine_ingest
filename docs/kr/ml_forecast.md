# 해양 장기 예측 모듈

## 개요

이 플러그인은 기존 72시간 파이프라인에 다음 기능을 추가합니다.

- RandomForest 기반 7일 ERI 예측 (24시간 간격)
- IsolationForest를 이용한 Sea State 이상 탐지
- `cache/ml_forecast/` 디렉터리에 모델 아티팩트 및 메타데이터 저장
- GitHub Actions `ml-retrain.yml`을 통한 주간 자동 재학습

## 학습 절차

```
python scripts/train_ml_model.py \
  --sources data/historical_marine_metrics.csv \
  --output cache/ml_forecast \
  --metadata cache/ml_forecast/metadata.json
```

실제 데이터가 없으면 합성 데이터로 자동 대체하여 항상 기준 모델이 생성됩니다.
학습된 행 수와 MAE는 메타데이터 파일에 기록됩니다.

## 파이프라인 연동

- `scripts/weather_job_3d.py`: 모델 로드 및 필요 시 재학습 수행
- `render_html_3d`: 7일 예측과 이상 탐지 결과를 HTML 보고서에 포함
- `write_side_outputs`: JSON/TXT/CSV 부가 산출물에 ML 정보를 확장

## CI 자동화

`ml-retrain.yml` 워크플로는 매주 실행되어 최신 모델을 학습하고 GitHub Artifact로 업로드합니다.
워크플로 실행 상세 화면에서 다운로드할 수 있습니다.
