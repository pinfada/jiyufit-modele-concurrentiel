"""Scénarios bifaces locaux : compatibilité, capacité, churn et OPEX.

Hypothèses de travail, non calibrées sur Mindbody/ClassPass. Le produit U*S
compte des paires possibles ; il ne constitue ni revenu ni loi empirique.
"""
from dataclasses import dataclass, asdict
import math


@dataclass(frozen=True)
class Parametres:
    marche_utilisateurs: float = 20000
    marche_prestataires: float = 200
    demandes_par_utilisateur: float = 4
    places_par_prestataire: float = 100
    compatibilite: float = .015
    recrutement_utilisateurs: float = 20
    recrutement_prestataires: float = 1
    effet_utilisateurs: float = .24
    effet_prestataires: float = .18
    attrition_utilisateurs: float = .08
    attrition_prestataires: float = .035
    prix_seance: float = 20
    commission: float = .20
    cout_variable_reservation: float = .60
    opex_fixes: float = 8000
    opex_par_prestataire: float = 5
    cac_utilisateur: float = 10
    cac_prestataire: float = 100

    def valider(self):
        if not all(math.isfinite(v) and v >= 0 for v in asdict(self).values()):
            raise ValueError('Paramètres finis et non négatifs requis')
        if min(self.marche_utilisateurs, self.marche_prestataires) <= 0:
            raise ValueError('Marchés adressables strictement positifs requis')
        for name in ('effet_utilisateurs','effet_prestataires','attrition_utilisateurs',
                     'attrition_prestataires','commission'):
            if getattr(self,name)>1: raise ValueError(name+' doit être entre 0 et 1')


def liquidite(utilisateurs, prestataires, p=Parametres()):
    p.valider()
    if not all(math.isfinite(v) and v>=0 for v in (utilisateurs,prestataires)):
        raise ValueError('États finis non négatifs requis')
    # Poisson : nombre d'offres compatibles pour une recherche locale.
    probable = -math.expm1(-p.compatibilite*prestataires) if p.places_par_prestataire else 0.
    demandes = p.demandes_par_utilisateur*utilisateurs
    capacite = p.places_par_prestataire*prestataires
    reservations = min(demandes*probable, capacite)
    return dict(paires_potentielles=utilisateurs*prestataires,
                probabilite_offre_compatible=probable, demandes=demandes, capacite=capacite,
                reservations=reservations,
                taux_service=reservations/demandes if demandes else None,
                remplissage=reservations/capacite if capacite else None)


def etape(utilisateurs, prestataires, p=Parametres()):
    metrics = liquidite(utilisateurs,prestataires,p)
    if utilisateurs>p.marche_utilisateurs or prestataires>p.marche_prestataires:
        raise ValueError('État supérieur au marché adressable')
    service = metrics['taux_service'] or 0.
    fill = metrics['remplissage'] or 0.
    def entrees(stock, ceiling, paid, feedback):
        saturation = 1-stock/ceiling
        acquisition, organique = paid*saturation, feedback*stock*saturation
        total = acquisition+organique
        facteur = min(1., (ceiling-stock)/total) if total else 1.
        return acquisition*facteur, organique*facteur
    paid_u, organic_u = entrees(utilisateurs,p.marche_utilisateurs,p.recrutement_utilisateurs,p.effet_utilisateurs*service)
    paid_s, organic_s = entrees(prestataires,p.marche_prestataires,p.recrutement_prestataires,p.effet_prestataires*fill)
    next_u = utilisateurs*(1-p.attrition_utilisateurs)+paid_u+organic_u
    next_s = prestataires*(1-p.attrition_prestataires)+paid_s+organic_s
    revenu = p.prix_seance*p.commission*metrics['reservations']
    couts = (p.cout_variable_reservation*metrics['reservations'] + p.opex_fixes
             + p.opex_par_prestataire*prestataires + p.cac_utilisateur*paid_u + p.cac_prestataire*paid_s)
    return dict(metrics, utilisateurs=utilisateurs, prestataires=prestataires,
                nouveaux_utilisateurs_payants=paid_u, nouveaux_utilisateurs_organiques=organic_u,
                nouveaux_prestataires_payants=paid_s, nouveaux_prestataires_organiques=organic_s,
                croissance_organique_utilisateurs=(organic_u-p.attrition_utilisateurs*utilisateurs),
                croissance_organique_prestataires=(organic_s-p.attrition_prestataires*prestataires),
                revenu_plateforme=revenu, couts_opex=couts, solde_exploitation=revenu-couts,
                utilisateurs_suivants=next_u, prestataires_suivants=next_s)


def simuler(utilisateurs=100, prestataires=5, mois=120, p=Parametres()):
    if type(mois) is not int or not 1<=mois<=1200: raise ValueError('Durée entre 1 et 1200 mois')
    rows, cumul, besoin = [], 0., 0.
    for t in range(mois):
        row = etape(utilisateurs,prestataires,p)
        cumul += row['solde_exploitation']; besoin=max(besoin,-cumul)
        rows.append(dict(mois=t,**row,solde_cumule=cumul,financement_cumule_requis=besoin))
        utilisateurs,prestataires = row['utilisateurs_suivants'],row['prestataires_suivants']
    return rows


def seuil_offre_necessaire(p=Parametres()):
    """Borne de densité nécessaire, hors saturation/congestion ; pas point de bascule estimé."""
    p.valider()
    if p.effet_utilisateurs<=p.attrition_utilisateurs or p.compatibilite==0:
        return None
    return -math.log1p(-p.attrition_utilisateurs/p.effet_utilisateurs)/p.compatibilite


def diagnostic_simulation(rows):
    # Définition opérationnelle annoncée, différente d'une bifurcation mathématique.
    first = next((i for i in range(len(rows)-2) if all(
        r['croissance_organique_utilisateurs']>0 and r['croissance_organique_prestataires']>0
        for r in rows[i:i+3])), None)
    return dict(premier_mois_croissance_organique_deux_faces_sur_3_mois=first,
                rentabilite_mensuelle_finale=rows[-1]['solde_exploitation'],
                financement_cumule_requis=rows[-1]['financement_cumule_requis'],
                calibration_empirique=False)


def elasticite_locale(utilisateurs,prestataires,p=Parametres()):
    """Sensibilité numérique des réservations à un doublement simultané, pas causalité."""
    before=liquidite(utilisateurs,prestataires,p)['reservations']
    after=liquidite(2*utilisateurs,2*prestataires,p)['reservations']
    return math.log(after/before,2) if before>0 else None
