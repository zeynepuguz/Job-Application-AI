import os

PORTFOLIO_KEYWORDS = (
    "portfolio",
    "portföy",
    "portfoy",
    "github",
    "personal website",
    "personal site",
    "web sitesi",
    "website link",
    "work sample",
    "work samples",
    "örnek çalışma",
    "örnek çalışmalar",
    "projeleriniz",
    "çalışmalarınız",
    "showcase",
    "resume link",
    "cv link",
    "online portfolio",
)

PORTFOLIO_INSTRUCTION_KEYWORDS = (
    "portföy",
    "portfolio",
    "portfoy",
    "portföyümü",
    "portfolyo",
    "include portfolio",
    "add portfolio",
    "portföy ekle",
    "portföy link",
)


def job_requests_portfolio(
    job_description: str | None,
    user_instruction: str | None,
) -> bool:
    text = f"{job_description or ''} {user_instruction or ''}".lower()
    return any(keyword in text for keyword in PORTFOLIO_KEYWORDS)


def user_requests_portfolio(user_instruction: str | None) -> bool:
    text = (user_instruction or "").lower()
    return any(keyword in text for keyword in PORTFOLIO_INSTRUCTION_KEYWORDS)


def default_portfolio_url() -> str | None:
    url = (os.getenv("PORTFOLIO_URL") or "").strip()
    return url or None


def resolve_portfolio_url(
    explicit_url: str | None,
    job_description: str | None,
    user_instruction: str | None,
) -> str | None:
    url = (explicit_url or "").strip() or default_portfolio_url()
    if not url:
        return None

    if job_requests_portfolio(job_description, user_instruction):
        return url

    if user_requests_portfolio(user_instruction):
        return url

    return None
