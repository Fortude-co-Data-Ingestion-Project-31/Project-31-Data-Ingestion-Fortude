import os
from pathlib import Path

from dotenv import load_dotenv


load_dotenv(Path(__file__).with_name(".env"))


JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "https://student-team-lf3k5yqq.atlassian.net/")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "jhua0145@student.monash.edu")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")


# def required_setting(name: str) -> str:
#     value = os.getenv(name)
#     if not value:
#         raise RuntimeError(f"Missing required environment setting: {name}")
#     return value

# # Infor M3
# INFOR_TENANT = required_setting("INFOR_TENANT")
# INFOR_CLIENT_ID = required_setting("INFOR_CLIENT_ID")
# INFOR_CLIENT_SECRET = required_setting("INFOR_CLIENT_SECRET")
# INFOR_USERNAME = required_setting("INFOR_USERNAME")
# INFOR_PASSWORD = required_setting("INFOR_PASSWORD")
# INFOR_TOKEN_URL = required_setting("INFOR_TOKEN_URL")
# INFOR_BASE_URL = required_setting("INFOR_BASE_URL")
