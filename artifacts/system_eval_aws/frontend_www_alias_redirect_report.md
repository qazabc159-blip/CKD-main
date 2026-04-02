# Frontend WWW Alias and Redirect Report

- generated_at_utc: `2026-04-02T13:04:05Z`
- distribution_id: `E2ICQ6REQ1B5S`
- primary_domain: `renal-risk.com`
- www_domain: `www.renal-risk.com`
- certificate_arn: `arn:aws:acm:us-east-1:098890538524:certificate/829a65ed-23d8-4835-bec4-e3d1a3e1bf9f`

## Result

The AWS frontend distribution has been updated so that both the apex and `www` hostnames are accepted by CloudFront, while `www` requests are redirected to the apex domain at the CloudFront Function layer.

## AWS changes applied

- CloudFront Function updated and republished: `ckd-inference-stack-ckd-frontend-rewrite`
- CloudFront aliases now include: `renal-risk.com, www.renal-risk.com`
- CloudFront viewer certificate switched to the multi-domain ACM certificate: `arn:aws:acm:us-east-1:098890538524:certificate/829a65ed-23d8-4835-bec4-e3d1a3e1bf9f`

## Redirect behavior

- requests for `https://www.renal-risk.com` now receive a redirect to `https://renal-risk.com`
- path and query string are preserved

## Remaining DNS step

Because DNS authority still sits on Cloudflare, the public `www` hostname still depends on a Cloudflare DNS record pointing `www` to the CloudFront distribution domain.

- required DNS record: `CNAME www -> d1k3j20wqbcyvv.cloudfront.net`
- recommended proxy mode: `DNS only` for the initial cutover
