# Run after restarting Windows and completing Ubuntu's first-run account setup.
param([string]$Distribution = 'Ubuntu-24.04')
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '../..')).Path
$bootstrapPath = Join-Path $repoRoot 'scripts/bootstrap_linux.sh'
$distributionNames = ((& wsl.exe --list --quiet) -join "`n") -replace "`0", ''
if ($LASTEXITCODE -ne 0 -or $distributionNames -notmatch "(?m)^$([regex]::Escape($Distribution))\s*$") {
    Write-Host 'Start Ubuntu 24.04 LTS from the Start menu once, create your Linux account, then run this script again.'
    exit 1
}
$linuxPath = & wsl.exe --distribution $Distribution --exec wslpath -a $bootstrapPath
if ($LASTEXITCODE -ne 0) {
    throw 'Ubuntu could not start. Restart Windows first; if it still fails, inspect wsl --status.'
}
$linuxPath = (($linuxPath -join "`n") -replace "`0", '').Trim()
& wsl.exe --distribution $Distribution --exec bash $linuxPath
if ($LASTEXITCODE -ne 0) {
    throw "Linux bootstrap stopped with exit code $LASTEXITCODE. Review the preceding output."
}
