import csv
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys

from outils.historique_comptable import CATEGORIES, construire_historique
from outils.qualite import auditer_source, empreinte


class LedgerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.folder = Path(self.tmp.name)
        self.journal = self.folder/'journal.csv'
        self.coverage = self.folder/'couverture.csv'
        self.rows = [dict(id=str(i), date='2025-01-15', territoire='ville', categorie=category,
                          montant_centimes=str(value), devise='EUR', reference='piece-'+str(i))
                     for i, (category, value) in enumerate(zip(CATEGORIES, (10001, 101, 200, 300)))]
        self.covers = [dict(mois='2025-01', territoire='ville', categorie=r['categorie'],
                            statut='observe', total_controle_centimes=r['montant_centimes'],
                            reference='controle-independant') for r in self.rows]

    def run_report(self):
        for path, rows, columns in (
            (self.journal, self.rows, ['id', 'date', 'territoire', 'categorie', 'montant_centimes', 'devise', 'reference']),
            (self.coverage, self.covers, ['mois', 'territoire', 'categorie', 'statut', 'total_controle_centimes', 'reference'])):
            with path.open('w', encoding='utf-8', newline='') as stream:
                writer = csv.DictWriter(stream, fieldnames=columns)
                writer.writeheader(); writer.writerows(rows)
        return construire_historique(self.journal, self.coverage)

    def test_exact_margin_includes_refunds_costs_and_acquisition(self):
        report = self.run_report()
        row = report['historique'][0]
        self.assertTrue(row['rapproche'])
        self.assertEqual(row['marge_apres_acquisition_centimes'], 9400)
        self.assertEqual(report['journal_sha256'], empreinte(self.journal))

    def test_duplicate_movement_rejected(self):
        self.rows.append(self.rows[0].copy())
        with self.assertRaisesRegex(ValueError, 'double'):
            self.run_report()

    def test_control_discrepancy_prevents_margin(self):
        self.covers[0]['total_controle_centimes'] = '10002'
        self.assertIsNone(self.run_report()['historique'][0]['marge_apres_acquisition_centimes'])

    def test_estimated_cost_prevents_margin(self):
        self.covers[2]['statut'] = 'estime'
        self.assertIsNone(self.run_report()['historique'][0]['marge_apres_acquisition_centimes'])

    def test_missing_month_is_not_zero(self):
        self.covers += [dict(r, mois='2025-03', total_controle_centimes='0') for r in self.covers]
        rows = self.run_report()['historique']
        self.assertEqual([r['mois'] for r in rows], ['2025-01', '2025-02', '2025-03'])
        self.assertIsNone(rows[1]['marge_apres_acquisition_centimes'])
        self.assertEqual(rows[2]['marge_apres_acquisition_centimes'], 0)

    def test_empty_journal_can_be_observed_zero_only_with_explicit_controls(self):
        self.rows = []
        for row in self.covers:
            row['total_controle_centimes'] = '0'
        self.assertEqual(self.run_report()['historique'][0]['marge_apres_acquisition_centimes'], 0)
        self.covers[0]['total_controle_centimes'] = ''
        self.assertIsNone(self.run_report()['historique'][0]['marge_apres_acquisition_centimes'])

    def test_uncovered_movements_are_not_silently_dropped(self):
        self.rows[0]['territoire'] = 'autre'
        with self.assertRaisesRegex(ValueError, 'hors couverture'):
            self.run_report()

    def test_noninteger_money_and_mixed_currencies_rejected(self):
        for value in ('1.5', '-100', 'nan', '1e3', ''):
            self.rows[0]['montant_centimes'] = value
            with self.assertRaises(ValueError):
                self.run_report()
        self.rows[0]['montant_centimes'] = '10001'
        self.rows[0]['devise'] = 'USD'
        with self.assertRaises(ValueError):
            self.run_report()

    def test_cli_reports_incomplete_history_with_nonzero_exit(self):
        self.covers[0]['statut'] = 'synthetique'
        self.run_report()
        output = self.folder/'report.json'
        result = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'outils.historique_comptable',
                                 str(self.journal), str(self.coverage), '--sortie', str(output)],
                                capture_output=True, text=True, encoding='utf-8')
        self.assertEqual(result.returncode, 1, result.stderr)
        report = json.loads(output.read_text(encoding='utf-8'))
        self.assertIsNone(report['historique'][0]['marge_apres_acquisition_centimes'])

    def test_cli_cannot_overwrite_input(self):
        self.run_report()
        before = self.journal.read_bytes()
        result = subprocess.run([sys.executable, '-X', 'utf8', '-m', 'outils.historique_comptable',
                                 str(self.journal), str(self.coverage), '--sortie', str(self.journal)],
                                capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.journal.read_bytes(), before)


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.csv = Path(self.tmp.name)/'duel.csv'
        self.csv.write_text('mois,acteur_J,acteur_m\n2025-01,10,20\n', encoding='utf-8')
        self.path = self.csv.with_suffix('.source.json')
        # Contrat de validation uniquement : les données de test restent dans un dossier temporaire.
        self.manifest = dict(source='test-contract', extraction_utc='2025-02-01T00:00:00Z',
                             territoire='ville', definition_mesure='clients distincts ayant consommé',
                             normalisation='aucune', acteur_J='J', acteur_m='M',
                             traitement_ruptures='aucune dans cette période de test',
                             sha256=empreinte(self.csv), debut='2025-01', fin='2025-01',
                             statut='observe', mesure='clients', perimetres_comparables=True)

    def audit(self):
        self.path.write_text(json.dumps(self.manifest), encoding='utf-8')
        return auditer_source(self.csv, self.path)

    def test_coherent_manifest_then_changed_csv(self):
        self.assertTrue(self.audit()['exploitable_clients'])
        self.csv.write_text('mois,acteur_J,acteur_m\n2025-01,11,20\n', encoding='utf-8')
        self.assertFalse(self.audit()['exploitable_clients'])

    def test_unknown_synthetic_proxy_and_bad_period_are_blocked(self):
        for field, value in [('statut', 'synthetique'), ('statut', 'inconnu'),
                             ('mesure', 'attention'), ('fin', '2025-02'),
                             ('extraction_utc', 'hier'), ('perimetres_comparables', 'true')]:
            old = self.manifest[field]
            self.manifest[field] = value
            self.assertFalse(self.audit()['exploitable_clients'])
            self.manifest[field] = old

    def test_absent_manifest_never_certifies_clients(self):
        self.assertFalse(auditer_source(self.csv)['exploitable_clients'])

    def test_duplicate_headers_and_extra_fields_rejected(self):
        for content in ('mois,acteur_J,acteur_m,acteur_J\n2025-01,10,20,30\n',
                        'mois,acteur_J,acteur_m\n2025-01,10,20,30\n'):
            self.csv.write_text(content, encoding='utf-8')
            with self.assertRaises(ValueError):
                auditer_source(self.csv)


if __name__ == '__main__':
    unittest.main()
