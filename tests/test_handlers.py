"""REST handler contract over the BindingManager.

Uses a stub manager so these tests stay fast and deterministic and cover the
HTTP translation (routing, JSON, status codes). Real bind behaviour — launching
a harness and opening a session — is covered by test_manager.py.
"""
from __future__ import annotations

import json

from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application

from jupyter_acp.binding import AlreadyBoundError
from jupyter_acp.handlers import (
    BindHandler,
    ConfigOptionHandler,
    HarnessesHandler,
    ModeHandler,
    ModelHandler,
    StateHandler,
)
from jupyter_acp.registry import HarnessNotFoundError, HarnessRegistry, HarnessSpec


class _StubState:
    def snapshot(self):
        return {
            "available_models": [{"id": "sonnet", "name": "Sonnet"}],
            "selected_model_id": "sonnet",
            "available_modes": [],
            "selected_mode_id": None,
            "config_options": [],
        }


class _StubSession:
    def __init__(self):
        self.calls = []
        self.session_state = _StubState()

    async def set_model(self, model_id):
        self.calls.append(("model", model_id))

    async def set_mode(self, mode_id):
        self.calls.append(("mode", mode_id))

    async def set_config_option(self, config_id, value):
        self.calls.append(("config", config_id, value))


class _StubBinding:
    def __init__(self, harness_id):
        self.harness_id = harness_id
        self.is_bound = True
        self.session = _StubSession()


class _StubManager:
    def __init__(self, registry, bind_error=None):
        self.registry = registry
        self._bindings = {}
        self._bind_error = bind_error

    def lookup(self, chat_id):
        return self._bindings.get(chat_id)

    async def bind(self, chat_id, harness_id, cwd=None):
        if self._bind_error is not None:
            raise self._bind_error
        binding = _StubBinding(harness_id)
        self._bindings[chat_id] = binding
        return binding


def _registry():
    registry = HarnessRegistry()
    registry.register(
        HarnessSpec(id="claude-code", display_name="Claude Code", command="claude-agent-acp")
    )
    return registry


class HandlerTestBase(AsyncHTTPTestCase):
    bind_error = None

    def get_app(self):
        self.registry = _registry()
        self.manager = _StubManager(self.registry, bind_error=self.bind_error)
        deps = dict(registry=self.registry, manager=self.manager)
        return Application(
            [
                (r"/harnesses", HarnessesHandler, deps),
                (r"/chats/(.+)/bind", BindHandler, deps),
                (r"/chats/(.+)/state", StateHandler, deps),
                (r"/chats/(.+)/model", ModelHandler, deps),
                (r"/chats/(.+)/mode", ModeHandler, deps),
                (r"/chats/(.+)/config-option", ConfigOptionHandler, deps),
            ]
        )

    def _post(self, path, payload):
        return self.fetch(path, method="POST", body=json.dumps(payload))


class TestHarnesses(HandlerTestBase):
    def test_lists_harnesses(self):
        resp = self.fetch("/harnesses")
        assert resp.code == 200
        assert json.loads(resp.body) == {
            "harnesses": [{"id": "claude-code", "display_name": "Claude Code"}]
        }


class TestBind(HandlerTestBase):
    def test_bind_ok(self):
        resp = self._post("/chats/chat-1/bind", {"harness_id": "claude-code"})
        assert resp.code == 200
        assert json.loads(resp.body)["harness_id"] == "claude-code"

    def test_missing_harness_id_400(self):
        resp = self._post("/chats/chat-1/bind", {})
        assert resp.code == 400


class TestBindUnknown(HandlerTestBase):
    bind_error = HarnessNotFoundError("nope")

    def test_unknown_harness_404(self):
        resp = self._post("/chats/chat-1/bind", {"harness_id": "nope"})
        assert resp.code == 404


class TestBindConflict(HandlerTestBase):
    bind_error = AlreadyBoundError("already")

    def test_already_bound_409(self):
        resp = self._post("/chats/chat-1/bind", {"harness_id": "x"})
        assert resp.code == 409


class TestState(HandlerTestBase):
    def test_unbound_returns_null(self):
        resp = self.fetch("/chats/absent/state")
        assert resp.code == 200
        assert json.loads(resp.body) == {"harness_id": None}

    def test_bound_returns_snapshot(self):
        self._post("/chats/chat-1/bind", {"harness_id": "claude-code"})
        resp = self.fetch("/chats/chat-1/state")
        assert resp.code == 200
        body = json.loads(resp.body)
        assert body["harness_id"] == "claude-code"
        assert body["selected_model_id"] == "sonnet"


class TestSetters(HandlerTestBase):
    def test_set_model_delegates(self):
        self._post("/chats/chat-1/bind", {"harness_id": "claude-code"})
        resp = self._post("/chats/chat-1/model", {"model_id": "opus"})
        assert resp.code == 200
        assert ("model", "opus") in self.manager.lookup("chat-1").session.calls

    def test_set_on_unbound_404(self):
        resp = self._post("/chats/absent/model", {"model_id": "opus"})
        assert resp.code == 404
