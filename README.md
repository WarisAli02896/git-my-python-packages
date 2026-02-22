# Database Connection

## Description
This project provides database connection functionality and utilities.

## Installation

### Prerequisites
- Python 3.x

### Dependencies

The following libraries are required for this project:

- **mysql-connector-python** (version 9.5.0)
  - Official MySQL connector for Python
  - Installation: `pip install mysql-connector-python`

- **PyMySQL** (version 1.1.2)
  - Pure Python MySQL client library
  - Installation: `pip install PyMySQL`

- **mysqlclient** (version 2.2.7)
  - MySQL database connector for Python (C API wrapper)
  - Installation: `pip install mysqlclient`

- **aiomysql** (version 0.3.2)
  - Async MySQL driver for asyncio
  - Installation: `pip install aiomysql`

- **SQLAlchemy** (version 2.0.44)
  - SQL toolkit and Object-Relational Mapping (ORM) library
  - Installation: `pip install SQLAlchemy`

- **python-dotenv** (version 1.2.1)
  - Loads environment variables from .env files
  - Useful for managing database connection credentials securely
  - Installation: `pip install python-dotenv`

## Setup

1. Clone this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   Or install individually:
   ```bash
   pip install mysql-connector-python PyMySQL mysqlclient aiomysql SQLAlchemy python-dotenv
   ```
3. Follow the usage instructions below

## Usage

### ReqRes API tests and full reporting pipeline

Run ReqRes.in API tests and then automatically run DB insertion, TestRail integration, and email report:

```bash
# Install deps and package
pip install -r requirements.txt
pip install -e .

# Run tests + DB + TestRail + email (uses config.ini)
python run_tests_with_reporting.py

# Skip specific steps
python run_tests_with_reporting.py --no-db --no-testrail   # only tests + email
python run_tests_with_reporting.py --no-email              # tests + DB + TestRail
```

**Flow:**
1. **Run tests** – Pytest runs `tests/api/test_reqres.py` (ReqRes API) and writes all reports into the **reports/** folder: **reports/Report.html** (HTML report), **reports/test_summary.json** (pytest-json-report), and **reports/summary.json** (pipeline stats: total, passed, failed, skipped, duration, etc.).
2. **DB** – Inserts a row into the table from `[database]` in config (e.g. `test_runs`) using stats from summary.json.
3. **TestRail** – If `[testrail]` has `project_name` and `case_ids` (comma-separated), creates a run and optionally adds results.
4. **Email** – Sends report using `[mail]` and the same summary (Mailer + EmailTemplate).

**Config:** `config.ini` must have `[suite_info]`, and optionally `[database]`, `[mail]`, `[testrail]`. For TestRail run creation, set `case_ids=1,2,3` (your TestRail case IDs). For DB, ensure your table has columns such as `suite_name`, `build_version`, `total_tests`, `passed`, `failed`, `skipped`, `duration`, `execution_date`, `branch`, `triggered_by` (or adjust the row in `run_tests_with_reporting.py`).

**Why do ReqRes API tests fail with 403?** reqres.in is behind **Cloudflare bot protection**. Automated requests (e.g. Python `requests`) are often blocked with 403 and an HTML "Just a moment..." page instead of the JSON API. The tests are correct; the same endpoints work in a browser. To get passing results when the API is blocked, use a mock server or run from a network that allows scripted access.

## Libraries Documentation

<!-- Detailed documentation for each library will be added here -->

## License

<!-- License information -->

## Contributing

<!-- Contributing guidelines -->

