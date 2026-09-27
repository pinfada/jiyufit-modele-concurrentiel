-- Agrégats uniquement : aucun nom, e-mail ou identifiant de paiement exporté.
-- L'origine réelle n'est PAS déduite du nom de la base ni du statut du paiement.
BEGIN TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY;
SET LOCAL statement_timeout = '30s';
SELECT json_build_object(
  'lecture_seule', current_setting('transaction_read_only'),
  'date_extraction_utc', to_char(current_timestamp AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"'),
  'compteurs', json_build_object(
    'paiements', (SELECT count(*) FROM payments),
    'reservations', (SELECT count(*) FROM reservations),
    'presences_confirmees', (SELECT count(*) FROM reservations WHERE presence_confirmed),
    'commissions', (SELECT count(*) FROM commission_transactions),
    'lieux', (SELECT count(*) FROM gymhouses)
  ),
  'paiements_par_mois_creation', COALESCE((SELECT json_agg(t) FROM (
    SELECT to_char(created_at, 'YYYY-MM') AS mois,
           status AS statut_application, total_currency AS devise,
           count(*) AS mouvements,
           sum(total_cents) AS total_centimes,
           sum(service_fee_cents) AS frais_service_centimes,
           count(*) FILTER (WHERE total_cents IS NULL) AS totaux_absents,
           count(*) FILTER (WHERE service_fee_cents IS NULL) AS frais_service_absents,
           count(*) FILTER (WHERE processing_fee_cents IS NULL) AS frais_traitement_absents,
           count(*) FILTER (WHERE confirmed_at IS NULL) AS confirmations_absentes
    FROM payments GROUP BY 1, 2, 3 ORDER BY 1, 2, 3
  ) t), '[]'::json),
  'commissions_par_mois_traitement', COALESCE((SELECT json_agg(t) FROM (
    SELECT to_char(processed_at, 'YYYY-MM') AS mois, status AS statut_application,
           count(*) AS mouvements, sum(commission_amount_cents) AS commissions_centimes
    FROM commission_transactions GROUP BY 1, 2 ORDER BY 1, 2
  ) t), '[]'::json)
);
ROLLBACK;
