import re
from urllib.parse import urlparse
# google_form_package.py
import os  # noqa
import json

import gspread
from google.oauth2.service_account import Credentials
from selenium import webdriver

class Sheet:
    def __init__(self):
        key_content = os.environ.get("SERVICE_ACCOUNT_KEY")
        if not key_content:
            raise ValueError("Set SERVICE_ACCOUNT_KEY before running.")
        spreadsheet_url = os.environ.get("SPREADSHEET_URL", "").strip()
        parsed_url = urlparse(spreadsheet_url)
        if (
            parsed_url.scheme != "https"
            or parsed_url.netloc != "docs.google.com"
            or not re.fullmatch(r"/spreadsheets/d/[A-Za-z0-9_-]+(?:/.*)?", parsed_url.path)
        ):
            raise ValueError("Set SPREADSHEET_URL to an authorized HTTPS Google Sheets URL.")
        try:
            key_info = json.loads(key_content)
            if not isinstance(key_info, dict):
                raise ValueError
            credentials = Credentials.from_service_account_info(
                key_info,
                scopes=[
                    "https://www.googleapis.com/auth/spreadsheets",
                    "https://www.googleapis.com/auth/drive",
                ],
            )
        except (ValueError, TypeError, KeyError):
            raise ValueError("SERVICE_ACCOUNT_KEY must contain valid service-account JSON.") from None
        gc = gspread.authorize(credentials)
        self.spreadsheet = gc.open_by_url(spreadsheet_url)

    @staticmethod
    def set_driver():
        # set options and driver settings
        user_agent = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36"
        options = webdriver.ChromeOptions()
        options.add_argument(f"user-agent={user_agent}")
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-extensions")
        options.add_argument('--start-maximized')
        driver = webdriver.Chrome(options=options)
        return driver

    def get_worksheet(self, sheet_name):
        return self.spreadsheet.worksheet(sheet_name)
