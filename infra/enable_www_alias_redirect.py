from __future__ import annotations

import argparse
import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import boto3


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts" / "system_eval_aws"
DEFAULT_REPORT_PATH = ARTIFACTS_DIR / "frontend_www_alias_redirect_report.md"
DEFAULT_STATE_PATH = ARTIFACTS_DIR / "frontend_www_alias_redirect_state.json"
DEFAULT_REGION = "us-east-1"


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def to_jsonable(value):
    if isinstance(value, datetime):
        return value.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    if isinstance(value, dict):
        return {k: to_jsonable(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_jsonable(v) for v in value]
    return value


def build_redirect_function_code(primary_domain: str, www_domain: str) -> str:
    return f"""function toQueryString(querystring) {{
  var keys = Object.keys(querystring);
  if (keys.length === 0) {{
    return '';
  }}

  var parts = [];
  for (var i = 0; i < keys.length; i++) {{
    var key = keys[i];
    var entry = querystring[key];

    if (entry.multiValue && entry.multiValue.length > 0) {{
      for (var j = 0; j < entry.multiValue.length; j++) {{
        var mv = entry.multiValue[j];
        if (mv.value && mv.value.length > 0) {{
          parts.push(encodeURIComponent(key) + '=' + encodeURIComponent(mv.value));
        }} else {{
          parts.push(encodeURIComponent(key));
        }}
      }}
      continue;
    }}

    if (entry.value && entry.value.length > 0) {{
      parts.push(encodeURIComponent(key) + '=' + encodeURIComponent(entry.value));
    }} else {{
      parts.push(encodeURIComponent(key));
    }}
  }}

  return parts.length > 0 ? '?' + parts.join('&') : '';
}}

function handler(event) {{
  var request = event.request;
  var uri = request.uri;
  var host = '';

  if (request.headers.host && request.headers.host.value) {{
    host = request.headers.host.value.toLowerCase();
  }}

  if (host === '{www_domain.lower()}') {{
    return {{
      statusCode: 301,
      statusDescription: 'Moved Permanently',
      headers: {{
        location: {{
          value: 'https://{primary_domain}' + uri + toQueryString(request.querystring)
        }},
        'cache-control': {{
          value: 'public, max-age=300'
        }}
      }}
    }};
  }}

  if (uri.endsWith('/')) {{
    request.uri = uri + 'index.html';
    return request;
  }}

  if (!uri.includes('.')) {{
    request.uri = uri + '/index.html';
  }}

  return request;
}}"""


def update_cloudfront_function(cloudfront, function_name: str, primary_domain: str, www_domain: str) -> dict:
    dev = cloudfront.describe_function(Name=function_name, Stage="DEVELOPMENT")
    dev_etag = dev["ETag"]
    config = dev["FunctionSummary"]["FunctionConfig"]
    code = build_redirect_function_code(primary_domain, www_domain).encode("utf-8")

    cloudfront.update_function(
        Name=function_name,
        IfMatch=dev_etag,
        FunctionConfig={
            "Comment": config["Comment"],
            "Runtime": config["Runtime"],
        },
        FunctionCode=code,
    )

    latest_dev = cloudfront.describe_function(Name=function_name, Stage="DEVELOPMENT")
    publish_etag = latest_dev["ETag"]
    published = cloudfront.publish_function(Name=function_name, IfMatch=publish_etag)
    return {
        "name": function_name,
        "stage": published["FunctionSummary"]["FunctionMetadata"]["Stage"],
        "arn": published["FunctionSummary"]["FunctionMetadata"]["FunctionARN"],
        "last_modified_time": published["FunctionSummary"]["FunctionMetadata"]["LastModifiedTime"],
    }


def update_distribution(cloudfront, distribution_id: str, certificate_arn: str, primary_domain: str, www_domain: str) -> dict:
    current = cloudfront.get_distribution_config(Id=distribution_id)
    etag = current["ETag"]
    config = deepcopy(current["DistributionConfig"])

    aliases = [primary_domain, www_domain]
    current_aliases = config.get("Aliases", {}).get("Items", [])
    current_cert_arn = config.get("ViewerCertificate", {}).get("ACMCertificateArn", "")

    if current_aliases == aliases and current_cert_arn == certificate_arn:
        dist = cloudfront.get_distribution(Id=distribution_id)["Distribution"]
        return {
            "id": dist["Id"],
            "status": dist["Status"],
            "domain_name": dist["DomainName"],
            "aliases": dist["DistributionConfig"]["Aliases"]["Items"],
            "last_modified_time": dist["LastModifiedTime"],
            "changed": False,
        }

    config["Aliases"] = {"Quantity": len(aliases), "Items": aliases}
    config["ViewerCertificate"] = {
        "CloudFrontDefaultCertificate": False,
        "ACMCertificateArn": certificate_arn,
        "SSLSupportMethod": "sni-only",
        "MinimumProtocolVersion": "TLSv1.2_2021",
        "Certificate": certificate_arn,
        "CertificateSource": "acm",
    }

    response = cloudfront.update_distribution(
        Id=distribution_id,
        IfMatch=etag,
        DistributionConfig=config,
    )
    dist = response["Distribution"]
    return {
        "id": dist["Id"],
        "status": dist["Status"],
        "domain_name": dist["DomainName"],
        "aliases": dist["DistributionConfig"]["Aliases"]["Items"],
        "last_modified_time": dist["LastModifiedTime"],
        "changed": True,
    }


def wait_for_distribution(cloudfront, distribution_id: str) -> dict:
    waiter = cloudfront.get_waiter("distribution_deployed")
    waiter.wait(Id=distribution_id, WaiterConfig={"Delay": 15, "MaxAttempts": 40})
    final = cloudfront.get_distribution(Id=distribution_id)["Distribution"]
    return {
        "id": final["Id"],
        "status": final["Status"],
        "domain_name": final["DomainName"],
        "aliases": final["DistributionConfig"]["Aliases"]["Items"],
        "last_modified_time": final["LastModifiedTime"],
    }


def write_report(path: Path, state: dict) -> None:
    lines = [
        "# Frontend WWW Alias and Redirect Report",
        "",
        f"- generated_at_utc: `{state['generated_at_utc']}`",
        f"- distribution_id: `{state['distribution_id']}`",
        f"- primary_domain: `{state['primary_domain']}`",
        f"- www_domain: `{state['www_domain']}`",
        f"- certificate_arn: `{state['certificate_arn']}`",
        "",
        "## Result",
        "",
        "The AWS frontend distribution has been updated so that both the apex and `www` hostnames are accepted by CloudFront, while `www` requests are redirected to the apex domain at the CloudFront Function layer.",
        "",
        "## AWS changes applied",
        "",
        f"- CloudFront Function updated and republished: `{state['function']['name']}`",
        f"- CloudFront aliases now include: `{', '.join(state['distribution']['aliases'])}`",
        f"- CloudFront viewer certificate switched to the multi-domain ACM certificate: `{state['certificate_arn']}`",
        "",
        "## Redirect behavior",
        "",
        f"- requests for `https://{state['www_domain']}` now receive a redirect to `https://{state['primary_domain']}`",
        "- path and query string are preserved",
        "",
        "## Remaining DNS step",
        "",
        "Because DNS authority still sits on Cloudflare, the public `www` hostname still depends on a Cloudflare DNS record pointing `www` to the CloudFront distribution domain.",
        "",
        f"- required DNS record: `CNAME www -> {state['distribution']['domain_name']}`",
        "- recommended proxy mode: `DNS only` for the initial cutover",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Enable a www alias on the frontend CloudFront distribution and redirect it to the apex domain.")
    parser.add_argument("--distribution-id", required=True)
    parser.add_argument("--function-name", required=True)
    parser.add_argument("--primary-domain", required=True)
    parser.add_argument("--www-domain", required=True)
    parser.add_argument("--certificate-arn", required=True)
    parser.add_argument("--state-out", default=str(DEFAULT_STATE_PATH))
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_PATH))
    args = parser.parse_args()

    cloudfront = boto3.client("cloudfront")

    function_state = update_cloudfront_function(
        cloudfront=cloudfront,
        function_name=args.function_name,
        primary_domain=args.primary_domain,
        www_domain=args.www_domain,
    )
    distribution_state = update_distribution(
        cloudfront=cloudfront,
        distribution_id=args.distribution_id,
        certificate_arn=args.certificate_arn,
        primary_domain=args.primary_domain,
        www_domain=args.www_domain,
    )
    final_distribution = wait_for_distribution(cloudfront, args.distribution_id)

    state = {
        "generated_at_utc": utc_now_iso(),
        "distribution_id": args.distribution_id,
        "primary_domain": args.primary_domain,
        "www_domain": args.www_domain,
        "certificate_arn": args.certificate_arn,
        "function": function_state,
        "distribution_update_response": distribution_state,
        "distribution": final_distribution,
    }

    state_path = Path(args.state_out).resolve()
    report_path = Path(args.report_out).resolve()
    state_path.parent.mkdir(parents=True, exist_ok=True)
    jsonable_state = to_jsonable(state)
    state_path.write_text(json.dumps(jsonable_state, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(report_path, jsonable_state)
    print(json.dumps(jsonable_state, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
