# Showerhead Tee — Session Log

## Session 1: Initial build

### Build sequence

1. **Block** — 1.18 x 3.5 x 1.18 in, centered X/Z, bottom at Y=-2.0.
2. **KF10 flanges** — body of revolution from 2D profile (bore_r → base_r → taper → rim). Three flanges unioned to block (top +Y, bottom -Y, side +X).
3. **Bores** — Y bore through full height, cross bore from YZ plane through side flange. Cut after all unions.
4. **Block resize** — height reduced to 2.59" (+Y face at 0.59"), +X face moved to 1.59" (side flange 1" further out), -X face at -0.59".
5. **Fillets** — 0.25" radius on block_cross ↔ block_top and block_cross ↔ block_bottom edges. Applied after unions, before bore cuts.
6. **Counterbores** — 0.49" dia x 0.10" deep on each flange front face. Cut after bores.
7. **Bore resize** — bore diameter reduced from 0.40" to 0.35".

### Key lessons

- **CadQuery XZ workplane offset direction**: `.workplane(offset=N)` on XZ plane offsets in -Y direction (opposite intuition). Negative extrude also mirrors through origin rather than reversing direction. Workaround: build cylinder on XY, then rotate+translate to desired position.
- **IN = 25.4 scaling**: CadQuery works in mm internally. All inch parameters multiplied by `IN` at API calls. Do NOT attempt STEP header unit conversion — it doesn't work reliably across viewers.
- **Back taper angle**: "15° from front face" means 15° from the plane perpendicular to the axis = 75° from the axis. `taper_z = (rim_r - base_r) * tan(15°)`.
- **Bore extent**: compute from absolute flange front positions with generous margin, not relative to block_h. Block height changes previously caused bore to stop short.
- **Radius disambiguation**: counterbore radius (0.245") = flange base radius (0.245"). Classifier must distinguish by centroid proximity to known positions (flange front face vs flange interface).
- **Cross bore stops at YZ plane**: prevents splitting the Y bore into two faces. Starting at X=0 keeps the Y bore as a single cylindrical surface.
- **Fillet before bore cuts**: fillets applied after unions but before bore/counterbore cuts. Edge selection via BoxSelector at known (X, Y) coordinates.
- **y_bore split detection**: second-pass in classifier checks if multiple Y-axis bore faces exist; renames the lower-centroid one to `y_bore_bottom`.

### Face naming convention

Block faces use descriptive names (`block_top`, `block_cross`, etc.) rather than numbered `block.planar_N`. The `_cross` face is the +X face where the side flange attaches. User provided named STEP file as reference for the convention.

### Iteration history

| Change | Faces | Notes |
|--------|-------|-------|
| Block only | 6 | Initial box |
| + 3 KF flanges | 18 | Body of revolution flanges |
| + bores | 20 | Y bore + cross bore |
| Cross bore stops at X=0 | 20 | 3 unnamed faces disappeared |
| Block extended -X | 20 | Classifier fixed for asymmetric block |
| Block +Y moved to 0.59" | 20 | Y bore extent fixed |
| Side flange moved +1" | 20 | half_d = 1.59 |
| + fillets (0.25") | 22 | 2 cylindrical fillet faces |
| + counterbores | 28 | 3 walls + 3 bottoms |
| Bore dia → 0.35" | 28 | Final |
