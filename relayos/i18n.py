"""i18n — 中英文国际化，所有面向用户的文字走这里。
"""
from __future__ import annotations

import locale
import sys

_STRINGS: dict[str, dict[str, str]] = {
    "zh": {
        # Welcome / Onboarding
        "welcome_title": "欢迎使用 RelayOS",
        "welcome_desc": "RelayOS 帮你把多个 AI 终端组成一个团队。\n先花 30 秒完成配置。",
        "step_choose_providers": "第 {n} 步：选择你有的 AI（↑↓ 移动，空格选择，Enter 确认）",
        "step_api_keys": "第 {n} 步：填入 API Key",
        "step_limits": "第 {n} 步：设置消费上限（防止意外扣费）",
        "enter_api_key": "{name} API Key：",
        "key_local_only": "（Key 只存在本地，不上传任何服务器）",
        "daily_limit": "每日上限：$ {amount}  （推荐）",
        "single_limit": "单次上限：$ {amount}  （推荐）",
        "wizard_done": "✓ 配置完成！",
        "wizard_usage": "你现在可以：\n\n  relay \"帮我写一个 Python 爬虫\"   ← 直接干活\n  relay                            ← 打开工作台\n  relayos cost report              ← 查看花费",

        # TUI
        "enter_task": "输入任务，按 Enter 执行",
        "type_task": "输入你的任务，按 Enter 执行。系统自动分配到最佳 Provider。",
        "providers_detected": "检测到 Provider：{names}",
        "no_providers": "未检测到 AI 终端。安装 claude、opencode 等，或添加 API Key。",
        "processing": "处理中：{task}",
        "task_done": "✓ {task}",
        "session_id": "会话：{id}",
        "new_task_hint": "[n] 新任务  [s] 设置  [q] 退出",
        "input_hint": "Enter=执行  s=设置  ?=帮助  q=退出",

        # Settings
        "settings_title": "设置",
        "mode_label": "模式：{mode}",
        "mode_auto": "自动 — 直接执行，不询问",
        "mode_edit": "手动 — 每次调用前询问",
        "mode_toggle": "[M] 切换模式",
        "providers_list": "Provider：",
        "back_hint": "[B] 返回  [M] 模式  [Q] 退出",

        # Cost / Budget
        "cost_preview": "预计费用：",
        "cost_total": "总计",
        "confirm_execute": "[Enter] 确认执行  [e] 编辑  [q] 取消",
        "daily_limit_hit": "今日已花费 ${used:.3f}，本次预计 ${est:.3f}，将超过每日上限 ${limit}",
        "task_limit_warn": "本次预计花费 ${cost:.3f}，超过单次上限 ${limit}，确认执行？[y/N]",
        "cost_report_title": "消费报告",
        "cost_today": "今日消费",
        "cost_month": "本月消费",
        "cost_total_label": "总计",
        "cost_no_data": "暂无消费记录。",

        # Help
        "help_title": "帮助",
        "help_keys": "按键：",
        "key_enter": "Enter    提交任务",
        "key_quit": "q         退出",
        "key_settings": "s         设置",
        "key_help": "?         帮助",
        "key_new": "n         新任务（结果页）",
        "help_providers": "Provider：",
        "help_api": "API：OpenAI、Anthropic、Google、DeepSeek",
        "help_cli": "CLI：claude、opencode、mimo（自动检测）",
        "help_modes": "模式：",
        "help_auto": "auto    直接执行，不询问",
        "help_edit": "edit    每次调用 Provider 前询问",
    },
    "en": {
        "welcome_title": "Welcome to RelayOS",
        "welcome_desc": "RelayOS turns your AI terminals into a team.\nLet's get you set up in 30 seconds.",
        "step_choose_providers": "Step {n}: Select your AI providers (↑↓ navigate, Space select, Enter confirm)",
        "step_api_keys": "Step {n}: Enter API Keys",
        "step_limits": "Step {n}: Set spending limits",
        "enter_api_key": "{name} API Key: ",
        "key_local_only": "(Keys are stored locally, never uploaded)",
        "daily_limit": "Daily limit: ${amount}  (recommended)",
        "single_limit": "Per-task limit: ${amount}  (recommended)",
        "wizard_done": "✓ Setup complete!",
        "wizard_usage": "You can now:\n\n  relay \"build a Python scraper\"   ← direct task\n  relay                             ← open workspace\n  relayos cost report               ← view spending",

        "enter_task": "Type your task, press Enter to execute",
        "type_task": "Type your task and press Enter. The system auto-routes to the best provider.",
        "providers_detected": "Providers: {names}",
        "no_providers": "No AI terminals detected. Install claude, opencode, or add API keys.",
        "processing": "Processing: {task}",
        "task_done": "✓ {task}",
        "session_id": "Session: {id}",
        "new_task_hint": "[n] new task  [s] settings  [q] quit",
        "input_hint": "Enter=execute  s=settings  ?=help  q=quit",

        "settings_title": "Settings",
        "mode_label": "Mode: {mode}",
        "mode_auto": "auto — execute without asking",
        "mode_edit": "edit — ask before each provider call",
        "mode_toggle": "[M] Toggle mode",
        "providers_list": "Providers:",
        "back_hint": "[B] Back  [M] Mode  [Q] Quit",

        "cost_preview": "Estimated cost:",
        "cost_total": "Total",
        "confirm_execute": "[Enter] Execute  [e] Edit  [q] Cancel",
        "daily_limit_hit": "Daily spend ${used:.3f} + estimated ${est:.3f} exceeds daily limit ${limit}",
        "task_limit_warn": "Estimated cost ${cost:.3f} exceeds per-task limit ${limit}. Confirm? [y/N]",
        "cost_report_title": "Cost Report",
        "cost_today": "Today",
        "cost_month": "This Month",
        "cost_total_label": "Total",
        "cost_no_data": "No usage recorded yet.",

        "help_title": "Help",
        "help_keys": "Keys:",
        "key_enter": "Enter    Submit task",
        "key_quit": "q        Quit",
        "key_settings": "s        Settings",
        "key_help": "?        Help",
        "key_new": "n        New task (results page)",
        "help_providers": "Providers:",
        "help_api": "API: OpenAI, Anthropic, Google, DeepSeek",
        "help_cli": "CLI: claude, opencode, mimo (auto-detected)",
        "help_modes": "Modes:",
        "help_auto": "auto    Execute without asking",
        "help_edit": "edit    Ask before each provider call",
    },
}


def _detect_lang() -> str:
    try:
        loc = locale.getdefaultlocale()[0] or "en"
        return "zh" if loc.startswith("zh") else "en"
    except Exception:
        return "en"


_LANG = _detect_lang()


def set_lang(lang: str):
    """Override language: 'zh' or 'en'."""
    global _LANG
    if lang in ("zh", "en"):
        _LANG = lang


def t(key: str, **kwargs) -> str:
    """Translate a key, optionally formatting with kwargs."""
    strings = _STRINGS.get(_LANG, _STRINGS["en"])
    template = strings.get(key, key)
    return template.format(**kwargs) if kwargs else template
