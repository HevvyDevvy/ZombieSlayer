"""IP allow-list management.

Tracks which remote IP addresses are permitted to hold connections once
they've been challenged by the ConnectionMonitor.
"""
from __future__ import annotations

import ipaddress
from typing import Iterable, List


class AllowList:
    """A simple, validated set of authorized IP addresses."""

    def __init__(self, ips: Iterable[str] | None = None) -> None:
        self._ips: set[str] = set()
        if ips:
            self.add_many(ips)

    def add(self, ip: str) -> bool:
        """Add a single IP if it's valid. Returns True if added."""
        ip = ip.strip()
        if not ip:
            return False
        try:
            ipaddress.ip_address(ip)
        except ValueError:
            return False
        self._ips.add(ip)
        return True

    def add_many(self, ips: Iterable[str]) -> List[str]:
        """Add several IPs at once. Returns the list of ones that were rejected."""
        rejected = []
        for ip in ips:
            if not self.add(ip):
                rejected.append(ip)
        return rejected

    def remove(self, ip: str) -> None:
        self._ips.discard(ip)

    def contains(self, ip: str) -> bool:
        return ip in self._ips

    def all(self) -> List[str]:
        return sorted(self._ips, key=lambda s: ipaddress.ip_address(s))

    def clear(self) -> None:
        self._ips.clear()

    def to_list(self) -> List[str]:
        return self.all()

    @classmethod
    def from_list(cls, ips: List[str]) -> "AllowList":
        return cls(ips)
