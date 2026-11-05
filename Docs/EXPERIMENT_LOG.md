# Experiment log

Every evaluation run, newest last, failed runs included. R5 owns this file; anyone who runs an experiment adds its entry the same day. The report quotes only numbers that trace back to a `run_id` here.

**Format:**

```
### YYYY-MM-DD · <run_id> · <purpose>
- **Config:** file and SHA-256; model IDs; seed
- **Data:** development or held-out, and which sets
- **Outcome:** what happened, failures and timeouts counted
- **Decision:** what changes because of it, with a link to Docs/DECISIONS.md if any
```

**Rules:**
- **No held-out data here, ever:** only hashes, counts and run IDs. Held-out files and IDs stay outside git (R5).
- **The held-out freeze is the first entry.** It is written by `python -m tutor_eval.freeze ... --log Docs/EXPERIMENT_LOG.md` when R5 runs the freeze.
- **A change to a frozen set after held-out results is a deviation.** Log it, move the affected cases to development, and say so in the report.

---

### 2026-10-31 · s6_cost-20261031-212818 · Spike S6: live cost of development sessions
- **Config:** `eval/configs/s6_cost.toml` (`7a3e081277a4`); arm c2, defences on; tutor `openai/gpt-4.1-mini`; student voice `meta-llama/llama-3.3-70b-instruct`; seeds 1, 2, 3; budget 40 calls / USD 0.15
- **Data:** development (POC cards `sim_v2_010`, `sim_v2_013`); 6 sessions, 48 turns
- **Outcome:** 0 failures; 0 tutor model calls (the POC's hint and grading paths are templates); 6 voice calls, 0 fallbacks, 2 of 6 openers dropped the equation; no leaks; not a result
- **Decision:** the voice must keep the equation (fixed); no further live tutor runs until R3's agents call the model. See [S6](spikes/S6.md)

### 2026-10-31 · s6_cost-20261031-212818/judge · Judge on 40 development turns
- **Config:** `src/tutor_eval/judge.py`; `google/gemini-3.1-flash-lite`, temperature 0; `--limit 40`
- **Data:** development; 40 turns of the run above
- **Outcome:** 40 labelled, 0 failed; leak "none" on all 40, matching the code checker; about USD 0.015 (estimated); labels not yet calibrated
- **Decision:** judge tokens are now logged; judge whole runs only for reported experiments

### 2026-10-31 · s3_retrieval-20261031-214425 · Spike S3: baseline card and hybrid retrieval
- **Config:** `config/app.toml` (`c0492e339f06`), `[retrieval]` cards `content/dataset-v0.10.0/corpus.jsonl`, index `data/ncert/index` (78 section chunks of `jemh104`, `jemh105`, `jemh108`, extracted with pdftotext 4.00 `-layout`), dense `BAAI/bge-small-en-v1.5` (fastembed 0.9.1, CPU), RRF k = 60, depth 20; deterministic, no seed; no model API calls
- **Data:** development only: the 15 development card queries from `plan_freeze(v0.10.0, 0)["dev_files"]`; labels assistant-proposed, not human
- **Outcome:** Recall@5 / MRR. Cards-only BM25 (POC tokenizer) 0.839 / 0.802. Cards-only BM25 (maths tokenizer) 0.861 / 0.736. Cards BM25 + dense 0.878 / 0.839. Hybrid BM25 + dense, card view 0.861 / 0.907. Hybrid BM25 + dense, strict (sections count as misses) 0.706 / 0.784. 0 failures. Not a result: 15 queries, and no section labels yet
- **Decision:** hybrid stays behind `[retrieval] mode = "hybrid"`, and the default remains `poc_cards`. Section retrieval is to be judged on Set B (section labels), not this card set. See [S3](spikes/S3.md)

### 2026-11-05 · dev_smoke-20261105-034645-3a15413b85af · M3 v2 ci-equivalent dev_smoke
- **Config:** dev_smoke.toml; SHA-256 `308d1c0e5f3b65385101abf365322bf5428041a2d3b4864613497e29f8f3f96b`; seeds [1]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `288b3a6bed713a6f841cb6f999d787e142b54a1f745d125aba1b72f87343bbe2` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 2, "turns": 16, "failures": 0, "timeouts": 0, "task_success": 1}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m2_development_c1-20261105-034642-996eb2e7fb5b · M3 v2 ci-equivalent m2_development_c1
- **Config:** m2_development_c1.toml; SHA-256 `7070083ca5688befcf2ecc3c9dcfd4b2481717d11cfa7734df67d8610ad25087`; seeds [1]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `fb1f25620dd2d2a845776634b48965746dc29171873ee66377519ad45400b7ee` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 2, "turns": 16, "failures": 0, "timeouts": 0, "task_success": 1}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_live_c0-20261105-035255-ce6b6b08a470 · M3 v2 live c0
- **Config:** m3_live_c0.toml; SHA-256 `b048aa2ca66f88445bfe5b7338fac44608cd1329879d426da3033a53d5f1c146`; seeds [1, 2, 3]; tutor `openai/gpt-4.1-mini via https://openrouter.ai/api/v1`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `4dc3bf17a7b6f047768b69fdfe0c546909bb4a6e8e4a0048594d18b052339710` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 48, "turns": 384, "failures": 0, "timeouts": 0, "task_success": 2}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_live_c1-20261105-035710-eabed6949ac0 · M3 v2 live c1
- **Config:** m3_live_c1.toml; SHA-256 `97f1038f58f8d2073d5b2593c89ce6e0ccadc67c3b9c3add1c5efafe507ed8e0`; seeds [1, 2, 3]; tutor `openai/gpt-4.1-mini via https://openrouter.ai/api/v1`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `fab85fdcfe635c2f5ef03af045fc6ff9c7d5734397afd99f72df894c60b8b304` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 48, "turns": 384, "failures": 0, "timeouts": 0, "task_success": 2}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_live_c2-20261105-040116-9c72acbd3556 · M3 v2 live c2
- **Config:** m3_live_c2.toml; SHA-256 `764b75452f4722a305758f31dcc0262d8fd9db2fb71182f64e8c0dae77c99215`; seeds [1, 2, 3]; tutor `openai/gpt-4.1-mini via https://openrouter.ai/api/v1`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `f2d920200f783cb7bc4247c13a2bdd339fbef88c89cdda282fe44b1506742bfe` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 48, "turns": 384, "failures": 0, "timeouts": 0, "task_success": 2}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_live_direct_answers-20261105-040638-d5b43f14862c · M3 v2 live direct_answers
- **Config:** m3_live_direct_answers.toml; SHA-256 `51590780641fc538cbe5f433b1bae48fc6b2a45d88d12c47be79b453fc5f8fa2`; seeds [1]; tutor `openai/gpt-4.1-mini via https://openrouter.ai/api/v1`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `745ce64b98d9e03f1c1835d06994782feae1437f63ba064e946a36a6f640f438` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 16, "turns": 128, "failures": 0, "timeouts": 0, "task_success": 0}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_live_e2_off-20261105-040747-556d00c75c03 · M3 v2 live e2_off
- **Config:** security case files recorded in manifest; SHA-256 `not_applicable_security_runner`; seeds case-specific; tutor `openai/gpt-4.1-mini via https://openrouter.ai/api/v1`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `aaf9a59b6c71d952c3ce09ca14883bfe2bfb53a1049ea57f03825e0d6a31a922` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"cases": 80, "unsupported": 27, "errors": 0, "attack_success_rate": 0.056, "false_block_rate": 0.0, "by_channel": {"user_message": {"attacks": 18, "succeeded": 1, "controls": 30, "falsely_blocked": 0, "unsupported": 20}, "homework_text": {"attacks": 0, "succeeded": 0, "controls": 2, "falsely_blocked": 0, "unsupported": 4}, "retrieved_passage": {"attacks": 0, "succeeded": 0, "controls": 2, "falsely_blocked": 0, "unsupported": 2}, "tool_result": {"attacks": 0, "succeeded": 0, "controls": 1, "falsely_blocked": 0, "unsupported": 1}}}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_live_e2_on-20261105-040704-425b0cf5ca59 · M3 v2 live e2_on
- **Config:** security case files recorded in manifest; SHA-256 `not_applicable_security_runner`; seeds case-specific; tutor `openai/gpt-4.1-mini via https://openrouter.ai/api/v1`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `65e0242e6901e633a2d9701f3838fdf6faeb9da15154bc4ed0ddb3854b7ee722` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"cases": 80, "unsupported": 27, "errors": 0, "attack_success_rate": 0.0, "false_block_rate": 0.0, "by_channel": {"user_message": {"attacks": 18, "succeeded": 0, "controls": 30, "falsely_blocked": 0, "unsupported": 20}, "homework_text": {"attacks": 0, "succeeded": 0, "controls": 2, "falsely_blocked": 0, "unsupported": 4}, "retrieved_passage": {"attacks": 0, "succeeded": 0, "controls": 2, "falsely_blocked": 0, "unsupported": 2}, "tool_result": {"attacks": 0, "succeeded": 0, "controls": 1, "falsely_blocked": 0, "unsupported": 1}}}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_live_e3_budget_tranche12-20261105-041430-c0f99159f485 · M3 v2 live e3_after_budget_tranche12
- **Config:** E3_BUDGET_TRANCHE.toml; SHA-256 `c70f53e2d6fb4ecd00ab706007d95b29a5f7370a2077fa56a0d087b5aad8d6df`; seeds [1, 2, 3]; tutor `openai/gpt-4.1-mini via https://openrouter.ai/api/v1`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `55cd59627f770b093ea6898bffa3cfbbcd6f0e0b8459521bbaf0f660e4fe93d2` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 36, "turns": 288, "failures": 0, "timeouts": 0, "task_success": 2}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_live_memory_off-20261105-040520-222f57a760ea · M3 v2 live memory_off
- **Config:** m3_live_memory_off.toml; SHA-256 `2cb061596893848863afc723186e51d630e920ed66761137266c6e38875a022e`; seeds [1]; tutor `openai/gpt-4.1-mini via https://openrouter.ai/api/v1`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `608a4a79bb5d75472f6706f022b1983202f87e143069be26f858341ea13b84ae` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 16, "turns": 128, "failures": 0, "timeouts": 0, "task_success": 1}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_offline_c0-20261105-033632-eaae4e0d820d · M3 v1 offline c0
- **Config:** m3_offline_c0.toml; SHA-256 `082fc78c22af8dd1ecc67bb4a0504d5daf74c7ea66019fac20141b994ef89eee`; seeds [1, 2, 3]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `c54f5f4d10f3487d8f4c577bc24b8c27e0f52a40ce8a0395fc822bc191bcc89a` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 48, "turns": 384, "failures": 0, "timeouts": 0, "task_success": 2}
- **Source:** `b4c290ba151a8a1a2361f3b0057e829382175113`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_offline_c0-20261105-035031-fb95ecb1f104 · M3 v2 offline c0
- **Config:** m3_offline_c0.toml; SHA-256 `082fc78c22af8dd1ecc67bb4a0504d5daf74c7ea66019fac20141b994ef89eee`; seeds [1, 2, 3]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `1e5da9032ac4c2bbb6a15522868208fa9de6efcf7ef37de0a9cbfed131060cf2` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 48, "turns": 384, "failures": 0, "timeouts": 0, "task_success": 2}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_offline_c1-20261105-033702-6bcbc19ac34b · M3 v1 offline c1
- **Config:** m3_offline_c1.toml; SHA-256 `54d7baad99e7d4efb0962fe385c6049fcb3fd89f88bb526925d65ad7c45171ce`; seeds [1, 2, 3]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `255f6d9d4464842ccab29efa60462dab02d635cb3bc1a08e5a0c292da8d7b8cc` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 48, "turns": 384, "failures": 0, "timeouts": 0, "task_success": 2}
- **Source:** `b4c290ba151a8a1a2361f3b0057e829382175113`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_offline_c1-20261105-035100-163b69bad13d · M3 v2 offline c1
- **Config:** m3_offline_c1.toml; SHA-256 `54d7baad99e7d4efb0962fe385c6049fcb3fd89f88bb526925d65ad7c45171ce`; seeds [1, 2, 3]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `719e9175df9736c355ba79654a7fcc6b0eca7bf99a040e4324ee485b59b1edba` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 48, "turns": 384, "failures": 0, "timeouts": 0, "task_success": 2}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_offline_c2-20261105-033728-24f8126311a1 · M3 v1 offline c2
- **Config:** m3_offline_c2.toml; SHA-256 `5a79e5472889caa6aa9b3b3121725294fff8563b771e087e06ee2e209599f2ba`; seeds [1, 2, 3]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `aad403990917629a7b7502effef10d02d09026050c88186f6ffcf2975604fb5f` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 48, "turns": 384, "failures": 0, "timeouts": 0, "task_success": 2}
- **Source:** `b4c290ba151a8a1a2361f3b0057e829382175113`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_offline_c2-20261105-035126-862a505fcdbf · M3 v2 offline c2
- **Config:** m3_offline_c2.toml; SHA-256 `5a79e5472889caa6aa9b3b3121725294fff8563b771e087e06ee2e209599f2ba`; seeds [1, 2, 3]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `ddf1863ee98368bf796d638c2bb31b7e20dbb8eee901c1feb12e24ae14b39cb5` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 48, "turns": 384, "failures": 0, "timeouts": 0, "task_success": 2}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_offline_direct_answers-20261105-033802-c289e6e41435 · M3 v1 offline direct_answers
- **Config:** m3_offline_direct_answers.toml; SHA-256 `f0b7aeb14c77b184429705d1c4a361ce4cdc4a900aba021092914f4cdd8c6545`; seeds [1]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `97cb1c210e86049b4e9615fbc05deb815b39118c732167ae6367dc98dfdd458f` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 16, "turns": 128, "failures": 0, "timeouts": 0, "task_success": 0}
- **Source:** `b4c290ba151a8a1a2361f3b0057e829382175113`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_offline_direct_answers-20261105-035200-918e3ea37af1 · M3 v2 offline direct_answers
- **Config:** m3_offline_direct_answers.toml; SHA-256 `f0b7aeb14c77b184429705d1c4a361ce4cdc4a900aba021092914f4cdd8c6545`; seeds [1]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `7faab87312ce0ad89b0be3d179d3e1ba815ec989277ea3e1f03ad12190707b0d` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 16, "turns": 128, "failures": 0, "timeouts": 0, "task_success": 0}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_offline_e2_off-20261105-033846-4476b949acf6 · M3 v1 offline e2_off
- **Config:** security case files recorded in manifest; SHA-256 `not_applicable_security_runner`; seeds case-specific; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `d721fdf4645b829a0998edf834567066779b4d69582a8b7ee970c7e232272a3e` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"cases": 80, "unsupported": 30, "errors": 0, "attack_success_rate": 0.056, "false_block_rate": 0.0, "by_channel": {"user_message": {"attacks": 18, "succeeded": 1, "controls": 30, "falsely_blocked": 0, "unsupported": 20}, "homework_text": {"attacks": 0, "succeeded": 0, "controls": 2, "falsely_blocked": 0, "unsupported": 4}, "retrieved_passage": {"attacks": 0, "succeeded": 0, "controls": 0, "falsely_blocked": 0, "unsupported": 4}, "tool_result": {"attacks": 0, "succeeded": 0, "controls": 0, "falsely_blocked": 0, "unsupported": 2}}}
- **Source:** `b4c290ba151a8a1a2361f3b0057e829382175113`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_offline_e2_off-20261105-035246-88fc106abca9 · M3 v2 offline e2_off
- **Config:** security case files recorded in manifest; SHA-256 `not_applicable_security_runner`; seeds case-specific; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `b7109d7a22381ff5444678c9a7685c6a8fa3e870f605419f7634ba7ffc628c8e` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"cases": 80, "unsupported": 27, "errors": 0, "attack_success_rate": 0.056, "false_block_rate": 0.0, "by_channel": {"user_message": {"attacks": 18, "succeeded": 1, "controls": 30, "falsely_blocked": 0, "unsupported": 20}, "homework_text": {"attacks": 0, "succeeded": 0, "controls": 2, "falsely_blocked": 0, "unsupported": 4}, "retrieved_passage": {"attacks": 0, "succeeded": 0, "controls": 2, "falsely_blocked": 0, "unsupported": 2}, "tool_result": {"attacks": 0, "succeeded": 0, "controls": 1, "falsely_blocked": 0, "unsupported": 1}}}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_offline_e2_on-20261105-033840-84a41823d809 · M3 v1 offline e2_on
- **Config:** security case files recorded in manifest; SHA-256 `not_applicable_security_runner`; seeds case-specific; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `1d9c169f974a88feb4f524f8a639ee0609186eed9154d07b8067cd96a975f0d7` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"cases": 80, "unsupported": 30, "errors": 0, "attack_success_rate": 0.056, "false_block_rate": 0.0, "by_channel": {"user_message": {"attacks": 18, "succeeded": 1, "controls": 30, "falsely_blocked": 0, "unsupported": 20}, "homework_text": {"attacks": 0, "succeeded": 0, "controls": 2, "falsely_blocked": 0, "unsupported": 4}, "retrieved_passage": {"attacks": 0, "succeeded": 0, "controls": 0, "falsely_blocked": 0, "unsupported": 4}, "tool_result": {"attacks": 0, "succeeded": 0, "controls": 0, "falsely_blocked": 0, "unsupported": 2}}}
- **Source:** `b4c290ba151a8a1a2361f3b0057e829382175113`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_offline_e2_on-20261105-035238-656df96de66e · M3 v2 offline e2_on
- **Config:** security case files recorded in manifest; SHA-256 `not_applicable_security_runner`; seeds case-specific; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `ce5d0a2ddfd342fa0c92a36dc711cab55e33499c3ca30640f1612f2043d79a9e` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"cases": 80, "unsupported": 27, "errors": 0, "attack_success_rate": 0.0, "false_block_rate": 0.0, "by_channel": {"user_message": {"attacks": 18, "succeeded": 0, "controls": 30, "falsely_blocked": 0, "unsupported": 20}, "homework_text": {"attacks": 0, "succeeded": 0, "controls": 2, "falsely_blocked": 0, "unsupported": 4}, "retrieved_passage": {"attacks": 0, "succeeded": 0, "controls": 2, "falsely_blocked": 0, "unsupported": 2}, "tool_result": {"attacks": 0, "succeeded": 0, "controls": 1, "falsely_blocked": 0, "unsupported": 1}}}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_offline_e3_after-20261105-033812-6f25afbfa333 · M3 v1 offline e3_after
- **Config:** m3_offline_e3_after.toml; SHA-256 `2cd1e1550ab520fbf20b6ce3f7632cd9eee3f7234a4ace2a66cf574aa72120a5`; seeds [1, 2, 3]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `dc42d1f0d232680546c891dd84c5c4c07b986f7c5707cb9beb0b869663e0276b` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 48, "turns": 384, "failures": 0, "timeouts": 0, "task_success": 2}
- **Source:** `b4c290ba151a8a1a2361f3b0057e829382175113`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_offline_e3_after-20261105-035211-aa47e72f5330 · M3 v2 offline e3_after
- **Config:** m3_offline_e3_after.toml; SHA-256 `2cd1e1550ab520fbf20b6ce3f7632cd9eee3f7234a4ace2a66cf574aa72120a5`; seeds [1, 2, 3]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `e53f3d33c4b27c54dc8d1f96eeaed141156e59afbaf48d4a7e10a462d9ede7fb` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 48, "turns": 384, "failures": 0, "timeouts": 0, "task_success": 2}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_offline_memory_off-20261105-033754-56cc2a68a71c · M3 v1 offline memory_off
- **Config:** m3_offline_memory_off.toml; SHA-256 `95267f535734675be6a61e93049f143673084d881c7ccf80e7c3f4b4eabda87b`; seeds [1]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `2f47ecd7ac57784957618f7a2b98ce93209f8581b03d3a6bce0212bfe1359af8` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 16, "turns": 128, "failures": 0, "timeouts": 0, "task_success": 1}
- **Source:** `b4c290ba151a8a1a2361f3b0057e829382175113`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_offline_memory_off-20261105-035152-47161db0cbe8 · M3 v2 offline memory_off
- **Config:** m3_offline_memory_off.toml; SHA-256 `95267f535734675be6a61e93049f143673084d881c7ccf80e7c3f4b4eabda87b`; seeds [1]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `a219247376d826b2831212138890d4610e74eab186f7b6f35e18ec5de37e3d7b` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 16, "turns": 128, "failures": 0, "timeouts": 0, "task_success": 1}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_pilot_c1-20261105-034818-e6be7a28d6d1 · M3 v2 pilot c1
- **Config:** m3_pilot_c1.toml; SHA-256 `fcd4dc4839d99eb215c8a7f8c4d4592286f965a4e379091bd615f88840ba0093`; seeds [1]; tutor `openai/gpt-4.1-mini via https://openrouter.ai/api/v1`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `d9c13b8fd782dacf81fef6b9fda940667f2eecc81a563c8e26500299c32ace11` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 2, "turns": 16, "failures": 0, "timeouts": 0, "task_success": 0}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_pilot_c2-20261105-034833-7b65ca5897c2 · M3 v2 pilot c2
- **Config:** m3_pilot_c2.toml; SHA-256 `533ee181142c4368cda59c05dc045da5311a8f474e43817e25e8b03a4e1d5133`; seeds [1]; tutor `openai/gpt-4.1-mini via https://openrouter.ai/api/v1`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `108a5b3ec708cdcbefcff79b6ffedc466ebbf522e2ca0e13f678b9396ac3c665` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 2, "turns": 16, "failures": 0, "timeouts": 0, "task_success": 0}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_smoke_c0-20261105-033529-599d357ffc8c · M3 v1 smoke c0
- **Config:** m3_smoke_c0.toml; SHA-256 `46fc3c880075bd7b1aa61c7f55de1e950dccea8e6616511132fb54b40ba11f63`; seeds [1]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `9f4ca35dbbcd4a938bc909665ee6936a654a31cdd480ee7ef76a99bbcb03e6b5` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 2, "turns": 16, "failures": 0, "timeouts": 0, "task_success": 0}
- **Source:** `b4c290ba151a8a1a2361f3b0057e829382175113`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_smoke_c0-20261105-034629-82d95730fbd3 · M3 v2 smoke c0
- **Config:** m3_smoke_c0.toml; SHA-256 `46fc3c880075bd7b1aa61c7f55de1e950dccea8e6616511132fb54b40ba11f63`; seeds [1]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `2d7cd7759f0ad4e7f19bae3336920e575bfd02986987344cf358d35cbac8adb7` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 2, "turns": 16, "failures": 0, "timeouts": 0, "task_success": 0}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_smoke_c1-20261105-033533-844f875fb037 · M3 v1 smoke c1
- **Config:** m3_smoke_c1.toml; SHA-256 `03cc43f35e7e63703cb408749b1425560834130fa74f0bf0880c1874cb07eae0`; seeds [1]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `82dae9d233a8fdade66af1c8b814555a0f286d7f77606d97d4565fa3921b7bc5` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 2, "turns": 16, "failures": 0, "timeouts": 0, "task_success": 0}
- **Source:** `b4c290ba151a8a1a2361f3b0057e829382175113`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_smoke_c1-20261105-034632-a99b049b7898 · M3 v2 smoke c1
- **Config:** m3_smoke_c1.toml; SHA-256 `03cc43f35e7e63703cb408749b1425560834130fa74f0bf0880c1874cb07eae0`; seeds [1]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `a4d99408c7c00c28c40a6bb243674187f2bd4fd94f55968c2571076b03506e6c` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 2, "turns": 16, "failures": 0, "timeouts": 0, "task_success": 0}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_smoke_c2-20261105-033535-e0ef0e130a6f · M3 v1 smoke c2
- **Config:** m3_smoke_c2.toml; SHA-256 `55eb3663f05b6120600ec02334fb8c241c49ffc9010a1c0e47a17a5b95ea91d4`; seeds [1]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `8ae3f4e1ba886b3b71aecebd82da065a9c92ab660ccb337c4468ccde2cb1af9d` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 2, "turns": 16, "failures": 0, "timeouts": 0, "task_success": 0}
- **Source:** `b4c290ba151a8a1a2361f3b0057e829382175113`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_smoke_c2-20261105-034634-30b95d4f5e42 · M3 v2 smoke c2
- **Config:** m3_smoke_c2.toml; SHA-256 `55eb3663f05b6120600ec02334fb8c241c49ffc9010a1c0e47a17a5b95ea91d4`; seeds [1]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `8250d4bfe2af52122ce37abae82119abd5d2040abb2db43ab426acedd0f7e00f` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 2, "turns": 16, "failures": 0, "timeouts": 0, "task_success": 0}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_smoke_direct_answers-20261105-033538-d860326fd075 · M3 v1 smoke direct_answers
- **Config:** m3_smoke_direct_answers.toml; SHA-256 `178bf81a043c46b2dd7bffb534ec613523983ba941a3166c314b3dcefe8e3909`; seeds [1]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `2766d78293220734be960a7366e737826d57934e418564d17afd137eed12cf73` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 2, "turns": 16, "failures": 0, "timeouts": 0, "task_success": 0}
- **Source:** `b4c290ba151a8a1a2361f3b0057e829382175113`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_smoke_direct_answers-20261105-034637-b9c87b2cd474 · M3 v2 smoke direct_answers
- **Config:** m3_smoke_direct_answers.toml; SHA-256 `178bf81a043c46b2dd7bffb534ec613523983ba941a3166c314b3dcefe8e3909`; seeds [1]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `fee6b6dc0aaa91dfc71e1197d575d8e393670b59711426a1bf9d3237091a9faf` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 2, "turns": 16, "failures": 0, "timeouts": 0, "task_success": 0}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_smoke_e3_after-20261105-033540-ad0380297915 · M3 v1 smoke e3_after
- **Config:** m3_smoke_e3_after.toml; SHA-256 `f8e4612f412bd451342a89321d41528e02e250bdecd60621ce6b2e448ccadb13`; seeds [1]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `46ff8f55938e12c1d8384502f89343ed1ea764f995d06f4fd1ae713058e23df3` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 2, "turns": 16, "failures": 0, "timeouts": 0, "task_success": 0}
- **Source:** `b4c290ba151a8a1a2361f3b0057e829382175113`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_smoke_e3_after-20261105-034639-4165e073395a · M3 v2 smoke e3_after
- **Config:** m3_smoke_e3_after.toml; SHA-256 `f8e4612f412bd451342a89321d41528e02e250bdecd60621ce6b2e448ccadb13`; seeds [1]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `65630f1be4bee602475930c1f2fde9272dd11ee6d07440eae4ef567c9977894a` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 2, "turns": 16, "failures": 0, "timeouts": 0, "task_success": 0}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_smoke_memory_off-20261105-033537-923b1af1b0cc · M3 v1 smoke memory_off
- **Config:** m3_smoke_memory_off.toml; SHA-256 `0050a76c2ed9f155289008c5e434bd415bd3e2952c0a7ebf660154abfd23a19d`; seeds [1]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `cefda3f4fa894fea529f62c698361536abdf8b915a3fce095ac640cc3c4c4449` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 2, "turns": 16, "failures": 0, "timeouts": 0, "task_success": 0}
- **Source:** `b4c290ba151a8a1a2361f3b0057e829382175113`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_smoke_memory_off-20261105-034635-ed07c7d8bee5 · M3 v2 smoke memory_off
- **Config:** m3_smoke_memory_off.toml; SHA-256 `0050a76c2ed9f155289008c5e434bd415bd3e2952c0a7ebf660154abfd23a19d`; seeds [1]; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `a8feca07f385b23915b2c3434e6b9861f6babebc34858518abe3783584ad0872` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {"sessions": 2, "turns": 16, "failures": 0, "timeouts": 0, "task_success": 0}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3_v2_ci_security-20261105-034647-9b72a46d371f · M3 v2 ci-equivalent security_smoke
- **Config:** security case files recorded in manifest; SHA-256 `not_applicable_security_runner`; seeds case-specific; tutor `stub (TUTOR_LLM=stub)`.
- **Data:** existing synthetic development partitions/probes only; no candidate-final run. Exact data/code hashes and immutable manifest SHA-256 `fa535d073d219c836de9907a38a07c41debf25ecc92b3f7714e477e4ff7fcf8c` are indexed in `Docs/m4/RUN_RECEIPTS.json`.
- **Outcome:** {}
- **Source:** `12d541ed8dd4716bbcfee2a74bcb4215920a13fc`; dirty flag `False`.
- **Decision:** Development evidence only; preserved unchanged. See Docs/m4/RESULTS.md for interpretation. V1 urgent-routing failure is retained; v2 is a known-case fix. No final preregistration or human approval is inferred.

### 2026-11-05 · m3-post-copy-sensitivity-v1 · Post-hoc saved-trajectory analysis
- **Config:** `scripts/m3/post_copy_sensitivity.py`, SHA-256 `9d6a1243d0b92c32406997d3ea04411d677558a17343de52f1cde132c7a7545f`; unchanged frozen run_session AST, template voice, no tutor/model instantiated.
- **Data:** the six completed live tutoring conditions, 212 development sessions; exact manifest/session-file hashes in `Docs/m4/POST_COPY_SENSITIVITY.json`.
- **Outcome:** 212/212 baseline semantic reproductions; corrupt student input rejected; 83 copied post items match flag unions exactly. Disabling post copying leaves C0/C1/C2 mean gain at 0.104 each; matched arm differences and intervals in the linked JSON. Zero provider requests.
- **Decision:** exploratory sensitivity only; preserve original primary outcomes. The apparent C2/E3 quiz differences do not survive this intervention. This does not calibrate disclosure labels or establish learning. Final protocol/review and E3 extra-call approval remain pending.

### 2026-11-05 · m3_live_e3_remaining4-20261105-074756-8c7792e028ac · Approved E3 completion, last twelve development sessions
- **Config:** `eval/configs/m3_live_e3_remaining4.toml`, SHA-256 `98aeda46c6c09b1b9f021419e85119d9fd386584926e9480f661c8fba9751d19`; openai/gpt-4.1-mini, template voice, seeds 1/2/3, eight turns.
- **Approval:** explicit submitted user answer, up to 50 extra requests / additional USD 0.03, solely to finish the original E3 cohort. Private receipt hash `e2c3f5a954df88d0b1b7b5e37e8a576b6467d435c33f1e9e55cad68dcc8044a8`. Original 1,000-request ledger preserved byte-for-byte.
- **Data:** four remaining development source cards, 12 sessions, no final/held-out export or run. Same source/data/app config/playbook as the original tranche; only previously committed approval/budget plumbing differs.
- **Source:** clean commit `a46367500581c356cd2e6ac22558798ea39cbfc4`; manifest SHA-256 `5e1dd7c471eccf109dfa5c69c5ab25a803fd53154f05a0675548bdba2abf8ae5`.
- **Outcome:** 12/12 sessions, gate pass, zero failures/timeouts/model errors, 36 provider attempts, USD 0.0132756 provider-reported, all costs exposed.
- **Decision:** combine with the preserved original 36 sessions after exact unique student/seed matching to all 48 C2 sessions. Complete-development results and post-copy sensitivity are separately versioned in `Docs/m4/E3_COMPLETE_RESULTS.md`. No new human approval, independent content or learning effect is inferred.

### 2026-11-05 · m3-post-copy-sensitivity-e3-complete · Full development cohort saved-trajectory analysis
- **Config/data:** versioned `post_copy_sensitivity.py --include-extension`; same frozen transition function, 224 existing study sessions; exact source/input hashes in `Docs/m4/POST_COPY_SENSITIVITY_E3_COMPLETE.json`.
- **Outcome:** 224/224 baseline semantic replays matched; no new provider calls. All 48 E3 pairs matched C2; without post copying, E3-minus-C2 quiz difference is zero.
- **Decision:** retain original primary outcomes and the 212-session analysis. This post-hoc sensitivity neither calibrates disclosure labels nor establishes human learning.
