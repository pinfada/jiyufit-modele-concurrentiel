# Sources retrouvées et données restant à obtenir

Vérification du 27 septembre 2026. Cette recherche distingue une source
identifiée, un accès testé et un historique réellement obtenu.

| Besoin | Source | Vérification et limites |
| --- | --- | --- |
| Offre sportive locale | [Data ES, ministère des Sports](https://www.data.gouv.fr/datasets/data-es-recensement-des-equipements-sportifs-et-lieux-de-pratique-complet-1) | API publique interrogée avec succès ; métadonnées téléchargées dans `artifacts/sources/data_es_metadata.json`. 334 430 enregistrements annoncés à l'extraction. Champs commune, installation, équipement, type et activité disponibles. Un équipement n'est ni un établissement unique ni un partenaire JiyuFit actif. |
| Taille et évolution des concurrents | [Rapport annuel Basic-Fit 2025](https://annualreport.basic-fit.com/2025/mbr/business-and-financial-review/) | Rapport consulté : revenus, clubs et adhérents. Fréquence et périmètre géographique à conserver ; les acquisitions modifient le périmètre. Ces agrégats ne remplacent pas une série mensuelle française de clients. |
| Identité des marques | [Site officiel EGYM Wellpass](https://fr.egym-wellpass.com/fr-fr) | Le site Gymlib redirige vers Wellpass et annonce le changement de nom. Date et traitement de cette rupture dans les anciens CSV non établis. Une recherche limitée à l'ancien nom pourrait confondre changement de marque et recul commercial. |
| Attention publique reproductible | [Export Google Trends](https://support.google.com/trends/answer/4365538?hl=fr) | Procédure officielle identifiée. Aucun nouvel export obtenu ici. Comparer les acteurs dans une même requête, avec géographie, période et normalisation documentées. Aucun élément retrouvé n'établit que les CSV existants proviennent de Google Trends. |
| Revenus et paiements JiyuFit | `../../jiyufit/app/services/analytics/revenue_analytics_service.rb` | Code lu : requêtes sur `CommissionTransaction` et `Payment`, avec périodes configurables. Ce code n'est pas un export de transactions réelles. La marge contributive demande aussi les coûts effectivement supportés ; le service contient notamment des frais de paiement forfaitaires. |
| Activité et partenaires JiyuFit | `../../jiyufit/app/services/metrics/unified_metrics_service.rb` | Code lu : comptes, réservations, paiements et lieux ; export Prometheus. `User.count` n'est pas un nombre de clients actifs et `Reservation.count` ne prouve pas une séance réalisée. L'historique dépend de la base et de la conservation des métriques. |
| Rétention et acquisition JiyuFit | `../../jiyufit/app/services/business_metrics_service.rb`, `../../jiyufit/config/marketing_budget.yml` | Méthodes de rétention repérées ; le collecteur CAC référence un fichier de budget marketing. Valeurs réelles et définitions des cohortes non auditées ; le budget configuré ne prouve pas une dépense réalisée. |

## Accès public effectivement testé

Métadonnées JSON :
<https://equipements.sports.gouv.fr/api/explore/v2.1/catalog/datasets/data-es>

Réponse obtenue sans authentification, licence ouverte 2.0, mise à jour annoncée
le 27 septembre 2026. Seules les métadonnées ont été enregistrées à ce stade,
pas l'intégralité des équipements. Pour une extraction territoriale, choisir
la commune ou le bassin, filtrer les activités pertinentes et dédupliquer les
installations avant toute comparaison avec les lieux partenaires.

## Recherche locale et prochaines données nécessaires

La recherche de fichiers CSV, SQLite, dumps et Parquet dans les deux dépôts
voisins `jiyufit` et `jiyufit-modele-concurrentiel` n'a pas retrouvé d'export
historique de production exploitable. Elle a retrouvé les trois CSV déjà
connus et un fichier de studios présenté comme exemple dans un calculateur.
Cette recherche ne démontre pas l'absence de données dans la base du service
ou dans Grafana. Aucune connexion à la production n'a été effectuée.

L'extraction interne utile doit produire, par mois et territoire : clients
ayant réellement consommé, séances réalisées, lieux actifs, revenus nets de
remboursements, coûts variables et dépenses d'acquisition réalisées. La
rétention demande des cohortes et des retours observés, avec exclusion des
comptes de test. Les coûts et capacités non enregistrés doivent être mesurés.

L'historique des concurrents doit utiliser les mêmes unités, dates et
périmètres. Sans dénominateur concurrent comparable, l'activité interne ne
suffit pas à reconstruire une part de marché. Enfin, identifier l'effet causal
des dépenses ou des effets de réseau exige des variations observées et une
stratégie d'identification ; des chiffres publics isolés ne suffisent pas.

Les données existantes et les coefficients du notebook n'ont pas été modifiés
sur la seule base de ces sources : elles documentent des compléments possibles,
elles ne constituent pas encore une nouvelle calibration validée.
