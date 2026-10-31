# Rater guide: labelling tutor turns

Two people label the same tutor turns independently. Their labels decide whether the LLM judge can be trusted (κ ≥ 0.6). This is a human-only task (human day, Sat 7 Nov): labels count only when the named rater writes them.

- **Raters:** R1 (Lakshya), plus R5b, R4 or R6.
- **Time:** about 2.5 hours each for 30 turns, plus about 30 extra turns for the leak label only.
- **Data:** development runs only. Never a held-out transcript.

## Steps

1. R5 makes the sample from a development run and shares the CSV:

   ```bash
   python -m tutor_eval.agreement sample --run var/runs/<run_id> --n 30 --out var/labels/sample.csv
   ```

2. Each rater copies it to `var/labels/<your name>.csv` and fills in every label column, **alone**: no discussion and no looking at the other file. Put your name in the `rater` column and anything unclear in `notes`.
3. When both are done, R5 scores the agreement:

   ```bash
   python -m tutor_eval.agreement score --raters var/labels/a.csv var/labels/b.csv --label leak
   ```

4. The raters meet and agree each item listed under `disagreements_to_adjudicate`, keeping both original files. Then repeat step 3 for `targets_seeded`.
5. R5 runs the judge on the same turns and scores it with `--judge`.

## Labels

Each row shows the problem, its reference answer, the student's message and the tutor's reply. Judge only the reply.

| Column | Options | Meaning |
|---|---|---|
| `leak` | `full` / `partial` / `none` | Teaching policy TP-L1/L2.<br/>• **full:** the reply gives the final answer (any equivalent form) or a complete solution before the student produced it.<br/>• **partial:** it gives an intermediate result the student should have found, such as the factorised form, the discriminant's value or the common difference.<br/>• **none:** repeating the student's own answer, naming a method, and general facts. |
| `targets_seeded` | `yes` / `no` | Does the reply specifically address one of the misconceptions listed in `seeded_misconceptions`? A general hint is `no` |
| `mistake_identification` | `Yes` / `To some extent` / `No` | Does the reply recognise that the student made a mistake? |
| `revealing_of_the_answer` | `Yes (and the revealed answer is correct)` / `Yes (but the revealed answer is incorrect)` / `No` | Does the reply give away the final answer, whether right or wrong? |
| `providing_guidance` | `Yes` / `To some extent` / `No` | Does the reply help with something correct and relevant, such as a hint, an explanation or an example? |
| `actionability` | `Yes` / `To some extent` / `No` | After reading the reply, would the student know what to do next? |

The MRBench dimensions follow Maurya et al., "Unifying AI Tutor Evaluation" ([arXiv:2412.09416](https://arxiv.org/html/2412.09416)). The label names and options are theirs, used word for word; the questions above are our own summaries.

## Rules

- **Label what is on the page.** Don't guess what the tutor meant.
- **"Not on screen" means `none` or `No`.** If the reply has no problem on screen, label leak `none` and mistake identification `No`.
- **Keep the files and their history.** Never edit the other rater's file. The CSVs stay in `var/labels/` (not in git) until the report.
