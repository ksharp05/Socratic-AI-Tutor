"""Copy-on-write review promotion with separate private review evidence.

Review records are declarations by registered operators, not an identity service.
The runtime projection never includes reviewer identities or scoring metadata.
"""
import argparse
import copy
import hashlib
import json
from datetime import datetime
from pathlib import Path
from .audit import digest, require, RUBRIC, read_rows, load_json
from .approved_store import MAX_EXAMPLE_BYTES

MINIMUM_THRESHOLDS = dict(zip(RUBRIC, [2, 1, 1, 1, 2, 2]))


def json_bytes(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + '\n').encode('utf-8')


def prepare_promotion(source_record, revision, decision, policy, reviewers):
    require(policy.get('ratified') is True and isinstance(policy.get('policy_id'), str) and policy['policy_id'], 'Policy ratification required')
    require(policy.get('ratification_reference') and policy.get('approved_by'), 'Policy owner evidence required')
    thresholds = policy.get('thresholds')
    require(isinstance(thresholds, dict) and set(thresholds) == set(RUBRIC), 'Explicit ratified rubric thresholds required')
    require(all(type(v) is int and MINIMUM_THRESHOLDS[k] <= v <= 2 for k, v in thresholds.items()), 'Unsupported or weakened policy thresholds')
    require(decision.get('decision') == 'approve' and decision.get('parent_id') == source_record['id'], 'Explicit human approval required')
    require(decision.get('parent_sha256') == digest(source_record) and decision.get('revision_sha256') == digest(revision), 'Review does not bind the exact revision')
    require(decision.get('policy_id') == policy['policy_id'] and decision.get('policy_sha256') == digest(policy), 'Stale policy content binding')
    identities = decision.get('reviewer_ids')
    require(isinstance(identities, list) and all(isinstance(i, str) and i for i in identities) and len(set(identities)) == len(identities) and len(identities) >= 2, 'Distinct reviewer identities required')
    require(all(i in reviewers and reviewers[i].get('active') is True for i in identities), 'Unregistered/inactive reviewer')
    subjects = {i for i in identities if 'subject' in reviewers[i].get('roles', [])}
    pedagogues = {i for i in identities if 'pedagogy' in reviewers[i].get('roles', [])}
    require(any(s != p for s in subjects for p in pedagogues), 'Distinct subject and pedagogy reviewers required')
    require(decision.get('review_origin') == 'human' and all(reviewers[i].get('kind') == 'human' for i in identities), 'AI approval is prohibited')
    stamp = decision.get('reviewed_at')
    require(isinstance(stamp, str), 'Actual review timestamp required')
    parsed = datetime.fromisoformat(stamp.replace('Z', '+00:00'))
    require(parsed.tzinfo is not None, 'Review timestamp needs a timezone')
    scores = decision.get('scores', {})
    require(set(scores) == set(RUBRIC) and all(type(v) is int and 0 <= v <= 2 for v in scores.values()), 'Invalid rubric scores')
    require(all(scores[k] >= thresholds[k] for k in RUBRIC), 'Ratified rubric promotion gate failed')
    require(source_record.get('mode') == 'practice' and isinstance(source_record.get('messages'), list) and source_record['id'].startswith('SYN-DLG-'), 'Only original practice dialogues can be reviewed here')
    require(source_record['split'] == 'development_only' and source_record['curriculum_scope'] == 'in_scope' and source_record['misconception_id'] != 'T08', 'Source not eligible for development-example review')
    attribution = {k: source_record.get(k) for k in ['source_origin', 'generator_version', 'creation_date', 'split']}
    require(all(isinstance(v, str) and v for v in attribution.values()), 'Source attribution is incomplete')
    require(revision.get('parent_id') == source_record['id'] and revision.get('kind') == 'reviewed_development_dialogue', 'Only reviewed dialogue revisions supported')
    require(set(revision) == {'parent_id', 'kind', 'chapter', 'misconception_id', 'messages'}, 'Unknown/private revision fields')
    require(revision['chapter'] == source_record['chapter'] and revision['misconception_id'] == source_record['misconception_id'], 'Unapproved scope/misconception change')
    require(isinstance(revision['messages'], list) and 2 <= len(revision['messages']) <= 40, 'Invalid dialogue message count')
    for i, message in enumerate(revision['messages']):
        require(set(message) == {'role', 'text'} and message['role'] == ('student' if i % 2 == 0 else 'tutor') and isinstance(message['text'], str) and 0 < len(message['text']) <= 4000, 'Invalid message shape/order')
        if message['role'] == 'tutor':
            require(len(message['text'].split()) <= 60 and message['text'].count('?') <= 1, 'Teaching turn shape violates bounded contract')
    return {'record_id': 'reviewed_' + digest(revision)[:24], 'parent_id': source_record['id'], 'parent_sha256': digest(source_record),
            'revision_sha256': digest(revision), 'source_attribution': attribution, 'policy_id': policy['policy_id'], 'policy_sha256': digest(policy),
            'reviewer_registry_sha256': digest(reviewers), 'reviewer_ids': identities, 'reviewed_at': stamp, 'scores': copy.deepcopy(scores),
            'review_origin': 'human', 'status': 'human_approved_development_example', 'not_independent_final_evaluation': True,
            'revision': copy.deepcopy(revision)}


def preflight_directory(directory, contents):
    require(not directory.is_symlink(), 'Linked output directory is prohibited')
    if not directory.exists():
        return
    require(directory.is_dir() and {p.name for p in directory.iterdir()} == set(contents), 'Use a new versioned output directory')
    for name, value in contents.items():
        path = directory / name
        require(path.is_file() and not path.is_symlink() and path.read_bytes() == value, 'Refusing to overwrite a different reviewed version')


def write_immutable_directory(directory, contents):
    preflight_directory(directory, contents)
    if directory.exists():
        return
    directory.mkdir(parents=True, exist_ok=False)
    for name, value in contents.items():
        with (directory / name).open('xb') as stream:
            stream.write(value)


def publish_projection(items, destination, *, policy, reviewers, evidence_directory=None, source_root=None):
    records = [prepare_promotion(item['source_record'], item['revision'], item['decision'], policy, reviewers) for item in items]
    require(records, 'No reviewed items supplied; do not create an approval claim')
    ids = [r['record_id'] for r in records]
    require(len(ids) == len(set(ids)), 'Duplicate approved revision')
    destination = Path(destination).absolute()
    evidence = Path(evidence_directory).absolute() if evidence_directory else destination.with_name(destination.name + '.review_evidence')
    dest_resolved, evidence_resolved = destination.resolve(), evidence.resolve()
    require(dest_resolved != evidence_resolved and dest_resolved not in evidence_resolved.parents and evidence_resolved not in dest_resolved.parents, 'Private review evidence must be outside runtime projection')
    if source_root is not None:
        source = Path(source_root).resolve()
        require(all(p != source and source not in p.parents for p in [dest_resolved, evidence_resolved]), 'Output cannot modify the original source snapshot')
    payload = [{'example_id': r['record_id'], 'chapter': r['revision']['chapter'], 'messages': r['revision']['messages']} for r in records]
    raw = b''.join((json.dumps(r, sort_keys=True, ensure_ascii=False, separators=(',', ':')) + '\n').encode('utf-8') for r in payload)
    require(len(raw)<=MAX_EXAMPLE_BYTES,'Approved examples exceed runtime bound; publish a smaller reviewed version')
    manifest = {'records': len(payload), 'file': 'examples.jsonl', 'sha256': hashlib.sha256(raw).hexdigest(),
                'policies': sorted({r['policy_id'] for r in records}), 'review_evidence_sha256': [digest(r) for r in records], 'teaching_permissions_unchanged': True}
    selected = sorted({i for r in records for i in r['reviewer_ids']})
    ledger = {'schema_version': 1, 'review_records': records, 'ratified_policy': copy.deepcopy(policy),
              'reviewer_registry_sha256': digest(reviewers),
              'registered_reviewers': {i: {k: reviewers[i].get(k) for k in ['kind', 'active', 'roles']} for i in selected},
              'identity_authentication': 'recorded_operator_declarations_not_an_authentication_service'}
    runtime_files = {'examples.jsonl': raw, 'MANIFEST.json': json_bytes(manifest)}
    private_files = {'review_ledger.json': json_bytes(ledger)}
    # Check both destinations before any mutation. Save private evidence before
    # publishing; partial outputs never satisfy the runtime's pinned manifest.
    preflight_directory(destination, runtime_files)
    preflight_directory(evidence, private_files)
    write_immutable_directory(evidence, private_files)
    write_immutable_directory(destination, runtime_files)
    return payload


def main():
    parser = argparse.ArgumentParser()
    for name in ['source', 'revision', 'decision', 'policy', 'reviewer-registry', 'destination']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--review-evidence-directory', type=Path)
    args = parser.parse_args()
    def read(path):
        return load_json(path.read_text(encoding='utf-8-sig'))
    revision, decision = read(args.revision), read(args.decision)
    sources = {r['id']: r for r in read_rows(args.source / 'dev/dialogues_synthetic.jsonl')}
    item = {'source_record': sources[revision['parent_id']], 'revision': revision, 'decision': decision}
    rows = publish_projection([item], args.destination, policy=read(args.policy), reviewers=read(args.reviewer_registry),
                              evidence_directory=args.review_evidence_directory, source_root=args.source)
    print(json.dumps({'promoted_development_examples': len(rows), 'not_independent_final_evaluation': True}))


if __name__ == '__main__':
    main()
