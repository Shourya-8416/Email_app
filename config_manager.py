import json, os

CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        # Create a default configuration file with empty values.
        default_config = {
            "smtp_server": "",
            "smtp_port": 587,
            "imap_server": "",
            "imap_port": 993,
            "email": "",
            "password": "",
            "subject": "",
            "email_template_html": "",
            "csv_file_path": "",
            "email_column_name": "",
            "first_name_column_name": ""
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(default_config, f, indent=4)
        return default_config
    else:
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)
