"""First-run setup wizard — 中文引导，30 秒完成配置。

第一次运行 relay 时自动触发，检测不到配置文件时进入向导。
"""
from __future__ import annotations

import sys

from relayos.i18n import t
from relayos.providers import detect_providers, ProviderDef
from relayos.config import get_config_dir


def _prompt(question: str, default: str = "") -> str:
    """Ask user for input."""
    try:
        return input(question).strip() or default
    except (EOFError, KeyboardInterrupt):
        return default


def run_wizard() -> bool:
    """Run the setup wizard.

    Returns True if config was created, False if skipped.
    """
    config_dir = get_config_dir()
    config_path = config_dir / "config.yaml"

    # Already configured?
    if config_path.exists():
        return False

    config_dir.mkdir(parents=True, exist_ok=True)

    # Detect available providers
    providers = detect_providers()
    api_providers = [p for p in providers if p.type == "api"]
    cli_providers = [p for p in providers if p.type == "cli"]
    installed_cli = [p for p in cli_providers if p.enabled]

    print("")
    print("=" * 50)
    print(f"  {t('welcome_title')}")
    print(f"  {t('welcome_desc')}")
    print("=" * 50)
    print("")

    # ── Step 1: API Keys ──
    print(f"  {t('step_api_keys', n=1)}")
    print(f"  {t('key_local_only')}")
    print("")

    collected_keys = {}
    for p in api_providers:
        env_var = {
            "openai": "OPENAI_API_KEY",
            "anthropic": "ANTHROPIC_API_KEY",
            "google": "GEMINI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
        }.get(p.provider, "")

        # Check if already set in env
        import os
        env_key = os.environ.get(env_var, "")
        if env_key:
            collected_keys[p.provider] = env_key
            print(f"  ✓ {p.display_name} — 已从环境变量读取")
            continue

        prompt_text = f"  {p.display_name} API Key（留空跳过）："
        key = _prompt(f"  {prompt_text} ")
        if key:
            collected_keys[p.provider] = key
            print(f"  ✓ {p.display_name} 已保存")
        else:
            print(f"  · {p.display_name} 已跳过")
        print("")

    # Show detected CLI terminals
    if installed_cli:
        print(f"  ✓ 检测到 CLI：{', '.join(p.display_name for p in installed_cli)}")
        print("")

    # ── Step 2: Budget limits ──
    print(f"  {t('step_limits', n=2)}")
    print("")

    daily_raw = _prompt(f"  {t('daily_limit', amount='1.00')} ", "1.00")
    try:
        daily_limit = float(daily_raw)
    except ValueError:
        daily_limit = 1.00

    task_raw = _prompt(f"  {t('single_limit', amount='0.05')} ", "0.05")
    try:
        task_limit = float(task_raw)
    except ValueError:
        task_limit = 0.05

    print("")

    # ── Write config ──
    providers_config = {}
    for prov, key in collected_keys.items():
        providers_config[prov] = {
            "api_key": key,
        }

    import yaml
    config = {
        "providers": providers_config,
        "limits": {
            "per_task_usd": task_limit,
            "daily_usd": daily_limit,
            "monthly_usd": daily_limit * 30,
            "warn_at_percent": 80,
        },
        "mode": "auto",
        "routing": {
            "default": "balanced",
        },
    }
    config_path.write_text(yaml.dump(config, default_flow_style=False, allow_unicode=True), encoding="utf-8")

    # ── Done ──
    print("─" * 50)
    print(f"  {t('wizard_done')}")
    print("")
    print(f"  {t('wizard_usage')}")
    print("")
    print("─" * 50)
    print("")

    return True
