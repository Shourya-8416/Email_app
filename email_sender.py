import time
import pandas as pd
import logging
from utils import clean_csv_file, send_email
from config_manager import load_config

# Global object to track campaign status
campaign_status = {
    "total": 0,
    "sent": 0,
    "failed": 0,
    "progress": "Not started",
    "start_time": None,
    "end_time": None
}

def run_campaign():
    config = load_config()
    campaign_status["progress"] = "Running"
    campaign_status["start_time"] = time.time()

    input_csv = config.get("csv_file_path", "Test_Emails.csv")
    cleaned_csv = "uploads/cleaned_emails.csv"
    email_column = config.get("email_column_name", "Email")
    name_column = config.get("first_name_column_name", "First Name")

    result = clean_csv_file(input_csv, cleaned_csv, email_column, name_column)
    if result is None:
        campaign_status["progress"] = "Error cleaning CSV"
        return

    try:
        email_data = pd.read_csv(cleaned_csv)
    except Exception as e:
        logging.error(f"Failed to read cleaned CSV: {e}")
        campaign_status["progress"] = "Error reading CSV"
        return

    campaign_status["total"] = len(email_data)
    for index, row in email_data.iterrows():
        recipient_email = row[email_column]
        recipient_first_name = row[name_column]
        if send_email(recipient_email, recipient_first_name):
            campaign_status["sent"] += 1
        else:
            campaign_status["failed"] += 1
        time.sleep(2)
    campaign_status["end_time"] = time.time()
    campaign_status["progress"] = "Completed"

def get_campaign_status():
    return campaign_status
