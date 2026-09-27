import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from outils.extraire_historique_postgres import extraire, enregistrer


class ExtractionTests(unittest.TestCase):
    @patch('outils.extraire_historique_postgres.subprocess.run')
    def test_read_only_and_no_secret_in_command_or_report(self, run):
        run.return_value = SimpleNamespace(returncode=0, stdout=json.dumps({
            'lecture_seule': 'on', 'compteurs': {'paiements': 0, 'commissions': 0},
            'paiements_par_mois_creation': []}))
        with patch.dict('os.environ', {'PGPASSWORD': 'secret-test'}):
            report = extraire('localhost', 5434, 'test', psql='psql')
        args, kwargs = run.call_args
        self.assertNotIn('secret-test', ' '.join(args[0]))
        self.assertNotIn('secret-test', json.dumps(report))
        self.assertIn('READ ONLY', kwargs['input'])
        self.assertIn('default_transaction_read_only=on', kwargs['env']['PGOPTIONS'])
        self.assertIn('ON_ERROR_STOP=1', args[0])
        self.assertEqual(report['statut'], 'origine_reelle_non_etablie')

    @patch('outils.extraire_historique_postgres.subprocess.run')
    def test_failed_extraction_redacts_driver_error(self, run):
        run.return_value = SimpleNamespace(returncode=1, stdout='', stderr='secret-test')
        with self.assertRaises(ValueError) as raised:
            extraire('localhost', 5434, 'test', psql='psql')
        self.assertNotIn('secret-test', str(raised.exception))

    @patch('outils.extraire_historique_postgres.subprocess.run')
    def test_missing_read_only_confirmation_is_rejected(self, run):
        run.return_value = SimpleNamespace(returncode=0, stdout='{"lecture_seule":"off"}')
        with self.assertRaisesRegex(ValueError, 'Lecture seule'):
            extraire('localhost', 5434, 'test', psql='psql')

    def test_snapshot_never_overwrites_and_empty_is_not_month_of_zero(self):
        report = {'donnees': {'paiements_par_mois_creation': []}}
        with tempfile.TemporaryDirectory() as tmp:
            folder = Path(tmp)/'snapshot'
            enregistrer(report, folder)
            self.assertEqual(len((folder/'paiements-mensuels-non-qualifies.csv').read_text().splitlines()), 1)
            self.assertEqual(len(json.loads((folder/'empreintes.json').read_text())), 2)
            with self.assertRaises(FileExistsError):
                enregistrer(report, folder)


if __name__ == '__main__':
    unittest.main()
