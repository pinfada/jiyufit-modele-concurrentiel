#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Outil de pilotage JiyuFit — suivi de trajectoire concurrentielle par ville.

Lit une série mensuelle au format du protocole (Section XXVI, option 1) :

    mois,acteur_J,acteur_m
    2027-01,340,910
    ...

où `acteur_J` est la mesure mensuelle de JiyuFit (idéalement : clients captés ;
à défaut : proxy d'attention) et `acteur_m` celle du rival désigné de la ville.

Produit un diagnostic fondé sur le modèle validé (Sections XXVII-XXIX du
notebook) : position sur la trajectoire, plateau prédit avec incertitude,
temps restant jusqu'au plateau, verdicts de gates (G1 lancement, G2 ouverture
de la ville suivante), et alerte de dérive de la sensibilité r.

Usage :
    python outils/suivi_ville.py data/ville_XXX.csv [--r-secteur 0.926]
        [--gate2-tolerance 0.05] [--png rapport.png]

Le r sectoriel par défaut (0.926) est l'estimation poolée IV sur 282 mois de
trois duels réels (Section XXIX). Le réestimer quand JiyuFit aura ses propres
données longues.
"""
import argparse
import csv
import sys

import numpy as np

R_SECTEUR_DEFAUT = 0.926          # Section XXIX : IV poolé, 3 duels, 282 mois
R_BANDE = (0.85, 0.98)            # bande d'incertitude propagée sur le plateau
MIN_MOIS_DIAG = 8                 # en deçà : collecte seulement, pas de diagnostic
MIN_MOIS_R_LOCAL = 30             # en deçà : r local non estimable, on garde le sectoriel


def charger(path):
    with open(path, newline='', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
    if not rows:
        sys.exit(f"ERREUR : {path} est vide")
    for col in ('mois', 'acteur_J', 'acteur_m'):
        if col not in rows[0]:
            sys.exit(f"ERREUR : colonne '{col}' absente (attendu : mois,acteur_J,acteur_m)")
    mois = [r['mois'] for r in rows]
    vJ = np.array([float(r['acteur_J']) for r in rows])
    vm = np.array([float(r['acteur_m']) for r in rows])
    if np.any(vJ < 0) or np.any(vm < 0) or np.any(vJ + vm <= 0):
        sys.exit("ERREUR : valeurs négatives ou mois sans aucune activité")
    # part de capture, bornée pour garder le logit fini sur les mois à zéro
    s = np.clip(vJ / (vJ + vm), 1e-4, 1 - 1e-4)
    return mois, s


def diagnostiquer(s, r_secteur):
    """Estime ln(c) à r sectoriel connu : L(t+1) = ln(c) + r L(t) + eps.
    Renvoie le plateau prédit (avec bande d'incertitude statistique ET de
    modèle via la bande sur r), la trajectoire prédite et son écart aux
    observations récentes."""
    L = np.log(s / (1 - s))
    eps = L[1:] - r_secteur * L[:-1]
    ln_c = float(eps.mean())
    se_lnc = float(eps.std(ddof=1) / np.sqrt(len(eps))) if len(eps) > 1 else float('inf')

    def plateau(lc, r):
        return 1.0 / (1.0 + np.exp(-lc / (1.0 - r)))

    s_star = plateau(ln_c, r_secteur)
    # bande : incertitude statistique sur ln(c) x bande de modèle sur r
    coins = [plateau(ln_c + k * 1.96 * se_lnc, r)
             for k in (-1, 1) for r in (R_BANDE[0], r_secteur, R_BANDE[1])]
    s_lo, s_hi = min(coins), max(coins)

    # trajectoire prédite depuis le 1er mois, et position actuelle vs prédite
    pred = [s[0]]
    cur = L[0]
    for _ in range(len(s) - 1):
        cur = ln_c + r_secteur * cur
        pred.append(1.0 / (1.0 + np.exp(-cur)))
    pred = np.array(pred)
    ecart_recent = float(np.mean(s[-3:] - pred[-3:])) if len(s) >= 3 else float('nan')

    # temps restant : l'écart de logit au point fixe décroît au rythme r par
    # mois ; nombre de mois pour le ramener sous 0.1 (part à ~2 pts du plateau)
    L_star = ln_c / (1.0 - r_secteur)
    gap = abs(L[-1] - L_star)
    mois_restants = (0 if gap <= 0.1
                     else int(np.ceil(np.log(0.1 / gap) / np.log(r_secteur))))
    return dict(ln_c=ln_c, se_lnc=se_lnc, s_star=s_star, s_lo=s_lo, s_hi=s_hi,
                pred=pred, ecart_recent=ecart_recent, L=L, L_star=L_star,
                mois_restants=mois_restants)


def alerte_r(s):
    """Dérive de sensibilité : r local (OLS, plancher) et IV si série assez
    longue. r IV localement >= 1 = signal d'entrée en zone instable."""
    if len(s) < MIN_MOIS_R_LOCAL:
        return None
    L = np.log(s / (1 - s))
    y, X = L[1:], L[:-1]
    xb = np.column_stack([np.ones(len(y)), X])
    beta, *_ = np.linalg.lstsq(xb, y, rcond=None)
    num = np.cov(L[2:], L[:-2])[0, 1]
    den = np.cov(L[1:-1], L[:-2])[0, 1]
    r_iv = num / den if abs(den) > 1e-12 else float('nan')
    return dict(r_ols=float(beta[1]), r_iv=float(r_iv))


def verdict_gates(s, d, tol_g2):
    """G1 (traction) : la part monte et le plateau prédit dépasse nettement le
    point de départ. G2 (ouvrir la ville suivante) : la part est à moins de
    tol_g2 du plateau prédit OU la trajectoire observée colle à la prédiction."""
    g1 = bool(s[-1] > s[0] and d['s_star'] > s[0] + 0.05)
    proche_plateau = bool(abs(s[-1] - d['s_star']) <= tol_g2)
    sur_trajectoire = bool(abs(d['ecart_recent']) <= tol_g2)
    g2 = bool(proche_plateau or (sur_trajectoire and d['mois_restants'] <= 6))
    return g1, g2, proche_plateau, sur_trajectoire


def main():
    ap = argparse.ArgumentParser(description="Suivi de trajectoire concurrentielle par ville")
    ap.add_argument('csv', help="série mensuelle : mois,acteur_J,acteur_m")
    ap.add_argument('--r-secteur', type=float, default=R_SECTEUR_DEFAUT)
    ap.add_argument('--gate2-tolerance', type=float, default=0.05,
                    help="écart de part toléré pour valider la gate G2 (défaut 0.05)")
    ap.add_argument('--png', default=None, help="chemin du graphique de sortie (optionnel)")
    args = ap.parse_args()

    mois, s = charger(args.csv)
    T = len(s)
    print(f"=== Suivi de ville : {args.csv} ===")
    print(f"{T} mois ({mois[0]} -> {mois[-1]}) | part actuelle : {s[-1]:.1%} "
          f"(moyenne 3 mois : {s[-3:].mean():.1%})")

    if T < MIN_MOIS_DIAG:
        print(f"\n[COLLECTE] Moins de {MIN_MOIS_DIAG} mois de données : diagnostic "
              f"différé, continuer la collecte.")
        return

    d = diagnostiquer(s, args.r_secteur)
    print(f"\n--- Diagnostic (r sectoriel = {args.r_secteur:.3f}, Section XXIX) ---")
    print(f"asymétrie estimée ln(c) = {d['ln_c']:+.3f} (± {1.96*d['se_lnc']:.3f})")
    print(f"PLATEAU PRÉDIT : {d['s_star']:.1%}   [bande : {d['s_lo']:.1%} – {d['s_hi']:.1%}]")
    print(f"écart récent observé - prédit (3 mois) : {d['ecart_recent']:+.3f}")
    print(f"temps estimé jusqu'au plateau (90% du chemin) : ~{d['mois_restants']} mois")

    g1, g2, proche, sur_traj = verdict_gates(s, d, args.gate2_tolerance)
    print("\n--- Gates ---")
    print(f"G1 traction   ({'VERTE' if g1 else 'ROUGE'}) : part en hausse et plateau "
          f"prédit au-dessus du point de départ")
    print(f"G2 expansion  ({'VERTE' if g2 else 'ROUGE'}) : "
          f"{'au plateau' if proche else 'pas encore au plateau'}, "
          f"{'sur' if sur_traj else 'hors'} trajectoire prédite"
          + ("" if g2 else " -> NE PAS ouvrir la ville suivante"))
    if d['s_star'] < 0.5:
        print("ATTENTION : plateau prédit sous la parité — l'asymétrie c est "
              "défavorable ; renforcer la densité/différenciation AVANT d'étendre "
              "(répliquer maintenant répliquerait le déficit).")

    al = alerte_r(s)
    print("\n--- Surveillance de la sensibilité r ---")
    if al is None:
        print(f"série < {MIN_MOIS_R_LOCAL} mois : r local non estimable, "
              f"sectoriel conservé (à réévaluer plus tard)")
    else:
        etat = 'ALERTE : zone instable possible' if al['r_iv'] >= 1.0 else 'ok (r < 1)'
        print(f"r local OLS (plancher) = {al['r_ols']:.3f} | r local IV = {al['r_iv']:.3f} -> {etat}")

    if args.png:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(9, 4.5))
        x = np.arange(T)
        ax.plot(x, s, 'ko-', ms=3, lw=1, label='part observée')
        ax.plot(x, d['pred'], '-', color='#2b8cbe', lw=2, label='trajectoire prédite (modèle)')
        ax.axhline(d['s_star'], color='#2b8cbe', ls=':', lw=1.2,
                   label=f"plateau prédit {d['s_star']:.1%}")
        ax.fill_between(x, d['s_lo'], d['s_hi'], color='#2b8cbe', alpha=0.10,
                        label='bande d\'incertitude du plateau')
        ax.axhline(0.5, color='k', lw=0.5)
        ticks = list(range(0, T, max(1, T // 10)))
        ax.set_xticks(ticks)
        ax.set_xticklabels([mois[i] for i in ticks], rotation=45, fontsize=8)
        ax.set_ylabel('part de capture JiyuFit')
        ax.set_title(f"Suivi de trajectoire — {args.csv}")
        ax.legend(fontsize=8, loc='best')
        plt.tight_layout()
        plt.savefig(args.png, dpi=130)
        print(f"\ngraphique écrit : {args.png}")


if __name__ == '__main__':
    main()
