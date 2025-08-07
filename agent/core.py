import json
import subprocess
import os
from agent.llm_service import get_llm_summary

def scan_dependencies(file_path: str) -> dict:
    """
    Scans a requirements.txt file and returns a structured report
    including a raw report and an LLM-generated summary.
    Args:
        file_path (str): The path to the file to scan.
    """
    final_report = {
        "raw_report": None,
        "llm_summary": None,
        "error": None
    }
    
    # Check if file exists first
    if not os.path.exists(file_path):
        return {"error": f"File not found: {file_path}", "llm_summary": None, "raw_report": None}
    
    try:
        # Use the new safety scan command with JSON output
        result = subprocess.run(
            ["safety", "scan", "-r", file_path, "--output", "json"],
            capture_output=True,
            text=True,
            check=False  # Don't raise exception on non-zero exit
        )
        
        # Parse the JSON output
        if result.stdout:
            try:
                raw_report = json.loads(result.stdout)
            except json.JSONDecodeError:
                return {
                    "error": "Failed to parse safety output as JSON",
                    "llm_summary": None, 
                    "raw_report": {"raw_output": result.stdout}
                }
        else:
            return {
                "error": "No output from safety command",
                "llm_summary": None,
                "raw_report": None
            }
            
    except FileNotFoundError:
        return {
            "error": "Safety command not found. Please install safety: pip install safety",
            "llm_summary": None,
            "raw_report": None
        }
    except Exception as e:
        return {
            "error": f"Unexpected error running safety: {str(e)}",
            "llm_summary": None,
            "raw_report": None
        }
    
    # Store the raw report in the final report
    final_report["raw_report"] = raw_report

    # Check if vulnerabilities were found
    # The new safety format might be different, let's handle multiple formats
    has_vulnerabilities = False
    if raw_report:
        # Handle new safety scan format
        if isinstance(raw_report, dict):
            # Check for various possible vulnerability keys
            vulnerabilities = raw_report.get("vulnerabilities", [])
            scan_target = raw_report.get("scan_target", {})
            
            if vulnerabilities:
                has_vulnerabilities = len(vulnerabilities) > 0
            elif scan_target and scan_target.get("vulnerabilities_found", 0) > 0:
                has_vulnerabilities = True
            # Check for files with vulnerabilities
            elif raw_report.get("files", []):
                for file_info in raw_report["files"]:
                    if file_info.get("issues", []):
                        has_vulnerabilities = True
                        break
        # Handle old format (list of vulnerabilities)
        elif isinstance(raw_report, list) and raw_report:
            has_vulnerabilities = True

    if has_vulnerabilities:
        final_report["llm_summary"] = get_llm_summary(raw_report)
    else:
        final_report["llm_summary"] = "Scan complete. No vulnerabilities found."

    return final_report