from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from dqmj3p_randomizer.global_catalog import merge_global_catalog
from dqmj3p_randomizer.global_randomizer import (
    GlobalOptions,
    patch_et_archive,
    patch_monsterparam,
    plan_encounter_randomization,
)


def _tables() -> tuple[bytes, bytes, bytes, set[str]]:
    kinds = bytearray(b"KINP")
    models = bytearray(b"KCOP")
    rows = (
        (300, "Alpha", "m300", 1, 1, 1), (400, "Beta", "m400", 1, 2, 2),
        (500, "Gamma", "m500", 1, 7, 3), (600, "Special", "m600", 1, 5, 6),
        (700, "Larger", "m700", 2, 7, 8), (800, "Unknown", "m800", 255, 1, 1),
        (900, "NoAsset", "m900", 1, 4, 4),
    )
    for kind, name, model, size_code, family_code, rank_code in rows:
        row = bytearray(120)
        row[:len(name)] = name.encode("ascii")
        struct.pack_into("<HBBH", row, 32, kind, rank_code, family_code, 1)
        struct.pack_into("<H", row, 48, size_code)
        if len(kinds) < 4 + (kind + 1) * 120:
            kinds.extend(bytes(4 + (kind + 1) * 120 - len(kinds)))
        kinds[4 + kind * 120:4 + (kind + 1) * 120] = row

        model_row = bytearray(88)
        model_row[2:2 + len(model)] = model.encode("ascii")
        if len(models) < 4 + (kind + 1) * 88:
            models.extend(bytes(4 + (kind + 1) * 88 - len(models)))
        models[4 + kind * 88:4 + (kind + 1) * 88] = model_row

    monster = bytearray(b"MONP")
    for instance, kind in ((100, 300), (200, 400), (300, 500), (400, 600), (500, 700), (600, 800), (700, 900)):
        row = bytearray(72)
        struct.pack_into("<HH", row, 0, instance, kind)
        row[4:] = bytes([instance // 100]) * 68
        monster.extend(row)
    assets = {f"data/Model/{model}.bch" for model in ("m300", "m400", "m500", "m600", "m700", "m800")}
    return bytes(kinds), bytes(monster), bytes(models), assets


def _smot_xbb() -> bytes:
    payload = bytearray(b"SMOT")
    for single, ref, kind in ((1, 100, 300), (2, 200, 400), (3, 300, 500)):
        row = bytearray(116)
        struct.pack_into("<5H", row, 0, single, ref, kind, ref, ref)
        payload.extend(row)
    payload_offset, name_offset = 0x80, 0x38
    archive = bytearray(payload_offset + len(payload))
    archive[:4] = b"XBB\x01"
    struct.pack_into("<I", archive, 4, 1)
    struct.pack_into("<IIII", archive, 0x20, payload_offset, len(payload), name_offset, 0)
    archive[name_offset:name_offset + 10] = b"2_single\0"
    archive[payload_offset:] = payload
    return bytes(archive)


class GlobalRandomizerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.kindparam, self.monsterparam, self.kindconfig, self.models = _tables()
        self.catalog = merge_global_catalog(self.kindparam, self.monsterparam, self.kindconfig, self.models)
        self.inventory = {"archives": [{"path": "data/Field/Table/Encount/ET_A.xbb", "records": [
            {"path": "data/Field/Table/Encount/ET_A.xbb", "member": "2_single.tp",
             "member_index": 0, "record_index": i, "single_id": i + 1,
             "kind_id": kind, "monp_refs": [instance, instance, instance]}
            for i, (kind, instance) in enumerate(((300, 100), (400, 200), (500, 300)))
        ]}]}

    def test_per_instance_mapping_is_seeded_same_size_and_avoids_fixed_points(self) -> None:
        options = GlobalOptions(seed=73)
        first = plan_encounter_randomization(self.catalog, self.inventory, options)
        second = plan_encounter_randomization(self.catalog, self.inventory, options)
        self.assertEqual(first["instance_mapping"], second["instance_mapping"])
        self.assertEqual(first["smot_row_mapping"], second["smot_row_mapping"])
        self.assertEqual(set(first["instance_mapping"]), {100, 200, 300})
        sizes = {row["kind_id"]: row["size_slots"] for row in self.catalog["species"]}
        for instance_id, target in first["instance_mapping"].items():
            source = self.catalog["monp_instances"][instance_id]["kind_id"]
            self.assertEqual(sizes[source], sizes[target])
            self.assertNotEqual(source, target)

    def test_patch_changes_only_monp_plus2_and_smot_plus4(self) -> None:
        plan = plan_encounter_randomization(self.catalog, self.inventory, GlobalOptions(seed=73))
        instance_mapping = dict(plan["instance_mapping"])
        instance_mapping[100] = 1025
        patched_monp, monp_audit = patch_monsterparam(
            self.monsterparam, set(plan["selected_instance_ids"]), instance_mapping=instance_mapping,
        )
        smot_mapping = dict(plan["smot_row_mapping"])
        smot_mapping[("data/field/table/encount/et_a.xbb", 0, 0)] = 1025
        before = _smot_xbb()
        patched_et, et_audit = patch_et_archive(before, "data/Field/Table/Encount/ET_A.xbb", smot_row_mapping=smot_mapping)
        allowed_monp = {4 + i * 72 + byte for i in range(3) for byte in (2, 3)}
        changed_monp = {i for i, (a, b) in enumerate(zip(self.monsterparam, patched_monp)) if a != b}
        self.assertTrue(changed_monp <= allowed_monp)
        self.assertTrue({6, 7} <= changed_monp)
        self.assertEqual(monp_audit["modified_byte_count"], len(changed_monp))
        allowed_et = {0x80 + 4 + i * 116 + byte for i in range(3) for byte in (4, 5)}
        changed_et = {i for i, (a, b) in enumerate(zip(before, patched_et)) if a != b}
        self.assertTrue(changed_et <= allowed_et)
        self.assertEqual(et_audit["modified_byte_count"], len(changed_et))

    def test_donor_pool_and_event_scope_expand_independently(self) -> None:
        baseline = plan_encounter_randomization(self.catalog, self.inventory, GlobalOptions(seed=2))
        all_instances = plan_encounter_randomization(
            self.catalog, self.inventory, GlobalOptions(seed=2, include_nonwild_instances=True),
        )
        special = plan_encounter_randomization(
            self.catalog, self.inventory, GlobalOptions(seed=2, include_special_donors=True),
        )
        self.assertEqual(baseline["normal_donor_kind_count"], 3)
        self.assertEqual(all_instances["selected_instance_ids"], [100, 200, 300, 400, 500, 600, 700])
        self.assertEqual(all_instances["donor_kind_count"], 3)
        self.assertEqual(all_instances["normal_donor_kind_count"], 3)
        self.assertNotIn(600, baseline["donor_kind_ids"])
        self.assertNotIn(900, special["donor_kind_ids"])
        self.assertIn(600, special["donor_kind_ids"])
        self.assertIn(700, special["donor_kind_ids"])

    def test_family_filter_limits_replacements_but_keeps_all_targets(self) -> None:
        plan = plan_encounter_randomization(
            self.catalog, self.inventory,
            GlobalOptions(seed=2, donor_family_codes=frozenset({1})),
        )
        self.assertEqual(plan["selected_instance_ids"], [100, 200, 300])
        self.assertEqual(set(plan["instance_mapping"]), {100, 200, 300})
        rows = plan["smot_row_mapping"]
        self.assertEqual(rows[("data/field/table/encount/et_a.xbb", 0, 0)], 300)
        self.assertEqual(rows[("data/field/table/encount/et_a.xbb", 0, 1)], 300)
        self.assertEqual(rows[("data/field/table/encount/et_a.xbb", 0, 2)], 300)
        self.assertEqual(plan["donor_kind_ids"], [300])

        event_scope = plan_encounter_randomization(
            self.catalog, self.inventory,
            GlobalOptions(
                seed=2, include_nonwild_instances=True,
                donor_family_codes=frozenset({1}),
            ),
        )
        self.assertEqual(event_scope["selected_instance_ids"], [100, 200, 300, 400, 500, 600, 700])
        self.assertEqual(event_scope["donor_kind_ids"], [300])

    def test_family_filter_requires_at_least_one_family(self) -> None:
        with self.assertRaisesRegex(ValueError, "almeno una famiglia"):
            GlobalOptions(seed=1, donor_family_codes=frozenset())

    def test_rank_filter_limits_replacements_but_keeps_all_targets(self) -> None:
        plan = plan_encounter_randomization(
            self.catalog, self.inventory,
            GlobalOptions(seed=2, donor_rank_codes=frozenset({1})),
        )
        self.assertEqual(plan["selected_instance_ids"], [100, 200, 300])
        self.assertEqual(set(plan["instance_mapping"]), {100, 200, 300})
        rows = plan["smot_row_mapping"]
        self.assertEqual(rows[("data/field/table/encount/et_a.xbb", 0, 0)], 300)
        self.assertEqual(rows[("data/field/table/encount/et_a.xbb", 0, 1)], 300)
        self.assertEqual(rows[("data/field/table/encount/et_a.xbb", 0, 2)], 300)
        self.assertEqual(plan["donor_kind_ids"], [300])

        event_scope = plan_encounter_randomization(
            self.catalog, self.inventory,
            GlobalOptions(
                seed=2, include_nonwild_instances=True,
                donor_rank_codes=frozenset({1}),
            ),
        )
        self.assertEqual(event_scope["selected_instance_ids"], [100, 200, 300, 400, 500, 600, 700])
        self.assertEqual(event_scope["donor_kind_ids"], [300])

        combined = plan_encounter_randomization(
            self.catalog, self.inventory,
            GlobalOptions(
                seed=2, include_special_donors=True,
                donor_family_codes=frozenset({5}),
                donor_rank_codes=frozenset({6}),
            ),
        )
        self.assertEqual(combined["selected_instance_ids"], [100, 200, 300])
        self.assertEqual(combined["donor_kind_ids"], [600])

    def test_rank_filter_requires_at_least_one_rank(self) -> None:
        with self.assertRaisesRegex(ValueError, "almeno un grado"):
            GlobalOptions(seed=1, donor_rank_codes=frozenset())

    def test_positive_unresolved_monp_reference_fails_closed(self) -> None:
        broken = {"archives": [{"path": "ET_BROKEN.xbb", "records": [{"kind_id": 300, "monp_refs": [9999, 0, 0]}]}]}
        with self.assertRaisesRegex(ValueError, "non presente"):
            plan_encounter_randomization(self.catalog, broken, GlobalOptions(seed=7))

    def test_reused_ids_share_donor_and_mismatched_leader_uses_nominal_rule(self) -> None:
        inventory = {"archives": [{"path": "data/Field/Table/Encount/ET_A.xbb", "records": [
            {"path": "data/Field/Table/Encount/ET_A.xbb", "member": "2_single.tp", "member_index": 0,
             "record_index": 0, "single_id": 1, "kind_id": 300, "monp_refs": [100, 100, 100]},
            {"path": "data/Field/Table/Encount/ET_A.xbb", "member": "2_single.tp", "member_index": 0,
             "record_index": 1, "single_id": 2, "kind_id": 300, "monp_refs": [100, 200, 200]},
            {"path": "data/Field/Table/Encount/ET_A.xbb", "member": "2_single.tp", "member_index": 0,
             "record_index": 2, "single_id": 3, "kind_id": 400, "monp_refs": [100, 200, 200]},
        ]}]}
        plan = plan_encounter_randomization(self.catalog, inventory, GlobalOptions(seed=73))
        first = plan["smot_row_mapping"][("data/field/table/encount/et_a.xbb", 0, 0)]
        repeated = plan["smot_row_mapping"][("data/field/table/encount/et_a.xbb", 0, 1)]
        fallback = plan["smot_row_details"][2]
        self.assertEqual(first, plan["instance_mapping"][100])
        self.assertEqual(repeated, first)
        self.assertEqual(fallback["rule"], "nominal_kind_independent_fallback")
        self.assertEqual(fallback["source_kind_id"], 400)
        self.assertNotEqual(fallback["donor_kind_id"], plan["instance_mapping"][100])


if __name__ == "__main__":
    unittest.main()
