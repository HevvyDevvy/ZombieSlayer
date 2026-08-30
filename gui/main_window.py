import os
from pathlib import Path

from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTabWidget,
)

from core import AllowList, ConnectionMonitor, SettingsStore, TerminationEngine, MonitorEvent
from .widgets import Dashboard, AllowListTab, LoadoutTab, SettingsTab

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"


class MonitorEventBridge(QObject):
    """Relays ConnectionMonitor events (fired on worker threads) to the Qt main
    thread as a signal, since Qt widgets must only be touched from the GUI thread."""

    event_received = Signal(object)

    def emit_event(self, event: MonitorEvent):
        self.event_received.emit(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Zombie Slayer")
        self.resize(880, 640)

        icon_path = ASSETS_DIR / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.settings = SettingsStore()
        self.allowlist = AllowList(self.settings.get("authorized_ips", []))
        self.termination_engine = TerminationEngine()
        self.monitor = ConnectionMonitor(
            allowlist=self.allowlist,
            termination_engine=self.termination_engine,
            ports=self.settings.get("ports_to_scan", []),
            auto_terminate_unauthorized=self.settings.get_option("automated_response"),
        )

        self.bridge = MonitorEventBridge()
        self.bridge.event_received.connect(self._on_monitor_event)
        self.monitor.subscribe(self.bridge.emit_event)

        self._build_ui()
        self._load_state_into_ui()

    # ---------------------------------------------------------------- UI

    def _build_ui(self):
        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        root.addWidget(self._build_header())

        tabs = QTabWidget()
        self.dashboard = Dashboard()
        self.allowlist_tab = AllowListTab()
        self.loadout_tab = LoadoutTab()
        self.settings_tab = SettingsTab()

        tabs.addTab(self.dashboard, "DASHBOARD")
        tabs.addTab(self.allowlist_tab, "ALLOW LIST")
        tabs.addTab(self.loadout_tab, "LOADOUT")
        tabs.addTab(self.settings_tab, "SETTINGS")
        root.addWidget(tabs, stretch=1)

        footer = QLabel("ZOMBIE SLAYER — NETWORK DEFENSE SYSTEM")
        footer.setObjectName("Footer")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(footer)

        self.setCentralWidget(central)

        # Wire signals
        self.dashboard.monitor_toggled.connect(self._on_monitor_toggled)
        self.allowlist_tab.ip_added.connect(self._on_ip_added)
        self.allowlist_tab.ip_removed.connect(self._on_ip_removed)
        self.loadout_tab.ports_changed.connect(self._on_ports_changed)
        self.settings_tab.option_changed.connect(self._on_option_changed)

    def _build_header(self) -> QWidget:
        header = QWidget()
        header.setObjectName("BrandHeader")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(16, 12, 16, 12)

        icon_path = ASSETS_DIR / "icon.png"
        if icon_path.exists():
            icon_label = QLabel()
            pix = QPixmap(str(icon_path)).scaled(
                40, 40, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
            )
            icon_label.setPixmap(pix)
            layout.addWidget(icon_label)

        title_box = QVBoxLayout()
        title = QLabel("ZOMBIE SLAYER")
        title.setObjectName("BrandTitle")
        subtitle = QLabel("NETWORK DEFENSE SYSTEM")
        subtitle.setObjectName("BrandSubtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        layout.addLayout(title_box)
        layout.addStretch()
        return header

    def _load_state_into_ui(self):
        self.allowlist_tab.set_ips(self.allowlist.all())
        self.loadout_tab.set_ports(self.settings.get("ports_to_scan", []))
        self.settings_tab.set_options(self.settings.all_options)

    # ------------------------------------------------------------ Handlers

    def _on_monitor_toggled(self, running: bool):
        if running:
            self.monitor.ports = self.settings.get("ports_to_scan", [])
            self.monitor.auto_terminate_unauthorized = self.settings.get_option(
                "automated_response"
            )
            self.monitor.start()
        else:
            self.monitor.stop()

    def _on_ip_added(self, ip: str):
        if self.allowlist.add(ip):
            self.settings.set("authorized_ips", self.allowlist.all())
            self.settings.save()
            self.allowlist_tab.set_ips(self.allowlist.all())
        else:
            self.allowlist_tab.show_rejected(ip)

    def _on_ip_removed(self, ip: str):
        self.allowlist.remove(ip)
        self.settings.set("authorized_ips", self.allowlist.all())
        self.settings.save()
        self.allowlist_tab.set_ips(self.allowlist.all())

    def _on_ports_changed(self, ports: list[int]):
        self.settings.set("ports_to_scan", ports)
        self.settings.save()
        self.monitor.ports = ports

    def _on_option_changed(self, name: str, value: bool):
        self.settings.set_option(name, value)
        self.settings.save()
        if name == "automated_response":
            self.monitor.auto_terminate_unauthorized = value

    def _on_monitor_event(self, event: MonitorEvent):
        self.dashboard.add_event(event)

    def closeEvent(self, event):
        self.monitor.stop()
        super().closeEvent(event)
