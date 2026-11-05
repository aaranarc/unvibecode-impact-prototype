"""Prototype of `unvibecode impact <file>`: who depends on this file, and how far to trust that answer.

Usage:
    python impact_prototype.py <shipreadyv2_resolved_graph.json | <repo>-repository-context.zip> <repo-relative file>

Reads output files that UnvibeCode 0.3.15 already writes (the resolved graph from its local fast lane,
or the context ZIP kept in ./unvibecode_results). It builds nothing itself and makes no network calls.
Static imports only: dynamic imports, string-based loading and runtime wiring are not counted.
"""
import json
import sys
import zipfile
from collections import defaultdict
from pathlib import PurePosixPath


def load(path):
    """Return (edges, unresolved, generated_at). Each edge: source, target, type, confidence, strategy, raw, level."""
    if path.endswith(".zip"):
        with zipfile.ZipFile(path) as z:
            def rows(name):
                return [json.loads(line) for line in z.read(name).decode().splitlines() if line.strip()]
            edges = [dict(source=r["source_file"], target=r["target_file"], type=r["relationship"],
                          confidence=r.get("confidence"), strategy=None, raw=None, level="file")
                     for r in rows("connections.jsonl")]
            # The ZIP mixes record shapes; keep only unresolved import records (no resolved target).
            unresolved = [dict(source=r.get("source_file") or r.get("source"), raw=r.get("raw"))
                          for r in rows("unresolved_relationships.jsonl")
                          if r.get("resolution_status", "unresolved") == "unresolved" and "target" not in r]
            return edges, unresolved, json.loads(z.read("manifest.json")).get("repository", "")
    with open(path, encoding="utf-8") as handle:
        g = json.load(handle)
    edges = [dict(source=e["source"], target=e["target"], type=e.get("type"), confidence=e.get("confidence"),
                  strategy=e.get("resolution_strategy"), raw=e.get("raw"), level=level)
             for level, key in (("file", "edges"), ("symbol", "symbol_edges")) for e in g.get(key, [])]
    unresolved = [dict(source=u["source"], raw=u.get("raw")) for u in g.get("unresolved_imports", [])]
    return edges, unresolved, g.get("generated_at", "")


def module_name(path):
    """src/flask/app.py -> flask.app ; src/flask/__init__.py -> flask (src/ layout aware)."""
    parts = list(PurePosixPath(path).with_suffix("").parts)
    if parts and parts[0] == "src":
        parts = parts[1:]
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def analyse(edges, unresolved, target):
    """Pure function: everything the report needs, as a dict (tested in test_impact.py)."""
    dependents_of = defaultdict(set)
    for e in edges:
        if e["source"] != e["target"]:
            dependents_of[e["target"]].add(e["source"])
    fan_in = {f: len(s) for f, s in dependents_of.items()}
    direct = sorted(dependents_of.get(target, ()))
    indirect = sorted({s for d in direct for s in dependents_of.get(d, ())} - set(direct) - {target})
    rank = 1 + sum(v > len(direct) for v in fan_in.values())
    weak = [e for e in edges if target in (e["source"], e["target"])
            and (e["strategy"] == "stem_fallback" or e["confidence"] != "high")]
    # stdlib imports are expected to be unresolved; listing them is noise.
    own_unresolved = sorted({u["raw"] for u in unresolved if u["source"] == target
                             and str(u["raw"]).split(".")[0] not in sys.stdlib_module_names})
    mod = module_name(target)
    # `import <this module>` that the graph did NOT connect to this file (e.g. src/ layout, issue #308).
    missed = [u for u in unresolved if u["raw"] == mod]
    misrouted = [e for e in edges if e["level"] == "file" and e["raw"] == mod and e["target"] != target]
    heavy = len(fan_in) >= 10 and rank <= round(0.1 * len(fan_in))  # top 10%; meaningless on tiny repos
    return dict(target=target, module=mod, direct=direct, indirect=indirect, rank=rank, files_with_dependents=len(fan_in),
                heavy=heavy, weak=weak, own_unresolved=own_unresolved, missed=missed, misrouted=misrouted)


def render(a, source_label, context=""):
    out = [f"impact: {a['target']}   (module `{a['module']}`; {source_label})", ""]
    if context:
        out.insert(1, context)
    head = f"Direct dependents: {len(a['direct'])}"
    if a["direct"]:
        head += f"   fan-in rank {a['rank']} of {a['files_with_dependents']} files with any dependents"
    out.append(head + ("  << heavily depended-on" if a["heavy"] else ""))
    out += [f"  {f}" for f in a["direct"]]
    out += ["", f"Indirect dependents (2 hops): {len(a['indirect'])}"] + [f"  {f}" for f in a["indirect"]]
    out += ["", f"Unresolved imports inside this file: {len(a['own_unresolved'])}  {', '.join(a['own_unresolved'])}"]
    out += ["", f"Low-confidence links touching this file (stem_fallback or not 'high'): {len(a['weak'])}"]
    out += [f"  {e['source']} -> {e['target']}  [{e['type']}, {e['confidence']}, {e['strategy'] or 'strategy n/a in ZIP'}]"
            for e in a["weak"][:15]]
    if a["missed"] or a["misrouted"]:
        elsewhere = ", ".join(sorted({e["target"] for e in a["misrouted"]})) or "-"
        out += ["", f"WARNING: dependents may be undercounted. `import {a['module']}` appears {len(a['missed'])}x unresolved "
                    f"and {len(a['misrouted'])}x linked to other files ({elsewhere})."]

    warn = []
    if a["heavy"]:
        warn.append(f"heavily depended-on (fan-in rank {a['rank']}/{a['files_with_dependents']})")
    if a["weak"]:
        warn.append(f"{len(a['weak'])} low-confidence link(s)")
    if a["own_unresolved"]:
        warn.append(f"{len(a['own_unresolved'])} unresolved import(s) inside the file")
    if a["missed"] or a["misrouted"]:
        warn.append(f"`import {a['module']}` not linked here {len(a['missed']) + len(a['misrouted'])}x, "
                    "so the dependent count may be too low")
    listed = [f"- {f}" for f in a["direct"][:10]] + ([f"- ... and {len(a['direct']) - 10} more"] if len(a["direct"]) > 10 else [])
    out += ["", "--- PR description block ---", "### Impact checked with UnvibeCode", "",
            f"`{a['target']}`: **{len(a['direct'])} direct** / **{len(a['indirect'])} indirect (2-hop)** dependents.", ""]
    out += listed
    out += ["", "**Check before merging:** " + ("; ".join(warn) if warn else "no low-confidence links found") + ".", "",
            "<sub>Generated by `unvibecode impact` (prototype) from the local Connected Code Map. "
            "Static imports only; not a test result.</sub>"]
    return "\n".join(out)


def context_tokens(path, target):
    if not path.endswith(".zip"):
        return ""
    with zipfile.ZipFile(path) as z:
        if "selections.jsonl" not in z.namelist():
            return ""
        selections = [json.loads(line) for line in z.read("selections.jsonl").decode().splitlines() if line.strip()]
    selection = next((s for s in selections if s["file"] == target), {})
    scope = selection.get("scopes", {}).get("1")
    if not scope:
        return ""
    total = sum(s["source_tokens"] for s in selections)
    return (f"AI context: radius 1 = {scope['estimated_tokens']:,} est. tokens ({len(scope['included_files'])} files) "
            f"vs {total:,} for the whole repo (UnvibeCode's estimates)")


def main(argv):
    if len(argv) != 3:
        sys.exit(__doc__)
    edges, unresolved, generated = load(argv[1])
    print(render(analyse(edges, unresolved, argv[2]), f"input: {PurePosixPath(argv[1]).name} {generated}".strip(),
                 context_tokens(argv[1], argv[2])))


if __name__ == "__main__":
    main(sys.argv)
