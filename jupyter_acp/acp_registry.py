"""Integration with the shared ACP Agent Registry.

The registry (https://agentclientprotocol.com, jointly maintained by Zed and
JetBrains) is a public JSON index of ACP agents. Each entry has a `distribution`
describing how to launch it; `npx` and `uvx` distributions are runnable on
demand (no separate install step), so we can offer any of them as a binding.
Binary distributions need a platform download and aren't supported yet.

This is how we emulate Zed's "add more agents" marketplace using the community
asset rather than a hand-maintained list.
"""
from __future__ import annotations

import json
import urllib.request
from typing import Any, Callable, Dict, List, Optional

from .registry import HarnessSpec

REGISTRY_URL = "https://cdn.agentclientprotocol.com/registry/v1/latest/registry.json"


def spec_from_distribution(agent: Dict[str, Any]) -> Optional[HarnessSpec]:
    """Derive a launchable HarnessSpec from a registry agent, or None if its
    distribution needs a separate install (binary)."""
    dist = agent.get("distribution", {})
    agent_id = agent["id"]
    name = agent.get("name", agent_id)
    if "npx" in dist:
        npx = dist["npx"]
        return HarnessSpec(
            id=agent_id,
            display_name=name,
            command="npx",
            args=("-y", npx["package"], *tuple(npx.get("args", []))),
        )
    if "uvx" in dist:
        uvx = dist["uvx"]
        return HarnessSpec(
            id=agent_id,
            display_name=name,
            command="uvx",
            args=(uvx["package"], *tuple(uvx.get("args", []))),
        )
    return None


class AcpRegistry:
    """Lazily-fetched, cached view of the shared ACP Agent Registry."""

    def __init__(
        self,
        url: str = REGISTRY_URL,
        fetch: Optional[Callable[[], Dict[str, Any]]] = None,
    ) -> None:
        self._url = url
        self._fetch = fetch or self._default_fetch
        self._agents: Dict[str, Dict[str, Any]] = {}
        self._loaded = False

    def _default_fetch(self) -> Dict[str, Any]:
        # The CDN 403s the default Python user-agent, so set our own.
        request = urllib.request.Request(self._url, headers={"User-Agent": "jupyter-acp"})
        with urllib.request.urlopen(request, timeout=10) as resp:
            return json.loads(resp.read())

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        try:
            data = self._fetch()
            self._agents = {a["id"]: a for a in data.get("agents", [])}
        except Exception:
            self._agents = {}  # offline / fetch failure: degrade quietly
        self._loaded = True

    def get(self, agent_id: str) -> Optional[Dict[str, Any]]:
        self._ensure_loaded()
        return self._agents.get(agent_id)

    def spec_for(self, agent_id: str) -> Optional[HarnessSpec]:
        agent = self.get(agent_id)
        return spec_from_distribution(agent) if agent else None

    def listing(self) -> List[Dict[str, Any]]:
        self._ensure_loaded()
        return [
            {
                "id": a["id"],
                "display_name": a.get("name", a["id"]),
                "description": a.get("description"),
                "icon": a.get("icon"),
                "launchable": spec_from_distribution(a) is not None,
            }
            for a in self._agents.values()
        ]
