# Web UI

This folder contains the frontend prototype for the CKD risk prediction platform.

## Current Status
- static site ready for AWS-native hosting upload
- app runtime config points to the live AWS inference endpoint
- current version should still be treated as a prototype frontend rather than a finalized production UI

## Deployment

The preferred static-site source for AWS-native hosting is this folder.

Suggested deployment flow:

1. provision S3 + CloudFront (and optional Route 53) through `infra/template.yaml`
2. upload this folder through `infra/deploy_frontend_static_site.py`
3. invalidate the CloudFront distribution

## Future Tasks
- align form fields with finalized feature schema
- continue refining UX and operational copy
- evaluate whether the landing/app split should remain as-is or be consolidated

## Notes
The UI currently supports:
- public landing page
- research and clinical intake surfaces
- submission to the live prediction API
- display of risk score and serving metadata
