"""Traçabilité des séries : contrôle de cohérence, pas certification de la source."""
import hashlib
import json
from datetime import datetime
from pathlib import Path

from outils.donnees import lire_duel


def empreinte(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def auditer_source(csv_path, manifest_path=None):
    months, _, clipped = lire_duel(csv_path)
    result = dict(sha256=empreinte(csv_path), debut=months[0], fin=months[-1],
                  mois=len(months), parts_bornees=clipped, exploitable_clients=False,
                  problemes=[], manifeste=None)
    problems = result['problemes']
    if manifest_path is None:
        problems.append('manifeste de provenance absent')
        return result
    manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8-sig'))
    if not isinstance(manifest, dict):
        raise ValueError('Le manifeste doit être un objet JSON')
    result['manifeste'] = manifest
    required = ('source', 'extraction_utc', 'territoire', 'definition_mesure',
                'normalisation', 'acteur_J', 'acteur_m', 'traitement_ruptures')
    for key in required:
        if not isinstance(manifest.get(key), str) or not manifest[key].strip():
            problems.append('provenance manquante : ' + key)
    try:
        extracted = datetime.fromisoformat(manifest.get('extraction_utc', '').replace('Z', '+00:00'))
        if extracted.utcoffset() is None or extracted.utcoffset().total_seconds() != 0:
            raise ValueError('UTC requis')
    except (ValueError, TypeError, AttributeError):
        problems.append("date d'extraction UTC invalide")
    if manifest.get('sha256') != result['sha256']:
        problems.append('empreinte du CSV différente du manifeste')
    for key in ('debut', 'fin'):
        if manifest.get(key) != result[key]:
            problems.append('période incompatible : ' + key)
    if manifest.get('statut') != 'observe':
        problems.append('données non déclarées observées (estimation, simulation ou origine inconnue)')
    if manifest.get('mesure') != 'clients':
        problems.append('la source ne mesure pas directement les clients')
    if manifest.get('perimetres_comparables') is not True:
        problems.append('comparabilité des acteurs non documentée')
    if clipped:
        problems.append('parts nulles ou extrêmes bornées : sensibilité non validée')
    result['exploitable_clients'] = not problems
    return result
