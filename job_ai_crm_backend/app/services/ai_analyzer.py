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