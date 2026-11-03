"""Teacher-page actions exercise the actual API with synthetic, stub-mode data."""
import json
from urllib.parse import urlsplit

import pytest
pytest.importorskip('streamlit')
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest


def test_teacher_page_rejects_stale_approval_and_reapproves(tmp_path, monkeypatch):
    import requests
    from pathlib import Path
    from tutor.app import TutorApp
    from tutor_api.main import create_app

    app_root = Path(__file__).resolve().parents[1]
    tutor = TutorApp(llm_mode='stub', db_name=str(tmp_path/'tutor.db'),
                     checkpoint_name=str(tmp_path/'checkpoints.db'))
    try:
        api = create_app(tutor=tutor, tokens='test-teacher:teacher:T-001')
        with TestClient(api) as client:
            def route_local(method, url, headers=None, timeout=None, **kwargs):
                return client.request(method, urlsplit(url).path, headers=headers, **kwargs)
            monkeypatch.setattr(requests, 'request', route_local)
            monkeypatch.setenv('TUTOR_API_URL', 'http://testserver')
            monkeypatch.setenv('TUTOR_UI_TOKEN', 'test-teacher')
            ui = AppTest.from_file(str(app_root/'ui/app.py')).run(timeout=30)

            def press(label):
                next(button for button in ui.button if button.label == label).click().run(timeout=30)
                assert not ui.exception

            auth = {'Authorization': 'Bearer test-teacher'}
            press('Propose a set')
            set_id = client.get('/teacher/proposals', headers=auth).json()['proposals'][0]['set_id']
            press('Approve')
            approved = client.get(f'/teacher/proposals/{set_id}', headers=auth).json()
            assert approved['status'] == 'published'
            selected = list(ui.multiselect[0].value)
            assert len(selected) > 1
            ui.multiselect[0].set_value(selected[:-1])
            press('Save edit')
            edited = client.get(f'/teacher/proposals/{set_id}', headers=auth).json()
            assert edited['status'] == 'pending' and edited['payload_sha256'] != approved['payload_sha256']
            press('Try publish')
            results = [json.loads(element.value) for element in ui.json if 'published' in element.value]
            assert any(result.get('published') is False and 'FORBIDDEN' in result.get('error', '') for result in results)
            press('Approve')
            assert client.get(f'/teacher/proposals/{set_id}', headers=auth).json()['status'] == 'published'
    finally:
        tutor.close()
