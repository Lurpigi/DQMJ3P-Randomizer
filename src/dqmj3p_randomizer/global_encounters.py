"""Read-only inventory of SMOT definitions found in every effective ET XBB."""

from __future__ import annotations

import hashlib
import struct
from typing import Any

from .inspector import XbbFormatError, parse_xbb_bytes
from .romfs_source import RomFsSource, RomFsSourceError


ENCOUNT_ROOT = "data/Field/Table/Encount"
MONP_PATH = "data/Parameter/MonsterParam.tp"
MONP_STRIDE = 72
SMOT_STRIDE = 116
MAX_RECORDS_PER_MEMBER = 250_000


class EncounterInventoryError(ValueError):
    """The source tables cannot be scanned safely or consistently."""


def parse_monp_species(data: bytes) -> dict[int, int]:
    """Read only the confirmed MONP ID and kind columns (record offsets +0/+2)."""
    if len(data) < 4 or data[:4] != b"MONP" or (len(data) - 4) % MONP_STRIDE:
        raise EncounterInventoryError("MonsterParam.tp non corrisponde alla struttura MONP/72 byte")
    count = (len(data) - 4) // MONP_STRIDE
    mapping: dict[int, int] = {}
    for index in range(count):
        monp_id, kind_id = struct.unpack_from("<HH", data, 4 + index * MONP_STRIDE)
        if not monp_id:
            continue
        if monp_id in mapping:
            raise EncounterInventoryError(f"ID MONP duplicato: {monp_id}")
        mapping[monp_id] = kind_id
    return mapping


def _is_et_archive(path: str) -> bool:
    normalized = path.replace("\\", "/").casefold()
    prefix = ENCOUNT_ROOT.casefold() + "/"
    name = normalized.rsplit("/", 1)[-1]
    return normalized.startswith(prefix) and name.startswith("et_") and name.endswith(".xbb")


def scan_et_archive(path: str, archive: bytes, monp_species: dict[int, int], source: str) -> dict[str, Any]:
    """Inventory any SMOT members in one ET archive; never modifies archive bytes."""
    try:
        index = parse_xbb_bytes(archive, path)
    except XbbFormatError as exc:
        return {
            "path": path,
            "source": source,
            "sha256": hashlib.sha256(archive).hexdigest(),
            "archive_size_bytes": len(archive),
            "error": str(exc),
            "smot_member_count": 0,
            "record_count": 0,
            "three_refs_match_smot_kind_count": 0,
            "other_reference_patterns_count": 0,
            "records": [],
        }
    records: list[dict[str, Any]] = []
    smot_member_count = 0
    member_errors: list[dict[str, Any]] = []
    for member in index["members"]:
        start = member["payload_offset"]
        size = member["size_bytes"]
        payload = archive[start:start + size]
        if payload[:4] != b"SMOT":
            continue
        smot_member_count += 1
        if (len(payload) - 4) % SMOT_STRIDE:
            member_errors.append({
                "member": member["name"],
                "error": f"SMOT size {len(payload)} non divisibile per header/stride verificati ({SMOT_STRIDE})",
            })
            continue
        row_count = (len(payload) - 4) // SMOT_STRIDE
        if row_count > MAX_RECORDS_PER_MEMBER:
            member_errors.append({"member": member["name"], "error": f"limite record superato: {row_count}"})
            continue
        for row_index in range(row_count):
            row_offset = 4 + row_index * SMOT_STRIDE
            single_id, ref_a, kind_id, ref_b, ref_c = struct.unpack_from("<5H", payload, row_offset)
            refs = (ref_a, ref_b, ref_c)
            missing_refs = [ref for ref in refs if ref != 0 and ref not in monp_species]
            mismatched_refs = [ref for ref in refs if ref in monp_species and monp_species[ref] != kind_id]
            if single_id == 0:
                status = "single_id_zero"
            elif kind_id == 0:
                status = "kind_zero"
            elif not any(refs):
                status = "all_refs_zero"
            elif any(ref == 0 for ref in refs):
                status = "partial_refs_zero"
            elif missing_refs:
                status = "monp_id_unresolved"
            elif mismatched_refs:
                status = "reference_kind_differs_from_smot"
            else:
                status = "three_refs_match_smot_kind"
            records.append({
                "path": path,
                "source": source,
                "member": member["name"],
                "member_index": member["index"],
                "record_index": row_index,
                "member_record_offset": row_offset,
                "single_id": single_id,
                "kind_id": kind_id,
                "monp_refs": list(refs),
                "status": status,
                "missing_monp_refs": missing_refs,
                "mismatched_monp_refs": mismatched_refs,
            })
    matching_ref_count = sum(item["status"] == "three_refs_match_smot_kind" for item in records)
    return {
        "path": path,
        "source": source,
        "sha256": hashlib.sha256(archive).hexdigest(),
        "archive_size_bytes": len(archive),
        "xbb_member_count": index["member_count"],
        "smot_member_count": smot_member_count,
        "record_count": len(records),
        "three_refs_match_smot_kind_count": matching_ref_count,
        "other_reference_patterns_count": len(records) - matching_ref_count,
        "member_errors": member_errors,
        "records": records,
    }


def scan_global_encounters(romfs: RomFsSource) -> dict[str, Any]:
    """Scan every effective `ET_*.xbb` below Field/Table/Encount."""
    try:
        monp_bytes = romfs.read(MONP_PATH)
    except RomFsSourceError as exc:
        raise EncounterInventoryError(f"Manca MonsterParam.tp nell'overlay: {exc}") from exc
    monp_species = parse_monp_species(monp_bytes)
    et_paths = [path for path in romfs.paths(ENCOUNT_ROOT) if _is_et_archive(path)]
    archives = []
    for path in et_paths:
        archives.append(scan_et_archive(path, romfs.read(path), monp_species, romfs.source_for(path)))
    records = [record for archive in archives for record in archive["records"]]
    by_kind: dict[int, dict[str, Any]] = {}
    for record in records:
        kind = record["kind_id"]
        item = by_kind.setdefault(kind, {"record_count": 0, "three_refs_match_smot_kind_count": 0, "paths": set(), "single_ids": set()})
        item["record_count"] += 1
        item["three_refs_match_smot_kind_count"] += int(record["status"] == "three_refs_match_smot_kind")
        item["paths"].add(record["path"])
        item["single_ids"].add(record["single_id"])
    species_summary = [
        {
            "kind_id": kind,
            "record_count": item["record_count"],
            "three_refs_match_smot_kind_count": item["three_refs_match_smot_kind_count"],
            "paths": sorted(item["paths"], key=str.casefold),
            "single_ids": sorted(item["single_ids"]),
        }
        for kind, item in sorted(by_kind.items())
    ]
    return {
        "scope": ENCOUNT_ROOT,
        "merge_policy": romfs.describe()["merge_policy"],
        "monp": {
            "path": MONP_PATH,
            "sha256": hashlib.sha256(monp_bytes).hexdigest(),
            "record_count": len(monp_species),
            "id_kind_count": len(monp_species),
        },
        "archive_count": len(archives),
        "archives_with_parse_errors": sum("error" in item for item in archives),
        "smot_member_count": sum(item["smot_member_count"] for item in archives),
        "record_count": len(records),
        "three_refs_match_smot_kind_count": sum(item["status"] == "three_refs_match_smot_kind" for item in records),
        "other_reference_patterns_count": sum(item["status"] != "three_refs_match_smot_kind" for item in records),
        "species": species_summary,
        "archives": archives,
    }
