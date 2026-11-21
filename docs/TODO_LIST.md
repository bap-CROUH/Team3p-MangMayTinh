# 📋 BẢNG KẾ HOẠCH & TIẾN ĐỘ THI CÔNG (2 TUẦN) - ĐỒ ÁN MẠNG MÁY TÍNH

Bảng kế hoạch này được đồng bộ trực tiếp với file Excel: [Timeline_DoAn_MMT.xlsx](file:///c:/Users/gbao1/Downloads/project%20MMT/LAN_Chat_P2P/docs/Timeline_DoAn_MMT.xlsx).

---

## 📅 PHẦN 1: MASTER TIMELINE (TỔNG QUAN THEO TUẦN)

| Tuần | Deadline | Trọng tâm tuần | Thành viên 1<br>(Core Network Lead) | Thành viên 2<br>(Transfer & Protocol) | Thành viên 3<br>(UI & Client Logic) | Kết quả chốt (Milestone) |
| :---: | :---: | :--- | :--- | :--- | :--- | :--- |
| **Tuần 1** | Ngày 1 – 7 | **Khởi tạo, Khung mạng P2P, UDP Discovery & Framing** | Thiết lập Socket UDP Broadcast (3s/lần), Lắng nghe cổng 9999, Quản lý danh sách Online Peer & Timeout 10s | Định nghĩa Protocol Framing (Header MSG\|FILE\|BYE), Tạo TCP Echo Client/Server, Viết cơ chế đọc đúng byte stream | Xây dựng luồng nhập lệnh CLI (/list, /help, /quit), Tích hợp prompt_toolkit chống đè chữ khi gõ | **Chốt Milestone 1 & 2**: Nhận diện peer qua UDP broadcast, gửi nhận bản tin TCP cơ bản có framing |
| **Tuần 2** | Ngày 8 – 14 | **Hoàn thiện P2P Chat, File Transfer, Wireshark & Báo cáo** | Xây dựng TCP Acceptor đa luồng, Quản lý kết nối P2P trực tiếp giữa các bạn chat, Xử lý peer crash / disconnect | Phát triển tính năng /send file trên luồng riêng, Thanh tiến độ %, Tự động lưu thư mục downloads/, Xử lý file lỗi | Hoàn thiện lệnh /chat, /leave, /status, Cơ chế Unread Notification, Bắt gói tin Wireshark, Viết báo cáo & Slide demo | **Chốt Milestone 3, 4, 5**: Chat & Gửi file song song mượt mà, Báo cáo kỹ thuật + Wireshark + Video demo 2 máy |

---

## 📝 PHẦN 2: CHI TIẾT TO-DO LIST HÀNG NGÀY

### TUẦN 1: NỀN TẢNG MẠNG, UDP DISCOVERY & ĐỊNH HÌNH GIAO THỨC
* [x] **Ngày 2** | **Toàn nhóm (Lead: TV1)**: Thống nhất cấu trúc thư mục, quy tắc Git 2 tầng, tạo Git repo và file README/CONTRIBUTING  
  *(File: `README.md`, `.gitignore` • Output: Repo GitHub chuẩn chỉ, phân nhánh thành công)*
* [x] **Ngày 3** | **Thành viên 2**: Đặc tả định dạng bản tin UDP (`HELLO|name|port|status`) và TCP Header (`MSG`, `FILE`, `BYE`)  
  *(File: `src/network/protocol.py` • Output: Module đóng gói và bóc tách Header chuẩn xác)*
* [ ] **Ngày 4** | **Thành viên 1**: Viết socket UDP broadcast phát sóng mỗi 3s và luồng lắng nghe trên cổng 9999  
  *(File: `src/network/udp_discovery.py` • Output: Tự động phát hiện các máy đang online trong LAN)*
* [ ] **Ngày 5** | **Thành viên 1**: Xây dựng bảng lưu danh sách peer online/away, kiểm tra timeout 10s tự động xóa peer offline  
  *(File: `src/core/peer_manager.py` • Output: Danh sách bạn bè tự cập nhật theo thời gian thực)*
* [ ] **Ngày 5** | **Thành viên 3**: Tạo màn hình console với `prompt_toolkit`, xử lý nhập lệnh cơ bản `/help`, `/list`, `/quit`  
  *(File: `src/ui/cli_interface.py` • Output: Console không bị vỡ giao diện, phím bấm nhạy)*
* [ ] **Ngày 6** | **Thành viên 2**: Viết TCP Socket truyền nhận đảm bảo đọc đủ số byte từ byte stream không bị phân mảnh  
  *(File: `src/network/tcp_handler.py` • Output: Truyền nhận bản tin không bị nuốt chữ / dính gói)*
* [ ] **Ngày 7** | **Toàn nhóm**: Họp nhóm test tích hợp UDP Discovery + TCP Echo trên 2 máy hoặc 2 terminal  
  *(File: `tests/test_milestone1.py` • Output: Đạt 100% Milestone 1 & 2 đề bài yêu cầu)*

---

### TUẦN 2: P2P CHAT, TRUYỀN FILE SONG SONG, BẮT GÓI WIRESHARK & BÁO CÁO
* [ ] **Ngày 9** | **Thành viên 1 & 3**: Xây dựng luồng TCP Acceptor, mở phiên chat `/chat <name>`, chuyển trạng thái chat  
  *(File: `src/network/tcp_server.py`, `src/ui/cli_interface.py` • Output: Hai máy chat qua lại 2 chiều ổn định)*
* [ ] **Ngày 10** | **Thành viên 3**: Xử lý tin nhắn đến từ người khác khi đang trong phiên chat khác, đếm số tin unread  
  *(File: `src/core/message_store.py` • Output: Hiện thông báo `[*] New message from X (1 unread)`)*
* [ ] **Ngày 11** | **Thành viên 2**: Tạo luồng gửi file riêng qua lệnh `/send <file>`, chia chunk nhị phân và gửi qua TCP  
  *(File: `src/network/file_transfer.py` • Output: Gửi nhận file không làm treo màn hình chat)*
* [ ] **Ngày 11** | **Thành viên 2 & 3**: Thanh tiến độ % hiển thị trên console, tự động lưu file tải về vào thư mục `downloads/`  
  *(File: `src/network/file_transfer.py`, `downloads/` • Output: File nhận về nguyên vẹn mã MD5/SHA256)*
* [ ] **Ngày 12** | **Thành viên 1 & 2**: Xử lý ngắt mạng đột ngột, peer crash, timeout, gửi file không tồn tại, dọn file rác  
  *(File: `src/utils/error_handler.py` • Output: Hệ thống chạy mượt mà, không bao giờ bị crash văng app)*
* [ ] **Ngày 13** | **Thành viên 3 & 1**: Dùng Wireshark bắt gói UDP Broadcast và TCP 3-way handshake khi chat và gửi file  
  *(File: `docs/wireshark/` • Output: Bộ ảnh chụp gói tin phân tích chi tiết từng trường header)*
* [ ] **Ngày 14** | **Toàn nhóm (Lead: TV3)**: Hoàn thiện Báo cáo kỹ thuật (5-10 trang), Slide thuyết trình, Video demo 2 máy  
  *(File: `docs/BAO_CAO_DO_AN.docx`, `docs/slide.pptx` • Output: Sẵn sàng nộp bài và bảo vệ đạt điểm tối đa 100%)*
