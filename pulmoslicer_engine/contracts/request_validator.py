"""CT02: strict validation of an isolated-worker job envelope."""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any, Mapping
from uuid import UUID

from .contract_registry import ContractRegistry, ContractVersionError


_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_STAGE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
_FIELDS = frozenset(
    {"contract_version", "job_id", "case_id", "stage_id", "input_hashes", "parameters"}
)


class RequestValidationError(ValueError):
    """A job request is malformed or violates the process contract."""


@dataclass(frozen=True)
class JobRequest:
    contract_version: str
    job_id: str
    case_id: str
    stage_id: str
    input_hashes: tuple[str, ...]
    parameters: Mapping[str, Any]


def _random_uuid(value: object, field_name: str) -> str:
    try:
        parsed = UUID(str(value))
    except (ValueError, TypeError, AttributeError) as exc:
        raise RequestValidationError(f"{field_name} must be a UUID") from exc
    if parsed.version != 4:
        raise RequestValidationError(f"{field_name} must be a random UUIDv4")
    return str(parsed)


def validate_job_request(
    payload: Mapping[str, Any], registry: ContractRegistry | None = None
) -> JobRequest:
    if not isinstance(payload, Mapping):
        raise RequestValidationError("job request must be an object")
    unknown = set(payload) - _FIELDS
    missing = _FIELDS - set(payload)
    if unknown or missing:
        raise RequestValidationError(
            f"invalid fields; missing={sorted(missing)}, unknown={sorted(unknown)}"
        )
    registry = registry or ContractRegistry()
    try:
        registry.require_readable("JobRequest", payload["contract_version"])
    except ContractVersionError as exc:
        raise RequestValidationError(str(exc)) from exc
    stage_id = payload["stage_id"]
    if not isinstance(stage_id, str) or not _STAGE.fullmatch(stage_id):
        raise RequestValidationError("stage_id must be a lowercase safe identifier")
    hashes = payload["input_hashes"]
    if not isinstance(hashes, list) or not hashes or not all(
        isinstance(item, str) and _SHA256.fullmatch(item) for item in hashes
    ):
        raise RequestValidationError("input_hashes must be a non-empty SHA256 list")
    parameters = payload["parameters"]
    if not isinstance(parameters, Mapping):
        raise RequestValidationError("parameters must be an object")
    return JobRequest(
        contract_version=payload["contract_version"],
        job_id=_random_uuid(payload["job_id"], "job_id"),
        case_id=_random_uuid(payload["case_id"], "case_id"),
        stage_id=stage_id,
        input_hashes=tuple(hashes),
        parameters=dict(parameters),
    )

