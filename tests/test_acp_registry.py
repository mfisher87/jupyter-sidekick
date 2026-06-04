"""The shared ACP Agent Registry (Zed + JetBrains): parse the index and derive
on-demand launch specs from npx/uvx distributions."""
from __future__ import annotations

from jupyter_acp.acp_registry import AcpRegistry, spec_from_distribution

SAMPLE = {
    "version": "1",
    "agents": [
        {
            "id": "cline",
            "name": "Cline",
            "description": "Autonomous coding agent",
            "icon": "https://x/cline.svg",
            "distribution": {"npx": {"package": "cline@3.0.17", "args": ["--acp"]}},
        },
        {
            "id": "fast-agent",
            "name": "fast-agent",
            "distribution": {"uvx": {"package": "fast-agent-acp", "args": ["acp"]}},
        },
        {
            "id": "somebin",
            "name": "SomeBin",
            "distribution": {"binary": {"linux-x86_64": {"archive": "u", "cmd": "bin/x"}}},
        },
    ],
}


def test_spec_from_npx_distribution():
    spec = spec_from_distribution(SAMPLE["agents"][0])
    assert spec.id == "cline"
    assert spec.command == "npx"
    assert spec.args == ("-y", "cline@3.0.17", "--acp")


def test_spec_from_uvx_distribution():
    spec = spec_from_distribution(SAMPLE["agents"][1])
    assert spec.command == "uvx"
    assert spec.args == ("fast-agent-acp", "acp")


def test_binary_distribution_not_launchable_yet():
    assert spec_from_distribution(SAMPLE["agents"][2]) is None


def test_registry_listing_and_spec_for():
    registry = AcpRegistry(fetch=lambda: SAMPLE)
    listing = {a["id"]: a for a in registry.listing()}
    assert listing["cline"]["launchable"] is True
    assert listing["cline"]["display_name"] == "Cline"
    assert listing["somebin"]["launchable"] is False
    assert registry.spec_for("cline").command == "npx"
    assert registry.spec_for("missing") is None


def test_offline_safe():
    def boom():
        raise OSError("no network")

    registry = AcpRegistry(fetch=boom)
    assert registry.listing() == []  # degrades quietly, never raises
