"""
Render STEP files to multi-view PNG images using PyVista.

Converts CadQuery/OCC geometry to PyVista mesh, renders standard views
plus an optional section cut. Camera positions can be overridden via
--camera flag with JSON.

Usage:
    python render_step.py <step_file>                    # 4 default views
    python render_step.py <step_file> --section          # + section cut
    python render_step.py <step_file> -o output.png      # custom output path
    python render_step.py --cq <build_script.py>         # render from build script

    # Override cameras with JSON (inline or file):
    python render_step.py part.step --camera '{"iso": {"direction": [1,1,-0.3], "zoom": 0.9}}'
    python render_step.py part.step --camera views.json

Camera JSON format:
    {
        "iso":     {"direction": [1, 1, -0.6], "up": [0, 0, 1], "zoom": 0.85},
        "front":   {"direction": [0, 1, 0]},
        "back":    {"direction": [0, -1, 0]},
        "top":     {"direction": [0, 0, -1], "up": [0, -1, 0]},
        "section": {"direction": [0, 1, 0], "normal": [0, 1, 0], "origin": [0, 0, 0]}
    }
    All fields are optional — omitted fields use defaults.
"""

import argparse
import json
import os
import numpy as np
import pyvista as pv


# ============================================================
# Default view definitions
# ============================================================

DEFAULT_VIEWS = {
    "iso":     {"direction": [1, 1, -0.6],  "up": [0, 0, 1], "zoom": 0.85},
    "front":   {"direction": [0, 1, 0],     "up": [0, 0, 1], "zoom": 0.85},
    "back":    {"direction": [0, -1, 0],    "up": [0, 0, 1], "zoom": 0.85},
    "top":     {"direction": [0, 0, -1],    "up": [0, -1, 0], "zoom": 0.85},
    "section": {"direction": [0, 1, 0],     "up": [0, 0, 1], "zoom": 0.85,
                "normal": [0, 1, 0], "origin": [0, 0, 0]},
}

VIEW_ORDER = ["iso", "front", "back", "top", "section"]


# ============================================================
# Mesh loading
# ============================================================

def step_to_mesh(step_path, tolerance=0.5):
    """Load STEP file and tessellate to PyVista PolyData."""
    import cadquery as cq

    result = cq.importers.importStep(step_path)
    shape = result.val()
    verts, tris = shape.tessellate(tolerance)

    points = np.array([(v.x, v.y, v.z) for v in verts])
    pv_faces = np.hstack([[3, t[0], t[1], t[2]] for t in tris])

    return pv.PolyData(points, pv_faces)


def cq_to_mesh(build_script_path, tolerance=0.5):
    """Run a CadQuery build script and tessellate the result."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("build_mod", build_script_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    result = mod.build_geometry()
    shape = result.val()
    verts, tris = shape.tessellate(tolerance)

    points = np.array([(v.x, v.y, v.z) for v in verts])
    pv_faces = np.hstack([[3, t[0], t[1], t[2]] for t in tris])

    return pv.PolyData(points, pv_faces)


# ============================================================
# Camera
# ============================================================

def _set_camera(plotter, mesh, direction, up=(0, 0, 1), zoom=0.85):
    """Point camera at mesh center from a direction, then auto-fit."""
    bounds = mesh.bounds
    center = np.array([
        (bounds[0] + bounds[1]) / 2,
        (bounds[2] + bounds[3]) / 2,
        (bounds[4] + bounds[5]) / 2,
    ])
    diag = np.sqrt(
        (bounds[1] - bounds[0])**2 +
        (bounds[3] - bounds[2])**2 +
        (bounds[5] - bounds[4])**2
    )
    d = np.array(direction, dtype=float)
    d = d / np.linalg.norm(d)
    camera_pos = center - d * diag * 2.0
    plotter.camera_position = (tuple(camera_pos), tuple(center), tuple(up))
    plotter.reset_camera()
    plotter.camera.Zoom(zoom)


# ============================================================
# Rendering
# ============================================================

def _merge_views(overrides):
    """Merge user camera overrides into default view definitions."""
    views = {}
    for name in VIEW_ORDER:
        base = dict(DEFAULT_VIEWS.get(name, {}))
        if overrides and name in overrides:
            base.update(overrides[name])
        views[name] = base
    return views


def render_views(mesh, output_path, section=False, camera_overrides=None):
    """Render views of the mesh to a single PNG."""
    pv.OFF_SCREEN = True

    all_views = _merge_views(camera_overrides)
    active = [name for name in VIEW_ORDER if name != "section" or section]

    mesh_kwargs = dict(
        color="#6899CC",
        show_edges=False,
        smooth_shading=True,
        specular=0.3,
        ambient=0.3,
    )

    n = len(active)
    rows, cols = (2, 3) if n > 4 else (2, 2)
    cell_w, cell_h = 600, 500

    p = pv.Plotter(
        off_screen=True,
        shape=(rows, cols),
        window_size=[cell_w * cols, cell_h * rows],
        border=True,
    )

    for idx, name in enumerate(active):
        r, c = divmod(idx, cols)
        p.subplot(r, c)
        v = all_views[name]

        if name == "section":
            normal = v.get("normal", [0, 1, 0])
            origin = v.get("origin", [0, 0, 0])
            clipped = mesh.clip(normal=normal, origin=origin, invert=False)
            p.add_mesh(clipped, **mesh_kwargs)
            _set_camera(p, clipped,
                        v.get("direction", [0, 1, 0]),
                        up=v.get("up", [0, 0, 1]),
                        zoom=v.get("zoom", 0.85))
            # Readable label from normal direction
            axis_names = {(1,0,0): "X=0", (-1,0,0): "X=0",
                          (0,1,0): "Y=0", (0,-1,0): "Y=0",
                          (0,0,1): "Z=0", (0,0,-1): "Z=0"}
            n_key = tuple(int(x) for x in np.sign(normal))
            label = f"Section {axis_names.get(n_key, str(normal))}"
        else:
            p.add_mesh(mesh, **mesh_kwargs)
            _set_camera(p, mesh,
                        v["direction"],
                        up=v.get("up", [0, 0, 1]),
                        zoom=v.get("zoom", 0.85))
            label = name.capitalize()

        p.add_text(label, font_size=12, position="upper_left")

    p.screenshot(output_path)
    p.close()
    print(f"Rendered {n} views → {output_path}")


# ============================================================
# CLI
# ============================================================

def _parse_camera(camera_arg):
    """Parse --camera argument: inline JSON string or path to JSON file."""
    if camera_arg is None:
        return None
    # Try as file path first
    if os.path.isfile(camera_arg):
        with open(camera_arg) as f:
            return json.load(f)
    # Otherwise parse as inline JSON
    return json.loads(camera_arg)


def main():
    parser = argparse.ArgumentParser(
        description="Render STEP file to multi-view PNG",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("step_file", nargs="?", help="Path to STEP file")
    group.add_argument("--cq", metavar="SCRIPT", help="Path to CadQuery build script")
    parser.add_argument("-o", "--output", help="Output PNG path")
    parser.add_argument("--section", action="store_true",
                        help="Include section cut view")
    parser.add_argument("--tolerance", type=float, default=0.5,
                        help="Tessellation tolerance (smaller = finer mesh)")
    parser.add_argument("--camera", metavar="JSON",
                        help="Camera overrides: inline JSON or path to .json file")
    args = parser.parse_args()

    camera_overrides = _parse_camera(args.camera)

    if args.cq:
        mesh = cq_to_mesh(args.cq, tolerance=args.tolerance)
        default_out = args.cq.replace(".py", "_views.png")
    else:
        mesh = step_to_mesh(args.step_file, tolerance=args.tolerance)
        default_out = args.step_file.replace(".step", "_views.png")

    output_path = args.output or default_out
    render_views(mesh, output_path, section=args.section,
                 camera_overrides=camera_overrides)


if __name__ == "__main__":
    main()
