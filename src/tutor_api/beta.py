"""Opt-in local Socrates beta mount. Existing capstone routes remain the default."""
from pathlib import Path
import os,sys


def mount_beta(api,config_path: str):
    config=Path(config_path).resolve(strict=True)
    workspace=Path(os.environ.get('TUTOR_BETA_WORKSPACE',config.parents[2])).resolve(strict=True)
    package=workspace/'src/socrates_beta'
    if not (package/'api.py').is_file():raise ValueError('The configured beta workspace has no socrates_beta package')
    os.environ.setdefault('SOCRATES_SOURCE_WORKSPACE',str(workspace))
    sys.path.insert(0,str(workspace/'src'))
    from socrates_beta.api import create_app
    beta=create_app(config,live=os.environ.get('TUTOR_BETA_LIVE')=='1')
    api.mount('/beta',beta,name='socrates-beta')
    return beta
