"""Export only existing development partitions, without freezing or selecting final cases."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]


def prepare(build: Path, out: Path):
    if out.exists():
        raise ValueError('Refuse to overwrite existing development evidence')
    private = build / 'private'
    originals = rows(private / 'simulated_students.jsonl')
    students = [c for c in originals if c['partition'] == 'development']
    all_pairs = rows(private / 'quiz_pairs.jsonl')
    pairs = [p for p in all_pairs if p['evaluation_partition'] == 'development']
    dev_ids = {p[k] for p in pairs for k in ('pre_id', 'post_id')}
    final_ids = {p[k] for p in all_pairs if p['evaluation_partition'] != 'development' for k in ('pre_id', 'post_id')}
    if dev_ids & final_ids:
        raise ValueError('Development/final quiz IDs overlap')
    cases = rows(private / 'cases.jsonl')
    items = {q['question_id']: q for q in cases if q['question_id'] in dev_ids}
    source_assignments = {a['student_id']: a['pair_ids'] for a in rows(private / 'student_quiz_assignments.jsonl')
                          if a['partition'] == 'development'}
    pair_map = {p['pair_id']: p for p in pairs}
    catalogue = {c['misconception_id']: c for c in rows(build / 'metadata/misconceptions.jsonl')}
    public_concepts = rows(build / 'metadata/concepts.jsonl')
    chapter_by_concept = {c['concept_id']: c['chapter'] for c in public_concepts}
    projections, assignments, missing = [], [], []
    for card in students:
        chapters = sorted({chapter_by_concept[catalogue[mid]['concept_id']]
                           for mid in card['hidden_card']['seeded_misconception_ids']})
        for chapter in chapters:
            selected = [pid for pid in source_assignments[card['student_id']] if pid in pair_map and
                        all(items[pair_map[pid][k]]['chapter'] == chapter for k in ('pre_id', 'post_id'))]
            if not selected:
                missing.append({'source_student': card['student_id'], 'chapter': chapter})
                continue
            derived = json.loads(json.dumps(card))
            derived.update(student_id=card['student_id'] + '__' + chapter, source_student_id=card['student_id'],
                           chapter=chapter, provenance='chapter_projection_of_existing_development_card')
            hidden = derived['hidden_card']
            hidden['seeded_misconception_ids'] = [mid for mid in hidden['seeded_misconception_ids']
                                                 if chapter_by_concept[catalogue[mid]['concept_id']] == chapter]
            hidden['target_concept_ids'] = [cid for cid in hidden['target_concept_ids'] if chapter_by_concept[cid] == chapter]
            hidden['true_mastery_by_concept'] = {cid: value for cid, value in hidden['true_mastery_by_concept'].items()
                                                if chapter_by_concept[cid] == chapter}
            projections.append(derived)
            assignments.append({'student_id': derived['student_id'], 'pair_ids': selected, 'partition': 'development'})
    export_pairs = [{**p, 'partition': 'development', 'pre': items[p['pre_id']], 'post': items[p['post_id']]} for p in pairs]
    out.mkdir(parents=True)
    for name, data in [('students.json', projections), ('pairs.json', export_pairs), ('assignments.json', assignments)]:
        (out / name).write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    public_practice = rows(build / 'development_preview/practice_questions.jsonl')
    canonical = lambda q: json.dumps(q['problem'], sort_keys=True)
    practice_givens = {canonical(q) for q in public_practice}
    audit = {'development_only': True, 'independent_evaluation': False,
             'source_student_count': len(students), 'chapter_projection_count': len(projections),
             'projection_is_not_an_independent_learner': True,
             'chapters': dict(Counter(c['chapter'] for c in projections)),
             'seeded_misconceptions': sorted({mid for c in projections for mid in c['hidden_card']['seeded_misconception_ids']}),
             'quiz_pairs': len(pairs), 'quiz_items': len(items), 'development_golden_cases': sum(q['split'] == 'development' for q in cases),
             'candidate_final_student_count': sum(c['partition'] == 'candidate_final' for c in originals),
             'candidate_final_quiz_pairs': sum(p['evaluation_partition'] == 'candidate_final' for p in all_pairs),
             'final_content_exported': False, 'missing_chapter_assignments': missing,
             'quiz_overlap_with_practice_problem_records': sum(canonical(q) in practice_givens for q in items.values()),
             'source_sha256': {name: hashlib.sha256((private / name).read_bytes()).hexdigest() for name in
                              ['simulated_students.jsonl', 'quiz_pairs.jsonl', 'cases.jsonl', 'student_quiz_assignments.jsonl']},
             'export_sha256': {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in out.glob('*.json')}}
    (out / 'AUDIT.json').write_text(json.dumps(audit, indent=2) + '\n', encoding='utf-8')
    return audit


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--build', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(prepare(args.build, args.out), indent=2))


if __name__ == '__main__':
    main()
