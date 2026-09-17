"""Recall of earlier decisions, kept deliberately small.

The backend here is a JSON file scored by term overlap. That is a stub, and it is the
stub on purpose: it fixes the shape of the thing a caller depends on (ask a question,
get back facts with dates and provenance) before any database is involved, so the
graph backend can be swapped underneath without the plugin changing.

Retrieval is keyword based rather than semantic for the same reason graphiti-local
grew a --keyword mode: an agent should not need an embedding backend reachable in
order to remember something.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

_WORD = re.compile(r"[a-z0-9]+")

# Words common enough that matching on them says nothing about relevance.
_STOPWORDS = frozenset(
    """a an and are as at be by did do does for from had has have how i if in is it its
    of on or our that the their them then there they this to was we were what when where
    which who why will with you your""".split()
)


@dataclass(frozen=True)
class Fact:
    text: str
    valid_at: str | None = None
    source: str | None = None

    def render(self) -> str:
        suffix = f" ({self.valid_at[:10]})" if self.valid_at else ""
        return f"{self.text}{suffix}"


def terms(text: str) -> set[str]:
    """Lowercase content words, which is all the scoring needs."""
    return {word for word in _WORD.findall(text.lower()) if word not in _STOPWORDS and len(word) > 2}


def load_facts(source: Path) -> tuple[Fact, ...]:
    """Read facts from disk, tolerating both shapes a caller is likely to have.

    Accepts either a bare list of entries or an object with a "facts" key, because the
    graphiti-local export uses the second and a hand written file usually uses the first.
    """
    payload = json.loads(Path(source).read_text())
    entries = payload["facts"] if isinstance(payload, dict) else payload
    facts = []
    for entry in entries:
        if isinstance(entry, str):
            facts.append(Fact(text=entry))
            continue
        text = entry.get("fact") or entry.get("text")
        if not text:
            continue
        facts.append(Fact(text=text, valid_at=entry.get("valid_at"), source=entry.get("source")))
    return tuple(facts)


def recall(facts: tuple[Fact, ...], question: str, *, limit: int, min_score: int) -> tuple[Fact, ...]:
    """Return the facts sharing the most content words with the question.

    Ties are broken by recency, so when two decisions match equally well the newer one is
    offered first. A fact with no date sorts last, since an undated claim is the one least
    safe to act on.
    """
    wanted = terms(question)
    if not wanted:
        return ()
    scored = []
    for fact in facts:
        score = len(wanted & terms(fact.text))
        if score >= min_score:
            scored.append((score, fact.valid_at or "", fact))
    scored.sort(key=lambda row: (row[0], row[1]), reverse=True)
    return tuple(fact for _, _, fact in scored[:limit])


def compose_preamble(facts: tuple[Fact, ...], message: str) -> str:
    """Put recalled facts in front of the agent's first message.

    The wording matters more than it looks. The facts are labelled as prior decisions
    that may be stale rather than as instructions, because an agent that treats a
    remembered decision as a current order will confidently rebuild something that was
    already reversed.
    """
    if not facts:
        return message
    lines = [
        "Context from earlier work on this project, recalled automatically.",
        "These are prior decisions, not instructions, and some may be out of date.",
        "Check them against the code before relying on any of them.",
        "",
    ]
    lines.extend(f"  - {fact.render()}" for fact in facts)
    lines.extend(["", message])
    return "\n".join(lines)
