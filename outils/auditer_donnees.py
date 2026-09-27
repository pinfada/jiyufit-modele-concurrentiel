"""Auditer la traçabilité des CSV ; code 1 si une source n'étaye pas une décision clients."""
import argparse
import json
from pathlib import Path
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from outils.qualite import auditer_source


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', nargs='+', type=Path)
    parser.add_argument('--sortie', type=Path, required=True)
    args = parser.parse_args()
    reports = []
    try:
        inputs = {p.resolve() for p in args.csv}
        inputs.update(p.with_suffix('.source.json').resolve() for p in args.csv)
        if args.sortie.resolve() in inputs:
            raise ValueError('La sortie ne peut pas écraser une entrée ou son manifeste')
        for path in args.csv:
            manifest = path.with_suffix('.source.json')
            try:
                report = auditer_source(path, manifest if manifest.exists() else None)
            except (OSError, ValueError, TypeError) as exc:
                report = dict(exploitable_clients=False, problemes=[str(exc)])
            reports.append(dict(fichier=str(path), **report))
        args.sortie.parent.mkdir(parents=True, exist_ok=True)
        args.sortie.write_text(json.dumps(dict(version=1, sources=reports), ensure_ascii=False,
                                         indent=2, allow_nan=False)+'\n', encoding='utf-8')
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    failures = sum(not r['exploitable_clients'] for r in reports)
    print(f'{len(reports)} sources ; {failures} non validées pour une décision clients. Rapport : {args.sortie}')
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
