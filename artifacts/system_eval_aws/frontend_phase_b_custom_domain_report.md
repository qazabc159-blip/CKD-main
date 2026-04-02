# Frontend Phase B Custom-Domain Report

- generated_at_utc: `2026-04-01T16:48:48Z`
- domain_name: `renal-risk.com`
- certificate_arn: `arn:aws:acm:us-east-1:098890538524:certificate/e30dfc5f-8bca-44a8-866b-fa0d57322b87`
- stack_status: `UPDATE_COMPLETE`

## AWS State

- FrontendDistributionId: `E2ICQ6REQ1B5S`
- FrontendDistributionDomainName: `d1k3j20wqbcyvv.cloudfront.net`
- FrontendUrl: `https://renal-risk.com`

## Boundary

Phase B updated the AWS stack so that CloudFront is configured with the custom domain and ACM certificate.
Because DNS is hosted on Cloudflare rather than Route 53, the final traffic cutover still depends on adding or updating the public DNS record in Cloudflare.
