import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def refine_email(
    current_subject: str,
    current_body: str,
    instruction: str
) -> dict:

    prompt = f"""
You are rewriting a job application email from scratch.

Current email:
{current_body}

User instruction:
{instruction}

VERY IMPORTANT:
- Do NOT lightly edit the email.
- Completely rewrite the email from scratch.
- Follow the user instruction strictly.
- Change tone, structure, and wording if needed.

Rules:
- Keep it natural and human-like
- Do not sound like AI
- Do not list experiences like a CV
- Keep it short (80–120 words)
- Do not include subject inside the body
- Keep signature if exists

Return ONLY the new email body.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.5,
        messages=[
            {
                "role": "system",
                "content": "You rewrite job application emails based on user feedback."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    refined_body = response.choices[0].message.content.strip()

    return {
        "subject": current_subject,
        "body": refined_body
    }