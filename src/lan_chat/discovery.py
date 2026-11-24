import socket
import threading
import time
from config import UDP_PORT, BROADCAST_INTERVAL, PEER_TIMEOUT


class PeerDiscovery:
    def __init__(self, my_name: str, my_tcp_port: int, bcast_ip: str):
        self.my_name = my_name
        self.my_tcp_port = my_tcp_port
        self.bcast_ip = bcast_ip
        self.my_status = "online"

        # Lưu danh sách peer: { name: {"ip": str, "tcp_port": int, "status": str, "last_seen": float} }
        self.peers = {}
        self.lock = threading.Lock()
        self.running = True
        self.sock = self._create_udp_socket()

    def _create_udp_socket(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Cho phép nhiều tiến trình dùng chung UDP port 9999 trên cùng 1 máy
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        if hasattr(socket, "SO_REUSEPORT"):
            try:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
            except OSError:
                pass
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.bind(("", UDP_PORT))
        s.settimeout(1.0)  # Tránh bị treo mãi ở recvfrom() khi thoát chương trình
        return s

    def start(self):
        threading.Thread(target=self._broadcaster_loop, daemon=True).start()
        threading.Thread(target=self._listener_loop, daemon=True).start()
        threading.Thread(target=self._cleanup_loop, daemon=True).start()

    def stop(self):
        self.running = False
        self.sock.close()

    def set_status(self, new_status: str):
        with self.lock:
            self.my_status = new_status
        # Gửi broadcast ngay lập tức để máy khác cập nhật trạng thái không cần chờ 3s
        self._send_hello()

    def _send_hello(self):
        with self.lock:
            msg = f"HELLO|{self.my_name}|{self.my_tcp_port}|{self.my_status}"
        try:
            self.sock.sendto(msg.encode("utf-8"), (self.bcast_ip, UDP_PORT))
        except OSError:
            pass

    def _broadcaster_loop(self):
        while self.running:
            self._send_hello()
            time.sleep(BROADCAST_INTERVAL)

    def _listener_loop(self):
        while self.running:
            try:
                data, addr = self.sock.recvfrom(1024)
            except socket.timeout:
                continue
            except OSError:
                break

            msg = data.decode("utf-8", errors="replace").strip()
            parts = msg.split("|")
            # Định dạng chuẩn: HELLO|<name>|<tcp_port>|<status>
            if len(parts) != 4 or parts[0] != "HELLO":
                continue

            name, tcp_port_str, status = parts[1], parts[2], parts[3]
            if name == self.my_name:
                continue  # Bỏ qua gói tin của chính mình

            try:
                tcp_port = int(tcp_port_str)
            except ValueError:
                continue

            now = time.time()
            with self.lock:
                is_new = name not in self.peers
                self.peers[name] = {
                    "ip": addr[0],
                    "tcp_port": tcp_port,
                    "status": status,
                    "last_seen": now,
                }
            if is_new:
                print(f"[*] {name} ({addr[0]}) is now {status}")

    def _cleanup_loop(self):
        """Kiểm tra mỗi giây để xóa các user quá 10 giây không có tín hiệu."""
        while self.running:
            time.sleep(1.0)
            now = time.time()
            offline_users = []
            with self.lock:
                for name, info in list(self.peers.items()):
                    if now - info["last_seen"] > PEER_TIMEOUT:
                        offline_users.append(name)
                        del self.peers[name]
            for name in offline_users:
                print(f"[*] {name} went offline")

    def get_online_list(self):
        """Trả về bản sao danh sách peer hiện tại (đã sắp xếp theo tên)."""
        with self.lock:
            return sorted(self.peers.items(), key=lambda x: x[0])