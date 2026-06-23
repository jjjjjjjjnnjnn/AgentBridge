"""MCP Client — connect to MCP servers for tools.

Currently supports stdio-based MCP servers.
Hub mode (bidirectional) comes in v1.0.
"""
from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any


class MCPClient:
    """Lightweight MCP client that connects to a stdio-based MCP server."""

    def __init__(self, server_config: dict):
        self.name = server_config.get("name", "unknown")
        self.command = server_config["command"]
        self.args = server_config.get("args", [])
        self.env = server_config.get("env", {})
        self._process: subprocess.Popen | None = None

    def start(self):
        env = {**__import__("os").environ, **self.env}
        self._process = subprocess.Popen(
            [self.command, *self.args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=Path.cwd(),
        )

    def send_request(self, method: str, params: dict | None = None) -> dict[str, Any]:
        if not self._process:
            self.start()

        req = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {},
        }
        payload = json.dumps(req) + "\n"
        self._process.stdin.write(payload.encode())
        self._process.stdin.flush()

        line = self._process.stdout.readline()
        return json.loads(line)

    def list_tools(self) -> list[dict]:
        result = self.send_request("tools/list")
        return result.get("result", {}).get("tools", [])

    def call_tool(self, name: str, arguments: dict | None = None) -> Any:
        result = self.send_request("tools/call", {"name": name, "arguments": arguments or {}})
        return result.get("result")

    def close(self):
        if self._process:
            self._process.terminate()
            self._process.wait(timeout=5)
            self._process = None


class MCPManager:
    """Manages multiple MCP client connections."""

    def __init__(self):
        self._clients: dict[str, MCPClient] = {}

    def add_server(self, name: str, config: dict):
        client = MCPClient({"name": name, **config})
        self._clients[name] = client
        return client

    def get_client(self, name: str) -> MCPClient | None:
        return self._clients.get(name)

    def list_servers(self) -> list[str]:
        return list(self._clients.keys())

    def call_tool(self, server: str, tool: str, args: dict | None = None) -> Any:
        client = self._clients.get(server)
        if not client:
            raise ValueError(f"MCP server '{server}' not found")
        return client.call_tool(tool, args)

    def close_all(self):
        for client in self._clients.values():
            try:
                client.close()
            except Exception:
                pass
