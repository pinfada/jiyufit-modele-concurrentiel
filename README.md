# JiyuFit — Modèle concurrentiel à capital de réseau

Modèle mathématique et simulation Python d'un duel de plateformes, avec
capital de réseau et populations de **sportifs** (`s`) et de **lieux
partenaires** (`l`). Le dépôt combine théorie, scénarios numériques,
exploration de trois proxys d'attention et suivi conditionnel d'une ville.

**Statut : outil de recherche et d'aide à la décision, non calibré sur des
données propres à JiyuFit.** L'exécution et les assertions vérifient des
propriétés du code ; elles ne démontrent pas une validité causale ou une
précision prospective universelle.

## Modèle biface, liquidité et OPEX

Le [rapport Mindbody/ClassPass](docs/MINDBODY_CLASSPASS_ET_MODELE_BIFACE.md)
présente les données publiques collectées, les tests exécutés et le modèle
local utilisateurs/prestataires. Celui-ci relie les réservations à la
compatibilité et à la capacité disponible, puis calcule croissance,
attrition et solde d'exploitation. Les effets de réseau peuvent produire
une accélération, sans imposer une trajectoire exponentielle.

Les 14 trimestres Mindbody servent à des contrôles prédictifs ; les
8 observations ClassPass conservent leurs fenêtres et définitions propres.
Les paramètres des scénarios bifaces restent **hypothétiques** : ces
publications ne permettent pas de calibrer la liquidité ni un point de bascule.
Le module `outils/liquidite_observee.py` prépare cette mesure à partir des
recherches réelles, incluant les recherches sans résultat.

```powershell
.\.venv\Scripts\python.exe -X utf8 outils/valider_plateformes.py
```

## Corrections scientifiques

Un [test sur les données officielles de Basic-Fit](docs/VALIDATION_CONCURRENT_BASICFIT.md)
utilise désormais 24 trimestres d'abonnements publiés, de 2020 à 2025. Le CSV,
les sources et les scripts de collecte et de validation sont livrés. Ce test
de dynamique des effectifs ne remplace pas une validation des parts de marché.

Les sections empiriques ont été révisées après audit :

- distinction entre la persistance observée `phi` et la sensibilité
  structurelle `r` de Tullock ;
- bootstrap de triplets de retards, sans faux voisinages aux raccords ;
- rééchantillonnage calendaire synchronisé entre les duels ;
- covariance HAC et diagnostic IV avec ensembles Anderson–Rubin ;
- comparaison à origines croissantes, horizons fixes 1/3/6 mois, RMSE et MAE ;
- gates cohérentes : une traction insuffisante ne peut plus autoriser l'expansion ;
- statut indéterminé si la calibration ou les preuves métier sont manquantes.

Les sources, adaptations et limites figurent dans les
[fondements scientifiques](docs/FONDEMENTS_SCIENTIFIQUES.md).
Le [rapport après corrections](docs/CORRECTIONS_ET_RESULTATS.md) présente les
résultats recalculés et leurs différences avec l'état initial.

## Fichiers

| Fichier | Rôle |
|---|---|
| `jiyufit_modele_concurrentiel.ipynb` | Théorie, simulation et évaluations, sections I–XXXVII |
| `outils/marche_biface.py` | Scénarios locaux : deux faces, liquidité, capacité et OPEX |
| `outils/valider_plateformes.py` | Contrôles Mindbody/ClassPass et export des scénarios |
| `outils/liquidite_observee.py` | Mesure sur recherches horodatées, sans inventer les données absentes |
| `outils/inference.py` | HAC, IV, bootstrap, diagnostics et backtests partagés |
| `outils/dynamique_reduite.py` | Accumulation finie et dérivée locale au point fixe |
| `outils/donnees.py` | Validation et lecture des séries mensuelles |
| `outils/suivi_ville.py` | Scénarios de trajectoire et gates G1/G2 |
| `outils/collecter_basicfit.py` | Collecte des tableaux trimestriels des rapports officiels |
| `outils/valider_concurrent.py` | Test externe sur effectifs réels, avec comparaisons chronologiques |
| `tests/` | Régressions métier, cas limites statistiques et absence de fuite temporelle |
| `data/` | Proxys historiques, données publiques Basic-Fit/Mindbody/ClassPass et gabarits |
| `docs/STRATEGIE_EXPANSION_MESURE.md` | Règles opérationnelles, hypothèses et format des critères métier |
| `.github/workflows/notebook-tests.yml` | Exécution des tests et du notebook à chaque push/PR |

## Plan du notebook

| Sections | Contenu et portée |
|---|---|
| I–X | Capture de Tullock, valeur biface stylisée, populations et capital ; dérivations et limites |
| XI–XII | Simulation adaptative et assertions numériques |
| XIII–XIX | Recherche et contrôle numérique des équilibres purs, cas symétriques et asymétriques |
| XX–XXII | Trajectoires pour paramètres illustratifs ; sensibilité au schéma adaptatif et aux conventions à effort nul |
| XXIII | Stratégies mixtes symétriques ; exploitabilité du jeu discrétisé et comparaison à la littérature |
| XXIV–XXV | Extension statique à n joueurs et sensibilité locale OAT |
| XXVI | Protocole de calibration et données propres à collecter |
| XXVII | AR(1)-logit descriptif, HAC et validation à origines croissantes |
| XXVIII | Bruit de mesure, IV, instruments faibles et bootstrap corrigé |
| XXIX | Comparaison des trois duels, pooling conditionnel et sensibilité |
| XXX–XXXIII | Garantie de fréquentation : simulations actuarielles, corrélation, persistance et queues épaisses ; tests T1–T13 |
| XXXIV | Accumulation finie : pourquoi la persistance ne suffit pas à identifier r |
| XXXV | Données officielles Basic-Fit : test prédictif trimestriel des effectifs, sans validation structurelle |
| XXXVI | Mindbody/ClassPass : données publiques et contrôles prédictifs, sans calibration de liquidité |
| XXXVII | Scénarios bifaces locaux : réseau, capacité, OPEX et bascule conditionnelle |

## Résultats descriptifs et domaine de validité

Sur le CSV Basic-Fit/Fitness Park, l'AR(1)-logit retrouve `phi OLS ≈ 0.814`
et `R² ≈ 0.842`. Le pooling IV donne environ `0.926` sous hypothèse d'un
coefficient commun. Cela ne démontre pas une constante sectorielle. Sans
le duel Basic-Fit/Fitness Park, l'estimation poolée est proche de `0.991`.

Les proxys ne sont pas des captures de clients ; leur source primaire reste
à documenter. Le point fixe ajusté et la moyenne de fin d'échantillon ne
constituent pas une validation hors échantillon d'un plateau. Les gains de
prévision varient selon le duel, l'horizon et la référence retenue.

Le seuil de persistance `phi = 1` est distinct du seuil du Nash pur `r*`.
La dissipation totale citée dans le régime mixte concerne le cas symétrique
étudié ; elle ne se transpose pas automatiquement à tous les marchés. Les
contrôles numériques sur grille ne couvrent pas toutes les déviations du
jeu continu. Le simulateur historique peut produire des états absorbants
artificiels via sa convention de réponse à un effort rival nul.

## Vérification locale sous Windows (PowerShell)

Depuis la racine du dépôt, installer une fois l'environnement et son noyau :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m ipykernel install --sys-prefix --name jiyufit-local --display-name "Python (JiyuFit local)"
```

Exécuter les tests, puis le notebook complet :

```powershell
.\.venv\Scripts\python.exe -X utf8 -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -X utf8 -m nbconvert --to notebook --execute --ExecutePreprocessor.kernel_name=jiyufit-local --ExecutePreprocessor.timeout=1500 jiyufit_modele_concurrentiel.ipynb --output executed-corrected.ipynb --output-dir artifacts
```

Les sorties recalculées sont dans `artifacts/executed-corrected.ipynb` ; les
prévisions et scores sont exportés par la section XXIX dans
`artifacts/backtest-predictions.csv` et `artifacts/backtest-scores.csv`.
Le notebook source reste sans sorties périmées. `.venv/`, `artifacts/` et les
caches Python sont exclus de Git. Une assertion en échec interrompt la
commande avec un code de sortie non nul.

## Linux, macOS et CI

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python -m unittest discover -s tests -v
.venv/bin/python -m nbconvert --to notebook --execute --ExecutePreprocessor.timeout=1500 jiyufit_modele_concurrentiel.ipynb --output executed-corrected.ipynb --output-dir artifacts
```

Les dépendances scientifiques seules restent dans `requirements.txt`.
`requirements-dev.txt` ajoute l'exécution Jupyter utilisée localement et en CI.

## Suivi d'une ville

Le [contrôle de qualité et les imports financiers](docs/QUALITE_ET_IMPORTS.md)
ajoutent un manifeste lié au CSV par SHA-256 et un journal mensuel rapproché.
Les déclarations métier seules ne suffisent plus à obtenir une G2 verte.
Les commandes d'audit, formats vierges et limites sont documentés dans ce guide.

Un [extracteur PostgreSQL en lecture seule](docs/CONSTITUTION_HISTORIQUE_REEL.md)
produit des instantanés agrégés et traçables. La base locale a été extraite ;
ses données de développement ne sont pas qualifiées comme historique réel.

```powershell
.\.venv\Scripts\python.exe -X utf8 outils/suivi_ville.py data/basicfit_vs_fitnesspark_attention_mensuelle.csv --png artifacts/suivi-corrige.png
```

Le coefficient par défaut est un scénario, pas une estimation locale.
Les options de calibration, la cible de part et le JSON des preuves métier
sont décrits dans la [stratégie et le dispositif de mesure](docs/STRATEGIE_EXPANSION_MESURE.md).
Sans mesures clients, marge positive, rétention, capacité, budget et
calibration documentés, l'outil ne délivre pas de feu vert d'expansion.

## Limites restantes

- Les trois séries fournies ne remplacent pas une collecte indépendante
  et reproductible, ni les données propres à JiyuFit.
- Le bootstrap par blocs et HAC restent conditionnels à leurs hypothèses ;
  leur validité n'est pas garantie au voisinage de l'unité ou sous rupture.
- La dynamique à n joueurs, les stratégies mixtes asymétriques et le
  couplage concurrence/garantie actuarielle ne sont pas implémentés.
- L'optimalité du rythme d'expansion et l'effet causal du marketing sur r
  doivent être évalués par des données et expériences adaptées.
