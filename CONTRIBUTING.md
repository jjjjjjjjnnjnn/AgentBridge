# Contributing to RelayOS

Thank you for your interest in contributing! RelayOS is an open-source operating system for AI agents, and we welcome contributions from the community.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/jjjjjjjjnnjnn/relayos.git
cd relayos

# Install in development mode
pip install -e .
```

## Code Standards

- **Type hints**: All functions must have complete type annotations
- **Error handling**: Use `AdapterError` for adapter errors, `MCPError` for MCP errors
- **Testing**: New features should include `pytest` tests in `tests/`
- **CLI**: New commands should use Click groups in `relayos/cli/`

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/amazing-feature`)
3. Commit using [Conventional Commits](https://www.conventionalcommits.org/)
4. Push to your fork and submit a Pull Request

## Adding a New Agent Adapter

1. Create `relayos/adapters/newprovider.py`
2. Implement `BaseAdapter` interface
3. Register in `relayos/adapters/__init__.py`
4. Add entry point in `pyproject.toml`

## Adding a New Terminal Type

1. Add terminal class in `relayos/terminals/adapters.py`
2. Register in `relayos/terminals/__init__.py`

## Code of Conduct

Be respectful, constructive, and inclusive.
