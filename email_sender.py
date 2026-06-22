import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PASSWORD = os.getenv('SENDER_PASSWORD')

def send_report_email(user_name, user_email, report_data):
    if not SENDER_EMAIL or not SENDER_PASSWORD:
        print("Email credentials not configured. Skipping email send.")
        return False

    msg = MIMEMultipart("alternative")
    msg['Subject'] = f"Your SysDiag Pro Report — {report_data['time']['date']}"
    msg['From'] = f"SysDiag Pro <{SENDER_EMAIL}>"
    msg['To'] = user_email

    issues_html = ""
    if report_data['issues']:
        issues_html = "<h3 style='color: #EC4899;'>Issues Found:</h3><ul>"
        for i, issue in enumerate(report_data['issues']):
            issues_html += f"<li><strong style='color: #ff4444;'>{issue}</strong> - <span style='color: #00ff88;'>{report_data['fixes'][i]}</span></li>"
        issues_html += "</ul>"
    else:
        issues_html = "<h3 style='color: #00ff88;'>No issues found. Your system is running smoothly!</h3>"

    sec_score = report_data['security']['score']
    sec_color = "#ff4444"
    if sec_score > 40: sec_color = "#ffd700"
    if sec_score > 70: sec_color = "#7C3AED"
    if sec_score > 90: sec_color = "#00ff88"

    html_content = f"""
    <html>
    <head>
    <style>
        body {{ font-family: 'Inter', Arial, sans-serif; background-color: #F9F7FF; color: #1F2937; }}
        .container {{ max-width: 600px; margin: 0 auto; background: #FFFFFF; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }}
        .header {{ text-align: center; border-bottom: 2px solid #7C3AED; padding-bottom: 10px; margin-bottom: 20px; }}
        .header h1 {{ color: #7C3AED; }}
        .metric-table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        .metric-table th, .metric-table td {{ border: 1px solid #E5E7EB; padding: 10px; text-align: left; }}
        .metric-table th {{ background-color: #F3F4F6; color: #4B5563; }}
        .sec-score {{ font-size: 24px; font-weight: bold; color: {sec_color}; }}
        .footer {{ text-align: center; margin-top: 30px; font-size: 12px; color: #9CA3AF; }}
        .btn {{ background-color: #EC4899; color: white; padding: 10px 15px; text-decoration: none; border-radius: 5px; display: inline-block; margin-top: 10px;}}
    </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>SysDiag Pro Report</h1>
            </div>
            <p>Hello <strong>{user_name}</strong>,</p>
            <p>Your system scan was completed on {report_data['time']['date']} at {report_data['time']['time']}. Here is your report summary:</p>
            
            <table class="metric-table">
                <tr><th>Metric</th><th>Value</th></tr>
                <tr><td>Security Score</td><td class="sec-score">{sec_score}/100</td></tr>
                <tr><td>CPU Usage</td><td>{report_data['cpu']['usage']}%</td></tr>
                <tr><td>RAM Usage</td><td>{report_data['ram']['usage_percent']}%</td></tr>
                <tr><td>Disk Usage</td><td>{report_data['disk']['usage_percent']}%</td></tr>
                <tr><td>Network Status</td><td>{report_data['network']['status']}</td></tr>
                <tr><td>OS</td><td>{report_data['os']['name_version']}</td></tr>
            </table>

            {issues_html}

            <div style="text-align: center;">
                <a href="http://127.0.0.1:5000/dashboard" class="btn">View Full Report Online</a>
            </div>

            <div class="footer">
                <p>SysDiag Pro &copy; 2026. Automated System Diagnostic tool.</p>
            </div>
        </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(html_content, 'html'))

    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.sendmail(SENDER_EMAIL, user_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
