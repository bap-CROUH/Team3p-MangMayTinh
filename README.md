# Ứng Dụng LAN Chat & Chia Sẻ File P2P (TCP & UDP Native Sockets)

**Đồ Án Môn Mạng Máy Tính — Nhóm Team3p-MangMayTinh (3 thành viên)**  
*Kho lưu trữ chính thức:* `https://github.com/bap-CROUH/Team3p-MangMayTinh`

Ứng dụng trò chuyện ngang hàng (**Peer-to-Peer LAN Chat & File Sharing**) chạy trên giao diện dòng lệnh (Console CLI), sử dụng **Python Native Socket API (`socket`, `threading`)** kết hợp cả hai giao thức tầng giao vận đúng theo thế mạnh của từng giao thức:
- **UDP Socket (Broadcast, cổng `9999`)**: Tự động phát hiện bạn bè trong mạng LAN (mỗi `3 giây`), cập nhật trạng thái `online` / `away` và loại bỏ peer mất tín hiệu sau `10 giây` timeout.
- **TCP Socket (Reliable Byte Stream)**: Trò chuyện 2 chiều thời gian thực với cơ chế đóng khung bản tin (**Message Framing**), lưu thông báo tin nhắn chưa đọc (**Unread Count**) từ nhiều peer, và truyền file nhị phân song song trên kết nối riêng có hiển thị `%` tiến độ mà không làm nghẽn luồng chat.

---

## 1. Đối Chiếu Yêu Cầu Đề Bài & Barem Chấm Điểm (100%)

| STT | Tiêu chí chấm điểm (Grading Rubric) | Trọng số | Module đảm nhiệm | Giải pháp kỹ thuật đạt điểm tối đa |
| :-: | :--- | :-: | :--- | :--- |
| 1 | **UDP Discovery, Online List, Status** | **15%** | `src/discovery.py` | Phát beacon `HELLO` mỗi `3s` (UDP `9999`, `SO_REUSEADDR`/`SO_BROADCAST`), quét xóa sau `10s`, hỗ trợ `/status online\|away`, chỉ báo khi peer mới vào/ra hoặc đổi trạng thái. |
| 2 | **TCP Chat (Send/Receive mọi lúc, đa Peer)** | **20%** | `src/chat_node.py` | Gửi/nhận bất đồng bộ 2 chiều, tái sử dụng kết nối mở sẵn, lưu hộp thư chờ & báo `[*] New message from X (N unread)` khi đang chat với người khác. |
| 3 | **File Transfer có `%` tiến độ, lưu đúng** | **15%** | `src/file_transfer.py` | Mở **kết nối TCP riêng** trên thread riêng (không bao giờ khóa/nghẽn socket chat), stream từng khối `64KB` vào `downloads/`, báo tiến độ theo mốc `%` và kiểm tra `SHA256`. |
| 4 | **Console UI không vỡ chữ khi đang gõ** | **15%** | `src/main.py` | Dùng `prompt_toolkit` (`PromptSession` + `patch_stdout()`) kết hợp khóa in màn hình để giữ nguyên dòng `> ` đang gõ dở khi có tin nhắn/thông báo đẩy về. |
| 5 | **Thiết kế Giao thức & Message Framing** | **10%** | `src/protocol.py` | Tách dòng Header kết thúc bằng `\n` + đọc chính xác số byte payload bằng vòng lặp `recv_exact(sock, n)`, xử lý triệt để hiện tượng dính gói / cắt mảnh TCP. |
| 6 | **Xử lý lỗi & Độ ổn định (Error Handling)** | **10%** | Toàn bộ `src/` | Peer tắt đột ngột không sập app; kết nối peer offline báo lỗi gọn; đứt mạng khi tải file tự xóa file `.part`; lọc `os.path.basename` chống Path Traversal; xử lý file `0 byte`. |
| 7 | **Báo cáo kỹ thuật & Ảnh chụp Wireshark** | **10%** | `docs/` | Báo cáo 5–10 trang (kiến trúc, 6 luồng, giao thức, lỗi & hướng giải quyết) + ảnh Wireshark bắt gói UDP Broadcast & TCP 3-way Handshake. |
| 8 | **Demo trực tiếp (2+ máy) & Chất lượng Code** | **5%** | Cả nhóm | Cấu trúc 6 file phẳng gọn sạch (~400–500 dòng), hằng số tập trung ở `config.py`, dễ đọc hiểu toàn bộ và sửa live-coding nhanh khi vấn đáp. |

---

## 2. Cấu Trúc Thư Mục Tối Giản (6 File Python Phẳng — Dễ Hiểu & Dễ Vấn Đáp)

Thay vì chia nhỏ quá nhiều thư mục con gây rối khi đọc chéo và vấn đáp, toàn bộ mã nguồn được tổ chức phẳng thành **6 module rõ ràng** trong `src/`:

```text
Team3p-MangMayTinh/
├── src/
│   ├── config.py              # [Chung] Tập trung toàn bộ hằng số (UDP_PORT=9999, 3s, 10s, CHUNK_SIZE=64KB...)
│   ├── protocol.py            # [TV2] Đóng gói/giải mã Header (HELLO, INTRO, MSG, FILE, BYE) & recv_line / recv_exact
│   ├── discovery.py           # [TV1] Luồng phát UDP Broadcast (3s), Luồng nghe UDP & Quét xóa peer timeout (10s)
│   ├── chat_node.py           # [TV1] TCP Acceptor, quản lý kết nối chat P2P 2 chiều, lịch sử chat & bộ đếm Unread
│   ├── file_transfer.py       # [TV2] Luồng gửi/nhận file trên kết nối TCP riêng, thanh tiến độ %, lưu .part & SHA256
│   └── main.py                # [TV3] Điểm khởi chạy CLI (--name, --port, --bcast), PromptSession & xử lý 8 lệnh
│
├── downloads/                 # Thư mục mặc định lưu các file nhận được (tự động dọn sạch .part nếu lỗi)
│
├── tests/                     # Bộ kiểm thử tự động (unittest)
│   ├── test_protocol.py       # Kiểm thử TCP framing (dính gói, cắt lẻ từng byte, tiếng Việt UTF-8, ký tự '|')
│   ├── test_discovery.py      # Kiểm thử phát/nhận UDP broadcast, lọc self-beacon theo peer_id & timeout 10s
│   └── test_file_transfer.py  # Kiểm thử truyền file (0 byte, file lớn, trùng tên, chống '../', xóa .part khi ngắt)
│
├── docs/                      # Tài liệu kế hoạch, ảnh chụp Wireshark & Báo cáo kỹ thuật
│   ├── TODO_LIST.md           # Bảng phân công chi tiết kèm hướng dẫn code từng hàm cho 3 thành viên
│   ├── KeHoach_DoAn_MMT_Den_08_12.xlsx  # Bảng tiến độ Excel 5 Sheet & kịch bản ôn tập Live-coding
│   ├── wireshark/             # Ảnh chụp gói tin Wireshark (UDP Broadcast 9999 & TCP 3-Way Handshake)
│   └── presentation/          # Báo cáo đồ án (5–10 trang) & Slide thuyết trình
│
├── .gitignore
└── requirements.txt           # Duy nhất 1 thư viện giao diện: prompt_toolkit
```

---

## 3. Hướng Dẫn Cài Đặt, Khởi Chạy & Kiểm Thử (Install, Run & Test)

### 3.1. Yêu cầu môi trường & Cài đặt
- **Python**: Phiên bản `3.9` trở lên (hỗ trợ Windows, macOS, Linux).
- Cài đặt thư viện giao diện dòng lệnh chống đè chữ:
  ```bash
  pip install -r requirements.txt
  ```

### 3.2. Cách chạy kiểm thử trên 1 máy tính (Nhiều cửa sổ Terminal)
Mở 3 cửa sổ Terminal tại thư mục gốc của dự án và chạy với cổng TCP (`--port`) khác nhau:
```bash
# Terminal 1 - Người dùng Quan
python src/main.py --name Quan --port 5001

# Terminal 2 - Người dùng Minh
python src/main.py --name Minh --port 5002

# Terminal 3 - Người dùng Huy
python src/main.py --name Huy --port 5003
```
> **Lưu ý khi máy tính đang Offline (không kết nối Wi-Fi/LAN):** Thêm tham số `--bcast 127.255.255.255` vào câu lệnh trên để các tiến trình quảng bá qua giao diện loopback cục bộ.

### 3.3. Cách chạy thực tế trên 2+ máy tính cùng mạng LAN / Wi-Fi
1. **Cấp quyền Firewall (Quan trọng trên Windows):** Khi chạy lần đầu và thấy bảng *Windows Defender Firewall*, tích chọn cả **Private networks** và **Public networks** rồi nhấn **Allow access** cho Python (nếu bị chặn sẽ không nhận được gói UDP Broadcast cổng `9999`).
2. **Chạy trên từng máy:**
   ```bash
   # Máy 1
   python src/main.py --name Quan --port 5000

   # Máy 2
   python src/main.py --name Minh --port 5000
   ```
3. **Xử lý máy cài nhiều Card mạng ảo (WSL, VMware, VirtualBox, Radmin VPN):** Trên Windows có nhiều card ảo, gói `255.255.255.255` đôi khi bị đẩy nhầm vào card ảo thay vì Wi-Fi thật. Hãy xem IP Wi-Fi của máy (ví dụ `192.168.1.15`, subnet `/24`) và chỉ định thẳng địa chỉ broadcast của mạng LAN:
   ```bash
   python src/main.py --name Quan --port 5000 --bcast 192.168.1.255
   ```

### 3.4. Danh sách Lệnh Điều Khiển CLI (Mục 4.1 Đề bài)

| Cú pháp lệnh | Chức năng chi tiết |
| :--- | :--- |
| `/list` | Hiển thị danh sách người dùng đang online kèm số thứ tự, Tên, `IP:TCP_Port`, trạng thái (`online`/`away`) và số tin chưa đọc (nếu có). |
| `/chat <tên\|số>` | Mở phiên trò chuyện TCP với người dùng theo tên hoặc số thứ tự trong `/list` (đồng thời hiển thị các tin nhắn chưa đọc của người đó). |
| `<nội dung bất kỳ>` | Gửi tin nhắn văn bản tới người đang trò chuyện hiện tại (không bắt đầu bằng dấu `/`). |
| `/send <đường_dẫn_file>` | Gửi file nhị phân tới người đang chat trên luồng & kết nối TCP riêng (vừa tải file vừa tiếp tục gõ chat bình thường). |
| `/leave` | Đóng phiên trò chuyện hiện tại (gửi báo hiệu `BYE`), quay về sảnh chờ chính. |
| `/status <online\|away>` | Đổi trạng thái hiển thị của bản thân và phát cập nhật qua UDP Broadcast. |
| `/help` | Hiển thị bảng hướng dẫn nhanh các lệnh. |
| `/quit` | Gửi `BYE` đóng các kết nối đang mở, dọn dẹp file `.part` dở dang và thoát chương trình an toàn. |

### 3.5. Chạy bộ Unit Tests tự động
```bash
python -m unittest discover -s tests -v
```

---

## 4. Mô Hình Đa Luồng (Thread Model) & Đồng Bộ Dữ Liệu

Chương trình vận hành **6 vai trò luồng** đúng theo Mục 5.1 của đề bài (bản cập nhật `09/11/2026`):

| Luồng (Thread) | Chờ sự kiện | Trách nhiệm chính |
| :--- | :--- | :--- |
| **1. Main Thread** | Bàn phím (`PromptSession`) | Đọc lệnh người dùng, điều phối `/list`, `/chat`, `/send`, `/leave`, `/status`, `/quit` và gửi tin nhắn chat. |
| **2. UDP Broadcaster** | Bộ đếm thời gian (`3s`) | Phát gói tin hiện diện `HELLO` qua cổng UDP `9999` (và phát ngay lập tức khi đổi `/status`). |
| **3. UDP Listener (+ Cleaner)** | Datagram cổng `9999` & chu kỳ `1s` | Cập nhật bảng `online_peers`, thông báo peer online/offline và xóa peer quá `10s` không phản hồi. |
| **4. TCP Acceptor** | Kết nối TCP mới đến | Chấp nhận kết nối đến và khởi tạo một luồng `TCP Receiver` riêng cho kết nối đó. |
| **5. TCP Receiver (1 luồng / kết nối)** | Socket của kết nối đó | Đọc dòng đầu tiên phân loại: nếu là **kết nối Chat** (`INTRO`) thì nhận `MSG`/`BYE`; nếu là **kết nối File** (`FILE`) thì lưu file vào `downloads/`. |
| **6. File Sender (1 luồng / lần gửi)** | Đọc đĩa & gửi chunk `64KB` | Mở kết nối TCP riêng tới bạn chat, truyền dữ liệu file, hiển thị `%` tiến độ mà không chặn luồng Chat. |

- **An toàn đa luồng (Thread-safety):** Danh sách `online_peers`, từ điển kết nối `active_chats`, lịch sử chat và bộ đếm `unread_counts` đều được bảo vệ nghiêm ngặt bằng `threading.Lock()`.

---

## 5. Đặc Tả Giao Thức Ứng Dụng & Các Cơ Chế Chống Lỗi Trọng Yếu

### 5.1. Bản tin UDP (1 Datagram độc lập — Cổng `9999`)
```text
HELLO|<peer_id>|<name>|<tcp_port>|<status>
```
- Ví dụ: `HELLO|a1b2c3d4|Quan|5001|online`
- **Chống trùng tên & tự nhận gói của chính mình:** Mỗi tiến trình sinh ngẫu nhiên một `peer_id` (8 ký tự hex) lúc khởi chạy. Bộ nghe UDP bỏ qua gói có `peer_id == my_peer_id`, giúp 2 máy trùng tên hoặc nhiều terminal trên cùng 1 máy vẫn nhận diện nhau chính xác 100%.

### 5.2. Bản tin TCP có Đóng Khung (Line Header `\n` + Exact Byte Payload)
Vì TCP là dòng byte liên tục không có ranh giới bản tin, mọi gói tin đều dùng **dòng Header kết thúc bằng `\n`** (đọc qua `recv_line` giới hạn tối đa `4096 bytes`), theo sau là phần thân đọc chính xác từng byte qua `recv_exact(sock, n)`:

1. **Định danh phiên Chat khi vừa mở kết nối (`INTRO`)**:
   ```text
   INTRO|<peer_id>|<name>|<listen_tcp_port>\n
   ```
   *Giải quyết triệt để lỗi cổng tạm (ephemeral port):* Khi A kết nối tới B trên cùng máy `127.0.0.1`, cổng nguồn hệ điều hành cấp cho A là cổng ngẫu nhiên (vd `54321`) chứ không phải cổng lắng nghe của A (`5001`). Nhờ gói `INTRO`, B biết chính xác người vừa kết nối là ai và tái sử dụng chung 1 kết nối TCP hai chiều duy nhất.

2. **Tin nhắn văn bản (`MSG`)**:
   ```text
   MSG|<byte_length>\n<utf8_bytes>
   ```
   *Ví dụ:* `MSG|15\nXin chào a|b!` — Nội dung nằm sau `\n` và đọc theo đúng `byte_length` byte UTF-8 nên người dùng gõ dấu `|`, tiếng Việt hay ký tự đặc biệt đều không bao giờ làm vỡ Header.

3. **Kết thúc phiên Chat (`BYE`)**:
   ```text
   BYE\n
   ```
   Báo cho đối phương đóng phiên chat hiện tại và trở về dấu nhắc chính (không làm sập chương trình).

4. **Truyền File trên kết nối TCP riêng (`FILE` & `FILE_OK`)**:
   ```text
   FILE|<sender_name>|<safe_filename>|<file_size>|<sha256_hex>\n<raw_file_bytes>
   ```
   - **Không tràn RAM & hiện tiến độ mượt:** Đọc/ghi trực tiếp từng khối `64KB` xuống file tạm `downloads/<safe_filename>.part`; chỉ in tiến độ tại các mốc phần trăm (mỗi `20%` – `25%` và `100%`) để không làm trôi màn hình chat.
   - **Bảo mật & Chống lỗi biên:** Tên file được lọc qua `os.path.basename()` chống tấn công ghi đè thư mục cha (`../`); nếu trùng tên tự động thêm hậu tố `_(1)`; nếu `file_size == 0` tạo file rỗng và báo `100%` ngay (tránh lỗi chia cho `0`).
   - **Đảm bảo toàn vẹn & dọn rác:** Khi nhận đủ `file_size` byte và khớp mã băm `SHA256`, bên nhận đổi tên `.part` thành file hoàn chỉnh rồi gửi lại `FILE_OK\n` trước khi đóng socket. Nếu đứt mạng giữa chừng hoặc sai mã băm, khối `finally` tự động xóa sạch file `.part`.

---

## 6. Quy Tắc Làm Việc Nhóm & Phân Nhánh Git

### 6.1. Cấu trúc nhánh chuẩn
- **`main`**: Nhánh ổn định chứa phiên bản ghép nối chạy được của cả nhóm (chỉ cập nhật qua Pull Request đã test).
- **3 nhánh phát triển theo đúng vai trò thành viên**:
  - **Thành viên 1 (Core Network — UDP & TCP Chat)**: nhánh `network-lead` (`src/discovery.py`, `src/chat_node.py`, phối hợp `src/config.py`)
  - **Thành viên 2 (Protocol Framing & File Transfer)**: nhánh `transfer-protocol` (`src/protocol.py`, `src/file_transfer.py`, phối hợp `src/config.py`)
  - **Thành viên 3 (Console UI, CLI & Báo cáo/Wireshark)**: nhánh `ui-client` (`src/main.py`, `docs/`)

### 6.2. Tài liệu Kế hoạch & Phân công Chi tiết
- Hướng dẫn từng bước viết code và mục tiêu từng nhiệm vụ: xem tại [docs/TODO_LIST.md](docs/TODO_LIST.md).
- Lịch trình chi tiết theo ngày (hoàn tất code & báo cáo trước `08/12`, tự kiểm tra & luyện vấn đáp `09/12 – 12/12`): xem tại [docs/KeHoach_DoAn_MMT_Den_08_12.xlsx](docs/KeHoach_DoAn_MMT_Den_08_12.xlsx).
