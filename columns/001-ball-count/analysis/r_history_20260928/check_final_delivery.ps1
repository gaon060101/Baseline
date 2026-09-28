param([Parameter(Mandatory=$true)][string]$OutputPath)
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $OutputPath) { throw '기존 검수 기록을 덮어쓰지 않습니다.' }
$analysisRoot = 'columns/001-ball-count/analysis'
$bcai = Get-Content -LiteralPath "$analysisRoot/r_history_20260928/report_validation.json" -Raw | ConvertFrom-Json
$bcap = Get-Content -LiteralPath "$analysisRoot/r_bcap_history_20260928/report_validation.json" -Raw | ConvertFrom-Json
$supplement = Get-Content -LiteralPath "$analysisRoot/r_supplement_20260928/postflight.json" -Raw | ConvertFrom-Json
$progress = Get-Content -LiteralPath "$analysisRoot/r_bcap_history_20260928/progress.json" -Raw | ConvertFrom-Json
$problems = [System.Collections.Generic.List[string]]::new()
function Require-True($condition, [string]$message) { if (-not $condition) { $problems.Add($message) } }
Require-True ($bcai.status -eq 'PASS' -and $bcai.completed_seasons -eq 11 -and $bcai.summary_rows -eq 132 -and @($bcai.pending_years).Count -eq 0) 'BCAI 완료 범위 불일치'
Require-True ($bcap.status -eq 'PASS' -and $bcap.complete_model_years -eq 44 -and $bcap.summary_rows -eq 2552 -and $bcap.mobile_charts -eq 44 -and @($bcap.pending_model_years).Count -eq 0) 'BCAP 완료 범위 불일치'
Require-True ($progress.status -eq 'COMPLETE') 'BCAP 실행기 미완료'
Require-True ($supplement.status -eq 'PASS' -and @($supplement.checks).Count -eq 24 -and @($supplement.checks | Where-Object status -ne 'PASS').Count -eq 0) '2026 검산 불일치'
Require-True ($supplement.intentional_geometry_holds.status -eq 'WITHHELD_MEASUREMENT') '2026 측정 보류 누락'
$bcaiIds = @($bcai.selected_runs)
$bcapIds = @($bcap.selected_model_years.run_id | Sort-Object -Unique)
$manifestPaths = @($bcaiIds + $bcapIds | ForEach-Object { "$analysisRoot/runs/$_/manifest.json" }) + @($supplement.runs.path)
Require-True ($bcaiIds.Count -eq 10 -and $bcapIds.Count -eq 40 -and $manifestPaths.Count -eq 53) '완료 실행 개수 불일치'
$manifests = foreach ($path in $manifestPaths) {
  $m = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
  Require-True ($m.status -eq 'COMPLETE') "미완료 실행: $path"
  [ordered]@{path=$path;run_id=$m.run_id;status=$m.status;model_id=$m.model_id;model_status=$m.model_status;sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()}
}
$references = @($bcai.inputs) + @($bcai.outputs) + @($bcap.inputs) + @($bcap.outputs) + @($supplement.runs) + @($supplement.outputs)
$checked = foreach ($ref in $references) {
  $actual = (Get-FileHash -LiteralPath $ref.path -Algorithm SHA256).Hash.ToLowerInvariant()
  $matches = $actual -eq $ref.sha256
  Require-True $matches "보고서 연결 해시 불일치: $($ref.path)"
  [ordered]@{path=$ref.path;sha256=$actual;matches=$matches}
}
$live = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(python|Rscript)\.exe$' -and $_.CommandLine -match 'run_bca[pi]_history\.py|render_bca[pi]_history\.R|execution_code[\\/].*[\\/]run\.R' } | Select-Object ProcessId,Name,CommandLine)
Require-True ($live.Count -eq 0) '완료 뒤에도 계산·보고 실행기가 동작 중'
$result = [ordered]@{
  checked_at=(Get-Date -Format o)
  status=$(if($problems.Count -eq 0){'PASS'}else{'FAIL'})
  scope_ko='기존 완료 manifest와 보고서 연결 파일의 무결성·범위 확인. 통계 재계산·재적합·시각 검수는 수행하지 않음; 독립 수치 및 화면 검수는 별도 기록 참조.'
  bcai_seasons=$bcai.completed_seasons
  bcap_model_years=$bcap.complete_model_years
  bcap_mobile_figures=$bcap.mobile_charts
  bcap_summary_rows=$bcap.summary_rows
  complete_runs=$manifestPaths.Count
  checked_hash_references=$checked.Count
  live_analysis_processes=$live
  holds=$supplement.intentional_geometry_holds
  manifests=$manifests
  file_checks=$checked
  problems=@($problems)
}
$result | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath $OutputPath -Encoding utf8
[pscustomobject]$result | Select-Object status,bcai_seasons,bcap_model_years,bcap_mobile_figures,bcap_summary_rows,complete_runs,checked_hash_references,problems | ConvertTo-Json -Depth 3
if ($problems.Count -gt 0) { exit 1 }
