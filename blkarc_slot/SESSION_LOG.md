# Session Log: Interactive CAD Workflow Proof-of-Concept

This section captures the findings from the first extended session where Claude Code was used as an interactive CAD tool, driven by conversational instructions from an engineer.

## What was built

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

## Methodology that emerged

Two distinct approaches were used depending on the edit:

- **STEP text surgery**: For geometry-only changes (moving walls, changing dimensions). Requires tracing the entity reference graph to find all affected CARTESIAN_POINT entries. Fast, preserves all other entities exactly. Used for the slot width change.

- **CadQuery rebuild + OCC labeling**: For topology changes (adding features, boolean cuts). Build with CadQuery, export STEP, classify faces via OCC surface type + centroid analysis, map labels through CLOSED_SHELL entity ordering, write back with regex. Used for slot deepening, angle change, and the entire cylinder build.

The decision point: if intersection curves between surfaces change, rebuild. If existing geometry just translates, text-edit.

## Key finding: practical scope

The features built in this session — cylinders, bores, splines, chamfers, channels, fillets, boolean cuts — represent roughly 85% of mechanical engineering parts. Shafts, bushings, housings, brackets, plates, manifolds, and fixtures are all combinations of these prismatic and rotational features.

The remaining ~15% (complex surface modeling — turbine blades, aerodynamic fairings, Class A surfaces) requires specialized CAD tools and is exactly where human engineers add the most value. This workflow is not trying to replace that.

## Known limitations

| Limitation | Impact | Mitigation |
|-----------|--------|------------|
| No visual feedback | Can't see the result; rely on user verification | User is the visual loop; OCC face counts provide sanity checks |
| CadQuery surface modeling | Weak for lofts, sweeps on curved paths, variable-radius fillets | Use SolidWorks/FreeCAD for those features, label with STEP Labeler |
| Face classifier complexity | Gets harder as features multiply, especially similar geometry at similar positions | Solvable case-by-case; not a wall |
| No round-trip to CAD tools | Build script is the feature tree; importing STEP back gives a dumb solid | Accept this; the build script is the source of truth |
| No drawings/GD&T/simulation | Output is geometry only | Out of scope for training data generation |

## Errors encountered and resolved

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| Both cylindrical faces got same label | OCC centroid X-sign needed, not STEP text parsing | Used `cq.importers.importStep()` centroid with CLOSED_SHELL mapping |
| Spline root faces misclassified as flanks | Through bore removed bore.floor, creating 16 horizontal faces at Z=20 | Check face normal Z-component (`nz > 0.9`) before spline flank classifier |
| Fillet edge selector found no edges | `edge.Center()` on circular edges returns circle center (0,0,z), not circumference point | Use bounding box: `edge_r = (bb.xmax - bb.xmin) / 2` |
| Counter display bug after chamfer | Indentation error in summary print loop | Labels were correct; only the summary was wrong |
