# Showerhead Tee — Part Spec

Vacuum manifold block with three KF10 flanges (top, bottom, side) and internal bores.

## Dimensions (inches)

All parameters in inches. CadQuery works in mm; `IN = 25.4` scaling applied at API calls.

### Block

| Parameter | Value | Direction |
|-----------|-------|-----------|
| Width | 1.18 | Z |
| Height | 2.59 | Y |
| Depth | 2.18 | X |
| Y bottom | -2.0 | — |
| Y top | 0.59 | — |
| +X face | 1.59 | side flange interface |
| -X face | -0.59 | — |

### KF10 Flange (body of revolution)

| Parameter | Value |
|-----------|-------|
| Rim diameter | 1.18 |
| Base diameter | 0.49 |
| Bore diameter | 0.35 |
| Rim width | 0.12 |
| Back taper angle | 15° from front face (75° from axis) |
| Taper axial depth | 0.092 |
| Base axial depth | 0.288 |
| Total length (front→interface) | 0.50 |

### Counterbores

| Parameter | Value |
|-----------|-------|
| Diameter | 0.49 |
| Depth | 0.10 |
| Location | Each flange front (sealing) face |

### Fillets

| Parameter | Value |
|-----------|-------|
| Radius | 0.25 |
| Location | block_cross ↔ block_top, block_cross ↔ block_bottom edges |

## Flange placement

| Flange | Interface face | Axis |
|--------|---------------|------|
| Top | Y = +0.59 (block_y_top) | +Y |
| Bottom | Y = -2.0 (block_y_bot) | -Y |
| Side | X = +1.59 (half_d) | +X |

## Bores

| Bore | Axis | Start | End |
|------|------|-------|-----|
| y_bore | Y | Through bottom flange | Through top flange |
| cross_bore | X | YZ plane (X=0) | Through side flange |

## Face inventory (28 faces)

| Label pattern | Count | Type | Description |
|---------------|-------|------|-------------|
| `block_top` | 1 | Plane | +Y block face |
| `block_bottom` | 1 | Plane | -Y block face |
| `block_cross` | 1 | Plane | +X block face (side flange interface) |
| `block_back` | 1 | Plane | -X block face |
| `block_left` | 1 | Plane | +Z block face |
| `block_right` | 1 | Plane | -Z block face |
| `fillet.cross_top_N` | 1 | Cylinder | Fillet at block_cross ↔ block_top |
| `fillet.cross_bottom_N` | 1 | Cylinder | Fillet at block_cross ↔ block_bottom |
| `kf_flange.cylindrical_N` | 6 | Cylinder | Flange rims + bases |
| `kf_flange.conical_N` | 3 | Cone | Back taper surfaces |
| `kf_flange.planar_N` | 3 | Plane | Front (sealing) face rings |
| `counterbore.wall_N` | 3 | Cylinder | Counterbore cylindrical walls |
| `counterbore.bottom_N` | 3 | Plane | Counterbore annular bottoms |
| `y_bore` | 1 | Cylinder | Vertical through-bore |
| `cross_bore` | 1 | Cylinder | Horizontal bore (X=0 to side flange) |
