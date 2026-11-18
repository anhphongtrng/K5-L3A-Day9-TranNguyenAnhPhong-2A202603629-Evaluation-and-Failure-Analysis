"""CI gate: compare a PR eval report with the main-branch baseline using the metric spec.

    python -m lab9.gate --pr reports/eval_workflow.json --baseline reports/baseline_v1.json

exit 0 = merge, exit 1 = blocked. Safety metrics: max 0, no averaging away.
Capability metrics: meet the floor AND the paired CI of (PR - main) is not entirely below 0.
Thresholds may only get stricter on the same eval-set version (ratchet).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from lab8.console import utf8_stdio
from lab9 import stats
from lab9.eval import SPEC, load_spec, per_item


def integrity_check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> list[str]:
    """M7 (Expert): refuse to compare reports that cannot be trusted. Return a list of problems
    (empty = trustworthy). A gate that passes a broken report is worse than no gate.
    Must catch at least:
      - any metric value in pr["metrics"] that is NaN or inf
      - len(pr["rows"]) != manifest items x len(manifest seeds)   (dropped / duplicated rows)
      - the (item_id, seed) set of PR differs from the baseline's (cherry-picked seeds/items)
      - pr["evaluator_failures"] non-empty, or a row whose value for a graded spec metric is
        None (a crashed grader silently scores as "missing" and drops out of the mean)
      - base_spec given and a threshold in spec is LOOSER than in base_spec for the same
        eval-set version (ratchet: max may not rise, min may not fall, a blocking metric may
        not become non-blocking, a metric may not disappear; the same for spec["slices"],
        including dropping no_significant_drop)
      - an item's slice tags in PR rows differ from the baseline's (relabelling an item out of a
        slice hides its regression from the slice gate)"""
    problems = []
    # Aggregate-only metrics are not expected as per-trial columns.
    aggregate_only = {"pass_5", "cost_per_success"}
    graded = {m["id"] for m in spec.get("metrics", [])
              if m["id"] not in aggregate_only
              and not m["id"].startswith(("pass_at_", "pass_hat_"))}

    def inspect(report, name):
        manifest = report.get("manifest", {})
        rows = report.get("rows", [])
        metrics = report.get("metrics", {})
        for mid, val in metrics.items():
            if isinstance(val, (float, int)) and not math.isfinite(val):
                problems.append(f"{name}: non-finite metric {mid} (NaN/inf)")
        if report.get("evaluator_failures"):
            problems.append(f"{name}: evaluator_failures is non-empty")
        keys = [(r.get("item_id"), r.get("seed")) for r in rows]
        pairs = set(keys)
        if len(pairs) != len(keys):
            problems.append(f"{name}: duplicate (item_id, seed) rows")
        items = {i for i, _ in pairs}
        seeds = manifest.get("seeds")
        count = manifest.get("items")
        if count is not None and seeds is not None:
            if len(rows) != count * len(seeds):
                problems.append(f"{name}: row count differs from manifest items x seeds")
            if (len(items) != count or len(set(seeds)) != len(seeds)
                    or pairs != {(i, s) for i in items for s in seeds}):
                problems.append(f"{name}: incomplete or inconsistent item/seed grid")
        tags = {}
        for r in rows:
            key = (r.get("item_id"), r.get("seed"))
            if None in key:
                problems.append(f"{name}: missing item_id or seed")
            for mid in graded:
                if r.get(mid) is None:
                    problems.append(f"{name}: missing graded metric {mid} at {key}")
                elif isinstance(r[mid], (int, float)) and not math.isfinite(r[mid]):
                    problems.append(f"{name}: non-finite row metric {mid} at {key}")
            tag = frozenset(r.get("slices") or [])
            if key[0] in tags and tags[key[0]] != tag:
                problems.append(f"{name}: inconsistent slice tags for {key[0]}")
            tags[key[0]] = tag
        return pairs, tags

    pr_pairs, pr_tags = inspect(pr, "PR")
    base_pairs, base_tags = inspect(base, "baseline")
    if pr_pairs != base_pairs:
        problems.append("PR item/seed pairs differ from baseline")
    if pr_tags != base_tags:
        problems.append("PR slice tags differ from baseline")

    def ratchet(old, new, label, old_threshold, new_threshold):
        if old.get("blocking") and not new.get("blocking"):
            problems.append(f"ratchet: {label} blocking removed")
        if old_threshold.get("no_significant_drop") and not new_threshold.get("no_significant_drop"):
            problems.append(f"ratchet: {label} no_significant_drop removed")
        for key in ("min", "max", "max_increase"):
            if key not in old_threshold:
                continue
            before, after = old_threshold[key], new_threshold.get(key)
            if after is None or (after < before if key == "min" else after > before):
                problems.append(f"ratchet: {label} {key} loosened or removed")

    if base_spec is not None and spec.get("eval_set_version") == base_spec.get("eval_set_version"):
        current = {m["id"]: m for m in spec.get("metrics", [])}
        for old in base_spec.get("metrics", []):
            mid = old["id"]
            if mid not in current:
                problems.append(f"ratchet: metric {mid} removed")
            else:
                new = current[mid]
                ratchet(old, new, mid, old.get("threshold", {}), new.get("threshold", {}))
        current_slices = {(s["name"], s["metric"]): s for s in spec.get("slices", [])}
        for old in base_spec.get("slices", []):
            key = (old["name"], old["metric"])
            label = f"slice:{key[0]}/{key[1]}"
            if key not in current_slices:
                problems.append(f"ratchet: {label} removed")
            else:
                new = current_slices[key]
                ratchet(old, new, label, old, new)
    return problems


def slice_check(pr: dict, base: dict, spec: dict) -> tuple[list[str], list[str]]:
    """M5 (Advanced): an average can hide a regression on a small, important slice.
    For each entry of spec["slices"] ({"name", "metric", "min"?, "no_significant_drop"?, "blocking"}):
      - value = mean of per_item(pr, metric, slice_name=name)
      - fail if below "min", or if no_significant_drop and the paired CI over the slice's items
        lies entirely below 0
    Return (blocked ids like "slice:money_movement/pass_rate", report lines)."""
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for entry in spec.get("slices", []):
        name, metric = entry["name"], entry["metric"]
        sid = f"slice:{name}/{metric}"
        a = per_item(pr, metric, slice_name=name)
        b = per_item(base, metric, slice_name=name)
        value = sum(a.values()) / len(a) if a else None
        failed = value is None or ("min" in entry and value < entry["min"])
        note = ""
        if entry.get("no_significant_drop"):
            if not a or set(a) != set(b):
                failed = True
                note = "missing or mismatched paired slice items"
            else:
                keys = sorted(a)
                d, lo, hi = stats.paired_bootstrap(
                    [a[k] for k in keys], [b[k] for k in keys],
                    n_resamples=bs.get("n_resamples", 1000),
                    rng=bs.get("rng", 2027),
                    confidence=bs.get("confidence", 0.95),
                )
                note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
                failed = failed or hi < 0
        if failed and entry.get("blocking"):
            blocked.append(sid)
        verdict = "BLOCK" if failed and entry.get("blocking") else "warn" if failed else "ok"
        shown = f"{value:.4f}" if value is not None else "None"
        lines.append(f"  {sid:<36} {shown:<8} min={entry.get('min', '-')} {note} {verdict}")
    return blocked, lines


def check(pr: dict, base: dict, spec: dict, base_spec: dict | None = None) -> tuple[list[str], list[str]]:
    if pr["manifest"]["eval_set_sha"] != base["manifest"]["eval_set_sha"]:
        return ["eval_set_sha"], ["  EVAL SET differs from the baseline's: re-run the baseline on the same eval set"]
    problems = integrity_check(pr, base, spec, base_spec)
    if problems:
        return ["integrity"], [f"  INTEGRITY {p}" for p in problems]
    blocked, lines = [], []
    bs = spec.get("bootstrap", {})
    for m in spec["metrics"]:
        mid, th, val = m["id"], m.get("threshold", {}), pr["metrics"].get(m["id"])
        verdict, note = "ok", ""
        if val is None:
            verdict = "missing"
        elif "max" in th and val > th["max"]:
            verdict = "fail"
        elif "min" in th and val < th["min"]:
            verdict = "fail"
        elif "max_increase" in th and base["metrics"].get(mid):
            if val > base["metrics"][mid] * (1 + th["max_increase"]):
                verdict = "fail"
        if th.get("no_significant_drop") and val is not None:
            a, b = per_item(pr, mid), per_item(base, mid)
            keys = sorted(set(a) & set(b))
            d, lo, hi = stats.paired_bootstrap([a[k] for k in keys], [b[k] for k in keys],
                                               n_resamples=bs.get("n_resamples", 1000), rng=bs.get("rng", 2027))
            note = f"Δ {d:+.3f} CI [{lo:+.3f}, {hi:+.3f}]"
            if hi < 0:
                verdict = "fail"
        if verdict != "ok" and m.get("blocking"):
            blocked.append(mid)
        label = {"ok": "ok", "missing": "MISSING"}.get(verdict, "BLOCK" if m.get("blocking") else "warn")
        lines.append(f"  {mid:<22} {val!s:<8} {json.dumps(th):<40} {note:<28} {label}")
    if spec.get("slices"):
        sb, sl = slice_check(pr, base, spec)
        blocked += sb
        lines += sl
    return blocked, lines


def main(argv: list[str] | None = None) -> int:
    utf8_stdio()
    ap = argparse.ArgumentParser(prog="lab9.gate")
    ap.add_argument("--pr", required=True)
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--spec", default=str(SPEC))
    ap.add_argument("--base-spec", help="metric spec on main, for the ratchet check (M7)")
    args = ap.parse_args(argv)
    pr = json.loads(Path(args.pr).read_text(encoding="utf-8"))
    base = json.loads(Path(args.baseline).read_text(encoding="utf-8"))
    base_spec = load_spec(Path(args.base_spec)) if args.base_spec else None
    blocked, lines = check(pr, base, load_spec(Path(args.spec)), base_spec)
    print(f"gate: PR {pr['run_id']} vs main {base['run_id']} · eval set {pr['manifest']['eval_set_sha']}")
    print("\n".join(lines))
    if blocked:
        print(f"exit 1 — blocked: {', '.join(blocked)}")
        return 1
    print("exit 0 — merge")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
