from sqlalchemy.orm import Session
from app.services.user_ai_memory import update_ai_preferences


def learn_from_sent_email(db: Session, generated_email) -> None:
    """
    Mail gönderildiğinde kaliteli çıktılardan tercih öğrenir.
    rewrite_count <= 1 ise (iyi kalite) strateji ve dil bilgisini UserAIPreference'a yansıtır.
    """
    if generated_email is None:
        return

    rewrite_count = generated_email.rewrite_count or 0
    if rewrite_count > 1:
        return

    strategy = generated_email.strategy or {}
    review = generated_email.review or {}

    naturalness = review.get("naturalness_score", 10)
    genericness = review.get("genericness_score", 0)
    if naturalness < 6 or genericness > 7:
        return

    updates = {}

    if generated_email.language:
        updates["preferred_language"] = generated_email.language

    max_length = strategy.get("max_length")
    if max_length in ("ultra_short", "short", "medium"):
        updates["email_length"] = max_length

    style = strategy.get("style")
    if style:
        updates["preferred_tone"] = style

    focus = strategy.get("focus") or strategy.get("preferred_focus")
    if focus:
        updates["preferred_focus"] = focus

    if updates:
        update_ai_preferences(db, **updates)


def learn_from_refine_instruction(db: Session, instruction: str) -> None:
    """
    Kullanıcının refine talimatından tercih örüntüsü çıkarır.
    Keyword eşleşmesiyle UserAIPreference'ı günceller.
    """
    if not instruction:
        return

    text = instruction.lower()
    updates = {}

    if any(k in text for k in ["çok kısa", "çok kısalt", "ultra short", "very short", "daha da kısa"]):
        updates["email_length"] = "ultra_short"
    elif any(k in text for k in ["kısa", "kısalt", "shorter", "brief", "özet"]):
        updates["email_length"] = "short"
    elif any(k in text for k in ["uzun", "detaylı", "longer", "detailed", "genişlet"]):
        updates["email_length"] = "medium"

    if any(k in text for k in ["direkt", "direct", "doğrudan", "to the point"]):
        updates["preferred_tone"] = "direct"
    elif any(k in text for k in ["samimi", "informal", "friendly", "sıcak"]):
        updates["preferred_tone"] = "friendly"
    elif any(k in text for k in ["profesyonel", "professional", "resmi", "formal"]):
        updates["preferred_tone"] = "professional"

    if any(k in text for k in ["teknik", "technical", "teknoloji", "skill"]):
        updates["preferred_focus"] = "technical"
    elif any(k in text for k in ["motivasyon", "motivation", "ilgi", "interest"]):
        updates["preferred_focus"] = "motivation"

    if updates:
        update_ai_preferences(db, **updates)
