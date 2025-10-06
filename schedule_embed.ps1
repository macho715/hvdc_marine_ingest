# KR: 3시간마다 임베딩 재생성 작업 등록
# EN: Register job to rebuild embeddings every 3 hours

$python = "C:\hvdc\marine-ingest\.venv\Scripts\python.exe"
$script = "C:\hvdc\marine-ingest\embed_index.py"

$action = New-ScheduledTaskAction -Execute $python -Argument $script
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(5) -RepetitionInterval (New-TimeSpan -Hours 3) -RepetitionDuration ([TimeSpan]::MaxValue)

Register-ScheduledTask -TaskName "HVDC_Marine_Embed" -Action $action -Trigger $trigger -Description "Rebuild marine embeddings every 3h" -User $env:UserName -RunLevel Highest
