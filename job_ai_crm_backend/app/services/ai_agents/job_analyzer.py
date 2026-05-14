import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def analyze_job(role: str | None, job_description: str | None) -> dict:
    prompt = f"""
Analyze this job application target.

Your job is NOT to write an email.
Your job is to understand the role, company signal and communication style.

Role:
{role or "Not specified"}

Job Description:
{job_description or "Not specified"}

Return ONLY valid JSON.
Do not include markdown.
Do not include explanations.

Analyze:
- role type
- seniority
- main skills
- technical level
- company style
- communication style
- whether this looks like a LinkedIn job post
- whether this looks like startup hiring
- whether this looks like corporate HR hiring

Allowed values:

seniority:
- intern
- junior
- mid
- senior
- unknown

technical_level:
- low
- medium
- high
- unknown

company_style:
- startup
- corporate
- agency
- unknown

communication_style:
- informal
- neutral
- formal

job_post_source:
- linkedin
- website
- email
- unknown

Return EXACTLY this JSON shape:

{{
  "role_type": "backend",
  "seniority": "junior",
  "main_skills": [],
  "technical_level": "medium",
  "tone": "direct",
  "company_style": "unknown",
  "company_culture": "unknown",
  "communication_style": "neutral",
  "job_post_source": "unknown",
  "looks_like_linkedin_post": false,
  "looks_like_startup_hiring": false,
  "looks_like_corporate_hiring": false
}}

Rules:
- If job_description is missing, do not guess.
- If role is missing, use "unknown".
- Do not invent skills.
- main_skills must only include skills explicitly present in role or job_description.
- If the description says remote, fast-paced, early-stage, founder, small team, seed, startup, use startup signals.
- If the description says HR, corporate, department, formal process, career page, use corporate signals.
- If LinkedIn, recruiter, apply, ilan, gönderi, paylaşım appears, set looks_like_linkedin_post true.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You analyze job postings and return only valid JSON."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    content = response.choices[0].message.content.strip()

    try:
        return json.loads(content)
    except Exception as e:
        print("JOB ANALYZER JSON ERROR:", e)
        print("RAW JOB ANALYZER OUTPUT:", content)

        return {
            "role_type": role or "unknown",
            "seniority": "unknown",
            "main_skills": [],
            "technical_level": "unknown",
            "tone": "direct",
            "company_style": "unknown",
            "company_culture": "unknown",
            "communication_style": "neutral",
            "job_post_source": "unknown",
            "looks_like_linkedin_post": False,
            "looks_like_startup_hiring": False,
            "looks_like_corporate_hiring": False,
        }