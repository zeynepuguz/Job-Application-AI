import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


def send_real_email(
    to_email: str,
    subject: str,
    body: str,
    cv_path: str | None = None
):
    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_APP_PASSWORD")

    if not smtp_email or not smtp_password:
        raise ValueError("SMTP_EMAIL or SMTP_APP_PASSWORD is missing in .env")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_email
    msg["To"] = to_email
    msg.set_content(body)

    if cv_path:
        if not os.path.exists(cv_path):
            raise FileNotFoundError(f"CV file not found: {cv_path}")

        with open(cv_path, "rb") as file:
            file_data = file.read()
            file_name = os.path.basename(cv_path)

        msg.add_attachment(
            file_data,
            maintype="application",
            subtype="pdf",
            filename=file_name
        )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(smtp_email, smtp_password)
        smtp.send_message(msg)