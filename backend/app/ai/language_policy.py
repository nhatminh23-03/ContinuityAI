"""What generated prose may say, expressed as checks rather than as prompt wording.

A prompt is a request; this module is the gate. Everything here exists because the same
sentence can be true and still be a liability: "no qualifying independent evidence for Incident
Recovery" and "Maria is unable to recover the system" describe the same evidence and only one of
them is defensible. PRD section 22, DOMAIN_MODEL.md sections 10.2 and 44.

Four rules, each with the failure it prevents:

1. **Prohibited phrases.** The canonical list (see `prohibited_phrases.txt`). Previously it lived
   only in tests/test_responsible_ai.py and was applied only to source-code literals, so nothing
   checked runtime output against it. Same list, now enforceable at runtime.
2. **Probability language.** A simulation identifies which capabilities lose adequate demonstrated
   coverage. It is not an outage forecast, and a percentage or a "will fail" turns a coverage
   statement into a prediction nobody can stand behind.
3. **Inability language.** PRD section 22.3: a gap is *absence of evidence*, never inability.
   Evidence not found is a statement about the record; "cannot" is a statement about the person.
4. **Unattested names.** A capability or a person that was not among the facts handed to the
   generator is an invention, and inventing a name attached to a person is the most damaging
   failure this product could have.

The name check is a heuristic and is deliberately biased. It reads multi-word capitalised runs as
proper names and requires every word of such a run to come from the given facts or to be an
ordinary function word. It therefore over-reports rather than under-reports: a false positive
costs the model-written sentence and falls back to the deterministic template, while a false
negative puts an invented claim in front of a manager.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from pathlib import Path

PHRASE_FILE = Path(__file__).parent / "prohibited_phrases.txt"


def _load_phrases(path: Path) -> tuple[str, ...]:
    lines = (line.strip() for line in path.read_text().splitlines())
    return tuple(line.lower() for line in lines if line and not line.startswith("#"))


FORBIDDEN_PHRASES: tuple[str, ...] = _load_phrases(PHRASE_FILE)

# docs/ARCHITECTURE.md section 30 and contract decision CI-32: the simulation reports coverage
# loss, and the "this is not an outage prediction" disclaimer is frontend copy. Output that
# quantifies a likelihood contradicts both.
PROBABILITY_MARKERS: tuple[str, ...] = ("%", "probability", "chance of", "will fail")

# PRD section 22.3. Kept separate from the phrase list because it applies only where a gap is
# described: a strength may legitimately say what was not observed, a gap may not say what a
# person is incapable of.
INABILITY_MARKERS: tuple[str, ...] = (
    "cannot",
    "can not",
    "can't",
    "unable to",
    "incapable of",
    "not capable of",
)

# Two or more adjacent capitalised words. Each word must start upper case and continue lower
# case, so screaming-case contract values (HIGH, CRITICAL_GAP, INC-2481) are not proper names.
# The separator is spaces only: a run must not reach across a line break, or the last word of one
# field and the first word of the next would read as a single name.
_PROPER_NAME = re.compile(r"[A-Z][a-z][\w'’-]*(?:[ \t]+[A-Z][a-z][\w'’-]*)+")
_WORD = re.compile(r"[\w'’-]+")

# Closed-class English words. A capitalised run can start with one of these purely because it
# starts a sentence ("Without Alex Chen, ..."), and no proper name is made of them.
_FUNCTION_WORDS = frozenset(
    {
        "a", "after", "all", "also", "an", "and", "another", "any", "as", "at", "because",
        "before", "both", "but", "by", "each", "either", "every", "for", "from", "her", "his",
        "however", "if", "in", "into", "its", "neither", "no", "none", "nor", "not", "of", "on",
        "once", "one", "only", "or", "our", "out", "over", "per", "since", "so", "some", "still",
        "than", "that", "the", "their", "them", "then", "there", "these", "they", "this", "those",
        "to", "two", "under", "until", "up", "when", "where", "which", "while", "who", "will",
        "with", "within", "without", "yet",
    }
)


def _normalise(word: str) -> str:
    token = word.strip("'’\"-.,;:!?()").lower()
    if token.endswith("'s") or token.endswith("’s"):
        token = token[:-2]
    return token


def _found(text: str, markers: Iterable[str]) -> list[str]:
    lowered = text.lower()
    return [marker for marker in markers if marker in lowered]


def find_forbidden_phrases(text: str) -> list[str]:
    """Prohibited wording present in `text`, in list order. Empty means clean."""
    return _found(text, FORBIDDEN_PHRASES)


def find_probability_language(text: str) -> list[str]:
    return _found(text, PROBABILITY_MARKERS)


def find_inability_language(text: str) -> list[str]:
    """Wording that describes a person's limits instead of the state of the evidence."""
    return _found(text, INABILITY_MARKERS)


def find_unattested_names(text: str, attested: Iterable[str]) -> list[str]:
    """Proper names in `text` that were not among the facts the generator was given.

    `attested` is every name the caller supplied to the generator — capabilities, systems,
    components, evidence references, and the people the context actually names. A run is accepted
    when every one of its words appears in one of those names, which tolerates rephrasing
    ("the Payment Gateway recovery path") while still catching a name that arrived from nowhere.

    The first word of a run that opens a sentence or a line is skipped: it may be capitalised by
    position rather than because it is part of a name, which is the difference between "Shadow
    Incident Recovery" as a task title and "Sarah Kim" as an invented colleague. Callers that
    assemble several fields into one string should join them with newlines so each field keeps
    its own opening position.
    """
    vocabulary = {
        _normalise(word)
        for name in attested
        if name
        for word in _WORD.findall(str(name))
    }
    vocabulary.discard("")
    unattested: list[str] = []
    for match in _PROPER_NAME.finditer(text):
        run = match.group(0)
        words = run.split()
        if _opens_a_sentence(text, match.start()):
            words = words[1:]
        tokens = [_normalise(word) for word in words]
        unknown = [
            token
            for token in tokens
            if token and token not in vocabulary and token not in _FUNCTION_WORDS
        ]
        if unknown and run not in unattested:
            unattested.append(run)
    return unattested


def _opens_a_sentence(text: str, position: int) -> bool:
    head = text[:position].rstrip(" \t")
    return not head or head[-1] in ".:;!?\n"
