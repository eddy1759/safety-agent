import os
import sys
import json
import traceback
import subprocess

from agent.llm_service import get_llm_summary

SCAN_TIMEOUT = int(os.getenv("AGENT_SCAN_TIMEOUT", "600"))


def _parse_pip_audit_report(report_data: dict) -> list:
    """
    A robust parser for the JSON output from `pip-audit`.
    It iterates through dependencies and collects any with vulnerabilities.
    """
    found_vulnerabilities = []
    for dependency in report_data.get("dependencies", []):
        if dependency.get("vulns"):
            found_vulnerabilities.append(dependency)
    return found_vulnerabilities


def _create_simplified_report(vulnerabilities: list) -> list:
    """
    Simplifies the full vulnerability report into a smaller, more focused list
    for the LLM to process.
    """
    simplified_vulns = []
    for dep in vulnerabilities:
        all_fix_versions = [
            v["fix_versions"] for v in dep.get("vulns", []) if v.get("fix_versions")
        ]
        highest_fix_version = sorted(
            [item for sublist in all_fix_versions for item in sublist], reverse=True
        )

        simplified_vulns.append(
            {
                "package_name": dep.get("name"),
                "current_version": dep.get("version"),
                "vulnerability_count": len(dep.get("vulns", [])),
                "recommended_upgrade": (
                    highest_fix_version[0] if highest_fix_version else "Not available"
                ),
                "example_vulnerability_description": dep.get("vulns", [{}])[0].get(
                    "description", "No description available."
                ),
            }
        )
    return simplified_vulns


def _create_compact_report(raw_report: dict, vulnerabilities: list) -> dict:
    """
    Create a minimal representation with only essential dependency info.
    """
    compact_deps = []

    for dep in vulnerabilities:
        compact_deps.append(
            {
                "name": dep.get("name"),
                "version": dep.get("version"),
                "vulnerability_count": len(dep.get("vulns", [])),
            }
        )

    return {"dependencies": compact_deps}


def scan_dependencies(file_path: str) -> dict:
    """
    Scans a single requirements file using pip-audit, the official PyPA tool.
    """
    final_report = {
        "vulnerabilities_found": False,
        "vulnerability_count": 0,
        "raw_report": None,
        "llm_summary": None,
        "error": None,
    }

    if not os.path.exists(file_path):
        final_report["error"] = f"File not found: {file_path}"
        return final_report

    try:
        print(
            f"INFO: Running security audit on {file_path} with pip-audit...",
            file=sys.stderr,
        )

        command = ["pip-audit", "--requirement", file_path, "--format", "json"]

        result = subprocess.run(
            command, capture_output=True, text=True, check=False, timeout=SCAN_TIMEOUT
        )

        if not result.stdout.strip() and result.returncode != 0:
            raise RuntimeError(
                f"pip-audit failed. No output received. Stderr: {result.stderr.strip()}"
            )

        if not result.stdout.strip():
            report_data = {}
        else:
            report_data = json.loads(result.stdout)

        final_report["raw_report"] = report_data

        vulnerabilities = _parse_pip_audit_report(report_data)

        if vulnerabilities:
            final_report["vulnerabilities_found"] = True
            final_report["vulnerability_count"] = sum(
                len(dep.get("vulns", [])) for dep in vulnerabilities
            )
            final_report["package_count"] = len(vulnerabilities)

            compact_report = _create_compact_report(report_data, vulnerabilities)
            final_report["raw_report"] = compact_report

            print(
                f"INFO: Found {len(vulnerabilities)} vulnerable package(s). Generating summary with LLM...",
                file=sys.stderr,
            )

            simplified_report_for_llm = _create_simplified_report(vulnerabilities)

            final_report["llm_summary"] = get_llm_summary(simplified_report_for_llm)
        else:
            final_report["llm_summary"] = "Scan complete. No vulnerabilities found."

    except subprocess.TimeoutExpired:
        final_report["error"] = (
            f"The 'pip-audit' scan timed out after {SCAN_TIMEOUT} seconds."
        )
    except json.JSONDecodeError:
        final_report["error"] = (
            f"Failed to parse pip-audit's JSON output. Raw output: {result.stdout}"
        )
    except Exception as e:
        error_info = traceback.format_exc()
        final_report["error"] = (
            f"An unexpected error occurred: {e}\n\nTraceback:\n{error_info}"
        )
        final_report["vulnerabilities_found"] = False
        final_report["raw_report"] = None
        final_report["llm_summary"] = None

    return final_report
