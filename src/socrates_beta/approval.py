"""Teacher-publication boundary for the beta mounted under the capstone API.

The standalone beta remains a development preview. This adapter does not link
anonymous browser profiles to authenticated graph learners.
"""
from contextlib import contextmanager
from filelock import Timeout

from tutor.mcp_servers.question_bank import ITEM_FIELDS
from tutor.toolbus import CallContext
from .maths import AssessmentService


class ApprovalUnavailable(Exception):
    """The current publication state cannot be verified."""


class ApprovedAssessmentService(AssessmentService):
    def __init__(self, repo, maths, tutor_provider):
        super().__init__(repo, maths)
        self.tutor_provider = tutor_provider
        self._available = {}

    @contextmanager
    def _published(self):
        try:
            try:
                tutor = self.tutor_provider()
                lock = tutor.bus.publication_lock
            except Exception as exc:
                raise ApprovalUnavailable('The question approval service is unavailable. Please try again.') from exc
            with lock:
                try:
                    rows = tutor.bus.call(CallContext(session_id='beta-publication-check'),
                                          'question_setter', 'question-bank', 'list_published', {})['items']
                    visible = {}
                    for item in rows:
                        qid = item['question_id']
                        source = self.maths.items.get(qid)
                        # Never accept evaluation fixtures, or use a key/hint from
                        # a public record that differs from the approved payload.
                        if (item['label'] != 'teacher_approved' or source is None or
                                any(source.get(k) != item.get(k) for k in ITEM_FIELDS)):
                            continue
                        visible.setdefault(qid, []).append((item['set_id'], item['set_payload_sha256']))
                except Exception as exc:
                    raise ApprovalUnavailable('The question approval service is unavailable. Please try again.') from exc
                yield visible
        except Timeout as exc:
            raise ApprovalUnavailable('Question approvals are busy. Please try again.') from exc

    def _eligible(self, scope, concept):
        return [item for item in super()._eligible(scope, concept) if item['question_id'] in self._available]

    def _bind_publication(self, record, eligible):
        record['state']['approval_versions'] = {
            item['question_id']: list(sorted(self._available[item['question_id']])[0]) for item in eligible}

    @staticmethod
    def _valid(record, visible):
        state = record['state']
        versions = state.get('approval_versions') or {}
        selected = set(state.get('queue', [])[:state.get('limit', 0)]) | set(state.get('used', []))
        return bool(selected) and all(qid in versions and tuple(versions[qid]) in visible.get(qid, []) for qid in selected)

    def _cancel(self, record):
        state = record['state']
        state.update(complete=True, approval_revoked=True)
        self.repo.save_assessment(record)
        return {'id':record['id'], 'mode':record['mode'], 'complete':True, 'revoked':True,
                'position':min(state['index']+1,state['limit']), 'total':state['limit'],
                'hint_stage':state['hint_stage'], 'item':None,
                'message':'This question set is no longer available. Please start a new practice or check.'}

    def start(self, session, mode='practice', concept=None, question_id=None):
        with self.lock, self._published() as visible:
            self._available = visible
            if not visible:
                raise ValueError('No teacher-approved practice is available for this topic yet.')
            return self._start(session, mode, concept, question_id)

    def public(self, record):
        with self.lock:
            if record['state'].get('approval_revoked'):
                return self._cancel(record)
            if record['state'].get('left_early'):
                return super().public(record)
            with self._published() as visible:
                return super().public(record) if self._valid(record, visible) else self._cancel(record)

    def submit(self, owner, aid, text, request_id):
        with self.lock, self._published() as visible:
            record = self.repo.assessment(aid, owner)
            if record['state'].get('approval_revoked') or not self._valid(record, visible):
                result = self._cancel(record)
                return {'status':'question_revoked', 'message':result['message'], 'assessment':result}
            return super().submit(owner, aid, text, request_id)

    def hint(self, owner, aid):
        with self.lock, self._published() as visible:
            record = self.repo.assessment(aid, owner)
            if record['state'].get('approval_revoked') or not self._valid(record, visible):
                result = self._cancel(record)
                return {'status':'question_revoked', 'hint':result['message'], 'stage':0, 'assessment':result}
            return super().hint(owner, aid)
