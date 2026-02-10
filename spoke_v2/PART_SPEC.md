# Spoke V2 — Part Spec

3-spoke disc with lenticular (double-taper) cross-section.

## Stock

- Cylinder: 200mm diameter, 20mm thick
- Bottom on XY plane (Z=0), centered on Z axis

## Features

### 1. Top revolved taper cut

Conical surface from center to rim, leaving a small top flat and an outer shelf.

| Parameter | Value |
|-----------|-------|
| Top flat diameter | 10mm (R=5) at Z=20 |
| Rim step height | 3mm from bottom (Z=3) |
| Rim step width | 10mm inward from OD (R=90→100) |
| Cone | (R=5, Z=20) → (R=90, Z=3) |

### 2. Bottom revolved conical recess

Concave cone cut upward from the bottom face.

| Parameter | Value |
|-----------|-------|
| Center bottom circle | 20mm diameter (R=10) at Z=0 |
| Bottom ring width | 10mm inward from OD (R=90→100) at Z=0 |
| Cone apex | Z=13 (7mm from top) at R=10 |
| Cone base | R=90 at Z=0 |

### 3. Spoke cutouts

3 spokes at 120° spacing with pizza-wedge windows between them.

| Parameter | Value |
|-----------|-------|
| Spoke count | 3 |
| Spoke width | 15mm (±7.5mm from radial centerline) |
| Hub diameter | 35mm (R=17.5) |
| First spoke | Along +X axis (0°) |

## Face inventory (23 faces)

| Label pattern | Count | Type | Description |
|---------------|-------|------|-------------|
| `top` | 1 | Plane | 10mm dia flat at Z=20 |
| `bottom` | 1 | Plane | 20mm dia center circle at Z=0 |
| `top_taper` | 1 | Cone | Upper conical surface |
| `bottom_taper` | 1 | Cone | Lower concave conical recess |
| `recess_wall` | 1 | Cylinder | Vertical wall at R=10 |
| `rim_NN` | 3 | Cylinder | Outer rim arcs at R=100 |
| `rim_step_NN` | 3 | Plane | Shelf faces at Z=3 |
| `bottom_ring_NN` | 3 | Plane | Bottom annular ring segments at Z=0 |
| `hub_NN` | 3 | Cylinder | Hub arcs at R=17.5 |
| `spoke_NN.left/right` | 6 | Plane | Spoke side walls |
