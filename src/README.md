# LAN Chat & File Sharing (TCP/UDP Socket)

Ứng dụng chat và chia sẻ file P2P (Peer-to-Peer) chạy trên môi trường dòng lệnh (CLI) trong mạng LAN/Wi-Fi, sử dụng kết hợp giao thức **UDP** (phát hiện người dùng, cập nhật trạng thái) và **TCP** (chat tin cậy, truyền file đa luồng).

## 1. Yêu cầu hệ thống & Cài đặt
- Python 3.8 trở lên.
- Cài đặt thư viện giao diện CLI:
  ```bash
  pip install prompt_toolkit

## Cách chạy chương trình
- Chạy trên 2 máy khác nhau (cùng mạng Wi-Fi/LAN)

Máy 1:
python lanchat.py --name Quan --port 5000

Máy 2:
python lanchat.py --name Minh --port 5000

- Chạy thử nhiều instance trên cùng 1 máy
python lanchat.py --name Quan --port 5001
python lanchat.py --name Minh --port 5002
## Cácn lệnh hỗ trợ
Lệnh	                Chức năng
/list	                Hiển thị danh sách người dùng đang online
/chat <name|number>	    Kết nối và mở khung chat với người dùng
<nội dung>	            Gửi tin nhắn tới đối tác đang chat
/send <đường_dẫn_file>	Gửi file chạy nền (lưu vào thư mục downloads/)
/leave	                Thoát khỏi cuộc trò chuyện hiện tại
/status <online|away>	Đổi trạng thái hiển thị
/help	                Xem danh sách lệnh
/quit	                Thoát chương trình