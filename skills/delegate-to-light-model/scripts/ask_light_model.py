#!/usr/bin/env python3
import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


class LightModelAsker:
    _DEFAULT_MODEL = "claude-haiku-5-5"
    _DEFAULT_MAX_TOKENS = 8192
    _TIMEOUT_SECONDS = 600

    def __init__(self, proxy_url: str, proxy_key: str) -> None:
        self._endpoint = proxy_url.rstrip("/") + "/v1/chat/completions"
        self._proxy_key = proxy_key

    def run(self, argv: list[str]) -> int:
        args = self._parse_args(argv)
        prompt = self._build_prompt(args.prompt, args.file, self._read_stdin())
        reply = self._ask(prompt, args.system, args.model, args.max_tokens)
        print(reply["text"])
        print(f"[{args.model}] in={reply['input_tokens']} out={reply['output_tokens']}", file=sys.stderr)
        return 0

    def _parse_args(self, argv: list[str]) -> argparse.Namespace:
        parser = argparse.ArgumentParser(description="Send one prompt to a model on the LLM proxy and print the reply.")
        parser.add_argument("prompt", help="The task or question.")
        parser.add_argument("-f", "--file", action="append", default=[], help="Attach a file's contents. Repeatable.")
        parser.add_argument("-s", "--system", default=None, help="Optional system prompt.")
        parser.add_argument("-m", "--model", default=self._DEFAULT_MODEL, help="Proxy model_name.")
        parser.add_argument("--max-tokens", type=int, default=self._DEFAULT_MAX_TOKENS)
        return parser.parse_args(argv)

    def _read_stdin(self) -> str:
        if sys.stdin.isatty():
            return ""
        return sys.stdin.read()

    def _build_prompt(self, prompt: str, file_paths: list[str], stdin_text: str) -> str:
        sections = [prompt]
        for file_path in file_paths:
            sections.append(f"<file path=\"{file_path}\">\n{Path(file_path).read_text()}\n</file>")
        if stdin_text.strip():
            sections.append(f"<stdin>\n{stdin_text}\n</stdin>")
        return "\n\n".join(sections)

    def _ask(self, prompt: str, system: str | None, model: str, max_tokens: int) -> dict:
        messages = [{"role": "system", "content": system}] if system else []
        messages.append({"role": "user", "content": prompt})
        body = json.dumps({"model": model, "messages": messages, "max_tokens": max_tokens}).encode()
        request = urllib.request.Request(
            self._endpoint,
            data=body,
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self._proxy_key}"},
        )
        with urllib.request.urlopen(request, timeout=self._TIMEOUT_SECONDS) as response:
            payload = json.load(response)
        usage = payload.get("usage") or {}
        return {
            "text": payload["choices"][0]["message"]["content"] or "",
            "input_tokens": usage.get("prompt_tokens", "?"),
            "output_tokens": usage.get("completion_tokens", "?"),
        }


ENV_FILE = Path.home() / ".config" / "llm-proxy" / "light_model.env"


def load_env_file() -> None:
    if not ENV_FILE.is_file():
        return
    for line in ENV_FILE.read_text().splitlines():
        name, separator, value = line.partition("=")
        if separator and name.strip() and not line.lstrip().startswith("#"):
            os.environ.setdefault(name.strip(), value.strip())


def main() -> int:
    load_env_file()
    proxy_url = os.environ.get("LIGHT_MODEL_PROXY_URL")
    proxy_key = os.environ.get("LIGHT_MODEL_PROXY_KEY")
    if not proxy_url or not proxy_key:
        print(f"LIGHT_MODEL_PROXY_URL and LIGHT_MODEL_PROXY_KEY must be set (env or {ENV_FILE}).", file=sys.stderr)
        return 2
    try:
        return LightModelAsker(proxy_url, proxy_key).run(sys.argv[1:])
    except urllib.error.HTTPError as error:
        print(f"Proxy returned HTTP {error.code}: {error.read().decode(errors='replace')[:500]}", file=sys.stderr)
        return 1
    except urllib.error.URLError as error:
        print(f"Could not reach the proxy: {error.reason}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
