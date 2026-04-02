# Contributing

This repository follows a lightweight but structured Git workflow designed for a thesis platform project.

For a shorter day-to-day version of this workflow, see:

- `docs/development/GIT_WORKFLOW_QUICKRULES.md`

## Branching model

- `main` is the stable integration branch.
- New work should start from a short-lived branch off `main`.
- Recommended branch prefixes:
  - `feature/...`
  - `fix/...`
  - `docs/...`
  - `infra/...`

Examples:

- `feature/www-redirect`
- `fix/github-ci-manifest`
- `docs/chapter-5-platform-update`

## Expected development flow

1. update local `main`
2. create a short-lived working branch
3. implement the change
4. run the relevant local checks before pushing
5. push the branch
6. open a pull request into `main`
7. wait for GitHub CI and the GitHub-to-CodeBuild bridge to complete
8. merge with **squash merge**

## Local verification

Before opening a PR, run the repository-native CI checks when relevant:

```bash
python infra/run_ci_checks.py
```

When the change touches deployment helpers or release wiring, also consider:

```bash
python infra/run_cd_release.py --dry-run
```

## Merge policy

Repository settings are intentionally aligned to a simple merge strategy:

- squash merge: enabled
- merge commit: disabled
- rebase merge: disabled
- delete branch on merge: enabled

This keeps history compact and easier to review later in the thesis and platform reports.

## Current GitHub plan boundary

The intended workflow is:

- work on branches
- open a PR to `main`
- let CI pass
- then squash merge

However, the current GitHub plan does **not** allow branch protection or rulesets for this private repository.

That means the following are currently **workflow conventions rather than platform-enforced rules**:

- blocking direct pushes to `main`
- requiring PR approval before merge
- enforcing required status checks at the repository policy level

If the repository is later upgraded to GitHub Pro, Team, or made public, these protections should be enabled formally.
