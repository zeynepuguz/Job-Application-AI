import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def extract_experience_from_cv(
    cv_text: str | None,
    role: str | None,
    job_description: str | None,
) -> list[str]:
    if not cv_text or not cv_text.strip():
        return []

    prompt = f"""Extract the most relevant skills, technologies, and experiences from this CV for the target role.

Target Role: {role or "Not specified"}

Job Description (first 500 chars):
{(job_description or "Not specified")[:500]}

CV Content:
{cv_text[:3000]}

Return 5-10 items that are most relevant to the role.
Focus on: technologies, tools, frameworks, specific projects, measurable achievements.
One item per line. No bullets, no numbers, no headers."""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.1,
        messages=[
            {
                "role": "system",
                "content": "You extract the most relevant technical skills and experiences from CVs. Be concise and specific. Return only what is explicitly written in the CV."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    result = response.choices[0].message.content.strip()
    return [line.strip() for line in result.split("\n") if line.strip()]
