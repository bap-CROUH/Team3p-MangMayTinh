import os
import socket
import threading
from config import DOWNLOAD_DIR, CHUNK_SIZE
from protocol import recv_until, recv_exact, send_ident, send_msg, send_bye


class ChatManager:
    def __init__(self, my_name: str, my_tcp_port: int):
        self.my_name = my_name
        self.my_tcp_port = my_tcp_port

        self.connections = {}   # { peer_name: socket }
        self.unread = {}        # { peer_name: [list of text messages] }
        self.current_partner = None

        self.lock = threading.Lock()
        self.running = True
        self.server_sock = self._create_tcp_server()

    def _create_tcp_server(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(("", self.my_tcp_port))
        s.listen(10)
        s.settimeout(1.0)
        return s

    def start(self):
        threading.Thread(target=self._acceptor_loop, daemon=True).start()

    def stop(self):
        self.running = False
        with self.lock:
            for sock in self.connections.values():
                send_bye(sock)
                try:
                    sock.close()
                except OSError:
                    pass
            self.connections.clear()
        try:
            self.server_sock.close()
        except OSError:
            pass

    def _acceptor_loop(self):
        """Luồng lắng nghe các kết nối TCP mới (cả chat và nhận file)."""
        while self.running:
            try:
                conn, addr = self.server_sock.accept()
            except socket.timeout:
                continue
            except OSError:
                break

            threading.Thread(
                target=self._handle_incoming_connection,
                args=(conn,),
                daemon=True,
            ).start()

    def _handle_incoming_connection(self, conn: socket.socket):
        """Phân loại kết nối đến: IDENT (chat) hoặc FILE (truyền file)."""
        try:
            cmd = recv_until(conn, b"|")
            if cmd == "IDENT":
                length = int(recv_until(conn, b"|"))
                peer_name = recv_exact(conn, length).decode("utf-8")
                with self.lock:
                    if peer_name in self.connections:
                        try:
                            self.connections[peer_name].close()
                        except OSError:
                            pass
                    self.connections[peer_name] = conn
                self._receiver_loop(peer_name, conn)

            elif cmd == "FILE":
                self._receive_file(conn)
            else:
                conn.close()
        except Exception:
            try:
                conn.close()
            except OSError:
                pass

    def _receive_file(self, conn: socket.socket):
        """Nhận file trên luồng riêng, lưu vào downloads/ và xóa nếu bị lỗi giữa chừng."""
        save_path = None
        try:
            sender_name = recv_until(conn, b"|")
            raw_filename = recv_until(conn, b"|")
            file_size = int(recv_until(conn, b"|"))

            # Chỉ lấy tên file, tránh lỗi bảo mật path traversal (../../)
            filename = os.path.basename(raw_filename)
            os.makedirs(DOWNLOAD_DIR, exist_ok=True)
            save_path = os.path.join(DOWNLOAD_DIR, filename)

            print(f"[*] Receiving '{filename}' ({file_size / (1024*1024):.2f} MB) from {sender_name}...")

            received = 0
            last_percent = 0
            with open(save_path, "wb") as f:
                while received < file_size:
                    to_read = min(CHUNK_SIZE, file_size - received)
                    chunk = conn.recv(to_read)
                    if not chunk:
                        raise ConnectionError("Connection lost during file transfer")
                    f.write(chunk)
                    received += len(chunk)

                    if file_size > 0:
                        percent = int(received * 100 / file_size)
                        if percent >= last_percent + 25 and percent < 100:
                            last_percent = (percent // 25) * 25
                            print(f"[*] Receiving '{filename}' ... {last_percent}%")

            print(f"[*] Received '{filename}' (100%). Saved to {save_path}")

        except Exception as e:
            print(f"[!] File transfer interrupted: {e}")
            # Xóa file đang tải dở nếu bị lỗi
            if save_path and os.path.exists(save_path):
                try:
                    os.remove(save_path)
                    print(f"[*] Deleted partial file: {save_path}")
                except OSError:
                    pass
        finally:
            try:
                conn.close()
            except OSError:
                pass

    def send_file(self, peer_name: str, ip: str, port: int, filepath: str):
        """Khởi chạy luồng riêng để gửi file không làm treo giao diện chat."""
        if not os.path.isfile(filepath):
            print(f"[!] File not found: {filepath}")
            return

        threading.Thread(
            target=self._file_sender_thread,
            args=(peer_name, ip, port, filepath),
            daemon=True,
        ).start()

    def _file_sender_thread(self, peer_name: str, ip: str, port: int, filepath: str):
        filename = os.path.basename(filepath)
        file_size = os.path.getsize(filepath)
        sock = None

        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            sock.connect((ip, port))
            sock.settimeout(None)

            # Gửi header: FILE|<sender>|<filename>|<size>|
            header = f"FILE|{self.my_name}|{filename}|{file_size}|".encode("utf-8")
            sock.sendall(header)

            print(f"[*] Sending '{filename}' ({file_size / (1024*1024):.2f} MB) to {peer_name}...")

            sent = 0
            last_percent = 0
            with open(filepath, "rb") as f:
                while True:
                    chunk = f.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    sock.sendall(chunk)
                    sent += len(chunk)

                    if file_size > 0:
                        percent = int(sent * 100 / file_size)
                        if percent >= last_percent + 25 and percent < 100:
                            last_percent = (percent // 25) * 25
                            print(f"[*] Sending '{filename}' ... {last_percent}%")

            print(f"[*] Sending '{filename}' ... 100%  Done.")

        except Exception as e:
            print(f"[!] Failed to send '{filename}': {e}")
        finally:
            if sock:
                try:
                    sock.close()
                except OSError:
                    pass

    def connect_to(self, peer_name: str, ip: str, port: int):
        """Mở kết nối TCP tới peer (hoặc chuyển sang chat nếu đã kết nối sẵn)."""
        with self.lock:
            already_connected = peer_name in self.connections

        if not already_connected:
            try:
                conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                conn.settimeout(5.0)
                conn.connect((ip, port))
                conn.settimeout(None)
                send_ident(conn, self.my_name)
            except OSError as e:
                print(f"[!] Could not connect to {peer_name} ({ip}:{port}): {e}")
                return

            with self.lock:
                self.connections[peer_name] = conn

            threading.Thread(
                target=self._receiver_loop,
                args=(peer_name, conn),
                daemon=True,
            ).start()
            print(f"[*] Connected to {peer_name} ({ip}:{port})")
        else:
            print(f"[*] Switched to {peer_name}")

        with self.lock:
            self.current_partner = peer_name
            pending = self.unread.pop(peer_name, [])

        if pending:
            print(f"[*] {len(pending)} unread message(s) from {peer_name}:")
            for msg in pending:
                print(f"[{peer_name}] {msg}")

    def _receiver_loop(self, peer_name: str, conn: socket.socket):
        """Luồng riêng cho từng peer để nhận tin nhắn liên tục."""
        try:
            while self.running:
                cmd = recv_until(conn, b"|")
                if cmd == "MSG":
                    length = int(recv_until(conn, b"|"))
                    text = recv_exact(conn, length).decode("utf-8", errors="replace")
                    self._on_message_received(peer_name, text)
                elif cmd == "BYE":
                    break
        except (ConnectionError, OSError, ValueError):
            pass
        finally:
            self._cleanup_peer(peer_name, conn)

    def _on_message_received(self, peer_name: str, text: str):
        with self.lock:
            is_current = (self.current_partner == peer_name)
            if not is_current:
                self.unread.setdefault(peer_name, []).append(text)
                count = len(self.unread[peer_name])

        if is_current:
            print(f"[{peer_name}] {text}")
        else:
            print(f"[*] New message from {peer_name} ({count} unread)")

    def _cleanup_peer(self, peer_name: str, conn: socket.socket):
        was_current = False
        with self.lock:
            if self.connections.get(peer_name) is conn:
                del self.connections[peer_name]
            if self.current_partner == peer_name:
                self.current_partner = None
                was_current = True
        try:
            conn.close()
        except OSError:
            pass

        if self.running and was_current:
            print(f"[*] {peer_name} disconnected. Returned to main prompt.")

    def send_chat_message(self, text: str):
        with self.lock:
            partner = self.current_partner
            conn = self.connections.get(partner) if partner else None

        if not partner or not conn:
            print("[!] Not in a chat. Use /chat <name|number> first.")
            return

        try:
            send_msg(conn, text)
            print(f"[{self.my_name}] {text}")
        except OSError:
            print(f"[!] Failed to send message. {partner} may have disconnected.")
            self._cleanup_peer(partner, conn)

    def leave_chat(self):
        with self.lock:
            partner = self.current_partner
            self.current_partner = None

        if partner:
            print(f"[*] Left chat with {partner}.")
        else:
            print("[!] You are not currently in a chat.")