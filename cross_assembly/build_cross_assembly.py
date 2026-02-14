import cadquery as cq
import re
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import (GeomAbs_Plane, GeomAbs_Cylinder, GeomAbs_Torus,
                          GeomAbs_BSplineSurface)

# ── Parameters ──
cyl_diameter = 10.0
cyl_radius = cyl_diameter / 2.0
cyl_length = 60.0
y_offset = 20.0
wall_thickness = 10.0
split_gap = 0.5
fillet_ext = 3.0              # external edge fillet (cast radius)
bolt_clearance_r = 2.75       # M5 clearance hole radius (5.5mm dia)

# Derived block dimensions
block_x = cyl_diameter + 2 * wall_thickness  # 30
block_z = cyl_diameter + 2 * wall_thickness  # 30
block_y_min = -cyl_radius - wall_thickness   # -15
block_y_max = y_offset + cyl_radius + wall_thickness  # 35
block_y = block_y_max - block_y_min          # 50
block_center_y = (block_y_min + block_y_max) / 2  # 10

# Stepped split transition
split_y = y_offset / 2  # 10

# Bolt positions
# Front bolts: Z-direction, near cyl_x bore at (y=0, z=0)
bolt_front = [(10, -8), (-10, -8)]     # (x, y) pairs
# Back bolts: X-direction, near cyl_z bore at (x=0, y=20)
bolt_back = [(30, 10), (30, -10)]      # (y, z) pairs

OUTPUT_PATH = "cross_assembly/cross_assembly.step"


def make_box(xmin, xmax, ymin, ymax, zmin, zmax):
    """Axis-aligned box from min/max coordinates."""
    return (
        cq.Workplane("XY")
        .transformed(offset=(
            (xmin + xmax) / 2,
            (ymin + ymax) / 2,
            (zmin + zmax) / 2,
        ))
        .box(xmax - xmin, ymax - ymin, zmax - zmin)
    )


def build_geometry():
    """Two cylinders + stepped-split clamp block (casting-ready).

    Cast features: filleted external edges (3mm).
    Machined features: bores, split faces, bolt holes.
    Stepped split: z=0 for y<10, x=0 for y>10.
    """
    # ── Cylinders ──
    cyl_x = (
        cq.Workplane("YZ")
        .circle(cyl_radius)
        .extrude(cyl_length / 2, both=True)
    )
    cyl_z = (
        cq.Workplane("XY")
        .transformed(offset=(0, y_offset, 0))
        .circle(cyl_radius)
        .extrude(cyl_length / 2, both=True)
    )

    # ── Block: cast body ──
    block = (
        cq.Workplane("XY")
        .transformed(offset=(0, block_center_y, 0))
        .box(block_x, block_y, block_z)
    )
    # Cast fillets on all external edges
    block = block.edges().fillet(fillet_ext)
    print(f"  Block after fillets: {len(block.faces().vals())} faces")

    # ── Machine bores ──
    big = 100
    bore_x = (
        cq.Workplane("YZ")
        .circle(cyl_radius)
        .extrude(big, both=True)
    )
    bore_z = (
        cq.Workplane("XY")
        .transformed(offset=(0, y_offset, 0))
        .circle(cyl_radius)
        .extrude(big, both=True)
    )
    block = block.cut(bore_x).cut(bore_z)
    print(f"  Block after bores: {len(block.faces().vals())} faces")

    # ── Stepped split ──
    g = split_gap / 2
    eps = 0.1

    # L-cutter A: removes lower-front + left-back
    a1 = make_box(-big, big, -big, split_y + eps, -big, g)
    a2 = make_box(-big, g, split_y - eps, big, -big, big)
    cutter_a = a1.union(a2)
    half_a = block.cut(cutter_a)

    # L-cutter B: removes upper-front + right-back
    b1 = make_box(-big, big, -big, split_y + eps, -g, big)
    b2 = make_box(-g, big, split_y - eps, big, -big, big)
    cutter_b = b1.union(b2)
    half_b = block.cut(cutter_b)

    # ── Bolt holes (drilled) ──
    # Front bolts: Z-direction at cyl_x bore region
    for x_pos, y_pos in bolt_front:
        bolt = (
            cq.Workplane("XY")
            .transformed(offset=(x_pos, y_pos, 0))
            .circle(bolt_clearance_r)
            .extrude(big, both=True)
        )
        half_a = half_a.cut(bolt)
        half_b = half_b.cut(bolt)

    # Back bolts: X-direction at cyl_z bore region
    for y_pos, z_pos in bolt_back:
        bolt = (
            cq.Workplane("YZ")
            .transformed(offset=(y_pos, z_pos, 0))
            .circle(bolt_clearance_r)
            .extrude(big, both=True)
        )
        half_a = half_a.cut(bolt)
        half_b = half_b.cut(bolt)

    for name, body in [("half_a", half_a), ("half_b", half_b)]:
        nf = len(body.faces().vals())
        ns = len(body.solids().vals())
        print(f"  {name}: {nf} faces, {ns} solids")

    return cyl_x, cyl_z, half_a, half_b


def classify_faces(filepath):
    """Face classification for the assembly."""
    result = cq.importers.importStep(filepath)
    faces = result.faces().vals()
    labels = []

    for i, face in enumerate(faces):
        props = GProp_GProps()
        BRepGProp.SurfaceProperties_s(face.wrapped, props)
        centroid = props.CentreOfMass()
        cx, cy, cz = centroid.X(), centroid.Y(), centroid.Z()

        surf = BRepAdaptor_Surface(face.wrapped)
        stype = surf.GetType()

        if stype == GeomAbs_Cylinder:
            axis = surf.Cylinder().Axis().Direction()
            r = surf.Cylinder().Radius()
            ax, ay, az = abs(axis.X()), abs(axis.Y()), abs(axis.Z())
            if abs(r - cyl_radius) < 0.1:
                # Bore or cylinder body
                if ax > 0.9:
                    if abs(cy) < 1.0 and abs(cz) < 6.0:
                        labels.append("cyl_x.wall")
                    else:
                        labels.append(f"block.bore_x_{'a' if cz > 0 else 'b'}")
                elif az > 0.9:
                    if abs(cy - y_offset) < 1.0 and abs(cx) < 6.0:
                        labels.append("cyl_z.wall")
                    else:
                        labels.append(f"block.bore_z_{'a' if cx > 0 else 'b'}")
                else:
                    labels.append(f"cyl_{i}")
            elif abs(r - bolt_clearance_r) < 0.1:
                labels.append(f"block.bolt_{i}")
            else:
                labels.append(f"cyl_{i}")
        elif stype == GeomAbs_Torus:
            labels.append(f"block.fillet_{i}")
        elif stype == GeomAbs_Plane:
            labels.append(f"plane_{i}")
        elif stype == GeomAbs_BSplineSurface:
            labels.append(f"block.fillet_{i}")
        else:
            labels.append(f"face_{i}")

    return labels


def write_labels(filepath, labels):
    """Write face labels into STEP file."""
    with open(filepath, "r") as f:
        step_text = f.read()

    cs_pattern = r"CLOSED_SHELL\s*\(\s*'[^']*'\s*,\s*\(([^)]+)\)\s*\)"
    cs_matches = re.findall(cs_pattern, step_text)

    face_ids = []
    for match in cs_matches:
        ids = re.findall(r"#(\d+)", match)
        face_ids.extend(ids)

    n = min(len(face_ids), len(labels))
    if len(face_ids) != len(labels):
        print(f"WARNING: {len(face_ids)} ADVANCED_FACEs vs {len(labels)} labels")

    for fid, label in zip(face_ids[:n], labels[:n]):
        pattern = rf"(#{fid}\s*=\s*ADVANCED_FACE\s*\()\s*'[^']*'"
        replacement = rf"\1'{label}'"
        step_text = re.sub(pattern, replacement, step_text)

    with open(filepath, "w") as f:
        f.write(step_text)
    print(f"Labeled {n} faces")


if __name__ == "__main__":
    cyl_x, cyl_z, half_a, half_b = build_geometry()

    assy = cq.Assembly()
    assy.add(cyl_x, name="cyl_x")
    assy.add(cyl_z, name="cyl_z")
    assy.add(half_a, name="block_half_a")
    assy.add(half_b, name="block_half_b")
    assy.save(OUTPUT_PATH)
    print(f"Exported to {OUTPUT_PATH}")

    labels = classify_faces(OUTPUT_PATH)
    print(f"Labels ({len(labels)}): {labels}")
    write_labels(OUTPUT_PATH, labels)
