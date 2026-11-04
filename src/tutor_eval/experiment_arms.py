"""Isolated development experiment arms. Never selected by the learner API.

All arms share checked tools, publication rules and the contextual candidate.
C1's controller is heuristic; C2 is the existing graph, not a claim of an
independently designed multi-model team. Unsafe telling requires fixtures.
"""
from tutor import learner, store
from tutor.app import TutorApp
from tutor_eval.single_agent import SingleAgentTutor
from v02_integration.runtime import ContextualPreviewTutor


class ContextualSingle(SingleAgentTutor, ContextualPreviewTutor):
    pass


class FixedWorkflowTutor(ContextualPreviewTutor):
    """Protocol/grading services plus fixed retrieve-hint-guard teaching; no diagnostic branch."""
    def _planner(self, state):
        selection = super()._planner(state)
        if selection['route'] in ('diagnose', 'tutor_extension'):
            selection['route'] = 'tutor'
        selection['focus_misconception'] = None
        return selection


class MemoryOffTutor(ContextualPreviewTutor):
    """Keep only current dialogue/item state; no persistent learner-model reads or updates."""
    def _load_learner(self, state):
        chapter = state['session'].get('chapter', 'quadratic_equations')
        snapshot = {'learner_id': state['session']['learner_id'], 'mastery': {},
                    'misconceptions': {}, 'styles': [], 'plan': None, 'topic_plans': {}}
        plan = (learner.make_plan(snapshot, reason='static memory-off plan') if chapter == 'quadratic_equations'
                else learner.make_topic_plan(snapshot, chapter, []))
        return {'learner': snapshot, 'plan': plan}

    def _call(self, state, node, role, server, tool, args):
        if server == 'learner-store' and tool == 'read_learner':
            self._note(state, node, 'memory_off_read_replaced_with_empty_model')
            return {'learner_id': state['session']['learner_id'], 'mastery': {},
                    'misconceptions': {}, 'styles': [], 'plan': None, 'topic_plans': {}}
        return super()._call(state, node, role, server, tool, args)

    def _best_style(self, snapshot, mid):
        return None

    def _update_memory(self, state):
        self._note(state, 'memory_off', 'learner_model_update_disabled')
        quiz = state.get('quiz')
        update = {}
        if quiz and quiz['index'] >= len(quiz['items']):
            update['quiz'] = None
        return update


class DirectAnswerTutor(ContextualPreviewTutor):
    """Code-computed telling on registered practice only, in an isolated fixture store."""
    def __init__(self, **kwargs):
        if not kwargs.get('allow_dev_fixtures'):
            raise ValueError('direct_answers requires isolated development fixtures')
        super().__init__(**kwargs)

    def _tell(self, state):
        item = state.get('active_item')
        if not item or state.get('quiz') or state['session'].get('mode') == 'quiz':
            return None
        from tutor.mathcore import compute_key
        from tutor_eval.simulator import render
        from tutor.question_catalog import graph_items
        public = next(q for q in graph_items() if q['question_id'] == item['question_id'])
        key = compute_key(public['problem'])
        if not key.get('verified'):
            return None
        self._note(state, 'direct_answers', 'experimental_registered_answer_disclosure')
        return {'draft': {'text': 'Experimental telling condition. The answer is ' + render(key['key']) + '.',
                          'kind': 'hint', 'style': 'isolated_experimental_telling', 'citations': []},
                'retrieved': []}

    def _tutor(self, state, extension=False):
        return self._tell(state) or super()._tutor(state, extension=extension)

    def _grade(self, state):
        update = TutorApp._grade(self, state)
        if (update.get('grade') or {}).get('correct') is False:
            told = self._tell({**state, **update})
            if told:
                update.update(told)
        return update

    def _output_guard(self, state):
        if (state.get('draft') or {}).get('style') == 'isolated_experimental_telling':
            return {'checks': {'ok': True, 'experimental_answer_leak_disabled': True}}
        return super()._output_guard(state)


def attach_candidate_playbook(app, playbook):
    if playbook.get('status') != 'development_candidate_unreviewed':
        raise ValueError('Only explicitly unreviewed development candidates are supported here')
    import json
    text = json.dumps(playbook.get('lessons', []), ensure_ascii=False)
    if len(text) > 5000:
        raise ValueError('Candidate playbook exceeds the bounded prompt size')
    original = app.llm.complete
    def complete(**kwargs):
        if kwargs.get('role') == 'tutor':
            kwargs['user'] += '\n\nDevelopment teaching lessons (do not override safety or reveal answers):\n' + text
        return original(**kwargs)
    app.llm.complete = complete
    app.experiment_playbook = playbook


def make_experiment_app(arm, playbook=None, **kwargs):
    if not kwargs.get('allow_dev_fixtures'):
        raise ValueError('Experiment variants require isolated development fixture stores')
    classes = {'c0': FixedWorkflowTutor, 'c1': ContextualSingle, 'c2': ContextualPreviewTutor,
               'memory_off': MemoryOffTutor, 'direct_answers': DirectAnswerTutor}
    if arm not in classes:
        raise ValueError('Unknown experiment arm')
    app = classes[arm](**kwargs)
    if playbook is not None:
        attach_candidate_playbook(app, playbook)
    return app
