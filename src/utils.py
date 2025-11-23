from datetime import datetime
from typing import Tuple, Optional


def get_current_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def validate_amount(text: str) -> Tuple[bool, Optional[float]]:
    if not text:
        return False, None
    try:
        normalized = text.replace(",", ".").strip()
        amount = float(normalized)
        if amount <= 0:
            return False, None
        return True, amount
    except Exception:
        return False, None


def format_currency(amount: float, currency: str = "RUB") -> str:
    return f"{amount:,.2f} {currency}".replace(",", " ")
