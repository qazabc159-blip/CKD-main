# Route 53 and Cloudflare Registrar Boundary Report

- generated_at_utc: `2026-04-01T16:55:00Z`
- domain_name: `renal-risk.com`
- route53_hosted_zone_id: `Z0418166FSA5EPCG6H84`
- cloudfront_distribution_id: `E2ICQ6REQ1B5S`
- cloudfront_distribution_domain: `d1k3j20wqbcyvv.cloudfront.net`

## Summary

This report records an important deployment boundary in the current frontend cutover.

The AWS side of the custom-domain path is now functionally ready:

- the frontend is hosted through `S3 + CloudFront`
- `renal-risk.com` is configured as a CloudFront alternate domain name
- the apex ACM certificate for `renal-risk.com` is `ISSUED`
- the supplementary ACM certificate for `www.renal-risk.com` is also `ISSUED`
- a public Route 53 hosted zone has been created
- Route 53 records for the apex alias and ACM validation CNAMEs have been prepared

## What was successfully completed

### AWS custom-domain configuration

- CloudFront now accepts the custom host:
  - `renal-risk.com`
- the stack output `FrontendUrl` now resolves to:
  - `https://renal-risk.com`

### Route 53 hosted zone preparation

The hosted zone `Z0418166FSA5EPCG6H84` contains:

- apex alias `A` -> CloudFront
- apex alias `AAAA` -> CloudFront
- ACM validation `CNAME` for `renal-risk.com`
- ACM validation `CNAME` for `www.renal-risk.com`

## Current operational reality

Although the Route 53 hosted zone has been prepared, it is **not** currently authoritative for the live domain.

The live domain remains:

- registered through `Cloudflare Registrar`
- DNS-hosted through `Cloudflare DNS`

The current production path is therefore:

- `Cloudflare Registrar`
- `Cloudflare DNS`
- `CloudFront`
- `S3 static site`

not:

- `Route 53`
- `CloudFront`
- `S3 static site`

## Why Route 53 is not authoritative yet

The blocker is not AWS configuration.

The blocker is registrar policy:

- the domain was registered through `Cloudflare Registrar`
- Cloudflare Registrar requires the domain to keep using Cloudflare nameservers
- because of that restriction, the Route 53 nameservers cannot currently be delegated as the authoritative nameservers for `renal-risk.com`

In other words:

- Route 53 is prepared
- Route 53 is not yet the live DNS authority

## Practical implication for architecture documentation

For any implementation-status figure, report, or thesis section describing the **current live system**, the DNS layer should be described as:

- `Cloudflare DNS`

rather than:

- `Route 53`

Route 53 can still appear in a target-architecture diagram, but it should be clearly labeled as:

- a prepared future DNS path
- or a target AWS-native DNS layer pending registrar-level cutover

## What would be required for a true Route 53 cutover

To make Route 53 authoritative in the future, one of the following would be needed:

1. transfer the domain away from Cloudflare Registrar after transfer restrictions permit it
2. move the domain to a registrar that allows custom nameserver delegation
3. then replace the current Cloudflare nameservers with the four Route 53 nameservers from the hosted zone

## Bottom line

The frontend is now genuinely AWS-hosted and reachable through the custom domain `renal-risk.com`, but the authoritative DNS layer remains on Cloudflare due to registrar-level restriction. This is an important implementation boundary and should be stated explicitly whenever the current architecture is described.
