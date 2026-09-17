"""`mngr kg-memory` so recall can be checked without creating an agent."""

from pathlib import Path

import click

from imbue.mngr_kg_memory.memory import load_facts
from imbue.mngr_kg_memory.memory import recall


@click.group("kg-memory")
def kg_memory_group() -> None:
    """Inspect the decisions a new agent would be given."""


@kg_memory_group.command("ask")
@click.argument("question")
@click.option("--source", type=click.Path(exists=True, dir_okay=False, path_type=Path), required=True)
@click.option("--limit", type=int, default=5, show_default=True)
@click.option("--min-score", type=int, default=1, show_default=True)
def ask(question: str, source: Path, limit: int, min_score: int) -> None:
    """Show which remembered facts QUESTION recalls."""
    matched = recall(load_facts(source), question, limit=limit, min_score=min_score)
    if not matched:
        click.echo("no match")
        return
    for fact in matched:
        click.echo(f"  - {fact.render()}")
