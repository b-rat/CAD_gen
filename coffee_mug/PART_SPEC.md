# Coffee Mug

Bulging body of revolution, hollowed cavity, swept handle, full-round rim. 50 faces total.

## Key Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Bottom diameter | 95mm | Cylindrical band, 9mm tall |
| Top diameter | 81.6mm | Cylindrical band, 9mm tall |
| Height | 107mm | Bottom on XY plane, axis along Z |
| Wall thickness | 5mm | Floor at Z=5, open top |
| Bulge max diameter | 100mm | At Z=50, arc cross-section |
| Handle center X | 65mm | From Z axis |
| Handle center Z | 80mm | Main arc center height |
| Handle main radius | 15mm | Main arc |
| Handle transition radius | 100mm | Tangent arcs to body at Z=20 and Z=87 |
| Handle cross-section | 18mm wide x 10mm thick | Rounded rectangle, 4mm corner radii |
| Rim | Full round | 2.5mm radius (wall_thickness / 2) |
| Handle-body fillet | 4mm | On union seam edges |

## Build Order (build_mug.py)

1. Outer body (revolved profile: cylindrical bands + bulge arc + full-round rim cap)
2. Handle via sweep (rounded rectangle cross-section along 3-arc centerline path)
3. Union handle with body
4. Cut cavity (revolved inner profile with matching rim cap, extends above to open top)
5. Fillet handle-body junction edges (4mm, custom edge selector)

## Named Faces

| Label Pattern | Count | Description |
|--------------|-------|-------------|
| `body.bottom_cyl` | 1 | Outer bottom cylindrical band |
| `body.bulge` | 1 | Outer bulge surface (SurfaceOfRevolution) |
| `body.top_cyl` | 1 | Outer top cylindrical band |
| `bottom` | 1 | Bottom face (Z=0 plane) |
| `cavity.bottom_cyl` | 1 | Inner bottom cylindrical wall |
| `cavity.bulge` | 1 | Inner bulge surface |
| `cavity.floor` | 1 | Interior floor (Z=5) |
| `cavity.top_cyl` | 1 | Inner top cylindrical wall |
| `handle` | 22 | Handle swept surfaces (flat sides + corner arcs) |
| `handle.fillet` | 16 | Handle-body junction fillet surfaces (BSpline) |
| `handle.side_pos` / `handle.side_neg` | 1 each | Handle flat side faces (Y=±9) |
| `rim` | 2 | Full-round rim (outer + inner toroidal halves) |
