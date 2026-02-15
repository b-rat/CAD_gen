"""
Build script for labeled track bike crankset (drive-side crank).

5-arm spider with integrated crank arm, single piece.
Generates crankset.step with all features and face labels.

Usage:
    python build_crankset.py
"""

import cadquery as cq
import math
import re
from OCP.BRepGProp import BRepGProp
from OCP.GProp import GProp_GProps
from OCP.GeomAbs import (
    GeomAbs_Plane, GeomAbs_Cylinder, GeomAbs_Cone,
    GeomAbs_Torus, GeomAbs_BSplineSurface, GeomAbs_SurfaceOfRevolution,
)
from OCP.BRepAdaptor import BRepAdaptor_Surface

# ============================================================
# Parameters
# ============================================================

# Spider
bcd = 144.0                     # bolt circle diameter (mm)
bcd_r = bcd / 2.0               # 72mm
spider_od = 160.0               # spider outer diameter
spider_od_r = spider_od / 2.0   # 80mm
n_arms = 5
arm_angular_spacing = 360.0 / n_arms  # 72°

# Spider thickness profile (lenticular/diamond cross-section)
spider_max_thickness = 13.0     # at hub center
spider_rim_thickness = 3.5      # at outer rim

# Hub
hub_od = 40.0                   # hub outer diameter
hub_od_r = hub_od / 2.0         # 20mm
hub_height = 20.0               # total hub protrusion (centered on spider mid-plane)
hub_boss_od = 30.0              # turned-down hub boss diameter (axle interface)
hub_boss_r = hub_boss_od / 2.0

# Axle bore (blind hole from front face)
axle_bore_dia = 20.0
axle_bore_r = axle_bore_dia / 2.0
axle_bore_depth = 5.0           # depth below front face

# Square taper bore (JIS)
taper_wide = 12.65              # across flats at wide end (mm)
taper_angle = 2.0               # degrees per side
taper_length = hub_height       # bore runs full hub height
taper_narrow = taper_wide - 2 * taper_length * math.tan(math.radians(taper_angle))

# Bolt holes
bolt_hole_dia = 10.0            # chainring bolt clearance holes
bolt_hole_r = bolt_hole_dia / 2.0
bolt_cbore_dia = 12.0           # counterbore diameter on back face
bolt_cbore_r = bolt_cbore_dia / 2.0
bolt_cbore_depth = 1.0          # counterbore depth into back surface

# Spider arm geometry (constant-width arms, parallel edges)
arm_width = 16.0                # constant width of each arm (mm)

# Crank arm (connects spider hub to pedal boss)
crank_length = 165.0            # center-to-center (spindle to pedal axis)
crank_arm_thickness = 10.0      # constant Z thickness
crank_arm_width = 24.0          # constant Y width

# Pedal boss
pedal_boss_dia = 27.0           # boss cylinder diameter, matches arm width
pedal_boss_r = pedal_boss_dia / 2.0
pedal_boss_z_face = 30.0        # pedal interface face Z (30mm from chainring surface)
pedal_boss_thickness = 10.0     # boss thickness in Z

# Boss extension: protrude past arm in Z for sliver-free boolean union
boss_z_ext_bot = 0.5            # mm below arm bottom (minimal, for clean boolean)

# Pedal bore
pedal_bore_dia = 0.4958 * 25.4  # 9/16"-20 minor diameter = 12.59mm
pedal_bore_r = pedal_bore_dia / 2.0

# Fillets
fillet_arm_spider = 5.0         # spider-to-arm junction fillet
fillet_arm_hub = 3.0            # arm-to-hub junction fillet
fillet_boss_od = 4.0            # boss OD edge fillet (pedal face rim + backside)
fillet_boss_junction = 8.0      # arm-to-boss blending fillet

# Crank arm direction: arm #1 aligned with XZ plane (+X axis)
crank_arm_angle = 0.0           # degrees from +X axis

# Back-side revolved cut (triangular profile)
back_cut_od_r = bcd_r - bolt_hole_r - 3  # 64mm, clears bolt holes inside BCD
back_cut_depth = 12.0                     # depth at hub OD into part from Z=0

# Chainring pocket (annular shelf cut from front face)
chainring_pocket_id_r = 64.0              # ~2.5mm clearance inside bolt hole inner edge
chainring_pocket_floor_z = 3.0             # pocket floor height above back face

# Front-side (top) revolved cut
spider_thickness = 3.0                    # Z-thickness of spider disc
back_slope = back_cut_depth / (back_cut_od_r - hub_od_r)  # Z/R slope of back taper
# Inner radius where angled front surface meets front face (Z=hub_height)
front_cut_id_r = spider_od_r - (hub_height - spider_thickness) / back_slope

OUTPUT_PATH = "/Users/brianratliff/machine_learning/AI_CAD/crankset/crankset.step"


# ============================================================
# Geometry
# ============================================================

def _arc_point(r, angle_deg):
    """Helper: point on circle of radius r at given angle (degrees)."""
    a = math.radians(angle_deg)
    return (r * math.cos(a), r * math.sin(a))


def _arm_edge_point(arm_angle_deg, side, radius):
    """Where a constant-width arm edge intersects a circle.

    side: +1 = right/CCW edge, -1 = left/CW edge.
    The arm centerline is radial at arm_angle_deg. Edges are parallel
    lines offset by arm_width/2 perpendicular to the centerline.
    """
    theta = math.radians(arm_angle_deg)
    w2 = arm_width / 2.0
    t = math.sqrt(radius**2 - w2**2)
    x = t * math.cos(theta) - side * w2 * math.sin(theta)
    y = t * math.sin(theta) + side * w2 * math.cos(theta)
    return (x, y)


def build_geometry():
    """Build crankset from stock using boolean cuts, like a machinist.

    Features are added incrementally.
    """

    # --- Step 1: Stock cylinder ---
    # Spider OD diameter, total thickness = hub_height
    # Back face on XY datum (Z=0), extrudes in +Z
    spider = (
        cq.Workplane("XY")
        .circle(spider_od_r)
        .extrude(hub_height)
    )

    # --- Step 2: Back-side revolved cut ---
    # Triangular profile in XZ plane, revolved around Z axis.
    # ID = hub OD, OD = inside BCD (clears bolt holes).
    # Creates the conical back surface of the spider disc.
    # Triangle: (hub_od_r, 0) → (hub_od_r, back_cut_depth) → (back_cut_od_r, 0)
    back_cut = (
        cq.Workplane("XZ")
        .moveTo(hub_od_r, 0)
        .lineTo(hub_od_r, back_cut_depth)
        .lineTo(back_cut_od_r, 0)
        .close()
        .revolve(360, (0, 0), (0, 1))
    )
    spider = spider.cut(back_cut)

    # --- Step 3: Front-side (top) revolved cut ---
    # Triangular profile: OD at spider OD, follows back taper angle
    # offset by spider_thickness (5mm). ID is where that angle meets
    # the front face (Z=hub_height).
    # Triangle: (front_cut_id_r, hub_height) → (OD, hub_height) → (OD, front_z_at_od)
    overshoot = spider_od_r + 1
    front_z_at_od = spider_thickness + back_slope * (spider_od_r - overshoot)
    front_cut = (
        cq.Workplane("XZ")
        .moveTo(front_cut_id_r, hub_height)
        .lineTo(overshoot, hub_height)
        .lineTo(overshoot, front_z_at_od)
        .close()
        .revolve(360, (0, 0), (0, 1))
    )
    spider = spider.cut(front_cut)

    # --- Step 4: Chainring pocket ---
    # Annular shelf cut from front taper into the spider disc.
    # OD = spider OD (rim stays), ID = 3mm past back taper / back face intersection.
    # Floor at chainring_pocket_floor_z, cut from above.
    chainring_pocket = (
        cq.Workplane("XY")
        .workplane(offset=chainring_pocket_floor_z)
        .circle(spider_od_r)
        .circle(chainring_pocket_id_r)
        .extrude(hub_height)
    )
    spider = spider.cut(chainring_pocket)

    # --- Step 5: Arm window cuts ---
    # Constant-width arms with parallel edges. Inner arc slightly OUTSIDE
    # hub_od_r to avoid tangent boolean hang — leaves hub protruding slightly.
    arm_angles = [(crank_arm_angle + i * arm_angular_spacing) % 360
                  for i in range(n_arms)]
    inner_r = hub_od_r + 0.5  # outside hub to avoid tangent; hub protrudes
    outer_r = spider_od_r + 1

    for i in range(n_arms):
        a_this = arm_angles[i]
        a_next = arm_angles[(i + 1) % n_arms]
        if a_next <= a_this:
            a_next += 360
        w_center = (a_this + a_next) / 2.0

        A = _arm_edge_point(a_this, +1, inner_r)
        B = _arm_edge_point(a_this, +1, outer_r)
        C = _arm_edge_point(a_next, -1, outer_r)
        D = _arm_edge_point(a_next, -1, inner_r)

        outer_mid = _arc_point(outer_r, w_center)
        inner_mid = _arc_point(inner_r, w_center)

        window = (
            cq.Workplane("XY")
            .workplane(offset=-1)
            .moveTo(*A)
            .lineTo(*B)
            .threePointArc(outer_mid, C)
            .lineTo(*D)
            .threePointArc(inner_mid, A)
            .close()
            .extrude(hub_height + 2)
        )
        spider = spider.cut(window)

    # --- Step 5b: Spider inner corner fillets ---
    # 5mm fillets where arm walls meet hub cylinder (inner edges of windows).
    spider_corner_fillet_r = 5.0

    class SpiderInnerCornerSelector(cq.Selector):
        def filter(self, objectList):
            out = []
            for obj in objectList:
                c = obj.Center()
                bb = obj.BoundingBox()
                r_c = math.sqrt(c.x**2 + c.y**2)
                z_span = bb.zmax - bb.zmin
                if abs(r_c - (hub_od_r + 0.5)) < 2.0 and z_span > 1.0:
                    out.append(obj)
            return out

    spider = spider.edges(SpiderInnerCornerSelector()).fillet(spider_corner_fillet_r)

    # --- Step 5c: Shorten hub ---
    # Move hub back face 5mm in +Z (remove bottom 5mm of hub cylinder).
    hub_back_offset = 5.0
    hub_cutback = (
        cq.Workplane("XY")
        .workplane(offset=-1)
        .circle(hub_od_r)
        .extrude(hub_back_offset + 1)
    )
    spider = spider.cut(hub_cutback)

    # --- Step 5d: Turn hub boss to 30mm ---
    # Reduce hub boss from 40mm to 30mm diameter on back side only.
    # The back taper meets the hub at Z=back_cut_depth. The boss protrudes
    # from Z=hub_back_offset to Z=back_cut_depth. Turn this down to 30mm.
    hub_turn_back = (
        cq.Workplane("XY")
        .workplane(offset=hub_back_offset - 0.1)
        .circle(hub_od_r)
        .circle(hub_boss_r)
        .extrude(back_cut_depth - hub_back_offset + 0.1)
    )
    spider = spider.cut(hub_turn_back)

    # Note: no front-side turn needed — front taper already meets
    # the hub at Z≈19.4, leaving minimal protrusion on that side.

    # --- Step 5d2: Fillets on hub boss back cylinder edges ---
    # 3mm fillets where boss OD (r=15) meets back face (Z=5) and Z=12 shelf.
    hub_boss_fillet_r = 3.0

    class HubBossEdgeSelector(cq.Selector):
        def filter(self, objectList):
            out = []
            for obj in objectList:
                c = obj.Center()
                bb = obj.BoundingBox()
                edge_r = (bb.xmax - bb.xmin) / 2
                if abs(edge_r - hub_boss_r) < 1.0 and (
                    abs(c.z - hub_back_offset) < 0.5 or
                    abs(c.z - back_cut_depth) < 0.5
                ):
                    out.append(obj)
            return out

    spider = spider.edges(HubBossEdgeSelector()).fillet(hub_boss_fillet_r)

    # --- Step 8: Bolt holes ---
    # 5x 10mm through-holes on 144mm BCD, one centered on each arm.
    # 12mm x 1mm counterbore on back surface for barrel nut.
    for i in range(n_arms):
        angle = math.radians(arm_angles[i])
        bx = bcd_r * math.cos(angle)
        by = bcd_r * math.sin(angle)

        # Through-hole
        hole = (
            cq.Workplane("XY")
            .workplane(offset=-1)
            .center(bx, by)
            .circle(bolt_hole_r)
            .extrude(hub_height + 2)
        )
        spider = spider.cut(hole)

        # Counterbore on back face
        cbore = (
            cq.Workplane("XY")
            .workplane(offset=-0.5)
            .center(bx, by)
            .circle(bolt_cbore_r)
            .extrude(bolt_cbore_depth + 0.5)
        )
        spider = spider.cut(cbore)

    # --- Step 6+7+10: Combined crank arm + pedal boss ---
    # Arm built via sweep with rounded-rectangle cross-section (4mm corner
    # radii) so arm long-edge fillets are part of the geometry — no fillet
    # API needed. This avoids the OCCT bug where pre-filleting the arm
    # produces a COMPOUND after union with the boss (bore only cuts one body).
    arm_x_inner = 10              # 10mm past hub center
    arm_x_outer = -crank_length   # pedal end (boss center)

    top_z_in = hub_height                    # Z=20 at spider end
    top_z_out = pedal_boss_z_face            # Z=30 at boss end
    bot_z_in = top_z_in - crank_arm_thickness   # Z=10
    bot_z_out = top_z_out - crank_arm_thickness  # Z=20

    z_drop = top_z_out - top_z_in            # 10mm
    span = abs(arm_x_outer - arm_x_inner)    # 175mm

    # Arc radius for tangent-to-horizontal at boss end
    R_arm = (span**2 + z_drop**2) / (2 * z_drop)

    # Arm centerline: midpoint between top and bottom surfaces
    mid_z_in = (top_z_in + bot_z_in) / 2     # Z=15
    mid_z_out = (top_z_out + bot_z_out) / 2   # Z=25
    top_arc_cz = top_z_out - R_arm
    bot_arc_cz = bot_z_out - R_arm
    mid_arc_cz = (top_arc_cz + bot_arc_cz) / 2

    # 3-point arc midpoint for centerline path
    a0_m = math.atan2(mid_z_in - mid_arc_cz, arm_x_inner - arm_x_outer)
    a1_m = math.atan2(mid_z_out - mid_arc_cz, 0)
    a_mid_m = (a0_m + a1_m) / 2
    mid_path_pt = (arm_x_outer + R_arm * math.cos(a_mid_m),
                   mid_arc_cz + R_arm * math.sin(a_mid_m))

    # Path wire for sweep
    path_wire = (
        cq.Workplane("XZ")
        .moveTo(arm_x_inner, mid_z_in)
        .threePointArc(mid_path_pt, (arm_x_outer, mid_z_out))
        .val()
    )

    # Rounded rectangle cross-section (24mm wide × 10mm tall, 4mm corner radii)
    arm_fillet_r = 4.0
    w2 = crank_arm_width / 2        # 12mm half-width
    h2 = crank_arm_thickness / 2    # 5mm half-height
    c45 = arm_fillet_r * math.cos(math.radians(45))
    s45 = arm_fillet_r * math.sin(math.radians(45))

    crank_arm = (
        cq.Workplane("YZ")
        .workplane(offset=arm_x_inner)
        .center(0, mid_z_in)
        .moveTo(-w2 + arm_fillet_r, -h2)
        .lineTo(w2 - arm_fillet_r, -h2)
        .threePointArc((w2 - arm_fillet_r + c45, -h2 + arm_fillet_r - s45),
                       (w2, -h2 + arm_fillet_r))
        .lineTo(w2, h2 - arm_fillet_r)
        .threePointArc((w2 - arm_fillet_r + c45, h2 - arm_fillet_r + s45),
                       (w2 - arm_fillet_r, h2))
        .lineTo(-w2 + arm_fillet_r, h2)
        .threePointArc((-w2 + arm_fillet_r - c45, h2 - arm_fillet_r + s45),
                       (-w2, h2 - arm_fillet_r))
        .lineTo(-w2, -h2 + arm_fillet_r)
        .threePointArc((-w2 + arm_fillet_r - c45, -h2 + arm_fillet_r - s45),
                       (-w2 + arm_fillet_r, -h2))
        .close()
        .sweep(cq.Wire.assembleEdges([path_wire]), isFrenet=True)
    )

    # Pedal boss with both OD fillets built into the revolved profile.
    # Quarter-circle arcs at top and bottom edges avoid the fillet API
    # entirely (API fails because arm-boss intersection creates complex edges).
    boss_bot_z = pedal_boss_z_face - pedal_boss_thickness - boss_z_ext_bot
    fillet_r = fillet_boss_od  # 4mm radius for both top and bottom arcs

    # Top fillet: transitions from cylinder (r=boss_r) to flat face (Z=boss_z_face)
    top_fillet_start_z = pedal_boss_z_face - fillet_r       # Z=26
    top_arc_cx = pedal_boss_r - fillet_r                    # r=9.5
    top_arc_mid_r = top_arc_cx + fillet_r * math.cos(math.radians(45))
    top_arc_mid_z = top_fillet_start_z + fillet_r * math.sin(math.radians(45))

    # Bottom fillet: transitions from flat face (Z=boss_bot_z) to cylinder (r=boss_r)
    bot_fillet_end_z = boss_bot_z + fillet_r                # Z=23.5
    bot_arc_cx = pedal_boss_r - fillet_r                    # r=9.5
    bot_arc_mid_r = bot_arc_cx + fillet_r * math.cos(math.radians(45))
    bot_arc_mid_z = boss_bot_z + fillet_r - fillet_r * math.sin(math.radians(45))

    pedal_boss = (
        cq.Workplane("XZ")
        .moveTo(0, boss_bot_z)
        .lineTo(bot_arc_cx, boss_bot_z)
        .threePointArc((bot_arc_mid_r, bot_arc_mid_z), (pedal_boss_r, bot_fillet_end_z))
        .lineTo(pedal_boss_r, top_fillet_start_z)
        .threePointArc((top_arc_mid_r, top_arc_mid_z), (top_arc_cx, pedal_boss_z_face))
        .lineTo(0, pedal_boss_z_face)
        .close()
        .revolve(360, (0, 0), (0, 1))
    )
    pedal_boss = pedal_boss.translate((-crank_length, 0, 0))

    # Union arm + boss. Swept arm (rounded cross-section) unions cleanly
    # with boss as 1 solid — no COMPOUND issue.
    crank_combined = crank_arm.union(pedal_boss)

    # 2mm blending fillet where arm faces meet boss faces.
    # Select junction edges: near boss center, skip boss's own circular edges.
    boss_cx = -crank_length

    class BossJunctionSelector(cq.Selector):
        def filter(self, objectList):
            out = []
            for obj in objectList:
                bb = obj.BoundingBox()
                c = obj.Center()
                dist = math.sqrt((c.x - boss_cx)**2 + c.y**2)
                if dist > pedal_boss_r + 3:
                    continue
                # Skip full circles (boss flat face edges, cylinder sections)
                x_span = bb.xmax - bb.xmin
                y_span = bb.ymax - bb.ymin
                is_circle = (abs(x_span - y_span) < 1.0 and x_span > 10
                             and abs(c.x - boss_cx) < 1.0)
                if is_circle:
                    continue
                out.append(obj)
            return out

    crank_combined = crank_combined.edges(BossJunctionSelector()).fillet(fillet_boss_junction)

    spider = spider.union(crank_combined)

    # --- Step 9: Pedal bore ---
    # 9/16"-20 minor diameter through-hole at pedal boss center.
    # Cut extends through all bodies (boss + arm). Must be after arm union.
    pedal_hole = (
        cq.Workplane("XY")
        .workplane(offset=-1)
        .center(-crank_length, 0)
        .circle(pedal_bore_r)
        .extrude(pedal_boss_z_face + 2)
    )
    spider = spider.cut(pedal_hole)

    # --- Step 5e: Axle bore (blind hole from front face) ---
    # 20mm diameter, 5mm below front face, through everything above.
    # Must be after crank arm union so the arm doesn't fill the bore.
    axle_bore_floor_z = hub_height - axle_bore_depth  # Z=15
    axle_bore = (
        cq.Workplane("XY")
        .workplane(offset=axle_bore_floor_z)
        .circle(axle_bore_r)
        .extrude(pedal_boss_z_face - axle_bore_floor_z + 2)  # past arm top surface
    )
    spider = spider.cut(axle_bore)

    # --- Step 5f: JIS square taper bore ---
    # Tapered square hole along Z axis, wide end at back face.
    # 12.65mm across flats at hub back face, 2° per side narrowing toward front.
    taper_z_bottom = hub_back_offset - 1       # below back face for clean cut
    taper_z_top = axle_bore_floor_z + 1        # past bore floor to merge cleanly
    taper_span = taper_z_top - taper_z_bottom

    # Across-flats at bottom (wide) and top (narrow) of the cut
    af_bottom = taper_wide + 2 * (hub_back_offset - taper_z_bottom) * math.tan(math.radians(taper_angle))
    af_top = taper_wide - 2 * (taper_z_top - hub_back_offset) * math.tan(math.radians(taper_angle))

    taper_bore = (
        cq.Workplane("XY")
        .workplane(offset=taper_z_bottom)
        .rect(af_bottom, af_bottom)
        .workplane(offset=taper_span)
        .rect(af_top, af_top)
        .loft()
    )
    spider = spider.cut(taper_bore)

    # Ensure single solid body
    spider = spider.clean()

    return spider


# ============================================================
# Face labeling
# ============================================================

def _nearest_arm_index(angle_deg):
    """Find which spider arm is nearest to the given angle."""
    arm_angles = [(crank_arm_angle + i * arm_angular_spacing) % 360
                  for i in range(n_arms)]
    min_diff = 999
    best = 0
    for i, aa in enumerate(arm_angles):
        diff = abs(angle_deg - aa)
        if diff > 180:
            diff = 360 - diff
        if diff < min_diff:
            min_diff = diff
            best = i
    return best


def classify_faces(solid):
    """Classify each face by OCC surface type + centroid position.

    Takes the in-memory CQ solid (not a filepath) so the face count
    matches the STEP CLOSED_SHELL exactly. Re-importing from STEP can
    split faces during the round-trip, causing count mismatches.
    """
    occ_faces = solid.faces().vals()

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
            # Crank arm arc radius (large ~1000mm)
            arm_span = crank_length + 10  # matches arm_x_inner=10
            R_arm = (arm_span**2 + (pedal_boss_z_face - hub_height)**2) / (2 * (pedal_boss_z_face - hub_height))
            if abs(r - 5.0) < 0.5 and r_centroid < hub_od_r + 7:
                angle_deg = math.degrees(math.atan2(cy, cx)) % 360
                arm_idx = _nearest_arm_index(angle_deg)
                label = f"spider.fillet_{arm_idx + 1:02d}"
            elif abs(r - R_arm) < 5.0 and cx < hub_od_r:
                label = "arm.top" if cz > (hub_height + pedal_boss_z_face) / 2 - crank_arm_thickness / 2 else "arm.bottom"
            elif abs(r - spider_od_r) < 1.0:
                label = "spider.rim"
            elif abs(r - chainring_pocket_id_r) < 1.0:
                label = "chainring.pocket_id"
            elif abs(r - hub_boss_r) < 1.0 and r_centroid < hub_boss_r + 3:
                label = "hub.boss"
            elif abs(r - axle_bore_r) < 0.5 and r_centroid < axle_bore_r + 2:
                label = "axle.bore_wall"
            elif abs(r - (hub_od_r + 0.5)) < 0.3 or abs(r - (hub_od_r + 1)) < 0.5:
                # Arcs at window inner edge / hub turn transition
                angle_deg = math.degrees(math.atan2(cy, cx)) % 360
                arm_idx = _nearest_arm_index(angle_deg)
                label = f"arm.root_{arm_idx + 1:02d}"
            elif abs(r - hub_od_r) < 1.0:
                if abs(cy) > crank_arm_width / 2 - 4:
                    label = "hub.arm_junction"
                else:
                    label = "hub.outer"
            elif abs(r - bolt_hole_r) < 0.5 and abs(r_centroid - bcd_r) < bolt_hole_r:
                angle_deg = math.degrees(math.atan2(cy, cx)) % 360
                arm_idx = _nearest_arm_index(angle_deg)
                label = f"bolt.hole_{arm_idx + 1:02d}"
            elif abs(r - bolt_cbore_r) < 0.5 and abs(r_centroid - bcd_r) < bolt_cbore_r:
                angle_deg = math.degrees(math.atan2(cy, cx)) % 360
                arm_idx = _nearest_arm_index(angle_deg)
                label = f"bolt.cbore_{arm_idx + 1:02d}"
            elif abs(r - fillet_boss_junction) < 0.5 and cx < -(crank_length - pedal_boss_r - 5):
                label = "pedal.fillet"
            elif abs(r - pedal_boss_r) < 1.0 and cx < -(crank_length - pedal_boss_r):
                label = "pedal.boss"
            elif abs(r - pedal_bore_r) < 0.5:
                label = "pedal.bore"

        elif stype == GeomAbs_Cone:
            # Two conical faces: back taper (centroid below midpoint) and front taper
            if cz < (back_cut_depth / 2 + spider_thickness / 2):
                label = "spider.back_taper"
            else:
                label = "spider.front_taper"

        elif stype == GeomAbs_Torus:
            if cx < -(spider_od_r + 10):
                label = "pedal.fillet"
            else:
                label = "fillet"

        elif stype == GeomAbs_SurfaceOfRevolution:
            # Swept arm corner rounds (rounded cross-section edges).
            # Disambiguate top vs bottom by Z relative to arm midline.
            _mid_z_in = hub_height - crank_arm_thickness / 2       # 15
            _mid_z_out = pedal_boss_z_face - crank_arm_thickness / 2  # 25
            _arm_x_in = 10
            _arm_x_out = -crank_length
            mid_z_at_cx = _mid_z_in + (_mid_z_out - _mid_z_in) * (_arm_x_in - cx) / (_arm_x_in - _arm_x_out)
            if cz > mid_z_at_cx:
                label = "arm.fillet_top_right" if cy > 0 else "arm.fillet_top_left"
            else:
                label = "arm.fillet_bot_right" if cy > 0 else "arm.fillet_bot_left"

        elif stype == GeomAbs_BSplineSurface:
            # Boss junction fillet surfaces (near pedal boss)
            if cx < -(spider_od_r + 10):
                label = "pedal.fillet"
            # Loft creates BSpline for square taper walls
            elif r_centroid < taper_wide and abs(cz - 10) < 8:
                if abs(cx) > abs(cy):
                    label = "axle.taper_xp" if cx > 0 else "axle.taper_xn"
                else:
                    label = "axle.taper_yp" if cy > 0 else "axle.taper_yn"

        elif stype == GeomAbs_Plane:
            pln = surf.Plane()
            nz = pln.Axis().Direction().Z()
            if abs(nz) > 0.9:
                # Pedal boss faces (far from center, near crank_length)
                if cx < -(spider_od_r + 10):
                    boss_back_z = pedal_boss_z_face - pedal_boss_thickness - boss_z_ext_bot
                    if abs(cz - pedal_boss_z_face) < 0.5:
                        label = "pedal.face"
                    elif abs(cz - boss_back_z) < 0.5:
                        label = "pedal.back"
                    else:
                        label = f"pedal.planar_z{cz:.0f}"
                elif abs(cz - bolt_cbore_depth) < 0.2 and abs(r_centroid - bcd_r) < bolt_cbore_r:
                    angle_deg = math.degrees(math.atan2(cy, cx)) % 360
                    arm_idx = _nearest_arm_index(angle_deg)
                    label = f"bolt.cbore_floor_{arm_idx + 1:02d}"
                elif abs(cz) < 0.1:
                    label = "back"
                elif abs(cz - hub_height) < 0.1:
                    label = "front"
                elif abs(cz - (hub_height - axle_bore_depth)) < 0.2 and r_centroid < axle_bore_r:
                    label = "axle.bore_floor"
                elif abs(cz - chainring_pocket_floor_z) < 0.2:
                    label = "chainring.pocket_floor"
                elif abs(cz - back_cut_depth) < 0.5 and r_centroid > hub_od_r:
                    label = "spider.back_shelf"
                else:
                    label = f"planar_z{cz:.0f}"
            else:
                # Near-vertical planar faces
                if r_centroid < taper_wide and abs(nz) < 0.1:
                    # Square taper bore walls (4 faces near Z axis)
                    nx = pln.Axis().Direction().X()
                    ny = pln.Axis().Direction().Y()
                    if abs(nx) > abs(ny):
                        label = "axle.taper_xp" if nx > 0 else "axle.taper_xn"
                    else:
                        label = "axle.taper_yp" if ny > 0 else "axle.taper_yn"
                elif cx < -(hub_od_r + 5) and abs(cy) < crank_arm_width:
                    # Crank arm side faces
                    label = "arm.side_right" if cy > 0 else "arm.side_left"
                else:
                    label = "planar_vertical"

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

    # Find ALL CLOSED_SHELLs → ordered ADVANCED_FACE entity IDs
    face_eids = []
    for eid, (text, _) in entities.items():
        if text.startswith('CLOSED_SHELL'):
            face_eids.extend(int(x) for x in re.findall(r'#(\d+)', text))

    if not face_eids:
        raise RuntimeError("No CLOSED_SHELL found in STEP file")

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

    print("Building crankset geometry...")
    result = build_geometry()

    print(f"Exporting to {OUTPUT_PATH}")
    cq.exporters.export(result, OUTPUT_PATH)

    print("Classifying faces...")
    labels = classify_faces(result)

    print("Writing labels...")
    write_labels(OUTPUT_PATH, labels)

    # Summary
    counts = Counter()
    for l in labels:
        parts = l.split('.')
        # Group numbered items
        if len(parts) >= 2 and parts[-1].startswith(('0', '1', '2', '3', '4', '5')):
            key = '.'.join(parts[:-1])
        elif len(parts) >= 2 and any(p.startswith(('0', '1', '2', '3', '4', '5'))
                                     for p in parts):
            # e.g., spider.arm_01.front → spider.arm.front
            key = '.'.join(p.split('_')[0] if p[0].isdigit() else p for p in parts)
        else:
            key = l
        counts[key] += 1

    print(f"\n{len(labels)} faces:")
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")

    unlabeled = [l for l in labels if l == "?"]
    if unlabeled:
        print(f"\n  WARNING: {len(unlabeled)} unlabeled faces")
        # Print details for debugging
        occ_faces = result.faces().vals()
        for i, (face, lbl) in enumerate(zip(occ_faces, labels)):
            if lbl == "?":
                props = GProp_GProps()
                BRepGProp.SurfaceProperties_s(face.wrapped, props)
                cog = props.CentreOfMass()
                surf = BRepAdaptor_Surface(face.wrapped)
                stype2 = surf.GetType()
                extra = ""
                if stype2 == GeomAbs_Cylinder:
                    extra = f" cyl_r={surf.Cylinder().Radius():.2f}"
                print(f"    Face {i}: type={stype2} "
                      f"centroid=({cog.X():.1f}, {cog.Y():.1f}, {cog.Z():.1f}) "
                      f"area={props.Mass():.1f}{extra}")
    else:
        print("\nAll faces labeled.")
