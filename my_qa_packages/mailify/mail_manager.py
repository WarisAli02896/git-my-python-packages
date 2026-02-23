import json
import os
import configparser
from datetime import datetime
from .mailer import Mailer
from .email_template import EmailTemplate

CONFIG_FILE = "config.ini"
SUMMARY_FILE = "reports/test_summary.json"
HTML_REPORT = "reports/report.html"


class Mail:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)

        self.smtp_config = {
            "smtp_server": config.get("mail", "smtp_server"),
            "port": config.getint("mail", "port", fallback=587),
            "username": config.get("mail", "username"),
            "password": config.get("mail", "password"),
            "use_tls": config.getboolean("mail", "use-tls", fallback=True),
            "sender": config.get("mail", "sender"),
        }

        self.recipients = config.get("mail", "recipients", fallback="")
        self.your_name = config.get("mail", "your_name")
        self.your_position = config.get("mail", "your_position")

        self.suite_name = config.get("suite_info", "suite_name", fallback="Automation Suite")
        self.build_version = config.get("suite_info", "build_version", fallback="N/A")
        self.branch = config.get("suite_info", "branch", fallback="N/A")
        self.triggered_by = config.get("suite_info", "triggered_by", fallback="Automation")

        self._report = None

    def _load_report(self):
        if self._report is not None:
            return self._report

        if not os.path.exists(SUMMARY_FILE):
            raise FileNotFoundError(f"Summary file not found: {SUMMARY_FILE}")

        with open(SUMMARY_FILE, "r") as f:
            self._report = json.load(f)
        return self._report

    def _parse_summary(self) -> dict:
        report = self._load_report()
        summary = report.get("summary", {})
        duration_secs = report.get("duration", 0)
        created = report.get("created", None)

        mins, secs = divmod(int(duration_secs), 60)
        duration_str = f"{mins}m {secs}s" if mins else f"{secs}s"

        date_str = ""
        if created:
            date_str = datetime.fromtimestamp(created).strftime("%Y-%m-%d %H:%M:%S")

        return {
            "total": summary.get("total", 0),
            "passed": summary.get("passed", 0),
            "failed": summary.get("failed", 0),
            "skipped": summary.get("skipped", 0),
            "duration": duration_str,
            "date": date_str,
        }

    def send(self):
        """
        Full flow:
        1. Load summary file
        2. Build email data from config + summary
        3. Prepare email body via template
        4. Send email with HTML report attachment
        """
        try:
            stats = self._parse_summary()

            email_data = {
                "build_version": self.build_version,
                "suite_name": self.suite_name,
                "date": stats["date"],
                "duration": stats["duration"],
                "branch": self.branch,
                "triggered_by": self.triggered_by,
                "total": stats["total"],
                "passed": stats["passed"],
                "failed": stats["failed"],
                "skipped": stats["skipped"],
                "your_name": self.your_name,
                "your_position": self.your_position,
            }

            if os.path.exists(HTML_REPORT):
                email_data["html_report_path"] = HTML_REPORT

            template = EmailTemplate(email_data)
            prepared = template.prepare_email_data()

            subject = f"Test Report - {self.suite_name} | {stats['passed']}/{stats['total']} Passed"

            mailer = Mailer(config=self.smtp_config)
            mailer.send_mail(
                recipients=self.recipients,
                subject=subject,
                body=prepared["body"],
                attachments=prepared["attachments"],
            )

            print(f"Report email sent to: {self.recipients}")
            return True

        except Exception as e:
            print(f"Mail integration failed: {e}")
            return False
