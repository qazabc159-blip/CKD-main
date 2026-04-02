# GitHub Publish Safety Audit

- generated_at: 2026-04-02
- scope: `CKD-main` local repository pre-publish audit

## Key findings

- No obvious credential files (`.env`, `.pem`, `.key`, `.p12`, `.pfx`, `credentials`) were found under the repository root.
- No obvious embedded cloud secret material was found in a keyword scan; matches were dominated by documentation, workflow descriptions, and data-audit terminology.
- The repository was not previously initialized as a Git repository.
- Local-only Claude configuration exists under `.claude/settings.local.json` and should not be published.
- AWS SAM local build output exists under `.aws-sam/` and should not be published.
- A generated CI source bundle exists at `artifacts/system_eval_aws/ckd-main-ci-source.zip` and should not be published.
- Local SageMaker smoke-training output exists under `artifacts/system_eval_aws/sagemaker_local_model/` and should not be published.

## Safety actions applied

- Added `.claude/` to `.gitignore`
- Added `.aws-sam/` to `.gitignore`
- Added `artifacts/system_eval_aws/ckd-main-ci-source.zip` to `.gitignore`
- Added `artifacts/system_eval_aws/sagemaker_local_model/` to `.gitignore`

## Remaining decision boundary

The local repository can now be initialized and committed safely.

Publishing to GitHub still requires a remote repository decision:

- safest: create a new **private** GitHub repository for the current `CKD-main` state
- not recommended without confirmation: push into the existing public `qazabc159-blip/CKD` repository, which is out of sync with the current local platform state
