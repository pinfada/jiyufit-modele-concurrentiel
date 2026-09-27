# Test sur un historique public réel : Basic-Fit

Exécution du 27 septembre 2026. JiyuFit n'ayant pas encore d'historique,
l'évaluation porte sur un acteur existant du fitness. Basic-Fit est un
concurrent indirect ; son réseau de clubs détenus n'est pas une marketplace
biface comme JiyuFit. Ce choix permet un test prédictif externe, pas une
validation de l'ensemble des équations structurelles.

## Données effectivement récupérées

24 trimestres consécutifs, de 2020-Q1 à 2025-Q4. Mesure : abonnements du
réseau Basic-Fit en fin de trimestre, publiés en millions avec deux décimales.
La conversion en unités conserve donc une précision de publication de
10 000 abonnements. Il ne s'agit ni de recherches Internet, ni de visites,
ni d'une part de marché. Aucune interpolation mensuelle n'a été effectuée.
La fenêtre s'arrête à l'exercice complet 2025 ; les communications 2026
après l'intégration de Clever Fit ne sont pas raccordées automatiquement.

Les quatre sources primaires sont :

- [Rapport annuel 2021, page PDF 26](https://corporate.basic-fit.com/docs/Basic-Fit%20Annual%20Report%202021%20WEB?a=6UWq4tddgh8ofCiyWyeA8G) : trimestres 2020 et 2021.
- [Rapport annuel 2022, page PDF 23](https://corporate.basic-fit.com/docs/Basic-Fit_Annual_Report_2022_Pdf.pdf?a=59eFPFFX7yWrajhSZAdWuA) : trimestres 2021 et 2022, avec contrôle du comparatif 2021.
- [Rapport annuel 2024, page PDF 22](https://corporate.basic-fit.com/docs/Basic-Fit%20Annual_Report_2024_Webversion.pdf?a=6YiUByKgbZ06bBQ3VnLkRj) : trimestres 2023 et 2024.
- [Rapport annuel 2025, tableau Membership development](https://annualreport.basic-fit.com/2025/mbr/business-and-financial-review/) : trimestres 2024 et 2025, avec contrôle du comparatif 2024. Le quatrième trimestre retient **4,82 millions hors Clever Fit**, pas les 5,8 millions du nouveau groupe.

Le CSV et sa provenance sont conservés dans `data/public/basicfit_2020_2025/`.
Chaque ligne référence sa source. Les empreintes des PDF/HTML et du CSV sont
enregistrées ; les originaux téléchargés restent dans `artifacts/sources/basicfit/`.

Les publications consultées de Wellhub et ClassPass fournissent des jalons
et indicateurs intéressants, mais les pages examinées n'ont pas fourni une
série régulière suffisante pour ce test. Le choix de Basic-Fit ne démontre
pas que ces plateformes ne disposent d'aucune autre donnée publique.

## Ce qui est testé

Le script de suivi initial exige deux séries mensuelles comparables pour
calculer une part de marché. Les abonnements d'une seule entreprise ne
satisfont pas ce contrat. Un chemin explicite d'évaluation a donc été ajouté :

`log(N[t+1]) = a + phi * log(N[t]) + erreur[t+1]`

C'est une adaptation descriptive de la dynamique autorégressive sur un
effectif, équivalente hors bruit à `N[t+1] = exp(a) * N[t]^phi`.
Elle diffère de `logit(s[t+1]) = a + phi * logit(s[t])` : aucun dénominateur
concurrent n'a été inventé pour faire rentrer les données dans le script.
Le coefficient est trimestriel et n'est pas le paramètre structurel `r`.
Les fonctions HAC communes au notebook sont réutilisées.

Apprentissage initial : 12 trimestres, de 2020 à 2022. À chaque origine,
l'estimation utilise uniquement le passé de la série. Comparaison à 1, 2 et
4 trimestres, aux mêmes origines pour tous les modèles, contre : dernière
valeur observée, même trimestre de l'année précédente, croissance logarithmique
moyenne et AR(1) avec saisonnalité harmonique. Aucun modèle n'est sélectionné
automatiquement sur les résultats.

Ces scores sont des simulations rétrospectives sur des valeurs issues de
rapports annuels ultérieurs. Les archives de première publication ne sont
pas reconstituées : ce n'est pas un backtest prouvant la disponibilité de
chaque valeur en temps réel. Les chocs COVID et changements de réseau restent
dans la série ; un second calcul commence en 2022 pour examiner la sensibilité.

## Résultats effectivement calculés

Erreur quadratique moyenne (RMSE), en nombre d'abonnements ; plus faible est
meilleur. Les chiffres ci-dessous sont arrondis à l'unité.

| Horizon | Prévisions par modèle | AR(1) log-effectif | Dernière valeur | Croissance logarithmique moyenne |
| --- | ---: | ---: | ---: | ---: |
| 1 trimestre | 12 | 113 240 | 148 857 | 91 033 |
| 2 trimestres | 11 | 182 386 | 246 392 | 83 846 |
| 4 trimestres | 9 | 418 835 | 475 698 | 100 454 |

L'AR(1) fait mieux que la dernière valeur, mais moins bien qu'une simple
extrapolation de croissance aux trois horizons du test principal. Ajouter
la saisonnalité harmonique détériore ici les résultats. Le R² d'ajustement
de 0,958 ne constitue donc pas une preuve de supériorité prédictive.

Le coefficient estimé sur les 24 trimestres est `phi = 1,0009`, avec un
intervalle HAC asymptotique approximatif `[0,8975 ; 1,1043]`. Ce petit
échantillon avec ruptures ne permet pas d'établir une convergence vers un
plateau stationnaire. Ce résultat sur un effectif ne réfute pas à lui seul
une équation de part de marché : les variables diffèrent.

La sensibilité depuis 2022, avec 8 trimestres initiaux d'apprentissage, change
le classement : l'AR(1) a une RMSE d'environ 119 958, 176 798 et 347 816 aux
trois horizons, contre 116 614, 188 670 et 421 850 pour la croissance moyenne.
Il n'y a que 8, 7 et 5 prévisions respectivement. La supériorité d'une
méthode n'est donc pas stable selon la fenêtre et l'horizon. Aucune différence
de performance n'est présentée comme statistiquement significative.
Les dates de test changent aussi dans cette sensibilité : elle n'isole pas
causalement l'effet de retirer la période COVID de l'apprentissage.

**Conclusion : données réelles acquises et script exécuté ; capacité prédictive
partielle, mais ni convergence universelle ni validation causale de JiyuFit
établies.** Les comportements concurrentiels, dépenses des deux acteurs,
captation et effets de réseau ne sont pas identifiés par cette seule série.

## Reproduire l'exécution

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -X utf8 outils/valider_concurrent.py data/public/basicfit_2020_2025/abonnements_trimestriels.csv --provenance data/public/basicfit_2020_2025/provenance.json --sortie artifacts/validation-basicfit
```

La validation utilise le CSV versionné et fonctionne sans réseau. Pour
reconstituer les données dans un nouveau dossier :

```powershell
.\.venv\Scripts\python.exe -X utf8 outils/collecter_basicfit.py --sortie artifacts/basicfit-recollecte
```

Le collecteur réutilise les originaux du cache quand ils existent ; un cache
neuf via `--cache` déclenche leur téléchargement. `--hors-ligne` exige que
toutes les sources soient déjà présentes. Le collecteur refuse d'écraser un
jeu existant et bloque si les comparatifs de deux rapports se contredisent.

Sorties : `resultats.json`, `scores.csv`, `predictions.csv` et `validation.png`
dans `artifacts/validation-basicfit/`. La section XXXV du notebook réexécute
ce test sans téléchargement et affiche les résultats et le graphique.

Vérification finale : 50 tests automatisés réussis ; notebook complet exécuté
avec 30 cellules de code et aucune erreur dans
`artifacts/executed-basicfit.ipynb`. Les tests incluent l'extraction des tableaux,
le refus des trous calendaires, la récupération d'une équation connue sur
données de test et l'absence d'influence des valeurs futures sur les prévisions
antérieures. Ces contrôles techniques ne constituent pas une validation économique.
