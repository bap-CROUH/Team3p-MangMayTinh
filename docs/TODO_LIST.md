# 📋 BẢNG KẾ HOẠCH & TIẾN ĐỘ THI CÔNG (2 TUẦN) - ĐỒ ÁN MẠNG MÁY TÍNH

File Excel gốc tương ứng (có 4 Sheet riêng biệt): [Timeline_DoAn_MMT.xlsx](file:///c:/Users/gbao1/Downloads/project%20MMT/Team3p-MangMayTinh/docs/Timeline_DoAn_MMT.xlsx)

---

## 📑 MỤC LỤC CÁC SHEET THEO NHÓM CÔNG VIỆC

1. [Sheet 1: Tổng Quan (Master Timeline)](#1-sheet-tổng-quan-master-timeline)
2. [Sheet 2: Thành Viên 1 - Core Network Lead](#2-sheet-thành-viên-1---core-network-lead)
3. [Sheet 3: Thành Viên 2 - Transfer & Protocol](#3-sheet-thành-viên-2---transfer--protocol)
4. [Sheet 4: Thành Viên 3 - Interactive UI & Client Logic](#4-sheet-thành-viên-3---interactive-ui--client-logic)

---

## 1. SHEET TỔNG QUAN (MASTER TIMELINE)

| Tuần | Deadline | Trọng tâm tuần | Thành viên 1<br>(Core Network Lead) | Thành viên 2<br>(Transfer & Protocol) | Thành viên 3<br>(UI & Client Logic) | Kết quả chốt (Milestone) |
| :---: | :---: | :--- | :--- | :--- | :--- | :--- |
| **Tuần 1** | Ngày 1 – 7 | **Nền tảng, Khung mạng P2P, UDP Discovery & Framing** | Cấu hình Socket UDP Broadcast (3s/lần), Lắng nghe cổng 9999, Quản lý danh sách Online Peer & Timeout 10s | Thiết kế Protocol Framing (Header MSG\|FILE\|BYE), Tạo TCP Echo Client/Server, Cơ chế đọc đúng byte stream | Xây dựng luồng nhập lệnh CLI (/list, /help, /quit), Tích hợp prompt_toolkit chống đè chữ khi gõ phím | **Milestone 1 & 2**: Phát hiện peer tự động qua UDP broadcast, trao đổi bản tin TCP có framing chuẩn |
| **Tuần 2** | Ngày 8 – 14 | **P2P Chat đa luồng, File Transfer, Wireshark & Báo cáo** | Xây dựng TCP Acceptor đa luồng, Quản lý kết nối P2P trực tiếp giữa các bạn chat, Xử lý peer crash / disconnect | Phát triển tính năng /send file trên luồng riêng, Thanh tiến độ %, Tự lưu thư mục downloads/, Xử lý file lỗi | Hoàn thiện lệnh /chat, /leave, /status, Cơ chế Unread Notification, Bắt gói tin Wireshark, Viết báo cáo & Slide demo | **Milestone 3, 4, 5**: Chat & Gửi file song song không nghẽn, Báo cáo kỹ thuật + Wireshark + Video demo 2 máy |

---

## 2. SHEET THÀNH VIÊN 1 - CORE NETWORK LEAD

> **Khu vực phụ trách**: `src/main.py`, `src/network/udp_discovery.py`, `src/core/peer_manager.py`, `src/network/tcp_server.py`.

| Tuần | Deadline | Mục tiêu chung | Nhiệm vụ cụ thể | Done | File làm việc | Output bàn giao |
| :---: | :---: | :--- | :--- | :---: | :--- | :--- |
| **Tuần 1** | Ngày 2 | Khởi tạo kiến trúc | Thống nhất kiến trúc P2P, tạo khung thư mục src/core, src/network và cấu hình Git repo | `[x]` | `src/main.py, .gitignore` | Khung ứng dụng chạy được lệnh python main.py |
| **Tuần 1** | Ngày 3 | Thiết lập Socket UDP | Viết socket UDP phát sóng presence beacon mỗi 3s (SO_BROADCAST, SO_REUSEADDR) trên cổng 9999 | `[ ]` | `src/network/udp_discovery.py` | Broadcast đều đặn HELLO\|name\|port\|status |
| **Tuần 1** | Ngày 4 | Lắng nghe UDP Broadcast | Tạo luồng chạy ngầm nhận gói tin UDP từ các máy khác, phân tách thông tin peer | `[ ]` | `src/network/udp_discovery.py` | Nhận diện tức thì khi có peer mới xuất hiện trong LAN |
| **Tuần 1** | Ngày 5 | Quản lý Online Peer List | Lưu trữ danh sách Online Peers (IP, port, status, last_seen), bảo vệ bằng threading.Lock | `[ ]` | `src/core/peer_manager.py` | Bộ nhớ lưu danh sách an toàn không bị Race Condition |
| **Tuần 1** | Ngày 6 | Quét Timeout 10s | Tạo luồng timer quét định kỳ danh sách peer, xóa peer nào sau 10s không gửi heartbeat | `[ ]` | `src/core/peer_manager.py` | Tự động phát hiện và xóa peer offline khỏi danh sách |
| **Tuần 1** | Ngày 7 | Nghiệm thu Tuần 1 | Kiểm tra chéo UDP Discovery trên 2 máy thật trong mạng LAN hoặc 2 terminal khác port | `[ ]` | `tests/test_discovery.py` | Hoàn tất 100% mục tiêu Milestone 1 & 2 |
| **Tuần 2** | Ngày 8 | TCP Server Acceptor | Xây dựng luồng TCP Server lắng nghe cổng chat, chấp nhận kết nối P2P từ các peer khác | `[ ]` | `src/network/tcp_server.py` | Mỗi kết nối đến được spawn 1 receiver thread riêng |
| **Tuần 2** | Ngày 10 | Quản lý đa kết nối P2P | Quản lý danh sách active socket kết nối với nhiều bạn chat cùng lúc, điều phối gửi tin | `[ ]` | `src/network/tcp_server.py` | Hỗ trợ kết nối đồng thời nhiều peer ổn định |
| **Tuần 2** | Ngày 12 | Bảo vệ luồng & Peer Crash | Xử lý đóng socket an toàn khi peer ngắt mạng, peer tắt đột ngột, giải phóng tài nguyên | `[ ]` | `src/core/peer_manager.py` | Không bị crash ứng dụng khi peer đối phương disconnect |
| **Tuần 2** | Ngày 14 | Tổng duyệt Demo & Kịch bản | Phối hợp chạy kịch bản kết nối 2 máy tính thật trong buổi bảo vệ trước giảng viên | `[ ]` | `docs/presentation/demo_guide.md` | Kịch bản demo trơn tru, chứng minh kết nối P2P |

---

## 3. SHEET THÀNH VIÊN 2 - TRANSFER & PROTOCOL

> **Khu vực phụ trách**: `src/network/protocol.py`, `src/network/tcp_handler.py`, `src/network/file_transfer.py`, `src/utils/error_handler.py`.

| Tuần | Deadline | Mục tiêu chung | Nhiệm vụ cụ thể | Done | File làm việc | Output bàn giao |
| :---: | :---: | :--- | :--- | :---: | :--- | :--- |
| **Tuần 1** | Ngày 2 | Đặc tả định dạng bản tin | Thống nhất format gói tin UDP (HELLO) và TCP Header phân tách MSG, FILE, BYE | `[x]` | `src/network/protocol.py` | Tài liệu & module định nghĩa giao thức dùng chung |
| **Tuần 1** | Ngày 3 | Đóng gói / bóc tách Header | Viết hàm pack_message, unpack_message bóc tách chính xác độ dài byte (framing) | `[ ]` | `src/network/protocol.py` | Không bị lỗi dính gói (sticky) hoặc phân mảnh TCP |
| **Tuần 1** | Ngày 5 | TCP Stream Reader chuẩn | Viết hàm recv_exact(n_bytes) lặp recv() liên tục đến khi đủ độ dài quy định trong header | `[ ]` | `src/network/tcp_handler.py` | Đọc chính xác 100% dữ liệu không thừa không thiếu byte |
| **Tuần 1** | Ngày 6 | Test TCP Echo có Framing | Viết kịch bản test gửi chuỗi dài có dấu tiếng Việt UTF-8 qua TCP socket có framing | `[ ]` | `tests/test_protocol.py` | Test pass 100% các trường hợp chuỗi dài, ký tự đặc biệt |
| **Tuần 1** | Ngày 7 | Kiểm tra tải gói tin | Phối hợp test truyền nhận gói tin liên tục nhiều lần xem có bị nghẽn buffer không | `[ ]` | `tests/test_protocol.py` | Giao thức truyền nhận ổn định, sẵn sàng ghép nối |
| **Tuần 2** | Ngày 9 | Luồng gửi file nhị phân | Phát triển hàm send_file chạy trên luồng riêng (non-blocking) qua lệnh /send <file> | `[ ]` | `src/network/file_transfer.py` | Gửi file mượt mà, không làm đơ hay giật lag luồng chat |
| **Tuần 2** | Ngày 10 | Luồng nhận file & Lưu trữ | Đọc header FILE, đọc kích thước bytes và ghi trực tiếp vào thư mục downloads/<tên_file> | `[ ]` | `src/network/file_transfer.py, downloads/` | File nhận về đầy đủ, chính xác, không bị hỏng định dạng |
| **Tuần 2** | Ngày 11 | Thanh tiến độ (Progress Bar) | Tính toán % dữ liệu đã truyền/nhận và phát tín hiệu cập nhật ra giao diện (VD: 45%... 100%) | `[ ]` | `src/network/file_transfer.py` | Hiển thị tiến độ truyền file theo thời gian thực |
| **Tuần 2** | Ngày 12 | Xử lý file lỗi & Kiểm tra MD5 | Bắt lỗi file không tồn tại, mất mạng giữa chừng thì dọn file tạm; so sánh mã băm SHA256 | `[ ]` | `src/utils/error_handler.py` | Đảm bảo tính toàn vẹn dữ liệu, dọn rác sạch sẽ |
| **Tuần 2** | Ngày 14 | Báo cáo phần Giao thức | Soạn nội dung mục 5 trong Báo cáo: Thiết kế Protocol Framing, phân tích Byte Stream TCP | `[ ]` | `docs/BAO_CAO_DO_AN.docx` | Hoàn thành 3 trang phân tích kỹ thuật tầng giao vận |

---

## 4. SHEET THÀNH VIÊN 3 - INTERACTIVE UI & CLIENT LOGIC

> **Khu vực phụ trách**: `src/ui/cli_interface.py`, `src/ui/command_handler.py`, `src/core/message_store.py`, `docs/wireshark/`, `docs/presentation/`.

| Tuần | Deadline | Mục tiêu chung | Nhiệm vụ cụ thể | Done | File làm việc | Output bàn giao |
| :---: | :---: | :--- | :--- | :---: | :--- | :--- |
| **Tuần 1** | Ngày 2 | Khảo sát giao diện Console | Nghiên cứu option_a_prompt_toolkit.py và cấu hình patch_stdout() cho giao diện tương tác | `[x]` | `src/ui/cli_interface.py` | Môi trường console hỗ trợ async và in bất đồng bộ |
| **Tuần 1** | Ngày 4 | Bộ điều phối lệnh CLI cơ bản | Viết parser bóc tách chuỗi người dùng gõ: xử lý /help (in trợ giúp), /list (xem online), /quit | `[ ]` | `src/ui/command_handler.py` | Hệ thống lệnh CLI hoạt động chính xác theo đề bài |
| **Tuần 1** | Ngày 5 | Giao diện chống đè chữ khi gõ | Hoàn thiện cơ chế giữ nguyên dòng prompt > đang gõ dở khi có thông báo mạng đẩy về | `[ ]` | `src/ui/cli_interface.py` | Đạt 15% tiêu chí Barem giao diện không bị gián đoạn |
| **Tuần 1** | Ngày 6 | Lệnh đổi trạng thái /status | Xử lý lệnh /status <online\|away>, cập nhật biến trạng thái để TV1 phát broadcast | `[ ]` | `src/ui/command_handler.py` | Đổi trạng thái hiển thị của bản thân ngay lập tức |
| **Tuần 1** | Ngày 7 | Thẩm định giao diện Tuần 1 | Chạy thử nghiệm gõ phím liên tục trong khi mô phỏng tin nhắn dồn dập đổ về | `[ ]` | `src/ui/cli_interface.py` | Giao diện mượt mà, màu sắc đẹp mắt, không giật lag |
| **Tuần 2** | Ngày 8 | Lệnh mở chat /chat & /leave | Xử lý lệnh /chat <name\|số> để kết nối tới peer, /leave để kết thúc phiên chat hiện tại | `[ ]` | `src/ui/command_handler.py` | Chuyển đổi linh hoạt giữa màn hình sảnh và phòng chat |
| **Tuần 2** | Ngày 9 | Hộp thư chờ & Tin nhắn Unread | Khi đang chat với A mà B nhắn đến: lưu tin nhắn của B và hiện thông báo [*] New message (1 unread) | `[ ]` | `src/core/message_store.py` | Đạt 100% yêu cầu chuyển ngữ cảnh và đếm tin chưa đọc |
| **Tuần 2** | Ngày 11 | Tích hợp thanh tiến độ gửi file | Ghép nối tín hiệu tiến độ % từ TV2 hiển thị lên màn hình console không làm đè chữ | `[ ]` | `src/ui/cli_interface.py` | Thanh progress bar hiện đẹp mắt trên console |
| **Tuần 2** | Ngày 13 | Bắt gói tin Wireshark | Dùng Wireshark bắt gói UDP broadcast, bắt tay 3 bước TCP SYN-ACK và dòng dữ liệu chat/file | `[ ]` | `docs/wireshark/` | Bộ ảnh chụp màn hình Wireshark kèm chú thích chi tiết |
| **Tuần 2** | Ngày 14 | Hoàn thiện Báo cáo & Slide | Chủ trì tổng hợp Báo cáo kỹ thuật (5-10 trang), thiết kế Slide bảo vệ và kịch bản thuyết trình | `[ ]` | `docs/BAO_CAO_DO_AN.docx, docs/slide.pptx` | Bộ hồ sơ nộp bài hoàn chỉnh, chỉn chu 100% |
