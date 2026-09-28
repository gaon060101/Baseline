$ErrorActionPreference = 'Stop'
$bcaiRun = 'columns/001-ball-count/analysis/runs/bcai_supplement__mlb_2026_ytd_20260907__20260928__r01'
$supplement = 'columns/001-ball-count/analysis/r_supplement_20260928'
& ./tools/run_r.ps1 -Script "$bcaiRun/execution_snapshot/run.R" "$bcaiRun/config.json"
& ./tools/run_r.ps1 -Script "$supplement/bcap_preparation_snapshot/prepare_raw.R" "$supplement/bcap_preparation_config.json"
& ./tools/run_r.ps1 -Script "$supplement/pitch_execution_snapshot/run.R" "$supplement/pitch_config.json"
& ./tools/run_r.ps1 -Script "$supplement/pitch_ff_execution_snapshot/run.R" "$supplement/pitch_ff_config.json"
