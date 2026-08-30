from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QPushButton,
)

from core import EventKind, MonitorEvent

EVENT_STYLE = {
    EventKind.INCOMING: ("INCOMING", "#9a9aa0"),
    EventKind.AUTHORIZED: ("ALLOWED", "#3fae5c"),
    EventKind.UNAUTHORIZED: ("BLOCKED", "#e21b2e"),
    EventKind.TERMINATED: ("TERMINATED", "#ff5f6d"),
    EventKind.SERVER_STARTED: ("LISTENING", "#5a8fe0"),
    EventKind.SERVER_ERROR: ("ERROR", "#ffb020"),
}


class Dashboard(QWidget):
    """Live status HUD + scrolling connection feed."""

    monitor_toggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._build_ui()
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._reset_pulse)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Status HUD row
        hud = QWidget()
        hud.setObjectName("StatusHud")
        hud_layout = QHBoxLayout(hud)
        hud_layout.setContentsMargins(14, 10, 14, 10)

        self.status_dot = QLabel()
        self.status_dot.setObjectName("StatusDotIdle")
        self.status_dot.setFixedSize(14, 14)

        self.status_label = QLabel("IDLE — DEFENSE SYSTEM OFFLINE")
        self.status_label.setObjectName("StatusLabel")

        self.toggle_button = QPushButton("ACTIVATE")
        self.toggle_button.setObjectName("PrimaryButton")
        self.toggle_button.clicked.connect(self._on_toggle_clicked)

        hud_layout.addWidget(self.status_dot)
        hud_layout.addWidget(self.status_label)
        hud_layout.addStretch()
        hud_layout.addWidget(self.toggle_button)

        layout.addWidget(hud)

        # Kill feed table
        feed_label = QLabel("LIVE FEED")
        feed_label.setObjectName("BrandSubtitle")
        layout.addWidget(feed_label)

        self.feed_table = QTableWidget(0, 5)
        self.feed_table.setHorizontalHeaderLabels(
            ["TIME", "STATUS", "IP", "PORT", "DETAIL"]
        )
        self.feed_table.horizontalHeader().setSectionResizeMode(
            4, QHeaderView.Stretch
        )
        self.feed_table.verticalHeader().setVisible(False)
        self.feed_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.feed_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.feed_table.setAlternatingRowColors(True)
        layout.addWidget(self.feed_table, stretch=1)

    def _on_toggle_clicked(self):
        self.set_running(not self._running)
        self.monitor_toggled.emit(self._running)

    def set_running(self, running: bool):
        self._running = running
        if running:
            self.status_dot.setObjectName("StatusDotActive")
            self.status_label.setText("ACTIVE — MONITORING CONNECTIONS")
            self.toggle_button.setText("DEACTIVATE")
        else:
            self.status_dot.setObjectName("StatusDotIdle")
            self.status_label.setText("IDLE — DEFENSE SYSTEM OFFLINE")
            self.toggle_button.setText("ACTIVATE")
        # force style re-evaluation for the dynamic objectName-based QSS
        self.status_dot.style().unpolish(self.status_dot)
        self.status_dot.style().polish(self.status_dot)

    def add_event(self, event: MonitorEvent):
        label, color = EVENT_STYLE.get(event.kind, ("EVENT", "#9a9aa0"))
        row = 0
        self.feed_table.insertRow(row)

        time_item = QTableWidgetItem(event.timestamp.strftime("%H:%M:%S"))
        status_item = QTableWidgetItem(label)
        status_item.setForeground(Qt.GlobalColor.white)
        from PySide6.QtGui import QColor

        status_item.setForeground(QColor(color))
        ip_item = QTableWidgetItem(event.ip)
        port_item = QTableWidgetItem(str(event.port))
        detail_item = QTableWidgetItem(event.message)

        for col, item in enumerate(
            [time_item, status_item, ip_item, port_item, detail_item]
        ):
            self.feed_table.setItem(row, col, item)

        # Cap the feed so it doesn't grow unbounded
        while self.feed_table.rowCount() > 500:
            self.feed_table.removeRow(self.feed_table.rowCount() - 1)

        if event.kind in (EventKind.UNAUTHORIZED, EventKind.TERMINATED):
            self._pulse(True)

    def _pulse(self, active: bool):
        if active:
            self.status_dot.setObjectName("StatusDotActive")
            self.status_dot.style().unpolish(self.status_dot)
            self.status_dot.style().polish(self.status_dot)
            self._pulse_timer.start(600)

    def _reset_pulse(self):
        self._pulse_timer.stop()
        self.set_running(self._running)
