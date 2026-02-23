import json
import os
import configparser
from datetime import datetime, timedelta
from .db_connection import create_db_connection, create_db_connection_with_tunnel
from .db_operations import insert_data

CONFIG_FILE = "config.ini"
SUMMARY_FILE = "reports/test_summary.json"
TABLE_AUTOMATION_RUN = "automation_run"
TABLE_TEST_CASE_EXECUTION = "test_case_execution"


class DB:
    def __init__(self):
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE)

        self.db_config = {
            "host": config.get("database", "host"),
            "user": config.get("database", "user"),
            "password": config.get("database", "password"),
            "database": config.get("database", "database"),
            "port": int(config.get("database", "port")),
        }

        self.ssh_config = None
        if config.has_section("SSH_Database"):
            self.ssh_config = {
                "ssh_host": config.get("SSH_Database", "SSH_HOST"),
                "ssh_user": config.get("SSH_Database", "SSH_USER"),
                "ssh_pem_path": config.get("SSH_Database", "SSH_PEM_PATH"),
            }

        self.test_run_config = {}
        if config.has_section("test_run_data"):
            for key, value in config.items("test_run_data"):
                try:
                    self.test_run_config[key] = int(value)
                except ValueError:
                    self.test_run_config[key] = value

        self.engine = None
        self.tunnel = None
        self.automation_run_id = None
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
        created = report.get("created", 0)
        duration = report.get("duration", 0)

        start_time = datetime.fromtimestamp(created)
        end_time = datetime.fromtimestamp(created + duration)

        return {
            "total_test_cases": summary.get("total", 0),
            "total_test_passed": summary.get("passed", 0),
            "total_test_failed": summary.get("failed", 0),
            "total_test_skipped": summary.get("skipped", 0),
            "execution_start_time": start_time.strftime("%Y-%m-%d %H:%M:%S"),
            "execution_end_time": end_time.strftime("%Y-%m-%d %H:%M:%S"),
        }

    def connect(self):
        if self.ssh_config:
            try:
                print("Attempting SSH tunnel connection...")
                self.engine, self.tunnel = create_db_connection_with_tunnel(
                    ssh_host=self.ssh_config["ssh_host"],
                    ssh_user=self.ssh_config["ssh_user"],
                    ssh_pkey_path=self.ssh_config["ssh_pem_path"],
                    db_host=self.db_config["host"],
                    db_port=self.db_config["port"],
                    db_user=self.db_config["user"],
                    db_password=self.db_config["password"],
                    db_name=self.db_config["database"],
                )
                return self.engine is not None
            except Exception as e:
                print(f"SSH tunnel connection failed: {e}, trying direct connection...")

        try:
            self.engine = create_db_connection(config=self.db_config)
            return self.engine is not None
        except Exception as e:
            print(f"Direct connection also failed: {e}")
            return False

    def insert_test_run(self):
        """
        Insert into automation_run and store the returned ID.
        """
        try:
            stats = self._parse_summary()
            row = {**self.test_run_config, **stats}
            row["executed_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if not self.engine:
                self.connect()

            if not self.engine:
                print("No database connection available")
                return None

            self.automation_run_id = insert_data(self.engine, TABLE_AUTOMATION_RUN, row)
            if self.automation_run_id:
                print(f"Test run inserted with id: {self.automation_run_id}")
            else:
                print("Failed to insert test run data")
            return self.automation_run_id

        except Exception as e:
            print(f"Failed to insert test run data: {e}")
            return None

    def insert_test_case_executions(self):
        """
        Loop through every test case in the summary file and
        insert a row into test_case_execution for each one.
        """
        try:
            if not self.automation_run_id:
                print("No automation_run_id. Call insert_test_run() first.")
                return False

            if not self.engine:
                self.connect()

            if not self.engine:
                print("No database connection available")
                return False

            report = self._load_report()
            tests = report.get("tests", [])
            created = report.get("created", 0)
            current_time = datetime.fromtimestamp(created)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            inserted = 0
            for test in tests:
                nodeid = test.get("nodeid", "")
                test_name = nodeid.split("::")[-1].split("[")[0] if "::" in nodeid else nodeid

                setup_duration = test.get("setup", {}).get("duration", 0)
                call_duration = test.get("call", {}).get("duration", 0)
                teardown_duration = test.get("teardown", {}).get("duration", 0)
                total_duration = setup_duration + call_duration + teardown_duration

                test_start = current_time
                test_end = current_time + timedelta(seconds=total_duration)

                outcome = test.get("outcome", "unknown")

                failure_reason = None
                if outcome == "failed":
                    call_data = test.get("call", {})
                    crash = call_data.get("crash", {})
                    failure_reason = crash.get("message", call_data.get("longrepr", ""))

                row = {
                    "automation_run_id": self.automation_run_id,
                    "test_case_id": nodeid,
                    "test_case_name": test_name,
                    "test_case_status": outcome,
                    "failure_reason": failure_reason,
                    "test_start_time": test_start.strftime("%Y-%m-%d %H:%M:%S"),
                    "test_end_time": test_end.strftime("%Y-%m-%d %H:%M:%S"),
                    "recorded_at": now,
                }

                result = insert_data(self.engine, TABLE_TEST_CASE_EXECUTION, row)
                if result:
                    inserted += 1

                current_time = test_end

            print(f"Inserted {inserted}/{len(tests)} test case executions")
            return inserted == len(tests)

        except Exception as e:
            print(f"Failed to insert test case executions: {e}")
            return False

    def close(self):
        if self.engine:
            self.engine.dispose()
        if self.tunnel:
            self.tunnel.stop()
            print("SSH tunnel closed")
