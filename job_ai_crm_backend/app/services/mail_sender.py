import base64
import os
import smtplib
import requests
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()


def _attach_bytes(msg: EmailMessage, data: bytes, filename: str) -> None:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
    subtype = "pdf" if ext == "pdf" else "octet-stream"
    msg.add_attachment(data, maintype="application", subtype=subtype, filename=filename)


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


def _send_via_sendgrid(to_email, subject, body, api_key, from_email, sg_attachments):
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
    smtp_email = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_APP_PASSWORD")
    sendgrid_key = os.getenv("SENDGRID_API_KEY")

    cv_bytes = _build_cv_bytes(cv_file_data, cv_path)

    # --- SendGrid (Railway'de SMTP bloke, bu çalışır) ---
    if sendgrid_key:
        from_email = os.getenv("SENDGRID_FROM_EMAIL") or smtp_email
        if not from_email:
            raise ValueError("SENDGRID_FROM_EMAIL veya SMTP_EMAIL tanımlı değil")

        sg_attachments = []
        if cv_bytes:
            sg_attachments.append({
                "content": base64.b64encode(cv_bytes).decode(),
                "filename": cv_filename,
                "type": "application/pdf",
                "disposition": "attachment",
            })
        if extra_attachment_path and os.path.exists(extra_attachment_path):
            with open(extra_attachment_path, "rb") as f:
                extra_bytes = f.read()
            ext = extra_attachment_path.rsplit(".", 1)[-1].lower()
            sg_attachments.append({
                "content": base64.b64encode(extra_bytes).decode(),
                "filename": os.path.basename(extra_attachment_path),
                "type": "application/pdf" if ext == "pdf" else "application/octet-stream",
                "disposition": "attachment",
            })

        _send_via_sendgrid(to_email, subject, body, sendgrid_key, from_email, sg_attachments)
        return

    # --- SMTP fallback (lokal geliştirme için) ---
    if not smtp_email or not smtp_password:
        raise ValueError("SMTP_EMAIL veya SMTP_APP_PASSWORD eksik")

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = smtp_email
    msg["To"] = to_email
    msg.set_content(body)

    if cv_bytes:
        _attach_bytes(msg, cv_bytes, cv_filename)
    if extra_attachment_path and os.path.exists(extra_attachment_path):
        with open(extra_attachment_path, "rb") as f:
            _attach_bytes(msg, f.read(), os.path.basename(extra_attachment_path))

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(smtp_email, smtp_password)
        smtp.send_message(msg)
