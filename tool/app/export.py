"""Export a mesh to the two files customers/team need: STL and 3MF (preferred)."""
from __future__ import annotations

import trimesh


def to_stl(mesh: trimesh.Trimesh) -> bytes:
    data = mesh.export(file_type="stl")
    return data if isinstance(data, bytes) else data.encode("utf-8")


def to_3mf(mesh: trimesh.Trimesh) -> bytes:
    data = mesh.export(file_type="3mf")
    return data if isinstance(data, bytes) else bytes(data)
