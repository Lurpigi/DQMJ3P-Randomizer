"""Create a portable ZIP of the app, public guides, and tests."""

from __future__ import annotations

import hashlib
import os
import shutil
import tempfile
import zipfile
from pathlib import Path


PROGRAM_ROOT = Path(__file__).resolve().parent
OUTPUT_ROOT = PROGRAM_ROOT / "output"
ARCHIVE_PATH = OUTPUT_ROOT / "dqmj3p_randomizer_portable.zip"


class PackageError(ValueError):
    pass


def _inside(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _files_to_package() -> list[tuple[Path, str]]:
    selected: list[tuple[Path, str]] = []

    def add_file(source: Path, archive_name: str) -> None:
        resolved = source.resolve(strict=True)
        if not _inside(resolved, PROGRAM_ROOT):
            raise PackageError(f"File fuori dalla cartella programma: {source}")
        if not source.is_file():
            raise PackageError(f"File programma mancante: {source}")
        selected.append((source, archive_name.replace("\\", "/")))

    for name in ("README.md", "randomizer_app.py", "randomize.py", "package_program.py"):
        add_file(PROGRAM_ROOT / name, name)
    add_file(PROGRAM_ROOT / "img" / "img.png", "img/img.png")

    source_root = PROGRAM_ROOT / "src" / "dqmj3p_randomizer"
    for path in sorted(source_root.rglob("*"), key=lambda item: item.as_posix().casefold()):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix.casefold() in {".pyc", ".pyo", ".bch", ".cia"}:
            continue
        relative = path.relative_to(PROGRAM_ROOT).as_posix()
        if relative.casefold().startswith("src/dqmj3p_randomizer/resources/game_data/"):
            continue
        add_file(path, relative)

    docs_root = PROGRAM_ROOT / "docs"
    doc_names = (
        "INSTALL.md",
        "FORMAT.md",
    )
    for name in doc_names:
        path = docs_root / name
        if path.is_file():
            add_file(path, f"docs/{name}")

    for path in sorted((PROGRAM_ROOT / "tests").glob("test_*.py"), key=lambda item: item.name.casefold()):
        add_file(path, f"tests/{path.name}")
    test_support = PROGRAM_ROOT / "tests" / "support.py"
    if test_support.is_file():
        add_file(test_support, "tests/support.py")

    names = [name.casefold() for _path, name in selected]
    if len(names) != len(set(names)):
        raise PackageError("Collisione di nomi case-insensitive nel pacchetto")
    if any(name.casefold().endswith((".cia", ".bch")) for name in names):
        raise PackageError("Il pacchetto non deve contenere CIA o BCH")
    if any(name.casefold().startswith(("output/", "docs/output/")) for name in names):
        raise PackageError("Il pacchetto non deve includere gli output generati")
    return selected


def create_portable_archive() -> Path:
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    if OUTPUT_ROOT.resolve(strict=True) != OUTPUT_ROOT:
        raise PackageError("La cartella output non deve essere un symlink")
    if ARCHIVE_PATH.exists():
        raise PackageError(f"Il pacchetto esiste già: {ARCHIVE_PATH}")
    files = _files_to_package()
    fd, temp_name = tempfile.mkstemp(prefix=".portable.", suffix=".zip.tmp", dir=OUTPUT_ROOT)
    os.close(fd)
    temp_path = Path(temp_name)
    owned_archive = False
    try:
        with zipfile.ZipFile(temp_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=7) as archive:
            for source, archive_name in files:
                archive.write(source, archive_name)
        if ARCHIVE_PATH.exists():
            raise PackageError(f"Il pacchetto è stato creato durante la preparazione: {ARCHIVE_PATH}")
        with ARCHIVE_PATH.open("xb") as output:
            owned_archive = True
            with temp_path.open("rb") as source:
                shutil.copyfileobj(source, output)
        with zipfile.ZipFile(ARCHIVE_PATH) as archive:
            corrupt = archive.testzip()
            if corrupt is not None:
                raise PackageError(f"File corrotto nel pacchetto: {corrupt}")
            names = archive.namelist()
            if any(name.casefold().endswith((".cia", ".bch")) for name in names):
                raise PackageError("Il pacchetto contiene un CIA o un modello BCH")
        return ARCHIVE_PATH
    except Exception:
        if owned_archive:
            ARCHIVE_PATH.unlink(missing_ok=True)
        raise
    finally:
        temp_path.unlink(missing_ok=True)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


if __name__ == "__main__":
    package = create_portable_archive()
    print(f"Creato: {package.relative_to(PROGRAM_ROOT)}")
    print(f"Dimensione: {package.stat().st_size} byte")
    print(f"SHA-256: {sha256(package)}")
