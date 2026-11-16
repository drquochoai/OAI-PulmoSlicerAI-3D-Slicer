"""DM02: immutable segmentation metadata; source masks remain external artifacts."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Mapping
from uuid import UUID

from .case_geometry import CaseGeometry


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class SegmentationArtifactError(ValueError):
    """Segmentation metadata is incomplete or not tied to its source geometry."""


@dataclass(frozen=True)
class SegmentationArtifact:
    artifact_id: str
    source_volume_sha256: str
    geometry: CaseGeometry
    class_map: Mapping[int, str]
    mask_sha256_by_class: Mapping[str, str]
    model_id: str
    model_weight_sha256: str
    stage_status: str = "VALIDATED"
    coordinate_system: str = "LPS"
    units: str = "mm"
    contract_version: str = "1.0.0"

    def __post_init__(self) -> None:
        try:
            artifact_uuid = UUID(self.artifact_id)
        except (ValueError, TypeError, AttributeError) as exc:
            raise SegmentationArtifactError("artifact_id must be a UUID") from exc
        if artifact_uuid.version != 4:
            raise SegmentationArtifactError("artifact_id must be a random UUIDv4")
        hashes = (self.source_volume_sha256, self.model_weight_sha256, *self.mask_sha256_by_class.values())
        if not all(_SHA256.fullmatch(value) for value in hashes):
            raise SegmentationArtifactError("all artifact hashes must be lowercase SHA256")
        if self.source_volume_sha256 != self.geometry.source_volume_sha256:
            raise SegmentationArtifactError("segmentation source does not match geometry source")
        if self.coordinate_system != "LPS" or self.units != "mm":
            raise SegmentationArtifactError("segmentation exchange frame must be LPS-mm")
        if self.stage_status != "VALIDATED":
            raise SegmentationArtifactError("only validated masks may become segmentation artifacts")
        expected_names = set(self.class_map.values())
        if not expected_names or expected_names != set(self.mask_sha256_by_class):
            raise SegmentationArtifactError("class map and mask hashes must match exactly")
        if len(expected_names) != len(self.class_map):
            raise SegmentationArtifactError("class names must be unique")

