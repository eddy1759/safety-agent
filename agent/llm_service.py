import os
import sys
import json
import traceback

import google.generativeai as genai


def configure_google_model():
    """
    Configures and returns a Google Gemini model instance.
    """
    try:
        api_key = os.getenv("GOOGLE_API_KEY")

        if not api_key:
            print(
                "Warning: GOOGLE_API_KEY environment variable not set.", file=sys.stderr
            )
            return None

        genai.configure(api_key=api_key)

        model = genai.GenerativeModel("gemini-1.5-flash-latest")
        return model
    except Exception as e:
        print(
            f"Warning: Google Gemini model could not be initialized. Error: {e}",
            file=sys.stderr,
        )
        return None


model = configure_google_model()


def get_llm_summary(vulnerability_report: dict | list) -> str:
    """
    Generates a summary of the vulnerability report using Google Gemini.
    """
    if model is None:
        return (
            "Google Gemini service is not available. Please check your GOOGLE_API_KEY."
        )

    report_json_str = json.dumps(vulnerability_report, indent=2)

    prompt = f"""
    You are a security expert assistant. Your task is to analyze the following simplified JSON security report and provide a clear, concise, and actionable summary for a developer. The report contains one or more vulnerable packages.

    Here is the simplified security report:
    ```json
    {report_json_str}
    ```

     ### Next Steps
    [1-2 sentences with immediate action items]
    """

    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(
            f"ERROR: An error occurred while communicating with the Google Gemini API.",
            file=sys.stderr,
        )
        traceback.print_exc()
        return f"Error communicating with Google Gemini API: {e}"
