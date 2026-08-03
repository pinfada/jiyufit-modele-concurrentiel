# Données empiriques

## `basicfit_vs_fitnesspark_attention_mensuelle.csv`

- **Contenu** : attention mensuelle publique (proxy) pour le duel Basic-Fit (`acteur_J`, challenger) vs Fitness Park (`acteur_m`, installé) sur le marché fitness français.
- **Période** : 2022-01 → 2026-06 (54 mois), colonne `mois` au format `AAAA-MM`.
- **Provenance** : série fournie par le porteur du projet le 2026-07-30, au format « option 1 » du protocole de calibration (Section XXVI du notebook) — proxy d'attention publique, pas une mesure directe de capture de clients.
- **Usage** : Section XXVII du notebook (épreuve empirique : estimation de la sensibilité `r` par AR(1)-logit, backtest contre références naïves). Le fichier est figé dans le dépôt pour que le notebook — et donc la CI — soit déterministe.
- **Ne pas modifier en place** : toute mise à jour de la série doit être un nouveau fichier versionné (les assertions de non-régression de la Section XXVII sont liées à ce contenu exact).

## `duel_classpass_vs_gympass.csv`

- **Contenu** : attention mensuelle publique (proxy) pour le duel ClassPass (`acteur_J`) vs Gympass/Wellhub (`acteur_m`), agrégateurs fitness internationaux.
- **Période** : 2017-01 → 2026-06 (114 mois). Couvre le choc COVID (mars–mai 2020), neutralisé par dummy dans la Section XXIX.
- **Provenance** : série fournie par le porteur du projet le 2026-07-30, même format « option 1 » que ci-dessus.
- **Usage** : Section XXIX (stabilité inter-marchés de `r`).

## `duel_gymlib_vs_urbansportsclub.csv`

- **Contenu** : attention mensuelle publique (proxy) pour le duel Gymlib (`acteur_J`) vs Urban Sports Club (`acteur_m`), agrégateurs FR/EU — le marché le plus proche de JiyuFit.
- **Période** : 2017-01 → 2026-06 (114 mois). Couvre le choc COVID.
- **Provenance** : série fournie par le porteur du projet le 2026-07-30, même format.
- **Usage** : Section XXIX. Série la plus bruitée des trois (volumes faibles) : `r` n'y est pas identifiable isolément, seulement en poolé — voir le texte de la section.

Règle commune : ces fichiers sont figés ; les assertions de non-régression des Sections XXVII–XXIX dépendent de leur contenu exact.
