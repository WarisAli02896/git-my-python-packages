from typing import Dict, List, Optional
from datetime import datetime


class EmailTemplate:
    """
    Class to prepare email body and attachments for test automation reports.
    """
    
    TEMPLATE = """Hello Team,

Below are the automation test results for the latest build **{build_version}**:

──────────────────────────────────────

📌 **Execution Summary**

──────────────────────────────────────

• Suite Name: {suite_name}

• Execution Date: {date}

• Duration: {duration}

• Branch: {branch}

• Triggered By: {triggered_by}

──────────────────────────────────────

📊 **Test Statistics**

──────────────────────────────────────

• Total Tests: {total}

• Passed: {passed}

• Failed: {failed}

• Skipped: {skipped}

• Failure Rate: {fail_rate}%

──────────────────────────────────────

📎 Attachments

──────────────────────────────────────

• HTML report

Report is attached for your review.

Regards,  

{your_name}  

{your_position}
"""
    
    def __init__(self, data: Dict):
        """
        Initialize EmailTemplate with test execution data.
        
        Args:
            data: Dictionary containing test execution data with keys:
                - build_version (str): Version/build number
                - suite_name (str): Test suite name
                - date (str, optional): Execution date (default: current date)
                - duration (str): Test execution duration
                - branch (str): Git branch name
                - triggered_by (str): Who/what triggered the test
                - total (int): Total number of tests
                - passed (int): Number of passed tests
                - failed (int): Number of failed tests
                - skipped (int): Number of skipped tests
                - your_name (str): Your name for signature
                - your_position (str): Your position/title
                - html_report_path (str, optional): Path to HTML report file
        """
        self.data = data
        self._validate_data()
        self._calculate_failure_rate()
    
    def _validate_data(self):
        """Validate required fields in data dictionary."""
        required_fields = [
            "build_version", "suite_name", "duration", "branch", 
            "triggered_by", "total", "passed", "failed", "skipped",
            "your_name", "your_position"
        ]
        
        missing_fields = [field for field in required_fields if field not in self.data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    def _calculate_failure_rate(self):
        """Calculate failure rate percentage."""
        total = self.data.get("total", 0)
        failed = self.data.get("failed", 0)
        
        if total > 0:
            self.data["fail_rate"] = round((failed / total) * 100, 2)
        else:
            self.data["fail_rate"] = 0.0
    
    def prepare_body(self) -> str:
        """
        Prepare email body by formatting the template with provided data.
        
        Returns:
            Formatted email body string
        """
        # Set default date if not provided
        if "date" not in self.data or not self.data["date"]:
            self.data["date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Format the template with data
        try:
            body = self.TEMPLATE.format(**self.data)
            return body
        except KeyError as e:
            raise ValueError(f"Missing template variable: {e}")
    
    def get_attachments(self) -> List[str]:
        """
        Get list of attachment file paths.
        
        Returns:
            List of attachment file paths
        """
        attachments = []
        
        # Add HTML report if provided
        html_report_path = self.data.get("html_report_path")
        if html_report_path:
            attachments.append(html_report_path)
        
        return attachments
    
    def prepare_email_data(self) -> Dict:
        """
        Prepare complete email data including body and attachments.
        
        Returns:
            Dictionary with 'body' and 'attachments' keys
        """
        return {
            "body": self.prepare_body(),
            "attachments": self.get_attachments()
        }

