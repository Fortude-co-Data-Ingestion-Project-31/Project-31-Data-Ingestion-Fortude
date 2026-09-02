import os
from dotenv import load_dotenv

load_dotenv()

# Set these in the shell before starting the Jira connector.
JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "").strip().strip('"').strip("'")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "").strip().strip('"').strip("'")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "").strip().strip('"').strip("'")