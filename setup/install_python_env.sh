#!/usr/bin/env bash
# Creates the repository's .venv with Python 3.12 and installs every Python dependency (macOS, Linux, Git Bash).
# Idempotent; touches only <repo>/.venv; no sudo, no system changes. Downloads from PyPI. No model calls.
#   bash setup/install_python_env.sh                  # dev, api, ui extras + requirements-beta-dev.txt
#   bash setup/install_python_env.sh --with-retrieval # also the optional "retrieval" extra (fastembed)
#   PYTHON=/path/to/python3.12 bash setup/install_python_env.sh
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"
EXTRAS="dev,api,ui"
[ "${1:-}" = "--with-retrieval" ] && EXTRAS="$EXTRAS,retrieval"

fail() { printf 'ERROR: %s\n' "$1" >&2; exit 1; }
step() { printf '\n==> %s\n' "$1"; }
pyver() { "$@" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])' 2>/dev/null; }

[ -f pyproject.toml ] || fail "pyproject.toml not found under $REPO_ROOT"

step "Finding Python 3.12"
PY=()
if [ -n "${PYTHON:-}" ]; then
  PY=("$PYTHON")
else
  for c in python3.12 "py -3.12" python3 python; do
    # shellcheck disable=SC2206
    cand=($c)
    command -v "${cand[0]}" >/dev/null 2>&1 || continue
    v="$(pyver "${cand[@]}" || true)"
    case "$v" in 3.12.*) PY=("${cand[@]}"); break ;; esac
  done
fi
[ ${#PY[@]} -gt 0 ] || fail "Python 3.12 not found. macOS: brew install python@3.12. Ubuntu/Debian: sudo apt install python3.12 python3.12-venv"
v="$(pyver "${PY[@]}" || true)"
case "$v" in 3.12.*) ;; *) fail "${PY[*]} is Python '$v', not 3.12" ;; esac
echo "Using Python $v: ${PY[*]}"

if [ -x .venv/bin/python ]; then VPY=.venv/bin/python
elif [ -x .venv/Scripts/python.exe ]; then VPY=.venv/Scripts/python.exe
else VPY=""; fi

if [ -n "$VPY" ]; then
  ev="$(pyver "$VPY" || true)"
  case "$ev" in 3.12.*) step "Reusing existing .venv (Python $ev)" ;;
    *) fail ".venv uses Python '$ev', not 3.12. Delete it yourself (rm -rf .venv) and run this again." ;; esac
else
  [ -e .venv ] && fail ".venv exists but has no python inside. Move or delete it, then run this again."
  step "Creating .venv"
  "${PY[@]}" -m venv .venv || fail "python -m venv failed (Debian/Ubuntu: sudo apt install python3.12-venv)"
  if [ -x .venv/bin/python ]; then VPY=.venv/bin/python; else VPY=.venv/Scripts/python.exe; fi
fi

export PIP_DISABLE_PIP_VERSION_CHECK=1
step "Upgrading pip inside .venv"
"$VPY" -m pip install --upgrade pip || fail "pip upgrade failed (network or proxy?)"
step "Installing the project: pip install -e \".[$EXTRAS]\" -r requirements-beta-dev.txt"
"$VPY" -m pip install -e ".[$EXTRAS]" -r requirements-beta-dev.txt || fail "pip install failed; see the first ERROR line above"
step "pip check"
"$VPY" -m pip check || fail "pip check reported conflicting requirements"
step "Import check"
TUTOR_LLM=stub "$VPY" -c "import tutor, tutor_api, tutor_eval, socratic_data, socrates_beta, ncert_pipeline, fastapi, uvicorn, streamlit, pytest; print('imports ok')" \
  || fail "import check failed"
TUTOR_LLM=stub "$VPY" -m tutor.cli --help >/dev/null || fail "tutor --help failed"

printf '\nPython environment ready.\nNext:\n'
printf '  source .venv/bin/activate        # Git Bash on Windows: source .venv/Scripts/activate\n'
printf '  pytest -q\n  tutor setup\n  bash setup/check_prerequisites.sh --python\n'
