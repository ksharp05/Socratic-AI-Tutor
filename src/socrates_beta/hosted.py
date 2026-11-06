"""Standalone persistent native beta, scoped to committed Class 10 maths references."""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from .api import create_app
from .deployment_budget import DeploymentBudget, HostedLanguage
from .public_index import prepare_public_index
from .transport import BrowserTransport

CODE_ROOT=Path(__file__).resolve().parents[2]


def read_grant():
    raw=os.environ.get("TUTOR_DEPLOYMENT_BUDGET_JSON")
    if not raw:
        raise ValueError("Live hosting needs a separately allocated deployment budget")
    return json.loads(raw)


def hosted_app(*,data=None,origin=None,live=None,language_factory=HostedLanguage):
    data=Path(data or os.environ.get("TUTOR_BETA_DATA_DIR","/var/data/socrates"))
    if not data.is_absolute():
        raise ValueError("Hosted state needs an absolute persistent data directory")
    origin=origin or os.environ.get("TUTOR_PUBLIC_ORIGIN") or os.environ.get("RENDER_EXTERNAL_URL")
    local=os.environ.get("TUTOR_BETA_LOCAL")=="1"
    if not origin and not local:
        raise ValueError("A canonical HTTPS public origin is required")
    transport=BrowserTransport.configured(origin)
    live=(os.environ.get("TUTOR_BETA_LIVE")=="1") if live is None else live
    if live and not origin:
        raise ValueError("Live hosting requires the HTTPS public origin")
    language=None
    if live:
        budget=DeploymentBudget(data,read_grant())
        language=language_factory(CODE_ROOT,budget)
    registry=prepare_public_index(CODE_ROOT,data)
    settings={"app_root":str(CODE_ROOT),"data_directory":str(data),"public_origin":origin,
              "assessment_policy":"reference_checked_beta","require_live_consent":bool(live)}
    beta=create_app(settings,registry=registry,language=language)
    app=FastAPI(title="Socrates beta host",docs_url=None,redoc_url=None,openapi_url=None)

    @app.get("/")
    def home():
        return RedirectResponse("/beta/")

    @app.get("/health")
    def health():
        registry.knowledge()
        return {"status":"ok","dataset_integrity":"verified","saved_progress":"persistent_browser_profile",
                "live":bool(live),"assessment_policy":"reference_checked_beta","R3_graph_integration":False}

    app.mount("/beta",beta)
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=list(transport.hosts))
    return app


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command",choices=("serve","init-budget"),nargs="?",default="serve")
    args=parser.parse_args()
    data=Path(os.environ.get("TUTOR_BETA_DATA_DIR","/var/data/socrates"))
    if args.command=="init-budget":
        if not data.is_absolute():
            raise ValueError("An absolute persistent data directory is required")
        DeploymentBudget.provision(data,read_grant())
        print("Deployment allocation provisioned once; no provider request was sent.")
        return
    port=int(os.environ.get("PORT","8000"))
    if not 1<=port<=65535:
        raise ValueError("Invalid HTTP port")
    import uvicorn
    uvicorn.run(hosted_app(data=data),host="0.0.0.0",port=port,workers=1,
                proxy_headers=False,server_header=False)


if __name__=="__main__":
    main()
