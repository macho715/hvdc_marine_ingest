# KR: 1회 실행 스크립트 — venv 활성화 → 수집(선택) → 임베딩 구축 → 테스트 질의
# EN: One‑shot runner — activate venv → (optional) ingest → build embeddings → test query

$ErrorActionPreference = "Stop"

# Activate venv
$venv = ".\.venv\Scripts\Activate.ps1"
if (Test-Path $venv) { . $venv } else { throw "Venv not found: $venv" }

# UTF-8
chcp 65001 | Out-Null
$env:PYTHONUTF8 = "1"

# Optional ingest from snapshot.html
if (Test-Path "snapshot.html") {
  Write-Host "[ingest] snapshot.html → data/marine_manual.csv"
  python .\ingest_standalone.py
}

# Build embeddings
Write-Host "[embed] CSV → DB(raw) → embeddings"
python .\embed_index.py

# Test query
Write-Host "[query] AGI high tide RORO window"
python .\query_knn.py

# Integrated weather report (demo mode)
Write-Host "[report] Integrated marine weather report (demo)"
python .\scripts\demo_integrated.py
