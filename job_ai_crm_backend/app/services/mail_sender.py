import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


def _attach_file(msg: EmailMessage, path: str) -> None:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Dosya bulunamadı: {path}")
    with open(path, "rb") as f:
        data = f.read()
    name = os.path.basename(path)
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else "octet-stream"
    subtype = "pdf" if ext == "pdf" else "octet-stream"
    msg.add_attachment(data, maintype="application", subtype=subtype, filename=name)


def send_real_email(
    to_email: str,
    subject: str,
    body: str,
    cv_path: str | None = None,
    extra_attachment_path: str | None = None,
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
        _attach_file(msg, cv_path)

    if extra_attachment_path:
        _attach_file(msg, extra_attachment_path)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(smtp_email, smtp_password)
        smtp.send_message(msg)