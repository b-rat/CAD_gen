# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Purpose

AI_CAD is a CAD workspace for creating and labeling FreeCAD geometry as face-annotated STEP files. These files feed into the broader AI+CAD pipeline for training graph neural networks on parametric CAD models.

## Pipeline Context

```
FreeCAD → STEP export → STEP Labeler (../steplabeler/) → Named STEP → Graph_CAD (../Graph_CAD/)
```

- **STEP Labeler** (`../steplabeler/`): Web app for visually selecting and naming faces on STEP files
- **Graph_CAD** (`../Graph_CAD/Graph_CAD/`): Graph Autoencoder + LLM project that uses labeled STEP files for training

## Folder Structure

```
AI_CAD/
├── CLAUDE.md
├── blkarc_slot/
│   ├── blkarc_slot.FCStd          # FreeCAD native project
│   ├── blkarc_slot.FCBak          # FreeCAD auto-backup
│   ├── blkarc_slot-Body.step      # STEP export, unnamed faces
│   └── blkarc_slot-Body_named.step # STEP export, labeled faces (7mm slot, 10° angle)
├── cylinder/
│   ├── build_cylinder.py          # Build script (parameters + geometry + labeling)
│   └── cylinder.step              # 66-face labeled cylinder
├── coffee_mug/
│   ├── build_mug.py              # Build script (parameters + geometry + labeling)
│   └── coffee_mug.step           # 50-face labeled coffee mug
└── crankset/
    ├── build_crankset.py          # Build script (parameters + geometry + labeling)
    ├── crankset.step              # 88-face labeled crankset
    └── crankset_named.step        # User-labeled version via STEP Labeler
```

## Geometry: blkarc_slot

A rectangular block (100mm x 50mm) with an arc-shaped top surface (R=100mm cylindrical) and an angled slot cut. Units are millimeters. 10 faces total.

### Named Faces

| Label | Type | Description |
|-------|------|-------------|
| `x_neg` | Planar | Face at x = -50 |
| `x_pos` | Planar | Face at x = +50 |
| `y_pos` | Planar | Side face at y = +25 |
| `y_neg` | Planar | Side face at y = -25 |
| `bottom_surface` | Planar | Bottom face at z = 0 |
| `top_surface.cylindrical_1` | Cylindrical | Right portion of arc top (R=100) |
| `top_surface.cylindrical_2` | Cylindrical | Left portion of arc top (R=100) |
| `slot.planar_1` | Planar | Slot wall (triangular face) |
| `slot.planar_2` | Planar | Slot wall (hexagonal face) |
| `slot.planar_3` | Planar | Slot wall (triangular face) |

## Geometry: crankset

A track bike drive-side crank — 5-arm spider with integrated crank arm, single piece. 88 faces total. Built iteratively via conversational instructions using the machinist approach (start from stock, subtract material).

### Key Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| BCD | 144mm | Track standard, 5-bolt |
| Spider OD | 160mm | |
| Hub OD | 40mm (turned to 30mm boss) | Axle interface area |
| Hub height | 20mm | Z=0 (back) to Z=20 (front/chainring side) |
| Spider thickness | 3mm | Lenticular profile, thick at hub, thin at rim |
| Crank arm length | 165mm | Center-to-center, spindle to pedal |
| Crank arm | 24mm wide, 10mm thick | Curved arc from spider to pedal boss |
| Pedal boss | 27mm dia, 10mm thick | |
| Axle bore | 20mm dia, 5mm deep blind hole | From front face |
| Square taper | JIS, 12.65mm across flats, 2°/side | Wide end at back |
| Bolt holes | 5x 10mm through, 12mm x 1mm counterbore | On 144mm BCD |
| Chainring pocket | Floor at Z=3, ID at r=64mm | |
| Pedal bore | 12.59mm (9/16"-20 minor dia) | Through all bodies |

### Build Order (in build_crankset.py)

1. Stock cylinder (spider OD x hub height)
2. Back-side revolved triangular cut (conical back taper)
3. Front-side revolved triangular cut (conical front taper, 3mm spider thickness)
4. Chainring pocket (annular shelf)
5. Arm window cuts (5 windows, inner_r = hub_od_r + 0.5 to avoid tangent boolean)
5b. Spider inner corner fillets (5mm, at window/hub junction)
5c. Hub shortening (back face moved to Z=5)
5d. Hub boss turn-down (40mm → 30mm, back side only)
5d2. Hub boss edge fillets (3mm, both Z=5 and Z=12 edges)
6. Pedal boss union
8. Bolt holes + counterbores
7. Crank arm union (with 4mm pre-union fillets on long edges)
9. Pedal bore (after arm union to cut through all bodies)
5e. Axle bore (after all unions so arm doesn't fill it back in)
5f. JIS square taper bore (loft between wide and narrow square profiles)

### Named Faces

| Label Pattern | Count | Description |
|--------------|-------|-------------|
| `spider.back_taper` | 1 | Conical back surface |
| `spider.front_taper` | 1 | Conical front surface |
| `spider.rim` | 5 | Outer cylindrical rim segments |
| `spider.fillet_NN` | 10 | Inner corner fillets (2 per arm) |
| `chainring.pocket_floor` | 5 | Pocket floor segments |
| `chainring.pocket_id` | 5 | Pocket inner diameter wall |
| `hub.boss` | 1 | Turned-down 30mm cylindrical surface |
| `axle.bore_wall` | 1 | 20mm blind bore cylinder |
| `axle.bore_floor` | 1 | Blind bore floor |
| `axle.taper_xp/xn/yp/yn` | 4 | Square taper walls |
| `bolt.hole_NN` | 5 | Through-holes on BCD |
| `bolt.cbore_NN` | 5 | Counterbore cylinders |
| `bolt.cbore_floor_NN` | 5 | Counterbore floor faces |
| `arm.top` / `arm.bottom` | 3/1 | Crank arm curved surfaces |
| `arm.side_left` / `arm.side_right` | 2/2 | Crank arm side faces |
| `arm.root_NN` | ~5 | Hub/window junction arcs |
| `pedal.face` / `pedal.back` / `pedal.boss` / `pedal.bore` | 1 each | Pedal boss features |
| `fillet` | 6 | Toroidal fillet faces (arm + hub boss) |
| `front` / `back` | 1/5 | Major planar faces |

## Geometry: coffee_mug

A coffee mug with bulging body, hollowed cavity, handle, and full-round rim. 50 faces total. Built iteratively — body of revolution, handle via sweep, junction fillets.

### Key Parameters

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

### Build Order (in build_mug.py)

1. Outer body (revolved profile: cylindrical bands + bulge arc + full-round rim cap)
2. Handle via sweep (rounded rectangle cross-section along 3-arc centerline path)
3. Union handle with body
4. Cut cavity (revolved inner profile with matching rim cap, extends above to open top)
5. Fillet handle-body junction edges (4mm, custom edge selector)

### Named Faces

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

### STEP Naming Convention

Faces use dot-separated `feature.sub_face` naming:
```
ADVANCED_FACE('top_surface.cylindrical_1', ...)
ADVANCED_FACE('slot.planar_2', ...)
```
Standalone faces use a single name: `ADVANCED_FACE('bottom_surface', ...)`

## Working with STEP Files

### Persist build scripts for every part

When building or modifying geometry with CadQuery, **always save the build script as a `.py` file** (e.g., `build_cylinder.py`). Structure it as:

```python
# Parameters (all dimensions, counts, derived values)
cyl_radius = 5.0
# ...

def build_geometry():
    """CadQuery boolean operations → CQ Workplane"""
    ...

def classify_faces(filepath):
    """OCC centroid + surface type → ordered label list"""
    ...

def write_labels(filepath, labels):
    """CLOSED_SHELL mapping → regex write labels into STEP"""
    ...

if __name__ == "__main__":
    result = build_geometry()
    cq.exporters.export(result, OUTPUT_PATH)
    labels = classify_faces(OUTPUT_PATH)
    write_labels(OUTPUT_PATH, labels)
```

**Why this matters:**
- The build script *is* the geometric understanding of the part — it encodes the construction sequence, parameter relationships, feature dependencies, and labeling logic. Reading it back provides the same parametric knowledge without reverse-engineering from the STEP file.
- Subsequent edits become parameter tweaks or localized feature additions rather than full rebuilds from verbal descriptions.
- The labeling classifier only needs to be extended (not rewritten) when new feature types are added.
- It's the equivalent of the CAD feature tree — without it, you only have the final solid.

**When creating a new part**, create the build script from the first CadQuery operation. Don't wait until the part is "done."

**When editing an existing part**, read its build script first. Modify parameters or add features to the script, then re-run it. This is faster and less error-prone than rebuilding from scratch or editing STEP text.

### Text editing vs CadQuery rebuild

**Use direct STEP text editing** when the change only affects coordinates and the topology (which faces/edges exist and how they connect) stays the same. Examples: moving a wall, changing a dimension, adjusting a radius. Trace CARTESIAN_POINT entities by ID through the entity reference graph (ADVANCED_FACE → PLANE → AXIS2_PLACEMENT_3D → CARTESIAN_POINT + DIRECTION). Update all affected entities: vertex points, line/circle/ellipse origins, plane reference points. Be careful with entities that share identical coordinate strings but are different entity IDs — edit by entity ID, not by text matching.

**Use CadQuery rebuild** when the topology changes — new faces appear, faces split, or edge connectivity changes. Example: deepening a slot past a surface transition (floor edges move from a cylinder to a planar face), or adding features like chamfers, fillets, or bores. Boolean operations (`shape.cut()`) handle the topology automatically.

**Rule of thumb**: if the edit requires computing new intersection curves between surfaces, rebuild with CadQuery. If it's just translating existing geometry, text-edit.

### CadQuery generation + STEP labeling pipeline

```python
# 1. Build geometry with CadQuery boolean operations
result = base_shape.cut(feature_solid)
cq.exporters.export(result, "output.step")

# 2. Classify faces using OCC
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Plane, GeomAbs_Cylinder, GeomAbs_Cone, GeomAbs_Torus

result2 = cq.importers.importStep("output.step")
for face in result2.faces().vals():
    props = GProp_GProps()
    BRepGProp.SurfaceProperties_s(face.wrapped, props)
    centroid = props.CentreOfMass()
    surf = BRepAdaptor_Surface(face.wrapped)
    surface_type = surf.GetType()
    # Classify by centroid position + surface type → assign label

# 3. Map OCC face order → STEP entity order via CLOSED_SHELL
#    Parse CLOSED_SHELL to get ordered ADVANCED_FACE entity IDs
#    These correspond 1:1 with cq.importers.importStep().faces().vals()

# 4. Write labels with regex: ADVANCED_FACE('old_name' → ADVANCED_FACE('new_label'
```

### Face classification strategies

- **Planar faces**: classify by centroid Z (top/bottom/floor), centroid X/Y (side faces), or normal direction (angled features like slot walls)
- **Cylindrical faces**: use `surf.Cylinder().Radius()` to distinguish outer surface, bore wall, channel floors, etc.
- **Conical faces**: chamfers (GeomAbs_Cone)
- **Toroidal faces**: fillets (GeomAbs_Torus)
- **Multiple faces of same type**: disambiguate by centroid position (e.g., cylindrical_1 vs cylindrical_2 by centroid X sign)
- **Slot/groove walls at an angle**: compute `sin(θ)*cx + cos(θ)*cy` and compare against the wall plane's d-parameter

### Gotchas

- **`edge.Center()` on circular edges** returns the center of the circle (on the axis), not a point on the circumference. To find a circular edge's radius, use the bounding box: `r = (bb.xmax - bb.xmin) / 2`.
- **STEP continuation lines** (lines starting with whitespace) must be joined to their parent entity before parsing. Join them before building the entity map.
- **Boolean operations can split faces unexpectedly.** A through bore that meets spline teeth at the same radius removes the bore floor and creates small root faces at the transition Z. Count faces after each boolean to verify.
- **Ellipse semi-axes for plane-cylinder intersections** depend only on the angle between the plane and cylinder axis, not the plane's position: `semi_major = R / cos(θ)`, `semi_minor = R`. Moving a plane parallel to itself doesn't change these.
- **Boolean cuts hang when a cut tool surface is tangent to an existing surface.** For example, cutting a window with an inner arc at exactly `hub_od_r` where the hub cylinder also lives creates a tangent condition that causes OCCT's boolean kernel to hang indefinitely. Fix: offset the cut tool surface slightly outside (e.g., `hub_od_r + 0.5`) so it intersects rather than osculates the existing surface, leaving the original feature protruding slightly. Then clean up with a separate annular cut to restore the original cylinder. This avoids tangency while producing clean geometry.
- **Union operations fill in previously-cut voids.** If you cut a bore, then union a solid that overlaps the bore, the union fills it back in. All cuts through shared volumes must go **after** all unions. This applies to any central bore/taper when a crank arm or similar feature passes through the same region.
- **Fillets fail on edges created by boolean unions (BRep_API: command not done).** Even 1mm fillets fail on union seam edges. **Workaround**: fillet the standalone solid BEFORE unioning it to the main body. This works for simple fillets (e.g., rounding arm edges) but not for the intersection curve itself.
- **Filleting curved bodies before union creates excessive fragment faces.** Filleting a cylinder (e.g., pedal boss) before unioning it to another curved body can produce 100+ tiny fragment faces from the boolean intersection of the fillet torus with the other body. No clean workaround in CadQuery — accept the limitation or skip the fillet.
- **CadQuery loft produces BSplineSurface, not Plane.** A loft between two square profiles (e.g., for a square taper) creates BSpline faces even though the result is geometrically planar. The face classifier must handle `GeomAbs_BSplineSurface` for these cases.
- **Annular cuts must be Z-limited to avoid cutting through spider webs.** When turning down a hub boss that's embedded in a spider structure, a full-height annular cut removes the spider web material between the tapers. Split the cut into segments that only cover where the boss actually protrudes beyond the taper surfaces.
- **Compute taper intersection Z before writing cuts.** For a conical taper at slope m meeting a cylinder at radius r, calculate the exact Z where they meet. Don't estimate — use the geometry: `Z_taper(r) = Z_vertex - m * (r - r_vertex)`. This avoids trial-and-error cuts that clip adjacent features.
- **Extrusion-based handle union can silently fail.** Extruding a 2D arc profile and unioning it to a revolved body may produce a COMPOUND instead of a fused SOLID — `union()` returns the original body unchanged. CadQuery's `.sweep()` along a centerline path works where extrusion fails. Sweep also avoids the twist artifacts that extrusion of arc profiles can produce.
- **Full rounds via revolved profile, not fillet API.** A full round on a rim (fillet radius = wall_thickness / 2) can be built directly into the revolved cross-section as quarter-circle arcs on both the outer body and cavity profiles. Both arcs share the same center point (midwall, height - rim_r), creating a perfect semicircular rim. This avoids the fillet API entirely.
- **Fillets on union seam edges CAN work for smooth geometry.** The crankset found that fillets on union seam edges always fail (BRep_API: command not done). However, the coffee mug (smooth surface of revolution + swept solid) successfully filleted union seam edges at 4mm. The difference appears to be geometry complexity — smooth curved intersections succeed where angular/multi-feature intersections fail. Always try the fillet; don't assume it will fail.
- **Rounded cross-section sweep avoids fillet API for handle edges.** Instead of sweeping a sharp rectangle and filleting edges afterward, sweep a rounded rectangle (rectangle with corner arcs) built from `lineTo` + `threePointArc` segments. This produces the same visual result with no fillet API calls and no fragment risk from pre-union filleting.
- **Handle face classifier must adapt to cross-section shape.** A sharp rectangular sweep produces cylinder faces with Y span = ±handle_half_width. A rounded rectangle sweep produces cylinder faces with Y span = ±(handle_half_width - fillet_r) for the flat portions, plus SurfaceOfRevolution faces with narrow Y bands (fillet_r wide) for the corners. The Y span is the primary discriminator — body cylinders (full revolutions) have Y spans equal to their diameter, while handle faces are always within handle width.
- **Handle geometry has coupled parameters.** Moving the handle arc center closer to the body (reducing handle_main_cx) can cause the top attachment point to fall inside the main arc circle, making transition arc geometry impossible (no real solution). When adjusting one handle parameter, check that the attachment points remain outside the main arc: `distance(attachment_pt, arc_center) > arc_radius`.

### Interpreting CAD instructions and resolving ambiguity

CAD edit instructions from users tend to hit a few predictable ambiguity categories:

- **Geometric reference**: "Add a chamfer on the top edge" — which edge? The outer rim, the bore rim, or the channel corner? Faces often share edges, so "the edge of X" is underspecified.
- **Measurement datum**: "10mm from the face" — measured to the nearest wall of the feature, the centerline, or the far wall? Channel/groove positioning is especially sensitive to this.
- **Feature direction**: "Add a bore from the top" — blind or through? If blind, how deep? Does "from the top" mean starting at the top face or referenced from it?
- **Naming conventions**: "Add a spline" — internal or external? Involute or straight-sided? Number of teeth, module, pressure angle?

**Face labels as shared vocabulary.** Once a part has labeled faces, ambiguity resolution becomes much more precise. Instead of "the edge between the bore and the top face," the user (or Claude) can say "the edge between `bore.wall` and `top`" or "the edge where `channel.bottom.floor` meets `channel.bottom.wall_lower`." This turns vague geometric references into exact topological references that map directly to OCC entities.

**Resolution strategy**: When an instruction is ambiguous, ask targeted clarifying questions that reference specific face labels. One or two questions typically resolve the ambiguity completely. For example: "Should the chamfer go on the edge between `top` and `cylinder`, or between `top` and `bore.wall`?"

### Re-labeling faces
Run STEP Labeler: `cd ../steplabeler && python app.py ../AI_CAD/blkarc_slot-Body.step`

## Tools

- **FreeCAD**: Native CAD modeling (produces `.FCStd` and `.step` exports)
- **CadQuery** (`pip install cadquery`): Programmatic CAD geometry generation via Python. Used for rebuilding geometry when topology changes.
- **STEP Labeler** (`../steplabeler/`): Face labeling web UI for manual/visual labeling
- **OCC (via CadQuery)**: `BRepGProp` for face centroids/areas, `BRepAdaptor_Surface` for surface type detection, `GeomAbs_*` for type classification
- **render_step.py**: PyVista-based offscreen renderer for visual verification (see below)

### Visual verification with render_step.py

After building or modifying geometry, **render and inspect the result** before moving on. This closes the visual feedback loop — Claude can see the geometry via PNG instead of relying solely on face counts and user verification.

```bash
# Render from STEP file (4 views: iso, front, back, top)
python render_step.py crankset/crankset.step

# Add section cut (5th view, Y=0 by default)
python render_step.py crankset/crankset.step --section

# Render directly from build script (no STEP export needed)
python render_step.py --cq crankset/build_crankset.py --section

# Override cameras (inline JSON or file)
python render_step.py part.step --camera '{"iso": {"direction": [1,0.5,-0.4]}, "section": {"normal": [1,0,0]}}'
python render_step.py part.step --camera views.json
```

**Camera JSON format** — all fields optional, merged with defaults:
```json
{
    "iso":     {"direction": [1, 1, -0.6], "up": [0, 0, 1], "zoom": 0.85},
    "front":   {"direction": [0, 1, 0]},
    "section": {"direction": [0, 1, 0], "normal": [0, 1, 0], "origin": [0, 0, 0]}
}
```

**When to render:**
- After each new feature (boolean cut, union, fillet) to verify shape
- After build order changes (cuts moving before/after unions)
- When internal features matter (bores, tapers, pockets) — use `--section`
- Before asking the user to visually verify — catch obvious errors yourself first

**Section cuts are the highest-value view.** Most geometry bugs during the crankset build (hub turn-down cutting through spider, union filling bore, bore not reaching arm top) were invisible from the outside but immediately obvious in cross-section.

Requires: `pip install pyvista cadquery` (PyVista 0.44.x with VTK 9.3.x for CadQuery compatibility)

---

## Session Log: Interactive CAD Workflow Proof-of-Concept

This section captures the findings from the first extended session where Claude Code was used as an interactive CAD tool, driven by conversational instructions from an engineer.

### What was built

**blkarc_slot modifications** (existing part):
1. Analyzed slot geometry: width = 10mm, angle = 25° from x_pos face
2. Narrowed slot from 10mm to 7mm via direct STEP text editing (14 entity updates, topology unchanged)
3. Deepened slot by 7mm — required CadQuery rebuild because the floor dropped below the cylinder-to-planar transition, changing topology
4. Changed slot angle from 25° to 10° via CadQuery rebuild

**cylinder part** (built from scratch, iteratively):
1. Base cylinder: 10mm dia × 50mm, 3 faces (bottom, top, cylinder)
2. 5mm blind bore from top, 30mm deep → 5 faces
3. 16 internal spline teeth (triangular, 0.5mm tall, R_min=2.5, R_max=3.0) → 36 faces
4. 5mm through bore from bottom (merges with spline at Z=20) → 52 faces
5. 30° chamfer on top, 8mm OD → 53 faces
6. Matching chamfer on bottom → 54 faces
7. 1.5mm × 0.5mm annular channels on OD, 10mm from each face → 62 faces
8. 0.1mm fillets on channel floor edges → 66 faces

Final output: `cylinder.step` (66 labeled faces) + `build_cylinder.py` (persistent build script)

### Methodology that emerged

Two distinct approaches were used depending on the edit:

- **STEP text surgery**: For geometry-only changes (moving walls, changing dimensions). Requires tracing the entity reference graph to find all affected CARTESIAN_POINT entries. Fast, preserves all other entities exactly. Used for the slot width change.

- **CadQuery rebuild + OCC labeling**: For topology changes (adding features, boolean cuts). Build with CadQuery, export STEP, classify faces via OCC surface type + centroid analysis, map labels through CLOSED_SHELL entity ordering, write back with regex. Used for slot deepening, angle change, and the entire cylinder build.

The decision point: if intersection curves between surfaces change, rebuild. If existing geometry just translates, text-edit.

### Key finding: practical scope

The features built in this session — cylinders, bores, splines, chamfers, channels, fillets, boolean cuts — represent roughly 85% of mechanical engineering parts. Shafts, bushings, housings, brackets, plates, manifolds, and fixtures are all combinations of these prismatic and rotational features.

The remaining ~15% (complex surface modeling — turbine blades, aerodynamic fairings, Class A surfaces) requires specialized CAD tools and is exactly where human engineers add the most value. This workflow is not trying to replace that.

### Known limitations

| Limitation | Impact | Mitigation |
|-----------|--------|------------|
| No visual feedback | Can't see the result; rely on user verification | User is the visual loop; OCC face counts provide sanity checks |
| CadQuery surface modeling | Weak for lofts, sweeps on curved paths, variable-radius fillets | Use SolidWorks/FreeCAD for those features, label with STEP Labeler |
| Face classifier complexity | Gets harder as features multiply, especially similar geometry at similar positions | Solvable case-by-case; not a wall |
| No round-trip to CAD tools | Build script is the feature tree; importing STEP back gives a dumb solid | Accept this; the build script is the source of truth |
| No drawings/GD&T/simulation | Output is geometry only | Out of scope for training data generation |

### Errors encountered and resolved

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| Both cylindrical faces got same label | OCC centroid X-sign needed, not STEP text parsing | Used `cq.importers.importStep()` centroid with CLOSED_SHELL mapping |
| Spline root faces misclassified as flanks | Through bore removed bore.floor, creating 16 horizontal faces at Z=20 | Check face normal Z-component (`nz > 0.9`) before spline flank classifier |
| Fillet edge selector found no edges | `edge.Center()` on circular edges returns circle center (0,0,z), not circumference point | Use bounding box: `edge_r = (bb.xmax - bb.xmin) / 2` |
| Counter display bug after chamfer | Indentation error in summary print loop | Labels were correct; only the summary was wrong |

---

## Session Log: Crankset Build

Second extended session — building a real-world multi-feature part from a hand sketch, driven by iterative engineer instructions.

### What was built

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

### What worked

**Machinist approach (stock → subtract).** Starting from a stock cylinder and removing material maps directly to CadQuery's boolean operations. Each feature is an isolated cut, easy to debug and reorder independently.

**Incremental build-and-verify loop.** Adding one feature at a time with user visual verification caught geometry problems immediately. The hub turn-down cutting through the spider would have been much harder to diagnose in a monolithic build.

**Pre-union fillets.** Filleting standalone solids before `union()` works around OCCT's inability to fillet union seam edges. The 4mm arm edge fillets and 3mm hub boss fillets both succeeded this way.

**Face classification scaling.** The centroid + surface type approach scaled to 88 faces. Adding a new feature type typically required 2-5 lines of classifier code. BSplineSurface fallback handled the loft-generated taper walls.

**Face labels as shared vocabulary.** Once faces were named, the user could give precise instructions like "add a fillet where hub.boss meets planar_z12" instead of ambiguous geometric descriptions.

### What didn't work

**Build order errors were the most common mistake.** The axle bore was placed before the crank arm union — the arm solid filled the bore back in. The pedal bore had the same issue earlier. **Rule: all cuts through shared volumes must go after all unions.** This is the single most important lesson.

**Hub turn-down took three attempts.** Failed to trace the taper intersection math before writing cuts. First cut had OD too large (went through spider arms). Second cut had Z range too tall (went through spider web). Third attempt needed splitting into back-only. **Rule: compute `Z_taper(r)` at the cut boundaries before writing any code.**

**No visual feedback is the biggest limitation.** Every geometry edit was a guess until user confirmation. Face counts catch added/removed faces but not shape errors. The hub turn-down especially — face count looked fine but the shape was wrong.

**Boss fillets were a dead end.** Filleting the pedal boss before union produced 114 fragment faces from curved-on-curved boolean intersections. Multiple approaches tried (bore-first, selective edges, smaller radius) — all produced the same fragmentation. Accepted as an OCCT limitation.

**Spatial reasoning errors are expensive.** Not understanding which volumes overlap led to most iteration. If a "what material exists at point (x,y,z)" query or cross-section render were available, most debugging would have been unnecessary.

### Key patterns established

| Pattern | When to use |
|---------|------------|
| Pre-union fillet | Need fillets on edges that will become union seams |
| Cuts after all unions | Any bore/hole through regions that unions will fill |
| Tangent avoidance (offset + 0.5mm) | Cut tool surface coincides with existing surface |
| Z-limited annular cuts | Turning down a boss embedded in tapered structure |
| BSplineSurface classifier fallback | Loft operations produce BSpline instead of expected types |
| Edge selector by bounding box radius + Z | Selecting circular edges for fillets |

### Errors encountered and resolved

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

---

## Session Log: Coffee Mug Build

Third extended session — building a consumer product (coffee mug) with curved handle geometry, demonstrating sweep-based construction and successful union seam fillets.

### What was built

**Coffee mug** (built from scratch iteratively):
1. Solid body of revolution (cylindrical bands + conical taper) → 5 faces
2. Bulge arc on body (threePointArc replacing cone) → 5 faces
3. Cavity hollowing (5mm wall, open top) → 9 faces
4. Handle via sweep (rounded rectangle cross-section along 3-arc path) → 18 faces (after union + cavity)
5. Full-round rim (built into revolved profiles) → +2 faces
6. Handle-body junction fillets (4mm) → 50 faces

Final output: `coffee_mug/coffee_mug.step` (50 labeled faces) + `coffee_mug/build_mug.py` (persistent build script)

### What worked

**Sweep for handle construction.** CadQuery's `.sweep()` along a centerline path with a rectangular cross-section produced a clean solid that unioned successfully with the revolved body. Extrusion of the same profile failed silently (produced COMPOUND instead of fused SOLID).

**Rounded cross-section instead of post-sweep fillets.** Instead of sweeping a sharp rectangle and filleting edges afterward, the cross-section was drawn as a rounded rectangle (lines + arcs). This avoids the fillet API entirely for handle edge rounding and eliminates the risk of fillet-on-curved-body fragment faces.

**Full round via profile modification.** The rim full round (r = wall_thickness/2) was built directly into both the outer body and cavity revolved profiles as quarter-circle arcs sharing the same center point. No fillet API needed.

**Union seam fillets succeeded.** The 4mm fillet on handle-body junction edges (union seam edges) worked — contradicting the crankset finding that "fillets on union seam edges always fail." The key difference: the mug has smooth curved surfaces (surface of revolution + swept solid) vs the crankset's angular multi-feature geometry. OCCT's fillet kernel handles smooth intersections better.

**Custom edge selector for junction fillets.** A CadQuery Selector subclass (`HandleJunctionSelector`) identified junction edges by checking: Y span within handle width, Z near attachment heights, X near body outer radius. This was more reliable than BoxSelector for finding the specific intersection edges.

**Parameter changes as one-line edits.** Adjusting handle size (cx from 70→65→60, radius from 19→15), fillet radius (2→4mm), and other dimensions required only parameter changes — the build script re-ran cleanly each time.

### What didn't work

**Extrusion-based handle union failed silently.** A 2D handle profile (outer + inner edges) extruded ±9mm from XZ plane created a valid 10-face solid. But `outer.union(handle)` returned the original body unchanged — OCC's `BRepAlgoAPI_Fuse` produced a COMPOUND rather than a single SOLID. `BRepAlgoAPI_Common` confirmed the solids did intersect. A simple box union worked fine. Root cause appears to be OCCT's boolean kernel failing on the intersection of extruded arc surfaces with the revolved body surface.

**Fillet API failed for rim full round.** Attempting `.edges(BoxSelector(...)).fillet(wall_thickness/2)` on the two circular rim edges failed with "BRep_API: command not done." This was expected (union seam-adjacent edges) and was solved by building the round into the profile.

**Handle parameter coupling.** Reducing `handle_main_cx` from 70 to 60 caused the top attachment point (44.2, 87.0) to fall inside the main arc circle (center 60, radius 19, distance 17.3 < 19). No transition arc of any radius or tangency type can connect a point inside a circle to the circle. Required also reducing `handle_main_r` from 19 to 15.

**Face classifier needed repeated updates.** Each geometry change (sharp→rounded cross-section, adding fillets) changed the surface types and bounding boxes of handle faces. The Y-span discriminator proved most robust across changes — body surfaces of revolution span their full diameter, while handle faces span only the handle width.

### Key patterns established

| Pattern | When to use |
|---------|------------|
| Sweep along centerline path | Handle-like features attached to curved bodies (extrusion may fail) |
| Rounded cross-section sweep | Need fillets on swept solid edges without fillet API |
| Profile-embedded full round | Full round on rim/lip of revolved body |
| Custom Selector subclass | Edge selection for fillets when position-based filtering is needed |
| Y-span face discriminator | Distinguishing handle faces from body faces on surface of revolution |
| Try union seam fillets first | Smooth geometry may succeed where angular geometry fails |

### Errors encountered and resolved

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| Handle extrusion union returned original body | OCCT boolean kernel fails on extruded arc ∩ revolved body | Switched to `.sweep()` along centerline path |
| Rim fillet failed (BRep_API: command not done) | Fillet on edges adjacent to union seams | Built full round into revolved profile (quarter-circle arcs) |
| Handle cx=60 → "No real solution for transition center" | Top attachment point inside main arc circle (d=17.3 < r=19) | Reduced handle_main_r from 19 to 15 |
| Handle cylinder faces unlabeled after rounded cross-section | Y span changed from ±9 to ±5 (hw - fillet_r) | Updated classifier to use `handle_half_width - handle_fillet_r` |
| Handle corner arcs classified as body.bulge | SurfaceOfRevolution with narrow Y band not distinguished from body | Added Y-span check: narrow band → handle, full span → body |
| Junction fillet faces classified as body.bulge | BSplineSurface fillet patches near body surface (cx < bulge_r) | Added Y-span check in BSplineSurface classifier → handle.fillet |
