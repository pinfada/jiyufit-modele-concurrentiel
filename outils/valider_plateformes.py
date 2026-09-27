"""Exécuter les contrôles publics Mindbody/ClassPass et des scénarios bifaces distincts."""
import argparse
import csv
from dataclasses import asdict, replace
import hashlib
import json
from pathlib import Path
import sys
import numpy as np

if __package__ in (None,''):
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from outils.valider_concurrent import backtest, scores
from outils.marche_biface import Parametres, simuler, diagnostic_simulation, seuil_offre_necessaire, elasticite_locale

ROOT=Path(__file__).resolve().parents[1]


def charger_public(folder):
    path=Path(folder)/'observations.csv'
    provenance=json.loads((Path(folder)/'provenance.json').read_text(encoding='utf-8'))
    if hashlib.sha256(path.read_bytes()).hexdigest()!=provenance['sha256_csv']:
        raise ValueError('Source publique modifiée : '+str(path))
    with path.open(encoding='utf-8',newline='') as stream:
        rows=list(csv.DictReader(stream))
    return rows,provenance


def evaluation_publique():
    mb,mb_source=charger_public(ROOT/'data/public/mindbody_2015_2018')
    cp,cp_source=charger_public(ROOT/'data/public/classpass_public')
    dates=[r['trimestre'] for r in mb]
    expected=[f'{2015+i//4}-Q{i%4+1}' for i in range(1,15)]
    if dates!=expected: raise ValueError('Mindbody : série trimestrielle irrégulière')
    series={'professionnels':np.array([float(r['abonnes_professionnels']) for r in mb]),
            'revenu_millions_usd':np.array([float(r['revenu_trimestriel_millions_usd']) for r in mb])}
    predictions=[]; results={}
    for name,values in series.items():
        rows=backtest(values,dates,min_train=8)
        # La fonction commune utilise des noms d'unité historiques : les adapter.
        results[name]=[dict(model=r['model'],horizon_trimestres=r['horizon_trimestres'],n=r['n'],
                            rmse=r['rmse_abonnements'],mae=r['mae_abonnements']) for r in scores(rows)]
        predictions.extend(dict(serie=name,**r) for r in rows)
    i,j=dates.index('2016-Q4'),dates.index('2017-Q4')
    report=dict(mindbody=dict(trimestres=len(mb),debut=dates[0],fin=dates[-1],scores=results,
                    variation_2017_professionnels=float(series['professionnels'][j]/series['professionnels'][i]-1),
                    variation_2017_revenu_trimestriel=float(series['revenu_millions_usd'][j]/series['revenu_millions_usd'][i]-1),
                    rupture_prix_2017=True,rupture_acquisitions_2018=True,
                    statut='contrôles prédictifs univariés ; pas calibration biface',
                    consommateurs_24m_pas_utilisateurs_actifs_mensuels=True),
                classpass=dict(observations=len(cp),observations_detail=cp,
                    statut='backtest de liquidité non identifiable avec les indicateurs publiés collectés',
                    raisons=['Pas de série régulière simultanée utilisateurs/offre disponible/recherches.',
                             'Cumuls et flux annuels non interchangeables ; fenêtres 2023/2024/2025 différentes.',
                             '27 millions de recherches Pilates et 15 millions de réservations sont des bornes et des événements différents.',
                             '85 % de classes non complètes ne mesure pas la probabilité de trouver une séance compatible.']),
                validation_metcalfe=False,calibration_point_bascule=False,
                independance_deux_marques_depuis_2021=False)
    return report,predictions,mb


def executer(sortie):
    report,predictions,mb=evaluation_publique()
    p=Parametres()
    scenarios={
        'reseau_et_compatibilite':p,
        'sans_boucle_reseau':replace(p,effet_utilisateurs=0,effet_prestataires=0),
        'offre_peu_compatible':replace(p,compatibilite=.001),
        'capacite_contrainte':replace(p,places_par_prestataire=2),
    }
    trajectories={name:simuler(p=config) for name,config in scenarios.items()}
    report['scenarios_non_calibres']={name:dict(parametres=asdict(config),
        **diagnostic_simulation(trajectories[name]),
        borne_offre_necessaire_hors_congestion=seuil_offre_necessaire(config)) for name,config in scenarios.items()}
    report['elasticite_reservations_doublement_deux_faces_synthetique']={
        'faible_densite':elasticite_locale(10,.01,p),
        'forte_densite':elasticite_locale(100,1000,p)}
    sortie=Path(sortie); sortie.mkdir(parents=True,exist_ok=True)
    (sortie/'resultats.json').write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    for name,rows in [('mindbody_predictions.csv',predictions),
                      ('scenarios_synthetiques.csv',[dict(scenario=name,**r) for name,rr in trajectories.items() for r in rr])]:
        with (sortie/name).open('w',encoding='utf-8',newline='') as stream:
            writer=csv.DictWriter(stream,fieldnames=list(rows[0]));writer.writeheader();writer.writerows(rows)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(2,2,figsize=(12,8),layout='constrained')
    for name,rows in trajectories.items():
        x=[r['mois'] for r in rows]
        for ax,field,label in [(axes[0,0],'utilisateurs','Utilisateurs'),(axes[0,1],'prestataires','Prestataires'),
                               (axes[1,0],'taux_service','Fraction des demandes servies'),
                               (axes[1,1],'solde_exploitation','Solde exploitation (EUR/mois)')]:
            ax.plot(x,[r[field] for r in rows],label=name);ax.set_ylabel(label);ax.set_xlabel('Mois simulé')
    axes[0,0].legend(fontsize=7)
    axes[1,0].set_ylim(0,1)
    axes[1,1].axhline(0,color='k',lw=.6)
    fig.suptitle('Scénarios bifaces hypothétiques — aucune calibration Mindbody/ClassPass')
    fig.savefig(sortie/'scenarios_bifaces.png',dpi=140);plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11,4),layout='constrained')
    for ax,key,label in [(axes[0],'abonnes_professionnels','Sites/praticiens abonnés'),
                         (axes[1],'revenu_trimestriel_millions_usd','CA trimestriel (millions USD)')]:
        ax.plot([r['trimestre'] for r in mb],[float(r[key]) for r in mb],'o-')
        ax.tick_params(axis='x',rotation=65,labelsize=7);ax.set_ylabel(label)
        ax.axvline(7,color='orange',ls=':',label='Recentrage 2017')
        ax.axvline(12,color='red',ls=':',label='Booker 2018')
    axes[0].legend(fontsize=7);fig.suptitle('Mindbody — observations publiées, périmètre changeant')
    fig.savefig(sortie/'mindbody_observe.png',dpi=140);plt.close(fig)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sortie',type=Path,default=Path('artifacts/validation-plateformes'))
    args=parser.parse_args()
    try: report=executer(args.sortie)
    except (OSError,ValueError,TypeError) as exc: parser.error(str(exc))
    print('Mindbody :',report['mindbody']['trimestres'],'trimestres, deux indicateurs observés.')
    print('ClassPass :',report['classpass']['observations'],'observations ; liquidité non identifiable.')
    for name,r in report['scenarios_non_calibres'].items():
        print(name,': premier mois de croissance organique des deux faces sur 3 mois =',
              r['premier_mois_croissance_organique_deux_faces_sur_3_mois'])
    print('Metcalfe et point de bascule empiriques : non validés. Rapport :',args.sortie)


if __name__=='__main__': main()
