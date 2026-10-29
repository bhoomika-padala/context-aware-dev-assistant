
import json
import os
import re
import time
from dataclasses import dataclass, field

from dotenv import load_dotenv

import config

load_dotenv()
_client = None


@dataclass
class ToolCall:
    id: str
    name: str
    args: dict


@dataclass
class LLMResponse:
    text: str = ""
    tool_calls: list = field(default_factory=list)
    tool_error: str = ""


def _get_client():
    global _client
    if _client is None:
        from groq import Groq
        _client = Groq(api_key=os.environ["GROQ_API_KEY"])
    return _client


def _provider_tools(tools):
    # neutral {name, description, parameters} -> Chat Completions format
    return [{"type": "function",
             "function": {"name": t["name"], "description": t["description"],
                          "parameters": t["parameters"]}} for t in tools]


def assistant_message(resp):
    """History entry for a model turn (keeps tool calls so results can be matched)."""
    msg = {"role": "assistant",
           "content": resp.text or (None if resp.tool_calls else "")}
    if resp.tool_calls:
        msg["tool_calls"] = [
            {"id": c.id, "type": "function",
             "function": {"name": c.name, "arguments": json.dumps(c.args)}}
            for c in resp.tool_calls]
    return msg


def tool_result_message(call_id, content):
    return {"role": "tool", "tool_call_id": call_id, "content": str(content)}


def _with_retry(fn):
    for attempt in range(config.LLM_RETRIES):
        try:
            return fn()
        except Exception as e:
            transient = (getattr(e, "status_code", None) in (429, 500, 502, 503)
                         or type(e).__name__ in ("RateLimitError", "APIConnectionError",
                                                 "InternalServerError"))
            if not transient or attempt == config.LLM_RETRIES - 1:
                raise
            time.sleep(2 ** attempt * 2)


def _parse(raw):
    msg = raw.choices[0].message
    calls = []
    for c in (getattr(msg, "tool_calls", None) or []):
        try:
            args = json.loads(c.function.arguments or "{}")
            if not isinstance(args, dict):
                raise ValueError("arguments not an object")
        except ValueError:
            args = {"_parse_error": c.function.arguments}
        calls.append(ToolCall(c.id, c.function.name, args))
    return LLMResponse(text=msg.content or "", tool_calls=calls)


def chat(system, messages, tools=None, json_mode=False, max_tokens=None, temperature=0.0):
    """The only function the rest of the project uses to talk to a model."""
    kwargs = dict(
        model=config.LLM_MODEL,
        messages=[{"role": "system", "content": system}] + list(messages),
        temperature=temperature,
        max_completion_tokens=max_tokens or config.LLM_MAX_TOKENS,
    )
    if tools:
        kwargs["tools"] = _provider_tools(tools)
        kwargs["tool_choice"] = "auto"
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}
    if config.LLM_REASONING_EFFORT:
        kwargs["reasoning_effort"] = config.LLM_REASONING_EFFORT

    try:
        raw = _with_retry(lambda: _get_client().chat.completions.create(**kwargs))
    except Exception as e:
        body = getattr(e, "body", None) or {}
        err = body.get("error", body) if isinstance(body, dict) else {}

        if (getattr(e, "status_code", None) == 400
                and err.get("code") == "tool_use_failed"):
            return LLMResponse(
                text="",
                tool_calls=[],
                tool_error=err.get("message", "invalid tool call")
            )
        raise

    return _parse(raw)


def parse_json(text):
    """Tolerant JSON extraction: strips code fences, finds the outer object."""
    text = (text or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text, flags=re.I).strip()
    try:
        return json.loads(text)
    except ValueError:
        pass
    start, end = text.find("{"), text.rfind("}")
    if start != -1 and end > start:
        return json.loads(text[start:end + 1])
    raise ValueError("no JSON object found")
