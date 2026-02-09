# blkarc_slot

Rectangular block (100mm x 50mm) with arc-shaped top surface (R=100mm cylindrical) and angled slot cut. Units: mm. 10 faces total.

## Named Faces

| Label | Type | Description |
|-------|------|-------------|
| `x_neg` | Planar | Face at x = -50 |
| `x_pos` | Planar | Face at x = +50 |
| `y_pos` | Planar | Side face at y = +25 |
| `y_neg` | Planar | Side face at y = -25 |
| `bottom_surface` | Planar | Bottom face at z = 0 |
| `top_surface.cylindrical_1` | Cylindrical | Right portion of arc top (R=100) |
| `top_surface.cylindrical_2` | Cylindrical | Left portion of arc top (R=100) |
| `slot.planar_1` | Planar | Slot wall (triangular face) |
| `slot.planar_2` | Planar | Slot wall (hexagonal face) |
| `slot.planar_3` | Planar | Slot wall (triangular face) |
