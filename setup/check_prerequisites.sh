#!/usr/bin/env bash
# Read-only prerequisite check for the Socratic Tutor (macOS, Linux; also runs in Git Bash on Windows,
# but on Windows prefer setup/check_prerequisites.ps1, which also checks WSL 2 and virtualization).
# Prints PASS / WARN / FAIL / INFO. Changes nothing, needs no sudo, makes no network calls, never prints secrets.
# Exit code 1 if any required item fails.
#   bash setup/check_prerequisites.sh            # both routes
#   bash setup/check_prerequisites.sh --docker   # Route A only
#   bash setup/check_prerequisites.sh --python   # Route B only
set -u

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT" || exit 1
CHECK_PY=1; CHECK_DOCKER=1
case "${1:-}" in
  --docker) CHECK_PY=0 ;;
  --python) CHECK_DOCKER=0 ;;
  "") ;;
  *) echo "usage: $0 [--docker|--python]"; exit 2 ;;
esac
NPASS=0; NWARN=0; NFAIL=0
res() {
  case "$1" in PASS) NPASS=$((NPASS+1));; WARN) NWARN=$((NWARN+1));; FAIL) NFAIL=$((NFAIL+1));; esac
  printf '[%s] %-26s %s\n' "$1" "$2" "$3"
}
# timeout is GNU coreutils; macOS may not have it.
tmo() { if command -v timeout >/dev/null 2>&1; then timeout "$@"; else shift; "$@"; fi; }
pyver() { "$@" -c 'import sys; print("%d.%d.%d" % sys.version_info[:3])' 2>/dev/null; }

echo "Socratic Tutor prerequisite check"
echo "Repository: $REPO_ROOT"
echo
[ -f pyproject.toml ] && res PASS "Repository" "pyproject.toml found" || res FAIL "Repository" "pyproject.toml not found"

if command -v git >/dev/null 2>&1; then
  res PASS "Git" "$(git --version)"
  res INFO "Git branch" "$(git rev-parse --abbrev-ref HEAD 2>/dev/null)"
else
  res FAIL "Git" "git not found on PATH"
fi

if [ "$CHECK_PY" = 1 ]; then
  PY=""; OTHERS=""
  for c in python3.12 "py -3.12" python3 python; do
    # shellcheck disable=SC2206
    cand=($c)
    command -v "${cand[0]}" >/dev/null 2>&1 || continue
    v="$(pyver "${cand[@]}" || true)"
    case "$v" in 3.12.*) PY="$c"; PYV="$v"; break ;; "") ;; *) OTHERS="$OTHERS $v($c)" ;; esac
  done
  if [ -n "$PY" ]; then res PASS "Python 3.12" "$PYV via '$PY'"
  elif [ -n "$OTHERS" ]; then res FAIL "Python 3.12" "not found; found only:$OTHERS. CI and the Dockerfile use 3.12"
  else res FAIL "Python 3.12" "not found"; fi

  [ -n "${VIRTUAL_ENV:-}" ] && res INFO "Active venv" "$VIRTUAL_ENV"
  if [ -x .venv/bin/python ]; then VPY=.venv/bin/python; TUTOR_BIN=.venv/bin/tutor
  elif [ -x .venv/Scripts/python.exe ]; then VPY=.venv/Scripts/python.exe; TUTOR_BIN=.venv/Scripts/tutor.exe
  else VPY=""; fi
  if [ -n "$VPY" ]; then
    ev="$(pyver "$VPY" || true)"
    case "$ev" in 3.12.*) res PASS ".venv" "exists, Python $ev" ;;
      "") res FAIL ".venv" "exists but its python does not run; recreate it" ;;
      *) res FAIL ".venv" "uses Python $ev; recreate it with 3.12" ;; esac
    MODS="tutor tutor_api tutor_eval socratic_data socrates_beta ncert_pipeline langgraph langgraph.checkpoint.sqlite langchain_openai fastmcp filelock bm25s sympy fastapi uvicorn prometheus_client httpx pydantic streamlit requests pytest pytest_asyncio"
    out="$(TUTOR_LLM=stub "$VPY" - "$MODS" "matplotlib" <<'EOF' 2>&1
import importlib, sys
def miss(names):
    out = []
    for m in names.split():
        try:
            importlib.import_module(m)
        except Exception as e:
            out.append(m + " (" + type(e).__name__ + ")")
    return ";".join(out)
print("REQ:" + miss(sys.argv[1]))
print("OPT:" + miss(sys.argv[2]))
EOF
)"
    req="$(printf '%s\n' "$out" | sed -n 's/^REQ://p')"
    opt="$(printf '%s\n' "$out" | sed -n 's/^OPT://p')"
    if ! printf '%s\n' "$out" | grep -q '^REQ:'; then res FAIL "Packages" "import check failed: $(printf '%s' "$out" | tail -1)"
    elif [ -n "$req" ]; then res FAIL "Packages" "missing: $req. Run setup/install_python_env.sh"
    else res PASS "Packages" "application, API, UI, beta-runtime and test packages import"; fi
    [ -n "$opt" ] && res WARN "Optional packages" "missing: $opt (only for scripts/beta/render_results.py)"
    pc="$("$VPY" -m pip check 2>&1)" && res PASS "pip check" "$pc" || res WARN "pip check" "$(printf '%s' "$pc" | head -1)"
    [ -e "$TUTOR_BIN" ] && res PASS "tutor command" "$TUTOR_BIN present" || res FAIL "tutor command" "not installed; run setup/install_python_env.sh"
  elif [ -n "$PY" ]; then
    # shellcheck disable=SC2086
    if $PY -c 'import venv, ensurepip' 2>/dev/null; then res WARN ".venv" "not created yet; run setup/install_python_env.sh"
    else res FAIL ".venv" "cannot be created: install the venv module (Debian/Ubuntu: python3.12-venv)"; fi
  else
    res FAIL ".venv" "not created, and no Python 3.12 to create it with"
  fi
fi

if [ "$CHECK_DOCKER" = 1 ]; then
  if command -v docker >/dev/null 2>&1; then
    res PASS "Docker CLI" "client $(docker version --format '{{.Client.Version}}' 2>/dev/null || echo '?')"
    sv="$(tmo 30 docker info --format '{{.ServerVersion}} {{.OperatingSystem}}' 2>/dev/null)"
    if [ -n "$sv" ]; then res PASS "Docker engine" "server $sv"
    else res FAIL "Docker engine" "not responding: start Docker Desktop (macOS/Windows) or the docker service (Linux); on Linux also check your user can reach the socket (docker group)"; fi
    cv="$(docker compose version --short 2>/dev/null)"
    if [ -n "$cv" ]; then res PASS "Docker Compose v2+" "docker compose $cv"
    elif command -v docker-compose >/dev/null 2>&1; then res FAIL "Docker Compose v2+" "only legacy docker-compose; install the compose plugin"
    else res FAIL "Docker Compose v2+" "'docker compose' not available (Linux: install docker-compose-plugin)"; fi
  else
    res FAIL "Docker CLI" "docker not found on PATH"
  fi
fi

port_busy() {
  if command -v lsof >/dev/null 2>&1; then lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1; return $?; fi
  if command -v ss >/dev/null 2>&1; then ss -ltn "sport = :$1" 2>/dev/null | grep -q LISTEN; return $?; fi
  if command -v netstat >/dev/null 2>&1; then netstat -an 2>/dev/null | grep -Eq "[:.]$1[[:space:]].*LISTEN"; return $?; fi
  return 2
}
for p in 8000 8501; do
  port_busy "$p"; rc=$?
  case $rc in 0) res WARN "Port $p" "in use (tutor stack already running? try: docker compose ps)" ;;
    1) res PASS "Port $p" "free" ;; *) res INFO "Port $p" "could not check (no lsof/ss/netstat)" ;; esac
done

if [ -f .env ]; then
  if git ls-files --error-unmatch .env >/dev/null 2>&1; then res FAIL ".env" "is TRACKED by git: remove it from the index and rotate the key"
  elif ! git check-ignore -q .env 2>/dev/null; then res FAIL ".env" "present but NOT git-ignored"
  else
    if grep -Eq '^[[:space:]]*LLM_API_KEY[[:space:]]*=[[:space:]]*[^[:space:]]' .env; then st="LLM_API_KEY is set (value not shown)"
    elif grep -Eq '^[[:space:]]*LLM_API_KEY[[:space:]]*=' .env; then st="LLM_API_KEY is empty"
    else st="no LLM_API_KEY line"; fi
    res PASS ".env" "present and git-ignored; $st. Optional: only needed for a live model"
  fi
else
  res INFO ".env" "absent: fine, the tutor uses the offline stub"
fi

echo
echo "Summary: $NPASS PASS, $NWARN WARN, $NFAIL FAIL"
if [ "$NFAIL" -gt 0 ]; then echo "Fix the FAIL items (Docs/SETUP.md, Troubleshooting), then run this check again."; exit 1; fi
echo "Required prerequisites are in place."
