# Calculateur — garantie de fréquentation

Calculatrice autonome : **un seul fichier HTML**, sans serveur, sans dépendance,
sans envoi de données. On l'ouvre dans un navigateur, on l'envoie par mail, ou on
la publie telle quelle. Elle n'est branchée ni à l'application JiyuFit ni à une
base de données.

Elle répond, activité par activité (salle, studio, club, cours en plein air…), aux questions de la
[doctrine de revenus](https://github.com/pinfada/jiyufit/blob/main/docs/02-business/REVENUE_MODEL_DOCTRINE.md) :

- **Ce que l'activité gagne** : revenu net moyen après commission, plancher garanti, et graphique mois par mois montrant où JiyuFit aurait complété.
- **À combien proposer la couverture** : prime pure (manque moyen sous le
  plancher), prime commerciale (γ × prime pure, jamais sous prime pure + frais).
- **Le seuil de rentabilité** : remplissage moyen sous lequel la garantie,
  vendue à un prix donné, devient perdante ; loss ratio ; stress « tout le
  réseau recule de N points » sur un portefeuille.

## Utilisation

Ouvrir `calculateur-garantie.html` dans un navigateur.

| Vue | Pour qui | Contenu |
|---|---|---|
| Vue communauté | Un prospect | Revenu, plancher, prix (et sa part du revenu), graphique, explication du prix, conditions |
| Vue JiyuFit | Interne | Prime pure, loss ratio, commission, marges, seuil de rentabilité |
| Portefeuille (CSV) | Interne | Plusieurs salles d'un coup, stress corrélé, export CSV |

**Version à diffuser** : ajouter `?public=1` à l'adresse (seule la vue communauté
reste ; le complément moyen attendu et la marge n'y apparaissent jamais). Les
réglages se passent aussi dans l'adresse :

```
calculateur-garantie.html?public=1&prix=49&commission=15
```

Paramètres : `prix` (€/mois ; vide = prime commerciale), `commission` (%),
`gamma`, `quantile` (% du plancher, 10 = P10), `frais` (€/mois/salle),
`sans_jiyufit` (% de remplissage sans JiyuFit), `observation` (mois avant
activation, 3 par défaut), `mode` (`estimation` ou `historique`), `vue`
(`communaute`, `jiyufit`, `portefeuille` ; l'ancien `salle` reste accepté).

## Données

Deux modes de saisie exclusifs (un seul jeu de champs visible, aucune priorité
implicite) :

- **Estimation rapide** : mois habituel + mauvais mois (un mois faible qui revient
  environ 1 fois sur 10) ; le remplissage suit une loi logit-normale, comme dans le
  notebook (section XXX). Le graphique montre « vos 10 mois types ».
- **Mois par mois** : une grille par mois nommé (12 à 36 mois, au moins 6
  renseignés). On peut coller une colonne copiée d'un tableur dans n'importe quelle
  case (virgules ou points, « % », espaces insécables acceptés) ; une série plus
  longue que les cases restantes est lue comme « les N derniers mois ». Le revenu
  moyen affiché est la moyenne réellement observée.

Ce que l'historique débloque :

| Mois renseignés | Plancher et prix | Test sur une année non utilisée | Creux saisonniers |
|---|---|---|---|
| 6 à 23 | Oui (bilan présenté « à titre indicatif ») | Non | Non |
| 24 et plus | Oui | Oui : plancher calculé sans la dernière année, puis appliqué à elle | Oui : mois sous 85 % de la moyenne chaque année |

Format CSV du portefeuille (séparateur `;` et décimales `,`, ou `,` et `.`) :

```
nom;places_mois;prix;commission;remplissage;mois_faible;historique;prix_propose;dernier_mois
Volt Fitness;173;12;15;65;54;;89;
Salle B;120;10;15;;;66 48 70 63 59 71 64 52;;2026-08
```

L'historique va du plus ancien au plus récent. `dernier_mois` (AAAA-MM, facultatif)
situe son dernier relevé ; sans lui, c'est le dernier mois écoulé. Il ne sert qu'à
nommer les creux saisonniers : un historique mal daté signalerait un creux au
mauvais mois.

C'est la porte d'entrée pour les données clients, puis pour un futur scraping :
tout ce qui produit ce CSV alimente l'outil sans le modifier.

## Jeu d'essai : `exemples/studios_lyon_2026-09.csv`

À importer dans la vue Portefeuille. **Ce ne sont pas des fréquentations mesurées** :

- **Prix réels** relevés le 27/09/2026 ([exo-sport.fr](https://exo-sport.fr/blog/meilleurs-studios-pilates-reformer-lyon)) :
  Pur Pilates Villeurbanne 25 €/séance (4 places max sur Reformer), The New Me
  Célestins 35 €, Pilates Social Club 42 €.
- **Capacités** : 4 places pour Pur Pilates (publié) ; 10 et 8 places pour les
  deux autres sont des **hypothèses** (non publiées), tout comme le nombre de
  séances par semaine.
- **Niveau de remplissage** : 77 %, milieu de la fourchette sectorielle
  d'utilisation des cours de 70 à 85 % ([Virtuagym, benchmarks 2025-2026](https://business.virtuagym.com/blog/fitness-industry-benchmarks/)) ;
  la dernière ligne teste 70 %.
- **Variations mensuelles** : profil réel de `data/basicfit_vs_fitnesspark_attention_mensuelle.csv`
  (Fitness Park, 2024-01 → 2025-12), chaque mois divisé par la moyenne mobile
  centrée sur 12 mois. C'est un indicateur d'attention en ligne, qui varie
  probablement plus que la fréquentation réelle : le jeu d'essai est prudent
  (primes plutôt surestimées). Le même profil s'applique à toutes les lignes, ce
  qui revient à des salles parfaitement corrélées.

Remplacer ces lignes par des historiques de salles réelles dès qu'ils existent.

## Promesse conditionnelle et anti-sélection

La calculatrice est une **démonstration de valeur avant compte**, pas une offre
ferme. Proposer un plancher à une activité dont JiyuFit n'a pas l'historique
expose au risque d'anti-sélection maximal. La vue communauté l'affiche donc comme
une promesse conditionnelle : la garantie s'active après une **période
d'observation** (`observation`, 3 mois par défaut) sur JiyuFit, et le plancher est
alors recalculé sur les données réelles. « Résiliable chaque mois » n'est plus mis
en avant.

Prérequis côté application (flag `occupancy_guarantee_v1`, à construire, hors de
cet outil) : règles d'éligibilité (historique minimum, TrustScore, remplissage
passé), délai de carence / observation, plafonds de couverture, paramétrés avant
le premier flux financier (cf. `REVENUE_MODEL_DOCTRINE.md` §6, « deux poisons »).

## Modèle et limites

- Plancher = quantile bas du remplissage (P10 par défaut) : on garantit ce qui
  est déjà vrai 9 mois sur 10.
- **Avec un historique, une seule méthode, quelle que soit sa durée** : loi
  logit-normale ajustée sur la moitié basse des mois (médiane et quartile bas).
  Deux méthodes écartées après essai sur des données réelles :
  - le quantile brut des mois : sur 12 mois, il tombe entre les deux pires mois,
    et retirer un seul mois divisait le prix par deux (57 € → 28 €) ;
  - un ajustement sur tous les mois : les mois complets (100 %, plafond de
    capacité) gonflaient la dispersion, et basculer de méthode à 24 mois créait
    un saut (73 € → 35 € en ajoutant un mois).
  Le quantile brut reste affiché en contrôle dans la vue JiyuFit.
- Prime pure = E[max(0, plancher − remplissage)] × payout plein, intégrée
  uniquement sous le plancher (Simpson) ; probabilité sous le plancher par la
  fonction de répartition normale. Vérifiées contre un Monte-Carlo et contre
  l'intégration complète dans les tests.
- Temps de calcul : ~6 ms par frappe (estimation), ~13 ms avec 24 mois, ~0,6 s
  pour un portefeuille de 50 activités.
- **La corrélation entre salles n'est pas modélisée**, hormis le stress « tout le
  réseau recule » du portefeuille. C'est le vrai risque de ruine (doctrine §6) :
  pour le mesurer, utiliser le notebook, sections XXX à XXXIII.
- Estimation indicative, pas une offre contractuelle.

Calibrage de référence (exemple Volt de la doctrine, conventions du notebook) :
payout plein 1 765 €, plancher 54 % (≈ 957 €), 10 % des mois sous le plancher,
prime pure ≈ 7,3 €/mois, prime commerciale ≈ 25,5 €/mois à γ = 3,5. Le prix
doctrinal de 89 €/mois correspond donc à un loss ratio d'environ 8 %.

## Tests

```bash
node --test outils/calculateur_garantie/tests/moteur.test.js
```

Le moteur de calcul est le bloc `<script id="moteur">` du fichier HTML ; les
tests l'en extraient, pour que la calculatrice reste un fichier unique.

Outre les cas nommés (Volt, historique de 12 mois signalé le 27/09/2026, studios
lyonnais), des tests de cohérence vérifient sur des activités tirées au hasard
(générateur déterministe) : relations comptables, seuil de rentabilité, somme du
portefeuille, monotonie (plus d'irrégularité ⇒ prix plus élevé), et convergence
vers le plancher théorique sur un long historique.
