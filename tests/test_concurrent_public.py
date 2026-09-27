import csv
import tempfile
from pathlib import Path
import unittest
import numpy as np

from outils.collecter_basicfit import extraire_table
from outils.valider_concurrent import prevoir, backtest, lire_abonnements, analyser


class PublicCompetitorTests(unittest.TestCase):
    def test_published_tables_extract_exact_quarters_and_footnotes(self):
        text = '\n'.join(f'{label} quarter {a} {b}' for label,a,b in
                         [('First','4.47','4.05'),('Second','4.51','4.09'),
                          ('Third','4.73','4.20'),('Fourth','4.82','4.25')])
        values = extraire_table(text)
        self.assertEqual(values[3], [4820000,4250000])
        html = '<table>'+''.join(f'<tr><td>{label} quarter<sup>1</sup></td><td>{a}</td><td>{b}</td></tr>'
                                for label,(a,b) in zip(('First','Second','Third','Fourth'),
                                [('4.47','4.05'),('4.51','4.09'),('4.73','4.20'),('4.82','4.25')]))+'</table>'
        self.assertEqual(extraire_table(html, html=True), values)

    def test_missing_or_duplicate_source_quarter_rejected(self):
        with self.assertRaises(ValueError):
            extraire_table('First quarter 1.00 2.00')

    def test_forecast_recovers_known_log_linear_equation(self):
        logs = [np.log(10000.)]
        for _ in range(19): logs.append(.7+.93*logs[-1])
        values = np.exp(logs)
        expected = np.exp(.7+.93*logs[-1])
        self.assertAlmostEqual(prevoir(values, 1, 'ar1_log'), expected, places=6)

    def test_future_data_cannot_change_earlier_predictions(self):
        dates = [f'{2020+i//4}-Q{i%4+1}' for i in range(24)]
        values = np.exp(12+.03*np.arange(24)+.02*np.sin(np.arange(24)))
        before = backtest(values, dates)
        values[18:] *= 2
        after = backtest(values, dates)
        for a,b in zip(before,after):
            if a['origine'] < dates[18]:
                self.assertEqual(a['prediction'], b['prediction'])

    def test_quarter_gap_is_not_interpolated(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'series.csv'
            with path.open('w',newline='') as stream:
                writer=csv.writer(stream); writer.writerow(['trimestre','abonnements'])
                writer.writerows((f'{2020+i//4}-Q{i%4+1}',100+i) for i in range(16) if i!=5)
            with self.assertRaises(ValueError): lire_abonnements(path)

    def test_official_dataset_integrity_and_test_targets(self):
        root=Path(__file__).resolve().parents[1]/'data/public/basicfit_2020_2025'
        report, rows = analyser(root/'abonnements_trimestriels.csv',root/'provenance.json')
        self.assertEqual(report['n'],24)
        self.assertFalse(report['validation_structurelle'])
        for h in (1,2,4):
            groups = [{(r['origine'],r['cible']) for r in rows
                       if r['horizon_trimestres']==h and r['model']==model}
                      for model in ('ar1_log','persistance','derive_log')]
            self.assertTrue(all(g==groups[0] for g in groups))


if __name__ == '__main__':
    unittest.main()
