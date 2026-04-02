# AWS-Native Frontend Hosting Report

## Purpose

This work item added an AWS-native static hosting path for the CKD platform frontend. The goal was to reduce the mismatch between the target architecture and the implementation status by replacing the earlier Cloudflare-only hosting story with a concrete AWS hosting option based on:

- S3
- CloudFront
- optional Route 53 alias records

## What Was Implemented

### 1. Frontend hosting resources in the SAM template

The shared SAM template now supports an optional frontend-hosting branch through these parameters:

- `EnableFrontendHosting`
- `FrontendBucketName`
- `FrontendPriceClass`
- `FrontendDomainName`
- `FrontendCertificateArn`
- `FrontendHostedZoneId`

When enabled, the template provisions:

- a private S3 bucket for static frontend assets
- a CloudFront distribution
- an origin access control (OAC) between CloudFront and S3
- a CloudFront Function that rewrites directory-style URLs to `index.html`
- cache policies for:
  - static assets
  - HTML and runtime configuration files
- optional Route 53 alias records for a custom frontend domain

### 2. Static-site deployment helper

A frontend deployment helper was added:

- `infra/deploy_frontend_static_site.py`

This script:

- uploads the static site from `web/` to the frontend S3 bucket
- applies cache-control headers
- supports CloudFormation stack-output lookup for:
  - `FrontendBucketName`
  - `FrontendDistributionId`
- can invalidate the CloudFront distribution
- supports dry-run mode and manifest output

### 3. Frontend source normalization

The preferred AWS-native deployment source is now the repo-local static site at:

- `web/`

The helper script intentionally excludes non-site files such as:

- `README.md`
- `CKD_UI`

so that the S3 deployment contains only frontend assets required for hosting.

### 4. Documentation updates

The following documentation was updated:

- `infra/README.md`
- `infra/lambda_inference/README.md`
- `infra/aws_target_architecture.md`
- `web/README.md`

These updates clarify:

- the intended AWS-native hosting path
- the custom-domain prerequisites
- the relationship between the frontend static site and the inference API
- how CloudFront invalidation fits into the deployment flow

## Verification

### Infrastructure validation

The updated SAM template passed:

- `sam validate --template-file infra/template.yaml`
- `sam validate --template-file infra/template.yaml --lint`

This confirms that the frontend-hosting resources are valid at the infrastructure-definition level.

### Frontend deployment dry run

`infra/deploy_frontend_static_site.py` was verified through dry-run execution. The dry run confirmed:

- 8 deployable frontend assets detected from `web/`
- correct path structure for:
  - `index.html`
  - `landing/*`
  - `app/*`
- no-cache headers for:
  - HTML files
  - `app/config.js`
- cacheable headers for static CSS and JavaScript assets
- optional CloudFront invalidation request generation

The dry-run manifest was written to:

- `artifacts/system_eval_aws/frontend_static_site_dry_run_manifest.json`

## Practical Thesis Value

This work item improves the thesis platform contribution in several ways.

1. It gives the architecture a real AWS-native frontend-hosting path rather than leaving that layer purely conceptual.
2. It reduces the implementation gap between the frontend and the already verified AWS inference slice.
3. It makes the platform more internally coherent by keeping:
   - static frontend hosting
   - API Gateway
   - Lambda inference
   - S3-backed artifacts
   within the AWS deployment story.
4. It adds a more realistic migration path from a public prototype into a fuller AWS-hosted stack.

## Current Boundary

This work item is complete at the infrastructure-definition and deployment-helper level, but not yet field-verified through a live custom-domain rollout.

The current boundary is therefore:

- AWS-native hosting resources: implemented
- static-site upload flow: implemented
- custom-domain Route 53 integration: supported by template
- live ACM certificate, Route 53 alias, and production cutover: still pending actual deployment inputs

CloudFront custom-domain mode specifically still depends on:

- a valid ACM certificate in `us-east-1`
- a Route 53 hosted zone ID
- a chosen frontend domain name

## Most Relevant Files

- `infra/template.yaml`
- `infra/deploy_frontend_static_site.py`
- `infra/README.md`
- `infra/aws_target_architecture.md`
- `web/README.md`
- `artifacts/system_eval_aws/frontend_static_site_dry_run_manifest.json`
