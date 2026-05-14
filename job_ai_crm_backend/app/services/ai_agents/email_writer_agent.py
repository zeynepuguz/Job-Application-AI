import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def write_email(
    company_name,
    role,
    strategy,
    user_instruction,
    previous_email=None,
    rewrite_reason=None,
    rewrite_issues=None,
    review_issue_types=None,
    memory=None,
    recent_email_patterns=None,
    allowed_experience=None,
):
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

    max_length = (strategy or {}).get("max_length", "short")

    word_limit = 100

    if max_length == "ultra_short":
        word_limit = 60
    elif max_length == "short":
        word_limit = 100
    elif max_length == "medium":
        word_limit = 140

    email_type = (strategy or {}).get("email_type", "cold_outreach")
    style = (strategy or {}).get("style", "neutral")

    prompt = f"""
Write a short, natural Turkish job application / outreach email.

Return ONLY the email body.
Do not include subject.
Do not include markdown.

Company:
{company_name or "Not specified"}

Role:
{role or "Not specified"}

User Instruction:
{user_instruction or "None"}

Email Strategy:
{json.dumps(strategy or {}, ensure_ascii=False)}

User Memory:
{json.dumps(memory or {}, ensure_ascii=False)}

Previous Email:
{previous_email or "None"}

Rewrite Reason:
{rewrite_reason or "None"}

Rewrite Issues:
{json.dumps(rewrite_issues or [], ensure_ascii=False)}

Rewrite Issue Types:
{json.dumps(review_issue_types or [], ensure_ascii=False)}

Recent Email Patterns:
{json.dumps(recent_email_patterns or [], ensure_ascii=False)}

ALLOWED EXPERIENCE ONLY:
{json.dumps(allowed_experience or [], ensure_ascii=False)}

CORE RULES:
- Write in Turkish.
- Keep it short.
- Maximum {word_limit} words.
- Sound like a real person.
- Do not sound like AI.
- Do not write a motivation letter.
- Do not write a CV summary.
- Do not over-explain.
- Do not use exaggerated praise.
- Do not use generic corporate compliments.
- Do not invent anything.

STRICT EXPERIENCE RULES:
- You may ONLY mention technologies, skills, projects, tools, experience or achievements that appear in ALLOWED EXPERIENCE ONLY.
- If ALLOWED EXPERIENCE ONLY is empty, do not mention any technology, skill, project, tool, experience, achievement, expertise or knowledge level.
- The role title is NOT evidence of experience.
- The job description is NOT evidence of user qualifications.
- Job requirements are NOT user skills.
- Never infer Python, React, FastAPI, AI, ML or any other technology from the role title.
- If no experience is explicitly allowed, keep the email interest-based only.

JOB POST RULES:
- Do not say "ilanınızı gördüm" unless job_description or strategy clearly says there is a job post.
- Do not mention LinkedIn unless strategy email_type is "linkedin_recruiter_mail".
- If job_description is missing, do not imply that there is an active job posting.

STYLE RULES:
- If email_type is "cold_outreach", write a direct short outreach email.
- If email_type is "linkedin_recruiter_mail", briefly mention the LinkedIn post.
- If email_type is "startup_founder_mail", sound direct, short and non-corporate.
- If email_type is "corporate_hr_mail", sound professional but concise.
- If confidence_score is low, keep wording neutral and safe.
- Avoid repeating openings from Recent Email Patterns.

REWRITE RULES:
- If Previous Email exists, rewrite it by fixing Rewrite Issues.
- If issue type includes hallucinated_experience, remove all unsupported experience claims.
- If issue type includes cv_summary, make it shorter and outreach-like.
- If issue type includes ai_tone or robotic_tone, use simpler Turkish.
- If issue type includes too_long, shorten aggressively.

FORBIDDEN:
- Do not use placeholders like [Adınız].
- Do not say "tutkum".
- Do not say "heyecan duyuyorum".
- Do not say "değer katacağıma inanıyorum".
- Do not say "katkı sağlamak".
- Do not say "dinamik ekibiniz".
- Do not say "vizyonunuz".
- Do not say "kendimi geliştirmek".
- Do not say "başarılı".
- Do not say "projeler geliştirdim" unless explicitly allowed.
- Do not say "Python üzerinde çalışıyorum" unless explicitly allowed.
- Do not say "bilgi sahibiyim" unless explicitly allowed.

End EXACTLY with:

{closing}
"""

    temperature = 0.35

    if email_type == "corporate_hr_mail":
        temperature = 0.25
    elif email_type == "startup_founder_mail":
        temperature = 0.55
    elif email_type in ["cold_outreach", "linkedin_recruiter_mail"]:
        temperature = 0.45
    elif style == "startup":
        temperature = 0.5

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=temperature,
        messages=[
            {
                "role": "system",
                "content": (
                    "You write short, realistic Turkish job application emails. "
                    "You only use information explicitly provided by the user. "
                    "You never infer skills, technologies, projects or experience from a role title."
                )
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.choices[0].message.content.strip()