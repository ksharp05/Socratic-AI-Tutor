# `socratic_data`: the dataset's maths kernel (vendored)

These five files are copied **unchanged** from `socratic_tutor_dataset_v2/src/socratic_data/` (dataset v0.10.0). `math-tools` uses them to compute answer keys by two independent routes and to grade typed answers.

Only the maths kernel is here. The dataset's build, generation and evaluation code, and its held-out data, are not in this repository.

| File | SHA-256 |
|---|---|
| `__init__.py` | `30060fca0b4036d6e5dc4418e1488f7f19ceebcfa475db76c8a392eceea1dd56` |
| `math_kernel.py` | `1da0ad82034592cdaf3b22aee2e8f418c968d321468d038304a5616e430579f6` |
| `tasks.py` | `7dc8a9bfa756be1cb5ce1db948138e2e5eeebcdb8e28935e5ae238d6f1a12ccd` |
| `assessment_tasks.py` | `bba0fa6ea5b70acacfec3a5ea7d892147af2b0c5c04b58fc8d4c9b05312eaf5a` |
| `specifications.py` | `92e71a261b3d64bcb5d13ae2079b0f8711b2d1532c4ae9c8ed02ca6d6b85b326` |

**Do not edit these files.** Put fixes or extensions in `src/tutor/mathcore.py`, so the keys stay identical to the frozen dataset's.
