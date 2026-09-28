$ErrorActionPreference='Stop'
$dir='columns/001-ball-count/analysis/r_bcap_history_20260928/figure_review_2019_20260928T045736Z'
$snapshot=Get-Content -Raw -LiteralPath "$dir/snapshot_manifest.json" | ConvertFrom-Json
$validation=Get-Content -Raw -LiteralPath "$dir/snapshot/report_validation.json" | ConvertFrom-Json
foreach($file in $snapshot.files) {
 if((Get-FileHash -LiteralPath $file.saved -Algorithm SHA256).Hash.ToLower() -ne $file.sha256) { throw "Snapshot changed: $($file.saved)" }
}
$results=@()
foreach($run in Get-ChildItem -LiteralPath "$dir/snapshot" -Directory) {
 $m=Get-Content -Raw -LiteralPath "$($run.FullName)/manifest.json" | ConvertFrom-Json
 $mt=Get-Content -Raw -LiteralPath "$($run.FullName)/metrics.json" | ConvertFrom-Json
 $checks=Get-Content -Raw -LiteralPath "$($run.FullName)/checks.json" | ConvertFrom-Json
 $rows=@(Import-Csv -LiteralPath "$($run.FullName)/year_values.csv")
 $counts=@($rows | Where-Object { $_.level -eq 'count' })
 $overall=@($rows | Where-Object { $_.level -eq 'overall' })[0]
 $cfg=$m.configuration
 if($m.status -ne 'COMPLETE' -or $checks.status -ne 'PASS' -or @($checks.checks | Where-Object { $_.status -ne 'PASS' }).Count -ne 0 -or -not $mt.all_fit_converged) { throw 'Saved status not PASS' }
 if($counts.Count -ne 12 -or [long]$overall.n_all -ne [long]$mt.n -or [long]$overall.n -ne [long]$mt.support) { throw 'Denominator mismatch' }
 if(($counts | Measure-Object -Property n -Sum).Sum -ne [long]$overall.n -or ($counts | Measure-Object -Property n_all -Sum).Sum -ne [long]$overall.n_all) { throw 'Count totals mismatch' }
 $maxIdentity=0.0
 foreach($r in $rows) {
  $gate=([double]$r.n -ge $cfg.min_rows -and [Math]::Min([double]$r.ESS0,[double]$r.ESS1) -ge $cfg.min_ess -and [Math]::Min([double]$r.games0,[double]$r.games1) -ge $cfg.min_arm_games -and [double]$r.coverage -ge $cfg.min_coverage -and [Math]::Max([double]$r.max_game_share0,[double]$r.max_game_share1) -le $cfg.max_game_share)
  if($gate -ne ($r.support_gate -eq 'TRUE')) { throw 'Support flag mismatch' }
  $expectedEvidence=if(-not $gate){'비교 자료 부족'}elseif([double]$r.family95_low -le 0 -and [double]$r.family95_high -ge 0){'차이 불명확'}else{'관찰상 방향 뚜렷'}
  if($r.evidence -ne $expectedEvidence) { throw 'Evidence label mismatch' }
  if(-not $gate -and -not [string]::IsNullOrEmpty($r.point_direction)) { throw 'Unsupported point direction displayed' }
  if(-not [string]::IsNullOrEmpty($r.recommendation)) { throw 'Unexpected action recommendation' }
  if([long]$r.rows0+[long]$r.rows1 -ne [long]$r.n) { throw 'Action denominator mismatch' }
  if($r.delta -ne '' -and $r.Q0 -ne '' -and $r.Q1 -ne '') {
   $contrastError=[Math]::Abs([double]$r.Q1-[double]$r.Q0-[double]$r.delta)
   $maxIdentity=[Math]::Max($maxIdentity,$contrastError)
   if($contrastError -gt 1e-10) { throw 'Q contrast mismatch' }
  }
 }
 $chart="$($m.run_config.model)_2019_count_mobile.png"
 $axis=@($validation.count_axis_checks | Where-Object { $_.chart -eq $chart })
 if($axis.Count -ne 1 -or -not $axis[0].passed -or ($axis[0].labels_top_to_bottom -join ',') -ne '0-0,0-1,0-2,1-0,1-1,1-2,2-0,2-1,2-2,3-0,3-1,3-2') { throw 'Count axis mismatch' }
 $png=@($snapshot.files | Where-Object { [IO.Path]::GetFileName($_.saved) -eq $chart })[0]
 $results+=[pscustomobject]@{model=$m.run_config.model;model_id=$m.model_id;run_id=$m.run_id;status='PASS';saved_checks=$checks.checks.Count;saved_fit_convergence=$mt.all_fit_converged;saved_fit_logs=$mt.fit_logs;eligible_rows=$mt.n;support_rows=$mt.support;support_coverage=$mt.coverage;supported_games=[long]$overall.games;eligible_games=$mt.games;primary_counts=$counts.Count;supported_primary_counts=@($counts | Where-Object { $_.support_gate -eq 'TRUE' }).Count;summary_groups=$rows.Count;unsupported_groups=@($rows | Where-Object { $_.support_gate -eq 'FALSE' }).Count;support_gates_match=$true;evidence_labels_match=$true;Q_difference_max_abs_error=$maxIdentity;count_axis_matches=$true;family=$cfg.comparison_family;scope=$checks.scope;viewed_png=$png.saved;viewed_png_sha256=$png.sha256}
}
$record=[ordered]@{status='PASS';reviewed_utc=(Get-Date).ToUniversalTime().ToString('o');snapshot_report_generated_at=$snapshot.report_generated_at;snapshot_report_validation_sha256=$snapshot.report_validation_sha256;reviewed_year=2019;models=$results;scope='저장된 2019년 4개 실행의 검사·수렴 플래그·232개 집계행 지원 판정과 해석 라벨을 확인하고 모바일 PNG 4장을 실제 열람함. 원 점수 재계산·재적합·전체 통계 타당성 검증은 수행하지 않음. 이후 자동 갱신과 2018년 결과는 이 검수 범위 밖.';verification_retry_note='첫 조회 명령은 PowerShell 예약 변수 Error 충돌로 중단됐다. 통계·보고서 파일 쓰기 전에 발생했고, 변수명을 contrastError로 수정한 현재 검증은 PASS다.'}
$record | ConvertTo-Json -Depth 12 | Set-Content -LiteralPath "$dir/qa_validation.json" -Encoding utf8
$results | Select-Object model,saved_checks,saved_fit_convergence,eligible_rows,support_rows,primary_counts,supported_primary_counts,summary_groups,unsupported_groups | ConvertTo-Json -Depth 4
