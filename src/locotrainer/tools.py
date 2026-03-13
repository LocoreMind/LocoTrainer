"""Tool executor — Read, Grep, Glob, Write, Bash.

Ported from agent_qa_synth.py with minimal changes.
Write tool redirects all output to the configured output directory.
"""

import subprocess
from pathlib import Path
from typing import Any


class ToolExecutor:
    def __init__(self, base_path: Path, output_dir: Path):
        self.base_path = base_path.resolve()
        self.output_dir = output_dir.resolve()

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> str:
        method = f"_execute_{tool_name.lower()}"
        if hasattr(self, method):
            try:
                return getattr(self, method)(arguments)
            except Exception as e:
                return f"Error executing {tool_name}: {e}"
        # Fallback: if tool_name looks like a command, treat as Bash
        if tool_name.startswith(("cat ", "ls ", "grep ", "find ")):
            return self._execute_bash({"command": tool_name})
        return f"Tool {tool_name} not implemented. Available tools: Read, Grep, Glob, Write, Bash"

    def _resolve(self, file_path: str) -> Path:
        p = Path(file_path)
        if not p.is_absolute():
            return self.base_path / p
        return p

    # ── Read ──────────────────────────────────────────────────────────────

    def _execute_read(self, args: dict[str, Any]) -> str:
        file_path = self._resolve(args.get("file_path") or args.get("file", ""))
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
            offset = args.get("offset", 0)
            limit = args.get("limit", len(lines))
            lines = lines[offset: offset + limit]
            start = offset + 1
            numbered = [f"{start + i:6d}\u2192{line}" for i, line in enumerate(lines)]
            output = "\n".join(numbered)
            if len(output) > 80000:
                output = output[:80000] + "\n... (truncated)"
            return output
        except FileNotFoundError:
            return f"Error: File not found: {file_path}"
        except Exception as e:
            return f"Error reading file: {e}"

    # ── Grep ──────────────────────────────────────────────────────────────

    def _execute_grep(self, args: dict[str, Any]) -> str:
        pattern = args["pattern"]
        path = self._resolve(args.get("path") or args.get("search_path") or args.get("output_dir") or ".")
        try:
            cmd = ["grep", "-r"]
            output_mode = args.get("output_mode", "files_with_matches")
            if output_mode == "content" and args.get("-n", True):
                cmd.append("-n")
            if args.get("-i"):
                cmd.append("-i")
            context = args.get("context") or args.get("-C")
            if context and output_mode == "content":
                cmd.extend(["-C", str(context)])
            if args.get("glob"):
                cmd.extend(["--include", args["glob"]])
            cmd.extend([pattern, str(path)])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            output = result.stdout
            if not output:
                return f"No matches found for pattern: {pattern}"

            if output_mode == "files_with_matches":
                files = set()
                for line in output.split("\n"):
                    if ":" in line:
                        files.add(line.split(":")[0])
                output = "\n".join(sorted(files))
            elif output_mode == "count":
                output = f"Found {len(output.strip().splitlines())} matches"

            head_limit = args.get("head_limit", 0)
            if head_limit > 0:
                output = "\n".join(output.split("\n")[:head_limit])

            if len(output) > 50000:
                output = output[:50000] + "\n... (truncated)"
            return output
        except Exception as e:
            return f"Error executing grep: {e}"

    # ── Glob ──────────────────────────────────────────────────────────────

    def _execute_glob(self, args: dict[str, Any]) -> str:
        pattern = args["pattern"]
        path = self._resolve(args.get("path", "."))
        try:
            matches = sorted(path.rglob(pattern))
            if not matches:
                return f"No files found matching pattern: {pattern}"
            return "\n".join(str(m) for m in matches[:100])
        except Exception as e:
            return f"Error executing glob: {e}"

    # ── Write ─────────────────────────────────────────────────────────────

    def _execute_write(self, args: dict[str, Any]) -> str:
        raw_path = args.get("file_path") or args.get("file", "")
        fname = Path(raw_path).name
        file_path = self.output_dir / fname
        content = args.get("content") or args.get("data", "")
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding="utf-8")
            return f"File written successfully: {file_path}"
        except Exception as e:
            return f"Error writing file: {e}"

    # ── Bash ──────────────────────────────────────────────────────────────

    def _execute_bash(self, args: dict[str, Any]) -> str:
        command = args["command"]
        try:
            result = subprocess.run(
                command, shell=True, capture_output=True, text=True,
                timeout=60, cwd=str(self.base_path),
            )
            output = result.stdout
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"
            return output or "(no output)"
        except Exception as e:
            return f"Error executing bash: {e}"
