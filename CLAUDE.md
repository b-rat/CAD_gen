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

## File Contents

| File | Description |
|------|-------------|
| `blkarc_slot.FCStd` | FreeCAD native project file (block with arc-shaped top and slot) |
| `blkarc_slot-Body.step` | STEP export with unnamed faces |
| `blkarc_slot-Body_named.step` | STEP export with semantically labeled faces (modified: 7mm slot width, 10° angle, deepened 7mm) |
| `build_cylinder.py` | Persistent build script for cylinder part (parameters + geometry + labeling) |
| `cylinder.step` | 66-face labeled cylinder: spline bore, chamfers, channels, fillets |
| `*.FCBak` | FreeCAD auto-backup files |

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
