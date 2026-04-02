# GitHub Git-Flow Design Report

- generated_at_utc: `2026-04-02T15:10:00Z`
- repository: `qazabc159-blip/CKD-main`

## Objective

Move the repository toward a more formal Git workflow while keeping the project practical for a small thesis-driven platform.

## Repository settings successfully applied

- repository visibility changed to `private`
- squash merge remains enabled
- merge commits were disabled
- rebase merges were disabled
- automatic branch deletion after merge was enabled

## Intended workflow

The intended working model is:

1. create a short-lived branch from `main`
2. push that branch
3. open a PR into `main`
4. let GitHub-hosted CI and the GitHub-to-CodeBuild bridge complete
5. merge through squash merge

## Practical repository assets added

- `CONTRIBUTING.md`
- `.github/pull_request_template.md`

These files formalize branch naming, PR expectations, and local verification habits even when repository policy cannot enforce them automatically.

## GitHub plan limitation discovered

Branch protection and repository rulesets could not be enabled for the current private repository under the present GitHub plan.

Observed API response:

> Upgrade to GitHub Pro or make this repository public to enable this feature.

This means the following protections are still unavailable at the platform-policy level:

- blocking direct pushes to `main`
- requiring pull-request approval before merge
- enforcing required status checks through branch protection

## Current interpretation

The repository is now more structured and better aligned with a formal branch-and-PR workflow, but enforcement remains partly procedural rather than policy-backed.

## Recommended next options

1. keep the repository private and follow the documented branch/PR workflow by convention
2. upgrade to GitHub Pro or a higher plan to enable branch protection on the private repository
3. make the repository public if policy enforcement is more important than privacy
