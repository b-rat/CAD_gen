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
7. Pedal boss (revolved profile with built-in 4mm OD fillets) + crank arm (swept rounded-rect cross-section) + 8mm junction fillet → ~90 faces
8. Bolt holes + counterbores → ~100 faces
9. Pedal bore + axle bore + JIS square taper → 104 faces

Final output: `crankset/crankset.step` (104 labeled faces) + `crankset/build_crankset.py` (persistent build script)

## What worked

**Machinist approach (stock → subtract).** Starting from a stock cylinder and removing material maps directly to CadQuery's boolean operations. Each feature is an isolated cut, easy to debug and reorder independently.

**Incremental build-and-verify loop.** Adding one feature at a time with user visual verification caught geometry problems immediately. The hub turn-down cutting through the spider would have been much harder to diagnose in a monolithic build.

**Swept rounded cross-section for arm.** Building the crank arm via `.sweep()` with a rounded-rectangle profile (4mm corner radii) instead of `extrude() + fillet()` solved two problems at once: the arm long-edge fillets are built into the geometry (no fillet API needed), and the swept solid unions cleanly with the pedal boss as 1 solid — no COMPOUND bug.

**Built-in fillets via revolved profile.** The pedal boss OD fillets (4mm top + bottom) were built as quarter-circle arcs in the XZ cross-section, then revolved. This completely avoids the fillet API for the boss edges, which consistently failed due to complex arm-boss intersection topology.

**Junction fillet on combined solid.** The 8mm blending fillet between arm and boss was applied to the arm+boss combined solid (after union, before spider union). Edge selector filtered by distance to boss center and excluded the boss's own circular edges. Max radius tested: 9.25mm (8mm chosen for margin).

**In-memory face classification.** Passing the CQ result object directly to `classify_faces()` instead of reimporting from STEP avoided the face count mismatch caused by OCCT export/import round-trip splitting faces (107 STEP faces vs 108 reimported faces).

**Face classification scaling.** The centroid + surface type approach scaled to 104 faces. `GeomAbs_SurfaceOfRevolution` was added for swept arm corner rounds. BSplineSurface handles boss junction fillets and loft-generated taper walls.

**Face labels as shared vocabulary.** Once faces were named, the user could give precise instructions like "add a fillet where hub.boss meets planar_z12" instead of ambiguous geometric descriptions.

## What didn't work

**Pre-fillet + union → COMPOUND (the hardest bug).** Filleting the arm (creating torus surfaces at Y=±12) before `union()` with the pedal boss produced a COMPOUND with 2 separate solids instead of 1 fused solid. The bore only cut through one body, leaving the boss solid with no hole. `.clean()` did not fix it. This was the critical blocker that required the swept cross-section approach.

**Fillet API on full-span arm edges after union.** The arm long edges (X=10 to X=-165) pass through the boss intersection zone. Filleting these edges after arm+boss union fails with "BRep_API: command not done" because the fillet surface collides with the boss geometry at the intersection.

**Face-cut approach for boss top fillet.** Tried filleting boss at Z=34, then face-cutting at Z=30 to flatten the pedal face. But the 4mm fillet extends from Z=30 to Z=34, so the face-cut at Z=30 removed the entire fillet. Multiple radius/offset combinations all failed.

**OD fillet API on arm+boss union seam edges.** After union (unfilleted arm + boss), the intersection edges between arm and boss are too complex for the fillet API at the boss OD. Both top and bottom OD fillets failed. Building fillets into the revolved profile was the only reliable approach.

**Build order errors were the most common mistake.** The axle bore was placed before the crank arm union — the arm solid filled the bore back in. The pedal bore had the same issue earlier. **Rule: all cuts through shared volumes must go after all unions.** This is the single most important lesson.

**Hub turn-down took three attempts.** Failed to trace the taper intersection math before writing cuts. First cut had OD too large (went through spider arms). Second cut had Z range too tall (went through spider web). Third attempt needed splitting into back-only. **Rule: compute `Z_taper(r)` at the cut boundaries before writing any code.**

## Key patterns established

| Pattern | When to use |
|---------|------------|
| Swept rounded cross-section | Need long-edge fillets on a body that will be unioned with another — avoids COMPOUND bug from pre-fillet + union |
| Built-in fillets via revolved profile | Boss/hub OD fillets where the fillet API fails on complex intersection edges |
| Junction fillet on combined solid | Blending fillet at union seam — select edges by proximity to junction, exclude own circular edges |
| In-memory face classification | Always — avoids face count mismatch from STEP export/import round-trip |
| Pre-union fillet | Need fillets on edges that will become union seams (but beware COMPOUND bug with curved intersections) |
| Cuts after all unions | Any bore/hole through regions that unions will fill |
| Tangent avoidance (offset + 0.5mm) | Cut tool surface coincides with existing surface |
| Z-limited annular cuts | Turning down a boss embedded in tapered structure |
| BSplineSurface classifier fallback | Loft operations produce BSpline instead of expected types |
| SurfaceOfRevolution classifier | Swept cross-section corner rounds |

## Errors encountered and resolved

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| Pre-fillet arm + boss union → COMPOUND (2 solids) | Torus fillet surfaces prevent boolean fusion | Swept rounded cross-section instead of extrude+fillet |
| Pedal bore covered up (not cutting through boss) | COMPOUND union — bore only cuts 1 of 2 solids | Fix union to produce 1 solid (swept arm approach) |
| Face count mismatch (107 STEP vs 108 reimported) | OCCT export/import round-trip splits a face | Classify in-memory solid, not reimported STEP |
| OD top fillet fails after removing junction fillets | Complex edge topology at arm-boss intersection | Build fillet into revolved boss profile as quarter-circle arc |
| Face-cut removes entire top fillet | Fillet zone (Z=30-34) falls within face-cut range | Build fillet into profile instead of API + face-cut |
| Arm long-edge fillet on combined solid fails | Edges pass through boss intersection zone | Swept rounded cross-section (no fillet API) |
| ArmLongEdgeSelector matches 0 edges | xmin filter excluded full-span edges (xmin=-165) | Moot — switched to sweep approach |
| Axle bore disappeared after arm union | Arm solid overlapped bore void, union filled it | Move bore cut to after all unions |
| Pedal bore didn't cut through arm | Bore placed before arm union in build order | Move bore to after arm union |
| Hub turn-down cut through spider web | Full-Z annular cut removed taper structure at r=15-20 | Split into back-only cut, Z-limited to boss protrusion zone |
| Hub turn-down still clipped front taper | Front cut started at Z=18.5, taper meets hub at Z=19.4 | Removed front cut entirely (minimal protrusion) |
| Fillet on union seam edges fails | OCCT BRep_API: command not done | Fillet standalone solid before union |
| Boss fillet → 114 fragment faces | Curved torus + curved cylinder boolean intersection | Build fillets into revolved profile |
| Square taper faces classified as "?" | Loft created BSplineSurface, not GeomAbs_Plane | Added BSplineSurface case to classifier |
| Axle bore not tall enough | Crank arm curves to Z≈22 at bore location, bore stopped at Z=22 | Extended bore to Z=32 (pedal_boss_z_face + 2) |
| Changing hub_od from 40→30 broke spider fillets | 5mm fillet too large for new 30mm hub geometry | Keep hub_od=40, add separate turn-down cut instead |
| Fillet at r=5.0mm fails but 5.5+ works | Likely OCCT edge-length coincidence at exactly 5mm | Skip; use 8mm (well within stable range) |
