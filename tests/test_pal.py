from pathlib import Path
import struct
import sys
import unittest
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from core.pine_ipc import MSG_READ16, MSG_READ32, MSG_WRITE16, PineIPC
from game.pal import PalSession, translate_table


class PalTests(unittest.TestCase):
    def test_wrong_revision_is_rejected_before_accessing_game_memory(self):
        ipc = Mock(spec=PineIPC)
        ipc.status.return_value = 0
        ipc.game_id.return_value = "SCES-50295"
        ipc.game_crc.return_value = "12345678"

        with self.assertRaisesRegex(ValueError, "0BAA8DD8"):
            PalSession(ipc).step()

        ipc.batch.assert_not_called()
        ipc.write16.assert_not_called()

    def test_european_shop_table_does_not_allow_out_of_bounds_writes(self):
        self.assertEqual(translate_table(0x20291D10, 2), 0x002941B0)
        with self.assertRaises(ValueError):
            translate_table(0x2029201F, 2)

    def test_pine_batch_has_one_status_byte_even_with_writes(self):
        ipc = PineIPC()
        ipc._send_recv = Mock(return_value=b"\0" + struct.pack("<HI", 400, 0x12345678))
        self.assertEqual(
            ipc.batch([(MSG_READ16, 10), (MSG_WRITE16, 12, 200), (MSG_READ32, 20)]),
            [400, None, 0x12345678],
        )


if __name__ == "__main__":
    unittest.main()
