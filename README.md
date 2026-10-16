# skadis-pegs-pattern

This repository holds STEP files of backplates with pegs for the IKEA SKÅDIS pegboard. Each file holds a 1 mm backplate and its pegs as separate bodies. Copies of a part tile with no gap, and each SKÅDIS slot under them gets one peg.

![A 3 x 2 part: 24 pegs on a 120 x 160 mm backplate](images/IKEA-Skadis-Peg-Tile_3x2-offset-120x160.png)

The peg dimensions and spacing come from [IKEA-Skadis-Pegboard-Mount-Generator](https://github.com/legna-namor/IKEA-Skadis-Pegboard-Mount-Generator) by Angel Roman.

## STEP files

| File | Backplate (mm) | Pegs | Preview |
|---|---|---|---|
| [IKEA-Skadis-Peg-Tile_1x1-offset-40x80.step](IKEA-Skadis-Peg-Tile_1x1-offset-40x80.step) | 40 × 80 | 4 | <img src="images/IKEA-Skadis-Peg-Tile_1x1-offset-40x80.png" width="240" alt="1 x 1 part"> |
| [IKEA-Skadis-Peg-Tile_2x1-offset-80x80.step](IKEA-Skadis-Peg-Tile_2x1-offset-80x80.step) | 80 × 80 | 8 | <img src="images/IKEA-Skadis-Peg-Tile_2x1-offset-80x80.png" width="240" alt="2 x 1 part"> |
| [IKEA-Skadis-Peg-Tile_1x3-offset-40x240.step](IKEA-Skadis-Peg-Tile_1x3-offset-40x240.step) | 40 × 240 | 12 | <img src="images/IKEA-Skadis-Peg-Tile_1x3-offset-40x240.png" width="240" alt="1 x 3 part"> |
| [IKEA-Skadis-Peg-Tile_3x2-offset-120x160.step](IKEA-Skadis-Peg-Tile_3x2-offset-120x160.step) | 120 × 160 | 24 | <img src="images/IKEA-Skadis-Peg-Tile_3x2-offset-120x160.png" width="240" alt="3 x 2 part"> |
| [IKEA-Skadis-Peg-Tile_10x8-offset-400x640.step](IKEA-Skadis-Peg-Tile_10x8-offset-400x640.step) | 400 × 640 | 320 | <img src="images/IKEA-Skadis-Peg-Tile_10x8-offset-400x640.png" width="240" alt="10 x 8 part"> |

### File names

`IKEA-Skadis-Peg-Tile_<tiles X>x<tiles Y>-offset-<offset X>x<offset Y>.step`

- **tiles X**: the number of tiles along X, down the board. Each tile adds 40 mm and 2 rows of pegs.
- **tiles Y**: the number of tiles along Y, across the board. Each tile adds 80 mm and 2 pegs to each row.
- **offset X** and **offset Y**: the spacing in mm between copies when you tile the part. These values are also the size of the backplate.

For example, `IKEA-Skadis-Peg-Tile_3x2-offset-120x160.step` has 3 × 2 tiles and 24 pegs. To tile it, space the copies 120 mm apart along X and 160 mm apart along Y.

### Axes

All dimensions are in millimeters.

- +X points down the board. The hooks hang toward +X.
- +Y points across the board.
- +Z points away from the board. The hook tips are at Z = 0, and the backplate is from Z = 10.2 to 11.2.

## Tile a part in CAD

Use the offsets from the file name as the spacing between copies. These steps are for Shapr3D. Most CAD tools have a similar tool for linear patterns.

1. Import the STEP file with **Insert > File**.
2. Go to **Transform > Pattern**.
3. Set **Type** to **Linear**.
4. Select every body of the part: the `Backplate` and all of the `Peg` bodies.
5. Drag the gizmo arrow that points along X.
6. Set **Spacing** to the X offset, and set **Quantity**.
7. Do steps 5 and 6 again with the Y arrow and the Y offset.
8. Select **Done**.

The copies touch edge to edge, and each SKÅDIS slot under them gets one peg.

![The 1 x 1 part in a 3 x 2 pattern](images/tiling.png)

*The outlined 1 x 1 part in a 3 x 2 pattern (3 along X, 2 along Y), seen from the peg side.*

## Make a custom peg layout

Each peg is a separate body. You can delete the pegs that you do not need.

1. Import the STEP file that covers the area that you want.
2. In the Items Manager, select the pegs to delete. To select more than one peg, hold Command.
3. Press Delete.

Do not move the remaining pegs. Each peg sits on a SKÅDIS slot.

The peg numbers follow the rows. `Peg 1` is in the row at the smallest X. In each row, the numbers increase along +Y.

## Make other sizes

You need [OpenSCAD](https://openscad.org) and [uv](https://docs.astral.sh/uv/).

```sh
uv run IKEA-Skadis-Peg-Tile-to-STEP.py --tiles 4x2 5x5
```

The script writes one STEP file for each tile count, with the file names above. Without `--tiles`, it uses `tile_x` and `tile_y` from `IKEA-Skadis-Peg-Tile.scad`.

OpenSCAD cannot export STEP. The script builds the same shapes with [build123d](https://github.com/gumyr/build123d). Before it writes a file, it compares the shapes with the OpenSCAD render.
