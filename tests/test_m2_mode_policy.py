"""Known dataset usage-policy gaps. Xfail is not a successful policy check."""
import json
from pathlib import Path

import pytest
from tutor.app import TutorApp
from tutor.seed import seed_learner
from socrates_beta.maths import AssessmentService,CheckedMaths
from socrates_beta.repository import Repository

ROOT=Path(__file__).resolve().parents[1]


class QuestionModePolicyViolation(AssertionError):
    pass


def public_policies():
    rows=(json.loads(line) for line in (ROOT/'content/dataset-v0.10.0/practice_questions.jsonl').read_text(encoding='utf-8-sig').splitlines())
    return {r['question_id']:r['mode_policy']['allowed_modes'] for r in rows}


@pytest.mark.xfail(strict=True,raises=QuestionModePolicyViolation,reason='Graph quiz currently serves public items whose dataset policy permits practice only')
def test_graph_quiz_only_uses_items_permitted_in_quiz_mode(tmp_path):
    app=TutorApp(llm_mode='stub',db_name=str(tmp_path/'tutor.db'),checkpoint_name=str(tmp_path/'checkpoints.db'))
    try:
        seed_learner(app.conn,'L-A',{'alias':'Synthetic'})
        proposal=app.propose_set('qe04');app.decide(proposal['set_id'],'approve','synthetic-teacher')
        response=app.turn('synthetic-quiz-policy','L-A','start a quiz',mode='quiz')
        assert response['route']=='quiz_start'
        quiz=app.graph.get_state({'configurable':{'thread_id':'synthetic-quiz-policy'}}).values['quiz']
        policies=public_policies()
        if not all('quiz' in policies[item['question_id']] for item in quiz['items']):
            raise QuestionModePolicyViolation('A practice-only question was selected for the graph quiz')
    finally:app.close()


@pytest.mark.xfail(strict=True,raises=QuestionModePolicyViolation,reason='Standalone beta quiz currently serves practice-only public items')
def test_standalone_quiz_only_uses_items_permitted_in_quiz_mode(tmp_path):
    repo=Repository(tmp_path/'beta.sqlite');maths=CheckedMaths(ROOT)
    session=repo.create_session('synthetic-owner','synthetic-dataset',
        {'grade':10,'subject':'Mathematics','book':None,'unit':None},'Synthetic')
    quiz=AssessmentService(repo,maths).start(session,'quiz')
    if 'quiz' not in maths.items[quiz['item']['id']]['mode_policy']['allowed_modes']:
        raise QuestionModePolicyViolation('A practice-only question was selected for the beta quiz')
