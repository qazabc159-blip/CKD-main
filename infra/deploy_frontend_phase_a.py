from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import boto3
import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[1]
INFRA_DIR = PROJECT_ROOT / "infra"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts" / "system_eval_aws"
DEFAULT_STACK_NAME = "ckd-inference-stack"
DEFAULT_REGION = "ap-northeast-1"
DEFAULT_TEMPLATE_PATH = INFRA_DIR / "template.yaml"
DEFAULT_MERGED_TEMPLATE_PATH = ARTIFACTS_DIR / "frontend_phase_a_merged_template.json"
DEFAULT_UPLOAD_MANIFEST_PATH = ARTIFACTS_DIR / "frontend_static_site_live_manifest.json"
DEFAULT_VERIFICATION_PATH = ARTIFACTS_DIR / "frontend_phase_a_verification.json"
DEFAULT_REPORT_PATH = ARTIFACTS_DIR / "frontend_phase_a_live_deployment_report.md"
DEFAULT_VERSION_FILE = PROJECT_ROOT / "web" / "DEPLOY_VERSION.txt"

FRONTEND_PARAMETER_KEYS = [
    "EnableFrontendHosting",
    "FrontendBucketName",
    "FrontendPriceClass",
    "FrontendDomainName",
    "FrontendCertificateArn",
    "FrontendHostedZoneId",
]

FRONTEND_CONDITION_KEYS = [
    "FrontendHostingEnabled",
    "HasFrontendBucketName",
    "HasFrontendDomainName",
    "HasFrontendCertificateArn",
    "HasFrontendHostedZoneId",
    "UseFrontendCustomDomain",
    "CreateFrontendDnsRecord",
]

FRONTEND_RESOURCE_KEYS = [
    "CkdFrontendSiteBucket",
    "CkdFrontendOriginAccessControl",
    "CkdFrontendUrlRewriteFunction",
    "CkdFrontendStaticCachePolicy",
    "CkdFrontendNoCachePolicy",
    "CkdFrontendDistribution",
    "CkdFrontendBucketPolicy",
    "CkdFrontendDnsRecordSetGroup",
]

FRONTEND_OUTPUT_KEYS = [
    "FrontendBucketName",
    "FrontendDistributionId",
    "FrontendDistributionDomainName",
    "FrontendUrl",
]


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class CfnLoader(yaml.SafeLoader):
    pass


def _ref_constructor(loader: CfnLoader, node: yaml.Node) -> dict[str, Any]:
    return {"Ref": loader.construct_scalar(node)}


def _getatt_constructor(loader: CfnLoader, node: yaml.Node) -> dict[str, Any]:
    value = loader.construct_scalar(node)
    if "." in value:
        return {"Fn::GetAtt": value.split(".", 1)}
    return {"Fn::GetAtt": [value]}


def _generic_intrinsic(name: str):
    def constructor(loader: CfnLoader, node: yaml.Node) -> dict[str, Any]:
        if isinstance(node, yaml.ScalarNode):
            value = loader.construct_scalar(node)
        elif isinstance(node, yaml.SequenceNode):
            value = loader.construct_sequence(node)
        else:
            value = loader.construct_mapping(node)
        return {name: value}

    return constructor


CfnLoader.add_constructor("!Ref", _ref_constructor)
CfnLoader.add_constructor("!GetAtt", _getatt_constructor)
for tag, name in {
    "!Sub": "Fn::Sub",
    "!If": "Fn::If",
    "!Equals": "Fn::Equals",
    "!Not": "Fn::Not",
    "!And": "Fn::And",
    "!Or": "Fn::Or",
    "!Split": "Fn::Split",
    "!Join": "Fn::Join",
    "!Select": "Fn::Select",
}.items():
    CfnLoader.add_constructor(tag, _generic_intrinsic(name))


def load_yaml_template(path: Path) -> dict[str, Any]:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=CfnLoader)


def load_processed_template(cloudformation: Any, stack_name: str) -> dict[str, Any]:
    response = cloudformation.get_template(StackName=stack_name, TemplateStage="Processed")
    return response["TemplateBody"]


def describe_stack(cloudformation: Any, stack_name: str) -> dict[str, Any]:
    response = cloudformation.describe_stacks(StackName=stack_name)
    stacks = response.get("Stacks", [])
    if not stacks:
        raise RuntimeError(f"Stack `{stack_name}` was not found.")
    return stacks[0]


def extract_frontend_sections(sam_template: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        "Parameters": {key: sam_template["Parameters"][key] for key in FRONTEND_PARAMETER_KEYS},
        "Conditions": {key: sam_template["Conditions"][key] for key in FRONTEND_CONDITION_KEYS},
        "Resources": {key: sam_template["Resources"][key] for key in FRONTEND_RESOURCE_KEYS},
        "Outputs": {key: sam_template["Outputs"][key] for key in FRONTEND_OUTPUT_KEYS},
    }


def merge_frontend_into_processed(processed: dict[str, Any], frontend: dict[str, dict[str, Any]]) -> dict[str, Any]:
    merged = json.loads(json.dumps(processed))
    for section in ("Parameters", "Conditions", "Resources", "Outputs"):
        merged.setdefault(section, {})
        merged[section].update(frontend[section])
    return merged


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_deploy_version(path: Path, stack_name: str) -> str:
    version = f"ckd-frontend-phase-a-{stack_name}-{utc_now_iso()}"
    path.write_text(version + "\n", encoding="utf-8")
    return version


def parameter_overrides_from_stack(stack: dict[str, Any], frontend_bucket_name: str) -> list[str]:
    overrides = [f"{item['ParameterKey']}={item['ParameterValue']}" for item in stack.get("Parameters", [])]
    overrides.append("EnableFrontendHosting=true")
    overrides.append("FrontendPriceClass=PriceClass_200")
    if frontend_bucket_name:
        overrides.append(f"FrontendBucketName={frontend_bucket_name}")
    return overrides


def run_cloudformation_deploy(stack_name: str, template_file: Path, overrides: list[str], region: str) -> None:
    aws_cli = shutil.which("aws") or str(Path(sys.executable).resolve().parent / "Scripts" / "aws.cmd")
    command = [
        aws_cli,
        "cloudformation",
        "deploy",
        "--stack-name",
        stack_name,
        "--template-file",
        str(template_file),
        "--region",
        region,
        "--capabilities",
        "CAPABILITY_IAM",
        "--no-fail-on-empty-changeset",
        "--parameter-overrides",
        *overrides,
    ]
    subprocess.run(command, check=True)


def run_upload(stack_name: str, region: str, manifest_path: Path) -> None:
    command = [
        sys.executable,
        str(INFRA_DIR / "deploy_frontend_static_site.py"),
        "--stack-name",
        stack_name,
        "--region",
        region,
        "--manifest-out",
        str(manifest_path),
    ]
    subprocess.run(command, check=True)


def fetch_text(url: str, timeout: float = 10.0) -> tuple[int, str]:
    request = urllib.request.Request(url, headers={"User-Agent": "ckd-frontend-phase-a-verifier/1.0"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        body = response.read().decode("utf-8-sig", errors="replace")
        return response.status, body


def verify_url(url: str, expected_substrings: list[str], attempts: int = 8, sleep_seconds: int = 15) -> dict[str, Any]:
    last_error = None
    for attempt in range(1, attempts + 1):
        try:
            status, body = fetch_text(url)
            if status == 200 and all(substring in body for substring in expected_substrings):
                return {
                    "url": url,
                    "status_code": status,
                    "matched": True,
                    "attempt": attempt,
                    "body_excerpt": body[:400],
                }
            last_error = f"status={status}, matched={all(substring in body for substring in expected_substrings)}"
        except urllib.error.URLError as exc:
            last_error = str(exc)
        if attempt < attempts:
            time.sleep(sleep_seconds)
    return {
        "url": url,
        "matched": False,
        "attempts": attempts,
        "last_error": last_error,
    }


def stack_outputs(stack: dict[str, Any]) -> dict[str, str]:
    return {
        item["OutputKey"]: item["OutputValue"]
        for item in stack.get("Outputs", [])
        if "OutputKey" in item and "OutputValue" in item
    }


def write_report(
    report_path: Path,
    stack_name: str,
    region: str,
    deploy_version: str,
    outputs: dict[str, str],
    verification: dict[str, Any],
) -> None:
    lines = [
        "# Frontend Phase A Live Deployment Report",
        "",
        f"- generated_at_utc: `{utc_now_iso()}`",
        f"- stack_name: `{stack_name}`",
        f"- region: `{region}`",
        f"- deploy_version: `{deploy_version}`",
        "",
        "## Scope",
        "",
        "This report records Phase A of the AWS-native frontend cutover:",
        "",
        "- provision S3 + CloudFront frontend hosting on the existing AWS stack",
        "- upload the static site from `web/`",
        "- verify the CloudFront-served frontend before any Route 53 or custom-domain cutover",
        "",
        "## Outputs",
        "",
        f"- FrontendBucketName: `{outputs.get('FrontendBucketName', '')}`",
        f"- FrontendDistributionId: `{outputs.get('FrontendDistributionId', '')}`",
        f"- FrontendDistributionDomainName: `{outputs.get('FrontendDistributionDomainName', '')}`",
        f"- FrontendUrl: `{outputs.get('FrontendUrl', '')}`",
        "",
        "## Verification Summary",
        "",
        f"- root_ok: `{verification['root'].get('matched')}`",
        f"- landing_ok: `{verification['landing'].get('matched')}`",
        f"- app_ok: `{verification['app'].get('matched')}`",
        f"- config_ok: `{verification['config'].get('matched')}`",
        "",
        "## Boundary",
        "",
        "Phase A confirms that the frontend can now run through the AWS-native S3 + CloudFront hosting path.",
        "Route 53 / custom-domain cutover remains a separate Phase B step.",
        "",
    ]
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Deploy the Phase A AWS-native frontend path (S3 + CloudFront) onto the existing inference stack.")
    parser.add_argument("--stack-name", default=DEFAULT_STACK_NAME)
    parser.add_argument("--region", default=DEFAULT_REGION)
    parser.add_argument("--sam-template", default=str(DEFAULT_TEMPLATE_PATH))
    parser.add_argument("--merged-template-out", default=str(DEFAULT_MERGED_TEMPLATE_PATH))
    parser.add_argument("--upload-manifest-out", default=str(DEFAULT_UPLOAD_MANIFEST_PATH))
    parser.add_argument("--verification-out", default=str(DEFAULT_VERIFICATION_PATH))
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT_PATH))
    parser.add_argument("--frontend-bucket-name", default="", help="Optional explicit frontend bucket name.")
    args = parser.parse_args()

    cloudformation = boto3.client("cloudformation", region_name=args.region)

    sam_template = load_yaml_template(Path(args.sam_template).resolve())
    processed_template = load_processed_template(cloudformation, args.stack_name)
    frontend_sections = extract_frontend_sections(sam_template)
    merged_template = merge_frontend_into_processed(processed_template, frontend_sections)

    merged_template_path = Path(args.merged_template_out).resolve()
    write_json(merged_template_path, merged_template)

    deploy_version = write_deploy_version(DEFAULT_VERSION_FILE, args.stack_name)

    stack_before = describe_stack(cloudformation, args.stack_name)
    overrides = parameter_overrides_from_stack(stack_before, args.frontend_bucket_name.strip())

    run_cloudformation_deploy(args.stack_name, merged_template_path, overrides, args.region)
    run_upload(args.stack_name, args.region, Path(args.upload_manifest_out).resolve())

    stack_after = describe_stack(cloudformation, args.stack_name)
    outputs = stack_outputs(stack_after)
    frontend_url = outputs["FrontendUrl"].rstrip("/")

    verification = {
        "generated_at": utc_now_iso(),
        "frontend_url": frontend_url,
        "root": verify_url(frontend_url + "/", ["Redirecting to CKD Showcase"]),
        "landing": verify_url(frontend_url + "/landing/", ["CKD"]),
        "app": verify_url(frontend_url + "/app/", ["Run CKD risk prediction"]),
        "config": verify_url(
            frontend_url + "/app/config.js",
            ["https://rrms3q06rb.execute-api.ap-northeast-1.amazonaws.com/prod", "useMockPrediction: false"],
        ),
        "outputs": outputs,
    }
    write_json(Path(args.verification_out).resolve(), verification)
    write_report(Path(args.report_out).resolve(), args.stack_name, args.region, deploy_version, outputs, verification)

    print(json.dumps({"deploy_version": deploy_version, "outputs": outputs, "verification": verification}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
