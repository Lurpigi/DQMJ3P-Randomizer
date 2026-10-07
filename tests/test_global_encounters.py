from __future__ import annotations

import struct
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dqmj3p_randomizer.global_encounters import scan_et_archive
from dqmj3p_randomizer.romfs_source import RomFsSource
from support import make_romfs_layers


def _smot(rows: list[tuple[int, int, int, int, int]]) -> bytes:
    data = bytearray(b"SMOT")
    for values in rows:
        offset = len(data)
        data.extend(struct.pack("<5H", *values))
        data.extend(bytes([values[0] % 251]) * (116 - 10))
        assert len(data) == offset + 116
    return bytes(data)


def _xbb_one_member(name: str, payload: bytes) -> bytes:
    payload_offset = 0x80
    name_offset = 0x38
    archive = bytearray(payload_offset + len(payload))
    archive[:4] = b"XBB\x01"
    struct.pack_into("<I", archive, 4, 1)
    struct.pack_into("<IIII", archive, 0x20, payload_offset, len(payload), name_offset, 0)
    archive[name_offset:name_offset + len(name) + 1] = name.encode("ascii") + b"\0"
    archive[payload_offset:] = payload
    return bytes(archive)


class GlobalEncounterScannerTests(unittest.TestCase):
    def test_scanner_distinguishes_ref_patterns_without_labeling_them_game_invalid(self) -> None:
        rows = [
            (1, 10, 128, 11, 12),    # all three MONP refs agree with SMOT kind
            (2, 10, 128, 0, 0),      # possible intentional one-ref definition
            (3, 10, 151, 11, 12),    # refs resolve, but use a different kind
            (4, 90, 128, 91, 92),    # unresolved IDs
            (5, 0, 128, 0, 0),       # all refs zero
        ]
        monp = {10: 128, 11: 128, 12: 128}
        report = scan_et_archive(
            "data/Field/Table/Encount/ET_TEST_00.xbb",
            _xbb_one_member("./temp/2_single.tp", _smot(rows)),
            monp,
            "base",
        )
        self.assertEqual(report["record_count"], 5)
        self.assertEqual(report["three_refs_match_smot_kind_count"], 1)
        self.assertEqual(report["records"][0]["status"], "three_refs_match_smot_kind")
        self.assertEqual(report["records"][1]["status"], "partial_refs_zero")
        self.assertEqual(report["records"][2]["status"], "reference_kind_differs_from_smot")
        self.assertEqual(report["records"][3]["status"], "monp_id_unresolved")
        self.assertEqual(report["records"][4]["status"], "all_refs_zero")

    def test_layered_romfs_indexes_encounters_and_resolves_paths_case_insensitively(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base, update = make_romfs_layers(
                Path(temporary) / "base", Path(temporary) / "update")
            romfs = RomFsSource(base, update)
            et_paths = romfs.paths("data/Field/Table/Encount")
            self.assertEqual(len(et_paths), 1)
            self.assertTrue(Path(et_paths[0]).name.casefold().startswith("et_"))
            self.assertEqual(romfs.read("DATA/PARAMETER/MONSTERPARAM.TP")[:4], b"MONP")
            self.assertEqual(romfs.source_for(et_paths[0]), "base")


if __name__ == "__main__":
    unittest.main()
