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
    greeting = f"Hi {recipient}," if recipient else "Hi,"
    return {
        "draft": f"{greeting}\n\n{purpose}\n\nBest,",
        "tone": tone,
        "send_status": "draft_only",
    }
