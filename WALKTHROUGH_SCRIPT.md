# Demo session: a failed approval check, then a fix

This is a recording script for an approximately 90-second walkthrough. It is not a recording
or a claim that a live presentation has already happened. The scenario is synthetic and the
checks run in shadow mode.

| Time | Show | Narration |
| --- | --- | --- |
| 0:00–0:15 | The public demo README, then the approval rule in the plan. | “This is a small approval policy for a simulated team. Two eligible reviewers must approve the current revision. The author cannot count toward that quorum.” |
| 0:15–0:30 | The one-line regression diff and its exact commit. | “This deliberate edit removes the author exclusion. A normal pair of reviewers can still work, but an author and one reviewer can now authorize the author's own change.” |
| 0:30–0:50 | The failed check and the self-approval test result. | “The controller checked this revision against the enrolled tests. The self-approval case failed. The report identifies the checked source and the receipt for this attempt.” |
| 0:50–1:10 | The correction diff, then the passing check. | “Restoring the exclusion passes the enrolled checks. The acceptance policy and tests stayed the same; the candidate changed.” |
| 1:10–1:25 | The evidence table with both revisions and the shared policy. | “These are two scoped results for one module. Shadow mode reports the outcome. This session does not demonstrate a production deployment or merge enforcement.” |
| 1:25–1:30 | The public repository's issue link. | “If your team has a similarly bounded rule to check, the repository has a place to discuss a trial.” |

The viewer should be able to open the [pull request](https://github.com/ZuluYokohama/jovin-harness-demo/pull/1), the
[failed check](https://github.com/ZuluYokohama/jovin-harness-demo/runs/135861077173), and the [passing check](https://github.com/ZuluYokohama/jovin-harness-demo/runs/135862042735)
from the README. Use the completed historical checks when presenting the recorded sequence;
do not describe a replay as a new execution.

Before recording, confirm that both public checks belong to the displayed revisions and the
same policy and test identities. Keep acceptance-readiness checks distinct from shadow results:
a passing shadow observation is not permission to merge. Record only the synthetic public
repository and approved evidence pages. Do not capture credentials, private repository pages,
operator paths, other projects, or personal notifications.

If the public run differs from this script, update the script to the observation. If a check
has not finished, show that state rather than substituting an expected outcome.
