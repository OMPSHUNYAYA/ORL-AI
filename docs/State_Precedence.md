# ORL-AI State Precedence

## Purpose

A single admitted structure may activate more than one condition. ORL-AI applies one frozen precedence order so that a lower-priority condition cannot mask a higher-priority condition.

The precedence is evaluated from highest to lowest:

1. `REFUSED / STRUCTURAL_INTAKE_REFUSAL`
2. `DENIED / ACTIVE_PROHIBITION`
3. `ABSTAIN / SOURCE_CONFLICT`
4. `ABSTAIN / MULTIPLE_ELIGIBLE_CANDIDATES`
5. `ABSTAIN / BLOCKING_DISAGREEMENT`
6. `ABSTAIN / COMPETING_PARTIAL_SUPPORT`
7. `INCOMPLETE / BOUNDARY_INCOMPLETE`
8. `RESOLVED / UNIQUE_ADMISSIBLE_CANDIDATE`
9. `INCOMPLETE / ADMISSION_REQUIREMENTS_UNMET`

`lower rank number -> higher precedence`

## Interpretation

`REFUSED` governs when the parsed document violates the supported structural contract. Raw parser refusals occur earlier and do not produce an ORL-AI bundle.

`DENIED` governs before boundary completeness. A supported candidate affected by an active prohibition is therefore denied even when the declared boundary is open or incomplete. This is a fail-closed structural rule; it does not imply that the remaining structure was complete.

Source-level contradiction and competing eligible candidates govern before ordinary opposition, partial competition, or boundary incompleteness.

A sealed, complete boundary with one eligible candidate resolves. If no candidate is eligible after higher-precedence conditions are absent, the result remains incomplete under the admission profile.

## Frozen Contests

The precedence verifier includes combined-condition scenarios such as:

- structural refusal over active prohibition;
- active prohibition over source conflict;
- active prohibition over boundary incompleteness;
- source conflict over multiple eligible candidates;
- multiple eligible candidates over opposition;
- blocking disagreement over boundary incompleteness;
- competing partial support over boundary incompleteness;
- boundary incompleteness over an otherwise admissible candidate.

Run:

```text
python -B verifier/ORL_AI_State_Precedence_Test_v5_0_0.py
```

The verifier asserts both the observed result and that the observed reason has the highest precedence among the deliberately injected conditions.

## Change Boundary

Changing this ordering changes the decision contract. Such a change requires a distinct ruleset boundary, regenerated examples and artifacts, and renewed cross-implementation verification.
