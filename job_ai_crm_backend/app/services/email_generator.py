import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_email(company, cv, role: str, language: str | None) -> dict:
    full_name = os.getenv("FULL_NAME")
    phone = os.getenv("PHONE_NUMBER")
    email = os.getenv("EMAIL_ADDRESS")
    linkedin = os.getenv("LINKEDIN_URL")

    lang = (language or "tr").lower()

    if lang == "en":
        lang_instruction = "Write the email in English."
        closing = f"""Best regards,
{full_name}
{phone}
{email}
{linkedin}"""
        subject = f"{role} Application"
    else:
        lang_instruction = "Write the email in Turkish. DO NOT use any English words."
        closing = f"""Saygılarımla,
{full_name}
{phone}
{email}
{linkedin}"""
        subject = f"{role} Başvurusu"

    prompt = f"""
You are writing a REALISTIC, short and natural email. It must feel like a real human wrote it.

Company:
- Name: {company.name}
- Description: {company.description}

Target Role:
{role}

Language:
- {lang_instruction}

IMPORTANT RULES:
- This is NOT a CV summary.
- Do NOT list experiences.
- Do NOT mention multiple projects.
- Do NOT explain background in detail.
- Do NOT say "I have experience in..." repeatedly.
- Do NOT assume there is a job opening.
- Do NOT sound like a template.

ROLE AWARENESS (VERY IMPORTANT):
- Understand the role carefully.
- If the role includes "backend", mention backend-related interest.
- If the role includes "AI" or "machine learning", mention AI/NLP interest.
- If both exist, combine them naturally (1 short phrase only).
- Do NOT ignore parts of the role.
- Do NOT over-explain, just hint.

WHAT TO DO:
- Write a short message (80–120 words max)
- Mention the company briefly (1 sentence)
- Say you are interested in working in this role area
- Mention ONLY ONE small relevant skill or focus area based on the role
- Ask if there could be a suitable opportunity
- Keep it simple and natural

STYLE RULES:
- Avoid overly emotional phrases (like "heyecanlandırıyor", "çok isterim")
- Avoid weak question forms like "acaba uygun bir fırsat var mı?"
- Use more confident wording
- Keep sentences clean and direct

TONE:
- Calm
- Natural
- Slightly informal but respectful
- Not robotic
- Not overly enthusiastic

STRUCTURE:
- Greeting
- 2 short paragraphs
- Closing

End EXACTLY with:

{closing}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.6,
        messages=[
            {
                "role": "system",
                "content": "You write very natural, short, human-like emails. Never write like AI."
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