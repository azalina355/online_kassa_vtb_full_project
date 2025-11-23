from dataclasses import dataclass
from typing import Optional


@dataclass
class Client:
    id: int
    name: str
    account_number: str
    balance: float
    currency: str = "RUB"


@dataclass
class Transaction:
    id: Optional[int]
    timestamp: str
    operation_type: str
    amount: float
    client_name: str
    description: str
    target_client: Optional[str] = None
