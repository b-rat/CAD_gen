import cadquery as cq
import math
import re

from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.BRepAdaptor import BRepAdaptor_Surface
from OCP.GeomAbs import (GeomAbs_Plane, GeomAbs_Cylinder, GeomAbs_Cone,
                          GeomAbs_Torus, GeomAbs_BSplineSurface)

# ── Unit conversion ──────────────────────────────────────────────
#   All dimensions specified in inches; CadQuery works in mm.
IN = 25.4   # multiply inch values by this for CadQuery

# ── KF10 Flange Dimensions (inches) ──────────────────────────────
#   From manufacturer spec drawing + user measurements
rim_dia     = 1.18     # outer flange diameter
rim_r       = rim_dia / 2   # 0.59
rim_width   = 0.12     # axial thickness of rim
base_dia    = 0.49     # base/interface section diameter
base_r      = base_dia / 2  # 0.245
taper_angle = 15.0     # back_taper cone angle (degrees from front face)
bore_dia    = 0.35     # tube bore diameter
bore_r      = bore_dia / 2  # 0.175
flange_len  = 0.50     # front face to interface face

# Computed from 15° taper measured from front face (perpendicular to axis)
taper_z    = (rim_r - base_r) * math.tan(math.radians(taper_angle))  # ≈ 0.092"
base_depth = flange_len - rim_width - taper_z                        # ≈ 0.288"

# ── Block Dimensions (inches) ────────────────────────────────────
block_w = 1.18    # Z direction (width)
block_h = 2.59    # Y direction (height)
block_d = 2.18    # X direction (depth)

block_y_bot = -2.0
block_y_top = block_y_bot + block_h   # 1.5

half_d   = 1.59          # +X face at 1.59 (side flange interface, moved 1" out)
half_w   = block_w / 2   # 0.59
block_x_ctr = half_d - block_d / 2   # −0.50 — shift so +X face stays put

fillet_r = 0.25   # fillet radius on block_cross ↔ block_top/bottom edges
cbore_dia   = 0.49   # counterbore diameter on flange front faces
cbore_r     = cbore_dia / 2  # 0.245
cbore_depth = 0.10   # counterbore depth

OUTPUT_PATH = "showerhead_tee/showerhead_tee.step"


# ── KF10 Flange Component ────────────────────────────────────────
def make_kf10_flange():
    """Create KF10 flange as body of revolution.

    Axis along Z.  Interface face at Z=0, front/sealing face at Z=flange_len.

    Profile (interface → front):
      base cylinder → back_taper cone → rim disc
    """
    z_base_end  = base_depth * IN
    z_taper_end = (base_depth + taper_z) * IN
    z_front     = flange_len * IN

    flange = (
        cq.Workplane("XZ")
        .moveTo(bore_r * IN, 0)                # interface face, bore edge
        .lineTo(base_r * IN, 0)                # interface face, base outer edge
        .lineTo(base_r * IN, z_base_end)       # end of base / start of taper
        .lineTo(rim_r * IN, z_taper_end)       # end of taper / start of rim
        .lineTo(rim_r * IN, z_front)           # front face, rim outer edge
        .lineTo(bore_r * IN, z_front)          # front face, bore edge
        .close()
        .revolve(360, (0, 0), (0, 1))
    )
    return flange


# ── Geometry ─────────────────────────────────────────────────────
def build_geometry():
    y_ctr = block_y_bot + block_h / 2

    # Block — offset in X so +X face stays at half_d, Y bore stays at origin
    block = (cq.Workplane("XY")
             .box(block_d * IN, block_h * IN, block_w * IN)
             .translate((block_x_ctr * IN, y_ctr * IN, 0)))

    # Build three flanges and position them
    top_flange = (make_kf10_flange()
                  .rotate((0, 0, 0), (1, 0, 0), -90)
                  .translate((0, block_y_top * IN, 0)))

    bot_flange = (make_kf10_flange()
                  .rotate((0, 0, 0), (1, 0, 0), 90)
                  .translate((0, block_y_bot * IN, 0)))

    side_flange = (make_kf10_flange()
                   .rotate((0, 0, 0), (0, 1, 0), 90)
                   .translate((half_d * IN, 0, 0)))

    # Union all
    result = block
    for part in [top_flange, bot_flange, side_flange]:
        result = result.union(part)

    # Fillet block_cross ↔ block_top and block_cross ↔ block_bottom edges
    xf = half_d * IN
    yt = block_y_top * IN
    yb = block_y_bot * IN
    tol_e = 1.0  # mm tolerance for edge selection

    fillet_edges = (
        result.edges()
        .filter(lambda e: (
            abs(e.Center().x - xf) < tol_e and
            (abs(e.Center().y - yt) < tol_e or abs(e.Center().y - yb) < tol_e)
        ))
    )
    result = result.newObject([result.val()]).edges(
        cq.selectors.BoxSelector(
            (xf - tol_e, yb - tol_e, -half_w * IN - tol_e),
            (xf + tol_e, yb + tol_e,  half_w * IN + tol_e)
        )
    ).fillet(fillet_r * IN)

    result = result.edges(
        cq.selectors.BoxSelector(
            (xf - tol_e, yt - tol_e, -half_w * IN - tol_e),
            (xf + tol_e, yt + tol_e,  half_w * IN + tol_e)
        )
    ).fillet(fillet_r * IN)

    # Cut bores (after all unions)
    y_start = (block_y_bot - flange_len - 1.0) * IN
    y_end   = (block_y_top + flange_len + 1.0) * IN
    y_len   = y_end - y_start
    y_bore  = (cq.Workplane("XZ")
               .workplane(offset=y_start)
               .circle(bore_r * IN)
               .extrude(y_len))

    # X bore – from YZ plane (X=0) through side port only
    x_bore  = (cq.Workplane("YZ")
               .workplane(offset=0)
               .circle(bore_r * IN)
               .extrude((half_d + flange_len + 0.5) * IN))

    result = result.cut(y_bore).cut(x_bore)

    # Counterbores on each flange front face (cut inward from sealing face)
    cd = cbore_depth * IN
    cr = cbore_r * IN

    # Build counterbore as Z-axis cylinder, then rotate+translate like flanges
    cbore_cyl = (cq.Workplane("XY").circle(cr).extrude(cd))

    # Top: counterbore at front face, recessed inward. Front at Y=block_y_top+flange_len.
    # Cylinder axis Z → rotate to Y axis, place at counterbore bottom.
    top_cb = (cbore_cyl
              .rotate((0,0,0), (1,0,0), -90)
              .translate((0, (block_y_top + flange_len - cbore_depth) * IN, 0)))

    # Bottom: front face at Y=block_y_bot-flange_len, recess goes +Y
    bot_cb = (cbore_cyl
              .rotate((0,0,0), (1,0,0), 90)
              .translate((0, (block_y_bot - flange_len + cbore_depth) * IN, 0)))

    # Side: front face at X=half_d+flange_len, recess goes −X
    side_cb = (cbore_cyl
               .rotate((0,0,0), (0,1,0), 90)
               .translate(((half_d + flange_len - cbore_depth) * IN, 0, 0)))

    result = result.cut(top_cb).cut(bot_cb).cut(side_cb)

    return result


# ── Face Classification ──────────────────────────────────────────
def classify_faces(filepath):
    """Classify each face by surface type + centroid position."""
    result = cq.importers.importStep(filepath)
    faces = result.faces().vals()

    # Reference radii in mm
    bore_rmm = bore_r * IN
    rim_rmm  = rim_r * IN
    base_rmm = base_r * IN
    tol = 0.5  # mm

    # Block extents in mm
    bx_max = half_d * IN                          # +X face
    bx_min = (block_x_ctr - block_d / 2) * IN    # −X face
    by_top = block_y_top * IN
    by_bot = block_y_bot * IN
    bz     = half_w * IN
    fl     = flange_len * IN

    fillet_rmm = fillet_r * IN
    cbore_rmm  = cbore_r * IN
    cbore_dmm  = cbore_depth * IN
    labels = []
    flange_cyl_n = 0
    flange_cone_n = 0
    flange_planar_n = 0
    cbore_cyl_n = 0
    cbore_planar_n = 0
    fillet_n = 0

    for i, face in enumerate(faces):
        props = GProp_GProps()
        BRepGProp.SurfaceProperties_s(face.wrapped, props)
        c = props.CentreOfMass()
        cx, cy, cz = c.X(), c.Y(), c.Z()
        surf = BRepAdaptor_Surface(face.wrapped)
        stype = surf.GetType()

        if stype == GeomAbs_Cylinder:
            r = surf.Cylinder().Radius()
            axis_d = surf.Cylinder().Axis().Direction()
            dx, dy, dz = axis_d.X(), axis_d.Y(), axis_d.Z()

            if abs(r - bore_rmm) < tol:
                # Bore surface — distinguish by axis direction
                if abs(dy) > 0.9:
                    label = "y_bore"
                elif abs(dx) > 0.9:
                    label = "cross_bore"
                else:
                    label = f"bore_({dx:.1f},{dy:.1f},{dz:.1f})"
            elif (abs(r - fillet_rmm) < tol and
                  cx > bx_max * 0.5 and
                  (abs(cy - by_top) < fillet_rmm * 2 or abs(cy - by_bot) < fillet_rmm * 2)):
                # Fillet surface near block_cross ↔ top/bottom edge
                fillet_n += 1
                if cy > 0:
                    label = f"fillet.cross_top_{fillet_n}"
                else:
                    label = f"fillet.cross_bottom_{fillet_n}"
            elif abs(r - rim_rmm) < tol:
                flange_cyl_n += 1
                label = f"kf_flange.cylindrical_{flange_cyl_n}"
            elif abs(r - base_rmm) < tol:
                # base_r == cbore_r — distinguish by proximity to front face
                # Counterbore walls are near the front face (outer end)
                top_front = (block_y_top + flange_len) * IN
                bot_front = (block_y_bot - flange_len) * IN
                side_front = (half_d + flange_len) * IN
                near_front = (
                    abs(cy - top_front) < cbore_dmm * 1.5 or
                    abs(cy - bot_front) < cbore_dmm * 1.5 or
                    abs(cx - side_front) < cbore_dmm * 1.5
                )
                if near_front:
                    cbore_cyl_n += 1
                    label = f"counterbore.wall_{cbore_cyl_n}"
                else:
                    flange_cyl_n += 1
                    label = f"kf_flange.cylindrical_{flange_cyl_n}"
            else:
                label = f"cyl_r{r:.2f}"

        elif stype == GeomAbs_Cone:
            flange_cone_n += 1
            label = f"kf_flange.conical_{flange_cone_n}"

        elif stype == GeomAbs_BSplineSurface:
            # BSpline from fillet near flange junction
            fillet_n += 1
            if cy > 0:
                label = f"fillet.cross_top_{fillet_n}"
            else:
                label = f"fillet.cross_bottom_{fillet_n}"

        elif stype == GeomAbs_Plane:
            pln  = surf.Plane()
            norm = pln.Axis().Direction()
            nx, ny, nz = norm.X(), norm.Y(), norm.Z()

            # Counterbore bottom positions (front face minus depth)
            top_cb_y = (block_y_top + flange_len - cbore_depth) * IN
            bot_cb_y = (block_y_bot - flange_len + cbore_depth) * IN
            side_cb_x = (half_d + flange_len - cbore_depth) * IN
            cb_tol = 1.0  # mm — tight tolerance for counterbore bottom

            if abs(nx) > 0.9:
                # X-normal: counterbore bottom, flange front, block_cross, block_back
                if (abs(cx - side_cb_x) < cb_tol and
                    abs(cy) < cbore_rmm * 1.5 and abs(cz) < cbore_rmm * 1.5):
                    cbore_planar_n += 1
                    label = f"counterbore.bottom_{cbore_planar_n}"
                elif cx > bx_max + fl * 0.3:
                    flange_planar_n += 1
                    label = f"kf_flange.planar_{flange_planar_n}"
                elif cx > 0:
                    label = "block_cross"
                else:
                    label = "block_back"
            elif abs(ny) > 0.9:
                # Y-normal: counterbore bottom, flange front, block_top, block_bottom
                if (abs(cy - top_cb_y) < cb_tol and
                    abs(cx) < cbore_rmm * 1.5 and abs(cz) < cbore_rmm * 1.5):
                    cbore_planar_n += 1
                    label = f"counterbore.bottom_{cbore_planar_n}"
                elif (abs(cy - bot_cb_y) < cb_tol and
                      abs(cx) < cbore_rmm * 1.5 and abs(cz) < cbore_rmm * 1.5):
                    cbore_planar_n += 1
                    label = f"counterbore.bottom_{cbore_planar_n}"
                elif cy > by_top + fl * 0.3 or cy < by_bot - fl * 0.3:
                    flange_planar_n += 1
                    label = f"kf_flange.planar_{flange_planar_n}"
                elif cy > 0:
                    label = "block_top"
                else:
                    label = "block_bottom"
            elif abs(nz) > 0.9:
                # Z-normal: block_left / block_right
                if cz > 0:
                    label = "block_left"
                else:
                    label = "block_right"
            else:
                label = f"planar_n({nx:.2f},{ny:.2f},{nz:.2f})"

        else:
            label = f"type_{stype}"

        labels.append(label)

    # Second pass: if y_bore got split into two faces, rename the lower one
    ybore_indices = [i for i, l in enumerate(labels) if l == "y_bore"]
    if len(ybore_indices) == 2:
        # Find centroids for both, rename the one with lower Y
        cy_vals = []
        for idx in ybore_indices:
            face = faces[idx]
            props = GProp_GProps()
            BRepGProp.SurfaceProperties_s(face.wrapped, props)
            cy_vals.append(props.CentreOfMass().Y())
        lower = ybore_indices[0] if cy_vals[0] < cy_vals[1] else ybore_indices[1]
        labels[lower] = "y_bore_bottom"

    for i, label in enumerate(labels):
        face = faces[i]
        props = GProp_GProps()
        BRepGProp.SurfaceProperties_s(face.wrapped, props)
        c = props.CentreOfMass()
        print(f"  face {i+1:3d}: c=({c.X():.1f},{c.Y():.1f},{c.Z():.1f}) → {label}")

    return labels


# ── Write Labels into STEP ───────────────────────────────────────
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


# ── Main ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    result = build_geometry()
    cq.exporters.export(result, OUTPUT_PATH)

    labels = classify_faces(OUTPUT_PATH)
    write_labels(OUTPUT_PATH, labels)

    actual_angle = math.degrees(math.atan2(rim_r - base_r, taper_z))
    print(f"\nExported to {OUTPUT_PATH}")
    print(f"  {len(labels)} faces labeled")
    print(f"  KF10 flange: rim {rim_dia}\", base {base_dia}\", length {flange_len}\"")
    print(f"  Back taper: {taper_z:.3f}\" axial, {actual_angle:.1f}° from axis")
    print(f"  Block: {block_d} x {block_h} x {block_w} in")
