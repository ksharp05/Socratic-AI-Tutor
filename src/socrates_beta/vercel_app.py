"""Vercel entrypoint with durable Postgres progress and an ephemeral public index."""
from __future__ import annotations
import os
import json
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .api import create_app
from .public_index import prepare_public_index
from .transport import BrowserTransport
from .postgres import PostgresRepository

CODE_ROOT = Path(__file__).resolve().parents[2]

def vercel_app(*, env=None, data=None, repository=None, language_factory=None):
    env = os.environ if env is None else env
    origin = env.get("TUTOR_PUBLIC_ORIGIN")
    transport = BrowserTransport.configured(origin)
    if not origin:
        raise ValueError("Set the exact HTTPS production origin")
    additional = tuple("https://"+env[key] for key in ("VERCEL_URL", "VERCEL_BRANCH_URL", "VERCEL_PROJECT_PRODUCTION_URL")
                       if env.get(key))
    transport = BrowserTransport.configured(origin, additional_origins=additional)
    live=env.get("TUTOR_BETA_LIVE", "0")=="1"
    if env.get("TUTOR_BETA_LIVE","0") not in ("0","1"):
        raise ValueError("Invalid live-model setting")
    if live and not env.get("TUTOR_DEPLOYMENT_BUDGET_JSON"):
        raise ValueError("Hosted live models require a separately funded database-backed budget")
    try:
        secret = bytes.fromhex(env.get("TUTOR_BROWSER_SECRET", ""))
    except ValueError:
        raise ValueError("A stable 32-byte browser secret is required") from None
    if len(secret) != 32:
        raise ValueError("A stable 32-byte browser secret is required")
    repo = repository or PostgresRepository(env.get("DATABASE_URL", ""))
    language=None
    if live:
        from .postgres_budget import PostgresBudget
        from .deployment_budget import HostedLanguage
        budget=PostgresBudget(repo,json.loads(env["TUTOR_DEPLOYMENT_BUDGET_JSON"]))
        language=(language_factory or HostedLanguage)(CODE_ROOT,budget)
    # Only reconstructible, public reference material is cached on the function disk.
    data = Path(data or "/tmp/socrates-public-v1")
    registry = prepare_public_index(CODE_ROOT, data)
    settings = {"app_root":str(CODE_ROOT), "data_directory":str(data),
                "public_origin":origin, "additional_origins":additional,
                "assessment_policy":"reference_checked_beta", "require_live_consent":live}
    beta = create_app(settings, registry=registry, repository=repo, browser_secret=secret,language=language)
    app = FastAPI(title="Socrates beta", docs_url=None, redoc_url=None, openapi_url=None)
    @app.get("/")
    def home():
        return RedirectResponse("/beta/")
    @app.get("/health")
    def health():
        registry.knowledge()
        with repo.connect() as conn:
            conn.execute("SELECT 1").fetchone()
        return {"status":"ok", "saved_progress":"postgres_browser_profile", "live":live,
                "assessment_policy":"reference_checked_beta", "R3_graph_integration":False}
    app.mount("/beta", beta)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(transport.hosts))
    return app
