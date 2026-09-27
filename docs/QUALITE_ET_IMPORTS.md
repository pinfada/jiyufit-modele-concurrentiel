# Contrôles de qualité et historique financier

Révision du 27 septembre 2026. Les contrôles ci-dessous sont exécutés par
Python. Ils vérifient la cohérence des données et de leur provenance déclarée ;
ils ne certifient pas l'authenticité des pièces ou les effets causaux du modèle.

## Angles morts traités

| Avant | Comportement corrigé |
| --- | --- |
| Une déclaration `mesure=clients` pouvait qualifier un CSV d'attention | G2 exige un manifeste clients cohérent, lié au CSV par SHA-256, avec période et territoire |
| Une marge positive saisie manuellement pouvait suffire côté financier | G2 vérifie les mouvements, les totaux de contrôle et la concordance de la marge déclarée |
| Pas d'historique financier importable | Journal catégorisé et couverture mensuelle produisent un rapport reproductible par territoire |
| Absence, estimation et zéro pouvaient être confondus | Une marge inconnue reste `null` ; zéro exige une couverture observée et un contrôle explicite |
| Risque de doublons et de coûts omis | Identifiants uniques, catégories obligatoires et rapprochement de chaque catégorie |
| Réutilisation d'une preuve d'une autre ville ou période | Jointure exacte territoire/mois ; trois derniers mois exigés pour G2 |

La règle des trois derniers mois tous positifs après acquisition est une
convention prudente de gouvernance, pas un seuil scientifique universel. Elle
ne garantit ni trésorerie suffisante ni couverture des coûts fixes.

## 1. Auditer les séries existantes

```powershell
.\.venv\Scripts\python.exe -X utf8 outils/auditer_donnees.py data/basicfit_vs_fitnesspark_attention_mensuelle.csv data/duel_classpass_vs_gympass.csv data/duel_gymlib_vs_urbansportsclub.csv --sortie artifacts/audit-sources.json
```

Code de sortie 0 : tous les contrats de provenance clients sont cohérents.
Code 1 : au moins une source ne permet pas cette qualification. Les calculs
exploratoires restent possibles. Code 2 : erreur d'utilisation ou de sortie.
Un CSV invalide est décrit dans le rapport sans masquer les autres fichiers.

Le manifeste est recherché à côté du CSV, avec le suffixe `.source.json`.
Le modèle vierge est dans `data/modeles/duel.source.json`. Le remplir à partir
de l'extraction réelle, pas à partir de suppositions : fournisseur/requête ou
référence d'export, horodatage ISO UTC, SHA-256 des octets exacts, territoire,
mois de début/fin, statut, unité, définitions, acteurs et traitement des
ruptures. `statut=observe`, `mesure=clients` et
`perimetres_comparables=true` sont nécessaires pour une décision clients.
Les champs vides, simulations, proxys et parts bornées ne passent pas ce contrôle.
L'empreinte prouve la correspondance avec le fichier, pas sa véracité.

## 2. Construire l'historique de gestion

Les en-têtes prêts à remplir sont dans `data/modeles/journal.csv` et
`data/modeles/couverture.csv`. Aucun chiffre fictif n'est fourni comme preuve.

Journal : une ligne par mouvement, identifiant unique, date `AAAA-MM-JJ`,
territoire stable, catégorie, centimes EUR entiers non négatifs, référence de
pièce ou d'export. Les catégories sont :

- `revenu_plateforme` : revenu revenant à JiyuFit, hors montants reversés aux lieux ;
- `remboursement_plateforme` : diminution du revenu propre de JiyuFit ;
- `cout_variable` : coûts variables réellement supportés, frais de paiement inclus ;
- `acquisition` : dépenses d'acquisition attribuées au territoire et au mois.

La marge est revenu plateforme moins les trois autres catégories. Une annulation
ou correction doit être normalisée en amont selon cette convention ; les
montants négatifs et conversions de devises implicites sont refusés. Ne pas
compter un même paiement à la fois comme paiement brut et comme commission.
Les dates suivent une convention de gestion uniforme, documentée dans les
références ; cet import ne constitue pas une comptabilité légale en partie double.

Couverture : une ligne par mois/territoire/catégorie, avec `statut` parmi
`observe`, `estime`, `synthetique`, `manquant`, total de contrôle en centimes et
référence. Le contrôle doit venir de la source ou du rapprochement des pièces,
pas d'une simple recopie de la somme du journal. Même un zéro doit être attesté.
Une dépense absente des deux fichiers n'est détectable que si la couverture
est sincère et exhaustive ; le logiciel ne peut pas découvrir une pièce cachée.

```powershell
.\.venv\Scripts\python.exe -X utf8 outils/historique_comptable.py data/journal.csv data/couverture.csv --sortie artifacts/historique-comptable.json
```

Les mois intermédiaires absents sont matérialisés comme inconnus. Le rapport
contient les montants, la marge, les écarts et les empreintes des deux entrées.
Code 0 si toutes les périodes sont rapprochées, 1 si des périodes sont
incomplètes/non rapprochées, 2 si l'entrée est mal formée. Une estimation
conserve son statut : elle ne devient pas une preuve observée.

## 3. Utilisation dans le suivi de ville

```powershell
.\.venv\Scripts\python.exe -X utf8 outils/suivi_ville.py data/ville.csv --source data/ville.source.json --journal data/journal.csv --couverture data/couverture.csv --criteres-metier data/criteres.json --phi-scenario 0.8 --phi-interval 0.72 0.88
```

Les paramètres numériques illustrent la syntaxe, pas une calibration réelle.
Le journal est recalculé depuis ses entrées à chaque exécution ; un ancien
rapport JSON ne sert pas de preuve financière. Les trois derniers mois de la
série doivent être rapprochés dans le territoire du manifeste, avec une marge
positive, et la dernière marge doit correspondre à la déclaration métier au
centime près. L'absence d'une preuve empêche le vert ; une contradiction avérée
donne rouge. Les critères de rétention, de capacité, de budget et la validation
scientifique de la calibration restent des revues métier explicites.

## 4. Audit de l'application JiyuFit voisine

Lecture du code et du schéma local, sans connexion à la production :

- `Analytics::RevenueAnalyticsService` utilise des commissions ou un repli
  sur les paiements : additionner les deux créerait un double comptage.
- `payments` comporte des frais de traitement et remboursements, mais leur
  présence dans le schéma ne garantit ni complétude ni bonne affectation au mois.
- `BusinessMetricsService#calculate_user_retention_rate` mesure un retour de
  connexion parmi les comptes anciens. Ce n'est pas une rétention de clients
  ayant consommé une prestation.
- `reservations` comporte `presence_confirmed` : une réservation créée ne
  prouve pas la consommation. La sémantique et la complétude de ce champ restent
  à auditer avant une extraction de cohortes.

Les collecteurs seuls ne sont pas un historique observé. Aucune donnée de
production ni dépense réelle n'a été inventée pour rendre G2 verte. La validation
prédictive, les ruptures de marque, la comparabilité concurrentielle et les
cohortes de consommation restent des limites explicites du dossier courant.

Le serveur Docker local `jiyufit_pilotage_pg` a également été interrogé avec
`default_transaction_read_only=on`. Son catalogue ne liste que `postgres`
et `jiyufit_test`. Aucun historique de production n'a donc été identifié dans
ce serveur ; le nom d'une base de test ne permet pas d'en faire une source
observée. Aucun enregistrement personnel n'a été extrait ni modifié.

## Vérifications réalisées

- 40 tests automatisés réussis, dont doublons, montants exacts, périodes
  absentes, contrôles divergents, simulations, empreintes incohérentes,
  protection des entrées et codes de sortie des imports.
- Notebook réexécuté : 29 cellules de code, aucune sortie d'erreur dans
  `artifacts/executed-quality.ipynb`.
- Audit réel des trois CSV : trois sources non validées pour une décision
  clients ; rapport `artifacts/audit-sources.json`, code de sortie 1 attendu.
- Suivi Basic-Fit exécuté avec graphique : G2 rouge et motifs explicites,
  y compris la provenance et les preuves financières manquantes.
