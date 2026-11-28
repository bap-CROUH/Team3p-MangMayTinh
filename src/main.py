"""
Console UI & CLI entrypoint for LAN Chat & File Sharing P2P (TV3 - ui-client).

Run examples:
    python src/main.py --name Quan --port 5001
    python src/main.py --name Quan --port 5001 --bcast 127.255.255.255
"""

import argparse
import os
import sys
import threading
import uuid

# Allow flat imports (config, discovery, chat_node, file_transfer) when running `python src/main.py`
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

try:
    from prompt_toolkit import PromptSession  # type: ignore
    from prompt_toolkit.patch_stdout import patch_stdout  # type: ignore
except ImportError:
    PromptSession = None
    patch_stdout = None

try:
    import config  # type: ignore
except ImportError:
    config = None

try:
    from discovery import DiscoveryService  # type: ignore
except ImportError:
    DiscoveryService = None

try:
    from chat_node import ChatNode  # type: ignore
except ImportError:
    ChatNode = None

try:
    import file_transfer  # type: ignore
except ImportError:
    file_transfer = None


DEFAULT_TCP_PORT = 5000
DEFAULT_UDP_PORT = getattr(config, "UDP_PORT", 9999)
DEFAULT_BCAST_ADDR = "255.255.255.255"
DEFAULT_DOWNLOAD_DIR = getattr(config, "DOWNLOAD_DIR", "downloads")

HELP_TEXT = """Available commands:
  /list                   Show online peers and unread message counts
  /chat <name|number>     Start or switch chat with a peer
  <text>                  Send a message to the current chat peer
  /send <file_path>       Send a file to the current chat peer
  /leave                  Leave the current chat and return to lobby
  /status <online|away>   Update your presence status
  /help                   Show this help message
  /quit                   Disconnect cleanly and exit"""


def validate_name(name: str) -> str:
    """Validate --name so it cannot break pipe-delimited protocol headers."""
    cleaned = name.strip()
    if not cleaned:
        raise argparse.ArgumentTypeError("Name must not be empty.")
    if any(ch in cleaned for ch in ("|", "\n", "\r")):
        raise argparse.ArgumentTypeError("Name must not contain '|', '\\n', or '\\r'.")
    return cleaned


def validate_port(port_str: str) -> int:
    """Validate --port is an integer within valid TCP port range (1..65535)."""
    try:
        port = int(port_str)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Port must be an integer.") from exc
    if not (1 <= port <= 65535):
        raise argparse.ArgumentTypeError("Port must be between 1 and 65535.")
    return port


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="LAN Chat & File Sharing P2P (Native TCP & UDP Sockets)"
    )
    parser.add_argument(
        "--name",
        required=True,
        type=validate_name,
        help="Your display name (must not contain '|' or newlines)",
    )
    parser.add_argument(
        "--port",
        default=DEFAULT_TCP_PORT,
        type=validate_port,
        help=f"Local TCP listening port (default: {DEFAULT_TCP_PORT})",
    )
    parser.add_argument(
        "--bcast",
        default=DEFAULT_BCAST_ADDR,
        help=f"UDP broadcast address (default: {DEFAULT_BCAST_ADDR})",
    )
    return parser.parse_args(argv)


def cleanup_partial_downloads(download_dir: str = DEFAULT_DOWNLOAD_DIR) -> int:
    """Remove leftover *.part temporary files in downloads/ on exit."""
    removed = 0
    if not os.path.isdir(download_dir):
        return removed
    for entry in os.listdir(download_dir):
        if entry.endswith(".part"):
            full_path = os.path.join(download_dir, entry)
            try:
                if os.path.isfile(full_path):
                    os.remove(full_path)
                    removed += 1
            except OSError:
                pass
    return removed


class ConsoleClient:
    """Coordinates Console UI (PromptSession + patch_stdout) and all 8 CLI commands."""

    def __init__(
        self,
        name: str,
        tcp_port: int,
        bcast_addr: str,
        discovery=None,
        chat_node=None,
        send_file_fn=None,
        download_dir: str = DEFAULT_DOWNLOAD_DIR,
    ):
        self.name = name
        self.tcp_port = tcp_port
        self.bcast_addr = bcast_addr
        self.status = "online"
        self.download_dir = download_dir

        self.ui_lock = threading.Lock()
        self.discovery = discovery
        self.chat_node = chat_node
        self.send_file_fn = send_file_fn

        self.peer_id = getattr(discovery, "peer_id", None) or uuid.uuid4().hex[:8]
        self.last_listed_peers = []
        self._current_peer = None  # Cached peer dict for dynamic prompt & /send

    def ui_print(self, message: str) -> None:
        """Thread-safe print callback passed to discovery, chat_node, and file_transfer."""
        with self.ui_lock:
            print(message, flush=True)

    def get_prompt_text(self) -> str:
        """Dynamic prompt: '> ' in lobby, '[Chat: <name>] > ' inside a chat."""
        peer = self._get_active_chat_peer()
        if peer:
            return f"[Chat: {peer['name']}] > "
        return "> "

    def _get_online_peers_list(self) -> list:
        """Normalize discovery.get_online_peers() whether it returns a list or dict."""
        if self.discovery is None:
            return []
        raw = self.discovery.get_online_peers()
        if isinstance(raw, dict):
            peers = []
            for pid, info in raw.items():
                item = dict(info)
                item.setdefault("peer_id", pid)
                peers.append(item)
            return peers
        return list(raw)

    def _get_unread_counts(self) -> dict:
        if self.chat_node is None or not hasattr(self.chat_node, "get_unread_counts"):
            return {}
        return self.chat_node.get_unread_counts() or {}

    def _get_active_chat_peer(self):
        """Sync active chat state with chat_node in case the remote peer left or disconnected."""
        if self.chat_node is not None and hasattr(self.chat_node, "current_chat_peer_id"):
            active_id = self.chat_node.current_chat_peer_id
            if active_id is None:
                self._current_peer = None
            elif self._current_peer is None or self._current_peer.get("peer_id") != active_id:
                for peer in self._get_online_peers_list():
                    if peer.get("peer_id") == active_id:
                        self._current_peer = peer
                        break
        return self._current_peer

    def _resolve_peer_target(self, target: str):
        """Resolve <name|number> to a peer dict; returns (peer, error_message)."""
        peers = self.last_listed_peers or self._get_online_peers_list()
        if not peers:
            return None, "[!] No online peers available. Wait for discovery or run /list."

        if target.isdigit():
            idx = int(target) - 1
            if 0 <= idx < len(peers):
                return peers[idx], None
            return None, f"[!] Invalid peer number '{target}'. Run /list to see valid numbers."

        # Refresh from live list when searching by name
        live_peers = self._get_online_peers_list() or peers
        matches = [p for p in live_peers if p.get("name", "").lower() == target.lower()]
        if not matches:
            return None, f"[!] Peer '{target}' not found. Run /list to see online peers."
        if len(matches) > 1:
            return (
                None,
                f"[!] Multiple peers named '{target}'. Run /list and use /chat <number>.",
            )
        return matches[0], None

    def _cmd_list(self) -> None:
        peers = self._get_online_peers_list()
        self.last_listed_peers = peers
        unread_counts = self._get_unread_counts()

        if not peers:
            self.ui_print("[*] No other peers online.")
            return

        lines = []
        for idx, peer in enumerate(peers, start=1):
            pid = peer.get("peer_id", "")
            name = peer.get("name", "Unknown")
            ip = peer.get("ip", "?")
            port = peer.get("tcp_port", "?")
            status = peer.get("status", "online")
            unread = unread_counts.get(pid, 0)
            unread_tag = f"  ({unread} unread)" if unread > 0 else ""
            lines.append(f"  {idx}. {name:<10} ({ip}:{port})  [{status}]{unread_tag}")
        self.ui_print("\n".join(lines))

    def _cmd_chat(self, arg: str) -> None:
        target = arg.strip()
        if not target:
            self.ui_print("[*] Usage: /chat <name|number>")
            return

        if self.chat_node is None:
            self.ui_print("[!] Chat module (src/chat_node.py) is not loaded yet.")
            return

        peer, err = self._resolve_peer_target(target)
        if err:
            self.ui_print(err)
            return

        try:
            unread_msgs = self.chat_node.open_chat(peer)
        except Exception as exc:
            self.ui_print(f"[!] Could not connect to {peer['name']}: {exc}")
            return

        self._current_peer = peer
        self.ui_print(f"[*] Connected to {peer['name']} ({peer['ip']}:{peer['tcp_port']})")

        if unread_msgs:
            self.ui_print(f"[*] Switched to {peer['name']} — {len(unread_msgs)} unread:")
            for msg in unread_msgs:
                self.ui_print(f"[{peer['name']}] {msg}")

    def _cmd_send(self, arg: str) -> None:
        peer = self._get_active_chat_peer()
        if not peer:
            self.ui_print("[*] Not in a chat. Use /chat <name|number> first.")
            return

        file_path = arg.strip().strip('"').strip("'")
        if not file_path:
            self.ui_print("[*] Usage: /send <file_path>")
            return

        if not os.path.isfile(file_path):
            self.ui_print(f"[!] File not found: {file_path}")
            return

        if self.send_file_fn is None:
            self.ui_print("[!] File transfer module (src/file_transfer.py) is not loaded yet.")
            return

        sender_thread = threading.Thread(
            target=self.send_file_fn,
            args=(peer["ip"], peer["tcp_port"], self.name, file_path, self.ui_print),
            daemon=True,
            name=f"file-sender-{os.path.basename(file_path)}",
        )
        sender_thread.start()

    def _cmd_leave(self) -> None:
        peer = self._get_active_chat_peer()
        if not peer:
            self.ui_print("[*] You are not in a chat.")
            return

        if self.chat_node is not None:
            self.chat_node.leave_current_chat()
        self._current_peer = None
        self.ui_print("[*] Left chat. Returned to lobby.")

    def _cmd_status(self, arg: str) -> None:
        new_status = arg.strip().lower()
        if new_status not in ("online", "away"):
            self.ui_print("[*] Usage: /status <online|away>")
            return

        self.status = new_status
        if self.discovery is not None:
            self.discovery.set_status(new_status)
            if hasattr(self.discovery, "broadcast_now"):
                self.discovery.broadcast_now()
        self.ui_print(f"[*] Status updated to: {new_status}")

    def handle_command(self, raw_line: str) -> bool:
        """
        Process one line of user input.
        Returns False when the user requests /quit, otherwise True.
        """
        text = raw_line.strip()
        if not text:
            return True

        if text.startswith("/"):
            parts = text.split(maxsplit=1)
            cmd = parts[0].lower()
            arg = parts[1] if len(parts) > 1 else ""

            if cmd == "/help":
                self.ui_print(HELP_TEXT)
            elif cmd == "/list":
                self._cmd_list()
            elif cmd == "/chat":
                self._cmd_chat(arg)
            elif cmd == "/send":
                self._cmd_send(arg)
            elif cmd == "/leave":
                self._cmd_leave()
            elif cmd == "/status":
                self._cmd_status(arg)
            elif cmd == "/quit":
                self.ui_print("[*] Shutting down...")
                return False
            else:
                self.ui_print(f"[!] Unknown command: '{cmd}'. Type /help for available commands.")
            return True

        # Plain text message -> send to current chat peer
        peer = self._get_active_chat_peer()
        if not peer:
            self.ui_print("[*] Not in a chat. Use /chat <name|number>")
            return True

        if self.chat_node is None:
            self.ui_print("[!] Chat module (src/chat_node.py) is not loaded yet.")
            return True

        try:
            self.chat_node.send_message(text)
            self.ui_print(f"[{self.name}] {text}")
        except Exception as exc:
            self.ui_print(f"[!] Failed to send message: {exc}")
        return True

    def run(self) -> None:
        """Run the interactive Console UI loop with prompt_toolkit + patch_stdout()."""
        if PromptSession is None or patch_stdout is None:
            self.ui_print(
                "[!] Missing dependency 'prompt_toolkit'. "
                "Install it with: pip install -r requirements.txt"
            )
            return

        session = PromptSession()
        self.ui_print(f"[*] Listening on TCP port {self.tcp_port} | Peer ID: {self.peer_id}")
        self.ui_print(
            f"[*] Broadcasting presence on UDP port {DEFAULT_UDP_PORT} "
            f"(target: {self.bcast_addr})"
        )
        self.ui_print("[*] Type /help to see all commands.")

        with patch_stdout():
            while True:
                try:
                    raw_line = session.prompt(self.get_prompt_text)
                except (KeyboardInterrupt, EOFError):
                    self.ui_print("\n[*] Exiting...")
                    break

                if not self.handle_command(raw_line):
                    break


def build_client(args: argparse.Namespace) -> ConsoleClient:
    """Wire ConsoleClient with DiscoveryService, ChatNode, and file_transfer when available."""
    send_file_fn = getattr(file_transfer, "send_file", None) if file_transfer else None
    receive_file_fn = getattr(file_transfer, "receive_file", None) if file_transfer else None

    client = ConsoleClient(
        name=args.name,
        tcp_port=args.port,
        bcast_addr=args.bcast,
        send_file_fn=send_file_fn,
    )

    if DiscoveryService is not None:
        discovery = DiscoveryService(
            name=args.name,
            tcp_port=args.port,
            bcast_addr=args.bcast,
            on_ui_print=client.ui_print,
        )
        client.discovery = discovery
        if getattr(discovery, "peer_id", None):
            client.peer_id = discovery.peer_id
        discovery.start()
    else:
        client.ui_print("[!] Running in UI-only mode (src/discovery.py not merged yet).")

    if ChatNode is not None:
        chat_node = ChatNode(
            peer_id=client.peer_id,
            name=args.name,
            tcp_port=args.port,
            on_ui_print=client.ui_print,
            on_incoming_file=receive_file_fn,
        )
        client.chat_node = chat_node
        chat_node.start()
    else:
        client.ui_print("[!] Running in UI-only mode (src/chat_node.py not merged yet).")

    return client


def main(argv=None) -> None:
    args = parse_args(argv)
    client = build_client(args)
    try:
        client.run()
    finally:
        if client.discovery is not None and hasattr(client.discovery, "stop"):
            try:
                client.discovery.stop()
            except Exception:
                pass
        if client.chat_node is not None and hasattr(client.chat_node, "shutdown"):
            try:
                client.chat_node.shutdown()
            except Exception:
                pass
        cleanup_partial_downloads(client.download_dir)


if __name__ == "__main__":
    main()
