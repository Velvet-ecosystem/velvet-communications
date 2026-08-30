"""Public contracts for truth-bound communication preparation."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Tuple


@dataclass(frozen=True)
class EvidenceReference:
    """Reference to evidence owned by another Velvet system."""

    system: str
    reference: str
    kind: str = "verified_record"

    def __post_init__(self) -> None:
        if not self.system.strip() or not self.reference.strip():
            raise ValueError("evidence system and reference are required")


@dataclass(frozen=True)
class CommunicationFact:
    """A claim eligible for communication because evidence is attached."""

    fact_id: str
    statement: str
    evidence: Tuple[EvidenceReference, ...]
    confidence: str = "verified"

    def __post_init__(self) -> None:
        if not self.fact_id.strip():
            raise ValueError("fact_id is required")
        if not self.statement.strip():
            raise ValueError("statement is required")
        if not self.evidence:
            raise ValueError("at least one evidence reference is required")
        if self.confidence != "verified":
            raise ValueError("only verified facts may enter communication drafts")


@dataclass(frozen=True)
class DraftPackage:
    """Owner-reviewable communication artifact with no publication authority."""

    schema: str
    audience: str
    title: str
    body: str
    fact_ids: Tuple[str, ...]
    evidence: Tuple[EvidenceReference, ...]
    status: str = "draft"
    owner_review_required: bool = True
    publication_authority: str = "none"
    metadata: Mapping[str, str] = field(default_factory=dict)
