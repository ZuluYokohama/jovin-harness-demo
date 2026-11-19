# Demo evidence

**Private staging draft: public demonstration execution and publication are pending.**

The internal rehearsal recorded a rejected self-approval regression followed by a passing
correction under the same policy and test identities. A later report-formatting revision was
enrolled separately. The comparison below must use one policy for both public attempts.

Public execution links and identities are pending in this local draft. The internal record is
not a substitute for visitor-accessible evidence. No public run is claimed by this draft.

| Evidence | Deliberate regression | Corrected candidate |
| --- | --- | --- |
| Git commit | `__PUBLIC_FAILED_COMMIT__` | `__PUBLIC_PASSED_COMMIT__` |
| Source SHA-256 | `__PUBLIC_FAILED_SOURCE_SHA256__` | `__PUBLIC_PASSED_SOURCE_SHA256__` |
| Policy SHA-256 | `__PUBLIC_SHARED_POLICY_SHA256__` | `__PUBLIC_SHARED_POLICY_SHA256__` |
| Tests SHA-256 | `__PUBLIC_SHARED_TESTS_SHA256__` | `__PUBLIC_SHARED_TESTS_SHA256__` |
| Check | [Inspect failed attempt](__PUBLIC_FAILED_CHECK_URL__) | [Inspect passing attempt](__PUBLIC_PASSED_CHECK_URL__) |
| Controller receipt | `__PUBLIC_FAILED_RECEIPT_ID__` | `__PUBLIC_PASSED_RECEIPT_ID__` |
| Receipt SHA-256 | `__PUBLIC_FAILED_RECEIPT_SHA256__` | `__PUBLIC_PASSED_RECEIPT_SHA256__` |

The published evidence should also identify the enrolled package, runner, and image for these
attempts. These identities bind the reported checks to particular artifacts; they do not attest
every property of the operator's host or establish that a receipt was digitally signed.

The scope is one supplied module, eleven named acceptance checks, and one deliberate GitHub
regression/correction sequence in shadow mode. A passing result does not cover other files,
authentication, database behavior, concurrency, deployment, a prospective merged tree, or
customer outcomes. The candidate and acceptance fixture were prepared in the same development
workflow; separate sandbox execution is not independent human approval of the policy.

This repository exposes the synthetic fixture and selected result evidence. The private
harness implementation is not included, so this demo is not a complete public reproduction
package for the controller and sandbox.
