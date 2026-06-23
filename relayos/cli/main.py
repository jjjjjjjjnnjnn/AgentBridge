"""CLI entry point -- `relayos run workflow.yaml` and more."""
from __future__ import annotations

import logging
import sys
from pathlib import Path

import click

from relayos import __version__
from relayos.adapters import get_adapter, list_adapters
from relayos.config import load_config
from relayos.memory.store import MemoryStore
from relayos.workflow.engine import WorkflowEngine
from relayos.workflow.models import Workflow, validate_workflow


@click.group()
@click.version_option(version=__version__, message="RelayOS v%(version)s")
def cli():
    """RelayOS — Persistent AI Workers for Developers. Like htop for your AI team..

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

    click.echo("+ RelayOS v" + __version__)
    click.echo("| Workflow: " + wf.name)
    click.echo("| Steps: " + str(len(wf.steps)))
    for i, step in enumerate(wf.steps):
        click.echo("|   " + str(i+1) + ". " + step.agent + ": " + step.prompt[:60] + "...")
    click.echo("+")

    # Initialize display and engine
    from relayos.cli.display import WorkflowDisplay
    memory = MemoryStore(cfg.memory.get("path", "~/.relayos/memory.db"))
    engine = WorkflowEngine(cfg, memory)

    display = WorkflowDisplay(wf.name)
    for s in wf.steps:
        display.add_step(s.agent, s.prompt)

    # Wire callbacks
    engine.on_step_start = lambda idx, agent, prompt: display.set_running(idx)
    engine.on_step_done = lambda idx, model, dur, chars: display.set_done(idx, model, dur, chars)
    engine.on_step_error = lambda idx, err: display.set_error(idx, err)

    # Start display and run
    display.start()
    try:
        results = engine.run(wf)
    except Exception as e:
        display.stop()
        click.echo(f"\n[ERR] {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)
    finally:
        display.stop()

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
    from relayos.adapters import list_adapters
    from relayos.config import PROVIDER_ENV_MAP

    click.echo("Available agents:")
    click.echo(f"{'Name':<15} {'Provider':<12} {'Default Model':<30} {'Config Key'}")
    click.echo("-" * 80)
    for name in list_adapters():
        from relayos.adapters import get_adapter
        try:
            inst = get_adapter(name, {})
            provider = getattr(inst, "provider", name)
            default = getattr(inst, "default_model", "-")
            key_hint = PROVIDER_ENV_MAP.get(name, "-")
            if not key_hint:
                key_hint = "-"
            click.echo(f"{name:<15} {provider:<12} {default:<30} {key_hint}")
        except Exception:
            click.echo(f"{name:<15} {'?':<12} {'?':<30} {'?'}")


@cli.command()
@click.argument("key")
@click.argument("value", nargs=-1, required=True)
@click.option("-s", "--session", help="Session ID")
@click.option("--db", default="~/.relayos/memory.db", help="DB path")
def remember(key: str, value: tuple[str], session: str | None, db: str):
    """Store a value in shared memory."""
    store = MemoryStore(db)
    store.set(key, " ".join(value), session)
    click.echo(f"[OK] Stored '{key}' in memory" + (f" (session: {session})" if session else ""))


@cli.command()
@click.argument("key")
@click.option("-s", "--session", help="Session ID")
@click.option("--db", default="~/.relayos/memory.db", help="DB path")
def recall(key: str, session: str | None, db: str):
    """Retrieve a value from shared memory."""
    store = MemoryStore(db)
    val = store.get(key, session)
    if val is None:
        click.echo(f"Key '{key}' not found in memory")
        sys.exit(1)
    click.echo(val)


@cli.command()
@click.option("--db", default="~/.relayos/memory.db", help="DB path")
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
@click.option("--db", default="~/.relayos/memory.db", help="DB path")
def init(db: str):
    """Create default config file."""
    from relayos.config import get_config_dir
    config_path = get_config_dir() / "config.yaml"
    if config_path.exists():
        click.echo(f"Config already exists: {config_path}")
        return

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("""# RelayOS Configuration
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

# Terminal instances (can have multiple of the same type)
# Each terminal wraps an AI CLI tool with its own model config.
terminals:
  - name: claude-main
    type: claude
    model: claude-sonnet-4-20250514

  - name: claude-fast
    type: claude
    model: claude-haiku-4-20251001

  - name: mimo-coder
    type: mimo
    model: gpt-4o

  - name: opencode-data
    type: opencode
    model: deepseek-chat

routing:
  default: balanced
  policies:
    coding: free_first
    research: quality_first
    quick: cheapest

mcp_servers: {}
""")
    click.echo(f"[OK] Created {config_path}")
    click.echo("  Edit it to add your API keys, then run: relayos run <workflow.yaml>")


# ─── Terminal Management ─────────────────────────────────────────


@cli.group()
def terminal():
    """Manage terminal instances -- spawn, list, run on AI CLI terminals."""
    pass


@terminal.command("types")
def terminal_types():
    """List all available terminal types and their installation status."""
    from relayos.terminals import list_terminal_types

    click.echo("Available terminal types:")
    click.echo(f"{'Type':<15} {'Binary':<15} {'Default Model':<30} {'Installed'}")
    click.echo("-" * 80)
    for t in list_terminal_types():
        status = "[OK]" if t["available"] else "[ERR]"
        click.echo(f"{t['type']:<15} {t['binary']:<15} {t['default_model']:<30} {status}")


@terminal.command("create")
@click.argument("type_name")
@click.option("-n", "--name", help="Friendly name for this terminal")
@click.option("-m", "--model", help="Model selection for this terminal")
@click.option("-c", "--config", type=click.Path(), help="Config file path")
def terminal_create(type_name: str, name: str | None, model: str | None, config: str | None):
    """Create a new terminal instance.

    TYPE_NAME is one of: claude, mimo, opencode, codex, qcode, custom
    """
    from relayos.orchestrator.pool import TerminalPool

    pool = TerminalPool(config)
    inst = pool.create(type_name=type_name, name=name, model=model)
    click.echo(f"[OK] Created terminal '{inst.name}' ({inst.id})")
    click.echo(f"  Type:  {inst.type}")
    click.echo(f"  Model: {inst.model}")
    click.echo(f"  Status: {inst.status}")


@terminal.command("list")
@click.option("-t", "--type", "type_filter", help="Filter by terminal type")
@click.option("-c", "--config", type=click.Path(), help="Config file path")
def terminal_list(type_filter: str | None, config: str | None):
    """List all running terminal instances."""
    from relayos.orchestrator.pool import TerminalPool

    pool = TerminalPool(config)
    instances = pool.list(type_filter=type_filter)

    if not instances:
        click.echo("No terminals. Create one: relayos terminal create claude")
        return

    h = f"{'ID':<20} {'Name':<20} {'Type':<12} {'Model':<30} {'Status':<10} {'Tasks':<8}"
    click.echo(h)
    click.echo("-" * len(h))
    for t in instances:
        click.echo(f"{t.id:<20} {t.name:<20} {t.type:<12} {t.model:<30} {t.status:<10} {t.task_count:<8}")


@terminal.command("run")
@click.argument("terminal_id")
@click.argument("prompt", nargs=-1, required=True)
@click.option("-c", "--config", type=click.Path(), help="Config file path")
def terminal_run(terminal_id: str, prompt: tuple[str], config: str | None):
    """Run a prompt on a specific terminal."""
    from relayos.orchestrator.pool import TerminalPool

    pool = TerminalPool(config)
    full_prompt = " ".join(prompt)
    click.echo(f"Running on '{terminal_id}'...")
    result = pool.run(terminal_id, full_prompt)
    if result.error:
        click.echo(f"[ERR] {result.error}", err=True)
    else:
        click.echo(result.content)
    click.echo(f"\n[Duration: {result.duration_ms}ms | Exit: {result.exit_code}]")


@terminal.command("remove")
@click.argument("terminal_id")
@click.option("-c", "--config", type=click.Path(), help="Config file path")
def terminal_remove(terminal_id: str, config: str | None):
    """Remove a terminal instance."""
    from relayos.orchestrator.pool import TerminalPool

    pool = TerminalPool(config)
    if pool.remove(terminal_id):
        click.echo(f"[OK] Removed terminal '{terminal_id}'")
    else:
        click.echo(f"[ERR] Terminal '{terminal_id}' not found", err=True)
        sys.exit(1)


@terminal.command("stats")
@click.option("-c", "--config", type=click.Path(), help="Config file path")
def terminal_stats(config: str | None):
    """Show terminal pool statistics."""
    from relayos.orchestrator.pool import TerminalPool

    pool = TerminalPool(config)
    s = pool.stats()
    click.echo("Terminal Pool Statistics:")
    click.echo(f"  Total:        {s['total']}")
    click.echo(f"  Idle:         {s['idle']}")
    click.echo(f"  Busy:         {s['busy']}")
    click.echo(f"  Error:        {s['error']}")
    click.echo(f"  Total Tasks:  {s['total_tasks']}")
    click.echo(f"  Est. Tokens:  {s['total_tokens_estimated']}")
    click.echo(f"  By Type:      {s['by_type']}")


@terminal.command("exec")
@click.argument("type_name")
@click.argument("prompt", nargs=-1, required=True)
@click.option("-m", "--model", help="Model override")
@click.option("-c", "--config", type=click.Path(), help="Config file path")
def terminal_exec(type_name: str, prompt: tuple[str], model: str | None, config: str | None):
    """Run on first available terminal of given type (auto-create if needed)."""
    from relayos.orchestrator.pool import TerminalPool

    pool = TerminalPool(config)
    full_prompt = " ".join(prompt)
    click.echo(f"Dispatching to {type_name}...")
    result = pool.run_on_type(type_name, full_prompt)
    if result.error:
        click.echo(f"[ERR] {result.error}", err=True)
    else:
        click.echo(result.content)
    click.echo(f"\n[Duration: {result.duration_ms}ms | Model: {result.model}]")


# ─── Cost Manager ───────────────────────────────────────────


@cli.group()
def cost():
    """Track API usage and costs across providers."""
    pass


@cost.command("report")
@click.option("--db", default="~/.relayos/cost.db", help="Cost DB path")
def cost_report(db: str):
    """Show API usage and cost summary."""
    from relayos.cost import CostManager
    cm = CostManager(db)
    click.echo(cm.get_summary())


@cost.command("track")
@click.argument("provider")
@click.argument("model")
@click.option("--input", "in_tokens", default=0, type=int)
@click.option("--output", "out_tokens", default=0, type=int)
@click.option("--db", default="~/.relayos/cost.db", help="Cost DB path")
def cost_track(provider: str, model: str, in_tokens: int, out_tokens: int, db: str):
    """Manually record API usage."""
    from relayos.cost import CostManager
    cm = CostManager(db)
    cm.track(provider, model, in_tokens, out_tokens)
    click.echo(f"[OK] Recorded {provider}/{model}: {in_tokens} in / {out_tokens} out")


# ─── Flow Router ────────────────────────────────────────────


@cli.group()
def route():
    """Analyze and route prompts to optimal providers."""
    pass


@route.command("analyze")
@click.argument("prompt", nargs=-1, required=True)
@click.option("-p", "--policy", default="balanced", help="Routing policy: balanced, cheapest, quality, free_first")
def route_analyze(prompt: tuple[str], policy: str):
    """Show which provider a prompt would be routed to."""
    from relayos.core.router import FlowRouter
    router = FlowRouter()
    full = " ".join(prompt)
    decision = router.route(full, policy=policy)
    click.echo(f"Task type:    {decision.task_type}")
    click.echo(f"Provider:     {decision.provider}")
    click.echo(f"Confidence:   {decision.confidence:.0%}")
    click.echo(f"Reason:       {decision.reason}")
    click.echo(f"Est. tokens:  {decision.estimated_tokens}")


# ─── Worker Inbox ───────────────────────────────────────────


@cli.group()
def inbox():
    """Worker inbox — send and receive messages between agents."""
    pass


@inbox.command("send")
@click.argument("to")
@click.argument("body", nargs=-1, required=True)
@click.option("-s", "--subject", default="", help="Message subject")
@click.option("-f", "--from-worker", default="cli", help="Sender")
def inbox_send(to: str, body: tuple[str], subject: str, from_worker: str):
    """Send a message to a worker."""
    from relayos.core.inbox import WorkerInbox
    inbox_mgr = WorkerInbox()
    mid = inbox_mgr.send(to=to, body=" ".join(body), subject=subject, from_worker=from_worker)
    click.echo(f"[OK] Sent message #{mid} to '{to}'")


@inbox.command("list")
@click.argument("worker")
@click.option("--all", "show_all", is_flag=True, help="Show all messages (not just unread)")
def inbox_list(worker: str, show_all: bool):
    """List inbox messages for a worker."""
    from relayos.core.inbox import WorkerInbox
    inbox_mgr = WorkerInbox()
    msgs = inbox_mgr.list_inbox(worker, unread_only=not show_all)
    if not msgs:
        click.echo(f"Inbox for '{worker}' is empty.")
        return
    for m in msgs:
        status = "📩" if m["status"] == "unread" else "📖"
        preview = m["body"][:80] + "..." if len(m["body"]) > 80 else m["body"]
        click.echo(f"  #{m['id']} {status} from:{m['from_worker']} | {m['subject'] or 'no subject'}")
        click.echo(f"      {preview}")

    unread = sum(1 for m in msgs if m["status"] == "unread")
    click.echo(f"\n[{len(msgs)} messages, {unread} unread]")


@inbox.command("stats")
def inbox_stats():
    """Show inbox statistics."""
    from relayos.core.inbox import WorkerInbox
    inbox_mgr = WorkerInbox()
    s = inbox_mgr.get_stats()
    click.echo(f"Total messages:  {s['total']}")
    click.echo(f"Unread:          {s['unread']}")
    click.echo(f"Per worker:      {s['per_worker']}")


# ─── Worker Focus ──────────────────────────────────────────


@cli.command()
@click.argument("worker_name")
def focus(worker_name: str):
    """Focus on a single worker — see their identity, decisions, inbox."""
    from relayos.tui.focus import focus_worker
    focus_worker(worker_name)


# ─── Team Templates ────────────────────────────────────────


@cli.group()
def team():
    """Manage AI teams — create from templates."""
    pass


@team.command("create")
@click.argument("template_name")
def team_create(template_name: str):
    """Create a team from a template (startup, research, devops, writing)."""
    from relayos.core.team import create_team, list_templates
    from relayos.core.worker import WorkerManager
    wm = WorkerManager()
    try:
        created = create_team(template_name, wm)
        if created:
            click.echo(f"[OK] Created team '{template_name}' with {len(created)} workers:")
            for name in created:
                w = wm.get(name)
                click.echo(f"  {w.emoji} {w.name:<15} {w.role:<14} {w.provider}/{w.model}" if w else f"  {name}")
        else:
            click.echo(f"[OK] Team '{template_name}' already exists.")
    except ValueError as e:
        click.echo(f"[ERR] {e}", err=True)


@team.command("list")
def team_list():
    """List available team templates."""
    from relayos.core.team import list_templates
    templates = list_templates()
    click.echo("Available team templates:")
    for t in templates:
        click.echo(f"  {t['name']:<15} {t['worker_count']} workers — {t['description']}")


# ─── Terminal Switching ─────────────────────────────────────


@cli.command()
@click.argument("terminal_name", required=False)
@click.option("--list", "list_flag", is_flag=True, help="Show available terminals")
def use(terminal_name: str | None, list_flag: bool):
    """Switch default terminal or show available terminals.

    Examples:
        relay use opencode    # switch to OpenCode (free)
        relay use mimo        # switch to Mimo (free)
        relay use claude      # switch to Claude
        relay use             # show current terminal
        relay use --list      # show all terminals with strengths
    """
    from relayos.config import get_config_dir, load_config
    import yaml

    if list_flag:
        from relayos.terminals.scheduler import format_terminal_help
        click.echo(format_terminal_help())
        return

    config_dir = get_config_dir()
    config_path = config_dir / "config.yaml"

    if not terminal_name:
        # Show current
        cfg = load_config()
        current = getattr(cfg, "routing", None)
        default = getattr(current, "default", "balanced") if current else "balanced"
        click.echo(f"Current terminal: {default}")
        click.echo("Switch: relay use <opencode|mimo|claude|free|balanced|quality>")
        return

    valid_terminals = ("opencode", "mimo", "claude", "codex", "qcode")
    valid_profiles = ("free", "balanced", "quality")

    if terminal_name in valid_profiles:
        # It's a profile name
        if config_path.exists():
            cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            cfg.setdefault("routing", {})["default"] = terminal_name
            config_path.write_text(yaml.dump(cfg, default_flow_style=False, allow_unicode=True), encoding="utf-8")
        click.echo(f"[OK] Switched to profile: {terminal_name}")
        return

    if terminal_name in valid_terminals:
        if config_path.exists():
            cfg = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            cfg.setdefault("routing", {})["default"] = terminal_name
            config_path.write_text(yaml.dump(cfg, default_flow_style=False, allow_unicode=True), encoding="utf-8")
        click.echo(f"[OK] Switched to terminal: {terminal_name}")
        return

    click.echo(f"[ERR] Unknown terminal/profile: {terminal_name}")
    click.echo("Try: opencode, mimo, claude, free, balanced, quality")


# ─── Execution Planner ──────────────────────────────────────


@cli.command()
@click.argument("task", nargs=-1, required=True)
@click.option("-p", "--profile", default="balanced", help="Routing profile: free, balanced, quality")
@click.option("--execute", "-x", is_flag=True, help="Execute the plan immediately")
def plan(task: tuple[str], profile: str, execute: bool):
    """Plan and execute multi-step tasks.

    Analyzes a task, decomposes it into steps, assigns optimal
    models, and optionally executes the full plan.

    Examples:
        relay plan "Implement JWT auth in FastAPI"
        relay plan "Review this codebase" -x
        relay plan "Design a payment system" --profile quality
    """
    from relayos.core.planner import ExecutionPlanner
    planner = ExecutionPlanner()
    task_str = " ".join(task)
    p = planner.plan(task_str, profile)
    click.echo(planner.format_plan(p))

    if execute:
        click.echo("Executing plan...")
        from relayos.core.worker import WorkerManager
        from relayos.adapters import get_adapter
        from relayos.config import load_config
        cfg = load_config()

        context = {}
        for i, step in enumerate(p.steps):
            click.echo(f"\n  [{i+1}/{len(p.steps)}] {step.description}...")
            prompt = step.prompt_template.format(task=task_str)
            # Resolve template variables from previous steps
            for k, v in context.items():
                prompt = prompt.replace("{{" + k + "}}", str(v))

            adapter = get_adapter(step.provider, {
                "api_key": cfg.resolve_api_key(step.provider),
                "model": step.model,
            })
            try:
                response = adapter.chat(prompt)
                step.status = "done"
                context[step.id] = response.content
                click.echo(f"  ✓ {len(response.content)} chars")
            except Exception as e:
                step.status = "error"
                click.echo(f"  ✗ {e}", err=True)

        done = sum(1 for s in p.steps if s.status == "done")
        click.echo(f"\n[OK] {done}/{len(p.steps)} steps completed")


@cli.command()
@click.argument("profile_name", default="balanced")
def profile(profile_name: str):
    """Set routing profile: free, balanced, or quality."""
    valid = ("free", "balanced", "quality")
    if profile_name not in valid:
        click.echo(f"[ERR] Invalid profile '{profile_name}'. Choose: {', '.join(valid)}", err=True)
        return
    # Save to config
    from relayos.config import get_config_dir
    import yaml
    config_dir = get_config_dir()
    config_path = config_dir / "config.yaml"
    if config_path.exists():
        cfg = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        if cfg is None:
            cfg = {}
        if "routing" not in cfg:
            cfg["routing"] = {}
        cfg["routing"]["default"] = profile_name
        config_path.write_text(yaml.dump(cfg, default_flow_style=False, allow_unicode=True), encoding="utf-8")
    click.echo(f"[OK] Routing profile set to '{profile_name}'")


@cli.command()
@click.argument("prompt", nargs=-1, required=True)
@click.option("-t", "--task-type", help="Task type (auto-detected if omitted)")
def estimate(prompt: tuple[str], task_type: str | None):
    """Estimate cost and best model for a task across all profiles."""
    from relayos.core.scheduler import ModelScheduler
    scheduler = ModelScheduler()
    full = " ".join(prompt)
    results = scheduler.estimate(full, task_type)

    click.echo("Cost Estimates:")
    click.echo(f"{'Profile':<12} {'Model':<32} {'Tier':<12} {'Cost':<12} {'Confidence':<10}")
    click.echo("-" * 80)
    for profile, info in results.items():
        cost_str = f"${info['estimated_cost']:.4f}" if info['estimated_cost'] > 0 else "free"
        click.echo(f"{profile:<12} {info['model']:<32} {info['cost_tier']:<12} {cost_str:<12} {info['confidence']:<10}")
        click.echo(f"  {'':<12} {info['reason']}")
    click.echo(f"\nApply: relayos profile <name>")


# ─── Register extension command groups ──────────────────────

try:
    from relayos.cli.config_commands import config as config_grp, plugin as plugin_grp
    cli.add_command(config_grp)
    cli.add_command(plugin_grp)
except ImportError:
    pass  # config_commands not available


@cli.command()
@click.option("--host", default="127.0.0.1", help="Bind address")
@click.option("--port", default=8080, type=int, help="Port")
@click.option("--open", "open_browser", is_flag=True, help="Open browser")
@click.option("-c", "--config", type=click.Path(), help="Config file path")
def serve(host: str, port: int, open_browser: bool, config: str | None):
    """Start the web dashboard."""
    import webbrowser
    import uvicorn

    from relayos.server.api import create_app
    app = create_app(config)

    url = f"http://{host}:{port}"
    click.echo(f"RelayOS Dashboard: {url}")
    if open_browser:
        webbrowser.open(url)

    uvicorn.run(app, host=host, port=port, log_level="info")
