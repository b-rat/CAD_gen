# Cross Assembly — Session Log

## Session 1: Initial cylinders + stepped split block

### Build sequence

1. **Two cylinders** — 10mm dia x 30mm, one along X at origin, one along Z at (0,20,0). Confirmed positions with render. 4 faces per cylinder (wall split by `both=True`).
2. **Stepped split design** — Recognized that perpendicular bore axes (skew lines, 20mm apart) can't share a single split plane. Designed L-shaped parting surface: z=0 for front section, x=0 for back section. Each bore gets half-round clamping channels.
3. **L-shaped boolean cutters** — Built each cutter as union of two overlapping boxes (0.1mm overlap at y=10 transition for clean boolean). Two cuts from the bored block produce two interlocking halves.
4. **Verified connectivity** — Both halves confirmed as single solids (1 solid each). Half A connects through (+x,+z) quadrant at y=10, Half B through (-x,-z) quadrant.

### Alternative design: parallel splits

User requested a simpler variant with both splits normal to Y axis:
- Split at y=0 (XZ plane) — clamps bore_x
- Split at y=20 (XZ plane) — clamps bore_z
- Produces 3 pieces: front cap, middle body, back cap (8, 10, 8 faces)

Saved separately. Simpler to manufacture but requires 3 block pieces instead of 2.

### Casting-ready refinement

Returned to stepped split design with manufacturing features:
1. **Wall thickness** increased from 5mm to 10mm — accommodates bolt holes with adequate clearance to bore surfaces.
2. **External fillets** (3mm) on all 12 block edges — applied before bore cuts. No boolean issues since fillets are on a simple box.
3. **Bore cuts** — machined features, sharp cylinder-to-face intersections (no bore entry fillets).
4. **Bolt holes** — 4x M5 clearance (5.5mm dia). Front pair in Z-direction at (x=+-10, y=-8), back pair in X-direction at (y=30, z=+-10).
5. **Cylinder length** doubled to 60mm for visual clarity.

### Key lessons

- **Skew bore axes need spatial split.** Two perpendicular bores offset in space can't share a split plane. The stepped/L-shaped parting surface solves this with one joint instead of two.
- **L-cutter overlap at transition.** When building the L-shaped cutter as a union of two boxes, add 0.1mm overlap at the transition (y=split_y +-0.1) to avoid coincident-face boolean failures.
- **Fillet before bores, bores before split.** Filleting a simple box is reliable. Bore cuts through filleted surfaces work fine. Splitting the bored+filleted block with box cutters works fine. This order avoids fillet failures on complex edge topologies.
- **Bolt clearance drives wall thickness.** With 5mm bore radius and 2.75mm bolt hole radius, minimum wall = 5 + 2.75 + ~2mm edge margin = ~10mm. Original 5mm wall was too thin.
- **YZ workplane for X-direction holes.** `cq.Workplane("YZ").transformed(offset=(y, z, 0))` places a circle at global (0, y, z). `.extrude(big, both=True)` creates the hole along X. The `.transformed()` offset maps local (x,y,z) → global (Y, Z, X).
- **`cq.Assembly().save()` FutureWarning.** `.save()` is deprecated; works but will be removed. No replacement API tested yet.

### Iteration history

| Change | Faces (per half) | Solids | Notes |
|--------|------------------|--------|-------|
| Block only | 6 | 1 | Simple box |
| + fillets | 26 | 1 | 3mm on all edges |
| + bores | 28 | 1 | X-bore + Z-bore |
| + stepped split | 14 | 1 each | L-shaped cut, no fillets |
| + fillets + split | 18 | 1 each | Cast block version |
| + bolt holes | 33 | 1 each | 4x M5 clearance |

### Assembly export

4 bodies via `cq.Assembly`: cyl_x, cyl_z, block_half_a, block_half_b. Each body gets its own CLOSED_SHELL in STEP. Face labeling iterates across all CLOSED_SHELLs.

### Design decisions

- **Stepped split over parallel splits**: 2 pieces vs 3, one joint vs two, interlocking step provides shear resistance. Trade-off: more complex parting surface (harder to machine).
- **Through-clearance bolt holes**: simplified geometry — real part would have clearance one side, tapped the other. Can add counterbores later.
- **No draft angles**: omitted for simplicity at this scale. Would add 1-3deg draft on cast faces for a production mold.
- **No bore entry fillets**: bores are machined features, sharp intersections are correct. Cast version would have small cored radii at bore entries.
