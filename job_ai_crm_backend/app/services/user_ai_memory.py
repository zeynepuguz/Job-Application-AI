from sqlalchemy.orm import Session

from app.models.user_ai_preference import UserAIPreference


def get_or_create_ai_preferences(db: Session) -> UserAIPreference:
    preference = (
        db.query(UserAIPreference)
        .first()
    )

    if preference:
        return preference

    preference = UserAIPreference(
        preferred_tone="natural",
        email_length="short",
        preferred_focus="technical",
        avoid_phrases=[
            "tutkum",
            "heyecan duyuyorum",
            "değer katacağıma inanıyorum",
        ],
        preferred_language="tr",
    )

    db.add(preference)
    db.commit()
    db.refresh(preference)

    return preference


def update_ai_preferences(
    db: Session,
    preferred_tone: str | None = None,
    email_length: str | None = None,
    preferred_focus: str | None = None,
    avoid_phrases: list[str] | None = None,
    preferred_language: str | None = None,
):
    preference = get_or_create_ai_preferences(db)

    if preferred_tone:
        preference.preferred_tone = preferred_tone

    if email_length:
        preference.email_length = email_length

    if preferred_focus:
        preference.preferred_focus = preferred_focus

    if avoid_phrases is not None:
        preference.avoid_phrases = avoid_phrases

    if preferred_language:
        preference.preferred_language = preferred_language

    db.commit()
    db.refresh(preference)

    return preference