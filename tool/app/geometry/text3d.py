"""
Text → extruded 3D geometry, for simple personalization (names, short words).

Uses matplotlib's font engine purely to obtain glyph *outlines* (no window, no
GUI). If matplotlib is unavailable for any reason, every function degrades
gracefully to "no text" so the rest of the pipeline keeps working.
"""
from __future__ import annotations

import trimesh
from shapely.geometry import MultiPolygon, Polygon
from shapely.ops import unary_union

try:  # matplotlib is optional — text is a nice-to-have, not a hard dependency.
    from matplotlib.font_manager import FontProperties
    from matplotlib.textpath import TextPath
    _HAVE_MPL = True
except Exception:  # pragma: no cover - exercised only on broken installs
    _HAVE_MPL = False


def text_available() -> bool:
    return _HAVE_MPL


def _rings_to_polygon(rings: list[list]) -> Polygon | MultiPolygon | None:
    """
    Turn raw closed outlines into a clean (Multi)Polygon, resolving holes
    (e.g. the inside of an 'o' or 'a') via even–odd nesting depth.
    """
    polys = [Polygon(r) for r in rings if len(r) >= 3]
    polys = [p for p in polys if p.is_valid and p.area > 1e-9]
    if not polys:
        return None

    fills, holes = [], []
    for i, p in enumerate(polys):
        point = p.representative_point()
        depth = sum(1 for j, q in enumerate(polys) if j != i and q.contains(point))
        (holes if depth % 2 else fills).append(p)

    if not fills:
        return None
    solid = unary_union(fills)
    if holes:
        solid = solid.difference(unary_union(holes))
    return solid


def text_polygon(text: str, cap_height_mm: float) -> Polygon | MultiPolygon | None:
    """
    Build a 2D outline for `text`, scaled so its height ≈ cap_height_mm and
    centred on the origin. Returns None if text is empty or matplotlib is absent.
    """
    text = (text or "").strip()
    if not text or not _HAVE_MPL:
        return None

    fp = FontProperties(family="DejaVu Sans", weight="bold")
    path = TextPath((0, 0), text, size=100, prop=fp)
    rings = path.to_polygons(closed_only=True)
    poly = _rings_to_polygon(rings)
    if poly is None or poly.is_empty:
        return None

    minx, miny, maxx, maxy = poly.bounds
    h = maxy - miny
    if h <= 0:
        return None
    scale = cap_height_mm / h

    from shapely.affinity import scale as shp_scale
    from shapely.affinity import translate as shp_translate

    poly = shp_translate(poly, xoff=-(minx + maxx) / 2, yoff=-(miny + maxy) / 2)
    poly = shp_scale(poly, xfact=scale, yfact=scale, origin=(0, 0))
    return poly


def extrude_text(text: str, cap_height_mm: float, depth_mm: float,
                 z0: float = 0.0) -> trimesh.Trimesh | None:
    """Return an extruded-text mesh sitting at z = z0, or None if unavailable."""
    poly = text_polygon(text, cap_height_mm)
    if poly is None:
        return None

    parts = list(poly.geoms) if isinstance(poly, MultiPolygon) else [poly]
    meshes = []
    for part in parts:
        try:
            m = trimesh.creation.extrude_polygon(part, height=depth_mm)
            meshes.append(m)
        except Exception:
            continue
    if not meshes:
        return None
    mesh = trimesh.util.concatenate(meshes)
    if z0:
        mesh.apply_translation((0.0, 0.0, z0))
    return mesh
