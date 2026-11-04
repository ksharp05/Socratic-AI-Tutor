# Install checklist

The one-page version of the [setup guide](SETUP.md). Tick each line; the guide has the details and fixes.

## Everyone

- [ ] GitHub invitation accepted; `git --version` answers
- [ ] Cloned: `git clone --branch milestone-2 https://github.com/ksharp05/Socratic-AI-Tutor.git` into your home folder (not OneDrive)
- [ ] `powershell -ExecutionPolicy Bypass -File setup\check_prerequisites.ps1` (macOS/Linux: `bash setup/check_prerequisites.sh`) shows no FAIL for the route you want

## Route A: Docker Compose

- [ ] Windows: virtualization enabled (Task Manager, Performance, CPU)
- [ ] Windows: `wsl --install --no-distribution` (administrator), then **restart**
- [ ] Docker Desktop installed **as administrator**, started, "Engine running"
- [ ] `docker version` shows a Server; `docker compose version` answers
- [ ] `docker compose up --build --wait` ends with both containers healthy
- [ ] http://localhost:8501 opens; sign in with `dev-teacher` or `dev-student-a`
- [ ] `docker compose down` when finished

## Route B: local Python

- [ ] Python 3.12: `py -3.12 --version` (macOS/Linux: `python3.12 --version`)
- [ ] `powershell -ExecutionPolicy Bypass -File setup\install_python_env.ps1` (macOS/Linux: `bash setup/install_python_env.sh`) ends with "Python environment ready"
- [ ] `.venv` activated: `(.venv)` in the prompt
- [ ] `pytest -q`: all passed (325 on 5 Nov 2026)
- [ ] `tutor setup`, then `tutor chat --learner A` answers

## Optional

- [ ] Live model: own key in `.env` as `LLM_API_KEY=...`; `tutor check-llm` says `1 of 1 models answered`; `git status` does not list `.env`
- [ ] Private data (only if the data owner gave it to you): `SOCRATES_SOURCE_WORKSPACE` set; `pytest -q tests tests_beta tests_book_pipeline tests_integration_v02` passes
