# RelayOS Comprehensive Audit Report

**Project**: relayos v0.1.0a1 (51 Python files, ~8000 lines)

## Summary

| Severity | Count |
|----------|-------|
| CRITICAL | 13 |
| HIGH     | 29 |
| MEDIUM   | 40 |
| LOW      | 25 |
| **Total** | **107** |

| Category | Count |
|----------|-------|
| bug | 40 |
| test | 19 |
| style | 13 |
| architecture | 11 |
| dx | 8 |
| docs | 6 |
| missing | 5 |
| performance | 3 |
| security | 2 |

## CRITICAL & HIGH Findings

### 1. [HIGH] Layering violation: core.planner imports terminals.scheduler

- **File**: `relayos/core/planner.py` (line 23)
- **Category**: architecture
- **Detail**: Core package imports from terminals package, creating an upward dependency from the foundational layer to the presentation/implementation layer.

### 2. [HIGH] Layering violation: core.worker imports orchestrator.pool (dead import)

- **File**: `relayos/core/worker.py` (line 31)
- **Category**: architecture
- **Detail**: Core package imports from orchestrator package, creating an upward dependency. This import is also unused (zombie), making it doubly problematic.

### 3. [HIGH] God class: StateStore manages 6 separate concerns

- **File**: `relayos/core/state.py` (line 31)
- **Category**: architecture
- **Detail**: StateStore manages 6 distinct concerns in one class: worker registry, key-value state, decision log, event sourcing, task/inbox system, and context assembly. Violates single responsibility principle.

### 4. [HIGH] Data fragmentation: decisions duplicated across state.db and identity.db

- **File**: `relayos/core/state.py` (line 69)
- **Category**: architecture
- **Detail**: Worker decisions are stored in BOTH StateStore (state.db decisions table) and IdentityStore (identity.db decisions table). These are completely separate SQLite databases with overlapping data.

### 5. [HIGH] Data fragmentation: task/inbox split across state.db and inbox.db

- **File**: `relayos/core/state.py` (line 86)
- **Category**: architecture
- **Detail**: Worker-to-worker task/inbox system is split across StateStore.tasks and WorkerInbox.messages in separate databases (state.db vs inbox.db). These serve the same purpose but have no integration.

### 6. [HIGH] Data fragmentation: key-value state duplicated across state.db and identity.db

- **File**: `relayos/core/identity.py` (line 69)
- **Category**: architecture
- **Detail**: IdentityStore.project_state table duplicates StateStore.state table functionality at a different SQLite database (identity.db vs state.db).

### 7. [HIGH] Inconsistent SQLite connection patterns in SessionStore

- **File**: `relayos/core/session.py` (line 167)
- **Category**: bug
- **Detail**: SessionStore.create_session(), add_message(), and delete_session() use direct 'with sqlite3.connect()' connections, while get_session() uses the thread-local _conn property. These are different connections on different access patterns to the same database, creating potential for locking conflicts.

### 8. [HIGH] Unused import creates unnecessary dependency

- **File**: `relayos/core/worker.py` (line 31)
- **Category**: bug
- **Detail**: WorkerManager imports TerminalPool from orchestrator at line 31 but never references it in any method body. This is dead code that also creates an unnecessary layering dependency.

### 9. [HIGH] Missing model parameter in fallback adapter call

- **File**: `relayos/core/conversation.py` (line 72)
- **Category**: bug
- **Detail**: ConversationEngine.chat() runs adapter.chat(message) at line 76 without a model parameter when creating a temporary adapter for an unknown worker, while the route call above determined a model.

### 10. [HIGH] Agent name used as provider key in config lookup

- **File**: `relayos\workflow\engine.py`
- **Category**: bug
- **Detail**: Lines 59-60: `provider_cfg = self.config.providers.get(step.agent, {})` and `get_adapter(step.agent, ...)` use `step.agent` (e.g., 'researcher', 'coder') as the provider key. The config's `providers` dict is keyed by actual provider names ('openai', 'anthropic'). Agent names will not match, so `provider_cfg` is always empty and `get_adapter` raises ValueError for any non-provider agent name.
- **Fix**: Map agent names to provider names through a worker-to-provider lookup or a config-level agent mapping. Either use the WorkflowStep's model/provider field directly, or add a workflow-level mapping from agent names to provider names.

### 11. [HIGH] Hardcoded DB path in remove method bypasses StateStore config

- **File**: `relayos\core\worker.py`
- **Category**: bug
- **Detail**: Lines 162-166: `remove()` opens `sqlite3.connect` directly on `~\.relayos\state.db` instead of using the StateStore's own connection. This path is hardcoded and will silently diverge if `StateStore` is ever initialized with a different `db_path` parameter. The worker record won't be deleted from the actual database.
- **Fix**: Add a `delete_worker` method to `StateStore` and call it from `WorkerManager.remove()`. The inline SQL path is fragile and duplicates persistence logic.

### 12. [HIGH] Worker status stuck in 'error' after exception

- **File**: `relayos\core\worker.py`
- **Category**: bug
- **Detail**: Line 200-201: In `WorkerManager.run()`, when an exception occurs, `w.status = "error"` is set and the exception is re-raised. The caller catches the exception, but `w.status` is never reset back to 'idle'. Once a worker hits an error, it is permanently stuck in 'error' state for the lifetime of the WorkerManager instance, even though the worker may be functional again.
- **Fix**: Reset status to 'idle' in a finally block: `finally: w.status = "idle"`, or at minimum catch and reset before the raise: `w.status = "idle"; raise`.

### 13. [HIGH] SQL INSERT mixes hardcoded values with parameter placeholders

- **File**: `relayos\core\session.py`
- **Category**: bug
- **Detail**: Line 169-170: The INSERT statement contains hardcoded `''`, `''`, `3`, `4` for `last_worker`, `last_model`, `max_parallel`, `max_models` mixed between parameter placeholders (`?`). This is fragile: if the column list is ever reordered (e.g., a migration adds a column before `last_worker`), the hardcoded values silently map to the wrong columns. The `max_parallel` and `max_models` values cannot be configured per-session since they are hardcoded.
- **Fix**: Use parameter placeholders for ALL columns. Pass `last_worker='', last_model='', max_parallel=3, max_models=4` as actual parameters: `INSERT INTO sessions (...) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)` with all values passed as `(sid, name, mode, parts, project_id, profile, '', '', last_capability, last_strategy, 3, 4, now, now)` or normalize the SQL pattern.

### 14. [HIGH] Model env vars removed instead of set in _build_env

- **File**: `relayos/terminals/base.py` (line 151)
- **Category**: bug
- **Detail**: The _build_env method at line 156-157 pops CLAUDE_MODEL, OPENAI_MODEL, ANTHROPIC_MODEL, and MODEL from the subprocess environment rather than setting them to instance.model. This means the only way a model override takes effect is through command-line flags in build_command(), but many terminal adapters do not support --model flags.

### 15. [HIGH] Quality profile shortcut 'q' is dead code because quit fires first

- **File**: `relayos/tui/app.py` (line 40)
- **Category**: bug
- **Detail**: Key 'q' on line 36 binds to `running = False` (quit). Line 40 checks `elif key == 'q_'` which can never match because getch() returns a single character. The key binding table in the footer (line 200) advertises 'q=quality', but pressing 'q' quits instead. Users cannot switch to quality mode from the TUI.

### 16. [HIGH] Duplicate config initialization: `init` and `config init` behave differently

- **File**: `relayos/cli/main.py` (line 198)
- **Category**: bug
- **Detail**: Line 198 defines a top-level `init` command that creates a hardcoded default config. config_commands.py defines `config init` which does auto-detection. `relayos init` and `relayos config init` do different things for the same purpose. The top-level `init` is dead code since `config init` is richer.

### 17. [HIGH] shlex.split on Windows mangles paths with backslashes

- **File**: `relayos/terminals/adapters.py` (line 238)
- **Category**: bug
- **Detail**: Line 238 uses shlex.split() which treats backslashes as escape characters (POSIX rule). On Windows, binary paths like 'C:\Users\...' or 'C:\Program Files\...' are mangled. The custom terminal command template breaks on any Windows path containing backslashes.

### 18. [HIGH] Windows getch decodes OEM code page bytes as UTF-8

- **File**: `relayos/tui/app.py` (line 92)
- **Category**: bug
- **Detail**: Line 92 calls msvcrt.getch().decode(errors='ignore'). On Windows, msvcrt.getch() returns bytes in the active OEM code page (e.g., cp437, cp936), not UTF-8. Decoding as UTF-8 produces mojibake or silently drops characters. The same pattern in focus.py line 58 has the same bug.

### 19. [HIGH] Error messages printed to stdout instead of stderr

- **File**: `relayos/cli/main.py` (line 617)
- **Category**: bug
- **Detail**: Several error messages omit err=True, sending diagnostics to stdout instead of stderr. The `use` command line 617, `recall` line 177-181, and `profile` line 953 all print [ERR] messages or file-not-found to stdout. This breaks stderr-based log filtering and pipeline separation.

### 20. [HIGH] 16 of 21 terminal types missing from scheduler capability scores

- **File**: `relayos/terminals/adapters.py` (line 10)
- **Category**: bug
- **Detail**: Terminal scheduler (scheduler.py TERMINAL_CAPABILITIES) only defines routing scores for 5 types: claude, opencode, mimo, codex, qcode. The other 16 adapters (pi, cursor, openclaw, continue, copilot, huggingface, gemini, aider, interpreter, fabric, sgpt, chatgpt, llm, kimi, copilot-ext, custom) have zero scores and fall back to '5' (average), making routing decisions meaningless for them.

### 21. [HIGH] MCPClient.start() spawns real subprocess -- no process abstraction for testing

- **File**: `relayos/mcp/client.py` (line 34)
- **Category**: test
- **Detail**: The start() method at line 34 calls subprocess.Popen with the server command, stdin/stdout pipes, and environment variables. send_request() at line 50 does blocking I/O with selectors. kill() on timeout. call_tool() and list_tools() call send_request(). There is no abstraction layer for the subprocess lifecycle. Testing requires either (a) a real MCP server binary, (b) a mock subprocess.Popen, or (c) extracting the transport layer behind an interface.
- **Fix**: Extract transport behind an MCPTransport Protocol with StdioTransport (real) and MockTransport (test). MCPClient should accept a transport instance via constructor. The MockTransport would simulate JSON-RPC responses without spawning processes. Write tests for protocol parsing, error handling, and timeouts using MockTransport.

### 22. [HIGH] PluginManager constructor has filesystem I/O and import side effects -- plus module-level global singleton

- **File**: `relayos/core/plugin.py` (line 65)
- **Category**: test
- **Detail**: Constructor at line 65 calls _discover_entry_points() (uses importlib.metadata to scan installed packages) and _discover_local() (reads ~/.relayos/plugins/*.py from disk). There is a module-level _manager singleton at line 183 with get_plugin_manager() at line 186 using the None-or-create pattern. __init__ cannot be tested without real installed packages and a real plugins directory. The singleton makes test isolation impossible without manual reset.
- **Fix**: Split plugin discovery from construction. Make discovery optional or explicit via a discover() method. Remove the module-level singleton or add a reset() method for testing. Accept entry_points and plugin_dir as injectable parameters with defaults. Write tests with controlled empty directories and mocked importlib.

### 23. [HIGH] TaskGraphExecutor has inline imports and makes real API calls -- no test seam

- **File**: `relayos/core/planner.py` (line 242)
- **Category**: test
- **Detail**: Constructor at line 242 inlines imports from relayos.adapters, relayos.config, relayos.core.artifacts, and relayos.core.schemas inside the method body (not at module level). The execute() method at line 254 calls self._get_adapter(provider, ...) which creates real LLM API connections. There is no interface for adapter calls. The resume() method at line 320 queries the real ArtifactStore to find completed steps.
- **Fix**: Move imports to module level. Make adapter factory injectable via constructor. Extract LLM execution behind a Callable Protocol. ArtifactStore should also be injectable. Write tests for the planning logic (pure, in ExecutionPlanner) separately from execution (requires mocking).

### 24. [HIGH] FlowRouter constructor reads YAML from filesystem as a side effect

- **File**: `relayos/core/router.py` (line 85)
- **Category**: test
- **Detail**: Constructor at line 83 accepts an optional rules_path. If provided, it uses pathlib.Path.exists() and Path.read_text() to load a YAML file from disk, then calls yaml.safe_load() on the contents. This file I/O happens during __init__ with no error handling other than silently skipping if the file doesn't exist. Testing with a real file path requires filesystem setup; testing without a path uses only defaults.
- **Fix**: Accept rules as an optional dict parameter instead of (or in addition to) a file path. If a path is given, defer file reading to a classmethod (FlowRouter.from_file(path)) or explicit load_rules() method. This keeps the constructor pure and testable.

### 25. [HIGH] MemoryStore shares the same untestable SQLite pattern with all 8 store classes

- **File**: `relayos/memory/store.py` (line 19)
- **Category**: test
- **Detail**: Uses hardcoded '~/.relayos/memory.db' path, creates tables in __init__, uses threading.local() for connections. The same pattern is repeated 8 times across StateStore, CostManager, MemoryStore, SessionStore, ArtifactStore, ProjectStore, IdentityStore, and WorkerInbox. Each stores its data in a separate .db file. None accepts a database connection or engine via constructor. None can use :memory: SQLite databases without modifying filesystem locations.
- **Fix**: Refactor to a shared base class or mixin that accepts a connection/engine. For tests, pass sqlite3.connect(':memory:') or a mock. Each subclass only defines its schema and table names. Alternatively, use a single database with table prefixes instead of 8 separate files.

### 26. [HIGH] SessionStore._init_db() has inline migration code using try/except ALTER TABLE

- **File**: `relayos/core/session.py` (line 126)
- **Category**: test
- **Detail**: Lines 126-155 contain 5 try/except blocks attempting ALTER TABLE ADD COLUMN statements. These are migrations, not idempotent schema definitions. They run every time SessionStore is instantiated. If a column already exists, the OperationalError is silently swallowed. This pattern means the store's constructor always has side effects, making it impossible to construct without a writable database.
- **Fix**: Move schema migrations out of the data access class into a separate migration module or Alembic-style version table. Track applied migrations explicitly. Keep _init_db() for the base CREATE TABLE IF NOT EXISTS only. For tests, use :memory: databases with known schemas.

### 27. [HIGH] Missing package-data for server static assets

- **File**: `pyproject.toml`
- **Category**: missing
- **Detail**: The `relayos/server/static/` directory contains 6 files (index.html, style.css, trace.css, trace.html, workers.css, workers.html) that are served by the FastAPI dashboard. These are not included in the wheel distribution because pyproject.toml has no `[tool.setuptools.package-data]` section and there is no MANIFEST.in. Installing from PyPI will leave the `relayos serve` command with missing templates.
- **Fix**: Add `[tool.setuptools.package-data]` section: `relayos = ["server/static/*", "py.typed"]` or create a MANIFEST.in with `recursive-include relayos/server/static *` and `include relayos/py.typed`

### 28. [HIGH] Architecture doc is outdated (claims v0.3 but code is at v0.9)

- **File**: `docs/architecture.md`
- **Category**: docs
- **Detail**: The architecture doc header says `Current (v0.3 -- Workforce)` and shows an architecture diagram that doesn't include the Model Scheduler, Capability Graph, TaskGraphExecutor, Session System, or Cross-Session Memory systems that have been implemented through v0.9. The storage layout shown (memory.db, workers.db, inbox.db, cost.db) doesn't match the actual ~/.relayos/ files (state.db, sessions.db, knowledge.db, artifacts.db, workers.db). Users and contributors get a misleading picture of the system.
- **Fix**: Update architecture.md to reflect v0.9 architecture: add ModelScheduler, CapabilityGraph, TaskGraphExecutor, ConversationEngine, KnowledgeBase/ProjectStore layers. Update the storage file list to match actual DBs.

### 29. [HIGH] Roadmap doc is outdated (still says v0.3 is current)

- **File**: `docs/roadmap.md`
- **Category**: docs
- **Detail**: The roadmap says `v0.3 -- Workforce (Current)` with in-progress items like 'Worker persistence' and 'Prompt Cache'. All features through v0.9 are already implemented and shipped per the CHANGELOG. The roadmap doesn't account for v0.4-v0.9 and has no future planning beyond v1.0.
- **Fix**: Update roadmap to mark v0.3 through v0.9 as completed. Either remove completed in-progress items or add accurate future plans beyond the current release.

### 30. [CRITICAL] Duplicate TERMINAL_CAPABILITIES with conflicting values

- **File**: `relayos/core/capabilities.py` (line 88)
- **Category**: bug
- **Detail**: TERMINAL_CAPABILITIES defined in two places with different structures and score values. core/capabilities.py uses 5 terminals (opencode, mimo, claude) while terminals/scheduler.py uses 5 different terminals (no mimo, includes codex/qcode). Claude coding scores differ: 9 vs 8.

### 31. [CRITICAL] Missing PRAGMA journal_mode=WAL on 6 out of 7 SQLite store classes

- **File**: `relayos/core/session.py` (line 84)
- **Category**: bug
- **Detail**: SessionStore, ArtifactStore, ProjectStore, IdentityStore, WorkerInbox, and MemoryStore all use thread-local connections but do NOT set PRAGMA journal_mode=WAL. Only StateStore sets WAL mode. Without WAL, concurrent reads block writers across threads.

### 32. [CRITICAL] group_chat passes worker name as provider to get_adapter

- **File**: `relayos\core\conversation.py`
- **Category**: bug
- **Detail**: Line 192 calls `get_adapter(worker_name, ...)` where `worker_name` is a role like 'researcher', 'architect', or 'coder'. The adapter registry only knows provider names ('openai', 'anthropic', 'google', 'deepseek', 'ollama' -- see `relayos/adapters/__init__.py`). Any worker name that is not a provider name will raise `ValueError` at runtime, breaking the entire group chat workflow.
- **Fix**: Map each worker name to its provider before calling get_adapter. Use the WorkerManager to look up the worker's assigned provider, then call get_adapter with that provider name. For example: `w = self.workers.get(worker_name); provider = w.provider if w else worker_name; adapter = get_adapter(provider, ...)`.

### 33. [CRITICAL] response.usage accessed without None guard in log line

- **File**: `relayos\workflow\engine.py`
- **Category**: bug
- **Detail**: Line 120: `logger.info(f"  [OK] {response.model} ({response.usage.get('output_tokens', 0)} tokens)")` calls `.get()` directly on `response.usage` without guarding for `None`. If the adapter returns a response with `usage=None`, this crashes with `AttributeError: 'NoneType' object has no attribute 'get'`. The cost tracking block (lines 98-104) correctly guards with `response.usage or {}`, but the log line does not.
- **Fix**: Change line 120 to `usage = response.usage or {}; logger.info(f"  [OK] {response.model} ({usage.get('output_tokens', 0)} tokens)")` or use `(response.usage or {}).get('output_tokens', 0)`.

### 34. [CRITICAL] Terminal run method crashes when result.content is None

- **File**: `relayos\orchestrator\pool.py`
- **Category**: bug
- **Detail**: Line 188: `inst.total_tokens += len(result.content) // 4` assumes `result.content` is a string. If `result.content` is `None`, `len(None)` raises `TypeError`. The `TerminalResult` dataclass declares `content` as `str` (in `relayos/terminals/base.py`), but error-path returns like lines 170-172 return `TerminalResult(content="", ...)` -- which is fine -- but an adapter returning `None` content would crash here.
- **Fix**: Add a None guard: `tokens = len(result.content or "") // 4; inst.total_tokens += tokens`.

### 35. [CRITICAL] Subprocess orphaned on timeout: run() does not kill the child process

- **File**: `relayos/terminals/base.py` (line 114)
- **Category**: bug
- **Detail**: When subprocess.run() raises TimeoutExpired, the child process continues running in the background. The code catches the exception but never calls process.terminate() or process.kill(). This leaks orphaned subprocesses that accumulate over time, especially with long-running AI CLI tools.

### 36. [CRITICAL] Run command always reports [OK] even when steps have errors

- **File**: `relayos/cli/main.py` (line 106)
- **Category**: bug
- **Detail**: Line 106 prints '[OK] Workflow completed' unconditionally. The WorkflowDisplay may show errors during execution, but the final CLI message always reports success. The results list does not indicate step failures in the final count message.

### 37. [CRITICAL] Zero test files exist in the entire project

- **File**: `tests/__init__.py` (line 1)
- **Category**: missing
- **Detail**: The tests/ directory contains only an empty __init__.py with a single comment. There are zero test files (.py), zero conftest.py files, zero pytest configuration files, no .coveragerc, no tox.ini, and no test-related sections in pyproject.toml. The project does not have pytest installed as a dependency. A ~4072-line codebase across 22 key modules has no tests whatsoever.
- **Fix**: Create a test plan covering all modules. Start with unit tests for pure-function modules (capabilities.py, schemas.py, compress.py, team.py) which require no mocking. Add pytest to project dependencies. Create conftest.py with fixtures for SQLite :memory: databases. Add coverage configuration.

### 38. [CRITICAL] StateStore has no database abstraction -- all SQLite stores use hardcoded filesystem paths with side-effect constructors

- **File**: `relayos/core/state.py` (line 34)
- **Category**: test
- **Detail**: Every store class (StateStore, CostManager, MemoryStore, SessionStore, ArtifactStore, ProjectStore, IdentityStore, WorkerInbox) follows the identical anti-pattern: (1) hardcoded default path like '~/.relayos/state.db', (2) constructor calls _init_db() which creates tables on disk as a side effect, (3) uses threading.local() for connection caching, (4) no abstraction layer or interface between business logic and SQLite. There are 8 such store classes, each with its own .db file. This makes unit testing impossible without real filesystem I/O and creates test pollution between parallel test runs.
- **Fix**: Add a DatabaseBackend abstract class/Protocol. Make all store classes accept it via constructor injection. Provide a SqliteBackend (real) and MemoryBackend (using sqlite3 :memory: or a dict-based mock). Remove table creation from __init__ -- use explicit migrate() or ensure_tables() methods. Use temporary files or in-memory databases in tests via conftest fixtures.

### 39. [CRITICAL] WorkerManager.__init__ has massive side effects: creates database, loads config, loads workers, creates default workers

- **File**: `relayos/core/worker.py` (line 113)
- **Category**: test
- **Detail**: Constructor at line 113-119 creates StateStore(), StateCompiler(), calls load_config(), then immediately calls _load_from_store() which queries the database and auto-creates 8 default workers if the database is empty. The run() method at line 169 calls get_adapter() for real LLM API calls with no mocking seam. The remove() method at line 161 opens a raw SQLite connection bypassing StateStore entirely. No dependency injection for any of these dependencies.
- **Fix**: Make StateStore, StateCompiler, and config injectable via constructor. Split initialization from construction: remove _load_from_store() from __init__, make it an explicit load() or init() method. Extract adapter creation behind a strategy/interface so tests can inject a mock adapter. Replace inline SQLite in remove() with a StateStore method.

### 40. [CRITICAL] ConversationEngine creates a 6-object dependency graph internally with zero injection points

- **File**: `relayos/core/conversation.py` (line 31)
- **Category**: test
- **Detail**: Constructor at line 31-37 instantiates SessionStore, StateStore, WorkerManager, ModelScheduler, ExecutionPlanner, and calls load_config() -- all internally with no parameters. The chat() method at line 41 orchestrates sessions, routing, adapter calls, and message storage. The ask() method at line 108 decomposes tasks and makes real API calls through adapters. There is no way to test any behavior without hitting real databases and real LLM APIs. This is the highest-value module for testing but the hardest to test.
- **Fix**: Make all six dependencies injectable via constructor with typed Protocol interfaces. Extract adapter call logic into a mockable interface. Break ConversationEngine into smaller, testable units: a ChatOrchestrator (routing logic, testable with mocks), a MessageRouter (pure logic), and keep ConversationEngine as a thin facade that wires injected dependencies together.

### 41. [CRITICAL] Rich library missing from dependencies

- **File**: `pyproject.toml`
- **Category**: bug
- **Detail**: The `relay` entry point (`relayos.tui.app:main`) imports from `rich` (Layout, Live, Panel, Table, Text), and `relayos/tui/focus.py` also imports rich. However, `rich` is not listed in `pyproject.toml` dependencies. A fresh `pip install relayos` will succeed but crash at runtime with `ModuleNotFoundError: No module named 'rich'` when trying to use the `relay` command, which is the primary advertised interface.
- **Fix**: Add `rich>=13.0` to the `dependencies` list in pyproject.toml, e.g.: `"rich>=13.0"`

### 42. [CRITICAL] Dockerfile build order breaks pip install

- **File**: `Dockerfile`
- **Category**: bug
- **Detail**: The Dockerfile copies pyproject.toml first (line 6), then runs `pip install -e .[server]` (line 7), and only then copies `relayos/` (line 10). The editable install requires the package directory to exist. This build will fail with `ERROR: file does not exist` because setuptools cannot find the `relayos` package at install time.
- **Fix**: Reverse the order: COPY relayos/ before running pip install. Or use a non-editable install (`pip install .[server]`) after copying both pyproject.toml and relayos/.

## MEDIUM Findings

### 1. [MEDIUM] Model cost data duplicated across capabilities.py and provider_registry.py
- **File**: `relayos/core/capabilities.py` (line 95)
- **Category**: style
- **Detail**: MODEL_COST_TIER in capabilities.py duplicates cost information already present in provider_registry.py ModelInfo cost_per_1k fields. Two different sources of truth for pricing data.

### 2. [MEDIUM] Provider default model mapping duplicated
- **File**: `relayos/core/capabilities.py` (line 104)
- **Category**: architecture
- **Detail**: PROVIDER_DEFAULT_MODEL dict in capabilities.py duplicates the default_model field already defined on each ProviderInfo in provider_registry.py. Two sources of truth for the same mapping.

### 3. [MEDIUM] Redundant local import json in TaskGraphExecutor.execute
- **File**: `relayos/core/planner.py` (line 273)
- **Category**: bug
- **Detail**: Two separate local 'import json' statements in the same method, one at line 273 and another at line 295 with a renamed alias 'import json as _j'. The first is never used because the function re-imports it.

### 4. [MEDIUM] _build_env removes model env vars without setting the correct one
- **File**: `relayos/terminals/base.py` (line 153)
- **Category**: style
- **Detail**: BaseTerminal._build_env() removes all model-related env vars (CLAUDE_MODEL, etc.) but never sets the appropriate env var to match instance.model. Terminal subprocesses lose the model selection context.

### 5. [MEDIUM] WorkerManager.remove bypasses StateStore with raw SQLite
- **File**: `relayos/core/worker.py` (line 162)
- **Category**: style
- **Detail**: WorkerManager.remove() imports sqlite3 locally and creates a direct connection to state.db, bypassing the StateStore abstraction entirely.

### 6. [MEDIUM] Extensive hardcoded configuration values throughout core modules
- **File**: `relayos/core/scheduler.py` (line 27)
- **Category**: style
- **Detail**: CONFIDENCE_THRESHOLD = 0.6 hardcoded at module level. CAPABILITY_SCORES, TASK_PATTERNS, DEFAULT_RULES all hardcoded. Many integer defaults (max_parallel=3, budget_chars=4800, etc.) hardcoded in function signatures.

### 7. [MEDIUM] Overlapping routing logic between FlowRouter and ModelScheduler
- **File**: `relayos/core/router.py` (line 76)
- **Category**: architecture
- **Detail**: FlowRouter (core/router.py) and ModelScheduler (core/scheduler.py) both do keyword-based task classification with similar pattern dictionaries. Two separate routing systems with overlapping responsibility.

### 8. [MEDIUM] No abstract interface for SQLite store classes
- **File**: `relayos/core/state.py` (line 31)
- **Category**: dx
- **Detail**: No abstract base class or protocol for store classes (StateStore, SessionStore, ArtifactStore, etc.). Each implements its own slightly different interface for similar operations (get/put/query semantics).

### 9. [MEDIUM] Dual routing: ModelScheduler and terminals.scheduler both make routing decisions
- **File**: `relayos/core/planner.py` (line 130)
- **Category**: architecture
- **Detail**: ExecutionPlanner delegates to ModelScheduler for model routing AND to best_terminal() from terminals/scheduler for terminal routing. Two separate routing decisions for a single planning step create coordination complexity.

### 10. [MEDIUM] Missing worker could reference stale route from earlier fallback
- **File**: `relayos\core\conversation.py`
- **Category**: bug
- **Detail**: Lines 68-83: If `self.workers.get(target)` returns None (worker not found), a fallback route and adapter call is made. But the second `self.scheduler.route(message, profile=session.profile)` call on line 70 does not pass a `task_type`. This means the route may select a different model than originally intended for the task type, potentially routing a coding task to a research-optimized model. The first route (line 64) correctly passed the capability.
- **Fix**: Pass the already-computed `capability` to the fallback route call: `route = self.scheduler.route(message, capability, profile=session.profile)` instead of dropping the task type.

### 11. [MEDIUM] Thread-local SQLite connections leak resources
- **File**: `relayos\core\session.py`
- **Category**: architecture
- **Detail**: The `_conn` property (lines 83-88) creates thread-local connections that are never explicitly closed. In a long-running application with many threads, each thread accumulates one connection per SessionStore instance, and they are only cleaned up when the thread dies. The `_init_db` method (lines 90-123) meanwhile opens and closes its own short-lived connections, creating up to 6 separate connections during initialization alone.
- **Fix**: Call `self._local.conn.close()` after each transaction, or use a connection pool with context managers. Alternatively, move `_conn` from a property to explicit `with sqlite3.connect(...)` blocks for each operation, matching the pattern used in `_init_db`.

### 12. [MEDIUM] Inline __import__() call bypasses proper module imports
- **File**: `relayos\orchestrator\pool.py`
- **Category**: style
- **Detail**: Line 185: `__import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()` is used instead of the already-imported `from datetime import datetime, timezone` at line 9. This is not only poor style but also 2x slower due to redundant dynamic imports. The same mistake appears on line 168.
- **Fix**: Replace with `datetime.now(timezone.utc).isoformat()` since `datetime` and `timezone` are already imported at line 9.

### 13. [MEDIUM] Duplicate logger assignment
- **File**: `relayos\core\worker.py`
- **Category**: style
- **Detail**: Lines 31 and 33: `logger = logging.getLogger(__name__)` is assigned twice. Line 31's assignment is immediately overwritten by line 33's. This does not change behavior (same logger name) but is dead code.
- **Fix**: Remove line 31's `logger = logging.getLogger(__name__)` -- the second assignment at line 33 is sufficient.

### 14. [MEDIUM] select_provider returns provider without checking availability
- **File**: `relayos\core\cost.py`
- **Category**: bug
- **Detail**: Lines 115-125: `select_provider` always returns the first element of the policy ordering list (e.g., always `'ollama'` for `free_first` policy). It never verifies whether that provider is actually configured or has an API key. If the returned provider is not available, the subsequent adapter call will fail. The function should filter providers by availability before returning.
- **Fix**: Accept an optional `available_providers` parameter (list of configured provider names) and iterate the policy order to find the first one that is available. If none are available, fall back to 'openai' or return None.

### 15. [MEDIUM] Redundant null check after dict.get() with default
- **File**: `relayos\core\session.py`
- **Category**: dx
- **Detail**: Lines 178-179 in `_init_db`: each ALTER TABLE is wrapped in a `try/except sqlite3.OperationalError` block that opens a new `sqlite3.connect()` connection. This creates 5 separate connections during migration when 1 would suffice. More importantly, it swallows ALL `OperationalError` exceptions, not just the 'duplicate column' error. A real SQL error during migration would be silently ignored.
- **Fix**: Run all ALTER TABLE statements inside a single connection, and consider using `PRAGMA table_info(sessions)` to check for column existence before attempting ALTER, rather than relying on exception handling for flow control.

### 16. [MEDIUM] Potential json.dumps of already-serialized values
- **File**: `relayos\core\knowledge.py`
- **Category**: bug
- **Detail**: Line 254: `json.dumps(value, ensure_ascii=False) if not isinstance(value, str) else value` -- but the value comes from `content.get(field)` where `content` was originally stored as `json.dumps(content)` in the ArtifactStore. When retrieved, `json.loads(d["content"])` is called (in `artifacts.py`), which correctly deserializes nested dicts/lists. However, if a field value itself is a JSON-encoded string (e.g., a double-serialized value), it gets stored as a plain string. The `isinstance(value, str)` check would pass and the raw string is stored, which is correct behavior. Not a crash but could lead to confusing nested-encoding in the knowledge DB.
- **Fix**: No action required for correctness -- the code handles this correctly. But document that knowledge values should not be pre-encoded JSON strings to avoid double-encoding.

### 17. [MEDIUM] Dead code after TASK_PATTERNS.get with default
- **File**: `relayos\core\planner.py`
- **Category**: bug
- **Detail**: Line 120: `pattern = TASK_PATTERNS.get(task_type, TASK_PATTERNS["coding"])` already returns `TASK_PATTERNS["coding"]` as the default for unknown task types. Lines 121-122: `if not pattern: pattern = TASK_PATTERNS["coding"]` is dead code -- `pattern` is always truthy because `get()` with a default never returns None and `TASK_PATTERNS["coding"]` is always a non-empty list.
- **Fix**: Remove lines 121-122 and 184-185: both are unreachable conditions. Simplify to `pattern = TASK_PATTERNS.get(task_type, TASK_PATTERNS["coding"])` alone.

### 18. [MEDIUM] Escalation chain semantics are inverted
- **File**: `relayos\core\scheduler.py`
- **Category**: bug
- **Detail**: Line 38: `escalation_chain: list[str]` is documented as 'models tried before this one'. But lines 143-147 build the chain as `[model]` (the selected model, which was NOT tried before selection), and optionally `[model, next_best]` when confidence is low. This does not represent models tried 'before' the current one; it represents 'the current model plus optionally a fallback'. The semantics are misleading and could confuse callers who read the field name.
- **Fix**: Either rename the field to `candidate_chain` or `fallback_chain` to reflect its actual content, or change the logic to track only model names that were attempted before settling on the current choice.

### 19. [MEDIUM] Token estimation assumes 4 chars/token inaccurate for CJK text or code
- **File**: `relayos/terminals/base.py` (line 104)
- **Category**: performance
- **Detail**: Line 104 calculates `instance.total_tokens += len(content) // 4`. For Chinese/Japanese/Korean text (1-2 chars/token) this underestimates by 2-4x. For code it is roughly correct but not accurate enough for cost tracking. This feeds the `terminal stats` display.

### 20. [MEDIUM] TUI update interval is 1.5s but refresh_per_second claims 4 Hz
- **File**: `relayos/tui/app.py` (line 52)
- **Category**: performance
- **Detail**: Line 52 sets Live(refresh_per_second=4) but the main loop sleeps 1.5s (line 58), yielding ~0.67 Hz. The unnecessary live.refresh() call on line 57 adds no value since update() handles rendering. The stale refresh rate variable misleads maintainers.

### 21. [MEDIUM] session use returns instead of sys.exit(1) on not-found
- **File**: `relayos/cli/main.py` (line 807)
- **Category**: bug
- **Detail**: Line 807 uses bare `return` when a session is not found. Other not-found handlers (recall line 180, terminal remove line 359) use sys.exit(1). Session command pipelines may silently continue with a zero exit code on error.

### 22. [MEDIUM] agents command uses fragile getattr with silent fallback on failure
- **File**: `relayos/cli/main.py` (line 147)
- **Category**: dx
- **Detail**: Lines 147-149 attempt `getattr(inst, 'default_model', '-')` but some adapters use default_model as a class attribute. The bare except Exception on line 154 silently sets all fields to '?' on any failure, hiding the real problem.

### 23. [MEDIUM] QCodeTerminal has no model override support
- **File**: `relayos/terminals/adapters.py` (line 66)
- **Category**: bug
- **Detail**: The QCode terminal adapter (line 61-67) builds a static command without any --model argument. If the user changes instance.model, it is silently ignored. This produces unexpected behavior when users believe they have configured a model override.

### 24. [MEDIUM] API keys passed through adapter options dict could leak in logs
- **File**: `relayos/cli/main.py` (line 119)
- **Category**: security
- **Detail**: Line 119-123 constructs an options dict containing 'api_key' and passes it to get_adapter(). If the adapter constructor or any downstream code logs its config argument, the full API key appears in logs. The key also lives in the adapter object's config dict for its lifetime.

### 25. [MEDIUM] use command hardcodes a subset of terminal types
- **File**: `relayos/cli/main.py` (line 597)
- **Category**: bug
- **Detail**: Line 597 hardcodes valid_terminals = ("opencode", "mimo", "claude", "codex", "qcode"). The 16 other terminal types (pi, cursor, openclaw, etc.) cannot be selected via `relay use`. Users who add custom terminals get "Unknown terminal/profile" even for valid types.

### 26. [MEDIUM] Default 300s subprocess timeout too low for complex AI prompts
- **File**: `relayos/terminals/base.py` (line 81)
- **Category**: performance
- **Detail**: Line 81 sets timeout=300s. Free models (deepseek, local ollama) commonly exceed 5 minutes on complex prompts. The error message is simply 'Timeout exceeded' with no hint to increase the timeout.

### 27. [MEDIUM] chat command catches no exceptions raw traceback on invalid agent
- **File**: `relayos/cli/main.py` (line 119)
- **Category**: bug
- **Detail**: Line 119 calls get_adapter(agent_name, ...) with no try/except. If agent_name is invalid, the user gets a raw Python traceback instead of a user-friendly 'Agent not found' message with available options.

### 28. [MEDIUM] Interactive API key captured via click.prompt visible in process env
- **File**: `relayos/cli/config_commands.py` (line 201)
- **Category**: security
- **Detail**: Line 202 prompts for API key and stores it via os.environ. The environment variable is visible in /proc/PID/environ on Linux and child processes inherit it. No masking on input.

### 29. [MEDIUM] _set_profile silently swallows all exceptions including KeyboardInterrupt
- **File**: `relayos/tui/app.py` (line 74)
- **Category**: bug
- **Detail**: Line 74 uses bare `except: pass` which swallows all exceptions including KeyboardInterrupt and SystemExit. If the YAML write fails, the user gets zero feedback. The TUI silently continues without applying the profile switch.

### 30. [MEDIUM] StateStore.build_worker_context() has a complex budget-splitting algorithm with no tests
- **File**: `relayos/core/state.py` (line 252)
- **Category**: test
- **Detail**: Lines 252-314 contain a 62-line method that builds structured context for workers within a character budget. It composes identity, state, decisions, and task sections with character counting and truncation. This is pure logic (no I/O once data is fetched) and could be tested independently, but it is tightly coupled to self.get_worker(), self.get_all_state(), self.get_decisions(), and self.get_inbox() which all hit SQLite.
- **Fix**: Extract the budget-allocation algorithm into a pure function that operates on already-fetched dict data. Test the pure function with various budget sizes, edge cases (empty state, many decisions, long strings). Keep the SQLite fetching as a thin wrapper.

### 31. [MEDIUM] ContextCompressor has zero tests despite being a pure-function module perfectly suited for unit testing
- **File**: `relayos/core/compress.py` (line 37)
- **Category**: test
- **Detail**: All four compression strategies (_truncate, _extract, _summary, _structured) are pure string-manipulation functions with no external dependencies. The compress() method returns a CompressedContext dataclass with metrics. This module is trivially testable but has no tests -- a missed opportunity for easy coverage.
- **Fix**: Write tests for each strategy: _truncate with short/long/exact boundary content, _extract with various content patterns (headings, bullets, key phrases), _summary with intro/conclusion/key-point content, _structured with key-value pairs. Test edge cases: empty string, single character, non-ASCII, markdown, JSON content. Test the ratio calculation.

### 32. [MEDIUM] Capability registry functions are pure and zero-effort to test but have no tests
- **File**: `relayos/core/capabilities.py` (line 113)
- **Category**: test
- **Detail**: get_capability(), get_best_model(), get_cost_tier(), score_models() are all pure functions operating on module-level dict data. These are the easiest possible test targets -- no mocking, no I/O, no dependencies. Yet they have zero tests.
- **Fix**: Write tests: get_capability with known/unknown model, get_best_model for each capability type, get_cost_tier for each model, score_models with different capability/cost weights. Verify the scoring order matches expectations. Test edge cases like misspelled model names.

### 33. [MEDIUM] ExecutionPlanner.plan() uses global TASK_PATTERNS and calls ModelScheduler -- no DI
- **File**: `relayos/core/planner.py` (line 111)
- **Category**: test
- **Detail**: Constructor at line 111 creates ModelScheduler() internally. plan() at line 114 uses global TASK_PATTERNS dict and calls self.scheduler.classify_task() and self.scheduler.route(). While the dependencies are testable through mocking, the lack of DI means tests must either mock ModelScheduler globally or let it use real PROVIDERS and CAPABILITY_SCORES.
- **Fix**: Make ModelScheduler injectable via constructor. Extract TASK_PATTERNS to an injectable parameter (defaulting to the module-level dict). Write tests for plan() with a mock scheduler to verify decomposition patterns, step ordering, and dependency graph construction.

### 34. [MEDIUM] IdentityStore is a near-duplicate of StateStore with its own separate SQLite database
- **File**: `relayos/core/identity.py` (line 41)
- **Category**: test
- **Detail**: IdentityStore at line 41 has nearly identical structure to StateStore: same threading.local() pattern, same _init_db() with hardcoded tables, same decision/project_state operations. It stores data in ~/.relayos/identity.db while StateStore uses ~/.relayos/state.db with overlapping functionality (decisions table exists in both). This is database sprawl and duplicate code, making test coverage harder because two stores must be set up.
- **Fix**: Merge IdentityStore functionality into StateStore which already has decisions and state tables. Alternatively, have IdentityStore accept a shared database connection from StateStore. Remove the separate .db file and consolidate schemas.

### 35. [MEDIUM] No conftest.py exists -- no test fixtures, no pytest configuration of any kind
- **File**: `tests/__init__.py` (line 1)
- **Category**: dx
- **Detail**: The project has zero test infrastructure: no conftest.py (for shared fixtures), no pytest.ini/pyproject.toml test config, no .coveragerc, no tox.ini, no pytest plugins configured. pytest is not even installed or listed as a dev dependency. A developer wanting to add tests must bootstrap the entire test infrastructure from scratch.
- **Fix**: Create tests/conftest.py with: (1) fixture for in-memory SQLite StateStore, (2) fixture for mocked ModelScheduler, (3) fixture for mocked adapters, (4) fixture for temporary config directory. Add [tool.pytest.ini_options] and [tool.coverage.run] to pyproject.toml. Add pytest and pytest-cov to dev dependencies.

### 36. [MEDIUM] ModelScheduler.classify_task() uses hardcoded keyword dict but the algorithm is testable
- **File**: `relayos/core/scheduler.py` (line 53)
- **Category**: test
- **Detail**: classify_task() at line 53 uses a hardcoded type_patterns dict to keyword-match prompts to task types. The algorithm is a simple counting heuristic. While this is easy to test, it has no tests. The _model_to_provider() method uses hardcoded string matching (line 173-191) which is fragile and also untested.
- **Fix**: Write boundary tests for classify_task: empty string, keywords from multiple categories, no matching keywords, case sensitivity, substring matching. Write tests for _model_to_provider covering all known model prefixes and unknown models. Consider extracting _model_to_provider into a data-driven mapping table.

### 37. [MEDIUM] Outdated development plan document
- **File**: `docs/v0.2-plan.md`
- **Category**: docs
- **Detail**: The docs/v0.2-plan.md evaluates features like 'Docker: missing' and 'Cost Manager: missing' and lists them as P0/P1 priorities. These features have been implemented for multiple versions. This document appears to be a historic planning artifact that is now misleading.
- **Fix**: Either archive docs/v0.2-plan.md, mark it clearly as superseded, or delete it to avoid confusion.

### 38. [MEDIUM] Phantom optional dependency `mco>=0.9` with no code usage
- **File**: `pyproject.toml`
- **Category**: bug
- **Detail**: The `[project.optional-dependencies] executor` section specifies `mco>=0.9` (multi-agent execution backend), but `import mco` or `from mco` appears nowhere in the codebase. This means either the dependency is unused and should be removed, or it is consumed via subprocess (which should be documented).
- **Fix**: Remove `mco>=0.9` from optional-dependencies if unused, or document how it's consumed if used at runtime via subprocess.

### 39. [MEDIUM] Silent import failure for config/plugin commands
- **File**: `relayos/cli/main.py`
- **Category**: style
- **Detail**: Lines 993-998 wrap the import of config_commands.py in a try/except that silently drops the entire `config` and `plugin` command groups on ImportError. There is no warning to the user that configuration commands are unavailable. Since the pyproject.toml entry point `relayos = relayos.cli.main:cli` leads here, any missing dependency in config_commands.py would silently degrade the CLI.
- **Fix**: Add a warning message in the except block, e.g., `click.echo('[WARN] Config commands unavailable: install with relayos[server] or check dependencies', err=True)`

### 40. [MEDIUM] README claims 21 terminal types but most are unimplemented stubs
- **File**: `README.md`
- **Category**: dx
- **Detail**: The README prominently features a table of '21 terminal types' with checkmarks and empty squares. Of the 21 listed terminals, the codebase only has actual adapter implementations for 5 providers (OpenAI, Anthropic/Claude, Google, DeepSeek, Ollama). The remaining 16 are listed with gray squares, meaning they are detected CLI tools, not integrated adapters. This over-promises capability and may mislead users about what actually works.
- **Fix**: Either implement the missing terminal adapters, or clearly label which are adapter-integrated versus just CLI-detectable. The README should set accurate expectations about which models/terminals actually route through RelayOS.

## LOW Findings

### 1. [LOW] Inline __import__ instead of proper import statement
- **File**: `relayos/terminals/base.py`
- **Category**: style
- **Detail**: BaseTerminal._build_env uses `__import__('os').environ` instead of a proper top-level `import os`. This pattern makes imports harder to find and lint.

### 2. [LOW] Inline __import__ of datetime in TerminalPool.run
- **File**: `relayos/orchestrator/pool.py`
- **Category**: style
- **Detail**: TerminalPool.run uses `__import__('datetime')` inline instead of a proper import at module level.

### 3. [LOW] Broad exception handling may mask unexpected errors
- **File**: `relayos/core/conversation.py`
- **Category**: style
- **Detail**: Both conversation.chat() (line 80) and ask() (line 151) use bare `except Exception as e` which catches everything including KeyboardInterrupt via inheritance.

### 4. [LOW] ConversationEngine constructs 6 dependencies eagerly in __init__
- **File**: `relayos/core/conversation.py`
- **Category**: architecture
- **Detail**: ConversationEngine creates instances of SessionStore, StateStore, WorkerManager, ModelScheduler, ExecutionPlanner, and loads config in __init__. This is 6 heavyweight object instantiations that all happen on construction.

### 5. [LOW] Cheapest policy hardcodes deepseek as fallback
- **File**: `relayos\core\router.py`
- **Category**: bug
- **Detail**: Lines 125-129: When `policy == "cheapest"`, the code overrides the selected provider to `'deepseek'` if the current rank > 0. But 'deepseek' may not be the cheapest available provider -- 'ollama' would be cheaper, but 'ollama' is already excluded by the `provider != "ollama"` guard on line 123. The policy is essentially 'switch to deepseek unless already on ollama', not 'select the cheapest provider'.

### 6. [LOW] Redundant second import of shutil
- **File**: `relayos\core\plugin.py`
- **Category**: style
- **Detail**: Line 133: `import shutil` inside `install_local()` is redundant because `shutil` is already imported at line 19 at the module level.

### 7. [LOW] Missing project_id in list_sessions column list could cause KeyError
- **File**: `relayos\core\session.py`
- **Category**: bug
- **Detail**: Lines 199-203: `list_sessions()` returns `dict(r)` for all rows, but the calling code that constructs timed messages may access `row['project_id']` without a KeyError guard.

### 8. [LOW] Template variable {{var}} not replaced with empty string when context key is missing
- **File**: `relayos\core\compress.py`
- **Category**: style
- **Detail**: Template placeholder handling in TaskGraphExecutor (planner.py lines 277-287) handles missing upstream data by replacing placeholders with empty strings, but compression strategies in compress.py operate on raw content only with no such logic.

### 9. [LOW] Thread-unsafe access to spinner iterator and running flag
- **File**: `relayos/cli/display.py`
- **Category**: bug
- **Detail**: Line 51 creates itertools.cycle(SPINNER_CHARS) without threading lock. The _render method advances the spinner from the animation thread while main-thread callbacks acquire the lock. self._running on line 134 is read without the lock, creating a race condition on stop.

### 10. [LOW] ANSI escape codes incompatible with Windows CMD no VT100 fallback
- **File**: `relayos/cli/display.py`
- **Category**: bug
- **Detail**: Lines 136-149 use ANSI escape codes for cursor hide and clear. On Windows CMD without Virtual Terminal Processing enabled, these print visible garbage characters. No os.system('cls') or ctypes fallback for non-VT terminals.

### 11. [LOW] Unicode spinner characters render as question marks on legacy Windows
- **File**: `relayos/cli/display.py`
- **Category**: bug
- **Detail**: Line 17 defines braille-pattern spinner chars. On Windows consoles using raster fonts or legacy code pages (cp437), these render as '?' placeholders. No ASCII fallback spinner.

### 12. [LOW] Prompt passed as both CLI argument and stdin potential duplication
- **File**: `relayos/terminals/base.py`
- **Category**: style
- **Detail**: Line 76 passes prompt as stdin when the command string representation contains '{stdin}'. A template like '{binary} --prompt {prompt}' would have the prompt both as a CLI arg and piped to stdin. Many AI CLIs would process the prompt twice or error.

### 13. [LOW] ImportError for config_commands silently swallowed
- **File**: `relayos/cli/main.py`
- **Category**: style
- **Detail**: Lines 993-998 wrap config_commands import in try/except ImportError pass. If config_commands.py has a genuine syntax error or missing dependency, the error is hidden and no config/plugin commands are available.

### 14. [LOW] Tilde path ~/.relayos/memory.db never expanded via expanduser()
- **File**: `relayos/cli/main.py`
- **Category**: bug
- **Detail**: Lines 70, 162, 167, 186, 199, 410, 421, 429 pass literal '~/.relayos/...' strings to store constructors. Path('~') does not resolve to the home directory -- only expanduser() does. On Windows this produces invalid paths like '~\.relayos\memory.db'.

### 15. [LOW] StateStore uses LIKE-based search in search_decisions -- SQL injection risk from test/untrusted data
- **File**: `relayos/core/state.py`
- **Category**: bug
- **Detail**: Line 177-180 uses f-string pattern for LIKE query: f'%{query}%'. While this doesn't enable classic SQL injection (parameterized query handles the actual input), the LIKE pattern wrapping means the query string is interpolated. If a test passes a string containing '%' or '_', the search behavior changes unexpectedly. No tests validate this.

### 16. [LOW] Team templates are pure data -- the module needs tests for template validation
- **File**: `relayos/core/team.py`
- **Category**: test
- **Detail**: create_team() at line 84 validates template existence and handles WorkerManager calls. list_templates() at line 108 returns formatted template data. These are moderate testability (WorkerManager is a dependency) but have no tests. The default templates have inconsistent provider assignments (reviewer uses different providers across templates).

### 17. [LOW] Schema lookup functions are pure and trivially testable -- zero tests
- **File**: `relayos/core/schemas.py`
- **Category**: test
- **Detail**: get_schema(), get_consumed_fields(), get_input_sources() at lines 74-91 are pure dict-lookup functions operating on the STEP_SCHEMAS constant. They return empty defaults for unknown step types. The prompt_template fields contain hardcoded upstream field references that could drift from the actual 'consumes' lists -- but no tests validate consistency.

### 18. [LOW] German README has encoding issues in umlaut characters
- **File**: `README_DE.md`
- **Category**: docs
- **Detail**: The German README contains `offnest`, `Losung`, `fur`, `Prufung` which are rendered correctly, but the file uses HTML character codes in some places inconsistently (e.g., standard umlauts mixed with potential encoding sequences). The line count (411 vs 410 in EN) suggests minor content additions or line-wrapping differences.

### 19. [LOW] README `relay config detect` and `relayos config` dual-naming confusion
- **File**: `README.md`
- **Category**: dx
- **Detail**: The README commands table lists `relay config detect` and `relayos plugin add` as separate commands, but both are on the `relayos` CLI group (registered under `relayos`), not the `relay` TUI entry point. A user typing `relay config detect` gets an error because `relay` (TUI entry point) serves the Rich dashboard, not the Click CLI. The README implies `relay` is the primary command and shows it in all examples, but some commands only work as `relayos`.

### 20. [LOW] No user-facing warning when `relay` TUI entry point has no workable terminals
- **File**: `relayos/cli/main.py`
- **Category**: dx
- **Detail**: The TUI app (`relayos.tui.app:main`) renders the worker panel, but if no API keys are configured and no terminals are available, the panel shows all workers as idle with no clear error message about missing configuration. The `init` command creates a config but doesn't validate API key availability.

### 21. [LOW] Empty test directory with only a placeholder file
- **File**: `tests/__init__.py`
- **Category**: missing
- **Detail**: The tests/ directory contains only `__init__.py` with 21 bytes. No actual tests exist despite CONTRIBUTING.md stating 'New features should include pytest tests in tests/'. The CI pipeline (`python -m pytest tests/`) effectively runs nothing and always succeeds.

### 22. [LOW] Adapter __init__.py may not export all registered adapters
- **File**: `relayos/adapters/__init__.py`
- **Category**: missing
- **Detail**: pyproject.toml declares entry points for 5 adapters (openai, anthropic, google, ollama, deepseek) under `[project.entry-points."relayos.adapters"]`, but the code has no corresponding `importlib.metadata` loader to actually discover these entry points at runtime. The `list_adapters()` and `get_adapter()` functions in `relayos/adapters/__init__.py` need to use `importlib.metadata.entry_points()` to discover them.

### 23. [LOW] COLLAB.md contains project-specific team instructions
- **File**: `COLLAB.md`
- **Category**: dx
- **Detail**: The COLLAB.md file references specific team member tools (mimo, opencode) for code review tasks and includes a team structure table. This appears to be a personal collaboration document that would confuse external contributors. It also contains PyPI publishing instructions (`twine upload dist/*`) with token input instructions.

### 24. [LOW] No CODE_OF_CONDUCT.md or SECURITY.md for community contributors
- **File**: `README.md`
- **Category**: missing
- **Detail**: The project has CONTRIBUTING.md and COLLAB.md but is missing standard open-source community files: CODE_OF_CONDUCT.md (for contributor behavior guidelines) and SECURITY.md (for vulnerability reporting process). This may discourage community contributions.

### 25. [LOW] CONTRIBUTING.md has no code of conduct section
- **File**: `CONTRIBUTING.md`
- **Category**: docs
- **Detail**: The CONTRIBUTING.md states 'Be respectful, constructive, and inclusive' as the code of conduct, but provides no link to a CODE_OF_CONDUCT.md, no enforcement policy, and no reporting channel. This is insufficient for an Apache 2.0 licensed project that expects community contributions.
