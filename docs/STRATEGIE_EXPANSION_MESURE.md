# JiyuFit — Stratégie d'expansion et dispositif de mesure

Stratégie opérationnelle dérivée du modèle concurrentiel **validé empiriquement**
(notebook, sections XXVII–XXIX : 3 duels réels, 282 mois). Chaque prescription
cite la section qui la fonde. Ce document distingue explicitement ce qui est
*établi par les données* de ce qui est *inféré de la mécanique du modèle*.

## 1. Fondements

| Fait | Statut | Source |
|---|---|---|
| La capture suit une dynamique d'accumulation AR(1)-logit, R² = 0,84 sur duel réel | **établi** | XXVII |
| La sensibilité `r` est une quasi-constante sectorielle ≈ 0,93 < 1 (P(r≥1) < 10⁻³) | **établi** (3 duels poolés) | XXIX |
| Régime stable : un challenger peut monter ; le plateau d'arrivée est prédictible à ±2,5 pts | **établi** | XXVII–XXIX |
| Les agrégateurs comparables convergent vers la parité ~50/50 ; seule l'asymétrie durable `c` déplace le plateau | **établi** (2 duels d'agrégateurs) | XXIX |
| Le secteur opère à <10 % de la frontière `r = 1` (guerre d'usure destructrice au-delà) | **établi** | XXVIII–XXIX, XVII–XXIII |
| Le capital de réseau et la valeur biface sont locaux → densité par ville = levier de `c` | *inféré* de la structure du modèle | III, VII, XXVI |
| Expansion séquentielle > simultanée (l'effort divisé affaiblit chaque duel) | *inféré* | V, XXII |

## 2. La stratégie en quatre phases

### Phase 0 — Instrumentation (avant le premier client)

1. Pour chaque ville visée : définir la **zone** et le **rival de référence**
   (l'acteur qui conteste les mêmes clients).
2. Mettre en place la collecte mensuelle au format standard (un CSV par ville,
   `data/README.md`) : `mois, acteur_J, acteur_m` — idéalement clients captés,
   à défaut proxy d'attention.
3. Collecter aussi, pour la calibration complète (section XXVI) : CAC, churn
   mensuel par segment, dépense d'acquisition, partenaires actifs.

> Chaque mois de collecte raccourcit le délai avant que la trajectoire soit
> évaluable. La collecte est le premier investissement stratégique, pas une
> tâche de reporting.

### Phase 1 — Ville pilote : la densité avant la demande

- **Construire l'offre d'abord** : atteindre un seuil de densité de partenaires
  (salles + hôtels) *avant* d'engager le marketing lourd. La valeur biface est
  locale : un effort d'acquisition sur une offre creuse achète des membres qui
  churnent (section III).
- Fixer le seuil de densité par rapport au **rival de référence** (l'objectif
  n'est pas un chiffre absolu mais la comparaison : l'offre JiyuFit doit être
  crédible face à la sienne dans la zone).
- **Gate G1 (traction), vers le mois 6–8** : part de capture en hausse et
  plateau prédit au-dessus du point de départ (mesuré par l'outil, §4). G1
  rouge → corriger l'offre/le positionnement avant tout budget supplémentaire.

### Phase 2 — Conduite du duel : investir en `c`, jamais en escalade

- La parité est l'attracteur par défaut du marché des agrégateurs (XXIX). Pour
  un plateau > 50 %, il faut une asymétrie durable `c` : densité d'offre,
  sport sans abonnement, gouvernance — ce que le rival ne copie pas en un
  trimestre.
- **Interdits** (ils poussent `r` vers la zone destructrice, XXVIII–XXIX) :
  surenchère publicitaire frontale, promotions en miroir du rival, guerre de
  prix. Le secteur est à <10 % de la frontière ; au-delà, même le gagnant ne
  gagne rien (XXIII : paiement espéré nul).
- Si le **plateau prédit < 50 %** : le déficit est dans `c`. Le corriger DANS
  la ville pilote — l'étendre à d'autres villes répliquerait le déficit.

### Phase 3 — Expansion séquentielle, ville par ville

- **Gate G2 (expansion)** : ouvrir la ville N+1 seulement quand la ville N est
  au plateau prédit (ou sur trajectoire avec < 6 mois restants) — verdict
  rendu par l'outil (§4).
- Répliquer le playbook (seuils de densité, séquence offre → demande) ; le
  temps de convergence observé est de l'ordre de 12–30 mois par ville
  (constante de temps du secteur : 1/(1−r) ≈ 14 mois).
- Ne jamais avoir plus de villes « en conquête » que ce que l'effort marketing
  permet de soutenir *sans diluer les duels en cours* (V, XXII).

## 3. Règles de conduite permanentes

1. **`c` avant `x`** : tout euro qui augmente la différenciation durable vaut
   plus qu'un euro d'effort marketing brut (la loi d'asymétrie XVIII :
   `P* = κ/(1+κ)`).
2. **Surveiller `r`** en continu (outil, §4) : c'est la jauge de risque du
   marché entier. `r` local IV ≥ 1 = signal d'entrée en zone instable →
   désescalader, pas surenchérir.
3. **Mettre à jour le `r` sectoriel** ~1×/an en rafraîchissant les séries des
   duels de référence (`data/`) et en réexécutant la section XXIX.
4. **Ne pas sur-réagir au mois-à-mois** : le modèle (et les données) montrent
   que le bruit mensuel est fort et saisonnier (creux d'été, XXVIII). La
   maille de décision est le trimestre.

## 4. Le dispositif de mesure

### 4.1 L'outil : `outils/suivi_ville.py`

```bash
python outils/suivi_ville.py data/ville_lyon.csv --png rapport_lyon.png
```

Entrée : le CSV mensuel de la ville. Sortie :

| Sortie | Interprétation | Décision associée |
|---|---|---|
| `ln(c)` estimé ± IC | asymétrie de JiyuFit face au rival | `ln(c) > 0` = différenciation qui paie |
| **Plateau prédit** + bande | point d'arrivée de la trajectoire | plateau < 50 % → corriger `c` avant d'étendre |
| Écart récent obs. − prédit | la ville suit-elle sa trajectoire ? | écart persistant → chercher la cause (offre, rival, données) |
| Temps restant au plateau | horizon de convergence | planification de la ville suivante |
| **Gate G1 / G2** | verdicts automatiques | cf. phases 1 et 3 |
| `r` local (OLS + IV, si ≥ 30 mois) | dérive de sensibilité | IV ≥ 1 → alerte désescalade |

L'outil refuse de diagnostiquer sous 8 mois de données (collecte d'abord) et
élargit honnêtement ses bandes d'incertitude sur séries courtes.

### 4.2 Tableau de bord mensuel par ville

| KPI | Définition | Cadence | Cible / seuil | Fondement |
|---|---|---|---|---|
| Part de capture | clients gagnés J / (J + rival) | mensuel | trajectoire prédite ± 5 pts | XXVII |
| Densité d'offre relative | partenaires actifs J / rival, même zone | mensuel | ≥ 1 avant marketing lourd | III (inféré) |
| Plateau prédit | sortie outil | trimestriel | > 50 % | XXIX |
| Churn mensuel (χ) | résiliations / base | mensuel | intrant calibration | XXVI |
| CAC / dépense d'acquisition | coût par client capté | mensuel | intrant calibration (effort x) | XXVI |
| `r` local / sectoriel | sortie outil + refresh XXIX | trim. / annuel | IV < 1 | XXVIII–XXIX |

### 4.3 Revue trimestrielle (rituel)

1. Ré-exécuter l'outil sur chaque ville active ; archiver les rapports.
2. Comparer trajectoire observée vs prédite : un écart > 5 pts sur 2 trimestres
   consécutifs invalide localement le diagnostic → réestimer `c`, vérifier le
   rival de référence et la qualité des données.
3. Statuer sur les gates (G1/G2) — les verdicts de l'outil se discutent, ne
   s'ignorent pas silencieusement.
4. Une fois ≥ 18 mois de données propres : basculer l'estimation de `r` du
   sectoriel vers les données JiyuFit (protocole complet, section XXVI).

## 5. Signaux d'alerte

| Signal | Lecture | Réaction |
|---|---|---|
| `r` IV local ≥ 1 | marché local en zone instable possible | désescalader l'intensité marketing, renforcer `c` |
| Plateau prédit < 50 % et stable | déficit structurel de différenciation | gel de l'expansion, chantier `c` |
| Écart trajectoire persistant (> 2 trim.) | modèle localement invalide ou données faussées | audit données + rival de référence |
| Part qui monte mais churn qui monte aussi | capture sans rétention (hors modèle de capture) | traiter la rétention avant de lire la part |

## 6. Limites de ce document

- La validation empirique porte sur des **proxys d'attention**, pas sur la
  capture réelle de clients — les données propres de JiyuFit lèveront cette
  limite (et c'est le but de la Phase 0).
- Le choix salles vs hôtels comme mix de densité est **hors du modèle** : à
  arbitrer sur le terrain comme deux variantes de `c` à comparer.
- La prescription « séquentiel plutôt que simultané » est une inférence de la
  mécanique du modèle (effort divisé = duels affaiblis), pas un résultat
  testé : la première paire de villes fournira le test réel.
