"""Run the eval scenarios with Claude Code in headless mode on a cheap model and check the results.

Usage (from the skill root):
    python evals/run_evals.py                  # with the skill installed (GREEN run)
    python evals/run_evals.py --no-skill       # baseline without the skill (RED run)
    python evals/run_evals.py --only E1,F1
Requires the `claude` CLI (Claude Code) installed and logged in.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL = HERE.parent
sys.path.insert(0, str(HERE))

from check import check_scenario  # noqa: E402

IGNORE = shutil.ignore_patterns(".git", ".venv", "evals", "tests", "docs", "__pycache__", ".pytest_cache", "wiki-studies")
TOOLS = ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]


def ask(prompt: str, cwd: Path, model: str, resume: str | None) -> dict:
    command = ["claude", "-p", prompt, "--model", model, "--output-format", "json", "--max-turns", "40", "--allowedTools", *TOOLS]
    if resume:
        command += ["--resume", resume]
    started = time.time()
    proc = subprocess.run(command, cwd=cwd, capture_output=True, text=True, timeout=1500)
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        data = {"result": proc.stdout + proc.stderr}
    data["seconds"] = round(time.time() - started)
    return data


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="claude-haiku-4-5-20251001")
    parser.add_argument("--no-skill", action="store_true")
    parser.add_argument("--only", default="")
    args = parser.parse_args()
    only = set(filter(None, args.only.split(",")))
    root = HERE / "workdir"
    sessions: dict[str, tuple[str | None, Path]] = {}
    rows = []
    for scenario in json.loads((HERE / "scenarios.json").read_text(encoding="utf-8")):
        sid = scenario["id"]
        if only and sid not in only:
            continue
        workdir = root / sid
        if workdir.exists():
            shutil.rmtree(workdir)
        if "after" in scenario:
            if scenario["after"] not in sessions:
                rows.append((sid, "SKIP", f"run {scenario['after']} first", 0, None))
                continue
            session, parent_dir = sessions[scenario["after"]]
            data = ask(scenario["prompt"], parent_dir, args.model, session)
            shutil.copytree(parent_dir, workdir, ignore=shutil.ignore_patterns(".claude"))
        else:
            (workdir / ".claude" / "skills").mkdir(parents=True)
            if not args.no_skill:
                shutil.copytree(SKILL, workdir / ".claude" / "skills" / SKILL.name, ignore=IGNORE)
            data = ask(scenario["prompt"], workdir, args.model, None)
            sessions[sid] = (data.get("session_id"), workdir)
        (workdir / "answer.md").write_text(data.get("result", ""), encoding="utf-8")
        failures = check_scenario(scenario, workdir)
        rows.append((sid, "FAIL" if failures else "PASS", "; ".join(failures), data["seconds"], data.get("total_cost_usd")))
    label = "baseline-no-skill" if args.no_skill else "with-skill"
    stamp = datetime.now().strftime("%Y%m%d-%H%M")
    lines = [f"# Eval run {stamp} · {label} · model {args.model}", "",
             "| scenario | result | seconds | cost, $ | details |", "|---|---|---|---|---|"]
    lines += [f"| {sid} | {res} | {sec} | {cost if cost is not None else '—'} | {details} |" for sid, res, details, sec, cost in rows]
    out = HERE / "results" / f"{stamp}-{label}.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    return 0 if rows and all(r[1] == "PASS" for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
