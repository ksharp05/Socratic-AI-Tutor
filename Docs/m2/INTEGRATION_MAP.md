# Milestone 2 integration map

The selected candidate entry boundary is the existing team FastAPI application: the existing authenticated student/teacher routes and an explicitly configured local `/beta` mount. This retains the original teacher authority and existing browser implementation under one server boundary. It is an integration target, not a claim that the two paths already share learner state or have passed the M2 demonstration.

```text
Browser beta (/beta) -> beta dialogue/knowledge/assessment -> beta SQLite state
Team UI -> team API (/chat, /teacher/...) -> TutorApp graph -> MCP tools / team SQLite state
                      \-> opt-in /beta mount -> beta service above
```

Current real boundaries: `src/tutor_api/main.py` owns the team graph and teacher endpoints; `src/tutor_api/beta.py` mounts `src/socrates_beta/api.py`; the beta owns its own anonymous session and study repository; its maths adapter calls the existing team kernel. Source-grounded beta chat is not automatically a graph tutor turn, and a beta practice result is not automatically a team-graph replan. No UI should imply those state systems are unified until the bridge is implemented and tested.

For the assessed demonstration, verify source-scoped Class 10 maths, a live guarded Socratic hint and trace, two learner histories and quiz replan, and teacher edit/reapproval through this declared application boundary. Record exactly which requests take which path. A mount, screenshot or post-hoc SSE chunks alone does not prove full integration or true token streaming.


## Connected graph browser journey — 4 November

The mounted browser now offers an explicitly signed-in graph conversation, quiz and learner plan. These calls use the authenticated team API and graph state; anonymous beta chat, assessments and plans remain separate. The connected graph now has chapter-scoped normalized source conversations for quadratic equations, arithmetic progressions and trigonometry; checked practice also supports selected AP and trigonometry families after teacher publication, and each chapter has a teacher-approved development quiz path and its own graph plan after a completed quiz. [Quiz and plan details](CHAPTER_QUIZZES_AND_PLANS.md). This has offline stub-model evidence, not a verified live cited hint. The anonymous beta identity/state integration remains unverified. See [connected journey](CONNECTED_GRAPH_JOURNEY.md) and [chapter scope](CHAPTER_SCOPED_RETRIEVAL.md).
