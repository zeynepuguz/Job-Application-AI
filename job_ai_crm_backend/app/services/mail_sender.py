import base64
import os
import smtplib
from email.message import EmailMessage
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()


def _build_cv_bytes(cv_file_data, cv_path):
    if cv_file_data:
        try:
            return base64.b64decode(cv_file_data)
        except Exception:
            pass
    if cv_path and os.path.exists(cv_path):
        with open(cv_path, "rb") as f:
            return f.read()
    return None


def _send_via_gmail_api(to_email, subject, body, client_id, client_secret, refresh_token, attachments):
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    creds = Credentials(
        token=None,
        refresh_token=refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/gmail.send"],
    )
    creds.refresh(Request())

    msg = MIMEMultipart()
    msg["to"] = to_email
    msg["subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    for data, filename in attachments:
        part = MIMEApplication(data, Name=filename)
        part["Content-Disposition"] = f'attachment; filename="{filename}"'
        msg.attach(part)

    raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
    service = build("gmail", "v1", credentials=creds)
    service.users().messages().send(userId="me", body={"raw": raw}).execute()


def _send_via_sendgrid(to_email, subject, body, api_key, from_email, attachments):
    import requests

    sg_attachments = []
    for data, filename in attachments:
        ext = filename.rsplit(".", 1)[-1].lower()
        sg_attachments.append({
            "content": base64.b64encode(data).decode(),
            "filename": filename,
            "type": "application/pdf" if ext == "pdf" else "application/octet-stream",
            "disposition": "attachment",
        })

    payload = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}],
    }
    if sg_attachments:
        payload["attachments"] = sg_attachments

    resp = requests.post(
        "https://api.sendgrid.com/v3/mail/send",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    if resp.status_code not in (200, 202):
        raise ValueError(f"SendGrid error {resp.status_code}: {resp.text}")


def send_real_email(
    to_email: str,
    subject: str,
    body: str,
    cv_path: str | None = None,
    extra_attachment_path: str | None = None,
    cv_file_data: str | None = None,
    cv_filename: str = "CV.pdf",
):
    cv_bytes = _build_cv_bytes(cv_file_data, cv_path)

    attachments = []
    if cv_bytes:
        attachments.append((cv_bytes, cv_filename))
    if extra_attachment_path and os.path.exists(extra_attachment_path):
        with open(extra_attachment_path, "rb") as f:
            attachments.append((f.read(), os.path.basename(extra_attachment_path)))

    gmail_client_id = os.getenv("GMAIL_CLIENT_ID")
    gmail_client_secret = os.getenv("GMAIL_CLIENT_SECRET")
    gmail_refresh_token = os.getenv("GMAIL_REFRESH_TOKEN")

    if gmail_client_id and gmail_client_secret and gmail_refresh_token:
        _send_via_gmail_api(
            to_email=to_email,
            subject=subject,
            body=body,
            client_id=gmail_client_id,
            client_secret=gmail_client_secret,
            refresh_token=gmail_refresh_token,
            attachments=attachments,
        )
        return

    # SendGrid fallback
    sendgrid_key = os.getenv("SENDGRID_API_KEY")
    smtp_email = os.getenv("SMTP_EMAIL")
    if sendgrid_key:
        from_email = os.getenv("SENDGRID_FROM_EMAIL") or smtp_email
        if not from_email:
            raise ValueError("SENDGRID_FROM_EMAIL veya SMTP_EMAIL tanımlı değil")
        _send_via_sendgrid(to_email, subject, body, sendgrid_key, from_email, attachments)
        return

    # SMTP fallback (lokal geliştirme)
    smtp_password = os.getenv("SMTP_APP_PASSWORD")
    if not smtp_email or not smtp_password:
        raise ValueError("SMTP_EMAIL veya SMTP_APP_PASSWORD eksik")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_email
    msg["To"] = to_email
    msg.set_content(body)
    for data, filename in attachments:
        ext = filename.rsplit(".", 1)[-1].lower()
        msg.add_attachment(data, maintype="application",
                           subtype="pdf" if ext == "pdf" else "octet-stream",
                           filename=filename)

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(smtp_email, smtp_password)
        smtp.send_message(msg)
