# ORL-AI Integration Guide

## Recommended Placement

Place ORL-AI between proposal production and a separately governed authorization or execution layer.

`models and tools -> typed proposal adapter -> ORL-AI -> authorization policy -> execution system`

Do not send unrestricted prose directly to the resolver. Convert upstream outputs into the exact input schema and validate all declared identities and evidence references.

## Integration Steps

1. Define a bounded question and finite candidate set.
2. Freeze a ruleset, profile, and text-profile identifier.
3. Register source identifiers, declared families, and source classes.
4. Commit evidence objects with stable digests.
5. Convert each source result into `SUPPORT`, `OPPOSE`, or `ABSTAIN` for one candidate.
6. Declare the exact expected observation and evidence identifier sets.
7. Mark the boundary `SEALED` only when the application has completed its declared collection procedure.
8. Resolve the canonical document.
9. Store the private bundle in a protected location.
10. Distribute the public receipt or capsule only after reviewing its disclosure boundary.
11. Apply separate authorization before any real-world action.

## Source Adapters

A source adapter should bind:

- a stable `source_id`;
- a declared `source_family`;
- a source class;
- one candidate identifier;
- one stance;
- one or more evidence identifiers for support.

Adapters must not set `authority_mode` to any value other than `NONE`.

## Evidence Adapters

ORL-AI accepts evidence metadata, not raw documents. An integration may store evidence separately and provide:

```json
{
  "evidence_id": "e-policy",
  "kind": "RULE_RESULT",
  "digest": "sha256:<64 lowercase hexadecimal characters>"
}
```

The integration is responsible for defining what bytes were digested and how those bytes can be retrieved and authenticated.

## Handling States

For `RESOLVED`, treat the candidate as admitted only within the declared profile. Continue to separate authorization and execution.

For `INCOMPLETE`, inspect `repair_requirements` and obtain missing declared structure. Do not fabricate evidence or source classes.

For `ABSTAIN`, inspect `blockers`. Do not resolve disagreement by using arrival order or a hidden score.

For `DENIED`, inspect the active constraint. Changing the constraint creates a different input and result identity.

For a raw parser refusal, correct the JSON bytes before structural processing. For canonical `REFUSED`, correct the structural intake contract before resubmission.

## JavaScript Intake and Hashing

Use `demo/ORL_AI_Strict_Json_v5_0_0.js` before the JavaScript resolver when raw JSON text or bytes are accepted. Do not replace it with plain `JSON.parse`, which cannot detect duplicate keys. The browser laboratory loads the strict parser before the resolver.

The resolver uses Web Crypto when available, Node.js Web Crypto in Node environments, and its verified pure-JavaScript SHA-256 implementation otherwise. Direct `file:` use does not require a network service or external hashing dependency.

## Persistence

Store canonical UTF-8 JSON bytes with LF termination. Preserve:

- the original submitted bytes where required;
- the parsed submission commitment;
- the canonical bundle;
- the public receipt;
- the profile, ruleset, text-profile, and artifact-profile definitions;
- the software version;
- the selected-file checksum manifest when one is generated after the final file freeze.

## Privacy

The private bundle contains source, observation, and evidence identifiers. Apply access control appropriate to the deployment.

The public receipt reduces direct identifiers but remains linkable through deterministic commitments and identities.

## Domain Validation

Before use in any consequential domain, independently validate:

- candidate definitions;
- source-registration rules;
- source-family claims;
- evidence semantics;
- prohibition rules;
- false-positive and false-negative behavior;
- authorization controls;
- incident response;
- legal and regulatory requirements.

The reference examples use synthetic queue-routing identifiers and provide no domain recommendation.
