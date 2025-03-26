from flask import Flask, render_template, request, redirect, url_for, flash
import os, threading
from email_sender import run_campaign, get_campaign_status
from config_manager import load_config, save_config

app = Flask(__name__)
app.secret_key = "supersecretkey"  # In production, use a secure key or environment variable

# Ensure the uploads directory exists
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.template_filter('datetimeformat')
def datetimeformat(value):
    import datetime
    return datetime.datetime.fromtimestamp(value).strftime('%Y-%m-%d %H:%M:%S')

# Dashboard
@app.route("/")
def index():
    status = get_campaign_status()
    config = load_config()
    return render_template("index.html", status=status, config=config)

# CSV Upload
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        if "file" not in request.files:
            flash("No file part in the request")
            return redirect(request.url)
        file = request.files["file"]
        if file.filename == "":
            flash("No file selected")
            return redirect(request.url)
        file_path = os.path.join(app.config["UPLOAD_FOLDER"], file.filename)
        file.save(file_path)
        # Update configuration to use the newly uploaded file
        config = load_config()
        config["csv_file_path"] = file_path
        save_config(config)
        flash("CSV file uploaded and configuration updated!")
        return redirect(url_for("index"))
    return render_template("upload.html")

# Start Campaign (runs in background)
@app.route("/start_campaign")
def start_campaign():
    threading.Thread(target=run_campaign, daemon=True).start()
    flash("Campaign started! Check dashboard for status.")
    return redirect(url_for("index"))

# Configuration page to update all settings
@app.route("/config", methods=["GET", "POST"])
def config():
    config = load_config()
    if request.method == "POST":
        # Update each setting from form fields
        config["smtp_server"] = request.form.get("smtp_server", config.get("smtp_server"))
        config["smtp_port"] = int(request.form.get("smtp_port", config.get("smtp_port", 587)))
        config["imap_server"] = request.form.get("imap_server", config.get("imap_server"))
        config["imap_port"] = int(request.form.get("imap_port", config.get("imap_port", 993)))
        config["email"] = request.form.get("email", config.get("email"))
        config["password"] = request.form.get("password", config.get("password"))
        config["subject"] = request.form.get("subject", config.get("subject"))
        config["email_template_html"] = request.form.get("email_template_html", config.get("email_template_html"))
        config["email_column_name"] = request.form.get("email_column_name", config.get("email_column_name"))
        config["first_name_column_name"] = request.form.get("first_name_column_name", config.get("first_name_column_name"))
        # Optional: unsubscribe domain and tracking URL can also be set
        config["unsubscribe_domain"] = request.form.get("unsubscribe_domain", config.get("unsubscribe_domain", "yourdomain.com"))
        config["tracking_url"] = request.form.get("tracking_url", config.get("tracking_url", "https://yourdomain.com/track?id="))
        
        save_config(config)
        flash("Configuration updated successfully!")
        return redirect(url_for("index"))
    return render_template("config.html", config=config)

if __name__ == "__main__":
    app.run(debug=True)
