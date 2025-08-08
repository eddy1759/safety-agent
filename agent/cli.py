import typer
import json
import sys
from agent.core import scan_dependencies

app = typer.Typer()


def format_json_output(data: dict) -> str:
    """
    Format JSON output in a clean, readable way.
    """
    return json.dumps(data, indent=2, ensure_ascii=False, separators=(",", ": "))


@app.callback(invoke_without_command=True)
def main(
    file_path: str = typer.Argument(
        ..., help="The path to the requirements file to scan."
    ),
):
    """
    Run the security agent on a given requirements file.
    """
    try:
        result = scan_dependencies(file_path)
    except Exception as e:
        print(f"A critical error occurred during the scan: {e}", file=sys.stderr)
        raise typer.Exit(code=1)

    print(format_json_output(result))

    if result.get("error"):
        print(f"\n❌ SCAN FAILED: {result['error']}", file=sys.stderr)
        raise typer.Exit(code=1)

    if result.get("vulnerabilities_found"):
        vuln_count = result.get("vulnerability_count", 0)
        pkg_count = result.get("package_count", 0)
        print(
            f"\n⚠️  VULNERABILITIES DETECTED: {vuln_count} issues in {pkg_count} package(s)",
            file=sys.stderr,
        )
        raise typer.Exit(code=1)
    else:
        print(f"\n✅ SCAN COMPLETE: No vulnerabilities found", file=sys.stderr)
        raise typer.Exit(code=0)


if __name__ == "__main__":
    app()
