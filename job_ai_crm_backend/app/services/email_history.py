from sqlalchemy.orm import Session

from app.models.generated_email import GeneratedEmail


def get_recent_email_patterns(
    db: Session,
    limit: int = 5,
) -> list[str]:
    emails = (
        db.query(GeneratedEmail)
        .order_by(GeneratedEmail.created_at.desc())
        .limit(limit)
        .all()
    )

    patterns = []

    for email in emails:
        if not email.body:
            continue

        body = email.body.strip()
        lines = [line.strip() for line in body.splitlines() if line.strip()]

        opening = lines[0] if lines else ""
        second_line = lines[1] if len(lines) > 1 else ""

        pattern = " ".join([opening, second_line]).strip()

        if pattern:
            patterns.append(pattern[:250])

    return patterns