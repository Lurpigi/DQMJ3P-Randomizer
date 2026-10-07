from __future__ import annotations

import sys
import tempfile
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dqmj3p_randomizer.romfs_source import RomFsSource, RomFsSourceError
from support import make_romfs_layers


class RomFsSourceTests(unittest.TestCase):
    def test_overlay_indexes_required_files_and_resolves_paths_case_insensitively(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base, update = make_romfs_layers(
                Path(temporary) / "base", Path(temporary) / "update")
            update_monster = bytearray((update / "data/Parameter/MonsterParam.tp").read_bytes())
            update_monster[8] = 0xA5
            (update / "data/Parameter/MonsterParam.tp").write_bytes(update_monster)
            source = RomFsSource(base, update)
            self.assertEqual(source.describe()["kind"], "user_extracted_layered_romfs")
            self.assertEqual(source.describe()["merge_policy"], "update overrides base case-insensitively")
            self.assertEqual(source.describe()["et_archive_count"], 1)
            self.assertEqual(source.read("DATA/PARAMETER/MONSTERPARAM.TP")[8], 0xA5)
            self.assertIn("data/Model/m300.bch", source.model_paths)
            self.assertEqual(source.source_for("data/Parameter/MonsterParam.tp"), "update")
            self.assertEqual(source.source_for("data/Field/Table/Encount/ET_TEST_00.xbb"), "base")

    def test_missing_required_file_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            base, update = make_romfs_layers(
                Path(temporary) / "base", Path(temporary) / "update")
            (base / "data/Parameter/MonsterParam.tp").unlink()
            (update / "data/Parameter/MonsterParam.tp").unlink()
            with self.assertRaisesRegex(RomFsSourceError, "MonsterParam.tp"):
                RomFsSource(base, update)


if __name__ == "__main__":
    unittest.main()
