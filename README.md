# JoVin Harness demo

Zulu Operations is building a way to check selected code against explicit acceptance rules and
leave a record of what actually ran. This demo follows one small Python approval policy from a
deliberate mistake to a passing correction.

**Start here:** [demo pull request](https://github.com/ZuluYokohama/jovin-harness-demo/pull/1) ·
[session record](DEMO_SESSION.md) · [evidence](EVIDENCE.md)

The scenario is a fictional SaaS team deciding whether a change has enough valid approvals.
Reviewers must belong to the right tenant, be active, and approve the current revision. The
author cannot approve their own change. Eleven acceptance checks cover those rules, distinct
reviewers, changes requested, withdrawals, and specified malformed inputs.

In the recorded session, the correct baseline passed all eleven criteria. Removing the author
exclusion produced ten passes and one failure: the self-approval check. Restoring the rule passed
all eleven again, under the same policy and tests. Each attempt has a receipt and the two PR
revisions have GitHub check results. This is a synthetic demonstration, not a customer case
study. [Read the session](DEMO_SESSION.md) or [inspect the evidence](EVIDENCE.md).

| Step | What to inspect |
| --- | --- |
| Read the contract | [Acceptance criteria](https://github.com/ZuluYokohama/jovin-harness-demo/blob/63804cb8a9477b9ea0245bdf5f027ff88b8d0ee1/sample/plan.json) and [tests](https://github.com/ZuluYokohama/jovin-harness-demo/blob/63804cb8a9477b9ea0245bdf5f027ff88b8d0ee1/sample/tests.py) |
| See the mistake | [Failing revision](https://github.com/ZuluYokohama/jovin-harness-demo/blob/0e563002dad428b43379b6d292ac0f3c6cb241d7/sample/approval_policy.py) and [failed check](https://github.com/ZuluYokohama/jovin-harness-demo/runs/135861077173) |
| See the correction | [Corrected revision](https://github.com/ZuluYokohama/jovin-harness-demo/blob/346c47fd251834b8eb1bee10a4d5aec370e5f069/sample/approval_policy.py) and [passing check](https://github.com/ZuluYokohama/jovin-harness-demo/runs/135862042735) |
| Compare the evidence | [Candidate and policy identities](EVIDENCE.md) |

The current gate is deliberately small: one repository and up to three enrolled standalone
Python modules using the standard library. It checks the submitted head against an
operator-enrolled plan and tests using the harness sandbox. This demonstration runs in shadow
mode; it reports results and does not demonstrate required merge enforcement. A separate
acceptance-readiness check intentionally remains unsuccessful while enforcement is inactive;
the linked shadow checks show the demonstrated failure and pass.

A pass covers the enrolled module and specified checks. It does not establish whole-application
correctness, production security, or the behavior of a future merged tree. This function also
does not authenticate actors or connect to a real SaaS service. The demo publishes synthetic
fixture code and selected evidence, not the private harness implementation or a complete
self-hosting package. Receipts are hash-chained records, not digital signatures.

If you have a small piece of Python that needs an explicit acceptance boundary, [open a trial
discussion](https://github.com/ZuluYokohama/jovin-harness-demo/issues/new). Describe the module, the rules that matter, and how you review
changes today. We can discuss whether a bounded trial would be useful and agree its scope.

Please keep private code, credentials, customer data, and internal logs out of public issues.
Use a small synthetic example to explain the rule you want to check.

The synthetic code is source-available under the [PolyForm Noncommercial License 1.0.0](LICENSE).
For a commercial trial, we need to agree appropriate permission and scope separately. A free
trial invitation does not itself grant commercial-use rights.
