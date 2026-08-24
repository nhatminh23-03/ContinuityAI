"""OpenRouter provider. The mirror image of the watsonx one.

`WatsonxProvider` lets a model do extraction and keeps the narratives deterministic. This one does
the opposite: extraction stays rule-based, and a model writes only the three manager-facing
narratives — the simulation sentence, a candidate's strengths and gaps, and the mitigation plan.

That split follows from where the damage is. Every risk number in the product is computed from the
extracted graph, so a model that quietly reads an artifact differently changes readiness, exposure
and continuity risk while every number still looks plausible. The narratives sit at the other end:
they are prose over facts the rules already decided, they change no conclusion, and they are the
part a manager actually reads out in a room. So this provider spends model calls where a bad answer
costs a wording and none where a bad answer would cost the graph.

What makes that defensible is not the prompt alone. Every generation passes `app/ai/validation.py`
before it is returned, the same gate the deterministic provider's output would pass, and anything
rejected — an invented capability, a colleague who does not exist, a likelihood, a plan with the
wrong number of actions — falls back to the deterministic template. A narrative failure of any kind,
transport, timeout, parse or validation, degrades the wording and never reaches the caller
unvalidated.

The prompts still carry real weight, and it is worth being precise about why. The gate's
`find_unattested_names` is a documented heuristic (see the docstring of `app/ai/language_policy.py`
and `test_known_blind_spots_of_the_name_check`): a single-word invention and a lower-case invented
capability both pass it. The prompt files under `prompts/` are therefore the primary defence for
grounding and the gate is the net under them, not the other way round.

Transport: OpenAI-compatible. `POST {base_url}/chat/completions`, `Authorization: Bearer <key>`,
reply at `choices[0].message.content`. The API key is used directly, so there is no token exchange
layer of the kind watsonx needs.
"""

from __future__ import annotations

import json
import logging
import re
import threading
import time
from pathlib import Path

import httpx

from app.ai.deterministic import DeterministicProvider
from app.ai.extraction import extract_with
from app.ai.provider import ExtractionContext
from app.ai.schemas import (
    ArtifactExtraction,
    ArtifactInput,
    CandidateNarrative,
    CandidateNarrativeContext,
    PlanContext,
    PlanDraft,
    PlanTaskDraft,
    SimulationSummaryContext,
)
from app.ai.validation import (
    _task_count_band,
    requires_recovery_drill,
    validate_candidate_narrative,
    validate_plan_draft,
    validate_simulation_summary,
)
from app.core.config import settings
from app.core.errors import AIExtractionError

logger = logging.getLogger(__name__)

CHAT_PATH = "/chat/completions"

PROMPT_DIR = Path(__file__).parent / "prompts"
SIMULATION_PROMPT_FILE = PROMPT_DIR / "simulation_summary_system.txt"
CANDIDATE_PROMPT_FILE = PROMPT_DIR / "candidate_narrative_system.txt"
PLAN_PROMPT_FILE = PROMPT_DIR / "mitigation_plan_system.txt"

# Restating computed facts is closer to classification than to writing: sampling buys nothing here
# and costs reproducibility, which the evaluation in app/evaluation/ depends on.
NARRATIVE_TEMPERATURE = 0.0
SUMMARY_MAX_TOKENS = 300
CANDIDATE_MAX_TOKENS = 700
PLAN_MAX_TOKENS = 1600

# A plan is one call per request; a candidate explanation is one of up to three in a row. The plan
# can therefore spend more of AC-14's 12-second budget without putting it at risk.
PLAN_TIMEOUT_MULTIPLIER = 2.0

# How one per-call budget is divided across httpx's four timeout phases. They must sum to 1.
#
# `httpx.Client(timeout=3.5)` does not mean "this call takes at most 3.5 seconds": it gives
# connect, write, read and pool 3.5 seconds *each*, so a call that spends 3.4 connecting and 3.4
# reading is inside every configured limit and outside the arithmetic AC-14 is sized against
# (3 x 3.5 = 10.5 inside 12). httpx has no total-request setting, so the total is built by
# splitting one budget across the phases that run in sequence.
#
# Connect carries the second-largest share because it is a real fixed cost here rather than a
# formality: a provider is constructed per request, so each request opens a fresh connection and
# pays a TLS handshake inside its own budget. Read carries the largest because that is where the
# model actually generates.
TIMEOUT_PHASE_SHARES = {"pool": 0.05, "connect": 0.25, "write": 0.05, "read": 0.65}

# Retry-After is honoured but bounded. A narrative call sits inside a request budget with a
# deterministic template behind it, so a gateway asking for a minute is asking for longer than the
# wording is worth.
MAX_RETRY_AFTER_SECONDS = 2.0
BACKOFF_BASE_SECONDS = 1.0

_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def _call_budget(total_seconds: float) -> httpx.Timeout:
    """Per-phase timeouts derived from one number.

    See `TIMEOUT_PHASE_SHARES` for why this is not simply `httpx.Timeout(total_seconds)`.

    **`total_seconds` is not a wall-clock ceiling, and measurement showed it is not even close to
    one.** httpx's `read` timeout bounds the gap *between* socket reads rather than the whole
    response, so anything that keeps the socket warm keeps resetting the clock. That was written
    here as a hypothetical "pathological slow trickle"; it is in fact the normal behaviour of the
    gateway, which sends padding while the model generates. Measured on 2026-08-21, calls nominally
    budgeted at 3.5s took about 6s, and the candidates endpoint reached 16.91s against AC-14's 12
    (OPEN-11).

    The fix is not a different number here. A total has to be enforced by something that can stop
    waiting, which is why `narrate_in_parallel` in `app/ai/budget.py` applies a real deadline and
    the callers use that. These phase timeouts remain useful for what they can bound — a dead host,
    a hung connect, a stalled socket — and that is all they are now relied on for.
    """
    return httpx.Timeout(
        connect=total_seconds * TIMEOUT_PHASE_SHARES["connect"],
        write=total_seconds * TIMEOUT_PHASE_SHARES["write"],
        read=total_seconds * TIMEOUT_PHASE_SHARES["read"],
        pool=total_seconds * TIMEOUT_PHASE_SHARES["pool"],
    )


# One connection pool for the process, not one per provider instance.
#
# A provider is constructed per request, so a per-instance client meant every request paid a fresh
# TCP connect and TLS handshake *inside* its own latency budget — which is why `connect` was given
# a quarter of it. Sharing the pool lets a warm connection be reused, so that quarter goes back to
# generation. `httpx.Client` is documented as thread-safe, and every call passes its own `timeout`,
# so nothing here depends on the client's construction-time timeout.
#
# Deliberately not closed per request. Closing it is what would defeat the purpose; the pool lives
# for the life of the process and is released when it exits.
_SHARED_CLIENT: httpx.Client | None = None
_SHARED_CLIENT_LOCK = threading.Lock()


def _shared_client() -> httpx.Client:
    global _SHARED_CLIENT
    if _SHARED_CLIENT is None:
        with _SHARED_CLIENT_LOCK:
            if _SHARED_CLIENT is None:
                _SHARED_CLIENT = httpx.Client(
                    timeout=_call_budget(settings.openrouter_timeout_seconds),
                    # Room for the parallel candidate narration, which issues up to `limit` calls
                    # at once.
                    limits=httpx.Limits(max_connections=8, max_keepalive_connections=4),
                )
    return _SHARED_CLIENT


def reset_shared_client() -> None:
    """Drop the pooled client. For tests that swap transports or settings between cases."""
    global _SHARED_CLIENT
    with _SHARED_CLIENT_LOCK:
        if _SHARED_CLIENT is not None:
            _SHARED_CLIENT.close()
        _SHARED_CLIENT = None


class CacheBuildRefusedError(AIExtractionError):
    """Retained for the error type; no longer raised by this provider.

    It existed because extraction here delegated to string matching, so a cache named
    `openrouter_cache.json` would have held rule-based output and a later reader comparing providers
    would have compared the deterministic provider against itself without knowing it. Extraction
    provenance is the one thing in this repository that must not be quietly wrong.

    That reason is now gone: this provider extracts with the model, so a cache built under it
    contains what its name says. Building one is not only permitted, it is the point.
    """


class OpenRouterProvider:
    name = "openrouter"

    # This provider now extracts with the model, so the honest answer is its own name. It used to
    # report `deterministic` here, because extraction delegated to string matching and anything
    # reporting provenance had to say so. That is no longer true, and reporting the old value would
    # now understate what built the graph rather than overstate it.
    extraction_provider_name = name

    def __init__(self) -> None:
        # All three, not only the key. `openrouter_base_url` and `openrouter_model` have defaults,
        # but an empty override in .env silently beats the default, and the symptom would be every
        # narrative degrading to the template forever behind a single WARN line — the exact silent
        # failure this provider is built to avoid. Missing configuration fails at construction.
        missing = [
            field
            for field in ("openrouter_api_key", "openrouter_base_url", "openrouter_model")
            if not getattr(settings, field)
        ]
        if missing:
            raise ValueError(
                f"AI_PROVIDER=openrouter requires {', '.join(m.upper() for m in missing)} in "
                f"backend/.env. Never commit real credentials."
            )
        self.model_id = settings.openrouter_model
        self._fallback = DeterministicProvider()
        self._simulation_prompt = SIMULATION_PROMPT_FILE.read_text()
        self._candidate_prompt = CANDIDATE_PROMPT_FILE.read_text()
        self._plan_prompt = PLAN_PROMPT_FILE.read_text()
        # The process-wide pool, not a new client. Kept as an instance attribute so a test can
        # install its own transport without touching the pool.
        self._client = _shared_client()

    # -- transport ----------------------------------------------------------------------

    def _chat(self, system: str, user: str, max_tokens: int, timeout: float | None = None) -> str:
        """One OpenAI-compatible chat call, with a bounded number of attempts.

        `timeout` overrides the configured per-call ceiling for the one narrative that can afford
        more of the budget; everything else takes the default. Either way the number is a total
        for the call, not a limit per connection phase — see `TIMEOUT_PHASE_SHARES`.
        """
        per_call = _call_budget(timeout or settings.openrouter_timeout_seconds)
        url = f"{settings.openrouter_base_url.rstrip('/')}{CHAT_PATH}"
        body = {
            "model": settings.openrouter_model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_tokens,
            "temperature": NARRATIVE_TEMPERATURE,
        }
        headers = {
            "Authorization": f"Bearer {settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        retries = max(settings.openrouter_max_retries, 0)
        last_error: str | None = None
        for attempt in range(retries + 1):
            attempts_left = attempt < retries
            try:
                response = self._client.post(
                    url,
                    json=body,
                    headers=headers,
                    timeout=per_call,
                )
            except httpx.HTTPError as exc:
                last_error = f"transport error: {exc}"
            else:
                if response.status_code == 200:
                    return self._reply_text(response)

                last_error = f"HTTP {response.status_code}: {response.text[:200]}"

                if response.status_code == 429 and attempts_left:
                    retry_after = response.headers.get("retry-after")
                    delay = (
                        float(retry_after)
                        if retry_after and retry_after.isdigit()
                        else BACKOFF_BASE_SECONDS
                    )
                    time.sleep(min(delay, MAX_RETRY_AFTER_SECONDS))
                    continue

            # Only when another attempt is actually coming. Sleeping before giving up would spend
            # the caller's budget on nothing.
            if attempts_left:
                time.sleep(BACKOFF_BASE_SECONDS * (attempt + 1))

        raise AIExtractionError(
            f"openrouter chat call failed after {retries + 1} attempt(s): {last_error}",
            {"model_id": self.model_id, "last_error": last_error},
        )

    @staticmethod
    def _reply_text(response: httpx.Response) -> str:
        """The reply, or a failure. A 200 with an unexpected shape is not a usable answer."""
        try:
            return response.json()["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise AIExtractionError(
                "openrouter returned a 200 that carries no message content.",
                {"model_id": settings.openrouter_model},
            ) from exc

    @staticmethod
    def _parse_json(raw: str) -> dict:
        """Models wrap JSON in prose or fences often enough that this must be tolerant."""
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            text = text[text.find("\n") + 1 :] if "\n" in text else text
            text = text.replace("json\n", "", 1)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = _JSON_BLOCK.search(text)
            if not match:
                raise
            return json.loads(match.group(0))

    # -- extraction: model-written, closed-world, gated ----------------------------------

    def extract_artifact_semantics(
        self, artifact: ArtifactInput, context: ExtractionContext
    ) -> ArtifactExtraction:
        """FR-004, for real: the model reads the artifact and returns structured claims.

        This used to delegate to the deterministic provider, which made `openrouter` a
        narratives-only provider. It is now the extraction path as well, running the same prompt and
        the same rules as `watsonx` through `app/ai/extraction.py` — so the two are comparable, and
        so there is exactly one definition of what extraction means.

        **Raises rather than falling back.** The narratives in this file degrade to a template on
        failure because a lost sentence costs wording. Extraction decides the graph every risk number
        is computed from, so a silent fallback here would mean an outage quietly produced a different
        knowledge graph while every number still looked plausible. The caller in
        `app/ingestion/pipeline.py` stops the run instead.
        """
        return extract_with(
            artifact,
            context,
            # The batch budget, not the narrative one. Extraction runs at seed time, outside any API
            # request, so AC-14's 12 seconds does not apply and the narrative timeout is far too tight
            # for a cold connection — see `openrouter_batch_timeout_seconds`.
            chat=lambda system, user, max_tokens: self._chat(
                system, user, max_tokens, timeout=settings.openrouter_batch_timeout_seconds
            ),
            provider_label=f"openrouter/{self.model_id}",
            is_conflicting=self._fallback._looks_conflicting(artifact),
        )

    # -- narratives: model -> gate -> template on any failure ----------------------------

    def summarize_simulation(self, context: SimulationSummaryContext) -> str | None:
        user = (
            f"ENGINEER UNAVAILABLE\n{context.engineer_name}\n\n"
            f"SCOPE\n{context.scope_name}\n\n"
            f"WOULD HAVE NO ADEQUATE COVERAGE\n{self._lines(context.critical_gap_capabilities)}\n\n"
            f"WOULD LOSE REDUNDANCY\n{self._lines(context.degraded_capabilities)}\n\n"
            f"REMAIN COVERED\n{self._lines(context.preserved_capabilities)}\n\n"
            f"RISK CLASS\nmoves from {context.risk_class_before} to {context.risk_class_after}"
        )
        try:
            sentence = self._chat(self._simulation_prompt, user, SUMMARY_MAX_TOKENS)
            sentence = sentence.strip().strip('"').strip()
            if validate_simulation_summary(sentence, context).accepted:
                return sentence
        except Exception as exc:  # noqa: BLE001 — see _degrade
            self._degrade("simulation summary", exc)
        return self._fallback.summarize_simulation(context)

    def explain_candidate(self, context: CandidateNarrativeContext) -> CandidateNarrative:
        user = (
            f"CANDIDATE (the only person who may be named)\n{context.candidate_name}\n\n"
            f"CAPABILITY UNDER REVIEW\n{context.capability_name}\n\n"
            f"DEMONSTRATED (independent evidence exists)\n"
            f"{self._lines(context.demonstrated_capabilities)}\n\n"
            f"ASSISTED (participated with support)\n"
            f"{self._lines(context.assisted_capabilities)}\n\n"
            f"MISSING (no qualifying evidence in the record)\n"
            f"{self._lines(context.missing_capabilities)}"
        )
        try:
            payload = self._parse_json(self._chat(self._candidate_prompt, user, CANDIDATE_MAX_TOKENS))
            narrative = CandidateNarrative(
                strengths=self._clean(payload.get("strengths")),
                gaps=self._clean(payload.get("gaps")),
            )
            if validate_candidate_narrative(narrative, context).accepted:
                return narrative
        except Exception as exc:  # noqa: BLE001 — see _degrade
            self._degrade("candidate narrative", exc)
        return self._fallback.explain_candidate(context)

    def generate_mitigation_plan(self, context: PlanContext) -> PlanDraft:
        known_evidence_ids = {
            str(e["evidence_id"]) for e in context.reference_evidence if e.get("evidence_id")
        }
        try:
            raw = self._chat(
                self._plan_prompt,
                self._plan_user_prompt(context),
                PLAN_MAX_TOKENS,
                timeout=settings.openrouter_timeout_seconds * PLAN_TIMEOUT_MULTIPLIER,
            )
            payload = self._parse_json(raw)
            draft = PlanDraft(
                # Never taken from the model: the target is decided upstream from the candidate's
                # readiness and the capability's criticality.
                target_readiness=context.target_readiness,
                tasks=[self._plan_task(entry) for entry in payload.get("tasks") or []],
            )
            outcome = validate_plan_draft(draft, context, known_evidence_ids)
            if outcome.accepted and outcome.draft is not None:
                # The gate's draft, not the one passed in: citations that do not resolve have been
                # filtered out of it.
                return outcome.draft
        except Exception as exc:  # noqa: BLE001 — see _degrade
            self._degrade("mitigation plan", exc)
        return self._fallback.generate_mitigation_plan(context)

    def _plan_user_prompt(self, context: PlanContext) -> str:
        drill_required = requires_recovery_drill(context.candidate_readiness)
        # The band the gate will apply, taken from the gate rather than restated here. A prompt
        # that asked for a count the validator rejects would fall back on every single call, and
        # the fallback is silent by construction.
        minimum, maximum = _task_count_band(context.candidate_readiness)
        count = (
            f"exactly {minimum}" if minimum == maximum else f"between {minimum} and {maximum}"
        )
        drill_line = (
            "This candidate has no hands-on evidence, so exactly one action must be a "
            "RECOVERY_DRILL."
            if drill_required
            else "This candidate has already participated with support, so do not include a "
            "RECOVERY_DRILL."
        )
        evidence_lines = (
            "\n".join(
                f"- {e.get('evidence_id')} — {e.get('source_reference', 'no reference recorded')}"
                for e in context.reference_evidence
            )
            or "- none recorded"
        )
        return (
            f"CAPABILITY TO TRANSFER\n{context.capability_name}\n\n"
            f"WHERE IT LIVES\nsystem: {context.system_name}\ncomponent: {context.component_name}\n\n"
            f"PEOPLE (the only two who may be named)\n"
            f"- source engineer: {context.source_engineer_name}\n"
            f"- candidate: {context.candidate_name}\n\n"
            f"OTHER CAPABILITIES THE CANDIDATE HAS NO QUALIFYING EVIDENCE FOR\n"
            f"{self._lines(context.missing_capabilities)}\n\n"
            f"REFERENCE EVIDENCE (the only permitted linked_evidence_ids)\n{evidence_lines}\n\n"
            f"WRITE {count} actions. {drill_line}"
        )

    @staticmethod
    def _plan_task(entry: dict) -> PlanTaskDraft:
        """Field by field, so a missing one is a failure here rather than a surprise downstream.

        Deliberately no `str()` coercion: a model that returns an object where a title was asked
        for has not answered the question, and coercing it would print a Python repr into a plan a
        manager approves. Letting the attribute error escape routes it to the template instead.
        """
        return PlanTaskDraft(
            title=entry["title"].strip(),
            description=entry["description"].strip(),
            task_type=entry["task_type"].strip().upper(),
            acceptance_criteria=OpenRouterProvider._clean(entry.get("acceptance_criteria")),
            linked_evidence_ids=OpenRouterProvider._clean(entry.get("linked_evidence_ids")),
        )

    @staticmethod
    def _clean(values: object) -> list[str]:
        """Text entries only.

        Same reason as above: `str()` on a dict the model invented — `{"capability": "...",
        "note": "..."}` where a line of prose was asked for — yields a repr that reads as garbage
        to a manager and passes the gate as one long unremarkable string. Dropping non-text
        entries empties the list, the gate rejects it for being empty, and the template is used.
        """
        if not isinstance(values, list):
            return []
        return [value.strip() for value in values if isinstance(value, str) and value.strip()]

    @staticmethod
    def _lines(names: list[str]) -> str:
        return "\n".join(f"- {name}" for name in names) or "- none"

    @staticmethod
    def _degrade(subject: str, exc: Exception) -> None:
        """Log a failed generation at WARN and let the caller use the template.

        The `except Exception` this serves is deliberate rather than lazy. Everything that can go
        wrong here — a timeout, a gateway error, output that is not JSON, a field the model left
        out, a pydantic complaint about a field it invented — has the same correct response, and
        the response is already sitting in the deterministic provider. What must never happen is a
        narrative failing into a 500: the numbers the manager is looking at were computed by rules
        and are unaffected by whether the sentence under them was written by a model.

        Rejections by the gate itself are logged by `app/ai/validation.py`, so they are visible
        without being logged twice here.
        """
        logger.warning("openrouter %s failed (%s); using the deterministic template", subject, exc)

    def close(self) -> None:
        """Deliberately does not close the connection pool.

        A provider is constructed per request but the pool is shared across the process, so closing
        it here would discard the warm connection the next request needs — and could close it under
        a request still using it. That per-request handshake is what OPEN-11 was partly paying for.
        The pool is released when the process exits; `reset_shared_client` exists for tests.
        """
