import configparser

CONFIG_FILE = "config.ini"


def execute():
    """
    Single entry point that reads [clients] from config.ini
    and triggers only the enabled clients.

    config.ini example:
        [clients]
        database_client=true
        testrail_client=false
        mail_client=true
    """
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE)

    db_enabled = config.getboolean("clients", "database_client", fallback=False)
    testrail_enabled = config.getboolean("clients", "testrail_client", fallback=False)
    mail_enabled = config.getboolean("clients", "mail_client", fallback=False)

    if db_enabled:
        try:
            from my_qa_packages.db import DB
            print("--- DB Client: Starting ---")
            db = DB()
            db.connect()
            db.insert_test_run()
            db.insert_test_case_executions()
            db.close()
            print("--- DB Client: Completed ---")
        except Exception as e:
            print(f"--- DB Client: Failed - {e} ---")

    if testrail_enabled:
        try:
            from my_qa_packages.testrail import TestRail
            print("--- TestRail Client: Starting ---")
            testrail = TestRail()
            testrail.run()
            print("--- TestRail Client: Completed ---")
        except Exception as e:
            print(f"--- TestRail Client: Failed - {e} ---")

    if mail_enabled:
        try:
            from my_qa_packages.mailify import Mail
            print("--- Mail Client: Starting ---")
            mail = Mail()
            mail.send()
            print("--- Mail Client: Completed ---")
        except Exception as e:
            print(f"--- Mail Client: Failed - {e} ---")

    if not any([db_enabled, testrail_enabled, mail_enabled]):
        print("No clients enabled in config.ini [clients] section")
