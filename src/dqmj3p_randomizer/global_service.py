"""Build a same-size per-record encounter overlay."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import shutil
import tempfile
from datetime import datetime, timezone
from collections import defaultdict
from pathlib import Path
from typing import Any
import zipfile

from .romfs_source import RomFsSource, RomFsSourceError
from .global_catalog import FAMILY_CODES, RANK_CODES, GlobalCatalogError, merge_global_catalog
from .global_encounters import ENCOUNT_ROOT, MONP_PATH, scan_global_encounters
from .global_party import intersect_candidate_party_words, scan_party_monp_candidates
from .global_randomizer import (
    GlobalOptions,
    patch_et_archive,
    patch_monsterparam,
    plan_encounter_randomization,
)


KINDPARAM_PATH = "data/Parameter/KindParam.tp"
KINDCONFIG_PATH = "data/Parameter/KindConfigParam.tp"
_VALID_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._ -]{0,79}$")


class GlobalBuildError(ValueError):
    """A global build could not be completed safely."""


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _safe_output(project_root: Path, output_dir: Path, name: str) -> tuple[Path, Path]:
    project = project_root.resolve(strict=True)
    output_root = project / "output"
    if output_root.resolve(strict=False) != output_root:
        raise GlobalBuildError("La cartella di output deve essere reale, non un collegamento simbolico")
    if not _VALID_NAME.fullmatch(name) or name.endswith((".", " ")):
        raise GlobalBuildError("Nome della cartella non valido")
    supplied = output_dir.expanduser()
    if not supplied.is_absolute():
        supplied = project / supplied
    resolved = supplied.resolve(strict=False)
    if resolved != output_root:
        raise GlobalBuildError(f"La cartella di output deve essere {output_root}")
    if supplied.exists() and supplied.resolve(strict=True) != resolved:
        raise GlobalBuildError("Il percorso di output contiene un collegamento simbolico non consentito")
    destination = resolved / name
    if not _within(destination, output_root) or destination.exists():
        raise GlobalBuildError(f"La cartella di destinazione esiste già o si trova fuori dal progetto: {destination}")
    zip_path = destination.with_name(destination.name + ".zip")
    if zip_path.exists():
        raise GlobalBuildError(f"Il file ZIP esiste già: {zip_path}")
    return output_root, destination


def build_global_overlay(
    *,
    project_root: Path,
    base_romfs_root: Path,
    update_romfs_root: Path,
    seed: int,
    output_name: str | None = None,
    include_special_donors: bool = False,
    include_nonwild_instances: bool = False,
    donor_family_codes: frozenset[int] | None = None,
    donor_rank_codes: frozenset[int] | None = None,
) -> dict[str, Any]:
    """Build a mod from user-extracted base and update RomFS folders."""
    project = project_root.resolve(strict=True)
    requested_seed = seed
    if seed == 0:
        seed = secrets.randbelow(2**64 - 1) + 1
    output_root = project / "output"
    if output_name is None:
        output_name = f"seed_{seed}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')}"
    output_root, destination = _safe_output(project, output_root, output_name)
    try:
        dataset = RomFsSource(base_romfs_root, update_romfs_root)
    except (RomFsSourceError, OSError) as exc:
        raise GlobalBuildError(f"Le cartelle RomFS non sono disponibili o sono incomplete: {exc}") from exc
    resolved_output_root = output_root.resolve(strict=False)
    if any(
        _within(resolved_output_root, source_root)
        or _within(source_root, resolved_output_root)
        for source_root in (dataset.base_root, dataset.update_root)
    ):
        raise GlobalBuildError("La cartella di output deve essere separata dalle cartelle RomFS")

    try:
        kindparam = dataset.read(KINDPARAM_PATH)
        monsterparam = dataset.read(MONP_PATH)
        kindconfig = dataset.read(KINDCONFIG_PATH)
    except RomFsSourceError as exc:
        raise GlobalBuildError(f"Manca una tabella Parameter richiesta: {exc}") from exc
    model_paths = dataset.model_paths
    catalog = merge_global_catalog(kindparam, monsterparam, kindconfig, model_paths)
    inventory = scan_global_encounters(dataset)
    options = GlobalOptions(
        seed=seed,
        include_special_donors=include_special_donors,
        include_nonwild_instances=include_nonwild_instances,
        donor_family_codes=donor_family_codes,
        donor_rank_codes=donor_rank_codes,
    )
    plan = plan_encounter_randomization(catalog, inventory, options)
    selected_ids = set(plan["selected_instance_ids"])

    patched_monster, monster_audit = patch_monsterparam(
        monsterparam, selected_ids,
        include_nonwild_instances=include_nonwild_instances,
        instance_mapping=plan["instance_mapping"],
    )
    changed_instance_ids = set(monster_audit["modified_instance_ids"])

    try:
        party_report = scan_party_monp_candidates(dataset, set(catalog["monp_instances"]))
    except GlobalCatalogError as exc:
        raise GlobalBuildError(str(exc)) from exc
    party_impact = intersect_candidate_party_words(party_report, changed_instance_ids)

    modified_files: dict[str, bytes] = {}
    file_audits: list[dict[str, Any]] = []
    if patched_monster != monsterparam:
        modified_files[MONP_PATH] = patched_monster
        file_audits.append(monster_audit)

    for path in dataset.paths(ENCOUNT_ROOT):
        filename = path.rsplit("/", 1)[-1].casefold()
        if not (filename.startswith("et_") and filename.endswith(".xbb")):
            continue
        source_bytes = dataset.read(path)
        patched, audit = patch_et_archive(
            source_bytes, path, smot_row_mapping=plan["smot_row_mapping"]
        )
        if patched != source_bytes:
            modified_files[path] = patched
            file_audits.append(audit)

    if not modified_files:
        raise GlobalBuildError("Con questo seed e questi filtri non è stata generata alcuna modifica")

    species = {row["kind_id"]: row for row in catalog["species"]}
    instance_rows = [
        {**row,
         "source_name": species.get(row["source_kind_id"], {}).get("name"),
         "donor_name": species.get(row["donor_kind_id"], {}).get("name")}
        for row in plan["instance_rows"]
    ]
    smot_row_details = [
        {**row,
         "source_name": species.get(row["source_kind_id"], {}).get("name"),
         "donor_name": species.get(row["donor_kind_id"], {}).get("name")}
        for row in plan["smot_row_details"]
    ]
    unchanged_rows = [
        {**row, "name": species.get(row.get("kind_id", 0), {}).get("name")}
        for row in plan["unchanged"]
    ]
    instance_row_uses: dict[int, set[tuple[str, int, int]]] = defaultdict(set)
    for archive in inventory["archives"]:
        for row in archive.get("records", ()):
            identity = (row["path"].casefold(), row["member_index"], row["record_index"])
            for instance_id in row["monp_refs"]:
                if instance_id:
                    instance_row_uses[instance_id].add(identity)
    shared_ids = [uses for uses in instance_row_uses.values() if len(uses) > 1]
    manifest: dict[str, Any] = {
        "tool": "dqmj3p-global-randomizer",
        "version": "0.5.0",
        "romfs_source": dataset.describe(),
        "requested_seed": requested_seed,
        "seed": seed,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_fingerprints": {
            "effective_romfs_sha256": dataset.describe()["content_sha256"],
            "effective_KindParam_sha256": _sha256(kindparam),
            "effective_MonsterParam_sha256": _sha256(monsterparam),
            "effective_KindConfigParam_sha256": _sha256(kindconfig),
        },
        "options": {
            "include_special_donors": include_special_donors,
            "include_nonwild_instances": include_nonwild_instances,
            "donor_family_codes": (
                sorted(options.donor_family_codes)
                if options.donor_family_codes is not None else None
            ),
            "donor_families": (
                [
                    {"code": code, "name": FAMILY_CODES.get(code, f"Family {code}")}
                    for code in sorted(options.donor_family_codes)
                ]
                if options.donor_family_codes is not None else "all"
            ),
            "donor_rank_codes": (
                sorted(options.donor_rank_codes)
                if options.donor_rank_codes is not None else None
            ),
            "donor_ranks": (
                [
                    {"code": code, "name": RANK_CODES.get(code, f"Rank {code}")}
                    for code in sorted(options.donor_rank_codes)
                ]
                if options.donor_rank_codes is not None else "all"
            ),
            "same_size_required": True,
            "avoid_fixed_points": True,
        },
        "scope": {
            "et_archive_count": inventory["archive_count"],
            "smot_member_count": inventory["smot_member_count"],
            "smot_record_count": inventory["record_count"],
            "active_kind_count": plan["active_kind_count"],
            "selected_monp_instance_count": len(selected_ids),
            "changed_monp_instance_count": len(changed_instance_ids),
            "unknown_size_kinds_unchanged": plan["unknown_size_kind_count"],
            "include_nonwild_instances": include_nonwild_instances,
            "monp_ids_shared_across_smot_rows": len(shared_ids),
            "maximum_smot_rows_using_one_monp_id": max((len(uses) for uses in instance_row_uses.values()), default=0),
        },
        "donors": {
            "normal_count": plan["normal_donor_kind_count"],
            "selected_count": plan["donor_kind_count"],
            "include_special_donors": include_special_donors,
        },
        "instance_mappings": instance_rows,
        "smot_definition_mappings": smot_row_details,
        "unchanged_records": unchanged_rows,
        "leader_rules": {
            "primary_ref_matched_original_smot_kind": plan["primary_matched_row_count"],
            "nominal_kind_independent_fallback": plan["nominal_fallback_row_count"],
        },
        "party_table_candidate_overlap": party_impact,
        "modified_files": file_audits,
        "validation": {
            "same_size_mapping": True,
            "only_monp_kind_plus2_and_smot_kind_plus4_changed": True,
            "all_user_source_files_read_only": True,
            "monp_ids_reuse_seeded_mapping": True,
        },
        "limitations": [
            "Il pacchetto legge solo i file necessari dal RomFS scelto dall'utente e non modifica i file originali.",
            "I quattro valori PTYT sono segnalati perché coincidono numericamente con ID MONP; il loro significato non è confermato.",
            "La modalità eventi include i record MONP fuori dagli incontri SMOT, ma non distingue i record di boss, eventi o contenuti della storia.",
            "Le specie senza una taglia nota o senza un sostituto con lo stesso numero di slot restano invariate.",
        ],
    }
    spoiler = [f"Seed: {seed}", "", "Sostituzioni per record MONP:"]
    spoiler.extend(
        f"- ID {row['instance_id']}: {row['source_name'] or 'kind ' + str(row['source_kind_id'])} -> "
        f"{row['donor_name'] or 'kind ' + str(row['donor_kind_id'])} ({row['size_slots']} slot)"
        for row in instance_rows
    )
    spoiler.extend(["", "Sostituzioni leader incontro:"])
    spoiler.extend(
        f"- {row['path']} / {row['member']} riga {row['record_index']}: "
        f"{row['source_name'] or row['source_kind_id']} -> {row['donor_name'] or row['donor_kind_id']} [{row['rule']}]"
        for row in smot_row_details
        if row["source_kind_id"] != row["donor_kind_id"]
    )
    spoiler.extend([
        "",
        f"Record SMOT analizzati: {inventory['record_count']}",
        f"Record MONP modificati: {len(changed_instance_ids)}",
        f"Parole PTYT candidate coincidenti con ID MONP modificati: {party_impact['candidate_party_words_matching_changed_monp_instance_ids']}",
        "La tabella PTYT è stata analizzata in base alle corrispondenze numeriche; questo non ne conferma il significato in gioco.",
    ])

    stage: Path | None = None
    promoted = False
    zip_temp: Path | None = None
    zip_promoted = False
    zip_owned = False
    zip_destination = destination.with_name(destination.name + ".zip")
    try:
        output_root.mkdir(parents=True, exist_ok=True)
        stage = Path(tempfile.mkdtemp(prefix=f".{output_name}.", dir=output_root))
        romfs_out = stage / "romfs"
        for relative, data in modified_files.items():
            target = romfs_out / Path(*relative.split("/"))
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        (stage / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        (stage / "spoiler.txt").write_text("\n".join(spoiler) + "\n", encoding="utf-8")
        config = {
            "seed": seed,
            "effective_romfs_sha256": dataset.describe()["content_sha256"],
            "include_special_donors": include_special_donors,
            "include_nonwild_instances": include_nonwild_instances,
            "donor_family_codes": (
                sorted(options.donor_family_codes)
                if options.donor_family_codes is not None else None
            ),
            "donor_rank_codes": (
                sorted(options.donor_rank_codes)
                if options.donor_rank_codes is not None else None
            ),
        }
        (stage / "config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        source_readme = project / "README.md"
        if source_readme.is_file():
            shutil.copyfile(source_readme, stage / "README.md")

        fd, temp_name = tempfile.mkstemp(prefix=f".{output_name}.", suffix=".zip.tmp", dir=output_root)
        os.close(fd)
        zip_temp = Path(temp_name)
        with zipfile.ZipFile(zip_temp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
            for file_path in sorted((item for item in stage.rglob("*") if item.is_file()), key=lambda item: item.as_posix().casefold()):
                bundle.write(file_path, file_path.relative_to(stage).as_posix())
        if destination.exists():
            raise GlobalBuildError(f"Destinazione creata durante la build: {destination}")
        if zip_destination.exists():
            raise GlobalBuildError(f"Archivio creato durante la build: {zip_destination}")
        os.replace(stage, destination)
        promoted = True
        stage = None
        # Exclusive create prevents replacing an archive from another run.
        with zip_destination.open("xb") as target:
            zip_owned = True
            with zip_temp.open("rb") as source:
                shutil.copyfileobj(source, target)
        zip_promoted = True
        zip_temp.unlink()
        zip_temp = None
    except Exception:
        if stage is not None and stage.exists():
            shutil.rmtree(stage, ignore_errors=True)
        if promoted and destination.exists():
            shutil.rmtree(destination, ignore_errors=True)
        if zip_owned and zip_destination.exists():
            zip_destination.unlink(missing_ok=True)
        if zip_temp is not None:
            zip_temp.unlink(missing_ok=True)
        raise
    return {"output_dir": str(destination), "zip_path": str(zip_destination), "manifest": manifest}
