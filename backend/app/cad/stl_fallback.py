"""Pure-Python binary STL writer for a rectangular box.

Exists so the golden path completes even without the CAD kernel installed.
Anything produced by this module is a labeled PLACEHOLDER, never presented
as real geometry.
"""

import struct
from pathlib import Path


def write_box_stl(path: Path, length: float, width: float, height: float) -> None:
    """Write a binary STL of an axis-aligned box centered in XY, base at z=0."""
    hx, hy = length / 2.0, width / 2.0
    v = [
        (-hx, -hy, 0), (hx, -hy, 0), (hx, hy, 0), (-hx, hy, 0),
        (-hx, -hy, height), (hx, -hy, height), (hx, hy, height), (-hx, hy, height),
    ]
    # 12 triangles (2 per face), outward-facing normals
    faces = [
        ((0, 2, 1), (0, 0, -1)), ((0, 3, 2), (0, 0, -1)),      # bottom
        ((4, 5, 6), (0, 0, 1)), ((4, 6, 7), (0, 0, 1)),        # top
        ((0, 1, 5), (0, -1, 0)), ((0, 5, 4), (0, -1, 0)),      # front
        ((2, 3, 7), (0, 1, 0)), ((2, 7, 6), (0, 1, 0)),        # back
        ((1, 2, 6), (1, 0, 0)), ((1, 6, 5), (1, 0, 0)),        # right
        ((3, 0, 4), (-1, 0, 0)), ((3, 4, 7), (-1, 0, 0)),      # left
    ]
    with open(path, "wb") as f:
        f.write(b"PLACEHOLDER BOX STL - not real geometry".ljust(80, b"\0"))
        f.write(struct.pack("<I", len(faces)))
        for (i, j, k), n in faces:
            f.write(struct.pack("<3f", *n))
            for idx in (i, j, k):
                f.write(struct.pack("<3f", *v[idx]))
            f.write(struct.pack("<H", 0))
