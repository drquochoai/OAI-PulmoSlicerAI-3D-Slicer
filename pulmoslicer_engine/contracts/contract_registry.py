"""CT01: supported contract versions and compatibility decisions."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import Mapping


_SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


class ContractVersionError(ValueError):
    """Raised when a contract name or semantic version is unsupported."""


def parse_semver(value: str) -> tuple[int, int, int]:
    if not isinstance(value, str) or not (match := _SEMVER.fullmatch(value)):
        raise ContractVersionError("contract version must be SemVer MAJOR.MINOR.PATCH")
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


@dataclass(frozen=True)
class ContractRegistry:
    """Immutable map of contract names to the newest readable version."""

    supported: Mapping[str, str] = field(
        default_factory=lambda: {
            "JobRequest": "1.0.0",
            "ImageGeometry": "1.0.0",
            "CompatibilityReport": "1.0.0",
            "SafeEvent": "1.0.0",
        }
    )

    def __post_init__(self) -> None:
        if not self.supported:
            raise ContractVersionError("contract registry cannot be empty")
        for name, version in self.supported.items():
            if not name or not isinstance(name, str):
                raise ContractVersionError("contract name must be non-empty")
            parse_semver(version)

    def require_readable(self, name: str, incoming: str) -> str:
        current = self.supported.get(name)
        if current is None:
            raise ContractVersionError(f"unknown contract: {name}")
        incoming_version = parse_semver(incoming)
        current_version = parse_semver(current)
        if incoming_version[0] != current_version[0]:
            raise ContractVersionError(
                f"INCOMPATIBLE_CONTRACT: {name} major {incoming_version[0]}"
            )
        if incoming_version > current_version:
            raise ContractVersionError(
                f"INCOMPATIBLE_CONTRACT: {name} {incoming} is newer than {current}"
            )
        return current

