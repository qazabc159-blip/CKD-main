# Frontend Phase A Live Deployment Report

- generated_at_utc: `2026-04-01T14:54:51Z`
- stack_name: `ckd-inference-stack`
- region: `ap-northeast-1`
- deploy_version: `ckd-frontend-phase-a-ckd-inference-stack-2026-04-01T14:51:00Z`

## Scope

This report records Phase A of the AWS-native frontend cutover:

- provision S3 + CloudFront frontend hosting on the existing AWS stack
- upload the static site from `web/`
- verify the CloudFront-served frontend before any Route 53 or custom-domain cutover

## Outputs

- FrontendBucketName: `ckd-inference-stack-ckdfrontendsitebucket-qab7ra6fn1ls`
- FrontendDistributionId: `E2ICQ6REQ1B5S`
- FrontendDistributionDomainName: `d1k3j20wqbcyvv.cloudfront.net`
- FrontendUrl: `https://d1k3j20wqbcyvv.cloudfront.net`

## Verification Summary

- root_ok: `True`
- landing_ok: `True`
- app_ok: `True`
- config_ok: `True`

## Boundary

Phase A confirms that the frontend can now run through the AWS-native S3 + CloudFront hosting path.
Route 53 / custom-domain cutover remains a separate Phase B step.
