param(
    [Parameter(Mandatory = $true)][string]$Script,
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$ScriptArguments
)
$ErrorActionPreference = 'Stop'
$candidates = @()
if ($env:BASELINE_RSCRIPT) { $candidates += $env:BASELINE_RSCRIPT }
$command = Get-Command Rscript.exe -ErrorAction SilentlyContinue
if ($command) { $candidates += $command.Source }
foreach ($registryPath in @('HKCU:\Software\R-core\R', 'HKLM:\Software\R-core\R')) {
    $entry = Get-ItemProperty $registryPath -ErrorAction SilentlyContinue
    if ($entry.InstallPath) { $candidates += Join-Path $entry.InstallPath 'bin\Rscript.exe' }
}
foreach ($root in @("$env:LOCALAPPDATA\Programs\R", "$env:ProgramFiles\R")) {
    if (Test-Path -LiteralPath $root) {
        $candidates += Get-ChildItem -LiteralPath $root -Directory |
            Sort-Object Name -Descending | ForEach-Object { Join-Path $_.FullName 'bin\Rscript.exe' }
    }
}
$rscriptPath = $candidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $rscriptPath) { throw 'Rscript.exe not found. Install R or set BASELINE_RSCRIPT.' }
# Codex may provide Linux locale names that Windows R cannot resolve.
# Adjust only this invocation and restore the parent process environment.
$localeNames = @('LANG', 'LC_ALL', 'LC_CTYPE')
$savedLocales = @{}
foreach ($name in $localeNames) {
    $savedLocales[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
    [Environment]::SetEnvironmentVariable($name, $null, 'Process')
}
try {
    & $rscriptPath --vanilla $Script @ScriptArguments
    if ($LASTEXITCODE -ne 0) { throw "R exited with code $LASTEXITCODE" }
} finally {
    foreach ($name in $localeNames) {
        [Environment]::SetEnvironmentVariable($name, $savedLocales[$name], 'Process')
    }
}
