# JiyuFit — Expansion et dispositif de mesure

Le modèle est un support de scénarios et d'expérimentation. Les trois séries
d'attention permettent une exploration descriptive, pas une validation
causale des prescriptions ci-dessous. Les
[fondements scientifiques](FONDEMENTS_SCIENTIFIQUES.md) précisent les hypothèses.

## 1. Statut des conclusions

| Proposition | Statut corrigé |
|---|---|
| Un AR(1)-logit ajuste les séries fournies | Résultat descriptif reproductible ; ne prouve pas la capture réelle |
| Un coefficient commun aux trois duels | Hypothèse de pooling ; pas une constante sectorielle démontrée |
| Plateau prévisible à ±2,5 points | Ancienne comparaison interne à l'échantillon ; pas une précision prospective garantie |
| Agrégateurs destinés à converger à 50/50 | Non établi ; le ratio de deux proxys n'est pas la totalité du marché |
| phi = 1 implique disparition du Nash pur | Faux rapprochement : persistance temporelle et sensibilité r sont distinctes |
| Densifier une ville avant de répliquer | Hypothèse opérationnelle à tester, conditionnelle aux coûts et à la rétention |
| Publicité ou promotions augmentent nécessairement r | Effet causal non identifié dans les données disponibles |

## 2. Ville pilote et collecte

Définir la zone, les clients contestés et le rival de référence. Collecter
chaque mois `mois,acteur_J,acteur_m`, avec des définitions comparables et une
source traçable. L'outil exige des mois consécutifs, triés et sans doublon,
des valeurs finies et aucune ligne d'activité totale nulle. Les parts nulles
ou unitaires sont bornées pour le logit et signalées explicitement.

Mesurer aussi la marge contributive mensuelle, le CAC, la rétention par
cohorte, les dépenses d'acquisition et les ressources opérationnelles. Pour
les deux côtés de la plateforme, suivre séparément utilisateurs et
prestataires : prix nets, coûts, partenaires réellement disponibles,
participation à plusieurs plateformes et transactions réalisées. Court/long
terme sont des segments de clientèle, pas les deux côtés de la plateforme.

Tester la densité de l'offre et l'acquisition par cohortes ou zones
comparables. La priorité d'un investissement doit venir de son effet mesuré
sur la contribution et la rétention, pas de l'affirmation que tout euro
dépensé en différenciation vaut plus qu'un euro de marketing.

## 3. Scénarios et incertitude

```powershell
.\.venv\Scripts\python.exe -X utf8 outils/suivi_ville.py data/ville_lyon.csv --png artifacts/lyon.png
```

Sans calibration locale, le coefficient `phi = 0.926` est un scénario
historique descriptif. Il ne constitue pas une sensibilité concurrentielle
mesurée ni une constante sectorielle. `--phi-scenario` permet de le modifier ;
`--r-secteur` reste un alias de compatibilité, avec la même interprétation.

Le point fixe et le temps de convergence sont conditionnels à ce scénario.
Le temps annoncé ramène l'écart de logit sous 0,1 (au plus 2,5 points de part),
ce qui n'est pas « 90 % du chemin ». Aucune durée universelle d'expansion par
ville n'en découle.

`--phi-interval MIN MAX` reçoit une plage provenant d'une calibration locale
documentée. L'intercept et son erreur HAC sont réestimés pour chacun des
101 scénarios de l'enveloppe. Celle-ci n'est pas un intervalle de confiance
joint à 95 %. Sans plage locale ou si elle touche phi >= 1, aucun plateau
stationnaire suffisamment étayé n'est retenu pour une décision verte.

À partir de 30 mois, un diagnostic OLS/IV et un ensemble Anderson–Rubin/HAC
sont affichés. Un résultat non borné, proche de l'unité ou sensible au bruit
appelle une revue du modèle et des données ; il ne dicte pas une baisse de
marketing. HAC et IV ne garantissent pas une inférence fiable près de l'unité.

## 4. Gates corrigées

**G1 — traction descriptive.** La moyenne des trois derniers mois dépasse
celle des trois premiers, et le plateau du scénario dépasse le niveau
initial de plus de cinq points. Ce seuil est une convention opérationnelle,
pas un test de significativité ni une preuve de rentabilité. Au moins huit
mois de données sont requis pour le diagnostic.

**G2 — expansion.** Un feu vert exige simultanément :

1. G1 verte ;
2. une trajectoire récente compatible avec le scénario et soit une proximité
   au plateau, soit au plus six mois de convergence conditionnelle restants ;
3. un plateau et la borne basse de son enveloppe au-dessus de la cible choisie ;
4. une plage locale de phi entièrement dans `(0,1)` et une calibration validée ;
5. des mesures de clients, pas seulement de l'attention ;
6. une marge contributive mensuelle positive ;
7. une rétention, une capacité opérationnelle et un budget d'expansion validés.

Un critère échoué donne **ROUGE**. Une preuve manquante ou une incertitude
non levée donne **INDÉTERMINÉE**, sans feu vert automatique. Chaque motif est
affiché. Une part constante de 10 % ne peut donc plus autoriser l'expansion.

La cible par défaut de 50 % est un choix de gouvernance configurable via
`--part-cible`. Une activité rentable peut viser moins de 50 % d'un duel ;
la littérature citée ne fournit pas ce seuil universel. La tolérance de
trajectoire (cinq points par défaut) est également configurable.

## 5. Critères métier explicites

Le fichier JSON passé à `--criteres-metier` contient les champs suivants :

| Champ | Valeur attendue pour une G2 verte | Preuve à conserver lors de la revue |
|---|---|---|
| `mesure` | `clients` | Définitions, extraction et période communes aux acteurs |
| `marge_contributive_mensuelle` | Nombre strictement positif | Recettes moins coûts variables et acquisition récurrente attribuables |
| `retention_validee` | `true` | Cohortes et seuil de rétention fixés avant revue |
| `capacite_validee` | `true` | Capacité de service et équipe disponibles |
| `budget_expansion_valide` | `true` | Budget et trésorerie suffisants pour la ville suivante |
| `calibration_locale_validee` | `true` | Audit des données, hypothèses et plage de phi |

Ces champs représentent une revue métier documentée ; le script ne vérifie
pas à lui seul la véracité des déclarations. Les champs absents restent
manquants. Les booléens doivent être des booléens JSON, pas les chaînes
`"true"` ou `"false"`.

```powershell
.\.venv\Scripts\python.exe -X utf8 outils/suivi_ville.py data/ville_lyon.csv --phi-scenario 0.8 --phi-interval 0.72 0.88 --part-cible 0.4 --criteres-metier data/criteres_lyon.json
```

Les nombres de cette commande illustrent la syntaxe : ils ne sont pas une
calibration de Lyon. Aucun fichier de critères prévalidés n'est fourni.

## 6. Revue trimestrielle

### Contrôles désormais obligatoires pour G2

Les déclarations ci-dessus ne suffisent plus au feu vert. Le suivi exige
également `--source` (manifeste clients lié au CSV exact), `--journal` et
`--couverture` (mouvements financiers et totaux de contrôle). Les trois derniers
mois doivent être rapprochés et positifs après acquisition, dans le territoire
de la série. Ce délai est une convention de gouvernance, pas un résultat
scientifique. La marge du dernier mois doit correspondre au JSON métier.
Voir les [formats et contrôles exécutables](QUALITE_ET_IMPORTS.md).

Archiver les données et les sorties. Examiner les erreurs de prévision à
1, 3 et 6 mois face aux références naïves ; comparer les mêmes périodes et
horizons. Vérifier les changements de définition, saisonnalités, événements
et rival de référence avant d'attribuer un écart à la concurrence.

Décider de l'expansion avec les marges, la rétention et les capacités de la
ville pilote. L'expansion séquentielle reste une hypothèse à comparer à
d'autres rythmes, pas un optimum démontré par ce modèle.
