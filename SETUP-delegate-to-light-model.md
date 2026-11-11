# Set up the `delegate-to-light-model` skill

Agent instructions. Paste this whole file into a Claude Code session and let the agent run it.

You are setting up a Claude Code skill that lets Claude Code hand low-stakes tasks to a light model (by default `claude-haiku-5-5`) through the six2eight LiteLLM gateway at `https://llm-proxy.cenario.ai`. The skill ships in the `light-model` plugin, installed from the `huyjack178/myclaudecode` GitHub repository. Follow the steps in order. Never ask the user to paste their key into the chat, and never print, echo or repeat it.

## 1. Check the prerequisites

Run these commands and stop if either one fails:

```bash
claude --version
python3 --version
```

Python must be 3.10 or newer.

## 2. Install the plugin from GitHub

Run these commands:

```bash
claude plugin marketplace add huyjack178/myclaudecode
claude plugin install light-model@myclaudecode
```

If a command fails, ask the user to run these lines in Claude Code themselves. They type them as slash commands, and then confirm:

```
/plugin marketplace add huyjack178/myclaudecode
/plugin install light-model@myclaudecode
```

If adding the marketplace fails with a "not found" or authentication error, the repository is private. Ask the user to get access from Jack and to check that `git clone https://github.com/huyjack178/myclaudecode` works for them, then repeat this step.

To get later updates, the user runs `/plugin marketplace update myclaudecode`.

If an old manual copy exists at `~/.claude/skills/delegate-to-light-model`, tell the user, and remove it only after they agree. Otherwise the skill loads twice.

## 3. Create the key file

Create the file with a placeholder, readable only by the user:

```bash
mkdir -p ~/.config/llm-proxy
umask 077
[ -f ~/.config/llm-proxy/light_model.env ] || printf 'LIGHT_MODEL_PROXY_URL=https://llm-proxy.cenario.ai\nLIGHT_MODEL_PROXY_KEY=PASTE_YOUR_KEY_HERE\n' > ~/.config/llm-proxy/light_model.env
chmod 600 ~/.config/llm-proxy/light_model.env
```

Then tell the user exactly this, and wait for them to confirm:

> Open `~/.config/llm-proxy/light_model.env` in your editor, replace `PASTE_YOUR_KEY_HERE` with your personal LiteLLM virtual key, and save it. If you don't have a key, ask Jack for one: it is scoped to `claude-haiku-5-5` with a spending cap. Don't paste the key into this chat.

Do not read or print the file after the user fills it in.

## 4. Verify

Find the installed skill folder. The expected result is one path ending in `delegate-to-light-model`:

```bash
SKILL_DIR="$(dirname "$(dirname "$(find ~/.claude/plugins -path '*delegate-to-light-model/scripts/ask_light_model.py' | head -1)")")"
echo "$SKILL_DIR"
```

Run each check and report the result. Report the model list and the model's replies, never the key.

1. Check which models the key can use. The expected result is a list that includes `claude-haiku-5-5`:

   ```bash
   python3 - <<'PY'
   import json, pathlib, urllib.request
   env = dict(l.split("=", 1) for l in pathlib.Path.home().joinpath(".config/llm-proxy/light_model.env").read_text().splitlines() if "=" in l)
   req = urllib.request.Request(env["LIGHT_MODEL_PROXY_URL"].rstrip("/") + "/v1/models", headers={"Authorization": "Bearer " + env["LIGHT_MODEL_PROXY_KEY"]})
   print([m["id"] for m in json.load(urllib.request.urlopen(req, timeout=30))["data"]])
   PY
   ```

2. Test ask mode. The expected result is a one-line `is_even` function, with a token-usage line on stderr:

   ```bash
   python3 "$SKILL_DIR/scripts/ask_light_model.py" "Write a one-line Python function is_even(n). Reply with code only." </dev/null
   ```

3. Test agent mode in a throwaway folder. The expected result is that `calc.py` ends with `return a + b`:

   ```bash
   mkdir -p /tmp/light-model-test && cd /tmp/light-model-test
   printf 'def add(a, b):\n    return a - b\n' > calc.py
   bash "$SKILL_DIR/scripts/light_model_agent.sh" "calc.py has a bug: add() subtracts. Fix it so add returns a + b. Edit the file, then reply with one sentence." --max-turns 6
   cat calc.py
   ```

   During this run, a warning that claude.ai connectors are disabled is expected and harmless.

If a check fails, use this table:

| Error | Fix |
|---|---|
| `SKILL_DIR` is empty | The plugin is not installed. Repeat step 2. |
| `must be set` (exit 2) | The key file is missing, or the placeholder is still in it |
| `HTTP 401` | The key is wrong or was revoked. Ask Jack for a new one. |
| `HTTP 400` naming the model | The key does not allow `claude-haiku-5-5`. Ask Jack to add it. |

## 5. Finish

Tell the user that setup is done, and that the skill loads in new Claude Code sessions, so they should restart Claude Code. Give them these example requests:

- "use the light model to draft unit tests for `<file>`"
- "ask the light model for a second opinion on this function"
- "have the light model fix the lint errors in `<folder>`"
