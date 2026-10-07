"""Command line entry point for the per-record RomFS randomizer."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .global_catalog import FAMILY_NAME_TO_CODE, RANK_NAME_TO_CODE
from .global_service import GlobalBuildError, build_global_overlay


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="dqmj3p-randomizer",
        description="Crea un pacchetto usando le cartelle RomFS già estratte del gioco base e dell'aggiornamento 1.3.",
    )
    parser.add_argument("--seed", required=True, type=int, help="Numero intero da 0 a 2^64-1; con 0 viene generato un seed casuale")
    parser.add_argument("--base-romfs", required=True, type=Path, help="Cartella RomFS estratta del gioco base")
    parser.add_argument("--update-romfs", required=True, type=Path, help="Cartella RomFS estratta dell'aggiornamento 1.3")
    parser.add_argument("--output-name", help="Nome della cartella da creare in randomizer/output")
    parser.add_argument("--include-special-donors", action="store_true", help="Aggiunge ai possibili sostituti i mostri compatibili degli eventi e dei boss")
    parser.add_argument("--include-nonwild-instances", action="store_true", help="Estende le modifiche ai record MONP fuori dagli incontri selvatici")
    parser.add_argument(
        "--family", action="append", choices=sorted(FAMILY_NAME_TO_CODE), metavar="FAMILY",
        help="Limita i possibili sostituti a questa famiglia; ripeti l'opzione per aggiungerne altre.",
    )
    parser.add_argument(
        "--rank", action="append", choices=sorted(RANK_NAME_TO_CODE), metavar="RANK",
        help="Limita i possibili sostituti a questo grado (f/e/d/c/b/a/s/ss); puoi ripetere l'opzione.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    project = Path(__file__).resolve().parents[2]
    try:
        result = build_global_overlay(
            project_root=project,
            base_romfs_root=args.base_romfs,
            update_romfs_root=args.update_romfs,
            seed=args.seed,
            output_name=args.output_name,
            include_special_donors=args.include_special_donors,
            include_nonwild_instances=args.include_nonwild_instances,
            donor_family_codes=(
                frozenset(FAMILY_NAME_TO_CODE[name] for name in args.family)
                if args.family else None
            ),
            donor_rank_codes=(
                frozenset(RANK_NAME_TO_CODE[name] for name in args.rank)
                if args.rank else None
            ),
        )
        print(result["output_dir"])
        print(f"ZIP: {result['zip_path']}")
        manifest = result["manifest"]
        count = manifest["scope"]["changed_monp_instance_count"]
        print(f"Record MONP modificati: {count}; file modificati: {len(manifest['modified_files'])}")
        return 0
    except (GlobalBuildError, OSError, ValueError) as exc:
        print(f"Errore: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
