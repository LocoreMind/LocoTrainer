"""Agent loop — drives the LLM ↔ tool-use conversation.

Ported from agent_qa_synth.py. The loop sends user queries to the LLM,
extracts <tool_call> blocks, executes them, and feeds results back until
the LLM stops issuing tool calls or max_turns is reached.
"""

import json
import time
from pathlib import Path
from typing import Any

from openai import OpenAI

from .config import Config
from .prompts import SYSTEM_PROMPT, get_system_reminder
from .tools import ToolExecutor


# ── Tool Call Extraction ─────────────────────────────────────────────────

def extract_tool_calls(text: str) -> list[tuple[dict[str, Any] | None, str]]:
    """Extract tool calls from assistant response.

    Returns list of (parsed_dict_or_None, raw_json_str) tuples.
    If JSON is malformed, parsed is None — caller returns a parse error
    as tool_response so the model can self-correct.
    """
    results = []
    start_tag = "<tool_call>"
    end_tag = "</tool_call>"
    pos = 0
    while True:
        start_idx = text.find(start_tag, pos)
        if start_idx == -1:
            break
        end_idx = text.find(end_tag, start_idx)
        if end_idx == -1:
            break
        inner = text[start_idx + len(start_tag):end_idx].strip()
        try:
            parsed = json.loads(inner)
            if isinstance(parsed, dict) and "name" in parsed:
                results.append((parsed, inner))
            else:
                results.append((None, inner))
        except json.JSONDecodeError:
            results.append((None, inner))
        pos = end_idx + len(end_tag)
    return results


def format_tool_responses(results: list[str]) -> str:
    parts = []
    for result in results:
        parts.append(f"<tool_response>\n{result}\n</tool_response>")
    return "\n".join(parts)


# ── Agent Loop ───────────────────────────────────────────────────────────

def run_agent(
    user_query: str,
    config: Config,
    verbose: bool = True,
) -> dict[str, Any]:
    """Run the agent loop: query → tool calls → responses → repeat.

    Returns a dict with final_response, total_turns, tool_calls, messages, etc.
    """
    client = OpenAI(api_key=config.api_key, base_url=config.base_url)
    executor = ToolExecutor(
        base_path=Path(config.codebase),
        output_dir=Path(config.output_dir),
    )

    if verbose:
        print(f"\n{'='*80}")
        print(f"User Query: {user_query}")
        print(f"Model: {config.model}")
        print(f"Codebase: {config.codebase}")
        print(f"Output: {config.output_dir}")
        print(f"{'='*80}\n")

    # Turn 1: system_reminder + user_query
    first_user_content = user_query
    reminder = get_system_reminder(turn=1)
    if reminder:
        first_user_content = reminder + user_query

    messages: list[dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": first_user_content},
    ]

    all_tool_calls: list[dict[str, Any]] = []

    for turn in range(1, config.max_turns + 1):
        if verbose:
            print(f"\n{'─'*60} Turn {turn} {'─'*60}")

        # Build API kwargs
        api_kwargs: dict[str, Any] = {
            "model": config.model,
            "messages": messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "frequency_penalty": config.frequency_penalty,
            "presence_penalty": config.presence_penalty,
        }
        if config.extra_body:
            api_kwargs["extra_body"] = config.extra_body

        resp = client.chat.completions.create(**api_kwargs)
        response_text = resp.choices[0].message.content or ""

        if verbose:
            preview = response_text[:400] + "..." if len(response_text) > 400 else response_text
            print(f"Assistant ({len(response_text)} chars):\n{preview}\n")

        extracted = extract_tool_calls(response_text)

        if not extracted:
            if verbose:
                print("No tool calls — task completed.")
            return {
                "final_response": response_text,
                "total_turns": turn,
                "total_tool_calls": len(all_tool_calls),
                "tool_calls": all_tool_calls,
                "messages": messages + [{"role": "assistant", "content": response_text}],
            }

        if verbose:
            print(f"Executing {len(extracted)} tool(s):")

        results = []
        for i, (parsed, raw) in enumerate(extracted, 1):
            if parsed is None:
                error_msg = f"Error: malformed tool call JSON. Could not parse:\n{raw[:500]}"
                results.append(error_msg)
                all_tool_calls.append({
                    "turn": turn, "tool": "PARSE_ERROR",
                    "args": {}, "result_length": len(error_msg),
                })
                if verbose:
                    print(f"  [{i}] PARSE_ERROR (malformed JSON)")
            else:
                name = parsed.get("name", "unknown")
                args = parsed.get("arguments", {})
                if verbose:
                    print(f"  [{i}] {name}({json.dumps(args, ensure_ascii=False)[:120]})")
                result = executor.execute(name, args)
                results.append(result)
                all_tool_calls.append({
                    "turn": turn, "tool": name,
                    "args": args, "result_length": len(result),
                })
                if verbose:
                    print(f"       -> {len(result)} chars")

        messages.append({"role": "assistant", "content": response_text})

        # Format tool responses, optionally prepend system reminder
        tool_response_content = format_tool_responses(results)
        next_turn = turn + 1
        reminder = get_system_reminder(next_turn)
        if reminder:
            tool_response_content = reminder + tool_response_content
            if verbose:
                print(f"  Added system reminder for turn {next_turn}")

        messages.append({"role": "user", "content": tool_response_content})

    return {
        "final_response": "Task incomplete: reached maximum turn limit",
        "total_turns": config.max_turns,
        "total_tool_calls": len(all_tool_calls),
        "tool_calls": all_tool_calls,
        "messages": messages,
    }
