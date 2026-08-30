import pytest

from velvet_communications import CommunicationCompiler, CommunicationFact, EvidenceReference


def evidence(system="velvet-receipts", reference="receipt:abc123"):
    return EvidenceReference(system=system, reference=reference)


def test_fact_requires_evidence():
    with pytest.raises(ValueError):
        CommunicationFact(fact_id="f1", statement="A thing happened.", evidence=())


def test_fact_rejects_unverified_confidence():
    with pytest.raises(ValueError):
        CommunicationFact(
            fact_id="f1",
            statement="A thing might have happened.",
            evidence=(evidence(),),
            confidence="uncertain",
        )


def test_compiler_produces_non_publishable_owner_review_draft():
    package = CommunicationCompiler().compile(
        audience="github",
        title="Milestone",
        facts=(
            CommunicationFact(
                fact_id="runtime-001",
                statement="Runtime completed the verified milestone.",
                evidence=(evidence(),),
            ),
        ),
    )

    assert package.status == "draft"
    assert package.owner_review_required is True
    assert package.publication_authority == "none"
    assert package.schema == "velvet.communications.draft-package.v1"
    assert package.fact_ids == ("runtime-001",)


def test_compiler_deduplicates_evidence_without_losing_fact_lineage():
    shared = evidence()
    package = CommunicationCompiler().compile(
        audience="public",
        title="Two verified changes",
        facts=(
            CommunicationFact("f1", "First verified change.", (shared,)),
            CommunicationFact("f2", "Second verified change.", (shared,)),
        ),
    )

    assert package.fact_ids == ("f1", "f2")
    assert package.evidence == (shared,)
    assert "First verified change." in package.body
    assert "Second verified change." in package.body


def test_compiler_rejects_duplicate_fact_ids():
    fact = CommunicationFact("f1", "Verified change.", (evidence(),))
    with pytest.raises(ValueError):
        CommunicationCompiler().compile(
            audience="developer",
            title="Duplicate",
            facts=(fact, fact),
        )


def test_compiler_rejects_unknown_audience():
    fact = CommunicationFact("f1", "Verified change.", (evidence(),))
    with pytest.raises(ValueError):
        CommunicationCompiler().compile(
            audience="autopublisher",
            title="Nope",
            facts=(fact,),
        )
