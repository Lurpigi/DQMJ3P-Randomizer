"""Inventory an extracted RomFS without changing its contents."""

from __future__ import annotations

import hashlib
import os
import struct
from pathlib import Path
import string
from typing import Any


HEADER_BYTES = 16
XBB_MAGIC = b"XBB\x01"
XBB_INDEX_OFFSET = 0x20
XBB_ENTRY_SIZE = 16
XBB_HASH_SIZE = 8
XBB_MAX_ENTRIES = 1_000_000


class InspectionError(ValueError):
    """Raised when the requested RomFS or report path is unsafe or invalid."""


class XbbFormatError(ValueError):
    """Raised when an XBB index or one of its member ranges is invalid."""


def parse_xbb(path: Path) -> dict[str, Any]:
    """Read and validate an XBB index and describe its member payloads.

    Layout assumptions come from verified local samples: magic at 0, count at
    4, 16-byte index rows at 0x20, followed by an 8-byte-per-entry hash table.
    Name offsets are absolute file offsets. Payload contents are never decoded.
    """
    file_size = path.stat().st_size
    with path.open("rb") as stream:
        data = stream.read()
    if len(data) != file_size:
        raise XbbFormatError("lettura incompleta del file")
    return parse_xbb_bytes(data, path.as_posix())


def parse_xbb_bytes(data: bytes, source: str = "<memory>") -> dict[str, Any]:
    """Parse XBB metadata from an in-memory archive with the same bounds checks."""
    file_size = len(data)
    if len(data) < XBB_INDEX_OFFSET or data[:4] != XBB_MAGIC:
        raise XbbFormatError("magic XBB\x01 o intestazione non valida")

    count = struct.unpack_from("<I", data, 4)[0]
    if count > XBB_MAX_ENTRIES:
        raise XbbFormatError(f"conteggio membri oltre il limite di sicurezza: {count}")
    name_region_start = XBB_INDEX_OFFSET + count * (XBB_ENTRY_SIZE + XBB_HASH_SIZE)
    if name_region_start > len(data):
        raise XbbFormatError("indice/hash table oltre la fine del file")

    raw_rows = []
    for index in range(count):
        row_offset = XBB_INDEX_OFFSET + index * XBB_ENTRY_SIZE
        payload_offset, payload_size, name_offset, name_hash = struct.unpack_from("<IIII", data, row_offset)
        if payload_offset > len(data) or payload_size > len(data) - payload_offset:
            raise XbbFormatError(f"membro {index}: intervallo payload fuori dal file")
        if payload_size and payload_offset < name_region_start:
            raise XbbFormatError(f"membro {index}: payload sovrapposto a intestazione o indice")
        if name_offset < name_region_start or name_offset >= len(data):
            raise XbbFormatError(f"membro {index}: nameOffset fuori dalla regione nomi")
        raw_rows.append((index, payload_offset, payload_size, name_offset, name_hash))

    payload_ranges = sorted(
        (offset, offset + size, index)
        for index, offset, size, _name_offset, _name_hash in raw_rows
        if size
    )
    for previous, current in zip(payload_ranges, payload_ranges[1:]):
        if current[0] < previous[1]:
            raise XbbFormatError(
                f"intervalli payload sovrapposti: membri {previous[2]} e {current[2]}"
            )
    first_payload_offset = payload_ranges[0][0] if payload_ranges else len(data)

    rows = []
    for index, payload_offset, payload_size, name_offset, name_hash in raw_rows:
        terminator = data.find(b"\0", name_offset)
        if terminator < 0 or terminator >= first_payload_offset:
            raise XbbFormatError(f"membro {index}: nome non terminato prima del primo payload")
        name_bytes = data[name_offset:terminator]
        name = name_bytes.decode("cp932", errors="replace")
        head = data[payload_offset:payload_offset + min(16, payload_size)]
        first_four = head[:4]
        ascii_magic = "".join(chr(byte) for byte in first_four)
        if not all(char in string.printable and char not in "\r\n\t\x0b\x0c" for char in ascii_magic):
            ascii_magic = ""
        rows.append({
            "index": index,
            "name": name,
            "name_offset": name_offset,
            "name_hash": f"0x{name_hash:08x}",
            "payload_offset": payload_offset,
            "size_bytes": payload_size,
            "magic": {"hex": head[:4].hex(" "), "ascii": ascii_magic},
            "header_hex": head.hex(" "),
        })

    return {
        "path": source,
        "archive_size_bytes": file_size,
        "magic": data[:4].hex(" "),
        "member_count": count,
        "index_offset": XBB_INDEX_OFFSET,
        "name_region_offset": name_region_start,
        "members": rows,
    }


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def validate_paths(romfs: Path, output: Path, project_root: Path) -> tuple[Path, Path]:
    """Resolve paths and guarantee writes remain under randomizer/output."""
    try:
        source = romfs.expanduser().resolve(strict=True)
    except OSError as exc:
        raise InspectionError(f"RomFS non accessibile: {romfs}: {exc}") from exc
    if not source.is_dir():
        raise InspectionError(f"Il percorso RomFS non è una cartella: {source}")

    if not (source / "data" / "Parameter").is_dir():
        raise InspectionError(f"RomFS non riconosciuto: manca data/Parameter in {source}")

    project = project_root.resolve()
    expected_output_root = project / "output"
    output_root = expected_output_root.resolve()
    if output_root != expected_output_root:
        raise InspectionError(f"La cartella output deve essere una cartella reale: {expected_output_root}")
    candidate = output.expanduser()
    if not candidate.is_absolute():
        candidate = project / candidate
    # Resolve the existing parent to catch .. and directory symlinks, then append
    # the filename. This allows the report file itself not to exist yet.
    try:
        resolved_parent = candidate.parent.resolve(strict=False)
    except OSError as exc:
        raise InspectionError(f"Percorso output non valido: {candidate}: {exc}") from exc
    destination = resolved_parent / candidate.name

    if not _is_within(destination, output_root):
        raise InspectionError(
            f"Il report deve essere scritto dentro {output_root}; richiesto: {destination}"
        )
    if _is_within(destination, source) or destination == source:
        raise InspectionError("Il report non può sovrascrivere o trovarsi dentro il RomFS sorgente")
    if destination.exists() and destination.is_dir():
        raise InspectionError(f"Il percorso output indica una cartella, serve un file JSON: {destination}")
    if destination.suffix.lower() != ".json":
        raise InspectionError("Il report deve avere estensione .json")
    return source, destination


def _header(path: Path) -> dict[str, str]:
    with path.open("rb") as stream:
        sample = stream.read(HEADER_BYTES)
    # Four bytes are often a useful magic identifier, but are only reported as
    # text when all bytes are printable ASCII. No format is inferred here.
    first_four = sample[:4]
    ascii_magic = "".join(chr(byte) for byte in first_four)
    if not all(char in string.printable and char not in "\r\n\t\x0b\x0c" for char in ascii_magic):
        ascii_magic = ""
    return {"hex": sample.hex(" "), "ascii_first_four": ascii_magic}


def _files(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted((path for path in directory.rglob("*") if path.is_file()), key=lambda p: p.as_posix().lower())


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def build_report(romfs: Path) -> dict[str, Any]:
    """Build a JSON-ready inventory of known RomFS areas, in read-only mode."""
    root = romfs.resolve(strict=True)
    parameter_root = root / "data" / "Parameter"
    parameter_files: list[dict[str, Any]] = []
    for path in _files(parameter_root):
        item: dict[str, Any] = {
            "path": _relative(path, root),
            "size_bytes": path.stat().st_size,
            "extension": path.suffix.lower(),
            "sha256": _sha256(path),
        }
        try:
            item["header"] = _header(path)
        except OSError as exc:
            item["read_error"] = str(exc)
        parameter_files.append(item)

    field_pos_root = root / "data" / "Field" / "Pos"
    field_pos_files = _files(field_pos_root)
    xbb_archives = []
    for path in field_pos_files:
        if path.suffix.lower() == ".xbb":
            try:
                archive = parse_xbb(path)
                archive["path"] = _relative(path, root)
                xbb_archives.append(archive)
            except (OSError, XbbFormatError) as exc:
                xbb_archives.append({"path": _relative(path, root), "validation_error": str(exc)})
    field_pos_dirs = sorted(
        (_relative(path, root) for path in field_pos_root.rglob("*") if path.is_dir()),
        key=str.lower,
    ) if field_pos_root.is_dir() else []

    nut_files = _files(root / "data")
    nut_files = [path for path in nut_files if path.suffix.lower() == ".nut"]
    nut_inventory = []
    for path in nut_files:
        try:
            size = path.stat().st_size
        except OSError:
            size = None
        nut_inventory.append({"path": _relative(path, root), "size_bytes": size})

    missing = [
        _relative(path, root)
        for path in (parameter_root, root / "data" / "Field" / "Pos", root / "data" / "Script")
        if not path.is_dir()
    ]
    return {
        "tool": "dqmj3p-randomizer-inspector",
        "version": "0.1.0",
        "mode": "read-only inventory; no binary fields decoded or modified",
        "romfs_root": str(root),
        "parameter": {
            "directory": _relative(parameter_root, root),
            "file_count": len(parameter_files),
            "files": parameter_files,
        },
        "field_pos": {
            "directory": _relative(field_pos_root, root),
            "file_count": len(field_pos_files),
            "directory_count": len(field_pos_dirs),
            "directories": field_pos_dirs,
            "files": [
                {"path": _relative(path, root), "size_bytes": path.stat().st_size}
                for path in field_pos_files
            ],
            "xbb_archive_count": len(xbb_archives),
            "xbb_archives": xbb_archives,
            "xbb_invalid_count": sum("validation_error" in archive for archive in xbb_archives),
        },
        "nut_files": {
            "scope": "data/**/*.nut (content type not classified)",
            "file_count": len(nut_inventory),
            "files": nut_inventory,
        },
        "missing_expected_directories": missing,
        "notes": [
            "Header bytes are reported as evidence only; no file format is assumed.",
            "The inventory does not change source files or generate a game mod.",
        ],
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def write_report(report: dict[str, Any], destination: Path) -> None:
    """Write a UTF-8 JSON report after path validation by the CLI."""
    import json

    destination.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive temporary file prevents partial JSON if the process is stopped.
    temp_path = destination.with_name(destination.name + ".tmp")
    try:
        with temp_path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(report, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
        os.replace(temp_path, destination)
    except FileExistsError as exc:
        raise InspectionError(f"File temporaneo report già presente: {temp_path}") from exc
    except Exception:
        try:
            temp_path.unlink(missing_ok=True)
        except OSError:
            pass
        raise
