import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def analyze_with_ai(text: str, url: str) -> dict:
    prompt = f"""
Analyze the following website content.

URL: {url}

Extract the following information and return it strictly in valid JSON format:

{{
  "name": "Company name",
  "industry": "Industry sector",
  "country": "Country if available, otherwise null",
  "city": "City if available, otherwise null",
  "description": "Short description of what the company does",
  "summary": "2-3 sentence concise summary",
  "contact_email": "Email if available, otherwise null"
}}

Rules:
- Return ONLY valid JSON.
- Do NOT include markdown.
- Do NOT include explanations.
- If a field is not found, set it to null.
- Never guess or infer email addresses.
- Only return contact_email if it appears explicitly in the website content.
- If an address is found, extract city and country from the address when possible.
- For Turkish addresses, city is often before "/ TÜRKİYE" or after district information.
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {"role": "system", "content": "You are a strict JSON generator."},
                {"role": "user", "content": prompt + f"\n\nWebsite content:\n{text[:8000]}"}
            ]
        )

        raw_output = response.choices[0].message.content.strip()

        print("AI RAW OUTPUT:", raw_output)

        # JSON parse
        parsed = json.loads(raw_output)

        return parsed

    except json.JSONDecodeError as e:
        print("JSON PARSE ERROR:", e)
        print("RAW OUTPUT:", raw_output)
        return {}

    except Exception as e:
        print("AI ERROR:", e)
        return {}


def generate_manual_email(
    company_name: str | None,
    role: str | None,
    recipient_email: str | None,
    job_description: str | None,
    user_instruction: str | None,
) -> dict:
    full_name = os.getenv("FULL_NAME")
    phone = os.getenv("PHONE_NUMBER")
    email = os.getenv("EMAIL_ADDRESS")
    linkedin = os.getenv("LINKEDIN_URL")

    closing_parts = ["Saygılarımla"]

    if full_name:
        closing_parts.append(full_name)
    if phone:
        closing_parts.append(phone)
    if email:
        closing_parts.append(email)
    if linkedin:
        closing_parts.append(linkedin)

    closing = "\n".join(closing_parts)

    subject = f"{role} Başvurusu" if role else "İş Başvurusu"

    prompt = f"""
You are writing a REALISTIC, short and natural job application email in Turkish.

Company:
{company_name or "Not specified"}

Role:
{role or "Not specified"}

Recipient Email:
{recipient_email or "Not specified"}

Job Description:
{job_description or "Not specified"}

User Instructions:
{user_instruction or "Not specified"}

STRICT RULES:
- Write in Turkish.
- Do NOT use English words.
- Do NOT use placeholders like [Adınız], [Telefon], [Email].
- Do NOT use exaggerated phrases like "tutkum", "heyecan duyuyorum", "değer katacağıma inanıyorum".
- Do NOT sound robotic or AI-generated.
- Do NOT invent experiences, projects, technologies or company details.
- Keep it short, direct and natural.
- Maximum 120 words.
- End EXACTLY with:

{closing}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.5,
        messages=[
            {
                "role": "system",
                "content": "You write short, natural Turkish job application emails. Never use placeholders."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    email_body = response.choices[0].message.content.strip()

    return {
        "subject": subject,
        "body": email_body
    }