$ErrorActionPreference='Stop'
$reviewDir='columns/001-ball-count/analysis/r_bcap_history_20260928/figure_review_20260928T042928Z'
$hub='columns/001-ball-count/analysis/r_bcap_history_20260928'
$before=Get-Content -Raw -LiteralPath "$reviewDir/before_snapshot.json" | ConvertFrom-Json
foreach($entry in $before.files) {
 $saved=Join-Path "$reviewDir/before" ([IO.Path]::GetFileName($entry.path))
 if((Get-FileHash -LiteralPath $saved -Algorithm SHA256).Hash.ToLower() -ne $entry.sha256) { throw "Before evidence changed: $saved" }
}
$validation=Get-Content -Raw -LiteralPath "$hub/report_validation.json" | ConvertFrom-Json
if($validation.status -ne 'PASS' -or -not $validation.checks.all_plot_count_axes_ordered -or -not $validation.checks.unsupported_counts_keep_axis_position) { throw 'Chart-axis assertions not PASS' }
$standard='0-0,0-1,0-2,1-0,1-1,1-2,2-0,2-1,2-2,3-0,3-1,3-2'
foreach($axis in $validation.count_axis_checks) {
 if(-not $axis.passed -or (($axis.labels_top_to_bottom -join ',') -ne $standard)) { throw "Bad axis: $($axis.chart)" }
}
if($validation.count_axis_checks.Count -ne ($validation.mobile_charts+4)) { throw 'Missing chart-axis assertions' }
New-Item -ItemType Directory -Path "$reviewDir/after" -ErrorAction Stop | Out-Null
$afterFiles=@()
foreach($entry in $validation.outputs) {
 if((Get-FileHash -LiteralPath $entry.path -Algorithm SHA256).Hash.ToLower() -ne $entry.sha256) { throw "Output changed: $($entry.path)" }
 Copy-Item -LiteralPath $entry.path -Destination "$reviewDir/after" -ErrorAction Stop
 $afterFiles+=@{path=$entry.path; sha256=$entry.sha256; bytes=$entry.bytes}
}
Copy-Item -LiteralPath "$hub/report_validation.json" -Destination "$reviewDir/after" -ErrorAction Stop
Copy-Item -LiteralPath 'tools/render_bcap_history.R' -Destination "$reviewDir/after" -ErrorAction Stop
foreach($path in @("$hub/report_validation.json",'tools/render_bcap_history.R')) {
 $afterFiles+=@{path=$path; sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLower(); bytes=(Get-Item -LiteralPath $path).Length}
}
$oldRows=@(Import-Csv -LiteralPath "$reviewDir/before/summary.csv")
$newRows=@(Import-Csv -LiteralPath "$reviewDir/after/summary.csv")
function RowKey($row) { @($row.model,$row.game_year,$row.level,$row.count,$row.region,$row.pitch_group) -join '|' }
$newIndex=@{}
foreach($row in $newRows) { $key=RowKey $row; if($newIndex.ContainsKey($key)) { throw "Duplicate new key: $key" }; $newIndex[$key]=$row }
foreach($row in $oldRows) {
 $key=RowKey $row
 if(-not $newIndex.ContainsKey($key)) { throw "Missing prior row: $key" }
 if(($row | ConvertTo-Json -Compress -Depth 5) -cne ($newIndex[$key] | ConvertTo-Json -Compress -Depth 5)) { throw "Changed prior row: $key" }
}
$oldValidation=Get-Content -Raw -LiteralPath "$reviewDir/before/report_validation.json" | ConvertFrom-Json
foreach($entry in $oldValidation.inputs) {
 if((Get-FileHash -LiteralPath $entry.path -Algorithm SHA256).Hash.ToLower() -ne $entry.sha256) { throw "Changed original model artifact: $($entry.path)" }
}
$checks=[ordered]@{
 status='PASS'; captured_utc=(Get-Date).ToUniversalTime().ToString('o');
 before_generated_at=$oldValidation.generated_at; after_generated_at=$validation.generated_at;
 before_model_years=$oldValidation.complete_model_years; after_model_years=$validation.complete_model_years;
 old_summary_rows=$oldRows.Count; current_summary_rows=$newRows.Count; overlapping_rows_exactly_unchanged=$oldRows.Count;
 original_input_hashes_unchanged=$oldValidation.inputs.Count;
 chart_axis_checks=$validation.count_axis_checks.Count; all_chart_axes_standard_order=$true; unsupported_3_0_retains_standard_position=$true;
 standard_order_top_to_bottom=$standard.Split(','); inputs=$before.files; after_files=$afterFiles;
 scope='보존한 보고서 사본의 축 순서·집계 불변·원 입력 해시 확인. 이후 자동 갱신 결과에 대한 육안 검수 주장이 아님.'
}
$checks | ConvertTo-Json -Depth 15 | Set-Content -LiteralPath "$reviewDir/snapshot_validation.json" -Encoding utf8
[pscustomobject]$checks | Select-Object status,before_generated_at,after_generated_at,before_model_years,after_model_years,overlapping_rows_exactly_unchanged,original_input_hashes_unchanged,chart_axis_checks | ConvertTo-Json
