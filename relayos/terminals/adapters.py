"""Terminal adapters for all supported AI CLIs — comprehensive definitions.

Each terminal type defines:
- The CLI binary name
- Default model
- How to build the command to send a prompt

Users can add any CLI with: relayos plugin add <binary>
"""
from relayos.terminals.base import BaseTerminal, TerminalInstance


class ClaudeCodeTerminal(BaseTerminal):
    type = "claude"
    binary = "claude"
    default_model = "claude-sonnet-4-20250514"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        cmd = [self.binary, "-p", prompt]
        if instance.model and instance.model != self.default_model:
            cmd.extend(["--model", instance.model])
        return cmd


class MimoCodeTerminal(BaseTerminal):
    type = "mimo"
    binary = "mimo"
    default_model = "gpt-4o"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        cmd = [self.binary, "run", prompt]
        if instance.model and instance.model != self.default_model:
            cmd.extend(["--model", instance.model])
        return cmd


class OpenCodeTerminal(BaseTerminal):
    type = "opencode"
    binary = "opencode"
    default_model = "deepseek-chat"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        cmd = [self.binary, "run", prompt]
        if instance.model and instance.model != self.default_model:
            cmd.extend(["--model", instance.model])
        return cmd


class CodexTerminal(BaseTerminal):
    type = "codex"
    binary = "codex"
    default_model = "gpt-4o"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        cmd = [self.binary, "prompt", prompt]
        if instance.model and instance.model != self.default_model:
            cmd.extend(["--model", instance.model])
        return cmd


class QCodeTerminal(BaseTerminal):
    type = "qcode"
    binary = "q"
    default_model = "qwen2.5:7b"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        return [self.binary, "--prompt", prompt]


class PiTerminal(BaseTerminal):
    """Pi Coding Agent (pi) — terminal-based AI coding agent."""
    type = "pi"
    binary = "pi"
    default_model = "gpt-4o"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        return [self.binary, prompt]


class CursorTerminal(BaseTerminal):
    """Cursor AI editor CLI (cursor) — AI-powered code editor CLI."""
    type = "cursor"
    binary = "cursor"
    default_model = "gpt-4o"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        return [self.binary, "--prompt", prompt]


class OpenClawTerminal(BaseTerminal):
    """OpenClaw (openclaw) — multi-agent gateway with LM Studio local models."""
    type = "openclaw"
    binary = "openclaw"
    default_model = "gpt-4o"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        return [self.binary, "run", prompt]


class ContinueTerminal(BaseTerminal):
    """Continue (continue) — open-source AI code assistant CLI."""
    type = "continue"
    binary = "continue"
    default_model = "gpt-4o"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        return [self.binary, "--prompt", prompt]


class GitHubCopilotTerminal(BaseTerminal):
    """GitHub Copilot CLI (gh copilot) — AI assistant in terminal."""
    type = "copilot"
    binary = "gh"
    default_model = "gpt-4o"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        return [self.binary, "copilot", "suggest", prompt]


class HuggingFaceTerminal(BaseTerminal):
    """HuggingFace CLI (huggingface-cli) — HF model interaction."""
    type = "huggingface"
    binary = "huggingface-cli"
    default_model = "gpt-4o"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        return [self.binary, "chat", "--message", prompt]


class GeminiCliTerminal(BaseTerminal):
    """Gemini CLI (gemini) — Google's Gemini CLI tool."""
    type = "gemini"
    binary = "gemini"
    default_model = "gemini-2.5-flash"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        return [self.binary, "chat", prompt]


class AiderTerminal(BaseTerminal):
    """Aider (aider) — AI pair programming in terminal."""
    type = "aider"
    binary = "aider"
    default_model = "gpt-4o"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        return [self.binary, "--message", prompt]


class OpenInterpreterTerminal(BaseTerminal):
    """Open Interpreter (interpreter) — natural language computing CLI."""
    type = "interpreter"
    binary = "interpreter"
    default_model = "gpt-4o"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        return [self.binary, prompt]


class FabricTerminal(BaseTerminal):
    """Fabric (fabric) — open-source AI CLI framework."""
    type = "fabric"
    binary = "fabric"
    default_model = "gpt-4o"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        return [self.binary, "--prompt", prompt]


class SgptTerminal(BaseTerminal):
    """ShellGPT (sgpt) — terminal AI assistant."""
    type = "sgpt"
    binary = "sgpt"
    default_model = "gpt-4o"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        return [self.binary, prompt]


class ChatgptCliTerminal(BaseTerminal):
    """ChatGPT CLI (chatgpt) — official OpenAI CLI."""
    type = "chatgpt"
    binary = "chatgpt"
    default_model = "gpt-4o"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        return [self.binary, prompt]


class LlmCliTerminal(BaseTerminal):
    """LLM CLI (llm) — Simon Willison's LLM tool."""
    type = "llm"
    binary = "llm"
    default_model = "gpt-4o"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        cmd = [self.binary, prompt]
        if instance.model:
            cmd.extend(["-m", instance.model])
        return cmd


class KimiTerminal(BaseTerminal):
    """Kimi (kimi) — Moonshot AI CLI (Chinese-first LLM)."""
    type = "kimi"
    binary = "kimi"
    default_model = "moonshot-v1-8k"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        return [self.binary, prompt]


class CopilotExtTerminal(BaseTerminal):
    """Copilot extension (copilot) — generic AI copilot CLI."""
    type = "copilot-ext"
    binary = "copilot"
    default_model = "gpt-4o"

    def build_command(self, instance: TerminalInstance, prompt: str, **kwargs) -> list[str]:
        return [self.binary, prompt]


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
        cmd_str = template.replace("{binary}", self.binary).replace("{prompt}", prompt).replace("{model}", instance.model)
        import shlex
        return shlex.split(cmd_str)
