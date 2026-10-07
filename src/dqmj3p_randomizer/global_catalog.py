"""Generic KINP/MONP catalog parser using the confirmed parameter layouts."""

from __future__ import annotations

import hashlib
import struct
from typing import Any

from .global_encounters import MONP_STRIDE


KINP_HEADER = b"KINP"
KINP_STRIDE = 120
KINP_SIZE_OFFSET = 48
KINP_NAME_BYTES = 32
KCOP_STRIDE = 88
KCOP_MODEL_OFFSET = 2
SIZE_CODE_TO_SLOTS = {0: 1, 1: 1, 2: 2, 3: 3, 4: 4}
RANK_CODES = {1: "F", 2: "E", 3: "D", 4: "C", 5: "B", 6: "A", 7: "S", 8: "SS"}
RANK_NAME_TO_CODE = {rank.lower(): code for code, rank in RANK_CODES.items()}
FAMILY_CODES = {
    1: "Slime",
    2: "Dragon",
    3: "Beast",
    4: "Nature",
    5: "Demon",
    6: "Undead",
    7: "Material",
    8: "Break",
    9: "Unknown",
}
FAMILY_NAME_TO_CODE = {
    "slime": 1,
    "dragon": 2,
    "beast": 3,
    "nature": 4,
    "demon": 5,
    "undead": 6,
    "material": 7,
    "break": 8,
    "unknown": 9,
}


class GlobalCatalogError(ValueError):
    """An input parameter table does not match its confirmed record layout."""


def parse_kind_catalog(kindparam: bytes) -> dict[str, Any]:
    if len(kindparam) < 4 or kindparam[:4] != KINP_HEADER or (len(kindparam) - 4) % KINP_STRIDE:
        raise GlobalCatalogError("KindParam.tp non corrisponde a KINP/120 byte")
    count = (len(kindparam) - 4) // KINP_STRIDE
    species = []
    for kind_id in range(count):
        offset = 4 + kind_id * KINP_STRIDE
        raw_name = kindparam[offset:offset + KINP_NAME_BYTES].split(b"\0", 1)[0]
        if not raw_name:
            continue
        name = raw_name.decode("cp932", errors="replace")
        order = struct.unpack_from("<H", kindparam, offset + 32)[0]
        rank_code, family_code = struct.unpack_from("<BB", kindparam, offset + 34)
        size_code = struct.unpack_from("<H", kindparam, offset + KINP_SIZE_OFFSET)[0]
        species.append({
            "kind_id": kind_id,
            "name": name,
            "order": order,
            "rank_code": rank_code,
            "rank": RANK_CODES.get(rank_code),
            "family_code": family_code,
            "family": FAMILY_CODES.get(family_code),
            "size_code": size_code,
            "size_slots": SIZE_CODE_TO_SLOTS.get(size_code),
            "record_offset": offset,
        })
    return {
        "sha256": hashlib.sha256(kindparam).hexdigest(),
        "record_size": KINP_STRIDE,
        "record_count": count,
        "named_species_count": len(species),
        "size_field": {"record_offset": KINP_SIZE_OFFSET, "type": "u16le", "semantics": "0/1=1 slot, 2=2, 3=3, 4=4; other values unknown"},
        "species": species,
    }


def parse_monp_instances(monsterparam: bytes) -> dict[str, Any]:
    if len(monsterparam) < 4 or monsterparam[:4] != b"MONP" or (len(monsterparam) - 4) % MONP_STRIDE:
        raise GlobalCatalogError("MonsterParam.tp non corrisponde a MONP/72 byte")
    rows_by_id: dict[int, dict[str, int]] = {}
    by_kind: dict[int, list[int]] = {}
    row_count = (len(monsterparam) - 4) // MONP_STRIDE
    for index in range(row_count):
        offset = 4 + index * MONP_STRIDE
        instance_id, kind_id = struct.unpack_from("<HH", monsterparam, offset)
        if instance_id == 0:
            continue
        if instance_id in rows_by_id:
            raise GlobalCatalogError(f"ID MONP duplicato: {instance_id}")
        rows_by_id[instance_id] = {"instance_id": instance_id, "kind_id": kind_id, "record_index": index, "record_offset": offset}
        by_kind.setdefault(kind_id, []).append(instance_id)
    return {
        "sha256": hashlib.sha256(monsterparam).hexdigest(),
        "record_size": MONP_STRIDE,
        "record_count": row_count,
        "nonzero_instance_count": len(rows_by_id),
        "instances": rows_by_id,
        "instance_ids_by_kind": {kind: sorted(ids) for kind, ids in by_kind.items()},
    }


def parse_model_catalog(kindconfig: bytes, model_paths: set[str] | None = None) -> dict[str, Any]:
    if len(kindconfig) < 4 or kindconfig[:4] != b"KCOP" or (len(kindconfig) - 4) % KCOP_STRIDE:
        raise GlobalCatalogError("KindConfigParam.tp non corrisponde a KCOP/88 byte")
    count = (len(kindconfig) - 4) // KCOP_STRIDE
    paths = {path.replace("\\", "/").casefold() for path in (model_paths or set())}
    entries = {}
    for kind_id in range(count):
        offset = 4 + kind_id * KCOP_STRIDE
        raw_model = kindconfig[offset + KCOP_MODEL_OFFSET:offset + KCOP_MODEL_OFFSET + 32].split(b"\0", 1)[0]
        if not raw_model:
            continue
        model = raw_model.decode("ascii", errors="replace")
        asset_path = f"data/Model/{model}.bch"
        entries[kind_id] = {
            "kind_id": kind_id,
            "model": model,
            "asset_path": asset_path,
            "asset_exists": asset_path.casefold() in paths if model_paths is not None else None,
            "record_offset": offset,
        }
    return {
        "sha256": hashlib.sha256(kindconfig).hexdigest(),
        "record_size": KCOP_STRIDE,
        "record_count": count,
        "model_count": len(entries),
        "entries": entries,
    }


def merge_global_catalog(
    kindparam: bytes,
    monsterparam: bytes,
    kindconfig: bytes | None = None,
    model_paths: set[str] | None = None,
) -> dict[str, Any]:
    kind_catalog = parse_kind_catalog(kindparam)
    monp_catalog = parse_monp_instances(monsterparam)
    model_catalog = parse_model_catalog(kindconfig, model_paths) if kindconfig is not None else None
    instances_by_kind = monp_catalog["instance_ids_by_kind"]
    for entry in kind_catalog["species"]:
        kind_id = entry["kind_id"]
        entry["monp_instance_count"] = len(instances_by_kind.get(kind_id, ()))
        entry["monp_instance_ids"] = instances_by_kind.get(kind_id, [])
        entry["has_monp_instance"] = bool(entry["monp_instance_count"])
        model_info = model_catalog["entries"].get(kind_id) if model_catalog is not None else None
        entry["model"] = model_info["model"] if model_info else None
        entry["model_asset_path"] = model_info["asset_path"] if model_info else None
        entry["has_model_asset"] = model_info["asset_exists"] if model_info else None
        entry["donor_size_supported"] = (
            entry["size_slots"] in {1, 2, 3, 4}
            and entry["has_monp_instance"]
            and (
                kindconfig is None
                or (model_info is not None and model_info["asset_exists"] is True)
            )
        )
    return {
        "kindparam": {key: value for key, value in kind_catalog.items() if key != "species"},
        "monsterparam": {key: value for key, value in monp_catalog.items() if key not in {"instances", "instance_ids_by_kind"}},
        "kindconfig": ({key: value for key, value in model_catalog.items() if key != "entries"} if model_catalog else None),
        "species": kind_catalog["species"],
        "monp_instances": monp_catalog["instances"],
        "instance_ids_by_kind": monp_catalog["instance_ids_by_kind"],
    }
