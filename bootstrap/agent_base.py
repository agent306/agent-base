"""Install the Codex baseline with scoped ownership and an external rollback journal.

Python 3.11+, standard library only. No command downloads or executes new code.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import tomllib

ROOT = Path(__file__).resolve().parents[1]
MANAGED = {"": ("model", "model_reasoning_effort"), "agents": (
    "enabled", "max_concurrent_threads_per_session", "default_subagent_model",
    "default_subagent_reasoning_effort")}
IGNORE = {".git", "__pycache__", ".tmp", ".venv"}
LEGACY_ROLES = tuple("agent-base-" + x + ".toml" for x in ("judgment", "implementation", "mechanical"))
MANIFEST = "agent-base-install.json"


def present(path):
    return os.path.lexists(path)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read_text(path):
    return Path(path).read_bytes().decode("utf-8-sig")


def desired():
    return tomllib.loads(read_text(ROOT / "profiles/codex/config.toml"))


def value(data, section, key):
    return data.get(section, {}).get(key) if section else data.get(key)


def is_link(path):
    # Junctions are not symlinks on Python 3.11. Never recurse into a reparse point.
    if not present(path):
        return False
    st = path.lstat()
    return path.is_symlink() or bool(getattr(st, "st_file_attributes", 0) & 0x400)


def linked_to(dest, source):
    return is_link(dest) and dest.resolve() == source.resolve()


def within(path, parent):
    return path.resolve().is_relative_to(parent.resolve())


def walk_tree(path, source=False):
    for directory, dirs, files in os.walk(path, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not source or d not in IGNORE)
        yield directory, dirs, files


def tree_files(path, source=False):
    result = {}
    for directory, dirs, files in os.walk(path, followlinks=False):
        dirs[:] = sorted(d for d in dirs if not source or d not in IGNORE)
        for name in dirs + sorted(files):
            p = Path(directory) / name
            if is_link(p):
                raise ValueError(f"Nested links are not supported in managed copies: {p}")
        for name in sorted(files):
            if source and name in IGNORE:
                continue
            p = Path(directory) / name
            result[p.relative_to(path).as_posix()] = base64.b64encode(p.read_bytes()).decode()
    return result


def capture(path, source=False):
    if not present(path):
        return {"kind": "missing"}
    if is_link(path):
        return {"kind": "link", "target": str(path.resolve()), "directory": path.is_dir()}
    if path.is_file():
        return {"kind": "file", "bytes": base64.b64encode(path.read_bytes()).decode()}
    if path.is_dir():
        return {"kind": "directory", "files": tree_files(path, source),
                "directories": sorted(str(Path(d).relative_to(path) / child).replace("\\", "/")
                                      for d, dirs, _ in walk_tree(path, source) for child in dirs)}
    raise ValueError(f"Unsupported filesystem object: {path}")


def fingerprint(state):
    return hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()


def file_state(data):
    return {"kind": "file", "bytes": base64.b64encode(data).decode()}


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=".agent-base-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data.encode() if isinstance(data, str) else data)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def unlink_resource(path):
    if not present(path):
        return
    if is_link(path):
        if os.name == "nt" and path.is_dir():
            path.rmdir()  # Remove junction itself; never its target.
        else:
            path.unlink()
    elif path.is_file():
        path.unlink()
    else:
        # Only a verified owned copy reaches here. Do not use recursive deletion.
        for directory, dirs, files in os.walk(path, topdown=False, followlinks=False):
            for name in files:
                (Path(directory) / name).unlink()
            for name in dirs:
                child = Path(directory) / name
                if is_link(child):
                    raise ValueError(f"Unexpected nested link: {child}")
                child.rmdir()
        path.rmdir()


def directory_link(dest, source):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if os.name == "nt":
        quote = lambda p: "'" + str(p).replace("'", "''") + "'"
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        f"New-Item -ItemType Junction -Path {quote(dest)} -Target {quote(source)} -ErrorAction Stop | Out-Null"],
                       check=True, stdout=subprocess.DEVNULL)
    else:
        dest.symlink_to(source, target_is_directory=True)


def restore(path, state):
    if capture(path) == state:
        return
    unlink_resource(path)
    if state["kind"] == "file":
        atomic_write(path, base64.b64decode(state["bytes"]))
    elif state["kind"] == "link":
        if state["directory"]:
            directory_link(path, Path(state["target"]))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.symlink_to(state["target"])
    elif state["kind"] == "directory":
        path.mkdir(parents=True, exist_ok=True)
        for name in state.get("directories", []):
            (path / name).mkdir(parents=True, exist_ok=True)
        for name, content in state["files"].items():
            atomic_write(path / name, base64.b64decode(content))


def config_slots(text):
    """Locate simple managed scalar assignments; refuse ambiguous TOML spellings."""
    data = tomllib.loads(text.lstrip("\ufeff"))
    lines = text.splitlines(keepends=True)
    section, slots = "", {}
    for index, line in enumerate(lines):
        clean = line.lstrip("\ufeff").strip()
        header = re.match(r'^\[([A-Za-z0-9_.-]+)\]\s*(?:#.*)?$', clean)
        if clean.startswith("["):
            section = header[1] if header else "!unsupported"
        if section in MANAGED:
            for key in MANAGED[section]:
                if re.match(rf'^\s*{re.escape(key)}\s*=', clean):
                    slots[(section, key)] = index
    for section, keys in MANAGED.items():
        for key in keys:
            existing = value(data, section, key)
            if existing is not None and (section, key) not in slots:
                raise ValueError(f"Managed key uses unsupported TOML spelling; custom merge required: {section}.{key}")
            if existing is not None and not isinstance(existing, (str, int, bool)):
                raise ValueError(f"Managed key is not a scalar: {section}.{key}")
    return data, lines, slots


def strip_managed(data):
    data = json.loads(json.dumps(data))
    for section, keys in MANAGED.items():
        obj = data.get(section, {}) if section else data
        if not isinstance(obj, dict):
            raise ValueError(f"Managed table must be a table: {section}")
        for key in keys:
            obj.pop(key, None)
        if section and data.get(section) == {}:
            data.pop(section)
    return data


def merge_config(text, keep=False, targets=None):
    """Change only six scalar lines; preserve unrelated text, BOM and line endings."""
    bom = "\ufeff" if text.startswith("\ufeff") else ""
    text = text.removeprefix("\ufeff")
    original, _, _ = config_slots(text)
    wanted = desired() if targets is None else targets
    newline = "\r\n" if "\r\n" in text else "\n"
    for section, keys in MANAGED.items():
        for key in keys:
            data, lines, slots = config_slots(text)
            target = value(wanted, section, key)
            existing = value(data, section, key)
            if keep and existing is not None:
                continue
            if target == existing:
                continue
            slot = slots.get((section, key))
            if target is None:
                if slot is not None:
                    del lines[slot]
            elif slot is not None:
                # Keep the user's inline comment and existing newline convention.
                old = lines[slot]
                suffix = re.search(r'\s+#.*', old.rstrip("\r\n"))
                comment = suffix[0] if suffix else ""
                prefix = "\ufeff" if old.startswith("\ufeff") else ""
                lines[slot] = f'{prefix}{key} = {json.dumps(target)}{comment}{newline}'
            else:
                headers = [(i, re.match(r'^\s*\[([^\]]+)\]', l)) for i, l in enumerate(lines)]
                if section:
                    match = next((i for i, m in headers if m and m[1] == section), None)
                    if match is None:
                        if lines and not lines[-1].endswith("\n"):
                            lines[-1] += newline
                        lines.extend([newline, f"[{section}]{newline}"])
                        insert = len(lines)
                    else:
                        insert = next((i for i, m in headers if m and i > match), len(lines))
                else:
                    insert = next((i for i, m in headers if m), len(lines))
                if insert and not lines[insert - 1].endswith("\n"):
                    lines[insert - 1] += newline
                lines.insert(insert, f'{key} = {json.dumps(target)}{newline}')
            text = "".join(lines)
    if strip_managed(tomllib.loads(text.lstrip("\ufeff"))) != strip_managed(original):
        raise ValueError("Merge would alter unmanaged configuration")
    return bom + text


def restore_config(current, before, installed):
    now = tomllib.loads(current.lstrip("\ufeff"))
    original = tomllib.loads(before.lstrip("\ufeff"))
    applied = tomllib.loads(installed.lstrip("\ufeff"))
    targets = json.loads(json.dumps(now))
    for section, keys in MANAGED.items():
        obj = targets.setdefault(section, {}) if section else targets
        for key in keys:
            if value(now, section, key) == value(applied, section, key):
                old = value(original, section, key)
                if old is None:
                    obj.pop(key, None)
                else:
                    obj[key] = old
    return merge_config(current, targets=targets)


def locations(args):
    home = Path(args.home).expanduser().resolve() if args.home else Path.home().resolve()
    codex = Path(args.codex_home or os.environ.get("CODEX_HOME") or home / ".codex").expanduser().resolve()
    if codex == Path(codex.anchor) or home == Path(home.anchor):
        raise ValueError("Refusing filesystem-root installation")
    return home, codex, home / ".agents/skills/ui-ux"


def legacy_loader(codex):
    return ("# Agent-base managed loader\n\nRead `" +
            (codex / "agent-base/profiles/codex/AGENTS.md").as_posix() +
            "` once before substantive work. It routes the reusable user baseline.\n"
            "Applicable project instructions and design take precedence.\n")


def generated(codex):
    text = "<!-- Generated by agent-base; edit the checkout, then run update. -->\n\n"
    text += read_text(ROOT / "governance/core.md").strip() + "\n\n"
    text += read_text(ROOT / "profiles/codex/AGENTS.md").strip() + "\n"
    return text.replace("{{BASE}}", (codex / "agent-base").as_posix()).encode()


def repo_validate():
    required = ("AGENTS.md", "BOOTSTRAP.md", "governance/core.md", "governance/workers.md",
                "profiles/codex/AGENTS.md", "profiles/codex/config.toml", "docs/runtime.md",
                "design/README.md", "skills/ui-ux/SKILL.md")
    for name in required:
        if not (ROOT / name).is_file():
            raise ValueError(f"Missing repository file: {name}")
    expected = {"model": "gpt-6-sol", "model_reasoning_effort": "medium", "agents": {
        "enabled": True, "max_concurrent_threads_per_session": 5,
        "default_subagent_model": "gpt-6-sol", "default_subagent_reasoning_effort": "medium"}}
    if desired() != expected:
        raise ValueError("Provider defaults differ from the approved six scalar settings")
    if list((ROOT / "profiles/codex/agents").glob("*.toml")):
        raise ValueError("Obsolete globally pinned baseline roles remain in the source")
    skill = read_text(ROOT / "skills/ui-ux/SKILL.md").replace("\r\n", "\n")
    if not skill.startswith("---\nname: ui-ux\ndescription:"):
        raise ValueError("Invalid skill metadata")


def git_state():
    def git(*args):
        return subprocess.check_output(["git", "-c", f"safe.directory={ROOT.as_posix()}", "-C", str(ROOT), *args], text=True, stderr=subprocess.DEVNULL).strip()
    try:
        return {"revision": git("rev-parse", "HEAD"), "dirty": bool(git("status", "--porcelain"))}
    except (OSError, subprocess.CalledProcessError):
        return {"revision": None, "dirty": None}


def load_manifest(codex):
    path = codex / MANIFEST
    if is_link(path):
        raise ValueError("Installation manifest must not be a link")
    return json.loads(read_text(path)) if path.is_file() else {}


def allowed_paths(codex, skill):
    return {str(p) for p in (codex / "AGENTS.md", codex / "config.toml",
            codex / MANIFEST, codex / "agent-base", codex / "skills/ui-ux", skill,
            *(codex / "agents" / name for name in LEGACY_ROLES))}


def verify_owned_paths(state, codex, skill):
    if set(state.get("resources", {})) - allowed_paths(codex, skill):
        raise ValueError("Manifest contains resources outside the installer ownership scope")


def profile_digest(data):
    return hashlib.sha256(json.dumps({"selected": data.get("profile"),
        "definition": data.get("profiles", {}).get(data.get("profile"), {})}, sort_keys=True).encode()).hexdigest()


def inspect(args):
    home, codex, skill = locations(args)
    state = load_manifest(codex)
    cfg = codex / "config.toml"
    data = tomllib.loads(read_text(cfg)) if cfg.is_file() else {}
    conflicts, notices = [], []
    verify_owned_paths(state, codex, skill)
    if state and state.get("provider") != "codex":
        conflicts.append("Manifest belongs to another provider")
    if state.get("version", 1) not in (1, 2):
        conflicts.append("Unsupported manifest version")
    if is_link(cfg):
        conflicts.append("config.toml is linked; resolve ownership before mutation")
    if codex.is_dir():
        for path in codex.iterdir():
            if path.name.lower() in ("agents.override.md", "agent.md") or (path.name.lower() == "agents.md" and path.name != "AGENTS.md"):
                conflicts.append(f"Alternate/override global instruction file: {path}")
    if data.get("project_doc_fallback_filenames"):
        notices.append("Configured project fallback instruction filenames: inspect their project-scoped content before attributing behavior")
    if data.get("profiles"):
        notices.append("Configured profiles can override defaults when selected; review them in the launching host")
    if data.get("profile") and (not cfg.is_file() or sha(cfg) != args.reviewed_config_sha256) and state.get("reviewed_profile") != profile_digest(data):
        conflicts.append("Selected profile can override defaults; review exact config and pass --reviewed-config-sha256")
    for name, config in data.get("agents", {}).items():
        if isinstance(config, dict):
            notices.append(f"Custom agent configuration may pin routing: agents.{name}; inspect before selecting that role")
    for path in (codex / "agents").glob("*.toml"):
        if path.name in LEGACY_ROLES and state.get("managed_agents", {}).get(path.name) == sha(path) and not is_link(path):
            continue
        role = tomllib.loads(read_text(path))
        if path.name in LEGACY_ROLES:
            conflicts.append(f"Unowned/modified legacy role: {path}")
        elif any(k in role for k in ("model", "model_reasoning_effort", "config_file")):
            notices.append(f"Custom role model/effort pin: {path}; preserved, inspect before using this role")
    duplicate = codex / "skills/ui-ux"
    if present(duplicate) and not (state and linked_to(duplicate, ROOT / "skills/ui-ux")):
        conflicts.append(f"Duplicate legacy ui-ux registration needs explicit retirement: {duplicate}")
    for path, source in ((codex / "agent-base", ROOT), (skill, ROOT / "skills/ui-ux")):
        if present(path) and not linked_to(path, source):
            digest = state.get("resources", {}).get(str(path))
            if not digest or fingerprint(capture(path)) != digest:
                conflicts.append(f"Occupied or locally modified registration: {path}")
        if present(path) and not path.exists():
            conflicts.append(f"Stale/broken link: {path}")
    instructions = codex / "AGENTS.md"
    if present(instructions):
        current = capture(instructions)
        accepted = (current == file_state(generated(codex)) or
                    fingerprint(current) == state.get("resources", {}).get(str(instructions)) or
                    (state and linked_to(instructions, ROOT / "profiles/codex/AGENTS.md")) or
                    (instructions.is_file() and (sha(instructions) == args.reviewed_instructions_sha256 or
                     (state.get("repository") == str(ROOT) and read_text(instructions).replace("\r\n", "\n") == legacy_loader(codex)))))
        if not accepted:
            conflicts.append(f"Occupied or locally modified global instructions: {instructions}; review diff and choose keep/baseline/custom merge")
    changes = []
    for section, keys in MANAGED.items():
        for key in keys:
            before, after = value(data, section, key), value(desired(), section, key)
            if before != after:
                changes.append({"key": f"{section}.{key}".lstrip("."), "existing": before, "baseline": after})
                owned = state.get("version") == 2 and before == value(state.get("config_values", {}), section, key)
                if before is not None and not owned and args.config_resolution == "stop":
                    conflicts.append(f"Conflicting setting {section}.{key}; choose keep/baseline or custom merge")
    if args.config_resolution == "keep" and changes:
        notices.append("Preserved differing settings; baseline defaults are only partially active")
    return {"os": sys.platform, "environment": "WSL" if os.environ.get("WSL_DISTRO_NAME") or os.environ.get("WSL_INTEROP") else "native",
            "provider": args.provider, "home": str(home), "codex_home": str(codex), "skill": str(skill),
            "checkout": str(ROOT), "git": git_state(), "config_changes": changes,
            "installation_status": state.get("status", "installed" if state else "not_installed"),
            "instructions_sha256": sha(instructions) if instructions.is_file() else None,
            "config_sha256": sha(cfg) if cfg.is_file() else None,
            "instruction_diff_command": "Compare existing AGENTS.md with generated core + Codex adapter before passing its reviewed SHA256.",
            "registrations": [{"path": str(p), "linked": is_link(p), "exists": present(p),
                               "target": str(p.resolve()) if is_link(p) else None}
                              for p in (codex / "agent-base", skill, duplicate)],
            "conflicts": conflicts, "notices": notices,
            "limits": ["Launch overrides, runtime model identity, and project-scoped policy require host/session inspection."]}


def snapshot_root(args, codex, home, existing=None):
    supplied = args.snapshot or existing
    if not supplied:
        raise ValueError("Mutation requires --snapshot outside instruction/skill discovery paths")
    root = Path(supplied).expanduser().resolve()
    if existing and root != Path(existing).resolve():
        raise ValueError("Reuse the original snapshot bundle; do not split installation history")
    for discovered in (codex, home / ".agents", ROOT):
        if within(root, discovered):
            raise ValueError("Snapshot must be outside checkout and instruction/skill discovery paths")
    return root


def transaction(snapshot, changes, metadata):
    folder = snapshot / "installer"
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    numbers = [int(p.stem) for p in folder.glob("*.json") if p.stem.isdigit()]
    path = folder / f"{max(numbers, default=0) + 1:04d}.json"
    journal = {"version": 2, "status": "prepared", "metadata": metadata, "changes": changes}
    atomic_write(path, json.dumps(journal, indent=2) + "\n")
    try:
        for change in changes:
            target = Path(change["path"])
            if capture(target) != change["before"]:
                raise ValueError(f"Resource changed after preflight: {target}")
            restore(target, change["after"])
        journal["status"] = "applied"
        atomic_write(path, json.dumps(journal, indent=2) + "\n")
    except BaseException:
        # Leave a recoverable journal if a platform failure prevents automatic restoration.
        for change in reversed(changes):
            target = Path(change["path"])
            current = capture(target)
            if current == change["after"]:
                restore(target, change["before"])
        journal["status"] = "failed"
        atomic_write(path, json.dumps(journal, indent=2) + "\n")
        raise
    return path


def setup(args):
    repo_validate()
    report = inspect(args)
    home, codex, skill = locations(args)
    state = load_manifest(codex)
    if state.get("status") == "partial_uninstall":
        raise ValueError("PARTIAL uninstall pending; resolve preserved edits and rerun uninstall, or roll back its transaction")
    owned = state.get("resources", {})
    plans, original_owned = [], []
    mode = "copy" if args.copy else state.get("mode", "linked")
    targets = {codex / "AGENTS.md": file_state(generated(codex))}
    for dest, source in ((codex / "agent-base", ROOT), (skill, ROOT / "skills/ui-ux")):
        targets[dest] = capture(source, source=True) if mode == "copy" else {"kind": "link", "target": str(source.resolve()), "directory": True}
    for name in LEGACY_ROLES:
        path = codex / "agents" / name
        if present(path):
            targets[path] = {"kind": "missing"}
    duplicate = codex / "skills/ui-ux"
    if state and linked_to(duplicate, ROOT / "skills/ui-ux"):
        targets[duplicate] = {"kind": "missing"}
    for path, after in targets.items():
        before = capture(path)
        resource_owned = str(path) in owned and fingerprint(before) == owned[str(path)]
        legacy_owned = (path.name in LEGACY_ROLES and before["kind"] == "file" and state.get("managed_agents", {}).get(path.name) == sha(path))
        old_loader = path.name == "AGENTS.md" and before["kind"] == "file" and read_text(path).replace("\r\n", "\n") == legacy_loader(codex) and state.get("repository") == str(ROOT)
        old_link = path.name == "AGENTS.md" and linked_to(path, ROOT / "profiles/codex/AGENTS.md") and bool(state)
        reviewed = path.name == "AGENTS.md" and before["kind"] == "file" and sha(path) == args.reviewed_instructions_sha256
        legacy_registration = (state.get("version", 1) == 1 and state.get("provider") == "codex" and
                               state.get("repository") == str(ROOT) and state.get("mode") == "linked" and
                               ((path == codex / "agent-base" and linked_to(path, ROOT)) or
                                (path == skill and linked_to(path, ROOT / "skills/ui-ux"))))
        legacy_owned = legacy_owned or old_loader or old_link or legacy_registration or (path == duplicate and state and linked_to(path, ROOT / "skills/ui-ux"))
        if legacy_owned:
            original_owned.append(str(path))
        if before == after:
            if state.get("version") != 2:
                plans.append({"path": str(path), "before": before, "after": after})
            continue
        if before["kind"] != "missing" and not (resource_owned or legacy_owned or reviewed):
            report["conflicts"].append(f"Occupied or locally modified resource: {path}; keep existing or review/custom merge")
        if mode == "copy" and resource_owned and before["kind"] == "directory" and not args.refresh_copy:
            report["conflicts"].append(f"Managed copy needs explicit --refresh-copy: {path}")
        plans.append({"path": str(path), "before": before, "after": after})
    cfg = codex / "config.toml"
    before_cfg = cfg.read_bytes() if cfg.is_file() else b""
    updated_cfg = merge_config(before_cfg.decode("utf-8"), args.config_resolution == "keep").encode()
    if before_cfg != updated_cfg:
        plans.append({"path": str(cfg), "before": capture(cfg), "after": file_state(updated_cfg), "config": True})
    if report["conflicts"]:
        raise ValueError("Unresolved conflicts; no installation writes performed:\n" + "\n".join(report["conflicts"]))
    revision = git_state()
    if not revision["revision"]:
        raise ValueError("Setup requires a versioned Git checkout; clone the source repository first")
    if revision["dirty"] is True:
        raise ValueError("Setup requires a clean reviewed checkout; preserve/commit source changes first")
    if state.get("version") == 2 and state.get("revision") != revision["revision"] and args.reviewed_revision != revision["revision"]:
        raise ValueError("Installed revision differs; review the new checkout and use update --reviewed-revision")
    if not plans and state.get("version") == 2 and state.get("revision") == revision["revision"]:
        print("Setup unchanged (idempotent); no new snapshot transaction")
        return
    snapshot = snapshot_root(args, codex, home, state.get("snapshot"))
    initial = state.get("initial_transaction")
    # Allocate deterministically before writing the manifest; transaction uses the same next number.
    numbers = [int(p.stem) for p in (snapshot / "installer").glob("*.json") if p.stem.isdigit()]
    next_path = snapshot / "installer" / f"{max(numbers, default=0) + 1:04d}.json"
    manifest = {"version": 2, "provider": "codex", "repository": str(ROOT), "mode": mode,
                "revision": revision["revision"], "dirty_at_install": revision["dirty"],
                "snapshot": str(snapshot), "initial_transaction": initial or str(next_path),
                "resources": {str(p): fingerprint(v) for p, v in targets.items()},
                "config_values": tomllib.loads(updated_cfg.decode("utf-8-sig")),
                "original_owned": state.get("original_owned", original_owned),
                "reviewed_profile": profile_digest(tomllib.loads(updated_cfg.decode("utf-8-sig")))}
    # Store only managed values in the manifest, never credentials/unrelated settings.
    manifest["config_values"] = {"agents": {}}
    parsed = tomllib.loads(updated_cfg.decode("utf-8-sig"))
    for section, keys in MANAGED.items():
        obj = manifest["config_values"][section] if section else manifest["config_values"]
        for key in keys:
            obj[key] = value(parsed, section, key)
    mpath = codex / MANIFEST
    plans.append({"path": str(mpath), "before": capture(mpath), "after": file_state((json.dumps(manifest, indent=2) + "\n").encode())})
    journal = transaction(snapshot, plans, {"command": "setup", "codex_home": str(codex), "home": str(home),
                                            "source_revision": revision["revision"], "prior_source_revision": state.get("revision"),
                                            "legacy_migration": bool(state) and state.get("version") != 2})
    print(f"Installed; transaction: {journal}")
    validate(args)


def validate(args):
    repo_validate()
    if args.repo_only:
        print("Repository static validation PASS")
        return
    home, codex, skill = locations(args)
    state = load_manifest(codex)
    if state.get("version") != 2:
        raise ValueError("Replacement installation manifest missing")
    if state.get("status") == "partial_uninstall":
        raise ValueError("PARTIAL uninstall pending; installation is not active/validated as a complete baseline")
    source = git_state()
    if source["revision"] != state.get("revision") or source["dirty"] is not False:
        raise ValueError("Source checkout differs from the recorded clean installed revision; review and update")
    report = inspect(args)
    if report["conflicts"]:
        raise ValueError("Conflicts: " + "; ".join(report["conflicts"]))
    for path, digest in state["resources"].items():
        if fingerprint(capture(Path(path))) != digest:
            raise ValueError(f"Managed resource drift: {path}")
    if (codex / "AGENTS.md").read_bytes() != generated(codex):
        raise ValueError("Generated instructions stale; review checkout and run update")
    for dest, source in ((codex / "agent-base", ROOT), (skill, ROOT / "skills/ui-ux")):
        if state["mode"] == "copy" and capture(dest) != capture(source, source=True):
            raise ValueError("Managed copy stale; review checkout and update --refresh-copy")
        if state["mode"] != "copy" and not linked_to(dest, source):
            raise ValueError(f"Incorrect managed link: {dest}")
    parsed = tomllib.loads(read_text(codex / "config.toml"))
    for section, keys in MANAGED.items():
        for key in keys:
            if value(parsed, section, key) != value(state["config_values"], section, key):
                raise ValueError(f"Managed setting drift: {section}.{key}")
    print("Installed static/configuration validation PASS; runtime behavior/identity not tested")


def uninstall(args):
    home, codex, skill = locations(args)
    state = load_manifest(codex)
    if state.get("version") != 2:
        raise ValueError("No replacement installation to uninstall")
    verify_owned_paths(state, codex, skill)
    snapshot = snapshot_root(args, codex, home, state["snapshot"])
    initial = json.loads(read_text(Path(state["initial_transaction"])))
    originals = {c["path"]: c for c in initial["changes"]}
    plans, preserved = [], []
    for name, digest in state["resources"].items():
        path = Path(name)
        before = capture(path)
        old = originals.get(name, {}).get("before", {"kind": "missing"})
        after = {"kind": "missing"} if name in state["original_owned"] else old
        if before == after:
            continue
        # Moving an edited resource away is an explicit safe resolution for retry.
        if before["kind"] != "missing" and fingerprint(before) != digest:
            preserved.append(name)
            continue
        # Never remove the actual checkout, even if someone changes its location.
        if not is_link(path) and path.resolve() == ROOT.resolve():
            raise ValueError("Refusing to remove physical authoritative checkout")
        plans.append({"path": name, "before": before, "after": after})
    cfg = codex / "config.toml"
    original = originals.get(str(cfg))
    if original and not state.get("uninstall_config_restored") and cfg.is_file() and not is_link(cfg):
        old = base64.b64decode(original["before"].get("bytes", "")).decode("utf-8")
        applied = base64.b64decode(original["after"]["bytes"]).decode("utf-8")
        current = cfg.read_bytes().decode("utf-8")
        restored = restore_config(current, old, applied)
        if restored != current:
            plans.append({"path": str(cfg), "before": capture(cfg), "after": file_state(restored.encode()), "config": True})
    mpath = codex / MANIFEST
    manifest_after = {"kind": "missing"}
    if preserved:
        remaining = dict(state)
        remaining.update(status="partial_uninstall", uninstall_config_restored=True,
                         resources={name: state["resources"][name] for name in preserved})
        manifest_after = file_state((json.dumps(remaining, indent=2) + "\n").encode())
    plans.append({"path": str(mpath), "before": capture(mpath), "after": manifest_after})
    # An unchanged retry retains ownership without generating another transaction.
    if all(change["before"] == change["after"] for change in plans):
        journal = "unchanged; existing recovery journal retained"
    else:
        journal = transaction(snapshot, plans, {"command": "uninstall", "codex_home": str(codex), "home": str(home)})
    if preserved:
        raise ValueError("PARTIAL uninstall; preserved locally edited resources and their ownership manifest: " +
                         ", ".join(preserved) + f". Transaction: {journal}. "
                         "Move edited resources outside discovery or restore their installed content/links, "
                         "then rerun uninstall with the same snapshot. No modified content was deleted.")
    print(f"Uninstalled; transaction: {journal}")


def rollback(args):
    home, codex, skill = locations(args)
    snapshot = snapshot_root(args, codex, home)
    journals = sorted((snapshot / "installer").glob("[0-9][0-9][0-9][0-9].json"))
    candidates = [(p, json.loads(read_text(p))) for p in journals]
    candidates = [(p, j) for p, j in candidates if j["status"] in ("applied", "prepared", "failed")]
    if args.transaction:
        candidates = [(p, j) for p, j in candidates if p.stem == args.transaction]
    if not candidates:
        raise ValueError("No transaction available for rollback")
    path, journal = candidates[-1]
    if journal["metadata"]["codex_home"] != str(codex) or journal["metadata"]["home"] != str(home):
        raise ValueError("Snapshot belongs to different installation roots")
    if {c["path"] for c in journal["changes"]} - allowed_paths(codex, skill):
        raise ValueError("Journal contains resources outside installation ownership scope")
    changes = []
    for change in reversed(journal["changes"]):
        target = Path(change["path"])
        current = capture(target)
        after = change["before"]
        if current == after:
            continue
        if current != change["after"]:
            if change.get("config") and current["kind"] == "file":
                now = base64.b64decode(current["bytes"]).decode("utf-8")
                before = base64.b64decode(change["before"].get("bytes", "")).decode("utf-8")
                installed = base64.b64decode(change["after"]["bytes"]).decode("utf-8")
                # Keep later local scalar edits as well as unrelated settings.
                after = file_state(restore_config(now, before, installed).encode())
            else:
                raise ValueError(f"Rollback conflict: resource edited since transaction: {target}")
        changes.append((target, after))
    for target, after in changes:
        restore(target, after)
    journal["status"] = "rolled_back"
    atomic_write(path, json.dumps(journal, indent=2) + "\n")
    print(f"Rolled back transaction {path.stem}; later unrelated config preserved")
    revision = journal["metadata"].get("prior_source_revision")
    if journal["metadata"].get("legacy_migration") or (revision and revision != git_state()["revision"]):
        print("SOURCE ROLLBACK REQUIRED for prior policy: file/link restoration does not revert the checkout. "
              "Review and restore the recorded source revision separately, preserving repository edits. "
              f"Prior installed revision: {revision or 'not recorded by legacy installer; use the external audit snapshot'}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("inspect", "setup", "validate", "update", "uninstall", "rollback"))
    parser.add_argument("--provider", default="codex" if os.environ.get("CODEX_THREAD_ID") else None)
    parser.add_argument("--home")
    parser.add_argument("--codex-home")
    parser.add_argument("--repo-only", action="store_true")
    parser.add_argument("--copy", action="store_true", help="Explicit managed copy fallback")
    parser.add_argument("--refresh-copy", action="store_true", help="Refresh unmodified managed copies after review")
    parser.add_argument("--config-resolution", choices=("stop", "baseline", "keep"), default="stop")
    parser.add_argument("--reviewed-instructions-sha256", default="")
    parser.add_argument("--reviewed-config-sha256", default="", help="Acknowledge the reviewed selected profile in this exact config")
    parser.add_argument("--snapshot", help="Single external rollback bundle; installer/ stores transactions")
    parser.add_argument("--transaction", help="Four digit transaction to roll back (default latest)")
    parser.add_argument("--reviewed-revision", "--reviewed-update", dest="reviewed_revision")
    args = parser.parse_args(argv)
    if args.repo_only and args.command == "validate":
        validate(args)
        return
    if args.provider != "codex":
        raise ValueError("No approved provider profile. Ask the user for model/effort mappings; do not install Codex settings")
    if args.command == "inspect":
        print(json.dumps(inspect(args), indent=2))
    elif args.command == "update":
        state = git_state()
        if state["dirty"] is not False:
            raise ValueError("Update requires a clean Git checkout")
        if not args.reviewed_revision or args.reviewed_revision != state["revision"]:
            raise ValueError("Review the current checkout separately, then pass --reviewed-revision with its full HEAD SHA; no automatic pull")
        setup(args)
    else:
        globals()[args.command](args)


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"agent-base: {error}", file=sys.stderr)
        sys.exit(2)
