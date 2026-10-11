---
name: blender-headless-check
description: Validate the SWISSBuildings import addon headlessly via `blender -b` and tools/headless_check.py. Use when verifying the import works, checking centering, comparing .gml vs .zip, or after changing parser/mesh code.
---

# Blender Headless Check

Run the addon's import **without a GUI** to confirm it works, geometry is
centered on the tile origin, and `.gml` vs `.zip` produce identical results.
No MCP, no display, no `context.window` — `blender -b` is enough.

## When to use

- After changing `parser.py`, `tooling.py`, or the import logic in `__init__.py`.
- To sanity-check a new demo file before loading it in the GUI.
- To confirm the `.zip` path (in-RAM decompression) matches the plain `.gml` path.
- When the user asks "does the import still work?" or "is it centered?".

## What you need

- `blender` on `PATH` (this machine: `/usr/bin/blender`, v5.2.0 LTS). Headless `-b` mode works here — verified.
- The repo's `tools/headless_check.py` (the harness). It is **the** entry point; do not reimplement its checks ad-hoc.
- Blender's internal Python already has `numpy` + `lxml`, so the venv is NOT required for the Blender path. (The venv is only needed for the no-bpy fallback path.)

## How to run

```bash
# Single small tile (fast, ~1s) — the default if you pass no files:
blender -b --factory-startup --python tools/headless_check.py -- demofiles/demo_Hinterrhein.gml

# A .gml + its .zip of the SAME tile (verifies equivalence):
blender -b --factory-startup --python tools/headless_check.py -- \
    demofiles/demo_2_multitile.gml demofiles/demo_2_multitile.zip

# A large multitile (heavier, ~1–2 min):
blender -b --factory-startup --python tools/headless_check.py -- demofiles/demo_1_multitile.zip
```

- Run from the **repo root**.
- `--` separates Blender's own flags from the harness's file args (the harness
  splits on the bare `--` and takes everything after it as files).
- No `files` argument → defaults to `demofiles/demo_Hinterrhein.gml` plus its
  `.zip` twin if present.
- Exit code `0` = pass, `1` = a check failed, `2` = a file was not found.

### Optional: no-Blender (parser-only) path

If Blender isn't available, the same script degrades to a parser-only check
(via the project venv) that validates the data structures but NOT object
creation / centering:

```bash
uv run python tools/headless_check.py -- demofiles/demo_Hinterrhein.gml
```

## What the harness checks (Blender path)

For each file it imports and reports:
- **Import completes** and creates the expected object count (buildings / meshes / verts).
- **World-origin anchor** `context.scene["swissbuildings_world_origin"]` is set,
  and equals the **first** tile's `(x, y, 0)` bounding-box center.
- **x/y centered on origin**: the scene-world bbox of the imported tile is
  centered near `(0, 0)` (within a few meters). Z is intentionally NOT centered
  (it keeps the absolute LV95 height datum) — do not "fix" a large z span.
- **Re-import idempotency**: importing the same file again replaces the content,
  it does not duplicate it.
- **gml ≡ zip equivalence**: when two files with the same basename (one `.gml`,
  one `.zip`) are given, their building/mesh/vertex counts must match exactly.

## Interpretation

- A line like `[ok] x/y centered near origin — center=(0.0, 0.0)` is good.
  A `center=(12.4, -3.1)` that's within a few meters is fine (the tile center is
  the anchor, individual tiles vary a bit); tens of meters is a real regression.
- `RESULT: PASS` / `RESULT: FAIL` is the final line. On FAIL the script lists
  the specific failed check(s) above it.
- The anchor value printed (e.g. `(2760667.193, 1241618.153, 0.0)`) is the
  LV95 tile center — large numbers are expected and correct.

## Gotchas (learned the hard way — do not re-derive)

- **`ModuleNotFoundError: No module named 'cattrs'`** at startup is HARMLESS.
  It's Blender's own `bl_pkg` addon failing to import its optional dependency,
  not your code. Ignore it. (Same for `[ALSOFT] ... PipeWire ... event context`
  and `socket(): Operation not permitted` — audio/display init noise in headless.)
- **Do NOT** derive the addon's import name from the repo's directory name. The
  addon is the top-level `__init__.py`; import it by explicit file path via
  `importlib.util.spec_from_file_location` (as the harness does). Guessing a
  module name breaks on any checkout.
- **`context.window_manager` / `context.scene` DO exist** in headless `-b`, so
  `import_swissbuildings(context, filepath)` runs fine unmodified — no stub
  context needed. (`context.window` does NOT exist, but the import path doesn't
  touch it.)
- The parser accepts a **file-like object**, so the zip path works by passing
  `zipfile.ZipFile(...).open(member)` straight in — nothing is written to disk.
- **RAM**: big multitiles (REDACTED,
  REDACTED) are the slow/heavy ones. Your box may have 15 GB total; a single tile import is fine, but don't import both big
  tiles in one run if memory is tight.
- The harness prints `RESULT: PASS` even when it fell back to parser-only mode
  — check the line that says `bpy available = True/False` to know which path
  actually ran.

## Files

- `tools/headless_check.py` — the harness (run via `blender -b --python` or `uv run python`).
- `demofiles/` — demo `.gml`/`.zip` tiles. `demo_Hinterrhein.gml` is the fast default; the `_multitile` ones are the heavy equivalence tests.
- `__init__.py` — the addon; `import_swissbuildings(context, filepath)` is the function under test.
