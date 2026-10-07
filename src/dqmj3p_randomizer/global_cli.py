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
        description="Crea un randomizer da cartelle RomFS base e update già estratte.",
    )
    parser.add_argument("--seed", required=True, type=int, help="Seed riproducibile unsigned a 64 bit")
    parser.add_argument("--base-romfs", required=True, type=Path, help="Cartella RomFS già estratta del gioco base")
    parser.add_argument("--update-romfs", required=True, type=Path, help="Cartella RomFS già estratta dell'update 1.3")
    parser.add_argument("--output-name", help="Nome nuova cartella dentro randomizer/output")
    parser.add_argument("--include-special-donors", action="store_true", help="Aggiunge alla pool donatori le specie speciali supportate")
    parser.add_argument("--include-nonwild-instances", action="store_true", help="Estende le modifiche a tutte le istanze MONP, incluse quelle fuori dalle definizioni SMOT")
    parser.add_argument(
        "--family", action="append", choices=sorted(FAMILY_NAME_TO_CODE), metavar="FAMILY",
        help="Limita il pool dei sostituti a questa famiglia; ripeti l'opzione per più famiglie.",
    )
    parser.add_argument(
        "--rank", action="append", choices=sorted(RANK_NAME_TO_CODE), metavar="RANK",
        help="Limita il pool dei sostituti a questo grado (f/e/d/c/b/a/s/ss); ripeti l'opzione.",
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
        print(f"Record randomizzati: {count}; file modificati: {len(manifest['modified_files'])}")
        return 0
    except (GlobalBuildError, OSError, ValueError) as exc:
        print(f"Errore: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
