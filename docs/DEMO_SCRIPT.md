# Demo video — script and recording plan

Three minutes maximum, landscape 16:9, three required parts: hook and problem, live demo, impact.
Target runtime **2:45**, which leaves fifteen seconds of headroom.

Every figure quoted here was verified against the running application on 2026-08-31. Do not change
a number in this script without re-checking it — the list to check against is at the bottom.

---

## Before recording

1. **Reset the data.** From `backend/`:
   `AI_PROVIDER=deterministic PYTHONPATH=. .venv/bin/python -m scripts.seed_demo`
   Then confirm Payment Gateway reads **74 / HIGH** and Incident Recovery **72 / no resilient backup**.
2. **Record on `AI_PROVIDER=deterministic`.** Every interaction answers in under a second. Under
   `hybrid` the candidate and plan steps wait up to eight seconds each, which is a quarter of the
   demo spent on a loading state.
3. **Start the backend from inside `backend/`.** Started from the repository root the `.env` file is
   not read and the provider silently reverts.
4. **Show the introduction strip.** In the browser console:
   `localStorage.removeItem('cai-intro-dismissed')`, then reload. It states what the product does in
   three steps and is worth its two seconds.
5. **Browser:** 1600×900 or 1920×1080, zoom at 100%, bookmarks bar hidden, no extensions in frame,
   one tab. The frontend runs on **port 3001**.
6. **Rehearse once end to end**, including approval.

---

## Part 1 — Hook and problem · 0:00 to 0:30

> **[0:00 — black card, text only]**
> Your servers have backups. Your knowledge does not.
>
> **[0:05 — cut to the dashboard]**
> Every engineering team has a service that only one person can actually fix. Not the person listed
> as the owner. The person who has actually done it.
>
> **[0:13]**
> Your tools cannot tell you who that is. Code ownership files record who was assigned. Contribution
> graphs count commits. Neither one knows who recovered production at three in the morning.
>
> **[0:22]**
> So the gap stays invisible. Until somebody resigns, or goes on leave during the incident that
> needed them.
>
> **[0:28]**
> ContinuityAI finds that person before you lose them.

## Part 2 — Demo · 0:30 to 2:05

> **[0:30 — dashboard, the Start here card in frame]**
> It reads the engineering record you already have. Incidents, pull requests, code reviews, tickets,
> runbooks.
>
> **[0:36]**
> Six hundred and forty artifacts become a map of who has demonstrably done what. And it opens on the
> one thing worth looking at first.
>
> **[0:44 — the Start here card]**
> Incident Recovery, on Payment Gateway. One engineer has repeatedly demonstrated it. No second
> engineer has demonstrated it at all.
>
> **[0:52 — evidence drawer open on Alex Chen]**
> Every claim opens. This is not an opinion about Alex. It is two production incidents where Alex
> carried out the recovery, with the record attached.
>
> **[1:02 — close the drawer, click the what-if button]**
> So ask the question that matters. What if Alex is unavailable?
>
> **[1:08 — simulation panel]**
> Seventy four to ninety three. High to critical. And it says exactly what breaks. Incident Recovery
> and Certificate Management lose coverage. Retry Logic and Monitoring stay fine.
>
> **[1:20]**
> That last part is the point. This is analysis, not alarm.
>
> **[1:25 — click Find backup candidates]**
> Then it answers the next question. Who could cover this?
>
> **[1:31 — candidates screen]**
> Maria Gomez. Ranked on demonstrated capability overlap, and nothing else. Not workload. Not
> performance. No score of any kind.
>
> **[1:40 — the gaps panel]**
> It also says what she has not done. A gap here means the evidence is missing. Never that the person
> is lacking.
>
> **[1:48 — click Generate transfer plan]**
> And it turns that into work. Four tasks, in order, each with acceptance criteria, the first one
> citing the incidents that justify it.
>
> **[1:58 — click Approve plan]**
> A human approves. Nothing is assigned, nothing is scheduled, nothing happens to anybody
> automatically.

## Part 3 — Impact and evidence · 2:05 to 2:45

> **[2:05 — the two summary sentences side by side]**
> The rules decide every number you just saw. A model writes the sentences that explain them, and a
> validator checks each one against the record before it can reach the screen.
>
> **[2:14]**
> We know where that line belongs because we measured it. We ran the whole corpus through a model and
> through the rules, and scored both against a hidden answer key.
>
> **[2:23 — the comparison table]**
> The rules won. Fifty six out of fifty six on readiness, against fifty four. Twenty five out of
> twenty five on simulation, against fifteen. And both model errors were too generous, on the one
> capability the demo depends on.
>
> **[2:33]**
> So we shipped the rules where they win, and the model where it wins. Eight checks against the
> answer key, all at a hundred percent, including seven adversarial artifacts the system is required
> to refuse.
>
> **[2:41]**
> We have not put this in front of users yet. That is next. What we have done is prove it against an
> answer key it could not see.

**Closing card:** product name, repository URL, "Wildcard Challenge — Build Intelligent Systems for
the Future of Work".

---

## Capture list

Record each as its own step.

| # | Screen | Action | Hold |
|---|---|---|---|
| 1 | Dashboard | Land on it; strip and Start here card in frame | 3s |
| 2 | Dashboard | Cursor over "Alex Chen" on the Start here card | 2s |
| 3 | System detail | Click through; let the coverage card settle | 3s |
| 4 | Evidence drawer | Open it on Alex Chen's row; scroll to INC-184 | 5s |
| 5 | Evidence drawer | Close | 1s |
| 6 | Simulation | Click "What if someone's unavailable?" | 4s |
| 7 | Simulation | Rest on 74 → 93, then on the impact rows | 6s |
| 8 | Candidates | Click "Find backup candidates" | 4s |
| 9 | Candidates | Rest on Maria Gomez, then on the gaps panel | 5s |
| 10 | Plan | Click "Generate transfer plan" | 4s |
| 11 | Plan | Scroll the tasks slowly; the INC-184 citation is visible on task one | 5s |
| 12 | Plan | Click "Approve plan"; rest on the confirmation | 4s |

### The one model insert

The main flow is recorded on `deterministic`, so the sentences on screen are templates. **Do not
claim on camera that a model wrote them.** To show the model path honestly, capture one extra clip:
set `AI_PROVIDER=hybrid`, restart the backend from `backend/`, run one simulation, and capture the
summary paragraph. One wait of under three seconds. Revert to `deterministic` afterwards.

Cut the two sentences side by side at 2:05:

- **Template:** "Without Alex Chen, Payment Gateway moves from HIGH to CRITICAL: 2 capability gaps
  (Incident Recovery and Certificate Management) would have no adequate demonstrated coverage;
  Provider Failover would lose redundancy. Retry Logic and Monitoring remain covered."
- **Model:** "If Alex Chen were unavailable for Payment Gateway, Incident Recovery and Certificate
  Management would have no adequate demonstrated coverage, Provider Failover would lose redundancy,
  Retry Logic and Monitoring would remain covered, and the risk class moves from HIGH to CRITICAL."

### Do not film

- The `/simulations` page. It is unlisted and duplicates the flow.
- The knowledge graph as a hero shot. It is supporting texture; a static graph reads badly on camera.
  Two seconds behind narration at most.

---

## Production notes

- Aspect ratio 16:9.
- Keep spoken lines under twelve words. Text-to-speech handles short clauses well.
- Numbers are spelled out above because they are read aloud. Leave on-screen text as digits.
- Worth overlaying: the hook at 0:00, "74 → 93" at 1:08, "56/56 vs 54/56" at 2:23.
- If the read-through runs past 2:50, cut the 1:20 line first, then the 1:40 line.

## Figures to check the final cut against

640 artifacts · 133 evidence records · 56 coverage relationships · 74 → 93 · HIGH → CRITICAL ·
readiness 56/56 against 54/56 · simulation 25/25 against 15/25 · 8 evaluation checks at 100% ·
7 adversarial artifacts declined · 347 tests passing.
