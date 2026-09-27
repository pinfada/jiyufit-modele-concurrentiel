"""Construire un historique financier de gestion rapproché, en centimes EUR.

Le journal contient des mouvements catégorisés, pas un grand livre légal.
Une couverture explicite et un total de contrôle sont requis pour chaque
mois/territoire/catégorie, même lorsqu'aucun mouvement n'a eu lieu.
"""
import argparse
import csv
from datetime import date
import json
from pathlib import Path
import re
import sys

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from outils.donnees import valider_mois
from outils.qualite import empreinte

CATEGORIES = ('revenu_plateforme', 'remboursement_plateforme',
              'cout_variable', 'acquisition')


def lire_csv(path, columns):
    with open(path, encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames and len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError('En-têtes CSV en double')
        if not set(columns).issubset(reader.fieldnames or []):
            raise ValueError('Colonnes requises : ' + ','.join(columns))
        rows = list(reader)
    if any(None in row or any(row.get(k) is None for k in columns) for row in rows):
        raise ValueError('Ligne CSV tronquée ou contenant trop de colonnes')
    return rows


def centimes(value):
    if not re.fullmatch(r'0|[1-9][0-9]*', value):
        raise ValueError('Montant requis en centimes entiers positifs ou nuls : ' + repr(value))
    return int(value)


def construire_historique(journal_path, couverture_path):
    journal = lire_csv(journal_path, ('id', 'date', 'territoire', 'categorie',
                                     'montant_centimes', 'devise', 'reference'))
    coverage = lire_csv(couverture_path, ('mois', 'territoire', 'categorie',
                                        'statut', 'total_controle_centimes', 'reference'))
    if not coverage:
        raise ValueError('Couverture vide : aucune période ne peut être attestée')
    covered, totals, ids, territories, periods = {}, {}, set(), set(), set()
    for row in coverage:
        valider_mois([row['mois']])
        if (not row['territoire'].strip() or not row['reference'].strip()
                or row['categorie'] not in CATEGORIES
                or row['statut'] not in ('observe', 'estime', 'synthetique', 'manquant')):
            raise ValueError('Couverture invalide : territoire, catégorie, statut ou référence')
        key = (row['mois'], row['territoire'], row['categorie'])
        if key in covered:
            raise ValueError('Couverture en double : ' + str(key))
        covered[key] = (row['statut'], centimes(row['total_controle_centimes'])
                        if row['total_controle_centimes'] != '' else None)
        periods.add(row['mois']); territories.add(row['territoire'])
    for row in journal:
        if (not row['id'].strip() or row['id'] in ids):
            raise ValueError('Identifiant de mouvement absent ou en double : ' + row['id'])
        ids.add(row['id'])
        if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', row['date']):
            raise ValueError('Date de mouvement attendue au format AAAA-MM-JJ')
        date.fromisoformat(row['date'])
        if row['devise'] != 'EUR' or row['categorie'] not in CATEGORIES or not row['reference'].strip():
            raise ValueError('Mouvement invalide : devise EUR, catégorie et référence requis')
        key = (row['date'][:7], row['territoire'], row['categorie'])
        if key not in covered:
            raise ValueError('Mouvement hors couverture : ' + str(key))
        totals[key] = totals.get(key, 0) + centimes(row['montant_centimes'])
    first, last = sorted(periods)[0], sorted(periods)[-1]
    def ordinal(value):
        year, month = map(int, value.split('-'))
        return year * 12 + month - 1
    months = [f'{i//12:04d}-{i%12+1:02d}' for i in range(ordinal(first), ordinal(last)+1)]
    history = []
    for territory in sorted(territories):
        for month in months:
            problems, values = [], {}
            for category in CATEGORIES:
                key = (month, territory, category)
                status, control = covered.get(key, ('manquant', None))
                total = totals.get(key, 0)
                if status != 'observe':
                    problems.append(f'{category} : statut {status}')
                if control is None:
                    problems.append(f'{category} : total de contrôle absent')
                elif total != control:
                    problems.append(f'{category} : journal {total} != contrôle {control}')
                values[category] = total if status == 'observe' and total == control else None
            margin = (values['revenu_plateforme'] - sum(values[k] for k in CATEGORIES[1:])
                      if not problems else None)
            history.append(dict(mois=month, territoire=territory, montants_centimes=values,
                                marge_apres_acquisition_centimes=margin,
                                rapproche=not problems, problemes=problems))
    return dict(version=1, devise='EUR', journal_sha256=empreinte(journal_path),
                couverture_sha256=empreinte(couverture_path), mouvements=len(journal),
                historique=history, avertissement='Rapprochement déclaratif, pas audit des pièces ni certification comptable')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('journal', type=Path)
    parser.add_argument('couverture', type=Path)
    parser.add_argument('--sortie', type=Path, required=True)
    args = parser.parse_args()
    try:
        report = construire_historique(args.journal, args.couverture)
        if args.sortie.resolve() in (args.journal.resolve(), args.couverture.resolve()):
            raise ValueError('La sortie ne peut pas écraser une entrée')
        args.sortie.parent.mkdir(parents=True, exist_ok=True)
        args.sortie.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    except (ValueError, OSError, TypeError) as exc:
        parser.error(str(exc))
    failures = sum(not row['rapproche'] for row in report['historique'])
    print(f"{len(report['historique'])} périodes ; {failures} non rapprochées. Rapport : {args.sortie}")
    return 1 if failures else 0


if __name__ == '__main__':
    sys.exit(main())
