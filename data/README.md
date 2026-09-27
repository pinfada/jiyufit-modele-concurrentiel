# Données empiriques

## Jeux publics documentés

`public/mindbody_2015_2018/` contient 14 trimestres d'abonnés professionnels
et de revenus, ainsi que les observations disponibles de consommateurs sur
24 mois. `public/classpass_public/` conserve 8 indicateurs publiés avec
leurs périodes, unités et qualifications (bornes, cumuls, flux).
Les sources sont liées ligne par ligne et les CSV contrôlés par SHA-256.
Ces données ne sont pas les anciens proxys d'attention ClassPass ci-dessous.
Elles ne permettent pas de calibrer une liquidité locale ; voir le
[rapport Mindbody/ClassPass](../docs/MINDBODY_CLASSPASS_ET_MODELE_BIFACE.md).

`modeles/recherches_liquidite.csv` est un gabarit vide pour les recherches
réelles, incluant celles sans résultat. Il ne contient aucune donnée client.

`public/basicfit_2020_2025/` contient 24 observations trimestrielles
d'abonnements publiés et leur provenance vérifiable. Ce jeu est distinct
des trois anciens proxys ci-dessous : il ne partage pas leur limite de source
inconnue. Voir [le test réalisé](../docs/VALIDATION_CONCURRENT_BASICFIT.md).

## Limite de provenance et portée (révision du 27 septembre 2026)

Ces fichiers ont été fournis par le porteur du projet. Le dépôt ne contient
pas la source primaire, les requêtes, la zone géographique exacte, la méthode
de normalisation ni les exports bruts permettant de reproduire leur collecte.
Leur authenticité et leur comparabilité externe ne sont donc pas vérifiées.
Ils restent utiles pour reproduire des calculs et explorer des hypothèses.
Aucun chiffre ni fichier source n'a été modifié lors de la correction.

Les assertions empiriques imposant un résultat favorable au modèle ont été
remplacées par des invariants techniques et des scores de comparaison. Une
actualisation des données peut changer les conclusions sans constituer un bug.
Les indications d'acteur « challenger/installé » ci-dessous sont les étiquettes
du jeu fourni, pas une vérification historique de leur position de marché.

Pour une nouvelle collecte, conserver : fournisseur et URL primaire, date
d'extraction, termes/identifiants recherchés, géographie, fréquence, unité,
normalisation commune aux acteurs, traitement des zéros et événements. Une
part dans un duel n'est pas une part de l'ensemble du marché.

## `basicfit_vs_fitnesspark_attention_mensuelle.csv`

- **Contenu** : attention mensuelle publique (proxy) pour le duel Basic-Fit (`acteur_J`, challenger) vs Fitness Park (`acteur_m`, installé) sur le marché fitness français.
- **Période** : 2022-01 → 2026-06 (54 mois), colonne `mois` au format `AAAA-MM`.
- **Provenance** : série fournie par le porteur du projet le 2026-07-30, au format « option 1 » du protocole de calibration (Section XXVI du notebook) — proxy d'attention publique, pas une mesure directe de capture de clients.
- **Usage** : Section XXVII du notebook (persistance descriptive `phi` par AR(1)-logit, backtest contre références naïves). Le fichier est figé pour rendre les calculs reproductibles.
- **Ne pas modifier en place** : toute mise à jour doit être un nouveau fichier versionné, afin de conserver les comparaisons avant/après.

## `duel_classpass_vs_gympass.csv`

- **Contenu** : attention mensuelle publique (proxy) pour le duel ClassPass (`acteur_J`) vs Gympass/Wellhub (`acteur_m`), agrégateurs fitness internationaux.
- **Période** : 2017-01 → 2026-06 (114 mois). Inclut la période COVID ; une rupture éventuelle n'est pas automatiquement neutralisée par le modèle.
- **Provenance** : série fournie par le porteur du projet le 2026-07-30, même format « option 1 » que ci-dessus.
- **Usage** : Section XXIX (hétérogénéité des persistances, pooling conditionnel et prévision).

## `duel_gymlib_vs_urbansportsclub.csv`

- **Contenu** : attention mensuelle publique (proxy) pour le duel Gymlib (`acteur_J`) vs Urban Sports Club (`acteur_m`), agrégateurs FR/EU — le marché le plus proche de JiyuFit.
- **Période** : 2017-01 → 2026-06 (114 mois). Couvre le choc COVID.
- **Provenance** : série fournie par le porteur du projet le 2026-07-30, même format.
- **Usage** : Section XXIX. L'IV est incertain ; le pooling impose un coefficient commun sans démontrer une constante sectorielle. Le coefficient estimé est une persistance `phi`, pas automatiquement le `r` structurel.

Règle commune : ces fichiers sont figés ; les résultats dépendent de leur contenu exact. Une source mieux documentée doit faire l'objet d'un nouveau jeu versionné.
