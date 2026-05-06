import os
from dotenv import load_dotenv
from openai import OpenAI
from sqlalchemy.orm import Session

from app.models.company_chat_message import CompanyChatMessage
from app.services.vector_store import search_company_context

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def answer_company_question(
    db: Session,
    company_id: str,
    question: str
) -> str:
    contexts = search_company_context(
        company_id=company_id,
        question=question,
        top_k=5
    )

    context_text = "\n\n---\n\n".join(contexts) if contexts else ""

    previous_messages = (
        db.query(CompanyChatMessage)
        .filter(CompanyChatMessage.company_id == company_id)
        .order_by(CompanyChatMessage.created_at.asc())
        .limit(10)
        .all()
    )

    messages = [
        {
            "role": "system",
            "content": """
You are a company research chatbot.

You answer questions about a company using:
1. Retrieved website context
2. Previous conversation history

Rules:
- Answer in Turkish unless the user asks in English.
- Use the provided website context.
- Use conversation history when needed.
- Do not invent facts.
- If the answer is not clear, say there is not enough information.
"""
        },
        {
            "role": "user",
            "content": f"""
Website context:
{context_text if context_text else "No retrieved context found."}
"""
        }
    ]

    for msg in previous_messages:
        messages.append({
            "role": msg.role,
            "content": msg.content
        })

    messages.append({
        "role": "user",
        "content": question
    })

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=messages
    )

    answer = response.choices[0].message.content.strip()

    user_message = CompanyChatMessage(
        company_id=company_id,
        role="user",
        content=question
    )

    assistant_message = CompanyChatMessage(
        company_id=company_id,
        role="assistant",
        content=answer
    )

    db.add(user_message)
    db.add(assistant_message)
    db.commit()

    return answer