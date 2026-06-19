"""
Low-level solid builders.

Everything here returns a watertight `trimesh.Trimesh`. We lean on shapely for
2D outlines (rounded rectangles, etc.) and extrude them, which keeps vertical
walls clean and the result manifold by construction. Boolean operations use the
manifold3d engine, which is robust and fast for the CSG shapes Phase 1 needs.
"""
from __future__ import annotations

import numpy as np
import trimesh
from shapely.geometry import Polygon
from shapely.geometry import box as shapely_box


# --------------------------------------------------------------------------- #
#  Boolean helper — always go through manifold3d, with a clear error if absent.
# --------------------------------------------------------------------------- #
def _boolean(op: str, meshes: list[trimesh.Trimesh]) -> trimesh.Trimesh:
    func = {
        "difference": trimesh.boolean.difference,
        "union": trimesh.boolean.union,
        "intersection": trimesh.boolean.intersection,
    }[op]
    try:
        result = func(meshes, engine="manifold")
    except TypeError:
        # Older/newer trimesh signatures: let it auto-pick the engine.
        result = func(meshes)
    if isinstance(result, list):
        result = trimesh.util.concatenate(result)
    return result


def difference(a: trimesh.Trimesh, *rest: trimesh.Trimesh) -> trimesh.Trimesh:
    return _boolean("difference", [a, *rest])


def union(*meshes: trimesh.Trimesh) -> trimesh.Trimesh:
    return _boolean("union", list(meshes))


# --------------------------------------------------------------------------- #
#  2D outlines
# --------------------------------------------------------------------------- #
def rounded_rect(length: float, width: float, radius: float) -> Polygon:
    """A length×width rectangle (centred on origin) with rounded vertical corners."""
    radius = max(0.0, min(radius, length / 2 - 1e-3, width / 2 - 1e-3))
    if radius <= 1e-3:
        return shapely_box(-length / 2, -width / 2, length / 2, width / 2)
    inner = shapely_box(
        -length / 2 + radius, -width / 2 + radius,
        length / 2 - radius, width / 2 - radius,
    )
    return inner.buffer(radius, join_style="round", quad_segs=24)


# --------------------------------------------------------------------------- #
#  Primitives
# --------------------------------------------------------------------------- #
def prism(polygon: Polygon, height: float, z0: float = 0.0) -> trimesh.Trimesh:
    """Extrude a 2D polygon to a solid prism whose base sits at z = z0."""
    mesh = trimesh.creation.extrude_polygon(polygon, height=height)
    if z0:
        mesh.apply_translation((0.0, 0.0, z0))
    return mesh


def rounded_box(length: float, width: float, height: float,
                radius: float = 0.0, z0: float = 0.0) -> trimesh.Trimesh:
    """A solid box with optionally rounded vertical edges, base at z = z0."""
    return prism(rounded_rect(length, width, radius), height, z0)


def cylinder(radius: float, height: float, z0: float = 0.0,
             sections: int = 96) -> trimesh.Trimesh:
    mesh = trimesh.creation.cylinder(radius=radius, height=height, sections=sections)
    # trimesh centres the cylinder on the origin; move base to z0.
    mesh.apply_translation((0.0, 0.0, height / 2 + z0))
    return mesh


def disc(radius: float, height: float, z0: float = 0.0, sections: int = 128) -> trimesh.Trimesh:
    return cylinder(radius, height, z0=z0, sections=sections)


# --------------------------------------------------------------------------- #
#  Finishing
# --------------------------------------------------------------------------- #
def cleanup(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Merge coincident vertices, fix winding/normals, drop tiny artefacts.

    Written defensively so it survives trimesh API drift across versions —
    manifold3d output is already clean, so this is mostly a safety net.
    """
    mesh.merge_vertices()
    for step in (
        lambda: mesh.update_faces(mesh.unique_faces()),
        lambda: mesh.update_faces(mesh.nondegenerate_faces()),
        lambda: mesh.remove_infinite_values(),
        lambda: mesh.fix_normals(),
    ):
        try:
            step()
        except Exception:
            pass
    return mesh


def place_on_bed(mesh: trimesh.Trimesh) -> trimesh.Trimesh:
    """Drop the mesh so its lowest point rests on z = 0 and it is centred in x/y."""
    bounds = mesh.bounds  # (2,3): min, max
    dx = -(bounds[0][0] + bounds[1][0]) / 2
    dy = -(bounds[0][1] + bounds[1][1]) / 2
    dz = -bounds[0][2]
    mesh.apply_translation((dx, dy, dz))
    return mesh
