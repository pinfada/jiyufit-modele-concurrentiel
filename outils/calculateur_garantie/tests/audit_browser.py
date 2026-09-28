"""Régressions de l'audit utilisateur. Optionnel : pip install playwright ; Edge installé."""
from pathlib import Path
import json
from playwright.sync_api import sync_playwright

root=Path(__file__).resolve().parents[3]
url=(Path(__file__).resolve().parents[1]/'calculateur-garantie.html').as_uri()
with sync_playwright() as pw:
    browser=pw.chromium.launch(channel='msedge',headless=True)
    page=browser.new_page(viewport={'width':1440,'height':1000})
    errors=[]
    page.on('pageerror',lambda error: errors.append(str(error)))
    page.goto(url)
    assert page.locator('#resultats-garantie').is_visible()
    page.locator('#prix').fill('0')
    assert 'strictement positif' in page.locator('#erreur').inner_text()
    assert not page.locator('#resultats-garantie').is_visible()
    page.locator('#prix').fill('12')
    page.locator('#remplissage').fill('5')
    page.locator('#moisFaible').fill('1')
    assert 'DEVIS REFUSÉ' in page.locator('#verdict-communaute').inner_text()
    page.locator('#remplissage').fill('65')
    page.locator('#moisFaible').fill('54')
    page.locator('#explication summary').click()
    assert '3,5' in page.locator('#explication-liste').inner_text()
    assert 'mois habituel' not in page.locator('#explication-liste').inner_text()
    page.locator('#placesParMois').fill('0')
    assert page.locator('#erreur').inner_text()
    assert not page.locator('#resultats-garantie').is_visible()
    page.locator('#placesParMois').fill('173')
    page.locator('#prix').fill('')
    assert page.locator('#erreur').inner_text()
    assert not page.locator('#resultats-garantie').is_visible()
    page.locator('#prix').fill('12')
    page.locator('#moisFaible').fill('90')
    assert 'inférieur' in page.locator('#erreur').inner_text()
    page.locator('#moisFaible').fill('54')
    page.locator('input[value="historique"]').check()
    saison=[64,67,62,66,65,64,40,20,15,68,65,66]
    def remplir(values):
        page.evaluate('''values=>{document.querySelectorAll('#grille-mois input').forEach((x,i)=>x.value=values[i]??'');document.querySelector('#mois-0').dispatchEvent(new Event('input',{bubbles:true}));}''',values)
    remplir(saison)
    assert 'DEVIS REFUSÉ' in page.locator('#verdict-communaute').inner_text()
    assert '25' in page.locator('#chiffres-communaute').inner_text()
    bilan=page.evaluate('''()=>{let r=window.garantieCourante.resultat;return {plancher:r.plancherEuros,prix:r.prime,modele:r.primePureModele,observe:r.primePureObservee,frequence:r.probaSousPlancher,suspendu:!r.tarifValide}}''')
    remplir(saison[:5])
    assert not page.locator('#resultats-garantie').is_visible()
    remplir(saison)
    page.locator('#mois-0').fill('abc')
    assert not page.locator('#resultats-garantie').is_visible()
    remplir([65]*12)
    assert page.evaluate('window.garantieCourante.resultat.prime')==10
    assert abs(page.evaluate('window.garantieCourante.resultat.plancherPartRevenu')-.9)<1e-9
    page.locator('#ajouter-mois').click()
    page.locator('#mois-0').evaluate(r'''el=>{const data=new DataTransfer();data.setData('text',Array(12).fill('62,5').join('\n'));el.dispatchEvent(new ClipboardEvent('paste',{clipboardData:data,bubbles:true,cancelable:true}));}''')
    assert page.locator('#mois-0').input_value()==''
    assert page.locator('#mois-12').input_value()=='62,5'
    assert page.locator('#mois-23').input_value()=='62,5'
    assert 'Série placée' in page.locator('#resume-collage').inner_text()
    page.locator('[data-vue="biface"]').click()
    assert page.locator('#bf-resultats').is_visible()
    assert page.locator('#bf-attrition_prestataires').input_value()=='3.5'
    page.locator('#bf-commission').fill('150')
    assert 'entre 0 et 100 %' in page.locator('#bf-erreur').inner_text()
    page.locator('#bf-commission').fill('0.2')
    assert '0,2 % saisi' in page.locator('#bf-unites').inner_text()
    assert 'saisissez 20' in page.locator('#bf-unites').inner_text()
    page.locator('#bf-commission').fill('20')
    assert page.locator('#commission').input_value()=='20'
    page.locator('#bf-prix_seance').fill('14')
    assert page.locator('#prix').input_value()=='14'
    page.locator('#bf-places_par_prestataire').fill('200')
    assert page.locator('#placesParMois').input_value()=='200'
    page.locator('#bf-attrition_utilisateurs').fill('120')
    assert 'Attrition utilisateurs' in page.locator('#bf-erreur').inner_text()
    assert 'attrition_utilisateurs' not in page.locator('#bf-erreur').inner_text()
    page.locator('#bf-attrition_utilisateurs').fill('8')
    page.locator('#bf-mois').fill('')
    page.locator('#bf-mois').press_sequentially('abc')
    assert 'Durée' in page.locator('#bf-erreur').inner_text()
    assert not page.locator('#bf-resultats').is_visible()
    page.locator('#bf-mois').fill('120')
    page.locator('#bf-garantie').click()
    assert float(page.locator('#bf-prime_garantie_prestataire').input_value())==10
    assert 'intégrée' in page.locator('#bf-lien-garantie').inner_text()
    for k,v in {'recrutement_utilisateurs':0,'recrutement_prestataires':0,'acquisition_seo_utilisateurs':25,'acquisition_seo_prestataires':2,'cout_seo_mensuel':300}.items():
        page.locator('#bf-'+k).fill(str(v))
    assert page.locator('#bf-resultats').is_visible()
    with page.expect_download() as download: page.locator('#bf-export').click()
    exported=json.loads(Path(download.value.path()).read_text())
    assert exported['parametres']['commission']==.2
    assert exported['trajectoire'][0]['nouveaux_utilisateurs_payants']==0
    assert exported['trajectoire'][0]['nouveaux_utilisateurs_seo']>0
    assert exported['trajectoire'][0]['revenu_garantie']==50
    page.locator('[data-vue="portefeuille"]').click()
    page.locator('#calculer-portefeuille').click()
    assert page.locator('#table-portefeuille').inner_text()
    page.locator('#csv').fill('invalide')
    assert page.locator('#erreur-portefeuille').inner_text()
    assert not page.locator('#table-portefeuille').inner_text()
    assert page.locator('#exporter').is_disabled()
    page.locator('#csv').fill('nom;places_mois;prix;historique\nSaison;173;12;'+' '.join(map(str,saison)))
    assert 'Revue requise' in page.locator('#chiffres-portefeuille').inner_text()
    page.locator('#choc').fill('0')
    assert 'Aucun choc' in page.locator('#chiffres-portefeuille').inner_text()
    page.goto(url+'?public=1&mode=historique')
    remplir(saison)
    assert 'DEVIS REFUSÉ' in page.locator('#verdict-communaute').inner_text()
    page.set_viewport_size({'width':390,'height':844})
    assert page.evaluate('document.documentElement.scrollWidth<=innerWidth')
    (root/'artifacts').mkdir(exist_ok=True)
    page.screenshot(path=str(root/'artifacts/audit-calculatrice-mobile.png'),full_page=True)
    assert not errors,errors
    browser.close()
print(json.dumps(bilan,ensure_ascii=False))
print('Audit navigateur : saisonnalité, prix minimum, saisies, résultats périmés, collage, SEO, paramètres partagés, garantie, export, public et mobile OK.')
