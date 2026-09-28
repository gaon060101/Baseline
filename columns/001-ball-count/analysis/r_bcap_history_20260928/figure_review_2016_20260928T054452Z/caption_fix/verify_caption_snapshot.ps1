$ErrorActionPreference='Stop'
$hub='columns/001-ball-count/analysis/r_bcap_history_20260928'
$dir="$hub/figure_review_2016_20260928T054452Z/caption_fix"
$old=Get-Content -Raw -LiteralPath "$dir/before/report_validation.json" | ConvertFrom-Json
$vp="$hub/report_validation.json"
$vhash=(Get-FileHash -LiteralPath $vp -Algorithm SHA256).Hash.ToLower()
$v=Get-Content -Raw -LiteralPath $vp | ConvertFrom-Json
if($v.generated_at -eq $old.generated_at -or -not $v.checks.legacy_velocity_caption_present_where_required) { throw 'Caption render not ready' }
if(@(Get-CimInstance Win32_Process -Filter "name='Rscript.exe'" | Where-Object { $_.CommandLine -like '*render_bcap_history.R*' }).Count -gt 0) { throw 'Renderer still active' }
New-Item -ItemType Directory -Path "$dir/after" -ErrorAction Stop | Out-Null
$entries=@($v.outputs)+@(@{path=$vp;sha256=$vhash;bytes=(Get-Item -LiteralPath $vp).Length},@{path='tools/render_bcap_history.R';sha256=(Get-FileHash -LiteralPath 'tools/render_bcap_history.R' -Algorithm SHA256).Hash.ToLower();bytes=(Get-Item -LiteralPath 'tools/render_bcap_history.R').Length})
$files=@()
foreach($e in $entries) {
 if((Get-FileHash -LiteralPath $e.path -Algorithm SHA256).Hash.ToLower() -ne $e.sha256) { throw 'After source mismatch' }
 $saved="$dir/after/$([IO.Path]::GetFileName($e.path))"
 Copy-Item -LiteralPath $e.path -Destination $saved -ErrorAction Stop
 if((Get-FileHash -LiteralPath $saved -Algorithm SHA256).Hash.ToLower() -ne $e.sha256) { throw 'After copy mismatch' }
 $files+=@{source=$e.path;saved=$saved;sha256=$e.sha256;bytes=$e.bytes}
}
if((Get-FileHash -LiteralPath $vp -Algorithm SHA256).Hash.ToLower() -ne $vhash) { throw 'Report changed during capture' }
$oldRows=@(Import-Csv -LiteralPath "$dir/before/summary.csv")
$newRows=@(Import-Csv -LiteralPath "$dir/after/summary.csv")
function ReviewKey($row) { @($row.model,$row.game_year,$row.level,$row.count,$row.region,$row.pitch_group) -join '|' }
$newIndex=@{}
foreach($row in $newRows) { $key=ReviewKey $row; if($newIndex.ContainsKey($key)) { throw 'Duplicate result key' }; $newIndex[$key]=$row }
foreach($row in $oldRows) {
 $key=ReviewKey $row
 if(-not $newIndex.ContainsKey($key) -or ($row | ConvertTo-Json -Compress -Depth 5) -cne ($newIndex[$key] | ConvertTo-Json -Compress -Depth 5)) { throw 'Prior aggregate changed' }
}
foreach($entry in $old.inputs) { if((Get-FileHash -LiteralPath $entry.path -Algorithm SHA256).Hash.ToLower() -ne $entry.sha256) { throw 'Original analysis input changed' } }
foreach($axis in $v.count_axis_checks) {
 if(-not $axis.passed -or ($axis.labels_top_to_bottom -join ',') -ne '0-0,0-1,0-2,1-0,1-1,1-2,2-0,2-1,2-2,3-0,3-1,3-2') { throw 'Count order failed' }
 if($axis.legacy_velocity_caption_required -and -not $axis.legacy_velocity_caption_present) { throw 'Missing required velocity caption' }
}
$mobileChecks=@()
foreach($model in @('pitch','pitch_sb','swing','pitch_ff')) {
 $chart="$($model)_2016_count_mobile.png"
 $axis=@($v.count_axis_checks | Where-Object { $_.chart -eq $chart })[0]
 if(-not $axis.legacy_velocity_caption_required -or -not $axis.legacy_velocity_caption_present) { throw '2016 mobile caption missing' }
 $imagePath="$dir/after/$chart"
 $b=[IO.File]::ReadAllBytes((Resolve-Path -LiteralPath $imagePath))
 $width=([int]$b[16] -shl 24) -bor ([int]$b[17] -shl 16) -bor ([int]$b[18] -shl 8) -bor [int]$b[19]
 $height=([int]$b[20] -shl 24) -bor ([int]$b[21] -shl 16) -bor ([int]$b[22] -shl 8) -bor [int]$b[23]
 if($width -ne 900 -or $height -ne 1350) { throw 'Mobile dimensions changed' }
 $mobileChecks+=@{chart=$chart;width_px=$width;height_px=$height;velocity_caption_present=$true;sha256=(Get-FileHash -LiteralPath $imagePath -Algorithm SHA256).Hash.ToLower()}
}
$beforeRecord=Get-Content -Raw -LiteralPath "$dir/before_snapshot.json" | ConvertFrom-Json
foreach($file in $beforeRecord.files) { if((Get-FileHash -LiteralPath $file.saved -Algorithm SHA256).Hash.ToLower() -ne $file.sha256) { throw 'Before evidence changed' } }
$record=[ordered]@{status='PASS';checked_utc=(Get-Date).ToUniversalTime().ToString('o');before_generated_at=$old.generated_at;after_generated_at=$v.generated_at;before_model_years=$old.complete_model_years;after_model_years=$v.complete_model_years;prior_aggregate_rows_unchanged=$oldRows.Count;after_aggregate_rows=$newRows.Count;prior_original_inputs_unchanged=$old.inputs.Count;axes_checked=$v.count_axis_checks.Count;all_count_axes_pass=$true;velocity_captions_required=@($v.count_axis_checks | Where-Object { $_.legacy_velocity_caption_required }).Count;all_required_velocity_captions_present=$true;mobile2016=$mobileChecks;after_files=$files;scope='표시 캡션 수정 후 사본·집계·원 입력 해시·실제 그림 캡션 설정 검증. 모델 재적합이나 통계 변경은 없음. 육안 열람 결과는 별도 기록.'}
$record | ConvertTo-Json -Depth 15 | Set-Content -LiteralPath "$dir/postflight.json" -Encoding utf8
[pscustomobject]$record | Select-Object status,before_generated_at,after_generated_at,before_model_years,after_model_years,prior_aggregate_rows_unchanged,prior_original_inputs_unchanged,axes_checked,velocity_captions_required | ConvertTo-Json
