import json
import os
import configparser
from datetime import datetime
from .testrail_client import TestRailClient

CONFIG_FILE = "config.ini"
SUMMARY_FILE = "reports/test_summary.json"


class TestRail:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)

        self.testrail_config = {
            "base_url": config.get("testrail", "base_url"),
            "username": config.get("testrail", "username"),
            "api_key": config.get("testrail", "api_key"),
        }
        self.project_name = config.get("testrail", "project_name")
        self.suite_id = config.get("testrail", "suite_id", fallback=None)
        if self.suite_id:
            self.suite_id = int(self.suite_id) if self.suite_id.strip() else None
        self.run_name = config.get("testrail", "run_name", fallback=None)
        self.run_description = config.get("testrail", "run_description", fallback=None)

        self.client = None
        self.project = None
        self.project_id = None
        self.run_id = None
        self._report = None

    def _load_report(self):
        if self._report is not None:
            return self._report

        if not os.path.exists(SUMMARY_FILE):
            raise FileNotFoundError(f"Summary file not found: {SUMMARY_FILE}")

        with open(SUMMARY_FILE, "r") as f:
            self._report = json.load(f)
        return self._report

    def _extract_test_info(self, test: dict) -> dict:
        """Extract section name, test name, and status from a test entry."""
        nodeid = test.get("nodeid", "")
        parts = nodeid.split("::")

        # tests/test_cart.py::TestCart::test_added_item_appears_in_cart[chromium]
        section_name = parts[1] if len(parts) > 1 else "General"
        full_test_name = parts[-1] if parts else nodeid
        test_name = full_test_name.split("[")[0]

        outcome = test.get("outcome", "unknown")
        status_map = {
            "passed": TestRailClient.STATUS_PASSED,
            "failed": TestRailClient.STATUS_FAILED,
            "skipped": TestRailClient.STATUS_BLOCKED,
        }
        status = status_map.get(outcome, TestRailClient.STATUS_UNTESTED)

        failure_reason = None
        if outcome == "failed":
            call_data = test.get("call", {})
            crash = call_data.get("crash", {})
            failure_reason = crash.get("message", call_data.get("longrepr", ""))

        return {
            "section_name": section_name,
            "test_name": test_name,
            "status": status,
            "failure_reason": failure_reason,
            "nodeid": nodeid,
        }

    def connect(self):
        self.client = TestRailClient(config=self.testrail_config)
        self.project = self.client.get_project_by_name(self.project_name)
        if not self.project:
            raise ValueError(f"Project '{self.project_name}' not found in TestRail")
        self.project_id = self.project.get("id")
        return True

    def run(self):
        """
        Full flow:
        1. Connect to TestRail
        2. Load test results from summary file
        3. Get/create sections and cases
        4. Create test run
        5. Update statuses
        """
        try:
            if not self.client:
                self.connect()

            report = self._load_report()
            tests = report.get("tests", [])

            if not tests:
                print("No tests found in summary file")
                return False

            # Parse all test info
            test_infos = [self._extract_test_info(t) for t in tests]

            # Get existing sections
            existing_sections = self.client.get_sections(self.project_id, self.suite_id)
            section_map = {s["name"]: s["id"] for s in existing_sections}

            # Get existing cases
            existing_cases = self.client.get_cases(self.project_id, self.suite_id)
            case_map = {c["title"]: c["id"] for c in existing_cases}

            # Create missing sections and cases
            case_ids = []
            case_to_info = {}

            for info in test_infos:
                section_name = info["section_name"]
                test_name = info["test_name"]

                # Get or create section
                if section_name not in section_map:
                    section = self.client.add_section(
                        self.project_id, section_name, suite_id=self.suite_id
                    )
                    section_map[section_name] = section["id"]

                section_id = section_map[section_name]

                # Get or create case
                if test_name not in case_map:
                    case = self.client.add_case(section_id, test_name)
                    case_map[test_name] = case["id"]

                case_id = case_map[test_name]
                case_ids.append(case_id)
                case_to_info[case_id] = info

            # Create test run
            run_name = self.run_name or f"Automation Run - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            test_run = self.client.create_test_run(
                project_name=self.project_name,
                test_case_ids=case_ids,
                suite_id=self.suite_id,
                name=run_name,
                description=self.run_description,
            )

            if not test_run:
                print("Failed to create test run")
                return False

            self.run_id = test_run.get("id")

            # Update statuses in batch
            results = []
            for case_id, info in case_to_info.items():
                result = {
                    "case_id": case_id,
                    "status_id": info["status"],
                }
                if info["failure_reason"]:
                    result["comment"] = info["failure_reason"]
                results.append(result)

            self.client.update_test_case_status_batch(self.run_id, results)
            print(f"TestRail run #{self.run_id} completed with {len(results)} results")
            return True

        except Exception as e:
            print(f"TestRail integration failed: {e}")
            return False
