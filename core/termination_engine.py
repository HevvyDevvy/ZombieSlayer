"""Termination engine.

Kills processes owning connections to/from a given IP, grouped by the
protocol/port they're associated with. Uses psutil so this works
identically on Windows, macOS, and Linux -- no shelling out to
platform-specific tools like pkill/taskkill required.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

import psutil

logger = logging.getLogger("zombieslayer.termination")

# Default port -> protocol label mapping, used for reporting/UI grouping.
DEFAULT_PROTOCOL_PORTS: Dict[str, List[int]] = {
    "ssh": [22],
    "telnet": [23],
    "http": [80, 8080],
    "https": [443, 8443],
    "ftp": [20, 21],
}


@dataclass
class TerminationResult:
    ip: str
    protocol: str
    pids_killed: List[int] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return bool(self.pids_killed) and not self.errors


class TerminationEngine:
    """Finds and kills local processes associated with connections to an IP."""

    def __init__(
        self,
        protocol_ports: Optional[Dict[str, List[int]]] = None,
        on_result: Optional[Callable[[TerminationResult], None]] = None,
    ) -> None:
        self.protocol_ports = protocol_ports or dict(DEFAULT_PROTOCOL_PORTS)
        self.on_result = on_result

    def _protocol_for_port(self, port: int) -> str:
        for protocol, ports in self.protocol_ports.items():
            if port in ports:
                return protocol
        return "other"

    def terminate_ip(self, ip: str) -> List[TerminationResult]:
        """Find every local connection touching `ip` and kill the owning process."""
        results_by_protocol: Dict[str, TerminationResult] = {}

        for conn in psutil.net_connections(kind="inet"):
            remote = conn.raddr
            if not remote or remote.ip != ip:
                continue
            if conn.pid is None:
                continue

            local_port = conn.laddr.port if conn.laddr else 0
            protocol = self._protocol_for_port(local_port)
            result = results_by_protocol.setdefault(
                protocol, TerminationResult(ip=ip, protocol=protocol)
            )

            try:
                proc = psutil.Process(conn.pid)
                proc.terminate()
                try:
                    proc.wait(timeout=2)
                except psutil.TimeoutExpired:
                    proc.kill()
                result.pids_killed.append(conn.pid)
                logger.info("Terminated PID %s (%s) for %s", conn.pid, protocol, ip)
            except psutil.NoSuchProcess:
                pass
            except psutil.AccessDenied:
                msg = f"Access denied killing PID {conn.pid} (try running elevated)"
                result.errors.append(msg)
                logger.warning(msg)
            except Exception as exc:  # pragma: no cover - defensive
                result.errors.append(str(exc))
                logger.exception("Unexpected error terminating PID %s", conn.pid)

        results = list(results_by_protocol.values())
        for result in results:
            if self.on_result:
                self.on_result(result)
        return results
