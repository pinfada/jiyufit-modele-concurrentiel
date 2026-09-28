"""Compare le moteur HTML autonome au moteur Python sur chaque mois et champ."""
from dataclasses import asdict
import json
from pathlib import Path
import shutil
import subprocess
import unittest

from outils.marche_biface import Parametres, simuler, diagnostic_simulation

ROOT = Path(__file__).resolve().parents[1]
JS = r'''
const fs=require('node:fs'),vm=require('node:vm');
const html=fs.readFileSync('outils/calculateur_garantie/calculateur-garantie.html','utf8');
const source=html.match(/<script id="moteur-biface">([\s\S]*?)<\/script>/)[1];
const box={module:{exports:{}}}; vm.runInNewContext(source,box);
const inputs=JSON.parse(fs.readFileSync(0,'utf8'));
console.log(JSON.stringify(inputs.map(p=>{try{return box.module.exports.simuler(p)}catch(e){return {error:e.message}}})));
'''


@unittest.skipUnless(shutil.which('node'), 'Node requis pour vérifier la calculatrice autonome')
class CalculatriceBifaceTests(unittest.TestCase):
    def run_js(self, cases):
        result = subprocess.run(['node','-e',JS],cwd=ROOT,input=json.dumps(cases),
                                text=True,capture_output=True,check=True)
        return json.loads(result.stdout)

    def test_parite_complete_avec_python(self):
        cases=[{}, {'parametres':{'effet_utilisateurs':0,'effet_prestataires':0}},
               {'parametres':{'compatibilite':.001}}, {'parametres':{'places_par_prestataire':2}},
               {'utilisateurs':0,'prestataires':0}, {'parametres':{'places_par_prestataire':0}},
               {'mois':1,'parametres':{'commission':0}},
               {'parametres':{'recrutement_utilisateurs':1e6,'recrutement_prestataires':1e6}},
               {'utilisateurs':0,'prestataires':0,'parametres':{'recrutement_utilisateurs':0,'recrutement_prestataires':0,
                'acquisition_seo_utilisateurs':25,'acquisition_seo_prestataires':2,'cout_seo_mensuel':300,
                'prime_garantie_prestataire':40,'complement_garantie_prestataire':15}}]
        for case, actual in zip(cases,self.run_js(cases)):
            params=Parametres(**(asdict(Parametres())|case.get('parametres',{})))
            expected=simuler(case.get('utilisateurs',100),case.get('prestataires',5),case.get('mois',120),params)
            self.assertEqual(actual['bascule'], diagnostic_simulation(expected)['premier_mois_croissance_organique_deux_faces_sur_3_mois'])
            self.assertFalse(actual['calibration_empirique'])
            for py,js in zip(expected,actual['trajectoire']):
                self.assertEqual(set(py),set(js))
                for key,value in py.items():
                    if value is None: self.assertIsNone(js[key])
                    else: self.assertAlmostEqual(value,js[key],delta=1e-8*max(1,abs(value)),msg=key)

    def test_saisies_invalides_refusees(self):
        cases=[{'mois':0},{'mois':1.5},{'utilisateurs':-1},{'utilisateurs':30000},
               {'parametres':{'commission':2}},{'parametres':{'opex_fixes':-1}},
               {'parametres':{'marche_prestataires':0}}]
        for result in self.run_js(cases): self.assertIn('error',result)


if __name__=='__main__': unittest.main()
