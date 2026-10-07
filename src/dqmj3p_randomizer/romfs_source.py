"""Read required files from two user-extracted RomFS layers."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path


REQUIRED_FILES = (
    "data/Parameter/KindParam.tp",
    "data/Parameter/MonsterParam.tp",
    "data/Parameter/KindConfigParam.tp",
    "data/Parameter/MonsterPartyTable.tp",
)
ENCOUNT_ROOT = "data/Field/Table/Encount"
MODEL_ROOT = "data/Model"


class RomFsSourceError(ValueError):
    """The selected RomFS layers are missing or unsafe to read."""


class RomFsSource:
    """Case-insensitive base/update overlay; update files take precedence."""

    def __init__(self, base_root: Path, update_root: Path) -> None:
        self.base_root = Path(base_root).expanduser().resolve(strict=True)
        self.update_root = Path(update_root).expanduser().resolve(strict=True)
        if not self.base_root.is_dir() or not self.update_root.is_dir():
            raise RomFsSourceError("Entrambe le selezioni devono essere cartelle RomFS")
        if self._within(self.base_root, self.update_root) or self._within(
            self.update_root, self.base_root
        ):
            raise RomFsSourceError("Le cartelle RomFS base e update devono essere separate")

        self._base = self._index(self.base_root)
        self._update = self._index(self.update_root)
        self._effective = dict(self._base)
        self._effective.update(self._update)

        for required in REQUIRED_FILES:
            if required.casefold() not in self._effective:
                raise RomFsSourceError(f"File richiesto non trovato: {required}")
        self._encount_paths = self.paths(ENCOUNT_ROOT)
        if not any(
            Path(path).name.casefold().startswith("et_")
            and path.casefold().endswith(".xbb")
            for path in self._encount_paths
        ):
            raise RomFsSourceError("Nessun archivio ET_*.xbb trovato nel RomFS")
        self._model_paths = tuple(
            path for path in self.paths(MODEL_ROOT) if path.casefold().endswith(".bch")
        )
        self._description: dict[str, object] | None = None

    @staticmethod
    def _within(path: Path, parent: Path) -> bool:
        try:
            path.relative_to(parent)
            return True
        except ValueError:
            return False

    @staticmethod
    def _index(root: Path) -> dict[str, tuple[str, Path]]:
        found: dict[str, tuple[str, Path]] = {}
        for current, dirs, files in os.walk(root, followlinks=False):
            current_path = Path(current)
            for dirname in dirs:
                if (current_path / dirname).is_symlink():
                    raise RomFsSourceError("Le cartelle RomFS non possono contenere symlink")
            for filename in files:
                path = current_path / filename
                if path.is_symlink():
                    raise RomFsSourceError("I file RomFS non possono essere symlink")
                relative = path.relative_to(root).as_posix()
                key = relative.casefold()
                if key in found:
                    raise RomFsSourceError(
                        f"Percorso duplicato senza distinzione maiuscole/minuscole: {relative}"
                    )
                found[key] = (relative, path)
        return found

    @property
    def model_paths(self) -> tuple[str, ...]:
        return self._model_paths

    def _entry(self, path: str) -> tuple[str, Path, str]:
        key = path.replace("\\", "/").strip("/").casefold()
        if not key or key.startswith("../") or "/../" in f"/{key}/":
            raise RomFsSourceError(f"Percorso RomFS non valido: {path}")
        entry = self._effective.get(key)
        if entry is None:
            raise RomFsSourceError(f"File RomFS non trovato: {path}")
        layer = "update" if key in self._update else "base"
        return entry[0], entry[1], layer

    def read(self, path: str) -> bytes:
        _relative, file_path, _layer = self._entry(path)
        return file_path.read_bytes()

    def source_for(self, path: str) -> str:
        _relative, _file_path, layer = self._entry(path)
        return layer

    def paths(self, prefix: str) -> list[str]:
        key = prefix.replace("\\", "/").strip("/").casefold()
        start = f"{key}/" if key else ""
        return sorted(
            (
                relative
                for relative, _file_path in self._effective.values()
                if relative.casefold().startswith(start)
            ),
            key=str.casefold,
        )

    def describe(self) -> dict[str, object]:
        if self._description is not None:
            return dict(self._description)
        content_hash = hashlib.sha256()
        fingerprint_paths = {
            path.casefold(): path for path in REQUIRED_FILES
        }
        for path in self._encount_paths:
            name = Path(path).name.casefold()
            if name.startswith("et_") and name.endswith(".xbb"):
                fingerprint_paths[path.casefold()] = path
        for model_path in self._model_paths:
            fingerprint_paths[model_path.casefold()] = model_path
        for key, relative in sorted(fingerprint_paths.items()):
            content_hash.update(key.encode("utf-8"))
            content_hash.update(b"\0")
            if relative.casefold().endswith(".bch"):
                content_hash.update(b"model-path-only\0")
            else:
                content_hash.update(hashlib.sha256(self.read(relative)).digest())

        self._description = {
            "kind": "user_extracted_layered_romfs",
            "merge_policy": "update overrides base case-insensitively",
            "et_archive_count": sum(
                Path(path).name.casefold().startswith("et_")
                and path.casefold().endswith(".xbb")
                for path in self._encount_paths
            ),
            "model_file_count": len(self._model_paths),
            "base_file_count": len(self._base),
            "update_file_count": len(self._update),
            "content_sha256": content_hash.hexdigest(),
        }
        return dict(self._description)
