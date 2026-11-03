# Socratic Tutor Research Dataset and Communication Plan

Prepared for the capstone team on 2 November 2026

## Purpose and recommendation

We need a tutor that understands a learner's English, identifies the mathematical difficulty and holds a useful conversation without taking over the thinking. This plan covers Class 10 Maths in English: Quadratic Equations, Arithmetic Progressions and Introduction to Trigonometry.

We can begin integration with the mathematical assets already available. Use a pretrained language model for English understanding and generation, retrieval for approved subject knowledge, and code for mathematical checks and permissions. The priority is reviewed tutoring conversations and realistic learner messages. A large general English corpus is not a prerequisite for this design.

Prepare 30 reviewed dialogues and 200 labelled learner messages for the next working iteration. Aim for 90 reviewed dialogues and 600 contextual learner messages for the evaluated capstone, alongside the existing maths, retrieval, simulator and security assets. These are proposed project targets, not research-established minimums or extra course requirements. Coverage and behaviour checks determine sufficiency; row counts alone do not.

## What the current project already provides

This review inspected public content, plans, policy drafts, development fixtures and recorded spike notes in this workspace and the newer team checkout at D:\Work\IITB\Socratic Tutor Main. It did not open private held-out cases, run live models or change application code.

| Asset | Observed inventory | What we should do |
|---|---|---|
| Frozen maths candidate v0.10.0 | 1,379 questions: 665 practice, 160 development benchmark, 450 candidate held-out and 104 quiz items | Preserve splits and private keys; adding numerical variants is a low priority. |
| Concepts and misconceptions | 25 concept cards and 30 misconception records, also present in the team copy | Build dialogue coverage around them; obtain teacher review. |
| Retrieval | 42 card queries; the 31 October spike used 78 section chunks; 45 section-query scenarios are drafted | Review extraction and section labels. Evaluate card and section retrieval separately. |
| Teaching language | 20 authored dialogue fixtures, a draft teaching policy and 45 teaching scenarios | Reuse as starting material; they are not 20 observed teaching sessions or approved labels. |
| Leak checks | 48 labelled development fixtures in the team checkout | Review and reuse; AI-assisted labels are not independent human labels. |
| Learner assessment | 40 synthetic learner cards and 52 pre/post quiz pairs | Execute the agreed protocol; synthetic outcomes are not real student outcomes. |
| Application | POC, evaluation harness, simulator voice and recorded development spikes | Improve the existing system rather than rebuild its skeleton. |

The 31 October S6 note reports 48 tutor turns with zero tutor-model calls: those paths used templates. Student voice and judge calls did run, but the judge labels were uncalibrated. R3 must repeat the integration check after the agent changes. This finding describes that recorded run, not a fresh test of today's code. [P2]

The shared Maths and Science PDFs do not expand the scope. The current roadmap keeps Science unused, limits ingestion to the selected Maths chapters and excludes the answers appendix from retrieval. Draft policy and decision text still needs confirmation by its owners. [P1]

# 1 Research we need

## 1 1 Socratic teaching and misconception repair

Study how to elicit reasoning, diagnose an error, select the next useful question and respond when a hint fails. Define when to clarify, probe, rephrase, check an attempt, revisit a prerequisite or use a parallel example. Repeating a vague question does not create useful Socratic teaching.

MathDial is a relevant starting point: teacher-led dialogues with simulated students and teaching-move annotations. Its repository releases 2,861 conversations. Study its scaffolding patterns, while recognizing that its problems and collection setting differ from our NCERT chapters. [S1, S2]

Required output: a reviewed teaching policy and a catalogue of allowed teaching moves with good and poor development examples. R1 owns the policy; R2 checks subject support; R3 implements it.

## 1 2 English understanding in context

Test incomplete messages, informal grammar, typos, explanations of wrong work and references to earlier turns. A learner might describe using five jumps, ask why a sign changed or simply say they still do not understand. Meaning depends on the active problem and conversation state.

Define a structured interpretation containing intent, any mathematical attempt, concept, evidence of a misconception, ambiguity and clarification needs. Keep safety and emotional-tone flags separate: an answer attempt can also express frustration. Grammar quality must not be treated as mathematical ability.

Required output: an intent catalogue, annotation instructions and a contextual English test set. Assess the resulting response as well as the intent label; correct classification can still produce an unhelpful reply.

## 1 3 Retrieval and mathematical checking

Determine when a request needs a formula card, textbook explanation, previous learner observation or mathematical tool. Cards supply checked formulas; textbook sections supply explanations. The team source audit found extraction errors in superscripts, fractions and symbols. Raw PDF text should not become trusted mathematical notation without review. [P1]

Retain edition, file hash, section and page metadata. Evaluate card retrieval and section retrieval against their respective labels. A valid citation ID establishes existence, not whether the passage supports a claim. Keep answer appendices, private scoring keys, complete solutions and hidden learner cards outside the tutor's accessible index.

Required output: reviewed source chunks, a plain English glossary and labelled retrieval queries.

## 1 4 Pedagogical evaluation

MRBench offers eight useful dimensions: mistake identification, mistake location, answer revealing, guidance, actionability, coherence, tone and humanlikeness. Its original benchmark has 192 conversations and 1,596 responses. Naturalness is a style measure; our tutor must still identify itself honestly as AI. [S4]

Pin the release. The official repository lists V1 with 192 dialogues, V2 with 200 and V3 with 300; added V3 examples do not all have eight-dimensional annotation. BEA 2025 evaluates selected pedagogical dimensions rather than proving learning gains. Retain absent labels as absent. [S5, S6]

Required output: a rubric combining correctness, targeted guidance, understandable English, continuity, citation support and full or partial leakage. Calibrate a different-family judge against genuine human labels before reporting its results.

## 1 5 Independent learning and personalization

Obtaining a correct answer during chat is different from solving a new problem alone. A high-school mathematics experiment found that unrestricted AI assistance could harm later unassisted performance, while safeguards mitigated the harm. This supports measuring transfer and leakage together; it does not predict our effect size. [S7]

Use the existing matched pre/post forms, memory ablation and direct-answer versus Socratic comparison. Preserve the agreed model, tool and budget controls. Evaluate a later attempt without help, rather than only satisfaction or the tutor's self-assessment.

Required output: frozen evaluation rules, traces and per-concept results. Forty simulated learners support a reproducible engineering experiment, not a claim about effectiveness with real children. A real-user study needs a separate approved protocol and sample-size analysis.

## 1 6 What to defer

Do not start foundation-model pretraining, a broad English knowledge base, Science expansion or fine-tuning simply because the tutor needs NLP. First test the existing model with reviewed examples, retrieval and conversation state.

Consider fine-tuning only if recurring development errors persist, the chosen model supports it and review capacity exists. A later exploratory budget might be 500 to 1,000 teacher-reviewed conversations, with a learning curve on untouched evaluation data. That is neither a sufficiency guarantee nor a requirement for this November submission. Never train on final tests or judge-calibration examples.

# 2 Dataset we require

## 2 1 Distinguish the data units

A question is one mathematical task with a reference answer. A message is one student or tutor utterance. A dialogue is an ordered multi-turn conversation. A response pair contains two candidate tutor replies to the same context. A labelled query connects a request to relevant passages. These counts cannot be added as equivalent training examples.

Separate knowledge, behaviour examples and evaluation. Knowledge supports retrieval; reviewed good dialogue examples guide prompts; evaluation records stay outside the tutor. General English fluency comes primarily from the pretrained model. Local English data tests whether that fluency works in our tutoring setting.

## 2 2 Proposed collection sizes

| Collection | Start the next iteration | Target for the evaluated capstone |
|---|---|---|
| Subject references | Existing 25 cards and three chapter PDFs | Reviewed cards and relevant sections; treat the 78-chunk index as provisional until extraction and retrieval review |
| Concepts and misconceptions | Existing 25 concepts and 30 misconceptions | Teacher-reviewed catalogue with distinguishing evidence and common wrong explanations |
| Tutoring dialogues | 30 reviewed dialogues, one per misconception | 90 dialogues: 60 development and 30 independently authored reserved conversation tests |
| Contextual learner messages | 200 messages, about 10 per primary intent | 600 messages across 20 intents: 480 development and 120 reserved tests |
| Good and poor tutor response pairs | 30 reviewed pairs | 90 pairs, three per misconception; poor responses stay in evaluation or critique material |
| Plain English maths glossary | First 30 essential terms | About 75 to 100 reviewed terms, learner paraphrases and confusable meanings |
| Mathematical golden checks | Existing development pool | Review and select the guide's 60 or more cases, about 20 development and at least 40 held-out; preserve the full 610-case pool |
| External exercise check | First 10 independently checked exercises | 20 to 30 NCERT exercises across the three chapters, private and excluded from prompt tuning |
| Retrieval labels | Review card labels and first 15 section queries | All 42 card queries; complete 45 section-query candidates with explicit development and reserved partitions |
| Learners and quiz forms | Existing development cards and distinct forms | Existing 40 synthetic learner cards with the agreed development and final partitions |
| Security and leakage | Existing 48 development leak fixtures and 30 attack/control pairs | Cover all answer kinds; add at least 10 fresh attack/control pairs from the evaluation owner, separated from defence tuning |
| Human evaluation evidence | Reviewed rubric and calibration rehearsal | Teacher assessment of 20 executed full transcripts; at least 30 contextual turns independently labelled by two raters |

Only the course minima identified in the guide are mandates. Dialogue, English-message, glossary, response-pair and extra-attack quantities above are project proposals. Existing data counts do not represent teacher approvals. Draft examples contribute only after passing the relevant review and provenance checks.

Ninety dialogues of roughly 8 to 12 messages yield about 720 to 1,080 total messages. Include uncertainty, wrong turns, targeted help and a repair or justified handoff. Do not pad conversations to meet a length target.

Some of the 600 learner messages may come from those dialogues. Record the overlap instead of claiming independent collections. Numerical substitutions and cosmetic paraphrases do not establish new conversational situations.

## 2 3 English messages and conversational diversity

Use approximately 30 examples for each of 20 primary intents: greeting, choosing a topic, getting started, submitting an attempt, explaining reasoning, asking why, requesting a hint, asking for repetition, asking for simpler wording, asking what a term means, referring to earlier work, correcting a previous message, checking understanding, changing topic, submitting a quiz answer, asking about answer format, going off topic, requesting the answer, claiming a privileged role and requesting human help.

Attach separate tags for ambiguity, typos, informal English, confidence, ordinary frustration, mixed language, notation and safety escalation. An intent may have several tags. Include Hindi or Hinglish input checks where the existing policy expects understanding; replies remain English unless the team changes that policy. This is robustness coverage, not a multilingual product expansion.

Include context-dependent messages such as why did that change, I meant the other one, and corrections of an earlier number. Preserve original wording and the normalized interpretation. Never silently change a minus sign, fraction grouping, unit or learner claim.

For 600 messages, 24 development and six reserved examples per intent give 480 and 120 respectively. Keep related conversation roots and paraphrase families together when assigning splits. Do not randomly divide sibling utterances between development and final tests.

## 2 4 Sources and acquisition

**Existing assets and NCERT.** Reuse checked cards, misconceptions, public practice items and development fixtures. Obtain textbook and exemplar material from official NCERT portals, selecting only the scoped chapters. Retain provenance and the project's restrictions on redistributing textbook material. The answers appendix is not a tutoring retrieval source. [S8, S9]

**Team-authored in-scope dialogue.** A domain reviewer specifies a misconception and development problem. An adult team member role-plays the learner, using realistic English and incomplete reasoning. Another member or a draft tutor supplies candidate replies. A teacher or designated domain reviewer edits and approves the teaching moves. Distinguish AI-generated, role-play and actual-session origins. Synthetic drafting becomes human-reviewed only when a named person performs that review.

**MathDial for research and selected examples.** Study a small training/development sample for scaffolding patterns. Do not put full transcripts into the knowledge index: they contain answers and do not match our curriculum. The official GitHub repository states CC BY-SA 4.0, while its Hugging Face card lists CC BY 4.0. Resolve terms for the exact artifact before copying or redistributing content. [S2, S3]

**MRBench for rubric and judge development.** Its annotated responses can inform labels and evaluator tests. Keep it separate from our final in-scope evaluation. MRBench uses MathDial and Bridge contexts, so differently named public datasets can overlap. The repository states CC BY-SA 4.0; record the chosen release and reuse terms. [S5]

**Executed development sessions.** After integration, capture consented adult team role-play or synthetic-learner runs with model and tool provenance. Review naturalness and helpfulness. Do not scrape private student chats or ask children for data for this capstone. A real-user pilot is a separate approved activity.

## 2 5 Record structure and quality checks

Every collection needs stable IDs, creation date, source and version/hash, origin, reviewer, review date, status and split. Distinguish raw, normalized, mathematically checked, pedagogically reviewed and approved-for-use states. Mathematical verification cannot substitute for pedagogical approval.

A dialogue also needs its active problem reference, chapter, concept, misconception where applicable, mode, speakers, ordered messages, expected teaching moves, permitted tools and expected outcome. Store reference answers and evaluation-only labels outside the tutor's view.

A language example needs its conversation prefix when required, raw learner wording, intended interpretation, intent, tags, expected route and acceptable response policy. Open English replies need semantic or rubric assessment, not exact-string matching.

A response pair needs a shared context, good and poor candidates, a preference rationale and labels for correctness, guidance and leakage. Poor replies must not enter the positive few-shot library.

A recorded session needs configuration/model IDs, prompt/content versions, tool calls, actual model-call counts, status, failures and available latency, token and cost measurements. Missing usage remains unknown. Teacher labels and judge labels remain distinguishable.

## 2 6 When the data is enough

Enough to start means the seed covers all 30 misconceptions and all 20 primary intents, with review. Begin integration while collecting the remainder. Add missing situations before adding more near-duplicate examples.

Enough for the capstone means reserved data stays outside tuning, required behaviours have examples and the Section 3 acceptance checks pass. Inspect errors by chapter, misconception, intent and language tag. Overall averages must not hide failure on ambiguous answers or rare human-help requests.

Compare development behaviour after 30 and 60 reviewed dialogues and after 200, 400 and 480 development messages, using the same evaluation method and budget. The 30 reserved dialogues and 120 reserved messages are for final testing, not prompt selection.

A 60-case final subset or 40 simulated learners supports a capstone report with limitations, not production reliability or real-user effectiveness. If a final test exposes a defect, record the deviation and reserve genuinely new cases after repair. Do not tune on the failed test and report it as untouched.

# 3 How we will communicate with the user

## 3 1 The communication contract

Use English text chat in the existing application. Prefer short paragraphs, familiar words and one purposeful question in an ordinary teaching turn. The current policy proposes a 60-word limit. Each question should give the learner a clear next action. [P3]

Understand informal grammar without grading it. Explain necessary mathematical terms in everyday language. Use prior work and the current problem so the learner need not repeat themselves. Adapt explanations from observed responses, not assumptions about ability or personality. Identify the tutor as AI and provide visible source and human-help routes.

## 3 2 What happens on each message

1. Recover authenticated role, mode, active problem and relevant conversation state. A claim in chat cannot change permissions.
2. Apply input safety and privacy checks. Treat quoted homework and retrieved text as data, not instructions. Serious distress takes the approved human-handoff route before teaching.
3. Interpret the message in context. Extract a mathematical attempt only when unambiguous; otherwise ask a specific clarification without silently marking it wrong or advancing the hint stage.
4. Retrieve a checked reference or explanatory section and use permitted mathematical tools when checking an attempt or calculation.
5. Select the next teaching move from concept, misconception evidence, previous hints and observed progress.
6. Generate a short English response, then check leakage, mathematical consistency, mode and citation support before display.
7. Store permitted progress observations, replan after quizzes and follow the teacher-alert rule for repeated difficulty on the same concept across three sessions.

NLP interprets and phrases the interaction. Code owns mathematical checks, roles, quiz restrictions, state writes and publication approvals. Whether a hint is useful still needs semantic evaluation; a solver verdict or citation ID cannot prove it.

If responses stream, checks must act before unsafe text reaches the learner. Buffering these short replies before display is a reasonable starting design. Measure the latency rather than allowing an unchecked answer to appear token by token.

## 3 3 Behaviour in common situations

| Situation | Communication behaviour |
|---|---|
| Practice begins | Establish the problem and ask what the learner tried or which part is unclear, unless already known. |
| Wrong parseable attempt | Acknowledge it, use the tool verdict and ask one question aimed at the likely mistake. Protect the correct result. |
| Unclear English or notation | Name the ambiguity and clarify; avoid wrong-answer or mastery penalties. |
| Hint fails | Rephrase or change explanation style according to the approved ladder, rather than repeat wording. |
| Correct attempt | Confirm after checking and ask for a short reason or transfer step. The draft allows a method summary after the learner supplies the answer. |
| Quiz mode | Use the deterministic assessment path. The current draft says Recorded at item level, with no hint or correctness feedback before the quiz ends. |
| Ordinary frustration | Briefly acknowledge it, offer a break or simpler step and follow the approved safety policy. |
| Serious distress or human help | Use the approved handoff route. R4 owns safety wording and thresholds with policy approval; do not improvise counselling or contact details. |
| Out of scope or role claim | Briefly explain the scope or authenticated-role requirement and offer the relevant next action. |

Quiz acknowledgements, safety handoffs and error messages are exceptions to the one-question teaching format. They should serve their own purpose.

The draft after-last-hint policy proposes a fully worked parallel example after all three item hints and at least two scorable wrong attempts. Code must verify different numbers, a different answer and the worked steps. This changes the frozen dataset's practice restrictions and needs explicit R1/R4 acceptance. The active item's solution stays protected. [P3]

## 3 4 Example conversation

This is an authored practice illustration, not a recorded session or gold test. The task asks for the fifth term of an AP starting at 3 with common difference 2. Mathematical checks and retrieval happen outside the visible dialogue.

**Learner:** I did 3 plus five lots of 2 and got 13.

**Tutor:** You counted five jumps. The first term is already 3. How many jumps take you from the first term to the fifth?

**Learner:** Four jumps I think.

**Tutor:** Use that jump count with your starting value of 3 and a jump size of 2. What value do you get?

**Learner:** 11.

**Tutor:** Your answer is correct. Why did you use four jumps rather than five?

The tutor uses the learner's reasoning and lets them produce the correction. A conceptual explanation can show the AP nth-term card as a readable reference, mapped to an actually retrieved passage rather than an invented section or page.

A message such as I got 12 why different may need clarification when context is missing. During an ongoing problem, use the known task and prior attempt first. Confirm the intended interpretation when two mathematical readings are possible.

## 3 5 Interface and memory

Show the active problem and mode clearly. Useful practice controls are Hint, Explain more simply, Check my attempt, Try a similar problem and Ask for human help. Disable teaching aids during a quiz as required. Teacher publication controls belong to the authenticated teacher view.

Render source titles or section labels for learners and keep stable passage IDs in traces. Do not expose tool prompts, private keys, hidden simulator beliefs or evaluator labels. Recover honestly from tool errors instead of guessing a verdict.

Short-term context includes the problem, recent work, unresolved question and hint stages. Long-term memory contains justified mastery observations, misconception evidence and explanation styles that appeared helpful, under the agreed retention/deletion policy. The hidden simulator card is never copied into that memory.

## 3 6 Acceptance checks

These are proposed local gates unless an accepted team policy already sets the value. Agree them before final runs. Failed gates require a fix or explicit limitation, not a changed denominator.

| Area | Proposed evidence and decision rule |
|---|---|
| Actual model integration | New traces show tutor-model calls on intended tutor routes. Deterministic quiz and safety paths are intentional exceptions; report template fallbacks separately. |
| Language understanding | On 120 reserved messages, target intent macro F1 of at least 0.85 and at least 90 percent correct clarification routing on ambiguous examples. Report small-subset counts and uncertainty. |
| English teaching quality | Review contextual replies for clarity, actionability and continuity; propose at least 90 percent acceptable, with full/partial leaks reported separately. This is an engineering gate, not a population estimate. |
| Maths and modes | Retain passing typed-answer checks; no quiz hint or key exposure in the executed suite. Report leaks beside student progress. |
| Retrieval | Reviewed card and section labels; report Recall at 5 separately, plus semantic support of citations. |
| Human and judge evidence | Teacher rubric on 20 full executed transcripts; two raters independently label at least 30 contextual turns. Apply the team's kappa gate of at least 0.6, with uncertainty and human-agreement comparison. |
| Learning and security | Run agreed E1 to E4 configurations and required repeats. Count failures/timeouts and distinguish synthetic gains from real learning. |

The existing leak-detector target of at least 0.9 precision and recall is a separate team-policy gate. The 48 development fixtures support implementation; they are not a blind final security test. Cover all answer kinds and language styles. [P3]

## 3 7 Collection plan before submission

The proposed allocation follows current milestones; the official submission remains 12 November EOD and the viva 15 November.

| When | Deliverable | Proposed ownership |
|---|---|---|
| 2 to 3 November | Confirm policy/annotation rules; review 30 seed dialogues and 200 messages; verify model routing | R1/R2 content, R3 integration, R4 safety |
| 4 to 5 November | Complete 60 development dialogues and 480 messages; review glossary, response pairs and retrieval labels | R2 coordinates; R1 reviews pedagogy; R3 implements; R5 manages evaluation |
| By 6 November | Freeze 30 reserved dialogues and 120 messages, configuration and scoring rules; complete private exercise checks | R5 with independent author/reviewer; keep tuning and evaluation access separate |
| 7 to 9 November | Execute experiments, teacher review and two-rater labels; report agreement, failures and uncertainty | R5/proposed R5b, teacher and named raters; R6 supports traces |
| 10 to 12 November | Resolve documented defects/deviations; complete report, demo and submission | All roles with Lead coordination |

At an estimated 8 to 12 minutes per dialogue, 90 reviews require about 12 to 18 reviewer-hours. Message labels, calibration and transcript review add effort. Allocate people and time before increasing counts. If capacity is short, preserve coverage, independence and human checks while cutting optional variants.

Some scenario drafts are already shared in the team repository. Moving rewritten queries into a private folder does not erase prior exposure. R5 should document who saw scenarios, labels and cases, and use fresh independently authored reserved examples where strict blindness is required.

The next action is to agree an annotation sheet and review the 30-dialogue seed around the existing misconceptions. R3 can use those development examples immediately while collection and evaluation preparation continue.

# Sources and project evidence

External sources checked on 2 November 2026. Release counts and terms below do not establish project suitability or approval.

**S1** Macina and colleagues, MathDial, Findings of EMNLP 2023. Teacher-led dialogue, simulated confusions and teaching moves. https://aclanthology.org/2023.findings-emnlp.372/

**S2** Official MathDial repository. Released count of 2,861 conversations and repository licence statement. https://github.com/eth-nlped/mathdial

**S3** Official MathDial dataset card. Its licence label differs from the repository; resolve terms for the exact artifact. https://huggingface.co/datasets/eth-nlped/mathdial

**S4** Maurya and colleagues, Unifying AI Tutor Evaluation, NAACL 2025. Original MRBench and eight pedagogical dimensions. https://aclanthology.org/2025.naacl-long.57/

**S5** Official MRBench repository. Version sizes, annotation coverage, shared origins and CC BY-SA 4.0 statement. https://github.com/kaushal0494/UnifyingAITutorEvaluation

**S6** BEA 2025 shared task organizer page. Pedagogical evaluation and task/data descriptions. https://sig-edu.org/sharedtask/2025

**S7** Bastani and colleagues, Generative AI Without Guardrails Can Harm Learning, author-hosted paper; published in PNAS in 2025. Unassisted learning and effects of assistance design. https://hamsabastani.github.io/education_llm.pdf

**S8** Official NCERT textbook portal. Select current Class 10 Mathematics and the scoped chapters; retain edition and hashes. https://ncert.nic.in/textbook.php?jemh1=0-14

**S9** Official NCERT exemplar portal. Select Class X Mathematics and relevant units under the project source-use rules. https://ncert.nic.in/exemplar-problems.php?ln=en

**P1** Team checkout: Docs/LEAD_ROADMAP.md, Docs/DECISIONS.md and Docs/plan/01-requirements.md. Scope, source findings, course minima, roles and milestone proposals. Snapshot includes commits through 1 November; this review did not fetch or certify the remote branch.

**P2** Team checkout: Docs/spikes/S6.md, Docs/EXPERIMENT_LOG.md, Docs/specs/R3_AGENTS.md and eval/README.md. Recorded development runs, template-path finding, simulator voice, judge limits and integration work.

**P3** Team checkout: Docs/policy/TEACHING_POLICY.md, Docs/policy/TEACHING_SCENARIOS.md, eval/fixtures/leak_examples.jsonl and eval/judge_calibration/RATER_GUIDE.md. Draft policy, 45 scenarios, 48 development leak examples and human-rating process. These are not blanket teacher approval.

**P4** Dataset workspace: PROJECT_CONTEXT.md, Socratic_Tutor_Requirements.md, socratic_tutor_dataset_v2/reports/RELEASE_AUDIT.md and builds/v0.10.0/metadata/counts.json. Frozen maths inventory and review limits. Team public-content counts were checked directly; private evaluation cases were not opened for communication design.
