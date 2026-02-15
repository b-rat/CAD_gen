# Crankset

Track bike drive-side crank — 5-arm spider with integrated crank arm, single piece. 104 faces total. Machinist approach (stock → subtract material).

## Key Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| BCD | 144mm | Track standard, 5-bolt |
| Spider OD | 160mm | |
| Hub OD | 40mm (turned to 30mm boss) | Axle interface area |
| Hub height | 20mm | Z=0 (back) to Z=20 (front/chainring side) |
| Spider thickness | 3mm | Lenticular profile, thick at hub, thin at rim |
| Crank arm length | 165mm | Center-to-center, spindle to pedal |
| Crank arm | 24mm wide, 10mm thick, 4mm corner radii | Swept rounded-rectangle cross-section |
| Pedal boss | 27mm dia, 10mm thick | 4mm OD fillets built into revolved profile |
| Boss junction fillet | 8mm | Blending fillet where arm meets boss |
| Axle bore | 20mm dia, 5mm deep blind hole | From front face |
| Square taper | JIS, 12.65mm across flats, 2°/side | Wide end at back |
| Bolt holes | 5x 10mm through, 12mm x 1mm counterbore | On 144mm BCD |
| Chainring pocket | Floor at Z=3, ID at r=64mm | |
| Pedal bore | 12.59mm (9/16"-20 minor dia) | Through all bodies |

## Build Order (build_crankset.py)

1. Stock cylinder (spider OD x hub height)
2. Back-side revolved triangular cut (conical back taper)
3. Front-side revolved triangular cut (conical front taper, 3mm spider thickness)
4. Chainring pocket (annular shelf)
5. Arm window cuts (5 windows, inner_r = hub_od_r + 0.5 to avoid tangent boolean)
5b. Spider inner corner fillets (5mm, at window/hub junction)
5c. Hub shortening (back face moved to Z=5)
5d. Hub boss turn-down (40mm → 30mm, back side only)
5d2. Hub boss edge fillets (3mm, both Z=5 and Z=12 edges)
6+7+10. Crank arm (swept rounded-rect cross-section) + pedal boss (revolved profile with built-in 4mm OD fillets) + 8mm junction fillet
8. Bolt holes + counterbores
9. Pedal bore (after arm union to cut through all bodies)
5e. Axle bore (after all unions so arm doesn't fill it back in)
5f. JIS square taper bore (loft between wide and narrow square profiles)

## Named Faces

| Label Pattern | Count | Description |
|--------------|-------|-------------|
| `spider.back_taper` | 1 | Conical back surface |
| `spider.front_taper` | 1 | Conical front surface |
| `spider.rim` | 5 | Outer cylindrical rim segments |
| `spider.fillet_NN` | 10 | Inner corner fillets (2 per arm) |
| `chainring.pocket_floor` | 5 | Pocket floor segments |
| `chainring.pocket_id` | 5 | Pocket inner diameter wall |
| `hub.boss` | 1 | Turned-down 30mm cylindrical surface |
| `axle.bore_wall` | 1 | 20mm blind bore cylinder |
| `axle.bore_floor` | 1 | Blind bore floor |
| `axle.taper_xp/xn/yp/yn` | 4 | Square taper walls |
| `bolt.hole_NN` | 5 | Through-holes on BCD |
| `bolt.cbore_NN` | 5 | Counterbore cylinders |
| `bolt.cbore_floor_NN` | 5 | Counterbore floor faces |
| `arm.top` / `arm.bottom` | 3/1 | Crank arm curved surfaces (sweep) |
| `arm.side_left` / `arm.side_right` | 2/2 | Crank arm side faces |
| `arm.fillet_top_left` / `_right` / `_bot_left` / `_bot_right` | 4 | Swept arm corner rounds (SurfaceOfRevolution) |
| `arm.root_NN` | ~5 | Hub/window junction arcs |
| `pedal.face` / `pedal.back` / `pedal.boss` / `pedal.bore` | 1 each | Pedal boss features |
| `pedal.fillet` | 16 | Boss OD fillets + junction blending fillets |
| `fillet` | 2 | Hub boss toroidal fillets |
| `front` / `back` | 1/5 | Major planar faces |
