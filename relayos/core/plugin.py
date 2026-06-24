"""Plugin System — extend RelayOS with custom terminals, adapters, and tools.

RelayOS plugins are Python packages that register via entry_points.
Any third-party AI terminal can be added as a plugin.

Usage:
    pip install relayos-plugin-foo
    # Plugin auto-registers via entry_points

Or manually:
    relayos plugin install ./my-terminal.py
"""
from __future__ import annotations

import importlib
import importlib.metadata
import inspect
import logging
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

logger = logging.getLogger(__name__)

# ── Plugin types ────────────────────────────────────────────

PLUGIN_TYPES = {
    "terminal",   # New CLI terminal type
    "adapter",    # New LLM provider adapter
    "tool",       # New MCP-like tool
    "hook",       # Lifecycle hook (pre_run, post_run)
}

ENTRY_POINT_GROUPS = {
    "terminal": "relayos.terminals",
    "adapter": "relayos.adapters",
    "tool": "relayos.tools",
    "hook": "relayos.hooks",
}


@dataclass
class PluginInfo:
    name: str
    version: str = "0.1.0"
    description: str = ""
    type: str = "terminal"
    author: str = ""
    entry_point: str = ""
    install_path: str = ""
    enabled: bool = True


class PluginManager:
    """Discovers, loads, and manages plugins.

    Plugins are discovered via:
    1. pip-installed packages with entry_points
    2. Local plugin files in ~/.relayos/plugins/
    3. Explicit registration
    """

    def __init__(self):
        self._plugins: dict[str, PluginInfo] = {}
        self._loaded: dict[str, Any] = {}
        self._discover_entry_points()
        self._discover_local()

    def _discover_entry_points(self):
        """Discover plugins from installed packages via entry_points."""
        for plugin_type, group in ENTRY_POINT_GROUPS.items():
            try:
                for ep in importlib.metadata.entry_points(group=group):
                    try:
                        cls = ep.load()
                        self._plugins[ep.name] = PluginInfo(
                            name=ep.name,
                            type=plugin_type,
                            entry_point=f"{group}:{ep.name}",
                            description=getattr(cls, "__doc__", "") or "",
                        )
                        self._loaded[ep.name] = cls
                    except Exception as e:
                        logger.debug(f"Failed to load plugin '{ep.name}': {e}")
            except Exception:
                pass

    def _discover_local(self):
        """Discover local plugins from ~/.relayos/plugins/ directory."""
        plugin_dir = Path.home() / ".relayos" / "plugins"
        if not plugin_dir.exists():
            return

        for f in plugin_dir.glob("*.py"):
            plugin_name = f.stem
            if plugin_name in self._plugins:
                continue  # entry_point takes precedence

            try:
                spec = importlib.util.spec_from_file_location(plugin_name, f)
                if spec and spec.loader:
                    mod = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(mod)
                    self._plugins[plugin_name] = PluginInfo(
                        name=plugin_name,
                        type="terminal",  # default type
                        install_path=str(f),
                    )
                    self._loaded[plugin_name] = mod
            except Exception as e:
                logger.warning(f"Failed to load local plugin '{plugin_name}': {e}")

    def list_plugins(self, plugin_type: Optional[str] = None) -> list[PluginInfo]:
        if plugin_type:
            return [p for p in self._plugins.values() if p.type == plugin_type]
        return list(self._plugins.values())

    def get(self, name: str) -> Optional[Any]:
        return self._loaded.get(name)

    def install_local(self, source_path: str) -> Optional[PluginInfo]:
        """Install a local plugin file."""
        src = Path(source_path)
        if not src.exists():
            logger.error(f"Plugin file not found: {source_path}")
            return None

        plugin_dir = Path.home() / ".relayos" / "plugins"
        plugin_dir.mkdir(parents=True, exist_ok=True)
        dst = plugin_dir / src.name
        import shutil
        shutil.copy2(src, dst)

        plugin_name = src.stem
        info = PluginInfo(
            name=plugin_name,
            type="terminal",
            install_path=str(dst),
        )
        self._plugins[plugin_name] = info
        logger.info(f"Installed plugin: {plugin_name}")
        return info

    def register_custom_terminal(self, name: str, binary: str, model: str = "",
                                   command_template: Optional[str] = None,
                                   type_name: str = "custom") -> None:
        """Register a custom terminal adapter at runtime.

        Args:
            name: Display name for the terminal
            binary: CLI binary path/name
            model: Default model
            command_template: How to build the command. Use {binary}, {prompt}, {model}
            type_name: Terminal type identifier
        """
        from relayos.terminals.adapters import CustomTerminal
        from relayos.terminals import register_terminal

        class DynamicTerminal(CustomTerminal):
            pass

        DynamicTerminal.type = type_name
        DynamicTerminal.binary = binary
        DynamicTerminal.default_model = model

        if command_template:
            DynamicTerminal._command_template = command_template

        register_terminal(type_name, DynamicTerminal)

        self._plugins[name] = PluginInfo(
            name=name,
            type="terminal",
            description=f"Custom terminal: {binary} ({type_name})",
        )

        logger.info(f"Registered custom terminal: {name} ({binary})")


# Module-level singleton
_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    global _manager
    if _manager is None:
        _manager = PluginManager()
    return _manager


def discover_custom_terminals() -> list[dict]:
    """Scan PATH for unknown AI CLI tools and suggest adding them."""
    known_binaries = {"claude", "mimo", "opencode", "codex", "q", "pi", "cursor",
                      "openclaw", "continue", "gh", "huggingface-cli", "gemini",
                      "aider", "interpreter", "fabric", "sgpt", "chatgpt", "llm",
                      "kimi", "copilot"}

    suggestions = []

    # Comprehensive list of AI CLI tools with their metadata
    common_clis = {
        "aider": ("Aider", "aider", "--message"),
        "chatgpt": ("ChatGPT CLI", "chatgpt", ""),
        "continue": ("Continue", "continue", "--prompt"),
        "copilot": ("GitHub Copilot", "gh", "copilot"),
        "cursor": ("Cursor", "cursor", "--prompt"),
        "fabric": ("Fabric", "fabric", "--prompt"),
        "gemini": ("Gemini CLI", "gemini", "chat"),
        "huggingface": ("HuggingFace CLI", "huggingface-cli", "chat"),
        "interpreter": ("Open Interpreter", "interpreter", ""),
        "kimi": ("Kimi (Moonshot)", "kimi", ""),
        "llm": ("LLM CLI", "llm", ""),
        "openclaw": ("OpenClaw", "openclaw", "run"),
        "pi": ("Pi Coding Agent", "pi", ""),
        "sgpt": ("ShellGPT", "sgpt", ""),
        "tabby": ("Tabby", "tabby", "prompt"),
        "windsurf": ("Windsurf", "windsurf", ""),
        "copilot-ext": ("Copilot Extension", "copilot", ""),
        "llama": ("LLaMA CLI", "llama", "prompt"),
        "qwen": ("Qwen CLI", "qwen", "chat"),
    }

    for name, (label, binary, flag) in common_clis.items():
        path = shutil.which(binary)
        if path and binary not in known_binaries:
            suggestions.append({
                "name": name,
                "label": label,
                "binary": binary,
                "path": path,
                "command_template": f"{binary} {flag} {{prompt}}" if flag else f"{binary} --prompt {{prompt}}",
            })

    return suggestions
