# Demo session: baseline, failed review, correction

**Private staging draft: public demonstration execution and publication are pending.**

**Local draft — fresh public capture pending.** This page becomes the completed session record
when its placeholders are replaced with captured outputs and verified public links. It is not
a video. No completed public run is claimed while this notice remains.

This session follows one synthetic approval-policy module through a baseline, a deliberate
self-approval regression, and its correction. The controller runs in shadow mode. The plan and
tests are held fixed across the candidate comparison.

| Session identity | Recorded value |
| --- | --- |
| Captured at (UTC) | `__PUBLIC_SESSION_CAPTURED_AT__` |
| Repository / PR | [Public demonstration](__PUBLIC_DEMO_PR_URL__) |
| Enrolled module | `__PUBLIC_ENROLLED_MODULE_PATH__` |
| Policy SHA-256 | `__PUBLIC_SHARED_POLICY_SHA256__` |
| Tests SHA-256 | `__PUBLIC_SHARED_TESTS_SHA256__` |
| Harness package SHA-256 | `__PUBLIC_PACKAGE_SHA256__` |
| Runner SHA-256 | `__PUBLIC_RUNNER_SHA256__` |
| Image identity | `__PUBLIC_IMAGE_ID__` |

## 1. Check the baseline

The target branch contains the correct approval policy at
[the baseline commit](__PUBLIC_BASELINE_SOURCE_URL__). The controller independently checks that
revision against the enrolled acceptance plan.

Controller command, with its private enrollment-directory argument redacted:

```text
jovin-harness gate --directory <private-enrollment-directory> baseline
```

Condensed captured CLI output — retain only the original keys shown in the capture:

```json
__CAPTURED_BASELINE_JSON__
```

Named acceptance criteria: **__PUBLIC_BASELINE_PASSED_COUNT__ passed,
__PUBLIC_BASELINE_FAILED_COUNT__ failed, __PUBLIC_BASELINE_OTHER_COUNT__ other** out of eleven.

[Baseline receipt](__PUBLIC_BASELINE_RECEIPT_URL__) ·
[Criterion outcomes](__PUBLIC_BASELINE_OUTCOMES_URL__)

## 2. Introduce the self-approval mistake

At [the deliberate regression commit](__PUBLIC_FAILED_SOURCE_URL__), one edit removes the
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
jovin-harness gate --directory <private-enrollment-directory> run --pr __PUBLIC_PR_NUMBER__ --retry
```

Condensed captured CLI output:

```json
__CAPTURED_FAILED_RUN_JSON__
```

Named acceptance criteria: **__PUBLIC_FAILED_PASSED_COUNT__ passed,
__PUBLIC_FAILED_FAILED_COUNT__ failed, __PUBLIC_FAILED_OTHER_COUNT__ other** out of eleven.
The captured self-approval outcome is **__PUBLIC_TEAM04_FAILED_OUTCOME__**.

[Failed check](__PUBLIC_FAILED_CHECK_URL__) ·
[Controller receipt](__PUBLIC_FAILED_RECEIPT_URL__) ·
[Criterion outcomes](__PUBLIC_FAILED_OUTCOMES_URL__)

The failure belongs to this candidate and these tests. It is not an inference from the source
diff alone.

## 3. Restore the rule and check the correction

[The corrected commit](__PUBLIC_PASSED_SOURCE_URL__) restores the author exclusion. The plan,
tests, and policy identity remain the same for this comparison.

```text
jovin-harness gate --directory <private-enrollment-directory> run --pr __PUBLIC_PR_NUMBER__ --retry
```

Condensed captured CLI output:

```json
__CAPTURED_PASSED_RUN_JSON__
```

Named acceptance criteria: **__PUBLIC_PASSED_PASSED_COUNT__ passed,
__PUBLIC_PASSED_FAILED_COUNT__ failed, __PUBLIC_PASSED_OTHER_COUNT__ other** out of eleven.
The captured self-approval outcome is **__PUBLIC_TEAM04_PASSED_OUTCOME__**.

[Passing check](__PUBLIC_PASSED_CHECK_URL__) ·
[Controller receipt](__PUBLIC_PASSED_RECEIPT_URL__) ·
[Criterion outcomes](__PUBLIC_PASSED_OUTCOMES_URL__)

## Reading the record

The criterion counts above come from the eleven named tests mapped by the acceptance plan.
They exclude the separate module-load event. The JSON excerpts preserve captured CLI fields;
criterion counts and links are derived from the corresponding receipt evidence, not invented
fields in the CLI output. See [the evidence table](EVIDENCE.md) for revision and receipt hashes.

These are scoped observations for one supplied module. Shadow checks report results; this
session does not demonstrate required merge enforcement. A pass does not verify the entire
SaaS workflow, other repository files, authentication, deployment, or a future merged tree.
The fixture and selected evidence are public source material; the private controller is not
included as a complete reproduction package. The accompanying license governs use of the
synthetic code; this page makes no OSI open-source claim.
