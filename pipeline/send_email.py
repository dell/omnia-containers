# Copyright 2026 Dell Inc. or its subsidiaries. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Email notification script for Omnia GitLab CI/CD pipeline.

Sends the test report as an HTML attachment via SMTP relay.
All configuration is read from GitLab CI/CD variables (environment):

    EMAIL_RECIPIENTS  - Comma-separated list of recipients (required)
    EMAIL_SENDER      - From address (required)
    SMTP_SERVER       - SMTP relay host (required)
    SMTP_PORT         - SMTP relay port (default: 25)
    SMTP_USER         - SMTP username (optional, for authenticated relay)
    SMTP_PASSWORD     - SMTP password (optional, for authenticated relay)
    REPORT_PATH       - Absolute path to test_report.html on target server (required)

GitLab-provided variables used automatically:
    PIPELINE_TRIGGER_TIME - Set by initialization stage
    CI_PIPELINE_URL       - Auto-set by GitLab
"""
import os
import smtplib
import time
import traceback
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# ---------------------------------------------------------------------------
recipients = [
    r.strip()
    for r in os.environ.get("EMAIL_RECIPIENTS", "").split(",")
    if r.strip()
]
SMTP_SERVER = os.environ.get("SMTP_SERVER", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "25"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
SENDER_EMAIL = os.environ.get("EMAIL_SENDER", "")
REPORT_PATH = os.environ.get("REPORT_PATH", "")
REPORT_FILENAME_ONLY = os.path.basename(REPORT_PATH)

trigger_time = os.environ.get("PIPELINE_TRIGGER_TIME", "")
pipeline_url = os.environ.get("CI_PIPELINE_URL", "")

# ---------------------------------------------------------------------------
missing = []
if not recipients:
    missing.append("EMAIL_RECIPIENTS")
if not SMTP_SERVER:
    missing.append("SMTP_SERVER")
if not SENDER_EMAIL:
    missing.append("EMAIL_SENDER")
if not REPORT_PATH:
    missing.append("REPORT_PATH")
if missing:
    raise SystemExit(
        f"Missing required GitLab CI/CD variables: {', '.join(missing)}"
    )

print(f"Recipients: {recipients}")
print(f"SMTP Server: {SMTP_SERVER}:{SMTP_PORT}")
print(f"Sender: {SENDER_EMAIL}")

# ---------------------------------------------------------------------------
if not trigger_time and os.path.exists("pipeline_time.env"):
    with open("pipeline_time.env", encoding="utf-8") as f:
        for line in f:
            if line.startswith("PIPELINE_TRIGGER_TIME="):
                trigger_time = line.split("=", 1)[1].strip()
                break

print(f"Trigger time: {trigger_time}")
print(f"Report path: {REPORT_PATH}")
print(f"Report exists: {os.path.exists(REPORT_PATH)}")

# ---------------------------------------------------------------------------
msg = MIMEMultipart()
msg["From"] = SENDER_EMAIL
msg["To"] = ", ".join(recipients)
msg["Subject"] = f"Omnia Automation Test Report - {trigger_time}"

html_body = f"""
<html>
<body style="font-family: Arial, sans-serif; margin: 20px;">
    <h2>Omnia Automation Test Report</h2>
    <p><strong>Pipeline Trigger Time:</strong> {trigger_time}</p>
    <p><strong>Pipeline URL:</strong>
        <a href="{pipeline_url}">{pipeline_url}</a></p>
    <br>
    <p>Please find the test report attached.</p>
    <br>
    <p style="color: #888; font-size: 12px;">
        This is an automated email from GitLab CI/CD pipeline.</p>
</body>
</html>
"""
msg.attach(MIMEText(html_body, "html"))

# ---------------------------------------------------------------------------
if os.path.exists(REPORT_PATH):
    try:
        with open(REPORT_PATH, "r", encoding="utf-8") as f:
            report_content = f.read()
        print(f"Read {len(report_content)} characters from report")

        attachment = MIMEText(report_content, "html", "utf-8")
        attachment.add_header(
            "Content-Disposition",
            "attachment",
            filename=REPORT_FILENAME_ONLY,
        )
        msg.attach(attachment)
        print(f"Attached: {REPORT_FILENAME_ONLY}")
    except Exception as e:
        print(f"Error attaching report: {e}")
        traceback.print_exc()
else:
    print(f"Report file not found: {REPORT_PATH}")

# ---------------------------------------------------------------------------
def send_email_with_retry(message, smtp_server, smtp_port, smtp_user, smtp_password, max_retries=3, retry_delay=5):
    """Send email via SMTP with retry logic for reliability."""
    for attempt in range(max_retries):
        try:
            print(f"Send attempt {attempt + 1}/{max_retries}")
            server = smtplib.SMTP(smtp_server, smtp_port, timeout=30)

            if smtp_user and smtp_password:
                server.login(smtp_user, smtp_password)
                print(f"Authenticated as: {smtp_user}")

            server.send_message(message)
            server.quit()
            print(f"Email sent successfully")
            return True

        except smtplib.SMTPException as e:
            print(f"SMTP error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                raise
        except Exception as e:
            print(f"Unexpected error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                raise
    return False

try:
    send_email_with_retry(msg, SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD)
    print("=== Email notification completed successfully ===")
except Exception as e:
    print(f"=== Failed to send email after retries: {e} ===")
    raise
