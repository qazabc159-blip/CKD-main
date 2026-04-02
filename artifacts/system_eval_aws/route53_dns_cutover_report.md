# Route 53 DNS Cutover Report

- generated_at_utc: `2026-04-01T16:50:00Z`
- hosted_zone_id: `Z0418166FSA5EPCG6H84`
- domain_name: `renal-risk.com`

## Route 53 name servers

- `ns-908.awsdns-49.net`
- `ns-475.awsdns-59.com`
- `ns-1144.awsdns-15.org`
- `ns-1974.awsdns-54.co.uk`

## AWS DNS records prepared

- apex alias A -> CloudFront
- apex alias AAAA -> CloudFront
- ACM validation CNAME for `renal-risk.com`
- ACM validation CNAME for `www.renal-risk.com`

## Next manual step

Update the registrar nameservers at Cloudflare Registrar so that the domain delegates to the Route 53 hosted zone.
