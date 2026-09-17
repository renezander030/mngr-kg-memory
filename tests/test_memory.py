"""Tests for recall and prompt composition.

These import only the pure module, so they run without mngr installed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from imbue.mngr_kg_memory.memory import Fact
from imbue.mngr_kg_memory.memory import compose_preamble
from imbue.mngr_kg_memory.memory import load_facts
from imbue.mngr_kg_memory.memory import recall
from imbue.mngr_kg_memory.memory import terms

FACTS = (
    Fact("Aurora Analytics migrated from DuckDB to PostgreSQL in June 2026.", "2026-06-14T00:00:00+00:00"),
    Fact("Aurora Analytics uses DuckDB as its database.", "2026-02-01T00:00:00+00:00"),
    Fact("The payments team writes its services in Go rather than Python.", "2026-03-09T00:00:00+00:00"),
)


def test_stopwords_do_not_count_as_matches() -> None:
    assert terms("what is the database") == {"database"}


def test_recall_ranks_by_overlap() -> None:
    matched = recall(FACTS, "which database does Aurora Analytics use", limit=3, min_score=1)
    assert "Aurora Analytics" in matched[0].text
    assert all("Aurora" in fact.text for fact in matched)


def test_newer_decision_wins_a_tie() -> None:
    """Two equally matching decisions must offer the later one first, or an agent
    rebuilds something that was already reversed."""
    matched = recall(FACTS, "Aurora Analytics DuckDB", limit=2, min_score=2)
    assert matched[0].valid_at.startswith("2026-06-14")


def test_min_score_filters_weak_matches() -> None:
    assert recall(FACTS, "Aurora", limit=5, min_score=2) == ()


def test_empty_question_recalls_nothing() -> None:
    assert recall(FACTS, "the and of", limit=5, min_score=1) == ()


def test_preamble_labels_facts_as_possibly_stale() -> None:
    out = compose_preamble(FACTS[:1], "Add a migration.")
    assert "not instructions" in out
    assert "out of date" in out
    assert out.endswith("Add a migration.")


def test_preamble_passes_message_through_when_nothing_recalled() -> None:
    assert compose_preamble((), "Add a migration.") == "Add a migration."


@pytest.mark.parametrize(
    "payload",
    [
        [{"fact": "A release needs two approvals.", "valid_at": "2026-05-30T00:00:00+00:00"}],
        {"facts": [{"text": "A release needs two approvals."}]},
        ["A release needs two approvals."],
    ],
)
def test_load_accepts_every_shape_a_caller_is_likely_to_have(tmp_path: Path, payload) -> None:
    path = tmp_path / "facts.json"
    path.write_text(json.dumps(payload))
    facts = load_facts(path)
    assert len(facts) == 1
    assert "two approvals" in facts[0].text


def test_load_skips_entries_with_no_text(tmp_path: Path) -> None:
    path = tmp_path / "facts.json"
    path.write_text(json.dumps([{"valid_at": "2026-01-01T00:00:00+00:00"}, {"fact": "kept"}]))
    assert [fact.text for fact in load_facts(path)] == ["kept"]
