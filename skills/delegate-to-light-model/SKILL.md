---
name: delegate-to-light-model
description: Use when the user asks to use the light model, "the proxy model" or a cheaper model for a task, or when a self-contained, low-stakes task (boilerplate, test scaffolding, bulk summarising or rewriting, a first draft, a second opinion on code) could be offloaded to a cheaper model to save cost.
---

# Delegate to a light model

## Overview

The light model runs on the deployed LiteLLM proxy. The default is `claude-haiku-5-5`, at about 1/20 of Sonnet 5.5's price ($0.10 in / $0.50 out per MTok). Above 100k prompt tokens Haiku 5.5 costs 5x more, so agent mode caps its context at 100k (`LIGHT_MODEL_AGENT_CONTEXT_TOKENS`) and you should keep ask-mode attachments well under that. You stay responsible for the result: the light model drafts, you review.

The scripts read `LIGHT_MODEL_PROXY_URL` and `LIGHT_MODEL_PROXY_KEY` from the environment, or from `~/.config/llm-proxy/light_model.env`. If a script exits 2 saying they are unset, tell the user; never ask for, read out or print the key.

## Choose the mode

`<skill-dir>` is the base directory shown when this skill loads.

| Mode | Command | Use for |
|---|---|---|
| Ask (default) | `python3 <skill-dir>/scripts/ask_light_model.py "<task>" -f <file>...` | Text in, text out. The light model sees only what you pass it and changes nothing. |
| Agent | `bash <skill-dir>/scripts/light_model_agent.sh "<task>"` | The light model works in the current directory with Claude Code's tools and may edit files. Only when the user asked for it, or the task is mechanical and fully specified. |

Ask mode: attach every file the light model needs with `-f` (repeatable) or pipe text on stdin. Use `-s` for a system prompt and `-m <model_name>` for another proxy model. Token usage goes to stderr.

Agent mode: runs a headless `claude -p` with the light model as the model and `--permission-mode acceptEdits`, so it can edit but not run shell commands. To allow specific commands, append flags, e.g. `--allowedTools "Bash(npm test:*)"`. Set `LIGHT_MODEL_AGENT_MODEL` for another proxy model. Run it with a Bash timeout of up to 600000 ms, and in the background for long tasks.

## Writing the task

The light model has none of your context. State the goal, the constraints (language, style rules, files it may touch), and the exact output shape you want back. One task per call.

## After it returns

- Ask mode: read the answer critically before using it. Apply edits yourself.
- Agent mode: run `git diff` and review every change before reporting. Revert what is wrong.
- Tell the user the work was done by the light model.

## Common mistakes

- Sending a task that needs judgment about this conversation, or about security, data migrations or production config. Do those yourself.
- Forgetting to attach files in ask mode, so the light model guesses at code it never saw.
- Trusting agent-mode output without reading the diff: a light model makes more mistakes than you do, and non-Claude models (`-m` / `LIGHT_MODEL_AGENT_MODEL`) also fail tool calls more often through the proxy.
