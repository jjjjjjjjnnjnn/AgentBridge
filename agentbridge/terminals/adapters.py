"""Terminal adapters for all supported AI CLIs."""
from agentbridge.terminals.base import BaseTerminal, TerminalInstance


class ClaudeCodeTerminal(BaseTerminal):
    """Claude Code CLI (claude) terminal."""
    type = "claude"
    binary = "claude"
    default_model = "claude-sonnet-4-20250514"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        cmd = [self.binary, "-p", prompt]
        # Model selection via env var (Claude Code reads ANTHROPIC_MODEL)
        if instance.model and instance.model != self.default_model:
            cmd.extend(["--model", instance.model])
        return cmd


class MimoCodeTerminal(BaseTerminal):
    """Mimo Code CLI (mimo) terminal."""
    type = "mimo"
    binary = "mimo"
    default_model = "gpt-4o"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        cmd = [self.binary, "run", prompt]
        if instance.model and instance.model != self.default_model:
            cmd.extend(["--model", instance.model])
        return cmd


class OpenCodeTerminal(BaseTerminal):
    """OpenCode CLI (opencode) terminal."""
    type = "opencode"
    binary = "opencode"
    default_model = "deepseek-chat"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        cmd = [self.binary, "run", prompt]
        if instance.model and instance.model != self.default_model:
            cmd.extend(["--model", instance.model])
        return cmd


class CodexTerminal(BaseTerminal):
    """OpenAI Codex CLI (codex) terminal."""
    type = "codex"
    binary = "codex"
    default_model = "gpt-4o"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        cmd = [self.binary, "prompt", prompt]
        if instance.model and instance.model != self.default_model:
            cmd.extend(["--model", instance.model])
        return cmd


class QCodeTerminal(BaseTerminal):
    """QCode CLI (q) terminal — generic terminal for Qwen/Qodo/etc."""
    type = "qcode"
    binary = "q"
    default_model = "qwen2.5:7b"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        return [self.binary, "--prompt", prompt]


class CustomTerminal(BaseTerminal):
    """Custom terminal — wraps any CLI command."""
    type = "custom"
    binary = ""

    def __init__(self, config: dict | None = None):
        super().__init__(config)
        self.type = config.get("type", "custom") if config else "custom"
        self.binary = config.get("binary", "") if config else ""
        self.default_model = config.get("default_model", "unknown") if config else "unknown"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        template = self.config.get("command_template", "{binary} --prompt {prompt}")
        # Use simple replace instead of str.format() to avoid KeyError on {braces} in prompt
        cmd_str = template.replace("{binary}", self.binary).replace("{prompt}", prompt).replace("{model}", instance.model)
        import shlex
        return shlex.split(cmd_str)
