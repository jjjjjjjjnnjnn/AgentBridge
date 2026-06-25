# RelayOS Keyboard Shortcuts

## TUI Mode (`relay`)

| Key | Action |
|-----|--------|
| `Ctrl+P` | Command palette — **all settings** (searchable) |
| `Tab` | Cycle through installed CLI providers (`mimo` → `claude` → `opencode` → ...) |
| `Shift+Tab` | Cycle mode: `auto` → `edit` → `group` |
| `Enter` | Send message / Confirm selection |
| `↑` / `↓` | History navigation |
| `Esc` | Cancel / Clear input / Close panel |
| `Backspace` | Delete character |
| `Ctrl+U` | Clear input line |
| `Ctrl+C` | Exit RelayOS |

## Command Palette (`Ctrl+P`)

Once open:

| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate items |
| `Enter` | Execute selected action |
| `Esc` or `Ctrl+P` | Close palette |
| Type any text | Filter commands by name/description |

## Switch Session Panel

| Key | Action |
|-----|--------|
| `Tab` | Toggle focus (search bar ↔ session list) |
| `↑` / `↓` | Navigate session list |
| `Enter` | Open selected session |
| `d` | Delete selected session |
| `Esc` | Close panel |
| Type any text | Filter sessions by name or message content |

## Slash Commands

| Command | Action |
|---------|--------|
| `/new` | Start a new conversation |
| `/fork` | Branch current session (copies all messages) |
| `/merge <id1> <id2>` | Combine multiple sessions |
| `/attach <id>` | Import context from another session |
| `/remember key: value` | Save cross-session knowledge |
| `/clear` | Clear current messages |
| `/help` | Show all commands |
| `/cost` | Show spending report |
| `/mode` | Cycle through modes (auto / edit / group) |

## Status Bar

```
RelayOS  sess-abc123  [Mimo]  [AUTO]  $0
```

- `RelayOS` — App name
- `sess-abc123` — Current session ID
- `[Mimo]` — Active CLI provider
- `[AUTO]` — Current mode (AUTO / EDIT / GROUP)
- `$0` — Today's spending

## Modes

| Mode | Behavior |
|------|----------|
| **AUTO** | Send to selected provider, auto-accept response |
| **EDIT** | Ask for confirmation before each provider call |
| **GROUP** | Send to multiple providers and show all responses |
