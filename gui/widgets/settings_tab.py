from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QGroupBox,
    QScrollArea,
    QLabel,
)

# Grouped so the 18 flags read as categories instead of a flat wall of checkboxes.
OPTION_GROUPS = {
    "DETECTION": [
        "logging",
        "suspicious_processes",
        "unauthorized_access_attempts",
        "dos_attacks",
        "data_exfiltration",
        "malware_detection",
    ],
    "RESPONSE": [
        "automated_response",
        "rate_limiting",
        "alerting",
        "resource_intensive_activities",
    ],
    "HARDENING": [
        "authentication",
        "encryption",
        "input_validation",
        "permissions",
        "system_integrity_checks",
        "security_patch_management",
        "regular_updates",
        "testing",
    ],
}


class SettingsTab(QWidget):
    option_changed = Signal(str, bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._checkboxes: dict[str, QCheckBox] = {}
        self._build_ui()

    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 16, 16, 16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QWidget()
        layout = QVBoxLayout(inner)
        layout.setSpacing(14)

        for group_name, options in OPTION_GROUPS.items():
            box = QGroupBox(group_name)
            box_layout = QVBoxLayout()
            for opt in options:
                cb = QCheckBox(opt.replace("_", " ").title())
                cb.stateChanged.connect(
                    lambda state, o=opt: self.option_changed.emit(o, bool(state))
                )
                self._checkboxes[opt] = cb
                box_layout.addWidget(cb)
            box.setLayout(box_layout)
            layout.addWidget(box)

        layout.addStretch()
        scroll.setWidget(inner)
        outer.addWidget(scroll)

    def set_options(self, options: dict[str, bool]):
        for name, value in options.items():
            cb = self._checkboxes.get(name)
            if cb is not None:
                cb.blockSignals(True)
                cb.setChecked(value)
                cb.blockSignals(False)
