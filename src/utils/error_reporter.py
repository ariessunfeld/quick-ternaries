import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

def send_error_log_via_email(subject, body):
    sender_email = "jimothy.jimson11@gmail.com"
    receiver_email = "jimothy.jimson11@gmail.com"
    app_password = "ewyzdrbbopjkuggx"

    msg = MIMEMultipart()
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.close()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

