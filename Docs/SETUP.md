# Setup guide: install the prerequisites and run the Socratic Tutor

One guide for a fresh machine. Windows 11 is covered step by step; macOS and Linux have short notes. Nothing here needs an API key or private data unless a step says so.

There are two ways to run the tutor. You can do either or both:

| Route | What you get | Needs |
| --- | --- | --- |
| **A. Docker Compose** | The API (port 8000) and the Streamlit web UI (port 8501) in containers | Git, Docker Desktop (Windows: also WSL 2 and virtualization) |
| **B. Local Python** | The `tutor` command line, the tests, the API and UI run directly | Git, Python 3.12 |

Developers need Route B for the tests. Route A is the quickest way to see the app in a browser.

**Two scripts do most of the work** (both in `setup/`):

- `check_prerequisites.ps1` / `.sh`: read-only. Prints PASS, WARN or FAIL for every prerequisite below and exits non-zero if something required is missing. Run it first, and again after each fix.
- `install_python_env.ps1` / `.sh`: creates `.venv` with Python 3.12 and installs every Python dependency (Route B). Safe to run again after a `git pull`.

Neither script needs administrator rights or changes anything outside the repository's `.venv`.

## Contents

1. [Requirements](#1-requirements)
2. [Get access and clone](#2-get-access-and-clone)
3. [Run the prerequisite check](#3-run-the-prerequisite-check)
4. [Route A: Docker Compose](#4-route-a-docker-compose)
5. [Route B: local Python](#5-route-b-local-python)
6. [Optional: a live model with your own key](#6-optional-a-live-model-with-your-own-key)
7. [What needs private data](#7-what-needs-private-data)
8. [Troubleshooting](#8-troubleshooting)
9. [Every time you come back](#9-every-time-you-come-back)

## 1. Requirements

Versions in the last column are the ones this project was installed and tested with in November 2026.

| Prerequisite | Needed for | Required version | Tested with |
| --- | --- | --- | --- |
| Git | Both routes | any 2.x | 2.45.1 (Windows) |
| Python | Route B | **3.12.x** (CI and the Dockerfile use 3.12; 3.13+ is untested and may compile packages from source) | 3.12.10 |
| Docker Desktop (or Docker Engine on Linux) | Route A | Compose v2 or later, run as `docker compose` | Desktop 4.98.0, Engine 29.9.2, Compose 5.6.1 |
| WSL 2 | Route A on Windows | WSL 2 (the Store/MSI WSL, not the old inbox WSL 1) | 2.7.14.0 |
| Hardware virtualization | Route A on Windows | Enabled in BIOS/UEFI, Virtual Machine Platform on | |
| Free ports | Both | 8000 (API) and 8501 (UI) | |
| Disk | Both | about 1 GB for `.venv`; several GB more for Docker images and WSL | |
| Internet | Install only | PyPI and Docker Hub (`python:3.12-slim`) | |
| A course API key | Optional, live model only | personal OpenRouter key | |

Pinned Python packages come from `pyproject.toml` (extras `dev`, `api`, `ui`) and `requirements-beta-dev.txt` (which includes `requirements-beta.txt`). You never install them by hand: the install script or the Dockerfile does it.

## 2. Get access and clone

The repository is private. Send Lakshya your GitHub username in the team group and accept the invitation email (or open [github.com/ksharp05/Socratic-AI-Tutor/invitations](https://github.com/ksharp05/Socratic-AI-Tutor/invitations) while signed in).

### Install Git (and Python 3.12 for Route B)

**Windows.** Either use the installers (Git: [git-scm.com/downloads/win](https://git-scm.com/downloads/win), accept the defaults; Python: [python.org/downloads/windows](https://www.python.org/downloads/windows/), the latest **3.12** "Windows installer (64-bit)", tick **Add python.exe to PATH**), or in PowerShell:

```powershell
winget install --id Git.Git -e
winget install --id Python.Python.3.12 -e
```

Close and reopen PowerShell afterwards. Check with `git --version` and `py -3.12 --version`.

**macOS:** `brew install git python@3.12` (Homebrew from [brew.sh](https://brew.sh/)). **Ubuntu 24.04 / Debian:** `sudo apt install -y git python3.12 python3.12-venv`. Check with `python3.12 --version`.

### Clone

Clone into your home folder, not OneDrive or iCloud (syncing breaks virtual environments). Current work is on the `milestone-2` branch:

```powershell
cd $HOME
git clone --branch milestone-2 https://github.com/ksharp05/Socratic-AI-Tutor.git
cd Socratic-AI-Tutor
```

On Windows the first clone opens a "Connect to GitHub" window: choose **Sign in with your browser**. On macOS/Linux, run `gh auth login` first (GitHub CLI; choose HTTPS and "Login with a web browser").

**Every command below runs inside the `Socratic-AI-Tutor` folder.**

## 3. Run the prerequisite check

Windows (PowerShell; `-ExecutionPolicy Bypass` applies only to this one command and changes no settings):

```powershell
powershell -ExecutionPolicy Bypass -File setup\check_prerequisites.ps1
```

macOS, Linux or Git Bash:

```bash
bash setup/check_prerequisites.sh
```

Add `-Route Docker` / `-Route Python` (PowerShell) or `--docker` / `--python` (bash) to check only one route. It checks: Git; Python 3.12; `.venv` (present, or creatable); every required package importing from `.venv`; `pip check`; the `tutor` command; Docker CLI, a responding engine and `docker compose`; on Windows also virtualization, a pending restart, WSL 2 and the `docker-desktop` WSL distribution; ports 8000 and 8501; and whether `.env` exists and is git-ignored. It never prints the contents of `.env`.

Example output on a machine with everything installed and the Compose stack already running (shortened):

```text
[PASS] Python 3.12                3.12.10 via 'py -3.12' (...\Python312\python.exe)
[PASS] Packages                   application, API, UI, beta-runtime and test packages import
[PASS] Virtualization             hypervisor is running
[PASS] WSL 2                      WSL version: 2.7.14.0
[PASS] Docker engine              server 29.9.2 Docker Desktop
[PASS] Docker Compose v2+         docker compose 5.6.1
[WARN] Port 8000                  in use by wslrelay, com.docker.backend: probably the tutor stack is already running ("docker compose ps")
Summary: 15 PASS, 3 WARN, 0 FAIL
```

FAIL lines tell you what to install next. Fix them with the route sections below and run the check again. WARN lines are advisory.

## 4. Route A: Docker Compose

### 4a. Install Docker Desktop on Windows

Do these in order. Steps 2 and 3 need an administrator account (the setup scripts themselves never do).

1. **Check virtualization.** Task Manager, Performance, CPU: "Virtualization: Enabled". If it says Disabled, enable Intel VT-x or AMD-V/SVM in your BIOS/UEFI settings (the key at boot varies by laptop maker).
2. **Install WSL 2.** In an **administrator** PowerShell:

   ```powershell
   wsl --install --no-distribution
   ```

   This also turns on the Virtual Machine Platform feature. **Restart Windows** afterwards; Docker will not start until you do. If WSL is already installed, run `wsl --update` instead. Check after the restart: `wsl --version` prints `WSL version: 2.x`.
3. **Install Docker Desktop** from [docs.docker.com/desktop/setup/install/windows-install](https://docs.docker.com/desktop/setup/install/windows-install/). Right-click the installer and choose **Run as administrator**, and keep **Use WSL 2 instead of Hyper-V** selected. (A per-user install without elevation failed to start on our test machine; see [Troubleshooting](#8-troubleshooting).) Sign out or restart if the installer asks.
4. **Start Docker Desktop** from the Start menu, accept its terms if they apply to you, and wait until it shows **Engine running**. Signing in to a Docker account is not needed.
5. **Check:** `docker version` must show both a Client and a Server section; `docker compose version` must answer; `wsl -l -v` lists `docker-desktop` with VERSION 2. Or rerun the check script with `-Route Docker`.

**macOS:** install Docker Desktop for Mac from docs.docker.com and start it. **Linux:** install Docker Engine and the `docker-compose-plugin` package from docs.docker.com, and add yourself to the `docker` group (log out and in). No WSL step on either.

### 4b. Run the stack

```powershell
docker compose up --build --wait
```

The first build downloads `python:3.12-slim` and the pinned packages; on our test machine the whole build-and-start took about 66 seconds. `--wait` returns once both containers report healthy. No `.env` is needed: Compose uses the offline stub model unless you opt in (section 6).

| Open | What |
| --- | --- |
| [http://localhost:8501](http://localhost:8501) | Streamlit UI. Enter an access token in the sidebar |
| [http://localhost:8000/health](http://localhost:8000/health) | API health (`"status": "ok"`) |
| [http://localhost:8000/docs](http://localhost:8000/docs) | Interactive API documentation |

**Tokens.** When `TUTOR_API_TOKENS` is unset, the API accepts the public development tokens `dev-student-a`, `dev-student-b` (students L-A, L-B) and `dev-teacher` (teacher T-001), and logs a warning. To use your own local tokens instead, set them before `up`:

```powershell
$env:TUTOR_API_TOKENS = 'local-student:student:L-DEMO,local-teacher:teacher:T-DEMO'
docker compose up --build --wait
```

(bash: `export TUTOR_API_TOKENS='local-student:student:L-DEMO,local-teacher:teacher:T-DEMO'`). The format is comma-separated `token:role:id`. These are development tokens only; never expose a server that uses them. Details: [deployment guide](deploy/README.md#tokens).

**Try it** (use the tokens that match how you started the stack):

| Step | Default tokens (`TUTOR_API_TOKENS` unset) | Local tokens (set as above) |
| --- | --- | --- |
| 1. Open http://localhost:8501 and type the token into **Access token** in the sidebar | `dev-teacher` | `local-teacher` |
| 2. On **Approvals**, propose a set for concept `qe04` (mode `practice`), review it and approve it | | |
| 3. Change the token to a student | `dev-student-a` | `local-student` |
| 4. On **Chat**, type `practice`, then try `hint`, a wrong answer such as `x = 999`, or a question such as "What should I practise next?" | | |
| 5. Back as the teacher, open **Session trace** and paste the student's conversation reference | | |

A student only gets questions after a teacher has approved a set; approve a `quiz`-mode set too if you want to try `start a quiz`. Set `TUTOR_CONTEXTUAL_HINTS=1` (and a key, section 6) for model-written hints and replies; the default is templates only.

| Task | Command |
| --- | --- |
| Status | `docker compose ps` |
| Logs | `docker compose logs -f api` (or `ui`) |
| Stop, keep data | `docker compose down` |
| Stop and delete the learner data volume | `docker compose down -v` |
| Also Prometheus (9090) and Grafana (3000) | `docker compose --profile ops up --build --wait` (not yet verified) |

The integrated overlay (`docker-compose.integrated.yml`) mounts a prepared textbook index and needs private data: see [section 7](#7-what-needs-private-data).

## 5. Route B: local Python

### 5a. Install

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File setup\install_python_env.ps1
```

macOS, Linux or Git Bash:

```bash
bash setup/install_python_env.sh
```

The script finds Python 3.12 (`py -3.12`, `python3.12`, `python` or `python3`; pass `-Python C:\path\python.exe` or `PYTHON=/path/python3.12` to choose), creates `.venv` if it is missing, and runs, inside `.venv`:

```text
python -m pip install --upgrade pip
python -m pip install -e ".[dev,api,ui]" -r requirements-beta-dev.txt
python -m pip check
```

then an import check and `tutor --help`. It took about 3 minutes on a fresh clone and 11 seconds when rerun. Add `-WithRetrieval` / `--with-retrieval` for the optional dense-retrieval extra (`fastembed`). If `.venv` already exists with a different Python version, the script stops and tells you to delete it yourself.

To do the same by hand: `py -3.12 -m venv .venv` (macOS/Linux: `python3.12 -m venv .venv`), activate it, then the `pip install` lines above.

### 5b. Activate (every new terminal)

| Terminal | Command |
| --- | --- |
| Windows PowerShell | `.venv\Scripts\Activate.ps1` |
| Windows Command Prompt | `.venv\Scripts\activate.bat` |
| Git Bash | `source .venv/Scripts/activate` |
| macOS, Linux | `source .venv/bin/activate` |

Your prompt then starts with `(.venv)`. If PowerShell says "running scripts is disabled on this system", run `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` once (affects only your user account), or use Command Prompt, or call `.venv\Scripts\python.exe` directly.

### 5c. Run the tests

```bash
pytest -q
```

Runs the `tests/` folder offline, with no key and no private data. On 5 November 2026 a fresh clone of `milestone-2` gave **325 passed** in about 2 minutes on Windows. The count grows as tests are added; any `F` or `E` is a failure.

CI (`.github/workflows/ci.yml`) also runs these, all offline:

```bash
pytest -q tests_beta/test_portable_registry.py
python -m tutor_eval.harness --config eval/configs/m2_development_c1.toml
python -m tutor_eval.harness --config eval/configs/dev_smoke.toml
python -m tutor_eval.security --cases eval/fixtures/security_smoke.jsonl --name ci_security --gate
```

Set `TUTOR_LLM=stub` first if you have a key in `.env` (PowerShell: `$env:TUTOR_LLM='stub'`; bash: `export TUTOR_LLM=stub`), as CI does. The other test folders need private data (section 7).

### 5d. Run the tutor

Command line (no key needed; replies come from templates):

```bash
tutor setup
tutor ask --learner A "I solved x^2 = 5x by dividing both sides by x and got x = 5. Why is there another answer?"
tutor chat --learner A
```

`tutor setup` resets local state in `var/` and seeds demo learners A and B. In `chat`, type `practice`, `hint`, `/plan`, `/trace` or `/exit`. The other subcommands are `trace`, `learners`, `tools`, `teacher` (`propose`, `pending`, `show`, `approve`, `edit`, `reject`, `try-publish`), `eval` and `check-llm`; see `tutor --help` and [the POC guide](https://github.com/ksharp05/Socratic-AI-Tutor/blob/docs-archive-2026-11-14/Docs/poc/README.md#things-to-try).

API and web UI without Docker, in two terminals with `.venv` active:

```bash
uvicorn tutor_api.main:app --port 8000
```

```bash
streamlit run ui/app.py
```

Open [http://localhost:8501](http://localhost:8501) and use the same tokens as in Route A. Stop either with Ctrl+C. Do not run this and the Compose stack at the same time: both use ports 8000 and 8501.

## 6. Optional: a live model with your own key

Everything above works without a key. For live replies, each member uses their **own** course key (OpenRouter, valid until 16 Nov 2026). Never paste it into chat, issues, screenshots or commits.

1. Create `.env` from the template, only if it does not exist yet:

   ```powershell
   if (-not (Test-Path .env)) { Copy-Item .env.example .env }
   notepad .env
   ```

   (macOS/Linux: `[ -f .env ] || cp .env.example .env`, then edit it.)
2. Put the key straight after `LLM_API_KEY=` on the same line, with no spaces or quotes, and save. Check that Notepad did not save it as `.env.txt`.
3. Check it (one short live call, a fraction of a cent):

   ```bash
   tutor check-llm
   ```

   It shows only the key's length and last four characters, then `1 of 1 models answered`. `tutor check-llm --all` tries every course model listed in `config/app.toml`; use it sparingly.
4. `git status` must not list `.env` (it is git-ignored). The check script also verifies this.

Models are configured in `config/app.toml`. Set `TUTOR_LLM=stub` to force the offline stub even with a key. In Docker, Compose reads `.env` but still uses the stub unless `.env` (or your shell) also sets `TUTOR_LLM=auto`; the live model inside a container has not been verified yet.

### Run the development test pack

`scripts/m2/testpack_run.py` plays a test pack's cases (for example the 180-case *IITB Socratic Tutor Development Test Pack v1*, unzipped anywhere) against the real API, one fresh local store per case. Results go to `Directions/testpack_runs/<run>/`, which git ignores; score them with the pack's own `scripts/eval_cli.py score`. Findings so far: [Docs/m2/TESTPACK_RESULTS.md](m2/TESTPACK_RESULTS.md).

```powershell
python scripts/m2/testpack_run.py <pack_dir> --smoke                  # 30 cases, offline, no model calls
python scripts/m2/testpack_run.py <pack_dir>                          # all 180 cases, offline
python scripts/m2/testpack_run.py <pack_dir> --live --max-calls 300   # uses your key; hard cap on model calls
python <pack_dir>/scripts/eval_cli.py score --responses Directions/testpack_runs/<run>/responses.jsonl --cases <pack_dir>/data/all_cases.jsonl --output Directions/testpack_runs/<run>/scores.json
```

A live run of all 180 cases used 95 calls on 5 November. The runner refuses any call beyond `--max-calls` before sending it. Agree a budget with the team before live runs, since course keys are tracked per person.

## 7. What needs private data

A fresh clone contains no NCERT PDFs, extracted indexes, frozen dataset builds or held-out evaluation data, by design. These parts need data you must get separately from the data owner (Lakshya), with authorization:

| Part | What it needs |
| --- | --- |
| `tests_beta/` (except `test_portable_registry.py`), `tests_book_pipeline/`, `tests_integration_v02/` | `SOCRATES_SOURCE_WORKSPACE` pointing to a workspace with the prepared dataset. Without it, a fresh clone gives 34 setup errors in these folders; that is expected, not an install problem |
| The browser beta, `socrates.ps1 serve` (port 8770) | A registered, hash-verified textbook index: see the [beta run guide](RUN_GUIDE.md) |
| `docker-compose.integrated.yml` | `TUTOR_INDEX_PATH` to an authorized `knowledge.sqlite` and its separately trusted `TUTOR_INDEX_SHA256`: see [integrated Compose](https://github.com/ksharp05/Socratic-AI-Tutor/blob/docs-archive-2026-11-14/Docs/m2/INTEGRATED_COMPOSE.md) |
| `book_pipeline.ps1`, PDF ingestion (`python -m tutor.retrieval.ingest`) | NCERT PDFs in `data/ncert/` (git-ignored) and poppler's `pdftotext` on PATH |

To run all four test folders with the data:

```powershell
$env:SOCRATES_SOURCE_WORKSPACE = 'C:\path\to\workspace-containing-Directions'
$env:TUTOR_LLM = 'stub'
pytest -q tests tests_beta tests_book_pipeline tests_integration_v02
```

## 8. Troubleshooting

Run the check script first; its FAIL line usually names the fix. If nothing here helps, post the exact error text in the team group, never your key.

### Docker and WSL (Windows)

| What you see | Fix |
| --- | --- |
| Docker Desktop does not start: `cannot find registry key "SOFTWARE\Docker Inc.\Docker Desktop"` | The per-user install did not register itself. Rerun the Docker Desktop installer **as administrator** (right-click, Run as administrator), then start Docker Desktop again. This fixed it on our test machine |
| "Virtualization support not detected", or the check says `no hypervisor running` | Enable virtualization in BIOS/UEFI; run `wsl --install --no-distribution` as administrator; **restart Windows** |
| `WSL 2 installation is incomplete`, or `wsl --version` is not recognized (old inbox WSL) | Administrator PowerShell: `wsl --update`, then restart Windows |
| Check script: `Windows reports a restart is pending` | Restart before starting Docker Desktop. Enabling Virtual Machine Platform only takes effect after a restart |
| `error during connect ... dockerDesktopLinuxEngine`, `Cannot connect to the Docker daemon`, or the check says `Docker engine not responding` | Docker Desktop is not running or still starting. Start it and wait for "Engine running". On Linux: `sudo systemctl start docker` and check the `docker` group |
| `docker: 'compose' is not a docker command` | Old Docker without the Compose v2 plugin. Update Docker Desktop (Linux: install `docker-compose-plugin`). The old `docker-compose` (v1) is not supported by this guide |
| `Bind for 0.0.0.0:8000 failed: port is already allocated`, or the check says the port is in use | Something already listens there. `docker compose ps` (an earlier stack: `docker compose down`), or find it with `Get-NetTCPConnection -LocalPort 8000 -State Listen` (PowerShell) / `lsof -iTCP:8000 -sTCP:LISTEN` (macOS/Linux). A local `uvicorn` or `streamlit` also uses these ports |
| `docker compose up --wait` reports a container `unhealthy` | `docker compose logs api` (or `ui`) shows why. The API may need up to 40 s on first start |
| Compose stops with `Set the trusted index SHA-256` | You ran the integrated overlay. Plain `docker compose up --build --wait` needs no index |

### Python (Route B)

| What you see | Fix |
| --- | --- |
| `Python was not found`, or the Microsoft Store opens | Use `py -3.12`; or turn off Settings, Apps, Advanced app settings, App execution aliases for `python.exe`/`python3.exe` |
| Check says `.venv ... uses Python 3.x`, or pip says `requires a different Python` | Delete `.venv` (`Remove-Item -Recurse -Force .venv`, or `rm -rf .venv`) and run the install script again |
| `Microsoft Visual C++ 14.0 or greater is required`, or a long build error | The venv uses a Python newer than 3.12; recreate it with 3.12 |
| `running scripts is disabled on this system` | Use `powershell -ExecutionPolicy Bypass -File ...` for the setup scripts; for `Activate.ps1`, see [5b](#5b-activate-every-new-terminal) |
| `tutor`, `pytest`, `uvicorn` or `streamlit` not recognized | Activate `.venv`, or call `.venv\Scripts\python.exe -m pytest -q` etc. |
| `pip install` times out, SSL or proxy errors | Campus networks often block PyPI. Retry on another network (phone hotspot) or add `--default-timeout=100` |
| 34 errors in `tests_beta`, `tests_book_pipeline`, `tests_integration_v02` | Expected without private data: [section 7](#7-what-needs-private-data). `pytest -q` alone runs only `tests/` |
| Check: `Optional packages missing: matplotlib` | Only `scripts/beta/render_results.py` needs it; the install script installs it |

### Live model

| What you see | Fix |
| --- | --- |
| `No API key found` | No `.env`, an empty `LLM_API_KEY=` line, or the file is `.env.txt` (`Rename-Item .env.txt .env`) |
| `FAILED: the key was rejected` (401) | Paste the whole key again directly after `LLM_API_KEY=` |
| `this key cannot reach this model` (404) or `may not use this model` (403) | Remove or comment out any `LLM_MODEL` line in `.env`; models come from `config/app.toml` |
| `rate limited` (429) or `run out of credit` (402) | Wait a minute; for credit, tell Lakshya |
| A chat reply has a line starting `!` | The live call failed and a template was used; run `tutor check-llm` |

## 9. Every time you come back

```powershell
cd $HOME\Socratic-AI-Tutor
git pull
powershell -ExecutionPolicy Bypass -File setup\install_python_env.ps1   # quick when nothing changed
.venv\Scripts\Activate.ps1
pytest -q
```

Work stays on the current milestone branch (`milestone-2`); see [CONTRIBUTING.md](../CONTRIBUTING.md) for branches, reviews and what never gets committed. What each role owns: [lead roadmap](LEAD_ROADMAP.md). A one-page version of this guide: [INSTALL_CHECKLIST.md](INSTALL_CHECKLIST.md).

### What this guide has and has not been verified on

- Verified on Windows 11 (5 Nov 2026), from a fresh clone of `milestone-2`: the install script (Python 3.12.10, `pip check` clean, rerun idempotent), `pytest -q` (325 passed), the CI test and evaluation commands, `tutor setup`, `tutor ask` and `tutor eval`, `uvicorn` and `streamlit` answering their health checks, and both check scripts (PowerShell, and the `.sh` versions in Git Bash). Compose from a fresh clone was accepted on 5 Nov 2026 ([evidence](m2/FRESH_INSTALL.md)).
- Not yet verified: macOS and Linux, a second Windows machine, the Docker install steps above on a machine other than ours, the `ops` profile (Prometheus, Grafana), and a live model inside Docker.
