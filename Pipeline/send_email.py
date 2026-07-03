import subprocess
import os
import glob
import base64
# Email sending logic
recipients = [r.strip() for r in os.environ.get("EMAIL_RECIPIENTS", "").split(",") if r.strip()]
trigger_time = os.environ.get("PIPELINE_TRIGGER_TIME", "")
pipeline_url = os.environ.get("CI_PIPELINE_URL", "")
print(f"EMAIL_RECIPIENTS value: {os.environ.get('EMAIL_RECIPIENTS', '')}")
print(f"Recipients list: {recipients}")
print(f"PIPELINE_TRIGGER_TIME value: {trigger_time}")
print(f"CI_PIPELINE_URL value: {pipeline_url}")
if not trigger_time and os.path.exists("pipeline_time.env"):
    with open("pipeline_time.env") as f:
        for line in f:
            if line.startswith("PIPELINE_TRIGGER_TIME="):
                trigger_time = line.split("=", 1)[1].strip()
                break
print(f"Final trigger_time: {trigger_time}")
report_files = glob.glob("final_reports/test_report_*.html")
if report_files:
    report_filename = report_files[0]
else:
    report_filename = "final_reports/test_report.html"
print(f"Report filename: {report_filename}")
report_filename_only = os.path.basename(report_filename)
# Read the report file
if os.path.exists(report_filename):
    with open(report_filename, "r") as f:
        report_content = f.read()
    
    # Encode content in base64
    encoded_content = base64.b64encode(report_content.encode()).decode()
    
    # Create email with attachment
    boundary = "==boundary=="
    email_body = f"""From: 
To: {", ".join(recipients)}
Subject: Omnia Automation Test Report - {trigger_time}
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="{boundary}"
--{boundary}
Content-Type: text/html; charset=UTF-8
<html>
<body style="font-family: Arial, sans-serif; margin: 20px;">
    <h2>Omnia Automation Test Report</h2>
    <p><strong>Pipeline Trigger Time:</strong> {trigger_time}</p>
    <p><strong>Pipeline URL:</strong> <a href="{pipeline_url}">{pipeline_url}</a></p>
    <br>
    <p>Please find the test report attached.</p>
    <br>
    <p style="color: #888; font-size: 12px;">This is an automated email from GitLab CI/CD pipeline.</p>
</body>
</html>
--{boundary}
Content-Type: text/html; name="{report_filename_only}"
Content-Transfer-Encoding: base64
Content-Disposition: attachment; filename="{report_filename_only}"
{encoded_content}
--{boundary}--
"""
else:
    print(f"Report file not found: {report_filename}")
    # Fallback to link - use summary job artifacts
    ci_server_url = os.environ.get("CI_SERVER_URL", "")
    ci_project_path = os.environ.get("CI_PROJECT_PATH", "")
    ci_job_id = os.environ.get("CI_JOB_ID", "")
    report_url = f"{ci_server_url}/{ci_project_path}/-/jobs/{ci_job_id}/artifacts/raw/final_reports/{os.path.basename(report_filename)}"
    print(f"CI_SERVER_URL: {ci_server_url}")
    print(f"CI_PROJECT_PATH: {ci_project_path}")
    print(f"CI_JOB_ID: {ci_job_id}")
    print(f"Generated report URL: {report_url}")
    
    email_body = f"""From:
To: {", ".join(recipients)}
Subject: Omnia Automation Test Report - {trigger_time}
MIME-Version: 1.0
Content-Type: text/html; charset=UTF-8
<html>
<body style="font-family: Arial, sans-serif; margin: 20px;">
    <h2>Omnia Automation Test Report</h2>
    <p><strong>Pipeline Trigger Time:</strong> {trigger_time}</p>
    <p><strong>Pipeline URL:</strong> <a href="{pipeline_url}">{pipeline_url}</a></p>
    <br>
    <p><a href="{report_url}">{report_filename_only}</a></p>
    <br>
    <p style="color: #888; font-size: 12px;">This is an automated email from GitLab CI/CD pipeline.</p>
</body>
</html>
"""
try:
    process = subprocess.Popen(["/usr/sbin/sendmail", "-t"], stdin=subprocess.PIPE)
    process.communicate(email_body.encode())
    print(f"Email sent successfully to: {', '.join(recipients)}")
except Exception as e:
    print(f"Failed to send email: {e}")
