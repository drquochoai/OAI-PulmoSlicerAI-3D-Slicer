"""Compact deterministic encoding for independent browser mesh chunks."""

from __future__ import annotations

from array import array
import base64
import gzip
import hashlib
import struct
import sys


MAGIC = b"PS3D1\0\0\0"


def _little_endian_bytes(typecode: str, values) -> bytes:
    data = array(typecode, values)
    if sys.byteorder != "little":
        data.byteswap()
    return data.tobytes()


def encode_mesh(positions, indices) -> tuple[str, str, int, bytes]:
    if len(positions) % 3:
        raise ValueError("Position array length must be divisible by 3")
    if len(indices) % 3:
        raise ValueError("Index array length must be divisible by 3")
    vertex_count = len(positions) // 3
    if vertex_count == 0 or not indices:
        raise ValueError("Mesh must contain vertices and triangles")
    if min(indices) < 0 or max(indices) >= vertex_count:
        raise ValueError("Mesh index is outside the vertex array")
    raw = b"".join(
        (
            MAGIC,
            struct.pack("<II", vertex_count, len(indices)),
            _little_endian_bytes("f", positions),
            _little_endian_bytes("I", indices),
        )
    )
    compressed = gzip.compress(raw, compresslevel=9, mtime=0)
    digest = hashlib.sha256(compressed).hexdigest()
    return base64.b64encode(compressed).decode("ascii"), digest, len(compressed), raw


def source_geometry_hash(positions, indices) -> str:
    digest = hashlib.sha256()
    digest.update(_little_endian_bytes("f", positions))
    digest.update(_little_endian_bytes("I", indices))
    return digest.hexdigest()
