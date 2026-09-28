import csv
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

from outils.marche_biface import (Parametres, liquidite, etape, simuler,
                                  elasticite_locale, diagnostic_simulation, seuil_offre_necessaire)
from outils.liquidite_observee import mesurer
from outils.valider_plateformes import evaluation_publique


class MarcheBifaceTests(unittest.TestCase):
    def test_seo_amorce_sans_acquisition_payante_et_couts_garantie(self):
        p=replace(Parametres(), recrutement_utilisateurs=0,recrutement_prestataires=0,
                  acquisition_seo_utilisateurs=25,acquisition_seo_prestataires=2,cout_seo_mensuel=300,
                  prime_garantie_prestataire=40,complement_garantie_prestataire=15)
        rows=simuler(0,0,12,p)
        self.assertEqual(rows[0]['utilisateurs_suivants'],25)
        self.assertEqual(rows[0]['prestataires_suivants'],2)
        self.assertEqual(rows[0]['couts_opex'],8300)
        self.assertTrue(all(r['nouveaux_utilisateurs_payants']==0 for r in rows))
        r=rows[1]
        self.assertEqual(r['revenu_garantie'],80)
        self.assertEqual(r['cout_garantie'],30)
        self.assertAlmostEqual(r['revenu_plateforme'],r['revenu_commission']+80)

    def test_aucune_transaction_sans_offre_demande_ou_compatibilite(self):
        p = Parametres()
        for u, s, config in [(0, 10, p), (100, 0, p),
                              (100, 10, replace(p, compatibilite=0)),
                              (100, 10, replace(p, places_par_prestataire=0))]:
            self.assertEqual(liquidite(u, s, config)['reservations'], 0)

    def test_capacite_et_probabilites(self):
        for u in (0, 1, 100, 20000):
            for s in (0, 1, 100):
                r = liquidite(u, s)
                self.assertLessEqual(r['reservations'], min(r['demandes'], r['capacite']))
                for key in ('probabilite_offre_compatible', 'taux_service', 'remplissage'):
                    if r[key] is not None:
                        self.assertGreaterEqual(r[key], 0)
                        self.assertLessEqual(r[key], 1)

    def test_agregation_geographique_ne_cree_pas_de_liquidite(self):
        # Utilisateurs et offre dans des villes différentes : zéro rencontre.
        local = liquidite(100, 0)['reservations'] + liquidite(0, 100)['reservations']
        self.assertEqual(local, 0)
        self.assertGreater(liquidite(100, 100)['reservations'], local)

    def test_metcalfe_n_est_pas_une_loi_globale(self):
        self.assertAlmostEqual(elasticite_locale(10, .01), 2, places=3)
        self.assertAlmostEqual(elasticite_locale(100, 1000), 1, places=5)

    def test_absence_de_bascule_forcee(self):
        rows = simuler(p=replace(Parametres(), effet_utilisateurs=0, effet_prestataires=0))
        self.assertIsNone(diagnostic_simulation(rows)['premier_mois_croissance_organique_deux_faces_sur_3_mois'])
        self.assertTrue(all(r['croissance_organique_utilisateurs'] <= 0 for r in rows))

    def test_borne_necessaire_insuffisante_si_congestion(self):
        p = replace(Parametres(), places_par_prestataire=.01)
        s = 2 * seuil_offre_necessaire(p)
        self.assertLess(etape(10000, s, p)['croissance_organique_utilisateurs'], 0)

    def test_opex_et_commission_sans_confusion_avec_volume_affaires(self):
        p = replace(Parametres(), recrutement_utilisateurs=0, recrutement_prestataires=0)
        r = etape(100, 10, p)
        self.assertAlmostEqual(r['revenu_plateforme'], r['reservations'] * 4)
        self.assertAlmostEqual(r['couts_opex'], 8000 + 50 + .6*r['reservations'])
        self.assertAlmostEqual(r['solde_exploitation'], r['revenu_plateforme'] - r['couts_opex'])

    def test_stocks_bornes_et_financement(self):
        p = replace(Parametres(), recrutement_utilisateurs=1e6, recrutement_prestataires=1e6)
        rows = simuler(p=p)
        for r in rows:
            self.assertTrue(0 <= r['utilisateurs_suivants'] <= p.marche_utilisateurs)
            self.assertTrue(0 <= r['prestataires_suivants'] <= p.marche_prestataires)
        self.assertEqual(rows[-1]['financement_cumule_requis'], max(0, -min(r['solde_cumule'] for r in rows)))


class LiquiditeObserveeTests(unittest.TestCase):
    def run_csv(self, rows):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'recherches.csv'
            with path.open('w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['recherche_id','horodatage','territoire','seances_compatibles_disponibles','reservation_confirmee'])
                writer.writerows(rows)
            return mesurer(path)

    def test_zero_resultat_inclus_et_conversion_distincte(self):
        rows = [[str(i), '2026-01-01T12:00:00+01:00', 'Paris', a, b]
                for i, (a, b) in enumerate([(0, 0), (3, 0), (1, 1)])]
        r = self.run_csv(rows)[0]
        self.assertEqual(r['liquidite'], 2/3)
        self.assertEqual(r['conversion_reservation'], 1/3)
        lo, hi = r['intervalle_wilson95_iid']
        self.assertLess(lo, 2/3)
        self.assertGreater(hi, 2/3)

    def test_donnees_absentes_ou_incoherentes_refusees(self):
        valid = ['a', '2026-01-01T12:00:00+01:00', 'Paris', 1, 0]
        for rows in ([], [valid, valid], [valid[:-1]],
                     [['b', '2026-01-01T12:00:00', 'Paris', 1, 0]],
                     [['b', valid[1], 'Paris', 0, 1]]):
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                self.run_csv(rows)

    def test_pas_de_pooling_des_villes(self):
        r = self.run_csv([['a','2026-01-01T12:00:00Z','Paris',1,0],
                          ['b','2026-01-01T12:00:00Z','Lyon',0,0]])
        self.assertEqual({x['territoire']: x['liquidite'] for x in r}, {'Paris':1, 'Lyon':0})


class DonneesPlateformesTests(unittest.TestCase):
    def test_donnees_reelles_ne_valident_pas_une_liquidite_non_observee(self):
        report, predictions, mb = evaluation_publique()
        self.assertEqual(len(mb), 14)
        self.assertEqual(report['classpass']['observations'], 8)
        self.assertFalse(report['validation_metcalfe'])
        self.assertFalse(report['calibration_point_bascule'])
        self.assertTrue(predictions)
        self.assertLess(report['mindbody']['variation_2017_professionnels'], 0)
        self.assertGreater(report['mindbody']['variation_2017_revenu_trimestriel'], 0)


if __name__ == '__main__':
    unittest.main()
