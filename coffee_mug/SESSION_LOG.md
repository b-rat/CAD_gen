# Session Log: Coffee Mug Build

Third extended session — building a consumer product (coffee mug) with curved handle geometry, demonstrating sweep-based construction and successful union seam fillets.

## What was built

**Coffee mug** (built from scratch iteratively):
1. Solid body of revolution (cylindrical bands + conical taper) → 5 faces
2. Bulge arc on body (threePointArc replacing cone) → 5 faces
3. Cavity hollowing (5mm wall, open top) → 9 faces
4. Handle via sweep (rounded rectangle cross-section along 3-arc path) → 18 faces (after union + cavity)
5. Full-round rim (built into revolved profiles) → +2 faces
6. Handle-body junction fillets (4mm) → 50 faces

Final output: `coffee_mug/coffee_mug.step` (50 labeled faces) + `coffee_mug/build_mug.py` (persistent build script)

## What worked

**Sweep for handle construction.** CadQuery's `.sweep()` along a centerline path with a rectangular cross-section produced a clean solid that unioned successfully with the revolved body. Extrusion of the same profile failed silently (produced COMPOUND instead of fused SOLID).

**Rounded cross-section instead of post-sweep fillets.** Instead of sweeping a sharp rectangle and filleting edges afterward, the cross-section was drawn as a rounded rectangle (lines + arcs). This avoids the fillet API entirely for handle edge rounding and eliminates the risk of fillet-on-curved-body fragment faces.

**Full round via profile modification.** The rim full round (r = wall_thickness/2) was built directly into both the outer body and cavity revolved profiles as quarter-circle arcs sharing the same center point. No fillet API needed.

**Union seam fillets succeeded.** The 4mm fillet on handle-body junction edges (union seam edges) worked — contradicting the crankset finding that "fillets on union seam edges always fail." The key difference: the mug has smooth curved surfaces (surface of revolution + swept solid) vs the crankset's angular multi-feature geometry. OCCT's fillet kernel handles smooth intersections better.

**Custom edge selector for junction fillets.** A CadQuery Selector subclass (`HandleJunctionSelector`) identified junction edges by checking: Y span within handle width, Z near attachment heights, X near body outer radius. This was more reliable than BoxSelector for finding the specific intersection edges.

**Parameter changes as one-line edits.** Adjusting handle size (cx from 70→65→60, radius from 19→15), fillet radius (2→4mm), and other dimensions required only parameter changes — the build script re-ran cleanly each time.

## What didn't work

**Extrusion-based handle union failed silently.** A 2D handle profile (outer + inner edges) extruded ±9mm from XZ plane created a valid 10-face solid. But `outer.union(handle)` returned the original body unchanged — OCC's `BRepAlgoAPI_Fuse` produced a COMPOUND rather than a single SOLID. `BRepAlgoAPI_Common` confirmed the solids did intersect. A simple box union worked fine. Root cause appears to be OCCT's boolean kernel failing on the intersection of extruded arc surfaces with the revolved body surface.

**Fillet API failed for rim full round.** Attempting `.edges(BoxSelector(...)).fillet(wall_thickness/2)` on the two circular rim edges failed with "BRep_API: command not done." This was expected (union seam-adjacent edges) and was solved by building the round into the profile.

**Handle parameter coupling.** Reducing `handle_main_cx` from 70 to 60 caused the top attachment point (44.2, 87.0) to fall inside the main arc circle (center 60, radius 19, distance 17.3 < 19). No transition arc of any radius or tangency type can connect a point inside a circle to the circle. Required also reducing `handle_main_r` from 19 to 15.

**Face classifier needed repeated updates.** Each geometry change (sharp→rounded cross-section, adding fillets) changed the surface types and bounding boxes of handle faces. The Y-span discriminator proved most robust across changes — body surfaces of revolution span their full diameter, while handle faces span only the handle width.

## Key patterns established

| Pattern | When to use |
|---------|------------|
| Sweep along centerline path | Handle-like features attached to curved bodies (extrusion may fail) |
| Rounded cross-section sweep | Need fillets on swept solid edges without fillet API |
| Profile-embedded full round | Full round on rim/lip of revolved body |
| Custom Selector subclass | Edge selection for fillets when position-based filtering is needed |
| Y-span face discriminator | Distinguishing handle faces from body faces on surface of revolution |
| Try union seam fillets first | Smooth geometry may succeed where angular geometry fails |

## Errors encountered and resolved

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| Handle extrusion union returned original body | OCCT boolean kernel fails on extruded arc ∩ revolved body | Switched to `.sweep()` along centerline path |
| Rim fillet failed (BRep_API: command not done) | Fillet on edges adjacent to union seams | Built full round into revolved profile (quarter-circle arcs) |
| Handle cx=60 → "No real solution for transition center" | Top attachment point inside main arc circle (d=17.3 < r=19) | Reduced handle_main_r from 19 to 15 |
| Handle cylinder faces unlabeled after rounded cross-section | Y span changed from ±9 to ±5 (hw - fillet_r) | Updated classifier to use `handle_half_width - handle_fillet_r` |
| Handle corner arcs classified as body.bulge | SurfaceOfRevolution with narrow Y band not distinguished from body | Added Y-span check: narrow band → handle, full span → body |
| Junction fillet faces classified as body.bulge | BSplineSurface fillet patches near body surface (cx < bulge_r) | Added Y-span check in BSplineSurface classifier → handle.fillet |
