"""
Build script for labeled cylinder part.

Generates cylinder.step with all features and face labels.

Usage:
    python build_cylinder.py
"""

import cadquery as cq
import math
import re
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.GeomAbs import (
    GeomAbs_Plane, GeomAbs_Cylinder, GeomAbs_Cone,
    GeomAbs_Torus, GeomAbs_BSplineSurface,
)
from OCP.BRepAdaptor import BRepAdaptor_Surface

# ============================================================
# Parameters
# ============================================================

# Base cylinder
cyl_radius = 5.0        # 10mm diameter
cyl_height = 50.0

# Internal spline (in bore, Z=20 to Z=50)
n_teeth = 16
spline_r_min = 2.5      # tooth tips (= bore diameter / 2)
spline_r_max = 3.0      # roots (grooves 0.5mm into material)
spline_depth = 30.0     # from top face downward

# Through bore (Z=0 to Z=50)
through_bore_r = 2.5    # 5mm diameter, matches spline tooth tips

# Chamfers (top and bottom, identical)
chamfer_outer_r = 4.0   # 8mm OD
chamfer_angle = 30.0    # degrees from face surface
chamfer_depth = chamfer_outer_r * math.tan(math.radians(chamfer_angle))

# Annular channels (top and bottom, identical)
channel_width = 1.5
channel_depth = 0.5     # into OD
channel_offset = 10.0   # from face to nearest channel wall
channel_floor_r = cyl_radius - channel_depth  # R=4.5
channel_fillet_r = 0.1  # fillet on floor-wall edges

# Derived positions
ch_bot_z = channel_offset                              # 10.0
ch_top_z = cyl_height - channel_offset - channel_width  # 38.5

OUTPUT_PATH = "/Users/brianratliff/machine_learning/AI_CAD/cylinder.step"


# ============================================================
# Geometry
# ============================================================

def build_geometry():
    # Base cylinder
    result = cq.Workplane("XY").circle(cyl_radius).extrude(cyl_height)

    # Spline bore (star-shaped, Z=20 to Z=50)
    pts = []
    for i in range(n_teeth * 2):
        angle = i * math.pi / n_teeth
        r = spline_r_min if i % 2 == 0 else spline_r_max
        pts.append((r * math.cos(angle), r * math.sin(angle)))

    bore_wp = cq.Workplane("XY").workplane(offset=cyl_height - spline_depth)
    bore_wp = bore_wp.moveTo(pts[0][0], pts[0][1])
    for p in pts[1:]:
        bore_wp = bore_wp.lineTo(p[0], p[1])
    result = result.cut(bore_wp.close().extrude(spline_depth))

    # Through bore
    result = result.cut(
        cq.Workplane("XY").circle(through_bore_r).extrude(cyl_height)
    )

    # Top chamfer
    result = result.cut(
        cq.Workplane("XZ")
        .moveTo(0, cyl_height - chamfer_depth)
        .lineTo(chamfer_outer_r, cyl_height)
        .lineTo(0, cyl_height)
        .close()
        .revolve(360, (0, 0), (0, 1))
    )

    # Bottom chamfer
    result = result.cut(
        cq.Workplane("XZ")
        .moveTo(0, chamfer_depth)
        .lineTo(chamfer_outer_r, 0)
        .lineTo(0, 0)
        .close()
        .revolve(360, (0, 0), (0, 1))
    )

    # Bottom channel
    result = result.cut(
        cq.Workplane("XY").workplane(offset=ch_bot_z)
        .circle(cyl_radius + 1).circle(channel_floor_r)
        .extrude(channel_width)
    )

    # Top channel
    result = result.cut(
        cq.Workplane("XY").workplane(offset=ch_top_z)
        .circle(cyl_radius + 1).circle(channel_floor_r)
        .extrude(channel_width)
    )

    # Fillets on channel floor-wall edges
    target_zs = [ch_bot_z, ch_bot_z + channel_width,
                 ch_top_z, ch_top_z + channel_width]

    class ChannelFloorEdgeSelector(cq.Selector):
        def filter(self, objectList):
            out = []
            for obj in objectList:
                c = obj.Center()
                bb = obj.BoundingBox()
                edge_r = (bb.xmax - bb.xmin) / 2
                if abs(edge_r - channel_floor_r) < 0.2:
                    for tz in target_zs:
                        if abs(c.z - tz) < 0.15:
                            out.append(obj)
                            break
            return out

    result = result.edges(ChannelFloorEdgeSelector()).fillet(channel_fillet_r)

    return result


# ============================================================
# Face labeling
# ============================================================

def classify_faces(filepath):
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
        r_centroid = math.sqrt(cx**2 + cy**2)

        label = "?"

        if stype == GeomAbs_Cylinder:
            r = surf.Cylinder().Radius()
            if abs(r - cyl_radius) < 0.1:
                label = "cylinder"
            elif abs(r - through_bore_r) < 0.1:
                label = "bore.wall"
            elif abs(r - channel_floor_r) < 0.2:
                label = ("channel.bottom.floor" if cz < 25
                         else "channel.top.floor")

        elif stype == GeomAbs_Cone:
            label = "chamfer.top" if cz > 25 else "chamfer.bottom"

        elif stype == GeomAbs_Torus:
            label = ("channel.bottom.fillet" if cz < 25
                     else "channel.top.fillet")

        elif stype == GeomAbs_BSplineSurface:
            # Fillets sometimes produce BSpline instead of torus
            ch_mid_bot = ch_bot_z + channel_width / 2
            ch_mid_top = ch_top_z + channel_width / 2
            if r_centroid > 4 and abs(cz - ch_mid_bot) < 2:
                label = "channel.bottom.fillet"
            elif r_centroid > 4 and abs(cz - ch_mid_top) < 2:
                label = "channel.top.fillet"

        elif stype == GeomAbs_Plane:
            pln = surf.Plane()
            nz = abs(pln.Axis().Direction().Z())

            if nz > 0.9:
                # Horizontal faces
                if abs(cz) < 0.2:
                    label = "bottom"
                elif abs(cz - cyl_height) < 0.2:
                    label = "top"
                elif abs(cz - (cyl_height - spline_depth)) < 0.5:
                    # Spline groove root faces at bore-to-spline transition
                    ang = math.degrees(math.atan2(cy, cx)) % 360
                    groove = int((ang + 180.0 / n_teeth)
                                 / (360.0 / n_teeth)) % n_teeth + 1
                    label = f"spline.root_{groove:02d}"
                elif abs(cz - ch_bot_z) < 0.2:
                    label = "channel.bottom.wall_lower"
                elif abs(cz - (ch_bot_z + channel_width)) < 0.2:
                    label = "channel.bottom.wall_upper"
                elif abs(cz - ch_top_z) < 0.2:
                    label = "channel.top.wall_lower"
                elif abs(cz - (ch_top_z + channel_width)) < 0.2:
                    label = "channel.top.wall_upper"
            else:
                # Vertical planar faces = spline tooth flanks
                ang = math.degrees(math.atan2(cy, cx)) % 360
                tooth = int(ang / (360.0 / n_teeth)) + 1
                half_step = 180.0 / n_teeth
                side = "r" if (ang % (360.0 / n_teeth)) < half_step else "l"
                label = f"spline.tooth_{tooth:02d}.{side}"

        labels.append(label)

    return labels


def write_labels(filepath, face_labels):
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
    for eid, (text, _) in entities.items():
        if text.startswith('CLOSED_SHELL'):
            face_eids = [int(x) for x in re.findall(r'#(\d+)', text)]
            break

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
    from collections import Counter

    print("Building geometry...")
    result = build_geometry()

    print(f"Exporting to {OUTPUT_PATH}")
    cq.exporters.export(result, OUTPUT_PATH)

    print("Classifying faces...")
    labels = classify_faces(OUTPUT_PATH)

    print("Writing labels...")
    write_labels(OUTPUT_PATH, labels)

    # Summary
    counts = Counter()
    for l in labels:
        parts = l.split('.')
        if parts[0] == 'spline':
            key = f"spline.{parts[1].split('_')[0]}"
        else:
            key = l
        counts[key] += 1

    print(f"\n{len(labels)} faces:")
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")

    unlabeled = [l for l in labels if l == "?"]
    if unlabeled:
        print(f"\n  WARNING: {len(unlabeled)} unlabeled faces")
    else:
        print("\nAll faces labeled.")
