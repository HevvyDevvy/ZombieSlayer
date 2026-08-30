"""Connection monitor.

Listens on a set of TCP ports. Every inbound connection is challenged
(allow/deny) against the AllowList. Denied/unauthorized connections are
handed to the TerminationEngine. All state changes are reported through
plain callbacks so any GUI (or none) can subscribe without this module
depending on a GUI toolkit.
"""
from __future__ import annotations

import logging
import socket
import threading
from dataclasses import dataclass
from datetime import datetime
from enum import Enum, auto
from typing import Callable, List, Optional

from .allowlist import AllowList
from .termination_engine import TerminationEngine

logger = logging.getLogger("zombieslayer.monitor")


class EventKind(Enum):
    INCOMING = auto()
    AUTHORIZED = auto()
    UNAUTHORIZED = auto()
    TERMINATED = auto()
    SERVER_STARTED = auto()
    SERVER_ERROR = auto()


@dataclass
class MonitorEvent:
    kind: EventKind
    ip: str
    port: int
    message: str = ""
    timestamp: datetime = None  # set in __post_init__

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


EventCallback = Callable[[MonitorEvent], None]


class ConnectionMonitor:
    """Owns one listening socket per configured port."""

    def __init__(
        self,
        allowlist: AllowList,
        termination_engine: TerminationEngine,
        ports: List[int],
        auto_terminate_unauthorized: bool = True,
    ) -> None:
        self.allowlist = allowlist
        self.termination_engine = termination_engine
        self.ports = ports
        self.auto_terminate_unauthorized = auto_terminate_unauthorized

        self._listeners: List[threading.Thread] = []
        self._servers: List[socket.socket] = []
        self._running = threading.Event()
        self._subscribers: List[EventCallback] = []

    def subscribe(self, callback: EventCallback) -> None:
        self._subscribers.append(callback)

    def _emit(self, event: MonitorEvent) -> None:
        for cb in self._subscribers:
            try:
                cb(event)
            except Exception:  # pragma: no cover - subscriber's fault, don't crash monitor
                logger.exception("Subscriber callback raised")

    def start(self) -> None:
        if self._running.is_set():
            return
        self._running.set()
        for port in self.ports:
            t = threading.Thread(target=self._run_server, args=(port,), daemon=True)
            t.start()
            self._listeners.append(t)

    def stop(self) -> None:
        self._running.clear()
        for server in self._servers:
            try:
                server.close()
            except OSError:
                pass
        self._servers.clear()
        self._listeners.clear()

    def _run_server(self, port: int) -> None:
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind(("0.0.0.0", port))
            server.listen(5)
            server.settimeout(1.0)  # allows periodic check of _running
        except OSError as exc:
            self._emit(MonitorEvent(EventKind.SERVER_ERROR, "0.0.0.0", port, str(exc)))
            return

        self._servers.append(server)
        self._emit(MonitorEvent(EventKind.SERVER_STARTED, "0.0.0.0", port))
        logger.info("Listening on port %s", port)

        while self._running.is_set():
            try:
                client, addr = server.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(
                target=self._handle_connection, args=(client, addr, port), daemon=True
            ).start()

    def _handle_connection(self, client: socket.socket, addr, port: int) -> None:
        remote_ip = addr[0]
        self._emit(MonitorEvent(EventKind.INCOMING, remote_ip, port))

        authorized = self.allowlist.contains(remote_ip)
        try:
            if authorized:
                client.sendall(b"Connection allowed.\n")
                self._emit(MonitorEvent(EventKind.AUTHORIZED, remote_ip, port))
            else:
                client.sendall(b"Connection denied. Unauthorized access.\n")
                self._emit(MonitorEvent(EventKind.UNAUTHORIZED, remote_ip, port))
                if self.auto_terminate_unauthorized:
                    results = self.termination_engine.terminate_ip(remote_ip)
                    for r in results:
                        msg = f"{len(r.pids_killed)} process(es) on {r.protocol}"
                        self._emit(
                            MonitorEvent(EventKind.TERMINATED, remote_ip, port, msg)
                        )
        finally:
            try:
                client.close()
            except OSError:
                pass
