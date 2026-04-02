from __future__ import annotations

import argparse
import json
from pathlib import Path

from deploy_frontend_phase_a import (
    DEFAULT_MERGED_TEMPLATE_PATH,
    DEFAULT_REGION,
    DEFAULT_REPORT_PATH,
    DEFAULT_STACK_NAME,
    describe_stack,
    extract_frontend_sections,
    load_processed_template,
    load_yaml_template,
    merge_frontend_into_processed,
    parameter_overrides_from_stack,
    run_cloudformation_deploy,
    stack_outputs,
    utc_now_iso,
    write_json,
)

import boto3


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INFRA_DIR = PROJECT_ROOT / "infra"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts" / "system_eval_aws"
DEFAULT_TEMPLATE_PATH = INFRA_DIR / "template.yaml"
DEFAULT_MERGED_TEMPLATE_B_PATH = ARTIFACTS_DIR / "frontend_phase_b_merged_template.json"
DEFAULT_PHASE_B_REPORT_PATH = ARTIFACTS_DIR / "frontend_phase_b_custom_domain_report.md"
DEFAULT_PHASE_B_STATE_PATH = ARTIFACTS_DIR / "frontend_phase_b_custom_domain_state.json"


def write_phase_b_report(report_path: Path, domain: str, cert_arn: str, outputs: dict[str, str], stack_status: str) -> None:
    lines = [
        "# Frontend Phase B Custom-Domain Report",
        "",
        f"- generated_at_utc: `{utc_now_iso()}`",
        f"- domain_name: `{domain}`",
        f"- certificate_arn: `{cert_arn}`",
        f"- stack_status: `{stack_status}`",
        "",
        "## AWS State",
        "",
        f"- FrontendDistributionId: `{outputs.get('FrontendDistributionId', '')}`",
        f"- FrontendDistributionDomainName: `{outputs.get('FrontendDistributionDomainName', '')}`",
        f"- FrontendUrl: `{outputs.get('FrontendUrl', '')}`",
        "",
        "## Boundary",
        "",
        "Phase B updated the AWS stack so that CloudFront is configured with the custom domain and ACM certificate.",
        "Because DNS is hosted on Cloudflare rather than Route 53, the final traffic cutover still depends on adding or updating the public DNS record in Cloudflare.",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply the Phase B custom-domain configuration for the AWS-native frontend.")
    parser.add_argument("--stack-name", default=DEFAULT_STACK_NAME)
    parser.add_argument("--region", default=DEFAULT_REGION)
    parser.add_argument("--sam-template", default=str(DEFAULT_TEMPLATE_PATH))
    parser.add_argument("--merged-template-out", default=str(DEFAULT_MERGED_TEMPLATE_B_PATH))
    parser.add_argument("--report-out", default=str(DEFAULT_PHASE_B_REPORT_PATH))
    parser.add_argument("--state-out", default=str(DEFAULT_PHASE_B_STATE_PATH))
    parser.add_argument("--domain-name", required=True)
    parser.add_argument("--certificate-arn", required=True)
    parser.add_argument("--frontend-bucket-name", default="")
    parser.add_argument("--hosted-zone-id", default="")
    args = parser.parse_args()

    cloudformation = boto3.client("cloudformation", region_name=args.region)
    sam_template = load_yaml_template(Path(args.sam_template).resolve())
    processed_template = load_processed_template(cloudformation, args.stack_name)
    frontend_sections = extract_frontend_sections(sam_template)
    merged_template = merge_frontend_into_processed(processed_template, frontend_sections)

    merged_template_path = Path(args.merged_template_out).resolve()
    write_json(merged_template_path, merged_template)

    stack_before = describe_stack(cloudformation, args.stack_name)
    overrides = parameter_overrides_from_stack(stack_before, args.frontend_bucket_name.strip())
    overrides.append(f"FrontendDomainName={args.domain_name}")
    overrides.append(f"FrontendCertificateArn={args.certificate_arn}")
    if args.hosted_zone_id.strip():
        overrides.append(f"FrontendHostedZoneId={args.hosted_zone_id.strip()}")

    run_cloudformation_deploy(args.stack_name, merged_template_path, overrides, args.region)

    stack_after = describe_stack(cloudformation, args.stack_name)
    outputs = stack_outputs(stack_after)
    state = {
        "generated_at": utc_now_iso(),
        "domain_name": args.domain_name,
        "certificate_arn": args.certificate_arn,
        "stack_name": args.stack_name,
        "stack_status": stack_after.get("StackStatus"),
        "outputs": outputs,
    }
    write_json(Path(args.state_out).resolve(), state)
    write_phase_b_report(Path(args.report_out).resolve(), args.domain_name, args.certificate_arn, outputs, stack_after.get("StackStatus", ""))
    print(json.dumps(state, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
