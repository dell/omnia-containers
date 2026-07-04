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

"""Email notification script for Omnia GitLab CI/CD pipeline."""
import subprocess
import os
import glob
import base64

# Email sending logic
recipients = [
    r.strip()
    for r in os.environ.get("EMAIL_RECIPIENTS", "").split(",")
    if r.strip()
]
trigger_time = os.environ.get("PIPELINE_TRIGGER_TIME", "")
pipeline_url = os.environ.get("CI_PIPELINE_URL", "")
print(f"EMAIL_RECIPIENTS value: {os.environ.get('EMAIL_RECIPIENTS', '')}")
print(f"Recipients list: {recipients}")
print(f"PIPELINE_TRIGGER_TIME value: {trigger_time}")
print(f"CI_PIPELINE_URL value: {pipeline_url}")
if not trigger_time and os.path.exists("pipeline_time.env"):
    with open("pipeline_time.env", encoding="utf-8") as f:
        for line in f:
            if line.startswith("PIPELINE_TRIGGER_TIME="):
                trigger_time = line.split("=", 1)[1].strip()
                break
print(f"Final trigger_time: {trigger_time}")
report_files = glob.glob("final_reports/test_report_*.html")
if report_files:
    REPORT_FILENAME = report_files[0]
else:
    REPORT_FILENAME = "final_reports/test_report.html"
print(f"Report filename: {REPORT_FILENAME}")
REPORT_FILENAME_ONLY = os.path.basename(REPORT_FILENAME)
# Read the report file
if os.path.exists(REPORT_FILENAME):
    with open(REPORT_FILENAME, "r", encoding="utf-8") as f:
        report_content = f.read()

    # Encode content in base64
    encoded_content = base64.b64encode(
        report_content.encode()
    ).decode()

    # Create email with attachment
    BOUNDARY = "==boundary=="
    email_body = f"""From:
To: {", ".join(recipients)}
Subject: Omnia Automation Test Report - {trigger_time}
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="{BOUNDARY}"
--{BOUNDARY}
Content-Type: text/html; charset=UTF-8
<html>
<body style="font-family: Arial, sans-serif; margin: 20px;">
    <h2>Omnia Automation Test Report</h2>
    <p><strong>Pipeline Trigger Time:</strong> {trigger_time}</p>
    <p><strong>Pipeline URL:</strong> \
<a href="{pipeline_url}">{pipeline_url}</a></p>
    <br>
    <p>Please find the test report attached.</p>
    <br>
    <p style="color: #888; font-size: 12px;">\
This is an automated email from GitLab CI/CD pipeline.</p>
</body>
</html>
--{BOUNDARY}
Content-Type: text/html; name="{REPORT_FILENAME_ONLY}"
Content-Transfer-Encoding: base64
Content-Disposition: attachment; filename="{REPORT_FILENAME_ONLY}"
{encoded_content}
--{BOUNDARY}--
"""
else:
    print(f"Report file not found: {REPORT_FILENAME}")
    # Fallback to link - use summary job artifacts
    ci_server_url = os.environ.get("CI_SERVER_URL", "")
    ci_project_path = os.environ.get("CI_PROJECT_PATH", "")
    ci_job_id = os.environ.get("CI_JOB_ID", "")
    REPORT_URL = (
        f"{ci_server_url}/{ci_project_path}"
        f"/-/jobs/{ci_job_id}/artifacts/raw"
        f"/final_reports/{os.path.basename(REPORT_FILENAME)}"
    )
    print(f"CI_SERVER_URL: {ci_server_url}")
    print(f"CI_PROJECT_PATH: {ci_project_path}")
    print(f"CI_JOB_ID: {ci_job_id}")
    print(f"Generated report URL: {REPORT_URL}")

    email_body = f"""From:
To: {", ".join(recipients)}
Subject: Omnia Automation Test Report - {trigger_time}
MIME-Version: 1.0
Content-Type: text/html; charset=UTF-8
<html>
<body style="font-family: Arial, sans-serif; margin: 20px;">
    <h2>Omnia Automation Test Report</h2>
    <p><strong>Pipeline Trigger Time:</strong> {trigger_time}</p>
    <p><strong>Pipeline URL:</strong> \
<a href="{pipeline_url}">{pipeline_url}</a></p>
    <br>
    <p><a href="{REPORT_URL}">{REPORT_FILENAME_ONLY}</a></p>
    <br>
    <p style="color: #888; font-size: 12px;">\
This is an automated email from GitLab CI/CD pipeline.</p>
</body>
</html>
"""
try:
    with subprocess.Popen(
        ["/usr/sbin/sendmail", "-t"], stdin=subprocess.PIPE
    ) as process:
        process.communicate(email_body.encode())
    print(f"Email sent successfully to: {', '.join(recipients)}")
except subprocess.SubprocessError as e:
    print(f"Failed to send email: {e}")
