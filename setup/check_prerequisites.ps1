<#
.SYNOPSIS
  Read-only prerequisite check for the Socratic Tutor (Windows, PowerShell 5.1 or 7).

.DESCRIPTION
  Prints PASS / WARN / FAIL / INFO for each prerequisite. Changes nothing, installs nothing,
  needs no administrator rights and makes no network calls. Never prints secret values.
  Exit code: 0 when no required item failed, 1 otherwise.

.PARAMETER Route
  All    (default) check both routes: Docker Compose and local Python.
  Docker check only what Route A (Docker Compose) needs.
  Python check only what Route B (local Python) needs.

.EXAMPLE
  powershell -ExecutionPolicy Bypass -File setup\check_prerequisites.ps1
  powershell -ExecutionPolicy Bypass -File setup\check_prerequisites.ps1 -Route Python
#>
[CmdletBinding()]
param(
    [ValidateSet('All', 'Docker', 'Python')]
    [string]$Route = 'All'
)

$ErrorActionPreference = 'Continue'
$RepoRoot = Split-Path -Parent $PSScriptRoot
$script:Counts = @{ PASS = 0; WARN = 0; FAIL = 0; INFO = 0 }
$CheckPython = $Route -ne 'Docker'
$CheckDocker = $Route -ne 'Python'

function Write-Result {
    param([string]$Status, [string]$Name, [string]$Detail = '')
    $script:Counts[$Status]++
    $color = @{ PASS = 'Green'; WARN = 'Yellow'; FAIL = 'Red'; INFO = 'Gray' }[$Status]
    Write-Host ('[{0}] ' -f $Status) -ForegroundColor $color -NoNewline
    Write-Host ('{0,-26} {1}' -f $Name, $Detail)
}

# Runs a program with a timeout; returns @{ Ok; ExitCode; Out; Err; TimedOut; Missing }.
function Invoke-Tool {
    param([string]$Exe, [string]$Arguments = '', [int]$TimeoutSec = 20, [hashtable]$Env = @{})
    $result = @{ Ok = $false; ExitCode = -1; Out = ''; Err = ''; TimedOut = $false; Missing = $false }
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $Exe
    $psi.Arguments = $Arguments
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true
    $psi.WorkingDirectory = $RepoRoot
    foreach ($k in $Env.Keys) { $psi.EnvironmentVariables[$k] = $Env[$k] }
    try { $p = [System.Diagnostics.Process]::Start($psi) } catch { $result.Missing = $true; $result.Err = $_.Exception.Message; return $result }
    $o = $p.StandardOutput.ReadToEndAsync()
    $e = $p.StandardError.ReadToEndAsync()
    if (-not $p.WaitForExit($TimeoutSec * 1000)) {
        try { $p.Kill() } catch { }
        $result.TimedOut = $true
        return $result
    }
    $p.WaitForExit()
    $result.ExitCode = $p.ExitCode
    $result.Out = ($o.Result -replace "`0", '').Trim()
    $result.Err = ($e.Result -replace "`0", '').Trim()
    $result.Ok = ($p.ExitCode -eq 0)
    return $result
}

function First-Line([string]$Text) { if ($Text) { return ($Text -split "`r?`n")[0].Trim() } return '' }

Write-Host "Socratic Tutor prerequisite check (route: $Route)"
Write-Host "Repository: $RepoRoot"
Write-Host ''

# ---------------------------------------------------------------- repository
if (Test-Path -LiteralPath (Join-Path $RepoRoot 'pyproject.toml')) {
    Write-Result PASS 'Repository' 'pyproject.toml found'
} else {
    Write-Result FAIL 'Repository' "pyproject.toml not found under $RepoRoot; run this script from the cloned repository"
}

# ---------------------------------------------------------------- git
$git = Invoke-Tool 'git' '--version'
if ($git.Ok) {
    Write-Result PASS 'Git' (First-Line $git.Out)
    $branch = Invoke-Tool 'git' 'rev-parse --abbrev-ref HEAD'
    if ($branch.Ok) { Write-Result INFO 'Git branch' (First-Line $branch.Out) }
} else {
    Write-Result FAIL 'Git' 'git not found on PATH (install Git for Windows, then open a new terminal)'
}

# ---------------------------------------------------------------- Python 3.12
$python312 = $null
$pythonDesc = ''
if ($CheckPython) {
    $probe = '-c "import sys; print(\"%d.%d.%d\" % sys.version_info[:3]); print(sys.executable)"'
    $candidates = @(@{ Exe = 'py'; Pre = '-3.12 ' }, @{ Exe = 'python3.12'; Pre = '' }, @{ Exe = 'python'; Pre = '' }, @{ Exe = 'python3'; Pre = '' })
    $other = @()
    foreach ($c in $candidates) {
        $r = Invoke-Tool $c.Exe ($c.Pre + $probe) 15
        if (-not $r.Ok) { continue }
        $lines = $r.Out -split "`r?`n"
        $ver = $lines[0].Trim()
        $exe = if ($lines.Count -gt 1) { $lines[1].Trim() } else { '' }
        if ($ver -like '3.12.*') { $python312 = $exe; $pythonDesc = "$ver via '$($c.Exe) $($c.Pre.Trim())' ($exe)"; break }
        $other += "$ver ($($c.Exe))"
    }
    if ($python312) {
        Write-Result PASS 'Python 3.12' $pythonDesc
    } elseif ($other.Count -gt 0) {
        Write-Result FAIL 'Python 3.12' ("not found; found only: " + (($other | Select-Object -Unique) -join ', ') + '. CI and the Dockerfile use 3.12')
    } else {
        Write-Result FAIL 'Python 3.12' 'not found (install Python 3.12 64-bit; "py -3.12 --version" should answer)'
    }

    # ------------------------------------------------------------ virtual environment
    $venvPy = Join-Path $RepoRoot '.venv\Scripts\python.exe'
    if ($env:VIRTUAL_ENV) { Write-Result INFO 'Active venv' $env:VIRTUAL_ENV }
    if (Test-Path -LiteralPath $venvPy) {
        $v = Invoke-Tool $venvPy '-c "import sys; print(\"%d.%d.%d\" % sys.version_info[:3])"' 15
        if ($v.Ok -and $v.Out -like '3.12.*') {
            Write-Result PASS '.venv' "exists, Python $($v.Out)"
        } elseif ($v.Ok) {
            Write-Result FAIL '.venv' "exists but uses Python $($v.Out); recreate it with 3.12 (see Docs/SETUP.md troubleshooting)"
        } else {
            Write-Result FAIL '.venv' 'exists but its python.exe does not run (broken or moved); recreate it'
        }
    } elseif ($python312) {
        $m = Invoke-Tool $python312 '-c "import venv, ensurepip"' 15
        if ($m.Ok) { Write-Result WARN '.venv' 'not created yet; run setup\install_python_env.ps1' }
        else { Write-Result FAIL '.venv' 'cannot be created: this Python lacks the venv/ensurepip modules' }
    } else {
        Write-Result FAIL '.venv' 'not created, and no Python 3.12 to create it with'
    }

    # ------------------------------------------------------------ packages
    if (Test-Path -LiteralPath $venvPy) {
        # Required: the app, API, UI, beta runtime and tests. Optional: matplotlib (only scripts/beta/render_results.py).
        $mods = 'tutor tutor_api tutor_eval socratic_data socrates_beta ncert_pipeline langgraph langgraph.checkpoint.sqlite langchain_openai fastmcp filelock bm25s sympy fastapi uvicorn prometheus_client httpx pydantic streamlit requests pytest pytest_asyncio'
        $optional = 'matplotlib'
        $code = "import importlib`ndef miss(names):`n    out=[]`n    for m in names.split():`n        try: importlib.import_module(m)`n        except Exception as e: out.append(m+' ('+type(e).__name__+')')`n    return ';'.join(out)`nprint('REQ:'+miss('$mods'))`nprint('OPT:'+miss('$optional'))"
        $tmp = Join-Path ([IO.Path]::GetTempPath()) ('tutor_check_' + [guid]::NewGuid().ToString('N') + '.py')
        Set-Content -LiteralPath $tmp -Value $code -Encoding ASCII
        $imp = Invoke-Tool $venvPy ('"' + $tmp + '"') 120 @{ TUTOR_LLM = 'stub' }
        Remove-Item -LiteralPath $tmp -ErrorAction SilentlyContinue
        $req = (($imp.Out -split "`r?`n") | Where-Object { $_ -like 'REQ:*' } | Select-Object -First 1); $opt = (($imp.Out -split "`r?`n") | Where-Object { $_ -like 'OPT:*' } | Select-Object -First 1)
        $impLines = @(([string]$req -replace '^REQ:', ''), ([string]$opt -replace '^OPT:', ''))
        if ($imp.TimedOut) { Write-Result WARN 'Packages' 'import check timed out' }
        elseif (-not $imp.Ok) { Write-Result FAIL 'Packages' ('import check failed: ' + (First-Line $imp.Err)) }
        elseif ($impLines[0].Trim()) { Write-Result FAIL 'Packages' ("missing: $($impLines[0].Trim()). Run setup\install_python_env.ps1") }
        else { Write-Result PASS 'Packages' 'application, API, UI, beta-runtime and test packages import' }
        if ($imp.Ok -and $impLines[1].Trim()) { Write-Result WARN 'Optional packages' ("missing: $($impLines[1].Trim()) (only for scripts/beta/render_results.py; in requirements-beta-dev.txt)") }

        $pc = Invoke-Tool $venvPy '-m pip check' 60
        if ($pc.Ok) { Write-Result PASS 'pip check' (First-Line $pc.Out) }
        else { Write-Result WARN 'pip check' (First-Line ($pc.Out + ' ' + $pc.Err)) }

        if (Test-Path -LiteralPath (Join-Path $RepoRoot '.venv\Scripts\tutor.exe')) { Write-Result PASS 'tutor command' '.venv\Scripts\tutor.exe present' }
        else { Write-Result FAIL 'tutor command' 'not installed in .venv; run setup\install_python_env.ps1' }
    } else {
        Write-Result WARN 'Packages' 'skipped: no .venv yet'
    }
}

# ---------------------------------------------------------------- Windows virtualization and WSL 2
if ($CheckDocker) {
    $cs = $null
    try { $cs = Get-CimInstance Win32_ComputerSystem -ErrorAction Stop } catch { }
    if ($cs -and $cs.HypervisorPresent) {
        Write-Result PASS 'Virtualization' 'hypervisor is running'
    } else {
        $fw = $null
        try { $fw = (Get-CimInstance Win32_Processor -ErrorAction Stop | Select-Object -First 1).VirtualizationFirmwareEnabled } catch { }
        if ($fw -eq $false) { Write-Result FAIL 'Virtualization' 'disabled in firmware: enable Intel VT-x / AMD-V (SVM) in BIOS/UEFI' }
        elseif ($cs) { Write-Result FAIL 'Virtualization' 'no hypervisor running: enable Virtual Machine Platform (install WSL), then restart Windows' }
        else { Write-Result WARN 'Virtualization' 'could not query Win32_ComputerSystem' }
    }

    $pending = (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Component Based Servicing\RebootPending') -or
               (Test-Path 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update\RebootRequired')
    if ($pending) { Write-Result WARN 'Pending restart' 'Windows reports a restart is pending; restart before starting Docker Desktop' }

    $wslEnv = @{ WSL_UTF8 = '1' }
    $wv = Invoke-Tool 'wsl' '--version' 20 $wslEnv
    if ($wv.Missing) {
        Write-Result FAIL 'WSL 2' 'wsl.exe not found; run "wsl --install" in an administrator terminal, then restart'
    } elseif ($wv.Ok) {
        Write-Result PASS 'WSL 2' (First-Line $wv.Out)
        $wl = Invoke-Tool 'wsl' '-l -v' 20 $wslEnv
        if ($wl.Ok) {
            $dd = ($wl.Out -split "`r?`n") | Where-Object { $_ -match 'docker-desktop' } | Select-Object -First 1
            if ($dd -and $dd -match '\s2\s*$') { Write-Result PASS 'WSL docker-desktop' (($dd -replace '\s+', ' ').Trim()) }
            elseif ($dd) { Write-Result WARN 'WSL docker-desktop' "not on WSL 2: $(($dd -replace '\s+', ' ').Trim())" }
            else { Write-Result INFO 'WSL docker-desktop' 'distribution not present yet (Docker Desktop creates it on first start)' }
        }
    } else {
        Write-Result FAIL 'WSL 2' ('"wsl --version" failed (inbox WSL 1 or not installed): ' + (First-Line ($wv.Out + ' ' + $wv.Err)) + '. Run "wsl --install" or "wsl --update"')
    }

    # ------------------------------------------------------------ Docker
    $dv = Invoke-Tool 'docker' 'version --format "{{.Client.Version}}"' 20
    if ($dv.Missing) {
        Write-Result FAIL 'Docker CLI' 'docker not found on PATH (install Docker Desktop, then open a new terminal)'
    } else {
        if ($dv.Out) { Write-Result PASS 'Docker CLI' ("client " + (First-Line $dv.Out)) }
        else { Write-Result PASS 'Docker CLI' 'found' }
        $di = Invoke-Tool 'docker' 'info --format "{{.ServerVersion}} {{.OperatingSystem}}"' 30
        if ($di.TimedOut) { Write-Result FAIL 'Docker engine' 'no answer within 30 s (Docker Desktop still starting or hung)' }
        elseif ($di.Ok -and $di.Out) { Write-Result PASS 'Docker engine' ("server " + (First-Line $di.Out)) }
        else { Write-Result FAIL 'Docker engine' 'not responding: start Docker Desktop and wait for "Engine running" (see Docs/SETUP.md troubleshooting)' }

        $dc = Invoke-Tool 'docker' 'compose version --short' 20
        if ($dc.Ok -and $dc.Out) { Write-Result PASS 'Docker Compose v2+' ("docker compose " + (First-Line $dc.Out)) }
        else {
            $legacy = Invoke-Tool 'docker-compose' 'version --short' 20
            if ($legacy.Ok) { Write-Result FAIL 'Docker Compose v2+' "only legacy docker-compose $(First-Line $legacy.Out); the guide uses 'docker compose' (update Docker Desktop)" }
            else { Write-Result FAIL 'Docker Compose v2+' "'docker compose' subcommand not available" }
        }
    }
}

# ---------------------------------------------------------------- ports
$listeners = @()
try { $listeners = @(Get-NetTCPConnection -State Listen -ErrorAction Stop) } catch { $listeners = $null }
foreach ($port in 8000, 8501) {
    $owners = @()
    if ($null -ne $listeners) {
        $owners = @($listeners | Where-Object { $_.LocalPort -eq $port } | ForEach-Object {
            $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
            if ($proc) { $proc.ProcessName } else { "pid $($_.OwningProcess)" }
        } | Select-Object -Unique)
    } else {
        $l = $null
        try { $l = New-Object System.Net.Sockets.TcpListener([Net.IPAddress]::Any, $port); $l.Start() } catch { $owners = @('unknown process') }
        finally { if ($l) { $l.Stop() } }
    }
    if ($owners.Count -eq 0) { Write-Result PASS "Port $port" 'free' }
    elseif ($owners -match 'docker|wslrelay|vpnkit') { Write-Result WARN "Port $port" ("in use by " + ($owners -join ', ') + ': probably the tutor stack is already running ("docker compose ps")') }
    else { Write-Result WARN "Port $port" ("in use by " + ($owners -join ', ') + '; stop it before starting the API/UI') }
}

# ---------------------------------------------------------------- .env (never print values)
$envFile = Join-Path $RepoRoot '.env'
if (Test-Path -LiteralPath $envFile) {
    $ignored = Invoke-Tool 'git' 'check-ignore -q .env'
    $tracked = Invoke-Tool 'git' 'ls-files --error-unmatch .env'
    if ($tracked.Ok) { Write-Result FAIL '.env' 'is TRACKED by git: remove it from the index and rotate the key' }
    elseif ($git.Ok -and -not $ignored.Ok) { Write-Result FAIL '.env' 'present but NOT git-ignored; check .gitignore before committing anything' }
    else {
        $keyLine = Get-Content -LiteralPath $envFile -ErrorAction SilentlyContinue | Where-Object { $_ -match '^\s*LLM_API_KEY\s*=' } | Select-Object -First 1
        $state = if (-not $keyLine) { 'no LLM_API_KEY line' } elseif ($keyLine -match '^\s*LLM_API_KEY\s*=\s*\S') { 'LLM_API_KEY is set (value not shown)' } else { 'LLM_API_KEY is empty' }
        Write-Result PASS '.env' "present and git-ignored; $state. Optional: only needed for a live model"
    }
} else {
    Write-Result INFO '.env' 'absent: fine, the tutor uses the offline stub. Copy .env.example to .env only for a live model'
}
if (Test-Path -LiteralPath (Join-Path $RepoRoot '.env.txt')) { Write-Result WARN '.env.txt' 'found: Notepad added .txt; rename it to .env' }

# ---------------------------------------------------------------- disk
try {
    $drive = (Get-Item -LiteralPath $RepoRoot).PSDrive
    $freeGb = [math]::Round($drive.Free / 1GB, 1)
    $need = if ($CheckDocker) { 10 } else { 2 }
    if ($freeGb -ge $need) { Write-Result PASS 'Disk space' "$freeGb GB free on $($drive.Name):" }
    else { Write-Result WARN 'Disk space' "$freeGb GB free on $($drive.Name): (recommend at least $need GB)" }
} catch { }

Write-Host ''
Write-Host ("Summary: {0} PASS, {1} WARN, {2} FAIL" -f $Counts.PASS, $Counts.WARN, $Counts.FAIL)
if ($Counts.FAIL -gt 0) {
    Write-Host 'Fix the FAIL items (Docs/SETUP.md, Troubleshooting), then run this check again.' -ForegroundColor Red
    exit 1
}
Write-Host 'Required prerequisites are in place.' -ForegroundColor Green
exit 0
