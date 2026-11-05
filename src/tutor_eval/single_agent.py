"""Development C1: one tutor-model controller with deterministic, guarded support services.

The single controller routes one learner turn; retrieval, maths, student-state,
quiz and approval operations reuse the same code-owned services, permissions,
budgets and output checks as C2. No independent specialist model is called for
diagnosis. The existing heuristic planner and tutor prompt are shared, so this
is a conservative architectural baseline, not an independently developed agent
or a claim about the benefit of multiple agents. No final held-out data is read.
"""
from langgraph.graph import END, START, StateGraph

from tutor.app import TutorApp, TutorState


class SingleAgentTutor(TutorApp):
    supports_model_diagnosis = False
    def _diagnose(self, state: TutorState) -> dict:
        # Deterministic diagnosis hypothesis. The single tutor model is reserved for
        # the tutoring action, so this baseline never calls the C2 diagnostician model.
        mid = state['focus_misconception']
        mis = self.misconceptions[mid]
        self._call(state, 'single_agent_diagnosis', 'diagnostician', 'learner-store',
                   'read_learner', {'learner_id': state['session']['learner_id']})
        flagged = state['learner']['misconceptions'].get(mid)
        opener = ("We've seen this idea trip you up before, so let's check it carefully. "
                  if flagged else "Good question, let's check one thing first. ")
        evidence = ['keywords in the student message; development baseline']
        self._note(state, 'single_agent', 'rule_diagnosis', {'misconception': mid})
        return {'draft': {'text': opener + mis['diagnostic_probe'], 'citations': [],
                          'kind': 'probe', 'misconception_id': mid},
                'diagnosis': {'misconception_id': mid,
                              'status': 'suspected', 'provisional': True,
                              'evidence': evidence},
                'focus_misconception': mid, 'probe_asked_for': mid, 'hint_stage': 0}

    def _single_controller(self, state: TutorState) -> dict:
        selection = self._planner(state)
        local = {**state, **selection}
        route = selection['route']
        actions = {
            'diagnose': self._diagnose,
            'tutor': self._tutor,
            'tutor_extension': lambda s: self._tutor(s, extension=True),
            'set_question': self._set_question,
            'grade': self._grade,
            'check_reasoning': self._check_reasoning,
            'quiz_start': self._quiz_start,
            'quiz_answer': self._quiz_answer,
            'refuse': self._refuse,
            'handoff': self._handoff,
            'question_revoked': self._question_revoked,
            'converse': self._converse,
        }
        self._note(local, 'single_agent', 'selected_action', {'route': route})
        return {**selection, **actions[route](local)}

    def _build_session_graph(self) -> StateGraph:
        graph = StateGraph(TutorState)
        graph.add_node('input_guard', self._input_guard)
        graph.add_node('load_learner', self._load_learner)
        graph.add_node('single_agent', self._single_controller)
        graph.add_node('output_guard', self._output_guard)
        graph.add_node('retry', self._retry)
        graph.add_node('fallback', self._fallback)
        graph.add_node('update_memory', self._update_memory)
        graph.add_node('respond', self._respond)
        graph.add_edge(START, 'input_guard')
        graph.add_edge('input_guard', 'load_learner')
        graph.add_edge('load_learner', 'single_agent')
        graph.add_edge('single_agent', 'output_guard')
        graph.add_conditional_edges('output_guard', self._after_guard,
                                    {'update_memory': 'update_memory', 'retry': 'retry', 'fallback': 'fallback'})
        graph.add_edge('retry', 'single_agent')
        graph.add_edge('fallback', 'update_memory')
        graph.add_edge('update_memory', 'respond')
        graph.add_edge('respond', END)
        return graph
