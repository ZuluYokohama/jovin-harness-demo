# Demo evidence

The dedicated demonstration chain records a passing baseline, a failed self-approval regression,
and a passing correction on 19 November 2026. The two PR attempts use the same operator-enrolled
policy and tests. [Read the chronological session](DEMO_SESSION.md).

| Attempt | Commit | Named criteria | GitHub check | Controller receipt |
| --- | --- | --- | --- | --- |
| Baseline | [63804cb8a947](https://github.com/ZuluYokohama/jovin-harness-demo/commit/63804cb8a9477b9ea0245bdf5f027ff88b8d0ee1) | 11/11 passed | Baseline command; no PR check | [20261119T202935Z-3c01cd06b944](evidence/receipts/20261119T202935Z-3c01cd06b944.json) |
| Deliberate regression | [0e563002dad4](https://github.com/ZuluYokohama/jovin-harness-demo/commit/0e563002dad428b43379b6d292ac0f3c6cb241d7) | 10/11 passed | [Inspect](https://github.com/ZuluYokohama/jovin-harness-demo/runs/135861077173) | [20261119T202949Z-35dcf27e0b91](evidence/receipts/20261119T202949Z-35dcf27e0b91.json) |
| Correction | [346c47fd2518](https://github.com/ZuluYokohama/jovin-harness-demo/commit/346c47fd251834b8eb1bee10a4d5aec370e5f069) | 11/11 passed | [Inspect](https://github.com/ZuluYokohama/jovin-harness-demo/runs/135862042735) | [20261119T203125Z-d54febe2b1ef](evidence/receipts/20261119T203125Z-d54febe2b1ef.json) |

The separately recorded module-load event passed in all three attempts; it is not one of the
eleven acceptance criteria. The failed criterion was TEAM04, which prohibits author self-approval.

| Shared artifact | Identity |
| --- | --- |
| Policy SHA-256 | `696da341eddcb63a0e5412c49502f03266a1f3c9ae9d35f5a7088deba76d12c7` |
| Tests SHA-256 | `f79db562576d3847c996b6de692e14f516b80491fbae5999738a25e9b130397a` |
| Harness package SHA-256 | `abdcc8c928525131ad55b86e2403fbe977dc0a8703ffc28f8ed6aa1c4934fecf` |
| Runner SHA-256 | `dae6416db04daabbec29ee352a7e069aabf5c40b821bbcf11abffc06c9e202cc` |
| Image | `sha256:183fe5eb96949827f42d491bc1b3d1560933cae9ec71cbf3c27e6d50517f0ce8` |

The baseline and corrected source share SHA-256
`76d2233e3c0531f88d30b8ce1f6e5aa7e564fce53a88f5608333cc1940fc7772`.
The deliberate regression has SHA-256
`251a1b07ec0084a5d04c8157bb5e3da83220e875dea833ad7acd6b6936827dc1`.
These identities bind the recorded checks to particular artifacts; they do not attest every
property of the operator's host.

## Inspect the records

[Complete dedicated receipt chain](evidence/receipts/index.jsonl) ·
[Artifact manifest](evidence-manifest.json) ·
[Standard-library offline verifier](evidence_tools/README.md)

The export contains 25 receipts, from its null predecessor through
`20261119T203125Z-d54febe2b1ef`. Its final receipt SHA-256 is
`dbc32477f13f8350d69d88d54c7965bc8208f3957aac20694b6b4d5ff4f05e7c`. The manifest identifies each file and the three candidate
snapshots. The receipt links above lead to the associated QA stages and functional outcomes.

The offline verifier checks consistency of the supplied hashes, chain, references, and recorded
outcomes. It reads data and does not execute the candidate or tests. A successful verification
does not authenticate the publisher, provide signatures, prove the execution environment or
GitHub acceptance, or establish that every event outside the exported chain was included.
Inspect the linked GitHub revisions and checks separately.

The scope is one supplied module, eleven named acceptance checks, and one deliberate regression
and correction in shadow mode. A pass does not cover other files, authentication, database
behavior, concurrency, deployment, a future merged tree, or customer outcomes. The candidate
and acceptance fixture were prepared in the same development workflow; separate sandbox
execution does not establish independent human approval of the policy.

The synthetic fixture and selected evidence are public source material under the accompanying
[license](LICENSE). The private harness implementation is not included, so this is not a complete
public reproduction package for the controller and sandbox.
