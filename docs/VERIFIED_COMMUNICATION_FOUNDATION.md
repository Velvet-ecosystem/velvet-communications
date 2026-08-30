# Verified Communication Foundation

The first working Communications slice is deliberately small.

```text
verified evidence owned elsewhere
        |
        v
CommunicationFact
  - fact_id
  - statement
  - evidence references
  - confidence = verified
        |
        v
CommunicationCompiler
        |
        v
DraftPackage
  - audience
  - title/body
  - fact lineage
  - evidence index
  - status = draft
  - owner_review_required = true
  - publication_authority = none
```

## Ownership

Receipts, Continuity, Runtime, Event Protocol, and other Velvet systems remain authoritative for their own records and contracts. Communications stores references to evidence; it does not become the canonical evidence store.

## Fail-closed behavior

The current compiler refuses:

- facts without evidence;
- facts whose confidence is not exactly `verified`;
- empty draft inputs;
- duplicate fact identifiers;
- unknown audience modes.

Evidence references are retained in the resulting draft package so claims remain traceable to the material that allowed them into communication.

## Publication boundary

There is no network publisher, social-media client, account credential handling, or external action executor in this foundation. A `DraftPackage` is preparation for review only.

Future generative rewriting may vary tone and length, but it must operate after fact admission and must not invent additional claims. Future publishing must use a separate authority-gated executor path rather than expanding the compiler into an autonomous publisher.
