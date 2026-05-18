import re
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup


CONTACT_KEYWORDS = [
    "iletisim",
    "iletişim",
    "contact",
    "about",
    "hakkimizda",
    "hakkımızda",
    "kurumsal",
    "ofis",
    "ofislerimiz",
    "kariyer",
    "career",
    "careers",
]


def normalize_url(url: str) -> str:
    if not url.startswith("http"):
        url = "https://" + url

    parsed = urlparse(url)
    netloc = parsed.netloc.replace("www.", "")

    return f"{parsed.scheme}://{netloc}".rstrip("/")


def extract_emails(text: str) -> list[str]:
    emails = re.findall(
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        text
    )
    return list(dict.fromkeys(emails))


def choose_best_email(emails: list[str]) -> str | None:
    preferred_emails = [
        email for email in emails
        if "iletisim" in email.lower()
        or "contact" in email.lower()
        or "info" in email.lower()
    ]

    if preferred_emails:
        return preferred_emails[0]

    if emails:
        return emails[0]

    return None


def fetch_single_page_text(url: str) -> tuple[str, list[str]]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    response = requests.get(url, headers=headers, timeout=15)
    response.raise_for_status()

    raw_html = response.text
    soup = BeautifulSoup(raw_html, "html.parser")

    discovered_links = []
    mailto_emails = []

    for a in soup.find_all("a", href=True):
        href = a["href"]
        link_text = a.get_text(" ", strip=True)
        combined = f"{href} {link_text}".lower()

        if href.lower().startswith("mailto:"):
            email_part = href[7:].split("?")[0].strip()
            if email_part:
                mailto_emails.append(email_part)

        if any(keyword in combined for keyword in CONTACT_KEYWORDS):
            discovered_links.append(href)

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    visible_text = soup.get_text(separator=" ")
    visible_text = re.sub(r"\s+", " ", visible_text).strip()

    mailto_block = " ".join(mailto_emails)
    combined_text = mailto_block + " " + visible_text + " " + raw_html

    return combined_text, discovered_links


def fetch_website_text(url: str) -> str:
    base_url = normalize_url(url)

    candidate_paths = [
        "",
        "/iletisim",
        "/contact",
        "/contact-us",
        "/about",
        "/about-us",
        "/hakkimizda",
        "/kurumsal",
        "/kurumsal/iletisim",
        "/ofislerimiz",
        "/kariyer",
        "/career",
        "/careers",
        "/tr",
        "/tr/iletisim",
        "/tr/hakkimizda",
        "/tr/kurumsal",
        "/tr/ofislerimiz",
        "/tr/kariyer",
    ]

    all_texts = []
    discovered_links = []

    for path in candidate_paths:
        page_url = urljoin(base_url + "/", path.lstrip("/"))

        try:
            page_text, links = fetch_single_page_text(page_url)

            if page_text:
                all_texts.append(f"\n\nPAGE URL: {page_url}\n{page_text}")

            discovered_links.extend(links)

        except Exception as e:
            print(f"Could not fetch {page_url}: {e}")

    unique_links = list(dict.fromkeys(discovered_links))

    print("DISCOVERED LINKS:")
    for link in unique_links:
        print(urljoin(base_url + "/", link))

    for link in unique_links[:20]:
        page_url = urljoin(base_url + "/", link)

        try:
            page_text, _ = fetch_single_page_text(page_url)

            if page_text:
                all_texts.append(f"\n\nDISCOVERED PAGE URL: {page_url}\n{page_text}")

        except Exception as e:
            print(f"Could not fetch discovered link {page_url}: {e}")

    combined_text = "\n".join(all_texts)

    emails = extract_emails(combined_text)

    print("EMAILS FOUND:", emails)
    print("TEXT LENGTH:", len(combined_text))

    email_block = "\n".join([f"FOUND EMAIL: {email}" for email in emails])

    return f"{email_block}\n\n{combined_text}"[:50000]


def extract_city_from_text(text: str) -> str | None:
    lower_text = text.lower()

    if "kocaeli" in lower_text:
        return "Kocaeli"

    if "gebze" in lower_text:
        return "Gebze"

    if "istanbul" in lower_text:
        return "İstanbul"

    if "ankara" in lower_text:
        return "Ankara"

    if "izmir" in lower_text:
        return "İzmir"

    return None


def extract_country_from_text(url: str, text: str) -> str | None:
    lower_text = text.lower()

    if ".com.tr" in url or "türkiye" in lower_text or "turkey" in lower_text:
        return "Türkiye"

    return None


def extract_company_data_from_text(url: str, text: str) -> dict:
    emails = extract_emails(text)
    contact_email = choose_best_email(emails)

    clean_name = (
        normalize_url(url)
        .replace("https://", "")
        .replace("http://", "")
        .replace("www.", "")
        .split("/")[0]
    )

    normalized_url = normalize_url(url)

    return {
        "name": clean_name,
        "website": normalized_url,
        "source_url": normalized_url,
        "country": extract_country_from_text(normalized_url, text),
        "city": extract_city_from_text(text),
        "work_mode": None,
        "contact_email": contact_email,
        "industry": None,
        "description": text[:1000],
        "ai_summary": text[:700],
    }