# jupyter-acp

Jupyter-native access to coding agents over the
[Agent Client Protocol (ACP)](https://agentclientprotocol.com) — a per-chat,
single-agent experience in JupyterLab, with capability-driven model/mode
selectors and slash-command + skill support that comes straight from whatever
ACP agent ("harness") you bind a chat to.

> **Status: early.** The design is settled (see
> [`docs/design-decisions.md`](docs/design-decisions.md)); the implementation
> spec and code are being written. A working proof-of-concept already exists in
> a separate fork — see [Reference implementation](#reference-implementation).

## The idea

A chat is **bound to one ACP agent for its life** — Claude Code, OpenCode,
Gemini CLI, Codex, Goose, and so on. The toolbar then surfaces *only what that
agent advertises over ACP*: its available models, its session modes
(plan / accept-edits / …), its config options, and its slash commands. Nothing
is hard-coded per harness; the UI is driven by the protocol.

This separates two axes that are usually conflated in AI chat UIs:

- **Harness** — which agent runtime mediates tool use, file I/O, MCP, and
  sub-agents.
- **Model** — which LLM that harness is talking to.

…and it leaves a third axis — **persona**, the bundle of context you bring to a
conversation — to be expressed the way the open ecosystem already expresses it:
as a [Skill](https://agentskills.io) or an MCP server the harness loads, not as
a bespoke Jupyter object. The reasoning is in
[`docs/personas-as-skills.md`](docs/personas-as-skills.md).

## Why it's in Jupyter at all

Because the agent can edit the **notebook you have open, live.** The harness
writes the `.ipynb` on disk; JupyterLab's collaborative document layer
(`jupyter-server-documents`) detects the out-of-band change and reflects it into
your open notebook view within a second or so — no chat-specific machinery
required. That live-document loop is the thing a terminal next to Jupyter can't
give you, and it's the reason this is a JupyterLab extension rather than a
standalone app.

## How it's built

`jupyter-acp` is deliberately a thin, additive layer on open standards:

- **[`agent-client-protocol`](https://agentclientprotocol.com)** — the official
  ACP Python library (the same one every ACP client builds on). All agent
  communication goes through it.
- **[`@jupyter/chat`](https://github.com/jupyterlab/jupyter-chat)** — the
  JupyterLab chat widget primitives.
- **`jupyter-server`** + its collaborative document layer — for the live
  notebook-editing loop above.

It does **not** depend on, fork, or vendor the `jupyter-ai` persona/router stack.
Its dependency graph is part of the argument: a Jupyter-native ACP experience
needs none of the persona abstraction. See
[`docs/design-decisions.md`](docs/design-decisions.md) (Fork 6) for the full
reasoning.

## Relationship to Project Jupyter and to Zed

This is an independent, community project — **not** an official Project Jupyter
package, and **not** affiliated with or endorsed by Zed Industries.

The per-chat single-agent model is **inspired by [Zed](https://zed.dev/acp)**,
which co-created ACP and pioneered this interaction design for external agents.
ACP is Zed's open protocol, released for exactly this kind of adoption; building
on it is how we honor that work. We're grateful for it.

## Reference implementation

A working proof-of-concept — the same idea built *inside* a fork of
`jupyterlab/jupyter-ai`, on top of the `jupyter-ai` stack — lives at
[`cboettig/jupyter-ai@acp-bridge-impl`](https://github.com/cboettig/jupyter-ai/tree/acp-bridge-impl/jupyter-ai-acp-bridge).
`jupyter-acp` is the ground-up redesign that sheds those dependencies; the PoC
remains a useful empirical reference for how each piece behaves.

## Context

This work is part of an ongoing conversation with the Jupyter AI team about how
personas, models, and agent harnesses should relate:
[`jupyterlab/jupyter-ai#1558`](https://github.com/jupyterlab/jupyter-ai/issues/1558).

## License

BSD 3-Clause. See [`LICENSE`](LICENSE).
