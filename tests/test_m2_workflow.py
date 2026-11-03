"""End-to-end development check of learner differentiation and quiz replanning."""
from fastapi.testclient import TestClient


def test_two_learners_and_quiz_replan_use_the_team_api(tmp_path):
    from tutor.app import TutorApp
    from tutor.seed import DEMO_LEARNERS, seed_learner
    from tutor_api.main import create_app

    tutor = TutorApp(llm_mode='stub', db_name=str(tmp_path / 'tutor.db'),
                     checkpoint_name=str(tmp_path / 'checkpoints.db'))
    try:
        for learner_id, spec in DEMO_LEARNERS.items():
            seed_learner(tutor.conn, learner_id, spec)
        tutor.conn.commit()
        api = create_app(tutor=tutor, tokens='a:student:L-A,b:student:L-B,t:teacher:T-001')
        with TestClient(api) as client:
            teacher = {'Authorization': 'Bearer t'}
            student_a = {'Authorization': 'Bearer a'}
            student_b = {'Authorization': 'Bearer b'}
            proposed = client.post('/teacher/proposals', headers=teacher, json={'concept_id': 'qe04'})
            assert proposed.status_code == 200
            assert client.post(f"/teacher/proposals/{proposed.json()['set_id']}/approve", headers=teacher).json()['status'] == 'published'

            prompt = 'I divided both sides by x in x² = 5x. Is that always valid?'
            a = client.post('/chat', headers=student_a, json={'text': prompt}).json()
            b = client.post('/chat', headers=student_b, json={'text': prompt}).json()
            assert a['learner_id'] == 'L-A' and b['learner_id'] == 'L-B'
            assert a['route'] != b['route'] and a['plan'] != b['plan']
            old_version = b['plan']['version']

            quiz = client.post('/chat', headers=student_b,
                               json={'session_id': b['session_id'], 'text': 'start a quiz', 'mode': 'quiz'}).json()
            assert quiz['route'] == 'quiz_start'
            for _ in range(3):
                quiz = client.post('/chat', headers=student_b,
                                   json={'session_id': b['session_id'], 'text': 'no real roots', 'mode': 'quiz'}).json()
            assert quiz['plan']['version'] > old_version
            assert quiz['plan']['replan_reason'].startswith('after quiz: scored ')
            assert client.get('/learners/L-B', headers=student_a).status_code == 403
    finally:
        tutor.close()
