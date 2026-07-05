# JiyuFit — Modèle de capture concurrentielle à capital de réseau

Modèle mathématique et simulation Python de la capture concurrentielle sur un marché à capital de réseau (effets de réseau), appliqué au cas JiyuFit. Le dépôt réunit les équations du modèle, leur dérivation, une implémentation vérifiée et une batterie de tests automatiques.

## Contenu du dépôt

- `jiyufit_modele_concurrentiel.ipynb` — notebook principal : équations, meilleure réponse, probabilité de capture, dynamique de simulation et tests automatiques (section XII).
- `requirements.txt` — dépendances Python.
- `README.md` — ce document.

## Aperçu du modèle

Le modèle décrit deux acteurs se disputant des segments de clientèle (court terme `s` et long terme `l`) sous contrainte de capacité (`K_s`, `K_l`). La probabilité de capture suit une forme à rendement `r > 0`, et chaque acteur choisit son effort marketing via une fonction de meilleure réponse :

- `capture_probability(...)` — probabilité de capturer un client selon les efforts relatifs et le paramètre de rendement `r`.
- `best_response(k_J, e_m, V_J, r=1.0)` — effort optimal : formule fermée pour `r = 1`, résolution numérique (racine de la condition du premier ordre via `scipy.optimize.brentq`) pour tout `r > 0`.
- `simulate(...)` — dynamique adaptative pas à pas des populations et des efforts.

## Tests automatiques (section XII)

Le notebook inclut une section de tests par `assert` qui vérifient notamment :

- normalisation des probabilités et bornes `0 <= P <= 1` ;
- respect du domaine des fonctions (défense contre `k_J <= 0`, etc.) ;
- optimalité : la meilleure réponse satisfait bien la condition du premier ordre (test FOC pour `r = 1` et pour `r` général) ;
- non-régression entre la branche analytique et la branche numérique en `r = 1` ;
- non-négativité des populations et absence de valeurs non finies dans la simulation.

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

Ouvrir `jiyufit_modele_concurrentiel.ipynb` dans Jupyter ou Google Colab, puis exécuter toutes les cellules. La section XII doit se terminer sans erreur d'assertion.

## Avertissement méthodologique

La simulation implémente une dynamique adaptative (chaque acteur joue itérativement sa meilleure réponse). Cette dynamique ne coïncide pas nécessairement avec un équilibre de Nash simultané : les points fixes de la dynamique, leur existence et leur stabilité font l'objet des développements à venir.
