# Corrections et résultats — 27 septembre 2026

Le modèle et son dispositif de décision ont été révisés à partir de la revue
initiale et d'une recherche de publications scientifiques. Les
[références et limites](FONDEMENTS_SCIENTIFIQUES.md) distinguent résultats
publiés, adaptations d'implémentation et dérivations propres au dépôt.

## 1. Défauts corrigés

| Avant | Après |
|---|---|
| G2 pouvait être verte alors que G1 était rouge | G2 exige G1 ; le cas constant à 10 % donne désormais deux rouges |
| La proximité d'un plateau suffisait à autoriser l'expansion | Cible configurable, incertitude, marge, rétention, capacité, budget, mesures clients et calibration locale exigés |
| Des preuves manquantes n'empêchaient pas un feu vert | Statut indéterminé explicite et motifs affichés |
| Bande arbitraire de r traitée comme une incertitude sectorielle | Scénario phi distinct d'une plage locale documentée ; intercept réestimé à chaque phi |
| Erreur-type de moyenne supposant l'indépendance | Covariance HAC, avec limites asymptotiques explicites |
| Retards reconstruits sur blocs de niveaux recollés | Triplets temporels construits avant tirage des blocs |
| Dernier départ de bloc omis | Départ `n - longueur_bloc` inclus |
| Duels bootstrapés indépendamment malgré des dates communes | Blocs calendaires synchronisés et masques d'observation conservés |
| Fréquence bootstrap présentée comme probabilité de stabilité | Percentiles et fréquences exploratoires ; aucune probabilité de régime revendiquée |
| phi assimilé automatiquement au r de Tullock | Notations et interprétations séparées ; formule à accumulation finie vérifiée |
| Assertions imposant des conclusions empiriques favorables | Invariants techniques, résultats défavorables conservés et rapportés |
| Dates/NaN/inf insuffisamment contrôlés | Validation commune, chronologie mensuelle stricte, zéros signalés |

Le vocabulaire a aussi été aligné sur les équations : `s` désigne les
sportifs, `l` les lieux partenaires. Les anciens libellés court/long terme
étaient incohérents avec les sections I et III. Les paramètres numériques
du modèle biface n'ont pas été recalibrés artificiellement.

## 2. Résultats statistiques après correction

Sur Basic-Fit/Fitness Park, l'estimation OLS demeure 0,814 et le R² 0,842.
La bande HAC indicative devient environ [0,644 ; 0,984], contre la bande
OLS classique [0,717 ; 0,911] précédemment affichée. Il s'agit d'inférences
conditionnelles, pas de preuves de stationnarité près de l'unité.

| Duel | phi IV | Ensemble Anderson–Rubin/HAC à 95 %, asymptotique |
|---|---:|---|
| Basic-Fit / Fitness Park | 0,916 | [0,824 ; 0,991] |
| ClassPass / Gympass | 0,979 | [0,860 ; 1,112] |
| Gymlib / Urban Sports Club | 1,026 | [0,788 ; 1,390] |

Les deux duels d'agrégateurs restent compatibles avec l'unité dans cette
analyse. Pour Basic-Fit, la borne supérieure du bootstrap de triplets à
blocs de quatre mois dépasse aussi 1 (environ 1,003), contrairement aux
blocs de huit ou douze mois. La sensibilité de méthode doit être conservée
dans l'interprétation, et non résolue en choisissant le résultat préféré.

Le pooling donne `phi ≈ 0,9260`. Pour des blocs synchronisés de huit mois
et 1 999 tirages, la médiane vaut environ 0,919 et les percentiles
[0,766 ; 0,977]. L'ancienne exécution affichait une médiane de 0,782 et
[0,584 ; 0,908] sur 4 000 tirages avec un rééchantillonnage différent.
Ces nombres avant/après sont des diagnostics de procédures différentes,
pas une expérience isolant un seul effet. Les blocs de quatre et douze
mois donnent respectivement [0,832 ; 0,995] et [0,727 ; 0,966].

Sans Basic-Fit/Fitness Park, le pooling donne environ **0,9910**. Sans
ClassPass/Gympass il vaut 0,9204 ; sans Gymlib/USC, 0,9226. Le point estimé
sur les trois duels ne suffit donc pas à démontrer une constante sectorielle
précise et transférable à JiyuFit.

## 3. Prévision à origines croissantes

Apprentissage initial : 30 mois ; horizon fixé à 1, 3 ou 6 mois. Chaque
modèle est ajusté uniquement sur le passé disponible à son origine.
Le tableau présente les RMSE en unités de part (0,01 = un point).

| Duel | Horizon | Origines | Persistance | AR(1) | AR(1) saisonnier | Meilleur RMSE observé parmi les cinq modèles |
|---|---:|---:|---:|---:|---:|---|
| Basic-Fit / Fitness Park | 1 | 24 | 0,0362 | 0,0355 | 0,0346 | AR(1) saisonnier |
| Basic-Fit / Fitness Park | 3 | 22 | 0,0531 | 0,0544 | 0,0493 | AR(1) saisonnier |
| Basic-Fit / Fitness Park | 6 | 19 | 0,0545 | 0,0604 | 0,0457 | Saisonnier naïf |
| ClassPass / Gympass | 1 | 84 | 0,0251 | 0,0235 | 0,0239 | AR(1) |
| ClassPass / Gympass | 3 | 82 | 0,0238 | 0,0256 | 0,0267 | Persistance |
| ClassPass / Gympass | 6 | 79 | 0,0269 | 0,0316 | 0,0325 | Saisonnier naïf |
| Gymlib / Urban Sports Club | 1 | 84 | 0,0215 | 0,0210 | 0,0212 | AR(1) |
| Gymlib / Urban Sports Club | 3 | 82 | 0,0220 | 0,0245 | 0,0253 | Persistance |
| Gymlib / Urban Sports Club | 6 | 79 | 0,0225 | 0,0260 | 0,0266 | Persistance |

La saisonnalité aide sur le premier duel, mais aucun modèle n'est supérieur
partout. Les horizons/tests recouvrent des périodes déjà inspectées ; aucune
significativité statistique ni performance garantie sur un marché nouveau
n'est déduite de ce tableau. La référence avec dérive et les MAE figurent
dans le CSV complet exporté.

## 4. Vérifications exécutées

- **23 tests unitaires réussis** : gates, données invalides, schéma métier,
  conservation des retards, bruit de mesure simulé, HAC, ensembles IV,
  chocs communs en panel, absence de fuite temporelle et dérivée analytique.
- **29 cellules Python exécutées de bout en bout**, dans l'ordre, sans
  erreur ni échec d'assertion ; les tests actuariels T1–T13 passent.
- L'outil complet s'exécute sur le CSV Basic-Fit/Fitness Park et produit le
  graphique. G2 est désormais rouge pour la cible de 50 % ; les preuves
  manquantes sont affichées, sans avertissement contredisant un feu vert.
- Les trois CSV sources n'ont pas été modifiés.
- La CI lance désormais les tests ciblés avant le notebook.

Environnement : Python 3.12.10, NumPy 2.5.3, SciPy 1.18.1, Matplotlib 3.11.2,
nbconvert 7.17.1 et ipykernel 7.3.0. Les commandes de reproduction sont dans
le [README](../README.md).

Résultats locaux (exclus de Git) :

- `artifacts/executed-corrected.ipynb` ;
- `artifacts/backtest-scores.csv` et `artifacts/backtest-predictions.csv` ;
- `artifacts/notebook-corrected-outputs.txt` et `artifacts/notebook-corrected.log` ;
- `artifacts/suivi-corrige.png`.

## 5. Limites qui restent ouvertes

La provenance primaire des proxys reste manquante. Une calibration de
JiyuFit exige ses données propres ; aucune série n'a été inventée ni remplacée.
L'inférence reste conditionnelle à la validité des instruments, à la
stationnarité appropriée et à l'absence de ruptures non modélisées.

Le simulateur adaptatif historique conserve sa convention de réponse à un
rival à effort nul, susceptible de créer un état absorbant artificiel.
Ses conclusions de rattrapage ou d'effondrement ont été requalifiées ; une
nouvelle loi comportementale demanderait un choix de modèle explicite, pas
un correctif silencieux. Les contrôles d'équilibre sur grille ne sont pas
des preuves exhaustives dans le jeu continu.

La recherche bibliographique améliore donc la rigueur de l'inférence, de
l'évaluation et des décisions. Elle ne transforme pas les proxys disponibles
en validation terrain du modèle économique.
