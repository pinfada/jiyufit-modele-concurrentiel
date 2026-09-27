// Tests du moteur de la calculatrice (node --test outils/calculateur_garantie/tests).
// Le moteur vit dans le fichier HTML (<script id="moteur">) pour que la
// calculatrice reste un fichier unique ; on l'extrait et on l'exécute ici.
'use strict';

const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const html = fs.readFileSync(path.join(__dirname, '..', 'calculateur-garantie.html'), 'utf8');
const source = html.match(/<script id="moteur">([\s\S]*?)<\/script>/)[1];
const bac = { module: { exports: {} } };
vm.runInNewContext(source, bac);
const M = bac.module.exports;

const proche = (reel, attendu, tolerance, message) =>
  assert.ok(Math.abs(reel - attendu) <= tolerance, `${message} : ${reel} au lieu de ${attendu} ± ${tolerance}`);

// Exemple canonique de REVENUE_MODEL_DOCTRINE.md §4 avec les conventions du
// notebook (section XXX) : médiane 65 %, dispersion logit 0,35, plancher P10.
const VOLT = { placesParMois: 173, prix: 12, commission: 0.15, remplissage: 0.65, dispersion: 0.35, quantilePlancher: 0.10, gamma: 3.5 };

test('Volt : payout plein, plancher et probabilité retrouvent la doctrine', () => {
  const r = M.evaluerSalle(VOLT);
  proche(r.payoutPlein, 1764.6, 0.1, 'payout plein');
  proche(r.plancherTaux, 0.543, 0.001, 'plancher (P10)');
  proche(r.plancherEuros, 957, 2, 'plancher en euros (doctrine : ~970)');
  proche(r.probaSousPlancher, 0.10, 0.002, 'probabilité sous plancher = quantile');
});

test('Volt : prime pure et commerciale conformes au calcul de référence', () => {
  const r = M.evaluerSalle(VOLT);
  proche(r.primePure, 7.28, 0.05, 'prime pure');
  proche(r.primeCommerciale, 25.5, 0.2, 'prime commerciale (γ = 3,5)');
  proche(r.lossRatio, 1 / 3.5, 1e-9, 'loss ratio = 1/γ au prix commercial');
});

test('au prix doctrinal de 89 €, le loss ratio et la marge suivent', () => {
  const r = M.evaluerSalle({ ...VOLT, prixPropose: 89 });
  proche(r.lossRatio, 7.28 / 89, 0.001, 'loss ratio à 89 €');
  proche(r.margeGarantie, 89 - r.primePure, 1e-9, 'marge garantie sans frais');
  proche(r.commissionJiyufit, r.remplissageMoyen * 173 * 12 * 0.15, 1e-9, 'commission');
});

test("l'intégration de Simpson concorde avec un Monte-Carlo indépendant", () => {
  const d = M.distributionLogitNormale(0.65, 0.35);
  const plancher = d.quantile(0.10);
  let graine = 42;
  const alea = () => { graine = (graine * 1103515245 + 12345) % 2147483648; return (graine + 0.5) / 2147483648; };
  const n = 200000;
  let somme = 0;
  for (let i = 0; i < n; i += 1) {
    const z = Math.sqrt(-2 * Math.log(alea())) * Math.cos(2 * Math.PI * alea());
    somme += Math.max(0, plancher - M.invLogit(M.logit(0.65) + 0.35 * z));
  }
  const monteCarlo = somme / n;
  const integrale = d.esperance((f) => Math.max(0, plancher - f));
  proche(integrale, monteCarlo, monteCarlo * 0.05, 'manque moyen (intégrale vs Monte-Carlo)');
});

test('le mauvais mois (P10) redonne la dispersion', () => {
  const s = M.dispersionDepuisMoisFaible(0.65, 0.5425, 0.10);
  proche(s, 0.35, 0.002, 'dispersion');
  assert.throws(() => M.dispersionDepuisMoisFaible(0.65, 0.70), /inférieur/);
});

// Deux années « réalistes » (creux en août, sept. → août), réutilisées plus bas.
const ANNEE = [0.80, 0.85, 0.90, 0.45, 0.60, 0.40, 0.60, 0.65, 0.70, 0.75, 0.50, 0.30];
const ANNEE_2 = [0.78, 0.83, 0.88, 0.48, 0.62, 0.44, 0.63, 0.66, 0.72, 0.74, 0.52, 0.33];

// Profil du studio lyonnais (exemples/studios_lyon_2026-09.csv), avec des mois
// complets à 100 % : c'est lui qui a révélé le saut 23 → 24 mois (73 € → 35 €).
const LYON = [100, 88.3, 82.3, 75.4, 77.6, 51.9, 64.1, 69.3, 81.1, 74, 65.7, 72, 100, 86.3, 75, 58.1, 66.7, 51.4, 100, 89.9, 100, 95.3, 67.5, 59].map((x) => x / 100);

test('méthode unique quelle que soit la durée : pas de saut en ajoutant un mois', () => {
  const base = { placesParMois: 173, prix: 12, commission: 0.15, gamma: 3.5 };
  const n24 = M.evaluerSalle({ ...base, historique: LYON });
  const n23 = M.evaluerSalle({ ...base, historique: LYON.slice(1) });
  assert.equal(n24.distribution, 'historique-ajuste');
  assert.equal(n23.distribution, 'historique-ajuste');
  assert.ok(Math.abs(n24.prime - n23.prime) / n24.prime < 0.10, `prix stable : ${n23.prime.toFixed(1)} → ${n24.prime.toFixed(1)}`);
  assert.ok(Math.abs(n24.plancherEuros - n23.plancherEuros) / n24.plancherEuros < 0.05, 'plancher stable');
  // Le quantile brut reste disponible comme contrôle interne.
  proche(n24.plancherBrutTaux, M.quantileEmpirique(LYON, 0.10), 1e-12, 'contrôle : quantile brut');
  assert.throws(() => M.evaluerSalle({ placesParMois: 100, prix: 10, historique: [0.6, 0.5] }), /trop court/);
});

test('les mois complets (plafond de capacité) ne gonflent pas le prix', () => {
  const base = { placesParMois: 173, prix: 12, commission: 0.15, gamma: 3.5 };
  const avecPleins = M.evaluerSalle({ ...base, historique: LYON });
  const plafonnes = M.evaluerSalle({ ...base, historique: LYON.map((x) => Math.min(x, 0.9)) });
  proche(avecPleins.prime, plafonnes.prime, 1e-9, 'plafonner les mois complets à 90 % ne change rien');
});

// Cas signalé par le fondateur le 27/09/2026 : 12 mois, un seul mois à 30 %.
// Quantile brut : 715 € sans août → 794 €, prix 57 € → 28 € (divisé par 2).
test('12 mois : ajustement robuste, bien moins sensible au pire mois que le quantile brut', () => {
  const base = { placesParMois: 173, prix: 12, commission: 0.15, gamma: 3.5 };
  const r = M.evaluerSalle({ ...base, historique: ANNEE });
  assert.equal(r.distribution, 'historique-ajuste');
  proche(r.remplissageMoyen, 0.625, 1e-12, 'revenu moyen = moyenne observée, pas celle du modèle');
  proche(r.plancherEuros, 644, 2, 'plancher ajusté (médiane 62,5 %, quartile bas 48,75 %)');
  const brut = { plancher: 715, prix: 57, plancherSans: 794, prixSans: 28 };
  const ecartPrixAjuste = Math.abs(r.sensibilite.prime - r.prime) / r.prime;
  const ecartPrixBrut = Math.abs(brut.prixSans - brut.prix) / brut.prix;
  assert.ok(ecartPrixAjuste < ecartPrixBrut, `le pire mois pèse moins : ${ecartPrixAjuste.toFixed(2)} < ${ecartPrixBrut.toFixed(2)}`);
  proche(r.sensibilite.pireMois, 0.30, 1e-12, 'pire mois identifié');
});

test('« X mois sur Y » et plancher en part du revenu moyen', () => {
  const r = M.evaluerSalle({ placesParMois: 173, prix: 12, commission: 0.15, historique: ANNEE });
  assert.equal(r.nombreMois, 12);
  assert.equal(r.moisAuDessus, ANNEE.filter((f) => f >= r.plancherTaux).length);
  proche(r.plancherPartRevenu, r.plancherTaux / 0.625, 1e-12, 'plancher / remplissage moyen');
});

test('test hors échantillon : calibré sans la dernière année, vérifié sur elle', () => {
  const e = { placesParMois: 173, prix: 12, commission: 0.15, gamma: 3.5, historique: [...ANNEE, ...ANNEE_2] };
  const t = M.testerSurDerniereAnnee(e);
  assert.equal(t.moisCalibrage, 12);
  assert.equal(t.moisTest, 12);
  const calib = M.evaluerSalle({ ...e, historique: ANNEE });
  proche(t.plancherEuros, calib.plancherEuros, 1e-9, 'plancher = celui de la première année');
  const attendu = ANNEE_2.reduce((a, f) => a + Math.max(0, calib.plancherTaux - f), 0) * calib.payoutPlein;
  proche(t.complementTotal, attendu, 1e-9, 'complément sur la seconde année');
  proche(t.lossRatio, attendu / (calib.prime * 12), 1e-12, 'loss ratio hors échantillon');
  assert.equal(M.testerSurDerniereAnnee({ ...e, historique: ANNEE }), null, 'impossible sous 24 mois');
});

test('creux saisonniers : un mois bas chaque année est signalé, un accident isolé non', () => {
  // moisAnnee : sept. = 8 … août = 7 (0 = janvier)
  const points = [...ANNEE, ...ANNEE_2].map((valeur, i) => ({ moisAnnee: (8 + i) % 12, valeur }));
  const creux = M.creuxSaisonniers(points);
  const mois = creux.map((c) => c.moisAnnee);
  assert.ok(mois.includes(7), 'août (30 % puis 33 %) est un creux récurrent');
  assert.ok(creux[0].ecart < -0.4, 'août est le plus marqué');
  assert.equal(mois.includes(10), false, 'novembre (90 %) n\'en est pas un');
  const accident = points.map((p, i) => (i === 3 ? p : { ...p, valeur: p.moisAnnee === 11 ? 0.75 : p.valeur }));
  assert.equal(M.creuxSaisonniers(accident).some((c) => c.moisAnnee === 11), false, 'décembre bas une seule année : pas récurrent');
  assert.equal(M.creuxSaisonniers(points.slice(0, 12)).length, 0, 'moins de 24 mois : pas de diagnostic');
});

test('seuil de rentabilité : à ce remplissage, la prime couvre tout juste le manque', () => {
  const r = M.evaluerSalle({ ...VOLT, prixPropose: 89, frais: 10 });
  assert.equal(r.seuil.deficitaire, false);
  assert.ok(r.seuil.remplissageMoyen < r.remplissageMoyen, 'le seuil est sous le remplissage actuel');
  const auSeuil = M.evaluerSalle({ ...VOLT, remplissage: 0.65 - r.seuil.recul, plancherTaux: r.plancherTaux, prixPropose: 89, frais: 10 });
  proche(auSeuil.margeGarantie, 0, 0.05, 'marge de la garantie au seuil');
});

test('une prime sous la prime pure est signalée déficitaire', () => {
  const r = M.evaluerSalle({ ...VOLT, prixPropose: 5 });
  assert.equal(r.seuil.deficitaire, true);
  assert.ok(r.margeGarantie < 0);
});

test('portefeuille : sommes cohérentes et stress corrélé plus coûteux', () => {
  const p = M.evaluerPortefeuille([
    { nom: 'A', ...VOLT, prixPropose: 89 },
    { nom: 'B', ...VOLT, remplissage: 0.55, prixPropose: 40 }
  ], { choc: 0.10 });
  proche(p.primes, 129, 1e-9, 'primes');
  proche(p.lossRatio, p.sinistresAttendus / p.primes, 1e-12, 'loss ratio portefeuille');
  assert.ok(p.lossRatioSousChoc > p.lossRatio * 3, 'un recul de 10 points de tout le réseau multiplie le loss ratio');
});

test('CSV : séparateur point-virgule, décimales à virgule, pourcentages, historique', () => {
  const salles = M.lireCsv('nom;places_mois;prix;commission;remplissage;mois_faible;historique;prix_propose\n' +
    'Volt;173;12,5;15;65;54;;89\n' +
    'Hist;100;10;;;;66 48 70 63 59 71;\n');
  assert.equal(salles.length, 2);
  assert.equal(salles[0].prix, 12.5);
  proche(salles[0].remplissage, 0.65, 1e-12, 'remplissage en fraction');
  assert.equal(salles[0].prixPropose, 89);
  assert.equal('commission' in salles[1], false, 'commission absente → défaut du moteur');
  assert.equal(JSON.stringify(salles[1].historique.map((x) => Math.round(x * 100))), '[66,48,70,63,59,71]');
  assert.throws(() => M.lireCsv('nom,prix\nA,10'), /places_mois/);
});

test('les saisies invalides sont refusées avec un message clair', () => {
  assert.throws(() => M.evaluerSalle({ ...VOLT, placesParMois: 0 }), /places/);
  assert.throws(() => M.evaluerSalle({ ...VOLT, dispersion: undefined, moisFaible: 0.9 }), /inférieur/);
  assert.throws(() => M.evaluerSalle({ ...VOLT, remplissage: 1.2 }), /entre 0 et 100/);
});

test('lireSerie accepte les formats réels de saisie et de copier-coller', () => {
  const lu = (t) => JSON.stringify(Array.from(M.lireSerie(t), (x) => Math.round(x * 1000) / 10));
  assert.equal(lu('100 88,3 82.3'), '[100,88.3,82.3]', 'virgule ou point décimal');
  assert.equal(lu('72%\t65 %  58'), '[72,65,58]', 'pourcent, tabulation, espaces multiples');
  assert.equal(lu('66\n48\r\n70;63|59'), '[66,48,70,63,59]', 'colonne de tableur et séparateurs');
  assert.equal(lu('  '), '[]', 'vide');
  assert.equal(lu('72\u00a0% 65\u202f%'), '[72,65]', 'espaces insécables des tableurs français');
  assert.throws(() => M.lireSerie('88,3,70'), /illisible/, 'virgules collées ambiguës');
  assert.throws(() => M.lireSerie('abc'), /illisible/);
  assert.throws(() => M.lireSerie('120'), /hors de 0-100/);
});

test('moisTypes : 10 mois ordonnés, exactement un sous le plancher P10', () => {
  const d = M.distributionLogitNormale(0.65, 0.35);
  const mois = M.moisTypes(d, 10);
  assert.equal(mois.length, 10);
  for (let i = 1; i < mois.length; i += 1) assert.ok(mois[i] > mois[i - 1], 'croissants');
  const plancher = d.quantile(0.10);
  assert.equal(mois.filter((m) => m < plancher).length, 1, 'un mois type sur dix sous le plancher');
});

test('portefeuille : test hors échantillon agrégé et creux saisonniers par activité', () => {
  const base = { placesParMois: 173, prix: 12, commission: 0.15, gamma: 3.5 };
  const salles = [
    { nom: 'Deux ans, août bas', ...base, historique: [...ANNEE, ...ANNEE_2] },
    { nom: 'Un an seulement', ...base, historique: ANNEE },
    { nom: 'Estimation', ...base, remplissage: 0.65, moisFaible: 0.54 }
  ];
  // Historiques terminés en août (7) : le 1er mois est septembre, comme ANNEE.
  const p = M.evaluerPortefeuille(salles, { moisFin: 7 });
  assert.ok(p.lignes[0].test, 'test pour 24 mois');
  assert.equal(p.lignes[1].test, null, 'pas de test sous 24 mois');
  assert.equal(p.lignes[2].test, null, 'pas de test sans historique');
  assert.ok(p.lignes[0].creux.some((c) => c.moisAnnee === 7), 'août repéré dans le portefeuille');
  assert.equal(p.horsEchantillon.activites, 1);
  proche(p.horsEchantillon.lossRatio, p.lignes[0].test.lossRatio, 1e-12, 'agrégat = seule activité testée');
  const sansDate = M.evaluerPortefeuille(salles, {});
  assert.equal(sansDate.lignes[0].creux.length, 0, 'sans mois de fin connu : pas de diagnostic saisonnier');
});

// ---------------------------------------------------------------------------
// Cohérence globale : invariants vérifiés sur des activités tirées au hasard
// (générateur déterministe : le test est reproductible).
// ---------------------------------------------------------------------------
function generateur(graine) {
  let g = graine;
  const u = () => { g = (g * 1103515245 + 12345) % 2147483648; return (g + 0.5) / 2147483648; };
  const normal = () => Math.sqrt(-2 * Math.log(u())) * Math.cos(2 * Math.PI * u());
  return { u, normal };
}

test('cohérence : invariants comptables et seuil sur 300 activités aléatoires', () => {
  const { u } = generateur(7);
  for (let i = 0; i < 300; i += 1) {
    const habituel = 0.35 + u() * 0.55;
    const e = {
      placesParMois: 20 + Math.floor(u() * 400), prix: 5 + u() * 45, commission: [0.05, 0.10, 0.15][i % 3],
      remplissage: habituel, moisFaible: habituel * (0.55 + u() * 0.4), gamma: 1.5 + u() * 4, frais: u() < 0.5 ? 0 : u() * 20
    };
    if (u() < 0.4) e.prixPropose = Math.round(u() * 150);
    const r = M.evaluerSalle(e);
    const ctx = `activité ${i}`;
    proche(r.payoutPlein, e.placesParMois * e.prix * (1 - e.commission), 1e-6, ctx + ' revenu plein');
    assert.ok(r.plancherTaux < r.remplissageMoyen, ctx + ' plancher sous la moyenne');
    proche(r.probaSousPlancher, 0.10, 0.003, ctx + ' 1 mois sur 10 sous le plancher');
    assert.ok(r.primeCommerciale >= r.primeMinimale - 1e-9, ctx + ' prix calculé ≥ prix minimal');
    proche(r.primeMinimale, r.primePure + (e.frais || 0), 1e-9, ctx + ' prix minimal');
    if (r.prime > 0) proche(r.lossRatio, r.primePure / r.prime, 1e-12, ctx + ' loss ratio');
    proche(r.margeJiyufit, r.commissionJiyufit + r.margeGarantie, 1e-9, ctx + ' marge totale');
    if (r.seuil.deficitaire) {
      assert.ok(r.margeGarantie <= 1e-9, ctx + ' déficitaire ⇒ marge garantie ≤ 0');
    } else {
      assert.ok(r.seuil.remplissageMoyen <= r.remplissageMoyen + 1e-9, ctx + ' seuil sous le remplissage actuel');
    }
  }
});

test('cohérence : plus les mois sont irréguliers, plus la garantie coûte', () => {
  let precedent = -Infinity;
  for (const s of [0.1, 0.2, 0.35, 0.5, 0.8, 1.2]) {
    const r = M.evaluerSalle({ ...VOLT, dispersion: s });
    assert.ok(r.primePure > precedent, `dispersion ${s} : prime pure croissante`);
    precedent = r.primePure;
  }
});

test('cohérence : sur un long historique tiré d’une loi connue, on retrouve son plancher', () => {
  const { normal } = generateur(2026);
  const mediane = 0.65, s = 0.35;
  const historique = Array.from({ length: 600 }, () => M.invLogit(M.logit(mediane) + s * normal()));
  const r = M.evaluerSalle({ placesParMois: 173, prix: 12, commission: 0.15, historique });
  const theorique = M.distributionLogitNormale(mediane, s).quantile(0.10);
  proche(r.plancherTaux, theorique, 0.015, 'plancher estimé ≈ plancher théorique (P10)');
  const estimation = M.evaluerSalle({ placesParMois: 173, prix: 12, commission: 0.15, remplissage: mediane, dispersion: s });
  proche(r.primePure, estimation.primePure, estimation.primePure * 0.25, 'même ordre de prix que le mode estimation');
});

test('cohérence : le portefeuille est exactement la somme de ses activités', () => {
  const { u } = generateur(99);
  const salles = Array.from({ length: 25 }, (_, i) => ({
    nom: 'A' + i, placesParMois: 50 + Math.floor(u() * 200), prix: 8 + u() * 30, commission: 0.15,
    remplissage: 0.5 + u() * 0.3, moisFaible: 0.3 + u() * 0.15, prixPropose: u() < 0.5 ? Math.round(20 + u() * 80) : null
  }));
  const p = M.evaluerPortefeuille(salles, { choc: 0.1 });
  const somme = (f) => p.lignes.reduce((a, l) => a + f(l.resultat), 0);
  proche(p.primes, somme((r) => r.prime), 1e-6, 'primes');
  proche(p.sinistresAttendus, somme((r) => r.primePure), 1e-6, 'compléments');
  proche(p.marge, somme((r) => r.margeJiyufit), 1e-6, 'marge');
  assert.ok(p.lossRatioSousChoc > p.lossRatio, 'le stress corrélé dégrade le loss ratio');
});

test('performance sans perte : complément et probabilité rapides = intégration complète', () => {
  for (const mediane of [0.3, 0.5, 0.65, 0.85]) {
    for (const s of [0.05, 0.35, 0.9, 1.6]) {
      const d = M.distributionLogitNormale(mediane, s);
      for (const q of [0.02, 0.1, 0.3]) {
        const plancher = d.quantile(q);
        const complet = d.esperance((f) => Math.max(0, plancher - f));
        proche(d.manqueMoyen(plancher), complet, Math.max(1e-7, complet * 1e-4), `manque (${mediane}, ${s}, P${q * 100})`);
        proche(d.probaSous(plancher), q, 1e-6, `probabilité (${mediane}, ${s}, P${q * 100})`);
      }
    }
  }
});

test('CSV : dernier_mois situe les creux au bon mois (studios lyonnais : juin, pas février)', () => {
  const csv = fs.readFileSync(path.join(__dirname, '..', 'exemples', 'studios_lyon_2026-09.csv'), 'utf8');
  const salles = M.lireCsv(csv);
  assert.equal(salles[0].moisFin, 11, 'dernier relevé en décembre 2025');
  const p = M.evaluerPortefeuille(salles, { moisFin: 7 });     // la colonne prime sur la convention (août)
  const creux = Array.from(p.lignes[0].creux, (c) => c.moisAnnee);
  assert.ok(creux.includes(5), 'juin (5) est bien le creux récurrent du profil');
  assert.equal(creux.includes(1), false, 'plus de faux creux en février');
  assert.throws(() => M.lireCsv('nom;places_mois;prix;dernier_mois\nA;10;10;2025/12'), /AAAA-MM/);
});
