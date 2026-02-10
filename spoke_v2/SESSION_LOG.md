# Spoke V2 — Session Log

## Session 1: Initial build

Built from scratch (not based on prior disc build script) as a collaboration test.

### Build sequence

1. **Stock cylinder** — 200mm dia, 20mm thick, bottom on XY. 3 faces: top, bottom, rim.
2. **Top revolved taper cut** — trapezoid cross-section revolved on XZ. Cone from (R=5, Z=20) to (R=90, Z=3). Created rim_step shelf and top_taper cone. 5 faces.
3. **Bottom revolved conical recess** — triangle cross-section revolved on XZ. Cone from (R=10, Z=13) to (R=90, Z=0). 8 faces.
4. **Spoke cutouts** — window ring (hub to beyond rim) minus spoke bars, cut from part. Started with 6 spokes at 20mm wide, iterated to final 3 spokes at 15mm. 23 faces.

### Classifier lessons

- **Symmetric annular faces at Z=0**: both center circle and bottom ring have centroid at (0,0,0) since they're axially symmetric. Used `props.Mass()` (surface area) to distinguish — center circle area ~314mm² vs ring area ~5969mm².
- **Cone disambiguation via apex**: top_taper and bottom_taper centroids both fall below Z=10 (midplane), making centroid Z unreliable. Used `surf.Cone().Apex().Z()` instead — top taper apex projects above the part (Z≈21), bottom taper apex is inside (Z≈14.6).
- **Spoke overlap at hub**: with 6 spokes at 20mm width and hub_r=17.5mm, spoke bars overlapped at the hub (gap = π*35/6 - 20 ≈ -1.7mm), eliminating hub arcs entirely. Narrowing to 15mm or reducing to 3 spokes resolved this.

### Iteration history

| Change | Spokes | Width | Faces | Hub arcs? |
|--------|--------|-------|-------|-----------|
| Initial | 6 | 20mm | 35 | No — bars overlap at R=17.5 |
| Narrow spokes | 6 | 15mm | 41 | Yes |
| Reduce count | 3 | 15mm | 23 | Yes |
