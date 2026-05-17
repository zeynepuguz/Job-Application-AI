import base64
import os
import smtplib
import tempfile
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


def _attach_bytes(msg: EmailMessage, data: bytes, filename: str) -> None:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    subtype = "pdf" if ext == "pdf" else "octet-stream"
    msg.add_attachment(data, maintype="application", subtype=subtype, filename=filename)


def send_real_email(
    to_email: str,
    subject: str,
    body: str,
    cv_path: str | None = None,
    extra_attachment_path: str | None = None,
    cv_file_data: str | None = None,  # base64-encoded PDF from DB
    cv_filename: str = "CV.pdf",
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

    # CV eki: önce DB'den (base64), yoksa disk yolundan, ikisi de yoksa eklentisiz gönder
    if cv_file_data:
        try:
            _attach_bytes(msg, base64.b64decode(cv_file_data), cv_filename)
        except Exception:
            pass
    elif cv_path and os.path.exists(cv_path):
        with open(cv_path, "rb") as f:
            _attach_bytes(msg, f.read(), os.path.basename(cv_path))

    if extra_attachment_path and os.path.exists(extra_attachment_path):
        with open(extra_attachment_path, "rb") as f:
            _attach_bytes(msg, f.read(), os.path.basename(extra_attachment_path))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as smtp:
        smtp.login(smtp_email, smtp_password)
        smtp.send_message(msg)
