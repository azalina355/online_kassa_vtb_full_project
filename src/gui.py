import sys
from typing import List

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QHeaderView,
    QFormLayout,
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont

from .database import Database
from .models import Client, Transaction
from .utils import format_currency, validate_amount


class CashierApp(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.db = Database()
        self.clients: List[Client] = []
        self._init_ui()
        self.load_clients()

    def _init_ui(self) -> None:
        self.setWindowTitle("Онлайн-касса ВТБ")
        self.resize(1000, 700)

        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #020617;
                color: #e5e7eb;
            }
            QLabel {
                color: #e5e7eb;
            }
            QLineEdit, QComboBox, QTextEdit, QTableWidget {
                background-color: #020617;
                color: #e5e7eb;
                border: 1px solid #1f2937;
                border-radius: 8px;
                padding: 6px;
                selection-background-color: #1d4ed8;
            }
            QTableWidget::item {
                padding: 6px;
            }
            QTabWidget::pane {
                border: 1px solid #1f2937;
                border-radius: 10px;
                margin-top: 4px;
            }
            QTabBar::tab {
                background-color: #0f172a;
                color: #9ca3af;
                padding: 8px 16px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
            }
            QTabBar::tab:selected {
                background-color: #1d4ed8;
                color: #f9fafb;
            }
            QPushButton {
                background-color: #2563eb;
                color: #f9fafb;
                border-radius: 10px;
                padding: 8px 18px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1d4ed8;
            }
            QPushButton:disabled {
                background-color: #4b5563;
            }
            QTextEdit {
                background-color: #020617;
                border-radius: 10px;
            }
            """
        )

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        title = QLabel("Онлайн-касса ВТБ")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.operations_tab = QWidget()
        self._setup_operations_tab()
        self.tabs.addTab(self.operations_tab, "Операции")

        self.history_tab = QWidget()
        self._setup_history_tab()
        self.tabs.addTab(self.history_tab, "История операций")

        self.admin_tab = QWidget()
        self._setup_admin_tab()
        self.tabs.addTab(self.admin_tab, "Админ-панель")

    def _setup_operations_tab(self) -> None:
        layout = QVBoxLayout(self.operations_tab)
        layout.setSpacing(12)

        client_layout = QHBoxLayout()
        client_label = QLabel("Клиент:")
        client_label.setMinimumWidth(70)
        client_layout.addWidget(client_label)

        self.client_combo = QComboBox()
        self.client_combo.currentIndexChanged.connect(self.on_client_changed)
        client_layout.addWidget(self.client_combo, stretch=1)
        client_layout.addStretch()
        layout.addLayout(client_layout)

        self.client_info = QLabel("Выберите клиента")
        self.client_info.setFont(QFont("Arial", 10))
        self.client_info.setStyleSheet(
            "background-color: #0f172a; padding: 10px; border-radius: 10px;"
        )
        layout.addWidget(self.client_info)

        form_layout = QFormLayout()

        self.operation_combo = QComboBox()
        self.operation_combo.addItems(
            ["Внесение средств", "Снятие средств", "Перевод другому клиенту"]
        )
        self.operation_combo.currentIndexChanged.connect(self.on_operation_changed)
        form_layout.addRow("Операция:", self.operation_combo)

        self.amount_edit = QLineEdit()
        self.amount_edit.setPlaceholderText("Введите сумму")
        form_layout.addRow("Сумма:", self.amount_edit)

        self.target_client_label = QLabel("Клиент-получатель:")
        self.target_client_combo = QComboBox()
        self.target_client_combo.setVisible(False)
        self.target_client_label.setVisible(False)
        form_layout.addRow(self.target_client_label, self.target_client_combo)

        self.description_edit = QLineEdit()
        self.description_edit.setPlaceholderText("Комментарий к операции")
        form_layout.addRow("Описание:", self.description_edit)

        layout.addLayout(form_layout)

        self.execute_btn = QPushButton("Выполнить операцию")
        self.execute_btn.clicked.connect(self.execute_operation)
        layout.addWidget(self.execute_btn)

        log_label = QLabel("Лог операций:")
        layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        layout.addWidget(self.log_text)

    def _setup_history_tab(self) -> None:
        layout = QVBoxLayout(self.history_tab)

        self.history_table = QTableWidget()
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(
            [
                "Дата/время",
                "Тип операции",
                "Сумма",
                "Клиент",
                "Описание",
                "Получатель",
            ]
        )
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.history_table)

        refresh_btn = QPushButton("Обновить историю")
        refresh_btn.clicked.connect(self.load_history)
        layout.addWidget(refresh_btn)

    def _setup_admin_tab(self) -> None:
        layout = QVBoxLayout(self.admin_tab)

        self.clients_table = QTableWidget()
        self.clients_table.setColumnCount(4)
        self.clients_table.setHorizontalHeaderLabels(
            ["ID", "ФИО", "Номер счёта", "Баланс"]
        )
        self.clients_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.clients_table)

        refresh_btn = QPushButton("Обновить данные клиентов")
        refresh_btn.clicked.connect(self.load_clients_admin)
        layout.addWidget(refresh_btn)

    def load_clients(self) -> None:
        self.clients = self.db.load_clients()
        self.client_combo.clear()
        self.target_client_combo.clear()

        for client in self.clients:
            text = f"{client.name} ({client.account_number[-4:]})"
            self.client_combo.addItem(text, client.id)
            self.target_client_combo.addItem(text, client.id)

        self.load_clients_admin()
        self.load_history()
        self.on_client_changed()

    def load_clients_admin(self) -> None:
        clients = self.db.load_clients()
        self.clients_table.setRowCount(0)

        for client in clients:
            row = self.clients_table.rowCount()
            self.clients_table.insertRow(row)
            self.clients_table.setItem(row, 0, QTableWidgetItem(str(client.id)))
            self.clients_table.setItem(row, 1, QTableWidgetItem(client.name))
            self.clients_table.setItem(row, 2, QTableWidgetItem(client.account_number))
            self.clients_table.setItem(
                row,
                3,
                QTableWidgetItem(format_currency(client.balance, client.currency)),
            )

    def on_client_changed(self) -> None:
        if self.client_combo.currentIndex() < 0:
            self.client_info.setText("Выберите клиента")
            return

        client_id = self.client_combo.currentData()
        client = self.db.get_client_by_id(int(client_id))
        if not client:
            self.client_info.setText("Клиент не найден")
            return

        self.client_info.setText(
            f"Клиент: {client.name}\n"
            f"Счёт: {client.account_number}\n"
            f"Баланс: {format_currency(client.balance, client.currency)}"
        )

    def on_operation_changed(self) -> None:
        is_transfer = self.operation_combo.currentText() == "Перевод другому клиенту"
        self.target_client_combo.setVisible(is_transfer)
        self.target_client_label.setVisible(is_transfer)

    def execute_operation(self) -> None:
        if self.client_combo.currentIndex() < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента.")
            return

        ok, amount = validate_amount(self.amount_edit.text())
        if not ok:
            QMessageBox.warning(self, "Ошибка", "Введите корректную сумму (> 0).")
            return

        client_id = int(self.client_combo.currentData())
        description = self.description_edit.text().strip()
        operation = self.operation_combo.currentText()

        try:
            if operation == "Внесение средств":
                tx = self.db.deposit(client_id, amount, description)
            elif operation == "Снятие средств":
                tx = self.db.withdraw(client_id, amount, description)
            else:
                if self.target_client_combo.currentIndex() < 0:
                    QMessageBox.warning(
                        self, "Ошибка", "Выберите клиента-получателя."
                    )
                    return
                target_id = int(self.target_client_combo.currentData())
                tx = self.db.transfer(client_id, target_id, amount, description)
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", str(e))
            return

        self._append_log(tx)
        self.amount_edit.clear()
        self.description_edit.clear()
        self.load_clients()
        self.load_history()

        QMessageBox.information(self, "Успех", "Операция выполнена успешно.")

    def _append_log(self, tx: Transaction) -> None:
        line = (
            f"[{tx.timestamp}] {tx.operation_type}: "
            f"{format_currency(tx.amount)} — {tx.client_name}"
        )
        if tx.target_client:
            line += f" → {tx.target_client}"
        if tx.description:
            line += f" ({tx.description})"
        self.log_text.append(line)

    def load_history(self) -> None:
        try:
            transactions = self.db.load_transactions()
        except Exception as e:
            QMessageBox.critical(
                self, "Ошибка", f"Не удалось загрузить историю операций: {e}"
            )
            return

        self.history_table.setRowCount(0)
        for tx in transactions:
            row = self.history_table.rowCount()
            self.history_table.insertRow(row)
            self.history_table.setItem(row, 0, QTableWidgetItem(tx.timestamp))
            self.history_table.setItem(row, 1, QTableWidgetItem(tx.operation_type))
            self.history_table.setItem(
                row, 2, QTableWidgetItem(format_currency(tx.amount))
            )
            self.history_table.setItem(row, 3, QTableWidgetItem(tx.client_name))
            self.history_table.setItem(row, 4, QTableWidgetItem(tx.description))
            self.history_table.setItem(
                row, 5, QTableWidgetItem(tx.target_client or "—")
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CashierApp()
    window.show()
    sys.exit(app.exec_())
