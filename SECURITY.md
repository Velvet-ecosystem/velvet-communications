# Security Policy

Velvet Communications prepares owner-reviewable communication from verified evidence. It does not publish autonomously and must not become an authority boundary.

## Sensitive material

Do not commit:

- credentials, API keys, bearer tokens, private keys, or certificates;
- private customer/user information or owner-only records;
- private receipts, continuity stores, runtime databases, or raw deployment logs;
- unreviewed media containing sensitive locations, identities, screens, or infrastructure details;
- deployment-local configuration that exposes private network or service details.

Generated drafts, exports, private media, runtime data, token/key material, and common local configuration are excluded by `.gitignore`.

## Authority boundary

A communication draft is not permission to publish. `publication_authority` remains `none`; owner review is required. Any future external publisher must live behind an explicit approved executor/authority path and must not be introduced as an implicit capability of the draft compiler.

Communications consumes references to evidence owned by systems such as Receipts and Continuity. It does not rewrite those sources, fabricate evidence, grant Runtime/Court authority, or convert uncertain material into verified fact.

## Reporting a vulnerability

Please avoid posting exploitable security details publicly before maintainers can review them. Use GitHub private vulnerability reporting when available. Otherwise contact the maintainers through an appropriate private project channel and include the affected version, reproduction details, impact, and suggested mitigation if known.
