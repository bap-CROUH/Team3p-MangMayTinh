import os
import tempfile
import unittest
from io import StringIO
from unittest.mock import MagicMock, patch

import sys

SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

import main as cli_main  # type: ignore  # noqa: E402


class TestMainCLI(unittest.TestCase):
    def test_parse_args_valid(self):
        args = cli_main.parse_args(["--name", "Hao", "--port", "5001", "--bcast", "127.255.255.255"])
        self.assertEqual(args.name, "Hao")
        self.assertEqual(args.port, 5001)
        self.assertEqual(args.bcast, "127.255.255.255")

    def test_parse_args_rejects_pipe_and_empty_name(self):
        with self.assertRaises(SystemExit):
            cli_main.parse_args(["--name", "Hao|Bad"])
        with self.assertRaises(SystemExit):
            cli_main.parse_args(["--name", "   "])
        with self.assertRaises(SystemExit):
            cli_main.parse_args(["--name", "Hao", "--port", "70000"])

    def test_commands_list_status_chat_send_leave_quit(self):
        fake_discovery = MagicMock()
        fake_discovery.peer_id = "aaaa1111"
        fake_discovery.get_online_peers.return_value = [
            {
                "peer_id": "bbbb2222",
                "name": "Minh",
                "ip": "127.0.0.1",
                "tcp_port": 5002,
                "status": "online",
            }
        ]

        fake_chat = MagicMock()
        fake_chat.current_chat_peer_id = None
        fake_chat.get_unread_counts.return_value = {"bbbb2222": 2}

        def fake_open_chat(peer):
            fake_chat.current_chat_peer_id = peer["peer_id"]
            return ["Hello 1", "Hello 2"]

        def fake_leave():
            fake_chat.current_chat_peer_id = None

        fake_chat.open_chat.side_effect = fake_open_chat
        fake_chat.leave_current_chat.side_effect = fake_leave

        sent_files = []

        def fake_send_file(ip, port, sender, path, on_ui_print):
            sent_files.append((ip, port, sender, path))

        client = cli_main.ConsoleClient(
            name="Hao",
            tcp_port=5001,
            bcast_addr="127.255.255.255",
            discovery=fake_discovery,
            chat_node=fake_chat,
            send_file_fn=fake_send_file,
        )

        with patch("sys.stdout", new_callable=StringIO) as out:
            self.assertTrue(client.handle_command("/list"))
            self.assertIn("Minh", out.getvalue())
            self.assertIn("(2 unread)", out.getvalue())

            self.assertTrue(client.handle_command("/status away"))
            fake_discovery.set_status.assert_called_with("away")
            fake_discovery.broadcast_now.assert_called_once()

            self.assertTrue(client.handle_command("/chat 1"))
            self.assertEqual(client.get_prompt_text(), "[Chat: Minh] > ")
            self.assertIn("Hello 1", out.getvalue())

            self.assertTrue(client.handle_command("Chao Minh"))
            fake_chat.send_message.assert_called_with("Chao Minh")

            with tempfile.NamedTemporaryFile(delete=False) as tf:
                tmp_path = tf.name
            try:
                self.assertTrue(client.handle_command(f'/send "{tmp_path}"'))
                # Wait briefly for daemon sender thread
                for _ in range(20):
                    if sent_files:
                        break
                    import time
                    time.sleep(0.01)
                self.assertEqual(sent_files, [("127.0.0.1", 5002, "Hao", tmp_path)])
            finally:
                os.remove(tmp_path)

            self.assertTrue(client.handle_command("/leave"))
            self.assertEqual(client.get_prompt_text(), "> ")

            self.assertTrue(client.handle_command("/unknown"))
            self.assertIn("Unknown command", out.getvalue())

            self.assertFalse(client.handle_command("/quit"))

    def test_cleanup_partial_downloads(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            part_file = os.path.join(tmpdir, "video.mp4.part")
            ok_file = os.path.join(tmpdir, "report.pdf")
            open(part_file, "wb").close()
            open(ok_file, "wb").close()

            removed = cli_main.cleanup_partial_downloads(tmpdir)
            self.assertEqual(removed, 1)
            self.assertFalse(os.path.exists(part_file))
            self.assertTrue(os.path.exists(ok_file))


if __name__ == "__main__":
    unittest.main()
