import argparse
from prompt_toolkit import PromptSession
from prompt_toolkit.patch_stdout import patch_stdout

from config import DEFAULT_BCAST, UDP_PORT
from discovery import PeerDiscovery
from chat_manager import ChatManager


def print_help():
    print("Available commands:")
    print("  /list                 - Show online users")
    print("  /chat <name|number>   - Open a chat with a user")
    print("  <any text>            - Send message to current chat partner")
    print("  /send <file>          - Send a file to current chat partner")
    print("  /leave                - Leave the current chat")
    print("  /status <online|away> - Change your status")
    print("  /help                 - Show all commands")
    print("  /quit                 - Exit the program")


def resolve_peer(target: str, online_peers: list):
    """Tìm peer theo số thứ tự (1, 2, ...) hoặc theo tên."""
    if target.isdigit():
        idx = int(target) - 1
        if 0 <= idx < len(online_peers):
            return online_peers[idx]
        return None
    for name, info in online_peers:
        if name.lower() == target.lower():
            return (name, info)
    return None


def main():
    parser = argparse.ArgumentParser(description="LAN Chat & File Sharing")
    parser.add_argument("--name", required=True, help="Your display name")
    parser.add_argument("--port", type=int, default=5000, help="Your TCP port")
    parser.add_argument("--bcast", default=DEFAULT_BCAST, help="Broadcast IP (use 127.255.255.255 if offline)")
    args = parser.parse_args()

    discovery = PeerDiscovery(args.name, args.port, args.bcast)
    chat = ChatManager(args.name, args.port)

    discovery.start()
    chat.start()

    print(f"[*] Listening on TCP port {args.port}")
    print(f"[*] Broadcasting presence on UDP port {UDP_PORT}")
    print("[*] Type /help to see commands.")

    session = PromptSession()

    with patch_stdout():
        while True:
            try:
                text = session.prompt("> ").strip()
            except (KeyboardInterrupt, EOFError):
                break

            if not text:
                continue

            if text.startswith("/"):
                parts = text.split(maxsplit=1)
                cmd = parts[0].lower()
                arg = parts[1].strip() if len(parts) > 1 else ""

                if cmd == "/quit":
                    break
                elif cmd == "/help":
                    print_help()
                elif cmd == "/list":
                    peers = discovery.get_online_list()
                    if not peers:
                        print("[*] No other users online.")
                    else:
                        for idx, (name, info) in enumerate(peers, start=1):
                            print(f"  {idx}. {name:<10} ({info['ip']}:{info['tcp_port']})  {info['status']}")
                elif cmd == "/status":
                    if arg in ("online", "away"):
                        discovery.set_status(arg)
                        print(f"[*] Status changed to {arg}")
                    else:
                        print("[!] Usage: /status <online|away>")
                elif cmd == "/chat":
                    if not arg:
                        print("[!] Usage: /chat <name|number>")
                        continue
                    peers = discovery.get_online_list()
                    found = resolve_peer(arg, peers)
                    if not found:
                        print(f"[!] User '{arg}' not found online. Run /list to check.")
                    else:
                        peer_name, info = found
                        chat.connect_to(peer_name, info["ip"], info["tcp_port"])
                elif cmd == "/send":
                    if not arg:
                        print("[!] Usage: /send <filepath>")
                        continue
                    partner = chat.current_partner
                    if not partner:
                        print("[!] Not in a chat. Use /chat <name|number> first.")
                        continue
                    peers = discovery.get_online_list()
                    found = resolve_peer(partner, peers)
                    if not found:
                        print(f"[!] {partner} is currently offline.")
                    else:
                        _, info = found
                        # Bỏ dấu ngoặc kép nếu người dùng kéo thả file vào terminal
                        filepath = arg.strip('"').strip("'")
                        chat.send_file(partner, info["ip"], info["tcp_port"], filepath)
                elif cmd == "/leave":
                    chat.leave_chat()
                else:
                    print("[!] Unknown command. Type /help for a list of commands.")
            else:
                chat.send_chat_message(text)

    chat.stop()
    discovery.stop()
    print("[*] Bye!")


if __name__ == "__main__":
    main()