"""Seeded per-record same-size substitutions and narrow MONP/SMOT patches."""

from __future__ import annotations

import hashlib
import random
import struct
from dataclasses import dataclass
from typing import Any, Mapping

from .global_catalog import (
    GlobalCatalogError, MONP_LEVEL_OFFSET, MONP_SKILL_OFFSETS, parse_monp_instances,
)
from .global_encounters import SMOT_STRIDE
from .inspector import XbbFormatError, parse_xbb_bytes


class GlobalRandomizerError(ValueError):
    """The selected inputs cannot produce a safe encounter plan."""


MIN_MONSTER_LEVEL = 1
MAX_MONSTER_LEVEL = 99
MONSTER_LEVELS = list(range(MIN_MONSTER_LEVEL, MAX_MONSTER_LEVEL + 1))


@dataclass(frozen=True)
class GlobalOptions:
    seed: int
    include_special_donors: bool = False
    include_nonwild_instances: bool = False
    randomize_levels: bool = False
    randomize_skills: bool = False
    avoid_fixed_points: bool = True
    donor_family_codes: frozenset[int] | None = None
    donor_rank_codes: frozenset[int] | None = None

    def __post_init__(self) -> None:
        if isinstance(self.seed, bool) or not isinstance(self.seed, int) or not 0 <= self.seed < 2**64:
            raise GlobalRandomizerError("Il seed deve essere un numero intero senza segno a 64 bit")
        for name in (
            "include_special_donors", "include_nonwild_instances", "randomize_levels", "randomize_skills",
            "avoid_fixed_points",
        ):
            if not isinstance(getattr(self, name), bool):
                raise GlobalRandomizerError(f"{name} deve essere booleano")
        if self.donor_family_codes is not None:
            try:
                family_codes = frozenset(self.donor_family_codes)
            except TypeError as exc:
                raise GlobalRandomizerError("Le famiglie selezionate non sono valide") from exc
            if not family_codes or any(
                isinstance(code, bool) or not isinstance(code, int) or code <= 0
                for code in family_codes
            ):
                raise GlobalRandomizerError("Seleziona almeno una famiglia valida")
            object.__setattr__(self, "donor_family_codes", family_codes)
        if self.donor_rank_codes is not None:
            try:
                rank_codes = frozenset(self.donor_rank_codes)
            except TypeError as exc:
                raise GlobalRandomizerError("I gradi selezionati non sono validi") from exc
            if not rank_codes or any(
                isinstance(code, bool) or not isinstance(code, int) or code <= 0
                for code in rank_codes
            ):
                raise GlobalRandomizerError("Seleziona almeno un grado valido")
            object.__setattr__(self, "donor_rank_codes", rank_codes)


def _seeded_choice(seed: int, key: str, choices: list[int]) -> int | None:
    if not choices:
        return None
    digest = hashlib.sha256(f"{seed}:{key}".encode("utf-8")).digest()
    rng = random.Random(int.from_bytes(digest[:16], "little"))
    return rng.choice(choices)


def plan_encounter_randomization(
    catalog: Mapping[str, Any],
    encounter_inventory: Mapping[str, Any],
    options: GlobalOptions,
) -> dict[str, Any]:
    """Plan same-size substitutions per MONP ID and SMOT encounter record."""
    species = {row["kind_id"]: row for row in catalog.get("species", ())}
    instances = catalog.get("monp_instances", {})
    if not species or not instances:
        raise GlobalRandomizerError("Catalogo KINP/MONP vuoto o non valido")

    # Use skill IDs already assigned in the source tables, never arbitrary IDs.
    skill_pool = sorted(
        {row["native_skill_id"] for row in species.values() if row["native_skill_id"]}
        | {skill for row in instances.values() if row["kind_id"] for skill in row["skill_ids"] if skill}
    )
    if options.randomize_skills and not skill_pool:
        raise GlobalRandomizerError("Nessun set di abilità disponibile nei dati di gioco")

    donor_family_codes = options.donor_family_codes
    donor_rank_codes = options.donor_rank_codes

    def donor_family_allowed(kind_id: int) -> bool:
        if donor_family_codes is None:
            return True
        kind = species.get(kind_id)
        return bool(kind and kind.get("family_code") in donor_family_codes)

    def donor_rank_allowed(kind_id: int) -> bool:
        if donor_rank_codes is None:
            return True
        kind = species.get(kind_id)
        return bool(kind and kind.get("rank_code") in donor_rank_codes)

    def donor_allowed(kind_id: int) -> bool:
        return donor_family_allowed(kind_id) and donor_rank_allowed(kind_id)

    selected_ids: set[int] = set()
    active_kinds: set[int] = set()
    for archive in encounter_inventory.get("archives", ()):
        if "error" in archive:
            raise GlobalRandomizerError(f"Archivio ET non valido: {archive.get('path')}: {archive['error']}")
        if archive.get("member_errors"):
            raise GlobalRandomizerError(f"SMOT non valido in {archive.get('path')}: {archive['member_errors'][0]}")
        for row in archive.get("records", ()):
            kind_id = row.get("kind_id", 0)
            if kind_id:
                active_kinds.add(kind_id)
            for instance_id in row.get("monp_refs", ()):
                if not instance_id:
                    continue
                instance = instances.get(instance_id)
                if instance is None:
                    raise GlobalRandomizerError(
                        f"La definizione SMOT riferisce l'ID MONP {instance_id}, non presente nella tabella effettiva"
                    )
                selected_ids.add(instance_id)
                if instance["kind_id"]:
                    active_kinds.add(instance["kind_id"])

    normal_donors = set(active_kinds)
    if options.include_nonwild_instances:
        selected_ids.update(int(instance_id) for instance_id in instances)
        active_kinds.update(row["kind_id"] for row in instances.values() if row["kind_id"])

    def backed(kind_id: int) -> bool:
        item = species.get(kind_id)
        return bool(item and item.get("donor_size_supported") and item.get("size_slots") in {1, 2, 3, 4})

    donor_ids = {
        kind_id for kind_id in species
        if backed(kind_id)
        and (options.include_special_donors or kind_id in normal_donors)
        and donor_allowed(kind_id)
    }
    if not donor_ids:
        raise GlobalRandomizerError(
            "Nessun sostituto soddisfa i filtri e ha taglia, record MONP e modello compatibili"
        )

    donors_by_size: dict[int, list[int]] = {}
    for kind_id in sorted(donor_ids):
        donors_by_size.setdefault(species[kind_id]["size_slots"], []).append(kind_id)

    def choose(source_kind: int, key: str, *, exclude: set[int] | None = None) -> tuple[int, str]:
        item = species.get(source_kind)
        size = item.get("size_slots") if item else None
        if size not in {1, 2, 3, 4}:
            return source_kind, "unknown_or_unlisted_size"
        pool = donors_by_size.get(size, [])
        alternatives = [kind for kind in pool if kind != source_kind]
        choices = alternatives if options.avoid_fixed_points and alternatives else [
            kind for kind in pool if not options.avoid_fixed_points or kind == source_kind
        ]
        if exclude:
            distinct = [kind for kind in choices if kind not in exclude]
            if distinct:
                choices = distinct
        target = _seeded_choice(options.seed, key, choices)
        if target is None:
            return source_kind, "no_same_size_donor"
        if target == source_kind:
            return target, "only_same_size_donor"
        return target, "mapped"

    # MONP +2 is the per-instance species field; IDs are stable links shared by SMOT rows.
    instance_mapping: dict[int, int] = {}
    level_mapping: dict[int, int] = {}
    skill_mapping: dict[int, tuple[int, ...]] = {}
    instance_rows: list[dict[str, Any]] = []
    unchanged: list[dict[str, Any]] = []
    for instance_id in sorted(selected_ids):
        row = instances.get(instance_id)
        if row is None:
            raise GlobalRandomizerError(f"ID di istanza MONP non trovato: {instance_id}")
        source_kind = row["kind_id"]
        if source_kind == 0:
            instance_mapping[instance_id] = 0
            unchanged.append({"instance_id": instance_id, "kind_id": 0, "reason": "kind_zero"})
            continue
        donor, reason = choose(source_kind, f"instance:{instance_id}")
        instance_mapping[instance_id] = donor
        source_level = row["level"]
        target_level = source_level
        if options.randomize_levels:
            selected_level = _seeded_choice(
                options.seed, f"level:{instance_id}", MONSTER_LEVELS)
            if selected_level is None:
                raise GlobalRandomizerError(f"Livello non pianificato per l'ID MONP {instance_id}")
            target_level = selected_level
            level_mapping[instance_id] = selected_level
        source_skills = row["skill_ids"]
        if options.randomize_skills:
            target_skills = [0, 0, 0]
            available_skills = list(skill_pool)
            for slot in (0, 1, 2):
                if slot and not source_skills[slot]:
                    continue
                skill = _seeded_choice(options.seed, f"skill:{instance_id}:{slot}", available_skills)
                if skill is None:
                    break
                target_skills[slot] = skill
                available_skills.remove(skill)
        else:
            # Only the first skill is species-specific; retain supplemental sets.
            native_skill = species.get(donor, {}).get("native_skill_id", source_skills[0])
            target_skills = [native_skill, *source_skills[1:]]
            seen_skills: set[int] = set()
            for slot, skill in enumerate(target_skills):
                if skill in seen_skills:
                    target_skills[slot] = 0
                elif skill:
                    seen_skills.add(skill)
        skill_mapping[instance_id] = tuple(target_skills)
        instance_rows.append({
            "instance_id": instance_id,
            "source_kind_id": source_kind,
            "donor_kind_id": donor,
            "source_level": source_level,
            "target_level": target_level,
            "source_skill_ids": list(source_skills),
            "target_skill_ids": target_skills,
            "size_slots": species.get(source_kind, {}).get("size_slots"),
            "reason": reason,
        })
        if reason != "mapped":
            unchanged.append({"instance_id": instance_id, "kind_id": source_kind, "reason": reason})

    row_mappings: dict[tuple[str, int, int], int] = {}
    row_details: list[dict[str, Any]] = []
    records = sorted(
        (record for archive in encounter_inventory.get("archives", ()) for record in archive.get("records", ())),
        key=lambda row: (row["path"].casefold(), row["member_index"], row["record_index"]),
    )
    for row in records:
        source_kind = row["kind_id"]
        primary_id = row["monp_refs"][0]
        primary_row = instances.get(primary_id) if primary_id else None
        primary_source_kind = primary_row["kind_id"] if primary_row else None
        if primary_id and primary_source_kind == source_kind:
            donor = instance_mapping.get(primary_id, source_kind)
            rule = "primary_ref_matched_original_smot_kind"
            mismatch_unavoidable = False
        else:
            # Preserve the original leader/primary mismatch instead of imposing a link.
            primary_donor = instance_mapping.get(primary_id) if primary_id else None
            donor, reason = choose(
                source_kind,
                f"smot:{row['path'].casefold()}:{row['member_index']}:{row['record_index']}",
                exclude={primary_donor} if primary_donor is not None else None,
            )
            rule = "nominal_kind_independent_fallback"
            mismatch_unavoidable = bool(
                primary_donor is not None and donor == primary_donor and source_kind != primary_source_kind
            )
            if reason != "mapped":
                unchanged.append({
                    "path": row["path"], "member": row["member"],
                    "record_index": row["record_index"], "kind_id": source_kind, "reason": reason,
                })
        identity = (row["path"].casefold(), row["member_index"], row["record_index"])
        row_mappings[identity] = donor
        row_details.append({
            "path": row["path"], "member": row["member"],
            "member_index": row["member_index"], "record_index": row["record_index"],
            "single_id": row["single_id"], "source_kind_id": source_kind, "donor_kind_id": donor,
            "size_slots": species.get(source_kind, {}).get("size_slots"), "rule": rule,
            "primary_monp_id": primary_id, "primary_monp_original_kind_id": primary_source_kind,
            "primary_monp_donor_kind_id": instance_mapping.get(primary_id) if primary_id else None,
            "primary_mismatch_not_avoidable_with_available_donors": mismatch_unavoidable,
        })

    target_kinds = set(active_kinds)
    if options.include_nonwild_instances:
        target_kinds.update(
            row["kind_id"] for row in instances.values()
            if row["kind_id"]
        )
    return {
        "seed": options.seed,
        "include_special_donors": options.include_special_donors,
        "include_nonwild_instances": options.include_nonwild_instances,
        "randomize_levels": options.randomize_levels,
        "randomize_skills": options.randomize_skills,
        "skill_mode": "random" if options.randomize_skills else "species",
        "skill_pool_count": len(skill_pool),
        "level_range": [MIN_MONSTER_LEVEL, MAX_MONSTER_LEVEL] if options.randomize_levels else None,
        "donor_family_codes": sorted(donor_family_codes) if donor_family_codes is not None else None,
        "donor_rank_codes": sorted(donor_rank_codes) if donor_rank_codes is not None else None,
        "instance_mapping": instance_mapping,
        "level_mapping": level_mapping,
        "skill_mapping": skill_mapping,
        "instance_rows": instance_rows,
        "smot_row_mapping": row_mappings,
        "smot_row_details": row_details,
        "unchanged": unchanged,
        "active_kind_count": len(active_kinds),
        "selected_instance_ids": sorted(selected_ids),
        "normal_donor_kind_count": sum(backed(kind_id) for kind_id in normal_donors),
        "donor_kind_count": len(donor_ids),
        "donor_kind_ids": sorted(donor_ids),
        "unknown_size_kind_count": sum(
            species.get(kind_id, {}).get("size_slots") not in {1, 2, 3, 4}
            for kind_id in target_kinds
        ),
        "primary_matched_row_count": sum(row["rule"] == "primary_ref_matched_original_smot_kind" for row in row_details),
        "nominal_fallback_row_count": sum(row["rule"] == "nominal_kind_independent_fallback" for row in row_details),
    }


def _patch_u16(data: bytearray, offset: int, value: int, allowed_offsets: set[int]) -> None:
    if offset < 0 or offset + 2 > len(data):
        raise GlobalRandomizerError("Tentativo di patch fuori dai limiti del file")
    if value < 0 or value > 0xFFFF:
        raise GlobalRandomizerError("ID della specie fuori dall'intervallo consentito (0-65535)")
    if offset not in allowed_offsets:
        raise GlobalRandomizerError("Tentativo di patch fuori dai campi autorizzati")
    struct.pack_into("<H", data, offset, value)


def _audit_changes(before: bytes, after: bytes, allowed: set[int], path: str) -> dict[str, Any]:
    if len(before) != len(after):
        raise GlobalRandomizerError(f"La patch ha cambiato la dimensione di {path}")
    changed = [index for index, (old, new) in enumerate(zip(before, after)) if old != new]
    if any(index not in allowed for index in changed):
        bad = next(index for index in changed if index not in allowed)
        raise GlobalRandomizerError(f"La patch ha alterato un byte non autorizzato in {path}: 0x{bad:x}")
    return {
        "path": path,
        "source_sha256": hashlib.sha256(before).hexdigest(),
        "output_sha256": hashlib.sha256(after).hexdigest(),
        "size_bytes": len(before),
        "modified_byte_count": len(changed),
        "modified_offsets": changed,
    }


def patch_monsterparam(
    data: bytes,
    selected_instance_ids: set[int],
    *,
    include_nonwild_instances: bool = False,
    instance_mapping: Mapping[int, int],
    level_mapping: Mapping[int, int] | None = None,
    skill_mapping: Mapping[int, tuple[int, ...]] | None = None,
) -> tuple[bytes, dict[str, Any]]:
    """Patch only MONP species (+2), level (+24), and skill (+64/+66/+68) fields."""
    try:
        parsed = parse_monp_instances(data)
    except GlobalCatalogError as exc:
        raise GlobalRandomizerError(str(exc)) from exc
    selected = set(parsed["instances"]) if include_nonwild_instances else set(selected_instance_ids)
    unknown = selected - set(parsed["instances"])
    if unknown:
        raise GlobalRandomizerError(f"ID MONP selezionati non trovati: {sorted(unknown)[:8]}")
    level_mapping = level_mapping or {}
    skill_mapping = skill_mapping or {}
    unknown_skill_ids = set(skill_mapping) - selected
    if unknown_skill_ids:
        raise GlobalRandomizerError(
            f"ID MONP con abilità pianificate ma non selezionati: {sorted(unknown_skill_ids)[:8]}"
        )
    for instance_id, skills in skill_mapping.items():
        if len(skills) != len(MONP_SKILL_OFFSETS) or any(
            isinstance(skill, bool) or not isinstance(skill, int) or not 0 <= skill <= 0xFFFF
            for skill in skills
        ):
            raise GlobalRandomizerError(f"Set di abilità non validi per l'ID MONP {instance_id}")
        if parsed["instances"][instance_id]["kind_id"] == 0:
            raise GlobalRandomizerError(f"Non è possibile assegnare abilità al record MONP vuoto {instance_id}")
    unknown_level_ids = set(level_mapping) - selected
    if unknown_level_ids:
        raise GlobalRandomizerError(
            f"ID MONP con livello pianificato ma non selezionati: {sorted(unknown_level_ids)[:8]}"
        )
    for instance_id, level in level_mapping.items():
        if isinstance(level, bool) or not isinstance(level, int) or not MIN_MONSTER_LEVEL <= level <= MAX_MONSTER_LEVEL:
            raise GlobalRandomizerError(
                f"Livello MONP non valido per l'ID {instance_id}: usa un valore da {MIN_MONSTER_LEVEL} a {MAX_MONSTER_LEVEL}"
            )
        if parsed["instances"][instance_id]["kind_id"] == 0:
            raise GlobalRandomizerError(f"Non è possibile assegnare un livello al record MONP vuoto {instance_id}")
    output = bytearray(data)
    allowed: set[int] = set()
    patched_kind_ids: list[int] = []
    patched_level_ids: list[int] = []
    patched_skill_ids: list[int] = []
    patched_ids: set[int] = set()
    for instance_id in sorted(selected):
        row = parsed["instances"][instance_id]
        old_kind = row["kind_id"]
        if instance_id not in instance_mapping:
            raise GlobalRandomizerError(f"ID MONP senza sostituzione pianificata: {instance_id}")
        new_kind = instance_mapping[instance_id]
        if new_kind != old_kind:
            offset = row["record_offset"] + 2  # MONP species field.
            allowed.update((offset, offset + 1))
            _patch_u16(output, offset, new_kind, allowed)
            patched_kind_ids.append(instance_id)
            patched_ids.add(instance_id)
        new_level = level_mapping.get(instance_id, row["level"])
        if new_level != row["level"]:
            offset = row["record_offset"] + MONP_LEVEL_OFFSET
            allowed.update((offset, offset + 1))
            struct.pack_into("<H", output, offset, new_level)
            patched_level_ids.append(instance_id)
            patched_ids.add(instance_id)
        old_skills = row["skill_ids"]
        new_skills = skill_mapping.get(instance_id, old_skills)
        if new_skills != old_skills:
            for relative, old_skill, new_skill in zip(MONP_SKILL_OFFSETS, old_skills, new_skills):
                if new_skill != old_skill:
                    offset = row["record_offset"] + relative
                    allowed.update((offset, offset + 1))
                    struct.pack_into("<H", output, offset, new_skill)
            patched_skill_ids.append(instance_id)
            patched_ids.add(instance_id)
    result = bytes(output)
    audit = _audit_changes(data, result, allowed, "data/Parameter/MonsterParam.tp")
    audit["modified_instance_ids"] = sorted(patched_ids)
    audit["modified_kind_instance_ids"] = patched_kind_ids
    audit["modified_level_instance_ids"] = patched_level_ids
    audit["modified_skill_instance_ids"] = patched_skill_ids
    audit["selected_instance_count"] = len(selected)
    return result, audit


def patch_et_archive(
    data: bytes,
    path: str,
    *,
    smot_row_mapping: Mapping[tuple[str, int, int], int],
) -> tuple[bytes, dict[str, Any]]:
    """Patch every supported ET SMOT row's kind field (+4), preserving XBB layout."""
    try:
        parsed = parse_xbb_bytes(data, path)
    except XbbFormatError as exc:
        raise GlobalRandomizerError(f"XBB non valido {path}: {exc}") from exc
    output = bytearray(data)
    allowed: set[int] = set()
    changed_rows: list[dict[str, int]] = []
    for member in parsed["members"]:
        start = member["payload_offset"]
        size = member["size_bytes"]
        payload = data[start:start + size]
        if payload[:4] != b"SMOT":
            continue
        if (size - 4) % SMOT_STRIDE:
            raise GlobalRandomizerError(f"SMOT non allineato a record {SMOT_STRIDE}: {path}/{member['name']}")
        rows = (size - 4) // SMOT_STRIDE
        for row_index in range(rows):
            row_offset = start + 4 + row_index * SMOT_STRIDE
            source_kind = struct.unpack_from("<H", data, row_offset + 4)[0]
            row_key = (path.casefold(), member["index"], row_index)
            if row_key not in smot_row_mapping:
                raise GlobalRandomizerError(f"SMOT senza sostituzione pianificata: {path}/{member['name']} riga {row_index}")
            target_kind = smot_row_mapping[row_key]
            if target_kind == source_kind:
                continue
            field_offset = row_offset + 4  # SMOT nominal leader species field.
            allowed.update((field_offset, field_offset + 1))
            _patch_u16(output, field_offset, target_kind, allowed)
            changed_rows.append({"member_index": member["index"], "record_index": row_index,
                                 "source_kind_id": source_kind, "donor_kind_id": target_kind})
    result = bytes(output)
    audit = _audit_changes(data, result, allowed, path)
    audit["modified_smot_rows"] = changed_rows
    return result, audit


