"""
Build script for labeled L-bracket part.

Generates l_bracket.step with all features and face labels.

Usage:
    python build_l_bracket.py
"""

import cadquery as cq
import re
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.GeomAbs import GeomAbs_Plane
from OCP.BRepAdaptor import BRepAdaptor_Surface

# ============================================================
# Parameters
# ============================================================

vert_height = 50.0      # vertical leg total height (Z)
horiz_length = 100.0    # horizontal leg length (X)
width = 25.0            # depth into page (Y)
wall_thickness = 5.0    # uniform wall thickness

OUTPUT_PATH = "/Users/brianratliff/machine_learning/AI_CAD/l_bracket/l_bracket.step"


# ============================================================
# Geometry
# ============================================================

def build_geometry():
    """L-shaped cross-section on XZ plane, extruded along Y."""
    result = (
        cq.Workplane("XZ")
        .moveTo(0, 0)
        .lineTo(horiz_length, 0)
        .lineTo(horiz_length, wall_thickness)
        .lineTo(wall_thickness, wall_thickness)
        .lineTo(wall_thickness, vert_height)
        .lineTo(0, vert_height)
        .close()
        .extrude(width)
    )
    return result


# ============================================================
# Face labeling
# ============================================================

def classify_faces(filepath):
    """Classify all faces by centroid position. All faces are planar."""
    result = cq.importers.importStep(filepath)
    occ_faces = result.faces().vals()

    labels = []
    for face in occ_faces:
        props = GProp_GProps()
        BRepGProp.SurfaceProperties_s(face.wrapped, props)
        cog = props.CentreOfMass()
        cx, cy, cz = cog.X(), cog.Y(), cog.Z()

        surf = BRepAdaptor_Surface(face.wrapped)
        stype = surf.GetType()

        label = "?"

        if stype == GeomAbs_Plane:
            pln = surf.Plane()
            axis = pln.Axis().Direction()
            nx, ny, nz = abs(axis.X()), abs(axis.Y()), abs(axis.Z())

            if nz > 0.9:
                # Horizontal faces: bottom (Z=0), shelf (Z=5), top (Z=50)
                if abs(cz) < 0.1:
                    label = "bottom"
                elif abs(cz - wall_thickness) < 0.1:
                    label = "shelf"
                elif abs(cz - vert_height) < 0.1:
                    label = "top"
            elif nx > 0.9:
                # Vertical faces normal to X: vert_outer (X=0), vert_inner (X=5), horiz_end (X=100)
                if abs(cx) < 0.1:
                    label = "vert_outer"
                elif abs(cx - wall_thickness) < 0.1:
                    label = "vert_inner"
                elif abs(cx - horiz_length) < 0.1:
                    label = "horiz_end"
            elif ny > 0.9:
                # Front/back faces normal to Y
                # XZ workplane extrudes along -Y, so faces at Y=0 and Y=-width
                if abs(cy) < 0.1:
                    label = "front"
                elif abs(abs(cy) - width) < 0.1:
                    label = "back"

        labels.append(label)

    return labels


def write_labels(filepath, face_labels):
    """Write face labels into STEP file via CLOSED_SHELL entity mapping."""
    with open(filepath) as f:
        content = f.read()

    # Join STEP continuation lines
    lines = content.split('\n')
    joined = []
    for line in lines:
        if line and line[0] in (' ', '\t') and joined:
            joined[-1] += line
        else:
            joined.append(line)

    # Parse entities
    entities = {}
    for i, line in enumerate(joined):
        m = re.match(r'^#(\d+)\s*=\s*(.*)', line)
        if m:
            entities[int(m.group(1))] = (m.group(2).strip(), i)

    # Find CLOSED_SHELL → ordered ADVANCED_FACE entity IDs
    face_eids = None
    for eid, (text, _) in entities.items():
        if text.startswith('CLOSED_SHELL'):
            face_eids = [int(x) for x in re.findall(r'#(\d+)', text)]
            break

    assert face_eids is not None, "No CLOSED_SHELL found in STEP file"
    assert len(face_eids) == len(face_labels), (
        f"STEP has {len(face_eids)} faces but got {len(face_labels)} labels"
    )

    # Write labels
    for idx, eid in enumerate(face_eids):
        text, line_idx = entities[eid]
        joined[line_idx] = re.sub(
            r"ADVANCED_FACE\s*\(\s*'[^']*'",
            f"ADVANCED_FACE('{face_labels[idx]}'",
            joined[line_idx],
        )

    with open(filepath, 'w') as f:
        f.write('\n'.join(joined))


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    print("Building geometry...")
    result = build_geometry()

    print(f"Exporting to {OUTPUT_PATH}")
    cq.exporters.export(result, OUTPUT_PATH)

    print("Classifying faces...")
    labels = classify_faces(OUTPUT_PATH)

    print("Writing labels...")
    write_labels(OUTPUT_PATH, labels)

    # Summary
    print(f"\n{len(labels)} faces:")
    for l in labels:
        print(f"  {l}")

    unlabeled = [l for l in labels if l == "?"]
    if unlabeled:
        print(f"\n  WARNING: {len(unlabeled)} unlabeled faces")
    else:
        print("\nAll faces labeled.")
