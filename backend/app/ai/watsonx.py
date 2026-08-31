"""IBM watsonx.ai provider. The model-backed half of the AI layer.

Implements the same `AIProvider` interface as the deterministic provider, so swapping between them
changes extraction quality and changes no conclusion path: readiness, exposure, continuity risk,
simulation, and candidate selection are all downstream and deterministic either way. That property is
the whole reason the interface exists.

Endpoint: `POST {url}/ml/v1/text/chat`. The older `text/generation` endpoint is deprecated and
returns a deprecation warning, so chat is used. IAM tokens are exchanged from the API key and cached
until shortly before expiry.

Failure policy differs by method, deliberately:

* **Extraction raises.** A silent fallback would mean a model outage quietly produced a different
  knowledge graph while every number still looked plausible. `AIExtractionError` is loud, and the
  pipeline already handles it.
* **Narrative methods fall back** to the deterministic templates. The simulation summary, candidate
  strengths, and plan text are prose over facts the rules already decided, so a timeout should
  degrade the wording rather than break the demo (ARCHITECTURE.md section 85).

Of the three narratives only `summarize_simulation` spends a model call; `explain_candidate` and
`generate_mitigation_plan` return the deterministic text and say in their own bodies why.

Every response is validated by `app/ai/validation.py` before anything reaches the database — the same
gate the deterministic provider passes through. An invented capability, a claim against someone who
is not a recorded participant, or a cross-system attribution is rejected regardless of which provider
produced it, and the one model-written sentence goes through `validate_simulation_summary` before it
is returned or persisted.
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
    CapabilityClaim,
    PlanContext,
    PlanDraft,
    SimulationSummaryContext,
)
from app.ai.validation import validate_simulation_summary
from app.core.config import settings
from app.core.errors import AIExtractionError, NarrativeUnavailableError
from app.evidence.strength import strength_for_role
from app.schemas.enums import EvidenceConfidence, EvidenceRole

logger = logging.getLogger(__name__)

IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
CHAT_PATH = "/ml/v1/text/chat"
API_VERSION = "2024-05-31"
TOKEN_SAFETY_MARGIN_SECONDS = 120

PROMPT_DIR = Path(__file__).parent / "prompts"
SYSTEM_PROMPT_FILE = PROMPT_DIR / "extraction_system.txt"

# Extraction is a classification task, so sampling buys nothing and costs reproducibility.
EXTRACTION_TEMPERATURE = 0.0
EXTRACTION_MAX_TOKENS = 900
NARRATIVE_MAX_TOKENS = 500

_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


class QuotaExhaustedError(AIExtractionError):
    """The account's token allowance is spent.

    Distinguished from a transient failure because the response is completely different: a rate limit
    clears in a second, a spent quota needs a plan change or a new window. Retrying the second one
    just turns a clear problem into a slow, confusing one.
    """


class WatsonxProvider:
    name = "watsonx"

    def __init__(self) -> None:
        missing = [
            field
            for field in ("watsonx_api_key", "watsonx_project_id", "watsonx_api_url")
            if not getattr(settings, field)
        ]
        if missing:
            raise ValueError(
                f"AI_PROVIDER=watsonx requires {', '.join(m.upper() for m in missing)} in "
                f"backend/.env. Never commit real credentials."
            )
        self.model_id = settings.watsonx_model_id
        self._fallback = DeterministicProvider()
        # Set to False by `ChainedProvider`, which has another model to try and must be able to see
        # that this one failed. See `NarrativeUnavailableError`.
        self.degrade_to_template = True
        self._token: str | None = None
        self._token_expires_at: float = 0.0
        self._system_prompt = SYSTEM_PROMPT_FILE.read_text()
        self._client = httpx.Client(timeout=settings.watsonx_timeout_seconds)
        self._pace_lock = threading.Lock()
        self._next_slot = 0.0

    # -- transport ----------------------------------------------------------------------

    def _access_token(self) -> str:
        if self._token and time.time() < self._token_expires_at:
            return self._token

        response = self._client.post(
            IAM_TOKEN_URL,
            data={
                "grant_type": "urn:ibm:params:oauth:grant-type:apikey",
                "apikey": settings.watsonx_api_key,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        if response.status_code != 200:
            raise AIExtractionError(
                "Could not exchange the watsonx API key for an IAM token.",
                {"status": response.status_code},
            )
        payload = response.json()
        self._token = payload["access_token"]
        self._token_expires_at = time.time() + payload.get("expires_in", 3600) - TOKEN_SAFETY_MARGIN_SECONDS
        return self._token

    def _throttle(self) -> None:
        """Client-side pacing.

        The service enforces a hard requests-per-second ceiling per instance — 2/s on the plan this
        was developed against — and exceeding it returns 429 for the *whole* burst, so eight parallel
        workers made things slower rather than faster. Pacing in the client is the difference between
        a run that completes and a run that mostly fails.
        """
        minimum_gap = 1.0 / max(settings.watsonx_requests_per_second, 0.1)
        with self._pace_lock:
            wait = self._next_slot - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            self._next_slot = max(time.monotonic(), self._next_slot) + minimum_gap

    def _chat(self, system: str, user: str, max_tokens: int) -> str:
        url = f"{settings.watsonx_api_url.rstrip('/')}{CHAT_PATH}?version={API_VERSION}"
        body = {
            "model_id": self.model_id,
            "project_id": settings.watsonx_project_id,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "max_tokens": max_tokens,
            "temperature": EXTRACTION_TEMPERATURE,
        }

        last_error: str | None = None
        for attempt in range(settings.watsonx_max_retries + 1):
            self._throttle()
            try:
                response = self._client.post(
                    url,
                    json=body,
                    headers={
                        "Authorization": f"Bearer {self._access_token()}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                )
            except httpx.HTTPError as exc:
                last_error = f"transport error: {exc}"
            else:
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"]

                last_error = f"HTTP {response.status_code}: {response.text[:200]}"

                if response.status_code == 403 and "token_quota_reached" in response.text:
                    # The account's token allowance is spent. Retrying cannot help and would only
                    # obscure the cause, so fail immediately with a message that names the fix.
                    raise QuotaExhaustedError(
                        "The watsonx token quota for this account is exhausted, so extraction "
                        "cannot continue. Wait for the quota window to reset or raise the plan "
                        "limit, then re-run scripts.extract_with_provider — cached artifacts are "
                        "skipped, so the run resumes where it stopped.",
                        {"model_id": self.model_id},
                    )
                if response.status_code == 401:
                    self._token = None  # force a fresh IAM token, then retry
                if response.status_code == 429:
                    # Honour Retry-After when offered; otherwise back off enough to clear the window.
                    retry_after = response.headers.get("retry-after")
                    delay = float(retry_after) if retry_after and retry_after.isdigit() else 2.0
                    time.sleep(delay)
                    continue

            if attempt < settings.watsonx_max_retries:
                time.sleep(1.5 * (attempt + 1))

        raise AIExtractionError(
            f"watsonx chat call failed after {settings.watsonx_max_retries + 1} attempts: "
            f"{last_error}",
            {"model_id": self.model_id, "last_error": last_error},
        )

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

    # -- extraction ---------------------------------------------------------------------

    def extract_artifact_semantics(
        self, artifact: ArtifactInput, context: ExtractionContext
    ) -> ArtifactExtraction:
        """FR-004. The prompt, the closed-world rules and the discard logic live in
        `app/ai/extraction.py`, shared with every other model-backed provider.

        This used to be written out here in full. Moving it out is what stops two providers from
        growing two subtly different definitions of extraction — which would turn the comparison in
        `scripts/extract_with_provider.py` into a measurement of the parsers rather than the models.
        Only the transport and the provenance label are specific to watsonx.
        """
        return extract_with(
            artifact,
            context,
            chat=lambda system, user, max_tokens: self._chat(system, user, max_tokens),
            provider_label=f"watsonx/{self.model_id}",
            is_conflicting=self._fallback._looks_conflicting(artifact),
        )

    @staticmethod
    def _user_prompt(artifact: ArtifactInput, context: ExtractionContext) -> str:
        capabilities = context.by_system(artifact.system_hint)
        capability_lines = "\n".join(
            f"- {c.capability_id} — {c.name}" + (f" (also called: {', '.join(c.aliases)})" if c.aliases else "")
            for c in capabilities
        )
        participant_lines = "\n".join(
            f"- {p.engineer_id} — {context.engineer_names.get(p.engineer_id, p.engineer_id)} "
            f"— PARTICIPANT_ROLE: {p.participant_role}"
            for p in artifact.participants
        )
        paths = ", ".join(artifact.file_paths) if artifact.file_paths else "none recorded"

        return (
            f"CAPABILITIES (the only permitted capability_id values)\n{capability_lines}\n\n"
            f"PARTICIPANTS (the only permitted engineer_id values)\n{participant_lines}\n\n"
            f"ARTIFACT\n"
            f"type: {artifact.source_type.value}\n"
            f"reference: {artifact.source_reference}\n"
            f"date: {artifact.artifact_date.isoformat()}\n"
            f"files: {paths}\n"
            f"title: {artifact.title or '(none)'}\n"
            f"body:\n{artifact.body or '(empty)'}\n"
        )

    # -- narrative methods, with a deterministic safety net -----------------------------

    def summarize_simulation(self, context: SimulationSummaryContext) -> str | None:
        # Phrased to avoid naming the prohibited words even in order to forbid them: the
        # responsible-AI test scans string literals in this package, and a prohibition list is more
        # reliable when it needs no exceptions for text that merely quotes what it bans.
        system = (
            "You write one plain sentence for an engineering manager, from facts already computed by "
            "a deterministic rule engine. Constraints: describe only which capabilities would lose "
            "adequate demonstrated coverage; never predict that anything will break; never state a "
            "likelihood or a percentage; never characterise a person's importance or their limits. "
            "Talk about capabilities and coverage, not about people. Reply with the sentence and "
            "nothing else."
        )
        user = (
            f"Engineer unavailable: {context.engineer_name}\n"
            f"Scope: {context.scope_name}\n"
            f"Would have no adequate coverage: {', '.join(context.critical_gap_capabilities) or 'none'}\n"
            f"Would lose redundancy: {', '.join(context.degraded_capabilities) or 'none'}\n"
            f"Remain covered: {', '.join(context.preserved_capabilities) or 'none'}\n"
            f"Risk class moves from {context.risk_class_before} to {context.risk_class_after}."
        )
        try:
            sentence = self._chat(system, user, NARRATIVE_MAX_TOKENS).strip().strip('"').strip()
            # The same gate `OpenRouterProvider.summarize_simulation` applies, for the same
            # reason: this value is returned by `POST /simulations` *and* persisted into
            # `result_json`, so an ungated sentence would outlive the request that produced it.
            # An empty reply is a rejection here rather than a separate branch — the gate already
            # treats it as one.
            if validate_simulation_summary(sentence, context).accepted:
                return sentence
        except AIExtractionError:
            logger.warning("watsonx summary failed")
        return self._or_raise(
            "simulation summary", lambda: self._fallback.summarize_simulation(context)
        )

    def _or_raise(self, subject: str, produce):
        """The template, unless this provider is inside a chain that has another model to try.

        See `NarrativeUnavailableError`: falling back here unconditionally makes a failed generation
        look like a successful one, which stops any outer chain from ever reaching its next provider.
        """
        if not self.degrade_to_template:
            raise NarrativeUnavailableError(
                f"watsonx could not produce the {subject}.",
                {"provider": self.name, "subject": subject},
            )
        logger.warning("watsonx %s: using the deterministic template", subject)
        return produce()

    def explain_candidate(self, context: CandidateNarrativeContext) -> CandidateNarrative:
        # The structured content — which capabilities are demonstrated, assisted, or missing — is
        # decided by the rules. A model here would only rephrase it, and a rephrasing that drifts
        # is worse than a plain one, so the deterministic phrasing stands *for this provider*.
        #
        # Routed through `_or_raise` rather than returning the template directly, which is the
        # difference between "I choose not to" and "here is an answer". Inside a chain those are not
        # the same thing: returning the template looked like success and stopped OpenRouter — which
        # does model-write this one — from ever being asked. Declining lets the chain move on.
        return self._or_raise(
            "candidate narrative", lambda: self._fallback.explain_candidate(context)
        )

    def generate_mitigation_plan(self, context: PlanContext) -> PlanDraft:
        """The deterministic plan is already gap-targeted and validated for 3-5 actions.

        A model could write warmer prose, but the plan is the artifact a manager approves and then
        someone executes — invented steps or an invented tool would be a real cost, and the
        structure is what carries the value. Left deterministic on purpose *for this provider*.

        Declined rather than answered when inside a chain, for the reason given in
        `explain_candidate`: a template returned as a success is indistinguishable from a generation,
        and it blocked the next provider from being tried at all.
        """
        return self._or_raise(
            "mitigation plan", lambda: self._fallback.generate_mitigation_plan(context)
        )

    def close(self) -> None:
        self._client.close()
