"""DM07: immutable human review tied to one exact artifact digest."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import re
from uuid import UUID


_SHA256 = re.compile(r"^[0-9a-f]{64}$")


class ReviewStatus(str, Enum):
    REVIEWED_ACCEPTED = "REVIEWED_ACCEPTED"
    REVIEWED_CORRECTED = "REVIEWED_CORRECTED"
    REJECTED = "REJECTED"
    STALE = "STALE"


class ReviewRecordError(ValueError):
    """Review identity, state, or artifact binding is invalid."""


@dataclass(frozen=True)
class ReviewRecord:
    review_id: str
    artifact_sha256: str
    reviewer_id: str
    status: ReviewStatus
    reason: str
    created_at: str
    supersedes_review_id: str | None = None
    contract_version: str = "1.0.0"

    def __post_init__(self) -> None:
        try:
            review_uuid = UUID(self.review_id)
            superseded = UUID(self.supersedes_review_id) if self.supersedes_review_id else None
        except (ValueError, TypeError, AttributeError) as exc:
            raise ReviewRecordError("review IDs must be UUIDs") from exc
        if review_uuid.version != 4 or (superseded and superseded.version != 4):
            raise ReviewRecordError("review IDs must be random UUIDv4")
        if not _SHA256.fullmatch(self.artifact_sha256):
            raise ReviewRecordError("review must bind to an artifact SHA256")
        if not self.reviewer_id.strip() or not self.reason.strip():
            raise ReviewRecordError("reviewer and reason are required")
        try:
            timestamp = datetime.fromisoformat(self.created_at)
        except ValueError as exc:
            raise ReviewRecordError("created_at must be ISO-8601") from exc
        if timestamp.tzinfo is None:
            raise ReviewRecordError("created_at must include a timezone")

    def invalidate(self, new_artifact_sha256: str, new_review_id: str) -> "ReviewRecord":
        if new_artifact_sha256 == self.artifact_sha256:
            raise ReviewRecordError("unchanged artifacts do not invalidate a review")
        return ReviewRecord(
            review_id=new_review_id,
            artifact_sha256=new_artifact_sha256,
            reviewer_id=self.reviewer_id,
            status=ReviewStatus.STALE,
            reason=f"Upstream artifact changed; supersedes {self.review_id}",
            created_at=datetime.now(timezone.utc).isoformat(),
            supersedes_review_id=self.review_id,
        )

