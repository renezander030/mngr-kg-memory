"""Give a new agent the decisions the last one already made.

mngr#2363 puts the problem plainly: agents start from scratch, and nothing carries
forward between runs. This plugin does the smallest useful version of carrying it
forward. When an agent is created with an initial message, the message is used as a
query against a file of remembered facts, and whatever matches is prepended.

on_before_create is the hook that can do this, because it is the only one in the
chain that returns modified arguments. on_before_send_message returns None, so a
later message cannot be enriched the same way, and that is a deliberate limit of
this version rather than an oversight.
"""

from collections.abc import Sequence

import click

from imbue.mngr import hookimpl
from imbue.mngr.config.plugin_registry import register_plugin_config
from imbue.mngr.plugins.hookspecs import MngrContext
from imbue.mngr.plugins.hookspecs import OnBeforeCreateArgs
from imbue.imbue_common.model_update import to_update

from imbue.mngr_kg_memory.cli import kg_memory_group
from imbue.mngr_kg_memory.config import KgMemoryPluginConfig
from imbue.mngr_kg_memory.memory import compose_preamble
from imbue.mngr_kg_memory.memory import load_facts
from imbue.mngr_kg_memory.memory import recall

PLUGIN_NAME = "kg_memory"

register_plugin_config(PLUGIN_NAME, KgMemoryPluginConfig)


@hookimpl
def register_cli_commands() -> Sequence[click.Command]:
    """Expose the same recall the hook uses, so it can be inspected without creating an agent."""
    return [kg_memory_group]


@hookimpl
def on_before_create(args: OnBeforeCreateArgs, mngr_ctx: MngrContext) -> OnBeforeCreateArgs | None:
    """Prepend remembered decisions to the agent's first message.

    Returns None whenever there is nothing to add, which leaves creation untouched.
    A missing or unreadable source is treated the same way: memory is an improvement
    to a prompt, and failing to find it must never stop an agent from being created.
    """
    config = mngr_ctx.get_plugin_config(PLUGIN_NAME, KgMemoryPluginConfig)
    if config.source is None:
        return None

    message = args.agent_options.initial_message
    if not message:
        return None

    try:
        facts = load_facts(config.source)
    except (OSError, ValueError):
        return None

    matched = recall(facts, message, limit=config.max_facts, min_score=config.min_score)
    if not matched:
        return None

    enriched = compose_preamble(matched, message)
    options = args.agent_options.model_copy_update(
        to_update(args.agent_options.field_ref().initial_message, enriched),
    )
    return args.model_copy_update(to_update(args.field_ref().agent_options, options))
