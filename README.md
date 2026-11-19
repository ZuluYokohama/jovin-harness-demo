# JoVin Harness demo

**Private staging draft: public demonstration execution and publication are pending.**

Zulu Operations is building a way to check selected code against agreed acceptance rules and
leave a record of what actually ran. This demo follows one small Python approval policy from a
deliberate mistake to a passing correction.

**Start here:** [demo pull request](__PUBLIC_DEMO_PR_URL__) ·
[session record](DEMO_SESSION.md) · [evidence](EVIDENCE.md)

The scenario is a fictional SaaS team deciding whether a change has enough valid approvals.
Reviewers must belong to the right tenant, be active, and approve the current revision. The
author cannot approve their own change. Eleven acceptance checks cover those rules, distinct
reviewers, changes requested, withdrawals, and specified malformed inputs.

In the internal trial, one deliberate edit removed the author exclusion. The self-approval
check failed. Restoring that exclusion passed the enrolled checks under the same policy and
test identities. The submitted revision and result were recorded for each attempt. This is an
observed internal test sequence, not a customer case study. [Evidence status](EVIDENCE.md)

| Step | What to inspect |
| --- | --- |
| Read the contract | [Acceptance criteria](__PUBLIC_PLAN_URL__) and [tests](__PUBLIC_TESTS_URL__) |
| See the mistake | [Failing revision](__PUBLIC_FAILED_SOURCE_URL__) and [failed check](__PUBLIC_FAILED_CHECK_URL__) |
| See the correction | [Corrected revision](__PUBLIC_PASSED_SOURCE_URL__) and [passing check](__PUBLIC_PASSED_CHECK_URL__) |
| Compare the evidence | [Candidate and policy identities](EVIDENCE.md) |

The current gate is deliberately small: one repository and up to three enrolled standalone
Python modules using the standard library. It checks the submitted head against an
operator-approved plan and tests using the harness sandbox. This demonstration runs in shadow
mode; it reports results and does not demonstrate required merge enforcement.

A pass covers the enrolled module and specified checks. It does not establish whole-application
correctness, production security, or the behavior of a future merged tree. This function also
does not authenticate actors or connect to a real SaaS service. The demo publishes synthetic
fixture code and selected evidence, not the private harness implementation or a complete
self-hosting package. Receipts are hash-chained records, not digital signatures.

If you have a small piece of Python that needs an explicit acceptance boundary, [open a trial
discussion](__PUBLIC_ISSUES_URL__). Describe the module, the rules that matter, and how you review
changes today. We can discuss whether a bounded trial would be useful and agree its scope.

Please keep private code, credentials, customer data, and internal logs out of public issues.
Use a small synthetic example to explain the rule you want to check.
