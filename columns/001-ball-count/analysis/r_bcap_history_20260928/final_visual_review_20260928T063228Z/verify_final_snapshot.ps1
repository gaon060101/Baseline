$ErrorActionPreference='Stop'
$dir='columns/001-ball-count/analysis/r_bcap_history_20260928/final_visual_review_20260928T063228Z'
$s=Get-Content -Raw -LiteralPath "$dir/snapshot_manifest.json" | ConvertFrom-Json
$v=Get-Content -Raw -LiteralPath "$dir/snapshot/report_validation.json" | ConvertFrom-Json
foreach($file in $s.files) {
 if((Get-FileHash -LiteralPath $file.saved -Algorithm SHA256).Hash.ToLower() -ne $file.sha256) { throw 'Snapshot changed' }
 if((Get-FileHash -LiteralPath $file.source -Algorithm SHA256).Hash.ToLower() -ne $file.sha256) { throw "Original source changed: $($file.source)" }
}
$summary=@(Import-Csv -LiteralPath "$dir/snapshot/summary.csv")
function FinalReviewKey($runId,$row) { @($runId,$row.game_year,$row.level,$row.count,$row.region,$row.pitch_group) -join '|' }
$index=@{}
foreach($row in $summary) { $key=FinalReviewKey $row.run_id $row; if($index.ContainsKey($key)) { throw 'Duplicate summary key' }; $index[$key]=$row }
$checkedRows=0
foreach($runId in @($s.selected_runs.run_id | Select-Object -Unique)) {
 $original=@(Import-Csv -LiteralPath "$dir/snapshot/source_runs/$runId/year_values.csv")
 foreach($sourceRow in $original) {
  $key=FinalReviewKey $runId $sourceRow
  if(-not $index.ContainsKey($key)) { throw 'Missing original row in final report' }
  $reportRow=$index[$key]
  foreach($field in $sourceRow.PSObject.Properties.Name) {
   if($sourceRow.$field -cne $reportRow.$field) { throw "Original/report field mismatch: $key $field" }
  }
  $checkedRows++
 }
}
if($checkedRows -ne $summary.Count -or $checkedRows -ne 2552) { throw 'Unexpected aggregate coverage' }
$main=@($summary | Where-Object { $_.level -eq 'count' })
$unsupported=@($main | Where-Object { $_.support_gate -eq 'FALSE' })
if($main.Count -ne 528 -or $unsupported.Count -ne 1 -or $unsupported[0].model -ne 'pitch' -or $unsupported[0].game_year -ne '2020' -or $unsupported[0].count -ne '3-0') { throw 'Unexpected unsupported primary group' }
foreach($r in $summary | Where-Object { $_.support_gate -eq 'FALSE' }) { if($r.evidence -ne '비교 자료 부족' -or -not [string]::IsNullOrEmpty($r.point_direction)) { throw 'Unsupported label/point direction mismatch' } }
if($v.count_axis_checks.Count -ne 48) { throw 'Missing chart checks' }
foreach($a in $v.count_axis_checks) {
 if(-not $a.passed -or ($a.labels_top_to_bottom -join ',') -ne '0-0,0-1,0-2,1-0,1-1,1-2,2-0,2-1,2-2,3-0,3-1,3-2') { throw 'Axis order mismatch' }
 if($a.legacy_velocity_caption_required -and -not $a.legacy_velocity_caption_present) { throw 'Required velocity caveat missing' }
}
$reportText=Get-Content -Raw -LiteralPath "$dir/snapshot/report.md"
if(-not $reportText.Contains('2015·2016 구속은 보정 PITCHf/x 기반이고 2017 이후 Statcast와 물리량 구간의 직접 비교는 미검증이다.')) { throw 'Missing report measurement limitation' }
$viewed=@()
foreach($model in @('pitch','pitch_sb','swing','pitch_ff')) {
 foreach($filename in @("$($model)_2015_count_mobile.png","$($model)_count_history.png")) {
  $file=@($s.files | Where-Object { [IO.Path]::GetFileName($_.saved) -eq $filename })[0]
  $b=[IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $file.saved))
  $width=([int]$b[16] -shl 24) -bor ([int]$b[17] -shl 16) -bor ([int]$b[18] -shl 8) -bor [int]$b[19]
  $height=([int]$b[20] -shl 24) -bor ([int]$b[21] -shl 16) -bor ([int]$b[22] -shl 8) -bor [int]$b[23]
  $mobile=$filename -like '*_mobile.png'
  if(($mobile -and ($width -ne 900 -or $height -ne 1350)) -or (-not $mobile -and ($width -ne 1860 -or $height -ne 3860))) { throw 'Unexpected image dimensions' }
  $viewed+=@{path=$file.saved;original_path=$file.source;sha256=$file.sha256;width_px=$width;height_px=$height;view_detail='original';actual_visual_review=$true;status='PASS';notes='원 해상도로 직접 열람. 한글·축·구속 측정 주의문·조건부 구간·연도별/공유 적합 설명 정상. 텍스트·점·구간 잘림 없음.'}
 }
}
$byModel2015=@()
foreach($model in @('pitch','pitch_sb','swing','pitch_ff')) {
 $rows=@($summary | Where-Object { $_.model -eq $model -and $_.game_year -eq '2015' })
 $byModel2015+=@{model=$model;summary_groups=$rows.Count;supported_primary_counts=@($rows | Where-Object { $_.level -eq 'count' -and $_.support_gate -eq 'TRUE' }).Count;unsupported_groups=@($rows | Where-Object { $_.support_gate -eq 'FALSE' }).Count}
}
$qa=[ordered]@{status='PASS';reviewed_utc=(Get-Date).ToUniversalTime().ToString('o');snapshot_report_generated_at=$v.generated_at;report_validation_sha256=$s.report_validation_sha256;complete_model_years=44;pending_model_years=@($v.pending_model_years).Count;all_snapshot_and_original_hashes_verified=$s.files.Count;completed_run_input_hashes_verified=$v.inputs.Count;aggregate_rows_exactly_match_originals=$checkedRows;main_chart_rows=528;supported_main_rows=527;unsupported_main_rows=@($unsupported | Select-Object model,game_year,count,support_gate,evidence);all_48_chart_axes_pass=$true;velocity_caption_required_charts=@($v.count_axis_checks | Where-Object { $_.legacy_velocity_caption_required }).Count;required_velocity_captions_present=$true;viewed_images=$viewed;year2015=$byModel2015;renderer_executed=$false;models_recomputed=$false;scope='2015 모바일 4장과 2015~2025 최종 종합 4장을 원본 해상도로 직접 열람. 2,552행은 원 저장 집계와 필드별 정확히 일치. 원 점수 재계산·인과 검증·전체 학습 불확실성 검증은 수행하지 않음. 다른 모바일 PNG의 육안 확인은 이전 날짜별 기록을 따른다.'}
$qa | ConvertTo-Json -Depth 15 | Set-Content -LiteralPath "$dir/visual_review.json" -Encoding utf8
[pscustomobject]@{status='PASS';generated_at=$v.generated_at;hashes=$s.files.Count;original_rows=$checkedRows;viewed=$viewed.Count;main_rows=$main.Count;unsupported_primary=$unsupported.Count;legacy_caption_charts=$qa.velocity_caption_required_charts;year2015=$byModel2015} | ConvertTo-Json -Depth 5
