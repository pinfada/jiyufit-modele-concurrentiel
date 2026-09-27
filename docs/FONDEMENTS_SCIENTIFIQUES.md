# Fondements scientifiques et corrections — 27 septembre 2026

Cette recherche documente les méthodes applicables au dépôt, leurs adaptations
et leurs limites. Les références ne constituent pas une validation empirique
de JiyuFit. Les trois CSV existants restent les seules observations utilisées.

## Travaux retenus et application

| Recherche scientifique | Apport au projet | Modification concrète |
|---|---|---|
| Newey & West (1987), *A Simple, Positive Semi-Definite, Heteroskedasticity and Autocorrelation Consistent Covariance Matrix*, Econometrica 55(3), 703–708. [Working paper des auteurs, NBER](https://www.nber.org/papers/t0055) | Tenir compte d'erreurs hétéroscédastiques et autocorrélées. | Covariance HAC à noyau Bartlett pour OLS, intercept conditionnel et test IV. |
| Künsch (1989), *The Jackknife and the Bootstrap for General Stationary Observations*, Annals of Statistics 17(3), 1217–1241. [Notice éditeur, DOI](https://doi.org/10.1214/aos/1176347265), [bibliographie de l'auteur, ETH](https://people.math.ethz.ch/~kuensch/papers/) | Cadre des blocs pour observations stationnaires dépendantes. | Blocs de triplets de retards construits avant rééchantillonnage ; sensibilité 4/8/12 mois. Adaptation spécifique au dépôt. |
| Hansen (1999), *The Grid Bootstrap and the Autoregressive Model*, Review of Economics and Statistics 81(4), 594–607. [Article sur le site de l'auteur](https://www.ssc.wisc.edu/~bhansen/papers/restat_99.pdf) | Les bootstrap usuels peuvent mal couvrir près d'une racine unitaire. | Suppression des affirmations de probabilité de stabilité et des assertions imposant phi < 1. Le grid bootstrap de Hansen n'est pas implémenté : son cadre ne corrige pas automatiquement un proxy bruité. |
| Staiger & Stock (1997), *Instrumental Variables Regression with Weak Instruments*, Econometrica 65(3), 557–586. [Working paper des auteurs, NBER](https://www.nber.org/papers/t0151) | Une faible corrélation instrument–régresseur fragilise l'inférence IV. | Diagnostic de première étape et conservation explicite des tirages non identifiés. |
| Lee, McCrary, Moreira & Porter (2022), *Valid t-Ratio Inference for IV*, American Economic Review 112(10), 3260–3290. [Version des auteurs](https://users.ssc.wisc.edu/~jrporter/Valid_IV_Inference_JustID_March2022.pdf) | Limites des intervalles IV usuels et des règles de seuil sur F ; discussion de l'inférence Anderson–Rubin. | Inversion Anderson–Rubin avec covariance HAC ; ensembles disjoints/non bornés conservés. La méthode tF propre à cet article n'est pas implémentée. |
| Bergmeir, Hyndman & Koo (2018), *A note on the validity of cross-validation for evaluating autoregressive time series prediction*, Computational Statistics & Data Analysis 120, 70–83. [Article des auteurs](https://robjhyndman.com/publications/cv-time-series/) | Le choix d'une validation temporelle dépend des hypothèses sur les erreurs. | Évaluation à origines croissantes, méthode explicitée par [Hyndman](https://robjhyndman.com/hyndsight/tscv/) et [tsCV](https://pkg.robjhyndman.com/forecast/reference/tsCV.html). Le papier n'affirme pas que tout K-fold est invalide. |
| Rochet & Tirole (2003), *Platform Competition in Two-Sided Markets*, JEEA 1(4), 990–1029. [Article, archive de Toulouse](https://publications.ut-capitole.fr/id/eprint/1019/1/platform.pdf) | Participation, structure des prix et multi-affiliation des deux côtés d'une plateforme. | Documentation alignée sur les sportifs et lieux déjà définis dans le modèle ; protocole de collecte enrichi. Aucune élasticité prestataire fictive n'est injectée. |
| Baye, Kovenock & de Vries (1994), *The solution to the Tullock rent-seeking game when R > 2*, Public Choice 81, 363–380. [Article, archive Erasmus](https://repub.eur.nl/pub/12413/TheSolutiontotheTullock_1994.pdf) | Régime mixte du contest symétrique, distinct de la persistance temporelle. | Domaine de validité clarifié : ni phi = 1 ni tout duel asymétrique ne peuvent être assimilés à ce résultat. |

Les textes de Hansen, Lee et al., Rochet–Tirole et Baye et al. ont été
consultés dans leurs versions intégrales accessibles. Pour Künsch, la notice
et la bibliographie de l'auteur ont été vérifiées ; le téléchargement intégral
via l'éditeur n'était pas accessible lors de cette recherche. Le choix précis
de rééchantillonner les triplets est une adaptation algorithmique documentée
et testée ici, pas une recette prétendument citée mot pour mot dans l'article.

## Ce qui change dans l'inférence

On note `phi` le coefficient de `L[t+1] = a + phi L[t] + erreur`. L'instrument
lag2 n'est valide que sous des restrictions sur les innovations et le bruit
de mesure. Il ne résout pas une saisonnalité omise, une rupture structurelle
ou une mesure d'attention non comparable entre acteurs.

L'ancien bootstrap reconstruisait les retards sur des blocs de niveaux
recollés. Des paires/triplets artificiels entraient donc dans les covariances.
Le nouveau bootstrap rééchantillonne des lignes déjà formées `(y, x, z)`.
En panel, les mêmes dates sont tirées pour tous les duels : les coïncidences
de chocs ne sont plus éliminées artificiellement. Les valeurs manquantes
liées aux périodes de disponibilité sont conservées.

Cette correction ne rend pas le panel stationnaire et ne démontre pas que
les duels ont le même coefficient. Le pooling reste conditionnel. Les
percentiles sont des diagnostics exploratoires, pas une probabilité du
paramètre ni un test valide de racine unitaire. Les tirages non identifiés
restent visibles au lieu d'être silencieusement supprimés.

Pour le diagnostic IV local, le test Anderson–Rubin consiste à régresser
`y - phi0*x` sur la constante et l'instrument `z`, puis à tester le coefficient
de `z` avec HAC. La statistique est le quotient d'un carré affine par une
variance quadratique en `phi0`. Son inversion résout une inégalité du second
degré sur tout l'axe réel. La validité asymptotique requiert notamment la
validité de l'instrument et une dépendance compatible avec HAC ; aucune
garantie uniforme près de l'unité n'est revendiquée ici.

La fenêtre HAC par défaut utilise `floor(4*(n/100)^(2/9))` retards et une
correction de degrés de liberté `n/(n-p)`. C'est un choix de mise en œuvre,
pas une garantie de précision en petit échantillon. Les fonctions exposent
le nombre de retards pour permettre une analyse de sensibilité.

## Ce qui change dans les prévisions

Chaque modèle est réestimé à chaque origine sur les observations disponibles
jusqu'à cette date. Les horizons sont fixés à 1, 3 et 6 mois et les cibles
sont identiques entre concurrents. La saisonnalité annuelle utilise un couple
sinus/cosinus, choisi comme variante parcimonieuse ; ce choix d'ingénierie
n'est pas une validation causale ni une découverte saisonnière indépendante.

Les résultats incluent RMSE, MAE et nombre d'origines, avec persistance,
saisonnier naïf et dérive comme références. Les périodes de test se
chevauchent : les erreurs ne sont pas des réplications indépendantes. Aucune
significativité d'un gain n'est annoncée sans une analyse dédiée.

## Lien corrigé entre accumulation et sensibilité

Dans la réduction à accumulation finie du dépôt, la dérivée au point fixe est

```text
phi_local = [1 + b*r*(1-s*)] / [1 + b*(1-s*)].
```

Cette formule est une dérivation propre au modèle, confrontée à des
différences finies dans les tests et en section XXXIV. Pour `0 < r < 1` et
`0 < b < infini`, elle situe la persistance locale entre r et 1. Elle explique
pourquoi la difficulté d'estimer b ne justifie pas de poser automatiquement
`phi = r`. Une régression globale bruitée n'identifie pas non plus cette
dérivée locale sans hypothèses supplémentaires.

## Ce que les publications ne permettent pas d'affirmer

- Un seuil de 50 % dans un duel n'est pas un seuil universel de rentabilité.
- Aucun de ces travaux ne calibre les marges, rétentions ou élasticités de JiyuFit.
- L'effet causal d'une promotion ou d'une hausse publicitaire sur r n'est pas établi.
- L'optimalité d'une expansion séquentielle n'est pas démontrée par les CSV.
- Les trajectoires à efforts nuls du simulateur historique dépendent de sa
  convention de réponse à zéro ; elles ne prouvent pas une guerre d'usure.
- La certification numérique des équilibres sur grille ne constitue pas une
  borne exhaustive sur les déviations possibles dans le jeu continu.

Le prochain gain de validité externe exige des sources d'attention
reproductibles et des séries propres de clients, rétention, prix, coûts,
dépenses d'acquisition et participation des prestataires. Ces données ne sont
pas présentes dans le dépôt ; elles n'ont pas été inventées.
