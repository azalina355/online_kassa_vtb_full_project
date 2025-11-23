import json
import os
from dataclasses import asdict
from typing import List, Optional

from .models import Client, Transaction
from .utils import get_current_timestamp


class Database:
    def __init__(self, data_dir: str = "data") -> None:
        self.data_dir = data_dir
        os.makedirs(self.data_dir, exist_ok=True)
        self.clients_file = os.path.join(self.data_dir, "clients.json")
        self.transactions_file = os.path.join(self.data_dir, "transactions.json")
        self._initialize_default_data()

    def _initialize_default_data(self) -> None:
        if not os.path.exists(self.clients_file):
            default_clients = [
                {
                    "id": 1,
                    "name": "Иванов Иван Иванович",
                    "account_number": "40817810099910004312",
                    "balance": 15000.50,
                    "currency": "RUB",
                },
                {
                    "id": 2,
                    "name": "Петрова Анна Сергеевна",
                    "account_number": "40817810099910004313",
                    "balance": 75000.00,
                    "currency": "RUB",
                },
                {
                    "id": 3,
                    "name": "Сидоров Алексей Владимирович",
                    "account_number": "40817810099910004314",
                    "balance": 25000.75,
                    "currency": "RUB",
                },
            ]
            with open(self.clients_file, "w", encoding="utf-8") as f:
                json.dump(default_clients, f, indent=2, ensure_ascii=False)

        if not os.path.exists(self.transactions_file):
            with open(self.transactions_file, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2, ensure_ascii=False)

    def load_clients(self) -> List[Client]:
        try:
            with open(self.clients_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [Client(**client) for client in data]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_clients(self, clients: List[Client]) -> None:
        with open(self.clients_file, "w", encoding="utf-8") as f:
            json.dump([asdict(client) for client in clients], f, indent=2, ensure_ascii=False)

    def get_client_by_id(self, client_id: int) -> Optional[Client]:
        clients = self.load_clients()
        for client in clients:
            if client.id == client_id:
                return client
        return None

    def update_client_balance(self, client_id: int, new_balance: float) -> None:
        clients = self.load_clients()
        updated = False
        for client in clients:
            if client.id == client_id:
                client.balance = round(new_balance, 2)
                updated = True
                break
        if updated:
            self.save_clients(clients)

    def load_transactions(self) -> List[Transaction]:
        try:
            with open(self.transactions_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [Transaction(**tx) for tx in data]
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_transactions(self, transactions: List[Transaction]) -> None:
        with open(self.transactions_file, "w", encoding="utf-8") as f:
            json.dump([asdict(t) for t in transactions], f, indent=2, ensure_ascii=False)

    def save_transaction(self, transaction: Transaction) -> Transaction:
        transactions = self.load_transactions()
        if transaction.id is None:
            transaction.id = len(transactions) + 1
        transactions.append(transaction)
        self._save_transactions(transactions)
        return transaction

    def deposit(self, client_id: int, amount: float, description: str = "") -> Transaction:
        clients = self.load_clients()
        client = next((c for c in clients if c.id == client_id), None)
        if client is None:
            raise ValueError("Клиент не найден")

        client.balance = round(client.balance + amount, 2)
        self.save_clients(clients)

        tx = Transaction(
            id=None,
            timestamp=get_current_timestamp(),
            operation_type="Внесение средств",
            amount=amount,
            client_name=client.name,
            description=description or "Пополнение счёта",
            target_client=None,
        )
        return self.save_transaction(tx)

    def withdraw(self, client_id: int, amount: float, description: str = "") -> Transaction:
        clients = self.load_clients()
        client = next((c for c in clients if c.id == client_id), None)
        if client is None:
            raise ValueError("Клиент не найден")

        if client.balance < amount:
            raise ValueError("Недостаточно средств на счёте")

        client.balance = round(client.balance - amount, 2)
        self.save_clients(clients)

        tx = Transaction(
            id=None,
            timestamp=get_current_timestamp(),
            operation_type="Снятие средств",
            amount=amount,
            client_name=client.name,
            description=description or "Снятие наличных",
            target_client=None,
        )
        return self.save_transaction(tx)

    def transfer(self, source_id: int, target_id: int, amount: float, description: str = "") -> Transaction:
        if source_id == target_id:
            raise ValueError("Нельзя переводить средства самому себе")

        clients = self.load_clients()
        source = next((c for c in clients if c.id == source_id), None)
        target = next((c for c in clients if c.id == target_id), None)

        if source is None or target is None:
            raise ValueError("Клиент не найден")

        if source.balance < amount:
            raise ValueError("Недостаточно средств на счёте отправителя")

        source.balance = round(source.balance - amount, 2)
        target.balance = round(target.balance + amount, 2)
        self.save_clients(clients)

        tx = Transaction(
            id=None,
            timestamp=get_current_timestamp(),
            operation_type="Перевод другому клиенту",
            amount=amount,
            client_name=source.name,
            description=description or f"Перевод клиенту {target.name}",
            target_client=target.name,
        )
        return self.save_transaction(tx)
