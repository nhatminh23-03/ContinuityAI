# UI Design Review — Phase 4

**Date:** 2026-08-17 · **Author:** Person B · **Inputs:** the six mockups in `UI Design/`
(each folder: `screen.png`, `code.html`, `DESIGN.md`), the binding design system and correction
list (working brief §A and §C), `docs/BACKEND_GAPS.md`, and the live payloads in
`docs/api-samples/`.

Ruling context: canonical values are DEC-01's (Payment Gateway **74/HIGH**, simulation
**74 → 93, HIGH → CRITICAL**, Identity 68, five capabilities, **Maria Gomez**), and the challenge
workflow UI **is in scope** (DEC-10 accepted). Corrections below re-base brief §C onto those
values; every §C intent stands.

The mockups are **art direction only**: layout and visual language are the reference; text,
numbers, labels, and data shapes are corrected against the specifications.

**One shared token sheet.** All six `DESIGN.md` files are byte-identical — a single Material-style
token export (Inter; warm near-white surfaces `#fcf8fa`–`#e4e2e4`; dark-slate on-surface
`#1b1b1d`; black primary; one error red `#ba1a1a`). Adopt the neutrals and the Inter type ramp as
the starting token set. Overridden by brief §A where they conflict: the mesh-gradient background
layer (absent from every mockup — restore), frosted ~85%-white cards with 20px radius, and the
four-status color discipline (the sheet's generic `error` red is *not* a status color; deep rose /
warm ochre / muted teal / dashed grey are the only saturated colors, applied to capabilities and
systems only).

---

## Mockup 1 — `dashboard/`

**Screen:** Dashboard (golden-path step 1). **Fed by:** `GET /platforms` +
`GET /platforms/{id}/systems` (both platforms; systems merged, sorted by risk desc).

**Usable as-is:** overall structure — left sidebar, page title + framing question
("Where does critical capability depend on one person?" is good copy), two platform cards above a
systems list; card proportions and generous whitespace; large light-weight metric numerals.

**Must change:**

1. Platform card values are invented: Payments **74** (not 58), Identity **68** (not 34). Label
   "RISK METRIC" → **"Highest system risk"** (it is a system index surfaced to the platform, per
   CI-10 — not a platform score).
2. **Remove the DEGRADED / COVERED pills from platform cards** — platform-level exposure class was
   frozen out under CI-10. No replacement.
3. Add `critical_gap_count` to each platform card ("1 critical gap" on both, live). Add
   `single_expert_dependency_count` **only if GAP-01 is approved** (`docs/BACKEND_GAPS.md`); until
   then the card carries gaps + drift only.
4. Drift is a color-only dot → render **text**: "Drift: new risk / risk increased / stable /
   risk reduced" (four wire values, mapped copy; Payments is `NEW_RISK`, Identity `STABLE`).
   Neutral text, not a saturated color — drift is not one of the four status classes.
5. Systems list: replace the three invented systems with the five real ones across both platforms
   (Payment Gateway 74 HIGH, Refund Engine 71 HIGH, Authentication 68 HIGH, Authorization 54
   MODERATE, Billing Integration 52 MODERATE). Add the **risk index per row, right-aligned,
   tabular, sorted descending**; show business criticality, exposure pill, evidence confidence,
   drift text.
6. **Remove the "DEPTH" label** (no value behind it). Remove prose subtitles ("Single maintainer
   dependency detected", "Documentation outdated by 14 months") — the second is an activity proxy;
   use the system `description` from the API or nothing.
7. Row icon tiles are saturated (red/blue) → monochrome; status color belongs to the exposure pill
   only.
8. Restore the mesh-gradient background layer behind frosted cards (§A) — the mockup lost it.

## Mockup 2 — `System-Detail/`

**Screen:** System Detail (golden-path step 2). **Fed by:** `GET /systems/{id}` + the unfocused
`GET /systems/{id}/graph` (capability names, exposure `status`, and criticality ride on graph
CAPABILITY nodes — design constraint 1 in `docs/BACKEND_GAPS.md`).

**Usable as-is:** breadcrumb; title + description block; four-cell metric strip with hairline
dividers; two-column body (graph canvas left, panels right); Declared Ownership card concept;
"Capabilities & Evidence" panel structure.

**Must change:**

1. **Metric strip:** "58 Elevated" → **74, class HIGH** ("Elevated" is not a valid class; with
   canonical data the corrected value is 74/HIGH, not the brief's stale "58 MODERATE"). 74 must
   not render red — risk-class chip colors: LOW muted teal · MODERATE warm ochre (light) · HIGH
   deep ochre · CRITICAL deep rose. "Dependencies / 3 critical" → **"Capabilities without
   resilient backup / 2"** (`degraded_capability_count`, the demo script's own wording; the brief's
   "Single-expert dependencies / 3" was stale and the true per-platform count awaits GAP-01).
   "Knowledge Gaps" → **"Critical gaps / 0"**. "Data Confidence" → **"Evidence confidence /
   HIGH"**.
2. **Replace "Edit System" with the primary action "Simulate unavailability"** — no edit endpoint
   exists, and simulation is the golden path's next step.
3. Add the **"Why this risk?" link** on the metric strip, driven by `rules_triggered`
   (`CRITICAL_CAPABILITY_DEGRADED`, `MULTIPLE_SOLE_EXPERT_CAPABILITIES` live) — opens the
   Why-panel (missing screen 2 below).
4. **Declared Ownership:** Maria Santos via "internal service registry sync" → **Jordan Lee,
   source CODEOWNERS**, with the ochre note **"Differs from demonstrated coverage"**
   (`mismatch_detected: true` live). This mismatch is the product's core demonstration (C.0).
5. **Capabilities panel:** correct names to the five real ones (Incident Recovery, Certificate
   Management, Provider Failover, Retry Logic, Monitoring). **Remove commit-count and activity
   chips** ("2 Commits (30d)", "1 PR Review", "No recent activity" — activity proxies are
   prohibited). Replace each with the **exposure pill + a coverage summary** ("1 validated ·
   1 assisted", composable from the graph's DEMONSTRATES edges per capability). **Move the
   signal-bar/ladder glyph off capabilities** — the ladder belongs to engineers only.
6. Add the **Coverage card**: Alex Chen, Maria Gomez, Jordan Lee with monochrome five-step
   readiness ladders (VALIDATED / ASSISTED / EXPOSED), freshness, and no numbers or ranking. Fed
   by `CapabilityDetail.engineer_coverage` for the focused capability, or graph edge metadata for
   the system view.
7. **Graph:** the mockup has no edges — floating pills and initials only. It must render the real
   14-node / 26-edge payload: solid **DEMONSTRATES** edges engineer → capability with thickness
   scaled by readiness (metadata carries readiness/freshness/confidence), and the one **dashed
   DECLARED_OWNER edge** Jordan Lee → Payment Gateway, labelled "declared owner". The
   solid-vs-dashed contrast is the most important visual in the product. Clicking a capability
   dims everything not connected to it, driven by `?focus_capability_id=` (which also brings in
   EVIDENCE nodes and `SUPPORTED_BY` edges).

## Mockup 3 — `Evidence-drawer/`

**Screen:** Evidence drawer / provenance ("Why?", golden-path step 3). **Fed by:**
`GET /capabilities/{id}/evidence` (optionally `?engineer_id=`), assessment block included.

**Usable as-is:** right-side drawer over a scrim; header with capability chip + engineer name;
scrollable evidence-card list with source ref, date, and indented italic excerpt — the list
structure fits the real 7-record payload well.

**Must change:**

1. **The "Knowledge Assessment" card is empty — populate it**: readiness (ladder), exposure,
   evidence confidence, `rules_triggered` copy, and the **declared-versus-demonstrated
   comparison** (`declared_vs_demonstrated`: declared Jordan Lee/CODEOWNERS vs strongest
   demonstrated Alex Chen, mismatch flagged).
2. **Every evidence card gains the typed model**: role badge (INDEPENDENT_EXECUTION /
   ASSISTED_EXECUTION / KNOWLEDGE_CAPTURE / CONTRIBUTION / EXPOSURE), strength (STRONG / MODERATE
   / WEAK), freshness (FRESH / AGING / STALE), source type icon, alongside source ref, date, and
   excerpt. The typed evidence model is the product's differentiator and is currently invisible.
3. Replace invented records (INC-142, PR-922, SLK-OPS…) with the real seven, strongest-first —
   `evidence_inc_184` (INDEPENDENT_EXECUTION / STRONG / FRESH) leads.
4. Add the **missing-evidence entries** (Jordan and Maria: "No qualifying independent incident
   recovery evidence found.") and the conflicting-evidence section when present — absence of
   evidence, never inability.
5. **Remove "Acknowledge Pattern"** — the mockup's premise ("no endpoint exists") is now outdated,
   but the button still goes: it is replaced by **"Challenge assessment"**, driving the DEC-10
   endpoint (missing screen 6 below). "Close" stays.

## Mockup 4 — `Stimulation-Sandbox/`

**Screen:** Simulation sandbox overlay (golden-path step 4). **Fed by:** `POST /simulations`
(ENGINEER_UNAVAILABLE, SYSTEM scope only — never offer PLATFORM, it 422s).

**Usable as-is:** modal-over-dim layout; before → after headline pair; capability impact matrix
with per-row state transitions; Cancel + primary CTA footer ("Find backup candidates" is exactly
the golden path).

**Must change (this mockup carries two of the three product-inverting defects):**

1. **The numbers are inverted: 93 → 58 must be 74 → 93.** Higher is worse. Relabel "System
   Resilience Score" → **"Continuity Risk Index"**, and show the class transition **HIGH →
   CRITICAL** beside the numbers.
2. **Delete the "Critical Silo Detected" panel** — it assigns Alex Chen "Level 5" knowledge with
   red signal bars labelled "Alex Chen's exclusive domain": a numeric competence level on a named
   person, risk color on a person, both prohibited. Express the fact as a capability statement:
   **"Incident Recovery — 1 engineer with validated readiness, no practiced backup."**
3. Remove "sudden departure", "standard project handover procedures fail", "Severe degradation…
   Immediate intervention required" — the model is unavailability, not departure, and the tool
   does not prescribe urgency. Use the API's grounded `summary` sentence instead.
4. Add the banner line **"Nothing has changed in your real data."** and the static disclaimer
   **"This models coverage loss. It does not predict an outage."** (frontend copy, CI-32).
5. Impact matrix: invalid states ("STABLE", "HIGH RISK") → only COVERED / DEGRADED / CRITICAL_GAP
   / INSUFFICIENT_EVIDENCE. Replace invented rows with the five real impacts, **including Retry
   Logic COVERED → COVERED and Monitoring COVERED → COVERED** — showing what survives is what
   makes the analysis credible. Add **best-remaining readiness** to every row (ASSISTED / PRACTICED
   / EXPOSED / VALIDATED / VALIDATED live). Add before → after gap/degraded/covered counts
   (0/2/3 → 2/1/2).

## Mockup 5 — `Back-up-Candidate/`

**Screen:** Backup candidates (golden-path step 5). **Fed by:**
`POST /recommendations/backup-candidates` (with `simulation_id` + `capability_id`).

**Usable as-is:** two side-by-side candidate cards; Technical Overlap HIGH / MEDIUM as the
headline (correct concept — never a percentage); the "Not considered in this comparison" panel
(genuinely good, keep prominent); breadcrumb back to context.

**Must change:**

1. **Replace Maria's photograph with monochrome initials** for both candidates — photographs
   invite the bias the product avoids (people are always monochrome, §A).
2. "Maria Santos" → **Maria Gomez**. Breadcrumb "INCIDENT RECOVERY / SYSTEM ALPHA" → Incident
   Recovery / Payment Gateway.
3. "Capability Depth" lists names with no depth → show **shared capabilities as chips** from
   `strengths[]`, or readiness ladders; add per-candidate **evidence confidence** (both MEDIUM
   live) with honest copy: "confidence in demonstrated coverage of this capability" (GAP-04).
4. Add a **gap statement per candidate** from `gaps[]` (descriptive, never evaluative).
5. **Replace "Review Details" with the primary action "Generate transfer plan"** — Review Details
   is a dead end that severs the golden path. Card click can still open evidence.
6. "Not considered" panel: keep, and extend the list with **career goals and performance history**
   alongside workload, on-call/leave, timezone, team priorities, staffing constraints (§11.6 +
   brief C.5). Render the API `disclaimer` string within it.

## Mockup 6 — `MitigationPlan/`

**Screen:** Mitigation plan (golden-path step 6). **Fed by:** `POST /mitigation-plans` →
`POST /mitigation-plans/{id}/approve` (edited tasks ride on the approve request, CI-12).

**Usable as-is:** 2×2 numbered task-card grid; "Approve plan" as the single primary action with
the tagline **"A human approves every plan."** (keep that line); plan header with the person
context.

> **The grid is superseded, 2026-08-29 (DEC-24).** The tasks are an ordered sequence and CI-23
> makes array position load-bearing, but a two-column grid presents them as peers doable in any
> order. The generated content settles it: task 3 requires performing the recovery *unaided*,
> which is only meaningful after the shadowing in task 2, and task 4 folds back "the gaps found
> during the exercise", which is only meaningful after task 3. They now render as a single-column
> `<ol>` with a real step count. The endorsement above was of a static mockup's composition, made
> before anyone reasoned about task dependency.

**Must change:**

1. **The roles are inverted (C.0-class defect):** the mockup reads as though Maria is departing
   and a "Successor" learns from her. **Maria Gomez is the backup being developed; Alex Chen holds
   the knowledge.** Rewrite header ("Develop Maria Gomez as backup for Incident Recovery · mentor:
   Alex Chen") and all four tasks with the real generated ones: review Payment Gateway Incident
   Recovery architecture → shadow **with Alex Chen** → execute in staging → update the runbook.
2. Add the **DRAFT status chip**, the **target readiness (PRACTICED)** labelled as a target, and
   the **capability being addressed** (Incident Recovery) to the header.
3. Task cards gain **task-type labels** (KNOWLEDGE_REVIEW / SHADOWING / PRACTICE / DOCUMENTATION)
   and **acceptance criteria** per task (both in the DTO); linked evidence chips where
   `linked_evidence_ids` is non-empty (task 1 links INC-184 / INC-221).
4. **Make task cards editable before approval** (title, description, criteria) — edits are
   submitted with the approve call (CI-12). After approve, render the post-approval state from
   client state (approved chip, timestamp, approver) — there is no read-back endpoint (GAP-02).
5. **Remove "Est. 2 weeks" and the mode chips** (Self-paced / Synchronous / Supervised /
   Deliverable) — neither is in the DTO; the Phase 3 recommendation is removal, not a contract
   amendment.
6. The content area sits on a black background — off-system; restore light mesh-gradient +
   frosted cards. Drop the top-right notification/avatar chrome (no identity model in MVP).

---

## Cross-cutting corrections (§A restorations, all six mockups)

- **Mesh-gradient background layer** (pale lilac / blush / sky fading to near-white) behind
  everything; never inside content surfaces. Every mockup lost it.
- Frosted near-white cards (~85% white, backdrop blur, 20px radius, hairline border, soft diffuse
  shadow).
- **Status color discipline:** deep rose = CRITICAL_GAP, warm ochre = DEGRADED, muted teal =
  COVERED, dashed grey outline = INSUFFICIENT_EVIDENCE — capabilities and systems only, the only
  saturated colors. Risk-class chips reuse the same restrained family (LOW teal · MODERATE light
  ochre · HIGH deep ochre · CRITICAL rose). **People are always monochrome** (initials avatars,
  grey ladders). Color never carries meaning alone — every status also reads as text.
- Inter everywhere; headings medium weight, tight tracking, dark slate; body 14–15px warm grey;
  **all numerals tabular**; large metrics 40–48px light.
- Never: donuts, gauges, progress rings, sparkline grids, traffic-light dashboards, leaderboards,
  percentage badges beside people, photographs of engineers, commit counts or activity metrics.
- Accessibility floor (skill pass): text contrast ≥ 4.5:1 on the frosted surfaces (the token
  sheet's `#45464d`-on-white passes; verify ochre/rose chip text), visible focus rings, 44px
  interactive targets, `prefers-reduced-motion` respected on graph/overlay transitions, drawer and
  overlay dismissible via Escape with focus return.

## Component inventory (shared, implied by the six screens)

| # | Component | Used by |
|---|---|---|
| 1 | `AppShell` — sidebar nav + mesh-gradient layer + content container | all |
| 2 | `FrostedCard` surface primitive | all |
| 3 | `RiskIndex` (large tabular numeral) + `RiskClassChip` | dashboard, system detail, simulation, why-panel |
| 4 | `ExposurePill` (4 states incl. dashed-outline INSUFFICIENT_EVIDENCE) | dashboard, system detail, simulation, capability detail |
| 5 | `ReadinessLadder` (five-step grey glyph; engineers only) | system detail coverage, evidence drawer, candidates, capability detail |
| 6 | `EngineerBadge` (monochrome initials + name + role) | coverage, candidates, plan, graph drawer |
| 7 | `DriftLabel` (4-value text mapping) | dashboard rows + platform cards |
| 8 | `MetricStrip` (label/value cells, hairline dividers) | system detail, simulation header |
| 9 | `EvidenceCard` (source-type icon, ref, date, role/strength/freshness badges, excerpt, provenance) | evidence drawer, capability detail, candidate detail |
| 10 | `MissingEvidenceNote` / `ConflictingEvidenceSection` | evidence drawer |
| 11 | `WhyPanel` (rules_triggered copy map + index_modifiers arithmetic) | system detail, capability detail |
| 12 | `GraphCanvas` (React Flow: typed node renderers, DEMONSTRATES thickness by readiness, dashed labelled DECLARED_OWNER, focus-dim mode) | system detail, evidence focus view |
| 13 | `ImpactRow` (before→after pills + best-remaining readiness) | simulation |
| 14 | `CandidateCard` (initials, overlap chip, strength/gap lists, confidence, CTA) | candidates |
| 15 | `TaskCard` (editable; type label, criteria list, evidence chips) | mitigation plan |
| 16 | `StatusChip` (DRAFT / APPROVED) + approval banner | plan |
| 17 | `Banner` / `Disclaimer` statics | simulation |
| 18 | `LoadingSkeleton` / `EmptyState` / `ErrorState` (switch on `error.code`) / `InsufficientEvidenceState` (designed) | all |
| 19 | `Breadcrumb`, `SectionHeader` | all |
| 20 | Display-copy maps: rule codes, modifier codes, drift, enums → labels (frontend-owned wording) | why-panel, dashboard, drawers |

## Screens with no mockup (to design in the same language)

1. **Capability detail** (endpoint 5) — engineer-by-engineer readiness for one capability:
   coverage list with ladders, freshness, confidence, `last_demonstrated_at`; exposure + index +
   class header; rules/modifiers link; entry point to the evidence drawer per engineer.
2. **"Why this risk?" panel** — the fired-rules list with frontend copy per code, plus the
   `index_modifiers` arithmetic ("HIGH anchor 70 + 1 sole adequate + 1 best-alternative-assisted
   = 72") — the strongest answer to "the score looks arbitrary".
3. **Loading, empty, and error states** for every screen — skeletons in card shapes; errors
   switch on `error.code` only.
4. **INSUFFICIENT_EVIDENCE as a designed state** — dashed-outline treatment, null index rendered
   as "—", copy: "Not enough evidence for a responsible assessment", never a manufactured value
   (`cap_permission_audit` is the live case).
5. **Post-approval plan state** — approved chip, timestamp, approver, final task list from client
   state (GAP-02).
6. **Challenge assessment drawer** (new since the brief; DEC-10 accepted) — three actions
   (link evidence / manager attestation / correct mapping), no score inputs by design, and the
   before → after recomputation view from the response snapshots (72/HIGH → 15/LOW beat).
7. **Simulations and Plans nav destinations** — the sidebar implies index pages, but no list
   endpoints exist. Recommendation: Simulations opens the sandbox launcher (pick engineer +
   system); Plans shows the current session's plan or an empty state. Decide before Phase 5.

## Design decisions — resolved 2026-08-17 (Person B)

1. **Risk-class chips render as liquid glass with gradient color.** Translucent glassy chips —
   soft gradient fill, backdrop blur, hairline border, subtle inner highlight — consistent with
   the frosted-card system. The gradient hues stay on the semantic scale so color keeps carrying
   meaning: LOW muted-teal gradient · MODERATE light-ochre · HIGH deep-ochre · CRITICAL deep-rose.
   Rose remains reserved for the worst states; people remain monochrome.
2. **Sidebar keeps the four entries, reinterpreted:** Dashboard; Systems anchors the dashboard
   systems list; Simulations opens the sandbox launcher (pick engineer + system); Plans shows the
   current session's plan or a designed empty state.

   > **Superseded 2026-08-27 (DEC-23).** The sidebar now carries three entries — Home, Systems,
   > Plans. A simulation is always run against a system the reader is already looking at, so the
   > Simulations entry offered a second, context-free way to begin one: a dropdown of system names,
   > chosen blind, duplicating the button on the system page. `/simulations` still resolves for
   > anyone holding the link; it is no longer advertised as a place to start.
3. **Engineer rows show name + role** (from graph `metadata.role`), monochrome; team is omitted.
