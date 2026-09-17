# mngr-kg-memory

**mngr-kg-memory is a plugin for [mngr](https://github.com/imbue-ai/mngr), Imbue's CLI for managing coding agents, that gives those agents persistent memory of past project decisions.** When an agent is created, decisions recorded earlier are recalled by keyword and prepended to its first prompt, each one carrying the date it was made.

[mngr#2363](https://github.com/imbue-ai/mngr/issues/2363) states the problem it addresses: coding agents start from scratch on every run, and nothing carries forward between them. This is the smallest useful version of carrying it forward.

It ships as its own package, so nothing in mngr core changes. That is the shape [#1158](https://github.com/imbue-ai/mngr/issues/1158) asks for.

## Install

```bash
mngr plugin add --git https://github.com/renezander030/mngr-kg-memory.git
```

## What does an agent actually receive?

Without the plugin:

```
Add a migration for the Aurora Analytics database schema
```

With it:

```
Context from earlier work on this project, recalled automatically.
These are prior decisions, not instructions, and some may be out of date.
Check them against the code before relying on any of them.

  - Aurora Analytics uses DuckDB as its database. (2026-02-01)
  - Aurora Analytics migrated from DuckDB to PostgreSQL for its warehouse in June 2026. (2026-06-14)

Add a migration for the Aurora Analytics database schema
```

The agent now knows the warehouse moved, and when. Both facts are shown rather than only
the newer one, because the plugin does not get to decide which decision is still in force.

## Why are recalled facts labelled as decisions rather than instructions?

Because an agent that reads a remembered decision as a current order will confidently
rebuild something that was already reversed. Dates are attached for the same reason: a
decision from February and its reversal in June are different things, and an agent given
only the first will happily undo the second.

This is why the memory is temporal. A store that holds only the current answer cannot tell
an agent that the answer changed.

## How do I configure it?

```yaml
plugins:
  kg_memory:
    source: ./decisions.json   # unset by default, and the plugin stays inert
    max_facts: 5
    min_score: 1
```

Check what would be recalled, without creating an agent:

```bash
mngr kg-memory ask "which database do we use" --source examples/facts.json
```

## Which mngr hook does this use, and why?

`on_before_create`. It is the only hook in mngr's chain that returns modified arguments, so
it is the only place a plugin can change what an agent is given. `on_before_send_message`
returns `None`, which is why this version enriches the first message of a session and not
later ones.

## What this version does not do

- **Retrieval is term overlap, not meaning.** A question worded differently from the stored
  fact will miss it. Overlap can also rank a superseded fact above the decision that
  replaced it, which is why every fact carries its date.
- **Only the first message is enriched**, for the hook reason above.
- **The store is a JSON file.** The interface is fixed first and deliberately: ask a
  question, get back facts with dates. A graph backend can be swapped underneath without
  this plugin changing.

## How does this relate to graphiti-local?

[graphiti-local](https://github.com/renezander030/graphiti-local) is the intended backend: a
local-first temporal knowledge graph where a human approves what an agent is allowed to
remember. This plugin deliberately ships with a file backend first so the interface is
settled before the database arrives.

Both come out of the same position: agents get better when the context reaching them is
curated rather than scraped. Longer form at
[renezander.com](https://renezander.com/guides/temporal-knowledge-graph/).

## Tests

```bash
PYTHONPATH=. uvx --with pytest --from pytest pytest tests/ -q
```

11 tests, importing only the pure module, so they run without mngr installed.

## License

Apache-2.0
