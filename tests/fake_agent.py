"""A protocol-correct minimal ACP agent, for tests.

Run as a subprocess over stdio via ``acp.run_agent``. Implements just enough of
``acp.Agent`` to exercise our client + harness without a real harness binary or
any auth:

- ``initialize`` / ``new_session``
- ``prompt`` echoes the incoming text back as an agent-message chunk, then ends
  the turn.

MUST NOT write to stdout except via the ACP transport — stdout is the protocol
channel.
"""
from __future__ import annotations

import asyncio

import acp


class FakeAgent(acp.Agent):
    def __init__(self) -> None:
        self._conn = None

    def on_connect(self, conn) -> None:
        # `conn` lets the agent call Client methods (e.g. session_update).
        self._conn = conn

    async def initialize(self, protocol_version, client_capabilities=None, client_info=None, **kwargs):
        return acp.InitializeResponse(protocolVersion=acp.PROTOCOL_VERSION)

    async def new_session(self, cwd, mcp_servers=None, **kwargs):
        return acp.NewSessionResponse(sessionId="fake-session-1")

    async def prompt(self, prompt, session_id, message_id=None, **kwargs):
        incoming = "".join(getattr(block, "text", "") for block in prompt)
        await self._conn.session_update(
            session_id=session_id,
            update=acp.update_agent_message_text(f"echo: {incoming}"),
        )
        return acp.PromptResponse(stopReason="end_turn")


if __name__ == "__main__":
    asyncio.run(acp.run_agent(FakeAgent()))
