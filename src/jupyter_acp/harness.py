"""A live binding to one ACP harness subprocess, for one chat.

`HarnessSession` wraps `acp.spawn_agent_process` and the session lifecycle:
launch the harness, `initialize`, open a session, and `prompt` it. One
`HarnessSession` corresponds to one bound chat — the per-chat single-agent model.
"""
from __future__ import annotations

import contextlib
from typing import Mapping, Optional

import acp

from .acp_client import HarnessClient


class HarnessSession:
    def __init__(
        self,
        command: str,
        *args: str,
        cwd: Optional[str] = None,
        env: Optional[Mapping[str, str]] = None,
        client: Optional[HarnessClient] = None,
    ) -> None:
        self.command = command
        self.args = args
        self.cwd = cwd
        self.env = env
        self.client = client if client is not None else HarnessClient()
        self._stack: Optional[contextlib.AsyncExitStack] = None
        self.conn = None
        self.process = None
        self.session_id: Optional[str] = None

    async def start(self) -> "HarnessSession":
        self._stack = contextlib.AsyncExitStack()
        self.conn, self.process = await self._stack.enter_async_context(
            acp.spawn_agent_process(
                self.client, self.command, *self.args, cwd=self.cwd, env=self.env
            )
        )
        await self.conn.initialize(protocol_version=acp.PROTOCOL_VERSION)
        return self

    async def new_session(self, cwd: Optional[str] = None):
        response = await self.conn.new_session(cwd=cwd or self.cwd or ".")
        self.session_id = response.sessionId
        return response

    async def prompt(self, text: str):
        return await self.conn.prompt(
            prompt=[acp.text_block(text)], session_id=self.session_id
        )

    async def close(self) -> None:
        if self._stack is not None:
            await self._stack.aclose()
            self._stack = None
