from __future__ import annotations

import struct
from pathlib import Path


def _parameter_tables() -> tuple[bytes, bytes, bytes, bytes]:
    kinds = bytearray(b"KINP")
    models = bytearray(b"KCOP")
    rows = (
        (300, "Alpha", "m300", 1),
        (400, "Beta", "m400", 1),
        (500, "Gamma", "m500", 1),
        (600, "Special", "m600", 1),
        (700, "Larger", "m700", 2),
        (800, "Unknown", "m800", 255),
        (900, "NoAsset", "m900", 1),
    )
    for kind, name, model, size_code in rows:
        row = bytearray(120)
        row[:len(name)] = name.encode("ascii")
        struct.pack_into("<HBBH", row, 32, kind, 1, 3, 1)
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
        monster.extend(row)
    party = bytearray(b"PTYT")
    party_row = bytearray(44)
    struct.pack_into("<4I", party_row, 0, 100, 200, 300, 400)
    party.extend(party_row)
    return bytes(kinds), bytes(models), bytes(monster), bytes(party)


def _encounter_archive() -> bytes:
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
    member_name = b"2_single\0"
    archive[name_offset:name_offset + len(member_name)] = member_name
    archive[payload_offset:] = payload
    return bytes(archive)


def make_romfs_layers(base_root: Path, update_root: Path) -> tuple[Path, Path]:
    """Create tiny synthetic RomFS layers for tests; they contain no game data."""
    kinds, config, monsters, party = _parameter_tables()
    base_parameter_root = base_root / "data" / "Parameter"
    update_parameter_root = update_root / "data" / "Parameter"
    encounter_root = base_root / "data" / "Field" / "Table" / "Encount"
    model_root = base_root / "data" / "Model"
    base_parameter_root.mkdir(parents=True, exist_ok=True)
    update_parameter_root.mkdir(parents=True, exist_ok=True)
    encounter_root.mkdir(parents=True, exist_ok=True)
    model_root.mkdir(parents=True, exist_ok=True)
    (base_parameter_root / "KindParam.tp").write_bytes(kinds)
    (base_parameter_root / "KindConfigParam.tp").write_bytes(config)
    (base_parameter_root / "MonsterParam.tp").write_bytes(monsters)
    (update_parameter_root / "MonsterParam.tp").write_bytes(monsters)
    (update_parameter_root / "MonsterPartyTable.tp").write_bytes(party)
    (encounter_root / "ET_TEST_00.xbb").write_bytes(_encounter_archive())
    for name in ("m300", "m400", "m500", "m600", "m700", "m800"):
        (model_root / f"{name}.bch").write_bytes(b"synthetic test model name only")
    return base_root, update_root
