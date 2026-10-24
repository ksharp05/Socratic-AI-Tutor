# Socratic AI Tutor

> Learning through questions, reasoning, and discovery.

> [!IMPORTANT]
> **A proposed project plan is ready for team review: [Docs/plan](Docs/plan/README.md).**
>
> Please read the overview and the documents for your role **before kickoff on Sunday 25 October**. Add your comments as a GitHub issue or pull request.

## Overview

Socratic AI Tutor is a project to build an AI learning companion that helps students develop understanding through guided dialogue. Instead of giving answers straight away, the tutor will ask questions, encourage reflection, and help learners explain their reasoning.

We are building it as Project 3 of the Agentic AI Capstone. It is an NCERT tutor for a Class 10 student and their teacher. It:
- finds what the student misunderstands;
- gives hints grounded in the textbook, without giving away the answer;
- checks work with a solver;
- plans what to practise next from a model of each learner.

## Learning Approach

The experience will follow the Socratic method: explore what a learner already knows, identify gaps, and guide them toward explanations. Questions and hints should support progress while keeping the learner actively involved in solving the problem.

## Planned Capabilities

- Guide students through concepts using progressive questions.
- Offer hints when learners become stuck.
- Adapt conversations to the learner's responses and understanding.
- Encourage students to justify answers and examine assumptions.
- Summarize key ideas and suggest areas for further practice.

## Project Status

**Planning.** There are two planning documents in `Docs/`:

| Document | What it covers | Status |
|---|---|---|
| [Socratic Tutor — Agentic AI Architecture Guide](Docs/Socratic%20Tutor%20%E2%80%94%20Agentic%20AI%20Architecture%20Guide.pdf) (Poonam, 19 Oct) | The architecture, the six team roles, the hand-offs between them, and who owns which folder | Reference |
| [Proposed project plan](Docs/plan/README.md) (24 Oct) | Builds on the guide with:<br/>• a dated schedule up to submission<br/>• design decisions<br/>• evaluation and experiment design<br/>• security and privacy<br/>• budget, risks and viva preparation | **Proposed: open for review** |

**Proposed scope:** Class 10 Maths in English. Chapters: Quadratic Equations, Arithmetic Progressions, and Introduction to Trigonometry.

| Key date | |
|---|---|
| Kickoff | Sunday 25 October 2026 |
| Submission | Thursday 12 November 2026, end of day |
| Review, demo and viva | Sunday 15 November 2026 |

Application code, setup instructions and evaluation results will be added once the plan is agreed.

### How to review the plan

1. **Start with the [plan overview](Docs/plan/README.md)** (about 10 minutes). It has the architecture diagram, the timeline, the roles and the eight open decisions.
2. **Read the documents for your role.** The overview's *How to read this plan* table tells you which ones.
3. **Raise comments, questions or proposed changes** as a GitHub issue or a pull request, so the discussion stays in one place.
4. **Come to kickoff ready to settle the open decisions** and put names to the six roles.

## Repository Structure

- **README.md** introduces the project, its purpose and its current status.
- **Docs/** holds requirements, learning flows, architecture notes and development decisions:
  - `Socratic Tutor — Agentic AI Architecture Guide.pdf`: the architecture and role guide.
  - `plan/`: the proposed project plan. It has an overview, nine topic documents and an appendix.

## Getting Started

Begin with this overview, then read the [proposed project plan](Docs/plan/README.md) and the Architecture Guide in `Docs/`.
