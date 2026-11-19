# Demo session: baseline, failed review, correction

This is the written record of the controller session on **19 November 2026**. It links the
actual baseline, failed candidate, and corrected candidate to their captured results. It is not
a video or a customer case study.

This session follows one synthetic approval-policy module through a baseline, a deliberate
self-approval regression, and its correction. The controller runs in shadow mode. The operator-enrolled plan and
tests are held fixed across the candidate comparison.

| Session identity | Recorded value |
| --- | --- |
| Captured at (UTC) | `2026-11-19, 20:29:35.781–20:31:25.168 UTC` |
| Repository / PR | [Public demonstration](https://github.com/ZuluYokohama/jovin-harness-demo/pull/1) |
| Enrolled module | `sample/approval_policy.py` |
| Policy SHA-256 | `696da341eddcb63a0e5412c49502f03266a1f3c9ae9d35f5a7088deba76d12c7` |
| Tests SHA-256 | `f79db562576d3847c996b6de692e14f516b80491fbae5999738a25e9b130397a` |
| Harness package SHA-256 | `abdcc8c928525131ad55b86e2403fbe977dc0a8703ffc28f8ed6aa1c4934fecf` |
| Runner SHA-256 | `dae6416db04daabbec29ee352a7e069aabf5c40b821bbcf11abffc06c9e202cc` |
| Image identity | `sha256:183fe5eb96949827f42d491bc1b3d1560933cae9ec71cbf3c27e6d50517f0ce8` |

## 1. Check the baseline

**20:29:35.781 UTC · exit status 0.**

The target branch contains the correct approval policy at
[the baseline commit](https://github.com/ZuluYokohama/jovin-harness-demo/blob/63804cb8a9477b9ea0245bdf5f027ff88b8d0ee1/sample/approval_policy.py). The controller independently checks that
revision against the enrolled acceptance plan.

The following command ran on the configured controller. Its private enrollment-directory
argument is redacted; this is a session record, not a complete installation recipe:

```text
jovin-harness gate --directory <private-enrollment-directory> baseline
```

Condensed captured CLI output:

```json
{
  "passed": true,
  "revision": "63804cb8a9477b9ea0245bdf5f027ff88b8d0ee1",
  "receipt_id": "20261119T202935Z-3c01cd06b944",
  "receipt_sha256": "6f36fbad0d46e16a44641523c8607cd73ed5cd38d92576f5beca1be40295b104"
}
```

Named acceptance criteria: **11 passed,
0 failed, 0 other** out of eleven.

[Baseline receipt](evidence/receipts/20261119T202935Z-3c01cd06b944.json) ·
[Criterion outcomes](evidence/receipts/20261119T202935Z-f985130e8a12.json)

## 2. Introduce the self-approval mistake

**20:29:49.146 UTC · exit status 1.**

At [the deliberate regression commit](https://github.com/ZuluYokohama/jovin-harness-demo/blob/0e563002dad428b43379b6d292ac0f3c6cb241d7/sample/approval_policy.py), one edit removes the
author exclusion:

```diff
-                    and actor_id != change["author_id"])
+                    and True)
```

The self-approval test supplies an administrator author and one other reviewer for a quorum of
two. The required result is a rejection with only one eligible approval. The changed function
instead counts the author.

Controller command against this exact PR head:

```text
jovin-harness gate --directory <private-enrollment-directory> run --pr 1
```

Condensed captured CLI output:

```json
{
  "mode": "shadow",
  "policy_sha256": "696da341eddcb63a0e5412c49502f03266a1f3c9ae9d35f5a7088deba76d12c7",
  "results": [
    {
      "number": 1,
      "passed": false,
      "mode": "shadow",
      "receipt_id": "20261119T202949Z-35dcf27e0b91",
      "receipt_sha256": "010f4067f5b03dca927e8f831845dac55d83f432e82ec48952054ca3a0543598",
      "check_id": 135861077173,
      "published": true
    }
  ],
  "passed": false
}
```

Named acceptance criteria: **10 passed,
1 failed, 0 other** out of eleven.
The captured self-approval outcome is **failed**.

[Failed check](https://github.com/ZuluYokohama/jovin-harness-demo/runs/135861077173) ·
[Controller receipt](evidence/receipts/20261119T202949Z-35dcf27e0b91.json) ·
[Criterion outcomes](evidence/receipts/20261119T202946Z-1ea20aab0f89.json)

The failure belongs to this candidate and these tests. It is not an inference from the source
diff alone.

## 3. Restore the rule and check the correction

**20:31:25.168 UTC · exit status 0.**

[The corrected commit](https://github.com/ZuluYokohama/jovin-harness-demo/blob/346c47fd251834b8eb1bee10a4d5aec370e5f069/sample/approval_policy.py) restores the author exclusion. The plan,
tests, and policy identity remain the same for this comparison.

```text
jovin-harness gate --directory <private-enrollment-directory> run --pr 1
```

Condensed captured CLI output:

```json
{
  "mode": "shadow",
  "policy_sha256": "696da341eddcb63a0e5412c49502f03266a1f3c9ae9d35f5a7088deba76d12c7",
  "results": [
    {
      "number": 1,
      "passed": true,
      "mode": "shadow",
      "receipt_id": "20261119T203125Z-d54febe2b1ef",
      "receipt_sha256": "dbc32477f13f8350d69d88d54c7965bc8208f3957aac20694b6b4d5ff4f05e7c",
      "check_id": 135862042735,
      "published": true
    }
  ],
  "passed": true
}
```

Named acceptance criteria: **11 passed,
0 failed, 0 other** out of eleven.
The captured self-approval outcome is **passed**.

[Passing check](https://github.com/ZuluYokohama/jovin-harness-demo/runs/135862042735) ·
[Controller receipt](evidence/receipts/20261119T203125Z-d54febe2b1ef.json) ·
[Criterion outcomes](evidence/receipts/20261119T203122Z-a962e4f81f6e.json)

## Reading the record

The criterion counts above come from the eleven named tests mapped by the acceptance plan.
They exclude the separate module-load event. The JSON excerpts preserve captured CLI fields;
criterion counts and links are derived from the corresponding receipt evidence, not invented
fields in the CLI output. See [the evidence table](EVIDENCE.md) for revision and receipt hashes, the complete published receipt chain, its manifest, and the
standard-library offline verifier. That verifier checks consistency of the supplied data; it
does not authenticate the publisher or prove the private execution environment.

These are scoped observations for one supplied module. Shadow checks report results; this
session does not demonstrate required merge enforcement. The separate
[acceptance-readiness check](https://github.com/ZuluYokohama/jovin-harness-demo/runs/135862114725) intentionally remains unsuccessful
because enforcement is inactive. The demonstrated result is the `jovin/shadow/696da341eddcb63a`
check, not permission to merge. A pass does not verify the entire
SaaS workflow, other repository files, authentication, deployment, or a future merged tree.
The fixture and selected evidence are public source material; the private controller is not
included as a complete reproduction package. The synthetic code is provided under the accompanying source-available license.

For a short presentation of this recorded sequence, use the separate
[walkthrough script](WALKTHROUGH_SCRIPT.md). A walkthrough or replay must not be described as a
new execution.
