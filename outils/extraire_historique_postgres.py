"""Extraire des agrégats JiyuFit en lecture seule, sans les qualifier de revenus réels."""
import argparse
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

SQL_PATH = Path(__file__).parent/'sql'/'historique_jiyufit.sql'


def trouver_psql():
    found = shutil.which('psql')
    if found:
        return found
    root = Path(os.environ.get('ProgramFiles', 'C:/Program Files'))/'PostgreSQL'
    candidates = sorted(root.glob('*/bin/psql.exe'), reverse=True) if root.exists() else []
    return str(candidates[0]) if candidates else None


def extraire(host, port, database, psql=None):
    executable = psql or trouver_psql()
    if not executable:
        raise ValueError('Client psql introuvable ; préciser --psql')
    sql = SQL_PATH.read_text(encoding='utf-8')
    env = os.environ.copy()
    if 'PGPASSWORD' not in env and 'DATABASE_PASSWORD' in env:
        env['PGPASSWORD'] = env['DATABASE_PASSWORD']
    env['PGCONNECT_TIMEOUT'] = '5'
    env['PGOPTIONS'] = '-c default_transaction_read_only=on -c statement_timeout=30000'
    user = env.get('PGUSER') or env.get('DATABASE_USER') or 'postgres'
    command = [executable, '-X', '-w', '-q', '-A', '-t', '-v', 'ON_ERROR_STOP=1',
               '-h', host, '-p', str(port), '-U', user, '-d', database]
    try:
        result = subprocess.run(command, input=sql, env=env, capture_output=True,
                                text=True, encoding='utf-8', timeout=45)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError('Connexion/extraction impossible ou délai dépassé') from exc
    if result.returncode:
        # Ne pas propager des messages pouvant inclure des paramètres de connexion.
        raise ValueError('Extraction refusée ou schéma incompatible ; vérifier connexion et schéma JiyuFit')
    payload = json.loads(result.stdout)
    if payload.get('lecture_seule') != 'on':
        raise ValueError('Lecture seule non confirmée')
    return dict(version=1, source=dict(host=host, port=port, database=database),
                statut='origine_reelle_non_etablie',
                extraction_utc=datetime.now(timezone.utc).isoformat(),
                sql_sha256=hashlib.sha256(sql.encode('utf-8')).hexdigest(),
                avertissements=[
                    'Le statut applicatif ne certifie pas une transaction réelle chez le prestataire.',
                    'Les mois sont ceux de création des paiements, pas un calendrier comptable validé.',
                    'Les commissions et paiements ne doivent pas être additionnés.',
                    'Les frais de service ne sont pas automatiquement un revenu plateforme rapproché.',
                    'Aucun coût absent ni mois sans ligne ne peut être supposé nul.'
                ], donnees=payload)


def enregistrer(report, folder):
    folder = Path(folder)
    # Un nouvel instantané ne doit jamais écraser un instantané existant.
    folder.mkdir(parents=True, exist_ok=False)
    content = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n'
    (folder/'extraction.json').write_text(content, encoding='utf-8')
    rows = report['donnees']['paiements_par_mois_creation']
    columns = ['mois', 'statut_application', 'devise', 'mouvements', 'total_centimes',
               'frais_service_centimes', 'totaux_absents', 'frais_service_absents',
               'frais_traitement_absents', 'confirmations_absentes']
    buffer = io.StringIO(newline='')
    writer = csv.DictWriter(buffer, fieldnames=columns)
    writer.writeheader(); writer.writerows(rows)
    (folder/'paiements-mensuels-non-qualifies.csv').write_text(buffer.getvalue(), encoding='utf-8', newline='')
    hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file()}
    (folder/'empreintes.json').write_text(json.dumps(hashes, indent=2)+'\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--host', required=True)
    parser.add_argument('--port', type=int, default=5432)
    parser.add_argument('--database', required=True)
    parser.add_argument('--psql')
    parser.add_argument('--sortie', type=Path, required=True, help='nouveau dossier pour cet instantané')
    args = parser.parse_args()
    try:
        if args.sortie.exists():
            raise ValueError('Choisir un nouveau dossier de sortie pour préserver les instantanés')
        report = extraire(args.host, args.port, args.database, args.psql)
        enregistrer(report, args.sortie)
    except (ValueError, OSError, TypeError) as exc:
        parser.error(str(exc))
    counters = report['donnees']['compteurs']
    print(f"Extraction sauvegardée : {args.sortie} ; {counters['paiements']} paiements, "
          f"{counters['commissions']} commissions. Origine réelle non certifiée.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
