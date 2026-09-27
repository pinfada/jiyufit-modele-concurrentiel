# Vérification Python du 27 septembre 2026

> **État historique avant corrections.** Ce rapport documente la première
> exécution. Les anomalies G1/G2 et bootstrap décrites plus bas ont ensuite
> été corrigées. Voir [le rapport après corrections](CORRECTIONS_ET_RESULTATS.md)
> et [les fondements scientifiques](FONDEMENTS_SCIENTIFIQUES.md).

## Environnement et exécution

Exécution locale sous Windows, Python 3.12.10, dans `.venv/` :

- NumPy 2.5.3, SciPy 1.18.1, Matplotlib 3.11.2 ;
- nbconvert 7.17.1, ipykernel 7.3.0 ;
- noyau `jiyufit-local`, installé dans l'environnement du projet ;
- `python -m pip check` : aucune incompatibilité déclarée.

Installation et commande reproductibles dans le README, rubrique
« Vérification locale sous Windows (PowerShell) ».

Le notebook source et les données n'ont pas été modifiés. SHA-256 du notebook :

```text
b1b9c0843c1876efa19287c2366b696fb2fd339858502cb9e285ddaa156a3e05
```

Résultat : **28 cellules Python exécutées dans l'ordre, compteurs 1 à 28,
aucune erreur et aucun échec d'assertion**. Le source contient 145 instructions
`assert` (certaines dans des fonctions ou boucles : ce n'est pas un nombre
de tests indépendants). Les tests actuariels T1–T13 passent également.
Huit sorties de figures PNG sont enregistrées. Les horodatages des cellules
indiquent environ 47 secondes de calcul, hors installation et démarrage.

Les résultats locaux, exclus de Git, sont disponibles dans :

- `artifacts/executed.ipynb` : notebook intégralement recalculé ;
- `artifacts/notebook-outputs.txt` : sorties textuelles ;
- `artifacts/notebook-execution.log` : journal d'exécution ;
- `artifacts/environment-freeze.txt` : versions exactes des dépendances.

## Résultats reproduits

| Mesure | Résultat recalculé |
|---|---|
| Basic-Fit / Fitness Park, AR(1) | r = 0,814 ; R² = 0,842 |
| Plateau de ce duel, section XXVII | 22,2 % ; moyenne observée finale 24,5 % |
| Backtest sans saisonnalité, section XXVII | Bat la persistance sur 1 fenêtre sur 3 |
| Estimation IV poolée, section XXIX | r = 0,926 |
| Backtest Gymlib / USC, section XXIX | RMSE 0,0293 contre 0,0650 pour la persistance |

Ces résultats confirment la reproductibilité numérique sur les données du
dépôt. Ils ne suffisent pas à établir la validité des hypothèses économiques,
la provenance des proxys ou la transférabilité à JiyuFit.

Un point supplémentaire mérite un audit statistique : pour r poolé = 0,926,
le bootstrap affiche une médiane de 0,782 et un intervalle percentile à 95 %
[0,584 ; 0,908]. L'estimation initiale est donc au-dessus de cet intervalle.
Ce décalage appelle une vérification de la procédure et de son biais avant
d'interpréter la fréquence bootstrap affichée comme une probabilité fiable
du régime du marché. Cette exécution ne constitue pas cet audit.

## Vérification ciblée des gates

Commande exécutée depuis la racine du dépôt :

```powershell
.\.venv\Scripts\python.exe -X utf8 -c "import numpy as np; from outils.suivi_ville import diagnostiquer, verdict_gates; s=np.full(12,0.1); d=diagnostiquer(s,0.926); print(d['s_star'], verdict_gates(s,d,0.05)[:2])"
```

Résultat : plateau = 0,10000000000000023 ; `(G1, G2) = (False, True)`.
Le cas signalé lors de la revue est donc reproduit : une part constante de
10 % sur douze mois donne une traction rouge et une expansion verte.

L'outil complet a aussi été exécuté sur
`data/basicfit_vs_fitnesspark_attention_mensuelle.csv`. Il termine sans erreur,
avec G1 et G2 vertes, un plateau de 29,2 % et un avertissement demandant de
renforcer la différenciation avant d'étendre. Le plateau diffère de celui du
notebook parce que l'outil fixe r au coefficient sectoriel de 0,926.

Les règles de décision n'ont pas été modifiées dans cette intervention :
leur incohérence est documentée, et reste à corriger séparément.
