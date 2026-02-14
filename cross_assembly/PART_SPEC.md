# Cross Assembly — Part Spec

Two-piece stepped-split clamp block joining two perpendicular cylinders. First assembly (multi-body) part in the repo.

## Assembly overview

Two 10mm-diameter cylinders pass through a cast block at perpendicular orientations, offset in Y. The block is split into two interlocking halves via a stepped parting surface. Bolts through each half clamp the bores onto the cylinders.

## Cylinders

| Parameter | Value | Axis | Center |
|-----------|-------|------|--------|
| Diameter | 10mm | — | — |
| Length | 60mm | — | — |
| cyl_x | — | X | (0, 0, 0) |
| cyl_z | — | Z | (0, 20, 0) |

## Block (cast body)

| Parameter | Value | Notes |
|-----------|-------|-------|
| X extent | 30mm | [-15, +15] |
| Y extent | 50mm | [-15, +35] |
| Z extent | 30mm | [-15, +15] |
| Wall thickness | 10mm | Around each bore |
| External fillet | 3mm | All 12 edges, cast radius |

## Bores (machined)

| Bore | Axis | Center | Radius | Extent |
|------|------|--------|--------|--------|
| bore_x | X | (y=0, z=0) | 5mm | Through block |
| bore_z | Z | (x=0, y=20) | 5mm | Through block |

Bore axes are skew lines — 20mm apart in Y, perpendicular orientations.

## Stepped split (machined)

Single parting surface that transitions between two planes:

| Region | Y range | Split plane | Bore served |
|--------|---------|-------------|-------------|
| Front | y < 10 | z = 0 (XY plane) | bore_x → upper/lower halves |
| Back | y > 10 | x = 0 (YZ plane) | bore_z → left/right halves |

Split gap: 0.5mm total (0.25mm per side).

**Transition at y=10**: Half A occupies the (+x, +z) quadrant, Half B occupies the (-x, -z) quadrant. Each half is a single connected solid joined through its diagonal quadrant (~10x10mm cross-section).

### Half A (upper-front / right-back)

- Front section (y < 10): z > 0.25 — upper half of bore_x
- Back section (y > 10): x > 0.25 — right half of bore_z

### Half B (lower-front / left-back)

- Front section (y < 10): z < -0.25 — lower half of bore_x
- Back section (y > 10): x < -0.25 — left half of bore_z

## Bolt holes (drilled)

| Bolt set | Direction | Positions | Bore clamped |
|----------|-----------|-----------|--------------|
| Front pair | Z-axis | (x=+10, y=-8), (x=-10, y=-8) | bore_x |
| Back pair | X-axis | (y=30, z=+10), (y=30, z=-10) | bore_z |

Hole diameter: 5.5mm (M5 clearance). 4 holes total.

## Face inventory (74 faces total)

### Cylinders (8 faces)

| Label | Count | Type | Description |
|-------|-------|------|-------------|
| `cyl_x.wall` | 4 | Cylinder | X-cylinder body (split by `both=True` extrude) |
| `cyl_z.wall` | 4 | Cylinder | Z-cylinder body |
| `cyl_x.end_pos/neg` | 2 | Plane | X-cylinder end caps |
| `cyl_z.end_pos/neg` | 2 | Plane | Z-cylinder end caps |

### Block halves (33 faces each, 66 total)

| Label pattern | Type | Description |
|---------------|------|-------------|
| `block.bore_x_a/b` | Cylinder | Half-round bore channels (X-bore) |
| `block.bore_z_a/b` | Cylinder | Half-round bore channels (Z-bore) |
| `block.bolt_N` | Cylinder | M5 clearance bolt holes |
| `block.fillet_N` | Torus/BSpline | External cast fillets |
| `plane_N` | Plane | Block faces, split faces, bolt hole annuli |

## Build sequence

1. Block box (30x50x30mm)
2. Fillet all 12 edges (3mm cast radius) — **before bores**
3. Cut bore_x and bore_z (machined features)
4. Stepped split via L-shaped boolean cutters
5. Drill bolt holes through both halves
6. Export as 4-body assembly (cyl_x, cyl_z, half_a, half_b)
