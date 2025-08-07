import typer
import json
import sys
from agent.core import scan_dependencies

app = typer.Typer()

@app.command()
def scan(file_path: str):
    """Run the security agent on a given requirements file."""
    try:
        result = scan_dependencies(file_path)
        
        # Pretty-print the JSON result
        print(json.dumps(result, indent=2))

        # Exit with non-zero code if vulnerabilities are found
        if result.get("error"):
            print(f"\nScan failed: {result['error']}", file=sys.stderr)
            sys.exit(1)
        elif result.get("raw_report") and isinstance(result["raw_report"], dict):
            vulnerabilities = result["raw_report"].get("vulnerabilities", [])
            if vulnerabilities:
                print(f"\nScan complete. Found {len(vulnerabilities)} vulnerable package(s).")
                sys.exit(1)
            else:
                print("\nScan complete. No vulnerabilities found.")
                sys.exit(0)
        else:
            print("\nScan complete. No vulnerabilities found.")
            sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    app()