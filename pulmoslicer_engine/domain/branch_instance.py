"""DM03: stable pulmonary branch instances supporting trees and vein forests."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
import re
from uuid import UUID


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class BranchSystem(str, Enum):
    AIRWAY = "AIRWAY"
    PULMONARY_ARTERY = "PULMONARY_ARTERY"
    PULMONARY_VEIN = "PULMONARY_VEIN"


class BranchLabelStatus(str, Enum):
    SUGGESTED = "SUGGESTED"
    MANUAL = "MANUAL"
    UNKNOWN = "UNKNOWN"
    VARIANT = "VARIANT"


class BranchInstanceError(ValueError):
    """Branch topology, location, or provenance is invalid."""


@dataclass(frozen=True)
class BranchInstance:
    branch_id: str
    system: BranchSystem
    parent_ids: tuple[str, ...]
    child_ids: tuple[str, ...]
    centerline_lps_mm: tuple[tuple[float, float, float], ...]
    source_mask_sha256: str
    display_label: str
    label_status: BranchLabelStatus
    confidence: float | None = None
    contract_version: str = "1.0.0"

    def __post_init__(self) -> None:
        try:
            branch_uuid = UUID(self.branch_id)
            related = tuple(UUID(value) for value in (*self.parent_ids, *self.child_ids))
        except (ValueError, TypeError, AttributeError) as exc:
            raise BranchInstanceError("branch and relationship IDs must be UUIDs") from exc
        if branch_uuid.version != 4 or any(item.version != 4 for item in related):
            raise BranchInstanceError("branch IDs must be random UUIDv4")
        if self.branch_id in self.parent_ids or self.branch_id in self.child_ids:
            raise BranchInstanceError("branch cannot be its own parent or child")
        if len(set(self.parent_ids)) != len(self.parent_ids) or len(set(self.child_ids)) != len(self.child_ids):
            raise BranchInstanceError("branch relationships must be unique")
        if not _SHA256.fullmatch(self.source_mask_sha256):
            raise BranchInstanceError("source mask SHA256 is required")
        if len(self.centerline_lps_mm) < 2 or any(
            len(point) != 3 or not all(math.isfinite(value) for value in point)
            for point in self.centerline_lps_mm
        ):
            raise BranchInstanceError("centerline requires at least two finite LPS-mm points")
        if not self.display_label.strip():
            raise BranchInstanceError("branch label cannot be empty; use UNKNOWN explicitly")
        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            raise BranchInstanceError("confidence must be in [0, 1]")
        if self.label_status in {BranchLabelStatus.UNKNOWN, BranchLabelStatus.VARIANT} and self.confidence is not None:
            raise BranchInstanceError("unknown/variant labels cannot expose false numeric certainty")

