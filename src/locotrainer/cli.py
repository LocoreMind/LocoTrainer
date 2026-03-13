"""CLI entry point — `locotrainer run`."""

import json
import time
from collections import Counter
from pathlib import Path

import click

from .agent import run_agent
from .config import Config
from .repo import ensure_repo


def build_user_query(query: str, codebase: str, output_dir: str) -> str:
    """Wrap the raw user query with explicit absolute paths for codebase and output."""
    codebase_abs = str(Path(codebase).resolve())
    output_abs = str((Path(output_dir) / "output.md").resolve())
    return (
        f"{query}\n\n"
        f"Analyze the codebase at {codebase_abs} and "
        f"save your findings as a well-structured markdown document to {output_abs}."
    )


@click.group()
@click.version_option()
def main():
    """LocoTrainer — lightweight code agent for codebase analysis."""


@main.command()
@click.option("--query", "-q", required=True, help="The question or task for the agent.")
@click.option("--codebase", "-c", default=None, help="Path to codebase to analyze. Default: auto-clone ms-swift.")
@click.option("--output", "-o", default=None, help="Output directory. Overrides .env.")
@click.option("--model", "-m", default=None, help="Model name. Overrides .env.")
@click.option("--api-key", default=None, help="API key. Overrides .env.")
@click.option("--base-url", default=None, help="API base URL. Overrides .env.")
@click.option("--max-turns", default=None, type=int, help="Max conversation turns.")
@click.option("--env-file", default=None, help="Path to .env file.")
@click.option("--save-trajectory", is_flag=True, default=True, help="Save full trajectory JSON.")
@click.option("--quiet", is_flag=True, help="Suppress verbose output.")
def run(query, codebase, output, model, api_key, base_url, max_turns, env_file, save_trajectory, quiet):
    """Run the agent on a query against a codebase."""
    config = Config.from_env(env_file)

    # CLI overrides
    if output:
        config.output_dir = output
    if model:
        config.model = model
    if api_key:
        config.api_key = api_key
    if base_url:
        config.base_url = base_url
    if max_turns:
        config.max_turns = max_turns

    # Resolve codebase: CLI flag > .env > auto-clone ms-swift
    if codebase:
        config.codebase = codebase
    elif config.codebase == ".":
        # No codebase configured — auto-clone ms-swift
        repo_path = ensure_repo()
        config.codebase = str(repo_path)

    if not config.api_key:
        raise click.ClickException(
            "No API key found. Set LOCOTRAINER_API_KEY or OPENAI_API_KEY in .env, "
            "or pass --api-key."
        )

    # Ensure output dir exists
    Path(config.output_dir).mkdir(parents=True, exist_ok=True)

    # Wrap query with absolute paths for codebase and output
    full_query = build_user_query(query, config.codebase, config.output_dir)

    t0 = time.time()
    result = run_agent(full_query, config, verbose=not quiet)
    elapsed = time.time() - t0

    # Summary
    click.echo(f"\n{'='*80}")
    click.echo("Summary")
    click.echo(f"{'='*80}")
    click.echo(f"Total turns: {result['total_turns']}")
    click.echo(f"Total tool calls: {result['total_tool_calls']}")
    click.echo(f"Elapsed: {elapsed:.1f}s")

    tool_counter = Counter(tc["tool"] for tc in result["tool_calls"])
    for tool, count in tool_counter.most_common():
        click.echo(f"  {tool}: {count}")

    # Check if output.md was created
    output_md = Path(config.output_dir) / "output.md"
    if output_md.exists():
        click.echo(f"\nReport saved: {output_md}")

    # Save trajectory
    if save_trajectory:
        traj_path = Path(config.output_dir) / "trajectory.json"
        with open(traj_path, "w", encoding="utf-8") as f:
            json.dump({
                "user_query": query,
                "model": config.model,
                "total_turns": result["total_turns"],
                "total_tool_calls": result["total_tool_calls"],
                "tool_calls": result["tool_calls"],
                "messages": result["messages"],
                "elapsed_seconds": elapsed,
            }, f, ensure_ascii=False, indent=2)
        click.echo(f"Trajectory saved: {traj_path}")

    # Print final response
    click.echo(f"\n{'='*80}")
    click.echo("Final Response")
    click.echo(f"{'='*80}")
    click.echo(result["final_response"])
