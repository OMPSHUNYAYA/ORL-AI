# ORL-AI Text Profile

## Identifier

`ORL-AI-UNICODE-SCALAR-EXACT-5-D01`

## Exact Sequence Rule

Strings are preserved as exact Unicode scalar sequences. No NFC, NFD, NFKC, NFKD, case folding, trimming, locale conversion, or visual-confusability mapping is applied.

`"café" != "cafe\u0301"`

The current schema restricts identifiers to ASCII letters, digits, `.`, `_`, `:`, and `-`, with an alphanumeric first character. Evidence digests use lowercase hexadecimal SHA-256 syntax.

## Refused Code Points

The Python producer, independent Python verifier, and JavaScript resolver refuse:

- surrogate code points;
- carriage return;
- U+FEFF;
- C0 controls except TAB and LF;
- C1 controls.

Most schema fields are identifiers and therefore have a narrower ASCII contract.

## Length and Resource Boundaries

The current implementation limits:

- string length to 512 code points during structural walking;
- recursive depth to 16;
- general array and object size to 512;
- candidates to 32;
- sources to 128;
- evidence items to 256;
- observations to 256;
- constraints to 128.

## Cross-Language Ordering

Object keys and set-like identifiers are ordered by exact Unicode scalar sequence rather than locale-sensitive comparison. The current identifiers remain ASCII-restricted, while the scalar comparator also governs unsupported object keys committed in deterministic refusal artifacts.

Unpaired surrogate escapes are refused during strict raw intake before canonical hashing.

## Change Rule

Changing character acceptance, normalization, identifier syntax, length bounds, control-code treatment, or canonical JSON encoding requires a new text-profile identifier and regenerated parity, corpus, receipt, capsule, falsification, and checksum artifacts.
