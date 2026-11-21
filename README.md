# 🤝 Quy Tắc Làm Việc Nhóm & Đóng Góp Code - Team3p-MangMayTinh

**Đồ Án Mạng Máy Tính: Ứng Dụng LAN Chat & Truyền File P2P (TCP & UDP Sockets)**  
*Kho lưu trữ chính thức của nhóm 3 người*: `https://github.com/bap-CROUH/Team3p-MangMayTinh`

---

## 🌳 Sơ Đồ Cấu Trúc Thư Mục Dự Án (Flow Folder Structure)

```text
Team3p-MangMayTinh/
├── src/                                    # 💻 TOÀN BỘ MÃ NGUỒN CỐT LÕI (PYTHON NATIVE SOCKET)
│   ├── core/                               # 🧠 QUẢN LÝ DỮ LIỆU & BỘ NHỚ TRẠNG THÁI (TV1 + TV3)
│   │   ├── __init__.py
│   │   ├── peer_manager.py                 # [TV1] Quản lý danh sách Online Peers, IP, Port, Status & Luồng quét Timeout 10s
│   │   └── message_store.py                # [TV3] Lưu lịch sử chat, hộp thư chờ, đếm tin nhắn chưa đọc (Unread Count)
│   │
│   ├── network/                            # 🌐 TẦNG TRUYỀN THÔNG SOCKET TCP / UDP (TV1 + TV2)
│   │   ├── __init__.py
│   │   ├── protocol.py                     # [TV2] [FILE DÙNG CHUNG] Đóng gói & Phân tách Header (MSG, FILE, BYE, HELLO)
│   │   ├── udp_discovery.py                # [TV1] Luồng phát UDP Broadcast (3s/lần) & Luồng lắng nghe cổng 9999
│   │   ├── tcp_server.py                   # [TV1] Luồng TCP Acceptor chờ kết nối đến & Quản lý các kết nối P2P
│   │   └── file_transfer.py                # [TV2] Luồng gửi/nhận file nhị phân non-blocking, thanh tiến độ % & dọn file lỗi
│   │
│   ├── ui/                                 # 🖥️ GIAO DIỆN CONSOLE ĐIỀU KHIỂN THÔNG MINH (TV3)
│   │   ├── __init__.py
│   │   ├── cli_interface.py                # [TV3] Điều phối giao diện Console, tích hợp prompt_toolkit chống đè chữ khi gõ
│   │   └── command_handler.py              # [TV3] Bóc tách & thực thi các lệnh: /list, /chat, /send, /status, /leave, /quit
│   │
│   ├── utils/                              # 🛠️ CÔNG CỤ PHỤ TRỢ & XỬ LÝ LỖI (TV2)
│   │   ├── __init__.py
│   │   ├── logger.py                       # [TV2] Ghi log kết nối, mã lỗi, trạng thái socket có gắn nhãn thời gian
│   │   └── error_handler.py                # [TV2] Xử lý ngắt mạng đột ngột, peer crash, timeout & kiểm tra file hợp lệ
│   │
│   └── main.py                             # 🚀 [TV1] Điểm khởi chạy ứng dụng, nạp tham số CLI (--name, --port) & khởi động các luồng
│
├── downloads/                              # 📥 Thư mục mặc định chứa các file nhị phân nhận được từ bạn chat
│
├── tests/                                  # 🧪 KIỂM THỬ TỰ ĐỘNG & TEST KỊCH BẢN (TV1 + TV2 + TV3)
│   ├── __init__.py
│   ├── test_protocol.py                    # Test đóng gói/giải mã header TCP & chống phân mảnh byte stream
│   ├── test_discovery.py                   # Test phát và nhận gói tin UDP broadcast trong mạng LAN / loopback
│   └── test_file_integrity.py              # Test tính toàn vẹn file sau khi truyền nhận (so sánh mã băm SHA256)
│
├── docs/                                   # 📄 TÀI LIỆU, BÁO CÁO & BẰNG CHỨNG THỰC NGHIỆM
│   ├── Timeline_DoAn_MMT.xlsx             # 📊 Bảng Excel Master Timeline & Chi tiết To-Do List 2 tuần
│   ├── wireshark/                          # Ảnh chụp bắt gói tin Wireshark (UDP Broadcast, TCP 3-way Handshake)
│   └── presentation/                       # Báo cáo kỹ thuật đồ án (5-10 trang), Slide bảo vệ & Video demo 2 máy
│
├── .gitignore                              # Danh sách các file/folder bỏ qua không commit (downloads/*, __pycache__/)
└── requirements.txt                        # Danh sách thư viện cần thiết (prompt_toolkit, openpyxl, ...)
```

---

## 1. Quy Tắc Git & Phân Nhánh (Mô Hình 2 Tầng)

### 1.1. Cấu trúc 2 tầng nhánh
* **`main`**: Nhánh ổn định cao nhất, chứa phiên bản chạy được của cả nhóm. Tuyệt đối không commit thẳng vào `main`.
* **Nhánh cố định theo vai trò (3 thành viên, mỗi người 1 nhánh cố định suốt 2 tuần)**:
  * **Thành viên 1 (Core Network Lead)**: `network-lead`
  * **Thành viên 2 (Transfer & Protocol)**: `transfer-protocol`
  * **Thành viên 3 (UI & Client Logic)**: `ui-client`

### 1.2. Quy trình 3 bước mỗi khi Push code
1. **Kéo code mới nhất từ `main` về nhánh cá nhân** để luôn đồng bộ:
   ```bash
   git checkout <ten-nhanh-cua-ban>
   git pull origin main
   ```
2. **Lưu và đẩy code lên nhánh của mình**:
   ```bash
   git add .
   git commit -m "[Tag] Mô tả ngắn gọn tính năng vừa hoàn thành"
   git push origin <ten-nhanh-cua-ban>
   ```
3. **Mở Pull Request (PR) trên GitHub**:
   - Yêu cầu ít nhất 1 thành viên khác review và kiểm tra chạy thử trước khi bấm Merge vào `main`.

### 1.3. Chuẩn viết Commit Message
Ghi ngắn gọn theo cú pháp: `[Tag] Nội dung công việc`
* `[NET]` - Các tác vụ liên quan đến socket UDP/TCP, lắng nghe, kết nối (`network-lead`).
* `[PROTO]` - Định nghĩa bản tin, phân tích framing, truyền nhận file (`transfer-protocol`).
* `[UI]` - Giao diện dòng lệnh, bắt phím, prompt_toolkit, xử lý lệnh (`ui-client`).
* `[DOCS]` - Cập nhật báo cáo, ảnh Wireshark, slide, README.
* `[FIX]` - Sửa lỗi kết nối, vá lỗi phân mảnh gói tin hoặc crash ứng dụng.

*Ví dụ:*
- `[NET] Thêm luồng UDP Broadcast phát tín hiệu HELLO mỗi 3 giây`
- `[PROTO] Xây dựng cơ chế Framing bóc tách MSG và FILE từ TCP stream`
- `[UI] Tích hợp prompt_toolkit chống trôi chữ khi bạn chat gửi tin`

---

## 2. Quy Tắc Phân Vùng & Sở Hữu File (Tránh Xung Đột Code)

Toàn nhóm tuân thủ việc chỉnh sửa đúng các file mình phụ trách theo bảng Timeline. Đối với **3 điểm nóng (file dùng chung)**, áp dụng nghiêm ngặt các quy tắc sau:

1. **`src/network/protocol.py`** *(Thành viên 2 chủ trì, Thành viên 1 & 3 phối hợp)*:
   - File này định nghĩa Header bản tin (`MSG|<len>|<text>`, `FILE|<name>|<size>|<bytes>`).
   - Phải chốt cứng định dạng phân cách (delimiter) ngay từ **Ngày 2 của Tuần 1**. Bất kỳ ai muốn thêm tham số hay thay đổi định dạng gói tin **bắt buộc phải họp nhóm thống nhất**.
2. **`src/core/peer_manager.py`** *(Thành viên 1 chủ trì, Thành viên 3 phối hợp)*:
   - Danh sách bạn bè online là tài nguyên dùng chung giữa luồng nhận UDP và giao diện hiển thị lệnh `/list`.
   - **Bắt buộc dùng `threading.Lock()`** khi đọc và ghi vào từ điển `online_peers` để tránh lỗi Race Condition.
3. **`src/main.py`** *(Thành viên 1 chủ trì)*:
   - Điểm nối toàn bộ các luồng (Thread initialization). Thành viên khác không tùy ý chỉnh sửa logic khởi động.
4. **`requirements.txt`**:
   - Khi cài thêm thư viện mới bằng `pip install`, phải cập nhật ngay vào `requirements.txt` và báo các bạn khác chạy `pip install -r requirements.txt`.

---

## 3. Quy Chuẩn Viết Mã Nguồn (Coding Conventions)

* **Ngôn ngữ**: Python 3.9+ (Sử dụng thư viện `socket`, `threading`, `select` chuẩn của Python).
* **Quy tắc đặt tên**:
  * Tên biến, tên hàm, tên file: `snake_case` (VD: `send_presence_beacon`, `parse_message_frame`).
  * Tên lớp (Classes): `PascalCase` (VD: `PeerManager`, `TCPConnectionHandler`).
  * Hằng số cấu hình: `UPPER_SNAKE_CASE` (VD: `BROADCAST_INTERVAL = 3.0`, `PEER_TIMEOUT = 10.0`, `DEFAULT_UDP_PORT = 9999`).
* **Type Hints & Chú thích hàm (Docstring) bắt buộc**:
  ```python
  def unpack_tcp_frame(stream_buffer: bytes) -> tuple[str, bytes, bytes]:
      """
      Bóc tách 1 bản tin hoàn chỉnh từ TCP stream buffer dựa trên Header.
      Trả về: (Loại bản tin 'MSG'/'FILE'/'BYE', Nội dung dữ liệu, Buffer còn dư).
      """
  ```
* **Quản lý đa luồng & Tránh đè chữ Console**:
  - Tất cả các luồng phụ trợ (Broadcaster, UDP Listener, File Transfer) phải được đặt `daemon = True` để tắt sạch khi người dùng gõ `/quit`.
  - Mọi thao tác xuất dữ liệu ra màn hình console phải đi qua kênh đồng bộ hoặc `patch_stdout` của `prompt_toolkit`.

---

## 4. Đặc Tả Giao Thức Tự Định Nghĩa (Protocol Specification)

### 4.1. Bản tin UDP (Tìm bạn & Báo trạng thái)
Được gửi dưới dạng 1 datagram UDP độc lập:
$$\text{HELLO}|<\text{name}>|<\text{tcp\_port}>|<\text{status}>$$
* *Ví dụ:* `HELLO|Minh|5001|online` hoặc `HELLO|Lan|5002|away`

### 4.2. Bản tin TCP (Framing giải quyết dòng byte stream liên tục)
Mỗi gói tin TCP bắt buộc có Header chứa kiểu và kích thước byte cụ thể:
* **Tin nhắn chat**: `MSG|<độ_dài_byte>|<nội_dung_utf8>`
  * *Ví dụ:* `MSG|12|Hello World!`
* **Truyền nhận File**: `FILE|<tên_file>|<kích_thước_byte>|<dữ_liệu_nhị_phân>`
* **Báo ngắt kết nối**: `BYE|`

---

## 5. Phân Chia Vai Trò Nhóm 3 Người & Bảng Tiến Độ 2 Tuần

| Thành viên | Vai trò chính | Trách nhiệm cốt lõi |
| :--- | :--- | :--- |
| **Thành viên 1** | **Core Network Lead** | UDP Broadcast/Discovery, TCP Server Acceptor, Quản lý Peer & Đồng bộ khóa đa luồng (Lock). |
| **Thành viên 2** | **Transfer & Protocol** | Đóng gói bản tin Framing, Truyền file song song không chặn chat, Thanh tiến độ %, Bắt ngoại lệ socket. |
| **Thành viên 3** | **Interactive UI & QA** | Giao diện Console chống đè chữ, Bộ điều phối lệnh CLI, Hộp thư unread, Bắt gói Wireshark & Báo cáo. |

Chi tiết kế hoạch từng ngày được lưu trữ tại: [Timeline_DoAn_MMT.xlsx](file:///c:/Users/gbao1/Downloads/project%20MMT/LAN_Chat_P2P/docs/Timeline_DoAn_MMT.xlsx).
