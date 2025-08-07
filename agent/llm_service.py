import os
import json
from openai import OpenAI

def get_openai_client():
    """
    Initialize OpenAI client with proper API key handling.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        print("Warning: OPENAI_API_KEY environment variable not set.")
        return None
    
    try:
        client = OpenAI(api_key=api_key)
        return client
    except Exception as e:
        print(f"Warning: OpenAI client could not be initialized. Error: {e}")
        return None

# Initialize the client
client = get_openai_client()
    
def get_llm_summary(vulnerability_report: dict) -> str:
    """
    Generates a summary of the vulnerability report using OpenAI's LLM.
    """
    if client is None:
        return "LLM service is not available. Please check your OPENAI_API_KEY environment variable."

    # Handle both old and new safety report formats
    vulnerabilities = []
    if isinstance(vulnerability_report, dict):
        vulnerabilities = vulnerability_report.get("vulnerabilities", [])
    elif isinstance(vulnerability_report, list):
        vulnerabilities = vulnerability_report
    
    if not vulnerabilities:
        return "No vulnerabilities found or report is empty."
    
    # Convert the dict to a JSON string for the prompt
    report_json_str = json.dumps(vulnerability_report, indent=2)
    
    prompt = f"""
    You are a security expert assistant. Your task is to analyze a JSON security report from the 'safety' library and provide a clear, concise, and actionable summary for a developer.

    Here is the security report:
    ```json
    {report_json_str}
    ```

    Please provide a response in Markdown format with the following sections:

    ### Executive Summary
    A brief, one-paragraph summary of the findings. Mention the number of vulnerabilities and the highest severity level found.

    ### Vulnerability Details
    For each vulnerability, provide:
    - **Package:** The name of the vulnerable package.
    - **Impact:** A simple, one-sentence explanation of the potential risk.
    - **Recommendation:** The specific action to take, like "Upgrade to version `X.Y.Z` or higher."

    ### Overall Recommendation
    Provide a final, clear recommendation on the next steps. For example, suggest creating a new `requirements.txt` with the fixed versions.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful security expert assistant."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error communicating with LLM API: {e}"