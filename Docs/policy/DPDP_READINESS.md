# DPDP readiness note (R1 policy)

**13 November 2026.** Scope: the anonymous Vercel beta (Neon Postgres, OpenRouter). Not legal advice. This note records what the team checked against the law and the code, and what it could not check.

## 1. Bottom line

The children's obligations under the Digital Personal Data Protection Act, 2023 (DPDP Act) are **not yet in force**. Section 9 of the Act and Rules 10 and 12 of the DPDP Rules, 2025 start **13 May 2027**, 18 months after the Rules were published on 13 November 2025. No source we found gives 13 March 2027. MeitY floated shortening the timeline in January 2026. As of the latest tracker we found (28 October 2026), nothing changing the dates has been notified. The October 2026 Removal of Difficulties Order fixed wording only. Our beta is likely to be used by under-18s, so from May 2027 it would need verifiable parental consent and would have to stop learner tracking, unless an exemption applies. A student project hosted on personal Vercel and Neon accounts is unlikely to count as an "educational institution" under the Fourth Schedule. Today the app has explicit consent for sending chat to the model provider, a clear notice and a working delete. It has no age or parent step, no retention limit, and no breach procedure.

## 2. Timeline

| Phase | What starts | Date | Status |
|---|---|---|---|
| Publication | DPDP Rules G.S.R. 846(E). Rules 1, 2 and 17–21 (Data Protection Board) start, along with the Act's Board and definitions sections (G.S.R. 843(E)) | 13 Nov 2025 | Verified from the Rule 1 text as reproduced; date agreed across sources |
| +12 months | Rule 4 (consent managers) | 13 Nov 2026 | Rule 1(3) says "one year after"; the date is our calculation |
| +18 months | Rules 3, 5–16, 22, 23: notice, security, breach, erasure, children (Rules 10 and 12). Act Sections 4–17 | **13 May 2027** | Rule 1(4) says "eighteen months after"; the date is our calculation, matched by trackers and DSCI. Some sources say 14 May |
| Jan–Feb 2026 | MeitY proposal to shorten the period from 18 to 12 months, reportedly for Significant Data Fiduciaries | Reported 22/23 Jan 2026; comment deadline reported as 4 Feb 2026 | **Not adopted** as of 28 Oct 2026, per tracker. A Lok Sabha answer on 12 Aug 2026 still said eighteen months |
| Removal of Difficulties Order, S.O. 5458(E) | Adds "of" in Section 9(1) and changes "audit" to "data audit" in Section 10(2)(c)(ii). No deadline change | Dated about 5 Oct 2026; Gazette 6 or 7 Oct 2026 | Secondary reports only |

Sources: [Rule 1 text (unofficial mirror)](https://dpdp1.pages.dev/rule/1), [Rule 10](https://dpdp1.pages.dev/rule/10), [SCC Online](https://www.scconline.com/blog/post/2025/11/14/meity-notified-digital-personal-data-protection-rules-2025/), [AZB & Partners](https://www.azbpartners.com/bank/update-indias-digital-personal-data-protection-framework-comes-into-effect/), [DSCI brief](https://www.dsci.in/files/content/knowledge-centre/2025/Insight-Brief-on-DPDP-Rules.pdf), [18-to-12-month tracker](https://dpdprules.org/blog/dpdp-18-months-to-12-months-proposal), [Conventus Law on S.O. 5458(E)](https://conventuslaw.com/report/india-a-missing-of-and-a-missing-data-the-dpdp-removal-of-difficulties-order-2026/), [Act text (MeitY)](https://www.meity.gov.in/static/uploads/2024/06/2bf1f0e9f04e6fb4f8fef35e82c42aa5.pdf).

**13 March vs 13 May 2027.** Eighteen months from 13 Nov 2025 is 13 May 2027. Every tracker and law-firm note we found gives May. The India Briefing figure looks like an error, but we did not open that article to confirm what it says.

## 3. Obligations and our gaps

Under the Act, a child is anyone under 18. Penalties are in the Schedule to the Act: up to Rs 250 crore for failing to take reasonable security safeguards, and up to Rs 200 crore each for failing to notify a breach or breaching the children's duties in Section 9. The Data Protection Board sets the actual amount by severity. Line references are in `D:\Work\IITB\Socratic Tutor Main`.

| Obligation (in force 13 May 2027) | Current state in our app | Gap / action | Owner |
|---|---|---|---|
| **Applicability.** Pseudonymous IDs linked to free-text chat can be personal data. The research exemption (Section 17(2)(b)) does not cover tutoring individual learners | Signed random browser ID (`src/socrates_beta/api.py:110-115`). Chat text is redacted for some personal details, but students can still type their own (`index.html:5` asks them not to) | Assume the Act applies. Do not plan around the research exemption | R1 |
| **Section 9(1), Rule 10: verifiable parental consent** before processing a child's data. The parent must be an identifiable adult (existing records, voluntary details, or a DigiLocker-type token) | No age question and no parent step. The catalogue targets Class 8–12 (`api.py:42`) | Before May 2027: add an age gate. Under 18 needs a parent-consent flow, or the app runs only in a no-storage, no-model mode. A consent checkbox ticked by the student does not count | R1 design, R2 build |
| **Section 9(3): no tracking, behavioural monitoring or targeted ads** directed at children | No ads. But the app stores per-learner `observations`, assessments, card reviews and a revisit queue to choose the next teaching step (`src/socrates_beta/repository.py:23-34`, `src/socrates_beta/postgres.py:19-28`) | Learner modelling is likely "behavioural monitoring". For under-18s, switch it off, or make it session-only, unless an exemption applies | R2 |
| **Rule 12 / Fourth Schedule exemption.** Part A covers an "educational institution", but only for tracking and monitoring for its own educational activities or the safety of enrolled children. Section 9(2) (no detrimental effect) still applies | Run by a student team on personal Vercel and Neon accounts, not by a school | We probably do not qualify. An ed-tech vendor does not inherit a school's exemption. If IITB or a school ran it for enrolled students, check again with that institution | R1 |
| **Section 5, Rule 3: notice.** Standalone and plain. It must list the data and purposes, how to withdraw consent and use rights, and how to complain to the Board. Available in English or any Eighth Schedule language on request | Short consent text (`src/socrates_beta/static/index.html:5`) and storage notice (`index.html:5`, `static/app.js:74`). Nothing on the Board, no contact point, no retention period, no named processors (Vercel, Neon), no Hindi version | Write a one-page privacy notice linked from onboarding. Include a grievance contact and Hindi text | R1 |
| **Consent and withdrawal (Section 6).** Withdrawing must be as easy as giving | Opt-in checkbox before chat reaches OpenRouter, enforced on the server (`api.py:44`, `api.py:67-71`). Withdrawal blocks future model calls (`Docs/deploy/VERCEL_BETA.md:51-52`) | Good model. Withdrawing does not delete past data or tell the provider; say so in the notice | R1 |
| **Section 8(7), 12: erasure.** Erase on request or when consent is withdrawn, and when the purpose ends. Rule 8's fixed 3-year periods cover only large e-commerce, gaming and social media platforms | `POST /api/forget` deletes this browser's turns, sessions, assessments, observations, cards, reviews, revisit queue and profile (`api.py:246-249`, `repository.py:239-246`) | No time limit. Rows stay after the 30-day cookie expires (`api.py:115`), and then nobody can reach them to delete them. Add a scheduled deletion (for example 30–90 days after last activity). Write down that Neon point-in-time and backup copies, and OpenRouter or upstream provider copies, are not deleted (`VERCEL_BETA.md:55`) | R2 policy, R6 job |
| **Rule 8(3): keep processing logs for at least one year** (for the Seventh Schedule purposes) | No application access log kept. Vercel and Neon platform logs follow those vendors' settings | Find out Vercel and Neon log retention. Decide what minimal log to keep for one year without keeping chat text | R6 |
| **Section 8(5), Rule 6: reasonable security safeguards** | HttpOnly, Secure, SameSite Strict signed cookie; CSP; same-origin JSON check; host allowlist (`api.py:102-120`). Provider key stored in Vercel's encrypted environment | Write down encryption at rest (Neon), who can access the database, and backups. Rule 6 expects access control, monitoring and logs | R6 |
| **Section 8(6), Rule 7: breach notice.** Tell each affected user without delay, and the Board without delay, with a full report within 72 hours | No procedure. Users are anonymous, so we cannot contact them | Write a one-page incident runbook: who decides, how to rotate keys and secrets, a banner on the site, Board report template | R6, R1 |
| **Processors (Section 8(2)).** We remain responsible for Vercel, Neon and OpenRouter | Consent covers OpenRouter only. No data-processing terms checked. Vercel and Neon regions not documented | Record each processor, its region and its retention terms. Overseas transfer is allowed unless the government restricts a country under Section 16; none restricted yet | R6 |
| **Section 8(10), 13: grievance redress and a contact** | None | Add a contact address and a response promise to the notice | R1 |

## 4. What we can truthfully say today (viva or report)

- "The DPDP Rules were notified on 13 November 2025. The children's provisions and most duties of data fiduciaries start on 13 May 2027, so they do not legally bind the beta yet. We designed toward them anyway."
- "Nothing goes to the model provider until the visitor ticks an explicit opt-in. The server enforces it, and the visitor can withdraw it."
- "No name or account is needed. Data is tied to a random signed browser cookie, and 'Forget my data' deletes every application table for that browser."
- "Our deletion is logical deletion in our database only. It does not reach Neon backups or the provider."
- "We have no age check or parental consent, and we keep per-learner progress records. Before May 2027 we would need an age gate and parental consent, or a no-storage mode for under-18s. A student project probably cannot use the educational-institution exemption."
- Do **not** say that the app is "DPDP compliant", that it has parental consent, that data is never stored, or that a person reviewed our data handling.

## 5. Not verified

- We did not read the official Gazette PDFs for G.S.R. 846(E), G.S.R. 843(E) or S.O. 5458(E). Rule wording comes from unofficial mirrors and law-firm summaries. The exact 13 May 2027 date is a calculation; no MeitY notice states it.
- What the India Briefing article actually says about 13 March 2027.
- Whether any change to the timeline was notified after 28 October 2026.
- The full Fourth Schedule wording, including the Part B purposes and the definition of "educational institution". The rule number (12 in the final Rules, 11 in the draft) comes from secondary sources.
- The exact penalty amounts by entry, as worded in the Act's Schedule (from memory and summaries).
- Data retention and region for Vercel, Neon and OpenRouter, and the terms for any upstream model provider.
- Whether pseudonymous browser data alone counts as "personal data" in a given case.
