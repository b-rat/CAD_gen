import math
import cadquery as cq
import re
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import GeomAbs_Plane, GeomAbs_Cylinder, GeomAbs_Cone

# ── Parameters ──────────────────────────────────────────────
diameter = 200.0  # mm
radius = diameter / 2.0
thickness = 20.0  # mm

# Top revolved taper cut
top_flat_dia = 10.0       # mm — remaining top surface diameter
top_flat_r = top_flat_dia / 2.0  # 5mm
rim_step_height = 3.0     # mm — shelf height from bottom (Z=0 to Z=3)
rim_step_width = 10.0     # mm — shelf width inward from OD
rim_step_r = radius - rim_step_width  # R=90mm, inner edge of rim_step

# Bottom revolved conical recess
bot_flat_dia = 20.0       # mm — center bottom circle diameter
bot_flat_r = bot_flat_dia / 2.0  # 10mm
bot_ring_width = 10.0     # mm — annular bottom ring width from OD inward
bot_ring_r = radius - bot_ring_width  # R=90mm, inner edge of bottom ring
bot_cone_gap = 7.0        # mm — gap from top surface to cone apex
bot_cone_peak_z = thickness - bot_cone_gap  # Z=13, cone apex near Z axis

# Spoke cutouts
n_spokes = 3
spoke_width = 15.0        # mm — parallel-edge arm width
spoke_half = spoke_width / 2.0  # 10mm
hub_dia = 35.0            # mm — inner hub diameter
hub_r = hub_dia / 2.0     # 17.5mm
spoke_angle_deg = 360.0 / n_spokes  # 60°

OUTPUT_PATH = "spoke_v2/spoke_v2.step"

# ── Geometry ────────────────────────────────────────────────
def build_geometry():
    """Stock cylinder: 200mm dia, 20mm thick, bottom on XY plane, centered on Z."""
    # 1. Stock disc
    result = (
        cq.Workplane("XY")
        .circle(radius)
        .extrude(thickness)
    )

    # 2. Top revolved taper cut
    #    Trapezoid cross-section on XZ: cone from (R=5, Z=20) to (R=90, Z=3),
    #    then shelf at Z=3 from R=90 to R=100, up to Z=20 at OD
    top_cut = (
        cq.Workplane("XZ")
        .moveTo(top_flat_r, thickness)
        .lineTo(radius, thickness)
        .lineTo(radius, rim_step_height)
        .lineTo(rim_step_r, rim_step_height)
        .close()
        .revolve(360, (0, 0), (0, 1))
    )
    result = result.cut(top_cut)

    # 3. Bottom revolved conical recess
    #    Triangle cross-section on XZ: cone from (R=10, Z=13) down to (R=90, Z=0)
    #    Center flat (R=0-10) stays at Z=0, outer ring (R=90-100) stays at Z=0
    bot_cut = (
        cq.Workplane("XZ")
        .moveTo(bot_flat_r, 0)
        .lineTo(bot_ring_r, 0)
        .lineTo(bot_flat_r, bot_cone_peak_z)
        .close()
        .revolve(360, (0, 0), (0, 1))
    )
    result = result.cut(bot_cut)

    # 4. Spoke cutouts — 6 pizza-wedge windows between spokes
    #    Annular ring from hub (R=17.5) to beyond rim, minus 6 spoke bars
    cut_height = thickness + 2  # oversized for clean through-cut
    bar_length = radius + 5     # center to beyond rim

    window_ring = (
        cq.Workplane("XY").workplane(offset=-1)
        .circle(radius + 1)
        .circle(hub_r)
        .extrude(cut_height)
    )

    for i in range(n_spokes):
        angle = i * spoke_angle_deg
        bar = (
            cq.Workplane("XY").workplane(offset=-1)
            .center(bar_length / 2, 0)
            .rect(bar_length, spoke_width)
            .extrude(cut_height)
        )
        if angle != 0:
            bar = bar.rotate((0, 0, 0), (0, 0, 1), angle)
        window_ring = window_ring.cut(bar)

    result = result.cut(window_ring)

    return result


# ── Face classification ─────────────────────────────────────
def classify_faces(filepath):
    """Read exported STEP, classify each face by surface type + centroid."""
    result = cq.importers.importStep(filepath)
    faces = result.faces().vals()

    labels = []
    for face in faces:
        props = GProp_GProps()
        BRepGProp.SurfaceProperties_s(face.wrapped, props)
        c = props.CentreOfMass()
        cx, cy, cz = c.X(), c.Y(), c.Z()

        surf = BRepAdaptor_Surface(face.wrapped)
        stype = surf.GetType()

        area = props.Mass()
        r_centroid = math.hypot(cx, cy)
        angle = math.degrees(math.atan2(cy, cx)) % 360

        if stype == GeomAbs_Plane:
            if abs(cz) < 0.01 and r_centroid < bot_flat_r + 1:
                label = "bottom"
            elif abs(cz) < 0.01:
                si = round(angle / spoke_angle_deg) % n_spokes
                label = f"bottom_ring_{si+1:02d}"
            elif abs(cz - thickness) < 0.01:
                label = "top"
            elif abs(cz - rim_step_height) < 0.1:
                si = round(angle / spoke_angle_deg) % n_spokes
                label = f"rim_step_{si+1:02d}"
            else:
                # Spoke side faces — vertical planar faces
                si = round(angle / spoke_angle_deg) % n_spokes
                spoke_a = math.radians(si * spoke_angle_deg)
                cross = math.cos(spoke_a) * cy - math.sin(spoke_a) * cx
                side = "left" if cross > 0 else "right"
                label = f"spoke_{si+1:02d}.{side}"
        elif stype == GeomAbs_Cylinder:
            r = surf.Cylinder().Radius()
            if abs(r - radius) < 0.1:
                si = round(angle / spoke_angle_deg) % n_spokes
                label = f"rim_{si+1:02d}"
            elif abs(r - hub_r) < 0.1:
                # Hub arc sits between two spokes
                wi = round(angle / spoke_angle_deg - 0.5) % n_spokes
                label = f"hub_{wi+1:02d}"
            elif abs(r - bot_flat_r) < 0.1:
                label = "recess_wall"
            else:
                label = f"cyl_r{r:.1f}"
        elif stype == GeomAbs_Cone:
            apex = surf.Cone().Apex()
            if apex.Z() > thickness:
                label = "top_taper"
            else:
                label = "bottom_taper"
        else:
            label = "?"

        labels.append(label)
        print(f"  face {len(labels):3d}: type={stype} centroid=({cx:.2f},{cy:.2f},{cz:.2f}) → {label}")

    return labels


# ── STEP labeling ───────────────────────────────────────────
def write_labels(filepath, labels):
    """Map OCC face order → CLOSED_SHELL order, write labels into STEP."""
    with open(filepath, "r") as f:
        raw = f.read()

    # Join continuation lines
    text = re.sub(r"\n\s+", " ", raw)

    # Find CLOSED_SHELL and extract ordered ADVANCED_FACE IDs
    cs_match = re.search(r"CLOSED_SHELL\s*\(\s*'[^']*'\s*,\s*\(([^)]+)\)", text)
    if not cs_match:
        raise RuntimeError("CLOSED_SHELL not found")

    face_ids = re.findall(r"#(\d+)", cs_match.group(1))
    print(f"\n  CLOSED_SHELL has {len(face_ids)} faces, classifier returned {len(labels)} labels")

    if len(face_ids) != len(labels):
        raise RuntimeError(f"Face count mismatch: STEP has {len(face_ids)}, classifier has {len(labels)}")

    for fid, label in zip(face_ids, labels):
        pattern = rf"(#{fid}\s*=\s*ADVANCED_FACE\s*\()\s*'[^']*'"
        replacement = rf"\g<1>'{label}'"
        text = re.sub(pattern, replacement, text)

    with open(filepath, "w") as f:
        f.write(text)

    print(f"  Wrote {len(labels)} labels to {filepath}")


# ── Main ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Building spoke_v2 geometry...")
    result = build_geometry()

    print(f"Exporting to {OUTPUT_PATH}...")
    cq.exporters.export(result, OUTPUT_PATH)

    print("Classifying faces...")
    labels = classify_faces(OUTPUT_PATH)

    print("Writing labels...")
    write_labels(OUTPUT_PATH, labels)

    print(f"\nDone. {len(labels)} faces labeled.")
