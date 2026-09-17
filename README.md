# mngr-kg-memory

Give a [mngr](https://github.com/imbue-ai/mngr) agent the decisions the last one already made.

[mngr#2363](https://github.com/imbue-ai/mngr/issues/2363) states the problem: agents start
from scratch, and nothing carries forward between runs. This is the smallest useful version
of carrying it forward. When an agent is created with an initial message, that message is
used as a query against a file of remembered facts, and whatever matches is prepended.

It is a plugin in its own package, so nothing in mngr core changes. Install it the way
[#1158](https://github.com/imbue-ai/mngr/issues/1158) describes:

```bash
mngr plugin add --git https://github.com/renezander030/mngr-kg-memory.git
```

## What an agent sees

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

The agent now knows the warehouse moved, and when. The facts are labelled as prior
decisions rather than instructions on purpose: an agent that reads a remembered decision
as a current order will confidently rebuild something that was already reversed.

## Configuration

```yaml
plugins:
  kg_memory:
    source: ./decisions.json   # unset by default, and the plugin stays inert
    max_facts: 5
    min_score: 1
```

Check recall without creating an agent:

```bash
mngr kg-memory ask "which database do we use" --source examples/facts.json
```

## What this version does not do

- **Retrieval is term overlap, not meaning.** A question worded differently from the stored
  fact will miss it. Overlap can also rank a superseded fact above the decision that
  replaced it, which is why every fact carries its date.
- **Only the first message is enriched.** `on_before_create` is the one hook in the chain
  that returns modified arguments; `on_before_send_message` returns `None`, so later
  messages in a session cannot be enriched the same way.
- **The store is a JSON file.** The interface is fixed first and deliberately: ask a
  question, get back facts with dates. A graph backend can be swapped underneath without
  this plugin changing, and [graphiti-local](https://github.com/renezander030/graphiti-local)
  is the intended one, with human approval sitting between an agent and what it writes.

## Tests

```bash
PYTHONPATH=. uvx --with pytest --from pytest pytest tests/ -q
```

## License

Apache-2.0
