# Contributing to AgentBridge

Thank you for your interest in contributing! AgentBridge is an open-source coordination layer for AI agents, and we welcome contributions from the community.

## Development Setup

```bash
# Clone the repository
git clone https://github.com/jjjjjjjjnnjnn/AgentBridge.git
cd AgentBridge

# Install in development mode
pip install -e .
```

## Code Standards

- **Type hints**: All functions must have complete type annotations
- **Error handling**: Use `AdapterError` for adapter-specific errors, `MCPError` for MCP errors
- **Testing**: New features should include tests (pytest in `tests/`)
- **CLI**: New commands should be added via Click groups in `cli/main.py` or new modules in `cli/`

## Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feat/amazing-feature`)
3. Commit your changes using [Conventional Commits](https://www.conventionalcommits.org/)
4. Push to your fork and submit a Pull Request

## Adding a New Agent Adapter

1. Create `agentbridge/adapters/newprovider.py`
2. Implement the `BaseAdapter` interface
3. Register in `agentbridge/adapters/__init__.py`
4. Add to `pyproject.toml` entry points

## Adding a New Terminal Type

1. Create the terminal class in `agentbridge/terminals/adapters.py`
2. Register in `agentbridge/terminals/__init__.py`

## Code of Conduct

Be respectful, constructive, and inclusive. We're all here to build something useful.
