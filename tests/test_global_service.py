from __future__ import annotations

import json
import re
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dqmj3p_randomizer.romfs_source import RomFsSource
from dqmj3p_randomizer.global_randomizer import GlobalRandomizerError, patch_et_archive
from dqmj3p_randomizer.global_service import build_global_overlay
from support import make_romfs_layers


class GlobalServiceTests(unittest.TestCase):
    def test_build_uses_romfs_layers_and_leaves_them_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary) / "portable_program"
            project.mkdir()
            base_root, update_root = make_romfs_layers(
                Path(temporary) / "base_romfs", Path(temporary) / "update_romfs")
            dataset = RomFsSource(base_root, update_root)
            before = {
                "monster": dataset.read("data/Parameter/MonsterParam.tp"),
                "first_et": dataset.read(dataset.paths("data/Field/Table/Encount")[0]),
            }
            result = build_global_overlay(
                project_root=project,
                base_romfs_root=base_root,
                update_romfs_root=update_root,
                seed=42, output_name="portable_test",
                donor_family_codes=frozenset({3}),
                donor_rank_codes=frozenset({1}),
            )
            output = Path(result["output_dir"])
            manifest = json.loads((output / "manifest.json").read_text(encoding="utf-8"))
            config_text = (output / "config.json").read_text(encoding="utf-8")
            manifest_text = json.dumps(manifest)
            self.assertEqual(manifest["romfs_source"]["kind"], "user_extracted_layered_romfs")
            self.assertEqual(manifest["romfs_source"]["merge_policy"], "update overrides base case-insensitively")
            self.assertEqual(manifest["version"], "0.5.0")
            self.assertEqual(manifest["scope"]["smot_record_count"], 3)
            self.assertEqual(manifest["options"]["donor_family_codes"], [3])
            self.assertEqual(manifest["options"]["donor_rank_codes"], [1])
            config = json.loads(config_text)
            self.assertEqual(config["donor_family_codes"], [3])
            self.assertEqual(config["donor_rank_codes"], [1])
            self.assertNotIn("individual_spawns", manifest["options"])
            self.assertGreater(manifest["scope"]["changed_monp_instance_count"], 0)
            self.assertEqual(manifest["leader_rules"]["primary_ref_matched_original_smot_kind"] +
                             manifest["leader_rules"]["nominal_kind_independent_fallback"], 3)
            self.assertNotIn("base_romfs", config_text)
            self.assertNotIn("update", config_text.casefold())
            self.assertIsNone(re.search(r"(?i)\b[A-Z]:[/\\]", config_text))
            self.assertIsNone(re.search(r"(?i)\b[A-Z]:[/\\]", manifest_text))
            self.assertEqual(dataset.read("data/Parameter/MonsterParam.tp"), before["monster"])
            self.assertEqual(dataset.read(dataset.paths("data/Field/Table/Encount")[0]), before["first_et"])
            with zipfile.ZipFile(result["zip_path"]) as bundle:
                self.assertIsNone(bundle.testzip())
                self.assertIn("romfs/data/Parameter/MonsterParam.tp", bundle.namelist())
                self.assertIn("manifest.json", bundle.namelist())
                self.assertIn("config.json", bundle.namelist())

    def test_invalid_xbb_is_rejected(self) -> None:
        with self.assertRaises(GlobalRandomizerError):
            patch_et_archive(b"not an XBB", "ET_BAD.xbb", smot_row_mapping={})


if __name__ == "__main__":
    unittest.main()
