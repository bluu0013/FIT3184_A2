# Working agreement

- **Everyone commits their own work.** The marking panel looks at commit balance. Do not hand your
  changes to a teammate to commit.
- **Branches:** `feature/<short-name>` off `main`. Open a pull request, get one review from a teammate, merge.
- **Small PRs** (under about 300 changed lines) so reviews happen the same day.
- **Cross-platform review.** Each PR is reviewed by someone from a different platform: AWS changes
  (A or C) get a review from B, GCP and UI changes (B) get a review from A or C, and A and C review
  each other's shared-layer changes. Everyone ends up seeing the whole system for the demo Q&A.
- **Cross-training in week 2.** Each person deploys another member's component once from the README.
  Anyone should be able to run any cloud, because the team must cover for a missing member.
- **Commit messages:** imperative and specific, e.g. `Add checksum check to upload_init`.
- **Contracts first.** If an API shape or the DynamoDB record changes, update `docs/api-contract.md`
  or `docs/data-model.md` in the same PR and tag both teammates.
- **No secrets in git.** No keys, tokens, passwords or account IDs in code, config files or commit
  history. Use stack parameters, SSM or Secret Manager. Cognito pool and client IDs are not secrets.
- **Tests:** add a unit test for any new pure logic. Run `python -m unittest discover -s tests` before pushing.
- **AI tools:** allowed, but note the tool and what it helped with in the PR description. You must be
  able to explain every line you merge. The demo Q&A checks this.
- **Cost:** shut down or scale to zero anything you are not using. Delete everything after assessment.
