import os
import json
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def review_email(email_text: str) -> dict:
    prompt = f"""
You are reviewing a Turkish job application email.

Your job is to evaluate whether this email feels:
- natural
- human-written
- personalized when possible
- concise
- professional
- non-generic
- non-AI-written

Flag rewrite_needed=true if the email contains:
- unsupported claims about experience
- invented projects or invented skills
- CV-summary tone
- generic motivation-letter wording
- overly polite AI-like wording
- exaggerated emotional phrases
- corporate cliché phrases
- long formal cover-letter style sentences

Flag rewrite_needed=true if the email includes any of these phrases or similar variants:
- "tutkum"
- "heyecan duyuyorum"
- "değer katacağıma inanıyorum"
- "kariyerim alanında"
- "başarılı"
- "deneyimlerimi paylaşmak"
- "katkıda bulunmak"
- "katkı sağlamak"
- "dinamik ekibiniz"
- "vizyonunuz"
- "yakından takip ediyorum"
- "kendimi geliştirmek"
- "gelişime açık"
- "yaklaşımınız dikkatimi çekti"
- "görüşme fırsatı bulursak"
- "uygun görürseniz değerlendirmek isterim"

Flag rewrite_needed=true if the email includes invented personal experience, such as:
- "bir öneri sistemi üzerinde çalıştım"
- "makine öğrenimi alanında çalıştım"
- "deneyim kazandım"
- "projelerimde"
- "çalışmalarımda"
- "önceki deneyimlerimde"
- "projeler geliştirdim"
- "Python üzerinde çalışıyorum"
- "bu alanda projeler geliştirdim"
- "backend geliştirme yapıyorum"
Flag rewrite_needed=true if the email turns job requirements into user experience.
For example, if the job asks for Python, the email must not claim "Python üzerinde çalışıyorum" unless the user explicitly provided that experience.
unless these details were explicitly provided.

Scoring guide:
- naturalness_score: 10 means very human and natural, 1 means robotic.
- genericness_score: 10 means very generic, 1 means specific and grounded.
- personalization_score: 10 means well-personalized, 1 means no personalization.
- professionalism_score: 10 means professional, 1 means inappropriate.
- cv_summary_score: 10 means it sounds like a CV summary, 1 means outreach-like.

IMPORTANT:
- Be strict.
- Prefer rewrite if the email sounds like AI.
- Prefer rewrite if it sounds like a motivation letter.
- Prefer rewrite if it uses vague compliments.
- Prefer rewrite if it invents experience.
- Prefer rewrite if it is longer than necessary.
- Do not approve emails with cliché wording.
- Do not approve emails that feel like a template.

Possible issue_types:
- ai_tone
- too_generic
- cv_summary
- hallucinated_experience
- too_formal
- motivation_letter_style
- repetitive_opening
- too_long
- weak_personalization
- robotic_tone

Email:

{email_text}

Return STRICT JSON.
Do not include markdown.
Do not include explanations.

{{
  "naturalness_score": 1,
  "genericness_score": 1,
  "personalization_score": 1,
  "professionalism_score": 1,
  "cv_summary_score": 1,
  "approved": true,
  "issues": [],
  "issue_types": [],
  "rewrite_needed": false,
  "rewrite_reason": ""
}}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are a strict recruiter and AI-writing detector. Return only valid JSON."
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
        print("EMAIL REVIEW JSON ERROR:", e)
        print("RAW REVIEW OUTPUT:", content)

        return {
            "naturalness_score": 5,
            "genericness_score": 7,
            "personalization_score": 4,
            "professionalism_score": 7,
            "cv_summary_score": 6,
            "approved": False,
            "issues": ["Reviewer JSON parse failed"],
            "issue_types": [],
            "rewrite_needed": True,
            "rewrite_reason": "Reviewer could not parse the response. Rewrite the email to be shorter, clearer, more natural, and less generic."
        }