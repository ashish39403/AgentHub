def summarize_text(arguments: dict) -> dict:
    text = str(arguments.get("text", "")).strip()
    max_chars = int(arguments.get("max_chars", 500))
    if not text:
        raise ValueError("text is required")
    return {
        "summary": text[:max_chars],
        "original_length": len(text),
    }


def draft_message(arguments: dict) -> dict:
    recipient = str(arguments.get("recipient", "")).strip()
    purpose = str(arguments.get("purpose", "")).strip()
    tone = str(arguments.get("tone", "professional")).strip()
    if not purpose:
        raise ValueError("purpose is required")
    clean_purpose = clean_draft_purpose(purpose)
    recipient_label = normalize_recipient(recipient, clean_purpose)
    greeting = f"Hi {recipient_label},"
    body = build_draft_body(clean_purpose, tone)
    return {
        "draft": f"{greeting}\n\n{body}\n\nBest,\nAshish",
        "tone": tone,
        "recipient": recipient_label,
        "purpose": clean_purpose,
        "send_status": "draft_only",
        "safety": "This is only a draft. No message was sent.",
    }


def clean_draft_purpose(purpose: str) -> str:
    prefixes = [
        "use draft_message tool to",
        "use the draft_message tool to",
        "draft_message tool to",
        "draft a",
        "draft an",
        "draft",
    ]
    clean = " ".join(purpose.strip().split())
    lower = clean.lower()
    for prefix in prefixes:
        if lower.startswith(prefix):
            clean = clean[len(prefix) :].strip(" .:")
            break
    return clean or purpose.strip()


def normalize_recipient(recipient: str, purpose: str) -> str:
    if recipient and recipient.lower() not in {"there", "someone", "user"}:
        return recipient
    if "recruiter" in purpose.lower():
        return "Recruiter"
    if "friend" in purpose.lower():
        return "Friend"
    return "there"


def build_draft_body(purpose: str, tone: str) -> str:
    lower = purpose.lower()
    if "recruiter" in lower and "internship" in lower:
        return (
            "I hope you're doing well. I am an engineering student interested in software engineering internship "
            "opportunities and wanted to ask if your team is currently hiring interns.\n\n"
            "I would be grateful for any guidance on open roles, application timelines, or the best way to apply. "
            "I can also share my resume and project details if helpful."
        )
    if "remind" in lower or "reminder" in lower:
        return f"Just a quick reminder: {purpose}."
    if tone.lower() in {"casual", "friendly"}:
        return f"I wanted to reach out about {purpose}. Let me know what you think."
    return f"I am reaching out regarding {purpose}. I would appreciate your guidance when convenient."
