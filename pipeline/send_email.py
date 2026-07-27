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

Sends a per-cluster email with all stage reports attached via SMTP relay.
Environment variables:
  EMAIL_RECIPIENTS  - comma-separated list of recipient addresses (required)
  EMAIL_SENDER      - sender address (required)
  SMTP_SERVER       - SMTP relay host (required)
  SMTP_PORT         - SMTP relay port (default: 25)
  SMTP_USER         - SMTP username (optional, for authenticated relay)
  SMTP_PASSWORD     - SMTP password (optional, for authenticated relay)
  CLUSTER           - cluster name for this child pipeline
  PIPELINE_TRIGGER_TIME - timestamp from initialization stage
  CI_PIPELINE_URL   - GitLab pipeline URL
"""
import os
import glob
import sys
import time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def load_trigger_time():
    """Load pipeline trigger time from env or file."""
    trigger_time = os.environ.get("PIPELINE_TRIGGER_TIME", "")
    if not trigger_time and os.path.exists("pipeline_time.env"):
        with open("pipeline_time.env", encoding="utf-8") as f:
            for line in f:
                if line.startswith("PIPELINE_TRIGGER_TIME="):
                    trigger_time = line.split("=", 1)[1].strip()
                    break
    return trigger_time


def build_report_list_html(report_files):
    """Build an HTML list of attached report filenames."""
    if not report_files:
        return "<p>No report files found.</p>"
    items = "".join(
        f"<li>{os.path.basename(f)}</li>" for f in sorted(report_files)
    )
    return f"<ul>{items}</ul>"


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


def main():
    recipients = [
        r.strip()
        for r in os.environ.get("EMAIL_RECIPIENTS", "").split(",")
        if r.strip()
    ]
    smtp_server = os.environ.get("SMTP_SERVER", "")
    smtp_port = int(os.environ.get("SMTP_PORT", "25"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_password = os.environ.get("SMTP_PASSWORD", "")
    sender = os.environ.get("EMAIL_SENDER", "")
    cluster = os.environ.get("CLUSTER", "unknown")
    trigger_time = load_trigger_time()
    pipeline_url = os.environ.get("CI_PIPELINE_URL", "")

    # Validate required configuration
    missing = []
    if not recipients:
        missing.append("EMAIL_RECIPIENTS")
    if not smtp_server:
        missing.append("SMTP_SERVER")
    if not sender:
        missing.append("EMAIL_SENDER")
    if missing:
        print(f"Missing required GitLab CI/CD variables: {', '.join(missing)}")
        sys.exit(0)

    print(f"Cluster: {cluster}")
    print(f"Recipients: {recipients}")
    print(f"Sender: {sender}")
    print(f"SMTP Server: {smtp_server}:{smtp_port}")
    print(f"Trigger time: {trigger_time}")
    print(f"Pipeline URL: {pipeline_url}")

    report_files = sorted(glob.glob("final_reports/report_*.html"))
    print(f"Found {len(report_files)} report file(s)")

    subject = f"Omnia Test Report - {cluster} - {trigger_time}"

    # Build email message
    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject

    html_body = f"""<html>
<body style="font-family: Arial, sans-serif; margin: 20px;">
    <h2>Omnia Automation Test Report - {cluster}</h2>
    <p><strong>Cluster:</strong> {cluster}</p>
    <p><strong>Pipeline Trigger Time:</strong> {trigger_time}</p>
    <p><strong>Pipeline URL:</strong> <a href="{pipeline_url}">{pipeline_url}</a></p>
    <br>
    <p><strong>Attached Reports ({len(report_files)}):</strong></p>
    {build_report_list_html(report_files)}
    <br>
    <p style="color: #888; font-size: 12px;">This is an automated email from the Omnia GitLab CI/CD pipeline.</p>
</body>
</html>"""
    msg.attach(MIMEText(html_body, "html"))

    # Attach all report files
    for report in report_files:
        try:
            with open(report, "r", encoding="utf-8") as f:
                report_content = f.read()
            attachment = MIMEText(report_content, "html", "utf-8")
            attachment.add_header(
                "Content-Disposition",
                "attachment",
                filename=os.path.basename(report),
            )
            msg.attach(attachment)
            print(f"Attached: {os.path.basename(report)}")
        except Exception as e:
            print(f"Error attaching {report}: {e}")

    try:
        send_email_with_retry(msg, smtp_server, smtp_port, smtp_user, smtp_password)
        print("=== Email notification completed successfully ===")
    except Exception as e:
        print(f"=== Failed to send email after retries: {e} ===")
        raise


if __name__ == "__main__":
    main()
