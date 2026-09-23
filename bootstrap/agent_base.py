"""Conflict-aware user baseline installer. Python 3.11+, standard library only."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib

ROOT = Path(__file__).resolve().parents[1]
MANAGED = {"": ("model", "model_reasoning_effort"), "agents": (
    "enabled", "max_concurrent_threads_per_session", "default_subagent_model",
    "default_subagent_reasoning_effort")}
IGNORE = {".git", "__pycache__", ".tmp", ".venv"}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def present(path):
    return os.path.lexists(path)


def tree_hash(path):
    digest = hashlib.sha256()
    for p in sorted(Path(path).rglob("*")):
        if p.is_file() and not any(x in IGNORE for x in p.relative_to(path).parts):
            digest.update(p.relative_to(path).as_posix().encode())
            digest.update(p.read_bytes())
    return digest.hexdigest()


def linked_to(dest, source):
    return present(dest) and dest.resolve() == source.resolve()


def desired():
    return tomllib.loads((ROOT / "profiles/codex/config.toml").read_text())


def value(data, section, key):
    return data.get(section, {}).get(key) if section else data.get(key)


def merge_config(text, keep=False):
    current = tomllib.loads(text)
    lines = text.splitlines(keepends=True)
    wanted = desired()
    for section, keys in MANAGED.items():
        for key in keys:
            target = value(wanted, section, key)
            existing = value(current, section, key)
            if keep and existing is not None and existing != target:
                continue
            start, end = 0, len(lines)
            if section:
                matches = [i for i, l in enumerate(lines) if l.strip() == f"[{section}]"]
                if not matches:
                    if lines and not lines[-1].endswith("\n"):
                        lines[-1] += "\n"
                    lines.extend(["\n", f"[{section}]\n"])
                    start = len(lines)
                else:
                    start = matches[0] + 1
                end = next((i for i in range(start, len(lines)) if lines[i].lstrip().startswith("[")), len(lines))
            else:
                end = next((i for i, l in enumerate(lines) if l.lstrip().startswith("[")), len(lines))
            new_line = f"{key} = {json.dumps(target)}\n"
            matches = [i for i in range(start, end) if re.match(rf"\s*{key}\s*=", lines[i])]
            if matches:
                lines[matches[0]] = new_line
            else:
                lines.insert(end, new_line)
    output = "".join(lines)
    after = tomllib.loads(output)
    # Prove every unmanaged parsed value survived. Preserve textual content except managed lines.
    for data in (current, after):
        for section, keys in MANAGED.items():
            obj = data.get(section, {}) if section else data
            for key in keys:
                obj.pop(key, None)
            if section and data.get(section) == {}:
                data.pop(section)
    if current != after:
        raise ValueError("Merge would alter unmanaged configuration")
    return output


def locations(args):
    home = Path(args.home).expanduser().resolve() if args.home else Path.home().resolve()
    codex = Path(args.codex_home or os.environ.get("CODEX_HOME") or home / ".codex").expanduser().resolve()
    if codex == Path(codex.anchor) or home == Path(home.anchor):
        raise ValueError("Refusing filesystem-root installation")
    return home, codex, home / ".agents/skills/ui-ux"


def loader(codex):
    return ("# Agent-base managed loader\n\nRead `" +
            (codex / "agent-base/profiles/codex/AGENTS.md").as_posix() +
            "` once before substantive work. It routes the reusable user baseline.\n"
            "Applicable project instructions and design take precedence.\n")


def inspect(args):
    home, codex, skill = locations(args)
    cfg = codex / "config.toml"
    instructions = codex / "AGENTS.md"
    data = tomllib.loads(cfg.read_text(encoding="utf-8-sig")) if cfg.exists() else {}
    conflicts, inventory = [], []
    seen = set()
    for name in ("AGENTS.override.md", "agents.md", "agent.md", "AGENT.md"):
        p = codex / name
        identity = os.path.normcase(str(p))
        if identity == os.path.normcase(str(instructions)) or identity in seen:
            continue
        seen.add(identity)
        if present(p):
            conflicts.append(f"C: alternate/override instruction file needs review: {p}")
    for d in (codex, home / ".agents"):
        if d.exists():
            inventory.extend(str(p) for p in d.iterdir() if "design" in p.name.lower())
    for d in (home / ".agents/skills", codex / "skills"):
        if d.exists():
            inventory.extend(str(p) for p in d.iterdir() if p.is_dir())
    for dest, source in ((codex / "agent-base", ROOT), (skill, ROOT / "skills/ui-ux")):
        if present(dest) and not linked_to(dest, source):
            if not (args.copy and dest.is_dir() and tree_hash(dest) == tree_hash(source)):
                conflicts.append(f"C: occupied installation path: {dest}")
    legacy_skill = codex / "skills/ui-ux"
    if present(legacy_skill) and not linked_to(legacy_skill, ROOT / "skills/ui-ux"):
        conflicts.append(f"C: another global ui-ux skill may be shadowed: {legacy_skill}")
    if cfg.is_symlink():
        conflicts.append(f"C: config.toml is externally linked; resolve ownership first: {cfg}")
    accepted = (instructions.exists() and (
        instructions.read_text(encoding="utf-8-sig") == loader(codex) or
        linked_to(instructions, ROOT / "profiles/codex/AGENTS.md")))
    if args.keep_instructions and not instructions.is_file():
        conflicts.append("C: cannot keep a missing/non-file global instruction entry")
    if present(instructions) and not accepted and not args.keep_instructions:
        if not instructions.is_file() or sha(instructions) != args.reviewed_instructions_sha256:
            conflicts.append("C: existing AGENTS.md needs semantic review; keep, use baseline or custom merge")
    changes = []
    for section, keys in MANAGED.items():
        for key in keys:
            before, after = value(data, section, key), value(desired(), section, key)
            if before != after:
                label = f"{section + '.' if section else ''}{key}"
                changes.append({"key": label, "existing": before, "baseline": after,
                                "class": "B" if before is None else "C"})
                if before is not None and args.config_resolution == "stop":
                    conflicts.append(f"C: {label}: {before!r} -> {after!r}; choose keep/baseline/custom")
    return {"os": sys.platform, "provider": args.provider, "home": str(home),
            "codex_home": str(codex), "skill": str(skill), "existing_inventory": inventory,
            "instructions_sha256": sha(instructions) if instructions.is_file() else None,
            "config_changes": changes, "conflicts": conflicts}


def backup(path, codex):
    if not present(path):
        return
    folder = codex / "agent-base-backups" / time.strftime("%Y%m%d-%H%M%S")
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    target = folder / (path.name + "-" + str(time.time_ns()))
    shutil.copy2(path, target)
    if os.name != "nt":
        target.chmod(0o600)


def atomic_write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=".agent-base-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def directory_link(dest, source, copy=False):
    if present(dest):
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    if copy:
        shutil.copytree(source, dest, ignore=shutil.ignore_patterns(*IGNORE))
    elif os.name == "nt":
        quote = lambda p: "'" + str(p).replace("'", "''") + "'"
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        f"New-Item -ItemType Junction -Path {quote(dest)} -Target {quote(source)} -ErrorAction Stop | Out-Null"],
                       check=True, stdout=subprocess.DEVNULL)
    else:
        dest.symlink_to(source, target_is_directory=True)


def repo_validate():
    required = ("AGENTS.md", "BOOTSTRAP.md", "governance/core.md", "governance/workers.md",
                "profiles/codex/AGENTS.md", "profiles/codex/config.toml", "profiles/codex/routing.md",
                "design/README.md", "design/visual.md", "design/operations.md", "skills/ui-ux/SKILL.md")
    for name in required:
        if not (ROOT / name).is_file():
            raise ValueError(f"Missing repository file: {name}")
    settings = desired()
    if set(settings) != {"model", "model_reasoning_effort", "agents"}:
        raise ValueError("Unexpected provider defaults; feature flags are not managed")
    for key, val in settings["agents"].items():
        if key not in MANAGED["agents"] or "terra" in str(val).lower():
            raise ValueError("Unexpected/forbidden worker default")
    if settings["model"] != "gpt-6-sol" or settings["model_reasoning_effort"] != "medium":
        raise ValueError("Default root must be Sol/Medium")
    skill = (ROOT / "skills/ui-ux/SKILL.md").read_text()
    if not skill.startswith("---\nname: ui-ux\ndescription:"):
        raise ValueError("Invalid skill metadata")
    print("Repository validation PASS")


def validate(args):
    repo_validate()
    if args.repo_only:
        return
    home, codex, skill = locations(args)
    state_path = codex / "agent-base-install.json"
    state = json.loads(state_path.read_text())
    copy = state["mode"] == "copy"
    for dest, source in ((codex / "agent-base", ROOT), (skill, ROOT / "skills/ui-ux")):
        if not (tree_hash(dest) == tree_hash(source) if copy else linked_to(dest, source)):
            raise ValueError(f"Missing/drifted installation: {dest}")
    p = codex / "AGENTS.md"
    if state.get("kept_instructions"):
        if sha(p) != state["kept_instructions"]:
            raise ValueError("User-kept instruction entry changed; inspect and rerun setup after review")
        print("User kept existing instructions; automatic baseline activation depends on their contents")
    elif not (linked_to(p, ROOT / "profiles/codex/AGENTS.md") or p.read_text() == loader(codex)):
        raise ValueError("Global instruction entry point drifted")
    data = tomllib.loads((codex / "config.toml").read_text(encoding="utf-8-sig"))
    deviations = [f"{s}.{k}".lstrip(".") for s, keys in MANAGED.items() for k in keys
                  if value(data, s, k) != value(desired(), s, k)]
    if deviations and not args.config_resolution == "keep":
        raise ValueError("Defaults differ: " + ", ".join(deviations))
    if deviations:
        print("User-kept departures: " + ", ".join(deviations))
    print("Installed validation PASS; " + ("COPY snapshot; updates need explicit refresh" if copy else "linked policies/skill"))


def setup(args):
    repo_validate()
    report = inspect(args)
    if report["conflicts"]:
        print(json.dumps(report, indent=2))
        raise ValueError("Unresolved conflicts; no installation writes performed")
    home, codex, skill = locations(args)
    cfg = codex / "config.toml"
    old = cfg.read_text(encoding="utf-8-sig") if cfg.exists() else ""
    updated = merge_config(old, args.config_resolution == "keep")
    codex.mkdir(parents=True, exist_ok=True)
    directory_link(codex / "agent-base", ROOT, args.copy)
    directory_link(skill, ROOT / "skills/ui-ux", args.copy)
    p = codex / "AGENTS.md"
    correct = linked_to(p, ROOT / "profiles/codex/AGENTS.md") or (p.is_file() and p.read_text() == loader(codex))
    if not correct and not args.keep_instructions:
        backup(p, codex)
        if os.name != "nt" and not args.copy:
            temporary_link = codex / (".agent-base-link-" + str(time.time_ns()))
            try:
                temporary_link.symlink_to(ROOT / "profiles/codex/AGENTS.md")
                os.replace(temporary_link, p)
            finally:
                if present(temporary_link):
                    temporary_link.unlink()
        else:
            atomic_write(p, loader(codex))
    if old != updated:
        backup(cfg, codex)
        atomic_write(cfg, updated)
    atomic_write(codex / "agent-base-install.json", json.dumps({"mode": "copy" if args.copy else "linked",
                  "repository": str(ROOT), "provider": "codex",
                  "kept_instructions": sha(p) if args.keep_instructions else None}, indent=2) + "\n")
    validate(args)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("inspect", "setup", "validate", "update"))
    parser.add_argument("--provider", default="codex" if os.environ.get("CODEX_THREAD_ID") else None)
    parser.add_argument("--home")
    parser.add_argument("--codex-home")
    parser.add_argument("--repo-only", action="store_true")
    parser.add_argument("--copy", action="store_true", help="Explicit opt-in: managed snapshot, not auto-synced")
    parser.add_argument("--config-resolution", choices=("stop", "baseline", "keep"), default="stop")
    parser.add_argument("--reviewed-instructions-sha256", default="")
    parser.add_argument("--keep-instructions", action="store_true", help="Explicit user choice: preserve the existing entry; report incomplete baseline activation")
    parser.add_argument("--reviewed-update")
    args = parser.parse_args(argv)
    if args.repo_only and args.command == "validate":
        repo_validate()
        return
    if args.provider != "codex":
        raise ValueError("No provider profile. Ask the user for model/reasoning mappings and verify installation paths; see BOOTSTRAP.md")
    if args.command == "inspect":
        print(json.dumps(inspect(args), indent=2))
    elif args.command == "validate":
        validate(args)
    elif args.command == "setup":
        setup(args)
    else:
        git = lambda *a: subprocess.check_output(["git", "-C", str(ROOT), *a], text=True).strip()
        if git("status", "--porcelain"):
            raise ValueError("Update requires a clean checkout")
        git("fetch")
        upstream = git("rev-parse", "@{u}")
        if args.reviewed_update != upstream and git("rev-parse", "HEAD") != upstream:
            print(git("diff", "HEAD", upstream, "--stat"))
            raise ValueError(f"Review git diff HEAD {upstream}; then pass --reviewed-update {upstream}")
        git("merge", "--ff-only", upstream)
        # Re-enter the reviewed installer version after the checkout changes.
        forwarded = list(argv if argv is not None else sys.argv[1:])
        forwarded[0] = "setup"
        subprocess.run([sys.executable, "-B", str(ROOT / "bootstrap/agent_base.py"), *forwarded], check=True)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"agent-base: {error}", file=sys.stderr)
        sys.exit(2)
