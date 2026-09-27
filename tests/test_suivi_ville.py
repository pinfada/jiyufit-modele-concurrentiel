import tempfile
import unittest
from pathlib import Path
import numpy as np
from scipy.special import expit, logit
from outils.donnees import lire_duel, valider_mois
from outils.suivi_ville import diagnostiquer, evaluer_gates, valider_metier


class CityTests(unittest.TestCase):
    def setUp(self):
        self.metier = dict(mesure='clients', marge_contributive_mensuelle=1000,
                          retention_validee=True, capacite_validee=True,
                          budget_expansion_valide=True, calibration_locale_validee=True)
        # Trajectoire analytique convergente à 70 %, données sans bruit.
        self.s = expit(logit(.7)+.8**np.arange(36)*(logit(.2)-logit(.7)))
        self.d = diagnostiquer(self.s, .8, (.8, .8))

    def test_constant_ten_percent_cannot_expand(self):
        s = np.full(12, .1)
        v = evaluer_gates(s, diagnostiquer(s, .926), metier=self.metier)
        self.assertFalse(v['g1']); self.assertFalse(v['g2'])

    def test_complete_viable_case_can_expand(self):
        source = dict(exploitable_clients=True, fin='2025-12', manifeste={'territoire': 'test'})
        history = {'historique': [dict(mois='2025-'+m, territoire='test', rapproche=True,
                                      marge_apres_acquisition_centimes=100000)
                                 for m in ('10', '11', '12')]}
        self.assertIs(evaluer_gates(self.s, self.d, metier=self.metier,
                                   source=source, comptabilite=history)['g2'], True)

    def test_boolean_declarations_alone_no_longer_allow_expansion(self):
        self.assertIsNone(evaluer_gates(self.s, self.d, metier=self.metier)['g2'])

    def test_wrong_period_or_territory_cannot_supply_margin(self):
        source = dict(exploitable_clients=True, fin='2025-12', manifeste={'territoire': 'test'})
        for territory, month in [('ailleurs', '2025-12'), ('test', '2024-12')]:
            history = {'historique': [dict(mois=month, territoire=territory, rapproche=True,
                                          marge_apres_acquisition_centimes=100000)]}
            self.assertIsNone(evaluer_gates(self.s, self.d, metier=self.metier,
                                           source=source, comptabilite=history)['g2'])

    def test_declared_margin_must_match_reconciled_margin(self):
        source = dict(exploitable_clients=True, fin='2025-12', manifeste={'territoire': 'test'})
        history = {'historique': [dict(mois='2025-'+m, territoire='test', rapproche=True,
                                      marge_apres_acquisition_centimes=100)
                                 for m in ('10', '11', '12')]}
        self.assertIs(evaluer_gates(self.s, self.d, metier=self.metier,
                                   source=source, comptabilite=history)['g2'], False)

    def test_g2_requires_g1(self):
        s = np.full(36, .7)
        d = diagnostiquer(s, .8, (.8, .8))
        self.assertIs(evaluer_gates(s, d, metier=self.metier)['g2'], False)

    def test_missing_business_evidence_is_indeterminate(self):
        self.assertIsNone(evaluer_gates(self.s, self.d)['g2'])

    def test_proxy_alone_cannot_expand(self):
        self.metier['mesure'] = 'attention'
        self.assertIsNone(evaluer_gates(self.s, self.d, metier=self.metier)['g2'])

    def test_negative_margin_blocks_expansion(self):
        self.metier['marge_contributive_mensuelle'] = -1
        self.assertIs(evaluer_gates(self.s, self.d, metier=self.metier)['g2'], False)

    def test_uncertain_phi_cannot_expand(self):
        for interval in (None, (.7, 1.02)):
            d = diagnostiquer(self.s, .8, interval)
            self.assertFalse(d['plateau_identifiable'])
            self.assertIsNone(evaluer_gates(self.s, d, metier=self.metier)['g2'])

    def test_intercept_is_refitted_with_phi(self):
        # Toute constante reste au même point fixe pour tout phi stationnaire.
        d = diagnostiquer(np.full(36, .3), .9, (.5, .98))
        self.assertAlmostEqual(d['s_lo'], .3)
        self.assertAlmostEqual(d['s_hi'], .3)

    def test_invalid_phi_and_parts_are_rejected(self):
        for phi in (0, 1, 1.1, -1, float('nan'), float('inf')):
            with self.assertRaises(ValueError):
                diagnostiquer(self.s, phi)
        with self.assertRaises(ValueError):
            diagnostiquer(np.zeros(12), .8)
        with self.assertRaises(ValueError):
            diagnostiquer(self.s, .8, (.9, .99))

    def test_dates_must_be_regular(self):
        for months in (['2024-01', '2024-03'], ['2024-01', '2024-01'],
                       ['2024-02', '2024-01'], ['2024-13'], []):
            with self.assertRaises(ValueError):
                valider_mois(months)

    def test_csv_rejects_nonfinite_negative_empty_activity(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'duel.csv'
            for j, m in [('nan', '1'), ('inf', '1'), ('-1', '1'), ('0', '0')]:
                path.write_text(f'mois,acteur_J,acteur_m\n2024-01,{j},{m}\n', encoding='utf-8')
                with self.assertRaises(ValueError):
                    lire_duel(path)

    def test_zero_share_is_explicitly_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'duel.csv'
            path.write_text('mois,acteur_J,acteur_m\n2024-01,0,100\n2024-02,100,0\n', encoding='utf-8')
            _, s, clipped = lire_duel(path)
            self.assertEqual(clipped, 2)
            self.assertTrue(np.all((s > 0) & (s < 1)))

    def test_business_schema_rejects_truthy_strings(self):
        for payload in ({'retention_validee': 'false'}, {'marge_contributive_mensuelle': float('nan')}, [], {'typo': True}):
            with self.assertRaises(ValueError):
                valider_metier(payload)


if __name__ == '__main__':
    unittest.main()
