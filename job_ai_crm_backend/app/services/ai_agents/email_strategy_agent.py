import json
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def build_email_strategy(job_context: dict, memory: dict | None = None) -> dict:
    memory = memory or {}

    prompt = f"""
You are an email strategy agent for a job application email generator.

Your job is NOT to write the email.
Your job is to decide the best email strategy.

Return ONLY valid JSON.
Do not include markdown.
Do not include explanations.

Job Context:
{json.dumps(job_context, ensure_ascii=False)}

User AI Memory:
{json.dumps(memory, ensure_ascii=False)}

Analyze these signals:
- company_name
- role
- job_description
- recipient_email
- source
- user_instruction
- job_analysis

Choose the most suitable strategy.

EMAIL TYPE OPTIONS:
- cold_outreach
- linkedin_recruiter_mail
- direct_hiring_mail
- startup_founder_mail
- corporate_hr_mail

STYLE OPTIONS:
- startup
- corporate
- neutral

TONE OPTIONS:
- direct
- warm
- professional
- concise

DETECTION RULES:
- If source includes LinkedIn or job_description looks like a LinkedIn job post, use linkedin_recruiter_mail.
- If recipient_email contains hr, ik, humanresources, recruitment, recruiter, careers, jobs, talent, use corporate_hr_mail.
- If recipient_email contains founder, cofounder, ceo, cto, use startup_founder_mail.
- If only email and role are provided, use cold_outreach.
- If company_name is missing, do not rely on company-specific personalization.
- If job_description is missing, do not mention job post details.
- If user_instruction exists, prioritize it.
- If the role or job description feels startup-like, prefer startup style.
- If it feels formal, enterprise or HR-like, prefer corporate style.

QUALITY RULES:
- Prefer short emails.
- Prefer direct tone.
- Avoid motivation letter style.
- Avoid generic compliments.
- Avoid AI-like polite phrases.
- Avoid exaggerated motivation.
- Avoid invented experience.
- Avoid CV-summary style.

JOB ANALYSIS SIGNALS:

- If company_style is "startup", prefer startup style.
- If communication_style is "informal", prefer direct tone.

- If looks_like_startup_hiring is true, prefer:
  - startup_founder_mail
  - direct tone
  - short length

- If looks_like_corporate_hiring is true, prefer:
  - corporate_hr_mail
  - professional tone
  - structured writing

- If looks_like_linkedin_post is true:
  - use linkedin_recruiter_mail
  - mention the job listing naturally

- If technical_level is high:
  - slightly increase technical specificity
  - but never become CV-summary style

confidence_score:
- Float between 0 and 1.
- Shows how confident you are in the selected email strategy.
- If only weak signals exist, use 0.4-0.6.
- If recipient email or job post clearly indicates the email type, use 0.7-0.9.
- If company style is unclear, do not use high confidence.

Return EXACTLY this JSON shape:

{{
  "tone": "direct",
  "style": "startup",
  "email_type": "cold_outreach",
  "max_length": "short",
  "avoid_generic_phrases": true,
  "avoid_motivation_letter_style": true,
  "avoid_cv_summary_style": true,
  "avoid_exaggerated_motivation": true,
  "should_mention_company": true,
  "should_mention_job_post": false,
  "should_mention_recipient_email": false,
  "should_sound_like": "real_person",
  "opening_style": "direct_context",
  "cta_style": "soft_meeting_request",
  "personalization_level": "low",
  "confidence_score": 0.8
}}
"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": "You are a strict JSON email strategy generator."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        raw_output = response.choices[0].message.content.strip()

        return json.loads(raw_output)

    except Exception as e:
        print("EMAIL STRATEGY ERROR:", e)

        return {
            "tone": "direct",
            "style": "neutral",
            "email_type": "cold_outreach",
            "max_length": "ultra_short",
            "avoid_generic_phrases": True,
            "avoid_motivation_letter_style": True,
            "avoid_cv_summary_style": True,
            "avoid_exaggerated_motivation": True,
            "should_mention_company": bool(job_context.get("company_name")),
            "should_mention_job_post": bool(job_context.get("job_description")),
            "should_mention_recipient_email": False,
            "should_sound_like": "real_person",
            "opening_style": "quick_intro",
            "cta_style": "soft_meeting_request",
            "personalization_level": "low",
            "confidence_score": 0.5,
        }