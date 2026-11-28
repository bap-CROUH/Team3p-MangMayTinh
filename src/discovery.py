"""UDP broadcast peer discovery for the LAN chat application."""

from __future__ import annotations

import socket
import threading
import time
import uuid
from typing import Callable

from config import BROADCAST_INTERVAL, PEER_TIMEOUT, UDP_PORT
from protocol import pack_hello, unpack_hello


class DiscoveryService:
    """Advertise this node and maintain a thread-safe list of online peers."""

    def __init__(
        self,
        name: str,
        tcp_port: int,
        bcast_addr: str = "255.255.255.255",
        on_ui_print: Callable[[str], None] | None = None,
        *,
        peer_id: str | None = None,
        udp_port: int = UDP_PORT,
    ) -> None:
        self.peer_id = peer_id or uuid.uuid4().hex[:8]
        self.name = name
        self.tcp_port = int(tcp_port)
        self.bcast_addr = bcast_addr
        self.udp_port = udp_port
        self.on_ui_print = on_ui_print or print
        self.online_peers: dict[str, dict] = {}
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self._broadcast_event = threading.Event()
        self._running = False
        self._threads: list[threading.Thread] = []
        self.my_status = "online"
        self.sock = self._create_udp_socket()

    def _create_udp_socket(self) -> socket.socket:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            if hasattr(socket, "SO_REUSEPORT"):
                try:
                    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
                except OSError:
                    # SO_REUSEPORT is optional and not supported on every OS.
                    pass
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.settimeout(0.5)
            sock.bind(("", self.udp_port))
            return sock
        except Exception:
            sock.close()
            raise

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._threads = [
            threading.Thread(target=self._broadcaster_loop, name="UDP Broadcaster", daemon=True),
            threading.Thread(target=self._listener_loop, name="UDP Listener", daemon=True),
            threading.Thread(target=self._cleaner_loop, name="Peer Cleaner", daemon=True),
        ]
        for thread in self._threads:
            thread.start()

    def stop(self) -> None:
        if not self._running:
            return
        self._running = False
        self._stop_event.set()
        self._broadcast_event.set()
        try:
            self.sock.close()
        except OSError:
            pass
        for thread in self._threads:
            if thread is not threading.current_thread():
                thread.join(timeout=1.0)

    def set_status(self, new_status: str) -> None:
        if new_status not in {"online", "away"}:
            raise ValueError("status must be 'online' or 'away'")
        with self._lock:
            self.my_status = new_status
        self.broadcast_now()

    def broadcast_now(self) -> None:
        self._broadcast_event.set()

    def _send_hello(self) -> None:
        with self._lock:
            payload = pack_hello(self.peer_id, self.name, self.tcp_port, self.my_status)
        try:
            self.sock.sendto(payload, (self.bcast_addr, self.udp_port))
        except OSError:
            if self._running:
                self.on_ui_print("[!] Could not send UDP presence beacon.")

    def _broadcaster_loop(self) -> None:
        while not self._stop_event.is_set():
            self._send_hello()
            self._broadcast_event.wait(BROADCAST_INTERVAL)
            self._broadcast_event.clear()

    def _listener_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                data, address = self.sock.recvfrom(4096)
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                beacon = unpack_hello(data)
                if isinstance(beacon, dict):
                    sender_id = beacon["peer_id"]
                    name = beacon["name"]
                    tcp_port = int(beacon["tcp_port"])
                    status = beacon["status"]
                else:
                    sender_id, name, tcp_port, status = beacon
                    tcp_port = int(tcp_port)
            except (KeyError, TypeError, ValueError, UnicodeError):
                continue
            if sender_id == self.peer_id or not name or status not in {"online", "away"}:
                continue
            if not 1 <= tcp_port <= 65535:
                continue

            now = time.time()
            with self._lock:
                previous = self.online_peers.get(sender_id)
                changed = previous is None or previous.get("status") != status
                self.online_peers[sender_id] = {
                    "peer_id": sender_id,
                    "name": name,
                    "ip": address[0],
                    "tcp_port": tcp_port,
                    "status": status,
                    "last_seen": now,
                }
            if changed:
                state = "online" if previous is None else f"now {status}"
                self.on_ui_print(f"[*] {name} ({address[0]}) is {state}.")

    def _cleaner_loop(self) -> None:
        while not self._stop_event.wait(1.0):
            now = time.time()
            offline: list[dict] = []
            with self._lock:
                for peer_id, peer in list(self.online_peers.items()):
                    if now - peer["last_seen"] > PEER_TIMEOUT:
                        offline.append(self.online_peers.pop(peer_id))
            for peer in offline:
                self.on_ui_print(f"[*] {peer['name']} went offline.")

    def get_online_peers(self) -> list[dict]:
        with self._lock:
            return [dict(peer) for peer in sorted(self.online_peers.values(), key=lambda p: p["name"].casefold())]

