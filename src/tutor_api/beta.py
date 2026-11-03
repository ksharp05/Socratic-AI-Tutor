"""Opt-in local Socrates beta mount. Existing capstone routes remain the default."""
from pathlib import Path
import json,os,sys


def mount_beta(api,config_path: str, *, tutor_provider):
    config=Path(config_path).resolve(strict=True)
    workspace=Path(os.environ.get('TUTOR_BETA_WORKSPACE',config.parents[2])).resolve(strict=True)
    package=workspace/'src/socrates_beta'
    if not (package/'api.py').is_file():raise ValueError('The configured beta workspace has no socrates_beta package')
    os.environ.setdefault('SOCRATES_SOURCE_WORKSPACE',str(workspace))
    sys.path.insert(0,str(workspace/'src'))
    from socrates_beta.api import create_app
    # The mounted beta must use the same tutor package and public practice slice
    # as this API; a standalone beta config may point at a different checkout.
    settings=json.loads(config.read_text(encoding='utf-8-sig'))
    settings['app_root']=str(Path(__file__).resolve().parents[2])
    beta=create_app(settings,live=os.environ.get('TUTOR_BETA_LIVE')=='1',tutor_provider=tutor_provider)
    api.mount('/beta',beta,name='socrates-beta')
    return beta
