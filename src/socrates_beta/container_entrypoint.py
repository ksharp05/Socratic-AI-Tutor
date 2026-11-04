"""Prepare a hash-pinned read-only index for the integrated container."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from ncert_pipeline.catalogue import sha256
from .knowledge import DatasetRegistry, SAFE_ID


def prepare_index(index: Path, data_directory: Path, dataset_id: str, expected_sha256: str) -> dict:
    """Register the supplied immutable index once; never replace an active dataset."""
    if not SAFE_ID.fullmatch(dataset_id or ''):
        raise ValueError('Invalid dataset ID')
    if not re.fullmatch(r'[0-9a-f]{64}', expected_sha256 or ''):
        raise ValueError('A trusted lowercase SHA-256 is required')
    index = Path(index).resolve(strict=True)
    if not index.is_file() or sha256(index) != expected_sha256:
        raise ValueError('Prepared index SHA-256 does not match the supplied value')
    registry = DatasetRegistry(Path(data_directory))
    entries = registry.entries()
    active = entries.get('active')
    if active:
        current = entries.get('datasets', {}).get(active) or {}
        if active != dataset_id or current.get('sha256') != expected_sha256 or current.get('path') != str(index):
            raise ValueError('A different dataset is already active; preserve it and use an explicit migration')
        registry.knowledge()
        return {'id': active, 'sha256': current['sha256'], 'passages': current['passages'], 'reused': True}
    entry = registry.register(dataset_id, index, title='Prepared local textbook index', activate=True,
                              expected_sha256=expected_sha256, provenance={'adapter': 'container-prepared-index'})
    return {'id': entry['id'], 'sha256': entry['sha256'], 'passages': entry['passages'], 'reused': False}


def main() -> None:
    config = Path(os.environ['TUTOR_BETA_CONFIG']).resolve(strict=True)
    settings = json.loads(config.read_text(encoding='utf-8-sig'))
    data = Path(settings['data_directory'])
    if not data.is_absolute():
        data = Path(os.environ.get('SOCRATES_SOURCE_WORKSPACE', Path(__file__).resolve().parents[2])) / data
    port = int(os.environ.get('TUTOR_BIND_PORT', '8000'))
    if not 1 <= port <= 65535:
        raise ValueError('Invalid server port')
    entry = prepare_index(Path(os.environ['TUTOR_CONTAINER_INDEX']), data,
                          os.environ.get('TUTOR_DATASET_ID', 'local-prepared-index'),
                          os.environ.get('TUTOR_INDEX_SHA256', ''))
    print(f"Prepared dataset {entry['id']}: {entry['passages']} passages (reused={entry['reused']}).", flush=True)
    import uvicorn
    uvicorn.run('tutor_api.main:app', host=os.environ.get('TUTOR_BIND_HOST', '0.0.0.0'), port=port)


if __name__ == '__main__':
    main()
