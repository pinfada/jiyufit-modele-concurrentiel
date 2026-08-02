# JiyuFit — Modèle de capture concurrentielle à capital de réseau

Modèle mathématique et simulation Python de la capture concurrentielle sur un marché à capital de réseau (effets de réseau), appliqué au cas JiyuFit. Le dépôt réunit les équations du modèle, leur dérivation vérifiée, une implémentation testée, la caractérisation complète des équilibres (purs **et** mixtes), et un protocole de calibration.

## Contenu du dépôt

- `jiyufit_modele_concurrentiel.ipynb` — notebook principal (sections I à XXIX, voir plan ci-dessous).
- `data/` — données empiriques figées (provenance documentée dans `data/README.md`), utilisées par les sections XXVII–XXIX.
- `docs/STRATEGIE_EXPANSION_MESURE.md` — stratégie opérationnelle dérivée du modèle validé (expansion séquentielle à densité locale) et dispositif de mesure (KPI, gates, rituel trimestriel).
- `outils/suivi_ville.py` — outil de pilotage : lit le CSV mensuel d'une ville et rend le diagnostic (plateau prédit, position sur trajectoire, gates G1/G2, alerte sur `r`).
- `requirements.txt` — dépendances Python.
- `.github/workflows/notebook-tests.yml` — CI : exécution complète du notebook (toutes les assertions) à chaque push.
- `README.md` — ce document.

## Aperçu du modèle

Deux acteurs (puis $n$, section XXIV) se disputent des segments de clientèle court terme `s` et long terme `l` sous contrainte de capacité (`K_s`, `K_l`). La capture suit un contest de Tullock de sensibilité `r > 0` sur les efforts *effectifs* `e = k·x` (capital de réseau × effort brut), la valeur capturable `V` est biface et endogène, et le capital de réseau `k(t)` s'accumule avec la part de marché et l'usage.

Fonctions principales :

- `capture_probability(...)` — probabilité de capture (Tullock généralisé).
- `best_response(k_J, e_m, V_J, r)` — effort optimal : forme fermée pour `r = 1`, résolution numérique (brentq sur la CPO, comparaison globale avec la solution de coin) pour tout `r > 0`.
- `simulate(...)` — duel dynamique symétrique : rival réactif, capital endogène, populations bifaces saturées.
- `find_nash_equilibrium(...)` / `find_nash_equilibrium_validated(...)` — équilibres de Nash par recherche directe, certifiés par absence de déviation profitable.
- `symmetric_mixed_equilibrium(...)` — équilibre en stratégies mixtes (fictitious play + certification par exploitabilité) pour le régime `r > r*`.

## Plan du notebook

| Sections | Contenu |
|---|---|
| I–IX | Équations du modèle : capture, valeur biface, gain espéré, meilleure réponse, dynamique des populations (saturation logistique), accumulation du capital de réseau, conditions de bascule et de survie. |
| X | Vérification algébrique des dérivations (CPO, concavité, limites asymptotiques, fermeture de Tullock) et points de vigilance de modélisation. |
| XI–XII | Implémentation NumPy/SciPy, simulation du duel, **tests automatiques par `assert`**. |
| XIII–XVI | Équilibre de Nash simultané par recherche directe (indépendante de la dynamique), stabilité locale (jacobien / rayon spectral), cohérence régime permanent de `simulate` ↔ Nash, validation stricte par absence de déviation profitable (rejet prouvé du profil (0,0)). |
| XVII–XIX | Existence de l'équilibre pur et seuil critique `r* = 2` (symétrique) ; cas asymétrique : forme fermée, loi d'asymétrie radicale `P_J* = κ/(1+κ)` ; déplacement du seuil `r*(κ)` vers 1 quand l'asymétrie croît. |
| XX–XXII | Dynamique vs équilibre (coïncidence exacte au régime linéaire `r = 1`, divergence pour `r > 1`), visualisation des trajectoires au seuil, fenêtre de rattrapage (désavantage initial maximal réversible). |
| XXIII | **Stratégies mixtes pour `r > r*`** : équilibre mixte numérique certifié ε-Nash par exploitabilité, validé contre Baye–Kovenock–de Vries 1994 (paiement espéré nul, dissipation totale de la rente). |
| XXIV | **Extension à `n` concurrents** : forme fermée `x*(n) = rV(n-1)/n²`, condition d'existence `r ≤ n/(n-1)`, dissipation asymptotique `rV`. |
| XXV | **Analyse de sensibilité OAT ±30 %** (figure tornado) : `r` domine, puis `δ_k` et `χ_s` — priorisation de la calibration. |
| XXVI | **Protocole de calibration au cas JiyuFit** : correspondance paramètre ↔ observable métier, démarche d'estimation, estimation de `r` (le point dur), domaine de validité. |
| XXVII | **Épreuve empirique sur données réelles** (Basic-Fit vs Fitness Park, 54 mois) : la réduction exacte du modèle en AR(1) sur le logit de la part explique R² ≈ 0,84 d'un duel réel ; `r` estimé ≈ 0,81, IC95 [0,72 ; 0,91] — régime stable identifié sur toutes les fenêtres ; le plateau prédit par la dynamique (~0,22) coïncide avec le plateau observé (~0,24) ; backtest honnête contre trois références naïves (bat la diffusion logistique partout, la persistance sur 1 fenêtre sur 3). |
| XXVIII | **Améliorations issues de l'épreuve** : intégration de la saisonnalité (creux d'été) — RMSE de backtest réduite sur toutes les fenêtres, jeu au moins égal avec la persistance sur 2/3 ; correction du biais d'atténuation dû au bruit du proxy (IV + série lissée) — `r` vraisemblable ≈ 0,92 plutôt que 0,81, régime stable maintenu (P(r ≥ 1) ≈ 0,001 par bootstrap par blocs) mais marge au seuil critique plus mince. |
| XXIX | **Stabilité inter-marchés de `r`** sur trois duels réels (+ ClassPass/Gympass et Gymlib/Urban Sports Club, 114 mois chacun) : la dispersion des `r` OLS (0,53–0,81) suit le niveau de bruit des séries (atténuation), les `r` corrigés se concentrent (0,92–1,03) ; estimation poolée `r ≈ 0,93 < 1` (P(r ≥ 1) < 10⁻³ sur 282 mois) — compatible avec une constante sectorielle, proche de la frontière ; plateaux prédits ≈ observés (± 2,5 pts) sur les trois duels ; le modèle bat la persistance de 55 % là où la trajectoire bouge encore (Gymlib/USC) ; `c` varie par marché (parité pour les agrégateurs, ~25/75 pour les salles), `r` non. |

## Domaine de validité — résumé

- **`r < r*(κ)`** : équilibre pur, dynamique adaptative fiable, conclusions des sections XX–XXII applicables. C'est le régime pour lequel JiyuFit est calibré.
- **`r > r*(κ)`** : aucun équilibre pur ; régime en stratégies mixtes (section XXIII) où le paiement espéré est nul — régime à **éviter**, pas à optimiser.
- La frontière `r*` dépend de l'asymétrie `κ = k_J V_J / (k_m V_m)` (section XIX) et du nombre de concurrents `n` (section XXIV : `r ≤ n/(n-1)`).

## Tests et intégration continue

Le notebook est auto-vérifiant : chaque section quantitative se termine par des assertions (normalisation des probabilités, conditions du premier ordre, non-régression analytique/numérique, certification des équilibres par déviation, oracles de littérature pour le régime mixte, bornes des populations). La CI GitHub Actions ré-exécute le notebook complet à chaque push et échoue si une seule assertion casse.

Exécution locale équivalente :

```bash
pip install -r requirements.txt jupyter
jupyter nbconvert --to notebook --execute jiyufit_modele_concurrentiel.ipynb --output /tmp/executed.ipynb
```

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

Ouvrir `jiyufit_modele_concurrentiel.ipynb` dans Jupyter ou Google Colab, puis exécuter toutes les cellules dans l'ordre. Toutes les sections doivent se terminer sans erreur d'assertion.

## Limites et travaux restants

- **Calibration** : les sections XXVII–XXIX corroborent la brique dynamique sur trois duels réels du secteur fitness (via des proxys d'attention, pas des mesures directes de capture), avec un `r` sectoriel poolé ≈ 0,93 — régime stable mais proche de la frontière `r = 1`, en particulier pour le marché des agrégateurs (celui de JiyuFit). Les paramètres propres à JiyuFit restent à estimer selon le protocole de la section XXVI. Les seuils critiques (`r* = 2`, `r*(κ)`) ne sont pas testés empiriquement — aucun des marchés observés n'a visité le régime instable.
- **Dynamique à `n` joueurs** : l'extension `n > 2` est établie au niveau statique (équilibre, section XXIV) ; `simulate(...)` reste un duel.
- **Stochasticité** : la dynamique est déterministe ; pas de chocs aléatoires ni d'intervalles de confiance sur les trajectoires.
- **Stratégies mixtes asymétriques** : la section XXIII couvre le cas symétrique (le seul pour lequel la littérature fournit un oracle exact) ; le cas mixte asymétrique reste ouvert.
