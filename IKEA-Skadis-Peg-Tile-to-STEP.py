#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.10"
# dependencies = ["build123d"]
# ///
"""Export IKEA-Skadis-Peg-Tile.scad to STEP with one solid per object.

OpenSCAD cannot write STEP. This script asks OpenSCAD for the tile layout
(the STEP_* echo lines in the .scad) and rebuilds the same geometry as exact
B-rep with build123d: a "Backplate" solid, one "Peg N" solid per peg, and a
"Locating cubes" group (a STEP sub-assembly) with one "Cube N" solid per cube.
Before writing, it renders the .scad with OpenSCAD and compares volume and
bounding box with the B-rep, so a change to the .scad's modules that this
script does not mirror fails loudly instead of producing a stale STEP.

Each export is written to step-files/clearance-<clearance>/ next to the .scad
as <scad name>_<tile_x>x<tile_y>-offset-<X>x<Y>.step, where X and Y are the
offsets in mm for tiling that part. A clearance above 0 also adds
-clearance-<clearance> before .step.

Usage: uv run IKEA-Skadis-Peg-Tile-to-STEP.py [tile.scad] [--tiles XxY ...] [--clearance MM ...]
  Without --tiles or --clearance it uses the values set in the .scad;
  --tiles 1x1 3x2 --clearance 0 0.1 exports one file per combination.
Needs `openscad` on PATH.
"""

import argparse
import itertools
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from build123d import Compound, Plane, Pos, SlotCenterToCenter, Solid, export_step, extrude


def run_openscad(scad: Path, out: Path, *args: str) -> None:
    result = subprocess.run(["openscad", *args, "-o", str(out), str(scad)], capture_output=True, text=True)
    if result.returncode != 0:
        sys.exit(f"openscad failed on {scad}:\n{result.stderr}")


def read_layout(scad: Path, tmp: Path, defines: list[str]) -> dict:
    echo = tmp / "layout.echo"
    run_openscad(scad, echo, *defines)
    lines = echo.read_text().splitlines()
    # A failed assert() still exits 0; its message lands in the echo output.
    if errors := [line for line in lines if line.startswith("ERROR:")]:
        sys.exit(f"openscad failed on {scad}:\n" + "\n".join(errors))
    layout = {}
    for line in lines:
        if m := re.fullmatch(r"ECHO: (STEP_\w+) = (.+)", line.strip()):
            layout[m[1]] = json.loads(m[2])
    missing = {"STEP_TILES", "STEP_PEG", "STEP_PEGS", "STEP_CUBES", "STEP_PLATE", "STEP_CLEARANCE"} - layout.keys()
    if missing:
        sys.exit(f"{scad} does not echo {', '.join(sorted(missing))}")
    return layout


def slot_prism(x: float, y: float, z: float, length: float, d: float, height: float):
    """The .scad's linear_extrude(height) slot_outline(length, d), placed at (x, y, z)."""
    sep = length - d
    return Pos(x + sep / 2, y, z) * extrude(SlotCenterToCenter(sep, d), amount=height)


def build_tile(layout: dict, label: str) -> Compound:
    d, hook_len, hook_h, neck_len, neck_h = layout["STEP_PEG"]
    corner, size = layout["STEP_PLATE"]

    # Built in place (no Location) so every body sits at an identity placement in the STEP.
    plate = Solid.make_box(*size, Plane(origin=corner))
    plate.label = "Backplate"

    pegs = []
    for i, (x, y) in enumerate(layout["STEP_PEGS"], 1):
        # skadis_peg(): hook behind the board, neck through the slot.
        peg = slot_prism(x, y, 0, hook_len, d, hook_h) + slot_prism(x, y, hook_h, neck_len, d, neck_h)
        if len(peg.solids()) != 1:
            sys.exit(f"Peg {i}: hook and neck do not form one solid")
        peg = peg.solid()
        peg.label = f"Peg {i}"
        pegs.append(peg)

    cubes = []
    for i, (corner, size) in enumerate(layout["STEP_CUBES"], 1):
        cube = Solid.make_box(size, size, size, Plane(origin=corner))
        cube.label = f"Cube {i}"
        cubes.append(cube)
    # A nested Compound becomes a STEP sub-assembly: one folder in Shapr3D's Items Manager.
    locating_cubes = Compound(label="Locating cubes", children=cubes)

    return Compound(label=label, children=[plate, locating_cubes, *pegs])


def check_against_openscad(scad: Path, tile: Compound, tmp: Path, defines: list[str]) -> None:
    stl = tmp / "render.stl"
    run_openscad(scad, stl, "--export-format", "binstl", "-D", "$fn=256", *defines)
    raw = stl.read_bytes()
    record = np.dtype([("normal", "<f4", 3), ("v", "<f4", (3, 3)), ("attr", "<u2")])
    tri = np.frombuffer(raw, record, int.from_bytes(raw[80:84], "little"), 84)["v"].astype(float)
    mesh_volume = np.einsum("ij,ij->i", tri[:, 0], np.cross(tri[:, 1], tri[:, 2])).sum() / 6
    mesh_box = np.array([tri.reshape(-1, 3).min(0), tri.reshape(-1, 3).max(0)])

    brep_volume = sum(s.volume for s in tile.solids())
    bb = tile.bounding_box()
    brep_box = np.array([tuple(bb.min), tuple(bb.max)])

    # $fn=256 facets shave about 1e-5 of the volume off the round slot ends.
    if abs(mesh_volume - brep_volume) > 1e-4 * brep_volume or not np.allclose(mesh_box, brep_box, atol=1e-3):
        sys.exit(
            "B-rep does not match the OpenSCAD render; the .scad modules changed in a way "
            "build_tile() does not mirror.\n"
            f"  volume: openscad {mesh_volume:.3f}, brep {brep_volume:.3f}\n"
            f"  bbox:   openscad {mesh_box.round(3).tolist()}, brep {brep_box.round(3).tolist()}"
        )


def tile_counts(value: str) -> tuple[int, int]:
    if not (m := re.fullmatch(r"([1-9]\d*)x([1-9]\d*)", value)):
        raise argparse.ArgumentTypeError(f"expected tile counts like 3x2, got {value!r}")
    return int(m[1]), int(m[2])


def clearance_mm(value: str) -> str:
    if not re.fullmatch(r"\d+(?:\.\d+)?", value):
        raise argparse.ArgumentTypeError(f"expected a clearance in mm like 0.1, got {value!r}")
    return value


def export_part(scad: Path, defines: list[str], tmp: Path) -> None:
    layout = read_layout(scad, tmp, defines)
    tile = build_tile(layout, scad.stem)
    check_against_openscad(scad, tile, tmp, defines)

    tile_x, tile_y = layout["STEP_TILES"]
    _, (offset_x, offset_y, _) = layout["STEP_PLATE"]
    clearance = layout["STEP_CLEARANCE"]
    suffix = f"-clearance-{clearance:g}" if clearance else ""
    out_dir = scad.parent / "step-files" / f"clearance-{clearance:g}"
    out_dir.mkdir(parents=True, exist_ok=True)
    step = out_dir / f"{scad.stem}_{tile_x:g}x{tile_y:g}-offset-{offset_x:g}x{offset_y:g}{suffix}.step"
    if not export_step(tile, step):
        sys.exit(f"export_step failed for {step}")
    print(f"Wrote {step}: Backplate, {len(layout['STEP_PEGS'])} pegs ({layout['STEP_PEG'][0]:g} mm wide), "
          f"{len(layout['STEP_CUBES'])} locating cubes")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("scad", nargs="?", type=Path, default=Path(__file__).with_name("IKEA-Skadis-Peg-Tile.scad"))
    parser.add_argument("--tiles", nargs="+", type=tile_counts, metavar="XxY",
                        help="tile counts to export, one file each (default: tile_x/tile_y from the .scad)")
    parser.add_argument("--clearance", nargs="+", type=clearance_mm, metavar="MM",
                        help="clearance per side in mm, one file each (default: clearance from the .scad)")
    args = parser.parse_args()

    tile_runs = [["-D", f"tile_x={x}", "-D", f"tile_y={y}"] for x, y in args.tiles] if args.tiles else [[]]
    clearance_runs = [["-D", f"clearance={c}"] for c in args.clearance] if args.clearance else [[]]
    with tempfile.TemporaryDirectory() as tmp:
        for tiles, clearance in itertools.product(tile_runs, clearance_runs):
            export_part(args.scad, tiles + clearance, Path(tmp))


if __name__ == "__main__":
    main()
