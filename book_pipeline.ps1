$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$pipelineCandidates = @($env:SOCRATES_PYTHON, (Join-Path $projectRoot '.venv_beta\Scripts\python.exe'), (Join-Path (Split-Path $projectRoot) 'Socratic Tutor Main\.venv\Scripts\python.exe'), (Join-Path $projectRoot '.venv\Scripts\python.exe'))
$pipelinePython = $pipelineCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if (-not $pipelinePython) { throw 'Configure SOCRATES_PYTHON or install the project runtime.' }
$previousPythonPath = $env:PYTHONPATH
$previousLocation = Get-Location
try {
    Set-Location -LiteralPath $projectRoot
    $env:PYTHONPATH = Join-Path $projectRoot 'src'
    & $pipelinePython -X utf8 -m ncert_pipeline @args
    $pipelineExit = $LASTEXITCODE
} finally {
    $env:PYTHONPATH = $previousPythonPath
    Set-Location -LiteralPath $previousLocation.Path
}
exit $pipelineExit
