"""Lecture commune des duels : dates régulières, valeurs finies et parts explicites."""
import csv
import re
import numpy as np


def valider_mois(months):
    if not months:
        raise ValueError("Aucun mois")
    ordinals = []
    for value in months:
        if not re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', value):
            raise ValueError(f"Mois invalide : {value!r} (AAAA-MM attendu)")
        year, month = map(int, value.split('-'))
        if year < 1:
            raise ValueError("Année invalide")
        ordinals.append(year*12 + month)
    if any(b-a != 1 for a, b in zip(ordinals, ordinals[1:])):
        raise ValueError("Les mois doivent être triés, uniques et consécutifs, sans trou")


def lire_duel(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames and len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ValueError('En-têtes CSV en double')
        if not {'mois', 'acteur_J', 'acteur_m'}.issubset(reader.fieldnames or []):
            raise ValueError("Colonnes requises : mois,acteur_J,acteur_m")
        rows = list(reader)
    if any(None in row or any(row.get(k) is None for k in ('mois', 'acteur_J', 'acteur_m')) for row in rows):
        raise ValueError('Ligne CSV tronquée ou contenant trop de colonnes')
    months = [r['mois'] for r in rows]
    valider_mois(months)
    try:
        values = np.array([[float(r['acteur_J']), float(r['acteur_m'])] for r in rows])
    except (ValueError, TypeError) as exc:
        raise ValueError("Mesures non numériques ou absentes") from exc
    if not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValueError("Les mesures doivent être finies et non négatives")
    # Éviter l'overflow de J+m pour de grandes valeurs finies.
    maximum = values.max(axis=1)
    if np.any(maximum <= 0):
        raise ValueError("Un mois sans aucune activité ne définit pas de part")
    scaled = values / maximum[:, None]
    raw = scaled[:, 0] / scaled.sum(axis=1)
    clipped = int(np.sum((raw < 1e-4) | (raw > 1-1e-4)))
    return months, np.clip(raw, 1e-4, 1-1e-4), clipped
