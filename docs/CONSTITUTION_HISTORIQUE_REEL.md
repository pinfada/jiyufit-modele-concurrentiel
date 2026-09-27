# Constitution de l'historique : extraction et qualification

Investigation du 27 septembre 2026. Résultat : un instantané de la base locale
a été constitué, mais son origine commerciale réelle n'est pas établie. Il ne
constitue pas l'historique financier réel demandé et n'alimente pas la calibration.

## Sources vérifiées

| Source | Résultat |
| --- | --- |
| Fichiers des dépôts JiyuFit et modèle | Pas d'export financier réel identifié ; CSV concurrentiels déjà connus et exemples |
| Sauvegardes dans `jiyufit/tmp` | Aucun fichier SQL, dump, backup, Parquet ou XLSX retrouvé par la recherche |
| Configuration locale de développement | Connexion de développement ; identifiants Stripe de test ou exemples, pas de source Stripe live identifiée |
| Google Drive connecté | Recherches « Jiyufit », « comptabilité » et « Stripe » sans résultat retourné ; cela ne prouve pas l'absence de fichiers ailleurs |
| PostgreSQL Windows, port 5432, `jiyufit_development` | Aucune des colonnes recherchées des cinq tables métier dans le schéma public |
| PostgreSQL local, port 5434, `jiyufit_development` | Tables métier présentes, extraction agrégée réussie en lecture seule |

La base de développement du port 5434 n'avait pas été identifiée lors du
premier inventaire Docker. La recherche a donc été étendue au service Windows
et aux connexions locales configurées. Aucun compte de production n'a été
modifié et aucune donnée nominative n'a été exportée.

## Instantané obtenu

Fichiers locaux ignorés par Git :

- `artifacts/historique-local/instantane-2026-09-27/extraction.json`
- `artifacts/historique-local/instantane-2026-09-27/paiements-mensuels-non-qualifies.csv`
- `artifacts/historique-local/instantane-2026-09-27/empreintes.json`

Les agrégats observés dans cette base sont : 14 paiements, 31 réservations,
13 lieux, aucune commission enregistrée et aucune présence confirmée.
Tous les paiements retrouvés sont datés de septembre 2026. Selon l'énumération
actuelle de `Payment`, six sont en attente, six en traitement, un attend un
moyen de paiement et un est marqué réussi. Ce dernier représente un montant
brut de 3 000 centimes et des frais de service de 300 centimes. Ce ne sont pas
des revenus réels JiyuFit certifiés : l'origine du paiement, son mode live/test
et son rapprochement chez le prestataire ne sont pas établis.

Un comptage complémentaire a repéré des marqueurs de test dans 18 des 30
comptes. Ce signal ne permet pas de classer individuellement les paiements,
mais empêche de supposer que toute la base est un historique de production.

## Extraction reproductible

```powershell
.\.venv\Scripts\python.exe -X utf8 outils/extraire_historique_postgres.py --host localhost --port 5434 --database jiyufit_development --sortie artifacts/historique-local/nouvel-instantane
```

Le client `psql` est recherché dans PATH puis dans l'installation PostgreSQL
Windows ; `--psql` permet de préciser son chemin. L'authentification réutilise
`PGUSER`/`PGPASSWORD` ou `DATABASE_USER`/`DATABASE_PASSWORD` dans l'environnement,
sans mettre le mot de passe dans la commande ni les rapports. Le code utilise
une transaction cohérente `REPEATABLE READ READ ONLY`, un délai maximal,
l'arrêt sur erreur et un nouveau dossier par instantané. Les résultats sont
agrégés, horodatés et accompagnés d'empreintes SHA-256. Le code 0 indique une
extraction réussie, pas une certification économique.

Le SQL ne somme pas paiements et commissions, ne traite pas tous les statuts
comme encaissés et ne transforme pas les mois absents en zéros. Il conserve
les devises et signale les champs manquants. Aucun journal de gestion
« observé » n'est produit automatiquement à partir de ces données non qualifiées.

## Élément externe désormais nécessaire

La source effective des opérations réelles n'a pas été identifiée : base de
production, compte Stripe actif ou exports de gestion. Une question a été
adressée au porteur pour en préciser l'emplacement, sans transmettre de secret
dans la conversation. Si JiyuFit n'a pas encore d'activité réelle, il n'existe
pas d'historique commercial propre à reconstituer ; les données de marché et
simulations doivent garder leur statut distinct.

Une fois une source réelle localisée, sa qualification exige notamment le
rapprochement des paiements live, remboursements, frais et commissions, puis
l'ajout des dépenses d'acquisition et autres coûts variables. L'extracteur
livré fournit les agrégats d'audit de la base ; il ne prétend pas reconstruire
des coûts absents ou certifier l'exhaustivité de la comptabilité.
