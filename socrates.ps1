$ErrorActionPreference = 'Stop'
$betaRoot = $PSScriptRoot
$betaConfigFile = Join-Path $betaRoot 'config\beta\local.json'
if (-not (Test-Path -LiteralPath $betaConfigFile)) { $betaConfigFile = Join-Path $betaRoot 'config\beta\local.example.json' }
$betaConfiguration = Get-Content -LiteralPath $betaConfigFile -Raw | ConvertFrom-Json
$betaAppRoot = if ([IO.Path]::IsPathRooted($betaConfiguration.app_root)) { $betaConfiguration.app_root } else { Join-Path $betaRoot $betaConfiguration.app_root }
$betaCandidates = @($env:SOCRATES_PYTHON, (Join-Path $betaRoot '.venv_beta\Scripts\python.exe'), (Join-Path $betaAppRoot '.venv\Scripts\python.exe'))
$betaPython = $betaCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if (-not $betaPython) { throw 'Configure SOCRATES_PYTHON or install requirements-beta.txt in .venv_beta. See Docs/beta/README.md.' }
$previousBetaPythonPath = $env:PYTHONPATH
$previousBetaLocation = Get-Location
try {
    Set-Location -LiteralPath $betaRoot
    $env:PYTHONPATH = Join-Path $betaRoot 'src'
    & $betaPython -X utf8 -m socrates_beta @args
    $betaResult = $LASTEXITCODE
} finally {
    $env:PYTHONPATH = $previousBetaPythonPath
    Set-Location -LiteralPath $previousBetaLocation.Path
}
exit $betaResult
