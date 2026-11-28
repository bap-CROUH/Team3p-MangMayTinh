"""TCP acceptor and asynchronous peer-to-peer chat sessions."""

from __future__ import annotations

import socket
import threading
from typing import Callable

from config import MAX_HEADER_BYTES
from protocol import pack_msg, recv_exact, recv_line


class ChatNode:
    """Own the TCP listener, active chat sockets, and unread message queues."""

    def __init__(
        self,
        peer_id: str,
        name: str,
        tcp_port: int,
        on_ui_print: Callable[[str], None] | None = None,
        on_incoming_file: Callable[[socket.socket, str], None] | None = None,
    ) -> None:
        self.peer_id = peer_id
        self.name = name
        self.tcp_port = int(tcp_port)
        self.on_ui_print = on_ui_print or print
        self.on_incoming_file = on_incoming_file
        self._lock = threading.RLock()
        self._stop_event = threading.Event()
        self.active_chats: dict[str, socket.socket] = {}
        self._chat_directions: dict[str, str] = {}
        self.peer_info: dict[str, dict] = {}
        self.unread_messages: dict[str, list[str]] = {}
        self.unread_counts: dict[str, int] = {}
        self.current_chat_peer_id: str | None = None
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server_sock.bind(("", self.tcp_port))
            self.server_sock.listen(16)
            self.server_sock.settimeout(0.5)
        except Exception:
            self.server_sock.close()
            raise
        self._accept_thread: threading.Thread | None = None

    def start(self) -> None:
        if self._accept_thread and self._accept_thread.is_alive():
            return
        self._accept_thread = threading.Thread(target=self._accept_loop, name="TCP Acceptor", daemon=True)
        self._accept_thread.start()

    def _accept_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                conn, address = self.server_sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break
            threading.Thread(
                target=self._handle_connection,
                args=(conn, address),
                name=f"TCP Connection {address[0]}",
                daemon=True,
            ).start()

    def _handle_connection(self, conn: socket.socket, address: tuple) -> None:
        """Route the first header to chat registration or the file callback."""
        try:
            first_line = recv_line(conn, MAX_HEADER_BYTES)
            if first_line is None:
                conn.close()
                return
            if first_line.startswith("FILE|"):
                if self.on_incoming_file is None:
                    conn.sendall(b"FILE_ERR|File receiving is unavailable\n")
                    conn.close()
                else:
                    # Ownership of conn passes to the file receiver callback.
                    self.on_incoming_file(conn, first_line)
                return
            if not first_line.startswith("INTRO|"):
                conn.sendall(b"BYE\n")
                conn.close()
                return
            fields = first_line.split("|", 3)
            if len(fields) != 4:
                conn.close()
                return
            _, remote_id, remote_name, remote_port = fields
            remote_port_int = int(remote_port)
            if not remote_id or remote_id == self.peer_id or not remote_name or not 1 <= remote_port_int <= 65535:
                conn.close()
                return
            registered = self._register_chat(
                remote_id, remote_name, address[0], remote_port_int, conn, direction="incoming"
            )
            if registered is conn:
                threading.Thread(
                    target=self._chat_receiver_loop,
                    args=(remote_id, conn),
                    name=f"TCP Chat Receiver {remote_name}",
                    daemon=True,
                ).start()
                self.on_ui_print(f"[*] {remote_name} is available to chat.")
        except (ConnectionError, OSError, ValueError):
            try:
                conn.close()
            except OSError:
                pass

    def _register_chat(
        self,
        peer_id: str,
        name: str,
        ip: str,
        port: int,
        conn: socket.socket,
        *,
        direction: str,
    ) -> socket.socket:
        with self._lock:
            existing = self.active_chats.get(peer_id)
            if existing is not None:
                try:
                    existing.getpeername()
                    # Both peers may call /chat at once. Both must keep the
                    # same physical connection: the lower peer_id keeps its
                    # outgoing socket, and the higher peer_id keeps incoming.
                    preferred = "outgoing" if self.peer_id < peer_id else "incoming"
                    if self._chat_directions.get(peer_id) == preferred:
                        conn.close()
                        return existing
                    try:
                        existing.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
                    existing.close()
                except OSError:
                    self.active_chats.pop(peer_id, None)
            self.active_chats[peer_id] = conn
            self._chat_directions[peer_id] = direction
            self.peer_info[peer_id] = {"peer_id": peer_id, "name": name, "ip": ip, "tcp_port": port}
            self.unread_messages.setdefault(peer_id, [])
            self.unread_counts.setdefault(peer_id, 0)
            return conn

    def open_chat(self, peer_info: dict) -> list[str]:
        """Open or reuse a chat and return any queued messages for this peer."""
        peer_id = peer_info["peer_id"]
        with self._lock:
            conn = self.active_chats.get(peer_id)
            if conn is not None:
                try:
                    conn.getpeername()
                except OSError:
                    self.active_chats.pop(peer_id, None)
                    conn = None
        if conn is None:
            conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            conn.settimeout(5.0)
            try:
                conn.connect((peer_info["ip"], int(peer_info["tcp_port"])))
                intro = f"INTRO|{self.peer_id}|{self.name}|{self.tcp_port}\n".encode("utf-8")
                conn.sendall(intro)
                conn.settimeout(None)
            except OSError:
                conn.close()
                raise
            registered = self._register_chat(
                peer_id,
                peer_info["name"],
                peer_info["ip"],
                int(peer_info["tcp_port"]),
                conn,
                direction="outgoing",
            )
            if registered is conn:
                threading.Thread(
                    target=self._chat_receiver_loop,
                    args=(peer_id, conn),
                    name=f"TCP Chat Receiver {peer_info['name']}",
                    daemon=True,
                ).start()

        with self._lock:
            self.current_chat_peer_id = peer_id
            self.peer_info[peer_id] = dict(peer_info)
            messages = self.unread_messages.pop(peer_id, [])
            self.unread_messages[peer_id] = []
            self.unread_counts[peer_id] = 0
        return messages

    def send_message(self, text: str) -> None:
        with self._lock:
            peer_id = self.current_chat_peer_id
            conn = self.active_chats.get(peer_id) if peer_id else None
            if conn is None:
                raise RuntimeError("Not in an active chat")
        try:
            conn.sendall(pack_msg(text))
        except OSError:
            self._drop_chat(peer_id, conn, notify=True)
            raise ConnectionError("Chat peer is no longer connected")

    def _chat_receiver_loop(self, peer_id: str, conn: socket.socket) -> None:
        try:
            while not self._stop_event.is_set():
                header = recv_line(conn, MAX_HEADER_BYTES)
                if header is None or header == "BYE":
                    break
                if not header.startswith("MSG|"):
                    continue
                try:
                    byte_count = int(header.split("|", 1)[1])
                    if byte_count < 0:
                        raise ValueError
                    message = recv_exact(conn, byte_count).decode("utf-8")
                except (ValueError, UnicodeError, ConnectionError):
                    break
                with self._lock:
                    info = self.peer_info.get(peer_id, {})
                    peer_name = info.get("name", peer_id)
                    is_current = peer_id == self.current_chat_peer_id
                    if not is_current:
                        queue = self.unread_messages.setdefault(peer_id, [])
                        queue.append(message)
                        count = self.unread_counts.get(peer_id, 0) + 1
                        self.unread_counts[peer_id] = count
                if is_current:
                    self.on_ui_print(f"[{peer_name}] {message}")
                else:
                    self.on_ui_print(f"[*] New message from {peer_name} ({count} unread)")
        except (ConnectionError, OSError, ValueError):
            pass
        finally:
            self._drop_chat(peer_id, conn, notify=not self._stop_event.is_set())

    def pop_unread(self, peer_id: str) -> list[str]:
        with self._lock:
            messages = self.unread_messages.get(peer_id, [])
            self.unread_messages[peer_id] = []
            self.unread_counts[peer_id] = 0
            return list(messages)

    def get_unread_counts(self) -> dict[str, int]:
        with self._lock:
            return dict(self.unread_counts)

    def leave_current_chat(self) -> None:
        with self._lock:
            peer_id = self.current_chat_peer_id
            self.current_chat_peer_id = None
            conn = self.active_chats.get(peer_id) if peer_id else None
        if conn is not None:
            try:
                conn.sendall(b"BYE\n")
            except OSError:
                pass
            self._drop_chat(peer_id, conn, notify=False)

    def _drop_chat(self, peer_id: str, conn: socket.socket, notify: bool) -> None:
        with self._lock:
            is_active_connection = self.active_chats.get(peer_id) is conn
            if is_active_connection:
                self.active_chats.pop(peer_id, None)
                self._chat_directions.pop(peer_id, None)
            info = self.peer_info.get(peer_id, {})
            if is_active_connection and self.current_chat_peer_id == peer_id:
                self.current_chat_peer_id = None
                left_current = True
            else:
                left_current = False
        try:
            conn.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass
        try:
            conn.close()
        except OSError:
            pass
        if notify and is_active_connection:
            name = info.get("name", peer_id)
            message = f"[*] {name} left the chat."
            if left_current:
                message += " Returned to the lobby."
            self.on_ui_print(message)

    def shutdown(self) -> None:
        if self._stop_event.is_set():
            return
        self._stop_event.set()
        with self._lock:
            chats = list(self.active_chats.items())
            self.active_chats.clear()
            self._chat_directions.clear()
            self.current_chat_peer_id = None
        for _, conn in chats:
            try:
                conn.sendall(b"BYE\n")
            except OSError:
                pass
            try:
                conn.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            try:
                conn.close()
            except OSError:
                pass
        try:
            self.server_sock.close()
        except OSError:
            pass
        if self._accept_thread and self._accept_thread is not threading.current_thread():
            self._accept_thread.join(timeout=1.0)

