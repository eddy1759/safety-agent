import pytest
from unittest.mock import patch, Mock
from agent.core import scan_dependencies


@patch('agent.core.get_llm_summary')
def test_scan_with_vulnerabilities_and_mocked_llm(mock_get_llm_summary):
    """
    Tests that the agent calls the LLM service when vulnerabilities are found.
    """
    # Configure the mock to return a predictable value
    mock_get_llm_summary.return_value = "This is a mocked LLM summary."

    # Mock subprocess to simulate vulnerabilities found
    with patch('agent.core.subprocess.run') as mock_run:
        # Simulate safety finding vulnerabilities
        mock_result = Mock()
        mock_result.stdout = '''{
            "report_meta": {},
            "vulnerabilities": [
                {
                    "package_name": "django",
                    "installed_version": "1.8",
                    "affected_versions": "<2.2.13",
                    "vulnerability_id": "12345",
                    "advisory": "SQL injection vulnerability"
                }
            ],
            "remediations": {}
        }'''
        mock_result.returncode = 1  # Non-zero indicates vulnerabilities found
        mock_run.return_value = mock_result

        # Run the scan
        result = scan_dependencies("test_data/unsafe_requirements.txt")

        # Assert that the mock was called exactly once
        mock_get_llm_summary.assert_called_once()

        # Assert that the result contains the mocked summary
        assert result["llm_summary"] == "This is a mocked LLM summary."
        assert result["raw_report"] is not None
        assert result["error"] is None


def test_scan_with_no_vulnerabilities():
    """
    Tests that the agent works correctly when no vulnerabilities are found.
    """
    # Mock subprocess to simulate no vulnerabilities
    with patch('agent.core.subprocess.run') as mock_run:
        mock_result = Mock()
        mock_result.stdout = '[]'  # Empty list means no vulnerabilities
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        result = scan_dependencies("test_data/safe_requirements.txt")
        
        assert result["llm_summary"] == "Scan complete. No vulnerabilities found."
        assert result["error"] is None
        assert result["raw_report"] == []


def test_scan_with_nonexistent_file():
    """
    Tests that the agent handles missing files gracefully.
    """
    result = scan_dependencies("nonexistent_file.txt")
    
    assert "File not found" in result["error"]
    assert result["llm_summary"] is None
    assert result["raw_report"] is None


@patch('agent.core.subprocess.run')
def test_safety_command_not_found(mock_run):
    """
    Tests handling when safety command is not installed.
    """
    mock_run.side_effect = FileNotFoundError("safety command not found")
    
    result = scan_dependencies("test_data/safe_requirements.txt")
    
    assert "Safety command not found" in result["error"]
    assert result["llm_summary"] is None
    assert result["raw_report"] is None


@patch('agent.core.subprocess.run')
def test_invalid_json_output(mock_run):
    """
    Tests handling when safety returns invalid JSON.
    """
    mock_result = Mock()
    mock_result.stdout = "This is not valid JSON"
    mock_result.returncode = 0
    mock_run.return_value = mock_result
    
    result = scan_dependencies("test_data/safe_requirements.txt")
    
    assert "Failed to parse safety output as JSON" in result["error"]
    assert result["llm_summary"] is None