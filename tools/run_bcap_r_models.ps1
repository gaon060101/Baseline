param(
    [string]$InputDirectory,
    [string]$InputRds,
    [Parameter(Mandatory=$true)][int[]]$Years,
    [string[]]$Models = @('pitch','pitch_sb','swing','pitch_ff'),
    [string]$Period,
    [int]$ComparisonFamily = 0
)
$ErrorActionPreference = 'Stop'
if ([bool]$InputDirectory -eq [bool]$InputRds) { throw 'Provide exactly one of InputDirectory and InputRds' }
if (-not $Period) { $Period = ($Years | Sort-Object) -join '_' }
$stamp = Get-Date -Format 'yyyyMMdd'
$runRoot = Join-Path $PSScriptRoot '../columns/001-ball-count/analysis/runs'
$configRoot = Join-Path $PSScriptRoot '../models/bcap/r/execution_configs'
New-Item -ItemType Directory -Path $configRoot -Force | Out-Null
foreach ($variant in $Models) {
    if ($variant -notin @('pitch','pitch_sb','swing','pitch_ff')) { throw 'Unknown BCAP model' }
    $revision = 1
    do {
        $runId = 'bcap_{0}_r__mlb_{1}__{2}__r{3:00}' -f $variant,$Period,$stamp,$revision
        $output = Join-Path $runRoot $runId
        $revision++
    } while (Test-Path -LiteralPath $output)
    $config = [ordered]@{ model=$variant; years=@($Years); output_dir=$output }
    if ($InputDirectory) { $config.input_dir=$InputDirectory } else { $config.input_rds=$InputRds }
    if ($ComparisonFamily -gt 0) { $config.comparison_family=$ComparisonFamily }
    $configPath = Join-Path $configRoot ($runId + '.json')
    if (Test-Path -LiteralPath $configPath) { throw "Config already exists: $configPath" }
    $config | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath $configPath -Encoding utf8
    $snapshot = Join-Path $configRoot $runId
    if (Test-Path -LiteralPath $snapshot) { throw "Execution snapshot already exists: $snapshot" }
    New-Item -ItemType Directory -Path $snapshot | Out-Null
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot '../models/bcap/r/run.R') -Destination (Join-Path $snapshot 'run.R')
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot '../models/bcap/r/engine.R') -Destination (Join-Path $snapshot 'engine.R')
    & (Join-Path $PSScriptRoot 'run_r.ps1') -Script (Join-Path $snapshot 'run.R') $configPath
    if ($LASTEXITCODE -ne 0) { throw "BCAP R failed: $runId" }
}
