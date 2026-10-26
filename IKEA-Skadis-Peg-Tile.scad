// --------------------------------------------------------------
//  IKEA SKÅDIS peg tile: 2 x 2 pegs per tile, tile_x by tile_y tiles
//  Peg dimensions and spacing match
//  IKEA-Skadis-Pegboard-Mount.scad by Angel Roman:
//  https://github.com/legna-namor/IKEA-Skadis-Pegboard-Mount-Generator
//
//  Axes (same as the original):
//    +X  down the board; hooks hang toward +X
//    +Y  across the board
//    +Z  away from the board; hook tips at Z = 0, backplate on top
//
//  Each tile is exactly one repeat of the SKÅDIS slot pattern
//  (40 mm on X, 80 mm on Y). The tile_x by tile_y tiles share one
//  backplate, and every slot under it gets exactly one peg. To tile
//  the finished part again with no gap, offset copies by
//    X = tile_x * 40 mm
//    Y = tile_y * 80 mm
//
//  STEP export (one solid per peg + one for the backplate):
//    uv run IKEA-Skadis-Peg-Tile-to-STEP.py   values below
//    uv run IKEA-Skadis-Peg-Tile-to-STEP.py --tiles 1x1 3x2 --clearance 0 0.1
//                                             one file per combination
//  Files are named IKEA-Skadis-Peg-Tile_<tile_x>x<tile_y>-offset-<X>x<Y>.step,
//  where X and Y are the offsets in mm for tiling that part. A clearance
//  above 0 adds -clearance-<clearance> before .step.
//  The script reads the STEP_* echo lines at the bottom of this file.
// --------------------------------------------------------------

// Number of tiles along X, down the board (whole number, 1 or more)
tile_x = 1;
// Number of tiles along Y, across the board (whole number, 1 or more)
tile_y = 1;
// Clearance per side in mm: moves each side face of every peg inward (0.1 gives 4.8 mm wide pegs)
clearance = 0;

$fn = 64;

// SKÅDIS slot lattice: slots in a row are slot_pitch apart; rows are
// row_pitch apart and every other row is shifted row_pitch across.
slot_pitch = 40;
row_pitch  = 20;

// Peg profile in mm (same values as the original mount).
peg_d    = 5;    // slot width
hook_len = 15;   // hook length, equal to the slot height
hook_h   = 5;    // hook thickness behind the board
neck_len = 7.5;
neck_h   = 5.2;  // gap for the board, which is about 5 mm thick

assert(clearance >= 0 && clearance < peg_d / 2,
       str("clearance must be at least 0 and less than ", peg_d / 2, " mm"));

// Peg outline after clearance. Every side face moves inward by clearance,
// so the round ends keep their centers and each peg stays on its slot.
peg_w  = peg_d - 2 * clearance;
hook_l = hook_len - 2 * clearance;
neck_l = neck_len - 2 * clearance;

plate_t = 1;

// One repeat of the lattice: 2 rows x 2 pegs.
tile_size_x = 2 * row_pitch;   // 40
tile_size_y = 2 * slot_pitch;  // 80

// Centers each tile's pegs on that tile.
margin_x = (tile_size_x - (row_pitch + hook_len)) / 2;            // 2.5
margin_y = (tile_size_y - (slot_pitch + row_pitch + peg_d)) / 2;  // 7.5

// Peg origins (center of the hook's upper round end, the origin of skadis_peg()),
// numbered row by row. Each tile holds 2 rows of 2 pegs; even rows are
// shifted row_pitch across from odd rows.
pegs = [
    for (row = [0 : 2 * tile_x - 1], col = [0 : 2 * tile_y - 1])
        [margin_x + peg_d / 2 + row * row_pitch,
         margin_y + peg_d / 2 + (1 - row % 2) * row_pitch + col * slot_pitch]
];

plate_size = [tile_x * tile_size_x, tile_y * tile_size_y, plate_t];
plate_z = hook_h + neck_h;  // 10.2

// --------------------------------------------------------------
// Slot outline: width d, overall length len along +X, first round end
// centered on the origin.
module slot_outline(len, d) {
    hull() for (x = [0, len - d]) translate([x, 0]) circle(d = d);
}

// One peg: the hook hangs behind the board, the neck passes through the slot.
module skadis_peg() {
    linear_extrude(hook_h) slot_outline(hook_l, peg_w);
    translate([0, 0, hook_h]) linear_extrude(neck_h) slot_outline(neck_l, peg_w);
}

// --------------------------------------------------------------
for (p = pegs) translate([p[0], p[1], 0]) skadis_peg();
translate([0, 0, plate_z]) cube(plate_size);

// Layout for IKEA-Skadis-Peg-Tile-to-STEP.py.
echo(STEP_PEG = [peg_w, hook_l, hook_h, neck_l, neck_h]);
echo(STEP_PEGS = pegs);
echo(STEP_PLATE = [[0, 0, plate_z], plate_size]);
echo(STEP_TILES = [tile_x, tile_y]);
echo(STEP_CLEARANCE = clearance);
