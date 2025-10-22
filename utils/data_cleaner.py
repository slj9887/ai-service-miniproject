import re

def clean_text(text: str) -> str:
    """텍스트에서 불필요한 기호, 공백 제거"""
    text = re.sub(r"[^A-Za-z0-9가-힣\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
