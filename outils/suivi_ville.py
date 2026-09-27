#!/usr/bin/env python3
"""Suivi conditionnel ; phi (persistance) n'identifie pas le r de Tullock.

L'expansion exige une traction suffisante, une calibration locale et des
preuves métier. Documentation : docs/STRATEGIE_EXPANSION_MESURE.md.
"""
import argparse
import json
from pathlib import Path
import sys
import numpy as np
from scipy.special import expit, logit

if __package__ in (None, ''):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from outils.donnees import lire_duel
from outils.inference import iv_diagnostic, moyenne_hac, ols_hac, serie_finie
from outils.qualite import auditer_source
from outils.historique_comptable import construire_historique

PHI_SCENARIO_DEFAUT = 0.926  # Arrondi historique descriptif, pas une constante.
R_SECTEUR_DEFAUT = PHI_SCENARIO_DEFAUT  # Ancien nom conservé pour compatibilité.
MIN_MOIS_DIAG = 8
MIN_MOIS_R_LOCAL = 30


def charger(path):
    months, shares, clipped = lire_duel(path)
    if clipped:
        print(f'ATTENTION : {clipped} parts bornées pour le logit ; sensibilité aux zéros.', file=sys.stderr)
    return months, shares


def diagnostiquer(s, r_secteur=PHI_SCENARIO_DEFAUT, phi_interval=None):
    """Scénario AR(1) ; intercept réestimé à chaque phi de l'enveloppe.

    Bande HAC asymptotique à phi fixé ; enveloppe de sensibilité si un
    intervalle local est fourni, pas un IC joint. Si l'intervalle rencontre
    phi >= 1, aucun plateau stationnaire robuste n'est annoncé.
    """
    s = serie_finie(s, MIN_MOIS_DIAG)
    if np.any((s <= 0) | (s >= 1)):
        raise ValueError('Les parts doivent être strictement entre 0 et 1')
    phi = float(r_secteur)
    if not np.isfinite(phi) or not 0 < phi < 1:
        raise ValueError('Le scénario de convergence exige 0 < phi < 1')
    if phi_interval is not None:
        lo, hi = map(float, phi_interval)
        if not np.isfinite([lo, hi]).all() or lo > hi or not lo <= phi <= hi:
            raise ValueError('Intervalle de phi fini, ordonné et contenant le scénario requis')
        phi_interval = (lo, hi)
    L = logit(s)
    intercept, se = moyenne_hac(L[1:] - phi*L[:-1])
    equilibrium = intercept/(1-phi)
    stationary = phi_interval is not None and 0 < phi_interval[0] <= phi_interval[1] < 1
    grid = np.linspace(*phi_interval, 101) if stationary else [phi]
    bounds = []
    for candidate in grid:
        a, error = moyenne_hac(L[1:] - candidate*L[:-1])
        bounds.extend(expit((a + np.array([-1, 1])*1.96*error)/(1-candidate)))
    current, pred = L[0], [s[0]]
    for _ in range(len(s)-1):
        current = intercept + phi*current
        pred.append(expit(current))
    pred = np.asarray(pred)
    gap = abs(L[-1]-equilibrium)
    remaining = 0 if gap <= .1 else int(np.ceil(np.log(.1/gap)/np.log(phi)))
    return dict(ln_c=intercept, se_lnc=se, s_star=float(expit(equilibrium)),
                s_lo=float(min(bounds)), s_hi=float(max(bounds)), phi=phi,
                phi_interval=phi_interval, plateau_identifiable=stationary,
                pred=pred, ecart_recent=float(np.mean(s[-3:]-pred[-3:])),
                L=L, L_star=equilibrium, mois_restants=remaining)


def alerte_r(s):
    """Ancien nom : diagnostic de phi, PAS du r structurel."""
    if len(s) < MIN_MOIS_R_LOCAL:
        return None
    L = logit(s)
    diagnostic = iv_diagnostic(L)
    try:
        beta, _, _ = ols_hac(L[1:], np.column_stack((np.ones(len(L)-1), L[:-1])))
        phi_ols = float(beta[1])
    except ValueError:
        phi_ols = float('nan')
    return dict(diagnostic, phi_ols=phi_ols)


def valider_metier(metier):
    if not isinstance(metier, dict):
        raise ValueError('Les critères métier doivent être un objet JSON')
    keys = {'mesure', 'marge_contributive_mensuelle', 'retention_validee',
            'capacite_validee', 'budget_expansion_valide', 'calibration_locale_validee'}
    if set(metier)-keys:
        raise ValueError(f'Critères inconnus : {sorted(set(metier)-keys)}')
    if 'mesure' in metier and metier['mesure'] not in ('clients', 'attention'):
        raise ValueError('mesure doit valoir clients ou attention')
    for key in keys-{'mesure', 'marge_contributive_mensuelle'}:
        if key in metier and type(metier[key]) is not bool:
            raise ValueError(f'{key} doit être un booléen JSON')
    if 'marge_contributive_mensuelle' in metier:
        margin = metier['marge_contributive_mensuelle']
        if type(margin) not in (int, float) or not np.isfinite(margin):
            raise ValueError('La marge contributive doit être un nombre fini')
    return metier


def evaluer_gates(s, d, tol_g2=.05, part_cible=.5, metier=None, *, source=None, comptabilite=None):
    """G2 : rouge si échec, indéterminée si preuve manquante/incertaine.

    La cible de 50 % est un choix configurable, pas un seuil scientifique.
    """
    if not np.isfinite(tol_g2) or not 0 < tol_g2 < 1:
        raise ValueError('La tolérance doit être entre 0 et 1')
    if not np.isfinite(part_cible) or not 0 < part_cible < 1:
        raise ValueError('La part cible doit être entre 0 et 1')
    s = serie_finie(s, MIN_MOIS_DIAG)
    metier = valider_metier({} if metier is None else metier)
    initial, recent = float(np.mean(s[:3])), float(np.mean(s[-3:]))
    g1 = bool(recent > initial and d['s_star'] > initial+.05)
    near = bool(abs(recent-d['s_star']) <= tol_g2)
    on_track = bool(abs(d['ecart_recent']) <= tol_g2)
    failed, missing = [], []
    if not source or not source.get('exploitable_clients'):
        missing.append('provenance clients non établie pour le CSV exact')
    if source and source.get('exploitable_clients'):
        territory = source['manifeste']['territoire']
        end = source['fin']
        year, month = map(int, end.split('-'))
        last = year*12+month-1
        expected = [f'{i//12:04d}-{i%12+1:02d}' for i in range(last-2, last+1)]
        rows = {r['mois']: r for r in (comptabilite or {}).get('historique', [])
                if r['territoire'] == territory}
        for period in expected:
            row = rows.get(period)
            if not row or not row['rapproche']:
                missing.append('historique financier non rapproché : ' + period)
            elif row['marge_apres_acquisition_centimes'] <= 0:
                failed.append('marge après acquisition non positive : ' + period)
        current = rows.get(end)
        if current and current['rapproche']:
            declared = metier.get('marge_contributive_mensuelle')
            if declared is not None and not np.isclose(
                    declared, current['marge_apres_acquisition_centimes']/100,
                    rtol=0, atol=.005):
                failed.append('marge déclarée incohérente avec le journal rapproché')
    else:
        missing.append('historique financier non rattaché à un territoire et une période vérifiés')
    if not g1:
        failed.append('traction G1 insuffisante')
    if d['s_star'] < part_cible:
        failed.append('plateau du scénario inférieur à la cible choisie')
    if not (on_track and (near or d['mois_restants'] <= 6)):
        failed.append('trajectoire ou convergence insuffisante')
    if not d['plateau_identifiable']:
        missing.append('intervalle local stationnaire de phi absent ou non concluant')
    elif d['s_lo'] < part_cible:
        missing.append('incertitude sur le plateau : borne basse sous la cible')
    if metier.get('mesure') != 'clients':
        missing.append('mesure directe des clients nécessaire ; attention seule insuffisante')
    checks = {'retention_validee': 'rétention', 'capacite_validee': 'capacité opérationnelle',
              'budget_expansion_valide': "budget d'expansion",
              'calibration_locale_validee': 'calibration locale et qualité des données'}
    for key, label in checks.items():
        if key not in metier:
            missing.append('information manquante : ' + label)
        elif not metier[key]:
            failed.append(label + ' non validée')
    margin = metier.get('marge_contributive_mensuelle')
    if margin is None:
        missing.append('marge contributive mensuelle manquante')
    elif margin <= 0:
        failed.append('marge contributive mensuelle non positive')
    g2 = False if failed else (None if missing else True)
    return dict(g1=g1, g2=g2, proche_plateau=near, sur_trajectoire=on_track,
                echecs=failed, manquants=missing)


def verdict_gates(s, d, tol_g2, *, part_cible=.5, metier=None, source=None, comptabilite=None):
    v = evaluer_gates(s, d, tol_g2, part_cible, metier, source=source, comptabilite=comptabilite)
    return tuple(v[k] for k in ('g1', 'g2', 'proche_plateau', 'sur_trajectoire'))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('csv', help='série mensuelle : mois,acteur_J,acteur_m')
    parser.add_argument('--phi-scenario', '--r-secteur', dest='phi', type=float,
                        default=PHI_SCENARIO_DEFAUT, help='persistance conditionnelle, 0 < phi < 1')
    parser.add_argument('--phi-interval', nargs=2, type=float, metavar=('MIN', 'MAX'),
                        help='intervalle issu de la calibration locale, à documenter')
    parser.add_argument('--gate2-tolerance', type=float, default=.05)
    parser.add_argument('--part-cible', type=float, default=.5, help='cible de gouvernance')
    parser.add_argument('--criteres-metier', type=Path, help='preuves métier JSON documentées')
    parser.add_argument('--source', type=Path, help='manifeste de provenance du CSV, avec empreinte SHA-256')
    parser.add_argument('--journal', type=Path, help='mouvements financiers de gestion en centimes EUR')
    parser.add_argument('--couverture', type=Path, help='périodes et totaux de contrôle du journal')
    parser.add_argument('--png', type=Path)
    args = parser.parse_args()
    try:
        if not 0 < args.phi < 1 or not 0 < args.gate2_tolerance < 1 or not 0 < args.part_cible < 1:
            raise ValueError('phi, tolérance et cible doivent être strictement entre 0 et 1')
        months, s = charger(args.csv)
        source = auditer_source(args.csv, args.source)
        if bool(args.journal) != bool(args.couverture):
            raise ValueError('--journal et --couverture doivent être fournis ensemble')
        comptabilite = construire_historique(args.journal, args.couverture) if args.journal else None
        metier = json.loads(args.criteres_metier.read_text(encoding='utf-8-sig')) if args.criteres_metier else {}
        valider_metier(metier)
        print(f'=== Suivi conditionnel : {args.csv} ===')
        print(f'{len(s)} mois ({months[0]} → {months[-1]}) | part récente : {s[-3:].mean():.1%}')
        if len(s) < MIN_MOIS_DIAG:
            print(f'[COLLECTE] Au moins {MIN_MOIS_DIAG} mois requis ; G1/G2 non évaluées.')
            return
        d = diagnostiquer(s, args.phi, args.phi_interval)
        v = evaluer_gates(s, d, args.gate2_tolerance, args.part_cible, metier,
                         source=source, comptabilite=comptabilite)
    except (OSError, ValueError, TypeError) as exc:
        parser.error(str(exc))
    print(f'Scénario phi = {args.phi:.3f} ; ne mesure pas la sensibilité concurrentielle r.')
    print('Provenance : ' + ('cohérente avec une mesure clients déclarée' if source['exploitable_clients'] else 'non validée pour une décision clients'))
    for problem in source['problemes']:
        print('  - ' + problem)
    print(f"Intercept = {d['ln_c']:+.3f} (± {1.96*d['se_lnc']:.3f}, HAC approximatif)")
    print(f"PLATEAU CONDITIONNEL : {d['s_star']:.1%}")
    label = 'enveloppe de sensibilité, pas IC joint' if d['plateau_identifiable'] else 'bande à phi fixé seulement'
    print(f"[{d['s_lo']:.1%} ; {d['s_hi']:.1%}] — {label}")
    print(f"Temps du scénario jusqu'à un écart de logit ≤ 0,1 : {d['mois_restants']} mois")
    print(f"G1 traction : {'VERTE' if v['g1'] else 'ROUGE'}")
    state = 'INDÉTERMINÉE' if v['g2'] is None else ('VERTE' if v['g2'] else 'ROUGE')
    print(f'G2 expansion : {state} (cible choisie : {args.part_cible:.0%})')
    for reason in v['echecs'] + v['manquants']:
        print('  - ' + reason)
    local = alerte_r(s)
    if local is None:
        print(f'Phi local : série < {MIN_MOIS_R_LOCAL} mois, diagnostic IV différé.')
    else:
        print(f"Phi OLS = {local['phi_ols']:.3f} ; IV lag2 = {local['phi_iv']:.3f}")
        intervals = ' ∪ '.join(f'[{lo:.3f} ; {hi:.3f}]' for lo, hi in local['confidence_set']) or 'vide'
        print(f'Ensemble Anderson–Rubin/HAC (asymptotique) : {intervals}')
        print(f"Première étape F HAC = {local['first_stage_f']:.2f} (diagnostic, pas certification)")
        print('Proximité de 1, instrument faible ou proxy bruité : audit local requis.')
    if args.png:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(9, 4.5))
        x = np.arange(len(s))
        ax.plot(x, s, 'ko-', ms=3, label='part observée dans le duel')
        ax.plot(x, d['pred'], color='#2b8cbe', label='scénario conditionnel')
        ax.axhline(d['s_star'], color='#2b8cbe', ls=':', label='plateau du scénario')
        ax.fill_between(x, d['s_lo'], d['s_hi'], alpha=.12, label=label)
        ax.axhline(args.part_cible, color='k', lw=.6, label='cible choisie')
        ticks = list(range(0, len(s), max(1, len(s)//10)))
        ax.set_xticks(ticks, [months[i] for i in ticks], rotation=45, fontsize=8)
        ax.set_ylabel('part dans le duel (clients ou attention selon la source)')
        ax.set_title('Trajectoire conditionnelle — hypothèses à valider localement')
        ax.legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(args.png, dpi=130)
        plt.close(fig)
        print(f'Graphique écrit : {args.png}')


if __name__ == '__main__':
    main()
