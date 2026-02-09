import math
import cadquery as cq
import re
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import (
    GeomAbs_Plane, GeomAbs_Cylinder, GeomAbs_Cone,
    GeomAbs_Torus, GeomAbs_BSplineSurface, GeomAbs_SurfaceOfRevolution,
)

# ── Parameters ──────────────────────────────────────────────
disc_diameter = 200.0   # mm
disc_radius   = disc_diameter / 2.0
disc_height   = 20.0    # mm

# Revolved taper cuts
top_flat_dia    = 10.0    # mm — flat area preserved on top face
top_flat_r      = top_flat_dia / 2.0   # 5mm
bot_flat_dia    = 20.0    # mm — flat area preserved on center bottom
bot_flat_r      = bot_flat_dia / 2.0   # 10mm
shelf_width     = 10.0    # mm — flat shelf width at outer rim (both top and bottom)
shelf_r         = disc_radius - shelf_width  # R=90mm, where tapers end
rim_height      = 3.0     # mm — outer rim height (Z=0 to Z=3)
taper_gap       = 7.0     # mm — gap between top surface and bottom cone at center
cone_peak_z     = disc_height - taper_gap  # Z=13 — bottom cone apex near Z axis

# Spoke cutouts
center_bore_dia = 5.0     # mm — center through-hole
center_bore_r   = center_bore_dia / 2.0  # 2.5mm
hub_dia         = 30.0    # mm — inner hub diameter
hub_r           = hub_dia / 2.0   # 15mm
n_spokes        = 5
spoke_width     = 10.0    # mm — parallel-edge arm width
spoke_half      = spoke_width / 2.0  # 5mm

OUTPUT_PATH = "disc/disc.step"

# ── Geometry ────────────────────────────────────────────────
def build_geometry():
    """Disc with two revolved conical tapers (lenticular profile)."""
    # 1. Stock disc
    result = (
        cq.Workplane("XY")
        .circle(disc_radius)
        .extrude(disc_height)
    )

    # 2. Top revolved taper cut — trapezoid cross-section on XZ plane
    #    Taper from (R=5, Z=20) to (R=90, Z=3), then shelf at Z=3 from R=90 to R=100
    top_cut = (
        cq.Workplane("XZ")
        .moveTo(top_flat_r, disc_height)
        .lineTo(disc_radius, disc_height)
        .lineTo(disc_radius, rim_height)
        .lineTo(shelf_r, rim_height)
        .close()
        .revolve(360, (0, 0), (0, 1))
    )
    result = result.cut(top_cut)

    # 3. Bottom concave conical recess — triangular cross-section on XZ plane
    #    Cone from (R=90, Z=0) up to (R=10, Z=13).  Center flat (R=0-10) stays at Z=0.
    bot_cut = (
        cq.Workplane("XZ")
        .moveTo(bot_flat_r, 0)
        .lineTo(shelf_r, 0)
        .lineTo(bot_flat_r, cone_peak_z)
        .close()
        .revolve(360, (0, 0), (0, 1))
    )
    result = result.cut(bot_cut)

    # 4. Window cutouts — 5 spoke pattern with parallel-edge arms
    #    Annular ring from hub (R=15) to shelf (R=90), minus 5 spoke bars
    cut_height = disc_height + 2  # oversized to ensure through-cut

    window_ring = (
        cq.Workplane("XY").workplane(offset=-1)
        .circle(disc_radius + 1)   # beyond rim to cut through shelf + rim
        .circle(hub_r)
        .extrude(cut_height)
    )

    spoke_angle_deg = 360.0 / n_spokes
    bar_length = disc_radius + 5  # one-sided: center to beyond rim
    for i in range(n_spokes):
        angle = i * spoke_angle_deg
        # Half-rectangle from center outward (not full diameter)
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

    # 5. Center through-hole (φ5mm)
    bore = (
        cq.Workplane("XY").workplane(offset=-1)
        .circle(center_bore_r)
        .extrude(disc_height + 2)
    )
    result = result.cut(bore)

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

        spoke_angle_deg = 360.0 / n_spokes

        if stype == GeomAbs_Plane:
            if abs(cz - disc_height) < 0.01:
                label = "top"
            elif abs(cz - rim_height) < 0.1:
                angle = math.degrees(math.atan2(cy, cx)) % 360
                si = round(angle / spoke_angle_deg) % n_spokes
                label = f"top_shelf_{si+1:02d}"
            elif abs(cz) < 0.01 and math.hypot(cx, cy) < bot_flat_r + 1:
                label = "bottom"
            elif abs(cz) < 0.01:
                angle = math.degrees(math.atan2(cy, cx)) % 360
                si = round(angle / spoke_angle_deg) % n_spokes
                label = f"bottom_shelf_{si+1:02d}"
            else:
                # Spoke side face
                angle = math.degrees(math.atan2(cy, cx)) % 360
                si = round(angle / spoke_angle_deg) % n_spokes
                spoke_a = math.radians(si * spoke_angle_deg)
                cross = math.cos(spoke_a) * cy - math.sin(spoke_a) * cx
                side = "left" if cross > 0 else "right"
                label = f"spoke_{si+1:02d}.{side}"
        elif stype == GeomAbs_Cylinder:
            r = surf.Cylinder().Radius()
            if abs(r - disc_radius) < 0.1:
                angle = math.degrees(math.atan2(cy, cx)) % 360
                si = round(angle / spoke_angle_deg) % n_spokes
                label = f"rim_{si+1:02d}"
            elif abs(r - hub_r) < 0.1:
                angle = math.degrees(math.atan2(cy, cx)) % 360
                wi = round(angle / spoke_angle_deg - 0.5) % n_spokes
                label = f"hub_{wi+1:02d}"
            elif abs(r - center_bore_r) < 0.1:
                label = "bore"
            elif abs(r - bot_flat_r) < 0.1:
                label = "recess_wall"
            else:
                label = f"cyl_r{r:.1f}"
        elif stype == GeomAbs_Cone:
            if cz > disc_height / 2:
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

    # Build replacements
    for fid, label in zip(face_ids, labels):
        pattern = rf"(#{fid}\s*=\s*ADVANCED_FACE\s*\()\s*'[^']*'"
        replacement = rf"\g<1>'{label}'"
        text = re.sub(pattern, replacement, text)

    with open(filepath, "w") as f:
        f.write(text)

    print(f"  Wrote {len(labels)} labels to {filepath}")


# ── Main ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Building disc geometry...")
    result = build_geometry()

    print(f"Exporting to {OUTPUT_PATH}...")
    cq.exporters.export(result, OUTPUT_PATH)

    print("Classifying faces...")
    labels = classify_faces(OUTPUT_PATH)

    print("Writing labels...")
    write_labels(OUTPUT_PATH, labels)

    print(f"\nDone. {len(labels)} faces labeled.")
