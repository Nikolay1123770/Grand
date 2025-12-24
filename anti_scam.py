SCAM_WORDS = ["дюп", "обман", "кидал", "фейк", "скам"]

def is_scam(text: str) -> bool:
    text = text.lower()
    return any(word in text for word in SCAM_WORDS)
