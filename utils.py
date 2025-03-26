import os
import re
import time
import logging
import pandas as pd
import chardet  # For detecting file encoding
import urllib.parse
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from config_manager import load_config

logging.basicConfig(filename="email_log.txt", level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Detect file encoding using chardet
def detect_encoding(file_path):
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            return result['encoding']
    except Exception as e:
        logging.warning(f"Encoding detection failed: {e}. Falling back to 'latin1'.")
        return 'latin1'

def clean_csv_file(input_file, output_file, email_column, name_column):
    try:
        encoding_to_use = detect_encoding(input_file) or 'latin1'
        try:
            df = pd.read_csv(input_file, encoding=encoding_to_use)
        except UnicodeDecodeError:
            logging.warning(f"Error reading with '{encoding_to_use}'. Trying 'cp1252' fallback.")
            df = pd.read_csv(input_file, encoding='cp1252')

        # Clean names
        df[name_column] = df[name_column].astype(str).apply(
            lambda name: ' '.join(word.capitalize() for word in re.sub(r'[^a-zA-Z\s]', '', name).split()) 
            if pd.notna(name) else 'Candidate'
        )
        # Clean and validate emails
        df[email_column] = df[email_column].astype(str).str.strip()
        valid_mask = df[email_column].apply(
            lambda email: bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))
        )
        df = df[valid_mask].drop_duplicates(subset=[email_column], keep='first')
        df.to_csv(output_file, index=False, encoding='utf-8')
        logging.info(f"Cleaned data saved to {output_file}")
        return output_file
    except Exception as e:
        logging.error(f"An error occurred during CSV cleaning: {e}")
        return None

def create_unsubscribe_link(email, config):
    encoded_email = urllib.parse.quote(email)
    # For example, user can update the domain via configuration.
    domain = config.get("unsubscribe_domain", "yourdomain.com")
    return f"https://{domain}/unsubscribe?email={encoded_email}"

def add_tracking_pixel(html_body, tracking_id, config):
    # User can set their own tracking URL base in the configuration.
    tracking_url_base = config.get("tracking_url", "https://yourdomain.com/track?id=")
    tracking_url = f"{tracking_url_base}{tracking_id}"
    tracking_pixel = f'<img src="{tracking_url}" width="1" height="1" alt="" style="display:none;" />'
    return html_body + tracking_pixel

def send_email(recipient, first_name):
    config = load_config()  # Get current configuration
    # Validate essential configuration parameters:
    if not config.get("email") or not config.get("password"):
        logging.error("Email credentials not configured!")
        return False

    message = MIMEMultipart("alternative")
    message["From"] = f"Campaign <{config.get('email')}>"
    message["To"] = recipient
    message["Subject"] = config.get("subject", "Your Subject Here")
    message["List-Unsubscribe"] = f"<{create_unsubscribe_link(recipient, config)}>"

    first_name = first_name.strip() if isinstance(first_name, str) and first_name.strip() else "Candidate"

    html_body = config.get("email_template_html", "").format(first_name=first_name)
    # Add tracking pixel (if desired)
    import uuid
    tracking_id = str(uuid.uuid4())
    html_body = add_tracking_pixel(html_body, tracking_id, config)
    part1 = MIMEText(html_body, "html")
    message.attach(part1)

    try:
        import smtplib
        with smtplib.SMTP(config.get("smtp_server"), int(config.get("smtp_port", 587))) as server:
            server.starttls()
            server.login(config.get("email"), config.get("password"))
            server.send_message(message)
        logging.info(f"Email sent successfully to {recipient}, Name: {first_name}")
        return True
    except Exception as e:
        logging.error(f"Error sending email to {recipient}: {e}")
        return False
