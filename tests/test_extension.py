"""The default harness registry the server extension wires up."""
from __future__ import annotations

from jupyter_acp.extension import build_default_registry


def test_default_registry_includes_claude_code():
    spec = build_default_registry().get("claude-code")
    assert spec.command == "claude-agent-acp"


def test_default_registry_lists_at_least_one_harness():
    ids = [s.id for s in build_default_registry().list()]
    assert "claude-code" in ids


def test_extension_points_reference_the_app_class():
    from jupyter_acp import _jupyter_server_extension_points
    from jupyter_acp.extension import AcpExtension

    point = _jupyter_server_extension_points()[0]
    assert point["module"] == "jupyter_acp.extension"
    assert point["app"] is AcpExtension  # the class, not a string
