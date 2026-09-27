# Mindbody, ClassPass et modèle biface de JiyuFit

## Résultat et portée

Les données publiques ont été collectées et les scripts exécutés. Le dépôt contient désormais un modèle local **utilisateurs × prestataires**, avec compatibilité, capacité, acquisition, attrition et OPEX. Basic-Fit reste un test externe de dynamique des effectifs ; ses données ne servent pas à calibrer ce modèle biface.

**La liquidité et les effets de réseau de JiyuFit ne sont pas encore estimés empiriquement.** Les données publiques collectées permettent des contrôles descriptifs et prédictifs sur Mindbody et documentent l'activité de ClassPass. Elles ne permettent pas d'estimer une probabilité de disponibilité à l'instant T, ni de dater un point de bascule pour JiyuFit. Aucun historique mensuel fictif n'a été reconstitué à partir de cumuls.

## Données réellement collectées

### Mindbody : 14 trimestres, 2015-T2 à 2018-T3

Fichiers : `data/public/mindbody_2015_2018/observations.csv` et `provenance.json`. Chaque ligne porte le lien du communiqué officiel. Les empreintes SHA-256 protègent l'intégrité des CSV transcrits, sans constituer une certification indépendante des publications.

- Abonnés professionnels : de 45 665 à 67 364. Il s'agit de sites ou de praticiens abonnés au logiciel, **pas de sportifs**.
- Chiffre d'affaires trimestriel : de 24,8 à 63,8 millions USD. Il combine des activités logicielles et de paiement ; ce n'est pas un revenu homogène de marketplace à la commission.
- Quelques publications donnent aussi des consommateurs uniques sur les **deux années précédentes**. Ces observations, parfois approximatives ou exprimées comme des bornes, sont conservées avec leur qualification. Les périodes manquantes restent vides. Ce ne sont pas des utilisateurs actifs mensuels.

Sources représentatives : [2015-T2](https://www.mindbodyonline.com/company/press/mindbody-reports-second-quarter-2015-financial-results), [2017-T4](https://www.mindbodyonline.com/company/press/mindbody-reports-fourth-quarter-and-full-year-2017-financial-results), [2018-T3](https://www.mindbodyonline.com/company/press/mindbody-reports-third-quarter-2018-financial-results), [déclaration SEC 2018-T1](https://www.sec.gov/Archives/edgar/data/1458962/000145896218000006/a2018-q1_10xq.htm) et [rapport Fitness in America, données septembre 2018](https://www.mindbodyonline.com/sites/default/files/public/education/learning-assets/2019-Fitness-in-America-Report.pdf).

Les pages ont été consultées avec l'outil web ; le téléchargement HTML direct des communiqués Mindbody échouait. La collecte est donc une transcription sourcée, pas un extracteur HTML automatisé. Aucun hash de page originale non téléchargée n'est revendiqué. Cette fenêtre historique correspond aux publications financières accessibles collectées ; elle ne décrit pas la situation actuelle.

Entre 2016-T4 et 2017-T4, les abonnés professionnels reculent de **2,98 %**, tandis que le CA trimestriel augmente de **30,10 %**. Le recentrage de l'offre et les tarifs changent en 2017 ; FitMetrix et Booker modifient le périmètre en 2018. Ces variations interdisent d'interpréter mécaniquement le CA comme une puissance du nombre de participants.

Le test à origines croissantes utilise 8 trimestres d'apprentissage initial, puis prévoit 1, 2 et 4 trimestres. À un trimestre, il ne reste que **6 erreurs de prévision** :

| Série | Persistance : RMSE | Dérive logarithmique : RMSE | AR(1) logarithmique : RMSE |
|---|---:|---:|---:|
| Abonnés professionnels | 4 211 | 4 343 | 4 080 |
| CA trimestriel, millions USD | 4,12 | 2,04 | 2,38 |

Ce faible échantillon avec ruptures ne démontre pas la supériorité générale d'un modèle. Le CA n'est pas mieux prévu par AR(1) que par une simple dérive. Aucun paramètre estimé ici n'est transféré au simulateur JiyuFit. Les chiffres sont ceux des publications collectées, sans reconstruction d'un jeu complet de millésimes disponibles en temps réel.

### ClassPass : 8 observations, avec leurs périodes et dénominateurs

Fichiers : `data/public/classpass_public/observations.csv` et `provenance.json`.

| Publication | Observation collectée | Usage et limite |
|---|---|---|
| [Bilan 2023](https://classpass.com/blog/2023-classpass-look-back-report/) | Réservations fitness +64 %, fenêtre janvier–novembre 2023 | Croissance publiée, pas volume annuel absolu |
| [Bilan 2024](https://classpass.com/blog/2024-classpass-look-back-report/) | Fitness +51 %, octobre 2023–octobre 2024 ; plus de 248 millions de réservations cumulées | Fenêtre différente ; cumul depuis l'origine distinct du flux annuel |
| [Bilan 2025](https://classpass.com/blog/2025-classpass-look-back-report/) | Plus de 27 millions de recherches Pilates et plus de 15 millions de réservations Pilates, 1er janvier–10 octobre 2025 | Bornes, événements non appariés : **15/27 n'est pas une liquidité observée** |
| [Industry Impact 2026](https://classpass.com/partners/2026-industry-impact-report) | 62 millions ou plus de réservations en 2025 ; 88 000 ou plus d'entreprises listées en janvier 2026 | Flux annuel et stock à une autre date ; établissements listés ≠ places disponibles |
| [FAQ partenaires](https://classpass.com/partners/faqs) | 85 % des cours non complets, base 2025 des partenaires intégrés | Ne mesure pas la probabilité qu'une recherche individuelle trouve une offre compatible |

Le script conserve les bornes et les fenêtres ; il refuse implicitement toute calibration de liquidité en retournant un statut **non identifiable**, sans produire de série artificielle. Les taux de croissance ne sont pas chaînés pour inventer des volumes annuels.

Mindbody a [achevé l'acquisition de ClassPass le 15 octobre 2021](https://www.mindbodyonline.com/company/press/mindbody-completes-acquisition-of-classpass). Ces marques ne constituent donc pas deux marchés indépendants après cette date.

## Équations ajoutées : une cellule locale et une période mensuelle

Implémentation : `outils/marche_biface.py`. Les paramètres par défaut sont **illustratifs**, en EUR pour les montants. Ils ne sont pas ajustés aux données concurrentes.

Pour une cellule cohérente de territoire, activité et créneau, on note U les utilisateurs et S les prestataires effectivement actifs. Les paires potentielles sont U×S. Additionner toute l'offre nationale masquerait les incompatibilités locales.

L'hypothèse de Poisson donne une approximation agrégée de compatibilité :

```
L = 1 − exp(−q S)
D = demandes par utilisateur × U
C = places par prestataire × S
B = min(D × L, C)
service = B / D ; remplissage = B / C
```

Les ratios sans dénominateur sont inconnus (`None`), et aucune réservation n'existe sans offre ou sans demande. Si la capacité est nulle, L est fixé à zéro. q résume notamment proximité, horaires, activité, prix et disponibilité ; son homogénéité est une simplification à tester. L représente une compatibilité avant rationnement agrégé, **pas une mesure réelle à l'instant T**. Le taux de service tient ensuite compte de la capacité. Un moteur d'inventaire horodaté serait nécessaire pour reproduire les collisions de réservation, annulations et files d'attente.

Pour chaque face, les entrants payants sont l'acquisition externe multipliée par `(1 − stock/marché adressable)`. Les entrants organiques sont :

```
utilisateurs : beta_U × U × service × (1 − U/K_U)
prestataires : beta_S × S × remplissage × (1 − S/K_S)
stock suivant = stock × (1 − attrition) + entrants payants + entrants organiques
```

Les entrants sont plafonnés par le marché restant. Les effets croisés passent par le service et le remplissage ; leurs intensités peuvent différer. Acquisition et activité sont séparées, mais l'attrition reste constante dans cette première extension, et la concurrence/multihoming n'est pas identifiée. Ce module est une extension locale de liquidité ; il ne prétend pas remplacer le jeu concurrentiel historique par un équilibre estimé.

À faible densité et sans congestion, `B ≈ demandes_par_utilisateur × q × U × S`. Doubler les deux faces donne alors presque quatre fois les transactions ; à forte compatibilité ou sous capacité contraignante, cet effet tend à devenir linéaire. C'est une propriété de l'hypothèse, **pas une confirmation empirique de Metcalfe**. Un produit U×S ne prescrit pas à lui seul une trajectoire exponentielle dans le temps. La saturation finit aussi par limiter la croissance.

### OPEX et financement

```
revenu plateforme = prix séance × commission × B
OPEX = fixe + coût variable × B + coût par prestataire × S
       + CAC_U × entrants payants U + CAC_S × entrants payants S
solde exploitation = revenu plateforme − OPEX
```

Le chiffre d'affaires net de commission est distinct du volume d'affaires. Les coûts d'acquisition ne sont pas imputés aux entrants organiques. Cette convention de commission est un scénario économique JiyuFit à renseigner ; elle ne reproduit pas la comptabilité d'abonnements/crédits ClassPass ou SaaS Mindbody. Les taxes, TVA, remboursements, BFR et investissements initiaux ne sont pas simulés. Le besoin cumulé est le creux des soldes cumulés, pas un plan de trésorerie certifié. Le simulateur continue en supposant le financement disponible ; il ne modélise pas une cessation d'activité faute de trésorerie.

### Bascule conditionnelle, sans date promise

Quatre scénarios de 120 mois sont exécutés : référence, effets de réseau désactivés, faible compatibilité et capacité réduite. La référence atteint au **mois d'indice 30** trois mois consécutifs de croissance organique nette positive sur les deux faces ; les trois autres scénarios ne le font pas. C'est une définition opérationnelle annoncée, **ni une bifurcation mathématique démontrée ni une prévision pour JiyuFit**. Le mois initial porte l'indice 0.

La borne `S > −ln(1 − attrition_U/beta_U)/q`, lorsque `beta_U > attrition_U`, est seulement une condition nécessaire côté utilisateurs, hors saturation. Elle n'est pas suffisante : une capacité trop faible peut empêcher la croissance même au-dessus de cette borne. Les tests le vérifient.

## Mesure opérationnelle préparée

`outils/liquidite_observee.py` calcule la proportion de recherches ayant au moins une séance compatible disponible, **en incluant les recherches sans résultat**. Il distingue ce taux de la conversion en réservation, groupe par territoire et mois, exige des horodatages avec fuseau et refuse les identifiants dupliqués ou les lignes incohérentes.

Le gabarit `data/modeles/recherches_liquidite.csv` est vide volontairement. Une entrée vide produit « liquidité inconnue », jamais zéro. Pour l'utiliser :

```python
from outils.liquidite_observee import mesurer
resultats = mesurer("chemin/vers/recherches_reelles.csv")
```

L'offre doit être capturée au moment de chaque recherche avec les filtres effectifs de l'utilisateur, et la réservation attribuée selon une fenêtre définie. Une simple extraction des réservations réussies serait biaisée. Le champ territoire doit identifier une cellule de mesure cohérente ; le script ne reconstitue pas des filtres absents. L'intervalle de Wilson fourni suppose des observations indépendantes et reste indicatif : les recherches répétées d'un même utilisateur demandent ensuite un traitement par grappes. Aucun fichier de recherches privées Mindbody/ClassPass n'a été obtenu ; ce module n'a été vérifié que sur des cas contrôlés.

## Appuis scientifiques et choix d'adaptation

- [Rochet et Tirole, 2003, Platform Competition in Two-Sided Markets](https://publications.ut-capitole.fr/id/eprint/1019/1/platform.pdf) : structure biface, participation et tarification. Soutient la distinction des faces, pas nos valeurs de paramètres.
- [Hinz, Otter et Skiera, 2020, Estimating Network Effects in Two-Sided Markets](https://www.jmis-web.org/articles/1468) : le résumé consulté souligne les effets croisés, l'acquisition/l'activité et les entrées/sorties des deux faces. Justifie des séries simultanées et des effets asymétriques ; aucune équation du texte intégral non consulté n'est revendiquée comme reproduite.
- [Roth, 2007, What Have We Learned From Market Design?](https://www.nber.org/papers/w13530) : épaisseur du marché et congestion sont deux dimensions distinctes. Motive la séparation compatibilité/capacité ; la formule de Poisson est notre hypothèse de travail.
- [Odlyzko et Tilly, 2005, A refutation of Metcalfe's Law](https://www-users.cse.umn.edu/~odlyzko/doc/metcalfe.pdf) : critique d'une valeur universellement quadratique. Motive l'abandon d'une croissance en N² imposée, sans démontrer une forme alternative universelle pour JiyuFit.

## Reproduction et vérification

Vérification locale effectuée le 27 septembre 2026 : **62 tests réussis**, puis
**32 cellules Python exécutées dans l'ordre, sans erreur**, avec validation
du format du notebook. Le notebook recalculé est
`artifacts/executed-biface.ipynb` ; le contrôle d'exécution est enregistré
dans `artifacts/validation-plateformes/execution.json`.

Depuis la racine du dépôt, sans téléchargement nécessaire pour rejouer les CSV collectés :

```powershell
.\.venv\Scripts\python.exe -X utf8 outils/valider_plateformes.py
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m nbconvert --to notebook --execute jiyufit_modele_concurrentiel.ipynb --output executed-biface.ipynb --output-dir artifacts --ExecutePreprocessor.timeout=600 --ExecutePreprocessor.kernel_name=jiyufit-local
```

Les résultats détaillés sont dans `artifacts/validation-plateformes/` : JSON, prévisions Mindbody, scénarios synthétiques CSV et deux graphiques. Les sections XXXVI–XXXVII du notebook exécutent et présentent ces résultats. Les tests couvrent notamment les capacités, les probabilités, l'absence de bascule imposée, les OPEX, la séparation géographique et les données de recherche manquantes. Ces vérifications portent sur le logiciel et les invariants, pas sur une validité causale déjà acquise.
