from app.services.ai_agents.job_analyzer import analyze_job
from app.services.ai_agents.email_strategy_agent import build_email_strategy
from app.services.ai_agents.email_writer_agent import write_email
from app.services.ai_agents.email_reviewer_agent import review_email


def should_rewrite(review: dict) -> bool:
    if review.get("rewrite_needed"):
        return True

    naturalness = review.get("naturalness_score", 10)
    genericness = review.get("genericness_score", 1)
    cv_summary = review.get("cv_summary_score", 1)
    personalization = review.get("personalization_score", 10)

    if naturalness < 7:
        return True

    if genericness > 6:
        return True

    if cv_summary > 6:
        return True

    if personalization < 5:
        return True

    return False


def extract_allowed_experience(user_instruction: str | None) -> list[str]:
    if not user_instruction:
        return []

    return [user_instruction.strip()]


def generate_agentic_email(
    company_name,
    role,
    job_description,
    user_instruction,
    memory=None,
    recipient_email=None,
    source=None,
    recent_email_patterns=None,
):
    allowed_experience = extract_allowed_experience(user_instruction)

    job_analysis = analyze_job(
        role=role,
        job_description=job_description
    )

    job_context = {
        "company_name": company_name,
        "role": role,
        "job_description": job_description,
        "user_instruction": user_instruction,
        "recipient_email": recipient_email,
        "source": source,
        "job_analysis": job_analysis,
        "allowed_experience": allowed_experience,
    }

    strategy = build_email_strategy(
        job_context=job_context,
        memory=memory,
    )

    email_body = write_email(
        company_name=company_name,
        role=role,
        strategy=strategy,
        user_instruction=user_instruction,
        memory=memory,
        recent_email_patterns=recent_email_patterns,
        allowed_experience=allowed_experience,
    )

    review = review_email(email_body)

    rewrite_count = 0
    max_retries = 3

    while should_rewrite(review) and rewrite_count < max_retries:
        rewrite_count += 1

        email_body = write_email(
            company_name=company_name,
            role=role,
            strategy=strategy,
            user_instruction=user_instruction,
            previous_email=email_body,
            rewrite_reason=review.get("rewrite_reason")
            or "Email quality score was low.",
            rewrite_issues=review.get("issues"),
            review_issue_types=review.get("issue_types"),
            memory=memory,
            recent_email_patterns=recent_email_patterns,
            allowed_experience=allowed_experience,
        )

        review = review_email(email_body)

    return {
        "job_analysis": job_analysis,
        "strategy": strategy,
        "review": review,
        "rewrite_count": rewrite_count,
        "body": email_body,
    }