from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import ssl
import smtplib
import json

CONFIG_FILE = "config.json"

def send_email(receiver, fileName):
    with open(CONFIG_FILE, "r", encoding="utf-8") as conf:
        config = json.load(conf)
    print(config)
    email_sender = config["EmailId"]
    email_password = config["Password"]
    subject = "Generated Report"
    body= """
    Please find attached generated report
    """
    
    em = MIMEMultipart()
    em['From'] = email_sender
    em['To'] = receiver
    em['subject'] = subject
    
    em.attach(MIMEText(body, "plain"))
    
    attachment_name = fileName
    attach_file = open(attachment_name, "rb")
    payload = MIMEBase("application", "octate-stream")
    payload.set_payload((attach_file).read())
    encoders.encode_base64(payload)
    payload.add_header("Content-Decomposition", "attachment", filename=fileName)
    em.attach(payload)

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender,email_password)
        smtp.sendmail(email_sender, receiver, em.as_string())


