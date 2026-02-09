# Disc

5-spoke disc with tapered profile, concave bottom recess, and center bore. 36 faces total. Built from hand sketches.

## Key Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Disc diameter | 200mm | Cylindrical stock |
| Disc height | 20mm | Z=0 (bottom) to Z=20 (top) |
| Top flat | φ10mm | Preserved at Z=20 |
| Bottom flat | φ20mm | Preserved at Z=0 |
| Shelf width | 10mm | Flat annular band at outer rim, both top (Z=3) and bottom (Z=0) |
| Rim height | 3mm | Outer cylindrical wall, Z=0 to Z=3 |
| Top taper | Cone | (R=5, Z=20) → (R=90, Z=3) |
| Bottom taper | Concave cone | (R=10, Z=13) → (R=90, Z=0), 7mm gap from top at center |
| Recess wall | Cylinder R=10 | Vertical inner wall of bottom conical recess |
| Hub diameter | 30mm | Central hub, R=0 to R=15 |
| Spoke width | 10mm | 5 parallel-edge arms (constant width, not radial) |
| Center bore | φ5mm | Through-hole |

## Build Order (build_disc.py)

1. Stock cylinder (φ200 × 20mm)
2. Top taper cut (trapezoid revolved: cone + shelf at Z=3)
3. Bottom concave conical recess (triangle revolved: cone from R=10 to R=90)
4. Window cutouts (annular ring minus 5 spoke bars, through rim)
5. Center bore (φ5mm through-hole, last to avoid fill-in)

## Named Faces

| Label Pattern | Count | Description |
|--------------|-------|-------------|
| `top` | 1 | Center flat at Z=20, φ10mm |
| `top_taper` | 1 | Conical surface, Z=20 at R=5 → Z=3 at R=90 |
| `top_shelf_NN` | 5 | Flat annular segments at Z=3, one per spoke |
| `rim_NN` | 5 | Outer cylindrical segments at R=100, 3mm tall |
| `bottom_shelf_NN` | 5 | Flat annular segments at Z=0, one per spoke |
| `bottom_taper` | 1 | Concave conical recess, Z=13 at R=10 → Z=0 at R=90 |
| `recess_wall` | 1 | Cylinder at R=10, inner wall of bottom recess |
| `bottom` | 1 | Center flat at Z=0, φ20mm |
| `hub_NN` | 5 | Hub arcs at R=15, one per window |
| `spoke_NN.left/right` | 10 | Spoke side faces (planar, vertical) |
| `bore` | 1 | Center bore cylinder at R=2.5 |
