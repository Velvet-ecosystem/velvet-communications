"""Compile verified facts into owner-reviewable communication drafts."""
from __future__ import annotations

from typing import Iterable, Sequence

from .contracts import CommunicationFact, DraftPackage, EvidenceReference


SCHEMA = "velvet.communications.draft-package.v1"
ALLOWED_AUDIENCES = {
    "owner",
    "developer",
    "public",
    "github",
    "tiktok",
    "youtube",
    "presentation",
    "documentation",
}


class CommunicationCompiler:
    """Deterministic compiler for evidence-backed draft communication."""

    def compile(
        self,
        *,
        audience: str,
        title: str,
        facts: Sequence[CommunicationFact],
        introduction: str = "",
    ) -> DraftPackage:
        audience_key = audience.strip().lower()
        if audience_key not in ALLOWED_AUDIENCES:
            raise ValueError("unsupported audience")
        title = title.strip()
        if not title:
            raise ValueError("title is required")
        if not facts:
            raise ValueError("at least one verified fact is required")

        seen_fact_ids = set()
        statements = []
        evidence = []
        evidence_keys = set()
        for fact in facts:
            if fact.fact_id in seen_fact_ids:
                raise ValueError("duplicate fact_id: %s" % fact.fact_id)
            seen_fact_ids.add(fact.fact_id)
            statements.append(fact.statement.strip())
            for ref in fact.evidence:
                key = (ref.system, ref.reference, ref.kind)
                if key not in evidence_keys:
                    evidence_keys.add(key)
                    evidence.append(ref)

        body_parts = []
        if introduction.strip():
            body_parts.append(introduction.strip())
        body_parts.extend(statements)
        body = "\n\n".join(body_parts)

        return DraftPackage(
            schema=SCHEMA,
            audience=audience_key,
            title=title,
            body=body,
            fact_ids=tuple(fact.fact_id for fact in facts),
            evidence=tuple(evidence),
            metadata={"compiler": "deterministic_verified_fact_v1"},
        )

    @staticmethod
    def evidence_index(facts: Iterable[CommunicationFact]) -> tuple[EvidenceReference, ...]:
        refs = []
        seen = set()
        for fact in facts:
            for ref in fact.evidence:
                key = (ref.system, ref.reference, ref.kind)
                if key not in seen:
                    seen.add(key)
                    refs.append(ref)
        return tuple(refs)
