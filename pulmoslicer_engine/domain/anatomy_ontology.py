"""DM08: draft branch-label vocabulary; clinical approval remains external."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from .branch_instance import BranchSystem


DRAFT_ONTOLOGY_VERSION = "0.1.0-DRAFT-NOT-CLINICALLY-APPROVED"


@dataclass(frozen=True)
class AnatomyLabel:
    code: str
    system: BranchSystem
    display_name: str
    fused_components: tuple[str, ...] = ()


class AnatomyOntologyError(ValueError):
    """Requested label is absent or inappropriate for the branch system."""


class AnatomyOntology:
    """Small safety vocabulary, intentionally not a full clinical ontology."""

    def __init__(self, labels: Mapping[str, AnatomyLabel] | None = None) -> None:
        defaults = {
            "UNKNOWN_AIRWAY": AnatomyLabel("UNKNOWN_AIRWAY", BranchSystem.AIRWAY, "Unknown bronchus"),
            "VARIANT_AIRWAY": AnatomyLabel("VARIANT_AIRWAY", BranchSystem.AIRWAY, "Variant bronchus"),
            "B1+2": AnatomyLabel("B1+2", BranchSystem.AIRWAY, "Left B1+2 fused bronchus", ("B1", "B2")),
            "B7+8": AnatomyLabel("B7+8", BranchSystem.AIRWAY, "Left B7+8 fused bronchus", ("B7", "B8")),
            "UNKNOWN_PA": AnatomyLabel("UNKNOWN_PA", BranchSystem.PULMONARY_ARTERY, "Unknown pulmonary artery"),
            "VARIANT_PA": AnatomyLabel("VARIANT_PA", BranchSystem.PULMONARY_ARTERY, "Variant pulmonary artery"),
            "UNKNOWN_PV": AnatomyLabel("UNKNOWN_PV", BranchSystem.PULMONARY_VEIN, "Unknown pulmonary vein"),
            "VARIANT_PV": AnatomyLabel("VARIANT_PV", BranchSystem.PULMONARY_VEIN, "Variant pulmonary vein"),
        }
        self._labels = dict(labels or defaults)

    def resolve(self, code: str, system: BranchSystem) -> AnatomyLabel:
        label = self._labels.get(code)
        if label is None or label.system is not system:
            raise AnatomyOntologyError(f"label {code!r} is unavailable for {system.value}")
        return label

