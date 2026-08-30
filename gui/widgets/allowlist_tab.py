from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QListWidget,
    QLabel,
    QMessageBox,
)


class AllowListTab(QWidget):
    """Add/remove authorized IP addresses."""

    ip_added = Signal(str)
    ip_removed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel("AUTHORIZED IP ADDRESSES")
        title.setObjectName("BrandSubtitle")
        layout.addWidget(title)

        entry_row = QHBoxLayout()
        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("e.g. 192.168.1.50")
        self.ip_input.returnPressed.connect(self._on_add)
        add_btn = QPushButton("ADD")
        add_btn.setObjectName("PrimaryButton")
        add_btn.clicked.connect(self._on_add)
        entry_row.addWidget(self.ip_input, stretch=1)
        entry_row.addWidget(add_btn)
        layout.addLayout(entry_row)

        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget, stretch=1)

        remove_btn = QPushButton("REMOVE SELECTED")
        remove_btn.setObjectName("DangerButton")
        remove_btn.clicked.connect(self._on_remove)
        layout.addWidget(remove_btn)

    def _on_add(self):
        ip = self.ip_input.text().strip()
        if not ip:
            return
        self.ip_added.emit(ip)
        self.ip_input.clear()

    def _on_remove(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        self.ip_removed.emit(item.text())

    def set_ips(self, ips: list[str]):
        self.list_widget.clear()
        self.list_widget.addItems(ips)

    def show_rejected(self, ip: str):
        QMessageBox.warning(self, "Invalid IP", f"'{ip}' is not a valid IP address.")
