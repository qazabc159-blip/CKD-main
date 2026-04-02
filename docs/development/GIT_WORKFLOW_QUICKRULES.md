# Git Workflow Quick Rules

This repository uses a lightweight solo-developer workflow designed to keep `main` stable without adding unnecessary process overhead.

## Short version

1. start from `main`
2. create a short-lived branch
3. make the change
4. run `python infra/run_ci_checks.py`
5. push the branch
6. open a PR into `main`
7. wait for CI to pass
8. squash merge
9. deploy manually only when needed

## Branch naming

Recommended prefixes:

- `feature/...`
- `fix/...`
- `docs/...`
- `infra/...`

Examples:

- `feature/www-redirect`
- `fix/github-ci-manifest`
- `docs/readme-refresh`

## Minimum checks before push

```bash
python infra/run_ci_checks.py
```

If the change affects deployment or release helpers, also consider:

```bash
python infra/run_cd_release.py --dry-run
```

## Merge policy

The current repository settings are intentionally simple:

- squash merge: enabled
- merge commit: disabled
- rebase merge: disabled
- delete branch on merge: enabled

## Current GitHub boundary

This repository currently relies on documented workflow conventions rather than platform-enforced branch protection.

That means:

- direct push to `main` is technically possible
- PR review is recommended but not enforced
- CI should be treated as a required habit, even if GitHub cannot currently enforce it on this private repository plan

## Practical rule

Even as a solo developer, use this mental checklist before touching `main`:

- Is this change isolated enough for its own branch?
- Did local CI pass?
- Did GitHub CI pass?
- Does this really need deployment now, or can it wait for the next grouped release?
