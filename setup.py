from setuptools import setup, find_packages

setup(
    name="python_packages",
    version="0.7",
    packages=find_packages(),
    install_requires = [
        "SQLAlchemy",
        "mysql-connector-python",
        "requests",
        "sshtunnel",
        "paramiko<4.0.0",
        "boto3",
    ],
    description="Library to make connection with database and add QA Test Suite reports",
    author="Waris Ghaffar",
    author_email="waris.ghaffar@venturedive.com"
)
