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

`find_unattested_names` is the only rule here that is a heuristic rather than a lookup, so be
precise about what it does and does not do. It removes every attested name from the line, then
looks at what capitalised multi-word runs survive, and applies two rules:

* **Recombination** — a surviving fragment of an attested *person's* name sitting next to another
  capitalised word. "Sarah Chen" where the record holds "Alex Chen" is an invented colleague
  wearing a real surname, and it is caught whatever the capitalisation style.
* **Unattested run** — a capitalised run containing a word from nowhere in the given facts, and
  only on a line that is otherwise sentence-cased.

The sentence-case condition is the load-bearing one and it is a real limitation, not a hedge. In
"Update The Payment Gateway Runbook" every word is capitalised, so capitalisation says nothing
about which words are names: "Runbook" and "The" look exactly like "Priya" would. Applying the
rule there rejects almost every well-formed title, and a gate that rejects everything is
indistinguishable from a gate that works, because both produce the deterministic template. So on
a fully capitalised line only the recombination rule runs.

What this check therefore **cannot** catch, stated plainly so that no caller assumes closed-world
grounding it does not have:

* a single-word invention — "ask Priya to confirm", "coordinate with Stripe". One capitalised word
  is structurally identical to any capitalised ordinary noun, and separating them needs a lexicon
  this module does not have;
* an invented capability written in lower case — "the settlement batching path";
* an invented capability on a fully capitalised line — "Review The Settlement Batching Runbook",
  and likewise inside a run that capitalises a function word mid-sentence, which is title casing
  quoted into prose and is exempt for the same reason.

Closing the second and third properly needs the capability taxonomy passed in, the way
`validate_extraction` receives it, rather than a better guess about capitalisation. Until then the
prompt, not this module, is what keeps invented capabilities out; this is a net under the prompt
and not a substitute for it.

Where the check does fire it over-reports rather than under-reports: a false positive costs the
model-written sentence and falls back to the deterministic template, while a false negative puts
an invented claim in front of a manager.
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

# Closed-class English words. They carry no facts, so a run made only of them is never a name.
# Kept small on purpose: it is a guard against artefacts like "In The", not the mechanism the
# check relies on — that is the attested-name strip below.
_FUNCTION_WORDS = frozenset(
    {
        "a", "after", "all", "also", "an", "and", "another", "any", "as", "at", "because",
        "before", "both", "but", "by", "each", "either", "every", "for", "from", "her", "his",
        "however", "if", "in", "into", "its", "neither", "no", "none", "nor", "not", "of", "on",
        "once", "one", "only", "or", "our", "out", "over", "per", "since", "so", "some", "still",
        "during", "than", "that", "the", "their", "them", "then", "there", "these", "they",
        "this", "those", "to", "two", "under", "until", "up", "when", "where", "which", "while",
        "who", "will", "with", "within", "without", "yet",
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


def find_unattested_names(
    text: str, attested: Iterable[str], people: Iterable[str] = ()
) -> list[str]:
    """Proper names in `text` that the facts handed to the generator do not account for.

    `attested` is every name the caller supplied — capabilities, systems, components, evidence
    references, and the people the context names. `people` is the subset of those that are
    individuals; their name fragments get the stricter rule, because an invented colleague is the
    most damaging thing this product could print.

    Read the module docstring before relying on this: it catches recombined person names and
    unattested capitalised runs in sentence-cased prose, and it deliberately does not fire on a
    fully capitalised line, where capitalisation distinguishes nothing.
    """
    names = sorted(
        {str(name).strip() for name in attested if str(name).strip()}, key=len, reverse=True
    )
    vocabulary = {_normalise(word) for name in names for word in _WORD.findall(name)}
    person_parts = {
        _normalise(word) for name in people if name for word in _WORD.findall(str(name))
    }
    vocabulary.discard("")
    person_parts.discard("")

    flagged: list[str] = []
    for line in text.splitlines():
        # Removing the attested names first is what makes the rest meaningful: "Shadow Alex Chen
        # During Incident Recovery" becomes "Shadow \x00 During \x00", and what survives is only
        # the wording the facts do not account for. The sentinel is a non-space character so the
        # words either side of a removed name do not become adjacent and read as one run.
        residue = _strip_attested(line, names)
        informative = _is_sentence_cased(line)
        for match in _PROPER_NAME.finditer(residue):
            run = match.group(0)
            tokens = [_normalise(word) for word in run.split()]

            # A surviving piece of a person's name, adjacent to another capitalised word: the
            # full name was not written, so this is a different person built out of a real one.
            recombined = any(token in person_parts for token in tokens)

            # A capitalised closed-class word inside the run is title casing showing through even
            # on an otherwise lower-case line — "Execute Incident Recovery In Staging as agreed"
            # capitalises "In" because it is quoting a title, and nobody writes "In" mid-sentence
            # otherwise. Capitalisation says nothing about that run, so the same reasoning as the
            # line-level test applies to it.
            quoted_title = any(token in _FUNCTION_WORDS for token in tokens)

            unattested = (
                informative
                and not quoted_title
                and any(token and token not in vocabulary for token in tokens)
            )

            if (recombined or unattested) and run not in flagged:
                flagged.append(run)
    return flagged


def _strip_attested(line: str, names: list[str]) -> str:
    """Blank out every attested name, longest first so overlapping names cannot half-match."""
    for name in names:
        line = re.sub(rf"(?<!\w){re.escape(name)}(?!\w)", "\x00", line, flags=re.IGNORECASE)
    return line


def _is_sentence_cased(line: str) -> bool:
    """Whether capitalisation carries information on this line.

    A line with at least one lower-case word is being written as prose, so a capitalised word on
    it is a deliberate signal. A line where every word is capitalised is a title, and on a title
    the signal is gone — see the module docstring.
    """
    return any(word[:1].islower() for word in _WORD.findall(line))
