"""
Coffee mug — hollowed body with handle.

Profile: cylindrical bottom (95mm dia, 9mm tall), arc bulge
(max 100mm dia at Z=50), cylindrical top (81.6mm dia, 9mm tall).
Total height 107mm. Bottom on XY plane, axis along Z.
5mm wall thickness, 5mm floor, open top.
Handle extruded ±9mm from XZ plane (18mm wide).
"""

import math
import re
import cadquery as cq
import numpy as np

# ============================================================
# Parameters
# ============================================================

bottom_dia = 95.0
bottom_r = bottom_dia / 2          # 47.5

top_dia = 81.6
top_r = top_dia / 2                # 40.8

height = 107.0
wall_thickness = 5.0

bottom_cyl_h = 9.0                 # cylindrical section at bottom
top_cyl_h = 9.0                    # cylindrical section at top
rim_r = wall_thickness / 2         # full round radius on rim (2.5)

bulge_max_dia = 100.0
bulge_r = bulge_max_dia / 2        # 50.0
bulge_z = 50.0                     # height of max bulge diameter

# Derived inner dimensions (5mm wall offset)
inner_bottom_r = bottom_r - wall_thickness   # 42.5
inner_top_r = top_r - wall_thickness         # 35.8
inner_bulge_r = bulge_r - wall_thickness     # 45.0
floor_z = wall_thickness                     # 5.0

# Handle parameters
handle_main_cx = 65.0              # main arc center X
handle_main_cz = 80.0              # main arc center Z
handle_main_r = 15.0               # main arc radius
handle_trans_r = 100.0             # transition arc radius
handle_thickness = 10.0            # thickness in XZ plane
handle_half_width = 9.0            # half-width in Y (total 18mm)
handle_fillet_r = 4.0              # edge fillet radius on handle
handle_bottom_z = 20.0             # bottom attachment Z
handle_top_z = 87.0                # top attachment Z (20mm from top)

OUTPUT_PATH = "coffee_mug/coffee_mug.step"


# ============================================================
# Handle geometry computation
# ============================================================

def _find_transition_center(attach_pt, main_center, main_r, trans_r):
    """Find center of transition arc (internal tangency with main arc,
    passing through attachment point). Returns the solution on the mug side."""
    px, pz = attach_pt
    cx, cz = main_center
    d_target = trans_r - main_r  # internal tangency

    # Two circles:
    # (x - px)^2 + (z - pz)^2 = trans_r^2       ... (1)
    # (x - cx)^2 + (z - cz)^2 = d_target^2       ... (2)
    # (2) - (1) gives linear: Ax + Bz = C
    A = 2 * (px - cx)
    B = 2 * (pz - cz)
    C = (d_target**2 - trans_r**2 - cx**2 + px**2 - cz**2 + pz**2)

    # Solve x in terms of z: x = (C - Bz) / A
    # Sub into circle 1 → quadratic in z
    a_q = (B / A)**2 + 1
    b_q = 2 * (B * (px - C / A)) / A - 2 * pz  # simplified
    # More carefully:
    # ((C - Bz)/A - px)^2 + (z - pz)^2 = trans_r^2
    # let u = (C/A - px), v = -B/A
    u = C / A - px
    v = -B / A
    a_q = v**2 + 1
    b_q = 2 * u * v - 2 * pz
    c_q = u**2 + pz**2 - trans_r**2

    disc = b_q**2 - 4 * a_q * c_q
    if disc < 0:
        raise ValueError("No real solution for transition center")

    z1 = (-b_q + math.sqrt(disc)) / (2 * a_q)
    z2 = (-b_q - math.sqrt(disc)) / (2 * a_q)
    x1 = (C - B * z1) / A
    x2 = (C - B * z2) / A

    # Pick the solution where the transition center is on the mug side
    # (closer to Z axis, i.e., smaller X)
    if x1 < x2:
        return (x1, z1)
    else:
        return (x2, z2)


def _tangent_point(main_center, main_r, trans_center):
    """Internal tangency point: on main arc, far side from trans center."""
    cx, cz = main_center
    tx, tz = trans_center
    dx, dz = cx - tx, cz - tz
    d = math.sqrt(dx**2 + dz**2)
    return (cx + main_r * dx / d, cz + main_r * dz / d)


def _arc_point(center, radius, angle_deg):
    """Point on circle at given angle (0° = +X)."""
    a = math.radians(angle_deg)
    return (center[0] + radius * math.cos(a),
            center[1] + radius * math.sin(a))


def _angle_to(center, point):
    """Angle from center to point, in degrees."""
    return math.degrees(math.atan2(point[1] - center[1],
                                    point[0] - center[0]))


def _mug_outer_radius_at_z(z):
    """Approximate mug outer radius at height z (on the bulge arc)."""
    # Bulge arc through (47.5, 9), (50, 50), (40.8, 98)
    # Circle center: (-130.0, 40.4), R=180.3  (precomputed)
    h, k, R = -130.0, 40.4, 180.3
    val = R**2 - (z - k)**2
    if val < 0:
        return 0
    return math.sqrt(val) + h


def compute_handle_profile():
    """Compute outer and inner handle edge points."""
    mc = (handle_main_cx, handle_main_cz)
    mr = handle_main_r

    # Mug body radius at attachment heights
    body_r_bottom = _mug_outer_radius_at_z(handle_bottom_z)
    body_r_top = _mug_outer_radius_at_z(handle_top_z)
    p_b = (body_r_bottom, handle_bottom_z)
    p_t = (body_r_top, handle_top_z)

    # Transition arc centers (internal tangency)
    c_bt = _find_transition_center(p_b, mc, mr, handle_trans_r)
    c_tt = _find_transition_center(p_t, mc, mr, handle_trans_r)

    # Tangent points on main arc
    t_b = _tangent_point(mc, mr, c_bt)
    t_t = _tangent_point(mc, mr, c_tt)

    # Midpoints on outer transition arcs
    ang_bt_start = _angle_to(c_bt, p_b)
    ang_bt_end = _angle_to(c_bt, t_b)
    mid_bt = _arc_point(c_bt, handle_trans_r, (ang_bt_start + ang_bt_end) / 2)

    ang_tt_start = _angle_to(c_tt, t_t)
    ang_tt_end = _angle_to(c_tt, p_t)
    mid_tt = _arc_point(c_tt, handle_trans_r, (ang_tt_start + ang_tt_end) / 2)

    # Main arc midpoint (rightmost point)
    mid_main = (mc[0] + mr, mc[1])

    return {
        'p_b': p_b, 'mid_bt': mid_bt, 't_b': t_b,
        'mid_main': mid_main,
        't_t': t_t, 'mid_tt': mid_tt, 'p_t': p_t,
        'c_bt': c_bt, 'c_tt': c_tt,
    }


# ============================================================
# Geometry
# ============================================================

def build_geometry():
    """Build mug: outer body → handle union → cavity cut."""

    # Step 1: Outer body (solid, not hollowed yet)
    outer = (
        cq.Workplane("XZ")
        .moveTo(0, 0)
        .lineTo(bottom_r, 0)
        .lineTo(bottom_r, bottom_cyl_h)
        .threePointArc((bulge_r, bulge_z),
                       (top_r, height - top_cyl_h))
        .lineTo(top_r, height - rim_r)
        .threePointArc(
            (top_r - rim_r + rim_r * math.cos(math.pi / 4),
             height - rim_r + rim_r * math.sin(math.pi / 4)),
            (top_r - rim_r, height))
        .lineTo(0, height)
        .close()
        .revolve(360, (0, 0), (0, 1))
    )

    # Step 2: Handle via sweep along centerline path
    h = compute_handle_profile()
    t2 = handle_thickness / 2  # 5mm offset for centerline

    # Centerline points (midway between outer and inner edges)
    pb_c = (h['p_b'][0] - t2, h['p_b'][1])
    mbt_c = (h['mid_bt'][0] - t2, h['mid_bt'][1])
    tb_c = (h['t_b'][0] - t2, h['t_b'][1])
    mm_c = (h['mid_main'][0] - t2, h['mid_main'][1])
    tt_c = (h['t_t'][0] - t2, h['t_t'][1])
    mtt_c = (h['mid_tt'][0] - t2, h['mid_tt'][1])
    pt_c = (h['p_t'][0] - t2, h['p_t'][1])

    # Handle path (centerline in XZ plane)
    path = (
        cq.Workplane("XZ")
        .moveTo(*pb_c)
        .threePointArc(mbt_c, tb_c)       # bottom transition
        .threePointArc(mm_c, tt_c)        # main arc
        .threePointArc(mtt_c, pt_c)       # top transition
    )

    # Sweep rounded-rectangle cross-section along path
    hw = handle_half_width             # 9mm half-width (Y)
    ht = handle_thickness / 2          # 5mm half-thickness (Z)
    fr = handle_fillet_r               # 2mm corner radius
    c45 = fr * math.cos(math.pi / 4)  # arc midpoint offset

    handle = (
        cq.Workplane("YZ")
        .workplane(offset=pb_c[0])
        .center(0, pb_c[1])
        .moveTo(-hw + fr, -ht)
        .lineTo(hw - fr, -ht)                                        # bottom
        .threePointArc((hw - fr + c45, -ht + fr - c45),
                       (hw, -ht + fr))                                # BR corner
        .lineTo(hw, ht - fr)                                         # right
        .threePointArc((hw - fr + c45, ht - fr + c45),
                       (hw - fr, ht))                                 # TR corner
        .lineTo(-hw + fr, ht)                                        # top
        .threePointArc((-hw + fr - c45, ht - fr + c45),
                       (-hw, ht - fr))                                # TL corner
        .lineTo(-hw, -ht + fr)                                       # left
        .threePointArc((-hw + fr - c45, -ht + fr - c45),
                       (-hw + fr, -ht))                               # BL corner
        .close()
        .sweep(path, transition='round')
    )

    # Step 3: Union handle with body
    result = outer.union(handle)

    # Step 4: Cut cavity (after union so handle material in wall is trimmed)
    cavity = (
        cq.Workplane("XZ")
        .moveTo(0, floor_z)
        .lineTo(inner_bottom_r, floor_z)
        .lineTo(inner_bottom_r, bottom_cyl_h)
        .threePointArc((inner_bulge_r, bulge_z),
                       (inner_top_r, height - top_cyl_h))
        .lineTo(inner_top_r, height - rim_r)
        .threePointArc(
            (inner_top_r + rim_r - rim_r * math.cos(math.pi / 4),
             height - rim_r + rim_r * math.sin(math.pi / 4)),
            (inner_top_r + rim_r, height))
        .lineTo(inner_top_r + rim_r, height + 5)
        .lineTo(0, height + 5)
        .close()
        .revolve(360, (0, 0), (0, 1))
    )

    result = result.cut(cavity)

    # Step 5: Fillet handle-body junction edges (union seam edges)
    handle_fillet = 4.0

    class HandleJunctionSelector(cq.Selector):
        """Select edges at the handle-body intersection."""
        def filter(self, objectList):
            selected = []
            for edge in objectList:
                bb = edge.BoundingBox()
                y_span = bb.ymax - bb.ymin
                z_mid = (bb.zmin + bb.zmax) / 2
                x_mid = (bb.xmin + bb.xmax) / 2
                # Junction edges: within handle Y width, near body surface,
                # near bottom or top attachment Z
                if y_span < handle_half_width * 2 + 2 and y_span > 0.5:
                    body_r = _mug_outer_radius_at_z(z_mid)
                    near_bottom = abs(z_mid - handle_bottom_z) < 12
                    near_top = abs(z_mid - handle_top_z) < 12
                    on_body = abs(x_mid - body_r) < 8
                    if (near_bottom or near_top) and on_body:
                        selected.append(edge)
            return selected

    result = result.edges(HandleJunctionSelector()).fillet(handle_fillet)

    return result


# ============================================================
# Face classification
# ============================================================

def classify_faces(filepath):
    """Classify faces by surface type and centroid position."""
    from OCP.BRepGProp import BRepGProp
    from OCP.GProp import GProp_GProps
    from OCP.BRepAdaptor import BRepAdaptor_Surface
    from OCP.GeomAbs import (GeomAbs_Plane, GeomAbs_Cylinder,
                              GeomAbs_Cone, GeomAbs_Torus,
                              GeomAbs_BSplineSurface,
                              GeomAbs_SurfaceOfRevolution)

    result = cq.importers.importStep(filepath)
    faces = result.faces().vals()
    labels = []

    for face in faces:
        props = GProp_GProps()
        BRepGProp.SurfaceProperties_s(face.wrapped, props)
        centroid = props.CentreOfMass()
        cx, cy, cz = centroid.X(), centroid.Y(), centroid.Z()
        r_centroid = math.sqrt(cx**2 + cy**2)

        surf = BRepAdaptor_Surface(face.wrapped)
        stype = surf.GetType()

        bb = face.BoundingBox()

        label = "?"

        # Handle region: cx > bulge_r (beyond the mug body)
        is_handle = cx > bulge_r + 2

        if stype == GeomAbs_Plane:
            pln = surf.Plane()
            nz = abs(pln.Axis().Direction().Z())
            ny = abs(pln.Axis().Direction().Y())
            nx = abs(pln.Axis().Direction().X())

            if nz > 0.9:
                if abs(cz) < 0.1:
                    label = "bottom"
                elif abs(cz - floor_z) < 0.5 and r_centroid < inner_bottom_r + 2:
                    label = "cavity.floor"
            elif ny > 0.9 and is_handle:
                # Handle side faces (extruded flat faces)
                if cy > 0:
                    label = "handle.side_pos"
                else:
                    label = "handle.side_neg"
            elif nx > 0.5 and is_handle:
                label = "handle.end"

        elif stype == GeomAbs_Cylinder:
            r = surf.Cylinder().Radius()
            # Handle flat sides: Y span ±(hw - fillet_r) for rounded cross-section
            handle_flat_hw = handle_half_width - handle_fillet_r
            is_handle_cyl = (abs(bb.ymax - handle_flat_hw) < 1 and
                             abs(bb.ymin + handle_flat_hw) < 1)
            if is_handle_cyl:
                label = "handle"
            elif abs(r - bottom_r) < 0.5:
                label = "body.bottom_cyl"
            elif abs(r - top_r) < 0.5:
                label = "body.top_cyl"
            elif abs(r - inner_bottom_r) < 0.5:
                label = "cavity.bottom_cyl"
            elif abs(r - inner_top_r) < 0.5:
                label = "cavity.top_cyl"

        elif stype == GeomAbs_Cone:
            label = "body.cone"

        elif stype == GeomAbs_Torus:
            tor_r = surf.Torus().MinorRadius()
            if abs(tor_r - wall_thickness / 2) < 0.5 and abs(cz - height) < 5:
                label = "rim"
            else:
                label = "body.bulge"

        elif stype == GeomAbs_SurfaceOfRevolution:
            y_span = bb.ymax - bb.ymin
            if y_span < handle_half_width:
                # Narrow Y band → handle corner arc
                label = "handle"
            else:
                max_r = max(abs(bb.xmax), abs(bb.xmin),
                            abs(bb.ymax), abs(bb.ymin))
                if max_r > (inner_bulge_r + bulge_r) / 2:
                    label = "body.bulge"
                else:
                    label = "cavity.bulge"

        elif stype == GeomAbs_BSplineSurface:
            y_span = bb.ymax - bb.ymin
            if is_handle:
                label = "handle"
            elif y_span < handle_half_width * 3:
                # Small Y span near body surface → junction fillet
                label = "handle.fillet"
            else:
                label = "body.bulge"

        else:
            label = f"?_type{stype}"

        labels.append(label)

    return labels


# ============================================================
# STEP labeling
# ============================================================

def write_labels(filepath, labels):
    """Write face labels into STEP file via CLOSED_SHELL entity mapping."""
    with open(filepath, "r") as f:
        text = f.read()

    # Join continuation lines
    joined = re.sub(r'\n\s+', ' ', text)

    # Find CLOSED_SHELL and extract ADVANCED_FACE IDs
    shell_match = re.search(r"CLOSED_SHELL\s*\(\s*'[^']*'\s*,\s*\(([^)]+)\)", joined)
    if not shell_match:
        print("ERROR: no CLOSED_SHELL found")
        return

    face_ids = re.findall(r'#(\d+)', shell_match.group(1))
    print(f"CLOSED_SHELL has {len(face_ids)} faces, classifier produced {len(labels)} labels")

    if len(face_ids) != len(labels):
        print("WARNING: face count mismatch!")
        return

    # Replace labels in original text (not joined)
    for fid, label in zip(face_ids, labels):
        pattern = rf"(#{fid}\s*=\s*ADVANCED_FACE\s*\(\s*')([^']*?)(')"
        text = re.sub(pattern, rf"\g<1>{label}\g<3>", text)

    with open(filepath, "w") as f:
        f.write(text)

    unlabeled = sum(1 for l in labels if l.startswith("?"))
    print(f"Wrote {len(labels)} labels ({unlabeled} unlabeled)")


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    # Print computed handle points for debugging
    h = compute_handle_profile()
    print("Handle points:")
    for k, v in h.items():
        if isinstance(v, tuple):
            print(f"  {k}: ({v[0]:.1f}, {v[1]:.1f})")

    result = build_geometry()
    cq.exporters.export(result, OUTPUT_PATH)
    print(f"\nExported → {OUTPUT_PATH}")

    labels = classify_faces(OUTPUT_PATH)
    write_labels(OUTPUT_PATH, labels)

    # Summary
    from collections import Counter
    counts = Counter(labels)
    print(f"\n{len(labels)} faces:")
    for label, count in sorted(counts.items()):
        print(f"  {label}: {count}")
