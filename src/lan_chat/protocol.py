import socket


def recv_exact(sock: socket.socket, num_bytes: int) -> bytes:
    """Đọc chính xác num_bytes từ TCP socket (lặp recv đến khi đủ)."""
    chunks = []
    received = 0
    while received < num_bytes:
        chunk = sock.recv(num_bytes - received)
        if not chunk:
            raise ConnectionError("Peer closed connection")
        chunks.append(chunk)
        received += len(chunk)
    return b"".join(chunks)


def recv_until(sock: socket.socket, delimiter: bytes = b"|") -> str:
    """Đọc từng byte cho đến khi gặp ký tự phân cách '|'."""
    data = bytearray()
    while True:
        ch = sock.recv(1)
        if not ch:
            raise ConnectionError("Peer closed connection")
        if ch == delimiter:
            return data.decode("utf-8", errors="replace")
        data.extend(ch)


def send_ident(sock: socket.socket, name: str):
    payload = name.encode("utf-8")
    header = f"IDENT|{len(payload)}|".encode("utf-8")
    sock.sendall(header + payload)


def send_msg(sock: socket.socket, text: str):
    payload = text.encode("utf-8")
    header = f"MSG|{len(payload)}|".encode("utf-8")
    sock.sendall(header + payload)


def send_bye(sock: socket.socket):
    try:
        sock.sendall(b"BYE|")
    except OSError:
        pass