"""HarnessRegistry: id -> launch spec for the agents the user can bind."""
from __future__ import annotations

import pytest

from jupyter_acp.registry import HarnessNotFoundError, HarnessRegistry, HarnessSpec


def _spec(id_: str = "fake") -> HarnessSpec:
    return HarnessSpec(id=id_, display_name=id_.title(), command="python", args=("-c", "pass"))


def test_register_and_get():
    registry = HarnessRegistry()
    spec = _spec()
    registry.register(spec)
    assert registry.get("fake") is spec


def test_get_missing_raises():
    with pytest.raises(HarnessNotFoundError):
        HarnessRegistry().get("nope")


def test_duplicate_register_raises():
    registry = HarnessRegistry()
    registry.register(_spec())
    with pytest.raises(ValueError):
        registry.register(_spec())


def test_list_preserves_registration_order():
    registry = HarnessRegistry()
    registry.register(_spec("a"))
    registry.register(_spec("b"))
    assert [s.id for s in registry.list()] == ["a", "b"]
