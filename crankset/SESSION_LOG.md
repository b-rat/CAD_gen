# Session Log: Crankset Build

Second extended session — building a real-world multi-feature part from a hand sketch, driven by iterative engineer instructions.

## What was built

**Track bike crankset** (drive-side crank, built from scratch iteratively):
1. Spider disc with lenticular profile (revolved triangular cuts) → 7 faces
2. Chainring pocket (annular shelf) → 9 faces
3. 5-arm window cuts (constant-width arms) → 40 faces
4. Spider inner corner fillets (5mm) → 50 faces
5. Hub shortening + boss turn-down (40mm → 30mm) → 51 faces
6. Hub boss fillets (3mm on both edges) → ~52 faces
7. Pedal boss union + bolt holes + counterbores → ~70 faces
8. Crank arm union (curved arc, pre-union 4mm fillets) → ~80 faces
9. Pedal bore + axle bore + JIS square taper → 88 faces

Final output: `crankset/crankset.step` (88 labeled faces) + `crankset/build_crankset.py` (persistent build script)

## What worked

**Machinist approach (stock → subtract).** Starting from a stock cylinder and removing material maps directly to CadQuery's boolean operations. Each feature is an isolated cut, easy to debug and reorder independently.

**Incremental build-and-verify loop.** Adding one feature at a time with user visual verification caught geometry problems immediately. The hub turn-down cutting through the spider would have been much harder to diagnose in a monolithic build.

**Pre-union fillets.** Filleting standalone solids before `union()` works around OCCT's inability to fillet union seam edges. The 4mm arm edge fillets and 3mm hub boss fillets both succeeded this way.

**Face classification scaling.** The centroid + surface type approach scaled to 88 faces. Adding a new feature type typically required 2-5 lines of classifier code. BSplineSurface fallback handled the loft-generated taper walls.

**Face labels as shared vocabulary.** Once faces were named, the user could give precise instructions like "add a fillet where hub.boss meets planar_z12" instead of ambiguous geometric descriptions.

## What didn't work

**Build order errors were the most common mistake.** The axle bore was placed before the crank arm union — the arm solid filled the bore back in. The pedal bore had the same issue earlier. **Rule: all cuts through shared volumes must go after all unions.** This is the single most important lesson.

**Hub turn-down took three attempts.** Failed to trace the taper intersection math before writing cuts. First cut had OD too large (went through spider arms). Second cut had Z range too tall (went through spider web). Third attempt needed splitting into back-only. **Rule: compute `Z_taper(r)` at the cut boundaries before writing any code.**

**No visual feedback is the biggest limitation.** Every geometry edit was a guess until user confirmation. Face counts catch added/removed faces but not shape errors. The hub turn-down especially — face count looked fine but the shape was wrong.

**Boss fillets were a dead end.** Filleting the pedal boss before union produced 114 fragment faces from curved-on-curved boolean intersections. Multiple approaches tried (bore-first, selective edges, smaller radius) — all produced the same fragmentation. Accepted as an OCCT limitation.

**Spatial reasoning errors are expensive.** Not understanding which volumes overlap led to most iteration. If a "what material exists at point (x,y,z)" query or cross-section render were available, most debugging would have been unnecessary.

## Key patterns established

| Pattern | When to use |
|---------|------------|
| Pre-union fillet | Need fillets on edges that will become union seams |
| Cuts after all unions | Any bore/hole through regions that unions will fill |
| Tangent avoidance (offset + 0.5mm) | Cut tool surface coincides with existing surface |
| Z-limited annular cuts | Turning down a boss embedded in tapered structure |
| BSplineSurface classifier fallback | Loft operations produce BSpline instead of expected types |
| Edge selector by bounding box radius + Z | Selecting circular edges for fillets |

## Errors encountered and resolved

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| Axle bore disappeared after arm union | Arm solid overlapped bore void, union filled it | Move bore cut to after all unions |
| Pedal bore didn't cut through arm | Bore placed before arm union in build order | Move bore to after arm union |
| Hub turn-down cut through spider web | Full-Z annular cut removed taper structure at r=15-20 | Split into back-only cut, Z-limited to boss protrusion zone |
| Hub turn-down still clipped front taper | Front cut started at Z=18.5, taper meets hub at Z=19.4 | Removed front cut entirely (minimal protrusion) |
| Fillet on union seam edges fails | OCCT BRep_API: command not done | Fillet standalone solid before union |
| Boss fillet → 114 fragment faces | Curved torus + curved cylinder boolean intersection | Removed boss fillet; accepted as OCCT limitation |
| Square taper faces classified as "?" | Loft created BSplineSurface, not GeomAbs_Plane | Added BSplineSurface case to classifier |
| Axle bore not tall enough | Crank arm curves to Z≈22 at bore location, bore stopped at Z=22 | Extended bore to Z=32 (pedal_boss_z_face + 2) |
| Changing hub_od from 40→30 broke spider fillets | 5mm fillet too large for new 30mm hub geometry | Keep hub_od=40, add separate turn-down cut instead |
