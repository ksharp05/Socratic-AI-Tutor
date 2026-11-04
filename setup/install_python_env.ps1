<#
.SYNOPSIS
  Creates the repository's .venv with Python 3.12 and installs every Python dependency (Windows).

.DESCRIPTION
  Idempotent: safe to run again after a git pull. Touches only <repo>\.venv; no system changes,
  no administrator rights. Downloads packages from PyPI (network needed). Makes no model calls.

  Installs:  pip install -e ".[dev,api,ui]" -r requirements-beta-dev.txt   (plus "retrieval" with -WithRetrieval)
  Then runs: pip check, an import check and "tutor --help".

.PARAMETER Python
  Path to a Python 3.12 interpreter to use instead of searching (py -3.12, python3.12, python, python3).

.PARAMETER WithRetrieval
  Also install the optional "retrieval" extra (fastembed, dense vectors for hybrid retrieval).

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File setup\install_python_env.ps1
#>
[CmdletBinding()]
param(
    [string]$Python = '',
    [switch]$WithRetrieval
)

$ErrorActionPreference = 'Continue'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$Venv = Join-Path $RepoRoot '.venv'
$VenvPy = Join-Path $Venv 'Scripts\python.exe'

function Fail([string]$Message) { Write-Host "ERROR: $Message" -ForegroundColor Red; exit 1 }
function Step([string]$Message) { Write-Host ''; Write-Host "==> $Message" -ForegroundColor Cyan }

function Get-PyVersion([string]$Exe, [string[]]$Pre) {
    try {
        $out = & $Exe @Pre -c "import sys; print('%d.%d.%d' % sys.version_info[:3]); print(sys.executable)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $out) { return @{ Version = ([string]$out[0]).Trim(); Exe = ([string]$out[1]).Trim() } }
    } catch { }
    return $null
}

if (-not (Test-Path -LiteralPath (Join-Path $RepoRoot 'pyproject.toml'))) { Fail "pyproject.toml not found under $RepoRoot" }
Set-Location -LiteralPath $RepoRoot

# ---------------------------------------------------------------- find Python 3.12
Step 'Finding Python 3.12'
$found = $null
if ($Python) {
    $found = Get-PyVersion $Python @()
    if (-not $found) { Fail "cannot run '$Python'" }
} else {
    foreach ($c in @(@('py', '-3.12'), @('python3.12'), @('python'), @('python3'))) {
        $pre = @(); if ($c.Count -gt 1) { $pre = @($c[1]) }
        $v = Get-PyVersion $c[0] $pre
        if ($v -and $v.Version -like '3.12.*') { $found = $v; break }
    }
}
if (-not $found -or $found.Version -notlike '3.12.*') {
    Fail 'Python 3.12 not found. Install Python 3.12 (64-bit) from python.org or "winget install --id Python.Python.3.12 -e", open a new terminal and run this again.'
}
Write-Host "Using Python $($found.Version): $($found.Exe)"

# ---------------------------------------------------------------- create or reuse .venv
if (Test-Path -LiteralPath $VenvPy) {
    $existing = Get-PyVersion $VenvPy @()
    if (-not $existing) { Fail ".venv exists but $VenvPy does not run. Delete .venv yourself (Remove-Item -Recurse -Force .venv) and run this again." }
    if ($existing.Version -notlike '3.12.*') { Fail ".venv uses Python $($existing.Version), not 3.12. Delete it yourself (Remove-Item -Recurse -Force .venv) and run this again." }
    Step "Reusing existing .venv (Python $($existing.Version))"
} else {
    if (Test-Path -LiteralPath $Venv) { Fail '.venv exists but has no Scripts\python.exe (not a Windows venv?). Move or delete it, then run this again.' }
    Step 'Creating .venv'
    & $found.Exe -m venv $Venv
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $VenvPy)) { Fail 'python -m venv failed' }
}

# ---------------------------------------------------------------- install
$env:PIP_DISABLE_PIP_VERSION_CHECK = '1'
Step 'Upgrading pip inside .venv'
& $VenvPy -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { Fail 'pip upgrade failed (network or proxy? see Docs/SETUP.md troubleshooting)' }

$extras = 'dev,api,ui'
if ($WithRetrieval) { $extras += ',retrieval' }
Step "Installing the project: pip install -e "".[$extras]"" -r requirements-beta-dev.txt"
& $VenvPy -m pip install -e ".[$extras]" -r requirements-beta-dev.txt
if ($LASTEXITCODE -ne 0) { Fail 'pip install failed; scroll up for the first red ERROR line' }

# ---------------------------------------------------------------- verify
Step 'pip check'
& $VenvPy -m pip check
if ($LASTEXITCODE -ne 0) { Fail 'pip check reported conflicting requirements' }

Step 'Import check'
$env:TUTOR_LLM = 'stub'
& $VenvPy -c "import tutor, tutor_api, tutor_eval, socratic_data, socrates_beta, ncert_pipeline, fastapi, uvicorn, streamlit, pytest; print('imports ok')"
if ($LASTEXITCODE -ne 0) { Fail 'import check failed' }

$tutorExe = Join-Path $Venv 'Scripts\tutor.exe'
$help = & $tutorExe --help
if ($LASTEXITCODE -ne 0) { Fail 'tutor --help failed' }
$help | Select-Object -First 2

Write-Host ''
Write-Host 'Python environment ready.' -ForegroundColor Green
Write-Host 'Next, in this terminal:'
Write-Host '  .venv\Scripts\Activate.ps1      # once per terminal'
Write-Host '  pytest -q                       # offline tests, no key or private data needed'
Write-Host '  tutor setup                     # seed demo learners A and B'
Write-Host '  powershell -ExecutionPolicy Bypass -File setup\check_prerequisites.ps1 -Route Python'
exit 0
