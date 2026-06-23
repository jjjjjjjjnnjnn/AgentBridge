"""CLI entry point — `agentmesh run workflow.yaml` and more."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import click

from agentmesh import __version__
from agentmesh.adapters import get_adapter, list_adapters
from agentmesh.config import load_config
from agentmesh.memory.store import MemoryStore
from agentmesh.workflow.engine import WorkflowEngine
from agentmesh.workflow.models import Workflow, validate_workflow


@click.group()
@click.version_option(version=__version__, message="AgentMesh v%(version)s")
def cli():
    """AgentMesh — Multi-agent orchestration for AI tools.

    Run workflows across Claude, GPT, Gemini and local models
    with shared memory and MCP tool integration.
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        stream=sys.stderr,
    )


@cli.command()
@click.argument("workflow_file", type=click.Path(exists=True))
@click.option("-c", "--config", type=click.Path(), help="Config file path")
@click.option("--verbose", "-v", is_flag=True, help="Show detailed output")
@click.option("--list-adapters", is_flag=True, help="List available adapters and exit")
def run(workflow_file: str, config: str | None, verbose: bool, list_adapters: bool):
    """Run a multi-agent workflow from a YAML file."""
    if list_adapters:
        click.echo("Available adapters:")
        for name in list_adapters():
            click.echo(f"  * {name}")
        return

    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Load config
    cfg = load_config(Path(config) if config else None)

    # Parse workflow
    wf = Workflow.from_yaml(workflow_file)
    errors = validate_workflow(wf)
    if errors:
        click.echo("Workflow validation errors:", err=True)
        for e in errors:
            click.echo(f"  [ERR] {e}", err=True)
        sys.exit(1)

    click.echo("+ AgentMesh v" + __version__)
    click.echo("| Workflow: " + wf.name)
    click.echo("| Steps: " + str(len(wf.steps)))
    for i, step in enumerate(wf.steps):
        click.echo("|   " + str(i+1) + ". " + step.agent + ": " + step.prompt[:60] + "...")
    click.echo("+")

    # Initialize engine
    memory = MemoryStore(cfg.memory.get("path", "~/.agentmesh/memory.db"))
    engine = WorkflowEngine(cfg, memory)

    # Run
    try:
        results = engine.run(wf)
    except Exception as e:
        click.echo(f"\n[ERR] Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

    # Output results
    click.echo(f"\n{'='*50}")
    click.echo("Results:")
    click.echo(f"{'='*50}")
    for r in results:
        click.echo(f"\n-- Step {r['step']}: {r['agent']} ({r['model']}) --")
        click.echo(r["content"])
        if r["usage"]:
            click.echo(f"  [tokens: {r['usage']}]")

    click.echo(f"\n[OK] Workflow '{wf.name}' completed ({len(results)} steps)")


@cli.command()
@click.argument("agent_name")
@click.argument("prompt", nargs=-1, required=True)
@click.option("-m", "--model", help="Model override")
@click.option("-c", "--config", type=click.Path(), help="Config file path")
def chat(agent_name: str, prompt: tuple[str], model: str | None, config: str | None):
    """Send a single prompt to one agent (quick test)."""
    cfg = load_config(Path(config) if config else None)
    provider_cfg = cfg.providers.get(agent_name, {})

    adapter = get_adapter(agent_name, {
        "api_key": cfg.resolve_api_key(agent_name),
        "model": model or provider_cfg.get("model", ""),
        "base_url": provider_cfg.get("base_url"),
    })

    full_prompt = " ".join(prompt)
    click.echo(f"Agent: {adapter.provider} ({adapter.model})")
    click.echo(f"Prompt: {full_prompt[:100]}...")
    click.echo()

    response = adapter.chat(full_prompt)
    click.echo(response.content)
    click.echo(f"\n[Model: {response.model} | Tokens: {response.usage}]")


@cli.command()
def agents():
    """List all available agent adapters and their default models."""
    click.echo("Available agents:")
    click.echo(f"{'Name':<15} {'Provider':<12} {'Default Model':<30} {'Config Key'}")
    click.echo("-" * 80)

    from agentmesh.adapters import _REGISTRY
    for name, cls in sorted(_REGISTRY.items()):
        provider = cls.provider if hasattr(cls, "provider") else name
        default = cls.default_model if hasattr(cls, "default_model") else "-"
        key_hint = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GEMINI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
        }.get(name, "-")
        click.echo(f"{name:<15} {provider:<12} {default:<30} {key_hint}")


@cli.command()
@click.argument("key")
@click.argument("value", nargs=-1, required=True)
@click.option("-s", "--session", help="Session ID")
@click.option("--db", default="~/.agentmesh/memory.db", help="DB path")
def remember(key: str, value: tuple[str], session: str | None, db: str):
    """Store a value in shared memory."""
    store = MemoryStore(db)
    store.set(key, " ".join(value), session)
    click.echo(f"[OK] Stored '{key}' in memory" + (f" (session: {session})" if session else ""))


@cli.command()
@click.argument("key")
@click.option("-s", "--session", help="Session ID")
@click.option("--db", default="~/.agentmesh/memory.db", help="DB path")
def recall(key: str, session: str | None, db: str):
    """Retrieve a value from shared memory."""
    store = MemoryStore(db)
    val = store.get(key, session)
    if val is None:
        click.echo(f"Key '{key}' not found in memory")
        sys.exit(1)
    click.echo(val)


@cli.command()
@click.option("--db", default="~/.agentmesh/memory.db", help="DB path")
def memory_list(db: str):
    """List all keys in shared memory."""
    store = MemoryStore(db)
    items = store.get_all()
    if not items:
        click.echo("Memory is empty")
        return
    for key, val in items.items():
        preview = val[:80] + "..." if len(val) > 80 else val
        click.echo(f"  {key}: {preview}")


@cli.command()
@click.option("--db", default="~/.agentmesh/memory.db", help="DB path")
def init(db: str):
    """Create default config file."""
    config_path = Path.home() / ".agentmesh" / "config.yaml"
    if config_path.exists():
        click.echo(f"Config already exists: {config_path}")
        return

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("""# AgentMesh Configuration
# Set API keys via environment variables or uncomment below.

providers:
  openai:
    model: gpt-4o
    # api_key: ${OPENAI_API_KEY}

  anthropic:
    model: claude-sonnet-4-20250514
    # api_key: ${ANTHROPIC_API_KEY}

  google:
    model: gemini-2.5-flash
    # api_key: ${GEMINI_API_KEY}

  deepseek:
    model: deepseek-chat
    # api_key: ${DEEPSEEK_API_KEY}

  ollama:
    model: qwen2.5:7b
    base_url: http://localhost:11434

routing:
  default: balanced
  policies:
    coding: free_first
    research: quality_first
    quick: cheapest
""")
    click.echo(f"[OK] Created {config_path}")
    click.echo("  Edit it to add your API keys, then run: agentmesh run <workflow.yaml>")
