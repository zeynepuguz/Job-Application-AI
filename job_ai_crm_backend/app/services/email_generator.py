import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def generate_email(
    company,
    cv,
    role: str,
    language: str | None,
    user_instruction: str | None = None,
) -> dict:
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

    extra = (user_instruction or "").strip()
    extra_block = (
        f"\n\nCandidate preferences (follow if compatible; do not invent facts):\n{extra}\n"
        if extra
        else ""
    )

    cv_snippet = (cv.content_text or "")[:3000].strip()

    prompt = f"""
You are writing a REALISTIC, short and natural email. It must feel like a real human wrote it.

Company:
- Name: {company.name}
- Description: {company.description}

Target Role:
{role}

Candidate CV (use this to pick ONE genuine skill to mention):
{cv_snippet}

Language:
- {lang_instruction}
{extra_block}

IMPORTANT RULES:
- This is NOT a CV summary.
- Do NOT list experiences.
- Do NOT mention multiple projects.
- Do NOT explain background in detail.
- Do NOT say "I have experience in..." repeatedly.
- Do NOT assume there is a job opening.
- Do NOT sound like a template.

SKILL SELECTION (VERY IMPORTANT):
- Read the CV carefully and find the ONE skill or experience that best matches the target role "{role}".
- Do NOT default to any specific technology — pick what is actually in the CV and fits the role.
- Do NOT paraphrase or expand the role title. The role is exactly: "{role}".
- Keep it to 1 short phrase. Do NOT over-explain.

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

    closing = f"""Saygılarımla,
{full_name}
{phone}
{email}
{linkedin}"""

    subject = (
        f"{role} Başvurusu"
        if role
        else "İş Başvurusu"
    )

    prompt = f"""
You are writing a REALISTIC, short and natural job application email.

IMPORTANT:
- The email MUST feel human-written.
- Never sound robotic or AI-generated.
- Avoid exaggerated enthusiasm.
- Avoid generic corporate phrases.

Application Information:

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
- Do NOT use phrases like:
  - "tutkum"
  - "beni heyecanlandırıyor"
  - "değer katacağıma inanıyorum"
  - "dinamik ekibiniz"
  - "vizyonunuz"
- Do NOT sound emotional.
- Keep confidence calm and natural.
- Keep the email SHORT.
- Maximum 120 words.
- Do NOT invent experiences.
- Do NOT invent technologies.
- If job description exists, adapt naturally.
- If user instruction exists, prioritize it.
- Never use placeholders like:
  [Adınız]
  [Telefon]
  [Email]

STYLE:
- clean
- direct
- modern
- realistic
- human

STRUCTURE:
- greeting
- 1-2 short paragraphs
- short closing

End EXACTLY with:

{closing}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.5,
        messages=[
            {
                "role": "system",
                "content": "You write extremely natural Turkish application emails. Never sound like AI."
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