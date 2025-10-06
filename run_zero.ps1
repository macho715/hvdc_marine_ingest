# KR: 수동 ZERO 보고서 생성
# EN: Manually emit ZERO report

$ErrorActionPreference = "Stop"
. "C:\hvdc\marine-ingest\.venv\Scripts\Activate.ps1"
chcp 65001 | Out-Null
$env:PYTHONUTF8 = "1"
python .\ncm_zero_guard.py --tz "Asia/Dubai"
