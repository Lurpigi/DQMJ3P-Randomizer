"""PTYT candidate-word cross-reference census; fields remain semantically unknown."""

from __future__ import annotations

import hashlib
import struct
from typing import Any, Iterable

from .global_catalog import GlobalCatalogError
from .romfs_source import RomFsSource, RomFsSourceError


PTYT_PATH = "data/Parameter/MonsterPartyTable.tp"
PTYT_STRIDE = 44


def scan_party_monp_candidates(romfs: RomFsSource, monp_instance_ids: set[int]) -> dict[str, Any]:
    """Report numeric words matching MONP IDs without calling them proven refs."""
    try:
        data = romfs.read(PTYT_PATH)
    except RomFsSourceError as exc:
        raise GlobalCatalogError(f"Manca {PTYT_PATH} nell'overlay: {exc}") from exc
    if len(data) < 4 or data[:4] != b"PTYT" or (len(data) - 4) % PTYT_STRIDE:
        raise GlobalCatalogError("MonsterPartyTable.tp non corrisponde a PTYT/44 byte")
    rows = (len(data) - 4) // PTYT_STRIDE
    words: list[dict[str, Any]] = []
    for row_index in range(rows):
        offset = 4 + row_index * PTYT_STRIDE
        name = data[offset + 16:offset + 32].split(b"\0", 1)[0].decode("ascii", errors="replace")
        for word_index in range(4):
            value = struct.unpack_from("<I", data, offset + word_index * 4)[0]
            if value in monp_instance_ids:
                words.append({
                    "record_index": row_index,
                    "record_offset": offset,
                    "word_index": word_index,
                    "value": value,
                    "key": name,
                })
    matching_ids = sorted({item["value"] for item in words})
    return {
        "path": PTYT_PATH,
        "sha256": hashlib.sha256(data).hexdigest(),
        "record_size": PTYT_STRIDE,
        "record_count": rows,
        "candidate_word_count": len(words),
        "candidate_instance_id_count": len(matching_ids),
        "candidate_instance_ids": matching_ids,
        "words": words,
        "semantic_confidence": "unconfirmed numeric words matching effective MONP instance IDs; not every word is proven to be a reference",
    }


def intersect_candidate_party_words(party_report: dict[str, Any], changed_monp_ids: set[int]) -> dict[str, Any]:
    selected_words = [item for item in party_report["words"] if item["value"] in changed_monp_ids]
    selected_ids = sorted({item["value"] for item in selected_words})
    return {
        "candidate_party_words_matching_changed_monp_instance_ids": len(selected_words),
        "candidate_party_changed_monp_instance_id_count": len(selected_ids),
        "candidate_party_changed_monp_instance_ids": selected_ids,
        "semantic_confidence": party_report["semantic_confidence"],
    }
