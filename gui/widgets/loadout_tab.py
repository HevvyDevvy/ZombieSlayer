from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QLabel,
    QGroupBox,
    QFormLayout,
)


class LoadoutTab(QWidget):
    """Configure which ports are watched, and which protocol each maps to."""

    ports_changed = Signal(list)  # list[int]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        title = QLabel("WATCHED PORTS")
        title.setObjectName("BrandSubtitle")
        layout.addWidget(title)

        port_row = QHBoxLayout()
        self.ports_input = QLineEdit()
        self.ports_input.setPlaceholderText("22, 23, 80, 443, 21 (comma-separated)")
        save_btn = QPushButton("APPLY")
        save_btn.setObjectName("PrimaryButton")
        save_btn.clicked.connect(self._on_apply)
        port_row.addWidget(self.ports_input, stretch=1)
        port_row.addWidget(save_btn)
        layout.addLayout(port_row)

        group = QGroupBox("PROTOCOL REFERENCE")
        form = QFormLayout()
        for label, ports in [
            ("SSH", "22"),
            ("Telnet", "23"),
            ("HTTP", "80, 8080"),
            ("HTTPS", "443, 8443"),
            ("FTP", "20, 21"),
        ]:
            form.addRow(QLabel(label + ":"), QLabel(ports))
        group.setLayout(form)
        layout.addWidget(group)

        note = QLabel(
            "Unauthorized connections on a watched port are terminated by killing\n"
            "the local process that owns the connection, matched by protocol."
        )
        note.setWordWrap(True)
        note.setObjectName("Footer")
        layout.addWidget(note)
        layout.addStretch()

    def _on_apply(self):
        raw = self.ports_input.text()
        ports = []
        for p in raw.split(","):
            p = p.strip()
            if p.isdigit():
                ports.append(int(p))
        self.ports_changed.emit(ports)

    def set_ports(self, ports: list[int]):
        self.ports_input.setText(", ".join(str(p) for p in ports))
