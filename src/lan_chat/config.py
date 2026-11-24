UDP_PORT = 9999
BROADCAST_INTERVAL = 3.0   # Gửi gói tin HELLO mỗi 3 giây
PEER_TIMEOUT = 10.0        # Xóa user nếu không thấy tín hiệu sau 10 giây
DEFAULT_BCAST = "255.255.255.255"

DOWNLOAD_DIR = "downloads" # Thư mục lưu file nhận được
CHUNK_SIZE = 65536         # Đọc/gửi mỗi lần 64 KB  