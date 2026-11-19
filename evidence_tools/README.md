# Offline demo evidence verifier

This standard-library tool checks the internal consistency of one synthetic public
demonstration: a passing baseline, an intentionally incorrect self-approval
revision, and a corrected revision. It reads JSON and file bytes. It never imports
or executes submitted candidate/test files and makes no network requests.

Run it from the public demo repository root with Python 3.11 or later:

    python3 evidence_tools/verify_evidence.py evidence-manifest.json

Exit status 0 and `valid: true` mean that the supplied hashes, chain, references and
recorded outcomes agree. Exit status 1 means evidence is missing, malformed or
inconsistent. The report always labels its conclusion `internal_consistency_only`
and `github_checked: false`.

Hashes are not signatures or host attestation. Anyone able to rewrite the bundle
can construct another internally consistent bundle. The verifier does not prove
that execution occurred, that GitHub accepted a check, that the supplied source
belongs to a Git commit, or that the eleven examples cover every input. Public
commit and check links let reviewers inspect those separately. A package digest
identifies the recorded implementation; it does not disclose or independently
audit a private implementation.

## Manifest and files

Place `evidence-manifest.json` at the demo repository root. All inventory and
reference paths are relative to that directory. Absolute paths, parent traversal,
links and reparse points are rejected. Individual files are limited to 4 MiB and
the inventoried bundle to 64 MiB.

`manifest.schema.json` specifies the manifest's JSON shape. The executable
verifier also checks relationships that JSON Schema cannot express.
`manifest.example.json` is a **non-runnable layout template** with fictional
IDs and zero hashes. Its artifact inventory is abbreviated: an actual manifest
must list every receipt file as well as the index, policy, tests and candidates.

The required fields are:

| Field | Meaning |
| --- | --- |
| `format` | `jovin-demo.evidence.v1` |
| `classification` | `synthetic-public-demo` |
| `repository` | Exact GitHub `full_name` and numeric `id` recorded by the gate |
| `branch`, `pull_request` | Target branch and the same draft PR's numeric identifier |
| `modules` | One object with enrolled repository `path` and inventoried `tests` file |
| `policy` | Public policy object's `path` and canonical JSON `sha256` |
| `artifacts` | Every input file's literal `path`, exact byte length `bytes` and raw-byte `sha256` |
| `chain` | Index path, record count, final receipt ID and final receipt SHA-256 |
| `stages` | Exactly `baseline`, `bad`, `fixed`; each has commit, source snapshot path, gate receipt ID/hash and optional check URL |

The public policy file contains exactly the enrollment bundle's `policy`
object. It does not contain the credential reference, local active pointer or
runtime state. Its digest is SHA-256 over UTF-8 JSON serialized with sorted keys,
no separator whitespace, non-ASCII characters preserved and non-finite numbers
disallowed. Artifact hashes separately cover the actual bytes of each file.

The receipt index is the original `index.jsonl`. Each indexed receipt must be an
unmodified `<receipt-id>.json` next to it and present in the artifact inventory.
The export must begin at a null predecessor and contain every record through
the declared head. No redacted receipt can retain the validity of its old hash.

Use a fresh dedicated public-demo store. Review all receipts before publication:
they may contain an operator account, engine identity, runtime metadata and
untrusted diagnostics. Never include an existing private mixed chain, App keys,
installation tokens, private deployment configuration or unrelated logs.

## Checked relationships

The tool verifies all artifact bytes and complete receipt hash-chain links,
including duplicate IDs, missing/unindexed records and the declared head. JSON
with duplicate keys or non-finite numbers is rejected.

The policy, enrolled plan, tests, gate records, each ordered QA stage and functional
execution records must bind to the same module, tests and source snapshot. Each
gate receipt must bind to its declared commit, repository, target branch and
shadow policy. Bad and fixed attempts must reference the same PR and the
baseline target revision. Their sequence must follow baseline, bad, fixed.
All three commits must differ; corrected source bytes must restore the baseline
and differ from the bad version.

The baseline and fixed revisions must record all eleven plan-named tests passing.
The bad revision must record exactly the TEAM04 author-self-approval test failing
and the other ten passing. The harness also records a separate passing
`<module>` initialization entry: there are twelve functional records in total.
Bad QA must stop at its failed functional stage; successful QA must reach final
acceptance. Recorded process isolation, inspected/kernel limits, immutable
image/runner identity and confirmed container cleanup must agree.

These checks establish consistency of recorded evidence. They do not independently
observe the host or certify authentication, overall application security, merged
behavior, human approval, customer demand or production enforcement.

## Self-tests

    python3 -m unittest discover -s evidence_tools -p test_verify_evidence.py -v

The self-tests fabricate receipt data solely to exercise verifier behavior. They
cover altered artifacts and receipts, missing/broken/non-genesis chains, incorrect
source/commit bindings, wrong failed criteria, policy changes, unconfirmed cleanup
and unsafe paths/JSON. Test receipt bundles are temporary and are not demo evidence.
