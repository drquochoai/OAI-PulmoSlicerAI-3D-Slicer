"""IN03: deterministic stage cache digests including geometry and model lineage."""

from __future__ import annotations

import hashlib
import json
from typing import Mapping


def build_cache_key(
    source_hash: str,
    affine: tuple[float, ...],
    model_hash: str,
    parameters: Mapping[str, object],
    code_revision: str,
) -> str:
    canonical = json.dumps(
        {
            "source_hash": source_hash,
            "affine": affine,
            "model_hash": model_hash,
            "parameters": parameters,
            "code_revision": code_revision,
        },
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()

